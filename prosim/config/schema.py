"""
Configuration schema for PROSIM simulation.

Provides Pydantic models for configuration validation and type safety.
All configuration parameters are documented with their sources
(verified from original data vs estimated/needs calibration).
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ProductionRatesConfig(BaseModel):
    """Production rates configuration."""

    parts_rates: dict[str, int] = Field(
        default={"X'": 60, "Y'": 50, "Z'": 40},
        description="Parts per productive hour by part type (verified)",
    )
    assembly_rates: dict[str, int] = Field(
        default={"X": 40, "Y": 30, "Z": 20},
        description="Products per productive hour by product type (verified)",
    )
    reject_rate: float = Field(
        default=0.178,
        ge=0.0,
        le=1.0,
        description="Fraction of production rejected (verified: ~17.8%)",
    )
    bom: dict[str, dict[str, int]] = Field(
        default={"X": {"X'": 1}, "Y": {"Y'": 1}, "Z": {"Z'": 1}},
        description="Bill of materials - parts required per product (verified: 1:1)",
    )
    raw_materials_per_part: dict[str, float] = Field(
        default={"X'": 1.0, "Y'": 1.0, "Z'": 1.0},
        description="Raw material units consumed per part (estimated)",
    )
    setup_time: dict[str, float] = Field(
        default={"parts_department": 2.0, "assembly_department": 2.0},
        description="Setup time in hours when changing part type (estimated)",
    )


class LogisticsConfig(BaseModel):
    """Lead times and shipping configuration."""

    lead_times: dict[str, int] = Field(
        default={
            "raw_materials_regular": 3,
            "raw_materials_expedited": 1,
            "purchased_parts": 1,
        },
        description="Lead times in weeks by order type (verified)",
    )
    expedited_shipping_cost: float = Field(
        default=1200.0,
        ge=0.0,
        description="Additional cost for expedited raw materials (verified: $1,200)",
    )


class OperatorEfficiencyConfig(BaseModel):
    """Operator efficiency parameters."""

    trained_min: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Minimum efficiency for trained operators",
    )
    trained_max: float = Field(
        default=1.00,
        ge=0.0,
        le=1.0,
        description="Maximum efficiency for trained operators",
    )
    untrained_min: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum efficiency for untrained operators",
    )
    untrained_max: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description="Maximum efficiency for untrained operators",
    )


class WorkforceCostsConfig(BaseModel):
    """Workforce-related costs."""

    hiring_cost: float = Field(
        default=2700.0,
        ge=0.0,
        description="Cost per new hire (verified: $2,700)",
    )
    layoff_cost_per_week: float = Field(
        default=200.0,
        ge=0.0,
        description="Cost per week an operator is unscheduled (verified: $200)",
    )
    termination_cost: float = Field(
        default=400.0,
        ge=0.0,
        description="Cost when operator is terminated after 2 weeks (verified: $400)",
    )
    training_cost_per_worker: float = Field(
        default=1000.0,
        ge=0.0,
        description="Cost per training session (estimated)",
    )


class WorkforceConfig(BaseModel):
    """Workforce configuration."""

    efficiency: OperatorEfficiencyConfig = Field(default_factory=OperatorEfficiencyConfig)
    costs: WorkforceCostsConfig = Field(default_factory=WorkforceCostsConfig)


class MachineRepairConfig(BaseModel):
    """Machine repair parameters (stochastic element)."""

    probability_per_machine_per_week: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Probability of machine breakdown per week (estimated: 10%)",
    )
    cost_per_repair: float = Field(
        default=400.0,
        ge=0.0,
        description="Cost per machine repair (verified: $400)",
    )


class EquipmentRatesConfig(BaseModel):
    """Equipment usage rates."""

    parts_department: float = Field(
        default=100.0,
        ge=0.0,
        description="Equipment usage cost per hour in parts dept (estimated)",
    )
    assembly_department: float = Field(
        default=80.0,
        ge=0.0,
        description="Equipment usage cost per hour in assembly dept (estimated)",
    )


class EquipmentConfig(BaseModel):
    """Equipment configuration."""

    repair: MachineRepairConfig = Field(default_factory=MachineRepairConfig)
    rates: EquipmentRatesConfig = Field(default_factory=EquipmentRatesConfig)


class FixedCostsConfig(BaseModel):
    """Fixed costs configuration."""

    fixed_expense_per_week: float = Field(
        default=1500.0,
        ge=0.0,
        description="Fixed weekly expense (verified: $1,500)",
    )


class CarryingCostRatesConfig(BaseModel):
    """Inventory carrying cost rates."""

    raw_materials: float = Field(
        default=0.01,
        ge=0.0,
        description="Carrying cost per RM unit per week (estimated)",
    )
    parts: float = Field(
        default=0.05,
        ge=0.0,
        description="Carrying cost per part per week (estimated)",
    )
    products: float = Field(
        default=0.10,
        ge=0.0,
        description="Carrying cost per product per week (estimated)",
    )


class LaborRatesConfig(BaseModel):
    """Labor cost rates."""

    regular_hourly: float = Field(
        default=10.0,
        ge=0.0,
        description="Regular hourly labor rate (verified from PPT: $10/hour)",
    )
    overtime_multiplier: float = Field(
        default=1.5,
        ge=1.0,
        description="Overtime pay multiplier (estimated)",
    )


class CostsConfig(BaseModel):
    """All cost-related configuration."""

    fixed: FixedCostsConfig = Field(default_factory=FixedCostsConfig)
    carrying: CarryingCostRatesConfig = Field(default_factory=CarryingCostRatesConfig)
    labor: LaborRatesConfig = Field(default_factory=LaborRatesConfig)


class DemandConfig(BaseModel):
    """Demand forecasting configuration."""

    forecast_std_dev_weeks_out: dict[int, int] = Field(
        default={4: 300, 3: 300, 2: 200, 1: 100, 0: 0},
        description="Standard deviation of demand forecast by weeks until shipping",
    )


class SimulationConfig(BaseModel):
    """Core simulation parameters."""

    parts_machines: int = Field(
        default=4,
        ge=1,
        description="Number of machines in parts department (verified: 4)",
    )
    assembly_machines: int = Field(
        default=5,
        ge=1,
        description="Number of machines in assembly department (verified: 5)",
    )
    max_scheduled_hours: float = Field(
        default=50.0,
        ge=0.0,
        description="Maximum hours that can be scheduled per machine per week",
    )
    regular_hours: float = Field(
        default=40.0,
        ge=0.0,
        description="Regular working hours per week",
    )
    shipping_frequency: int = Field(
        default=4,
        ge=1,
        description="Weeks between shipping events (monthly = 4)",
    )
    random_seed: int | None = Field(
        default=None,
        description="Random seed for reproducible simulations (None = random)",
    )


class ProsimConfig(BaseModel):
    """Complete PROSIM configuration.

    This is the top-level configuration object that contains all
    simulation parameters.
    """

    production: ProductionRatesConfig = Field(default_factory=ProductionRatesConfig)
    logistics: LogisticsConfig = Field(default_factory=LogisticsConfig)
    workforce: WorkforceConfig = Field(default_factory=WorkforceConfig)
    equipment: EquipmentConfig = Field(default_factory=EquipmentConfig)
    costs: CostsConfig = Field(default_factory=CostsConfig)
    demand: DemandConfig = Field(default_factory=DemandConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProsimConfig":
        """Create configuration from a dictionary.

        Args:
            data: Configuration dictionary (can be partial)

        Returns:
            ProsimConfig with defaults for any missing values
        """
        return cls.model_validate(data)

    @classmethod
    def from_file(cls, path: str | Path) -> "ProsimConfig":
        """Load configuration from a JSON or YAML file.

        Args:
            path: Path to configuration file (.json or .yaml/.yml)

        Returns:
            Parsed configuration

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        suffix = path.suffix.lower()

        if suffix == ".json":
            import json

            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        elif suffix in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore[import-untyped]

                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except ImportError as e:
                raise ImportError(
                    "PyYAML is required for YAML config files. "
                    "Install with: pip install pyyaml"
                ) from e
        else:
            raise ValueError(
                f"Unsupported config file format: {suffix}. "
                "Use .json or .yaml/.yml"
            )

        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary."""
        return self.model_dump()

    def to_file(self, path: str | Path) -> None:
        """Save configuration to a JSON or YAML file.

        Args:
            path: Path to save configuration to

        Raises:
            ValueError: If file format is not supported
        """
        path = Path(path)
        suffix = path.suffix.lower()
        data = self.to_dict()

        if suffix == ".json":
            import json

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        elif suffix in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore[import-untyped]

                with open(path, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            except ImportError as e:
                raise ImportError(
                    "PyYAML is required for YAML config files. "
                    "Install with: pip install pyyaml"
                ) from e
        else:
            raise ValueError(
                f"Unsupported config file format: {suffix}. "
                "Use .json or .yaml/.yml"
            )

    def merge(self, overrides: dict[str, Any]) -> "ProsimConfig":
        """Create a new config with overrides applied.

        Args:
            overrides: Dictionary of values to override

        Returns:
            New ProsimConfig with overrides merged in
        """
        base = self.to_dict()
        _deep_merge(base, overrides)
        return ProsimConfig.from_dict(base)


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> None:
    """Deep merge overrides into base dict (in place).

    Args:
        base: Base dictionary to merge into
        overrides: Values to merge in
    """
    for key, value in overrides.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def get_default_config() -> ProsimConfig:
    """Get the default PROSIM configuration.

    Returns:
        ProsimConfig with all default values
    """
    return ProsimConfig()
