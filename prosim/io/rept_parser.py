"""
REPT file parser for PROSIM simulation.

Parses report output files in the original PROSIM format.

File format (space-separated values, reconstructed from original files):
    Line 1: [Week] [Company] [Parts_machines] [Assembly_machines] [?]
    Lines 2-11: Cost data (weekly X, Y, Z, Total; cumulative X, Y, Z, Total)
        - Labor, Setup, Repair, RM, Parts, Equip, Parts Carrying, Products Carrying, Demand Penalty, Subtotal
    Line 12: [Weekly Total] [Cumulative Total]
    Lines 13-14: Overhead costs (weekly 8 values; cumulative 8 values)
    Lines 15-23: Production per machine (9 lines)
    Line 24: Raw materials (Beginning, Received, Used, Ending)
    Lines 25-31: Pending orders (WeekDue, Amount pairs)
    Lines 32-37: Parts and products inventory
    Lines 38-40: Demand estimates
    Lines 41-42: Performance metrics (weekly, cumulative)
"""

from pathlib import Path
from typing import TextIO

from prosim.models.report import (
    CostReport,
    DemandReport,
    InventoryReport,
    MachineProduction,
    OverheadCosts,
    PartsReport,
    PendingOrderReport,
    PerformanceMetrics,
    ProductCosts,
    ProductionReport,
    ProductsReport,
    RawMaterialsReport,
    WeeklyReport,
)


class REPTParseError(Exception):
    """Error parsing a REPT file."""

    def __init__(self, message: str, line_number: int | None = None) -> None:
        self.line_number = line_number
        if line_number is not None:
            message = f"Line {line_number}: {message}"
        super().__init__(message)


def _parse_floats(line: str) -> list[float]:
    """Parse a line of space-separated float values."""
    return [float(x.strip().rstrip(".")) for x in line.split() if x.strip()]


def _parse_ints(line: str) -> list[int]:
    """Parse a line of space-separated int values."""
    return [int(float(x.strip().rstrip("."))) for x in line.split() if x.strip()]


def parse_rept(source: str | Path | TextIO) -> WeeklyReport:
    """Parse a REPT file into a WeeklyReport object.

    Args:
        source: File path, path object, or file-like object containing REPT data

    Returns:
        Parsed WeeklyReport object

    Raises:
        REPTParseError: If the file format is invalid
        FileNotFoundError: If source is a path and file doesn't exist

    Example:
        >>> report = parse_rept("archive/data/REPT12.DAT")
        >>> report.week
        12
        >>> report.weekly_costs.total_costs
        54148.0
    """
    # Get lines from source
    if isinstance(source, (str, Path)):
        with open(source, encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = source.read().splitlines()

    # Strip carriage returns (Windows line endings)
    lines = [line.replace("\r", "").strip() for line in lines]

    # Filter out empty lines
    lines = [line for line in lines if line]

    if len(lines) < 42:
        raise REPTParseError(
            f"REPT file must have at least 42 lines, got {len(lines)}"
        )

    # Line 1: Header [Week] [Company] [Parts_machines] [Assembly_machines] [?]
    header = _parse_ints(lines[0])
    if len(header) < 2:
        raise REPTParseError("Invalid header format", 1)
    week = header[0]
    company_id = header[1]

    # Lines 2-11: Cost data (10 cost categories)
    # Each line has 8 values: Weekly(X, Y, Z, Total), Cumulative(X, Y, Z, Total)
    cost_lines = [_parse_floats(lines[i]) for i in range(1, 11)]

    # Create product costs from cost lines
    weekly_x = ProductCosts(
        product_type="X",
        labor=cost_lines[0][0],
        machine_setup=cost_lines[1][0],
        machine_repair=cost_lines[2][0],
        raw_materials=cost_lines[3][0],
        purchased_parts=cost_lines[4][0],
        equipment_usage=cost_lines[5][0],
        parts_carrying=cost_lines[6][0],
        products_carrying=cost_lines[7][0],
        demand_penalty=cost_lines[8][0],
    )
    weekly_y = ProductCosts(
        product_type="Y",
        labor=cost_lines[0][1],
        machine_setup=cost_lines[1][1],
        machine_repair=cost_lines[2][1],
        raw_materials=cost_lines[3][1],
        purchased_parts=cost_lines[4][1],
        equipment_usage=cost_lines[5][1],
        parts_carrying=cost_lines[6][1],
        products_carrying=cost_lines[7][1],
        demand_penalty=cost_lines[8][1],
    )
    weekly_z = ProductCosts(
        product_type="Z",
        labor=cost_lines[0][2],
        machine_setup=cost_lines[1][2],
        machine_repair=cost_lines[2][2],
        raw_materials=cost_lines[3][2],
        purchased_parts=cost_lines[4][2],
        equipment_usage=cost_lines[5][2],
        parts_carrying=cost_lines[6][2],
        products_carrying=cost_lines[7][2],
        demand_penalty=cost_lines[8][2],
    )

    cumulative_x = ProductCosts(
        product_type="X",
        labor=cost_lines[0][4],
        machine_setup=cost_lines[1][4],
        machine_repair=cost_lines[2][4],
        raw_materials=cost_lines[3][4],
        purchased_parts=cost_lines[4][4],
        equipment_usage=cost_lines[5][4],
        parts_carrying=cost_lines[6][4],
        products_carrying=cost_lines[7][4],
        demand_penalty=cost_lines[8][4],
    )
    cumulative_y = ProductCosts(
        product_type="Y",
        labor=cost_lines[0][5],
        machine_setup=cost_lines[1][5],
        machine_repair=cost_lines[2][5],
        raw_materials=cost_lines[3][5],
        purchased_parts=cost_lines[4][5],
        equipment_usage=cost_lines[5][5],
        parts_carrying=cost_lines[6][5],
        products_carrying=cost_lines[7][5],
        demand_penalty=cost_lines[8][5],
    )
    cumulative_z = ProductCosts(
        product_type="Z",
        labor=cost_lines[0][6],
        machine_setup=cost_lines[1][6],
        machine_repair=cost_lines[2][6],
        raw_materials=cost_lines[3][6],
        purchased_parts=cost_lines[4][6],
        equipment_usage=cost_lines[5][6],
        parts_carrying=cost_lines[6][6],
        products_carrying=cost_lines[7][6],
        demand_penalty=cost_lines[8][6],
    )

    # Line 12: Total costs [Weekly, Cumulative]
    totals = _parse_floats(lines[11])

    # Lines 13-14: Overhead costs
    # 8 values each: Quality, Maint, Training, Hiring, Layoff, RM Carry, Order, Fixed
    weekly_overhead_values = _parse_floats(lines[12])
    cumulative_overhead_values = _parse_floats(lines[13])

    weekly_overhead = OverheadCosts(
        quality_planning=weekly_overhead_values[0],
        plant_maintenance=weekly_overhead_values[1],
        training_cost=weekly_overhead_values[2],
        hiring_cost=weekly_overhead_values[3],
        layoff_firing_cost=weekly_overhead_values[4],
        raw_materials_carrying=weekly_overhead_values[5],
        ordering_cost=weekly_overhead_values[6],
        fixed_expense=weekly_overhead_values[7],
    )
    cumulative_overhead = OverheadCosts(
        quality_planning=cumulative_overhead_values[0],
        plant_maintenance=cumulative_overhead_values[1],
        training_cost=cumulative_overhead_values[2],
        hiring_cost=cumulative_overhead_values[3],
        layoff_firing_cost=cumulative_overhead_values[4],
        raw_materials_carrying=cumulative_overhead_values[5],
        ordering_cost=cumulative_overhead_values[6],
        fixed_expense=cumulative_overhead_values[7],
    )

    weekly_costs = CostReport(
        x_costs=weekly_x,
        y_costs=weekly_y,
        z_costs=weekly_z,
        overhead=weekly_overhead,
    )
    cumulative_costs = CostReport(
        x_costs=cumulative_x,
        y_costs=cumulative_y,
        z_costs=cumulative_z,
        overhead=cumulative_overhead,
    )

    # Lines 15-23: Production data (9 machines)
    # Format: [MachineID] [PartType] [SchedHours] [ProdHours] [Production] [Rejects]
    parts_production: list[MachineProduction] = []
    assembly_production: list[MachineProduction] = []

    for i in range(14, 23):
        values = _parse_floats(lines[i])
        if len(values) < 6 or values[0] == 0:
            # Skip empty/placeholder lines
            continue

        machine_id = int(values[0])
        part_type_code = int(values[1])
        part_types = {1: "X", 2: "Y", 3: "Z"}
        part_type = part_types.get(part_type_code, "X")

        mp = MachineProduction(
            machine_id=machine_id,
            operator_id=machine_id,  # Assuming operator_id == machine_id
            part_type=part_type,
            scheduled_hours=values[2],
            productive_hours=values[3],
            production=values[4],
            rejects=values[5],
        )

        # First 4 are parts department, next 5 are assembly
        if len(parts_production) < 4:
            # Add prime marker for parts
            mp = mp.model_copy(update={"part_type": part_type + "'"})
            parts_production.append(mp)
        else:
            assembly_production.append(mp)

    production = ProductionReport(
        parts_department=parts_production,
        assembly_department=assembly_production,
    )

    # Line 24: Raw materials [Beginning, Received, Used, Ending]
    rm_values = _parse_floats(lines[23])
    raw_materials = RawMaterialsReport(
        beginning_inventory=rm_values[0],
        orders_received=rm_values[1],
        used_in_production=rm_values[2],
        ending_inventory=rm_values[3],
    )

    # Lines 25-31: Pending orders (7 order slots)
    # Format: [WeekDue] [Amount] pairs (0 if empty)
    pending_orders: list[PendingOrderReport] = []
    order_types = [
        "Raw Materials (Reg)",
        "Raw Materials (Reg)",
        "Raw Materials (Reg)",
        "Raw Materials (Exp)",
        "Finished Part X'",
        "Finished Part Y'",
        "Finished Part Z'",
    ]

    for i, order_type in enumerate(order_types):
        values = _parse_floats(lines[24 + i])
        if len(values) >= 2 and values[0] > 0:
            pending_orders.append(
                PendingOrderReport(
                    order_type=order_type,
                    week_due=int(values[0]),
                    amount=values[1],
                )
            )

    # Lines 32-37: Parts and products inventory
    # Parts X': Beginning, Received, Used, Produced, Ending
    parts_x_values = _parse_floats(lines[31])
    products_x_values = _parse_floats(lines[32])
    parts_y_values = _parse_floats(lines[33])
    products_y_values = _parse_floats(lines[34])
    parts_z_values = _parse_floats(lines[35])
    products_z_values = _parse_floats(lines[36])

    parts_x = PartsReport(
        part_type="X'",
        beginning_inventory=parts_x_values[0],
        orders_received=parts_x_values[1],
        used_in_production=parts_x_values[2],
        production_this_week=parts_x_values[3],
        ending_inventory=parts_x_values[4],
    )
    products_x = ProductsReport(
        product_type="X",
        beginning_inventory=products_x_values[0],
        production_this_week=products_x_values[1],
        demand_this_week=products_x_values[2],
        ending_inventory=products_x_values[3],
    )
    parts_y = PartsReport(
        part_type="Y'",
        beginning_inventory=parts_y_values[0],
        orders_received=parts_y_values[1],
        used_in_production=parts_y_values[2],
        production_this_week=parts_y_values[3],
        ending_inventory=parts_y_values[4],
    )
    products_y = ProductsReport(
        product_type="Y",
        beginning_inventory=products_y_values[0],
        production_this_week=products_y_values[1],
        demand_this_week=products_y_values[2],
        ending_inventory=products_y_values[3],
    )
    parts_z = PartsReport(
        part_type="Z'",
        beginning_inventory=parts_z_values[0],
        orders_received=parts_z_values[1],
        used_in_production=parts_z_values[2],
        production_this_week=parts_z_values[3],
        ending_inventory=parts_z_values[4],
    )
    products_z = ProductsReport(
        product_type="Z",
        beginning_inventory=products_z_values[0],
        production_this_week=products_z_values[1],
        demand_this_week=products_z_values[2],
        ending_inventory=products_z_values[3],
    )

    inventory = InventoryReport(
        raw_materials=raw_materials,
        parts_x=parts_x,
        parts_y=parts_y,
        parts_z=parts_z,
        products_x=products_x,
        products_y=products_y,
        products_z=products_z,
    )

    # Lines 38-40: Demand estimates (X, Y, Z)
    demand_x_values = _parse_floats(lines[37])
    demand_y_values = _parse_floats(lines[38])
    demand_z_values = _parse_floats(lines[39])

    demand_x = DemandReport(
        product_type="X",
        estimated_demand=demand_x_values[0],
        carryover=demand_x_values[1],
        total_demand=demand_x_values[2],
    )
    demand_y = DemandReport(
        product_type="Y",
        estimated_demand=demand_y_values[0],
        carryover=demand_y_values[1],
        total_demand=demand_y_values[2],
    )
    demand_z = DemandReport(
        product_type="Z",
        estimated_demand=demand_z_values[0],
        carryover=demand_z_values[1],
        total_demand=demand_z_values[2],
    )

    # Lines 41-42: Performance metrics (weekly, cumulative)
    weekly_perf_values = _parse_floats(lines[40])
    cumulative_perf_values = _parse_floats(lines[41])

    weekly_performance = PerformanceMetrics(
        total_standard_costs=weekly_perf_values[0],
        total_actual_costs=totals[0],
        percent_efficiency=weekly_perf_values[1],
        variance_per_unit=weekly_perf_values[2],
        on_time_delivery=weekly_perf_values[3] if weekly_perf_values[3] > 0 else None,
    )
    cumulative_performance = PerformanceMetrics(
        total_standard_costs=cumulative_perf_values[0],
        total_actual_costs=totals[1],
        percent_efficiency=cumulative_perf_values[1],
        variance_per_unit=cumulative_perf_values[2],
        on_time_delivery=(
            cumulative_perf_values[3] if cumulative_perf_values[3] > 0 else None
        ),
    )

    return WeeklyReport(
        week=week,
        company_id=company_id,
        weekly_costs=weekly_costs,
        cumulative_costs=cumulative_costs,
        production=production,
        inventory=inventory,
        pending_orders=pending_orders,
        demand_x=demand_x,
        demand_y=demand_y,
        demand_z=demand_z,
        weekly_performance=weekly_performance,
        cumulative_performance=cumulative_performance,
    )


def write_rept(report: WeeklyReport, destination: str | Path | TextIO) -> None:
    """Write a WeeklyReport object to a REPT file.

    Args:
        report: WeeklyReport object to write
        destination: File path, path object, or file-like object to write to

    Example:
        >>> write_rept(report, "output/REPT01.DAT")
    """
    lines: list[str] = []

    # Line 1: Header
    lines.append(f"{report.week} {report.company_id} 4 4 5")

    # Lines 2-11: Cost data
    wc = report.weekly_costs
    cc = report.cumulative_costs

    def fmt_cost_line(
        w_x: float,
        w_y: float,
        w_z: float,
        w_t: float,
        c_x: float,
        c_y: float,
        c_z: float,
        c_t: float,
    ) -> str:
        return (
            f"{w_x:.1f} {w_y:.1f} {w_z:.1f} {w_t:.1f} "
            f"{c_x:.1f} {c_y:.1f} {c_z:.1f} {c_t:.1f}"
        )

    # Labor
    lines.append(
        fmt_cost_line(
            wc.x_costs.labor,
            wc.y_costs.labor,
            wc.z_costs.labor,
            wc.x_costs.labor + wc.y_costs.labor + wc.z_costs.labor,
            cc.x_costs.labor,
            cc.y_costs.labor,
            cc.z_costs.labor,
            cc.x_costs.labor + cc.y_costs.labor + cc.z_costs.labor,
        )
    )
    # Setup
    lines.append(
        fmt_cost_line(
            wc.x_costs.machine_setup,
            wc.y_costs.machine_setup,
            wc.z_costs.machine_setup,
            wc.x_costs.machine_setup + wc.y_costs.machine_setup + wc.z_costs.machine_setup,
            cc.x_costs.machine_setup,
            cc.y_costs.machine_setup,
            cc.z_costs.machine_setup,
            cc.x_costs.machine_setup + cc.y_costs.machine_setup + cc.z_costs.machine_setup,
        )
    )
    # Repair
    lines.append(
        fmt_cost_line(
            wc.x_costs.machine_repair,
            wc.y_costs.machine_repair,
            wc.z_costs.machine_repair,
            wc.x_costs.machine_repair + wc.y_costs.machine_repair + wc.z_costs.machine_repair,
            cc.x_costs.machine_repair,
            cc.y_costs.machine_repair,
            cc.z_costs.machine_repair,
            cc.x_costs.machine_repair + cc.y_costs.machine_repair + cc.z_costs.machine_repair,
        )
    )
    # Raw Materials
    lines.append(
        fmt_cost_line(
            wc.x_costs.raw_materials,
            wc.y_costs.raw_materials,
            wc.z_costs.raw_materials,
            wc.x_costs.raw_materials + wc.y_costs.raw_materials + wc.z_costs.raw_materials,
            cc.x_costs.raw_materials,
            cc.y_costs.raw_materials,
            cc.z_costs.raw_materials,
            cc.x_costs.raw_materials + cc.y_costs.raw_materials + cc.z_costs.raw_materials,
        )
    )
    # Purchased Parts
    lines.append(
        fmt_cost_line(
            wc.x_costs.purchased_parts,
            wc.y_costs.purchased_parts,
            wc.z_costs.purchased_parts,
            wc.x_costs.purchased_parts + wc.y_costs.purchased_parts + wc.z_costs.purchased_parts,
            cc.x_costs.purchased_parts,
            cc.y_costs.purchased_parts,
            cc.z_costs.purchased_parts,
            cc.x_costs.purchased_parts + cc.y_costs.purchased_parts + cc.z_costs.purchased_parts,
        )
    )
    # Equipment Usage
    lines.append(
        fmt_cost_line(
            wc.x_costs.equipment_usage,
            wc.y_costs.equipment_usage,
            wc.z_costs.equipment_usage,
            wc.x_costs.equipment_usage + wc.y_costs.equipment_usage + wc.z_costs.equipment_usage,
            cc.x_costs.equipment_usage,
            cc.y_costs.equipment_usage,
            cc.z_costs.equipment_usage,
            cc.x_costs.equipment_usage + cc.y_costs.equipment_usage + cc.z_costs.equipment_usage,
        )
    )
    # Parts Carrying
    lines.append(
        fmt_cost_line(
            wc.x_costs.parts_carrying,
            wc.y_costs.parts_carrying,
            wc.z_costs.parts_carrying,
            wc.x_costs.parts_carrying + wc.y_costs.parts_carrying + wc.z_costs.parts_carrying,
            cc.x_costs.parts_carrying,
            cc.y_costs.parts_carrying,
            cc.z_costs.parts_carrying,
            cc.x_costs.parts_carrying + cc.y_costs.parts_carrying + cc.z_costs.parts_carrying,
        )
    )
    # Products Carrying
    lines.append(
        fmt_cost_line(
            wc.x_costs.products_carrying,
            wc.y_costs.products_carrying,
            wc.z_costs.products_carrying,
            wc.x_costs.products_carrying + wc.y_costs.products_carrying + wc.z_costs.products_carrying,
            cc.x_costs.products_carrying,
            cc.y_costs.products_carrying,
            cc.z_costs.products_carrying,
            cc.x_costs.products_carrying + cc.y_costs.products_carrying + cc.z_costs.products_carrying,
        )
    )
    # Demand Penalty
    lines.append(
        fmt_cost_line(
            wc.x_costs.demand_penalty,
            wc.y_costs.demand_penalty,
            wc.z_costs.demand_penalty,
            wc.x_costs.demand_penalty + wc.y_costs.demand_penalty + wc.z_costs.demand_penalty,
            cc.x_costs.demand_penalty,
            cc.y_costs.demand_penalty,
            cc.z_costs.demand_penalty,
            cc.x_costs.demand_penalty + cc.y_costs.demand_penalty + cc.z_costs.demand_penalty,
        )
    )
    # Subtotal
    lines.append(
        fmt_cost_line(
            wc.x_costs.subtotal,
            wc.y_costs.subtotal,
            wc.z_costs.subtotal,
            wc.product_subtotal,
            cc.x_costs.subtotal,
            cc.y_costs.subtotal,
            cc.z_costs.subtotal,
            cc.product_subtotal,
        )
    )

    # Line 12: Total costs
    lines.append(f"{wc.total_costs:.1f} {cc.total_costs:.1f}")

    # Lines 13-14: Overhead costs
    wo = wc.overhead
    co = cc.overhead
    lines.append(
        f"{wo.quality_planning:.1f} {wo.plant_maintenance:.1f} "
        f"{wo.training_cost:.1f} {wo.hiring_cost:.1f} "
        f"{wo.layoff_firing_cost:.1f} {wo.raw_materials_carrying:.1f} "
        f"{wo.ordering_cost:.1f} {wo.fixed_expense:.1f} {wo.subtotal:.1f}"
    )
    lines.append(
        f"{co.quality_planning:.1f} {co.plant_maintenance:.1f} "
        f"{co.training_cost:.1f} {co.hiring_cost:.1f} "
        f"{co.layoff_firing_cost:.1f} {co.raw_materials_carrying:.1f} "
        f"{co.ordering_cost:.1f} {co.fixed_expense:.1f} {co.subtotal:.1f}"
    )

    # Lines 15-23: Production data
    all_machines = (
        report.production.parts_department + report.production.assembly_department
    )
    for i in range(9):
        if i < len(all_machines):
            mp = all_machines[i]
            # Convert part type for output (remove prime for code)
            part_code = {"X": 1, "Y": 2, "Z": 3, "X'": 1, "Y'": 2, "Z'": 3}.get(
                mp.part_type, 1
            )
            lines.append(
                f"{mp.machine_id} {part_code} {int(mp.scheduled_hours)} "
                f"{mp.productive_hours:.1f} {mp.production:.1f} {mp.rejects:.1f}"
            )
        else:
            lines.append("0 0 0 0. 0. 0.")

    # Line 24: Raw materials
    rm = report.inventory.raw_materials
    lines.append(
        f"{rm.beginning_inventory:.1f} {rm.orders_received:.1f} "
        f"{rm.used_in_production:.1f} {rm.ending_inventory:.1f}"
    )

    # Lines 25-31: Pending orders (7 slots)
    orders_by_type: dict[str, list[PendingOrderReport]] = {
        "Raw Materials (Reg)": [],
        "Raw Materials (Exp)": [],
        "Finished Part X'": [],
        "Finished Part Y'": [],
        "Finished Part Z'": [],
    }
    for order in report.pending_orders:
        if order.order_type in orders_by_type:
            orders_by_type[order.order_type].append(order)

    # Regular RM orders (3 slots)
    rm_orders = orders_by_type["Raw Materials (Reg)"]
    for i in range(3):
        if i < len(rm_orders):
            lines.append(f"{rm_orders[i].week_due}. {rm_orders[i].amount:.1f}")
        else:
            lines.append("0. 0.")
    # Expedited RM (1 slot)
    exp_orders = orders_by_type["Raw Materials (Exp)"]
    if exp_orders:
        lines.append(f"{exp_orders[0].week_due}. {exp_orders[0].amount:.1f}")
    else:
        lines.append("0. 0.")
    # Parts orders (3 slots)
    for part_type in ["X'", "Y'", "Z'"]:
        part_orders = orders_by_type[f"Finished Part {part_type}"]
        if part_orders:
            lines.append(f"{part_orders[0].week_due}. {part_orders[0].amount:.1f}")
        else:
            lines.append("0. 0.")

    # Lines 32-37: Parts and products inventory
    inv = report.inventory
    lines.append(
        f"{inv.parts_x.beginning_inventory:.1f} {inv.parts_x.orders_received:.1f} "
        f"{inv.parts_x.used_in_production:.1f} {inv.parts_x.production_this_week:.1f} "
        f"{inv.parts_x.ending_inventory:.1f}"
    )
    lines.append(
        f"{inv.products_x.beginning_inventory:.1f} {inv.products_x.production_this_week:.1f} "
        f"{inv.products_x.demand_this_week:.1f} {inv.products_x.ending_inventory:.1f}"
    )
    lines.append(
        f"{inv.parts_y.beginning_inventory:.1f} {inv.parts_y.orders_received:.1f} "
        f"{inv.parts_y.used_in_production:.1f} {inv.parts_y.production_this_week:.1f} "
        f"{inv.parts_y.ending_inventory:.1f}"
    )
    lines.append(
        f"{inv.products_y.beginning_inventory:.1f} {inv.products_y.production_this_week:.1f} "
        f"{inv.products_y.demand_this_week:.1f} {inv.products_y.ending_inventory:.1f}"
    )
    lines.append(
        f"{inv.parts_z.beginning_inventory:.1f} {inv.parts_z.orders_received:.1f} "
        f"{inv.parts_z.used_in_production:.1f} {inv.parts_z.production_this_week:.1f} "
        f"{inv.parts_z.ending_inventory:.1f}"
    )
    lines.append(
        f"{inv.products_z.beginning_inventory:.1f} {inv.products_z.production_this_week:.1f} "
        f"{inv.products_z.demand_this_week:.1f} {inv.products_z.ending_inventory:.1f}"
    )

    # Lines 38-40: Demand estimates
    lines.append(
        f"{report.demand_x.estimated_demand:.1f} {report.demand_x.carryover:.1f} "
        f"{report.demand_x.total_demand:.1f}"
    )
    lines.append(
        f"{report.demand_y.estimated_demand:.1f} {report.demand_y.carryover:.1f} "
        f"{report.demand_y.total_demand:.1f}"
    )
    lines.append(
        f"{report.demand_z.estimated_demand:.1f} {report.demand_z.carryover:.1f} "
        f"{report.demand_z.total_demand:.1f}"
    )

    # Lines 41-42: Performance metrics
    wp = report.weekly_performance
    cp = report.cumulative_performance
    lines.append(
        f"{wp.total_standard_costs:.1f} {wp.percent_efficiency:.2f} "
        f"{wp.variance_per_unit:.2f} {wp.on_time_delivery or 0:.1f}"
    )
    lines.append(
        f"{cp.total_standard_costs:.1f} {cp.percent_efficiency:.2f} "
        f"{cp.variance_per_unit:.2f} {cp.on_time_delivery or 0:.1f}"
    )

    content = "\n".join(lines) + "\n"

    # Write to destination
    if isinstance(destination, (str, Path)):
        with open(destination, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        destination.write(content)


def write_rept_human_readable(
    report: WeeklyReport, destination: str | Path | TextIO
) -> None:
    """Write a WeeklyReport in human-readable format (like week1.txt).

    Args:
        report: WeeklyReport object to write
        destination: File path, path object, or file-like object to write to
    """
    lines: list[str] = []

    lines.append("[Cost Information]")
    lines.append("")
    lines.append(
        f"Costs for Week:                X          Y          Z         Total"
    )
    lines.append("")

    wc = report.weekly_costs

    def fmt_row(name: str, x: float, y: float, z: float) -> str:
        total = x + y + z
        return f"{name:<24}{x:>10.1f}{y:>11.1f}{z:>11.1f}{total:>13.1f}"

    lines.append(
        fmt_row("Labor", wc.x_costs.labor, wc.y_costs.labor, wc.z_costs.labor)
    )
    lines.append(
        fmt_row(
            "Machine Set-Up",
            wc.x_costs.machine_setup,
            wc.y_costs.machine_setup,
            wc.z_costs.machine_setup,
        )
    )
    lines.append(
        fmt_row(
            "Machine Repair",
            wc.x_costs.machine_repair,
            wc.y_costs.machine_repair,
            wc.z_costs.machine_repair,
        )
    )
    lines.append(
        fmt_row(
            "Raw Materials",
            wc.x_costs.raw_materials,
            wc.y_costs.raw_materials,
            wc.z_costs.raw_materials,
        )
    )
    lines.append(
        fmt_row(
            "Purchased Finished Parts",
            wc.x_costs.purchased_parts,
            wc.y_costs.purchased_parts,
            wc.z_costs.purchased_parts,
        )
    )
    lines.append(
        fmt_row(
            "Equipment Usage",
            wc.x_costs.equipment_usage,
            wc.y_costs.equipment_usage,
            wc.z_costs.equipment_usage,
        )
    )
    lines.append(
        fmt_row(
            "Parts Carrying Cost",
            wc.x_costs.parts_carrying,
            wc.y_costs.parts_carrying,
            wc.z_costs.parts_carrying,
        )
    )
    lines.append(
        fmt_row(
            "Products Carrying Cost",
            wc.x_costs.products_carrying,
            wc.y_costs.products_carrying,
            wc.z_costs.products_carrying,
        )
    )
    lines.append(
        fmt_row(
            "Demand Penalty",
            wc.x_costs.demand_penalty,
            wc.y_costs.demand_penalty,
            wc.z_costs.demand_penalty,
        )
    )
    lines.append("")
    lines.append(
        fmt_row(
            "Sub-Total",
            wc.x_costs.subtotal,
            wc.y_costs.subtotal,
            wc.z_costs.subtotal,
        )
    )
    lines.append("")

    # Overhead
    wo = wc.overhead
    lines.append(f"Quality Planning{wo.quality_planning:>52.1f}")
    lines.append(f"Plant Maintenance{wo.plant_maintenance:>51.1f}")
    lines.append(f"Training Cost{wo.training_cost:>55.1f}")
    lines.append(f"Hiring Cost{wo.hiring_cost:>57.1f}")
    lines.append(f"Layoff and Firing Cost{wo.layoff_firing_cost:>46.1f}")
    lines.append(f"Raw Materials Carrying Cost{wo.raw_materials_carrying:>41.1f}")
    lines.append(f"Ordering Cost{wo.ordering_cost:>55.1f}")
    lines.append(f"Fixed Expense{wo.fixed_expense:>55.1f}")
    lines.append("")
    lines.append(f"Sub-Total{wo.subtotal:>59.1f}")
    lines.append("")
    lines.append(f"Total Costs{wc.total_costs:>57.1f}")
    lines.append("")

    # Production Information
    lines.append("")
    lines.append("[Production Information]")
    lines.append("")
    lines.append("Part Department:")
    lines.append(
        "                             Sched.  Productive"
    )
    lines.append(
        "Machine  Operator    Part    Hours     Hours     Production   Rejects"
    )
    lines.append("")

    for mp in report.production.parts_department:
        lines.append(
            f"   {mp.machine_id:<9}{mp.operator_id:<9}{mp.part_type:<8}"
            f"{mp.scheduled_hours:>5.1f}      {mp.productive_hours:>5.1f}"
            f"        {int(mp.production):>5}.       {int(mp.rejects):>3}."
        )

    lines.append("")
    lines.append("Assembly Department:")
    lines.append(
        "                             Sched.  Productive"
    )
    lines.append(
        "Machine  Operator  Product   Hours     Hours     Production   Rejects"
    )
    lines.append("")

    for mp in report.production.assembly_department:
        lines.append(
            f"   {mp.machine_id:<9}{mp.operator_id:<9}{mp.part_type:<8}"
            f"{mp.scheduled_hours:>5.1f}      {mp.productive_hours:>5.1f}"
            f"        {int(mp.production):>5}.       {int(mp.rejects):>3}."
        )

    # Inventory Information
    lines.append("")
    lines.append("")
    lines.append("[Inventory Information]")
    lines.append("")
    lines.append("Raw Materials:")
    lines.append(
        "     Beginning      Orders       Used in         Ending"
    )
    lines.append(
        "     Inventory     Received    Production      Inventory"
    )
    rm = report.inventory.raw_materials
    lines.append(
        f"       {int(rm.beginning_inventory)}.         {int(rm.orders_received)}."
        f"       {int(rm.used_in_production)}.              {int(rm.ending_inventory)}."
    )

    lines.append("")
    lines.append("Parts:")
    lines.append(
        "     Beginning      Orders       Used in      Production      Ending"
    )
    lines.append(
        "     Inventory     Received    Production     This  Week    Inventory"
    )
    for part_type, part_report in [
        ("X'", report.inventory.parts_x),
        ("Y'", report.inventory.parts_y),
        ("Z'", report.inventory.parts_z),
    ]:
        lines.append(
            f"  {part_type}   {int(part_report.beginning_inventory)}.         "
            f"{int(part_report.orders_received)}.        {int(part_report.used_in_production)}."
            f"          {int(part_report.production_this_week)}.        "
            f"{int(part_report.ending_inventory)}."
        )

    lines.append("")
    lines.append("Products:")
    lines.append(
        "     Beginning    Production      Demand        Ending"
    )
    lines.append(
        "     Inventory    This  Week    This Week     Inventory"
    )
    for prod_type, prod_report in [
        ("X", report.inventory.products_x),
        ("Y", report.inventory.products_y),
        ("Z", report.inventory.products_z),
    ]:
        lines.append(
            f"  {prod_type}      {int(prod_report.beginning_inventory)}.         "
            f"{int(prod_report.production_this_week)}.           {int(prod_report.demand_this_week)}."
            f"          {int(prod_report.ending_inventory)}."
        )

    # Demand Information
    lines.append("")
    lines.append("")
    lines.append("[Demand Information]")
    lines.append("")
    lines.append(
        "     Estimated     Carry Over      Estimated"
    )
    lines.append(
        "       Demand         From       Total Demand"
    )
    lines.append(
        "    This Month     Last Month     This Month"
    )
    for prod_type, demand in [
        ("X", report.demand_x),
        ("Y", report.demand_y),
        ("Z", report.demand_z),
    ]:
        lines.append(
            f"  {prod_type}    {int(demand.estimated_demand)}.           "
            f"{int(demand.carryover)}.            {int(demand.total_demand)}."
        )

    # Performance Measures
    lines.append("")
    lines.append("")
    lines.append("[Performance Measures]")
    lines.append("")
    lines.append("Current Week:")
    lines.append("")
    lines.append(
        "     Total         Total       Percent of    $ Variance   % On-Time"
    )
    lines.append(
        "   Std. Costs    Act. Costs    Efficiency     Per Unit     Delivery"
    )
    wp = report.weekly_performance
    on_time = f"{wp.on_time_delivery:.1f}" if wp.on_time_delivery else "NA"
    lines.append(
        f"     {wp.total_standard_costs:.1f}       {wp.total_actual_costs:.1f}"
        f"        {wp.percent_efficiency:.1f}          {wp.variance_per_unit:.1f}"
        f"          {on_time}"
    )

    lines.append("")
    lines.append("Cumulative:")
    lines.append("")
    lines.append(
        "     Total         Total       Percent of    $ Variance   % On-Time"
    )
    lines.append(
        "   Std. Costs    Act. Costs    Efficiency     Per Unit     Delivery"
    )
    cp = report.cumulative_performance
    cum_on_time = f"{cp.on_time_delivery:.1f}" if cp.on_time_delivery else "NA"
    lines.append(
        f"     {cp.total_standard_costs:.1f}       {cp.total_actual_costs:.1f}"
        f"        {cp.percent_efficiency:.1f}          {cp.variance_per_unit:.1f}"
        f"          {cum_on_time}"
    )
    lines.append("")

    content = "\n".join(lines)

    # Write to destination
    if isinstance(destination, (str, Path)):
        with open(destination, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        destination.write(content)


class REPTParser:
    """Parser for batch processing multiple REPT files.

    Provides validation and batch parsing capabilities.
    """

    def __init__(self, strict: bool = True) -> None:
        """Initialize parser.

        Args:
            strict: If True, raise errors on validation failures.
        """
        self.strict = strict

    def parse_file(self, path: str | Path) -> WeeklyReport:
        """Parse a single REPT file."""
        return parse_rept(path)

    def parse_directory(
        self, directory: str | Path, pattern: str = "REPT*.DAT"
    ) -> list[WeeklyReport]:
        """Parse all REPT files in a directory.

        Returns:
            List of parsed WeeklyReport objects, sorted by week
        """
        directory = Path(directory)
        reports: list[WeeklyReport] = []

        for file_path in sorted(directory.glob(pattern)):
            try:
                report = parse_rept(file_path)
                reports.append(report)
            except REPTParseError as e:
                if self.strict:
                    raise REPTParseError(
                        f"Error parsing {file_path}: {e}"
                    ) from e

        reports.sort(key=lambda r: (r.company_id, r.week))
        return reports
