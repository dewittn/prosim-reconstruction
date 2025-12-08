"""
PROSIM simulation engine.

This module contains the core simulation logic:
- Inventory management
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
    ProductionInput,
)

__all__ = [
    "InventoryManager",
    "OrderReceiptResult",
    "ConsumptionResult",
    "ProductionInput",
    "DemandFulfillmentResult",
]

# Additional engine components will be imported here as they are implemented
# from prosim.engine.simulation import Simulation
# from prosim.engine.production import calculate_production
# from prosim.engine.costs import calculate_costs
# from prosim.engine.demand import generate_demand
