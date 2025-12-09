"""
Tests for the workforce/operator management module.

Tests cover:
- Efficiency calculations (trained vs untrained)
- Training status progression
- Operator scheduling and unscheduling
- Consecutive unscheduled week tracking
- Hiring and termination logic
- Workforce cost calculations
"""

import pytest

from prosim.config.schema import (
    OperatorEfficiencyConfig,
    ProsimConfig,
    WorkforceCostsConfig,
    WorkforceConfig,
)
from prosim.engine.workforce import (
    OperatorEfficiencyResult,
    OperatorManager,
    TrainingResult,
    WorkforceCostResult,
    WorkforceSchedulingResult,
)
from prosim.models.machines import Machine, MachineAssignment
from prosim.models.operators import (
    Department,
    Operator,
    TrainingStatus,
    Workforce,
)


class TestEfficiencyCalculations:
    """Tests for operator efficiency calculations."""

    def test_trained_operator_efficiency_in_range(self):
        """Test that trained operator efficiency is within configured range."""
        manager = OperatorManager(random_seed=42)
        operator = Operator(operator_id=1, training_status=TrainingStatus.TRAINED)

        # Test multiple times to verify range
        efficiencies = [manager.calculate_efficiency(operator) for _ in range(100)]

        assert all(0.95 <= e <= 1.00 for e in efficiencies)

    def test_untrained_operator_efficiency_in_range(self):
        """Test that untrained operator efficiency is within configured range."""
        manager = OperatorManager(random_seed=42)
        operator = Operator(operator_id=1, training_status=TrainingStatus.UNTRAINED)

        # Test multiple times to verify range
        efficiencies = [manager.calculate_efficiency(operator) for _ in range(100)]

        assert all(0.60 <= e <= 0.90 for e in efficiencies)

    def test_training_operator_efficiency_zero(self):
        """Test that operator in training has zero efficiency."""
        manager = OperatorManager(random_seed=42)
        operator = Operator(operator_id=1, training_status=TrainingStatus.TRAINING)

        efficiency = manager.calculate_efficiency(operator)

        assert efficiency == 0.0

    def test_custom_efficiency_ranges(self):
        """Test efficiency calculations with custom configuration."""
        config = ProsimConfig(
            workforce=WorkforceConfig(
                efficiency=OperatorEfficiencyConfig(
                    trained_min=0.99,
                    trained_max=1.00,
                    untrained_min=0.50,
                    untrained_max=0.70,
                )
            )
        )
        manager = OperatorManager(config=config, random_seed=42)

        trained_op = Operator(operator_id=1, training_status=TrainingStatus.TRAINED)
        untrained_op = Operator(operator_id=2, training_status=TrainingStatus.UNTRAINED)

        trained_eff = [manager.calculate_efficiency(trained_op) for _ in range(100)]
        untrained_eff = [manager.calculate_efficiency(untrained_op) for _ in range(100)]

        assert all(0.99 <= e <= 1.00 for e in trained_eff)
        assert all(0.50 <= e <= 0.70 for e in untrained_eff)

    def test_productive_hours_calculation(self):
        """Test productive hours based on efficiency."""
        manager = OperatorManager(random_seed=42)
        operator = Operator(operator_id=1, training_status=TrainingStatus.TRAINED)

        result = manager.calculate_productive_hours(operator, scheduled_hours=40.0)

        assert isinstance(result, OperatorEfficiencyResult)
        assert result.operator_id == 1
        assert result.scheduled_hours == 40.0
        assert 38.0 <= result.productive_hours <= 40.0  # 95-100% of 40
        assert result.training_status == TrainingStatus.TRAINED
        assert not result.is_in_training

    def test_productive_hours_while_training(self):
        """Test that operators in training have zero productive hours."""
        manager = OperatorManager(random_seed=42)
        operator = Operator(operator_id=1, training_status=TrainingStatus.TRAINING)

        result = manager.calculate_productive_hours(operator, scheduled_hours=40.0)

        assert result.productive_hours == 0.0
        assert result.is_in_training

    def test_reproducible_with_seed(self):
        """Test that results are reproducible with same seed."""
        operator = Operator(operator_id=1, training_status=TrainingStatus.UNTRAINED)

        manager1 = OperatorManager(random_seed=12345)
        manager2 = OperatorManager(random_seed=12345)

        eff1 = [manager1.calculate_efficiency(operator) for _ in range(10)]
        eff2 = [manager2.calculate_efficiency(operator) for _ in range(10)]

        assert eff1 == eff2


class TestTrainingOperations:
    """Tests for training operations."""

    def test_send_to_training(self):
        """Test sending untrained operators to training."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=0)

        new_workforce, result = manager.send_to_training(workforce, [1, 2])

        assert result.operators_sent_to_training == [1, 2]
        assert new_workforce.operators[1].training_status == TrainingStatus.TRAINING
        assert new_workforce.operators[2].training_status == TrainingStatus.TRAINING
        assert new_workforce.operators[3].training_status == TrainingStatus.UNTRAINED

    def test_send_trained_operator_to_training_ignored(self):
        """Test that already trained operators cannot be sent to training."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=2)

        # Try to send trained operators to training
        new_workforce, result = manager.send_to_training(workforce, [1, 2])

        # Should not be sent to training
        assert result.operators_sent_to_training == []
        assert new_workforce.operators[1].training_status == TrainingStatus.TRAINED
        assert new_workforce.operators[2].training_status == TrainingStatus.TRAINED

    def test_training_completion(self):
        """Test that operators in training become trained."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=0)

        # Send to training
        workforce, _ = manager.send_to_training(workforce, [1, 2])

        # Complete training (simulates next week start)
        new_workforce, completed = manager.process_training_completion(workforce)

        assert completed == [1, 2]
        assert new_workforce.operators[1].training_status == TrainingStatus.TRAINED
        assert new_workforce.operators[2].training_status == TrainingStatus.TRAINED
        assert new_workforce.operators[3].training_status == TrainingStatus.UNTRAINED

    def test_training_cost(self):
        """Test training cost calculation."""
        config = ProsimConfig(
            workforce=WorkforceConfig(
                costs=WorkforceCostsConfig(training_cost_per_worker=1500.0)
            )
        )
        manager = OperatorManager(config=config, random_seed=42)
        workforce = Workforce.create_initial(num_operators=5, num_trained=0)

        _, result = manager.send_to_training(workforce, [1, 2, 3])

        assert result.training_cost == 4500.0  # 3 * 1500


def create_machine(machine_id: int, operator_id: int, part_type: str, scheduled_hours: float) -> Machine:
    """Helper function to create a Machine with assignment."""
    department = Department.PARTS if machine_id <= 4 else Department.ASSEMBLY
    return Machine(
        machine_id=machine_id,
        department=department,
        assignment=MachineAssignment(
            operator_id=operator_id,
            part_type=part_type,
            scheduled_hours=scheduled_hours,
        ),
    )


class TestSchedulingOperations:
    """Tests for scheduling operators to machines."""

    def test_schedule_operators_basic(self):
        """Test basic operator scheduling."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=4, num_trained=4)

        machines = [
            create_machine(1, 1, "X'", 40.0),
            create_machine(2, 2, "Y'", 50.0),
        ]

        new_workforce, result = manager.schedule_operators(workforce, machines)

        assert len(result.scheduled_operators) == 2
        assert result.unscheduled_operator_ids == [3, 4]
        assert new_workforce.operators[1].department == Department.PARTS
        assert new_workforce.operators[2].department == Department.PARTS
        assert new_workforce.operators[3].department == Department.UNASSIGNED
        assert new_workforce.operators[4].department == Department.UNASSIGNED

    def test_schedule_operators_assembly_department(self):
        """Test scheduling operators to assembly department."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=2, num_trained=2)

        # Machines 5+ are in assembly department (default config has 4 parts machines)
        machines = [
            create_machine(5, 1, "X", 40.0),
            create_machine(6, 2, "Y", 40.0),
        ]

        new_workforce, result = manager.schedule_operators(workforce, machines)

        assert new_workforce.operators[1].department == Department.ASSEMBLY
        assert new_workforce.operators[2].department == Department.ASSEMBLY

    def test_schedule_resets_consecutive_weeks(self):
        """Test that scheduling resets consecutive unscheduled weeks."""
        manager = OperatorManager(random_seed=42)

        # Create workforce with operator who has been unscheduled
        operators = {
            1: Operator(operator_id=1, training_status=TrainingStatus.TRAINED, consecutive_weeks_unscheduled=1),
        }
        workforce = Workforce(operators=operators, next_operator_id=2)

        machines = [create_machine(1, 1, "X'", 40.0)]

        new_workforce, _ = manager.schedule_operators(workforce, machines)

        assert new_workforce.operators[1].consecutive_weeks_unscheduled == 0

    def test_unscheduled_increments_consecutive_weeks(self):
        """Test that unscheduled operators get consecutive weeks incremented."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=2, num_trained=2)

        # Only schedule one operator
        machines = [create_machine(1, 1, "X'", 40.0)]

        new_workforce, result = manager.schedule_operators(workforce, machines)

        assert new_workforce.operators[1].consecutive_weeks_unscheduled == 0
        assert new_workforce.operators[2].consecutive_weeks_unscheduled == 1
        assert 2 in result.unscheduled_operator_ids

    def test_operators_in_training_not_counted_as_unscheduled(self):
        """Test that operators in training are not marked as unscheduled."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=0)

        # Send operator 2 to training
        workforce, _ = manager.send_to_training(workforce, [2])

        # Schedule only operator 1
        machines = [create_machine(1, 1, "X'", 40.0)]

        new_workforce, result = manager.schedule_operators(workforce, machines)

        # Operator 2 in training, operator 3 unscheduled
        assert 2 in result.operators_in_training
        assert 3 in result.unscheduled_operator_ids
        assert 2 not in result.unscheduled_operator_ids
        # Operator 2's consecutive weeks should not increase (they're in training)
        assert new_workforce.operators[2].consecutive_weeks_unscheduled == 0

    def test_scheduling_result_totals(self):
        """Test scheduling result totals calculation."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=2, num_trained=2)

        machines = [
            create_machine(1, 1, "X'", 40.0),
            create_machine(2, 2, "Y'", 50.0),
        ]

        _, result = manager.schedule_operators(workforce, machines)

        assert result.total_scheduled_hours == 90.0
        # Productive hours should be close to scheduled (trained operators)
        assert 85.5 <= result.total_productive_hours <= 90.0


class TestHiringOperations:
    """Tests for hiring operations."""

    def test_hire_untrained_operators(self):
        """Test hiring untrained operators."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=2, num_trained=0)

        new_workforce, hired = manager.hire_operators(workforce, count=3, trained=False)

        assert len(hired) == 3
        assert all(op.training_status == TrainingStatus.UNTRAINED for op in hired)
        assert all(op.is_new_hire for op in hired)
        assert len(new_workforce.operators) == 5  # 2 original + 3 new
        # IDs should be 3, 4, 5
        assert {op.operator_id for op in hired} == {3, 4, 5}

    def test_hire_trained_operators(self):
        """Test hiring trained operators."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=2, num_trained=0)

        new_workforce, hired = manager.hire_operators(workforce, count=2, trained=True)

        assert len(hired) == 2
        assert all(op.training_status == TrainingStatus.TRAINED for op in hired)

    def test_hire_zero_operators(self):
        """Test hiring zero operators."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=2, num_trained=0)

        new_workforce, hired = manager.hire_operators(workforce, count=0)

        assert len(hired) == 0
        assert len(new_workforce.operators) == 2


class TestTerminationOperations:
    """Tests for termination operations."""

    def test_process_terminations(self):
        """Test automatic termination of long-unscheduled operators."""
        manager = OperatorManager(random_seed=42)

        # Create workforce with operator who has been unscheduled 2 weeks
        operators = {
            1: Operator(operator_id=1, training_status=TrainingStatus.TRAINED, consecutive_weeks_unscheduled=2),
            2: Operator(operator_id=2, training_status=TrainingStatus.TRAINED, consecutive_weeks_unscheduled=1),
            3: Operator(operator_id=3, training_status=TrainingStatus.TRAINED, consecutive_weeks_unscheduled=0),
        }
        workforce = Workforce(operators=operators, next_operator_id=4)

        new_workforce, terminated = manager.process_terminations(workforce)

        assert terminated == [1]
        assert 1 not in new_workforce.operators
        assert 2 in new_workforce.operators
        assert 3 in new_workforce.operators

    def test_process_terminations_multiple(self):
        """Test terminating multiple operators."""
        manager = OperatorManager(random_seed=42)

        operators = {
            1: Operator(operator_id=1, training_status=TrainingStatus.TRAINED, consecutive_weeks_unscheduled=2),
            2: Operator(operator_id=2, training_status=TrainingStatus.TRAINED, consecutive_weeks_unscheduled=3),
            3: Operator(operator_id=3, training_status=TrainingStatus.TRAINED, consecutive_weeks_unscheduled=0),
        }
        workforce = Workforce(operators=operators, next_operator_id=4)

        new_workforce, terminated = manager.process_terminations(workforce)

        assert set(terminated) == {1, 2}
        assert len(new_workforce.operators) == 1
        assert 3 in new_workforce.operators

    def test_process_terminations_none(self):
        """Test when no operators should be terminated."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=3)

        new_workforce, terminated = manager.process_terminations(workforce)

        assert terminated == []
        assert len(new_workforce.operators) == 3


class TestCostCalculations:
    """Tests for workforce cost calculations."""

    def test_hiring_cost(self):
        """Test hiring cost calculation."""
        config = ProsimConfig(
            workforce=WorkforceConfig(
                costs=WorkforceCostsConfig(hiring_cost=2700.0)
            )
        )
        manager = OperatorManager(config=config, random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=3)

        result = manager.calculate_weekly_costs(workforce, operators_hired=2)

        assert result.hiring_cost == 5400.0  # 2 * 2700
        assert result.operators_hired == 2

    def test_training_cost(self):
        """Test training cost calculation."""
        config = ProsimConfig(
            workforce=WorkforceConfig(
                costs=WorkforceCostsConfig(training_cost_per_worker=1000.0)
            )
        )
        manager = OperatorManager(config=config, random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=0)

        result = manager.calculate_weekly_costs(workforce, operators_trained=3)

        assert result.training_cost == 3000.0  # 3 * 1000
        assert result.operators_trained == 3

    def test_layoff_cost(self):
        """Test layoff cost calculation."""
        config = ProsimConfig(
            workforce=WorkforceConfig(
                costs=WorkforceCostsConfig(layoff_cost_per_week=200.0)
            )
        )
        manager = OperatorManager(config=config, random_seed=42)

        # Create workforce with unscheduled operators
        operators = {
            1: Operator(
                operator_id=1,
                training_status=TrainingStatus.TRAINED,
                consecutive_weeks_unscheduled=1,
                department=Department.UNASSIGNED,
            ),
            2: Operator(
                operator_id=2,
                training_status=TrainingStatus.TRAINED,
                consecutive_weeks_unscheduled=1,
                department=Department.UNASSIGNED,
            ),
            3: Operator(
                operator_id=3,
                training_status=TrainingStatus.TRAINED,
                consecutive_weeks_unscheduled=0,
                department=Department.PARTS,
            ),
        }
        workforce = Workforce(operators=operators, next_operator_id=4)

        result = manager.calculate_weekly_costs(workforce)

        assert result.layoff_cost == 400.0  # 2 * 200
        assert result.operators_laid_off == 2

    def test_termination_cost(self):
        """Test termination cost calculation."""
        config = ProsimConfig(
            workforce=WorkforceConfig(
                costs=WorkforceCostsConfig(termination_cost=400.0)
            )
        )
        manager = OperatorManager(config=config, random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=3)

        result = manager.calculate_weekly_costs(
            workforce, operators_terminated=[1, 2]
        )

        assert result.termination_cost == 800.0  # 2 * 400
        assert result.operators_terminated == 2

    def test_total_cost_calculation(self):
        """Test total cost calculation."""
        config = ProsimConfig(
            workforce=WorkforceConfig(
                costs=WorkforceCostsConfig(
                    hiring_cost=2700.0,
                    training_cost_per_worker=1000.0,
                    layoff_cost_per_week=200.0,
                    termination_cost=400.0,
                )
            )
        )
        manager = OperatorManager(config=config, random_seed=42)

        operators = {
            1: Operator(
                operator_id=1,
                training_status=TrainingStatus.TRAINED,
                consecutive_weeks_unscheduled=1,
                department=Department.UNASSIGNED,
            ),
        }
        workforce = Workforce(operators=operators, next_operator_id=2)

        result = manager.calculate_weekly_costs(
            workforce,
            operators_hired=1,
            operators_trained=2,
            operators_terminated=[5],
        )

        expected_total = (
            2700.0  # hiring: 1 * 2700
            + 2000.0  # training: 2 * 1000
            + 200.0  # layoff: 1 * 200
            + 400.0  # termination: 1 * 400
        )
        assert result.total_cost == expected_total


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_department_operators(self):
        """Test getting operators by department."""
        manager = OperatorManager(random_seed=42)

        operators = {
            1: Operator(operator_id=1, training_status=TrainingStatus.TRAINED, department=Department.PARTS),
            2: Operator(operator_id=2, training_status=TrainingStatus.TRAINED, department=Department.PARTS),
            3: Operator(operator_id=3, training_status=TrainingStatus.TRAINED, department=Department.ASSEMBLY),
            4: Operator(operator_id=4, training_status=TrainingStatus.TRAINED, department=Department.UNASSIGNED),
        }
        workforce = Workforce(operators=operators, next_operator_id=5)

        parts_ops = manager.get_department_operators(workforce, Department.PARTS)
        assembly_ops = manager.get_department_operators(workforce, Department.ASSEMBLY)

        assert len(parts_ops) == 2
        assert {op.operator_id for op in parts_ops} == {1, 2}
        assert len(assembly_ops) == 1
        assert assembly_ops[0].operator_id == 3

    def test_get_available_operators(self):
        """Test getting operators available for scheduling."""
        manager = OperatorManager(random_seed=42)

        operators = {
            1: Operator(operator_id=1, training_status=TrainingStatus.TRAINED),
            2: Operator(operator_id=2, training_status=TrainingStatus.UNTRAINED),
            3: Operator(operator_id=3, training_status=TrainingStatus.TRAINING),
        }
        workforce = Workforce(operators=operators, next_operator_id=4)

        available = manager.get_available_operators(workforce)

        assert len(available) == 2
        assert {op.operator_id for op in available} == {1, 2}


class TestProcessWeekOperations:
    """Tests for week start/end operations."""

    def test_process_week_start(self):
        """Test processing week start operations."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=0)

        # Send operator 1 to training last week
        workforce, _ = manager.send_to_training(workforce, [1])

        # Process week start: complete training, send more to train, hire
        new_workforce, training_result, hired = manager.process_week_start(
            workforce,
            operators_to_train=[2],
            operators_to_hire=1,
        )

        # Operator 1 should now be trained
        assert new_workforce.operators[1].training_status == TrainingStatus.TRAINED
        assert 1 in training_result.operators_completed_training

        # Operator 2 should be in training
        assert new_workforce.operators[2].training_status == TrainingStatus.TRAINING
        assert 2 in training_result.operators_sent_to_training

        # Should have hired 1 new operator
        assert len(hired) == 1
        assert len(new_workforce.operators) == 4

    def test_process_week_end(self):
        """Test processing week end operations."""
        manager = OperatorManager(random_seed=42)

        operators = {
            1: Operator(operator_id=1, training_status=TrainingStatus.TRAINED, consecutive_weeks_unscheduled=2),
            2: Operator(operator_id=2, training_status=TrainingStatus.TRAINED, consecutive_weeks_unscheduled=0),
        }
        workforce = Workforce(operators=operators, next_operator_id=3)

        new_workforce, terminated = manager.process_week_end(workforce)

        assert terminated == [1]
        assert 1 not in new_workforce.operators


class TestIntegration:
    """Integration tests for full workforce flow."""

    def test_full_week_workforce_flow(self):
        """Test a complete week's workforce operations."""
        manager = OperatorManager(random_seed=42)

        # Start with 5 untrained operators
        workforce = Workforce.create_initial(num_operators=5, num_trained=0)

        # Week 1 start: Send 2 operators to training
        workforce, training_result, hired = manager.process_week_start(
            workforce,
            operators_to_train=[1, 2],
            operators_to_hire=0,
        )

        assert len(training_result.operators_sent_to_training) == 2

        # Schedule remaining operators
        machines = [
            create_machine(1, 3, "X'", 40.0),
            create_machine(2, 4, "Y'", 40.0),
            create_machine(5, 5, "X", 50.0),
        ]

        workforce, scheduling_result = manager.schedule_operators(workforce, machines)

        # All operators except 1, 2 (in training) should be scheduled
        assert len(scheduling_result.scheduled_operators) == 3
        assert scheduling_result.operators_in_training == [1, 2]
        assert scheduling_result.unscheduled_operator_ids == []

        # Calculate costs
        costs = manager.calculate_weekly_costs(
            workforce,
            operators_trained=len(training_result.operators_sent_to_training),
        )

        assert costs.training_cost == 2000.0  # 2 * 1000

        # Week 1 end: no terminations expected
        workforce, terminated = manager.process_week_end(workforce)
        assert terminated == []

        # Week 2 start: operators 1, 2 complete training
        workforce, training_result, hired = manager.process_week_start(
            workforce,
            operators_to_train=[],
            operators_to_hire=0,
        )

        assert 1 in training_result.operators_completed_training
        assert 2 in training_result.operators_completed_training
        assert workforce.operators[1].training_status == TrainingStatus.TRAINED
        assert workforce.operators[2].training_status == TrainingStatus.TRAINED

    def test_layoff_to_termination_flow(self):
        """Test the full layoff to termination flow over multiple weeks."""
        manager = OperatorManager(random_seed=42)
        workforce = Workforce.create_initial(num_operators=3, num_trained=3)

        # Week 1: Schedule only operators 1, 2
        machines = [
            create_machine(1, 1, "X'", 40.0),
            create_machine(2, 2, "Y'", 40.0),
        ]
        workforce, result1 = manager.schedule_operators(workforce, machines)

        # Operator 3 is unscheduled for first week
        assert workforce.operators[3].consecutive_weeks_unscheduled == 1
        assert 3 in result1.unscheduled_operator_ids

        # Week 1 end: no terminations yet
        workforce, terminated1 = manager.process_week_end(workforce)
        assert terminated1 == []

        # Week 2: Still don't schedule operator 3
        workforce, result2 = manager.schedule_operators(workforce, machines)

        # Operator 3 unscheduled for second week
        assert workforce.operators[3].consecutive_weeks_unscheduled == 2

        # Week 2 end: operator 3 should be terminated
        workforce, terminated2 = manager.process_week_end(workforce)
        assert terminated2 == [3]
        assert 3 not in workforce.operators
        assert len(workforce.operators) == 2
