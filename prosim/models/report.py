"""
Report models for PROSIM simulation.

Represents the weekly reports generated via REPT files.
Structure based on week1.txt human-readable format:
- Cost Information (per-product and overhead)
- Order Information (pending orders)
- Production Information (per-machine)
- Inventory Information (raw materials, parts, products)
- Demand Information
- Performance Measures
"""

from pydantic import BaseModel, Field


class ProductCosts(BaseModel):
    """Costs breakdown for a single product type (X, Y, or Z).

    Nine cost categories as shown in week1.txt.
    """

    product_type: str = Field(description="Product type (X, Y, or Z)")
    labor: float = Field(default=0.0, ge=0)
    machine_setup: float = Field(default=0.0, ge=0)
    machine_repair: float = Field(default=0.0, ge=0)
    raw_materials: float = Field(default=0.0, ge=0)
    purchased_parts: float = Field(default=0.0, ge=0)
    equipment_usage: float = Field(default=0.0, ge=0)
    parts_carrying: float = Field(default=0.0, ge=0)
    products_carrying: float = Field(default=0.0, ge=0)
    demand_penalty: float = Field(default=0.0, ge=0)

    @property
    def subtotal(self) -> float:
        """Calculate subtotal of all per-product costs."""
        return (
            self.labor
            + self.machine_setup
            + self.machine_repair
            + self.raw_materials
            + self.purchased_parts
            + self.equipment_usage
            + self.parts_carrying
            + self.products_carrying
            + self.demand_penalty
        )


class OverheadCosts(BaseModel):
    """Overhead costs not attributed to specific products.

    Eight overhead categories as shown in week1.txt.
    """

    quality_planning: float = Field(default=0.0, ge=0)
    plant_maintenance: float = Field(default=0.0, ge=0)
    training_cost: float = Field(default=0.0, ge=0)
    hiring_cost: float = Field(default=0.0, ge=0)
    layoff_firing_cost: float = Field(default=0.0, ge=0)
    raw_materials_carrying: float = Field(default=0.0, ge=0)
    ordering_cost: float = Field(default=0.0, ge=0)
    fixed_expense: float = Field(default=0.0, ge=0)

    @property
    def subtotal(self) -> float:
        """Calculate subtotal of all overhead costs."""
        return (
            self.quality_planning
            + self.plant_maintenance
            + self.training_cost
            + self.hiring_cost
            + self.layoff_firing_cost
            + self.raw_materials_carrying
            + self.ordering_cost
            + self.fixed_expense
        )


class CostReport(BaseModel):
    """Complete cost report for a week.

    Includes per-product costs and overhead, both weekly and cumulative.
    """

    x_costs: ProductCosts = Field(default_factory=lambda: ProductCosts(product_type="X"))
    y_costs: ProductCosts = Field(default_factory=lambda: ProductCosts(product_type="Y"))
    z_costs: ProductCosts = Field(default_factory=lambda: ProductCosts(product_type="Z"))
    overhead: OverheadCosts = Field(default_factory=OverheadCosts)

    @property
    def product_subtotal(self) -> float:
        """Total of all per-product costs."""
        return self.x_costs.subtotal + self.y_costs.subtotal + self.z_costs.subtotal

    @property
    def total_costs(self) -> float:
        """Total of all costs (products + overhead)."""
        return self.product_subtotal + self.overhead.subtotal

    def get_product_costs(self, product_type: str) -> ProductCosts:
        """Get costs for a specific product type."""
        mapping = {
            "X": self.x_costs,
            "Y": self.y_costs,
            "Z": self.z_costs,
        }
        if product_type not in mapping:
            raise ValueError(f"Unknown product type: {product_type}")
        return mapping[product_type]


class MachineProduction(BaseModel):
    """Production data for a single machine.

    From Production Information section of report.
    """

    machine_id: int = Field(ge=1, description="Machine identifier")
    operator_id: int = Field(ge=1, description="Assigned operator")
    part_type: str = Field(description="Part/product type produced")
    scheduled_hours: float = Field(default=0.0, ge=0)
    productive_hours: float = Field(default=0.0, ge=0)
    production: float = Field(default=0.0, ge=0, description="Units produced (gross)")
    rejects: float = Field(default=0.0, ge=0, description="Units rejected")

    @property
    def net_production(self) -> float:
        """Production minus rejects."""
        return self.production - self.rejects

    @property
    def efficiency(self) -> float:
        """Productive hours / scheduled hours."""
        if self.scheduled_hours == 0:
            return 0.0
        return self.productive_hours / self.scheduled_hours

    @property
    def reject_rate(self) -> float:
        """Reject rate (rejects / production)."""
        if self.production == 0:
            return 0.0
        return self.rejects / self.production


class ProductionReport(BaseModel):
    """Production data for all machines."""

    parts_department: list[MachineProduction] = Field(default_factory=list)
    assembly_department: list[MachineProduction] = Field(default_factory=list)

    @property
    def all_machines(self) -> list[MachineProduction]:
        """Get all machine production records."""
        return self.parts_department + self.assembly_department

    def total_production_by_type(self, part_type: str) -> float:
        """Calculate total net production for a part type."""
        return sum(
            mp.net_production
            for mp in self.all_machines
            if mp.part_type == part_type
        )

    def total_rejects_by_type(self, part_type: str) -> float:
        """Calculate total rejects for a part type."""
        return sum(
            mp.rejects for mp in self.all_machines if mp.part_type == part_type
        )


class RawMaterialsReport(BaseModel):
    """Raw materials inventory report."""

    beginning_inventory: float = Field(default=0.0, ge=0)
    orders_received: float = Field(default=0.0, ge=0)
    used_in_production: float = Field(default=0.0, ge=0)
    ending_inventory: float = Field(default=0.0, ge=0)


class PartsReport(BaseModel):
    """Parts inventory report for one part type."""

    part_type: str = Field(description="Part type (X', Y', or Z')")
    beginning_inventory: float = Field(default=0.0, ge=0)
    orders_received: float = Field(default=0.0, ge=0)
    used_in_production: float = Field(default=0.0, ge=0)
    production_this_week: float = Field(default=0.0, ge=0)
    ending_inventory: float = Field(default=0.0, ge=0)


class ProductsReport(BaseModel):
    """Products inventory report for one product type."""

    product_type: str = Field(description="Product type (X, Y, or Z)")
    beginning_inventory: float = Field(default=0.0, ge=0)
    production_this_week: float = Field(default=0.0, ge=0)
    demand_this_week: float = Field(default=0.0, ge=0)
    ending_inventory: float = Field(default=0.0, ge=0)


class InventoryReport(BaseModel):
    """Complete inventory report."""

    raw_materials: RawMaterialsReport = Field(default_factory=RawMaterialsReport)
    parts_x: PartsReport = Field(default_factory=lambda: PartsReport(part_type="X'"))
    parts_y: PartsReport = Field(default_factory=lambda: PartsReport(part_type="Y'"))
    parts_z: PartsReport = Field(default_factory=lambda: PartsReport(part_type="Z'"))
    products_x: ProductsReport = Field(
        default_factory=lambda: ProductsReport(product_type="X")
    )
    products_y: ProductsReport = Field(
        default_factory=lambda: ProductsReport(product_type="Y")
    )
    products_z: ProductsReport = Field(
        default_factory=lambda: ProductsReport(product_type="Z")
    )

    def get_parts(self, part_type: str) -> PartsReport:
        """Get parts report by type."""
        mapping = {"X'": self.parts_x, "Y'": self.parts_y, "Z'": self.parts_z}
        return mapping.get(part_type, self.parts_x)

    def get_products(self, product_type: str) -> ProductsReport:
        """Get products report by type."""
        mapping = {"X": self.products_x, "Y": self.products_y, "Z": self.products_z}
        return mapping.get(product_type, self.products_x)


class PendingOrderReport(BaseModel):
    """Report of a single pending order."""

    order_type: str = Field(description="Type of order")
    week_due: int = Field(ge=1, description="Week when order arrives")
    amount: float = Field(ge=0, description="Quantity ordered")


class DemandReport(BaseModel):
    """Demand information for one product."""

    product_type: str = Field(description="Product type (X, Y, or Z)")
    estimated_demand: float = Field(default=0.0, ge=0)
    carryover: float = Field(default=0.0, ge=0)
    total_demand: float = Field(default=0.0, ge=0)


class PerformanceMetrics(BaseModel):
    """Performance measures from the report."""

    total_standard_costs: float = Field(default=0.0, ge=0)
    total_actual_costs: float = Field(default=0.0, ge=0)
    percent_efficiency: float = Field(default=0.0)
    variance_per_unit: float = Field(default=0.0)
    on_time_delivery: float | None = Field(
        default=None, description="On-time delivery percentage (NA if no shipments)"
    )

    @property
    def efficiency_ratio(self) -> float:
        """Standard costs / actual costs."""
        if self.total_actual_costs == 0:
            return 0.0
        return self.total_standard_costs / self.total_actual_costs


class WeeklyReport(BaseModel):
    """Complete weekly report (REPT file representation).

    Combines all report sections for a single week.
    """

    week: int = Field(ge=1, description="Simulation week number")
    company_id: int = Field(ge=1, description="Company identifier")

    # Cost information
    weekly_costs: CostReport = Field(default_factory=CostReport)
    cumulative_costs: CostReport = Field(default_factory=CostReport)

    # Production information
    production: ProductionReport = Field(default_factory=ProductionReport)

    # Inventory information
    inventory: InventoryReport = Field(default_factory=InventoryReport)

    # Order information
    pending_orders: list[PendingOrderReport] = Field(default_factory=list)

    # Demand information
    demand_x: DemandReport = Field(default_factory=lambda: DemandReport(product_type="X"))
    demand_y: DemandReport = Field(default_factory=lambda: DemandReport(product_type="Y"))
    demand_z: DemandReport = Field(default_factory=lambda: DemandReport(product_type="Z"))

    # Performance metrics
    weekly_performance: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    cumulative_performance: PerformanceMetrics = Field(default_factory=PerformanceMetrics)

    def get_demand(self, product_type: str) -> DemandReport:
        """Get demand report by product type."""
        mapping = {"X": self.demand_x, "Y": self.demand_y, "Z": self.demand_z}
        return mapping.get(product_type, self.demand_x)
