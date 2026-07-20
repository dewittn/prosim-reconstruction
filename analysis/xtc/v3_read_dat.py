"""Read DECS raw and parse REPT files into readable structures."""
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction")
from prosim.io.rept_parser import parse_rept

D = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/"

print("########## DECS FILES (raw lines) ##########")
for fn in ["DECS14.DAT", "DECS14_week3.DAT", "DECS14_Aroot.DAT", "DECS12.txt"]:
    print(f"\n----- {fn} -----")
    with open(D + fn) as f:
        for i, line in enumerate(f):
            print(f"  {i}: {repr(line.rstrip())}")

print("\n\n########## REPT FILES parsed ##########")
for fn in ["REPT14.DAT", "REPT12.DAT", "REPT13.DAT"]:
    print(f"\n========== {fn} ==========")
    r = parse_rept(D + fn)
    print(f"week={r.week} company={r.company_id}")
    print("PRODUCTION parts dept:")
    for mp in r.production.parts_department:
        print(f"  M{mp.machine_id} op{mp.operator_id} {mp.part_type} sched={mp.scheduled_hours} prodhrs={mp.productive_hours} prod={mp.production} rej={mp.rejects}")
    print("PRODUCTION assembly dept:")
    for mp in r.production.assembly_department:
        print(f"  M{mp.machine_id} op{mp.operator_id} {mp.part_type} sched={mp.scheduled_hours} prodhrs={mp.productive_hours} prod={mp.production} rej={mp.rejects}")
    inv = r.inventory
    print("RAW MATERIALS:", inv.raw_materials)
    print(f"PARTS X': {inv.parts_x}")
    print(f"PARTS Y': {inv.parts_y}")
    print(f"PARTS Z': {inv.parts_z}")
    print(f"PRODUCTS X: {inv.products_x}")
    print(f"PRODUCTS Y: {inv.products_y}")
    print(f"PRODUCTS Z: {inv.products_z}")
    print(f"DEMAND X: {r.demand_x}")
    print(f"DEMAND Y: {r.demand_y}")
    print(f"DEMAND Z: {r.demand_z}")
    print(f"WEEKLY PERF: {r.weekly_performance}")
    print(f"CUM PERF: {r.cumulative_performance}")
    wc = r.weekly_costs
    print(f"WEEKLY totals: X_sub={wc.x_costs.subtotal} Y_sub={wc.y_costs.subtotal} Z_sub={wc.z_costs.subtotal} total={wc.total_costs}")
    print(f"  labor X/Y/Z = {wc.x_costs.labor}/{wc.y_costs.labor}/{wc.z_costs.labor}")
    print(f"  RM    X/Y/Z = {wc.x_costs.raw_materials}/{wc.y_costs.raw_materials}/{wc.z_costs.raw_materials}")
    print(f"  equip X/Y/Z = {wc.x_costs.equipment_usage}/{wc.y_costs.equipment_usage}/{wc.z_costs.equipment_usage}")
    print(f"  demandpen X/Y/Z = {wc.x_costs.demand_penalty}/{wc.y_costs.demand_penalty}/{wc.z_costs.demand_penalty}")
