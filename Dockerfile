# =============================================================================
# UI Build Stage
# =============================================================================
FROM node:22-alpine AS ui-build

WORKDIR /app

COPY ui/package.json ui/package-lock.json* ./
RUN npm install

COPY ui/ .
RUN npm run build

# =============================================================================
# UI Production Stage (nginx)
# =============================================================================
FROM nginx:alpine AS ui

COPY --from=ui-build /app/dist /usr/share/nginx/html
COPY ui/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# =============================================================================
# Backend Stage (API + Worker)
# =============================================================================
FROM python:3.12-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml README.md ./
COPY bizon_platform_lite ./bizon_platform_lite
COPY alembic.ini ./

# Install dependencies
RUN uv pip install --system -e .

# Create directories
RUN mkdir -p /tmp/bizon-outputs /custom_sources

# Default command runs the API
CMD ["python", "-m", "bizon_platform_lite"]
