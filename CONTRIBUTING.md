# Contributing to Bizon

Thank you for your interest in contributing to Bizon! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and constructive in all interactions. We welcome contributors of all backgrounds and experience levels.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Docker (optional, for containerized development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/bizon-data/bizon.git
   cd bizon
   ```

2. **Install backend dependencies**
   ```bash
   uv sync
   ```

3. **Install frontend dependencies**
   ```bash
   cd ui
   npm install
   cd ..
   ```

4. **Start PostgreSQL**
   ```bash
   docker compose up -d db
   ```

5. **Set up environment**
   ```bash
   cp .env.example .env
   # Generate encryption key
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   # Add the key to .env
   ```

6. **Run database migrations**
   ```bash
   uv run alembic upgrade head
   ```

7. **Start the services**
   ```bash
   # Terminal 1: API server
   uv run python -m bizon_platform

   # Terminal 2: Worker
   uv run python -m bizon_platform.worker

   # Terminal 3: UI
   cd ui && npm run dev
   ```

### Using Docker

For a simpler setup:
```bash
export ENCRYPTION_KEY=$(make key)
make dev
```

## Code Style

We use automated tools to maintain consistent code style.

### Python

- **Formatter**: ruff format
- **Linter**: ruff check
- **Type checker**: mypy

Run manually:
```bash
uv run ruff check bizon_platform tests --fix
uv run ruff format bizon_platform tests
uv run mypy bizon_platform
```

### TypeScript/React

- **Linter**: ESLint
- **Formatter**: Prettier

```bash
cd ui
npm run lint
npm run format
```

### Pre-commit Hooks

Install pre-commit hooks for automatic formatting:
```bash
uv run pre-commit install
```

Run on all files:
```bash
uv run pre-commit run --all-files
```

## Testing

### Running Tests

```bash
# All tests
uv run pytest -v

# Specific test file
uv run pytest tests/api/test_pipelines.py -v

# With coverage
uv run pytest --cov=bizon_platform --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Use `pytest` fixtures from `tests/conftest.py`
- Test files should be named `test_*.py`
- Test functions should be named `test_*`

Example:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_pipeline(client: AsyncClient):
    response = await client.post("/api/pipelines", json={...})
    assert response.status_code == 201
```

## Creating Custom Sources

Custom sources allow you to connect to any data source. They live in `custom_sources/`.

### Structure

```
custom_sources/
└── my_source/
    └── source.py
```

### Template

```python
from typing import List, Tuple
from requests.auth import AuthBase
from bizon.source.config import SourceConfig
from bizon.source.models import SourceIteration, SourceRecord
from bizon.source.source import AbstractSource


class MySourceConfig(SourceConfig):
    """Configuration for my source."""
    api_key: str | None = None


class MySource(AbstractSource):
    """Custom source implementation."""

    @staticmethod
    def streams() -> List[str]:
        return ["stream1", "stream2"]

    @staticmethod
    def get_config_class() -> type:
        return MySourceConfig

    def get_authenticator(self) -> AuthBase | None:
        return None

    def check_connection(self) -> Tuple[bool, str | None]:
        return True, None

    def get_total_records_count(self) -> int | None:
        return None

    def get(self, pagination: dict = None) -> SourceIteration:
        records = [
            SourceRecord(id="1", data={"key": "value"})
        ]
        return SourceIteration(
            next_pagination={},  # Empty = no more pages
            records=records
        )
```

### Testing Your Source

```bash
uv run python -c "
from bizon.source.discover import get_external_source_class_by_source_and_stream

source_class = get_external_source_class_by_source_and_stream(
    source_name='my_source',
    stream_name='stream1',
    filepath='custom_sources/my_source/source.py'
)
print(f'Streams: {source_class.streams()}')

config = source_class.get_config_class()(name='my_source', stream='stream1')
source = source_class(config=config)

success, error = source.check_connection()
print(f'Connection: {\"OK\" if success else error}')
"
```

## Pull Request Process

1. **Fork the repository** and create a feature branch
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** following the code style guidelines

3. **Add tests** for new functionality

4. **Run the test suite**
   ```bash
   uv run pytest -v
   ```

5. **Commit your changes** with a clear message
   ```bash
   git commit -m "feat: add support for X"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation
   - `refactor:` code refactoring
   - `test:` adding tests
   - `chore:` maintenance

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/my-feature
   ```

7. **Describe your changes** in the PR description:
   - What problem does this solve?
   - How did you solve it?
   - Any breaking changes?

## Reporting Issues

When reporting issues, please include:

1. **Description**: Clear description of the problem
2. **Steps to reproduce**: Minimal steps to reproduce
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**: OS, Python version, etc.
6. **Logs**: Relevant error messages or logs

## Questions?

- Open a [GitHub Discussion](https://github.com/bizon-data/bizon/discussions) for questions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0 License.
