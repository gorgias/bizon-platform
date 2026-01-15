# Bizon

A lightweight, single-tenant platform for running data pipelines. No authentication required.

## Features

- **Pipeline CRUD** - Create, read, update, delete pipelines
- **Cron Scheduling** - Schedule pipelines with cron expressions via APScheduler
- **Saved Connectors** - Reusable source/destination configurations
- **Custom Sources** - Local Python files for custom connectors
- **Security Validation** - AST-based transform validation to prevent malicious code

## Quick Start

### Using Docker Compose

```bash
# Generate encryption key
export ENCRYPTION_KEY=$(make key)

# Development (hot reload)
make dev

# Production
make prod
```

| Mode | UI | API | Hot Reload |
|------|-----|-----|------------|
| `make dev` | http://localhost:5173 | http://localhost:8000 | Yes |
| `make prod` | http://localhost:3000 | http://localhost:8000 | No |

### Available Commands

```bash
make dev          # Start dev environment with hot reload
make dev-build    # Rebuild and start dev environment
make prod         # Start production environment
make prod-build   # Rebuild and start production
make down         # Stop all services
make clean        # Stop and remove volumes
make logs         # View logs
make db           # Start only PostgreSQL
make test         # Run tests
make lint         # Run linter and formatter
make key          # Generate encryption key
```

### Local Development (without Docker)

**Backend:**
```bash
# Install dependencies
uv sync

# Start PostgreSQL
docker compose up -d db

# Run migrations
alembic upgrade head

# Start the API server (includes scheduler)
uv run python -m bizon_platform_lite

# In a separate terminal, start the worker
uv run python -m bizon_platform_lite.worker
```

**Frontend (UI):**
```bash
cd ui
npm install
npm run dev     # Start dev server at http://localhost:5173
```

## Testing

```bash
# Install dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest tests/api/test_pipelines.py -v

# Run with coverage
uv run pytest --cov=bizon_platform_lite --cov-report=html
```

### Test Structure

```
tests/
├── conftest.py              # Fixtures (client, database setup)
├── helpers.py               # Test helper functions
├── fixtures/
│   └── configs.py           # Test configurations
├── api/
│   ├── test_health.py       # Health check tests
│   ├── test_pipelines.py    # Pipeline CRUD tests
│   └── test_saved_connectors.py  # Saved connector tests
└── unit/
    └── test_validators.py   # Security validator tests
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://bizon:bizon@localhost:5432/bizon_platform_lite` | PostgreSQL connection URL |
| `ENCRYPTION_KEY` | (required) | Fernet key for encrypting configs |
| `STORAGE_LOCAL_PATH` | `/tmp/bizon-outputs` | Path for pipeline output files |
| `CUSTOM_SOURCES_DIR` | `./custom-sources` | Directory for custom source files |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | Allowed CORS origins |

Generate encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## API Reference

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |

### Pipelines
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/pipelines` | List pipelines |
| POST | `/api/pipelines` | Create pipeline |
| GET | `/api/pipelines/{id}` | Get pipeline |
| PUT | `/api/pipelines/{id}` | Update pipeline |
| DELETE | `/api/pipelines/{id}` | Delete pipeline |
| POST | `/api/pipelines/{id}/run` | Trigger run |
| POST | `/api/pipelines/{id}/duplicate` | Duplicate pipeline |
| GET | `/api/pipelines/{id}/runs` | List runs |

### Pipeline Runs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/pipelines/runs/{id}` | Get run status |
| GET | `/api/pipelines/runs/{id}/logs` | Get run logs |
| POST | `/api/pipelines/runs/{id}/cancel` | Cancel run |

### Connectors
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/connectors/sources` | List source connectors |
| GET | `/api/connectors/destinations` | List destination connectors |

### Saved Connectors
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/saved/sources` | List saved sources |
| POST | `/api/saved/sources` | Create saved source |
| GET | `/api/saved/sources/{id}` | Get saved source |
| PUT | `/api/saved/sources/{id}` | Update saved source |
| DELETE | `/api/saved/sources/{id}` | Delete saved source |
| GET | `/api/saved/destinations` | List saved destinations |
| POST | `/api/saved/destinations` | Create saved destination |
| GET | `/api/saved/destinations/{id}` | Get saved destination |
| PUT | `/api/saved/destinations/{id}` | Update saved destination |
| DELETE | `/api/saved/destinations/{id}` | Delete saved destination |

## Custom Sources

Custom sources let you create your own data connectors by writing Python code.

### Quick Start

1. Create a folder in `custom-sources/` (e.g., `my_api/`)
2. Create `source.py` with a class extending `AbstractSource`
3. Reference it in your pipeline with `source_file_path`

### Example Pipeline Config

```json
{
  "name": "custom source to bigquery",
  "source": {
    "source_file_path": "/custom-sources/jsonplaceholder/source.py",
    "name": "jsonplaceholder",
    "stream": "posts"
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "my-project",
      "dataset": "raw_data"
    }
  }
}
```

### Tutorial

See `custom-sources/jsonplaceholder/source.py` for a complete working example.

Full documentation: `custom-sources/README.md`

## Example Pipeline Config

### Minimal Config
```json
{
  "name": "dummy to logger",
  "source": {
    "name": "dummy",
    "stream": "creatures",
    "authentication": {
      "type": "api_key",
      "params": { "token": "dummy_key" }
    }
  },
  "destination": {
    "name": "logger",
    "config": { "dummy": "dummy" }
  }
}
```

### With Transforms
```json
{
  "name": "hubspot to bigquery",
  "source": {
    "name": "hubspot",
    "stream": "contacts",
    "authentication": {
      "type": "api_key",
      "params": { "token": "pat-xxx" }
    }
  },
  "destination": {
    "name": "bigquery",
    "config": {
      "project_id": "my-project",
      "dataset": "raw_data"
    }
  },
  "transforms": [
    {
      "label": "normalize_email",
      "python": "record['email'] = record.get('email', '').lower(); return record"
    }
  ]
}
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  React UI   │────▶│   FastAPI   │────▶│  PostgreSQL │
│             │     │     API     │     │             │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                   │
                    ┌──────┴──────┐            │
                    │             │            │
                    ▼             ▼            │
             ┌─────────────┐  ┌─────────────┐  │
             │  Scheduler  │  │   Worker    │──┘
             │ (APScheduler)│  │(subprocess) │
             └─────────────┘  └─────────────┘
```

## Project Structure

```
bizon-platform-lite/
├── bizon_platform_lite/
│   ├── api/
│   │   ├── app.py           # FastAPI app
│   │   ├── schemas.py       # Pydantic models
│   │   ├── validators.py    # Security validators
│   │   └── routes/          # API route handlers
│   ├── db/
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── session.py       # Database session
│   │   ├── types.py         # Custom types (EncryptedJSON)
│   │   └── migrations/      # Alembic migrations
│   ├── worker/              # Background job execution
│   ├── scheduler/           # Cron scheduling
│   ├── storage/             # File storage
│   ├── crypto.py            # Config encryption
│   └── settings.py          # Configuration
├── ui/                      # React frontend
├── tests/                   # Test suite
├── custom-sources/          # Custom Python sources
├── docker-compose.yml       # Dev + prod profiles
├── Dockerfile               # Multi-stage build
├── Makefile                 # Build commands
└── pyproject.toml
```

## Database Schema

Three tables:

- **pipelines** - Pipeline definitions with encrypted config
- **pipeline_runs** - Run history and status
- **saved_connectors** - Reusable connector configurations

## Development

### Pre-commit Hooks

Install pre-commit hooks for automatic linting and formatting:

```bash
# Install pre-commit
uv add --dev pre-commit

# Install hooks
uv run pre-commit install

# Run on all files (optional)
uv run pre-commit run --all-files
```

The pre-commit config uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting.

### Manual Commands

```bash
# Lint and fix
uv run ruff check bizon_platform_lite tests --fix

# Format
uv run ruff format bizon_platform_lite tests

# Type checking
uv run mypy bizon_platform_lite
```

## License

MIT
