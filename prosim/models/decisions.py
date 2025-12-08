"""
Decision models for PROSIM simulation.

Represents the weekly decisions submitted via DECS files.
Format from original:
  Line 1: [Week] [Company#] [QualityBudget] [MaintBudget] [RMOrderReg] [RMOrderExp]
  Line 2: [PartOrderX'] [PartOrderY'] [PartOrderZ']
  Lines 3-11: [MachineID] [TrainFlag] [PartType] [ScheduledHours]
"""

from pydantic import BaseModel, Field, field_validator


class MachineDecision(BaseModel):
    """Decision for a single machine assignment.

    Maps to one line in DECS file (lines 3-11).
    """

    machine_id: int = Field(ge=1, description="Machine/operator identifier")
    send_for_training: bool = Field(
        default=False,
        description="Whether to send operator for training (0=train, 1=work)"
    )
    part_type: int = Field(
        ge=1,
        le=3,
        description="Part/product type (1=X/X', 2=Y/Y', 3=Z/Z')"
    )
    scheduled_hours: float = Field(
        ge=0,
        le=50,
        description="Hours to schedule (0-50)"
    )

    @field_validator("send_for_training", mode="before")
    @classmethod
    def parse_train_flag(cls, v: int | bool) -> bool:
        """Parse train flag from DECS format.

        In DECS files: 0 = send for training, 1 = already trained/working
        We invert this for clarity: True = send for training
        """
        if isinstance(v, bool):
            return v
        return v == 0  # 0 means "send for training"

    @property
    def part_type_str(self) -> str:
        """Get part type as string based on machine department.

        Note: Caller needs to determine if this is parts or assembly
        to get the correct string (X' vs X).
        """
        mapping = {1: "X", 2: "Y", 3: "Z"}
        return mapping.get(self.part_type, "X")

    @property
    def is_scheduled(self) -> bool:
        """Check if machine is scheduled for production."""
        return self.scheduled_hours > 0 and not self.send_for_training


class PartOrders(BaseModel):
    """Orders for purchased finished parts.

    Maps to line 2 of DECS file.
    """

    x_prime: float = Field(default=0.0, ge=0, description="X' parts to order")
    y_prime: float = Field(default=0.0, ge=0, description="Y' parts to order")
    z_prime: float = Field(default=0.0, ge=0, description="Z' parts to order")

    @classmethod
    def from_list(cls, values: list[float]) -> "PartOrders":
        """Create from list of three values."""
        if len(values) != 3:
            raise ValueError(f"Expected 3 values, got {len(values)}")
        return cls(x_prime=values[0], y_prime=values[1], z_prime=values[2])

    def get(self, part_type: str) -> float:
        """Get order amount by part type."""
        mapping = {
            "X'": self.x_prime,
            "Y'": self.y_prime,
            "Z'": self.z_prime,
            "1": self.x_prime,
            "2": self.y_prime,
            "3": self.z_prime,
        }
        return mapping.get(part_type, 0.0)


class Decisions(BaseModel):
    """Complete weekly decisions for a company.

    Represents the full DECS file submission.
    """

    week: int = Field(ge=1, description="Simulation week number")
    company_id: int = Field(ge=1, description="Company identifier")
    quality_budget: float = Field(
        ge=0,
        description="Budget for quality planning"
    )
    maintenance_budget: float = Field(
        ge=0,
        description="Budget for plant maintenance"
    )
    raw_materials_regular: float = Field(
        default=0.0,
        ge=0,
        description="Regular raw materials order (3 week lead)"
    )
    raw_materials_expedited: float = Field(
        default=0.0,
        ge=0,
        description="Expedited raw materials order (1 week lead, +$1200)"
    )
    part_orders: PartOrders = Field(
        default_factory=PartOrders,
        description="Purchased parts orders"
    )
    machine_decisions: list[MachineDecision] = Field(
        default_factory=list,
        description="Machine assignments (9 machines)"
    )

    @field_validator("machine_decisions")
    @classmethod
    def validate_machine_count(
        cls, v: list[MachineDecision]
    ) -> list[MachineDecision]:
        """Ensure we have exactly 9 machine decisions."""
        if len(v) != 9:
            raise ValueError(f"Expected 9 machine decisions, got {len(v)}")
        return v

    def get_machine_decision(self, machine_id: int) -> MachineDecision | None:
        """Get decision for a specific machine."""
        for md in self.machine_decisions:
            if md.machine_id == machine_id:
                return md
        return None

    @property
    def parts_department_decisions(self) -> list[MachineDecision]:
        """Get decisions for Parts Department machines (1-4)."""
        return [md for md in self.machine_decisions if md.machine_id <= 4]

    @property
    def assembly_department_decisions(self) -> list[MachineDecision]:
        """Get decisions for Assembly Department machines (5-9)."""
        return [md for md in self.machine_decisions if md.machine_id > 4]

    @property
    def total_raw_materials_ordered(self) -> float:
        """Total raw materials ordered this week."""
        return self.raw_materials_regular + self.raw_materials_expedited

    @property
    def total_parts_ordered(self) -> float:
        """Total purchased parts ordered this week."""
        return (
            self.part_orders.x_prime
            + self.part_orders.y_prime
            + self.part_orders.z_prime
        )

    @property
    def operators_training(self) -> list[int]:
        """List of machine IDs where operators are sent for training."""
        return [md.machine_id for md in self.machine_decisions if md.send_for_training]

    @property
    def total_scheduled_hours(self) -> float:
        """Total hours scheduled across all machines."""
        return sum(
            md.scheduled_hours
            for md in self.machine_decisions
            if not md.send_for_training
        )

    @classmethod
    def create_default(cls, week: int, company_id: int = 1) -> "Decisions":
        """Create a default decisions object with minimal values.

        Useful for testing or creating empty templates.
        """
        machine_decisions = [
            MachineDecision(
                machine_id=i,
                send_for_training=False,
                part_type=((i - 1) % 3) + 1,  # Cycle through 1, 2, 3
                scheduled_hours=0.0,
            )
            for i in range(1, 10)
        ]
        return cls(
            week=week,
            company_id=company_id,
            quality_budget=0.0,
            maintenance_budget=0.0,
            raw_materials_regular=0.0,
            raw_materials_expedited=0.0,
            part_orders=PartOrders(),
            machine_decisions=machine_decisions,
        )
