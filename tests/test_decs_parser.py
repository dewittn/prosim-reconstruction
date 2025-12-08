"""Tests for DECS file parser."""

import io
from pathlib import Path

import pytest

from prosim.io.decs_parser import (
    DECSParseError,
    DECSParser,
    parse_decs,
    write_decs,
)
from prosim.models.decisions import Decisions


# Sample DECS file content matching archive/data/DECS12.txt format
DECS12_CONTENT = """ 12            1             750           500           10000         10000
 600           500           400
 1             0             1             40
 2             1             2             40
 3             1             3             40
 4             0             1             40
 5             0             3             40
 6             1             2             40
 7             1             1             40
 8             0             3             40
 9             1             3             40
"""


class TestParseDecs:
    """Tests for parse_decs function."""

    def test_parse_from_string_io(self) -> None:
        """Parse DECS content from a StringIO object."""
        f = io.StringIO(DECS12_CONTENT)
        decisions = parse_decs(f)

        assert decisions.week == 12
        assert decisions.company_id == 1
        assert decisions.quality_budget == 750
        assert decisions.maintenance_budget == 500
        assert decisions.raw_materials_regular == 10000
        assert decisions.raw_materials_expedited == 10000

    def test_parse_part_orders(self) -> None:
        """Parse part orders from DECS content."""
        f = io.StringIO(DECS12_CONTENT)
        decisions = parse_decs(f)

        assert decisions.part_orders.x_prime == 600
        assert decisions.part_orders.y_prime == 500
        assert decisions.part_orders.z_prime == 400

    def test_parse_machine_decisions(self) -> None:
        """Parse machine decisions from DECS content."""
        f = io.StringIO(DECS12_CONTENT)
        decisions = parse_decs(f)

        assert len(decisions.machine_decisions) == 9

        # Machine 1: send for training (train_flag=0)
        md1 = decisions.get_machine_decision(1)
        assert md1 is not None
        assert md1.send_for_training is True
        assert md1.part_type == 1
        assert md1.scheduled_hours == 40

        # Machine 2: working (train_flag=1)
        md2 = decisions.get_machine_decision(2)
        assert md2 is not None
        assert md2.send_for_training is False
        assert md2.part_type == 2
        assert md2.scheduled_hours == 40

    def test_parse_original_file(self) -> None:
        """Parse the original DECS12.txt file."""
        path = Path("archive/data/DECS12.txt")
        if not path.exists():
            pytest.skip("Original DECS12.txt file not found")

        decisions = parse_decs(path)

        assert decisions.week == 12
        assert decisions.company_id == 1
        assert len(decisions.machine_decisions) == 9

    def test_parse_with_crlf_line_endings(self) -> None:
        """Parse content with Windows-style line endings."""
        content = DECS12_CONTENT.replace("\n", "\r\n")
        f = io.StringIO(content)
        decisions = parse_decs(f)

        assert decisions.week == 12
        assert decisions.company_id == 1

    def test_parse_error_invalid_line_count(self) -> None:
        """Raise error when file has too few lines."""
        content = " 12            1             750           500           10000         10000\n"
        f = io.StringIO(content)

        with pytest.raises(DECSParseError) as exc_info:
            parse_decs(f)

        assert "at least 11 lines" in str(exc_info.value)

    def test_parse_error_invalid_header(self) -> None:
        """Raise error when header has wrong number of values."""
        content = " 12            1             750\n" + "\n".join([
            " 600           500           400",
            " 1             0             1             40",
            " 2             1             2             40",
            " 3             1             3             40",
            " 4             0             1             40",
            " 5             0             3             40",
            " 6             1             2             40",
            " 7             1             1             40",
            " 8             0             3             40",
            " 9             1             3             40",
        ])
        f = io.StringIO(content)

        with pytest.raises(DECSParseError) as exc_info:
            parse_decs(f)

        assert "Line 1" in str(exc_info.value)
        assert "Expected 6 values" in str(exc_info.value)

    def test_parse_error_invalid_numeric_value(self) -> None:
        """Raise error when a value cannot be parsed as a number."""
        content = DECS12_CONTENT.replace("750", "abc")
        f = io.StringIO(content)

        with pytest.raises(DECSParseError) as exc_info:
            parse_decs(f)

        assert "Invalid numeric value" in str(exc_info.value)


class TestWriteDecs:
    """Tests for write_decs function."""

    def test_write_to_string_io(self) -> None:
        """Write DECS content to a StringIO object."""
        decisions = Decisions.create_default(week=5, company_id=2)
        decisions = decisions.model_copy(
            update={
                "quality_budget": 1000.0,
                "maintenance_budget": 800.0,
                "raw_materials_regular": 5000.0,
                "raw_materials_expedited": 1000.0,
            }
        )

        f = io.StringIO()
        write_decs(decisions, f)
        content = f.getvalue()

        assert "5" in content  # week
        assert "2" in content  # company_id
        assert "1000" in content  # quality_budget
        assert "800" in content  # maintenance_budget

    def test_roundtrip_parse_write(self) -> None:
        """Parse and write should produce equivalent decisions."""
        f1 = io.StringIO(DECS12_CONTENT)
        original = parse_decs(f1)

        f2 = io.StringIO()
        write_decs(original, f2)
        f2.seek(0)

        reparsed = parse_decs(f2)

        assert reparsed.week == original.week
        assert reparsed.company_id == original.company_id
        assert reparsed.quality_budget == original.quality_budget
        assert reparsed.maintenance_budget == original.maintenance_budget
        assert reparsed.raw_materials_regular == original.raw_materials_regular
        assert reparsed.raw_materials_expedited == original.raw_materials_expedited
        assert reparsed.part_orders.x_prime == original.part_orders.x_prime
        assert reparsed.part_orders.y_prime == original.part_orders.y_prime
        assert reparsed.part_orders.z_prime == original.part_orders.z_prime

        for i, (orig_md, new_md) in enumerate(
            zip(original.machine_decisions, reparsed.machine_decisions)
        ):
            assert new_md.machine_id == orig_md.machine_id, f"Machine {i+1} ID mismatch"
            assert (
                new_md.send_for_training == orig_md.send_for_training
            ), f"Machine {i+1} training mismatch"
            assert new_md.part_type == orig_md.part_type, f"Machine {i+1} part mismatch"
            assert (
                new_md.scheduled_hours == orig_md.scheduled_hours
            ), f"Machine {i+1} hours mismatch"


class TestDECSParser:
    """Tests for DECSParser class."""

    def test_validate_duplicate_machine_ids(self) -> None:
        """Detect duplicate machine IDs."""
        from prosim.models.decisions import MachineDecision

        decisions = Decisions.create_default(week=1)
        # Create duplicate by modifying machine_decisions
        modified_decisions = list(decisions.machine_decisions)
        modified_decisions[1] = MachineDecision(
            machine_id=1,  # Duplicate of machine 1
            send_for_training=False,
            part_type=2,
            scheduled_hours=40.0,
        )

        # Use model_construct to bypass the 9-unique-machines validation
        invalid_decisions = Decisions.model_construct(
            week=1,
            company_id=1,
            quality_budget=0.0,
            maintenance_budget=0.0,
            raw_materials_regular=0.0,
            raw_materials_expedited=0.0,
            part_orders=decisions.part_orders,
            machine_decisions=modified_decisions,
        )

        parser = DECSParser()
        warnings = parser.validate(invalid_decisions)

        assert any("Duplicate machine IDs" in w for w in warnings)

    def test_validate_training_with_hours(self) -> None:
        """Warn when operator is training but has hours scheduled."""
        from prosim.models.decisions import MachineDecision

        decisions = Decisions.create_default(week=1)

        # Create state where operator is training but has hours
        modified_decisions = list(decisions.machine_decisions)
        modified_decisions[0] = MachineDecision(
            machine_id=1,
            send_for_training=True,  # Training
            part_type=1,
            scheduled_hours=30.0,  # But has hours scheduled
        )

        test_decisions = Decisions.model_construct(
            week=1,
            company_id=1,
            quality_budget=0.0,
            maintenance_budget=0.0,
            raw_materials_regular=0.0,
            raw_materials_expedited=0.0,
            part_orders=decisions.part_orders,
            machine_decisions=modified_decisions,
        )

        parser = DECSParser()
        warnings = parser.validate(test_decisions)

        assert any("Operator in training but hours scheduled" in w for w in warnings)

    def test_validate_zero_budgets(self) -> None:
        """Warn about zero quality and maintenance budgets."""
        decisions = Decisions.create_default(week=1)
        # Default decisions have zero budgets

        parser = DECSParser()
        warnings = parser.validate(decisions)

        assert any("Quality budget is zero" in w for w in warnings)
        assert any("Maintenance budget is zero" in w for w in warnings)

    def test_parse_directory(self, tmp_path: Path) -> None:
        """Parse multiple DECS files from a directory."""
        # Create test files
        (tmp_path / "DECS01.DAT").write_text(DECS12_CONTENT.replace("12", " 1"))
        (tmp_path / "DECS02.DAT").write_text(DECS12_CONTENT.replace("12", " 2"))

        parser = DECSParser()
        decisions_list = parser.parse_directory(tmp_path)

        assert len(decisions_list) == 2
        assert decisions_list[0].week == 1
        assert decisions_list[1].week == 2


class TestOriginalFiles:
    """Tests against original DECS files in archive."""

    @pytest.fixture
    def archive_path(self) -> Path:
        return Path("archive/data")

    def test_parse_decs12(self, archive_path: Path) -> None:
        """Parse original DECS12.txt file."""
        path = archive_path / "DECS12.txt"
        if not path.exists():
            pytest.skip("DECS12.txt not found")

        decisions = parse_decs(path)

        # Verify known values from the file
        assert decisions.week == 12
        assert decisions.company_id == 1
        assert decisions.quality_budget == 750
        assert decisions.maintenance_budget == 500
        assert decisions.raw_materials_regular == 10000
        assert decisions.raw_materials_expedited == 10000

        assert decisions.part_orders.x_prime == 600
        assert decisions.part_orders.y_prime == 500
        assert decisions.part_orders.z_prime == 400

        # Verify machines
        assert len(decisions.machine_decisions) == 9

        # Check specific machines
        assert decisions.get_machine_decision(1) is not None
        assert decisions.get_machine_decision(1).send_for_training is True
        assert decisions.get_machine_decision(2) is not None
        assert decisions.get_machine_decision(2).send_for_training is False
