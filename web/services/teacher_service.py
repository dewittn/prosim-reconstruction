"""
Teacher mode service for PROSIM web interface.

Manages:
- Auto-advance (process weeks with default/AI decisions)
- AI competitor creation and management
- Competitor week processing
"""

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from prosim.config.schema import ProsimConfig
from prosim.engine.ai_player import create_ai_player
from prosim.engine.simulation import Simulation
from prosim.models.company import Company
from prosim.models.report import WeeklyReport
from web.database.models import AICompetitor, GameSession
from web.services.game_service import get_game_service
from web.services.simulation_service import get_simulation_service

# Difficulty -> AI strategy mapping
DIFFICULTY_STRATEGIES = {
    "easy": "conservative",
    "medium": "balanced",
    "hard": "aggressive",
}


@dataclass
class CompetitorInfo:
    """Summary of an AI competitor for display."""

    competitor_id: str
    company_name: str
    strategy: str
    current_week: int
    total_costs: float
    is_active: bool


@dataclass
class AutoAdvanceResult:
    """Result from auto-advancing weeks."""

    weeks_processed: int
    reports: list[WeeklyReport]
    final_week: int
    total_costs: float


class TeacherService:
    """Service for teacher mode features.

    Manages auto-advance and AI competitor lifecycle.
    """

    def auto_advance(
        self,
        db: Session,
        db_game: GameSession,
        num_weeks: int = 1,
        strategy: str = "balanced",
    ) -> AutoAdvanceResult:
        """Process N weeks using AI-generated decisions.

        Args:
            db: Database session.
            db_game: Game session to advance.
            num_weeks: Number of weeks to process.
            strategy: AI strategy for generating decisions.

        Returns:
            AutoAdvanceResult with processed reports.
        """
        game_service = get_game_service()
        sim_service = get_simulation_service()

        game_state = game_service.get_game_state(db_game)
        company = game_state.get_company(1)
        config = game_service.get_config(db_game)

        reports: list[WeeklyReport] = []
        weeks_done = 0

        for _ in range(num_weeks):
            if not game_state.is_active or company.current_week > db_game.max_weeks:
                break

            # Generate AI decisions for the player's company
            ai = create_ai_player(strategy, company, config)
            decisions = ai.generate_decisions(company.current_week)

            # Process the week
            result = sim_service.process_week(
                game_id=db_game.game_id,
                company=company,
                decisions=decisions,
                random_seed=db_game.random_seed,
            )

            # Save decision record
            game_service.save_decision(
                db=db,
                db_game=db_game,
                decisions_json=decisions.model_dump_json(),
                week=company.current_week,
                report=result.weekly_report,
            )

            # Update game state
            company = result.updated_company
            game_state = game_state.update_company(company)
            if company.current_week > db_game.max_weeks:
                game_state = game_state.model_copy(
                    update={"current_week": company.current_week, "is_active": False}
                )
            else:
                game_state = game_state.model_copy(
                    update={"current_week": company.current_week}
                )

            reports.append(result.weekly_report)
            weeks_done += 1

        # Persist final state
        game_service.save_game_state(db, db_game, game_state)

        # Also process competitors for these weeks
        self._process_competitors_for_weeks(db, db_game, weeks_done, config)

        return AutoAdvanceResult(
            weeks_processed=weeks_done,
            reports=reports,
            final_week=company.current_week,
            total_costs=company.total_costs,
        )

    def create_ai_competitor(
        self,
        db: Session,
        db_game: GameSession,
        strategy: str,
        company_name: str,
    ) -> str:
        """Create an AI competitor linked to the player's game.

        Args:
            db: Database session.
            db_game: Parent game session.
            strategy: AI strategy name.
            company_name: Display name for the competitor.

        Returns:
            competitor_id for the new competitor.
        """
        competitor_id = str(uuid4())[:12]

        # Create a fresh Company for the competitor
        company = Company.create_new(
            company_id=100
            + db.query(AICompetitor)
            .filter(AICompetitor.game_session_id == db_game.id)
            .count(),
            name=company_name,
        )

        db_competitor = AICompetitor(
            competitor_id=competitor_id,
            game_session_id=db_game.id,
            company_name=company_name,
            strategy=strategy,
            company_state_json=company.model_dump_json(),
            current_week=1,
            total_costs=0.0,
        )

        db.add(db_competitor)
        db.commit()
        db.refresh(db_competitor)

        # Advance the competitor to match the player's current week
        self._catch_up_competitor(db, db_game, db_competitor)

        return competitor_id

    def get_competitors(
        self,
        db: Session,
        db_game: GameSession,
    ) -> list[CompetitorInfo]:
        """Get all AI competitors for a game.

        Args:
            db: Database session.
            db_game: Parent game session.

        Returns:
            List of CompetitorInfo summaries.
        """
        competitors = (
            db.query(AICompetitor)
            .filter(AICompetitor.game_session_id == db_game.id)
            .order_by(AICompetitor.created_at)
            .all()
        )

        return [
            CompetitorInfo(
                competitor_id=c.competitor_id,
                company_name=c.company_name,
                strategy=c.strategy,
                current_week=c.current_week,
                total_costs=c.total_costs,
                is_active=c.is_active,
            )
            for c in competitors
        ]

    def delete_competitor(
        self,
        db: Session,
        db_game: GameSession,
        competitor_id: str,
    ) -> bool:
        """Delete an AI competitor.

        Returns True if deleted, False if not found.
        """
        competitor = (
            db.query(AICompetitor)
            .filter(
                AICompetitor.game_session_id == db_game.id,
                AICompetitor.competitor_id == competitor_id,
            )
            .first()
        )
        if not competitor:
            return False

        db.delete(competitor)
        db.commit()
        return True

    def process_competitors_week(
        self,
        db: Session,
        db_game: GameSession,
        target_week: int,
    ) -> None:
        """Process the current week for all AI competitors.

        Advances all competitors to match target_week.

        Args:
            db: Database session.
            db_game: Parent game session.
            target_week: Week to advance to.
        """
        config = get_game_service().get_config(db_game)
        competitors = (
            db.query(AICompetitor)
            .filter(
                AICompetitor.game_session_id == db_game.id,
                AICompetitor.is_active.is_(True),
            )
            .all()
        )

        for competitor in competitors:
            self._advance_competitor_to(db, competitor, target_week, config)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _catch_up_competitor(
        self,
        db: Session,
        db_game: GameSession,
        db_competitor: "AICompetitor",
    ) -> None:
        """Advance a new competitor to match the player's current week."""
        config = get_game_service().get_config(db_game)
        target_week = db_game.current_week
        self._advance_competitor_to(db, db_competitor, target_week, config)

    def _advance_competitor_to(
        self,
        db: Session,
        db_competitor: "AICompetitor",
        target_week: int,
        config: ProsimConfig,
    ) -> None:
        """Advance a competitor to a target week."""
        company = Company.model_validate_json(db_competitor.company_state_json)
        sim = Simulation(config=config)

        while company.current_week < target_week:
            if company.current_week > 16:  # Safety limit
                break

            ai = create_ai_player(db_competitor.strategy, company, config)
            decisions = ai.generate_decisions(company.current_week)

            result = sim.process_week(company, decisions)
            company = result.updated_company

        # Save updated state
        db_competitor.company_state_json = company.model_dump_json()
        db_competitor.current_week = company.current_week
        db_competitor.total_costs = company.total_costs
        if company.current_week > 16:
            db_competitor.is_active = False

        db.commit()

    def _process_competitors_for_weeks(
        self,
        db: Session,
        db_game: GameSession,
        num_weeks: int,
        config: ProsimConfig,
    ) -> None:
        """Process all competitors for the given number of weeks."""
        target_week = db_game.current_week
        competitors = (
            db.query(AICompetitor)
            .filter(
                AICompetitor.game_session_id == db_game.id,
                AICompetitor.is_active.is_(True),
            )
            .all()
        )

        for competitor in competitors:
            self._advance_competitor_to(db, competitor, target_week, config)


# Global service instance
_teacher_service: TeacherService | None = None


def get_teacher_service() -> TeacherService:
    """Get or create the global TeacherService instance."""
    global _teacher_service
    if _teacher_service is None:
        _teacher_service = TeacherService()
    return _teacher_service
