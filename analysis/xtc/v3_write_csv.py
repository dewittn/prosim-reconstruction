"""Write the consolidated v3_accuracy.csv with all scoreable categories."""
import csv, xlrd
BASE="/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/spreadsheets/"
OUT="/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/v3_accuracy.csv"
book=xlrd.open_workbook(BASE+"ProsimTable.xls")
def cell(sh,r,c): return sh.cell_value(r,c)

ops=book.sheet_by_name("Operators"); res=book.sheet_by_name("Results")
est={};act={}
for r in [20,22,24,26,28,30,32,34,36]:
    op=int(cell(ops,r,3)); act[op]=cell(ops,r,4); est[op]=cell(ops,r,5)
prod={}
for r in list(range(2,6))+list(range(7,12)):
    op=cell(res,r,0)
    if isinstance(op,float) and op!=0: prod[int(op)]=cell(res,r,3)

rows=[]
# operator efficiency forecast pairs
for op in est:
    a=act[op]; e=est[op]
    rows.append(dict(category="operator_efficiency_forecast", item=f"op{op}",
        predicted=round(e,4), actual=round(a,4), pct_error=round(abs(e-a)/a*100,2),
        accuracy_pct=round((1-abs(e-a)/a)*100,2),
        note="predicted (round est) vs game-reported operator efficiency"))
# per-operator production implied by efficiency forecast
for op in prod:
    ap=prod[op]; pp=ap*est[op]/act[op]
    rows.append(dict(category="operator_production_forecast", item=f"op{op}",
        predicted=round(pp,0), actual=round(ap,0), pct_error=round(abs(pp-ap)/ap*100,2),
        accuracy_pct=round((1-abs(pp-ap)/ap)*100,2),
        note="production=hours*std*eff; predicted uses estimated eff"))
# aggregate production
ta=sum(prod[o] for o in prod); tp=sum(prod[o]*est[o]/act[o] for o in prod)
rows.append(dict(category="AGGREGATE_production", item="all_operators_total",
    predicted=round(tp,0), actual=round(ta,0), pct_error=round(abs(tp-ta)/ta*100,2),
    accuracy_pct=round((1-abs(tp-ta)/ta)*100,2),
    note="net total; per-op over/under errors partially cancel"))
# game efficiency reference (NOT prediction accuracy)
eff=book.sheet_by_name("Eff")
series=[cell(eff,r,6) for r in range(24,38)]
rows.append(dict(category="REFERENCE_game_efficiency", item="cumulative_Eff!I24",
    predicted="", actual=round(cell(eff,24,8),4), pct_error="",
    accuracy_pct=round(cell(eff,24,8)*100,2),
    note="GAME cost-efficiency (std cost/actual cost), NOT forecast accuracy"))
rows.append(dict(category="REFERENCE_game_efficiency", item="mean_weekly_1_14",
    predicted="", actual=round(sum(series)/len(series),4), pct_error="",
    accuracy_pct=round(sum(series)/len(series)*100,2),
    note="mean of 14 weekly game efficiencies (0.647..1.282)"))

fields=["category","item","predicted","actual","pct_error","accuracy_pct","note"]
with open(OUT,"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for r in rows: w.writerow(r)
print(f"wrote {len(rows)} rows -> {OUT}")
# print category aggregates
from collections import defaultdict
import statistics
byc=defaultdict(list)
for r in rows:
    if isinstance(r["accuracy_pct"],(int,float)) and r["category"].startswith(("operator","AGG")):
        byc[r["category"]].append(r["accuracy_pct"])
for c,v in byc.items():
    print(f"  {c}: n={len(v)} mean={statistics.mean(v):.1f}% median={statistics.median(v):.1f}% range={min(v):.1f}-{max(v):.1f}%")
