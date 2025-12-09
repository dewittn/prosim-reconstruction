"""
PROSIM simulation engine.

This module contains the core simulation logic:
- Inventory management
- Workforce/operator management
- Production calculations (Parts and Assembly departments)
- Cost calculations
- Demand generation and fulfillment
- Main simulation loop
"""

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
