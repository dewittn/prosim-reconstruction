"""
Teacher mode routes for PROSIM web interface.

Handles auto-advance, AI competitor management, and comparison views.
All routes use HTMX for dynamic updates.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from web.database.models import GameSession
from web.database.session import get_db
from web.dependencies import get_templates
from web.services.teacher_service import (
    DIFFICULTY_STRATEGIES,
    get_teacher_service,
)

router = APIRouter(prefix="/game/{session_id}/teacher", tags=["teacher"])


def _get_game(session_id: str, db: Session) -> GameSession | None:
    """Look up a game session by session_id."""
    return db.query(GameSession).filter(GameSession.session_id == session_id).first()


@router.get("", response_class=HTMLResponse)
async def teacher_panel(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    """Render the teacher mode panel page."""
    templates = get_templates(request)
    db_game = _get_game(session_id, db)

    if not db_game:
        return templates.TemplateResponse(
            "pages/not_found.html",
            {"request": request, "message": "Game not found"},
            status_code=404,
        )

    teacher_service = get_teacher_service()
    competitors = teacher_service.get_competitors(db, db_game)

    return templates.TemplateResponse(
        "pages/teacher.html",
        {
            "request": request,
            "game": db_game,
            "competitors": competitors,
            "strategies": list(DIFFICULTY_STRATEGIES.keys()),
        },
    )


@router.post("/auto-advance", response_class=HTMLResponse)
async def auto_advance(
    request: Request,
    session_id: str,
    num_weeks: int = Form(default=1),
    strategy: str = Form(default="balanced"),
    db: Session = Depends(get_db),
):
    """Auto-process N weeks using AI decisions. Returns HTMX fragment."""
    templates = get_templates(request)
    db_game = _get_game(session_id, db)

    if not db_game:
        return HTMLResponse("<p>Game not found</p>", status_code=404)

    if not db_game.is_active:
        return HTMLResponse("<p>Game is complete.</p>")

    # Validate strategy against known values
    allowed_strategies = {"conservative", "balanced", "aggressive"}
    if strategy not in allowed_strategies:
        strategy = "balanced"

    teacher_service = get_teacher_service()

    # Clamp weeks
    num_weeks = max(1, min(num_weeks, db_game.max_weeks - db_game.current_week + 1))

    result = teacher_service.auto_advance(
        db=db,
        db_game=db_game,
        num_weeks=num_weeks,
        strategy=strategy,
    )

    # Re-fetch competitors for the updated comparison
    competitors = teacher_service.get_competitors(db, db_game)

    # Refresh db_game after save
    db.refresh(db_game)

    return templates.TemplateResponse(
        "components/teacher_status.html",
        {
            "request": request,
            "game": db_game,
            "competitors": competitors,
            "advance_result": {
                "weeks_processed": result.weeks_processed,
                "final_week": result.final_week,
                "total_costs": result.total_costs,
            },
        },
    )


@router.post("/competitors", response_class=HTMLResponse)
async def add_competitor(
    request: Request,
    session_id: str,
    company_name: str = Form(...),
    difficulty: str = Form(default="medium"),
    db: Session = Depends(get_db),
):
    """Add an AI competitor. Returns HTMX fragment."""
    templates = get_templates(request)
    db_game = _get_game(session_id, db)

    if not db_game:
        return HTMLResponse("<p>Game not found</p>", status_code=404)

    # Validate difficulty against allowed values
    if difficulty not in DIFFICULTY_STRATEGIES:
        difficulty = "medium"
    strategy = DIFFICULTY_STRATEGIES[difficulty]

    teacher_service = get_teacher_service()
    teacher_service.create_ai_competitor(
        db=db,
        db_game=db_game,
        strategy=strategy,
        company_name=company_name,
    )

    # Return updated competitor list
    competitors = teacher_service.get_competitors(db, db_game)

    return templates.TemplateResponse(
        "components/competitor_list.html",
        {
            "request": request,
            "game": db_game,
            "competitors": competitors,
        },
    )


@router.get("/competitors", response_class=HTMLResponse)
async def list_competitors(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    """View competitors' status. Returns HTMX fragment."""
    templates = get_templates(request)
    db_game = _get_game(session_id, db)

    if not db_game:
        return HTMLResponse("<p>Game not found</p>", status_code=404)

    teacher_service = get_teacher_service()
    competitors = teacher_service.get_competitors(db, db_game)

    return templates.TemplateResponse(
        "components/competitor_list.html",
        {
            "request": request,
            "game": db_game,
            "competitors": competitors,
        },
    )


@router.delete("/competitors/{competitor_id}", response_class=HTMLResponse)
async def remove_competitor(
    request: Request,
    session_id: str,
    competitor_id: str,
    db: Session = Depends(get_db),
):
    """Remove an AI competitor. Returns empty for HTMX swap."""
    db_game = _get_game(session_id, db)

    if not db_game:
        return HTMLResponse("", status_code=404)

    teacher_service = get_teacher_service()
    teacher_service.delete_competitor(db, db_game, competitor_id)

    # Return updated competitor list
    templates = get_templates(request)
    competitors = teacher_service.get_competitors(db, db_game)

    return templates.TemplateResponse(
        "components/competitor_list.html",
        {
            "request": request,
            "game": db_game,
            "competitors": competitors,
        },
    )


@router.post("/competitors/process", response_class=HTMLResponse)
async def process_competitors(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    """Process the current week for all AI competitors."""
    templates = get_templates(request)
    db_game = _get_game(session_id, db)

    if not db_game:
        return HTMLResponse("<p>Game not found</p>", status_code=404)

    teacher_service = get_teacher_service()
    teacher_service.process_competitors_week(
        db=db,
        db_game=db_game,
        target_week=db_game.current_week,
    )

    competitors = teacher_service.get_competitors(db, db_game)

    return templates.TemplateResponse(
        "components/competitor_list.html",
        {
            "request": request,
            "game": db_game,
            "competitors": competitors,
        },
    )
