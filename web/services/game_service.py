"""
Game service for PROSIM web interface.

Manages game state persistence between the SQLAlchemy models
and the Pydantic domain models.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.models.company import Company, GameState
from prosim.models.report import WeeklyReport
from web.database.models import GameSession, WeeklyDecision


class GameService:
    """Service for managing game state persistence.

    Handles serialization/deserialization of Pydantic models
    to/from the database.
    """

    def create_game(
        self,
        db: Session,
        company_name: str,
        max_weeks: int = 16,
        random_seed: Optional[int] = None,
        config: Optional[ProsimConfig] = None,
    ) -> GameSession:
        """Create a new game session.

        Args:
            db: Database session.
            company_name: Name for the player's company.
            max_weeks: Maximum weeks to play (default 16).
            random_seed: Optional seed for reproducibility.
            config: Optional custom game configuration.

        Returns:
            The created GameSession database record.
        """
        # Generate unique identifiers
        session_id = str(uuid4())
        game_id = str(uuid4())[:8].upper()

        # Create the game state using prosim models
        config = config or get_default_config()

        game_state = GameState.create_single_player(
            game_id=game_id,
            company_name=company_name,
            max_weeks=max_weeks,
        )

        # Create database record
        db_game = GameSession(
            session_id=session_id,
            game_id=game_id,
            company_name=company_name,
            game_state_json=game_state.model_dump_json(),
            config_json=config.model_dump_json() if config else None,
            current_week=1,
            max_weeks=max_weeks,
            random_seed=random_seed,
        )

        db.add(db_game)
        db.commit()
        db.refresh(db_game)

        return db_game

    def get_game_state(self, db_game: GameSession) -> GameState:
        """Deserialize GameState from database record.

        Args:
            db_game: Database game session record.

        Returns:
            GameState Pydantic model.
        """
        return GameState.model_validate_json(db_game.game_state_json)

    def get_company(self, db_game: GameSession, company_id: int = 1) -> Optional[Company]:
        """Get a company from a game session.

        Args:
            db_game: Database game session record.
            company_id: Company ID (default 1 for single-player).

        Returns:
            Company model or None if not found.
        """
        game_state = self.get_game_state(db_game)
        return game_state.get_company(company_id)

    def get_config(self, db_game: GameSession) -> ProsimConfig:
        """Get the game configuration.

        Args:
            db_game: Database game session record.

        Returns:
            ProsimConfig for the game.
        """
        if db_game.config_json:
            return ProsimConfig.model_validate_json(db_game.config_json)
        return get_default_config()

    def save_game_state(
        self,
        db: Session,
        db_game: GameSession,
        game_state: GameState,
    ) -> None:
        """Save updated game state to database.

        Args:
            db: Database session.
            db_game: Database game session record.
            game_state: Updated GameState to save.
        """
        db_game.game_state_json = game_state.model_dump_json()
        db_game.current_week = game_state.current_week
        db_game.is_active = game_state.is_active
        db_game.updated_at = datetime.utcnow()
        db_game.last_played = datetime.utcnow()

        # Update denormalized fields
        company = game_state.get_company(1)
        if company:
            db_game.total_costs = company.total_costs

        # Check if game is complete
        if game_state.current_week > db_game.max_weeks:
            db_game.is_complete = True
            db_game.is_active = False

        db.commit()

    def save_decision(
        self,
        db: Session,
        db_game: GameSession,
        decisions_json: str,
        week: int,
        report: Optional[WeeklyReport] = None,
    ) -> WeeklyDecision:
        """Save a decision record for audit/history.

        Args:
            db: Database session.
            db_game: Database game session record.
            decisions_json: JSON-serialized Decisions.
            week: Week number.
            report: Optional resulting report.

        Returns:
            The created WeeklyDecision record.
        """
        decision = WeeklyDecision(
            game_session_id=db_game.id,
            week=week,
            decisions_json=decisions_json,
            was_processed=report is not None,
            report_json=report.model_dump_json() if report else None,
        )

        db.add(decision)
        db.commit()
        db.refresh(decision)

        return decision

    def get_decisions_history(
        self,
        db: Session,
        db_game: GameSession,
    ) -> list[WeeklyDecision]:
        """Get all decision records for a game.

        Args:
            db: Database session.
            db_game: Database game session record.

        Returns:
            List of WeeklyDecision records, ordered by week.
        """
        return (
            db.query(WeeklyDecision)
            .filter(WeeklyDecision.game_session_id == db_game.id)
            .order_by(WeeklyDecision.week)
            .all()
        )

    def get_report(
        self,
        db: Session,
        db_game: GameSession,
        week: int,
    ) -> Optional[WeeklyReport]:
        """Get a weekly report from decision history.

        Args:
            db: Database session.
            db_game: Database game session record.
            week: Week number.

        Returns:
            WeeklyReport if found, None otherwise.
        """
        decision = (
            db.query(WeeklyDecision)
            .filter(
                WeeklyDecision.game_session_id == db_game.id,
                WeeklyDecision.week == week,
            )
            .first()
        )

        if decision and decision.report_json:
            return WeeklyReport.model_validate_json(decision.report_json)
        return None

    def list_games(
        self,
        db: Session,
        active_only: bool = False,
    ) -> list[GameSession]:
        """List all game sessions.

        Args:
            db: Database session.
            active_only: If True, only return active games.

        Returns:
            List of GameSession records.
        """
        query = db.query(GameSession)
        if active_only:
            query = query.filter(GameSession.is_active == True)
        return query.order_by(GameSession.last_played.desc()).all()

    def delete_game(self, db: Session, db_game: GameSession) -> None:
        """Delete a game and its decision history.

        Args:
            db: Database session.
            db_game: Database game session record.
        """
        # Delete decision history
        db.query(WeeklyDecision).filter(
            WeeklyDecision.game_session_id == db_game.id
        ).delete()

        # Delete game
        db.delete(db_game)
        db.commit()


# Global service instance (singleton pattern)
_game_service: Optional[GameService] = None


def get_game_service() -> GameService:
    """Get or create the global GameService instance."""
    global _game_service
    if _game_service is None:
        _game_service = GameService()
    return _game_service
