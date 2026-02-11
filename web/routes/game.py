"""
Game management routes for PROSIM web interface.

Handles game creation, listing, viewing, deletion,
decision entry, and week processing.
"""

import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from prosim.models.decisions import Decisions, MachineDecision, PartOrders
from web.database.models import GameSession
from web.database.session import get_db
from web.dependencies import (
    get_templates,
    set_session_cookie,
)
from web.services.game_service import get_game_service
from web.services.simulation_service import get_simulation_service

logger = logging.getLogger(__name__)

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
    max_weeks: int = Form(default=16),
    random_seed: int | None = Form(default=None),
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
    db_game = db.query(GameSession).filter(GameSession.session_id == session_id).first()

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

    db_game = db.query(GameSession).filter(GameSession.session_id == session_id).first()

    if db_game:
        game_service.delete_game(db, db_game)

    # For HTMX, return empty response to remove element
    return HTMLResponse(content="", status_code=200)


@router.get("/game/{session_id}/reports/{week}", response_class=HTMLResponse)
async def view_report(
    request: Request,
    session_id: str,
    week: int,
    db: Session = Depends(get_db),
):
    """View a weekly report in authentic PROSIM format.

    Uses the original report format verified against week1.txt and report.doc
    from the 2004 course materials. This is exactly what students saw.
    """
    import io

    from prosim.io.rept_parser import write_rept_human_readable

    templates = get_templates(request)
    game_service = get_game_service()

    # Get game from database
    db_game = db.query(GameSession).filter(GameSession.session_id == session_id).first()

    if not db_game:
        return templates.TemplateResponse(
            "pages/not_found.html",
            {"request": request, "message": "Game not found"},
            status_code=404,
        )

    # Get the full game state and find the report
    game_state = game_service.get_game_state(db_game)
    company = game_state.get_company(1)

    report = company.get_report(week)
    if not report:
        return templates.TemplateResponse(
            "pages/not_found.html",
            {"request": request, "message": f"Report for week {week} not found"},
            status_code=404,
        )

    # Generate authentic PROSIM report format
    output = io.StringIO()
    write_rept_human_readable(report, output)
    report_text = output.getvalue()

    return templates.TemplateResponse(
        "pages/report.html",
        {
            "request": request,
            "game": db_game,
            "week": week,
            "report_text": report_text,
        },
    )


@router.get("/game/{session_id}/decisions", response_class=HTMLResponse)
async def decisions_form(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    """Show the decision entry form for the current week."""
    templates = get_templates(request)
    game_service = get_game_service()

    db_game = db.query(GameSession).filter(GameSession.session_id == session_id).first()

    if not db_game:
        return templates.TemplateResponse(
            "pages/not_found.html",
            {"request": request, "message": "Game not found"},
            status_code=404,
        )

    if not db_game.is_active or db_game.is_complete:
        return RedirectResponse(
            url=f"/game/{session_id}",
            status_code=303,
        )

    game_state = game_service.get_game_state(db_game)
    company = game_state.get_company(1)

    # Try to get previous week's decisions for pre-fill
    prev_decisions = None
    history = game_service.get_decisions_history(db, db_game)
    if history:
        last = history[-1]
        if last.decisions_json:
            try:
                prev_decisions = Decisions.model_validate_json(last.decisions_json)
            except Exception:
                pass

    return templates.TemplateResponse(
        "pages/decisions.html",
        {
            "request": request,
            "game": db_game,
            "company": company,
            "week": company.current_week,
            "prev": prev_decisions,
            "errors": [],
            "warnings": [],
        },
    )


@router.post("/game/{session_id}/decisions")
async def submit_decisions(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
):
    """Process submitted decisions and advance the game one week."""
    templates = get_templates(request)
    game_service = get_game_service()
    simulation_service = get_simulation_service()

    db_game = db.query(GameSession).filter(GameSession.session_id == session_id).first()

    if not db_game:
        return templates.TemplateResponse(
            "pages/not_found.html",
            {"request": request, "message": "Game not found"},
            status_code=404,
        )

    if not db_game.is_active or db_game.is_complete:
        return RedirectResponse(
            url=f"/game/{session_id}",
            status_code=303,
        )

    game_state = game_service.get_game_state(db_game)
    company = game_state.get_company(1)
    week = company.current_week

    # Parse form data
    form = await request.form()

    try:
        quality_budget = float(form.get("quality_budget", 0))
        maintenance_budget = float(form.get("maintenance_budget", 0))
        raw_materials_regular = float(form.get("raw_materials_regular", 0))
        raw_materials_expedited = float(form.get("raw_materials_expedited", 0))
        part_orders_x = float(form.get("part_orders_x", 0))
        part_orders_y = float(form.get("part_orders_y", 0))
        part_orders_z = float(form.get("part_orders_z", 0))

        machine_decisions = []
        for machine_id in range(1, 10):
            send_for_training = form.get(f"m{machine_id}_training") == "1"
            part_type = int(form.get(f"m{machine_id}_part_type", 1))
            scheduled_hours = float(form.get(f"m{machine_id}_hours", 0))

            # If sending for training, zero out hours
            if send_for_training:
                scheduled_hours = 0.0

            machine_decisions.append(
                MachineDecision(
                    machine_id=machine_id,
                    send_for_training=send_for_training,
                    part_type=part_type,
                    scheduled_hours=scheduled_hours,
                )
            )

        decisions = Decisions(
            week=week,
            company_id=company.company_id,
            quality_budget=quality_budget,
            maintenance_budget=maintenance_budget,
            raw_materials_regular=raw_materials_regular,
            raw_materials_expedited=raw_materials_expedited,
            part_orders=PartOrders(
                x_prime=part_orders_x,
                y_prime=part_orders_y,
                z_prime=part_orders_z,
            ),
            machine_decisions=machine_decisions,
        )
    except (ValueError, TypeError) as e:
        logger.warning("Failed to parse decision form data: %s", e)
        return templates.TemplateResponse(
            "pages/decisions.html",
            {
                "request": request,
                "game": db_game,
                "company": company,
                "week": week,
                "prev": None,
                "errors": [
                    {
                        "field": "form",
                        "message": f"Invalid input: {e}",
                        "suggestion": None,
                    }
                ],
                "warnings": [],
            },
            status_code=422,
        )

    # Validate decisions
    validation = simulation_service.validate_decisions(decisions, company)

    if not validation.valid:
        return templates.TemplateResponse(
            "pages/decisions.html",
            {
                "request": request,
                "game": db_game,
                "company": company,
                "week": week,
                "prev": decisions,
                "errors": validation.errors,
                "warnings": validation.warnings,
            },
            status_code=422,
        )

    # Process the week
    try:
        result = simulation_service.process_week(
            game_id=db_game.game_id,
            company=company,
            decisions=decisions,
            random_seed=db_game.random_seed,
        )
    except Exception as e:
        logger.error(
            "Simulation error for game %s week %d: %s", db_game.game_id, week, e
        )
        return templates.TemplateResponse(
            "pages/decisions.html",
            {
                "request": request,
                "game": db_game,
                "company": company,
                "week": week,
                "prev": decisions,
                "errors": [
                    {
                        "field": "simulation",
                        "message": f"Simulation error: {e}",
                        "suggestion": None,
                    }
                ],
                "warnings": [],
            },
            status_code=500,
        )

    # Update game state with the result
    updated_game_state = game_state.update_company(result.updated_company)
    updated_game_state = updated_game_state.model_copy(
        update={"current_week": result.updated_company.current_week}
    )

    # Check if game is complete
    if updated_game_state.current_week > db_game.max_weeks:
        updated_game_state = updated_game_state.model_copy(update={"is_active": False})

    # Save decision record and updated game state
    game_service.save_decision(
        db=db,
        db_game=db_game,
        decisions_json=decisions.model_dump_json(),
        week=week,
        report=result.weekly_report,
    )
    game_service.save_game_state(db, db_game, updated_game_state)

    # Redirect to report view for the processed week
    return RedirectResponse(
        url=f"/game/{session_id}/reports/{week}",
        status_code=303,
    )


@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """Game help and documentation page."""
    templates = get_templates(request)

    return templates.TemplateResponse(
        "pages/help.html",
        {"request": request},
    )
