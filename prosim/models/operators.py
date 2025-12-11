"""
Operator (workforce) models for PROSIM simulation.

TWO-COMPONENT EFFICIENCY MODEL (verified Dec 2025):
    Actual_Efficiency = Training_Matrix[tier][level] × Proficiency

Operators have:
- Quality tier (0-9): Determines training matrix row (time efficiency potential)
- Training level (0-10): Advances with weeks of work (time efficiency progress)
- Proficiency (0.8-1.2): Fixed multiplier at hire (output quality multiplier)
- Consecutive weeks tracking (for layoff/termination costs)

The two components were reverse-engineered from:
1. XTC game state files - stored efficiency and proficiency as separate floats
2. ProsimTable.xls Week 16 data - actual vs estimated efficiency ratios

Example: Operator 3 (the "expert")
- Quality tier 9, Training level I (8) → Matrix = 118%
- Proficiency = 1.122 (derived from 132.4% actual / 118% matrix)
- Combined efficiency = 118% × 1.122 = 132.4%
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from prosim.config.defaults import (
    TRAINING_MATRIX,
    get_operator_efficiency,
    STARTING_OPERATOR_PROFILES,
)


# Maximum training level (0=untrained, 10=fully trained "J")
MAX_TRAINING_LEVEL = 10

# Quality tier range
MIN_QUALITY_TIER = 0
MAX_QUALITY_TIER = 9


class TrainingStatus(str, Enum):
    """Operator training status (simplified view of training level)."""

    UNTRAINED = "untrained"  # training_level == 0
    TRAINING = "training"    # Currently in training this week (not working)
    TRAINED = "trained"      # training_level >= 1


class Department(str, Enum):
    """Department assignment for operators."""

    PARTS = "parts"
    ASSEMBLY = "assembly"
    UNASSIGNED = "unassigned"


class Operator(BaseModel):
    """Represents a single operator/worker.

    Operators are identified by number (1-9 in original game).
    Each operator has:
    - Quality tier (0-9): Determines training matrix row
    - Training level (0-10): Determines training matrix column
    - Proficiency (0.8-1.2): Fixed multiplier at hire

    Two-component efficiency model:
        efficiency = TRAINING_MATRIX[tier][level] × proficiency

    Training progression:
    - Level 0 = Untrained (~20-22% time efficiency)
    - Level 10 = Fully trained "J" (~109-120% time efficiency)
    - Advances +1 level per week of work (not while in training class)
    - Proficiency is fixed at hire and cannot change
    """

    operator_id: int = Field(ge=1, description="Unique operator identifier")
    name: Optional[str] = Field(
        default=None,
        description="Custom name for the operator (None uses default 'Operator N')"
    )
    quality_tier: int = Field(
        default=5,
        ge=MIN_QUALITY_TIER,
        le=MAX_QUALITY_TIER,
        description="Quality tier (0-9): Determines training matrix row"
    )
    training_level: int = Field(
        default=0,
        ge=0,
        le=MAX_TRAINING_LEVEL,
        description="Training level (0-10): Determines training matrix column"
    )
    proficiency: float = Field(
        default=1.0,
        ge=0.5,
        le=1.5,
        description="Proficiency multiplier (fixed at hire): 0.8-1.2 typical range"
    )
    is_in_training_class: bool = Field(
        default=False,
        description="Whether operator is in training class this week (not working)"
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
    def display_name(self) -> str:
        """Get display name (custom name or default 'Operator N')."""
        return self.name if self.name else f"Operator {self.operator_id}"

    def rename(self, new_name: Optional[str]) -> "Operator":
        """Rename the operator.

        Args:
            new_name: New name, or None to reset to default

        Returns:
            Updated Operator with new name
        """
        return self.model_copy(update={"name": new_name if new_name else None})

    @property
    def training_status(self) -> TrainingStatus:
        """Get simplified training status based on training_level and is_in_training_class."""
        if self.is_in_training_class:
            return TrainingStatus.TRAINING
        elif self.training_level >= 1:
            return TrainingStatus.TRAINED
        else:
            return TrainingStatus.UNTRAINED

    @property
    def is_trained(self) -> bool:
        """Check if operator has any training (level >= 1)."""
        return self.training_level >= 1

    @property
    def is_fully_trained(self) -> bool:
        """Check if operator is at maximum training level."""
        return self.training_level >= MAX_TRAINING_LEVEL

    @property
    def time_efficiency(self) -> float:
        """Get time efficiency component from training matrix.

        This is the first component of the two-component model.
        Returns decimal (e.g., 1.18 for 118% at tier 9, level I).
        """
        return get_operator_efficiency(self.quality_tier, self.training_level)

    @property
    def efficiency(self) -> float:
        """Get combined operator efficiency (two-component model).

        Combined efficiency = time_efficiency × proficiency

        Returns efficiency as decimal (e.g., 1.32 for 132%).
        If in training class, returns 0.0 (not productive).

        Example: Operator 3 (expert)
        - Time efficiency (tier 9, level I): 118%
        - Proficiency: 1.122
        - Combined: 118% × 1.122 = 132.4%
        """
        if self.is_in_training_class:
            return 0.0
        return self.time_efficiency * self.proficiency

    @property
    def max_efficiency(self) -> float:
        """Get maximum possible efficiency for this operator (at full training).

        Returns the combined efficiency at max training level.
        """
        max_time_eff = get_operator_efficiency(self.quality_tier, MAX_TRAINING_LEVEL)
        return max_time_eff * self.proficiency

    @property
    def training_level_name(self) -> str:
        """Get human-readable training level name."""
        from prosim.config.defaults import TRAINING_LEVELS
        return TRAINING_LEVELS[min(self.training_level, len(TRAINING_LEVELS) - 1)]

    @property
    def should_be_terminated(self) -> bool:
        """Check if operator should be terminated (2+ consecutive unscheduled weeks)."""
        return self.consecutive_weeks_unscheduled >= 2

    def send_to_training_class(self) -> "Operator":
        """Send operator to training class this week.

        Operator will not work this week but will gain +1 training level
        when training completes.
        """
        return self.model_copy(update={"is_in_training_class": True})

    def complete_training_class(self) -> "Operator":
        """Complete training class and advance training level.

        Called at end of week to graduate from training class.
        Advances training level by 1 (up to max).
        """
        new_level = min(self.training_level + 1, MAX_TRAINING_LEVEL)
        return self.model_copy(update={
            "is_in_training_class": False,
            "training_level": new_level,
        })

    def advance_training_from_work(self) -> "Operator":
        """Advance training level from working (on-the-job training).

        Called at end of week for operators who worked.
        Advances training level by 1 (up to max).
        """
        if self.is_in_training_class:
            return self  # Don't advance if in training class
        new_level = min(self.training_level + 1, MAX_TRAINING_LEVEL)
        return self.model_copy(update={"training_level": new_level})

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

    def hire_operator(
        self,
        quality_tier: int = 5,
        proficiency: float = 1.0,
        trained: bool = False,
    ) -> tuple["Workforce", Operator]:
        """Hire a new operator.

        Args:
            quality_tier: Quality tier (0-9) for the new hire. Default 5 (average).
            proficiency: Proficiency multiplier (0.8-1.2 typical). Default 1.0.
                        In original game, hired operators (10+) had randomized values.
            trained: If True, hire as trained (training_level=1). Default False.

        Returns updated workforce and the new operator.
        """
        new_op = Operator(
            operator_id=self.next_operator_id,
            quality_tier=quality_tier,
            proficiency=proficiency,
            training_level=1 if trained else 0,
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

    def rename_operator(self, operator_id: int, new_name: Optional[str]) -> "Workforce":
        """Rename an operator.

        Args:
            operator_id: ID of the operator to rename
            new_name: New name, or None to reset to default

        Returns:
            Updated Workforce with renamed operator
        """
        if operator_id not in self.operators:
            return self
        operator = self.operators[operator_id]
        renamed_operator = operator.rename(new_name)
        new_operators = {**self.operators, operator_id: renamed_operator}
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

        Starting operators (1-9) have FIXED profiles (quality_tier + proficiency)
        that are consistent across all game instances, derived from forensic
        analysis of ProsimTable.xls Week 16 data.

        Two-component model:
            efficiency = TRAINING_MATRIX[tier][level] × proficiency

        Notable operators:
        - Op 3: tier 9, proficiency 1.122 (EXPERT - reaches 132% at max training)
        - Op 6: tier 9, proficiency 0.836 (high tier but low proficiency)

        Args:
            num_operators: Total number of operators to create
            num_trained: Number of operators that start trained (training_level=1)

        Returns:
            Workforce with the specified operators
        """
        operators = {}
        for i in range(1, num_operators + 1):
            # Use fixed profiles for starting operators (1-9)
            if i in STARTING_OPERATOR_PROFILES:
                profile = STARTING_OPERATOR_PROFILES[i]
                quality_tier = profile["quality_tier"]
                proficiency = profile["proficiency"]
            else:
                # Hired operators (10+) get default values
                quality_tier = 5
                proficiency = 1.0

            operators[i] = Operator(
                operator_id=i,
                quality_tier=quality_tier,
                proficiency=proficiency,
                training_level=1 if i <= num_trained else 0,
            )
        return cls(operators=operators, next_operator_id=num_operators + 1)
