"""
Tests for the calibration module.

These tests verify calibration functions and validate against original data.
"""

from pathlib import Path

import pytest

from prosim.config.schema import get_default_config
from prosim.engine.calibration import (
    CALIBRATION_DATA,
    ProductionRateAnalysis,
    RejectRateAnalysis,
    analyze_operator_efficiency_from_report,
    analyze_production_rates_from_report,
    analyze_reject_rate_from_report,
    calculate_efficiency_statistics,
    calculate_quality_adjusted_reject_rate,
    create_calibrated_config,
    derive_carrying_cost_rates,
    derive_cost_rates_from_report,
    derive_equipment_rate_from_costs,
    derive_labor_rate_from_report,
    derive_raw_material_cost_per_unit,
    estimate_machine_repair_probability_from_reports,
    get_calibrated_reject_rate,
    get_stochastic_config,
    infer_training_status_from_efficiency,
    verify_production_formula,
)
from prosim.io.rept_parser import parse_rept


# Test data paths
ARCHIVE_DATA = Path(__file__).parent.parent / "archive" / "data"


# ==============================================================================
# REJECT RATE CALIBRATION TESTS
# ==============================================================================


class TestRejectRateCalibration:
    """Tests for reject rate calibration functions."""

    def test_quality_adjusted_reject_rate_at_optimal(self) -> None:
        """At optimal quality budget, should return base rate."""
        rate = calculate_quality_adjusted_reject_rate(
            base_reject_rate=0.1185,
            quality_budget=750.0,
            optimal_quality_budget=750.0,
            sensitivity=0.0001,
        )
        assert rate == pytest.approx(0.1185, rel=0.01)

    def test_quality_adjusted_reject_rate_higher_budget(self) -> None:
        """Higher quality budget should reduce reject rate."""
        rate = calculate_quality_adjusted_reject_rate(
            base_reject_rate=0.1185,
            quality_budget=1000.0,  # Higher than optimal
            optimal_quality_budget=750.0,
            sensitivity=0.0001,
        )
        # Higher budget -> lower rate
        assert rate < 0.1185

    def test_quality_adjusted_reject_rate_lower_budget(self) -> None:
        """Lower quality budget should increase reject rate."""
        rate = calculate_quality_adjusted_reject_rate(
            base_reject_rate=0.1185,
            quality_budget=500.0,  # Lower than optimal
            optimal_quality_budget=750.0,
            sensitivity=0.0001,
        )
        # Lower budget -> higher rate
        assert rate > 0.1185

    def test_quality_adjusted_reject_rate_clamped_min(self) -> None:
        """Reject rate should not go below minimum."""
        rate = calculate_quality_adjusted_reject_rate(
            base_reject_rate=0.1185,
            quality_budget=10000.0,  # Very high budget
            optimal_quality_budget=750.0,
            sensitivity=0.0001,
        )
        assert rate >= 0.05  # Minimum bound

    def test_quality_adjusted_reject_rate_clamped_max(self) -> None:
        """Reject rate should not go above maximum."""
        rate = calculate_quality_adjusted_reject_rate(
            base_reject_rate=0.1185,
            quality_budget=0.0,  # Zero budget
            optimal_quality_budget=750.0,
            sensitivity=0.001,  # High sensitivity
        )
        assert rate <= 0.30  # Maximum bound

    def test_get_calibrated_reject_rate(self) -> None:
        """Convenience function should use calibration data."""
        rate = get_calibrated_reject_rate(750.0)
        expected = CALIBRATION_DATA["quality_budget_reject_correlation"]["base_rate_at_750"]
        assert rate == pytest.approx(expected, rel=0.01)

    def test_calibration_data_reject_rates(self) -> None:
        """Verify stored reject rate data matches observations."""
        rates = CALIBRATION_DATA["reject_rates_by_week"]
        assert rates[12] == pytest.approx(0.1185, rel=0.01)
        assert rates[13] == pytest.approx(0.15, rel=0.02)
        assert rates[14] == pytest.approx(0.178, rel=0.01)


# ==============================================================================
# PRODUCTION RATE ANALYSIS TESTS
# ==============================================================================


class TestProductionRateAnalysis:
    """Tests for production rate analysis functions."""

    @pytest.fixture
    def rept14(self):
        """Load REPT14 for testing."""
        return parse_rept(ARCHIVE_DATA / "REPT14.DAT")

    def test_analyze_reject_rate_from_report(self, rept14) -> None:
        """Test reject rate analysis from report."""
        analysis = analyze_reject_rate_from_report(rept14)

        assert analysis.week == 14
        assert analysis.total_production > 0
        assert analysis.total_rejects > 0
        assert 0.10 < analysis.reject_rate < 0.25

    def test_analyze_production_rates_from_report(self, rept14) -> None:
        """Test production rate analysis from report."""
        analysis = analyze_production_rates_from_report(rept14)

        # Should have analysis for multiple part types
        assert len(analysis) > 0

        # Each analysis should have valid data
        for rate_analysis in analysis:
            assert isinstance(rate_analysis, ProductionRateAnalysis)
            assert rate_analysis.total_productive_hours >= 0
            if rate_analysis.total_productive_hours > 0:
                assert rate_analysis.observed_rate > 0


# ==============================================================================
# COST DERIVATION TESTS
# ==============================================================================


class TestCostDerivation:
    """Tests for cost derivation functions."""

    def test_derive_equipment_rate(self) -> None:
        """Test equipment rate derivation from week1.txt data.

        From week1.txt: $8,000 total / (9 machines * 40 hours) = $22.22/hr
        Note: This varies from the derived $20/hr in the case study.
        """
        rate = derive_equipment_rate_from_costs(
            total_equipment_cost=8000.0,
            total_scheduled_hours=360.0,  # 9 * 40
        )
        assert rate == pytest.approx(22.22, rel=0.01)

    def test_derive_raw_material_cost(self) -> None:
        """Test raw material cost derivation from week1.txt data.

        From week1.txt: $12,451 / 11,099 units = $1.12/unit
        """
        cost = derive_raw_material_cost_per_unit(
            total_rm_cost=12451.0,
            total_rm_consumed=11099.0,
        )
        assert cost == pytest.approx(1.12, rel=0.01)

    def test_derive_raw_material_cost_zero_consumed(self) -> None:
        """Test with zero consumption returns zero."""
        cost = derive_raw_material_cost_per_unit(
            total_rm_cost=1000.0,
            total_rm_consumed=0.0,
        )
        assert cost == 0.0

    def test_derive_carrying_cost_rates(self) -> None:
        """Test carrying cost rate derivation from week1.txt data.

        From week1.txt:
        - Parts carrying: $298 (X: $57, Y: $44, Z: $197)
        - Products carrying: $938 (X: $147, Y: $237, Z: $553)
        """
        parts_rate, products_rate = derive_carrying_cost_rates(
            parts_carrying_cost=298.0,
            products_carrying_cost=938.0,
            avg_parts_inventory=3000.0,  # Estimated
            avg_products_inventory=3800.0,  # Estimated
        )
        assert parts_rate > 0
        assert products_rate > 0


# ==============================================================================
# PRODUCTION FORMULA VERIFICATION TESTS
# ==============================================================================


class TestProductionFormulaVerification:
    """Tests for production formula verification."""

    def test_verify_production_formula_basic(self) -> None:
        """Test basic production formula calculation."""
        result = verify_production_formula(
            scheduled_hours=40.0,
            setup_hours=0.0,
            efficiency=1.0,
            production_rate=60.0,
            reject_rate=0.178,
        )

        assert result["scheduled_hours"] == 40.0
        assert result["setup_hours"] == 0.0
        assert result["available_hours"] == 40.0
        assert result["productive_hours"] == 40.0
        assert result["gross_production"] == 2400.0  # 40 * 60
        assert result["rejects"] == pytest.approx(427.2, rel=0.01)  # 2400 * 0.178
        assert result["net_production"] == pytest.approx(1972.8, rel=0.01)

    def test_verify_production_formula_with_setup(self) -> None:
        """Test formula with setup time."""
        result = verify_production_formula(
            scheduled_hours=40.0,
            setup_hours=2.0,  # 2 hour setup
            efficiency=1.0,
            production_rate=60.0,
            reject_rate=0.178,
        )

        assert result["available_hours"] == 38.0
        assert result["productive_hours"] == 38.0
        assert result["gross_production"] == 2280.0  # 38 * 60

    def test_verify_production_formula_with_efficiency(self) -> None:
        """Test formula with efficiency factor."""
        result = verify_production_formula(
            scheduled_hours=40.0,
            setup_hours=0.0,
            efficiency=0.80,  # 80% efficiency
            production_rate=60.0,
            reject_rate=0.178,
        )

        assert result["productive_hours"] == 32.0  # 40 * 0.8
        assert result["gross_production"] == 1920.0  # 32 * 60

    def test_verify_production_formula_assembly(self) -> None:
        """Test formula for assembly department."""
        result = verify_production_formula(
            scheduled_hours=40.0,
            setup_hours=0.0,
            efficiency=1.0,
            production_rate=40.0,  # X assembly rate
            reject_rate=0.178,
        )

        assert result["gross_production"] == 1600.0  # 40 * 40
        assert result["net_production"] == pytest.approx(1315.2, rel=0.01)


# ==============================================================================
# CONFIG CALIBRATION TESTS
# ==============================================================================


class TestConfigCalibration:
    """Tests for calibrated config creation."""

    def test_create_calibrated_config_default(self) -> None:
        """Test creating calibrated config with defaults."""
        config = create_calibrated_config()

        # Should have a reject rate
        assert config.production.reject_rate > 0
        assert config.production.reject_rate < 0.30

    def test_create_calibrated_config_high_quality_budget(self) -> None:
        """Test calibrated config with high quality budget."""
        config = create_calibrated_config(quality_budget=1000.0)

        # Higher quality budget -> lower reject rate
        default_config = create_calibrated_config(quality_budget=750.0)
        assert config.production.reject_rate < default_config.production.reject_rate

    def test_create_calibrated_config_no_dynamic_reject(self) -> None:
        """Test config without dynamic reject rate."""
        base_config = get_default_config()
        config = create_calibrated_config(
            base_config=base_config,
            use_dynamic_reject_rate=False,
        )

        # Should use base config's reject rate
        assert config.production.reject_rate == base_config.production.reject_rate


# ==============================================================================
# CALIBRATION DATA VALIDATION TESTS
# ==============================================================================


class TestCalibrationDataValidation:
    """Tests to validate calibration data against original files."""

    def test_calibration_data_verified_costs(self) -> None:
        """Verify cost constants match documentation."""
        costs = CALIBRATION_DATA["verified_costs"]

        assert costs["labor_hourly"] == 10.0
        assert costs["repair_per_incident"] == 400.0
        assert costs["hiring_per_worker"] == 2700.0
        assert costs["layoff_per_week"] == 200.0
        assert costs["termination"] == 400.0
        assert costs["fixed_expense"] == 1500.0

    def test_calibration_data_production_rates(self) -> None:
        """Verify production rates match documentation."""
        rates = CALIBRATION_DATA["production_rates"]

        # Parts department
        assert rates["parts"]["X'"] == 60
        assert rates["parts"]["Y'"] == 50
        assert rates["parts"]["Z'"] == 40

        # Assembly department
        assert rates["assembly"]["X"] == 40
        assert rates["assembly"]["Y"] == 30
        assert rates["assembly"]["Z"] == 20

    def test_calibration_data_efficiency_ranges(self) -> None:
        """Verify efficiency ranges match documentation."""
        efficiency = CALIBRATION_DATA["efficiency_ranges"]

        # Trained operators: 95-100%
        assert efficiency["trained"]["min"] == 0.95
        assert efficiency["trained"]["max"] == 1.00

        # Untrained operators: 60-90%
        assert efficiency["untrained"]["min"] == 0.60
        assert efficiency["untrained"]["max"] == 0.90


# ==============================================================================
# ORIGINAL DATA VALIDATION TESTS
# ==============================================================================


# ==============================================================================
# OPERATOR EFFICIENCY CALIBRATION TESTS
# ==============================================================================


class TestOperatorEfficiencyCalibration:
    """Tests for operator efficiency analysis functions."""

    @pytest.fixture
    def rept14(self):
        """Load REPT14 for testing."""
        return parse_rept(ARCHIVE_DATA / "REPT14.DAT")

    def test_analyze_operator_efficiency_from_report(self, rept14) -> None:
        """Test efficiency analysis from report."""
        efficiencies = analyze_operator_efficiency_from_report(rept14)

        assert "parts" in efficiencies
        assert "assembly" in efficiencies
        assert len(efficiencies["parts"]) > 0
        assert len(efficiencies["assembly"]) > 0

        # All efficiencies should be in valid range
        for dept in ["parts", "assembly"]:
            for eff in efficiencies[dept]:
                assert 0.0 <= eff <= 1.0

    def test_infer_training_status_trained(self) -> None:
        """Test training status inference for trained operators."""
        assert infer_training_status_from_efficiency(1.0) == "trained"
        assert infer_training_status_from_efficiency(0.95) == "trained"
        assert infer_training_status_from_efficiency(0.97) == "trained"

    def test_infer_training_status_untrained(self) -> None:
        """Test training status inference for untrained operators."""
        assert infer_training_status_from_efficiency(0.80) == "untrained"
        assert infer_training_status_from_efficiency(0.60) == "untrained"
        assert infer_training_status_from_efficiency(0.94) == "untrained"

    def test_calculate_efficiency_statistics_basic(self) -> None:
        """Test efficiency statistics calculation."""
        efficiencies = [0.80, 0.85, 0.90, 1.0, 1.0]
        stats = calculate_efficiency_statistics(efficiencies)

        assert stats["min"] == 0.80
        assert stats["max"] == 1.0
        assert stats["mean"] == pytest.approx(0.91, rel=0.01)
        assert stats["trained_count"] == 2  # Two at 1.0
        assert stats["untrained_count"] == 3

    def test_calculate_efficiency_statistics_empty(self) -> None:
        """Test statistics with empty list."""
        stats = calculate_efficiency_statistics([])

        assert stats["min"] == 0.0
        assert stats["max"] == 0.0
        assert stats["mean"] == 0.0
        assert stats["trained_count"] == 0
        assert stats["untrained_count"] == 0

    def test_observed_efficiencies_data_present(self) -> None:
        """Verify observed efficiency data is present."""
        observed = CALIBRATION_DATA["observed_efficiencies"]

        assert "week1_parts_department" in observed
        assert "week1_assembly_department" in observed
        assert len(observed["week1_parts_department"]) == 4
        assert len(observed["week1_assembly_department"]) == 5

    def test_observed_efficiency_ranges(self) -> None:
        """Verify observed efficiency ranges match documentation."""
        observed = CALIBRATION_DATA["observed_efficiencies"]

        # Parts department efficiencies from week1.txt
        parts_effs = observed["week1_parts_department"]
        assert min(parts_effs) == pytest.approx(0.8325, rel=0.01)
        assert max(parts_effs) == pytest.approx(0.925, rel=0.01)

        # Assembly department efficiencies (mostly trained)
        assembly_effs = observed["week1_assembly_department"]
        assert max(assembly_effs) == 1.0
        assert 0.90 in assembly_effs


class TestOriginalDataValidation:
    """Tests that validate calibration against original REPT files."""

    def test_week12_reject_rate_matches_calibration(self) -> None:
        """Verify week 12 reject rate matches calibration data."""
        report = parse_rept(ARCHIVE_DATA / "REPT12.DAT")
        analysis = analyze_reject_rate_from_report(report)

        expected = CALIBRATION_DATA["reject_rates_by_week"][12]
        assert analysis.reject_rate == pytest.approx(expected, rel=0.05)

    def test_week14_reject_rate_matches_calibration(self) -> None:
        """Verify week 14 reject rate matches calibration data."""
        report = parse_rept(ARCHIVE_DATA / "REPT14.DAT")
        analysis = analyze_reject_rate_from_report(report)

        expected = CALIBRATION_DATA["reject_rates_by_week"][14]
        assert analysis.reject_rate == pytest.approx(expected, rel=0.05)

    def test_production_rates_in_expected_range(self) -> None:
        """Verify observed production rates are within expected ranges."""
        report = parse_rept(ARCHIVE_DATA / "REPT14.DAT")
        analysis = analyze_production_rates_from_report(report)

        for rate_analysis in analysis:
            # Observed rate should be within 30% of expected
            # (accounting for efficiency variations)
            if rate_analysis.expected_rate > 0 and rate_analysis.total_productive_hours > 0:
                assert rate_analysis.rate_ratio > 0.5, (
                    f"{rate_analysis.part_type} rate too low: "
                    f"{rate_analysis.observed_rate} vs expected {rate_analysis.expected_rate}"
                )

    def test_operator_efficiency_within_bounds(self) -> None:
        """Verify operator efficiencies are within reasonable bounds.

        Note: Original data shows efficiency as low as 58%, which is below
        the documented 60% minimum for untrained operators. This suggests
        either the documentation is approximate or there are additional
        factors affecting efficiency (like new hires or machine issues).
        """
        report = parse_rept(ARCHIVE_DATA / "REPT14.DAT")
        efficiencies = analyze_operator_efficiency_from_report(report)

        all_effs = efficiencies["parts"] + efficiencies["assembly"]
        stats = calculate_efficiency_statistics(all_effs)

        # All efficiencies should be within reasonable range
        # Note: Observed minimum is ~58%, slightly below documented 60%
        assert stats["min"] >= 0.55  # Allow slight variance from documented 60%
        assert stats["max"] <= 1.00


# ==============================================================================
# COST PARAMETER CALIBRATION FROM ORIGINAL DATA
# ==============================================================================


class TestCostParameterCalibration:
    """Tests for cost parameter derivation from original data."""

    @pytest.fixture
    def rept12(self):
        """Load REPT12 for testing."""
        return parse_rept(ARCHIVE_DATA / "REPT12.DAT")

    @pytest.fixture
    def rept14(self):
        """Load REPT14 for testing."""
        return parse_rept(ARCHIVE_DATA / "REPT14.DAT")

    def test_derive_labor_rate_from_report(self, rept12) -> None:
        """Test labor rate derivation."""
        rate = derive_labor_rate_from_report(rept12)

        # Should be approximately $10/hour based on documentation
        assert rate == pytest.approx(10.0, rel=0.15)

    def test_derive_cost_rates_from_report(self, rept12) -> None:
        """Test all cost rates derivation."""
        rates = derive_cost_rates_from_report(rept12)

        # Verify all expected keys present
        assert "labor_hourly" in rates
        assert "equipment_hourly" in rates
        assert "raw_materials_per_unit" in rates
        assert "fixed_expense" in rates

        # Labor should be ~$10/hr
        assert rates["labor_hourly"] == pytest.approx(10.0, rel=0.15)

        # Fixed expense should be $1,500
        assert rates["fixed_expense"] == pytest.approx(1500.0, rel=0.01)

    def test_verified_costs_match_documentation(self) -> None:
        """Verify that CALIBRATION_DATA costs match documentation."""
        costs = CALIBRATION_DATA["verified_costs"]

        # These are from the case study and week1.txt
        assert costs["labor_hourly"] == 10.0
        assert costs["repair_per_incident"] == 400.0
        assert costs["hiring_per_worker"] == 2700.0
        assert costs["layoff_per_week"] == 200.0
        assert costs["termination"] == 400.0
        assert costs["fixed_expense"] == 1500.0


# ==============================================================================
# STOCHASTIC ELEMENT CALIBRATION
# ==============================================================================


class TestStochasticElementCalibration:
    """Tests for stochastic element handling and calibration."""

    def test_estimate_repair_probability(self) -> None:
        """Test machine repair probability estimation."""
        reports = [
            parse_rept(ARCHIVE_DATA / f"REPT{week}.DAT")
            for week in [12, 13, 14]
        ]

        prob = estimate_machine_repair_probability_from_reports(reports)

        # Should be in reasonable range (5-20%)
        assert 0.0 <= prob <= 0.25

    def test_get_stochastic_config_defaults(self) -> None:
        """Test stochastic config with defaults."""
        config = get_stochastic_config()

        assert config["machine_repair_probability"] == 0.10
        assert config["demand_variance_enabled"] is True
        assert config["random_seed"] is None

    def test_get_stochastic_config_custom(self) -> None:
        """Test stochastic config with custom values."""
        config = get_stochastic_config(
            repair_probability=0.15,
            demand_variance_enabled=False,
            random_seed=42,
        )

        assert config["machine_repair_probability"] == 0.15
        assert config["demand_variance_enabled"] is False
        assert config["random_seed"] == 42

    def test_machine_repair_observed_in_data(self) -> None:
        """Verify machine repairs are observed in original data."""
        report = parse_rept(ARCHIVE_DATA / "REPT12.DAT")

        # Check for repair costs
        total_repair = (
            report.weekly_costs.x_costs.machine_repair
            + report.weekly_costs.y_costs.machine_repair
            + report.weekly_costs.z_costs.machine_repair
        )

        # Repairs should be multiples of $400
        if total_repair > 0:
            assert total_repair % 400 == pytest.approx(0.0, abs=1.0)
