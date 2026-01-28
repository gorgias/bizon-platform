"""Custom source: BuildBetter - Fetches feedback and signals from BuildBetter."""

from typing import List, Tuple

import requests
from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.source import AbstractSource
from requests.auth import AuthBase


class BuildBetterSourceConfig(SourceConfig):
    """Configuration for BuildBetter source."""

    api_key: str


# Incremental query with created_at filter
SIGNALS_QUERY_INCREMENTAL = """
query GetSignals($limit: Int!, $cursor: timestamp!) {
  extraction(
    limit: $limit,
    order_by: { created_at: asc },
    where: { created_at: { _gt: $cursor } }
  ) {
    id
    summary
    context
    start_sec
    end_sec
    interview_id
    created_at
    types { type { name } }
    topics { topic { text } }
    attendee {
      person {
        first_name
        last_name
        email
      }
    }
  }
}
"""

# Full sync query (no filter)
SIGNALS_QUERY_FULL = """
query GetSignals($limit: Int!, $offset: Int!) {
  extraction(
    limit: $limit,
    offset: $offset,
    order_by: { created_at: asc }
  ) {
    id
    summary
    context
    start_sec
    end_sec
    interview_id
    created_at
    types { type { name } }
    topics { topic { text } }
    attendee {
      person {
        first_name
        last_name
        email
      }
    }
  }
}
"""

# Incremental feedback query
FEEDBACK_QUERY_INCREMENTAL = """
query GetFeedback($limit: Int!, $cursor: timestamptz!) {
  conversation_message(
    limit: $limit,
    order_by: { created_at: asc },
    where: {
      _and: [
        { message: { _ilike: "%Feedback Submitted%" } },
        { created_at: { _gt: $cursor } }
      ]
    }
  ) {
    id
    message
    sent_at
    created_at
    speaker
    conversation_id
    author {
      id
      person {
        first_name
        last_name
        email
      }
    }
  }
}
"""

# Full sync feedback query
FEEDBACK_QUERY_FULL = """
query GetFeedback($limit: Int!, $offset: Int!) {
  conversation_message(
    limit: $limit,
    offset: $offset,
    order_by: { created_at: asc },
    where: { message: { _ilike: "%Feedback Submitted%" } }
  ) {
    id
    message
    sent_at
    created_at
    speaker
    conversation_id
    author {
      id
      person {
        first_name
        last_name
        email
      }
    }
  }
}
"""


class BuildBetterSource(AbstractSource):
    """Source connector for BuildBetter.

    Supports incremental sync using created_at as cursor field.
    Configure with: sync_mode: incremental, cursor_field: created_at
    """

    API_URL = "https://api.buildbetter.app/v1/graphql"
    PAGE_SIZE = 100

    def __init__(self, config: BuildBetterSourceConfig):
        super().__init__(config)
        self.config: BuildBetterSourceConfig = config

    @staticmethod
    def streams() -> List[str]:
        """Return available streams."""
        return ["feedback", "signals"]

    @staticmethod
    def get_config_class() -> type:
        """Return the config class."""
        return BuildBetterSourceConfig

    def get_authenticator(self) -> AuthBase | None:
        """Return authenticator if needed."""
        return None

    def _get_headers(self) -> dict:
        """Return headers for API requests."""
        return {
            "Content-Type": "application/json",
            "X-Buildbetter-API-Key": self.config.api_key,
        }

    def _execute_query(self, query: str, variables: dict) -> dict:
        """Execute a GraphQL query."""
        response = requests.post(
            self.API_URL,
            json={"query": query, "variables": variables},
            headers=self._get_headers(),
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def check_connection(self) -> Tuple[bool, str | None]:
        """Test the connection by fetching a single record."""
        try:
            if self.config.stream == "feedback":
                result = self._execute_query(FEEDBACK_QUERY_FULL, {"limit": 1, "offset": 0})
            else:
                result = self._execute_query(SIGNALS_QUERY_FULL, {"limit": 1, "offset": 0})

            if "errors" in result:
                return False, f"GraphQL error: {result['errors']}"
            return True, None
        except requests.exceptions.RequestException as e:
            return False, f"Connection failed: {str(e)}"

    def get_total_records_count(self) -> int | None:
        """Return total record count if known."""
        return None

    def _transform_signal(self, signal: dict) -> dict:
        """Transform a signal record to flat structure."""
        # Extract types as comma-separated string
        types = ",".join(
            t.get("type", {}).get("name", "") for t in signal.get("types", []) if t.get("type")
        )

        # Extract topics as comma-separated string
        topics = ",".join(
            t.get("topic", {}).get("text", "") for t in signal.get("topics", []) if t.get("topic")
        )

        # Extract speaker info
        attendee = signal.get("attendee") or {}
        person = attendee.get("person") or {}
        speaker_first = person.get("first_name", "")
        speaker_last = person.get("last_name", "")
        speaker_name = f"{speaker_first} {speaker_last}".strip() if speaker_first or speaker_last else None
        speaker_email = person.get("email")

        return {
            "id": signal.get("id"),
            "summary": signal.get("summary"),
            "context": signal.get("context"),
            "start_sec": signal.get("start_sec"),
            "end_sec": signal.get("end_sec"),
            "interview_id": signal.get("interview_id"),
            "created_at": signal.get("created_at"),
            "types": types or None,
            "topics": topics or None,
            "speaker_name": speaker_name,
            "speaker_email": speaker_email,
        }

    def _transform_feedback(self, msg: dict) -> dict:
        """Transform a feedback message to flat structure."""
        # Extract author info
        author = msg.get("author") or {}
        person = author.get("person") or {}
        author_first = person.get("first_name", "")
        author_last = person.get("last_name", "")
        author_name = f"{author_first} {author_last}".strip() if author_first or author_last else None
        author_email = person.get("email")

        return {
            "id": msg.get("id"),
            "message": msg.get("message"),
            "sent_at": msg.get("sent_at"),
            "created_at": msg.get("created_at"),
            "conversation_id": msg.get("conversation_id"),
            "author_name": author_name,
            "author_email": author_email,
        }

    def get(self, pagination: dict = None) -> SourceIteration:
        """Fetch records from BuildBetter.

        Supports incremental sync via cursor in pagination:
        - pagination.cursor: ISO timestamp to fetch records created after
        - pagination.offset: For full sync pagination
        """
        pagination = pagination or {}
        cursor = pagination.get("cursor")

        if self.config.stream == "feedback":
            return self._get_feedback(pagination, cursor)
        else:
            return self._get_signals(pagination, cursor)

    def _get_signals(self, pagination: dict, cursor: str | None) -> SourceIteration:
        """Fetch signals (AI-extracted insights)."""
        if cursor:
            # Incremental sync - filter by created_at > cursor
            result = self._execute_query(
                SIGNALS_QUERY_INCREMENTAL,
                {"limit": self.PAGE_SIZE, "cursor": cursor},
            )
        else:
            # Full sync - use offset pagination
            offset = pagination.get("offset", 0)
            result = self._execute_query(
                SIGNALS_QUERY_FULL,
                {"limit": self.PAGE_SIZE, "offset": offset},
            )

        if "errors" in result:
            raise Exception(f"GraphQL error: {result['errors']}")

        extractions = result.get("data", {}).get("extraction", [])

        records = [
            SourceRecord(id=str(signal["id"]), data=self._transform_signal(signal))
            for signal in extractions
        ]

        # Determine next pagination
        next_pagination = {}
        if len(extractions) == self.PAGE_SIZE:
            if cursor:
                # For incremental, use the last record's created_at as next cursor
                last_created_at = extractions[-1].get("created_at")
                next_pagination = {"cursor": last_created_at}
            else:
                # For full sync, use offset
                offset = pagination.get("offset", 0)
                next_pagination = {"offset": offset + self.PAGE_SIZE}

        return SourceIteration(next_pagination=next_pagination, records=records)

    def _get_feedback(self, pagination: dict, cursor: str | None) -> SourceIteration:
        """Fetch feedback form submissions."""
        if cursor:
            # Incremental sync
            result = self._execute_query(
                FEEDBACK_QUERY_INCREMENTAL,
                {"limit": self.PAGE_SIZE, "cursor": cursor},
            )
        else:
            # Full sync
            offset = pagination.get("offset", 0)
            result = self._execute_query(
                FEEDBACK_QUERY_FULL,
                {"limit": self.PAGE_SIZE, "offset": offset},
            )

        if "errors" in result:
            raise Exception(f"GraphQL error: {result['errors']}")

        messages = result.get("data", {}).get("conversation_message", [])

        records = [
            SourceRecord(id=str(msg["id"]), data=self._transform_feedback(msg))
            for msg in messages
        ]

        # Determine next pagination
        next_pagination = {}
        if len(messages) == self.PAGE_SIZE:
            if cursor:
                last_created_at = messages[-1].get("created_at")
                next_pagination = {"cursor": last_created_at}
            else:
                offset = pagination.get("offset", 0)
                next_pagination = {"offset": offset + self.PAGE_SIZE}

        return SourceIteration(next_pagination=next_pagination, records=records)
