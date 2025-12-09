"""
Cost calculations for PROSIM simulation.

This module handles:
- Per-product costs (9 categories: Labor, Setup, Repair, Raw Materials,
  Purchased Parts, Equipment, Parts Carrying, Products Carrying, Demand Penalty)
- Overhead costs (8 categories: Quality, Maintenance, Training, Hiring,
  Layoff/Firing, RM Carrying, Ordering, Fixed Expense)
- Weekly and cumulative cost tracking

Cost structure from original week1.txt:
    Per-Product (X, Y, Z):
        1. Labor - productive hours * hourly rate
        2. Machine Set-Up - setup time * setup rate
        3. Machine Repair - random repairs * $400
        4. Raw Materials - production * RM cost
        5. Purchased Finished Parts - parts ordered * part cost
        6. Equipment Usage - hours * equipment rate
        7. Parts Carrying Cost - ending inventory * rate
        8. Products Carrying Cost - ending inventory * rate
        9. Demand Penalty - unfulfilled demand * penalty rate

    Overhead:
        1. Quality Planning - decision input
        2. Plant Maintenance - decision input
        3. Training Cost - $1,000 per worker trained
        4. Hiring Cost - $2,700 per new hire
        5. Layoff and Firing Cost - $200/week + $400 termination
        6. Raw Materials Carrying Cost - ending RM * rate
        7. Ordering Cost - per order cost
        8. Fixed Expense - $1,500/week
"""

from dataclasses import dataclass, field
from typing import Optional

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.engine.production import DepartmentProductionResult, ProductionResult
from prosim.engine.workforce import WorkforceCostResult
from prosim.models.inventory import Inventory
from prosim.models.orders import OrderBook


@dataclass
class ProductCosts:
    """Costs for a single product type (X, Y, or Z)."""

    product_type: str
    labor: float = 0.0
    machine_setup: float = 0.0
    machine_repair: float = 0.0
    raw_materials: float = 0.0
    purchased_parts: float = 0.0
    equipment_usage: float = 0.0
    parts_carrying: float = 0.0
    products_carrying: float = 0.0
    demand_penalty: float = 0.0

    @property
    def total(self) -> float:
        """Total cost for this product."""
        return (
            self.labor
            + self.machine_setup
            + self.machine_repair
            + self.raw_materials
            + self.purchased_parts
            + self.equipment_usage
            + self.parts_carrying
            + self.products_carrying
            + self.demand_penalty
        )


@dataclass
class OverheadCosts:
    """Overhead costs not attributed to specific products."""

    quality_planning: float = 0.0
    plant_maintenance: float = 0.0
    training_cost: float = 0.0
    hiring_cost: float = 0.0
    layoff_firing_cost: float = 0.0
    raw_materials_carrying: float = 0.0
    ordering_cost: float = 0.0
    fixed_expense: float = 0.0

    @property
    def total(self) -> float:
        """Total overhead costs."""
        return (
            self.quality_planning
            + self.plant_maintenance
            + self.training_cost
            + self.hiring_cost
            + self.layoff_firing_cost
            + self.raw_materials_carrying
            + self.ordering_cost
            + self.fixed_expense
        )


@dataclass
class WeeklyCostReport:
    """Complete cost report for a week."""

    week: int
    product_costs: dict[str, ProductCosts]  # X, Y, Z -> costs
    overhead_costs: OverheadCosts
    product_subtotal: float
    overhead_subtotal: float
    total_costs: float


@dataclass
class CumulativeCostReport:
    """Cumulative costs across all weeks."""

    through_week: int
    product_costs: dict[str, ProductCosts]  # X, Y, Z -> cumulative costs
    overhead_costs: OverheadCosts
    product_subtotal: float
    overhead_subtotal: float
    total_costs: float


@dataclass
class CostCalculationInput:
    """Input data needed for cost calculations."""

    week: int
    production_result: ProductionResult
    inventory: Inventory
    order_book: OrderBook
    workforce_costs: WorkforceCostResult
    quality_budget: float = 0.0
    maintenance_budget: float = 0.0
    demand_fulfilled: dict[str, float] = field(default_factory=dict)
    demand_shortage: dict[str, float] = field(default_factory=dict)
    expedited_orders_count: int = 0
    regular_orders_count: int = 0
    parts_orders_count: int = 0
    machine_repairs: dict[str, int] = field(default_factory=dict)  # Product type -> repair count


class CostCalculator:
    """Calculates all costs for the PROSIM simulation.

    This calculator handles:
    1. Per-product costs (allocated by product type)
    2. Overhead costs (company-wide)
    3. Weekly and cumulative tracking
    """

    def __init__(self, config: Optional[ProsimConfig] = None):
        """Initialize cost calculator.

        Args:
            config: Simulation configuration (uses defaults if None)
        """
        self.config = config or get_default_config()

    def calculate_labor_costs(
        self,
        production_result: ProductionResult,
    ) -> dict[str, float]:
        """Calculate labor costs by product type.

        Labor cost = productive hours * hourly rate

        Args:
            production_result: Production results for the week

        Returns:
            Labor costs by product type
        """
        labor_rate = self.config.costs.labor.regular_hourly
        costs: dict[str, float] = {"X": 0.0, "Y": 0.0, "Z": 0.0}

        # Parts department contributes to parts' products
        for result in production_result.parts_department.machine_results:
            if result.part_type:
                # Map part type to product type (X' -> X, etc.)
                product_type = result.part_type.replace("'", "")
                if product_type in costs:
                    costs[product_type] += result.productive_hours * labor_rate

        # Assembly department contributes directly
        for result in production_result.assembly_department.machine_results:
            if result.part_type and result.part_type in costs:
                costs[result.part_type] += result.productive_hours * labor_rate

        return costs

    def calculate_setup_costs(
        self,
        production_result: ProductionResult,
        setup_cost_per_hour: float = 40.0,
    ) -> dict[str, float]:
        """Calculate machine setup costs by product type.

        Args:
            production_result: Production results for the week
            setup_cost_per_hour: Cost per setup hour

        Returns:
            Setup costs by product type
        """
        costs: dict[str, float] = {"X": 0.0, "Y": 0.0, "Z": 0.0}

        # Parts department setup
        for result in production_result.parts_department.machine_results:
            if result.setup_hours > 0 and result.part_type:
                product_type = result.part_type.replace("'", "")
                if product_type in costs:
                    costs[product_type] += result.setup_hours * setup_cost_per_hour

        # Assembly department setup
        for result in production_result.assembly_department.machine_results:
            if result.setup_hours > 0 and result.part_type:
                if result.part_type in costs:
                    costs[result.part_type] += result.setup_hours * setup_cost_per_hour

        return costs

    def calculate_repair_costs(
        self,
        machine_repairs: dict[str, int],
    ) -> dict[str, float]:
        """Calculate machine repair costs by product type.

        Args:
            machine_repairs: Number of repairs by product type

        Returns:
            Repair costs by product type
        """
        repair_cost = self.config.equipment.repair.cost_per_repair
        return {
            product_type: count * repair_cost
            for product_type, count in machine_repairs.items()
        }

    def calculate_raw_material_costs(
        self,
        production_result: ProductionResult,
        rm_cost_per_unit: float = 1.0,
    ) -> dict[str, float]:
        """Calculate raw material costs by product type.

        Based on gross production (materials consumed regardless of rejects).

        Args:
            production_result: Production results for the week
            rm_cost_per_unit: Cost per raw material unit

        Returns:
            Raw material costs by product type
        """
        costs: dict[str, float] = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        rm_per_part = self.config.production.raw_materials_per_part

        for part_type, gross_qty in production_result.parts_department.gross_production_by_type.items():
            product_type = part_type.replace("'", "")
            if product_type in costs:
                rate = rm_per_part.get(part_type, 1.0)
                costs[product_type] += gross_qty * rate * rm_cost_per_unit

        return costs

    def calculate_purchased_parts_costs(
        self,
        orders_received: dict[str, float],
        part_costs: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Calculate purchased parts costs by product type.

        Args:
            orders_received: Parts received this week by type
            part_costs: Cost per part by type (uses defaults if None)

        Returns:
            Purchased parts costs by product type
        """
        if part_costs is None:
            # Default costs - these should be configurable
            part_costs = {"X'": 4.25, "Y'": 6.20, "Z'": 8.06}

        costs: dict[str, float] = {"X": 0.0, "Y": 0.0, "Z": 0.0}

        for part_type, qty in orders_received.items():
            product_type = part_type.replace("'", "")
            if product_type in costs and part_type in part_costs:
                costs[product_type] += qty * part_costs[part_type]

        return costs

    def calculate_equipment_costs(
        self,
        production_result: ProductionResult,
    ) -> dict[str, float]:
        """Calculate equipment usage costs by product type.

        Args:
            production_result: Production results for the week

        Returns:
            Equipment costs by product type
        """
        costs: dict[str, float] = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        rates = self.config.equipment.rates

        # Parts department
        for result in production_result.parts_department.machine_results:
            if result.part_type:
                product_type = result.part_type.replace("'", "")
                if product_type in costs:
                    costs[product_type] += result.productive_hours * rates.parts_department

        # Assembly department
        for result in production_result.assembly_department.machine_results:
            if result.part_type and result.part_type in costs:
                costs[result.part_type] += result.productive_hours * rates.assembly_department

        return costs

    def calculate_parts_carrying_costs(
        self,
        inventory: Inventory,
    ) -> dict[str, float]:
        """Calculate parts inventory carrying costs by product type.

        Args:
            inventory: Current inventory state

        Returns:
            Parts carrying costs by product type
        """
        rate = self.config.costs.carrying.parts
        return {
            "X": inventory.parts.x_prime.ending * rate,
            "Y": inventory.parts.y_prime.ending * rate,
            "Z": inventory.parts.z_prime.ending * rate,
        }

    def calculate_products_carrying_costs(
        self,
        inventory: Inventory,
    ) -> dict[str, float]:
        """Calculate products inventory carrying costs by product type.

        Args:
            inventory: Current inventory state

        Returns:
            Products carrying costs by product type
        """
        rate = self.config.costs.carrying.products
        return {
            "X": inventory.products.x.ending * rate,
            "Y": inventory.products.y.ending * rate,
            "Z": inventory.products.z.ending * rate,
        }

    def calculate_demand_penalty(
        self,
        demand_shortage: dict[str, float],
        penalty_per_unit: float = 10.0,
    ) -> dict[str, float]:
        """Calculate demand penalty costs by product type.

        Args:
            demand_shortage: Unfulfilled demand by product type
            penalty_per_unit: Penalty per unit of unfulfilled demand

        Returns:
            Demand penalty costs by product type
        """
        return {
            product_type: shortage * penalty_per_unit
            for product_type, shortage in demand_shortage.items()
        }

    def calculate_raw_materials_carrying(
        self,
        inventory: Inventory,
    ) -> float:
        """Calculate raw materials carrying cost.

        Args:
            inventory: Current inventory state

        Returns:
            Raw materials carrying cost
        """
        rate = self.config.costs.carrying.raw_materials
        return inventory.raw_materials.ending * rate

    def calculate_ordering_cost(
        self,
        expedited_count: int,
        regular_count: int,
        parts_count: int,
        cost_per_order: float = 100.0,
        expedited_surcharge: float = 1200.0,
    ) -> float:
        """Calculate ordering costs.

        Args:
            expedited_count: Number of expedited RM orders
            regular_count: Number of regular RM orders
            parts_count: Number of parts orders
            cost_per_order: Base cost per order
            expedited_surcharge: Additional cost for expedited orders

        Returns:
            Total ordering cost
        """
        base_cost = (expedited_count + regular_count + parts_count) * cost_per_order
        expedited_cost = expedited_count * expedited_surcharge
        return base_cost + expedited_cost

    def calculate_product_costs(
        self,
        calc_input: CostCalculationInput,
    ) -> dict[str, ProductCosts]:
        """Calculate all per-product costs.

        Args:
            calc_input: All input data for cost calculations

        Returns:
            ProductCosts for each product type
        """
        # Calculate each cost category
        labor = self.calculate_labor_costs(calc_input.production_result)
        setup = self.calculate_setup_costs(calc_input.production_result)
        repair = self.calculate_repair_costs(calc_input.machine_repairs)
        raw_materials = self.calculate_raw_material_costs(calc_input.production_result)

        # Get parts received this week
        parts_received = {
            "X'": calc_input.inventory.parts.x_prime.orders_received,
            "Y'": calc_input.inventory.parts.y_prime.orders_received,
            "Z'": calc_input.inventory.parts.z_prime.orders_received,
        }
        purchased_parts = self.calculate_purchased_parts_costs(parts_received)

        equipment = self.calculate_equipment_costs(calc_input.production_result)
        parts_carrying = self.calculate_parts_carrying_costs(calc_input.inventory)
        products_carrying = self.calculate_products_carrying_costs(calc_input.inventory)
        demand_penalty = self.calculate_demand_penalty(calc_input.demand_shortage)

        # Assemble costs for each product type
        result = {}
        for product_type in ["X", "Y", "Z"]:
            result[product_type] = ProductCosts(
                product_type=product_type,
                labor=labor.get(product_type, 0.0),
                machine_setup=setup.get(product_type, 0.0),
                machine_repair=repair.get(product_type, 0.0),
                raw_materials=raw_materials.get(product_type, 0.0),
                purchased_parts=purchased_parts.get(product_type, 0.0),
                equipment_usage=equipment.get(product_type, 0.0),
                parts_carrying=parts_carrying.get(product_type, 0.0),
                products_carrying=products_carrying.get(product_type, 0.0),
                demand_penalty=demand_penalty.get(product_type, 0.0),
            )

        return result

    def calculate_overhead_costs(
        self,
        calc_input: CostCalculationInput,
    ) -> OverheadCosts:
        """Calculate all overhead costs.

        Args:
            calc_input: All input data for cost calculations

        Returns:
            OverheadCosts for the week
        """
        rm_carrying = self.calculate_raw_materials_carrying(calc_input.inventory)
        ordering = self.calculate_ordering_cost(
            calc_input.expedited_orders_count,
            calc_input.regular_orders_count,
            calc_input.parts_orders_count,
        )

        return OverheadCosts(
            quality_planning=calc_input.quality_budget,
            plant_maintenance=calc_input.maintenance_budget,
            training_cost=calc_input.workforce_costs.training_cost,
            hiring_cost=calc_input.workforce_costs.hiring_cost,
            layoff_firing_cost=(
                calc_input.workforce_costs.layoff_cost
                + calc_input.workforce_costs.termination_cost
            ),
            raw_materials_carrying=rm_carrying,
            ordering_cost=ordering,
            fixed_expense=self.config.costs.fixed.fixed_expense_per_week,
        )

    def calculate_weekly_costs(
        self,
        calc_input: CostCalculationInput,
    ) -> WeeklyCostReport:
        """Calculate all costs for a week.

        This is the main entry point for weekly cost calculations.

        Args:
            calc_input: All input data for cost calculations

        Returns:
            WeeklyCostReport with all costs
        """
        product_costs = self.calculate_product_costs(calc_input)
        overhead_costs = self.calculate_overhead_costs(calc_input)

        product_subtotal = sum(pc.total for pc in product_costs.values())
        overhead_subtotal = overhead_costs.total
        total = product_subtotal + overhead_subtotal

        return WeeklyCostReport(
            week=calc_input.week,
            product_costs=product_costs,
            overhead_costs=overhead_costs,
            product_subtotal=product_subtotal,
            overhead_subtotal=overhead_subtotal,
            total_costs=total,
        )

    def accumulate_costs(
        self,
        current_cumulative: Optional[CumulativeCostReport],
        weekly_report: WeeklyCostReport,
    ) -> CumulativeCostReport:
        """Add weekly costs to cumulative totals.

        Args:
            current_cumulative: Current cumulative totals (None for first week)
            weekly_report: This week's cost report

        Returns:
            Updated cumulative cost report
        """
        if current_cumulative is None:
            # First week - cumulative equals weekly
            return CumulativeCostReport(
                through_week=weekly_report.week,
                product_costs={
                    pt: ProductCosts(
                        product_type=pt,
                        labor=pc.labor,
                        machine_setup=pc.machine_setup,
                        machine_repair=pc.machine_repair,
                        raw_materials=pc.raw_materials,
                        purchased_parts=pc.purchased_parts,
                        equipment_usage=pc.equipment_usage,
                        parts_carrying=pc.parts_carrying,
                        products_carrying=pc.products_carrying,
                        demand_penalty=pc.demand_penalty,
                    )
                    for pt, pc in weekly_report.product_costs.items()
                },
                overhead_costs=OverheadCosts(
                    quality_planning=weekly_report.overhead_costs.quality_planning,
                    plant_maintenance=weekly_report.overhead_costs.plant_maintenance,
                    training_cost=weekly_report.overhead_costs.training_cost,
                    hiring_cost=weekly_report.overhead_costs.hiring_cost,
                    layoff_firing_cost=weekly_report.overhead_costs.layoff_firing_cost,
                    raw_materials_carrying=weekly_report.overhead_costs.raw_materials_carrying,
                    ordering_cost=weekly_report.overhead_costs.ordering_cost,
                    fixed_expense=weekly_report.overhead_costs.fixed_expense,
                ),
                product_subtotal=weekly_report.product_subtotal,
                overhead_subtotal=weekly_report.overhead_subtotal,
                total_costs=weekly_report.total_costs,
            )

        # Add weekly to cumulative
        new_product_costs = {}
        for pt in ["X", "Y", "Z"]:
            curr = current_cumulative.product_costs[pt]
            week = weekly_report.product_costs[pt]
            new_product_costs[pt] = ProductCosts(
                product_type=pt,
                labor=curr.labor + week.labor,
                machine_setup=curr.machine_setup + week.machine_setup,
                machine_repair=curr.machine_repair + week.machine_repair,
                raw_materials=curr.raw_materials + week.raw_materials,
                purchased_parts=curr.purchased_parts + week.purchased_parts,
                equipment_usage=curr.equipment_usage + week.equipment_usage,
                parts_carrying=curr.parts_carrying + week.parts_carrying,
                products_carrying=curr.products_carrying + week.products_carrying,
                demand_penalty=curr.demand_penalty + week.demand_penalty,
            )

        curr_oh = current_cumulative.overhead_costs
        week_oh = weekly_report.overhead_costs
        new_overhead = OverheadCosts(
            quality_planning=curr_oh.quality_planning + week_oh.quality_planning,
            plant_maintenance=curr_oh.plant_maintenance + week_oh.plant_maintenance,
            training_cost=curr_oh.training_cost + week_oh.training_cost,
            hiring_cost=curr_oh.hiring_cost + week_oh.hiring_cost,
            layoff_firing_cost=curr_oh.layoff_firing_cost + week_oh.layoff_firing_cost,
            raw_materials_carrying=curr_oh.raw_materials_carrying + week_oh.raw_materials_carrying,
            ordering_cost=curr_oh.ordering_cost + week_oh.ordering_cost,
            fixed_expense=curr_oh.fixed_expense + week_oh.fixed_expense,
        )

        new_product_subtotal = sum(pc.total for pc in new_product_costs.values())
        new_overhead_subtotal = new_overhead.total

        return CumulativeCostReport(
            through_week=weekly_report.week,
            product_costs=new_product_costs,
            overhead_costs=new_overhead,
            product_subtotal=new_product_subtotal,
            overhead_subtotal=new_overhead_subtotal,
            total_costs=new_product_subtotal + new_overhead_subtotal,
        )
