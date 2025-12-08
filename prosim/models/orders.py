"""
Order models for PROSIM simulation.

Tracks pending orders for:
- Raw materials (regular: 3 week lead, expedited: 1 week lead)
- Purchased finished parts (1 week lead time)
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderType(str, Enum):
    """Types of orders that can be placed."""

    RAW_MATERIALS_REGULAR = "raw_materials_regular"
    RAW_MATERIALS_EXPEDITED = "raw_materials_expedited"
    PARTS_X_PRIME = "parts_X'"
    PARTS_Y_PRIME = "parts_Y'"
    PARTS_Z_PRIME = "parts_Z'"


# Lead times by order type (in weeks)
LEAD_TIMES = {
    OrderType.RAW_MATERIALS_REGULAR: 3,
    OrderType.RAW_MATERIALS_EXPEDITED: 1,
    OrderType.PARTS_X_PRIME: 1,
    OrderType.PARTS_Y_PRIME: 1,
    OrderType.PARTS_Z_PRIME: 1,
}


class Order(BaseModel):
    """Represents a pending order.

    Orders are placed in one week and received after the lead time.
    """

    order_type: OrderType = Field(description="Type of order")
    amount: float = Field(ge=0, description="Quantity ordered")
    week_placed: int = Field(ge=1, description="Week when order was placed")
    week_due: int = Field(ge=1, description="Week when order will be received")

    @property
    def is_raw_materials(self) -> bool:
        """Check if this is a raw materials order."""
        return self.order_type in (
            OrderType.RAW_MATERIALS_REGULAR,
            OrderType.RAW_MATERIALS_EXPEDITED,
        )

    @property
    def is_expedited(self) -> bool:
        """Check if this is an expedited order."""
        return self.order_type == OrderType.RAW_MATERIALS_EXPEDITED

    @property
    def is_parts(self) -> bool:
        """Check if this is a parts order."""
        return self.order_type in (
            OrderType.PARTS_X_PRIME,
            OrderType.PARTS_Y_PRIME,
            OrderType.PARTS_Z_PRIME,
        )

    @property
    def part_type(self) -> Optional[str]:
        """Get part type if this is a parts order."""
        mapping = {
            OrderType.PARTS_X_PRIME: "X'",
            OrderType.PARTS_Y_PRIME: "Y'",
            OrderType.PARTS_Z_PRIME: "Z'",
        }
        return mapping.get(self.order_type)

    def is_due(self, current_week: int) -> bool:
        """Check if order is due in the current week."""
        return self.week_due == current_week


class OrderBook(BaseModel):
    """Manages all pending orders for a company."""

    orders: list[Order] = Field(default_factory=list, description="List of pending orders")

    def place_order(
        self,
        order_type: OrderType,
        amount: float,
        current_week: int,
    ) -> tuple["OrderBook", Order]:
        """Place a new order.

        Args:
            order_type: Type of order to place
            amount: Quantity to order
            current_week: Current simulation week

        Returns:
            Tuple of (updated OrderBook, new Order)
        """
        lead_time = LEAD_TIMES[order_type]
        order = Order(
            order_type=order_type,
            amount=amount,
            week_placed=current_week,
            week_due=current_week + lead_time,
        )
        new_orders = self.orders + [order]
        return self.model_copy(update={"orders": new_orders}), order

    def get_due_orders(self, current_week: int) -> list[Order]:
        """Get all orders due in the current week."""
        return [o for o in self.orders if o.is_due(current_week)]

    def get_due_raw_materials(self, current_week: int) -> list[Order]:
        """Get raw materials orders due in the current week."""
        return [
            o for o in self.orders
            if o.is_due(current_week) and o.is_raw_materials
        ]

    def get_due_parts(self, current_week: int) -> list[Order]:
        """Get parts orders due in the current week."""
        return [o for o in self.orders if o.is_due(current_week) and o.is_parts]

    def get_due_parts_by_type(
        self, current_week: int, part_type: str
    ) -> list[Order]:
        """Get parts orders due for a specific part type."""
        return [
            o for o in self.orders
            if o.is_due(current_week) and o.part_type == part_type
        ]

    def get_pending_orders(self, current_week: int) -> list[Order]:
        """Get all orders not yet received."""
        return [o for o in self.orders if o.week_due > current_week]

    def receive_orders(self, current_week: int) -> tuple["OrderBook", list[Order]]:
        """Receive all orders due this week.

        Returns:
            Tuple of (updated OrderBook without received orders, list of received orders)
        """
        received = self.get_due_orders(current_week)
        remaining = [o for o in self.orders if not o.is_due(current_week)]
        return self.model_copy(update={"orders": remaining}), received

    def total_raw_materials_due(self, current_week: int) -> float:
        """Calculate total raw materials due this week."""
        return sum(o.amount for o in self.get_due_raw_materials(current_week))

    def total_parts_due_by_type(self, current_week: int) -> dict[str, float]:
        """Calculate total parts due by type this week."""
        totals: dict[str, float] = {"X'": 0.0, "Y'": 0.0, "Z'": 0.0}
        for order in self.get_due_parts(current_week):
            if order.part_type:
                totals[order.part_type] += order.amount
        return totals


class DemandForecast(BaseModel):
    """Demand forecast for products.

    Forecasts have uncertainty that decreases as the shipping week approaches.
    """

    product_type: str = Field(description="Product type (X, Y, or Z)")
    shipping_week: int = Field(ge=1, description="Week when demand must be fulfilled")
    estimated_demand: float = Field(ge=0, description="Estimated demand quantity")
    actual_demand: Optional[float] = Field(
        default=None,
        ge=0,
        description="Actual demand (known only at shipping week)"
    )
    carryover: float = Field(
        default=0.0,
        ge=0,
        description="Unfulfilled demand from previous period"
    )

    @property
    def total_demand(self) -> float:
        """Total demand including carryover."""
        demand = self.actual_demand if self.actual_demand is not None else self.estimated_demand
        return demand + self.carryover


class DemandSchedule(BaseModel):
    """Manages demand forecasts for all products."""

    forecasts: list[DemandForecast] = Field(
        default_factory=list,
        description="List of demand forecasts"
    )
    shipping_frequency: int = Field(
        default=4,
        ge=1,
        description="Weeks between shipping periods"
    )

    def get_forecasts_for_week(self, week: int) -> list[DemandForecast]:
        """Get all forecasts with shipping in a given week."""
        return [f for f in self.forecasts if f.shipping_week == week]

    def get_forecast(self, product_type: str, shipping_week: int) -> Optional[DemandForecast]:
        """Get specific forecast by product and shipping week."""
        for f in self.forecasts:
            if f.product_type == product_type and f.shipping_week == shipping_week:
                return f
        return None

    def add_forecast(self, forecast: DemandForecast) -> "DemandSchedule":
        """Add a new demand forecast."""
        new_forecasts = self.forecasts + [forecast]
        return self.model_copy(update={"forecasts": new_forecasts})

    def update_forecast(
        self,
        product_type: str,
        shipping_week: int,
        actual_demand: Optional[float] = None,
        carryover: Optional[float] = None,
    ) -> "DemandSchedule":
        """Update an existing forecast."""
        new_forecasts = []
        for f in self.forecasts:
            if f.product_type == product_type and f.shipping_week == shipping_week:
                updates = {}
                if actual_demand is not None:
                    updates["actual_demand"] = actual_demand
                if carryover is not None:
                    updates["carryover"] = carryover
                new_forecasts.append(f.model_copy(update=updates))
            else:
                new_forecasts.append(f)
        return self.model_copy(update={"forecasts": new_forecasts})

    def is_shipping_week(self, week: int) -> bool:
        """Check if the given week is a shipping week."""
        return week % self.shipping_frequency == 0

    def next_shipping_week(self, current_week: int) -> int:
        """Calculate the next shipping week."""
        remainder = current_week % self.shipping_frequency
        if remainder == 0:
            return current_week
        return current_week + (self.shipping_frequency - remainder)
