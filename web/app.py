"""
FastAPI application for PROSIM web interface.

This is the main entry point for the web application.
Run with: uvicorn web.app:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from web.config import get_settings
from web.database.session import init_db
from web.theme import DEFAULT_THEME, THEME_COOKIE_NAME, VALID_THEMES


class ThemeMiddleware(BaseHTTPMiddleware):
    """Read the theme cookie and store it on request.state for templates.

    Also re-sets the theme cookie on redirect responses to ensure the
    cookie persists through POST-redirect-GET flows (e.g., new game creation).
    """

    async def dispatch(self, request: Request, call_next):
        theme = request.cookies.get(THEME_COOKIE_NAME, DEFAULT_THEME)
        if theme not in VALID_THEMES:
            theme = DEFAULT_THEME
        request.state.theme = theme
        response = await call_next(request)
        # On redirects, re-set the theme cookie so it survives the redirect chain
        if 300 <= response.status_code < 400 and theme != DEFAULT_THEME:
            response.set_cookie(
                key=THEME_COOKIE_NAME,
                value=theme,
                max_age=60 * 60 * 24 * 365,  # 1 year
                httponly=False,
                samesite="lax",
                path="/",
            )
        return response


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

    # Theme middleware (reads cookie, sets request.state.theme)
    app.add_middleware(ThemeMiddleware)

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
    from web.routes.teacher import router as teacher_router
    from web.routes.theme import router as theme_router

    app.include_router(game_router)
    app.include_router(teacher_router)
    app.include_router(theme_router)

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
