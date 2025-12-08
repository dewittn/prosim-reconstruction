"""
Tests for the inventory management module.

Tests cover:
- Order receiving (raw materials and purchased parts)
- Placing new orders
- Raw material consumption for parts production
- Parts consumption for product assembly
- Product production tracking
- Demand fulfillment and carryover
- Available inventory queries
"""

import pytest

from prosim.config.schema import ProsimConfig, ProductionRatesConfig
from prosim.engine.inventory import (
    ConsumptionResult,
    DemandFulfillmentResult,
    InventoryManager,
    OrderReceiptResult,
)
from prosim.models.inventory import (
    AllPartsInventory,
    AllProductsInventory,
    Inventory,
    PartsInventory,
    ProductsInventory,
    RawMaterialsInventory,
)
from prosim.models.orders import Order, OrderBook, OrderType


class TestOrderReceiving:
    """Tests for receiving orders."""

    def test_receive_raw_materials_regular(self):
        """Test receiving regular raw materials order."""
        manager = InventoryManager()
        inventory = Inventory()

        # Place order in week 1, due in week 4 (3 week lead time)
        order_book = OrderBook()
        order_book, _ = order_book.place_order(
            OrderType.RAW_MATERIALS_REGULAR, 1000.0, current_week=1
        )

        # Receive in week 4
        new_inv, new_book, result = manager.receive_orders(
            inventory, order_book, current_week=4
        )

        assert result.raw_materials_received == 1000.0
        assert new_inv.raw_materials.orders_received == 1000.0
        assert len(new_book.orders) == 0

    def test_receive_raw_materials_expedited(self):
        """Test receiving expedited raw materials order."""
        manager = InventoryManager()
        inventory = Inventory()

        # Place expedited order in week 1, due in week 2 (1 week lead time)
        order_book = OrderBook()
        order_book, _ = order_book.place_order(
            OrderType.RAW_MATERIALS_EXPEDITED, 500.0, current_week=1
        )

        # Receive in week 2
        new_inv, new_book, result = manager.receive_orders(
            inventory, order_book, current_week=2
        )

        assert result.raw_materials_received == 500.0
        assert new_inv.raw_materials.orders_received == 500.0
        assert len(new_book.orders) == 0

    def test_receive_purchased_parts(self):
        """Test receiving purchased parts orders."""
        manager = InventoryManager()
        inventory = Inventory()

        # Place parts orders in week 1, due in week 2 (1 week lead time)
        order_book = OrderBook()
        order_book, _ = order_book.place_order(
            OrderType.PARTS_X_PRIME, 100.0, current_week=1
        )
        order_book, _ = order_book.place_order(
            OrderType.PARTS_Y_PRIME, 200.0, current_week=1
        )
        order_book, _ = order_book.place_order(
            OrderType.PARTS_Z_PRIME, 150.0, current_week=1
        )

        # Receive in week 2
        new_inv, new_book, result = manager.receive_orders(
            inventory, order_book, current_week=2
        )

        assert result.parts_received == {"X'": 100.0, "Y'": 200.0, "Z'": 150.0}
        assert new_inv.parts.x_prime.orders_received == 100.0
        assert new_inv.parts.y_prime.orders_received == 200.0
        assert new_inv.parts.z_prime.orders_received == 150.0
        assert len(new_book.orders) == 0

    def test_receive_mixed_orders(self):
        """Test receiving mix of raw materials and parts."""
        manager = InventoryManager()
        inventory = Inventory()

        order_book = OrderBook()
        # Expedited RM due week 2
        order_book, _ = order_book.place_order(
            OrderType.RAW_MATERIALS_EXPEDITED, 500.0, current_week=1
        )
        # Parts due week 2
        order_book, _ = order_book.place_order(
            OrderType.PARTS_X_PRIME, 100.0, current_week=1
        )
        # Regular RM due week 4 (not received yet)
        order_book, _ = order_book.place_order(
            OrderType.RAW_MATERIALS_REGULAR, 1000.0, current_week=1
        )

        # Receive in week 2
        new_inv, new_book, result = manager.receive_orders(
            inventory, order_book, current_week=2
        )

        assert result.raw_materials_received == 500.0
        assert result.parts_received["X'"] == 100.0
        assert len(result.orders_processed) == 2
        assert len(new_book.orders) == 1  # Regular RM still pending

    def test_no_orders_due(self):
        """Test when no orders are due."""
        manager = InventoryManager()
        inventory = Inventory()

        order_book = OrderBook()
        order_book, _ = order_book.place_order(
            OrderType.RAW_MATERIALS_REGULAR, 1000.0, current_week=1
        )

        # Check week 2 (order not due until week 4)
        new_inv, new_book, result = manager.receive_orders(
            inventory, order_book, current_week=2
        )

        assert result.raw_materials_received == 0.0
        assert len(result.orders_processed) == 0
        assert len(new_book.orders) == 1


class TestPlaceOrders:
    """Tests for placing new orders."""

    def test_place_all_order_types(self):
        """Test placing all types of orders."""
        manager = InventoryManager()
        order_book = OrderBook()

        new_book = manager.place_orders(
            order_book,
            current_week=1,
            raw_materials_regular=1000.0,
            raw_materials_expedited=500.0,
            parts_x_prime=100.0,
            parts_y_prime=200.0,
            parts_z_prime=150.0,
        )

        assert len(new_book.orders) == 5

        # Check regular RM (due week 4)
        rm_regular = [
            o for o in new_book.orders
            if o.order_type == OrderType.RAW_MATERIALS_REGULAR
        ]
        assert len(rm_regular) == 1
        assert rm_regular[0].amount == 1000.0
        assert rm_regular[0].week_due == 4

        # Check expedited RM (due week 2)
        rm_exp = [
            o for o in new_book.orders
            if o.order_type == OrderType.RAW_MATERIALS_EXPEDITED
        ]
        assert len(rm_exp) == 1
        assert rm_exp[0].amount == 500.0
        assert rm_exp[0].week_due == 2

    def test_place_zero_orders_ignored(self):
        """Test that zero quantities don't create orders."""
        manager = InventoryManager()
        order_book = OrderBook()

        new_book = manager.place_orders(
            order_book,
            current_week=1,
            raw_materials_regular=0.0,
            parts_x_prime=100.0,
        )

        assert len(new_book.orders) == 1
        assert new_book.orders[0].order_type == OrderType.PARTS_X_PRIME


class TestRawMaterialConsumption:
    """Tests for raw material consumption calculations."""

    def test_calculate_consumption_standard_bom(self):
        """Test raw material consumption with default 1:1 BOM."""
        manager = InventoryManager()

        gross_production = {"X'": 100.0, "Y'": 200.0, "Z'": 150.0}
        consumed = manager.calculate_raw_material_consumption(gross_production)

        # With default 1:1 ratio, total should equal sum of production
        assert consumed == 450.0

    def test_calculate_consumption_custom_rates(self):
        """Test raw material consumption with custom rates."""
        config = ProsimConfig(
            production=ProductionRatesConfig(
                raw_materials_per_part={"X'": 2.0, "Y'": 1.5, "Z'": 1.0}
            )
        )
        manager = InventoryManager(config)

        gross_production = {"X'": 100.0, "Y'": 200.0, "Z'": 150.0}
        consumed = manager.calculate_raw_material_consumption(gross_production)

        # X': 100 * 2.0 = 200
        # Y': 200 * 1.5 = 300
        # Z': 150 * 1.0 = 150
        assert consumed == 650.0

    def test_consume_raw_materials_sufficient(self):
        """Test consuming raw materials when sufficient available."""
        manager = InventoryManager()

        # Start with 500 RM
        inventory = Inventory(
            raw_materials=RawMaterialsInventory(beginning=500.0)
        )

        gross_production = {"X'": 100.0, "Y'": 200.0}  # Needs 300 RM

        new_inv, result = manager.consume_raw_materials(
            inventory, gross_production
        )

        assert result.raw_materials_consumed == 300.0
        assert result.raw_materials_shortage == 0.0
        assert new_inv.raw_materials.used_in_production == 300.0
        assert new_inv.raw_materials.ending == 200.0

    def test_consume_raw_materials_insufficient(self):
        """Test consuming raw materials when insufficient available."""
        manager = InventoryManager()

        # Start with only 200 RM
        inventory = Inventory(
            raw_materials=RawMaterialsInventory(beginning=200.0)
        )

        gross_production = {"X'": 100.0, "Y'": 200.0}  # Needs 300 RM

        new_inv, result = manager.consume_raw_materials(
            inventory, gross_production
        )

        assert result.raw_materials_consumed == 200.0  # Only what's available
        assert result.raw_materials_shortage == 100.0
        assert new_inv.raw_materials.used_in_production == 200.0
        assert new_inv.raw_materials.ending == 0.0


class TestPartsInventory:
    """Tests for parts inventory management."""

    def test_add_parts_production(self):
        """Test adding parts production to inventory."""
        manager = InventoryManager()
        inventory = Inventory()

        net_production = {"X'": 80.0, "Y'": 120.0, "Z'": 100.0}
        new_inv = manager.add_parts_production(inventory, net_production)

        assert new_inv.parts.x_prime.production == 80.0
        assert new_inv.parts.y_prime.production == 120.0
        assert new_inv.parts.z_prime.production == 100.0

    def test_parts_production_accumulates(self):
        """Test that multiple production additions accumulate."""
        manager = InventoryManager()
        inventory = Inventory()

        # First production run
        inventory = manager.add_parts_production(
            inventory, {"X'": 50.0, "Y'": 60.0, "Z'": 40.0}
        )

        # Second production run
        inventory = manager.add_parts_production(
            inventory, {"X'": 30.0, "Y'": 40.0, "Z'": 20.0}
        )

        assert inventory.parts.x_prime.production == 80.0
        assert inventory.parts.y_prime.production == 100.0
        assert inventory.parts.z_prime.production == 60.0


class TestPartsConsumption:
    """Tests for parts consumption during assembly."""

    def test_calculate_parts_consumption_standard_bom(self):
        """Test parts consumption with default 1:1 BOM."""
        manager = InventoryManager()

        gross_assembly = {"X": 100.0, "Y": 200.0, "Z": 150.0}
        consumed = manager.calculate_parts_consumption(gross_assembly)

        # With default 1:1 BOM (X needs X', Y needs Y', Z needs Z')
        assert consumed == {"X'": 100.0, "Y'": 200.0, "Z'": 150.0}

    def test_consume_parts_sufficient(self):
        """Test consuming parts when sufficient available."""
        manager = InventoryManager()

        # Start with parts in inventory
        inventory = Inventory(
            parts=AllPartsInventory(
                x_prime=PartsInventory(part_type="X'", beginning=200.0),
                y_prime=PartsInventory(part_type="Y'", beginning=300.0),
                z_prime=PartsInventory(part_type="Z'", beginning=250.0),
            )
        )

        gross_assembly = {"X": 100.0, "Y": 150.0, "Z": 100.0}

        new_inv, result = manager.consume_parts(inventory, gross_assembly)

        assert result.parts_consumed == {"X'": 100.0, "Y'": 150.0, "Z'": 100.0}
        assert result.parts_shortage == {"X'": 0.0, "Y'": 0.0, "Z'": 0.0}
        assert new_inv.parts.x_prime.used_in_assembly == 100.0
        assert new_inv.parts.y_prime.used_in_assembly == 150.0
        assert new_inv.parts.z_prime.used_in_assembly == 100.0

    def test_consume_parts_insufficient(self):
        """Test consuming parts when insufficient available."""
        manager = InventoryManager()

        # Start with limited parts
        inventory = Inventory(
            parts=AllPartsInventory(
                x_prime=PartsInventory(part_type="X'", beginning=50.0),
                y_prime=PartsInventory(part_type="Y'", beginning=300.0),
                z_prime=PartsInventory(part_type="Z'", beginning=250.0),
            )
        )

        gross_assembly = {"X": 100.0, "Y": 150.0, "Z": 100.0}

        new_inv, result = manager.consume_parts(inventory, gross_assembly)

        # X' is short, others are sufficient
        assert result.parts_consumed == {"X'": 50.0, "Y'": 150.0, "Z'": 100.0}
        assert result.parts_shortage == {"X'": 50.0, "Y'": 0.0, "Z'": 0.0}


class TestProductsInventory:
    """Tests for products inventory management."""

    def test_add_products_production(self):
        """Test adding assembled products to inventory."""
        manager = InventoryManager()
        inventory = Inventory()

        net_production = {"X": 80.0, "Y": 120.0, "Z": 100.0}
        new_inv = manager.add_products_production(inventory, net_production)

        assert new_inv.products.x.production == 80.0
        assert new_inv.products.y.production == 120.0
        assert new_inv.products.z.production == 100.0

    def test_products_production_accumulates(self):
        """Test that multiple assembly runs accumulate."""
        manager = InventoryManager()
        inventory = Inventory()

        # First assembly run
        inventory = manager.add_products_production(
            inventory, {"X": 50.0, "Y": 60.0, "Z": 40.0}
        )

        # Second assembly run
        inventory = manager.add_products_production(
            inventory, {"X": 30.0, "Y": 40.0, "Z": 20.0}
        )

        assert inventory.products.x.production == 80.0
        assert inventory.products.y.production == 100.0
        assert inventory.products.z.production == 60.0


class TestDemandFulfillment:
    """Tests for demand fulfillment."""

    def test_fulfill_demand_sufficient(self):
        """Test fulfilling demand when sufficient inventory."""
        manager = InventoryManager()

        inventory = Inventory(
            products=AllProductsInventory(
                x=ProductsInventory(product_type="X", beginning=200.0),
                y=ProductsInventory(product_type="Y", beginning=300.0),
                z=ProductsInventory(product_type="Z", beginning=250.0),
            )
        )

        demand = {"X": 100.0, "Y": 150.0, "Z": 100.0}

        new_inv, result = manager.fulfill_demand(inventory, demand)

        assert result.units_shipped == {"X": 100.0, "Y": 150.0, "Z": 100.0}
        assert result.units_short == {"X": 0.0, "Y": 0.0, "Z": 0.0}
        assert result.carryover == {"X": 0.0, "Y": 0.0, "Z": 0.0}
        assert new_inv.products.x.demand_fulfilled == 100.0
        assert new_inv.products.x.ending == 100.0

    def test_fulfill_demand_insufficient(self):
        """Test fulfilling demand when insufficient inventory."""
        manager = InventoryManager()

        inventory = Inventory(
            products=AllProductsInventory(
                x=ProductsInventory(product_type="X", beginning=50.0),
                y=ProductsInventory(product_type="Y", beginning=300.0),
                z=ProductsInventory(product_type="Z", beginning=250.0),
            )
        )

        demand = {"X": 100.0, "Y": 150.0, "Z": 100.0}

        new_inv, result = manager.fulfill_demand(inventory, demand)

        # X is short
        assert result.units_shipped == {"X": 50.0, "Y": 150.0, "Z": 100.0}
        assert result.units_short == {"X": 50.0, "Y": 0.0, "Z": 0.0}
        assert result.carryover == {"X": 50.0, "Y": 0.0, "Z": 0.0}
        assert new_inv.products.x.ending == 0.0

    def test_fulfill_demand_with_production(self):
        """Test fulfilling demand including current week's production."""
        manager = InventoryManager()

        inventory = Inventory(
            products=AllProductsInventory(
                x=ProductsInventory(product_type="X", beginning=50.0, production=100.0),
                y=ProductsInventory(product_type="Y", beginning=100.0, production=50.0),
                z=ProductsInventory(product_type="Z", beginning=75.0, production=25.0),
            )
        )

        demand = {"X": 120.0, "Y": 100.0, "Z": 80.0}

        new_inv, result = manager.fulfill_demand(inventory, demand)

        # X: 50 + 100 = 150 available, need 120 -> ship 120, end 30
        # Y: 100 + 50 = 150 available, need 100 -> ship 100, end 50
        # Z: 75 + 25 = 100 available, need 80 -> ship 80, end 20
        assert result.units_shipped == {"X": 120.0, "Y": 100.0, "Z": 80.0}
        assert result.units_short == {"X": 0.0, "Y": 0.0, "Z": 0.0}
        assert new_inv.products.x.ending == 30.0
        assert new_inv.products.y.ending == 50.0
        assert new_inv.products.z.ending == 20.0


class TestAvailableInventoryQueries:
    """Tests for available inventory queries."""

    def test_get_available_raw_materials(self):
        """Test getting available raw materials."""
        manager = InventoryManager()

        inventory = Inventory(
            raw_materials=RawMaterialsInventory(
                beginning=100.0,
                orders_received=50.0,
                used_in_production=30.0,
            )
        )

        available = manager.get_available_raw_materials(inventory)
        assert available == 120.0  # 100 + 50 - 30

    def test_get_available_parts(self):
        """Test getting available parts."""
        manager = InventoryManager()

        inventory = Inventory(
            parts=AllPartsInventory(
                x_prime=PartsInventory(
                    part_type="X'",
                    beginning=100.0,
                    orders_received=20.0,
                    production=50.0,
                    used_in_assembly=30.0,
                ),
                y_prime=PartsInventory(part_type="Y'", beginning=200.0),
                z_prime=PartsInventory(part_type="Z'", beginning=150.0),
            )
        )

        available = manager.get_available_parts(inventory)

        assert available["X'"] == 140.0  # 100 + 20 + 50 - 30
        assert available["Y'"] == 200.0
        assert available["Z'"] == 150.0

    def test_get_available_products(self):
        """Test getting available products."""
        manager = InventoryManager()

        inventory = Inventory(
            products=AllProductsInventory(
                x=ProductsInventory(
                    product_type="X",
                    beginning=100.0,
                    production=50.0,
                    demand_fulfilled=30.0,
                ),
                y=ProductsInventory(product_type="Y", beginning=200.0),
                z=ProductsInventory(product_type="Z", beginning=150.0),
            )
        )

        available = manager.get_available_products(inventory)

        assert available["X"] == 120.0  # 100 + 50 - 30
        assert available["Y"] == 200.0
        assert available["Z"] == 150.0

    def test_get_ending_inventory(self):
        """Test getting all ending inventory values."""
        manager = InventoryManager()

        inventory = Inventory(
            raw_materials=RawMaterialsInventory(
                beginning=100.0,
                orders_received=50.0,
                used_in_production=30.0,
            ),
            parts=AllPartsInventory(
                x_prime=PartsInventory(part_type="X'", beginning=100.0, production=50.0),
                y_prime=PartsInventory(part_type="Y'", beginning=200.0),
                z_prime=PartsInventory(part_type="Z'", beginning=150.0),
            ),
            products=AllProductsInventory(
                x=ProductsInventory(product_type="X", beginning=100.0, production=50.0),
                y=ProductsInventory(product_type="Y", beginning=200.0),
                z=ProductsInventory(product_type="Z", beginning=150.0),
            ),
        )

        ending = manager.get_ending_inventory(inventory)

        assert ending["raw_materials"] == 120.0
        assert ending["X'"] == 150.0
        assert ending["Y'"] == 200.0
        assert ending["Z'"] == 150.0
        assert ending["X"] == 150.0
        assert ending["Y"] == 200.0
        assert ending["Z"] == 150.0


class TestIntegration:
    """Integration tests for full inventory flow."""

    def test_full_week_inventory_flow(self):
        """Test a complete week's inventory operations."""
        manager = InventoryManager()

        # Initial state: some raw materials and pending orders
        inventory = Inventory(
            raw_materials=RawMaterialsInventory(beginning=1000.0),
            parts=AllPartsInventory(
                x_prime=PartsInventory(part_type="X'", beginning=100.0),
                y_prime=PartsInventory(part_type="Y'", beginning=150.0),
                z_prime=PartsInventory(part_type="Z'", beginning=200.0),
            ),
            products=AllProductsInventory(
                x=ProductsInventory(product_type="X", beginning=50.0),
                y=ProductsInventory(product_type="Y", beginning=75.0),
                z=ProductsInventory(product_type="Z", beginning=100.0),
            ),
        )

        # Set up orders to be received this week
        order_book = OrderBook()
        order_book, _ = order_book.place_order(
            OrderType.RAW_MATERIALS_EXPEDITED, 500.0, current_week=3
        )
        order_book, _ = order_book.place_order(
            OrderType.PARTS_X_PRIME, 50.0, current_week=3
        )

        # Week 4: Receive orders
        inventory, order_book, receipt = manager.receive_orders(
            inventory, order_book, current_week=4
        )

        assert receipt.raw_materials_received == 500.0
        assert receipt.parts_received["X'"] == 50.0

        # Simulate parts production (gross production)
        gross_parts = {"X'": 200.0, "Y'": 250.0, "Z'": 180.0}

        # Consume raw materials
        inventory, rm_result = manager.consume_raw_materials(inventory, gross_parts)

        # RM consumed: 200 + 250 + 180 = 630
        assert rm_result.raw_materials_consumed == 630.0
        assert rm_result.raw_materials_shortage == 0.0

        # Add net parts production (after 17.8% reject)
        reject_rate = 0.178
        net_parts = {k: v * (1 - reject_rate) for k, v in gross_parts.items()}
        inventory = manager.add_parts_production(inventory, net_parts)

        # Simulate assembly (gross production)
        gross_assembly = {"X": 80.0, "Y": 100.0, "Z": 120.0}

        # Consume parts
        inventory, parts_result = manager.consume_parts(inventory, gross_assembly)

        # Add net product production
        net_products = {k: v * (1 - reject_rate) for k, v in gross_assembly.items()}
        inventory = manager.add_products_production(inventory, net_products)

        # Fulfill demand (shipping week)
        demand = {"X": 100.0, "Y": 100.0, "Z": 100.0}
        inventory, fulfillment = manager.fulfill_demand(inventory, demand)

        # Verify final state
        ending = manager.get_ending_inventory(inventory)

        # Raw materials: 1000 + 500 - 630 = 870
        assert ending["raw_materials"] == 870.0

        # Check that we can advance the week
        new_week_inv = inventory.advance_week()
        assert new_week_inv.raw_materials.beginning == 870.0
