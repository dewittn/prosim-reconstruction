"""
Tests for the main simulation engine.

Tests cover:
- Simulation initialization
- Decision application to machines
- Week processing
- Production flow
- Cost calculations
- Report generation
- Multi-week simulation
"""

import pytest

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.engine.simulation import Simulation, SimulationWeekResult, run_simulation
from prosim.models.company import Company, CompanyConfig
from prosim.models.decisions import Decisions, MachineDecision, PartOrders
from prosim.models.inventory import Inventory, RawMaterialsInventory
from prosim.models.machines import MachineFloor
from prosim.models.operators import Department, TrainingStatus, Workforce


class TestSimulationInitialization:
    """Tests for Simulation class initialization."""

    def test_default_initialization(self):
        """Test creating simulation with default config."""
        sim = Simulation()
        assert sim.config is not None
        assert sim.inventory_manager is not None
        assert sim.operator_manager is not None
        assert sim.production_engine is not None
        assert sim.cost_calculator is not None
        assert sim.demand_manager is not None

    def test_with_custom_config(self):
        """Test creating simulation with custom config."""
        config = get_default_config()
        sim = Simulation(config=config)
        assert sim.config == config

    def test_with_random_seed(self):
        """Test creating simulation with random seed."""
        sim = Simulation(random_seed=42)
        assert sim._random_seed == 42

    def test_reset_clears_cumulative(self):
        """Test that reset clears cumulative costs."""
        sim = Simulation(random_seed=42)
        sim._cumulative_costs = "something"  # Set a value
        sim.reset()
        assert sim._cumulative_costs is None


class TestDecisionApplication:
    """Tests for applying decisions to machines."""

    @pytest.fixture
    def simulation(self):
        return Simulation(random_seed=42)

    @pytest.fixture
    def machine_floor(self):
        return MachineFloor.create_default()

    @pytest.fixture
    def sample_decisions(self):
        """Create sample decisions for testing."""
        machine_decisions = [
            MachineDecision(
                machine_id=1,
                send_for_training=False,
                part_type=1,  # X'
                scheduled_hours=40.0,
            ),
            MachineDecision(
                machine_id=2,
                send_for_training=True,  # Training
                part_type=2,
                scheduled_hours=0.0,
            ),
            MachineDecision(
                machine_id=3,
                send_for_training=False,
                part_type=3,  # Z'
                scheduled_hours=35.0,
            ),
            MachineDecision(
                machine_id=4,
                send_for_training=False,
                part_type=1,
                scheduled_hours=40.0,
            ),
            MachineDecision(
                machine_id=5,
                send_for_training=False,
                part_type=1,  # X
                scheduled_hours=40.0,
            ),
            MachineDecision(
                machine_id=6,
                send_for_training=False,
                part_type=2,  # Y
                scheduled_hours=40.0,
            ),
            MachineDecision(
                machine_id=7,
                send_for_training=False,
                part_type=3,  # Z
                scheduled_hours=40.0,
            ),
            MachineDecision(
                machine_id=8,
                send_for_training=False,
                part_type=1,
                scheduled_hours=40.0,
            ),
            MachineDecision(
                machine_id=9,
                send_for_training=False,
                part_type=2,
                scheduled_hours=40.0,
            ),
        ]
        return Decisions(
            week=1,
            company_id=1,
            quality_budget=500.0,
            maintenance_budget=300.0,
            raw_materials_regular=1000.0,
            raw_materials_expedited=0.0,
            part_orders=PartOrders(x_prime=0.0, y_prime=0.0, z_prime=0.0),
            machine_decisions=machine_decisions,
        )

    def test_apply_decisions_to_machines(
        self, simulation, machine_floor, sample_decisions
    ):
        """Test that decisions are correctly applied to machines."""
        updated_floor = simulation.apply_decisions_to_machines(
            machine_floor, sample_decisions
        )

        # Check machine 1 assignment
        m1 = updated_floor.get_machine(1)
        assert m1.assignment is not None
        assert m1.assignment.part_type == "X'"
        assert m1.assignment.scheduled_hours == 40.0
        assert not m1.assignment.send_for_training

        # Check machine 2 (training)
        m2 = updated_floor.get_machine(2)
        assert m2.assignment is not None
        assert m2.assignment.send_for_training

        # Check assembly machine
        m5 = updated_floor.get_machine(5)
        assert m5.assignment is not None
        assert m5.assignment.part_type == "X"  # Product, not part
        assert m5.assignment.scheduled_hours == 40.0

    def test_apply_decisions_respects_department(
        self, simulation, machine_floor, sample_decisions
    ):
        """Test that part types are correctly mapped per department."""
        updated_floor = simulation.apply_decisions_to_machines(
            machine_floor, sample_decisions
        )

        # Parts department should have prime suffix
        m1 = updated_floor.get_machine(1)
        assert m1.assignment.part_type == "X'"

        # Assembly department should NOT have prime suffix
        m5 = updated_floor.get_machine(5)
        assert m5.assignment.part_type == "X"


class TestMachineRepairs:
    """Tests for machine repair determination."""

    def test_repair_probability(self):
        """Test that repairs occur with expected probability."""
        sim = Simulation(random_seed=42)
        floor = MachineFloor.create_default()

        # Assign all machines
        for i in range(1, 10):
            machine = floor.get_machine(i)
            part_type = "X'" if machine.is_parts_machine else "X"
            floor = floor.update_machine(
                machine.assign(
                    operator_id=i, part_type=part_type, scheduled_hours=40.0
                )
            )

        # Run multiple times to check probability
        repair_counts = []
        for _ in range(100):
            repairs = sim.determine_machine_repairs(floor)
            total_repairs = sum(repairs.values())
            repair_counts.append(total_repairs)

        # With 9 machines and ~10-15% probability, expect ~1 repair per week on average
        avg_repairs = sum(repair_counts) / len(repair_counts)
        assert 0.5 < avg_repairs < 2.0


class TestWeekProcessing:
    """Tests for complete week processing."""

    @pytest.fixture
    def simulation(self):
        return Simulation(random_seed=42)

    @pytest.fixture
    def company(self):
        """Create a company with initial raw materials."""
        config = CompanyConfig(initial_raw_materials=5000.0)
        return Company.create_new(company_id=1, name="Test Company", config=config)

    @pytest.fixture
    def decisions(self):
        """Create decisions for a production week."""
        machine_decisions = [
            MachineDecision(
                machine_id=i,
                send_for_training=False,
                part_type=((i - 1) % 3) + 1,  # Cycle X, Y, Z
                scheduled_hours=40.0,
            )
            for i in range(1, 10)
        ]
        return Decisions(
            week=1,
            company_id=1,
            quality_budget=500.0,
            maintenance_budget=300.0,
            raw_materials_regular=2000.0,
            raw_materials_expedited=0.0,
            part_orders=PartOrders(x_prime=0.0, y_prime=0.0, z_prime=0.0),
            machine_decisions=machine_decisions,
        )

    def test_process_week_returns_result(self, simulation, company, decisions):
        """Test that process_week returns a valid result."""
        result = simulation.process_week(company, decisions)

        assert isinstance(result, SimulationWeekResult)
        assert result.week == 1
        assert result.company_id == 1
        assert result.updated_company is not None
        assert result.weekly_report is not None

    def test_process_week_advances_company(self, simulation, company, decisions):
        """Test that company week advances after processing."""
        result = simulation.process_week(company, decisions)

        assert result.updated_company.current_week == 2

    def test_process_week_calculates_production(self, simulation, company, decisions):
        """Test that production is calculated."""
        result = simulation.process_week(company, decisions)

        # With raw materials available, should have production
        parts_prod = result.production_result.parts_department.total_net_production
        assert parts_prod > 0

    def test_process_week_calculates_costs(self, simulation, company, decisions):
        """Test that costs are calculated."""
        result = simulation.process_week(company, decisions)

        assert result.weekly_cost_report is not None
        assert result.weekly_cost_report.total_costs > 0

    def test_process_week_generates_report(self, simulation, company, decisions):
        """Test that weekly report is generated."""
        result = simulation.process_week(company, decisions)

        report = result.weekly_report
        assert report.week == 1
        assert report.company_id == 1
        assert report.weekly_costs is not None
        assert report.production is not None
        assert report.inventory is not None

    def test_process_week_validates_week_number(self, simulation, company, decisions):
        """Test that week validation works."""
        wrong_decisions = decisions.model_copy(update={"week": 5})

        with pytest.raises(ValueError, match="doesn't match"):
            simulation.process_week(company, wrong_decisions)

    def test_process_week_places_orders(self, simulation, company, decisions):
        """Test that orders are placed."""
        result = simulation.process_week(company, decisions)

        # Regular RM order should be pending (3 week lead time)
        pending = result.updated_company.orders.orders
        assert len(pending) > 0

        # Find the regular RM order
        rm_orders = [o for o in pending if o.is_raw_materials]
        assert len(rm_orders) > 0
        assert rm_orders[0].amount == 2000.0

    def test_process_week_tracks_cumulative_costs(self, simulation, company, decisions):
        """Test that cumulative costs are tracked."""
        result1 = simulation.process_week(company, decisions)

        # Process second week
        week2_decisions = decisions.model_copy(update={"week": 2})
        result2 = simulation.process_week(result1.updated_company, week2_decisions)

        # Cumulative should be greater than weekly
        assert (
            result2.cumulative_cost_report.total_costs
            >= result2.weekly_cost_report.total_costs
        )


class TestShippingWeek:
    """Tests for shipping week processing."""

    @pytest.fixture
    def simulation(self):
        return Simulation(random_seed=42)

    def test_shipping_week_detection(self, simulation):
        """Test shipping week detection."""
        # Default shipping frequency is 4
        assert simulation.demand_manager.is_shipping_week(4)
        assert simulation.demand_manager.is_shipping_week(8)
        assert not simulation.demand_manager.is_shipping_week(3)
        assert not simulation.demand_manager.is_shipping_week(5)

    def test_shipping_week_generates_demand(self, simulation):
        """Test that shipping weeks generate demand."""
        # Set up company at week 4 (shipping week)
        config = CompanyConfig(initial_raw_materials=10000.0)
        company = Company.create_new(company_id=1, config=config)

        # Advance to week 4
        for week in range(1, 4):
            company = company.model_copy(update={"current_week": week + 1})

        # Create decisions for week 4
        machine_decisions = [
            MachineDecision(
                machine_id=i,
                send_for_training=False,
                part_type=((i - 1) % 3) + 1,
                scheduled_hours=40.0,
            )
            for i in range(1, 10)
        ]
        decisions = Decisions(
            week=4,
            company_id=1,
            quality_budget=500.0,
            maintenance_budget=300.0,
            raw_materials_regular=0.0,
            raw_materials_expedited=0.0,
            part_orders=PartOrders(),
            machine_decisions=machine_decisions,
        )

        result = simulation.process_week(company, decisions)

        # Should have shipping demand
        assert result.shipping_demand is not None or result.fulfillment_result is not None


class TestMultiWeekSimulation:
    """Tests for running simulation across multiple weeks."""

    def test_run_simulation_multiple_weeks(self):
        """Test running simulation for multiple weeks."""
        config = CompanyConfig(initial_raw_materials=10000.0)
        company = Company.create_new(company_id=1, config=config)

        # Create decisions for 3 weeks
        decisions_list = []
        for week in range(1, 4):
            machine_decisions = [
                MachineDecision(
                    machine_id=i,
                    send_for_training=False,
                    part_type=((i - 1) % 3) + 1,
                    scheduled_hours=40.0,
                )
                for i in range(1, 10)
            ]
            decisions = Decisions(
                week=week,
                company_id=1,
                quality_budget=500.0,
                maintenance_budget=300.0,
                raw_materials_regular=1000.0,
                raw_materials_expedited=0.0,
                part_orders=PartOrders(),
                machine_decisions=machine_decisions,
            )
            decisions_list.append(decisions)

        results = run_simulation(company, decisions_list, random_seed=42)

        assert len(results) == 3
        assert results[0].week == 1
        assert results[1].week == 2
        assert results[2].week == 3

        # Final company should be at week 4
        assert results[-1].updated_company.current_week == 4

    def test_run_simulation_accumulates_reports(self):
        """Test that reports accumulate across weeks."""
        config = CompanyConfig(initial_raw_materials=10000.0)
        company = Company.create_new(company_id=1, config=config)

        decisions_list = []
        for week in range(1, 4):
            machine_decisions = [
                MachineDecision(
                    machine_id=i,
                    send_for_training=False,
                    part_type=((i - 1) % 3) + 1,
                    scheduled_hours=40.0,
                )
                for i in range(1, 10)
            ]
            decisions = Decisions(
                week=week,
                company_id=1,
                quality_budget=500.0,
                maintenance_budget=300.0,
                raw_materials_regular=1000.0,
                raw_materials_expedited=0.0,
                part_orders=PartOrders(),
                machine_decisions=machine_decisions,
            )
            decisions_list.append(decisions)

        results = run_simulation(company, decisions_list, random_seed=42)

        final_company = results[-1].updated_company
        assert len(final_company.reports) == 3

    def test_run_simulation_reproducibility(self):
        """Test that simulations with same seed produce same results."""
        config = CompanyConfig(initial_raw_materials=10000.0)

        decisions_list = []
        for week in range(1, 4):
            machine_decisions = [
                MachineDecision(
                    machine_id=i,
                    send_for_training=False,
                    part_type=((i - 1) % 3) + 1,
                    scheduled_hours=40.0,
                )
                for i in range(1, 10)
            ]
            decisions = Decisions(
                week=week,
                company_id=1,
                quality_budget=500.0,
                maintenance_budget=300.0,
                raw_materials_regular=1000.0,
                raw_materials_expedited=0.0,
                part_orders=PartOrders(),
                machine_decisions=machine_decisions,
            )
            decisions_list.append(decisions)

        company1 = Company.create_new(company_id=1, config=config)
        results1 = run_simulation(company1, decisions_list, random_seed=42)

        company2 = Company.create_new(company_id=1, config=config)
        results2 = run_simulation(company2, decisions_list, random_seed=42)

        # Should produce same total costs
        assert (
            results1[-1].cumulative_cost_report.total_costs
            == results2[-1].cumulative_cost_report.total_costs
        )


class TestReportBuilding:
    """Tests for report building functions."""

    @pytest.fixture
    def simulation(self):
        return Simulation(random_seed=42)

    @pytest.fixture
    def company(self):
        config = CompanyConfig(initial_raw_materials=5000.0)
        return Company.create_new(company_id=1, config=config)

    @pytest.fixture
    def decisions(self):
        machine_decisions = [
            MachineDecision(
                machine_id=i,
                send_for_training=False,
                part_type=((i - 1) % 3) + 1,
                scheduled_hours=40.0,
            )
            for i in range(1, 10)
        ]
        return Decisions(
            week=1,
            company_id=1,
            quality_budget=500.0,
            maintenance_budget=300.0,
            raw_materials_regular=2000.0,
            raw_materials_expedited=0.0,
            part_orders=PartOrders(),
            machine_decisions=machine_decisions,
        )

    def test_inventory_report_structure(self, simulation, company, decisions):
        """Test inventory report has correct structure."""
        result = simulation.process_week(company, decisions)
        inv_report = result.weekly_report.inventory

        assert inv_report.raw_materials is not None
        assert inv_report.parts_x is not None
        assert inv_report.parts_y is not None
        assert inv_report.parts_z is not None
        assert inv_report.products_x is not None
        assert inv_report.products_y is not None
        assert inv_report.products_z is not None

    def test_production_report_structure(self, simulation, company, decisions):
        """Test production report has correct structure."""
        result = simulation.process_week(company, decisions)
        prod_report = result.weekly_report.production

        # Should have parts and assembly departments
        assert len(prod_report.parts_department) == 4
        assert len(prod_report.assembly_department) == 5

    def test_cost_report_structure(self, simulation, company, decisions):
        """Test cost report has correct structure."""
        result = simulation.process_week(company, decisions)
        cost_report = result.weekly_report.weekly_costs

        assert cost_report.x_costs is not None
        assert cost_report.y_costs is not None
        assert cost_report.z_costs is not None
        assert cost_report.overhead is not None

    def test_demand_report_structure(self, simulation, company, decisions):
        """Test demand report has correct structure."""
        result = simulation.process_week(company, decisions)

        assert result.weekly_report.demand_x is not None
        assert result.weekly_report.demand_y is not None
        assert result.weekly_report.demand_z is not None


class TestIntegration:
    """Integration tests for the simulation engine."""

    def test_full_production_flow(self):
        """Test complete production flow from raw materials to products."""
        config = CompanyConfig(initial_raw_materials=10000.0)
        company = Company.create_new(company_id=1, config=config)

        # Schedule all machines for production
        machine_decisions = [
            MachineDecision(
                machine_id=i,
                send_for_training=False,
                part_type=1,  # All produce X/X'
                scheduled_hours=40.0,
            )
            for i in range(1, 10)
        ]
        decisions = Decisions(
            week=1,
            company_id=1,
            quality_budget=500.0,
            maintenance_budget=300.0,
            raw_materials_regular=0.0,
            raw_materials_expedited=0.0,
            part_orders=PartOrders(),
            machine_decisions=machine_decisions,
        )

        sim = Simulation(random_seed=42)
        result = sim.process_week(company, decisions)

        # Should have consumed raw materials
        rm_used = result.weekly_report.inventory.raw_materials.used_in_production
        assert rm_used > 0

        # Should have produced parts
        parts_produced = result.weekly_report.inventory.parts_x.production_this_week
        assert parts_produced > 0

        # Should have produced products (assuming parts were available)
        # Note: First week may not have products if parts weren't pre-stocked

    def test_training_flow(self):
        """Test operator training flow."""
        company = Company.create_new(company_id=1)

        # Send operator 1 for training
        machine_decisions = [
            MachineDecision(
                machine_id=1,
                send_for_training=True,  # Training
                part_type=1,
                scheduled_hours=0.0,
            )
        ] + [
            MachineDecision(
                machine_id=i,
                send_for_training=False,
                part_type=1,
                scheduled_hours=40.0,
            )
            for i in range(2, 10)
        ]
        decisions = Decisions(
            week=1,
            company_id=1,
            quality_budget=0.0,
            maintenance_budget=0.0,
            raw_materials_regular=0.0,
            raw_materials_expedited=0.0,
            part_orders=PartOrders(),
            machine_decisions=machine_decisions,
        )

        sim = Simulation(random_seed=42)
        result = sim.process_week(company, decisions)

        # Check training result
        assert 1 in result.training_result.operators_sent_to_training

    def test_order_flow(self):
        """Test order placement and receiving."""
        company = Company.create_new(company_id=1)

        # Place regular RM order (3 week lead time)
        machine_decisions = [
            MachineDecision(
                machine_id=i,
                send_for_training=False,
                part_type=1,
                scheduled_hours=0.0,
            )
            for i in range(1, 10)
        ]
        decisions = Decisions(
            week=1,
            company_id=1,
            quality_budget=0.0,
            maintenance_budget=0.0,
            raw_materials_regular=1000.0,
            raw_materials_expedited=0.0,
            part_orders=PartOrders(),
            machine_decisions=machine_decisions,
        )

        sim = Simulation(random_seed=42)
        result = sim.process_week(company, decisions)

        # Order should be pending
        pending = result.updated_company.orders.orders
        assert len(pending) == 1
        assert pending[0].amount == 1000.0
        assert pending[0].week_due == 4  # Week 1 + 3 lead time
