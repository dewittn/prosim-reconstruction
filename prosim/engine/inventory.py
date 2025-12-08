"""
Inventory management for PROSIM simulation.

This module handles:
- Raw material tracking and order receiving
- Parts inventory (X', Y', Z') - manufactured and purchased
- Products inventory (X, Y, Z) - assembled goods
- Consumption calculations throughout the production chain

The flow is:
    Raw Materials → Parts Department → Parts (X', Y', Z')
    Parts → Assembly Department → Products (X, Y, Z)
    Products → Shipped to meet demand
"""

from dataclasses import dataclass
from typing import Optional

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.models.inventory import (
    AllPartsInventory,
    AllProductsInventory,
    Inventory,
    PartsInventory,
    ProductsInventory,
    RawMaterialsInventory,
)
from prosim.models.orders import Order, OrderBook, OrderType


@dataclass
class OrderReceiptResult:
    """Result of receiving orders for a week."""

    raw_materials_received: float
    parts_received: dict[str, float]  # Part type -> quantity
    orders_processed: list[Order]


@dataclass
class ConsumptionResult:
    """Result of consumption calculations."""

    raw_materials_consumed: float
    parts_consumed: dict[str, float]  # Part type -> quantity consumed
    raw_materials_shortage: float  # Amount that couldn't be consumed
    parts_shortage: dict[str, float]  # Part type -> shortage


@dataclass
class ProductionInput:
    """Input for production calculations (from production engine)."""

    parts_produced: dict[str, float]  # Part type -> gross production
    products_assembled: dict[str, float]  # Product type -> gross production


@dataclass
class DemandFulfillmentResult:
    """Result of fulfilling demand."""

    units_shipped: dict[str, float]  # Product type -> shipped
    units_short: dict[str, float]  # Product type -> unfulfilled
    carryover: dict[str, float]  # Product type -> carryover to next period


class InventoryManager:
    """Manages all inventory operations for a company.

    This class coordinates inventory updates across the production chain:
    1. Receive orders (raw materials and purchased parts)
    2. Consume raw materials during parts production
    3. Track parts produced in Parts Department
    4. Consume parts during assembly
    5. Track products assembled in Assembly Department
    6. Ship products to fulfill demand
    """

    def __init__(self, config: Optional[ProsimConfig] = None):
        """Initialize inventory manager.

        Args:
            config: Simulation configuration (uses defaults if None)
        """
        self.config = config or get_default_config()

    def receive_orders(
        self,
        inventory: Inventory,
        order_book: OrderBook,
        current_week: int,
    ) -> tuple[Inventory, OrderBook, OrderReceiptResult]:
        """Receive all orders due in the current week.

        Updates inventory with received raw materials and purchased parts,
        and removes fulfilled orders from the order book.

        Args:
            inventory: Current inventory state
            order_book: Current order book with pending orders
            current_week: Current simulation week

        Returns:
            Tuple of (updated inventory, updated order book, receipt details)
        """
        # Get orders due this week
        due_orders = order_book.get_due_orders(current_week)

        # Track what was received
        raw_materials_received = 0.0
        parts_received: dict[str, float] = {"X'": 0.0, "Y'": 0.0, "Z'": 0.0}

        for order in due_orders:
            if order.is_raw_materials:
                raw_materials_received += order.amount
            elif order.is_parts and order.part_type:
                parts_received[order.part_type] += order.amount

        # Update raw materials inventory
        new_rm = inventory.raw_materials.model_copy(
            update={
                "orders_received": inventory.raw_materials.orders_received
                + raw_materials_received
            }
        )

        # Update parts inventory
        new_x_prime = inventory.parts.x_prime.model_copy(
            update={
                "orders_received": inventory.parts.x_prime.orders_received
                + parts_received["X'"]
            }
        )
        new_y_prime = inventory.parts.y_prime.model_copy(
            update={
                "orders_received": inventory.parts.y_prime.orders_received
                + parts_received["Y'"]
            }
        )
        new_z_prime = inventory.parts.z_prime.model_copy(
            update={
                "orders_received": inventory.parts.z_prime.orders_received
                + parts_received["Z'"]
            }
        )

        new_parts = AllPartsInventory(
            x_prime=new_x_prime,
            y_prime=new_y_prime,
            z_prime=new_z_prime,
        )

        # Create updated inventory
        new_inventory = Inventory(
            raw_materials=new_rm,
            parts=new_parts,
            products=inventory.products,
        )

        # Remove fulfilled orders from order book
        new_order_book, _ = order_book.receive_orders(current_week)

        result = OrderReceiptResult(
            raw_materials_received=raw_materials_received,
            parts_received=parts_received,
            orders_processed=due_orders,
        )

        return new_inventory, new_order_book, result

    def place_orders(
        self,
        order_book: OrderBook,
        current_week: int,
        raw_materials_regular: float = 0.0,
        raw_materials_expedited: float = 0.0,
        parts_x_prime: float = 0.0,
        parts_y_prime: float = 0.0,
        parts_z_prime: float = 0.0,
    ) -> OrderBook:
        """Place new orders for raw materials and parts.

        Args:
            order_book: Current order book
            current_week: Current simulation week
            raw_materials_regular: Regular raw materials to order (3 week lead)
            raw_materials_expedited: Expedited raw materials (1 week lead)
            parts_x_prime: X' parts to purchase (1 week lead)
            parts_y_prime: Y' parts to purchase (1 week lead)
            parts_z_prime: Z' parts to purchase (1 week lead)

        Returns:
            Updated order book with new orders
        """
        current_book = order_book

        if raw_materials_regular > 0:
            current_book, _ = current_book.place_order(
                OrderType.RAW_MATERIALS_REGULAR,
                raw_materials_regular,
                current_week,
            )

        if raw_materials_expedited > 0:
            current_book, _ = current_book.place_order(
                OrderType.RAW_MATERIALS_EXPEDITED,
                raw_materials_expedited,
                current_week,
            )

        if parts_x_prime > 0:
            current_book, _ = current_book.place_order(
                OrderType.PARTS_X_PRIME,
                parts_x_prime,
                current_week,
            )

        if parts_y_prime > 0:
            current_book, _ = current_book.place_order(
                OrderType.PARTS_Y_PRIME,
                parts_y_prime,
                current_week,
            )

        if parts_z_prime > 0:
            current_book, _ = current_book.place_order(
                OrderType.PARTS_Z_PRIME,
                parts_z_prime,
                current_week,
            )

        return current_book

    def calculate_raw_material_consumption(
        self,
        gross_parts_production: dict[str, float],
    ) -> float:
        """Calculate raw materials consumed for parts production.

        Raw materials are consumed based on gross production (before rejects).

        Args:
            gross_parts_production: Parts produced by type (before reject removal)

        Returns:
            Total raw materials consumed
        """
        rm_per_part = self.config.production.raw_materials_per_part
        total = 0.0

        for part_type, quantity in gross_parts_production.items():
            # Normalize part type (allow both "X'" and "X")
            lookup_key = part_type if part_type.endswith("'") else f"{part_type}'"
            rate = rm_per_part.get(lookup_key, 1.0)
            total += quantity * rate

        return total

    def calculate_parts_consumption(
        self,
        gross_products_production: dict[str, float],
    ) -> dict[str, float]:
        """Calculate parts consumed for product assembly.

        Parts are consumed based on the bill of materials (BOM).
        Consumption is based on gross production (before rejects).

        Args:
            gross_products_production: Products assembled by type (before rejects)

        Returns:
            Parts consumed by type
        """
        bom = self.config.production.bom
        consumption: dict[str, float] = {"X'": 0.0, "Y'": 0.0, "Z'": 0.0}

        for product_type, quantity in gross_products_production.items():
            if product_type in bom:
                for part_type, parts_per_product in bom[product_type].items():
                    consumption[part_type] += quantity * parts_per_product

        return consumption

    def consume_raw_materials(
        self,
        inventory: Inventory,
        gross_parts_production: dict[str, float],
    ) -> tuple[Inventory, ConsumptionResult]:
        """Consume raw materials for parts production.

        If insufficient raw materials are available, production is limited.

        Args:
            inventory: Current inventory state
            gross_parts_production: Parts to produce by type

        Returns:
            Tuple of (updated inventory, consumption result)
        """
        required = self.calculate_raw_material_consumption(gross_parts_production)

        # Calculate available raw materials
        available = (
            inventory.raw_materials.beginning
            + inventory.raw_materials.orders_received
            - inventory.raw_materials.used_in_production
        )

        # Determine actual consumption
        actual_consumption = min(required, available)
        shortage = max(0.0, required - available)

        # Update raw materials inventory
        new_rm = inventory.raw_materials.model_copy(
            update={
                "used_in_production": inventory.raw_materials.used_in_production
                + actual_consumption
            }
        )

        new_inventory = Inventory(
            raw_materials=new_rm,
            parts=inventory.parts,
            products=inventory.products,
        )

        result = ConsumptionResult(
            raw_materials_consumed=actual_consumption,
            parts_consumed={},
            raw_materials_shortage=shortage,
            parts_shortage={},
        )

        return new_inventory, result

    def add_parts_production(
        self,
        inventory: Inventory,
        net_parts_production: dict[str, float],
    ) -> Inventory:
        """Add parts production to inventory.

        Parts are added after reject removal (net production).

        Args:
            inventory: Current inventory state
            net_parts_production: Net parts produced by type (after rejects)

        Returns:
            Updated inventory with new parts
        """
        new_x_prime = inventory.parts.x_prime.model_copy(
            update={
                "production": inventory.parts.x_prime.production
                + net_parts_production.get("X'", 0.0)
            }
        )
        new_y_prime = inventory.parts.y_prime.model_copy(
            update={
                "production": inventory.parts.y_prime.production
                + net_parts_production.get("Y'", 0.0)
            }
        )
        new_z_prime = inventory.parts.z_prime.model_copy(
            update={
                "production": inventory.parts.z_prime.production
                + net_parts_production.get("Z'", 0.0)
            }
        )

        new_parts = AllPartsInventory(
            x_prime=new_x_prime,
            y_prime=new_y_prime,
            z_prime=new_z_prime,
        )

        return Inventory(
            raw_materials=inventory.raw_materials,
            parts=new_parts,
            products=inventory.products,
        )

    def consume_parts(
        self,
        inventory: Inventory,
        gross_products_production: dict[str, float],
    ) -> tuple[Inventory, ConsumptionResult]:
        """Consume parts for product assembly.

        If insufficient parts are available, assembly is limited.

        Args:
            inventory: Current inventory state
            gross_products_production: Products to assemble by type

        Returns:
            Tuple of (updated inventory, consumption result)
        """
        required = self.calculate_parts_consumption(gross_products_production)

        actual_consumption: dict[str, float] = {}
        shortage: dict[str, float] = {}

        # Process each part type
        for part_type in ["X'", "Y'", "Z'"]:
            part_inv = inventory.parts.get(part_type)
            available = (
                part_inv.beginning
                + part_inv.orders_received
                + part_inv.production
                - part_inv.used_in_assembly
            )
            req = required.get(part_type, 0.0)
            actual_consumption[part_type] = min(req, available)
            shortage[part_type] = max(0.0, req - available)

        # Update parts inventory
        new_x_prime = inventory.parts.x_prime.model_copy(
            update={
                "used_in_assembly": inventory.parts.x_prime.used_in_assembly
                + actual_consumption["X'"]
            }
        )
        new_y_prime = inventory.parts.y_prime.model_copy(
            update={
                "used_in_assembly": inventory.parts.y_prime.used_in_assembly
                + actual_consumption["Y'"]
            }
        )
        new_z_prime = inventory.parts.z_prime.model_copy(
            update={
                "used_in_assembly": inventory.parts.z_prime.used_in_assembly
                + actual_consumption["Z'"]
            }
        )

        new_parts = AllPartsInventory(
            x_prime=new_x_prime,
            y_prime=new_y_prime,
            z_prime=new_z_prime,
        )

        new_inventory = Inventory(
            raw_materials=inventory.raw_materials,
            parts=new_parts,
            products=inventory.products,
        )

        result = ConsumptionResult(
            raw_materials_consumed=0.0,
            parts_consumed=actual_consumption,
            raw_materials_shortage=0.0,
            parts_shortage=shortage,
        )

        return new_inventory, result

    def add_products_production(
        self,
        inventory: Inventory,
        net_products_production: dict[str, float],
    ) -> Inventory:
        """Add assembled products to inventory.

        Products are added after reject removal (net production).

        Args:
            inventory: Current inventory state
            net_products_production: Net products assembled by type (after rejects)

        Returns:
            Updated inventory with new products
        """
        new_x = inventory.products.x.model_copy(
            update={
                "production": inventory.products.x.production
                + net_products_production.get("X", 0.0)
            }
        )
        new_y = inventory.products.y.model_copy(
            update={
                "production": inventory.products.y.production
                + net_products_production.get("Y", 0.0)
            }
        )
        new_z = inventory.products.z.model_copy(
            update={
                "production": inventory.products.z.production
                + net_products_production.get("Z", 0.0)
            }
        )

        new_products = AllProductsInventory(
            x=new_x,
            y=new_y,
            z=new_z,
        )

        return Inventory(
            raw_materials=inventory.raw_materials,
            parts=inventory.parts,
            products=new_products,
        )

    def fulfill_demand(
        self,
        inventory: Inventory,
        demand: dict[str, float],
    ) -> tuple[Inventory, DemandFulfillmentResult]:
        """Fulfill customer demand from products inventory.

        Ships as much as possible from available inventory.
        Unfulfilled demand becomes carryover for next period.

        Args:
            inventory: Current inventory state
            demand: Total demand by product type (including carryover)

        Returns:
            Tuple of (updated inventory, fulfillment result)
        """
        shipped: dict[str, float] = {}
        short: dict[str, float] = {}
        carryover: dict[str, float] = {}

        for product_type in ["X", "Y", "Z"]:
            product_inv = inventory.products.get(product_type)
            available = (
                product_inv.beginning
                + product_inv.production
                - product_inv.demand_fulfilled
            )
            requested = demand.get(product_type, 0.0)

            units_shipped = min(requested, available)
            units_short = max(0.0, requested - available)

            shipped[product_type] = units_shipped
            short[product_type] = units_short
            carryover[product_type] = units_short  # Unfulfilled becomes carryover

        # Update products inventory
        new_x = inventory.products.x.model_copy(
            update={
                "demand_fulfilled": inventory.products.x.demand_fulfilled
                + shipped["X"]
            }
        )
        new_y = inventory.products.y.model_copy(
            update={
                "demand_fulfilled": inventory.products.y.demand_fulfilled
                + shipped["Y"]
            }
        )
        new_z = inventory.products.z.model_copy(
            update={
                "demand_fulfilled": inventory.products.z.demand_fulfilled
                + shipped["Z"]
            }
        )

        new_products = AllProductsInventory(
            x=new_x,
            y=new_y,
            z=new_z,
        )

        new_inventory = Inventory(
            raw_materials=inventory.raw_materials,
            parts=inventory.parts,
            products=new_products,
        )

        result = DemandFulfillmentResult(
            units_shipped=shipped,
            units_short=short,
            carryover=carryover,
        )

        return new_inventory, result

    def get_available_raw_materials(self, inventory: Inventory) -> float:
        """Get available raw materials for production.

        Args:
            inventory: Current inventory state

        Returns:
            Available raw materials
        """
        rm = inventory.raw_materials
        return rm.beginning + rm.orders_received - rm.used_in_production

    def get_available_parts(self, inventory: Inventory) -> dict[str, float]:
        """Get available parts for assembly.

        Args:
            inventory: Current inventory state

        Returns:
            Available parts by type
        """
        result = {}
        for part_type in ["X'", "Y'", "Z'"]:
            part_inv = inventory.parts.get(part_type)
            result[part_type] = (
                part_inv.beginning
                + part_inv.orders_received
                + part_inv.production
                - part_inv.used_in_assembly
            )
        return result

    def get_available_products(self, inventory: Inventory) -> dict[str, float]:
        """Get available products for shipping.

        Args:
            inventory: Current inventory state

        Returns:
            Available products by type
        """
        result = {}
        for product_type in ["X", "Y", "Z"]:
            product_inv = inventory.products.get(product_type)
            result[product_type] = (
                product_inv.beginning
                + product_inv.production
                - product_inv.demand_fulfilled
            )
        return result

    def get_ending_inventory(self, inventory: Inventory) -> dict[str, float]:
        """Get all ending inventory values.

        Args:
            inventory: Current inventory state

        Returns:
            Dictionary with all ending inventory values
        """
        return {
            "raw_materials": inventory.raw_materials.ending,
            "X'": inventory.parts.x_prime.ending,
            "Y'": inventory.parts.y_prime.ending,
            "Z'": inventory.parts.z_prime.ending,
            "X": inventory.products.x.ending,
            "Y": inventory.products.y.ending,
            "Z": inventory.products.z.ending,
        }
