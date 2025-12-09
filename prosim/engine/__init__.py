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
]

# Additional engine components will be imported here as they are implemented
# from prosim.engine.simulation import Simulation
# from prosim.engine.costs import calculate_costs
# from prosim.engine.demand import generate_demand
