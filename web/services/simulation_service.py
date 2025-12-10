"""
Simulation service for PROSIM web interface.

Wraps the prosim.engine.Simulation class for web use,
providing a clean interface for processing weeks.
"""

from typing import Optional

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.engine.simulation import Simulation, SimulationWeekResult
from prosim.engine.validation import ValidationResult, validate_decisions
from prosim.models.company import Company
from prosim.models.decisions import Decisions


class SimulationService:
    """Service for running PROSIM simulation.

    Wraps the core Simulation class with caching and
    web-friendly interfaces.
    """

    def __init__(self, config: Optional[ProsimConfig] = None):
        """Initialize the simulation service.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or get_default_config()
        self._simulations: dict[str, Simulation] = {}

    def get_simulation(
        self,
        game_id: str,
        random_seed: Optional[int] = None,
    ) -> Simulation:
        """Get or create a Simulation instance for a game.

        Simulations are cached by game_id to maintain state
        (primarily for the random number generator).

        Args:
            game_id: Unique game identifier.
            random_seed: Optional seed for reproducibility.

        Returns:
            Simulation instance for the game.
        """
        if game_id not in self._simulations:
            self._simulations[game_id] = Simulation(
                config=self.config,
                random_seed=random_seed,
            )
        return self._simulations[game_id]

    def clear_simulation(self, game_id: str) -> None:
        """Clear cached simulation for a game.

        Call this when a game is deleted or reset.
        """
        self._simulations.pop(game_id, None)

    def validate_decisions(
        self,
        decisions: Decisions,
        company: Company,
    ) -> ValidationResult:
        """Validate decisions against current company state.

        Args:
            decisions: The decisions to validate.
            company: Current company state.

        Returns:
            ValidationResult with any errors/warnings.
        """
        return validate_decisions(decisions, company)

    def process_week(
        self,
        game_id: str,
        company: Company,
        decisions: Decisions,
        random_seed: Optional[int] = None,
    ) -> SimulationWeekResult:
        """Process a week of simulation.

        Args:
            game_id: Unique game identifier.
            company: Current company state.
            decisions: Decisions for this week.
            random_seed: Optional seed for reproducibility.

        Returns:
            SimulationWeekResult with updated state and report.
        """
        sim = self.get_simulation(game_id, random_seed)
        return sim.process_week(company, decisions)


# Global service instance (singleton pattern)
_simulation_service: Optional[SimulationService] = None


def get_simulation_service() -> SimulationService:
    """Get or create the global SimulationService instance."""
    global _simulation_service
    if _simulation_service is None:
        _simulation_service = SimulationService()
    return _simulation_service
