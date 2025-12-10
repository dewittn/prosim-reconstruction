"""
FastAPI dependency injection helpers for PROSIM web interface.

Provides common dependencies for routes including:
- Database sessions
- Cookie-based session handling
- Template rendering
"""

from typing import Optional
from uuid import uuid4

from fastapi import Cookie, Depends, HTTPException, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from web.config import get_settings
from web.database.models import GameSession
from web.database.session import get_db

# Session cookie name
SESSION_COOKIE_NAME = "prosim_session"


def get_templates(request: Request) -> Jinja2Templates:
    """Get the Jinja2 templates instance from app state."""
    return request.app.state.templates


def get_or_create_session_id(
    prosim_session: Optional[str] = Cookie(default=None),
) -> str:
    """Get existing session ID from cookie or generate a new one.

    This is used when we want to identify a user but don't require
    an existing session (e.g., on the landing page).
    """
    if prosim_session:
        return prosim_session
    return str(uuid4())


def require_session_id(
    prosim_session: str = Cookie(...),
) -> str:
    """Require an existing session ID from cookie.

    Use this dependency when the route requires an authenticated session.
    """
    return prosim_session


def set_session_cookie(response: Response, session_id: str) -> None:
    """Set the session cookie on a response.

    Call this after creating a new session to persist it in the browser.
    """
    config = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        max_age=config.session_max_age,
        samesite="lax",
    )


async def get_game_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> GameSession:
    """Get a game session by its session_id.

    Raises 404 if not found.
    """
    game = db.query(GameSession).filter(GameSession.session_id == session_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


async def get_game_or_none(
    session_id: str,
    db: Session = Depends(get_db),
) -> Optional[GameSession]:
    """Get a game session by its session_id, or None if not found."""
    return db.query(GameSession).filter(GameSession.session_id == session_id).first()


class GameSessionDep:
    """Dependency class for getting a game session from URL path.

    Usage in routes:
        @router.get("/game/{session_id}")
        async def game_view(
            session_id: str,
            game: GameSession = Depends(GameSessionDep()),
            db: Session = Depends(get_db),
        ):
            ...
    """

    async def __call__(
        self,
        session_id: str,
        db: Session = Depends(get_db),
    ) -> GameSession:
        game = db.query(GameSession).filter(GameSession.session_id == session_id).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game
