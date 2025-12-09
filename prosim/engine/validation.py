"""
Decision validation for PROSIM.

Validates weekly decisions before they are processed by the simulation.
Provides helpful error messages for invalid inputs.
"""

from dataclasses import dataclass, field
from typing import Optional

from prosim.models.company import Company
from prosim.models.decisions import Decisions, MachineDecision


@dataclass
class ValidationError:
    """A single validation error."""

    field: str
    message: str
    value: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        msg = f"{self.field}: {self.message}"
        if self.value:
            msg += f" (got: {self.value})"
        if self.suggestion:
            msg += f" - {self.suggestion}"
        return msg


@dataclass
class ValidationResult:
    """Result of validating decisions."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(valid=True)

    @classmethod
    def failure(cls, errors: list[ValidationError]) -> "ValidationResult":
        """Create a failed validation result."""
        return cls(valid=False, errors=errors)

    def add_error(self, error: ValidationError) -> None:
        """Add an error and mark as invalid."""
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: ValidationError) -> None:
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(warning)

    def merge(self, other: "ValidationResult") -> None:
        """Merge another result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.valid:
            self.valid = False


def validate_decisions(
    decisions: Decisions,
    company: Company,
    strict: bool = False,
) -> ValidationResult:
    """Validate decisions against company state.

    Args:
        decisions: Decisions to validate
        company: Current company state
        strict: If True, treat warnings as errors

    Returns:
        ValidationResult with any errors/warnings
    """
    result = ValidationResult(valid=True)

    # Validate week matches
    result.merge(_validate_week(decisions, company))

    # Validate budgets
    result.merge(_validate_budgets(decisions))

    # Validate orders
    result.merge(_validate_orders(decisions, company))

    # Validate machine assignments
    result.merge(_validate_machine_assignments(decisions, company))

    # In strict mode, treat warnings as errors
    if strict:
        for warning in result.warnings:
            result.add_error(warning)
        result.warnings = []

    return result


def _validate_week(decisions: Decisions, company: Company) -> ValidationResult:
    """Validate decision week matches company week."""
    result = ValidationResult(valid=True)

    if decisions.week != company.current_week:
        result.add_error(ValidationError(
            field="week",
            message="Decision week doesn't match company's current week",
            value=f"decision={decisions.week}, company={company.current_week}",
            suggestion="Ensure you're submitting decisions for the current week",
        ))

    if decisions.company_id != company.company_id:
        result.add_error(ValidationError(
            field="company_id",
            message="Decision company ID doesn't match",
            value=f"decision={decisions.company_id}, company={company.company_id}",
        ))

    return result


def _validate_budgets(decisions: Decisions) -> ValidationResult:
    """Validate budget values."""
    result = ValidationResult(valid=True)

    # Quality budget validation
    if decisions.quality_budget < 0:
        result.add_error(ValidationError(
            field="quality_budget",
            message="Quality budget cannot be negative",
            value=str(decisions.quality_budget),
        ))
    elif decisions.quality_budget > 10000:
        result.add_warning(ValidationError(
            field="quality_budget",
            message="Quality budget seems unusually high",
            value=str(decisions.quality_budget),
            suggestion="Typical budgets are $0-$5,000",
        ))

    # Maintenance budget validation
    if decisions.maintenance_budget < 0:
        result.add_error(ValidationError(
            field="maintenance_budget",
            message="Maintenance budget cannot be negative",
            value=str(decisions.maintenance_budget),
        ))
    elif decisions.maintenance_budget > 10000:
        result.add_warning(ValidationError(
            field="maintenance_budget",
            message="Maintenance budget seems unusually high",
            value=str(decisions.maintenance_budget),
            suggestion="Typical budgets are $0-$5,000",
        ))

    return result


def _validate_orders(decisions: Decisions, company: Company) -> ValidationResult:
    """Validate order quantities."""
    result = ValidationResult(valid=True)

    # Raw materials validation
    if decisions.raw_materials_regular < 0:
        result.add_error(ValidationError(
            field="raw_materials_regular",
            message="Regular raw materials order cannot be negative",
            value=str(decisions.raw_materials_regular),
        ))

    if decisions.raw_materials_expedited < 0:
        result.add_error(ValidationError(
            field="raw_materials_expedited",
            message="Expedited raw materials order cannot be negative",
            value=str(decisions.raw_materials_expedited),
        ))

    # Warning for expedited without regular
    if decisions.raw_materials_expedited > 0 and decisions.raw_materials_regular == 0:
        result.add_warning(ValidationError(
            field="raw_materials_expedited",
            message="Using expedited orders is expensive (+$1,200)",
            suggestion="Consider regular orders (3-week lead) for non-urgent needs",
        ))

    # Parts orders validation
    parts = decisions.part_orders
    for part_type, value in [
        ("x_prime", parts.x_prime),
        ("y_prime", parts.y_prime),
        ("z_prime", parts.z_prime),
    ]:
        if value < 0:
            result.add_error(ValidationError(
                field=f"part_orders.{part_type}",
                message=f"Parts order cannot be negative",
                value=str(value),
            ))

    # Warning for buying parts vs manufacturing
    total_parts_ordered = decisions.total_parts_ordered
    if total_parts_ordered > 1000:
        result.add_warning(ValidationError(
            field="part_orders",
            message="Buying large quantities of parts may be expensive",
            value=str(total_parts_ordered),
            suggestion="Consider manufacturing parts in-house when possible",
        ))

    return result


def _validate_machine_assignments(
    decisions: Decisions,
    company: Company,
) -> ValidationResult:
    """Validate machine assignments."""
    result = ValidationResult(valid=True)

    # Check we have exactly 9 machines
    if len(decisions.machine_decisions) != 9:
        result.add_error(ValidationError(
            field="machine_decisions",
            message="Must have exactly 9 machine decisions",
            value=str(len(decisions.machine_decisions)),
        ))
        return result  # Can't validate further

    # Track which operators are assigned
    scheduled_hours_by_type: dict[str, float] = {
        "X'": 0, "Y'": 0, "Z'": 0,
        "X": 0, "Y": 0, "Z": 0,
    }

    for md in decisions.machine_decisions:
        result.merge(_validate_machine_decision(md, company))

        # Track scheduled production
        if md.is_scheduled:
            dept = "parts" if md.machine_id <= 4 else "assembly"
            type_suffix = "'" if dept == "parts" else ""
            type_map = {1: "X", 2: "Y", 3: "Z"}
            part_type = type_map[md.part_type] + type_suffix
            scheduled_hours_by_type[part_type] += md.scheduled_hours

    # Check for unbalanced production
    parts_hours = sum(v for k, v in scheduled_hours_by_type.items() if k.endswith("'"))
    assembly_hours = sum(v for k, v in scheduled_hours_by_type.items() if not k.endswith("'"))

    if parts_hours > 0 and assembly_hours == 0:
        result.add_warning(ValidationError(
            field="machine_decisions",
            message="Parts are being produced but no assembly is scheduled",
            suggestion="Schedule assembly machines to produce finished products",
        ))

    # Check for training too many operators
    training_count = len(decisions.operators_training)
    if training_count > 3:
        result.add_warning(ValidationError(
            field="machine_decisions",
            message=f"Training {training_count} operators at once will significantly reduce production",
            suggestion="Consider training 1-2 operators at a time",
        ))

    return result


def _validate_machine_decision(
    md: MachineDecision,
    company: Company,
) -> ValidationResult:
    """Validate a single machine decision."""
    result = ValidationResult(valid=True)

    # Machine ID validation
    if md.machine_id < 1 or md.machine_id > 9:
        result.add_error(ValidationError(
            field=f"machine_{md.machine_id}",
            message="Machine ID must be between 1 and 9",
            value=str(md.machine_id),
        ))
        return result

    # Hours validation
    if md.scheduled_hours < 0:
        result.add_error(ValidationError(
            field=f"machine_{md.machine_id}.scheduled_hours",
            message="Scheduled hours cannot be negative",
            value=str(md.scheduled_hours),
        ))
    elif md.scheduled_hours > 50:
        result.add_error(ValidationError(
            field=f"machine_{md.machine_id}.scheduled_hours",
            message="Scheduled hours cannot exceed 50 per week",
            value=str(md.scheduled_hours),
            suggestion="Maximum is 50 hours per week",
        ))

    # Part type validation
    if md.part_type < 1 or md.part_type > 3:
        result.add_error(ValidationError(
            field=f"machine_{md.machine_id}.part_type",
            message="Part type must be 1, 2, or 3 (X, Y, Z)",
            value=str(md.part_type),
        ))

    # Check operator status for training
    if md.send_for_training:
        operator = company.workforce.get_operator(md.machine_id)
        if operator and operator.is_trained:
            result.add_warning(ValidationError(
                field=f"machine_{md.machine_id}",
                message="Operator is already trained",
                suggestion="No benefit to training again",
            ))

    return result


def validate_decisions_with_messages(
    decisions: Decisions,
    company: Company,
) -> tuple[bool, list[str]]:
    """Validate decisions and return simple message list.

    Convenience function for CLI usage.

    Args:
        decisions: Decisions to validate
        company: Current company state

    Returns:
        Tuple of (valid, list of error/warning messages)
    """
    result = validate_decisions(decisions, company)

    messages = []
    for error in result.errors:
        messages.append(f"[ERROR] {error}")
    for warning in result.warnings:
        messages.append(f"[WARNING] {warning}")

    return result.valid, messages
