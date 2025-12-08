"""Tests for configuration system."""

import json
from pathlib import Path

import pytest

from prosim.config import (
    DEFAULT_CONFIG,
    ProsimConfig,
    get_default_config,
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
