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


SIGNALS_QUERY = """
query GetSignals($limit: Int!, $offset: Int!) {
  extraction(limit: $limit, offset: $offset, order_by: { id: asc }) {
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

FEEDBACK_QUERY = """
query GetFeedback($limit: Int!, $offset: Int!) {
  conversation_message(
    limit: $limit,
    offset: $offset,
    order_by: { id: asc },
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
    """Source connector for BuildBetter."""

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
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def check_connection(self) -> Tuple[bool, str | None]:
        """Test the connection by fetching a single record."""
        try:
            if self.config.stream == "feedback":
                result = self._execute_query(FEEDBACK_QUERY, {"limit": 1, "offset": 0})
            else:
                result = self._execute_query(SIGNALS_QUERY, {"limit": 1, "offset": 0})

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
        """Fetch records from BuildBetter."""
        offset = pagination.get("offset", 0) if pagination else 0

        if self.config.stream == "feedback":
            return self._get_feedback(offset)
        else:
            return self._get_signals(offset)

    def _get_signals(self, offset: int) -> SourceIteration:
        """Fetch signals (AI-extracted insights)."""
        result = self._execute_query(SIGNALS_QUERY, {"limit": self.PAGE_SIZE, "offset": offset})

        if "errors" in result:
            raise Exception(f"GraphQL error: {result['errors']}")

        extractions = result.get("data", {}).get("extraction", [])

        records = [
            SourceRecord(id=str(signal["id"]), data=self._transform_signal(signal))
            for signal in extractions
        ]

        next_pagination = {}
        if len(extractions) == self.PAGE_SIZE:
            next_pagination = {"offset": offset + self.PAGE_SIZE}

        return SourceIteration(next_pagination=next_pagination, records=records)

    def _get_feedback(self, offset: int) -> SourceIteration:
        """Fetch feedback form submissions."""
        result = self._execute_query(FEEDBACK_QUERY, {"limit": self.PAGE_SIZE, "offset": offset})

        if "errors" in result:
            raise Exception(f"GraphQL error: {result['errors']}")

        messages = result.get("data", {}).get("conversation_message", [])

        records = [
            SourceRecord(id=str(msg["id"]), data=self._transform_feedback(msg))
            for msg in messages
        ]

        next_pagination = {}
        if len(messages) == self.PAGE_SIZE:
            next_pagination = {"offset": offset + self.PAGE_SIZE}

        return SourceIteration(next_pagination=next_pagination, records=records)
