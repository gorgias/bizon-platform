"""Custom source: pokeapi"""

from typing import List, Tuple

from requests.auth import AuthBase

from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.source import AbstractSource


class PokeapiConfig(SourceConfig):
    """Configuration for pokeapi source."""

    # Add your config fields here
    # api_key: str = ""
    pass


class PokeapiSource(AbstractSource):
    """Source connector for pokeapi."""

    def __init__(self, config: PokeapiConfig):
        super().__init__(config)
        self.config: PokeapiConfig = config

    @staticmethod
    def streams() -> List[str]:
        """Return available streams."""
        return ["default"]

    @staticmethod
    def get_config_class() -> type:
        """Return the config class."""
        return PokeapiConfig

    def get_authenticator(self) -> AuthBase | None:
        """Return authenticator if needed."""
        return None

    def check_connection(self) -> Tuple[bool, str | None]:
        """Test the connection."""
        # TODO: Implement connection check
        return True, None

    def get_total_records_count(self) -> int | None:
        """Return total record count if known."""
        return None

    def get(self, pagination: dict = None) -> SourceIteration:
        """Fetch records from the source."""
        # TODO: Implement data fetching
        records = [
            SourceRecord(id="1", data={"message": "Hello from pokeapi!"}),
        ]

        return SourceIteration(
            next_pagination=None,  # Set to dict for more pages
            records=records,
        )
