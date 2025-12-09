"""
Tests for the production engine module.

Tests cover:
- Setup time calculations
- Production rate lookups
- Machine production calculations
- Department aggregation
- Full production workflow
- Raw material and parts consumption calculations
"""

import pytest

from prosim.config.schema import ProsimConfig, ProductionRatesConfig
from prosim.engine.production import (
    DepartmentProductionResult,
    MachineProductionResult,
    ProductionEngine,
    ProductionInput,
    ProductionResult,
)
from prosim.engine.workforce import OperatorEfficiencyResult
from prosim.models.machines import Machine, MachineAssignment, MachineFloor
from prosim.models.operators import Department, TrainingStatus


def create_efficiency_result(
    operator_id: int,
    scheduled_hours: float,
    efficiency: float = 1.0,
) -> OperatorEfficiencyResult:
    """Helper to create efficiency results."""
    return OperatorEfficiencyResult(
        operator_id=operator_id,
        scheduled_hours=scheduled_hours,
        productive_hours=scheduled_hours * efficiency,
        efficiency=efficiency,
        training_status=TrainingStatus.TRAINED,
        is_in_training=False,
    )


def create_parts_machine(
    machine_id: int,
    operator_id: int,
    part_type: str,
    scheduled_hours: float,
    last_part_type: str | None = None,
) -> Machine:
    """Helper to create a parts department machine with assignment."""
    return Machine(
        machine_id=machine_id,
        department=Department.PARTS,
        last_part_type=last_part_type,
        assignment=MachineAssignment(
            operator_id=operator_id,
            part_type=part_type,
            scheduled_hours=scheduled_hours,
        ),
    )


def create_assembly_machine(
    machine_id: int,
    operator_id: int,
    product_type: str,
    scheduled_hours: float,
    last_part_type: str | None = None,
) -> Machine:
    """Helper to create an assembly department machine with assignment."""
    return Machine(
        machine_id=machine_id,
        department=Department.ASSEMBLY,
        last_part_type=last_part_type,
        assignment=MachineAssignment(
            operator_id=operator_id,
            part_type=product_type,
            scheduled_hours=scheduled_hours,
        ),
    )


class TestSetupTimeCalculations:
    """Tests for setup time calculations."""

    def test_no_setup_time_first_production(self):
        """Test no setup time when no previous part type."""
        engine = ProductionEngine()
        machine = Machine(
            machine_id=1,
            department=Department.PARTS,
            last_part_type=None,
        )

        setup_time = engine.calculate_setup_time(machine, "X'")

        assert setup_time == 0.0

    def test_no_setup_time_same_part_type(self):
        """Test no setup time when same part type as last week."""
        engine = ProductionEngine()
        machine = Machine(
            machine_id=1,
            department=Department.PARTS,
            last_part_type="X'",
        )

        setup_time = engine.calculate_setup_time(machine, "X'")

        assert setup_time == 0.0

    def test_setup_time_different_part_type_parts_dept(self):
        """Test setup time when changing part types in parts department."""
        engine = ProductionEngine()
        machine = Machine(
            machine_id=1,
            department=Department.PARTS,
            last_part_type="X'",
        )

        setup_time = engine.calculate_setup_time(machine, "Y'")

        assert setup_time == 2.0  # Default parts department setup time

    def test_setup_time_different_part_type_assembly_dept(self):
        """Test setup time when changing product types in assembly department."""
        engine = ProductionEngine()
        machine = Machine(
            machine_id=5,
            department=Department.ASSEMBLY,
            last_part_type="X",
        )

        setup_time = engine.calculate_setup_time(machine, "Y")

        assert setup_time == 2.0  # Default assembly department setup time

    def test_setup_time_none_part_type(self):
        """Test no setup time when new part type is None."""
        engine = ProductionEngine()
        machine = Machine(
            machine_id=1,
            department=Department.PARTS,
            last_part_type="X'",
        )

        setup_time = engine.calculate_setup_time(machine, None)

        assert setup_time == 0.0

    def test_custom_setup_times(self):
        """Test setup time with custom configuration."""
        config = ProsimConfig(
            production=ProductionRatesConfig(
                setup_time={"parts_department": 3.0, "assembly_department": 4.0}
            )
        )
        engine = ProductionEngine(config)

        parts_machine = Machine(
            machine_id=1, department=Department.PARTS, last_part_type="X'"
        )
        assembly_machine = Machine(
            machine_id=5, department=Department.ASSEMBLY, last_part_type="X"
        )

        assert engine.calculate_setup_time(parts_machine, "Y'") == 3.0
        assert engine.calculate_setup_time(assembly_machine, "Y") == 4.0


class TestProductionRates:
    """Tests for production rate lookups."""

    def test_parts_department_rates(self):
        """Test production rates for parts department."""
        engine = ProductionEngine()

        assert engine.get_production_rate("X'", Department.PARTS) == 60.0
        assert engine.get_production_rate("Y'", Department.PARTS) == 50.0
        assert engine.get_production_rate("Z'", Department.PARTS) == 40.0

    def test_assembly_department_rates(self):
        """Test production rates for assembly department."""
        engine = ProductionEngine()

        assert engine.get_production_rate("X", Department.ASSEMBLY) == 40.0
        assert engine.get_production_rate("Y", Department.ASSEMBLY) == 30.0
        assert engine.get_production_rate("Z", Department.ASSEMBLY) == 20.0

    def test_unknown_part_type_returns_zero(self):
        """Test that unknown part types return zero rate."""
        engine = ProductionEngine()

        assert engine.get_production_rate("W'", Department.PARTS) == 0.0
        assert engine.get_production_rate("W", Department.ASSEMBLY) == 0.0

    def test_custom_production_rates(self):
        """Test production rates with custom configuration."""
        config = ProsimConfig(
            production=ProductionRatesConfig(
                parts_rates={"X'": 100, "Y'": 80, "Z'": 60},
                assembly_rates={"X": 50, "Y": 40, "Z": 30},
            )
        )
        engine = ProductionEngine(config)

        assert engine.get_production_rate("X'", Department.PARTS) == 100.0
        assert engine.get_production_rate("X", Department.ASSEMBLY) == 50.0


class TestMachineProductionCalculations:
    """Tests for individual machine production calculations."""

    def test_basic_parts_production(self):
        """Test basic parts production calculation."""
        engine = ProductionEngine()

        machine = create_parts_machine(1, 1, "X'", 40.0)
        efficiency = create_efficiency_result(1, 40.0, 1.0)
        production_input = ProductionInput(machine=machine, efficiency_result=efficiency)

        result = engine.calculate_machine_production(production_input)

        # 40 hours * 1.0 efficiency * 60 parts/hour = 2400 gross
        assert result.machine_id == 1
        assert result.department == Department.PARTS
        assert result.scheduled_hours == 40.0
        assert result.setup_hours == 0.0
        assert result.productive_hours == 40.0
        assert result.gross_production == 2400.0
        # 17.8% reject rate
        assert result.rejects == pytest.approx(427.2, rel=0.01)
        assert result.net_production == pytest.approx(1972.8, rel=0.01)

    def test_parts_production_with_efficiency(self):
        """Test parts production with reduced efficiency."""
        engine = ProductionEngine()

        machine = create_parts_machine(1, 1, "Y'", 50.0)
        efficiency = create_efficiency_result(1, 50.0, 0.80)
        production_input = ProductionInput(machine=machine, efficiency_result=efficiency)

        result = engine.calculate_machine_production(production_input)

        # 50 hours * 0.80 efficiency * 50 parts/hour = 2000 gross
        assert result.productive_hours == 40.0
        assert result.gross_production == 2000.0

    def test_production_with_setup_time(self):
        """Test production with setup time deduction."""
        engine = ProductionEngine()

        machine = create_parts_machine(1, 1, "Y'", 40.0, last_part_type="X'")
        efficiency = create_efficiency_result(1, 40.0, 1.0)
        production_input = ProductionInput(machine=machine, efficiency_result=efficiency)

        result = engine.calculate_machine_production(production_input)

        # (40 - 2 setup) * 1.0 efficiency * 50 parts/hour = 1900 gross
        assert result.setup_hours == 2.0
        assert result.productive_hours == 38.0
        assert result.gross_production == 1900.0

    def test_assembly_production(self):
        """Test assembly production calculation."""
        engine = ProductionEngine()

        machine = create_assembly_machine(5, 1, "X", 40.0)
        efficiency = create_efficiency_result(1, 40.0, 1.0)
        production_input = ProductionInput(machine=machine, efficiency_result=efficiency)

        result = engine.calculate_machine_production(production_input)

        # 40 hours * 1.0 efficiency * 40 products/hour = 1600 gross
        assert result.department == Department.ASSEMBLY
        assert result.gross_production == 1600.0

    def test_unassigned_machine_zero_production(self):
        """Test that unassigned machines produce nothing."""
        engine = ProductionEngine()

        machine = Machine(machine_id=1, department=Department.PARTS)
        production_input = ProductionInput(machine=machine, efficiency_result=None)

        result = engine.calculate_machine_production(production_input)

        assert result.scheduled_hours == 0.0
        assert result.productive_hours == 0.0
        assert result.gross_production == 0.0
        assert result.net_production == 0.0

    def test_custom_reject_rate(self):
        """Test production with custom reject rate."""
        config = ProsimConfig(
            production=ProductionRatesConfig(reject_rate=0.10)
        )
        engine = ProductionEngine(config)

        machine = create_parts_machine(1, 1, "X'", 40.0)
        efficiency = create_efficiency_result(1, 40.0, 1.0)
        production_input = ProductionInput(machine=machine, efficiency_result=efficiency)

        result = engine.calculate_machine_production(production_input)

        # 10% reject rate instead of 17.8%
        assert result.gross_production == 2400.0
        assert result.rejects == 240.0
        assert result.net_production == 2160.0


class TestDepartmentAggregation:
    """Tests for department-level aggregation."""

    def test_aggregate_parts_department(self):
        """Test aggregating multiple parts machines."""
        engine = ProductionEngine()

        machine_results = [
            MachineProductionResult(
                machine_id=1,
                department=Department.PARTS,
                operator_id=1,
                part_type="X'",
                scheduled_hours=40.0,
                setup_hours=0.0,
                productive_hours=40.0,
                efficiency=1.0,
                gross_production=2400.0,
                rejects=427.2,
                net_production=1972.8,
            ),
            MachineProductionResult(
                machine_id=2,
                department=Department.PARTS,
                operator_id=2,
                part_type="Y'",
                scheduled_hours=40.0,
                setup_hours=0.0,
                productive_hours=40.0,
                efficiency=1.0,
                gross_production=2000.0,
                rejects=356.0,
                net_production=1644.0,
            ),
        ]

        result = engine.aggregate_department_results(machine_results, Department.PARTS)

        assert result.department == Department.PARTS
        assert len(result.machine_results) == 2
        assert result.total_scheduled_hours == 80.0
        assert result.total_gross_production == 4400.0
        assert result.gross_production_by_type == {"X'": 2400.0, "Y'": 2000.0}
        assert result.net_production_by_type["X'"] == pytest.approx(1972.8, rel=0.01)

    def test_aggregate_filters_by_department(self):
        """Test that aggregation filters to correct department."""
        engine = ProductionEngine()

        machine_results = [
            MachineProductionResult(
                machine_id=1,
                department=Department.PARTS,
                operator_id=1,
                part_type="X'",
                scheduled_hours=40.0,
                setup_hours=0.0,
                productive_hours=40.0,
                efficiency=1.0,
                gross_production=2400.0,
                rejects=427.2,
                net_production=1972.8,
            ),
            MachineProductionResult(
                machine_id=5,
                department=Department.ASSEMBLY,
                operator_id=2,
                part_type="X",
                scheduled_hours=40.0,
                setup_hours=0.0,
                productive_hours=40.0,
                efficiency=1.0,
                gross_production=1600.0,
                rejects=284.8,
                net_production=1315.2,
            ),
        ]

        parts_result = engine.aggregate_department_results(machine_results, Department.PARTS)
        assembly_result = engine.aggregate_department_results(machine_results, Department.ASSEMBLY)

        assert len(parts_result.machine_results) == 1
        assert parts_result.total_gross_production == 2400.0

        assert len(assembly_result.machine_results) == 1
        assert assembly_result.total_gross_production == 1600.0


class TestFullProduction:
    """Tests for full production workflow."""

    def test_calculate_production_full_workflow(self):
        """Test complete production calculation."""
        engine = ProductionEngine()

        # Two parts machines, two assembly machines
        production_inputs = [
            ProductionInput(
                machine=create_parts_machine(1, 1, "X'", 40.0),
                efficiency_result=create_efficiency_result(1, 40.0, 1.0),
            ),
            ProductionInput(
                machine=create_parts_machine(2, 2, "Y'", 40.0),
                efficiency_result=create_efficiency_result(2, 40.0, 0.9),
            ),
            ProductionInput(
                machine=create_assembly_machine(5, 3, "X", 40.0),
                efficiency_result=create_efficiency_result(3, 40.0, 1.0),
            ),
            ProductionInput(
                machine=create_assembly_machine(6, 4, "Y", 40.0),
                efficiency_result=create_efficiency_result(4, 40.0, 0.95),
            ),
        ]

        result = engine.calculate_production(production_inputs)

        # Parts department: 2 machines
        assert len(result.parts_department.machine_results) == 2
        assert result.parts_department.total_scheduled_hours == 80.0

        # Assembly department: 2 machines
        assert len(result.assembly_department.machine_results) == 2
        assert result.assembly_department.total_scheduled_hours == 80.0

        # Totals
        assert result.total_gross_production > 0
        assert result.total_rejects > 0
        assert result.total_net_production > 0
        assert result.total_net_production < result.total_gross_production

    def test_calculate_from_machine_floor(self):
        """Test production calculation from MachineFloor."""
        engine = ProductionEngine()

        # Create machine floor
        machine_floor = MachineFloor.create_default(num_parts_machines=2, num_assembly_machines=2)

        # Assign machines
        machine1 = machine_floor.get_machine(1)
        machine1 = machine1.assign(1, "X'", 40.0)
        machine_floor = machine_floor.update_machine(machine1)

        machine3 = machine_floor.get_machine(3)  # First assembly machine
        machine3 = machine3.assign(2, "X", 40.0)
        machine_floor = machine_floor.update_machine(machine3)

        # Create efficiency results
        efficiency_results = {
            1: create_efficiency_result(1, 40.0, 1.0),
            2: create_efficiency_result(2, 40.0, 1.0),
        }

        result = engine.calculate_from_machine_floor(machine_floor, efficiency_results)

        # Should have production from assigned machines
        assert result.parts_department.total_gross_production > 0
        assert result.assembly_department.total_gross_production > 0


class TestMaterialConsumption:
    """Tests for material consumption calculations."""

    def test_get_raw_materials_needed(self):
        """Test raw materials needed calculation."""
        engine = ProductionEngine()

        parts_result = DepartmentProductionResult(
            department=Department.PARTS,
            machine_results=[],
            total_scheduled_hours=80.0,
            total_setup_hours=0.0,
            total_productive_hours=80.0,
            gross_production_by_type={"X'": 1000.0, "Y'": 500.0, "Z'": 300.0},
            rejects_by_type={},
            net_production_by_type={},
            total_gross_production=1800.0,
            total_rejects=0.0,
            total_net_production=0.0,
        )

        rm_needed = engine.get_raw_materials_needed(parts_result)

        # With default 1:1 ratio, should equal total gross production
        assert rm_needed == 1800.0

    def test_get_raw_materials_needed_custom_rates(self):
        """Test raw materials needed with custom rates."""
        config = ProsimConfig(
            production=ProductionRatesConfig(
                raw_materials_per_part={"X'": 2.0, "Y'": 1.5, "Z'": 1.0}
            )
        )
        engine = ProductionEngine(config)

        parts_result = DepartmentProductionResult(
            department=Department.PARTS,
            machine_results=[],
            total_scheduled_hours=80.0,
            total_setup_hours=0.0,
            total_productive_hours=80.0,
            gross_production_by_type={"X'": 100.0, "Y'": 100.0, "Z'": 100.0},
            rejects_by_type={},
            net_production_by_type={},
            total_gross_production=300.0,
            total_rejects=0.0,
            total_net_production=0.0,
        )

        rm_needed = engine.get_raw_materials_needed(parts_result)

        # X': 100 * 2.0 = 200
        # Y': 100 * 1.5 = 150
        # Z': 100 * 1.0 = 100
        assert rm_needed == 450.0

    def test_get_parts_needed(self):
        """Test parts needed for assembly calculation."""
        engine = ProductionEngine()

        assembly_result = DepartmentProductionResult(
            department=Department.ASSEMBLY,
            machine_results=[],
            total_scheduled_hours=80.0,
            total_setup_hours=0.0,
            total_productive_hours=80.0,
            gross_production_by_type={"X": 100.0, "Y": 150.0, "Z": 200.0},
            rejects_by_type={},
            net_production_by_type={},
            total_gross_production=450.0,
            total_rejects=0.0,
            total_net_production=0.0,
        )

        parts_needed = engine.get_parts_needed(assembly_result)

        # With default 1:1 BOM
        assert parts_needed == {"X'": 100.0, "Y'": 150.0, "Z'": 200.0}


class TestMachineFloorUpdates:
    """Tests for updating machine floor after production."""

    def test_update_machine_floor_last_part_type(self):
        """Test that machine floor updates last_part_type after production."""
        engine = ProductionEngine()

        machine_floor = MachineFloor.create_default(num_parts_machines=2, num_assembly_machines=1)

        # Assign machine 1 to produce X'
        machine1 = machine_floor.get_machine(1)
        machine1 = machine1.assign(1, "X'", 40.0)
        machine_floor = machine_floor.update_machine(machine1)

        # Create production result
        parts_result = DepartmentProductionResult(
            department=Department.PARTS,
            machine_results=[
                MachineProductionResult(
                    machine_id=1,
                    department=Department.PARTS,
                    operator_id=1,
                    part_type="X'",
                    scheduled_hours=40.0,
                    setup_hours=0.0,
                    productive_hours=40.0,
                    efficiency=1.0,
                    gross_production=2400.0,
                    rejects=427.2,
                    net_production=1972.8,
                ),
            ],
            total_scheduled_hours=40.0,
            total_setup_hours=0.0,
            total_productive_hours=40.0,
            gross_production_by_type={"X'": 2400.0},
            rejects_by_type={"X'": 427.2},
            net_production_by_type={"X'": 1972.8},
            total_gross_production=2400.0,
            total_rejects=427.2,
            total_net_production=1972.8,
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

        production_result = ProductionResult(
            parts_department=parts_result,
            assembly_department=assembly_result,
            total_gross_production=2400.0,
            total_rejects=427.2,
            total_net_production=1972.8,
        )

        updated_floor = engine.update_machine_floor_after_production(
            machine_floor, production_result
        )

        # Machine 1 should now have X' as last_part_type
        updated_machine1 = updated_floor.get_machine(1)
        assert updated_machine1.last_part_type == "X'"


class TestIntegration:
    """Integration tests for production engine."""

    def test_verified_reject_rate(self):
        """Test that reject rate matches verified 17.8% from original data."""
        engine = ProductionEngine()

        # Simulate production similar to REPT14.DAT data
        machine = create_parts_machine(1, 1, "X'", 42.5)
        efficiency = create_efficiency_result(1, 42.5, 1.0)
        production_input = ProductionInput(machine=machine, efficiency_result=efficiency)

        result = engine.calculate_machine_production(production_input)

        # Verify ~17.8% reject rate
        actual_reject_rate = result.rejects / result.gross_production
        assert actual_reject_rate == pytest.approx(0.178, rel=0.01)

    def test_production_formulas_match_case_study(self):
        """Test that production formulas match the case study documentation."""
        engine = ProductionEngine()

        # From case study:
        # Actual Production = Productive Hours × Standard Parts/Hour
        # Rejects = Actual Production × Reject Rate
        # Net Production = Actual Production - Rejects

        machine = create_parts_machine(1, 1, "X'", 40.0)
        efficiency = create_efficiency_result(1, 40.0, 0.90)  # 90% efficiency
        production_input = ProductionInput(machine=machine, efficiency_result=efficiency)

        result = engine.calculate_machine_production(production_input)

        # Manual calculation
        expected_productive = 40.0 * 0.90  # 36 hours
        expected_gross = expected_productive * 60  # 2160 parts
        expected_rejects = expected_gross * 0.178  # 384.48 rejects
        expected_net = expected_gross - expected_rejects  # 1775.52 net

        assert result.productive_hours == pytest.approx(expected_productive, rel=0.01)
        assert result.gross_production == pytest.approx(expected_gross, rel=0.01)
        assert result.rejects == pytest.approx(expected_rejects, rel=0.01)
        assert result.net_production == pytest.approx(expected_net, rel=0.01)
