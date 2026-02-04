import json
from abc import ABC
from enum import Enum
from http import HTTPStatus
from typing import Any, Generator, List, Optional, Tuple

from bizon.source.auth.authenticators.oauth import Oauth2AuthParams
from bizon.source.auth.authenticators.token import TokenAuthParams
from bizon.source.auth.builder import AuthBuilder
from bizon.source.auth.config import AuthType
from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.session import Session
from bizon.source.source import AbstractSource
from loguru import logger
from pydantic import BaseModel, Field
from requests import HTTPError
from requests.adapters import HTTPAdapter, Retry
from requests.auth import AuthBase

URL_BASE = "https://api.hubapi.com"
URL_GRANTED_SCOPES = f"{URL_BASE}/oauth/v1/access-tokens"
URL_TOKEN_REFRESH = f"{URL_BASE}/oauth/v1/token"


class HubSpotBaseSource(AbstractSource, ABC):
    def get_session(self) -> Session:
        """Apply custom strategy for HubSpot"""
        session = Session()

        # Retry policy if rate-limited by HubSpot
        retries = Retry(
            total=50,
            backoff_factor=1,
            raise_on_status=True,
            status_forcelist=[429, 500, 502, 503, 504],
            status=30,
            allowed_methods=["GET", "POST"],
        )
        session.mount("https://", HTTPAdapter(max_retries=retries, pool_maxsize=64))
        return session

    def get_authenticator(self) -> AuthBase:
        if self.config.authentication.type.value == AuthType.OAUTH.value:
            return AuthBuilder.oauth2(
                params=Oauth2AuthParams(
                    token_refresh_endpoint=URL_TOKEN_REFRESH,
                    client_id=self.config.authentication.params.client_id,
                    client_secret=self.config.authentication.params.client_secret,
                    refresh_token=self.config.authentication.params.refresh_token,
                )
            )

        elif self.config.authentication.type.value == AuthType.API_KEY.value:
            return AuthBuilder.token(
                params=TokenAuthParams(
                    token=self.config.authentication.params.token,
                )
            )

        raise NotImplementedError(f"Auth type {self.config.authentication.type} not implemented for HubSpot")

    def check_connection(self) -> Tuple[bool, Optional[Any]]:
        """Check connection"""
        alive = True
        error_msg = None
        try:
            objects, state = self.get()
        except HTTPError as error:
            alive = False
            error_msg = repr(error)
            if error.response.status_code == HTTPStatus.BAD_REQUEST:
                response_json = error.response.json()
                error_msg = (
                    f"400 Bad Request: {response_json['message']}, please check if provided credentials are valid."
                )
        except Exception as e:
            alive = False
            error_msg = repr(e)
        return alive, error_msg

    def get_granted_scopes(self) -> List[str]:
        try:
            if self.config.authentication.type == AuthType.OAUTH.value:
                response = self.session.get(url=f"{URL_GRANTED_SCOPES}/{self.session.auth.access_token}")
            else:
                raise NotImplementedError("Scope endpoint for API Key are not supported.")
            response.raise_for_status()
            response_json = response.json()
            granted_scopes = response_json["scopes"]
            return granted_scopes
        except Exception as e:
            return False, repr(e)


class PropertiesStrategy(str, Enum):
    ALL = "all"
    SELECTED = "selected"


class PropertiesConfig(BaseModel):
    strategy: PropertiesStrategy = Field(PropertiesStrategy.ALL, description="Properties strategy")
    selected_properties: Optional[List[str]] = Field([], description="List of selected properties")


class HubSpotSourceConfig(SourceConfig):
    properties: PropertiesConfig = PropertiesConfig(strategy=PropertiesStrategy.ALL, selected_properties=None)
    associations_types: List[str] = Field([], description="List of associations types to retrieve")


class HubSpotObjectsSource(HubSpotBaseSource):
    api_version = "v3"

    object_path = f"crm/{api_version}/objects"
    properties_path = f"crm/{api_version}/properties"

    def __init__(self, config: HubSpotSourceConfig):
        super().__init__(config)
        self.config: HubSpotSourceConfig = config
        self.object = self.config.stream
        self.selected_properties = []  # Initialize properties to empty list

        # If we are initializing the pipeline, we retrieve the selected properties from HubSpot
        if config.init_pipeline:
            self.selected_properties = self.get_selected_properties()

    @staticmethod
    def streams() -> List[str]:
        return [
            "contacts",
            "companies",
            "deals",
            "2-48391801",  # Partner Onboarding
            "2-48061043",  # ARR Forecasts
        ]

    @staticmethod
    def get_config_class() -> SourceConfig:
        return HubSpotSourceConfig

    @property
    def url_list(self) -> str:
        return f"{URL_BASE}/{self.object_path}/{self.object}"

    @property
    def url_list_properties(self) -> str:
        return f"{URL_BASE}/{self.properties_path}/{self.object}"

    @property
    def url_search(self) -> str:
        return f"{URL_BASE}/{self.object_path}/{self.object}/search"

    def _request_api(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        payload: Optional[dict] = None,
        headers=None,
    ) -> Generator[dict, None, None]:
        # Call HubSpot API
        response = self.session.call(
            method=method,
            url=url,
            params=params,
            data=json.dumps(payload),
            headers=headers,
        )
        return response.json()

    def get_selected_properties(self) -> List[str]:
        properties = []

        if self.config.properties.strategy == "selected":
            # We check that all properties slected are present in the list of all properties
            properties = self.config.properties.selected_properties

        return properties

    def _get(self, after: str = None) -> Optional[dict]:
        params = {
            "limit": 100,
            "properties": ",".join(self.selected_properties),
            "associations": ",".join(self.config.associations_types),
        }
        if after:
            params["after"] = after

        return self._request_api(method="GET", url=self.url_list, params=params)

    def get(
        self,
        pagination: dict = None,
    ) -> SourceIteration:
        """Return the next page of data from HubSpot
        Returns:
            dict, Optional[List[dict]]]: Next pagination dict and data
        """

        if not pagination:
            response = self._get()
        else:
            response = self._get(after=pagination["after"])

        return self.parse_response(response)

    def parse_response(self, response: dict) -> SourceIteration:
        # If no response or no results, we return empty dict
        if not response or len(response.get("results", [])) == 0:
            return SourceIteration(next_pagination={}, records=[])

        # If no next page, we set is_finished to True
        if response.get("paging", dict()).get("next", None) is None:
            return SourceIteration(
                next_pagination={},
                records=[
                    SourceRecord(
                        id=record["id"],
                        data=record,
                    )
                    for record in response["results"]
                ],
            )

        # If there is a next page, we set the paging object
        next_pagination_dict = {
            "link": response["paging"]["next"]["link"],
            "after": response["paging"]["next"]["after"],
        }
        return SourceIteration(
            next_pagination=next_pagination_dict,
            records=[
                SourceRecord(
                    id=record["id"],
                    data=record,
                )
                for record in response["results"]
            ],
        )

    def get_total_records_count(self) -> Optional[int]:
        search_response = self._request_api(
            method="POST",
            url=self.url_search,
            payload={"filterGroups": [{"filters": [{"operator": "HAS_PROPERTY", "propertyName": "hs_object_id"}]}]},
        )
        total = search_response["total"]
        logger.info(f"Number of {self.object} in HubSpot: {'{:,}'.format(total).replace(',', ' ')}")

        # Do not raise an error if no records are found
        # As we don't have records yet for ARR forecasts
        if total == 0:
            return None

        return total
