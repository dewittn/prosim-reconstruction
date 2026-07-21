"""
DECS14 -> REPT14 end-to-end replay regression test (Discovery #19).

This is the productionized version of ``analysis/replay/r5_replay.py``. It feeds
Nelson's real week-14 decisions (``archive/data/DECS14.DAT``) through the
reconstruction's NATIVE engine (ProductionEngine + CostCalculator) and asserts
an EXACT match against the historical REPT14 report on every deterministic field
that the engine is now expected to reproduce.

What is injected as an observed ORACLE (values that the engine has no generative
model for, so they are supplied from the historical record / derived-exact
sources per ``analysis/replay/r5_week13_state.md``):

- Per-operator effective efficiency multiplier (derived-exact; recorded in
  ProsimTable(Nelson).xls and independently re-derivable from REPT14).
- Per-operator productive/availability hours (a stochastic downtime input the
  engine deliberately does NOT model -- see the PARTIAL note on
  ProductionInput.availability_hours).
- Week-13 ending inventories used for carrying-cost valuation (derived-exact:
  REPT14's beginning column is week-13's ending column).

Everything else (production identity, reject rate on gross, labor with overtime,
equipment per scheduled hour, raw-material per-type costing, value-scaled
carrying rates, and the DECS operator-id -> machine-slot mapping) is computed by
the engine's own code paths.

Known exclusions (documented, not asserted):
- Setup costs (REPT14 wk: X=80, Y=120). Reproducing these needs Nelson's
  week-13 machine->operator assignments, which are NOT in the archive (state
  gap, not an engine bug). All machines start with last_part_type=None here, so
  the engine charges zero setup.
- Machine repair (stochastic; REPT14 wk repair = 0 anyway).
- Any per-product split of equipment/RM cost: only the deterministic TOTALS are
  asserted for those two (the single-week per-department decomposition is
  unresolved -- see Discovery #19).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from prosim.config.defaults import calculate_reject_rate
from prosim.config.schema import get_default_config
from prosim.engine.costs import CostCalculationInput, CostCalculator
from prosim.engine.production import ProductionEngine, ProductionInput
from prosim.engine.workforce import OperatorEfficiencyResult, WorkforceCostResult
from prosim.io.decs_parser import parse_decs
from prosim.models.inventory import (
    AllPartsInventory,
    AllProductsInventory,
    Inventory,
    PartsInventory,
    ProductsInventory,
    RawMaterialsInventory,
)
from prosim.models.machines import MachineFloor
from prosim.models.operators import TrainingStatus
from prosim.models.orders import OrderBook

REPO = Path(__file__).resolve().parent.parent
DECS14 = REPO / "archive" / "data" / "DECS14.DAT"

QUALITY_BUDGET = 750.0  # DECS14 line 1

# ---------------------------------------------------------------------------
# Observed ORACLE per operator, in DECS14 row order (rows 1-4 Parts, 5-9
# Assembly). efficiency and productive_hours are derived-exact / observed;
# real_net and real_rejects are the REPT14 "Production"/"Rejects" columns.
# ---------------------------------------------------------------------------
OPERATORS = [
    # operator, efficiency,  productive_hrs, real_net, real_rejects
    (3, 1.252083, 40.0, 2550, 455),
    (5, 0.656000, 40.0, 1113, 199),
    (2, 0.914912, 38.0, 1770, 316),
    (7, 1.055833, 40.0, 2150, 384),
    (4, 0.675521, 48.0, 1101, 196),
    (6, 0.926901, 34.2, 807, 144),
    (1, 0.840000, 50.0, 1426, 254),
    (26, 0.721703, 32.1, 590, 105),
    (18, 0.678161, 11.6, 200, 36),
]

# Week-13 ending inventories (= week-14 beginning), derived-exact from REPT14.
WEEK13_ENDING_PARTS = {"X'": 1139.0, "Y'": 492.0, "Z'": 1517.0}
WEEK13_ENDING_PRODUCTS = {"X": 1472.0, "Y": 1032.0, "Z": 1317.0}

# REPT14 week-14 ENDING inventories used for carrying valuation (derived-exact).
REPT14_ENDING_PARTS = {"X'": 3348.0, "Y'": 223.0, "Z'": 1917.0}
REPT14_ENDING_PRODUCTS = {"X": 3999.0, "Y": 2630.0, "Z": 1317.0}

# REPT14 deterministic cost targets (weekly totals / per-type).
REPT14_LABOR_TOTAL = 4000.0
REPT14_LABOR_BY_PRODUCT = {"X": 2300.0, "Y": 1700.0, "Z": 0.0}
REPT14_EQUIPMENT_TOTAL = 8000.0
REPT14_RM_TOTAL = 11700.0
REPT14_PARTS_CARRY_TOTAL = 437.0
REPT14_PARTS_CARRY_BY_PRODUCT = {"X": 167.0, "Y": 20.0, "Z": 249.0}
REPT14_PRODUCTS_CARRY_TOTAL = 1558.0
REPT14_PRODUCTS_CARRY_BY_PRODUCT = {"X": 400.0, "Y": 605.0, "Z": 553.0}


def _build_engine_report():
    """Run the native engine over DECS14 with observed oracle inputs."""
    config = get_default_config()
    engine = ProductionEngine(config=config)

    # Parse Nelson's real decisions and apply them via the engine's own mapping
    # (exercises the fixed apply_decisions_to_machines: DECS col-1 is the
    # operator id, machine slot comes from row position).
    decisions = parse_decs(DECS14)

    from prosim.engine.simulation import Simulation

    sim = Simulation(config=config)
    floor = MachineFloor.create_default()
    floor = sim.apply_decisions_to_machines(floor, decisions)

    eff_by_op = {op: eff for op, eff, _, _, _ in OPERATORS}
    prod_by_op = {op: hrs for op, _, hrs, _, _ in OPERATORS}

    reject_rate = calculate_reject_rate(QUALITY_BUDGET)

    inputs = []
    for machine in floor.machines.values():
        assignment = machine.assignment
        if assignment is None or assignment.operator_id is None:
            continue
        op = assignment.operator_id
        efficiency = eff_by_op[op]
        eff_result = OperatorEfficiencyResult(
            operator_id=op,
            scheduled_hours=assignment.scheduled_hours,
            productive_hours=prod_by_op[op] * efficiency,
            efficiency=efficiency,
            training_status=TrainingStatus.TRAINED,
            is_in_training=False,
        )
        inputs.append(
            ProductionInput(
                machine=machine,
                efficiency_result=eff_result,
                availability_hours=prod_by_op[op],
                reject_rate=reject_rate,
            )
        )

    production_result = engine.calculate_production(inputs)
    return floor, production_result, config


def _machine_results_by_operator(production_result):
    out = {}
    for mr in (
        production_result.parts_department.machine_results
        + production_result.assembly_department.machine_results
    ):
        if mr.operator_id is not None:
            out[mr.operator_id] = mr
    return out


def test_decs_operator_mapping_places_all_nine_operators():
    """The fixed DECS mapping assigns operators by row position to slots 1-9.

    This is the regression for Discovery #19 fix #7: the old code used DECS
    col-1 as the machine id and silently dropped hired operators 18 and 26.
    """
    floor, _, _ = _build_engine_report()
    slot_to_operator = {
        mid: floor.machines[mid].assignment.operator_id
        for mid in sorted(floor.machines)
        if floor.machines[mid].assignment
    }
    assert slot_to_operator == {
        1: 3,
        2: 5,
        3: 2,
        4: 7,
        5: 4,
        6: 6,
        7: 1,
        8: 26,
        9: 18,
    }


@pytest.mark.parametrize("operator, _eff, _hrs, real_net, real_rejects", OPERATORS)
def test_per_operator_production_exact(operator, _eff, _hrs, real_net, real_rejects):
    """Each operator's net production and rejects match REPT14 exactly."""
    _, production_result, _ = _build_engine_report()
    results = _machine_results_by_operator(production_result)
    mr = results[operator]
    assert round(mr.net_production) == real_net
    assert round(mr.rejects) == real_rejects


def _cost_report():
    floor, production_result, config = _build_engine_report()

    inventory = Inventory(
        raw_materials=RawMaterialsInventory(beginning=0.0),
        parts=AllPartsInventory(
            x_prime=PartsInventory(
                part_type="X'", beginning=REPT14_ENDING_PARTS["X'"]
            ),
            y_prime=PartsInventory(
                part_type="Y'", beginning=REPT14_ENDING_PARTS["Y'"]
            ),
            z_prime=PartsInventory(
                part_type="Z'", beginning=REPT14_ENDING_PARTS["Z'"]
            ),
        ),
        products=AllProductsInventory(
            x=ProductsInventory(product_type="X", beginning=REPT14_ENDING_PRODUCTS["X"]),
            y=ProductsInventory(product_type="Y", beginning=REPT14_ENDING_PRODUCTS["Y"]),
            z=ProductsInventory(product_type="Z", beginning=REPT14_ENDING_PRODUCTS["Z"]),
        ),
    )

    calc = CostCalculator(config=config)
    calc_input = CostCalculationInput(
        week=14,
        production_result=production_result,
        inventory=inventory,
        order_book=OrderBook(),
        workforce_costs=WorkforceCostResult(
            training_cost=0.0,
            hiring_cost=0.0,
            layoff_cost=0.0,
            termination_cost=0.0,
            total_cost=0.0,
            operators_hired=0,
            operators_terminated=0,
            operators_trained=0,
            operators_laid_off=0,
        ),
        quality_budget=QUALITY_BUDGET,
        maintenance_budget=600.0,
    )
    return calc.calculate_weekly_costs(calc_input)


def test_labor_cost_exact():
    """Labor = scheduled hours * $10 + overtime premium; matches REPT14 exactly."""
    report = _cost_report()
    labor_by_product = {
        pt: report.product_costs[pt].labor for pt in ("X", "Y", "Z")
    }
    for pt, expected in REPT14_LABOR_BY_PRODUCT.items():
        assert labor_by_product[pt] == pytest.approx(expected)
    assert sum(labor_by_product.values()) == pytest.approx(REPT14_LABOR_TOTAL)


def test_equipment_cost_total_exact():
    """Equipment = scheduled hours * per-scheduled-hour rate; total matches 8000."""
    report = _cost_report()
    total = sum(report.product_costs[pt].equipment_usage for pt in ("X", "Y", "Z"))
    assert round(total) == REPT14_EQUIPMENT_TOTAL


def test_raw_material_cost_total_matches():
    """RM = gross parts * per-type units * weighted-avg price; total ~= 11700."""
    report = _cost_report()
    total = sum(report.product_costs[pt].raw_materials for pt in ("X", "Y", "Z"))
    # Small residual from gross rounding + blended price; assert to reported precision.
    assert round(total) == REPT14_RM_TOTAL


def test_parts_carrying_cost_exact():
    """Value-scaled parts carrying (X' 0.05, Y' 0.09, Z' 0.13) matches REPT14."""
    report = _cost_report()
    by_product = {pt: report.product_costs[pt].parts_carrying for pt in ("X", "Y", "Z")}
    for pt, expected in REPT14_PARTS_CARRY_BY_PRODUCT.items():
        assert round(by_product[pt]) == expected
    # REPT14's own total (437) is round(sum of unrounded per-type), not the sum
    # of the rounded per-type values (436) -- a reporting rounding artifact.
    assert round(sum(by_product.values())) == REPT14_PARTS_CARRY_TOTAL


def test_products_carrying_cost_exact():
    """Value-scaled products carrying (X 0.10, Y 0.23, Z 0.42) matches REPT14."""
    report = _cost_report()
    by_product = {
        pt: report.product_costs[pt].products_carrying for pt in ("X", "Y", "Z")
    }
    for pt, expected in REPT14_PRODUCTS_CARRY_BY_PRODUCT.items():
        assert round(by_product[pt]) == expected
    assert round(sum(by_product.values())) == REPT14_PRODUCTS_CARRY_TOTAL


def test_reject_rate_curve_anchor():
    """The reject curve returns the verified 15.14% of gross at the $750 budget."""
    assert calculate_reject_rate(QUALITY_BUDGET) == pytest.approx(0.1514, abs=1e-4)
