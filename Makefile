.PHONY: dev prod build build-dev down clean logs test lint

# Development with hot reload
dev:
	docker compose --profile dev up

dev-build:
	docker compose --profile dev up --build

# Production
prod:
	docker compose --profile prod up -d

prod-build:
	docker compose --profile prod up -d --build

# Build images only
build:
	docker compose --profile prod build

# Stop all services
down:
	docker compose --profile dev --profile prod down

# Clean everything (volumes included)
clean:
	docker compose --profile dev --profile prod down -v

# View logs
logs:
	docker compose --profile dev --profile prod logs -f

# Database only (for local development without Docker)
db:
	docker compose up -d db

# Run tests
test:
	uv run pytest -v

# Lint and format
lint:
	uv run ruff check bizon_platform_lite tests --fix
	uv run black bizon_platform_lite tests

# Generate encryption key
key:
	@python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
