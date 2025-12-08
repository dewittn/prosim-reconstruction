"""
Machine models for PROSIM simulation.

Machines are assigned to departments:
- Parts Department: Machines 1-4 (produce parts X', Y', Z')
- Assembly Department: Machines 5-9 (produce products X, Y, Z)

Each machine can be assigned an operator and scheduled for production.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from prosim.models.operators import Department


class PartType(str, Enum):
    """Part types produced in Parts Department."""

    X_PRIME = "X'"
    Y_PRIME = "Y'"
    Z_PRIME = "Z'"


class ProductType(str, Enum):
    """Product types produced in Assembly Department."""

    X = "X"
    Y = "Y"
    Z = "Z"


# Maps part type code (from DECS file) to PartType/ProductType
PART_TYPE_CODES = {
    1: PartType.X_PRIME,
    2: PartType.Y_PRIME,
    3: PartType.Z_PRIME,
}

PRODUCT_TYPE_CODES = {
    1: ProductType.X,
    2: ProductType.Y,
    3: ProductType.Z,
}


class MachineAssignment(BaseModel):
    """Represents a machine's assignment for a week.

    Includes operator, part/product type, and scheduled hours.
    """

    operator_id: Optional[int] = Field(
        default=None,
        description="Assigned operator ID (None if unassigned)"
    )
    part_type: Optional[str] = Field(
        default=None,
        description="Part or product type to produce"
    )
    scheduled_hours: float = Field(
        default=0.0,
        ge=0,
        le=50,  # Max 50 hours per week
        description="Hours scheduled for production"
    )
    send_for_training: bool = Field(
        default=False,
        description="Whether operator should be sent for training"
    )


class Machine(BaseModel):
    """Represents a single machine.

    Machines are identified by number and assigned to departments.
    Parts machines: 1-4
    Assembly machines: 5-9 (or 1-5 in some numbering schemes)
    """

    machine_id: int = Field(ge=1, description="Unique machine identifier")
    department: Department = Field(description="Department this machine belongs to")
    assignment: Optional[MachineAssignment] = Field(
        default=None,
        description="Current week's assignment"
    )
    needs_repair: bool = Field(
        default=False,
        description="Whether machine broke down and needed repair"
    )
    setup_hours: float = Field(
        default=0.0,
        ge=0,
        description="Setup time if switching product types"
    )
    last_part_type: Optional[str] = Field(
        default=None,
        description="Part type produced last week (for setup calculation)"
    )

    @property
    def is_parts_machine(self) -> bool:
        """Check if this is a Parts Department machine."""
        return self.department == Department.PARTS

    @property
    def is_assembly_machine(self) -> bool:
        """Check if this is an Assembly Department machine."""
        return self.department == Department.ASSEMBLY

    @property
    def is_assigned(self) -> bool:
        """Check if machine has an assignment this week."""
        return self.assignment is not None and self.assignment.scheduled_hours > 0

    def assign(
        self,
        operator_id: int,
        part_type: str,
        scheduled_hours: float,
        send_for_training: bool = False,
    ) -> "Machine":
        """Create assignment for this machine."""
        return self.model_copy(
            update={
                "assignment": MachineAssignment(
                    operator_id=operator_id,
                    part_type=part_type,
                    scheduled_hours=scheduled_hours,
                    send_for_training=send_for_training,
                )
            }
        )

    def clear_assignment(self) -> "Machine":
        """Clear current assignment."""
        return self.model_copy(update={"assignment": None})

    def calculate_setup_time(self, new_part_type: str, default_setup: float = 2.0) -> float:
        """Calculate setup time if switching part types.

        Args:
            new_part_type: The part type to produce this week
            default_setup: Default setup time in hours

        Returns:
            Setup time in hours (0 if no change)
        """
        if self.last_part_type is None or self.last_part_type == new_part_type:
            return 0.0
        return default_setup

    def advance_week(self) -> "Machine":
        """Prepare machine for next week.

        Updates last_part_type and clears assignment.
        """
        new_last_part = (
            self.assignment.part_type
            if self.assignment and self.assignment.part_type
            else self.last_part_type
        )
        return self.model_copy(
            update={
                "assignment": None,
                "needs_repair": False,
                "setup_hours": 0.0,
                "last_part_type": new_last_part,
            }
        )


class MachineFloor(BaseModel):
    """Manages all machines in the factory.

    Default configuration:
    - Parts Department: 4 machines (IDs 1-4)
    - Assembly Department: 5 machines (IDs 5-9)
    """

    machines: dict[int, Machine] = Field(
        default_factory=dict,
        description="Map of machine_id to Machine"
    )

    def get_machine(self, machine_id: int) -> Optional[Machine]:
        """Get machine by ID."""
        return self.machines.get(machine_id)

    @property
    def parts_machines(self) -> list[Machine]:
        """Get all Parts Department machines."""
        return [m for m in self.machines.values() if m.is_parts_machine]

    @property
    def assembly_machines(self) -> list[Machine]:
        """Get all Assembly Department machines."""
        return [m for m in self.machines.values() if m.is_assembly_machine]

    @property
    def assigned_machines(self) -> list[Machine]:
        """Get all machines with assignments."""
        return [m for m in self.machines.values() if m.is_assigned]

    def update_machine(self, machine: Machine) -> "MachineFloor":
        """Update a machine in the floor."""
        new_machines = {**self.machines, machine.machine_id: machine}
        return self.model_copy(update={"machines": new_machines})

    def advance_week(self) -> "MachineFloor":
        """Prepare all machines for next week."""
        new_machines = {
            mid: m.advance_week() for mid, m in self.machines.items()
        }
        return self.model_copy(update={"machines": new_machines})

    @classmethod
    def create_default(
        cls,
        num_parts_machines: int = 4,
        num_assembly_machines: int = 5,
    ) -> "MachineFloor":
        """Create default machine floor configuration.

        Args:
            num_parts_machines: Number of Parts Department machines
            num_assembly_machines: Number of Assembly Department machines

        Returns:
            MachineFloor with the specified configuration
        """
        machines = {}

        # Parts Department machines (1 to num_parts_machines)
        for i in range(1, num_parts_machines + 1):
            machines[i] = Machine(machine_id=i, department=Department.PARTS)

        # Assembly Department machines (starts after parts machines)
        start_id = num_parts_machines + 1
        for i in range(start_id, start_id + num_assembly_machines):
            machines[i] = Machine(machine_id=i, department=Department.ASSEMBLY)

        return cls(machines=machines)


def part_type_from_code(code: int, department: Department) -> str:
    """Convert numeric part type code to string.

    Args:
        code: Numeric code (1, 2, or 3)
        department: Department to determine if part or product

    Returns:
        Part type string (X', Y', Z') or product type (X, Y, Z)
    """
    if department == Department.PARTS:
        return PART_TYPE_CODES.get(code, PartType.X_PRIME).value
    else:
        return PRODUCT_TYPE_CODES.get(code, ProductType.X).value
