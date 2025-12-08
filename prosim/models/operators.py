"""
Operator (workforce) models for PROSIM simulation.

Operators are assigned to machines and have:
- Training status (trained vs untrained)
- Efficiency (affects productive hours)
- Consecutive weeks tracking (for layoff/termination costs)
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TrainingStatus(str, Enum):
    """Operator training status."""

    UNTRAINED = "untrained"
    TRAINING = "training"  # Currently in training this week
    TRAINED = "trained"


class Department(str, Enum):
    """Department assignment for operators."""

    PARTS = "parts"
    ASSEMBLY = "assembly"
    UNASSIGNED = "unassigned"


class Operator(BaseModel):
    """Represents a single operator/worker.

    Operators are identified by number (1-9 in original game).
    Training status affects productive hours and costs.
    Consecutive unscheduled weeks affect layoff/termination costs.
    """

    operator_id: int = Field(ge=1, description="Unique operator identifier")
    training_status: TrainingStatus = Field(
        default=TrainingStatus.UNTRAINED,
        description="Current training status"
    )
    consecutive_weeks_unscheduled: int = Field(
        default=0,
        ge=0,
        description="Consecutive weeks not scheduled (for layoff costs)"
    )
    department: Department = Field(
        default=Department.UNASSIGNED,
        description="Current department assignment"
    )
    is_new_hire: bool = Field(
        default=False,
        description="Whether this operator was hired this week"
    )

    @property
    def is_trained(self) -> bool:
        """Check if operator is trained."""
        return self.training_status == TrainingStatus.TRAINED

    @property
    def efficiency_range(self) -> tuple[float, float]:
        """Get efficiency range based on training status.

        Returns (min_efficiency, max_efficiency) tuple.
        Trained: 95-100%
        Untrained: 60-90%
        Training: 0% (not working this week)
        """
        if self.training_status == TrainingStatus.TRAINED:
            return (0.95, 1.00)
        elif self.training_status == TrainingStatus.TRAINING:
            return (0.0, 0.0)  # Not productive while training
        else:
            return (0.60, 0.90)

    @property
    def should_be_terminated(self) -> bool:
        """Check if operator should be terminated (2+ consecutive unscheduled weeks)."""
        return self.consecutive_weeks_unscheduled >= 2

    def send_to_training(self) -> "Operator":
        """Send operator to training this week."""
        return self.model_copy(update={"training_status": TrainingStatus.TRAINING})

    def complete_training(self) -> "Operator":
        """Mark operator as trained after training week."""
        return self.model_copy(update={"training_status": TrainingStatus.TRAINED})

    def schedule(self, department: Department) -> "Operator":
        """Schedule operator for work this week."""
        return self.model_copy(
            update={
                "consecutive_weeks_unscheduled": 0,
                "department": department,
                "is_new_hire": False,
            }
        )

    def unschedule(self) -> "Operator":
        """Mark operator as not scheduled this week."""
        return self.model_copy(
            update={
                "consecutive_weeks_unscheduled": self.consecutive_weeks_unscheduled + 1,
                "department": Department.UNASSIGNED,
            }
        )


class Workforce(BaseModel):
    """Manages all operators for a company.

    Tracks hiring, training, scheduling, and termination.
    """

    operators: dict[int, Operator] = Field(
        default_factory=dict,
        description="Map of operator_id to Operator"
    )
    next_operator_id: int = Field(
        default=1,
        ge=1,
        description="Next ID to assign to new hires"
    )

    def get_operator(self, operator_id: int) -> Optional[Operator]:
        """Get operator by ID."""
        return self.operators.get(operator_id)

    def hire_operator(self, trained: bool = False) -> tuple["Workforce", Operator]:
        """Hire a new operator.

        Returns updated workforce and the new operator.
        """
        new_op = Operator(
            operator_id=self.next_operator_id,
            training_status=TrainingStatus.TRAINED if trained else TrainingStatus.UNTRAINED,
            is_new_hire=True,
        )
        new_operators = {**self.operators, self.next_operator_id: new_op}
        new_workforce = self.model_copy(
            update={
                "operators": new_operators,
                "next_operator_id": self.next_operator_id + 1,
            }
        )
        return new_workforce, new_op

    def terminate_operator(self, operator_id: int) -> "Workforce":
        """Terminate an operator."""
        new_operators = {k: v for k, v in self.operators.items() if k != operator_id}
        return self.model_copy(update={"operators": new_operators})

    @property
    def active_operators(self) -> list[Operator]:
        """Get all active (not terminated) operators."""
        return list(self.operators.values())

    @property
    def trained_operators(self) -> list[Operator]:
        """Get all trained operators."""
        return [op for op in self.operators.values() if op.is_trained]

    @property
    def untrained_operators(self) -> list[Operator]:
        """Get all untrained operators."""
        return [
            op for op in self.operators.values()
            if op.training_status == TrainingStatus.UNTRAINED
        ]

    @property
    def operators_in_training(self) -> list[Operator]:
        """Get operators currently in training."""
        return [
            op for op in self.operators.values()
            if op.training_status == TrainingStatus.TRAINING
        ]

    @property
    def unscheduled_operators(self) -> list[Operator]:
        """Get operators not scheduled this week."""
        return [
            op for op in self.operators.values()
            if op.department == Department.UNASSIGNED
        ]

    def count_by_status(self) -> dict[TrainingStatus, int]:
        """Count operators by training status."""
        counts = {status: 0 for status in TrainingStatus}
        for op in self.operators.values():
            counts[op.training_status] += 1
        return counts

    @classmethod
    def create_initial(cls, num_operators: int = 9, num_trained: int = 0) -> "Workforce":
        """Create initial workforce for a new game.

        Args:
            num_operators: Total number of operators to create
            num_trained: Number of operators that start trained

        Returns:
            Workforce with the specified operators
        """
        operators = {}
        for i in range(1, num_operators + 1):
            operators[i] = Operator(
                operator_id=i,
                training_status=(
                    TrainingStatus.TRAINED if i <= num_trained
                    else TrainingStatus.UNTRAINED
                ),
            )
        return cls(operators=operators, next_operator_id=num_operators + 1)
