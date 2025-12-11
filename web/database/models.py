"""
SQLAlchemy models for PROSIM web interface.

These models store game sessions and decision history in SQLite.
The actual game state (Company, GameState) is serialized as JSON
using Pydantic's built-in serialization.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class GameSession(Base):
    """Persistent game session for web interface.

    Stores the full game state as serialized JSON, along with
    metadata for quick filtering and display.
    """

    __tablename__ = "game_sessions"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    session_id: str = Column(
        String(64), unique=True, nullable=False, index=True
    )  # Cookie-based identifier

    # Game identification
    game_id: str = Column(String(16), nullable=False)
    company_name: str = Column(String(100), default="")

    # Game state (serialized Pydantic models)
    game_state_json: str = Column(Text, nullable=False)  # JSON serialized GameState
    config_json: Optional[str] = Column(Text, nullable=True)  # JSON serialized ProsimConfig

    # Denormalized metadata for quick queries
    current_week: int = Column(Integer, default=1)
    max_weeks: int = Column(Integer, default=16)
    total_costs: float = Column(Float, default=0.0)
    is_active: bool = Column(Boolean, default=True)
    is_complete: bool = Column(Boolean, default=False)

    # Teacher mode settings
    auto_process: bool = Column(Boolean, default=False)
    auto_process_interval: Optional[int] = Column(Integer, nullable=True)  # Hours
    next_auto_process: Optional[datetime] = Column(DateTime, nullable=True)

    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_played: datetime = Column(DateTime, default=datetime.utcnow)

    # Random seed for reproducibility
    random_seed: Optional[int] = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<GameSession(id={self.id}, game_id={self.game_id}, "
            f"company={self.company_name}, week={self.current_week})>"
        )


class WeeklyDecision(Base):
    """Record of submitted decisions for audit/replay.

    Stores each week's decisions and resulting report as JSON
    for historical tracking and potential replay functionality.
    """

    __tablename__ = "weekly_decisions"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    game_session_id: int = Column(
        Integer, nullable=False, index=True
    )  # FK to game_sessions.id

    week: int = Column(Integer, nullable=False)
    decisions_json: str = Column(Text, nullable=False)  # JSON serialized Decisions

    submitted_at: datetime = Column(DateTime, default=datetime.utcnow)

    # Result tracking
    was_processed: bool = Column(Boolean, default=False)
    report_json: Optional[str] = Column(Text, nullable=True)  # JSON serialized WeeklyReport

    def __repr__(self) -> str:
        return (
            f"<WeeklyDecision(id={self.id}, game={self.game_session_id}, "
            f"week={self.week}, processed={self.was_processed})>"
        )
