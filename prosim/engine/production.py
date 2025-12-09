"""
Production engine for PROSIM simulation.

This module handles:
- Parts Department production (X', Y', Z')
- Assembly Department production (X, Y, Z)
- Setup time calculations when changing part types
- Reject rate application
- Production output tracking by machine and department

Production flow:
    Raw Materials → Parts Department → Parts (with rejects)
    Parts → Assembly Department → Products (with rejects)

Production Formula:
    Productive Hours = (Scheduled Hours - Setup Time) * Operator Efficiency
    Gross Production = Productive Hours * Production Rate
    Rejects = Gross Production * Reject Rate
    Net Production = Gross Production - Rejects
"""

from dataclasses import dataclass, field
from typing import Optional

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.engine.workforce import OperatorEfficiencyResult
from prosim.models.machines import Machine, MachineFloor
from prosim.models.operators import Department


@dataclass
class MachineProductionResult:
    """Production result for a single machine."""

    machine_id: int
    department: Department
    operator_id: Optional[int]
    part_type: Optional[str]
    scheduled_hours: float
    setup_hours: float
    productive_hours: float
    efficiency: float
    gross_production: float
    rejects: float
    net_production: float


@dataclass
class DepartmentProductionResult:
    """Production result for a department."""

    department: Department
    machine_results: list[MachineProductionResult]
    total_scheduled_hours: float
    total_setup_hours: float
    total_productive_hours: float
    gross_production_by_type: dict[str, float]
    rejects_by_type: dict[str, float]
    net_production_by_type: dict[str, float]
    total_gross_production: float
    total_rejects: float
    total_net_production: float


@dataclass
class ProductionResult:
    """Complete production result for a week."""

    parts_department: DepartmentProductionResult
    assembly_department: DepartmentProductionResult
    total_gross_production: float
    total_rejects: float
    total_net_production: float


@dataclass
class ProductionInput:
    """Input for production calculations.

    Combines machine assignments with operator efficiency results.
    """

    machine: Machine
    efficiency_result: Optional[OperatorEfficiencyResult] = None


class ProductionEngine:
    """Calculates production output for Parts and Assembly departments.

    This engine coordinates:
    1. Setup time calculations (when part type changes from last week)
    2. Productive hours based on operator efficiency
    3. Gross production based on production rates
    4. Net production after reject rate applied
    """

    def __init__(self, config: Optional[ProsimConfig] = None):
        """Initialize production engine.

        Args:
            config: Simulation configuration (uses defaults if None)
        """
        self.config = config or get_default_config()

    def calculate_setup_time(
        self,
        machine: Machine,
        new_part_type: Optional[str],
    ) -> float:
        """Calculate setup time for a machine.

        Setup time is incurred when the part type changes from last week.

        Args:
            machine: The machine with last_part_type tracking
            new_part_type: The part type to produce this week

        Returns:
            Setup time in hours (0 if no change or first production)
        """
        if new_part_type is None:
            return 0.0

        if machine.last_part_type is None:
            return 0.0

        if machine.last_part_type == new_part_type:
            return 0.0

        # Determine department for setup time lookup
        setup_times = self.config.production.setup_time
        if machine.department == Department.PARTS:
            return setup_times.get("parts_department", 2.0)
        else:
            return setup_times.get("assembly_department", 2.0)

    def get_production_rate(
        self,
        part_type: str,
        department: Department,
    ) -> float:
        """Get production rate for a part/product type.

        Args:
            part_type: The part or product type (X', Y', Z' or X, Y, Z)
            department: The department (determines which rate table to use)

        Returns:
            Units per productive hour
        """
        if department == Department.PARTS:
            return float(self.config.production.parts_rates.get(part_type, 0))
        else:
            return float(self.config.production.assembly_rates.get(part_type, 0))

    def calculate_machine_production(
        self,
        production_input: ProductionInput,
    ) -> MachineProductionResult:
        """Calculate production for a single machine.

        Args:
            production_input: Machine and operator efficiency data

        Returns:
            MachineProductionResult with all production metrics
        """
        machine = production_input.machine
        efficiency_result = production_input.efficiency_result
        assignment = machine.assignment

        # Default values for unassigned machines
        if assignment is None or efficiency_result is None:
            return MachineProductionResult(
                machine_id=machine.machine_id,
                department=machine.department,
                operator_id=None,
                part_type=None,
                scheduled_hours=0.0,
                setup_hours=0.0,
                productive_hours=0.0,
                efficiency=0.0,
                gross_production=0.0,
                rejects=0.0,
                net_production=0.0,
            )

        part_type = assignment.part_type
        scheduled_hours = assignment.scheduled_hours

        # Calculate setup time
        setup_hours = self.calculate_setup_time(machine, part_type)

        # Calculate productive hours
        # Productive hours = (scheduled - setup) * efficiency
        available_hours = max(0.0, scheduled_hours - setup_hours)
        productive_hours = available_hours * efficiency_result.efficiency

        # Calculate gross production
        production_rate = self.get_production_rate(part_type or "", machine.department)
        gross_production = productive_hours * production_rate

        # Apply reject rate
        reject_rate = self.config.production.reject_rate
        rejects = gross_production * reject_rate
        net_production = gross_production - rejects

        return MachineProductionResult(
            machine_id=machine.machine_id,
            department=machine.department,
            operator_id=assignment.operator_id,
            part_type=part_type,
            scheduled_hours=scheduled_hours,
            setup_hours=setup_hours,
            productive_hours=productive_hours,
            efficiency=efficiency_result.efficiency,
            gross_production=gross_production,
            rejects=rejects,
            net_production=net_production,
        )

    def aggregate_department_results(
        self,
        machine_results: list[MachineProductionResult],
        department: Department,
    ) -> DepartmentProductionResult:
        """Aggregate machine results into department totals.

        Args:
            machine_results: List of individual machine results
            department: The department being aggregated

        Returns:
            DepartmentProductionResult with totals and breakdowns
        """
        # Filter to just this department
        dept_results = [r for r in machine_results if r.department == department]

        # Initialize aggregates
        gross_by_type: dict[str, float] = {}
        rejects_by_type: dict[str, float] = {}
        net_by_type: dict[str, float] = {}

        total_scheduled = 0.0
        total_setup = 0.0
        total_productive = 0.0
        total_gross = 0.0
        total_rejects = 0.0
        total_net = 0.0

        for result in dept_results:
            total_scheduled += result.scheduled_hours
            total_setup += result.setup_hours
            total_productive += result.productive_hours
            total_gross += result.gross_production
            total_rejects += result.rejects
            total_net += result.net_production

            if result.part_type:
                gross_by_type[result.part_type] = (
                    gross_by_type.get(result.part_type, 0.0) + result.gross_production
                )
                rejects_by_type[result.part_type] = (
                    rejects_by_type.get(result.part_type, 0.0) + result.rejects
                )
                net_by_type[result.part_type] = (
                    net_by_type.get(result.part_type, 0.0) + result.net_production
                )

        return DepartmentProductionResult(
            department=department,
            machine_results=dept_results,
            total_scheduled_hours=total_scheduled,
            total_setup_hours=total_setup,
            total_productive_hours=total_productive,
            gross_production_by_type=gross_by_type,
            rejects_by_type=rejects_by_type,
            net_production_by_type=net_by_type,
            total_gross_production=total_gross,
            total_rejects=total_rejects,
            total_net_production=total_net,
        )

    def calculate_production(
        self,
        production_inputs: list[ProductionInput],
    ) -> ProductionResult:
        """Calculate production for all machines.

        This is the main entry point for production calculations.

        Args:
            production_inputs: List of machines with their efficiency results

        Returns:
            ProductionResult with department and total breakdowns
        """
        # Calculate production for each machine
        machine_results = [
            self.calculate_machine_production(inp) for inp in production_inputs
        ]

        # Aggregate by department
        parts_result = self.aggregate_department_results(
            machine_results, Department.PARTS
        )
        assembly_result = self.aggregate_department_results(
            machine_results, Department.ASSEMBLY
        )

        # Calculate totals
        total_gross = parts_result.total_gross_production + assembly_result.total_gross_production
        total_rejects = parts_result.total_rejects + assembly_result.total_rejects
        total_net = parts_result.total_net_production + assembly_result.total_net_production

        return ProductionResult(
            parts_department=parts_result,
            assembly_department=assembly_result,
            total_gross_production=total_gross,
            total_rejects=total_rejects,
            total_net_production=total_net,
        )

    def calculate_from_machine_floor(
        self,
        machine_floor: MachineFloor,
        efficiency_results: dict[int, OperatorEfficiencyResult],
    ) -> ProductionResult:
        """Calculate production from a MachineFloor with efficiency results.

        Convenience method that builds ProductionInputs from the floor.

        Args:
            machine_floor: The machine floor with all machines
            efficiency_results: Map of operator_id to their efficiency result

        Returns:
            ProductionResult with all production calculations
        """
        production_inputs = []

        for machine in machine_floor.machines.values():
            # Find efficiency result for this machine's operator
            efficiency_result = None
            if machine.assignment and machine.assignment.operator_id:
                efficiency_result = efficiency_results.get(
                    machine.assignment.operator_id
                )

            production_inputs.append(
                ProductionInput(machine=machine, efficiency_result=efficiency_result)
            )

        return self.calculate_production(production_inputs)

    def update_machine_floor_after_production(
        self,
        machine_floor: MachineFloor,
        production_result: ProductionResult,
    ) -> MachineFloor:
        """Update machine floor with production results.

        Updates last_part_type and setup_hours on each machine.

        Args:
            machine_floor: The current machine floor
            production_result: The production results for the week

        Returns:
            Updated MachineFloor
        """
        updated_floor = machine_floor

        # Update each machine with its production results
        all_machine_results = (
            production_result.parts_department.machine_results
            + production_result.assembly_department.machine_results
        )

        for result in all_machine_results:
            machine = updated_floor.get_machine(result.machine_id)
            if machine is None:
                continue

            # Update last_part_type if production occurred
            updates: dict = {"setup_hours": result.setup_hours}
            if result.part_type and result.net_production > 0:
                updates["last_part_type"] = result.part_type

            updated_machine = machine.model_copy(update=updates)
            updated_floor = updated_floor.update_machine(updated_machine)

        return updated_floor

    def get_raw_materials_needed(
        self,
        parts_production: DepartmentProductionResult,
    ) -> float:
        """Calculate raw materials needed for parts production.

        Uses gross production (before rejects) since raw materials
        are consumed regardless of whether parts pass QC.

        Args:
            parts_production: Parts department production result

        Returns:
            Total raw materials needed
        """
        rm_per_part = self.config.production.raw_materials_per_part
        total_rm = 0.0

        for part_type, gross_qty in parts_production.gross_production_by_type.items():
            rate = rm_per_part.get(part_type, 1.0)
            total_rm += gross_qty * rate

        return total_rm

    def get_parts_needed(
        self,
        assembly_production: DepartmentProductionResult,
    ) -> dict[str, float]:
        """Calculate parts needed for assembly production.

        Uses gross production (before rejects) since parts are
        consumed regardless of whether products pass QC.

        Args:
            assembly_production: Assembly department production result

        Returns:
            Parts needed by type
        """
        bom = self.config.production.bom
        parts_needed: dict[str, float] = {}

        for product_type, gross_qty in assembly_production.gross_production_by_type.items():
            if product_type in bom:
                for part_type, parts_per_product in bom[product_type].items():
                    parts_needed[part_type] = (
                        parts_needed.get(part_type, 0.0) + gross_qty * parts_per_product
                    )

        return parts_needed
