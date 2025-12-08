"""
DECS file parser for PROSIM simulation.

Parses decision input files in the original PROSIM format.

File format (space-separated values):
    Line 1: [Week] [Company#] [QualityBudget] [MaintBudget] [RMOrderReg] [RMOrderExp]
    Line 2: [PartOrderX'] [PartOrderY'] [PartOrderZ']
    Lines 3-11: [MachineID] [TrainFlag] [PartType] [ScheduledHours] (9 machines)
"""

from pathlib import Path
from typing import TextIO

from prosim.models.decisions import Decisions, MachineDecision, PartOrders


class DECSParseError(Exception):
    """Error parsing a DECS file."""

    def __init__(self, message: str, line_number: int | None = None) -> None:
        self.line_number = line_number
        if line_number is not None:
            message = f"Line {line_number}: {message}"
        super().__init__(message)


def _parse_line_values(line: str, expected: int, line_number: int) -> list[float]:
    """Parse a line of space-separated numeric values.

    Args:
        line: Line to parse
        expected: Expected number of values
        line_number: Line number for error reporting

    Returns:
        List of parsed float values

    Raises:
        DECSParseError: If parsing fails or value count doesn't match
    """
    parts = line.split()
    if len(parts) != expected:
        raise DECSParseError(
            f"Expected {expected} values, got {len(parts)}", line_number
        )

    try:
        return [float(p) for p in parts]
    except ValueError as e:
        raise DECSParseError(f"Invalid numeric value: {e}", line_number) from e


def parse_decs(source: str | Path | TextIO) -> Decisions:
    """Parse a DECS file into a Decisions object.

    Args:
        source: File path, path object, or file-like object containing DECS data

    Returns:
        Parsed Decisions object

    Raises:
        DECSParseError: If the file format is invalid
        FileNotFoundError: If source is a path and file doesn't exist

    Example:
        >>> decisions = parse_decs("archive/data/DECS12.txt")
        >>> decisions.week
        12
        >>> decisions.company_id
        1
    """
    # Get lines from source
    if isinstance(source, (str, Path)):
        with open(source, encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = source.read().splitlines()

    # Strip carriage returns (Windows line endings)
    lines = [line.replace("\r", "") for line in lines]

    # Filter out empty lines
    lines = [line for line in lines if line.strip()]

    if len(lines) < 11:
        raise DECSParseError(
            f"DECS file must have at least 11 lines, got {len(lines)}"
        )

    # Parse Line 1: Header
    header = _parse_line_values(lines[0], 6, 1)
    week = int(header[0])
    company_id = int(header[1])
    quality_budget = header[2]
    maintenance_budget = header[3]
    raw_materials_regular = header[4]
    raw_materials_expedited = header[5]

    # Parse Line 2: Part orders
    part_values = _parse_line_values(lines[1], 3, 2)
    part_orders = PartOrders.from_list(part_values)

    # Parse Lines 3-11: Machine decisions
    machine_decisions: list[MachineDecision] = []
    for i, line in enumerate(lines[2:11], start=3):
        values = _parse_line_values(line, 4, i)
        machine_id = int(values[0])
        train_flag = int(values[1])
        part_type = int(values[2])
        scheduled_hours = values[3]

        machine_decisions.append(
            MachineDecision(
                machine_id=machine_id,
                send_for_training=(train_flag == 0),
                part_type=part_type,
                scheduled_hours=scheduled_hours,
            )
        )

    return Decisions(
        week=week,
        company_id=company_id,
        quality_budget=quality_budget,
        maintenance_budget=maintenance_budget,
        raw_materials_regular=raw_materials_regular,
        raw_materials_expedited=raw_materials_expedited,
        part_orders=part_orders,
        machine_decisions=machine_decisions,
    )


def write_decs(decisions: Decisions, destination: str | Path | TextIO) -> None:
    """Write a Decisions object to a DECS file.

    Args:
        decisions: Decisions object to write
        destination: File path, path object, or file-like object to write to

    Example:
        >>> decisions = Decisions.create_default(week=1)
        >>> write_decs(decisions, "output/DECS01.DAT")
    """
    # Build file content
    lines = []

    # Line 1: Header
    lines.append(
        f" {decisions.week:<13}"
        f"{decisions.company_id:<14}"
        f"{int(decisions.quality_budget):<14}"
        f"{int(decisions.maintenance_budget):<14}"
        f"{int(decisions.raw_materials_regular):<14}"
        f"{int(decisions.raw_materials_expedited)}"
    )

    # Line 2: Part orders
    lines.append(
        f" {int(decisions.part_orders.x_prime):<14}"
        f"{int(decisions.part_orders.y_prime):<14}"
        f"{int(decisions.part_orders.z_prime)}"
    )

    # Lines 3-11: Machine decisions
    for md in decisions.machine_decisions:
        train_flag = 0 if md.send_for_training else 1
        lines.append(
            f" {md.machine_id:<14}"
            f"{train_flag:<14}"
            f"{md.part_type:<14}"
            f"{int(md.scheduled_hours)}"
        )

    content = "\n".join(lines) + "\n"

    # Write to destination
    if isinstance(destination, (str, Path)):
        with open(destination, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        destination.write(content)


class DECSParser:
    """Parser for batch processing multiple DECS files.

    Provides validation and batch parsing capabilities.

    Example:
        >>> parser = DECSParser(strict=True)
        >>> decisions = parser.parse_file("DECS12.txt")
        >>> all_decisions = parser.parse_directory("archive/data")
    """

    def __init__(self, strict: bool = True) -> None:
        """Initialize parser.

        Args:
            strict: If True, raise errors on validation failures.
                   If False, log warnings and continue.
        """
        self.strict = strict

    def parse_file(self, path: str | Path) -> Decisions:
        """Parse a single DECS file.

        Args:
            path: Path to the DECS file

        Returns:
            Parsed Decisions object

        Raises:
            DECSParseError: If parsing fails and strict mode is enabled
        """
        return parse_decs(path)

    def parse_directory(
        self, directory: str | Path, pattern: str = "DECS*.DAT"
    ) -> list[Decisions]:
        """Parse all DECS files in a directory.

        Args:
            directory: Directory to search
            pattern: Glob pattern for matching DECS files

        Returns:
            List of parsed Decisions objects, sorted by week

        Raises:
            DECSParseError: If any file fails to parse and strict mode is enabled
        """
        directory = Path(directory)
        decisions_list: list[Decisions] = []

        for file_path in sorted(directory.glob(pattern)):
            try:
                decisions = parse_decs(file_path)
                decisions_list.append(decisions)
            except DECSParseError as e:
                if self.strict:
                    raise DECSParseError(
                        f"Error parsing {file_path}: {e}"
                    ) from e
                # In non-strict mode, we'd log and continue

        # Also try .txt extension
        for file_path in sorted(directory.glob(pattern.replace(".DAT", ".txt"))):
            try:
                decisions = parse_decs(file_path)
                decisions_list.append(decisions)
            except DECSParseError as e:
                if self.strict:
                    raise DECSParseError(
                        f"Error parsing {file_path}: {e}"
                    ) from e

        # Sort by week
        decisions_list.sort(key=lambda d: (d.company_id, d.week))

        return decisions_list

    def validate(self, decisions: Decisions) -> list[str]:
        """Validate a Decisions object for logical consistency.

        Args:
            decisions: Decisions object to validate

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings: list[str] = []

        # Check for duplicate machine IDs
        machine_ids = [md.machine_id for md in decisions.machine_decisions]
        if len(machine_ids) != len(set(machine_ids)):
            warnings.append("Duplicate machine IDs in decisions")

        # Check if any operator is both training and scheduled
        for md in decisions.machine_decisions:
            if md.send_for_training and md.scheduled_hours > 0:
                warnings.append(
                    f"Machine {md.machine_id}: Operator in training but hours scheduled"
                )

        # Check for excessive hours (max is typically 50 per week)
        for md in decisions.machine_decisions:
            if md.scheduled_hours > 50:
                warnings.append(
                    f"Machine {md.machine_id}: Scheduled hours ({md.scheduled_hours}) "
                    "exceeds typical maximum (50)"
                )

        # Check for zero-budget concerns
        if decisions.quality_budget == 0:
            warnings.append("Quality budget is zero (may increase reject rate)")

        if decisions.maintenance_budget == 0:
            warnings.append("Maintenance budget is zero (may increase breakdowns)")

        return warnings
