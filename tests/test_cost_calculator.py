"""
Tests for the cost calculator module.

Tests cover:
- Per-product cost calculations (all 9 categories)
- Overhead cost calculations (all 8 categories)
- Weekly cost reports
- Cumulative cost tracking
"""

import pytest

from prosim.config.schema import (
    CarryingCostRatesConfig,
    CostsConfig,
    EquipmentConfig,
    EquipmentRatesConfig,
    FixedCostsConfig,
    LaborRatesConfig,
    MachineRepairConfig,
    ProsimConfig,
)
from prosim.engine.costs import (
    CostCalculationInput,
    CostCalculator,
    CumulativeCostReport,
    OverheadCosts,
    ProductCosts,
    WeeklyCostReport,
)
from prosim.engine.production import (
    DepartmentProductionResult,
    MachineProductionResult,
    ProductionResult,
)
from prosim.engine.workforce import WorkforceCostResult
from prosim.models.inventory import (
    AllPartsInventory,
    AllProductsInventory,
    Inventory,
    PartsInventory,
    ProductsInventory,
    RawMaterialsInventory,
)
from prosim.models.operators import Department
from prosim.models.orders import OrderBook


def create_mock_production_result(
    parts_by_type: dict[str, float] | None = None,
    assembly_by_type: dict[str, float] | None = None,
) -> ProductionResult:
    """Helper to create mock production results."""
    if parts_by_type is None:
        parts_by_type = {}
    if assembly_by_type is None:
        assembly_by_type = {}

    parts_machine_results = []
    for part_type, hours in parts_by_type.items():
        parts_machine_results.append(
            MachineProductionResult(
                machine_id=1,
                department=Department.PARTS,
                operator_id=1,
                part_type=part_type,
                scheduled_hours=hours,
                setup_hours=0.0,
                productive_hours=hours,
                efficiency=1.0,
                gross_production=hours * 60,  # Simplified
                rejects=hours * 60 * 0.178,
                net_production=hours * 60 * 0.822,
            )
        )

    assembly_machine_results = []
    for product_type, hours in assembly_by_type.items():
        assembly_machine_results.append(
            MachineProductionResult(
                machine_id=5,
                department=Department.ASSEMBLY,
                operator_id=2,
                part_type=product_type,
                scheduled_hours=hours,
                setup_hours=0.0,
                productive_hours=hours,
                efficiency=1.0,
                gross_production=hours * 40,  # Simplified
                rejects=hours * 40 * 0.178,
                net_production=hours * 40 * 0.822,
            )
        )

    parts_result = DepartmentProductionResult(
        department=Department.PARTS,
        machine_results=parts_machine_results,
        total_scheduled_hours=sum(parts_by_type.values()) if parts_by_type else 0,
        total_setup_hours=0.0,
        total_productive_hours=sum(parts_by_type.values()) if parts_by_type else 0,
        gross_production_by_type={k: v * 60 for k, v in parts_by_type.items()},
        rejects_by_type={k: v * 60 * 0.178 for k, v in parts_by_type.items()},
        net_production_by_type={k: v * 60 * 0.822 for k, v in parts_by_type.items()},
        total_gross_production=sum(v * 60 for v in parts_by_type.values()) if parts_by_type else 0,
        total_rejects=sum(v * 60 * 0.178 for v in parts_by_type.values()) if parts_by_type else 0,
        total_net_production=sum(v * 60 * 0.822 for v in parts_by_type.values()) if parts_by_type else 0,
    )

    assembly_result = DepartmentProductionResult(
        department=Department.ASSEMBLY,
        machine_results=assembly_machine_results,
        total_scheduled_hours=sum(assembly_by_type.values()) if assembly_by_type else 0,
        total_setup_hours=0.0,
        total_productive_hours=sum(assembly_by_type.values()) if assembly_by_type else 0,
        gross_production_by_type={k: v * 40 for k, v in assembly_by_type.items()},
        rejects_by_type={k: v * 40 * 0.178 for k, v in assembly_by_type.items()},
        net_production_by_type={k: v * 40 * 0.822 for k, v in assembly_by_type.items()},
        total_gross_production=sum(v * 40 for v in assembly_by_type.values()) if assembly_by_type else 0,
        total_rejects=sum(v * 40 * 0.178 for v in assembly_by_type.values()) if assembly_by_type else 0,
        total_net_production=sum(v * 40 * 0.822 for v in assembly_by_type.values()) if assembly_by_type else 0,
    )

    return ProductionResult(
        parts_department=parts_result,
        assembly_department=assembly_result,
        total_gross_production=parts_result.total_gross_production + assembly_result.total_gross_production,
        total_rejects=parts_result.total_rejects + assembly_result.total_rejects,
        total_net_production=parts_result.total_net_production + assembly_result.total_net_production,
    )


def create_mock_inventory(
    rm_ending: float = 0.0,
    parts_ending: dict[str, float] | None = None,
    products_ending: dict[str, float] | None = None,
    parts_received: dict[str, float] | None = None,
) -> Inventory:
    """Helper to create mock inventory."""
    if parts_ending is None:
        parts_ending = {"X'": 0.0, "Y'": 0.0, "Z'": 0.0}
    if products_ending is None:
        products_ending = {"X": 0.0, "Y": 0.0, "Z": 0.0}
    if parts_received is None:
        parts_received = {"X'": 0.0, "Y'": 0.0, "Z'": 0.0}

    return Inventory(
        raw_materials=RawMaterialsInventory(beginning=rm_ending),
        parts=AllPartsInventory(
            x_prime=PartsInventory(
                part_type="X'",
                beginning=parts_ending.get("X'", 0.0),
                orders_received=parts_received.get("X'", 0.0),
            ),
            y_prime=PartsInventory(
                part_type="Y'",
                beginning=parts_ending.get("Y'", 0.0),
                orders_received=parts_received.get("Y'", 0.0),
            ),
            z_prime=PartsInventory(
                part_type="Z'",
                beginning=parts_ending.get("Z'", 0.0),
                orders_received=parts_received.get("Z'", 0.0),
            ),
        ),
        products=AllProductsInventory(
            x=ProductsInventory(product_type="X", beginning=products_ending.get("X", 0.0)),
            y=ProductsInventory(product_type="Y", beginning=products_ending.get("Y", 0.0)),
            z=ProductsInventory(product_type="Z", beginning=products_ending.get("Z", 0.0)),
        ),
    )


def create_mock_workforce_costs(
    training: float = 0.0,
    hiring: float = 0.0,
    layoff: float = 0.0,
    termination: float = 0.0,
) -> WorkforceCostResult:
    """Helper to create mock workforce costs."""
    return WorkforceCostResult(
        training_cost=training,
        hiring_cost=hiring,
        layoff_cost=layoff,
        termination_cost=termination,
        total_cost=training + hiring + layoff + termination,
        operators_hired=int(hiring / 2700) if hiring else 0,
        operators_terminated=int(termination / 400) if termination else 0,
        operators_trained=int(training / 1000) if training else 0,
        operators_laid_off=int(layoff / 200) if layoff else 0,
    )


class TestProductCosts:
    """Tests for ProductCosts dataclass."""

    def test_product_costs_total(self):
        """Test ProductCosts total calculation."""
        costs = ProductCosts(
            product_type="X",
            labor=100.0,
            machine_setup=50.0,
            machine_repair=400.0,
            raw_materials=200.0,
            purchased_parts=150.0,
            equipment_usage=80.0,
            parts_carrying=20.0,
            products_carrying=30.0,
            demand_penalty=0.0,
        )

        assert costs.total == 1030.0


class TestOverheadCosts:
    """Tests for OverheadCosts dataclass."""

    def test_overhead_costs_total(self):
        """Test OverheadCosts total calculation."""
        costs = OverheadCosts(
            quality_planning=750.0,
            plant_maintenance=500.0,
            training_cost=1000.0,
            hiring_cost=2700.0,
            layoff_firing_cost=200.0,
            raw_materials_carrying=50.0,
            ordering_cost=100.0,
            fixed_expense=1500.0,
        )

        assert costs.total == 6800.0


class TestLaborCosts:
    """Tests for labor cost calculations."""

    def test_labor_costs_basic(self):
        """Test basic labor cost calculation."""
        calculator = CostCalculator()
        production = create_mock_production_result(
            parts_by_type={"X'": 40.0},
            assembly_by_type={"X": 30.0},
        )

        costs = calculator.calculate_labor_costs(production)

        # Parts: 40 hours * $10 = $400
        # Assembly: 30 hours * $10 = $300
        # Total X = $700
        assert costs["X"] == 700.0
        assert costs["Y"] == 0.0
        assert costs["Z"] == 0.0

    def test_labor_costs_all_products(self):
        """Test labor costs for all product types."""
        calculator = CostCalculator()
        production = create_mock_production_result(
            parts_by_type={"X'": 40.0, "Y'": 30.0, "Z'": 20.0},
            assembly_by_type={"X": 20.0, "Y": 25.0, "Z": 30.0},
        )

        costs = calculator.calculate_labor_costs(production)

        assert costs["X"] == 600.0  # 40 + 20 hours * $10
        assert costs["Y"] == 550.0  # 30 + 25 hours * $10
        assert costs["Z"] == 500.0  # 20 + 30 hours * $10

    def test_labor_costs_custom_rate(self):
        """Test labor costs with custom hourly rate."""
        config = ProsimConfig(
            costs=CostsConfig(labor=LaborRatesConfig(regular_hourly=15.0))
        )
        calculator = CostCalculator(config)
        production = create_mock_production_result(
            parts_by_type={"X'": 10.0},
        )

        costs = calculator.calculate_labor_costs(production)

        assert costs["X"] == 150.0  # 10 hours * $15


class TestSetupCosts:
    """Tests for setup cost calculations."""

    def test_setup_costs_with_setup_time(self):
        """Test setup costs when setup time is incurred."""
        calculator = CostCalculator()

        # Create production with setup time
        parts_result = DepartmentProductionResult(
            department=Department.PARTS,
            machine_results=[
                MachineProductionResult(
                    machine_id=1,
                    department=Department.PARTS,
                    operator_id=1,
                    part_type="X'",
                    scheduled_hours=40.0,
                    setup_hours=2.0,  # 2 hour setup
                    productive_hours=38.0,
                    efficiency=1.0,
                    gross_production=2280.0,
                    rejects=405.84,
                    net_production=1874.16,
                )
            ],
            total_scheduled_hours=40.0,
            total_setup_hours=2.0,
            total_productive_hours=38.0,
            gross_production_by_type={"X'": 2280.0},
            rejects_by_type={},
            net_production_by_type={},
            total_gross_production=2280.0,
            total_rejects=405.84,
            total_net_production=1874.16,
        )

        assembly_result = DepartmentProductionResult(
            department=Department.ASSEMBLY,
            machine_results=[],
            total_scheduled_hours=0.0,
            total_setup_hours=0.0,
            total_productive_hours=0.0,
            gross_production_by_type={},
            rejects_by_type={},
            net_production_by_type={},
            total_gross_production=0.0,
            total_rejects=0.0,
            total_net_production=0.0,
        )

        production = ProductionResult(
            parts_department=parts_result,
            assembly_department=assembly_result,
            total_gross_production=2280.0,
            total_rejects=405.84,
            total_net_production=1874.16,
        )

        costs = calculator.calculate_setup_costs(production)

        # 2 hours * $40/hour = $80
        assert costs["X"] == 80.0


class TestRepairCosts:
    """Tests for machine repair cost calculations."""

    def test_repair_costs_single_repair(self):
        """Test repair costs with single repair."""
        calculator = CostCalculator()
        repairs = {"X": 1, "Y": 0, "Z": 0}

        costs = calculator.calculate_repair_costs(repairs)

        assert costs["X"] == 400.0  # Default $400 per repair
        assert costs["Y"] == 0.0
        assert costs["Z"] == 0.0

    def test_repair_costs_multiple_repairs(self):
        """Test repair costs with multiple repairs."""
        calculator = CostCalculator()
        repairs = {"X": 2, "Y": 1, "Z": 0}

        costs = calculator.calculate_repair_costs(repairs)

        assert costs["X"] == 800.0
        assert costs["Y"] == 400.0
        assert costs["Z"] == 0.0

    def test_repair_costs_custom_rate(self):
        """Test repair costs with custom rate."""
        config = ProsimConfig(
            equipment=EquipmentConfig(
                repair=MachineRepairConfig(cost_per_repair=500.0)
            )
        )
        calculator = CostCalculator(config)
        repairs = {"X": 1}

        costs = calculator.calculate_repair_costs(repairs)

        assert costs["X"] == 500.0


class TestEquipmentCosts:
    """Tests for equipment usage cost calculations."""

    def test_equipment_costs_basic(self):
        """Test basic equipment cost calculation."""
        calculator = CostCalculator()
        production = create_mock_production_result(
            parts_by_type={"X'": 40.0},
            assembly_by_type={"X": 30.0},
        )

        costs = calculator.calculate_equipment_costs(production)

        # Parts: 40 hours * $100 = $4000
        # Assembly: 30 hours * $80 = $2400
        # Total X = $6400
        assert costs["X"] == 6400.0

    def test_equipment_costs_custom_rates(self):
        """Test equipment costs with custom rates."""
        config = ProsimConfig(
            equipment=EquipmentConfig(
                rates=EquipmentRatesConfig(
                    parts_department=50.0,
                    assembly_department=40.0,
                )
            )
        )
        calculator = CostCalculator(config)
        production = create_mock_production_result(
            parts_by_type={"X'": 10.0},
            assembly_by_type={"X": 10.0},
        )

        costs = calculator.calculate_equipment_costs(production)

        # Parts: 10 hours * $50 = $500
        # Assembly: 10 hours * $40 = $400
        assert costs["X"] == 900.0


class TestCarryingCosts:
    """Tests for inventory carrying cost calculations."""

    def test_parts_carrying_costs(self):
        """Test parts carrying cost calculation."""
        calculator = CostCalculator()
        inventory = create_mock_inventory(
            parts_ending={"X'": 1000.0, "Y'": 500.0, "Z'": 200.0}
        )

        costs = calculator.calculate_parts_carrying_costs(inventory)

        # Default rate is $0.05 per part
        assert costs["X"] == 50.0  # 1000 * 0.05
        assert costs["Y"] == 25.0  # 500 * 0.05
        assert costs["Z"] == 10.0  # 200 * 0.05

    def test_products_carrying_costs(self):
        """Test products carrying cost calculation."""
        calculator = CostCalculator()
        inventory = create_mock_inventory(
            products_ending={"X": 100.0, "Y": 200.0, "Z": 150.0}
        )

        costs = calculator.calculate_products_carrying_costs(inventory)

        # Default rate is $0.10 per product
        assert costs["X"] == 10.0  # 100 * 0.10
        assert costs["Y"] == 20.0  # 200 * 0.10
        assert costs["Z"] == 15.0  # 150 * 0.10

    def test_raw_materials_carrying_costs(self):
        """Test raw materials carrying cost calculation."""
        calculator = CostCalculator()
        inventory = create_mock_inventory(rm_ending=5000.0)

        cost = calculator.calculate_raw_materials_carrying(inventory)

        # Default rate is $0.01 per unit
        assert cost == 50.0  # 5000 * 0.01

    def test_carrying_costs_custom_rates(self):
        """Test carrying costs with custom rates."""
        config = ProsimConfig(
            costs=CostsConfig(
                carrying=CarryingCostRatesConfig(
                    raw_materials=0.02,
                    parts=0.10,
                    products=0.20,
                )
            )
        )
        calculator = CostCalculator(config)
        inventory = create_mock_inventory(
            rm_ending=1000.0,
            parts_ending={"X'": 100.0, "Y'": 0.0, "Z'": 0.0},
            products_ending={"X": 50.0, "Y": 0.0, "Z": 0.0},
        )

        parts_costs = calculator.calculate_parts_carrying_costs(inventory)
        products_costs = calculator.calculate_products_carrying_costs(inventory)
        rm_cost = calculator.calculate_raw_materials_carrying(inventory)

        assert parts_costs["X"] == 10.0  # 100 * 0.10
        assert products_costs["X"] == 10.0  # 50 * 0.20
        assert rm_cost == 20.0  # 1000 * 0.02


class TestDemandPenalty:
    """Tests for demand penalty calculations."""

    def test_demand_penalty_basic(self):
        """Test basic demand penalty calculation."""
        calculator = CostCalculator()
        shortage = {"X": 100.0, "Y": 50.0, "Z": 0.0}

        costs = calculator.calculate_demand_penalty(shortage)

        # Default $10 per unit
        assert costs["X"] == 1000.0
        assert costs["Y"] == 500.0
        assert costs["Z"] == 0.0

    def test_demand_penalty_custom_rate(self):
        """Test demand penalty with custom rate."""
        calculator = CostCalculator()
        shortage = {"X": 100.0}

        costs = calculator.calculate_demand_penalty(shortage, penalty_per_unit=20.0)

        assert costs["X"] == 2000.0


class TestOrderingCosts:
    """Tests for ordering cost calculations."""

    def test_ordering_costs_basic(self):
        """Test basic ordering cost calculation."""
        calculator = CostCalculator()

        cost = calculator.calculate_ordering_cost(
            expedited_count=1,
            regular_count=1,
            parts_count=3,
        )

        # (1 + 1 + 3) * $100 base + 1 * $1200 expedited = $1700
        assert cost == 1700.0

    def test_ordering_costs_no_expedited(self):
        """Test ordering costs without expedited orders."""
        calculator = CostCalculator()

        cost = calculator.calculate_ordering_cost(
            expedited_count=0,
            regular_count=2,
            parts_count=3,
        )

        # (0 + 2 + 3) * $100 = $500
        assert cost == 500.0


class TestOverheadCalculation:
    """Tests for complete overhead cost calculations."""

    def test_overhead_costs_complete(self):
        """Test complete overhead cost calculation."""
        calculator = CostCalculator()

        production = create_mock_production_result()
        inventory = create_mock_inventory(rm_ending=1000.0)
        workforce = create_mock_workforce_costs(
            training=2000.0,
            hiring=2700.0,
            layoff=200.0,
            termination=400.0,
        )

        calc_input = CostCalculationInput(
            week=1,
            production_result=production,
            inventory=inventory,
            order_book=OrderBook(),
            workforce_costs=workforce,
            quality_budget=750.0,
            maintenance_budget=500.0,
            expedited_orders_count=1,
            regular_orders_count=1,
            parts_orders_count=3,
        )

        overhead = calculator.calculate_overhead_costs(calc_input)

        assert overhead.quality_planning == 750.0
        assert overhead.plant_maintenance == 500.0
        assert overhead.training_cost == 2000.0
        assert overhead.hiring_cost == 2700.0
        assert overhead.layoff_firing_cost == 600.0  # 200 + 400
        assert overhead.raw_materials_carrying == 10.0  # 1000 * 0.01
        assert overhead.ordering_cost == 1700.0  # See test above
        assert overhead.fixed_expense == 1500.0


class TestWeeklyCostReport:
    """Tests for weekly cost report generation."""

    def test_weekly_cost_report(self):
        """Test generating a complete weekly cost report."""
        calculator = CostCalculator()

        production = create_mock_production_result(
            parts_by_type={"X'": 40.0, "Y'": 30.0},
            assembly_by_type={"X": 20.0, "Y": 15.0},
        )
        inventory = create_mock_inventory(
            rm_ending=500.0,
            parts_ending={"X'": 100.0, "Y'": 200.0, "Z'": 0.0},
            products_ending={"X": 50.0, "Y": 75.0, "Z": 0.0},
        )
        workforce = create_mock_workforce_costs(training=1000.0, hiring=2700.0)

        calc_input = CostCalculationInput(
            week=1,
            production_result=production,
            inventory=inventory,
            order_book=OrderBook(),
            workforce_costs=workforce,
            quality_budget=750.0,
            maintenance_budget=500.0,
            demand_shortage={"X": 0.0, "Y": 0.0, "Z": 0.0},
            machine_repairs={"X": 0, "Y": 1, "Z": 0},
            expedited_orders_count=0,
            regular_orders_count=1,
            parts_orders_count=0,
        )

        report = calculator.calculate_weekly_costs(calc_input)

        assert report.week == 1
        assert "X" in report.product_costs
        assert "Y" in report.product_costs
        assert "Z" in report.product_costs
        assert report.product_subtotal > 0
        assert report.overhead_subtotal > 0
        assert report.total_costs == report.product_subtotal + report.overhead_subtotal


class TestCumulativeCostReport:
    """Tests for cumulative cost tracking."""

    def test_accumulate_first_week(self):
        """Test accumulating first week (no previous cumulative)."""
        calculator = CostCalculator()

        weekly = WeeklyCostReport(
            week=1,
            product_costs={
                "X": ProductCosts(product_type="X", labor=100.0),
                "Y": ProductCosts(product_type="Y", labor=200.0),
                "Z": ProductCosts(product_type="Z", labor=150.0),
            },
            overhead_costs=OverheadCosts(fixed_expense=1500.0),
            product_subtotal=450.0,
            overhead_subtotal=1500.0,
            total_costs=1950.0,
        )

        cumulative = calculator.accumulate_costs(None, weekly)

        assert cumulative.through_week == 1
        assert cumulative.product_costs["X"].labor == 100.0
        assert cumulative.overhead_costs.fixed_expense == 1500.0
        assert cumulative.total_costs == 1950.0

    def test_accumulate_multiple_weeks(self):
        """Test accumulating multiple weeks."""
        calculator = CostCalculator()

        # Week 1
        week1 = WeeklyCostReport(
            week=1,
            product_costs={
                "X": ProductCosts(product_type="X", labor=100.0, machine_repair=400.0),
                "Y": ProductCosts(product_type="Y", labor=200.0),
                "Z": ProductCosts(product_type="Z", labor=150.0),
            },
            overhead_costs=OverheadCosts(fixed_expense=1500.0, training_cost=1000.0),
            product_subtotal=850.0,
            overhead_subtotal=2500.0,
            total_costs=3350.0,
        )

        cumulative = calculator.accumulate_costs(None, week1)

        # Week 2
        week2 = WeeklyCostReport(
            week=2,
            product_costs={
                "X": ProductCosts(product_type="X", labor=120.0, machine_repair=0.0),
                "Y": ProductCosts(product_type="Y", labor=180.0, machine_repair=400.0),
                "Z": ProductCosts(product_type="Z", labor=160.0),
            },
            overhead_costs=OverheadCosts(fixed_expense=1500.0, hiring_cost=2700.0),
            product_subtotal=860.0,
            overhead_subtotal=4200.0,
            total_costs=5060.0,
        )

        cumulative = calculator.accumulate_costs(cumulative, week2)

        assert cumulative.through_week == 2
        assert cumulative.product_costs["X"].labor == 220.0  # 100 + 120
        assert cumulative.product_costs["X"].machine_repair == 400.0  # Only week 1
        assert cumulative.product_costs["Y"].machine_repair == 400.0  # Only week 2
        assert cumulative.overhead_costs.fixed_expense == 3000.0  # 1500 * 2
        assert cumulative.overhead_costs.training_cost == 1000.0  # Only week 1
        assert cumulative.overhead_costs.hiring_cost == 2700.0  # Only week 2
        assert cumulative.total_costs == 3350.0 + 5060.0


class TestIntegration:
    """Integration tests for cost calculations."""

    def test_week1_costs_match_original_structure(self):
        """Test that cost structure matches original week1.txt format."""
        calculator = CostCalculator()

        # Verify we can produce all cost categories from week1.txt
        production = create_mock_production_result(
            parts_by_type={"X'": 40.0, "Y'": 40.0, "Z'": 40.0},
            assembly_by_type={"X": 40.0, "Y": 40.0, "Z": 40.0},
        )
        inventory = create_mock_inventory(
            rm_ending=0.0,
            parts_ending={"X'": 1139.0, "Y'": 492.0, "Z'": 1517.0},
            products_ending={"X": 1472.0, "Y": 1032.0, "Z": 1317.0},
            parts_received={"X'": 600.0, "Y'": 500.0, "Z'": 400.0},
        )
        workforce = create_mock_workforce_costs(
            training=1000.0,
            hiring=2700.0,
        )

        calc_input = CostCalculationInput(
            week=1,
            production_result=production,
            inventory=inventory,
            order_book=OrderBook(),
            workforce_costs=workforce,
            quality_budget=750.0,
            maintenance_budget=500.0,
            demand_shortage={"X": 0.0, "Y": 0.0, "Z": 0.0},
            machine_repairs={"X": 0, "Y": 1, "Z": 0},
            expedited_orders_count=1,
            regular_orders_count=2,
            parts_orders_count=3,
        )

        report = calculator.calculate_weekly_costs(calc_input)

        # Verify all expected cost categories exist
        for product_type in ["X", "Y", "Z"]:
            pc = report.product_costs[product_type]
            assert hasattr(pc, "labor")
            assert hasattr(pc, "machine_setup")
            assert hasattr(pc, "machine_repair")
            assert hasattr(pc, "raw_materials")
            assert hasattr(pc, "purchased_parts")
            assert hasattr(pc, "equipment_usage")
            assert hasattr(pc, "parts_carrying")
            assert hasattr(pc, "products_carrying")
            assert hasattr(pc, "demand_penalty")

        oh = report.overhead_costs
        assert hasattr(oh, "quality_planning")
        assert hasattr(oh, "plant_maintenance")
        assert hasattr(oh, "training_cost")
        assert hasattr(oh, "hiring_cost")
        assert hasattr(oh, "layoff_firing_cost")
        assert hasattr(oh, "raw_materials_carrying")
        assert hasattr(oh, "ordering_cost")
        assert hasattr(oh, "fixed_expense")

        # Verify repair cost assigned to Y (as in week1.txt)
        assert report.product_costs["Y"].machine_repair == 400.0
