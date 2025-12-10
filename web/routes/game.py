"""
Game management routes for PROSIM web interface.

Handles game creation, listing, viewing, and deletion.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from web.database.models import GameSession
from web.database.session import get_db
from web.dependencies import (
    GameSessionDep,
    get_or_create_session_id,
    get_templates,
    set_session_cookie,
)
from web.services.game_service import get_game_service

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    db: Session = Depends(get_db),
):
    """Landing page - show list of existing games."""
    templates = get_templates(request)
    game_service = get_game_service()

    games = game_service.list_games(db)

    return templates.TemplateResponse(
        "pages/index.html",
        {
            "request": request,
            "games": games,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_game_form(request: Request):
    """Show the new game creation form."""
    templates = get_templates(request)

    return templates.TemplateResponse(
        "pages/new_game.html",
        {
            "request": request,
        },
    )


@router.post("/new")
async def create_game(
    request: Request,
    company_name: str = Form(...),
    max_weeks: int = Form(default=15),
    random_seed: Optional[int] = Form(default=None),
    db: Session = Depends(get_db),
):
    """Create a new game and redirect to it."""
    game_service = get_game_service()

    # Create the game
    db_game = game_service.create_game(
        db=db,
        company_name=company_name,
        max_weeks=max_weeks,
        random_seed=random_seed,
    )

    # Redirect to the game view
    response = RedirectResponse(
        url=f"/game/{db_game.session_id}",
        status_code=303,  # See Other - for POST redirect
    )

    # Set session cookie
    set_session_cookie(response, db_game.session_id)

    return response


@router.get("/game/{session_id}", response_class=HTMLResponse)
async def game_view(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    """Main game dashboard view."""
    templates = get_templates(request)
    game_service = get_game_service()

    # Get game from database
    db_game = (
        db.query(GameSession).filter(GameSession.session_id == session_id).first()
    )

    if not db_game:
        return templates.TemplateResponse(
            "pages/not_found.html",
            {"request": request, "message": "Game not found"},
            status_code=404,
        )

    # Get the full game state
    game_state = game_service.get_game_state(db_game)
    company = game_state.get_company(1)
    config = game_service.get_config(db_game)

    # Get decision history for reports
    decisions = game_service.get_decisions_history(db, db_game)

    return templates.TemplateResponse(
        "pages/game.html",
        {
            "request": request,
            "game": db_game,
            "game_state": game_state,
            "company": company,
            "config": config,
            "decisions": decisions,
        },
    )


@router.delete("/game/{session_id}")
async def delete_game(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Delete a game session."""
    game_service = get_game_service()

    db_game = (
        db.query(GameSession).filter(GameSession.session_id == session_id).first()
    )

    if db_game:
        game_service.delete_game(db, db_game)

    # For HTMX, return empty response to remove element
    return HTMLResponse(content="", status_code=200)


@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """Game help and documentation page."""
    templates = get_templates(request)

    return templates.TemplateResponse(
        "pages/help.html",
        {"request": request},
    )
