"""
Demand generation and management for PROSIM simulation.

This module handles:
- Demand forecasting with uncertainty that decreases as shipping approaches
- Actual demand generation at shipping weeks
- Carryover/backlog tracking from unfulfilled demand
- Shipping period coordination

The demand system uses:
- Base demand per product (configurable, defaults from presentations: X=600, Y=400, Z=200)
- Forecast uncertainty based on weeks until shipping (std dev: 4w=300, 3w=300, 2w=200, 1w=100, 0w=0)
- Shipping every N weeks (default: 4 weeks = monthly)
"""

import random
from dataclasses import dataclass, field
from typing import Optional

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.models.orders import DemandForecast, DemandSchedule


@dataclass
class DemandGenerationResult:
    """Result of demand generation for a shipping period."""

    product_type: str
    base_demand: float
    variation: float
    actual_demand: float
    carryover_from_previous: float
    total_demand: float


@dataclass
class ShippingPeriodDemand:
    """Demand for all products in a shipping period."""

    shipping_week: int
    demands: dict[str, DemandGenerationResult] = field(default_factory=dict)

    @property
    def total_demand_by_product(self) -> dict[str, float]:
        """Get total demand (actual + carryover) by product type."""
        return {
            product_type: result.total_demand
            for product_type, result in self.demands.items()
        }


@dataclass
class ForecastUpdateResult:
    """Result of updating forecasts for a week."""

    week: int
    forecasts_updated: list[DemandForecast]
    new_forecasts_created: list[DemandForecast]


class DemandManager:
    """Manages demand generation, forecasting, and carryover tracking.

    The demand system follows these principles:
    1. Demand is generated for each shipping period (every N weeks)
    2. Forecasts have uncertainty that decreases as shipping approaches
    3. At shipping week, actual demand is revealed (no uncertainty)
    4. Unfulfilled demand carries over to the next shipping period
    5. Random variation is applied using configurable standard deviations
    """

    # Default base demand per product (from presentations: 600/400/200 typical starting point)
    DEFAULT_BASE_DEMAND = {"X": 600.0, "Y": 400.0, "Z": 200.0}

    def __init__(
        self,
        config: Optional[ProsimConfig] = None,
        random_seed: Optional[int] = None,
        base_demand: Optional[dict[str, float]] = None,
    ):
        """Initialize demand manager.

        Args:
            config: Simulation configuration (uses defaults if None)
            random_seed: Random seed for reproducible demand generation
            base_demand: Base demand per product type (uses defaults if None)
        """
        self.config = config or get_default_config()
        self._rng = random.Random(random_seed)
        self.base_demand = base_demand or self.DEFAULT_BASE_DEMAND.copy()

    def set_random_seed(self, seed: Optional[int]) -> None:
        """Set random seed for reproducible demand generation.

        Args:
            seed: Random seed (None for system random)
        """
        self._rng = random.Random(seed)

    def get_forecast_std_dev(self, weeks_until_shipping: int) -> float:
        """Get forecast standard deviation based on weeks until shipping.

        Args:
            weeks_until_shipping: Number of weeks until shipping period

        Returns:
            Standard deviation for forecast uncertainty
        """
        std_devs = self.config.demand.forecast_std_dev_weeks_out
        # Use configured value or default to 0 if beyond known range
        return float(std_devs.get(weeks_until_shipping, 0))

    def generate_forecast(
        self,
        product_type: str,
        shipping_week: int,
        current_week: int,
        carryover: float = 0.0,
    ) -> DemandForecast:
        """Generate a demand forecast for a product.

        The forecast includes uncertainty based on how far out the shipping week is.

        Args:
            product_type: Product type (X, Y, or Z)
            shipping_week: Week when shipping will occur
            current_week: Current simulation week
            carryover: Unfulfilled demand from previous period

        Returns:
            DemandForecast with estimated demand
        """
        base = self.base_demand.get(product_type, 0.0)
        weeks_out = shipping_week - current_week

        # Get standard deviation for this many weeks out
        std_dev = self.get_forecast_std_dev(weeks_out)

        # Generate estimated demand with uncertainty
        if std_dev > 0:
            # Use normal distribution for forecast uncertainty
            variation = self._rng.gauss(0, std_dev)
            estimated = max(0.0, base + variation)  # Demand can't be negative
        else:
            estimated = base

        return DemandForecast(
            product_type=product_type,
            shipping_week=shipping_week,
            estimated_demand=estimated,
            actual_demand=None,  # Not known until shipping week
            carryover=carryover,
        )

    def reveal_actual_demand(
        self,
        product_type: str,
        shipping_week: int,
        carryover: float = 0.0,
    ) -> DemandGenerationResult:
        """Reveal actual demand at shipping week.

        At the shipping week, uncertainty is zero - this is the true demand.

        Args:
            product_type: Product type (X, Y, or Z)
            shipping_week: Shipping week (should be current week)
            carryover: Unfulfilled demand from previous period

        Returns:
            DemandGenerationResult with actual demand
        """
        base = self.base_demand.get(product_type, 0.0)

        # At shipping week, std_dev is 0 - no uncertainty in actual demand
        # But we still apply the random variation that was "building up"
        # The actual demand IS the base demand for this implementation
        # (In a more complex model, actual could still vary from base)
        actual = base
        variation = 0.0

        total = actual + carryover

        return DemandGenerationResult(
            product_type=product_type,
            base_demand=base,
            variation=variation,
            actual_demand=actual,
            carryover_from_previous=carryover,
            total_demand=total,
        )

    def generate_shipping_period_demand(
        self,
        shipping_week: int,
        carryover: Optional[dict[str, float]] = None,
    ) -> ShippingPeriodDemand:
        """Generate demand for all products in a shipping period.

        Args:
            shipping_week: Shipping week
            carryover: Carryover by product type from previous period

        Returns:
            ShippingPeriodDemand with demand for all products
        """
        carryover = carryover or {"X": 0.0, "Y": 0.0, "Z": 0.0}
        demands = {}

        for product_type in ["X", "Y", "Z"]:
            prev_carryover = carryover.get(product_type, 0.0)
            result = self.reveal_actual_demand(
                product_type=product_type,
                shipping_week=shipping_week,
                carryover=prev_carryover,
            )
            demands[product_type] = result

        return ShippingPeriodDemand(
            shipping_week=shipping_week,
            demands=demands,
        )

    def is_shipping_week(self, week: int) -> bool:
        """Check if the given week is a shipping week.

        Args:
            week: Week number to check

        Returns:
            True if this is a shipping week
        """
        frequency = self.config.simulation.shipping_frequency
        return week % frequency == 0

    def next_shipping_week(self, current_week: int) -> int:
        """Calculate the next shipping week.

        Args:
            current_week: Current simulation week

        Returns:
            Next shipping week number
        """
        frequency = self.config.simulation.shipping_frequency
        remainder = current_week % frequency
        if remainder == 0:
            return current_week
        return current_week + (frequency - remainder)

    def initialize_demand_schedule(
        self,
        start_week: int,
        periods_ahead: int = 2,
    ) -> DemandSchedule:
        """Initialize demand schedule with forecasts for upcoming periods.

        Args:
            start_week: Starting week of simulation
            periods_ahead: How many shipping periods ahead to forecast

        Returns:
            Initialized DemandSchedule
        """
        schedule = DemandSchedule(
            shipping_frequency=self.config.simulation.shipping_frequency,
        )

        # Find the first shipping week at or after start_week
        first_shipping = self.next_shipping_week(start_week)

        # Generate forecasts for each period
        for i in range(periods_ahead):
            shipping_week = first_shipping + (i * self.config.simulation.shipping_frequency)

            for product_type in ["X", "Y", "Z"]:
                forecast = self.generate_forecast(
                    product_type=product_type,
                    shipping_week=shipping_week,
                    current_week=start_week,
                    carryover=0.0,
                )
                schedule = schedule.add_forecast(forecast)

        return schedule

    def update_forecasts_for_week(
        self,
        schedule: DemandSchedule,
        current_week: int,
    ) -> tuple[DemandSchedule, ForecastUpdateResult]:
        """Update forecasts based on current week.

        As weeks pass, forecast uncertainty decreases. This method updates
        the estimated demand for all forecasts based on the new weeks-out value.

        Args:
            schedule: Current demand schedule
            current_week: Current simulation week

        Returns:
            Tuple of (updated schedule, result with details)
        """
        updated_forecasts: list[DemandForecast] = []
        new_forecasts: list[DemandForecast] = []
        new_schedule = schedule

        # Get all forecasts for future shipping weeks
        for forecast in schedule.forecasts:
            if forecast.shipping_week >= current_week:
                weeks_out = forecast.shipping_week - current_week

                # Regenerate forecast with updated uncertainty
                new_forecast = self.generate_forecast(
                    product_type=forecast.product_type,
                    shipping_week=forecast.shipping_week,
                    current_week=current_week,
                    carryover=forecast.carryover,
                )

                # Keep actual_demand if already set
                if forecast.actual_demand is not None:
                    new_forecast = DemandForecast(
                        product_type=new_forecast.product_type,
                        shipping_week=new_forecast.shipping_week,
                        estimated_demand=new_forecast.estimated_demand,
                        actual_demand=forecast.actual_demand,
                        carryover=new_forecast.carryover,
                    )

                new_schedule = new_schedule.update_forecast(
                    product_type=forecast.product_type,
                    shipping_week=forecast.shipping_week,
                    actual_demand=new_forecast.actual_demand,
                    carryover=new_forecast.carryover,
                )
                updated_forecasts.append(new_forecast)

        result = ForecastUpdateResult(
            week=current_week,
            forecasts_updated=updated_forecasts,
            new_forecasts_created=new_forecasts,
        )

        return new_schedule, result

    def process_shipping_week(
        self,
        schedule: DemandSchedule,
        shipping_week: int,
        units_shipped: dict[str, float],
    ) -> tuple[DemandSchedule, ShippingPeriodDemand, dict[str, float]]:
        """Process a shipping week: reveal demand, calculate fulfillment, track carryover.

        Args:
            schedule: Current demand schedule
            shipping_week: The shipping week being processed
            units_shipped: Units actually shipped by product type

        Returns:
            Tuple of:
            - Updated demand schedule
            - ShippingPeriodDemand with actual demand
            - New carryover by product type
        """
        # Get forecasts for this shipping week
        forecasts = schedule.get_forecasts_for_week(shipping_week)

        # Build carryover from forecasts
        carryover = {}
        for forecast in forecasts:
            carryover[forecast.product_type] = forecast.carryover

        # Generate actual demand
        period_demand = self.generate_shipping_period_demand(
            shipping_week=shipping_week,
            carryover=carryover,
        )

        # Calculate new carryover based on what was shipped
        new_carryover = {}
        for product_type, demand_result in period_demand.demands.items():
            shipped = units_shipped.get(product_type, 0.0)
            unfulfilled = max(0.0, demand_result.total_demand - shipped)
            new_carryover[product_type] = unfulfilled

        # Update schedule with actual demand values
        updated_schedule = schedule
        for product_type, demand_result in period_demand.demands.items():
            updated_schedule = updated_schedule.update_forecast(
                product_type=product_type,
                shipping_week=shipping_week,
                actual_demand=demand_result.actual_demand,
            )

        return updated_schedule, period_demand, new_carryover

    def add_next_period_forecasts(
        self,
        schedule: DemandSchedule,
        current_week: int,
        carryover: dict[str, float],
    ) -> DemandSchedule:
        """Add forecasts for the next shipping period.

        Called after processing a shipping week to add forecasts for the
        newly visible period.

        Args:
            schedule: Current demand schedule
            current_week: Current simulation week
            carryover: Carryover from the just-completed shipping period

        Returns:
            Updated schedule with new forecasts
        """
        # Calculate the new shipping week to forecast
        frequency = self.config.simulation.shipping_frequency
        next_shipping = self.next_shipping_week(current_week)

        # Find the furthest shipping week we already have forecasts for
        max_shipping_week = 0
        for forecast in schedule.forecasts:
            if forecast.shipping_week > max_shipping_week:
                max_shipping_week = forecast.shipping_week

        # Add forecasts for the next period after max
        new_shipping_week = max_shipping_week + frequency

        updated_schedule = schedule
        for product_type in ["X", "Y", "Z"]:
            forecast = self.generate_forecast(
                product_type=product_type,
                shipping_week=new_shipping_week,
                current_week=current_week,
                carryover=carryover.get(product_type, 0.0),
            )
            updated_schedule = updated_schedule.add_forecast(forecast)

        return updated_schedule

    def calculate_demand_penalty_units(
        self,
        demand: dict[str, float],
        shipped: dict[str, float],
    ) -> dict[str, float]:
        """Calculate unfulfilled demand units for penalty calculation.

        Args:
            demand: Total demand by product type
            shipped: Units shipped by product type

        Returns:
            Unfulfilled units by product type (for penalty calculation)
        """
        shortage = {}
        for product_type in ["X", "Y", "Z"]:
            total_demand = demand.get(product_type, 0.0)
            units_shipped = shipped.get(product_type, 0.0)
            shortage[product_type] = max(0.0, total_demand - units_shipped)
        return shortage

    def get_demand_for_week(
        self,
        schedule: DemandSchedule,
        week: int,
    ) -> Optional[dict[str, float]]:
        """Get demand amounts for a shipping week.

        Returns actual demand if available, otherwise estimated demand.

        Args:
            schedule: Current demand schedule
            week: Week to get demand for

        Returns:
            Demand by product type, or None if not a shipping week
        """
        if not self.is_shipping_week(week):
            return None

        forecasts = schedule.get_forecasts_for_week(week)
        if not forecasts:
            return None

        demand = {}
        for forecast in forecasts:
            # Use actual if available, else estimated
            base_demand = (
                forecast.actual_demand
                if forecast.actual_demand is not None
                else forecast.estimated_demand
            )
            demand[forecast.product_type] = base_demand + forecast.carryover

        return demand
