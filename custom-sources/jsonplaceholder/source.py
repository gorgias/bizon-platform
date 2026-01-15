"""
JSONPlaceholder Custom Source - Tutorial Example

This is a simple custom source that fetches data from JSONPlaceholder API.
Use this as a template for creating your own custom sources.

Usage in pipeline config:
{
    "source": {
        "source_file_path": "/custom-sources/jsonplaceholder/source.py",
        "name": "jsonplaceholder",
        "stream": "posts"
    },
    "destination": {
        "name": "logger",
        "config": {"dummy": "dummy"}
    }
}
"""

from typing import List, Tuple

from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.source import AbstractSource
from requests.auth import AuthBase

# JSONPlaceholder API base URL
BASE_URL = "https://jsonplaceholder.typicode.com"


class JSONPlaceholderSourceConfig(SourceConfig):
    """Configuration for JSONPlaceholder source.

    Inherits from SourceConfig which provides:
    - name: str (source name)
    - stream: str (which stream to fetch)
    - source_file_path: Optional[str] (path to this file)
    """

    pass  # No additional config needed for this simple source


class JSONPlaceholderSource(AbstractSource):
    """Custom source for JSONPlaceholder API.

    Demonstrates how to create a simple custom source with:
    - Multiple streams (posts, comments, users, todos)
    - Pagination (fetches all records at once since API is simple)
    - No authentication required
    """

    def __init__(self, config: JSONPlaceholderSourceConfig):
        super().__init__(config)
        self.config: JSONPlaceholderSourceConfig = config

    @staticmethod
    def streams() -> List[str]:
        """Define available streams for this source."""
        return ["posts", "comments", "users", "todos", "albums", "photos"]

    @staticmethod
    def get_config_class() -> type:
        """Return the config class for this source."""
        return JSONPlaceholderSourceConfig

    def get_authenticator(self) -> AuthBase | None:
        """Return authenticator - None since JSONPlaceholder is public."""
        return None

    def check_connection(self) -> Tuple[bool, str | None]:
        """Test if we can connect to the API."""
        try:
            response = self.session.get(f"{BASE_URL}/posts/1")
            if response.status_code == 200:
                return True, None
            return False, f"API returned status {response.status_code}"
        except Exception as e:
            return False, str(e)

    def get_total_records_count(self) -> int | None:
        """Return total record count if known, None otherwise."""
        # JSONPlaceholder has fixed counts per stream
        counts = {
            "posts": 100,
            "comments": 500,
            "users": 10,
            "todos": 200,
            "albums": 100,
            "photos": 5000,
        }
        return counts.get(self.config.stream)

    def get(self, pagination: dict = None) -> SourceIteration:
        """Fetch records from the API.

        Args:
            pagination: Dict with pagination state (None for first page)

        Returns:
            SourceIteration with records and next_pagination
        """
        # If we already fetched (pagination exists), we're done
        if pagination and pagination.get("done"):
            return SourceIteration(next_pagination={}, records=[])

        # Fetch all records for this stream
        url = f"{BASE_URL}/{self.config.stream}"
        response = self.session.get(url)
        data = response.json()

        # Convert to SourceRecords
        records = [
            SourceRecord(
                id=str(item.get("id", idx)),
                data=item,
            )
            for idx, item in enumerate(data)
        ]

        # Return records with "done" flag - no more pages
        return SourceIteration(
            next_pagination={"done": True},
            records=records,
        )
