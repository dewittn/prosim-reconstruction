"""
Main simulation engine for PROSIM.

This module orchestrates all the component engines to process a complete
week of simulation:
1. Apply decisions from DECS file
2. Process workforce operations (training, hiring)
3. Receive due orders
4. Place new orders
5. Calculate production (Parts and Assembly departments)
6. Update inventory (consumption, production, shipping)
7. Calculate costs
8. Generate weekly report
9. Advance to next week

The simulation maintains state across weeks and tracks cumulative metrics.
"""

import random
from dataclasses import dataclass, field
from typing import Optional

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.engine.costs import (
    CostCalculationInput,
    CostCalculator,
    CumulativeCostReport,
    OverheadCosts as EngineOverheadCosts,
    ProductCosts as EngineProductCosts,
    WeeklyCostReport,
)
from prosim.engine.demand import DemandManager, ShippingPeriodDemand
from prosim.engine.inventory import DemandFulfillmentResult, InventoryManager
from prosim.engine.production import ProductionEngine, ProductionInput, ProductionResult
from prosim.engine.workforce import (
    OperatorEfficiencyResult,
    OperatorManager,
    TrainingResult,
    WorkforceCostResult,
    WorkforceSchedulingResult,
)
from prosim.models.company import Company
from prosim.models.decisions import Decisions
from prosim.models.inventory import Inventory
from prosim.models.machines import MachineFloor, part_type_from_code
from prosim.models.operators import Department, Workforce
from prosim.models.orders import DemandSchedule, OrderBook
from prosim.models.report import (
    CostReport,
    DemandReport,
    InventoryReport,
    MachineProduction,
    OverheadCosts,
    PartsReport,
    PendingOrderReport,
    PerformanceMetrics,
    ProductCosts,
    ProductionReport,
    ProductsReport,
    RawMaterialsReport,
    WeeklyReport,
)


@dataclass
class SimulationWeekResult:
    """Results from processing a single week of simulation."""

    week: int
    company_id: int

    # Component results
    training_result: TrainingResult
    scheduling_result: WorkforceSchedulingResult
    production_result: ProductionResult
    workforce_cost_result: WorkforceCostResult
    weekly_cost_report: WeeklyCostReport
    cumulative_cost_report: CumulativeCostReport

    # Shipping results (only on shipping weeks)
    shipping_demand: Optional[ShippingPeriodDemand] = None
    fulfillment_result: Optional[DemandFulfillmentResult] = None

    # Updated state
    updated_company: Company = field(default=None)  # type: ignore
    weekly_report: WeeklyReport = field(default=None)  # type: ignore


class Simulation:
    """Main simulation engine that orchestrates all component engines.

    This class manages the complete simulation flow for a PROSIM game.
    It coordinates inventory, workforce, production, costs, and demand
    across simulation weeks.

    Usage:
        simulation = Simulation()
        company = Company.create_new(company_id=1)
        decisions = parse_decs("DECS01.DAT")

        result = simulation.process_week(company, decisions)
        # result.updated_company contains the new state
        # result.weekly_report contains the generated report
    """

    def __init__(
        self,
        config: Optional[ProsimConfig] = None,
        random_seed: Optional[int] = None,
    ):
        """Initialize the simulation engine.

        Args:
            config: Simulation configuration (uses defaults if None)
            random_seed: Random seed for reproducible simulations
        """
        self.config = config or get_default_config()
        self._random_seed = random_seed
        self._rng = random.Random(random_seed)

        # Initialize component engines
        self.inventory_manager = InventoryManager(config=self.config)
        self.operator_manager = OperatorManager(
            config=self.config, random_seed=random_seed
        )
        self.production_engine = ProductionEngine(config=self.config)
        self.cost_calculator = CostCalculator(config=self.config)
        self.demand_manager = DemandManager(
            config=self.config, random_seed=random_seed
        )

        # Cumulative tracking
        self._cumulative_costs: Optional[CumulativeCostReport] = None

    def set_random_seed(self, seed: Optional[int]) -> None:
        """Set random seed for reproducible simulations.

        Args:
            seed: Random seed (None for system random)
        """
        self._random_seed = seed
        self._rng = random.Random(seed)
        if seed is not None:
            self.operator_manager.set_random_seed(seed)
        self.demand_manager.set_random_seed(seed)

    def apply_decisions_to_machines(
        self,
        machine_floor: MachineFloor,
        decisions: Decisions,
    ) -> MachineFloor:
        """Apply DECS decisions to machine floor.

        Args:
            machine_floor: Current machine floor state
            decisions: Decisions from DECS file

        Returns:
            Updated MachineFloor with assignments applied
        """
        updated_floor = machine_floor

        for md in decisions.machine_decisions:
            machine = updated_floor.get_machine(md.machine_id)
            if machine is None:
                continue

            # Determine part type based on department
            part_type = part_type_from_code(md.part_type, machine.department)

            # Apply assignment
            if md.send_for_training:
                # Clear assignment if being sent for training
                updated_machine = machine.assign(
                    operator_id=md.machine_id,  # Operator ID = machine ID convention
                    part_type=part_type,
                    scheduled_hours=0.0,
                    send_for_training=True,
                )
            else:
                updated_machine = machine.assign(
                    operator_id=md.machine_id,
                    part_type=part_type,
                    scheduled_hours=md.scheduled_hours,
                    send_for_training=False,
                )

            updated_floor = updated_floor.update_machine(updated_machine)

        return updated_floor

    def determine_machine_repairs(
        self,
        machine_floor: MachineFloor,
    ) -> dict[str, int]:
        """Randomly determine which machines need repair.

        Args:
            machine_floor: Current machine floor

        Returns:
            Repair counts by product type
        """
        repairs: dict[str, int] = {"X": 0, "Y": 0, "Z": 0}
        repair_probability = self.config.equipment.repair.probability_per_machine_per_week

        for machine in machine_floor.assigned_machines:
            if self._rng.random() < repair_probability:
                # Determine product type for cost attribution
                if machine.assignment and machine.assignment.part_type:
                    # Strip prime from part type for product association
                    product_type = machine.assignment.part_type.replace("'", "")
                    if product_type in repairs:
                        repairs[product_type] += 1

        return repairs

    def build_production_inputs(
        self,
        machine_floor: MachineFloor,
        efficiency_results: dict[int, OperatorEfficiencyResult],
    ) -> list[ProductionInput]:
        """Build production inputs from machine floor and efficiency results.

        Args:
            machine_floor: Machine floor with assignments
            efficiency_results: Map of operator_id to efficiency result

        Returns:
            List of ProductionInput for production calculations
        """
        inputs = []
        for machine in machine_floor.machines.values():
            efficiency_result = None
            if machine.assignment and machine.assignment.operator_id:
                efficiency_result = efficiency_results.get(
                    machine.assignment.operator_id
                )
            inputs.append(
                ProductionInput(machine=machine, efficiency_result=efficiency_result)
            )
        return inputs

    def build_inventory_report(
        self,
        inventory: Inventory,
        production_result: ProductionResult,
    ) -> InventoryReport:
        """Build inventory report from current state.

        Args:
            inventory: Current inventory state
            production_result: Production results for the week

        Returns:
            InventoryReport for the weekly report
        """
        rm = inventory.raw_materials
        raw_materials = RawMaterialsReport(
            beginning_inventory=rm.beginning,
            orders_received=rm.orders_received,
            used_in_production=rm.used_in_production,
            ending_inventory=rm.ending,
        )

        # Get production by part type
        parts_production = production_result.parts_department.net_production_by_type
        products_production = production_result.assembly_department.net_production_by_type

        parts_x = PartsReport(
            part_type="X'",
            beginning_inventory=inventory.parts.x_prime.beginning,
            orders_received=inventory.parts.x_prime.orders_received,
            used_in_production=inventory.parts.x_prime.used_in_assembly,
            production_this_week=parts_production.get("X'", 0.0),
            ending_inventory=inventory.parts.x_prime.ending,
        )
        parts_y = PartsReport(
            part_type="Y'",
            beginning_inventory=inventory.parts.y_prime.beginning,
            orders_received=inventory.parts.y_prime.orders_received,
            used_in_production=inventory.parts.y_prime.used_in_assembly,
            production_this_week=parts_production.get("Y'", 0.0),
            ending_inventory=inventory.parts.y_prime.ending,
        )
        parts_z = PartsReport(
            part_type="Z'",
            beginning_inventory=inventory.parts.z_prime.beginning,
            orders_received=inventory.parts.z_prime.orders_received,
            used_in_production=inventory.parts.z_prime.used_in_assembly,
            production_this_week=parts_production.get("Z'", 0.0),
            ending_inventory=inventory.parts.z_prime.ending,
        )

        products_x = ProductsReport(
            product_type="X",
            beginning_inventory=inventory.products.x.beginning,
            production_this_week=products_production.get("X", 0.0),
            demand_this_week=inventory.products.x.demand_fulfilled,
            ending_inventory=inventory.products.x.ending,
        )
        products_y = ProductsReport(
            product_type="Y",
            beginning_inventory=inventory.products.y.beginning,
            production_this_week=products_production.get("Y", 0.0),
            demand_this_week=inventory.products.y.demand_fulfilled,
            ending_inventory=inventory.products.y.ending,
        )
        products_z = ProductsReport(
            product_type="Z",
            beginning_inventory=inventory.products.z.beginning,
            production_this_week=products_production.get("Z", 0.0),
            demand_this_week=inventory.products.z.demand_fulfilled,
            ending_inventory=inventory.products.z.ending,
        )

        return InventoryReport(
            raw_materials=raw_materials,
            parts_x=parts_x,
            parts_y=parts_y,
            parts_z=parts_z,
            products_x=products_x,
            products_y=products_y,
            products_z=products_z,
        )

    def build_production_report(
        self,
        production_result: ProductionResult,
    ) -> ProductionReport:
        """Build production report from production results.

        Args:
            production_result: Production results for the week

        Returns:
            ProductionReport for the weekly report
        """
        parts_machines = []
        for mr in production_result.parts_department.machine_results:
            parts_machines.append(
                MachineProduction(
                    machine_id=mr.machine_id,
                    operator_id=mr.operator_id or mr.machine_id,
                    part_type=mr.part_type or "X'",
                    scheduled_hours=mr.scheduled_hours,
                    productive_hours=mr.productive_hours,
                    production=mr.gross_production,
                    rejects=mr.rejects,
                )
            )

        assembly_machines = []
        for mr in production_result.assembly_department.machine_results:
            assembly_machines.append(
                MachineProduction(
                    machine_id=mr.machine_id,
                    operator_id=mr.operator_id or mr.machine_id,
                    part_type=mr.part_type or "X",
                    scheduled_hours=mr.scheduled_hours,
                    productive_hours=mr.productive_hours,
                    production=mr.gross_production,
                    rejects=mr.rejects,
                )
            )

        return ProductionReport(
            parts_department=parts_machines,
            assembly_department=assembly_machines,
        )

    def build_pending_orders_report(
        self,
        order_book: OrderBook,
        current_week: int,
    ) -> list[PendingOrderReport]:
        """Build pending orders report from order book.

        Args:
            order_book: Current order book
            current_week: Current simulation week

        Returns:
            List of PendingOrderReport for the weekly report
        """
        pending = []
        order_type_map = {
            "raw_materials_regular": "Raw Materials (Reg)",
            "raw_materials_expedited": "Raw Materials (Exp)",
            "parts_X'": "Finished Part X'",
            "parts_Y'": "Finished Part Y'",
            "parts_Z'": "Finished Part Z'",
        }

        for order in order_book.orders:
            order_type_str = order_type_map.get(
                order.order_type.value, str(order.order_type)
            )
            pending.append(
                PendingOrderReport(
                    order_type=order_type_str,
                    week_due=order.week_due,
                    amount=order.amount,
                )
            )

        return pending

    def build_demand_reports(
        self,
        demand_schedule: DemandSchedule,
        current_week: int,
    ) -> tuple[DemandReport, DemandReport, DemandReport]:
        """Build demand reports from schedule.

        Args:
            demand_schedule: Current demand schedule
            current_week: Current simulation week

        Returns:
            Tuple of (demand_x, demand_y, demand_z) reports
        """
        next_shipping = self.demand_manager.next_shipping_week(current_week)
        forecasts = demand_schedule.get_forecasts_for_week(next_shipping)

        # Build forecast map
        forecast_map = {f.product_type: f for f in forecasts}

        def make_demand_report(product_type: str) -> DemandReport:
            forecast = forecast_map.get(product_type)
            if forecast:
                actual_or_estimate = (
                    forecast.actual_demand
                    if forecast.actual_demand is not None
                    else forecast.estimated_demand
                )
                return DemandReport(
                    product_type=product_type,
                    estimated_demand=actual_or_estimate,
                    carryover=forecast.carryover,
                    total_demand=actual_or_estimate + forecast.carryover,
                )
            return DemandReport(
                product_type=product_type,
                estimated_demand=0.0,
                carryover=0.0,
                total_demand=0.0,
            )

        return (
            make_demand_report("X"),
            make_demand_report("Y"),
            make_demand_report("Z"),
        )

    def build_cost_report(
        self,
        weekly_costs: WeeklyCostReport,
    ) -> CostReport:
        """Build cost report model from engine cost report.

        Args:
            weekly_costs: Weekly cost report from engine

        Returns:
            CostReport model for weekly report
        """
        def to_model_costs(pc: EngineProductCosts) -> ProductCosts:
            return ProductCosts(
                product_type=pc.product_type,
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

        def to_model_overhead(
            oh: EngineOverheadCosts,
        ) -> OverheadCosts:
            return OverheadCosts(
                quality_planning=oh.quality_planning,
                plant_maintenance=oh.plant_maintenance,
                training_cost=oh.training_cost,
                hiring_cost=oh.hiring_cost,
                layoff_firing_cost=oh.layoff_firing_cost,
                raw_materials_carrying=oh.raw_materials_carrying,
                ordering_cost=oh.ordering_cost,
                fixed_expense=oh.fixed_expense,
            )

        return CostReport(
            x_costs=to_model_costs(weekly_costs.product_costs["X"]),
            y_costs=to_model_costs(weekly_costs.product_costs["Y"]),
            z_costs=to_model_costs(weekly_costs.product_costs["Z"]),
            overhead=to_model_overhead(weekly_costs.overhead_costs),
        )

    def build_cumulative_cost_report(
        self,
        cumulative_costs: CumulativeCostReport,
    ) -> CostReport:
        """Build cost report model from cumulative cost report.

        Args:
            cumulative_costs: Cumulative cost report from engine

        Returns:
            CostReport model for weekly report
        """
        def to_model_costs(pc: EngineProductCosts) -> ProductCosts:
            return ProductCosts(
                product_type=pc.product_type,
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

        def to_model_overhead(
            oh: EngineOverheadCosts,
        ) -> OverheadCosts:
            return OverheadCosts(
                quality_planning=oh.quality_planning,
                plant_maintenance=oh.plant_maintenance,
                training_cost=oh.training_cost,
                hiring_cost=oh.hiring_cost,
                layoff_firing_cost=oh.layoff_firing_cost,
                raw_materials_carrying=oh.raw_materials_carrying,
                ordering_cost=oh.ordering_cost,
                fixed_expense=oh.fixed_expense,
            )

        return CostReport(
            x_costs=to_model_costs(cumulative_costs.product_costs["X"]),
            y_costs=to_model_costs(cumulative_costs.product_costs["Y"]),
            z_costs=to_model_costs(cumulative_costs.product_costs["Z"]),
            overhead=to_model_overhead(cumulative_costs.overhead_costs),
        )

    def calculate_performance_metrics(
        self,
        production_result: ProductionResult,
        weekly_costs: WeeklyCostReport,
        fulfillment_result: Optional[DemandFulfillmentResult],
    ) -> PerformanceMetrics:
        """Calculate weekly performance metrics.

        Args:
            production_result: Production results for the week
            weekly_costs: Weekly cost report
            fulfillment_result: Demand fulfillment result (if shipping week)

        Returns:
            PerformanceMetrics for the week
        """
        # Standard costs calculation (simplified - based on production rates)
        # In a more complete implementation, this would use standard cost per unit
        total_production = production_result.total_net_production
        standard_cost_estimate = (
            total_production * 10.0  # Placeholder standard cost per unit
        )

        actual_costs = weekly_costs.total_costs

        # Efficiency percentage
        if actual_costs > 0:
            efficiency = (standard_cost_estimate / actual_costs) * 100
        else:
            efficiency = 100.0

        # Variance per unit
        if total_production > 0:
            variance = (actual_costs - standard_cost_estimate) / total_production
        else:
            variance = 0.0

        # On-time delivery (only on shipping weeks)
        on_time_delivery = None
        if fulfillment_result:
            total_demand = sum(
                fulfillment_result.units_shipped.get(p, 0)
                + fulfillment_result.units_short.get(p, 0)
                for p in ["X", "Y", "Z"]
            )
            total_shipped = sum(fulfillment_result.units_shipped.values())
            if total_demand > 0:
                on_time_delivery = (total_shipped / total_demand) * 100

        return PerformanceMetrics(
            total_standard_costs=standard_cost_estimate,
            total_actual_costs=actual_costs,
            percent_efficiency=efficiency,
            variance_per_unit=variance,
            on_time_delivery=on_time_delivery,
        )

    def process_week(
        self,
        company: Company,
        decisions: Decisions,
    ) -> SimulationWeekResult:
        """Process a complete week of simulation.

        This is the main entry point for simulation processing.

        Args:
            company: Current company state
            decisions: Decisions from DECS file

        Returns:
            SimulationWeekResult with updated state and report
        """
        current_week = company.current_week

        # Validate decisions match company week
        if decisions.week != current_week:
            raise ValueError(
                f"Decisions week {decisions.week} doesn't match "
                f"company week {current_week}"
            )

        # Initialize demand schedule if needed
        demand_schedule = company.demand
        if not demand_schedule.forecasts:
            demand_schedule = self.demand_manager.initialize_demand_schedule(
                start_week=current_week,
                periods_ahead=2,
            )

        # 1. Apply decisions to machine floor
        machine_floor = self.apply_decisions_to_machines(
            company.machines, decisions
        )

        # 2. Process workforce start of week
        operators_to_train = decisions.operators_training
        workforce, training_result, hired_operators = (
            self.operator_manager.process_week_start(
                company.workforce,
                operators_to_train=operators_to_train,
                operators_to_hire=0,  # Hiring based on decisions not implemented yet
            )
        )

        # 3. Schedule operators based on machine assignments
        workforce, scheduling_result = self.operator_manager.schedule_operators(
            workforce, list(machine_floor.machines.values())
        )

        # 4. Receive due orders
        inventory = company.inventory
        order_book = company.orders
        inventory, order_book, receipt_result = self.inventory_manager.receive_orders(
            inventory, order_book, current_week
        )

        # 5. Place new orders from decisions
        order_book = self.inventory_manager.place_orders(
            order_book,
            current_week,
            raw_materials_regular=decisions.raw_materials_regular,
            raw_materials_expedited=decisions.raw_materials_expedited,
            parts_x_prime=decisions.part_orders.x_prime,
            parts_y_prime=decisions.part_orders.y_prime,
            parts_z_prime=decisions.part_orders.z_prime,
        )

        # Count orders for cost calculation
        regular_orders = 1 if decisions.raw_materials_regular > 0 else 0
        expedited_orders = 1 if decisions.raw_materials_expedited > 0 else 0
        parts_orders = sum(
            1
            for p in [
                decisions.part_orders.x_prime,
                decisions.part_orders.y_prime,
                decisions.part_orders.z_prime,
            ]
            if p > 0
        )

        # 6. Build efficiency results map
        efficiency_map: dict[int, OperatorEfficiencyResult] = {
            er.operator_id: er for er in scheduling_result.scheduled_operators
        }

        # 7. Calculate production
        production_inputs = self.build_production_inputs(machine_floor, efficiency_map)
        production_result = self.production_engine.calculate_production(production_inputs)

        # 8. Update machine floor with production results
        machine_floor = self.production_engine.update_machine_floor_after_production(
            machine_floor, production_result
        )

        # 9. Consume raw materials for parts production
        gross_parts = production_result.parts_department.gross_production_by_type
        inventory, _ = self.inventory_manager.consume_raw_materials(
            inventory, gross_parts
        )

        # 10. Add parts production to inventory
        net_parts = production_result.parts_department.net_production_by_type
        inventory = self.inventory_manager.add_parts_production(inventory, net_parts)

        # 11. Consume parts for assembly
        gross_products = production_result.assembly_department.gross_production_by_type
        inventory, _ = self.inventory_manager.consume_parts(inventory, gross_products)

        # 12. Add products to inventory
        net_products = production_result.assembly_department.net_production_by_type
        inventory = self.inventory_manager.add_products_production(
            inventory, net_products
        )

        # 13. Handle shipping week demand
        shipping_demand: Optional[ShippingPeriodDemand] = None
        fulfillment_result: Optional[DemandFulfillmentResult] = None
        demand_shortage: dict[str, float] = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        carryover: dict[str, float] = {"X": 0.0, "Y": 0.0, "Z": 0.0}

        if self.demand_manager.is_shipping_week(current_week):
            # Get demand for this shipping week
            demand = self.demand_manager.get_demand_for_week(
                demand_schedule, current_week
            )
            if demand:
                # Fulfill demand from inventory
                inventory, fulfillment_result = self.inventory_manager.fulfill_demand(
                    inventory, demand
                )

                # Process shipping in demand manager
                demand_schedule, shipping_demand, carryover = (
                    self.demand_manager.process_shipping_week(
                        demand_schedule,
                        current_week,
                        fulfillment_result.units_shipped,
                    )
                )

                # Calculate shortage for penalty
                demand_shortage = self.demand_manager.calculate_demand_penalty_units(
                    demand, fulfillment_result.units_shipped
                )

            # Add forecasts for next period
            demand_schedule = self.demand_manager.add_next_period_forecasts(
                demand_schedule, current_week, carryover
            )

        # 14. Determine machine repairs
        machine_repairs = self.determine_machine_repairs(machine_floor)

        # 15. Process workforce end of week (terminations)
        workforce, terminated_ids = self.operator_manager.process_week_end(workforce)

        # 16. Calculate workforce costs
        workforce_costs = self.operator_manager.calculate_weekly_costs(
            workforce,
            operators_hired=len(hired_operators),
            operators_trained=len(training_result.operators_sent_to_training),
            operators_terminated=terminated_ids,
        )

        # 17. Calculate all costs
        cost_input = CostCalculationInput(
            week=current_week,
            production_result=production_result,
            inventory=inventory,
            order_book=order_book,
            workforce_costs=workforce_costs,
            quality_budget=decisions.quality_budget,
            maintenance_budget=decisions.maintenance_budget,
            demand_fulfilled={
                p: fulfillment_result.units_shipped.get(p, 0.0)
                if fulfillment_result
                else 0.0
                for p in ["X", "Y", "Z"]
            },
            demand_shortage=demand_shortage,
            expedited_orders_count=expedited_orders,
            regular_orders_count=regular_orders,
            parts_orders_count=parts_orders,
            machine_repairs=machine_repairs,
        )

        weekly_cost_report = self.cost_calculator.calculate_weekly_costs(cost_input)
        cumulative_cost_report = self.cost_calculator.accumulate_costs(
            self._cumulative_costs, weekly_cost_report
        )
        self._cumulative_costs = cumulative_cost_report

        # 18. Build weekly report
        demand_x, demand_y, demand_z = self.build_demand_reports(
            demand_schedule, current_week
        )

        weekly_performance = self.calculate_performance_metrics(
            production_result, weekly_cost_report, fulfillment_result
        )

        # Calculate cumulative performance (simplified)
        cumulative_performance = PerformanceMetrics(
            total_standard_costs=cumulative_cost_report.total_costs * 0.8,  # Estimate
            total_actual_costs=cumulative_cost_report.total_costs,
            percent_efficiency=weekly_performance.percent_efficiency,
            variance_per_unit=weekly_performance.variance_per_unit,
            on_time_delivery=weekly_performance.on_time_delivery,
        )

        weekly_report = WeeklyReport(
            week=current_week,
            company_id=company.company_id,
            weekly_costs=self.build_cost_report(weekly_cost_report),
            cumulative_costs=self.build_cumulative_cost_report(cumulative_cost_report),
            production=self.build_production_report(production_result),
            inventory=self.build_inventory_report(inventory, production_result),
            pending_orders=self.build_pending_orders_report(order_book, current_week),
            demand_x=demand_x,
            demand_y=demand_y,
            demand_z=demand_z,
            weekly_performance=weekly_performance,
            cumulative_performance=cumulative_performance,
        )

        # 19. Update company state
        updated_company = company.model_copy(
            update={
                "inventory": inventory,
                "machines": machine_floor,
                "workforce": workforce,
                "orders": order_book,
                "demand": demand_schedule,
                "total_costs": company.total_costs + weekly_cost_report.total_costs,
            }
        )

        # Add report and advance week
        updated_company = updated_company.add_report(weekly_report)
        updated_company = updated_company.advance_week()

        return SimulationWeekResult(
            week=current_week,
            company_id=company.company_id,
            training_result=training_result,
            scheduling_result=scheduling_result,
            production_result=production_result,
            workforce_cost_result=workforce_costs,
            weekly_cost_report=weekly_cost_report,
            cumulative_cost_report=cumulative_cost_report,
            shipping_demand=shipping_demand,
            fulfillment_result=fulfillment_result,
            updated_company=updated_company,
            weekly_report=weekly_report,
        )

    def reset(self) -> None:
        """Reset simulation state for a new game."""
        self._cumulative_costs = None
        if self._random_seed is not None:
            self.set_random_seed(self._random_seed)


def run_simulation(
    company: Company,
    decisions_list: list[Decisions],
    config: Optional[ProsimConfig] = None,
    random_seed: Optional[int] = None,
) -> list[SimulationWeekResult]:
    """Run simulation for multiple weeks.

    Convenience function to process multiple weeks of decisions.

    Args:
        company: Initial company state
        decisions_list: List of decisions for each week
        config: Simulation configuration
        random_seed: Random seed for reproducibility

    Returns:
        List of SimulationWeekResult for each week
    """
    simulation = Simulation(config=config, random_seed=random_seed)
    results = []
    current_company = company

    for decisions in decisions_list:
        result = simulation.process_week(current_company, decisions)
        results.append(result)
        current_company = result.updated_company

    return results
