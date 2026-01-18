#!/bin/bash
set -e

echo "Setting up Bizon Platform Lite development environment..."

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Setup environment file
cp .env.example .env
echo "ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env

# Install Python dependencies
uv sync

# Install frontend dependencies
cd ui && npm install && cd ..

# Start PostgreSQL in Docker
docker run --name bizon-db -d \
  -e POSTGRES_USER=bizon \
  -e POSTGRES_PASSWORD=bizon \
  -e POSTGRES_DB=bizon_platform_lite \
  -p 5432:5432 \
  postgres:16-alpine

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5
until docker exec bizon-db pg_isready -U bizon -d bizon_platform_lite; do
  sleep 1
done

# Run migrations and seed data
uv run alembic upgrade head
uv run python -m bizon_platform_lite.seed

echo ""
echo "Setup complete! To start the development servers:"
echo ""
echo "  Terminal 1 (Backend):  uv run python -m bizon_platform_lite"
echo "  Terminal 2 (Worker):   uv run python -m bizon_platform_lite.worker"
echo "  Terminal 3 (Frontend): cd ui && npm run dev"
echo ""
