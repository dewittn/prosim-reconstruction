"""
Tests for the DemandManager class.

Tests cover:
- Forecast generation with uncertainty
- Actual demand revelation at shipping week
- Carryover tracking
- Shipping period coordination
- Demand schedule management
- Integration with fulfillment
"""

import pytest

from prosim.config.schema import DemandConfig, ProsimConfig, SimulationConfig
from prosim.engine.demand import (
    DemandGenerationResult,
    DemandManager,
    ForecastUpdateResult,
    ShippingPeriodDemand,
)
from prosim.models.orders import DemandForecast, DemandSchedule


class TestDemandManagerInit:
    """Tests for DemandManager initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        manager = DemandManager()
        assert manager.config is not None
        assert manager.base_demand == {"X": 600.0, "Y": 400.0, "Z": 200.0}

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = ProsimConfig(
            simulation=SimulationConfig(shipping_frequency=6),
        )
        manager = DemandManager(config=config)
        assert manager.config.simulation.shipping_frequency == 6

    def test_init_with_random_seed(self):
        """Test initialization with random seed for reproducibility."""
        manager1 = DemandManager(random_seed=42)
        manager2 = DemandManager(random_seed=42)

        # Generate forecasts - should be identical with same seed
        forecast1 = manager1.generate_forecast("X", shipping_week=4, current_week=1)
        forecast2 = manager2.generate_forecast("X", shipping_week=4, current_week=1)
        assert forecast1.estimated_demand == forecast2.estimated_demand

    def test_init_with_custom_base_demand(self):
        """Test initialization with custom base demand."""
        custom_demand = {"X": 500.0, "Y": 300.0, "Z": 100.0}
        manager = DemandManager(base_demand=custom_demand)
        assert manager.base_demand == custom_demand

    def test_set_random_seed(self):
        """Test setting random seed after initialization."""
        manager = DemandManager()
        manager.set_random_seed(42)

        # Verify reproducibility
        forecast1 = manager.generate_forecast("X", shipping_week=4, current_week=1)
        manager.set_random_seed(42)
        forecast2 = manager.generate_forecast("X", shipping_week=4, current_week=1)
        assert forecast1.estimated_demand == forecast2.estimated_demand


class TestForecastGeneration:
    """Tests for demand forecast generation."""

    def test_generate_forecast_basic(self):
        """Test basic forecast generation."""
        manager = DemandManager(random_seed=42)
        forecast = manager.generate_forecast(
            product_type="X",
            shipping_week=4,
            current_week=1,
        )
        assert forecast.product_type == "X"
        assert forecast.shipping_week == 4
        assert forecast.estimated_demand > 0
        assert forecast.actual_demand is None  # Not revealed yet
        assert forecast.carryover == 0.0

    def test_generate_forecast_with_carryover(self):
        """Test forecast generation with carryover."""
        manager = DemandManager(random_seed=42)
        forecast = manager.generate_forecast(
            product_type="Y",
            shipping_week=8,
            current_week=4,
            carryover=50.0,
        )
        assert forecast.carryover == 50.0
        assert forecast.total_demand == forecast.estimated_demand + 50.0

    def test_forecast_uncertainty_decreases_over_time(self):
        """Test that forecast uncertainty decreases as shipping approaches."""
        manager = DemandManager(random_seed=123)

        # Generate many forecasts at different weeks out
        std_devs = manager.config.demand.forecast_std_dev_weeks_out

        # At 4 weeks out, std_dev should be 300
        assert manager.get_forecast_std_dev(4) == 300
        # At 2 weeks out, std_dev should be 200
        assert manager.get_forecast_std_dev(2) == 200
        # At 1 week out, std_dev should be 100
        assert manager.get_forecast_std_dev(1) == 100
        # At shipping week (0 weeks out), std_dev should be 0
        assert manager.get_forecast_std_dev(0) == 0

    def test_forecast_zero_uncertainty_at_shipping_week(self):
        """Test that there's no uncertainty at shipping week itself."""
        manager = DemandManager(random_seed=42)

        # When current_week == shipping_week (0 weeks out)
        forecast = manager.generate_forecast(
            product_type="X",
            shipping_week=4,
            current_week=4,
        )

        # With 0 std dev, should be exactly base demand
        assert forecast.estimated_demand == 600.0

    def test_forecast_all_product_types(self):
        """Test forecast generation for all product types."""
        manager = DemandManager(random_seed=42)

        for product_type, expected_base in [("X", 600.0), ("Y", 400.0), ("Z", 200.0)]:
            forecast = manager.generate_forecast(
                product_type=product_type,
                shipping_week=4,
                current_week=4,  # At shipping week, no uncertainty
            )
            assert forecast.product_type == product_type
            assert forecast.estimated_demand == expected_base


class TestActualDemand:
    """Tests for actual demand revelation."""

    def test_reveal_actual_demand_basic(self):
        """Test basic actual demand revelation."""
        manager = DemandManager(random_seed=42)
        result = manager.reveal_actual_demand(
            product_type="X",
            shipping_week=4,
        )
        assert isinstance(result, DemandGenerationResult)
        assert result.product_type == "X"
        assert result.base_demand == 600.0
        assert result.actual_demand == 600.0  # Base demand at shipping
        assert result.variation == 0.0
        assert result.total_demand == 600.0

    def test_reveal_actual_demand_with_carryover(self):
        """Test actual demand with carryover from previous period."""
        manager = DemandManager()
        result = manager.reveal_actual_demand(
            product_type="Y",
            shipping_week=4,
            carryover=100.0,
        )
        assert result.actual_demand == 400.0  # Base Y demand
        assert result.carryover_from_previous == 100.0
        assert result.total_demand == 500.0  # 400 + 100

    def test_reveal_actual_demand_all_products(self):
        """Test actual demand revelation for all products."""
        manager = DemandManager()

        for product_type, expected in [("X", 600.0), ("Y", 400.0), ("Z", 200.0)]:
            result = manager.reveal_actual_demand(product_type, shipping_week=4)
            assert result.actual_demand == expected


class TestShippingPeriodDemand:
    """Tests for shipping period demand generation."""

    def test_generate_shipping_period_demand_basic(self):
        """Test basic shipping period demand generation."""
        manager = DemandManager()
        result = manager.generate_shipping_period_demand(shipping_week=4)

        assert isinstance(result, ShippingPeriodDemand)
        assert result.shipping_week == 4
        assert "X" in result.demands
        assert "Y" in result.demands
        assert "Z" in result.demands

    def test_generate_shipping_period_demand_with_carryover(self):
        """Test shipping period demand with carryover."""
        manager = DemandManager()
        carryover = {"X": 50.0, "Y": 30.0, "Z": 10.0}
        result = manager.generate_shipping_period_demand(
            shipping_week=8,
            carryover=carryover,
        )

        assert result.demands["X"].carryover_from_previous == 50.0
        assert result.demands["Y"].carryover_from_previous == 30.0
        assert result.demands["Z"].carryover_from_previous == 10.0

        # Total demand should include carryover
        assert result.demands["X"].total_demand == 650.0  # 600 + 50
        assert result.demands["Y"].total_demand == 430.0  # 400 + 30
        assert result.demands["Z"].total_demand == 210.0  # 200 + 10

    def test_total_demand_by_product_property(self):
        """Test total_demand_by_product property."""
        manager = DemandManager()
        carryover = {"X": 100.0, "Y": 50.0, "Z": 25.0}
        result = manager.generate_shipping_period_demand(
            shipping_week=4,
            carryover=carryover,
        )

        totals = result.total_demand_by_product
        assert totals["X"] == 700.0  # 600 + 100
        assert totals["Y"] == 450.0  # 400 + 50
        assert totals["Z"] == 225.0  # 200 + 25


class TestShippingWeekHelpers:
    """Tests for shipping week helper methods."""

    def test_is_shipping_week_default_frequency(self):
        """Test is_shipping_week with default 4-week frequency."""
        manager = DemandManager()

        # Shipping weeks: 4, 8, 12, 16...
        assert not manager.is_shipping_week(1)
        assert not manager.is_shipping_week(2)
        assert not manager.is_shipping_week(3)
        assert manager.is_shipping_week(4)
        assert not manager.is_shipping_week(5)
        assert manager.is_shipping_week(8)
        assert manager.is_shipping_week(12)

    def test_is_shipping_week_custom_frequency(self):
        """Test is_shipping_week with custom frequency."""
        config = ProsimConfig(simulation=SimulationConfig(shipping_frequency=6))
        manager = DemandManager(config=config)

        # Shipping weeks: 6, 12, 18...
        assert not manager.is_shipping_week(4)
        assert manager.is_shipping_week(6)
        assert not manager.is_shipping_week(8)
        assert manager.is_shipping_week(12)

    def test_next_shipping_week_basic(self):
        """Test next_shipping_week calculation."""
        manager = DemandManager()

        assert manager.next_shipping_week(1) == 4
        assert manager.next_shipping_week(2) == 4
        assert manager.next_shipping_week(3) == 4
        assert manager.next_shipping_week(4) == 4  # At shipping week
        assert manager.next_shipping_week(5) == 8
        assert manager.next_shipping_week(9) == 12

    def test_next_shipping_week_custom_frequency(self):
        """Test next_shipping_week with custom frequency."""
        config = ProsimConfig(simulation=SimulationConfig(shipping_frequency=3))
        manager = DemandManager(config=config)

        assert manager.next_shipping_week(1) == 3
        assert manager.next_shipping_week(3) == 3
        assert manager.next_shipping_week(4) == 6


class TestDemandScheduleManagement:
    """Tests for demand schedule management."""

    def test_initialize_demand_schedule_basic(self):
        """Test basic demand schedule initialization."""
        manager = DemandManager(random_seed=42)
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=2)

        assert isinstance(schedule, DemandSchedule)
        assert len(schedule.forecasts) == 6  # 3 products * 2 periods

        # Check forecasts exist for both periods
        week4_forecasts = schedule.get_forecasts_for_week(4)
        week8_forecasts = schedule.get_forecasts_for_week(8)
        assert len(week4_forecasts) == 3
        assert len(week8_forecasts) == 3

    def test_initialize_demand_schedule_from_mid_period(self):
        """Test schedule initialization when starting mid-period."""
        manager = DemandManager(random_seed=42)
        schedule = manager.initialize_demand_schedule(start_week=6, periods_ahead=2)

        # Should start from next shipping week (8)
        week8_forecasts = schedule.get_forecasts_for_week(8)
        week12_forecasts = schedule.get_forecasts_for_week(12)
        assert len(week8_forecasts) == 3
        assert len(week12_forecasts) == 3

    def test_update_forecasts_for_week(self):
        """Test updating forecasts as weeks progress."""
        manager = DemandManager(random_seed=42)
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=2)

        # Update to week 2
        updated_schedule, result = manager.update_forecasts_for_week(schedule, current_week=2)

        assert isinstance(result, ForecastUpdateResult)
        assert result.week == 2

    def test_process_shipping_week_basic(self):
        """Test processing a shipping week."""
        manager = DemandManager(random_seed=42)
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=2)

        # Ship some products at week 4
        units_shipped = {"X": 500.0, "Y": 400.0, "Z": 200.0}
        updated_schedule, demand, carryover = manager.process_shipping_week(
            schedule=schedule,
            shipping_week=4,
            units_shipped=units_shipped,
        )

        assert isinstance(demand, ShippingPeriodDemand)
        assert demand.shipping_week == 4

        # X shipped less than demand (600), so carryover
        assert carryover["X"] == 100.0  # 600 - 500
        # Y and Z fully shipped
        assert carryover["Y"] == 0.0
        assert carryover["Z"] == 0.0

    def test_process_shipping_week_full_shortage(self):
        """Test processing when nothing is shipped."""
        manager = DemandManager()
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=2)

        units_shipped = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        _, demand, carryover = manager.process_shipping_week(
            schedule=schedule,
            shipping_week=4,
            units_shipped=units_shipped,
        )

        # All demand becomes carryover
        assert carryover["X"] == 600.0
        assert carryover["Y"] == 400.0
        assert carryover["Z"] == 200.0

    def test_add_next_period_forecasts(self):
        """Test adding forecasts for the next period."""
        manager = DemandManager(random_seed=42)
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=1)

        # Initially only week 4 forecasts
        assert len(schedule.forecasts) == 3

        # Add next period after processing week 4
        carryover = {"X": 50.0, "Y": 0.0, "Z": 0.0}
        updated = manager.add_next_period_forecasts(
            schedule=schedule,
            current_week=4,
            carryover=carryover,
        )

        # Now should have week 4 and week 8 forecasts
        assert len(updated.forecasts) == 6
        week8_forecasts = updated.get_forecasts_for_week(8)
        assert len(week8_forecasts) == 3

        # Carryover should be included in new forecasts
        x_forecast = next(f for f in week8_forecasts if f.product_type == "X")
        assert x_forecast.carryover == 50.0


class TestDemandPenalty:
    """Tests for demand penalty calculation."""

    def test_calculate_demand_penalty_units_basic(self):
        """Test basic demand penalty unit calculation."""
        manager = DemandManager()
        demand = {"X": 600.0, "Y": 400.0, "Z": 200.0}
        shipped = {"X": 500.0, "Y": 400.0, "Z": 150.0}

        shortage = manager.calculate_demand_penalty_units(demand, shipped)

        assert shortage["X"] == 100.0  # 600 - 500
        assert shortage["Y"] == 0.0    # Fully shipped
        assert shortage["Z"] == 50.0   # 200 - 150

    def test_calculate_demand_penalty_units_no_shortage(self):
        """Test when there's no shortage."""
        manager = DemandManager()
        demand = {"X": 600.0, "Y": 400.0, "Z": 200.0}
        shipped = {"X": 600.0, "Y": 400.0, "Z": 200.0}

        shortage = manager.calculate_demand_penalty_units(demand, shipped)

        assert shortage["X"] == 0.0
        assert shortage["Y"] == 0.0
        assert shortage["Z"] == 0.0

    def test_calculate_demand_penalty_units_overship(self):
        """Test that overshipping doesn't result in negative shortage."""
        manager = DemandManager()
        demand = {"X": 600.0, "Y": 400.0, "Z": 200.0}
        shipped = {"X": 700.0, "Y": 500.0, "Z": 300.0}  # Shipped more than demand

        shortage = manager.calculate_demand_penalty_units(demand, shipped)

        # Shortage should never be negative
        assert shortage["X"] == 0.0
        assert shortage["Y"] == 0.0
        assert shortage["Z"] == 0.0


class TestGetDemandForWeek:
    """Tests for getting demand for a specific week."""

    def test_get_demand_for_shipping_week(self):
        """Test getting demand for a shipping week."""
        manager = DemandManager(random_seed=42)
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=2)

        demand = manager.get_demand_for_week(schedule, week=4)

        assert demand is not None
        assert "X" in demand
        assert "Y" in demand
        assert "Z" in demand

    def test_get_demand_for_non_shipping_week(self):
        """Test getting demand for a non-shipping week returns None."""
        manager = DemandManager()
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=2)

        demand = manager.get_demand_for_week(schedule, week=3)
        assert demand is None

    def test_get_demand_uses_actual_if_available(self):
        """Test that actual demand is used over estimated when available."""
        manager = DemandManager()
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=2)

        # Process shipping week to set actual demand
        units_shipped = {"X": 600.0, "Y": 400.0, "Z": 200.0}
        updated_schedule, _, _ = manager.process_shipping_week(
            schedule=schedule,
            shipping_week=4,
            units_shipped=units_shipped,
        )

        demand = manager.get_demand_for_week(updated_schedule, week=4)
        assert demand is not None


class TestReproducibility:
    """Tests for reproducible demand generation."""

    def test_same_seed_same_forecasts(self):
        """Test that same seed produces same forecast sequences."""
        manager1 = DemandManager(random_seed=12345)
        manager2 = DemandManager(random_seed=12345)

        # Generate a sequence of forecasts
        forecasts1 = [
            manager1.generate_forecast("X", 4, 1),
            manager1.generate_forecast("Y", 4, 1),
            manager1.generate_forecast("Z", 4, 1),
        ]
        forecasts2 = [
            manager2.generate_forecast("X", 4, 1),
            manager2.generate_forecast("Y", 4, 1),
            manager2.generate_forecast("Z", 4, 1),
        ]

        for f1, f2 in zip(forecasts1, forecasts2):
            assert f1.estimated_demand == f2.estimated_demand

    def test_different_seeds_different_forecasts(self):
        """Test that different seeds produce different forecasts."""
        manager1 = DemandManager(random_seed=111)
        manager2 = DemandManager(random_seed=222)

        # Use shipping_week=4, current_week=1 (3 weeks out, std_dev=300)
        forecast1 = manager1.generate_forecast("X", 4, 1)
        forecast2 = manager2.generate_forecast("X", 4, 1)

        # With uncertainty (3 weeks out, std_dev=300), forecasts should differ
        # Note: Very small chance they could be same, but extremely unlikely
        assert forecast1.estimated_demand != forecast2.estimated_demand


class TestIntegration:
    """Integration tests for complete demand flow."""

    def test_full_shipping_cycle(self):
        """Test a complete shipping cycle from forecast to fulfillment."""
        manager = DemandManager(random_seed=42)

        # Initialize schedule at week 1
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=2)

        # Simulate weeks 1-3 (non-shipping weeks)
        for week in range(1, 4):
            assert not manager.is_shipping_week(week)

        # Week 4: Shipping week
        assert manager.is_shipping_week(4)

        # Process shipping with partial fulfillment
        units_shipped = {"X": 500.0, "Y": 350.0, "Z": 200.0}
        updated_schedule, demand, carryover = manager.process_shipping_week(
            schedule=schedule,
            shipping_week=4,
            units_shipped=units_shipped,
        )

        # Verify carryover
        assert carryover["X"] == 100.0  # 600 - 500
        assert carryover["Y"] == 50.0   # 400 - 350
        assert carryover["Z"] == 0.0    # Fully shipped

        # Add next period forecasts
        final_schedule = manager.add_next_period_forecasts(
            schedule=updated_schedule,
            current_week=4,
            carryover=carryover,
        )

        # Verify new period includes carryover
        week12_forecasts = final_schedule.get_forecasts_for_week(12)
        assert len(week12_forecasts) == 3

    def test_multiple_shipping_periods_with_accumulating_carryover(self):
        """Test multiple shipping periods with accumulating carryover."""
        manager = DemandManager(random_seed=42)
        schedule = manager.initialize_demand_schedule(start_week=1, periods_ahead=3)

        # Period 1 (Week 4): Ship nothing
        _, _, carryover1 = manager.process_shipping_week(
            schedule=schedule,
            shipping_week=4,
            units_shipped={"X": 0.0, "Y": 0.0, "Z": 0.0},
        )

        # All demand carries over
        assert carryover1["X"] == 600.0
        assert carryover1["Y"] == 400.0
        assert carryover1["Z"] == 200.0

        # Period 2 (Week 8): Ship some, but less than accumulated demand
        period2_demand = manager.generate_shipping_period_demand(
            shipping_week=8,
            carryover=carryover1,
        )

        # Total demand should be base + carryover
        assert period2_demand.demands["X"].total_demand == 1200.0  # 600 + 600
        assert period2_demand.demands["Y"].total_demand == 800.0   # 400 + 400
        assert period2_demand.demands["Z"].total_demand == 400.0   # 200 + 200

    def test_demand_penalty_integration(self):
        """Test demand penalty calculation in context of shipping."""
        manager = DemandManager()

        # Generate demand
        period = manager.generate_shipping_period_demand(shipping_week=4)
        total_demand = period.total_demand_by_product

        # Ship only half
        shipped = {pt: d / 2 for pt, d in total_demand.items()}
        shortage = manager.calculate_demand_penalty_units(total_demand, shipped)

        # Should have 50% shortage
        for pt in ["X", "Y", "Z"]:
            expected_shortage = total_demand[pt] / 2
            assert abs(shortage[pt] - expected_shortage) < 0.01
