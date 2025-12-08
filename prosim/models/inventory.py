"""
Inventory models for PROSIM simulation.

Tracks three types of inventory:
- Raw Materials: Single pool, converted to parts in Parts Department
- Parts: X', Y', Z' - manufactured or purchased, consumed in Assembly
- Products: X, Y, Z - finished goods for customer demand
"""

from pydantic import BaseModel, Field


class RawMaterialsInventory(BaseModel):
    """Tracks raw materials inventory (single pool).

    Raw materials are ordered (regular or expedited) and consumed
    during parts production in the Parts Department.
    """

    beginning: float = Field(default=0.0, ge=0, description="Beginning inventory for the week")
    orders_received: float = Field(default=0.0, ge=0, description="Orders received this week")
    used_in_production: float = Field(default=0.0, ge=0, description="Consumed in parts production")

    @property
    def ending(self) -> float:
        """Calculate ending inventory."""
        return max(0.0, self.beginning + self.orders_received - self.used_in_production)

    def advance_week(self) -> "RawMaterialsInventory":
        """Create next week's inventory with ending as new beginning."""
        return RawMaterialsInventory(
            beginning=self.ending,
            orders_received=0.0,
            used_in_production=0.0,
        )


class PartsInventory(BaseModel):
    """Tracks inventory for a single part type (X', Y', or Z').

    Parts can be manufactured in the Parts Department or purchased
    from external suppliers. They are consumed during assembly.
    """

    part_type: str = Field(description="Part type identifier (X', Y', or Z')")
    beginning: float = Field(default=0.0, ge=0, description="Beginning inventory for the week")
    orders_received: float = Field(default=0.0, ge=0, description="Purchased parts received")
    production: float = Field(default=0.0, ge=0, description="Parts produced this week (net of rejects)")
    used_in_assembly: float = Field(default=0.0, ge=0, description="Consumed in product assembly")

    @property
    def ending(self) -> float:
        """Calculate ending inventory."""
        return max(
            0.0,
            self.beginning + self.orders_received + self.production - self.used_in_assembly
        )

    def advance_week(self) -> "PartsInventory":
        """Create next week's inventory with ending as new beginning."""
        return PartsInventory(
            part_type=self.part_type,
            beginning=self.ending,
            orders_received=0.0,
            production=0.0,
            used_in_assembly=0.0,
        )


class ProductsInventory(BaseModel):
    """Tracks inventory for a single product type (X, Y, or Z).

    Products are manufactured in the Assembly Department and
    shipped to meet customer demand.
    """

    product_type: str = Field(description="Product type identifier (X, Y, or Z)")
    beginning: float = Field(default=0.0, ge=0, description="Beginning inventory for the week")
    production: float = Field(default=0.0, ge=0, description="Products assembled this week (net of rejects)")
    demand_fulfilled: float = Field(default=0.0, ge=0, description="Units shipped to meet demand")

    @property
    def ending(self) -> float:
        """Calculate ending inventory."""
        return max(0.0, self.beginning + self.production - self.demand_fulfilled)

    def advance_week(self) -> "ProductsInventory":
        """Create next week's inventory with ending as new beginning."""
        return ProductsInventory(
            product_type=self.product_type,
            beginning=self.ending,
            production=0.0,
            demand_fulfilled=0.0,
        )


class AllPartsInventory(BaseModel):
    """Container for all three part types."""

    x_prime: PartsInventory = Field(default_factory=lambda: PartsInventory(part_type="X'"))
    y_prime: PartsInventory = Field(default_factory=lambda: PartsInventory(part_type="Y'"))
    z_prime: PartsInventory = Field(default_factory=lambda: PartsInventory(part_type="Z'"))

    def get(self, part_type: str) -> PartsInventory:
        """Get inventory by part type."""
        mapping = {
            "X'": self.x_prime,
            "Y'": self.y_prime,
            "Z'": self.z_prime,
            # Also accept without prime
            "X": self.x_prime,
            "Y": self.y_prime,
            "Z": self.z_prime,
            # Numeric mapping (1=X', 2=Y', 3=Z')
            "1": self.x_prime,
            "2": self.y_prime,
            "3": self.z_prime,
        }
        if part_type not in mapping:
            raise ValueError(f"Unknown part type: {part_type}")
        return mapping[part_type]

    def advance_week(self) -> "AllPartsInventory":
        """Create next week's inventory for all parts."""
        return AllPartsInventory(
            x_prime=self.x_prime.advance_week(),
            y_prime=self.y_prime.advance_week(),
            z_prime=self.z_prime.advance_week(),
        )


class AllProductsInventory(BaseModel):
    """Container for all three product types."""

    x: ProductsInventory = Field(default_factory=lambda: ProductsInventory(product_type="X"))
    y: ProductsInventory = Field(default_factory=lambda: ProductsInventory(product_type="Y"))
    z: ProductsInventory = Field(default_factory=lambda: ProductsInventory(product_type="Z"))

    def get(self, product_type: str) -> ProductsInventory:
        """Get inventory by product type."""
        mapping = {
            "X": self.x,
            "Y": self.y,
            "Z": self.z,
            # Numeric mapping (1=X, 2=Y, 3=Z)
            "1": self.x,
            "2": self.y,
            "3": self.z,
        }
        if product_type not in mapping:
            raise ValueError(f"Unknown product type: {product_type}")
        return mapping[product_type]

    def advance_week(self) -> "AllProductsInventory":
        """Create next week's inventory for all products."""
        return AllProductsInventory(
            x=self.x.advance_week(),
            y=self.y.advance_week(),
            z=self.z.advance_week(),
        )


class Inventory(BaseModel):
    """Complete inventory state for a company.

    Combines raw materials, parts, and products tracking.
    """

    raw_materials: RawMaterialsInventory = Field(default_factory=RawMaterialsInventory)
    parts: AllPartsInventory = Field(default_factory=AllPartsInventory)
    products: AllProductsInventory = Field(default_factory=AllProductsInventory)

    def advance_week(self) -> "Inventory":
        """Create next week's inventory state."""
        return Inventory(
            raw_materials=self.raw_materials.advance_week(),
            parts=self.parts.advance_week(),
            products=self.products.advance_week(),
        )
