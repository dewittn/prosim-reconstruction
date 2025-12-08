"""Tests for REPT file parser."""

import io
from pathlib import Path

import pytest

from prosim.io.rept_parser import (
    REPTParseError,
    REPTParser,
    parse_rept,
    write_rept,
    write_rept_human_readable,
)
from prosim.models.report import WeeklyReport


class TestParseRept:
    """Tests for parse_rept function."""

    def test_parse_original_rept12(self) -> None:
        """Parse original REPT12.DAT file."""
        path = Path("archive/data/REPT12.DAT")
        if not path.exists():
            pytest.skip("REPT12.DAT not found")

        report = parse_rept(path)

        assert report.week == 12
        assert report.company_id == 2

    def test_parse_original_rept14(self) -> None:
        """Parse original REPT14.DAT file."""
        path = Path("archive/data/REPT14.DAT")
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        report = parse_rept(path)

        assert report.week == 14
        assert report.company_id == 2

    def test_parse_cost_data(self) -> None:
        """Verify cost data is parsed correctly from REPT14."""
        path = Path("archive/data/REPT14.DAT")
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        report = parse_rept(path)

        # Check weekly labor costs (first cost line)
        assert report.weekly_costs.x_costs.labor == 2300.0
        assert report.weekly_costs.y_costs.labor == 1700.0
        assert report.weekly_costs.z_costs.labor == 0.0

        # Check cumulative labor costs
        assert report.cumulative_costs.x_costs.labor == 3500.0
        assert report.cumulative_costs.y_costs.labor == 2500.0

    def test_parse_production_data(self) -> None:
        """Verify production data is parsed correctly."""
        path = Path("archive/data/REPT14.DAT")
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        report = parse_rept(path)

        # Should have parts and assembly production
        assert len(report.production.parts_department) == 4
        assert len(report.production.assembly_department) == 5

        # Check first machine in parts department
        mp1 = report.production.parts_department[0]
        assert mp1.machine_id == 3
        assert mp1.part_type == "X'"
        assert mp1.scheduled_hours == 40
        assert mp1.productive_hours == 40.0
        assert mp1.production == 2550.0
        assert mp1.rejects == 455.0

    def test_parse_inventory_data(self) -> None:
        """Verify inventory data is parsed correctly."""
        path = Path("archive/data/REPT14.DAT")
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        report = parse_rept(path)

        # Raw materials
        assert report.inventory.raw_materials.beginning_inventory == 0.0
        assert report.inventory.raw_materials.orders_received == 22000.0
        assert report.inventory.raw_materials.used_in_production == 10247.0
        assert report.inventory.raw_materials.ending_inventory == 11753.0

        # Parts X'
        assert report.inventory.parts_x.beginning_inventory == 1139.0
        assert report.inventory.parts_x.orders_received == 600.0
        assert report.inventory.parts_x.ending_inventory == 3348.0

    def test_parse_demand_data(self) -> None:
        """Verify demand data is parsed correctly."""
        path = Path("archive/data/REPT14.DAT")
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        report = parse_rept(path)

        assert report.demand_x.estimated_demand == 8127.0
        assert report.demand_x.carryover == 0.0
        assert report.demand_x.total_demand == 8127.0

    def test_parse_performance_metrics(self) -> None:
        """Verify performance metrics are parsed correctly."""
        path = Path("archive/data/REPT14.DAT")
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        report = parse_rept(path)

        # Weekly performance
        assert report.weekly_performance.total_standard_costs == 20214.0
        assert report.weekly_performance.percent_efficiency == pytest.approx(54.86, abs=0.01)
        assert report.weekly_performance.variance_per_unit == pytest.approx(-4.03, abs=0.01)

        # Cumulative performance
        assert report.cumulative_performance.total_standard_costs == 49123.0
        assert report.cumulative_performance.percent_efficiency == pytest.approx(60.25, abs=0.01)

    def test_parse_error_insufficient_lines(self) -> None:
        """Raise error when file has too few lines."""
        content = "14 2 4 4 5\n" * 10  # Only 10 lines
        f = io.StringIO(content)

        with pytest.raises(REPTParseError) as exc_info:
            parse_rept(f)

        assert "at least 42 lines" in str(exc_info.value)


class TestWriteRept:
    """Tests for write_rept function."""

    def test_roundtrip_parse_write(self) -> None:
        """Parse and write should produce equivalent reports."""
        path = Path("archive/data/REPT14.DAT")
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        original = parse_rept(path)

        # Write to StringIO
        f = io.StringIO()
        write_rept(original, f)
        f.seek(0)

        # Re-parse
        reparsed = parse_rept(f)

        # Verify key fields match
        assert reparsed.week == original.week
        assert reparsed.company_id == original.company_id

        # Check costs
        assert reparsed.weekly_costs.x_costs.labor == original.weekly_costs.x_costs.labor
        assert reparsed.weekly_costs.y_costs.labor == original.weekly_costs.y_costs.labor

        # Check inventory
        assert (
            reparsed.inventory.raw_materials.ending_inventory
            == original.inventory.raw_materials.ending_inventory
        )

    def test_write_human_readable(self) -> None:
        """Test human-readable output format."""
        path = Path("archive/data/REPT14.DAT")
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        report = parse_rept(path)

        f = io.StringIO()
        write_rept_human_readable(report, f)
        content = f.getvalue()

        # Check for expected sections
        assert "[Cost Information]" in content
        assert "[Production Information]" in content
        assert "[Inventory Information]" in content
        assert "[Demand Information]" in content
        assert "[Performance Measures]" in content

        # Check for some specific values
        assert "Labor" in content
        assert "Machine Set-Up" in content


class TestREPTParser:
    """Tests for REPTParser class."""

    def test_parse_file(self) -> None:
        """Parse a single REPT file using parser class."""
        path = Path("archive/data/REPT14.DAT")
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        parser = REPTParser()
        report = parser.parse_file(path)

        assert report.week == 14

    def test_parse_directory(self) -> None:
        """Parse all REPT files in a directory."""
        path = Path("archive/data")
        if not path.exists():
            pytest.skip("archive/data not found")

        parser = REPTParser()
        reports = parser.parse_directory(path)

        # Should find at least the REPT files we know exist
        assert len(reports) >= 1
        # Should be sorted by week
        for i in range(1, len(reports)):
            assert reports[i].week >= reports[i - 1].week


class TestOriginalFiles:
    """Tests against original REPT files for validation."""

    @pytest.fixture
    def archive_path(self) -> Path:
        return Path("archive/data")

    def test_reject_rate_rept14(self, archive_path: Path) -> None:
        """Verify reject rate calculation from REPT14.

        From case study: reject rate should be ~17.8%
        """
        path = archive_path / "REPT14.DAT"
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        report = parse_rept(path)

        # Calculate overall reject rate from all production
        total_production = 0.0
        total_rejects = 0.0
        for mp in report.production.all_machines:
            total_production += mp.production
            total_rejects += mp.rejects

        reject_rate = total_rejects / total_production if total_production > 0 else 0.0

        # From case study: reject rate should be ~17.8%
        assert reject_rate == pytest.approx(0.178, abs=0.02)

    def test_cost_totals_match(self, archive_path: Path) -> None:
        """Verify cost subtotals are consistent."""
        path = archive_path / "REPT14.DAT"
        if not path.exists():
            pytest.skip("REPT14.DAT not found")

        report = parse_rept(path)

        # Product subtotals should match sum of product costs
        calc_subtotal = (
            report.weekly_costs.x_costs.subtotal
            + report.weekly_costs.y_costs.subtotal
            + report.weekly_costs.z_costs.subtotal
        )
        assert report.weekly_costs.product_subtotal == pytest.approx(calc_subtotal, abs=1.0)
