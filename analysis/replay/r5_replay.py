"""
r5_replay.py — DECS14 -> REPT14 end-to-end replay experiment.

Reconstructs the week-13 ENDING state of Nelson's 2004 game (company 2) from
REPT14's own beginning-of-week fields, feeds DECS14's actual decisions into the
project's simulation engine, and diffs the simulated week-14 report field by
field against the real REPT14.

Writes CSV artifacts next to this file. Does NOT modify anything under prosim/.

Run:
    .venv/bin/python analysis/replay/r5_replay.py
"""

from __future__ import annotations

import csv
import math
import os
from pathlib import Path

import xlrd

REPO = Path("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction")
DATA = REPO / "archive" / "data"
SHEETS = REPO / "archive" / "spreadsheets"
OUT = REPO / "analysis" / "replay"

# ---------------------------------------------------------------------------
# Config mirrored from prosim/config/defaults.py (READ-ONLY reference values).
# ---------------------------------------------------------------------------
PARTS_RATE = {"X'": 60, "Y'": 50, "Z'": 40}
ASM_RATE = {"X": 40, "Y": 30, "Z": 20}
TYPE_CODE = {1: "X", 2: "Y", 3: "Z"}
REJECT_RATE_TRUE = 0.1514   # derived from REPT14: rejects / (net+rejects)
REJECT_RATE_ENGINE = 0.178  # prosim REJECT_RATE constant used in production.py


# ---------------------------------------------------------------------------
# Raw parsers (self-contained; do not rely on engine parsers so we can inspect
# every raw number exactly as it appears on disk).
# ---------------------------------------------------------------------------
def read_nums(line: str) -> list[float]:
    return [float(t.rstrip(".")) for t in line.replace("\r", "").split() if t.strip()]


def parse_decs(path: Path) -> dict:
    lines = [l for l in path.read_text().splitlines() if l.strip()]
    h = read_nums(lines[0])
    parts = read_nums(lines[1])
    machines = []
    for i in range(2, 11):
        v = read_nums(lines[i])
        machines.append(
            {"operator": int(v[0]), "train_flag": int(v[1]),
             "type_code": int(v[2]), "sched": v[3]}
        )
    return {
        "week": int(h[0]), "company": int(h[1]),
        "quality": h[2], "maint": h[3], "rm_reg": h[4], "rm_exp": h[5],
        "part_orders": {"X'": parts[0], "Y'": parts[1], "Z'": parts[2]},
        "machines": machines,
    }


def parse_rept(path: Path) -> dict:
    L = [l for l in path.read_text().splitlines() if l.strip()]
    hdr = read_nums(L[0])
    cost_rows = [read_nums(L[i]) for i in range(1, 11)]  # 10 cost categories
    cost_names = ["labor", "setup", "repair", "raw_materials", "purchased_parts",
                  "equipment", "parts_carry", "products_carry", "demand_penalty",
                  "subtotal"]
    total = read_nums(L[11])
    oh_wk = read_nums(L[12])
    oh_cum = read_nums(L[13])
    prod = []
    for i in range(14, 23):
        v = read_nums(L[i])
        prod.append({"operator": int(v[0]), "type_code": int(v[1]),
                     "sched": v[2], "productive": v[3],
                     "production": v[4], "rejects": v[5]})
    rm = read_nums(L[23])  # beginning received used ending
    pending = [read_nums(L[i]) for i in range(24, 31)]
    parts_x = read_nums(L[31]); prod_x = read_nums(L[32])
    parts_y = read_nums(L[33]); prod_y = read_nums(L[34])
    parts_z = read_nums(L[35]); prod_z = read_nums(L[36])
    dem_x = read_nums(L[37]); dem_y = read_nums(L[38]); dem_z = read_nums(L[39])
    perf_wk = read_nums(L[40]); perf_cum = read_nums(L[41])
    return {
        "week": int(hdr[0]), "company": int(hdr[1]),
        "cost_names": cost_names, "cost_rows": cost_rows,
        "total_wk": total[0], "total_cum": total[1],
        "oh_wk": oh_wk, "oh_cum": oh_cum,
        "prod": prod,
        "rm": {"beginning": rm[0], "received": rm[1], "used": rm[2], "ending": rm[3]},
        "pending": pending,
        "parts": {"X'": parts_x, "Y'": parts_y, "Z'": parts_z},
        "products": {"X": prod_x, "Y": prod_y, "Z": prod_z},
        "demand": {"X": dem_x, "Y": dem_y, "Z": dem_z},
        "perf_wk": perf_wk, "perf_cum": perf_cum,
    }


def load_efficiencies() -> dict[int, float]:
    wb = xlrd.open_workbook(str(SHEETS / "ProsimTable(Nelson).xls"))
    sh = wb.sheet_by_name("Operators")
    eff = {}
    for r in range(4, sh.nrows):  # rows: OP | %
        a = sh.cell_value(r, 0)
        b = sh.cell_value(r, 1)
        if isinstance(a, float) and isinstance(b, float) and b:
            eff[int(a)] = b
    return eff


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def dept_and_type(slot_idx: int, type_code: int) -> tuple[str, str, float]:
    """slot_idx 0-3 parts, 4-8 assembly. Returns (dept, type_label, base_rate)."""
    if slot_idx < 4:
        label = {1: "X'", 2: "Y'", 3: "Z'"}[type_code]
        return "parts", label, PARTS_RATE[label]
    label = {1: "X", 2: "Y", 3: "Z"}[type_code]
    return "assembly", label, ASM_RATE[label]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    decs = parse_decs(DATA / "DECS14.DAT")
    rept = parse_rept(DATA / "REPT14.DAT")
    eff = load_efficiencies()

    # ---- 1. Field table --------------------------------------------------
    write_field_table(rept)

    # ---- 2. Per-operator production formula validation -------------------
    prod_rows = []
    for slot, (d, r) in enumerate(zip(decs["machines"], rept["prod"])):
        op = r["operator"]
        dept, label, base = dept_and_type(slot, r["type_code"])
        e = eff.get(op, float("nan"))
        real_prod = r["production"]   # NET good units (verified)
        real_rej = r["rejects"]
        real_gross = real_prod + real_rej
        prodhrs = r["productive"]
        sched = r["sched"]

        # Formula using REAL productive hours + real efficiency (oracle):
        gross_f = prodhrs * base * e
        rej_f = round(gross_f * REJECT_RATE_TRUE)
        net_f = round(gross_f) - rej_f

        # Engine-native path: gross = scheduled * eff * base ; reject 17.8%
        gross_eng_sched = sched * base * e
        rej_eng = round(gross_eng_sched * REJECT_RATE_ENGINE)
        net_eng = round(gross_eng_sched) - rej_eng

        prod_rows.append({
            "slot": slot + 1, "operator": op, "dept": dept, "type": label,
            "base_rate": base, "efficiency": round(e, 6),
            "sched_hrs": sched, "real_productive_hrs": prodhrs,
            "real_gross": round(real_gross), "real_net": round(real_prod),
            "real_rejects": round(real_rej),
            "formula_gross(prodhrs*base*eff)": round(gross_f, 1),
            "formula_net": net_f, "formula_rej": rej_f,
            "net_err_formula": net_f - round(real_prod),
            "engine_gross(sched*base*eff)": round(gross_eng_sched, 1),
            "engine_net(17.8%rej)": net_eng,
            "net_err_engine": net_eng - round(real_prod),
        })

    with open(OUT / "r5_production_check.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(prod_rows[0].keys()))
        w.writeheader(); w.writerows(prod_rows)

    # ---- 3. Derive week-13 ending state ----------------------------------
    week13 = derive_week13(rept)
    (OUT / "r5_week13_derived.txt").write_text(week13)

    # ---- 4. Run the actual engine forward with a corrected harness -------
    engine_report = run_engine(decs, rept, eff)

    # ---- 5. Field-by-field diff ------------------------------------------
    diff = build_diff(rept, prod_rows, engine_report)
    with open(OUT / "r5_diff.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(diff[0].keys()))
        w.writeheader(); w.writerows(diff)

    # ---- 6. Console summary ----------------------------------------------
    print_summary(prod_rows, rept, engine_report, diff)


def write_field_table(rept: dict) -> None:
    rows = []
    cn = rept["cost_names"]
    cols = ["wk_X", "wk_Y", "wk_Z", "wk_T", "cum_X", "cum_Y", "cum_Z", "cum_T"]
    for name, vals in zip(cn, rept["cost_rows"]):
        for c, v in zip(cols, vals):
            rows.append({"section": "cost", "field": f"{name}_{c}", "value": v})
    oh_names = ["quality", "maint", "training", "hiring", "layoff",
                "rm_carry", "ordering", "fixed", "subtotal"]
    for n, v in zip(oh_names, rept["oh_wk"]):
        rows.append({"section": "overhead_wk", "field": n, "value": v})
    for n, v in zip(oh_names, rept["oh_cum"]):
        rows.append({"section": "overhead_cum", "field": n, "value": v})
    rows.append({"section": "total", "field": "weekly", "value": rept["total_wk"]})
    rows.append({"section": "total", "field": "cumulative", "value": rept["total_cum"]})
    for p in rept["prod"]:
        tag = f"op{p['operator']}_{TYPE_CODE[p['type_code']]}"
        for k in ["sched", "productive", "production", "rejects"]:
            rows.append({"section": "production", "field": f"{tag}_{k}", "value": p[k]})
    for k, v in rept["rm"].items():
        rows.append({"section": "raw_materials", "field": k, "value": v})
    for t, vals in rept["parts"].items():
        for k, v in zip(["beginning", "received", "used", "produced", "ending"], vals):
            rows.append({"section": "parts", "field": f"{t}_{k}", "value": v})
    for t, vals in rept["products"].items():
        for k, v in zip(["beginning", "produced", "demand", "ending"], vals):
            rows.append({"section": "products", "field": f"{t}_{k}", "value": v})
    for t, vals in rept["demand"].items():
        for k, v in zip(["estimated", "carryover", "total"], vals):
            rows.append({"section": "demand", "field": f"{t}_{k}", "value": v})
    with open(OUT / "r5_rept14_fields.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["section", "field", "value"])
        w.writeheader(); w.writerows(rows)


def derive_week13(rept: dict) -> str:
    L = []
    L.append("WEEK-13 ENDING STATE (= week-14 beginning), derived from REPT14 itself")
    L.append("=" * 70)
    L.append("")
    L.append("INVENTORIES (derived-exact: report beginning col = prior week ending)")
    L.append(f"  Raw materials beginning : {rept['rm']['beginning']:.0f}")
    for t in ["X'", "Y'", "Z'"]:
        L.append(f"  Parts {t} beginning      : {rept['parts'][t][0]:.0f}")
    for t in ["X", "Y", "Z"]:
        L.append(f"  Products {t} beginning    : {rept['products'][t][0]:.0f}")
    L.append("")
    L.append("CUMULATIVE COSTS THROUGH WEEK 13 (derived-exact: cum - weekly)")
    for name, vals in zip(rept["cost_names"], rept["cost_rows"]):
        wk_t, cum_t = vals[3], vals[7]
        L.append(f"  {name:16s}: cum13_total = {cum_t - wk_t:10.1f}"
                 f"   (cum14 {cum_t:.1f} - wk14 {wk_t:.1f})")
    L.append(f"  {'TOTAL':16s}: cum13_total = {rept['total_cum']-rept['total_wk']:10.1f}")
    L.append("")
    L.append("WEEK-14 RECEIPTS (observed inputs set by week-<=13 ordering decisions)")
    L.append(f"  Raw materials received  : {rept['rm']['received']:.0f}")
    for t in ["X'", "Y'", "Z'"]:
        L.append(f"  Parts {t} received       : {rept['parts'][t][1]:.0f}")
    return "\n".join(L)


def run_engine(decs: dict, rept: dict, eff: dict) -> dict:
    """Run prosim's real ProductionEngine + CostCalculator via a corrected
    harness that maps DECS operator-ids to machine slots (the built-in
    apply_decisions_to_machines cannot, because it treats col-1 as machine id).

    Efficiency is injected as an oracle (exact real per-operator multiplier) by
    fixing tier/level to a known matrix cell and back-solving proficiency.
    """
    from prosim.config.defaults import get_operator_efficiency
    from prosim.config.schema import get_default_config
    from prosim.engine.production import ProductionEngine, ProductionInput
    from prosim.engine.workforce import OperatorEfficiencyResult
    from prosim.models.machines import Machine
    from prosim.models.operators import Department, Operator, TrainingStatus

    cfg = get_default_config()
    engine = ProductionEngine(config=cfg)

    tier, level = 5, 5
    cell = get_operator_efficiency(tier, level)  # 1.08

    results = {"native": [], "oracle_sched": [], "oracle_prodhrs": []}
    for slot, (d, r) in enumerate(zip(decs["machines"], rept["prod"])):
        op = r["operator"]
        dept = Department.PARTS if slot < 4 else Department.ASSEMBLY
        label = ({1: "X'", 2: "Y'", 3: "Z'"} if slot < 4
                 else {1: "X", 2: "Y", 3: "Z"})[r["type_code"]]
        base = (PARTS_RATE if slot < 4 else ASM_RATE)[label]
        target_eff = eff[op]
        prof = max(0.5, min(1.5, target_eff / cell))

        machine = Machine(machine_id=slot + 1, department=dept)
        machine = machine.assign(operator_id=op, part_type=label,
                                 scheduled_hours=r["sched"])
        # oracle operator with exact efficiency
        oracle_op = Operator(operator_id=op, quality_tier=tier,
                             training_level=level, proficiency=prof)
        er_sched = OperatorEfficiencyResult(
            operator_id=op, scheduled_hours=r["sched"],
            productive_hours=r["sched"] * oracle_op.efficiency,
            efficiency=oracle_op.efficiency,
            training_status=TrainingStatus.TRAINED, is_in_training=False)
        mr = engine.calculate_machine_production(
            ProductionInput(machine=machine, efficiency_result=er_sched))
        results["oracle_sched"].append(
            {"operator": op, "type": label, "gross": mr.gross_production,
             "net": mr.net_production, "rejects": mr.rejects,
             "productive": mr.productive_hours})

        # oracle + observed productive hours (inject availability)
        machine2 = Machine(machine_id=slot + 1, department=dept)
        machine2 = machine2.assign(operator_id=op, part_type=label,
                                   scheduled_hours=r["productive"])
        er_p = OperatorEfficiencyResult(
            operator_id=op, scheduled_hours=r["productive"],
            productive_hours=r["productive"] * oracle_op.efficiency,
            efficiency=oracle_op.efficiency,
            training_status=TrainingStatus.TRAINED, is_in_training=False)
        mr2 = engine.calculate_machine_production(
            ProductionInput(machine=machine2, efficiency_result=er_p))
        results["oracle_prodhrs"].append(
            {"operator": op, "type": label, "gross": mr2.gross_production,
             "net": mr2.net_production, "rejects": mr2.rejects,
             "productive": mr2.productive_hours})

        # native: engine's own default operator (max-trained by week 14)
        from prosim.config.defaults import STARTING_OPERATOR_PROFILES
        prof_n = STARTING_OPERATOR_PROFILES.get(op, {}).get("proficiency", 1.0)
        tier_n = STARTING_OPERATOR_PROFILES.get(op, {}).get("quality_tier", 5)
        nat_op = Operator(operator_id=op, quality_tier=tier_n,
                          training_level=10, proficiency=prof_n)
        er_n = OperatorEfficiencyResult(
            operator_id=op, scheduled_hours=r["sched"],
            productive_hours=r["sched"] * nat_op.efficiency,
            efficiency=nat_op.efficiency,
            training_status=TrainingStatus.TRAINED, is_in_training=False)
        mrn = engine.calculate_machine_production(
            ProductionInput(machine=machine, efficiency_result=er_n))
        results["native"].append(
            {"operator": op, "type": label, "gross": mrn.gross_production,
             "net": mrn.net_production, "rejects": mrn.rejects,
             "efficiency": nat_op.efficiency})
    return results


def build_diff(rept: dict, prod_rows: list, engine: dict) -> list:
    rows = []
    for pr, os_, on in zip(prod_rows, engine["oracle_sched"], engine["native"]):
        real = pr["real_net"]
        rows.append({
            "field": f"prod_op{pr['operator']}_{pr['type']}_net",
            "real": real,
            "engine_native": round(on["net"]),
            "engine_oracle_sched": round(os_["net"]),
            "err_native": round(on["net"]) - real,
            "err_oracle_sched": round(os_["net"]) - real,
            "category": "production",
        })
    return rows


def print_summary(prod_rows, rept, engine, diff) -> None:
    print("=" * 74)
    print("PRODUCTION FORMULA VALIDATION (net good units)")
    print("=" * 74)
    print(f"{'op':>3} {'type':>4} {'real_net':>9} {'formula':>9} {'err':>5} "
          f"{'eng_sched':>10} {'err':>6} {'eng_native':>11} {'err':>7}")
    tot_real = tot_ferr = tot_serr = tot_nerr = 0
    for pr, os_, on in zip(prod_rows, engine["oracle_sched"], engine["native"]):
        real = pr["real_net"]
        ferr = pr["formula_net"] - real
        serr = round(os_["net"]) - real
        nerr = round(on["net"]) - real
        tot_real += real; tot_ferr += abs(ferr)
        tot_serr += abs(serr); tot_nerr += abs(nerr)
        print(f"{pr['operator']:>3} {pr['type']:>4} {real:>9} "
              f"{pr['formula_net']:>9} {ferr:>5} {round(os_['net']):>10} {serr:>6} "
              f"{round(on['net']):>11} {nerr:>7}")
    print("-" * 74)
    print(f"total real net units: {tot_real}")
    print(f"formula abs err (oracle eff + real productive hrs): {tot_ferr} "
          f"({100*tot_ferr/tot_real:.2f}%)")
    print(f"engine abs err (oracle eff + scheduled hrs):        {tot_serr} "
          f"({100*tot_serr/tot_real:.2f}%)")
    print(f"engine abs err (native max-trained profiles):       {tot_nerr} "
          f"({100*tot_nerr/tot_real:.2f}%)")
    print()
    print("COST CATEGORY REALITY vs ENGINE FORMULA")
    print("-" * 74)
    labor_real = rept["cost_rows"][0][3]
    rm_real = rept["cost_rows"][3][3]
    equip_real = rept["cost_rows"][5][3]
    print(f"labor weekly total:     real={labor_real:.0f}  "
          f"engine=productive*$10 (no OT, no sched basis)")
    print(f"raw materials weekly:   real={rm_real:.0f}  "
          f"engine=gross_parts*1.0*1.0 (ignores X'/Y'/Z'=1/2/3 units & $1.14 avg)")
    print(f"equipment weekly:       real={equip_real:.0f}  "
          f"engine=productive*$100/$80 (real ~ $20-25/scheduled-hr)")


if __name__ == "__main__":
    main()
