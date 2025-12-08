"""
Company model for PROSIM simulation.

The Company is the top-level container that holds all state
for a single simulated manufacturing company.
"""

from typing import Optional

from pydantic import BaseModel, Field

from prosim.models.inventory import Inventory
from prosim.models.machines import MachineFloor
from prosim.models.operators import Workforce
from prosim.models.orders import DemandSchedule, OrderBook
from prosim.models.report import WeeklyReport


class CompanyConfig(BaseModel):
    """Configuration for a company.

    These parameters can be customized for different game scenarios.
    """

    num_parts_machines: int = Field(default=4, ge=1, description="Number of Parts Department machines")
    num_assembly_machines: int = Field(default=5, ge=1, description="Number of Assembly Department machines")
    num_operators: int = Field(default=9, ge=1, description="Number of initial operators")
    num_trained_operators: int = Field(default=0, ge=0, description="Number of operators that start trained")
    initial_raw_materials: float = Field(default=0.0, ge=0, description="Starting raw materials inventory")
    shipping_frequency: int = Field(default=4, ge=1, description="Weeks between shipping periods")


class Company(BaseModel):
    """Complete state for a single company in the simulation.

    This is the main container that aggregates all component models.
    """

    company_id: int = Field(ge=1, description="Unique company identifier")
    name: str = Field(default="", description="Company name (optional)")
    current_week: int = Field(default=1, ge=1, description="Current simulation week")

    # Component models
    inventory: Inventory = Field(default_factory=Inventory)
    machines: MachineFloor = Field(default_factory=MachineFloor.create_default)
    workforce: Workforce = Field(default_factory=lambda: Workforce.create_initial(9, 0))
    orders: OrderBook = Field(default_factory=OrderBook)
    demand: DemandSchedule = Field(default_factory=DemandSchedule)

    # Historical data
    reports: list[WeeklyReport] = Field(
        default_factory=list,
        description="Historical weekly reports"
    )

    # Cumulative tracking
    total_costs: float = Field(default=0.0, ge=0, description="Cumulative total costs")
    total_revenue: float = Field(default=0.0, ge=0, description="Cumulative revenue")
    total_units_shipped: dict[str, float] = Field(
        default_factory=lambda: {"X": 0.0, "Y": 0.0, "Z": 0.0},
        description="Cumulative units shipped by product"
    )

    @property
    def latest_report(self) -> Optional[WeeklyReport]:
        """Get the most recent weekly report."""
        if not self.reports:
            return None
        return self.reports[-1]

    @property
    def profit(self) -> float:
        """Calculate cumulative profit (revenue - costs)."""
        return self.total_revenue - self.total_costs

    def get_report(self, week: int) -> Optional[WeeklyReport]:
        """Get report for a specific week."""
        for report in self.reports:
            if report.week == week:
                return report
        return None

    def add_report(self, report: WeeklyReport) -> "Company":
        """Add a weekly report to history."""
        new_reports = self.reports + [report]
        return self.model_copy(update={"reports": new_reports})

    def advance_week(self) -> "Company":
        """Advance to the next week.

        Prepares state for the next simulation week.
        """
        return self.model_copy(
            update={
                "current_week": self.current_week + 1,
                "inventory": self.inventory.advance_week(),
                "machines": self.machines.advance_week(),
            }
        )

    @classmethod
    def create_new(
        cls,
        company_id: int,
        name: str = "",
        config: Optional[CompanyConfig] = None,
    ) -> "Company":
        """Create a new company with initial state.

        Args:
            company_id: Unique identifier for this company
            name: Optional company name
            config: Configuration parameters (uses defaults if None)

        Returns:
            New Company instance ready for simulation
        """
        if config is None:
            config = CompanyConfig()

        # Create component models
        machines = MachineFloor.create_default(
            num_parts_machines=config.num_parts_machines,
            num_assembly_machines=config.num_assembly_machines,
        )
        workforce = Workforce.create_initial(
            num_operators=config.num_operators,
            num_trained=config.num_trained_operators,
        )
        demand = DemandSchedule(shipping_frequency=config.shipping_frequency)

        # Set up initial inventory
        inventory = Inventory()
        if config.initial_raw_materials > 0:
            inventory = inventory.model_copy(
                update={
                    "raw_materials": inventory.raw_materials.model_copy(
                        update={"beginning": config.initial_raw_materials}
                    )
                }
            )

        return cls(
            company_id=company_id,
            name=name,
            current_week=1,
            inventory=inventory,
            machines=machines,
            workforce=workforce,
            orders=OrderBook(),
            demand=demand,
            reports=[],
            total_costs=0.0,
            total_revenue=0.0,
            total_units_shipped={"X": 0.0, "Y": 0.0, "Z": 0.0},
        )


class GameState(BaseModel):
    """Complete game state for a simulation session.

    Supports single-player (one company) or multiplayer (multiple companies).
    """

    game_id: str = Field(description="Unique game identifier")
    companies: dict[int, Company] = Field(
        default_factory=dict,
        description="Map of company_id to Company"
    )
    current_week: int = Field(default=1, ge=1, description="Current game week")
    max_weeks: int = Field(default=15, ge=1, description="Maximum simulation weeks")
    is_active: bool = Field(default=True, description="Whether game is still active")
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )

    def get_company(self, company_id: int) -> Optional[Company]:
        """Get company by ID."""
        return self.companies.get(company_id)

    def add_company(self, company: Company) -> "GameState":
        """Add a company to the game."""
        new_companies = {**self.companies, company.company_id: company}
        return self.model_copy(update={"companies": new_companies})

    def update_company(self, company: Company) -> "GameState":
        """Update a company in the game."""
        return self.add_company(company)

    @property
    def is_complete(self) -> bool:
        """Check if game has reached max weeks."""
        return self.current_week > self.max_weeks

    def advance_week(self) -> "GameState":
        """Advance all companies to the next week."""
        new_companies = {
            cid: c.advance_week() for cid, c in self.companies.items()
        }
        new_week = self.current_week + 1
        is_active = new_week <= self.max_weeks
        return self.model_copy(
            update={
                "companies": new_companies,
                "current_week": new_week,
                "is_active": is_active,
            }
        )

    @classmethod
    def create_single_player(
        cls,
        game_id: str,
        company_name: str = "",
        config: Optional[CompanyConfig] = None,
        max_weeks: int = 15,
        random_seed: Optional[int] = None,
    ) -> "GameState":
        """Create a new single-player game.

        Args:
            game_id: Unique game identifier
            company_name: Name for the player's company
            config: Company configuration
            max_weeks: Maximum simulation weeks
            random_seed: Random seed for reproducibility

        Returns:
            New GameState with one company
        """
        company = Company.create_new(
            company_id=1,
            name=company_name,
            config=config,
        )
        return cls(
            game_id=game_id,
            companies={1: company},
            current_week=1,
            max_weeks=max_weeks,
            is_active=True,
            random_seed=random_seed,
        )

    @classmethod
    def create_multiplayer(
        cls,
        game_id: str,
        num_companies: int,
        config: Optional[CompanyConfig] = None,
        max_weeks: int = 15,
        random_seed: Optional[int] = None,
    ) -> "GameState":
        """Create a new multiplayer game.

        Args:
            game_id: Unique game identifier
            num_companies: Number of competing companies
            config: Company configuration (same for all)
            max_weeks: Maximum simulation weeks
            random_seed: Random seed for reproducibility

        Returns:
            New GameState with multiple companies
        """
        companies = {}
        for i in range(1, num_companies + 1):
            companies[i] = Company.create_new(
                company_id=i,
                name=f"Company {i}",
                config=config,
            )
        return cls(
            game_id=game_id,
            companies=companies,
            current_week=1,
            max_weeks=max_weeks,
            is_active=True,
            random_seed=random_seed,
        )
