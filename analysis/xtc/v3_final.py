"""Consolidate: DECS variant match, production-model fidelity test, accuracy CSV."""
import sys, csv
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction")
import xlrd
from prosim.io.rept_parser import parse_rept

BASE = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/spreadsheets/"
D = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/"
OUT = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/v3_accuracy.csv"

def cell(sh,r,c):
    return sh.cell_value(r,c) if (r<sh.nrows and c<sh.ncols) else None

book = xlrd.open_workbook(BASE+"ProsimTable.xls")

# ---------- DECS14 tab vs the three DECS variants ----------
print("="*80)
print("DECS14 tab (spreadsheet) vs DECS .DAT variants")
dsh = book.sheet_by_name("DECS14")
sheet_hdr = [cell(dsh,0,c) for c in range(1,7)]
sheet_ops = {}
for r in range(2,11):
    op=cell(dsh,r,1); train=cell(dsh,r,2); typ=cell(dsh,r,3); hrs=cell(dsh,r,4)
    if isinstance(op,float): sheet_ops[int(op)] = (int(train), int(typ), int(hrs))
print(f"  SHEET DECS14 header(f2..f6) = {sheet_hdr}")
print(f"  SHEET ops = {sheet_ops}")

def read_decs(fn):
    hdr=None; ops={}
    with open(D+fn) as f:
        for i,line in enumerate(f):
            t=line.split()
            if i==0: hdr=[float(x) for x in t]
            elif i>=2 and len(t)>=4:
                ops[int(float(t[0]))]=(int(float(t[1])),int(float(t[2])),int(float(t[3])))
    return hdr,ops
for fn in ["DECS14.DAT","DECS14_week3.DAT","DECS14_Aroot.DAT"]:
    hdr,ops=read_decs(fn)
    # compare op->(train,type,hours)
    common=set(sheet_ops)&set(ops)
    exact=sum(1 for op in common if sheet_ops[op]==ops[op])
    print(f"  {fn}: header={hdr[1:6]} rosters {'SAME' if set(ops)==set(sheet_ops) else 'DIFF'}; ops match {exact}/{len(common)}")

# Which variant produced REPT14?  (match scheduled hours+type)
print("\n  Which DECS produced REPT14.DAT?")
r14=parse_rept(D+"REPT14.DAT")
r14ops={mp.operator_id:(mp.part_type.rstrip("'"),mp.scheduled_hours) for mp in list(r14.production.parts_department)+list(r14.production.assembly_department)}
typemap={1:'X',2:'Y',3:'Z'}
for fn in ["DECS14.DAT","DECS14_week3.DAT","DECS14_Aroot.DAT"]:
    hdr,ops=read_decs(fn)
    ok=0; tot=0
    for op,(tr,ty,hr) in ops.items():
        if op in r14ops:
            tot+=1
            if r14ops[op][0]==typemap.get(ty) and abs(r14ops[op][1]-hr)<0.5: ok+=1
    print(f"    {fn}: {ok}/{tot} op-type-hours match REPT14 production")

# ---------- Production-model fidelity: reconstruct REPT12 gross from hours*std*eff ----------
# Nelson(May25) Sheet1 gives per-op standard rate + back-calc eff for week12 (its 'last week').
# Test: does produced ~= prodhrs * standard * eff * (1-reject)?  (model self-consistency)
print("\n"+"="*80)
print("Production identity check on REPT12 (gross = prodhrs*standard*eff)")
nb=xlrd.open_workbook(BASE+"ProsimTable(Nelson).xls"); s1=nb.sheet_by_name("Sheet1")
for r in range(4,12):
    op=cell(s1,r,0)
    if not isinstance(op,float) or op==0: continue
    acthrs=cell(s1,r,3); produced=cell(s1,r,4); rej=cell(s1,r,5); std=cell(s1,r,6); eff=cell(s1,r,7)
    gross=produced+rej
    pred_gross=acthrs*std*eff
    print(f"  op{int(op):>2}: gross={gross:.0f} vs hrs*std*eff={pred_gross:.1f}  (std={std} eff={eff:.3f})")

# ---------- Build accuracy CSV: operator-efficiency predictions (the genuine forecast pairs) ----------
print("\n"+"="*80)
print("Writing accuracy CSV (operator-efficiency prediction pairs, FINAL Operators tab)")
ops_sh=book.sheet_by_name("Operators")
rows=[]
for r in [20,22,24,26,28,30,32,34,36]:
    op=cell(ops_sh,r,3); act=cell(ops_sh,r,4); est=cell(ops_sh,r,5)
    if isinstance(act,float) and isinstance(est,float) and est:
        acc=1-abs(est-act)/abs(act)
        rows.append(dict(category="operator_efficiency", item=f"op{int(op)}",
                         predicted=round(est,4), actual=round(act,4),
                         ratio=round(act/est,4), pct_error=round(abs(est-act)/abs(act)*100,2),
                         accuracy_pct=round(acc*100,2)))
with open(OUT,"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["category","item","predicted","actual","ratio","pct_error","accuracy_pct"])
    w.writeheader()
    for row in rows: w.writerow(row)
    # aggregate
    m=sum(x["accuracy_pct"] for x in rows)/len(rows)
import statistics
accs=[x["accuracy_pct"] for x in rows]
print(f"  wrote {len(rows)} rows to {OUT}")
print(f"  operator_efficiency: mean acc={statistics.mean(accs):.1f}%  median={statistics.median(accs):.1f}%  min={min(accs):.1f}% max={max(accs):.1f}%")

# ---------- Efficiency series stats (game score, NOT prediction accuracy) ----------
print("\n"+"="*80)
print("Eff series (game cost-efficiency = std cost/actual cost) summary")
eff=book.sheet_by_name("Eff")
series=[cell(eff,r,6) for r in range(24,38)]
print(f"  weeks: {[round(x,3) for x in series]}")
print(f"  cume cell (Eff r24 c8) = {cell(eff,24,8):.4f}  ;  other cell (r23 c6) = {cell(eff,23,6):.4f}")
print(f"  simple mean of weekly = {statistics.mean(series):.4f}")
