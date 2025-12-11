"""
Workforce/operator management for PROSIM simulation.

This module handles:
- Operator efficiency calculations from training matrix
- Training level tracking and progression (0-10)
- Quality tier management (fixed at hire)
- Scheduling and unscheduling operators to machines
- Consecutive unscheduled week tracking (layoff/termination)
- Hiring and termination logic
- Workforce cost calculations

The efficiency model (verified Dec 2025):
    - Each operator has quality_tier (0-9): fixed innate ability at hire
    - Each operator has training_level (0-10): advances with work
    - Efficiency = TRAINING_MATRIX[tier][level] / 100.0
    - Range: ~20% (tier 0, level 0) to ~120% (tier 9, level 10)
    - Operators in training class: 0% productive (unavailable that week)
"""

import random
from dataclasses import dataclass
from typing import Optional

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.models.machines import Machine
from prosim.models.operators import (
    Department,
    MAX_QUALITY_TIER,
    MIN_QUALITY_TIER,
    Operator,
    TrainingStatus,
    Workforce,
)


@dataclass
class OperatorEfficiencyResult:
    """Result of efficiency calculation for an operator."""

    operator_id: int
    scheduled_hours: float
    productive_hours: float
    efficiency: float
    training_status: TrainingStatus
    is_in_training: bool


@dataclass
class WorkforceSchedulingResult:
    """Result of scheduling the workforce for a week."""

    scheduled_operators: list[OperatorEfficiencyResult]
    unscheduled_operator_ids: list[int]
    operators_in_training: list[int]
    total_scheduled_hours: float
    total_productive_hours: float


@dataclass
class WorkforceCostResult:
    """Workforce-related costs for a week."""

    training_cost: float
    hiring_cost: float
    layoff_cost: float
    termination_cost: float
    total_cost: float
    operators_hired: int
    operators_terminated: int
    operators_trained: int
    operators_laid_off: int


@dataclass
class TrainingResult:
    """Result of processing training for a week."""

    operators_sent_to_training: list[int]
    operators_completed_training: list[int]
    training_cost: float


class OperatorManager:
    """Manages all operator/workforce operations for a company.

    This class coordinates:
    1. Efficiency calculations based on training status
    2. Training status progression (untrained -> training -> trained)
    3. Scheduling operators to machines
    4. Tracking unscheduled weeks for layoff/termination
    5. Hiring new operators when needed
    6. Cost calculations for workforce
    """

    def __init__(
        self,
        config: Optional[ProsimConfig] = None,
        random_seed: Optional[int] = None,
    ):
        """Initialize operator manager.

        Args:
            config: Simulation configuration (uses defaults if None)
            random_seed: Random seed for reproducible efficiency calculations
        """
        self.config = config or get_default_config()
        self._rng = random.Random(random_seed)

    def set_random_seed(self, seed: int) -> None:
        """Set random seed for reproducible results.

        Args:
            seed: Random seed
        """
        self._rng = random.Random(seed)

    def calculate_efficiency(
        self,
        operator: Operator,
    ) -> float:
        """Calculate efficiency for an operator.

        Efficiency is looked up from the training matrix based on the operator's
        quality tier and training level. This replaces the old random-range model.

        Args:
            operator: The operator to calculate efficiency for

        Returns:
            Efficiency as a float (e.g., 1.03 for 103% efficiency)
            Returns 0.0 if operator is in training class
        """
        # Efficiency is now a property that uses the training matrix
        return operator.efficiency

    def calculate_productive_hours(
        self,
        operator: Operator,
        scheduled_hours: float,
    ) -> OperatorEfficiencyResult:
        """Calculate productive hours for an operator given scheduled hours.

        Args:
            operator: The operator
            scheduled_hours: Hours the operator is scheduled to work

        Returns:
            OperatorEfficiencyResult with efficiency and productive hours
        """
        efficiency = self.calculate_efficiency(operator)
        productive_hours = scheduled_hours * efficiency

        return OperatorEfficiencyResult(
            operator_id=operator.operator_id,
            scheduled_hours=scheduled_hours,
            productive_hours=productive_hours,
            efficiency=efficiency,
            training_status=operator.training_status,
            is_in_training=operator.training_status == TrainingStatus.TRAINING,
        )

    def send_to_training(
        self,
        workforce: Workforce,
        operator_ids: list[int],
    ) -> tuple[Workforce, TrainingResult]:
        """Send operators to training class for this week.

        Operators in training class produce 0 productive hours but gain +1
        training level at the end of the week (up to max level 10).

        Training can be sent at any level - it always advances training by 1.
        This matches the original PROSIM behavior where training is beneficial
        even for partially trained operators.

        Args:
            workforce: Current workforce state
            operator_ids: List of operator IDs to send to training

        Returns:
            Tuple of (updated workforce, training result)
        """
        current_workforce = workforce
        sent_to_training: list[int] = []
        training_cost = 0.0

        for op_id in operator_ids:
            operator = current_workforce.get_operator(op_id)
            if operator is None:
                continue

            # Can train any operator not already in training and not at max level
            if not operator.is_in_training_class and not operator.is_fully_trained:
                updated_operator = operator.send_to_training_class()
                new_operators = {
                    **current_workforce.operators,
                    op_id: updated_operator,
                }
                current_workforce = current_workforce.model_copy(
                    update={"operators": new_operators}
                )
                sent_to_training.append(op_id)
                training_cost += self.config.workforce.costs.training_cost_per_worker

        result = TrainingResult(
            operators_sent_to_training=sent_to_training,
            operators_completed_training=[],  # Completed in process_training_completion
            training_cost=training_cost,
        )

        return current_workforce, result

    def process_training_completion(
        self,
        workforce: Workforce,
    ) -> tuple[Workforce, list[int]]:
        """Complete training class for operators who were in training.

        Called at the start of a week to graduate operators from training class.
        Each operator gains +1 training level (up to max 10).

        Args:
            workforce: Current workforce state

        Returns:
            Tuple of (updated workforce, list of operator IDs who completed training)
        """
        current_workforce = workforce
        completed: list[int] = []

        for op_id, operator in workforce.operators.items():
            if operator.is_in_training_class:
                updated_operator = operator.complete_training_class()
                new_operators = {
                    **current_workforce.operators,
                    op_id: updated_operator,
                }
                current_workforce = current_workforce.model_copy(
                    update={"operators": new_operators}
                )
                completed.append(op_id)

        return current_workforce, completed

    def schedule_operators(
        self,
        workforce: Workforce,
        machines: list[Machine],
    ) -> tuple[Workforce, WorkforceSchedulingResult]:
        """Schedule operators based on machine assignments.

        Updates operator department assignments and calculates efficiency.
        Operators not assigned to any machine are marked as unscheduled.

        Args:
            workforce: Current workforce state
            machines: List of machines with their assignments for the week

        Returns:
            Tuple of (updated workforce, scheduling result)
        """
        # Track which operators are scheduled
        scheduled_operator_ids: set[int] = set()
        scheduled_results: list[OperatorEfficiencyResult] = []

        current_workforce = workforce

        for machine in machines:
            assignment = machine.assignment
            if assignment is None or assignment.operator_id is None:
                continue

            operator = current_workforce.get_operator(assignment.operator_id)
            if operator is None:
                continue

            scheduled_operator_ids.add(assignment.operator_id)

            # Determine department from machine
            department = (
                Department.PARTS
                if machine.machine_id <= self.config.simulation.parts_machines
                else Department.ASSEMBLY
            )

            # Schedule the operator
            updated_operator = operator.schedule(department)
            new_operators = {
                **current_workforce.operators,
                assignment.operator_id: updated_operator,
            }
            current_workforce = current_workforce.model_copy(
                update={"operators": new_operators}
            )

            # Calculate efficiency for this operator
            efficiency_result = self.calculate_productive_hours(
                updated_operator,
                assignment.scheduled_hours,
            )
            scheduled_results.append(efficiency_result)

        # Mark unscheduled operators
        unscheduled_ids: list[int] = []
        in_training_ids: list[int] = []

        for op_id, operator in current_workforce.operators.items():
            if op_id not in scheduled_operator_ids:
                if operator.is_in_training_class:
                    in_training_ids.append(op_id)
                else:
                    # Mark as unscheduled (increment consecutive weeks)
                    updated_operator = operator.unschedule()
                    new_operators = {
                        **current_workforce.operators,
                        op_id: updated_operator,
                    }
                    current_workforce = current_workforce.model_copy(
                        update={"operators": new_operators}
                    )
                    unscheduled_ids.append(op_id)

        # Calculate totals
        total_scheduled = sum(r.scheduled_hours for r in scheduled_results)
        total_productive = sum(r.productive_hours for r in scheduled_results)

        result = WorkforceSchedulingResult(
            scheduled_operators=scheduled_results,
            unscheduled_operator_ids=unscheduled_ids,
            operators_in_training=in_training_ids,
            total_scheduled_hours=total_scheduled,
            total_productive_hours=total_productive,
        )

        return current_workforce, result

    def hire_operators(
        self,
        workforce: Workforce,
        count: int,
        trained: bool = False,
    ) -> tuple[Workforce, list[Operator]]:
        """Hire new operators.

        Hired operators (10+) receive randomized quality tiers, unlike
        starting operators (1-9) who have fixed profiles.

        Args:
            workforce: Current workforce state
            count: Number of operators to hire
            trained: Whether to hire trained operators (default: untrained)

        Returns:
            Tuple of (updated workforce, list of newly hired operators)
        """
        current_workforce = workforce
        hired: list[Operator] = []

        for _ in range(count):
            # Randomize quality tier and proficiency for new hires (original PROSIM behavior)
            quality_tier = self._rng.randint(MIN_QUALITY_TIER, MAX_QUALITY_TIER)
            # Proficiency ranges from 0.85 to 1.15 for hired operators (estimated)
            proficiency = self._rng.uniform(0.85, 1.15)
            current_workforce, new_op = current_workforce.hire_operator(
                quality_tier=quality_tier, proficiency=proficiency, trained=trained
            )
            hired.append(new_op)

        return current_workforce, hired

    def process_terminations(
        self,
        workforce: Workforce,
    ) -> tuple[Workforce, list[int]]:
        """Process automatic terminations for operators unscheduled too long.

        Operators with 2+ consecutive unscheduled weeks are terminated.

        Args:
            workforce: Current workforce state

        Returns:
            Tuple of (updated workforce, list of terminated operator IDs)
        """
        terminated: list[int] = []
        current_workforce = workforce

        for op_id, operator in workforce.operators.items():
            if operator.should_be_terminated:
                current_workforce = current_workforce.terminate_operator(op_id)
                terminated.append(op_id)

        return current_workforce, terminated

    def calculate_weekly_costs(
        self,
        workforce: Workforce,
        operators_hired: int = 0,
        operators_trained: int = 0,
        operators_terminated: list[int] | None = None,
    ) -> WorkforceCostResult:
        """Calculate all workforce costs for a week.

        Args:
            workforce: Current workforce state
            operators_hired: Number of operators hired this week
            operators_trained: Number of operators sent to training
            operators_terminated: List of operator IDs terminated this week

        Returns:
            WorkforceCostResult with all cost breakdowns
        """
        if operators_terminated is None:
            operators_terminated = []

        costs = self.config.workforce.costs

        # Hiring cost
        hiring_cost = operators_hired * costs.hiring_cost

        # Training cost
        training_cost = operators_trained * costs.training_cost_per_worker

        # Count unscheduled (but not terminated) operators for layoff cost
        laid_off_count = 0
        for operator in workforce.active_operators:
            if (
                operator.department == Department.UNASSIGNED
                and not operator.is_in_training_class
                and operator.consecutive_weeks_unscheduled == 1
            ):
                # Only count first week of being unscheduled (before termination)
                laid_off_count += 1

        layoff_cost = laid_off_count * costs.layoff_cost_per_week

        # Termination cost
        termination_cost = len(operators_terminated) * costs.termination_cost

        total = hiring_cost + training_cost + layoff_cost + termination_cost

        return WorkforceCostResult(
            training_cost=training_cost,
            hiring_cost=hiring_cost,
            layoff_cost=layoff_cost,
            termination_cost=termination_cost,
            total_cost=total,
            operators_hired=operators_hired,
            operators_terminated=len(operators_terminated),
            operators_trained=operators_trained,
            operators_laid_off=laid_off_count,
        )

    def get_department_operators(
        self,
        workforce: Workforce,
        department: Department,
    ) -> list[Operator]:
        """Get all operators assigned to a department.

        Args:
            workforce: Current workforce state
            department: Department to filter by

        Returns:
            List of operators in the department
        """
        return [
            op for op in workforce.active_operators if op.department == department
        ]

    def get_available_operators(
        self,
        workforce: Workforce,
    ) -> list[Operator]:
        """Get operators available for scheduling.

        Excludes operators in training class.

        Args:
            workforce: Current workforce state

        Returns:
            List of operators available for work
        """
        return [
            op
            for op in workforce.active_operators
            if not op.is_in_training_class
        ]

    def process_week_start(
        self,
        workforce: Workforce,
        operators_to_train: list[int] | None = None,
        operators_to_hire: int = 0,
    ) -> tuple[Workforce, TrainingResult, list[Operator]]:
        """Process start of week operations.

        This handles:
        1. Complete training for operators who were in training
        2. Send new operators to training
        3. Hire new operators

        Args:
            workforce: Current workforce state
            operators_to_train: Operator IDs to send to training this week
            operators_to_hire: Number of new operators to hire

        Returns:
            Tuple of (updated workforce, training result, newly hired operators)
        """
        if operators_to_train is None:
            operators_to_train = []

        # Complete training for operators who were in training
        current_workforce, completed = self.process_training_completion(workforce)

        # Send new operators to training
        current_workforce, training_result = self.send_to_training(
            current_workforce, operators_to_train
        )
        training_result = TrainingResult(
            operators_sent_to_training=training_result.operators_sent_to_training,
            operators_completed_training=completed,
            training_cost=training_result.training_cost,
        )

        # Hire new operators
        current_workforce, hired = self.hire_operators(
            current_workforce, operators_to_hire
        )

        return current_workforce, training_result, hired

    def process_week_end(
        self,
        workforce: Workforce,
    ) -> tuple[Workforce, list[int]]:
        """Process end of week operations.

        This handles automatic terminations for long-unscheduled operators.

        Args:
            workforce: Current workforce state

        Returns:
            Tuple of (updated workforce, terminated operator IDs)
        """
        return self.process_terminations(workforce)
