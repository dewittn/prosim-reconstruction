"""
PROSIM simulation engine.

This module contains the core simulation logic:
- Inventory management
- Workforce/operator management
- Production calculations (Parts and Assembly departments)
- Cost calculations
- Demand generation and fulfillment
- Main simulation loop
- Calibration utilities for parameter tuning
"""

from prosim.engine.calibration import (
    CALIBRATION_DATA,
    CalibrationReport,
    ProductionRateAnalysis,
    RejectRateAnalysis,
    analyze_operator_efficiency_from_report,
    analyze_production_rates_from_report,
    analyze_reject_rate_from_report,
    calculate_efficiency_statistics,
    calculate_quality_adjusted_reject_rate,
    create_calibrated_config,
    get_calibrated_reject_rate,
    infer_training_status_from_efficiency,
    verify_production_formula,
)
from prosim.engine.costs import (
    CostCalculationInput,
    CostCalculator,
    CumulativeCostReport,
    OverheadCosts,
    ProductCosts,
    WeeklyCostReport,
)
from prosim.engine.demand import (
    DemandGenerationResult,
    DemandManager,
    ForecastUpdateResult,
    ShippingPeriodDemand,
)
from prosim.engine.inventory import (
    ConsumptionResult,
    DemandFulfillmentResult,
    InventoryManager,
    OrderReceiptResult,
)
from prosim.engine.production import (
    DepartmentProductionResult,
    MachineProductionResult,
    ProductionEngine,
    ProductionInput,
    ProductionResult,
)
from prosim.engine.workforce import (
    OperatorEfficiencyResult,
    OperatorManager,
    TrainingResult,
    WorkforceCostResult,
    WorkforceSchedulingResult,
)

__all__ = [
    # Calibration
    "CALIBRATION_DATA",
    "CalibrationReport",
    "ProductionRateAnalysis",
    "RejectRateAnalysis",
    "analyze_operator_efficiency_from_report",
    "analyze_production_rates_from_report",
    "analyze_reject_rate_from_report",
    "calculate_efficiency_statistics",
    "calculate_quality_adjusted_reject_rate",
    "create_calibrated_config",
    "get_calibrated_reject_rate",
    "infer_training_status_from_efficiency",
    "verify_production_formula",
    # Costs
    "CostCalculator",
    "CostCalculationInput",
    "WeeklyCostReport",
    "CumulativeCostReport",
    "ProductCosts",
    "OverheadCosts",
    # Demand
    "DemandManager",
    "DemandGenerationResult",
    "ShippingPeriodDemand",
    "ForecastUpdateResult",
    # Inventory
    "InventoryManager",
    "OrderReceiptResult",
    "ConsumptionResult",
    "DemandFulfillmentResult",
    # Production
    "ProductionEngine",
    "ProductionInput",
    "ProductionResult",
    "DepartmentProductionResult",
    "MachineProductionResult",
    # Workforce
    "OperatorManager",
    "OperatorEfficiencyResult",
    "WorkforceSchedulingResult",
    "WorkforceCostResult",
    "TrainingResult",
    # Simulation
    "Simulation",
    "SimulationWeekResult",
    "run_simulation",
]

from prosim.engine.simulation import (
    Simulation,
    SimulationWeekResult,
    run_simulation,
)
