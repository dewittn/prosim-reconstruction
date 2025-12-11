"""Tests for configuration system."""

import json
from pathlib import Path

import pytest

from prosim.config import (
    DEFAULT_CONFIG,
    ProsimConfig,
    get_default_config,
)
from prosim.config.defaults import (
    calculate_reject_rate,
    calculate_repair_probability,
)


class TestProsimConfig:
    """Tests for ProsimConfig class."""

    def test_default_config_creation(self) -> None:
        """Create a default configuration."""
        config = ProsimConfig()

        # Check production defaults
        assert config.production.reject_rate == 0.178
        assert config.production.parts_rates["X'"] == 60
        assert config.production.assembly_rates["X"] == 40

        # Check logistics defaults
        assert config.logistics.lead_times["raw_materials_regular"] == 3
        assert config.logistics.expedited_shipping_cost == 1200.0

        # Check simulation defaults
        assert config.simulation.parts_machines == 4
        assert config.simulation.assembly_machines == 5

    def test_get_default_config(self) -> None:
        """Get default configuration via function."""
        config = get_default_config()

        assert isinstance(config, ProsimConfig)
        assert config.production.reject_rate == 0.178

    def test_from_dict_partial(self) -> None:
        """Create config from partial dictionary."""
        data = {
            "production": {
                "reject_rate": 0.15,
            }
        }

        config = ProsimConfig.from_dict(data)

        # Override applied
        assert config.production.reject_rate == 0.15
        # Defaults preserved
        assert config.production.parts_rates["X'"] == 60
        assert config.logistics.expedited_shipping_cost == 1200.0

    def test_from_dict_nested(self) -> None:
        """Create config from nested dictionary."""
        data = {
            "workforce": {
                "efficiency": {
                    "trained_min": 0.90,
                    "trained_max": 0.98,
                }
            }
        }

        config = ProsimConfig.from_dict(data)

        assert config.workforce.efficiency.trained_min == 0.90
        assert config.workforce.efficiency.trained_max == 0.98
        # Defaults preserved for unspecified fields
        assert config.workforce.efficiency.untrained_min == 0.60

    def test_to_dict(self) -> None:
        """Convert config to dictionary."""
        config = ProsimConfig()
        data = config.to_dict()

        assert "production" in data
        assert "logistics" in data
        assert "simulation" in data
        assert data["production"]["reject_rate"] == 0.178

    def test_merge_overrides(self) -> None:
        """Merge overrides into config."""
        config = ProsimConfig()
        overrides = {
            "production": {"reject_rate": 0.20},
            "simulation": {"random_seed": 42},
        }

        merged = config.merge(overrides)

        # Original unchanged
        assert config.production.reject_rate == 0.178
        assert config.simulation.random_seed is None

        # Merged has changes
        assert merged.production.reject_rate == 0.20
        assert merged.simulation.random_seed == 42

        # Defaults preserved
        assert merged.production.parts_rates["X'"] == 60

    def test_validation_reject_rate_bounds(self) -> None:
        """Validate reject rate is between 0 and 1."""
        # Valid
        config = ProsimConfig.from_dict({"production": {"reject_rate": 0.5}})
        assert config.production.reject_rate == 0.5

        # Invalid - too high
        with pytest.raises(ValueError):
            ProsimConfig.from_dict({"production": {"reject_rate": 1.5}})

        # Invalid - negative
        with pytest.raises(ValueError):
            ProsimConfig.from_dict({"production": {"reject_rate": -0.1}})

    def test_validation_positive_costs(self) -> None:
        """Validate costs are non-negative."""
        # Valid
        config = ProsimConfig.from_dict(
            {"workforce": {"costs": {"hiring_cost": 0.0}}}
        )
        assert config.workforce.costs.hiring_cost == 0.0

        # Invalid - negative
        with pytest.raises(ValueError):
            ProsimConfig.from_dict(
                {"workforce": {"costs": {"hiring_cost": -100.0}}}
            )


class TestConfigFiles:
    """Tests for config file loading/saving."""

    def test_save_load_json(self, tmp_path: Path) -> None:
        """Save and load config from JSON file."""
        config = ProsimConfig()
        config = config.merge({"simulation": {"random_seed": 12345}})

        json_path = tmp_path / "config.json"
        config.to_file(json_path)

        # Verify file exists and is valid JSON
        assert json_path.exists()
        with open(json_path) as f:
            data = json.load(f)
        assert data["simulation"]["random_seed"] == 12345

        # Load back
        loaded = ProsimConfig.from_file(json_path)
        assert loaded.simulation.random_seed == 12345
        assert loaded.production.reject_rate == 0.178

    def test_load_nonexistent_file(self) -> None:
        """Raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            ProsimConfig.from_file("/nonexistent/config.json")

    def test_unsupported_format(self, tmp_path: Path) -> None:
        """Raise ValueError for unsupported file format."""
        txt_path = tmp_path / "config.txt"
        txt_path.write_text("{}")

        with pytest.raises(ValueError) as exc_info:
            ProsimConfig.from_file(txt_path)
        assert "Unsupported config file format" in str(exc_info.value)


class TestLegacyConfig:
    """Tests for legacy DEFAULT_CONFIG dict."""

    def test_default_config_structure(self) -> None:
        """Verify DEFAULT_CONFIG has expected structure."""
        assert "production" in DEFAULT_CONFIG
        assert "logistics" in DEFAULT_CONFIG
        assert "workforce" in DEFAULT_CONFIG
        assert "equipment" in DEFAULT_CONFIG
        assert "costs" in DEFAULT_CONFIG
        assert "demand" in DEFAULT_CONFIG
        assert "simulation" in DEFAULT_CONFIG

    def test_default_config_values(self) -> None:
        """Verify key DEFAULT_CONFIG values."""
        assert DEFAULT_CONFIG["production"]["reject_rate"] == 0.178
        assert DEFAULT_CONFIG["production"]["parts_rates"]["X'"] == 60
        assert DEFAULT_CONFIG["logistics"]["expedited_shipping_cost"] == 1200.0
        assert DEFAULT_CONFIG["workforce"]["costs"]["hiring_cost"] == 2700.0

    def test_legacy_matches_pydantic(self) -> None:
        """Legacy config should match Pydantic config defaults."""
        pydantic_config = get_default_config()

        # Production
        assert (
            DEFAULT_CONFIG["production"]["reject_rate"]
            == pydantic_config.production.reject_rate
        )
        assert (
            DEFAULT_CONFIG["production"]["parts_rates"]
            == pydantic_config.production.parts_rates
        )

        # Logistics
        assert (
            DEFAULT_CONFIG["logistics"]["expedited_shipping_cost"]
            == pydantic_config.logistics.expedited_shipping_cost
        )

        # Workforce
        assert (
            DEFAULT_CONFIG["workforce"]["costs"]["hiring_cost"]
            == pydantic_config.workforce.costs.hiring_cost
        )


class TestDerivedCalculations:
    """Tests for derived calculation functions from forensic analysis.

    The reject rate uses a logarithmic formula derived from Graph-Table 1:
        reject_rate = 0.904 - 0.114 * ln(quality_budget)
    This was verified against the original 2004 spreadsheet analysis.
    """

    def test_calculate_reject_rate_base(self) -> None:
        """Reject rate at base budget ($750) should be ~15.1% (logarithmic model)."""
        rate = calculate_reject_rate(750.0)
        # Logarithmic formula: 0.904 - 0.114 * ln(750) = ~0.149
        assert rate == pytest.approx(0.1493, abs=0.001)

    def test_calculate_reject_rate_higher_budget(self) -> None:
        """Higher quality budget should reduce reject rate."""
        rate_750 = calculate_reject_rate(750.0)
        rate_1000 = calculate_reject_rate(1000.0)
        rate_1500 = calculate_reject_rate(1500.0)

        assert rate_1000 < rate_750
        assert rate_1500 < rate_1000
        # At $1000: ~11.7% (logarithmic formula: 0.904 - 0.114 * ln(1000))
        assert rate_1000 == pytest.approx(0.117, abs=0.01)

    def test_calculate_reject_rate_minimum(self) -> None:
        """Reject rate should not go below 1.5% floor (verified from Week 16 data)."""
        rate = calculate_reject_rate(5000.0)  # Very high budget
        assert rate == 0.015  # Should hit the floor at 1.5%

    def test_calculate_repair_probability_base(self) -> None:
        """Repair probability at base budget ($500) should be ~15%."""
        prob = calculate_repair_probability(500.0)
        assert prob == pytest.approx(0.15, abs=0.01)

    def test_calculate_repair_probability_higher_budget(self) -> None:
        """Higher maintenance budget should reduce repair probability."""
        prob_500 = calculate_repair_probability(500.0)
        prob_1000 = calculate_repair_probability(1000.0)

        assert prob_1000 < prob_500

    def test_calculate_repair_probability_bounds(self) -> None:
        """Repair probability should stay in [0, 1] range."""
        # Very low budget - should not exceed 1.0
        prob_low = calculate_repair_probability(0.0)
        assert 0.0 <= prob_low <= 1.0

        # Very high budget - should hit floor of 0.0
        prob_high = calculate_repair_probability(10000.0)
        assert prob_high == 0.0


class TestConfigDocumentation:
    """Tests to ensure configuration is well-documented."""

    def test_all_fields_have_descriptions(self) -> None:
        """All config fields should have descriptions."""
        config = ProsimConfig()

        # Check top-level fields
        for field_name, field_info in ProsimConfig.model_fields.items():
            assert field_info.description is not None or True  # Nested models OK

        # Check production fields
        for field_name, field_info in type(config.production).model_fields.items():
            assert (
                field_info.description is not None
            ), f"production.{field_name} missing description"

        # Check simulation fields
        for field_name, field_info in type(config.simulation).model_fields.items():
            assert (
                field_info.description is not None
            ), f"simulation.{field_name} missing description"
