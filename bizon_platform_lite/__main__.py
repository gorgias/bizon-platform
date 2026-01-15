"""Entry point for running the API server."""

import uvicorn

from bizon_platform_lite.settings import settings


def main():
    """Run the API server."""
    uvicorn.run(
        "bizon_platform_lite.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
