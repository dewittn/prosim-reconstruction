"""
Configuration management for PROSIM.

This module provides:
- Default simulation parameters
- Configuration schema and validation
- Support for custom configuration files (JSON/YAML)
"""

from prosim.config.defaults import DEFAULT_CONFIG
from prosim.config.schema import (
    CarryingCostRatesConfig,
    CostsConfig,
    DemandConfig,
    EquipmentConfig,
    EquipmentRatesConfig,
    FixedCostsConfig,
    LaborRatesConfig,
    LogisticsConfig,
    MachineRepairConfig,
    OperatorEfficiencyConfig,
    ProductionRatesConfig,
    ProsimConfig,
    SimulationConfig,
    WorkforceConfig,
    WorkforceCostsConfig,
    get_default_config,
)

__all__ = [
    # Legacy dict-based config
    "DEFAULT_CONFIG",
    # Pydantic config classes
    "CarryingCostRatesConfig",
    "CostsConfig",
    "DemandConfig",
    "EquipmentConfig",
    "EquipmentRatesConfig",
    "FixedCostsConfig",
    "LaborRatesConfig",
    "LogisticsConfig",
    "MachineRepairConfig",
    "OperatorEfficiencyConfig",
    "ProductionRatesConfig",
    "ProsimConfig",
    "SimulationConfig",
    "WorkforceConfig",
    "WorkforceCostsConfig",
    # Functions
    "get_default_config",
]
