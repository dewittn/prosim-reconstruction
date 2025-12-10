"""
FastAPI application for PROSIM web interface.

This is the main entry point for the web application.
Run with: uvicorn web.app:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.config import get_settings
from web.database.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    init_db()
    yield
    # Shutdown (nothing to do for now)


def create_app() -> FastAPI:
    """Application factory for creating the FastAPI app."""
    config = get_settings()

    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        description="A Production Management Simulation Game (1968-2025)",
        lifespan=lifespan,
    )

    # Mount static files
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Set up templates
    templates_path = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(templates_path))

    # Store templates in app state for access in routes
    app.state.templates = templates

    # Import and include routers
    from web.routes.game import router as game_router

    app.include_router(game_router)

    return app


# Create the application instance
app = create_app()


# Template helper for routes
def get_templates(request: Request) -> Jinja2Templates:
    """Get the Jinja2 templates instance from app state."""
    return request.app.state.templates


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "app": "prosim"}
