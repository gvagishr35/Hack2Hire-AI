"""Application entry point for local development and process managers."""

import uvicorn

from app.core.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
