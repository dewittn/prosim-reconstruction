"""Systematic prediction-vs-actual extraction and scoring.

Strategy:
 - Load REPT12/13/14 actual per-operator production (net produced, rejects, prod hours).
 - Load each spreadsheet version's prediction blocks + pasted-actual blocks.
 - Cross-match by operator-set + scheduled hours to see which snapshots refer to
   the same game week as any held REPT.
 - Score every prediction/actual pair we can defensibly form.
"""
import sys, csv
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction")
import xlrd
from prosim.io.rept_parser import parse_rept

BASE = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/spreadsheets/"
D = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/"

def cell(sh, r, c):
    if r < sh.nrows and c < sh.ncols:
        v = sh.cell_value(r, c)
        return v
    return None

# ---------- REPT actuals ----------
print("="*90)
print("REPT ACTUAL per-operator production (net produced)")
rept = {}
for wk, fn in [(12,"REPT12.DAT"),(13,"REPT13.DAT"),(14,"REPT14.DAT")]:
    r = parse_rept(D+fn)
    ops = {}
    for mp in list(r.production.parts_department)+list(r.production.assembly_department):
        ops[mp.operator_id] = dict(type=mp.part_type.rstrip("'"), sched=mp.scheduled_hours,
                                   prodhrs=mp.productive_hours, prod=mp.production, rej=mp.rejects)
    rept[wk] = dict(report=r, ops=ops)
    print(f"REPT{wk}: ops={sorted(ops)}")
    for op in sorted(ops):
        o=ops[op]
        print(f"   op{op:>2} {o['type']} sched{o['sched']:.0f} prodhrs{o['prodhrs']:.1f} produced{o['prod']:.0f} rej{o['rej']:.0f} (gross{o['prod']+o['rej']:.0f})")

# ---------- Eff tab exact series (final) ----------
print("\n"+"="*90)
print("Eff tab weekly efficiency series (FINAL) - exact")
book = xlrd.open_workbook(BASE+"ProsimTable.xls")
eff = book.sheet_by_name("Eff")
for r in range(24,38):
    wknum = cell(eff,r,5); val = cell(eff,r,6)
    extra = cell(eff,r,8)
    print(f"  week {wknum}: eff={val}   {'CUME='+str(extra) if extra not in (None,'') else ''}")
print("  0.9212 cell (r23c6):", cell(eff,23,6))

# compare to REPT efficiencies
print("\nREPT reported efficiencies (weekly / cumulative):")
for wk in (12,13,14):
    r=rept[wk]['report']
    print(f"  REPT{wk}: weekly={r.weekly_performance.percent_efficiency}  cum={r.cumulative_performance.percent_efficiency}")

# ---------- Operators tab: Actual vs Estimated efficiency (FINAL) ----------
print("\n"+"="*90)
print("Operators tab: predicted (Estimated) vs Actual operator efficiency (FINAL)")
ops_sh = book.sheet_by_name("Operators")
pairs = []
for r in [20,22,24,26,28,30,32,34,36]:
    op = cell(ops_sh,r,3); act = cell(ops_sh,r,4); est = cell(ops_sh,r,5)
    if isinstance(act,float) and isinstance(est,float) and est:
        acc = 1 - abs(est-act)/abs(act)
        pairs.append(("op_eff", f"op{int(op)}", est, act, acc))
        print(f"  op{int(op):>2}: estimated={est:.4f} actual={act:.4f}  ratio={act/est:.4f}  acc={acc*100:.1f}%")
if pairs:
    m = sum(p[4] for p in pairs)/len(pairs)
    print(f"  --> mean operator-efficiency prediction accuracy = {m*100:.1f}% (n={len(pairs)})")

# ---------- Nelson(May25) Sheet1 vs REPT12 (verify paste) ----------
print("\n"+"="*90)
print("Nelson(May25) Sheet1 'last week' vs REPT12 actuals (verify exact paste)")
nb = xlrd.open_workbook(BASE+"ProsimTable(Nelson).xls")
s1 = nb.sheet_by_name("Sheet1")
match=0; tot=0
for r in range(4,12):
    op=cell(s1,r,0); prod=cell(s1,r,4); rej=cell(s1,r,5)
    if not isinstance(op,float) or op==0: continue
    op=int(op)
    if op in rept[12]['ops']:
        a=rept[12]['ops'][op]
        tot+=1
        ok = abs(prod-a['prod'])<0.5 and abs(rej-a['rej'])<0.5
        match+=ok
        print(f"  op{op:>2}: sheet produced={prod:.0f} rej={rej:.0f} | REPT12 produced={a['prod']:.0f} rej={a['rej']:.0f}  {'MATCH' if ok else 'DIFF'}")
print(f"  --> {match}/{tot} exact matches")

# ---------- Cross-match: does any spreadsheet PREDICTION block equal a REPT week? ----------
print("\n"+"="*90)
print("Cross-match spreadsheet 100%-estimate rosters/hours against REPT scheduled hours")
def results_pred(book, label):
    sh = book.sheet_by_name("Results")
    rows=[]
    for r in list(range(2,6))+list(range(7,12)):
        op=cell(sh,r,0); pct=cell(sh,r,1); typ=cell(sh,r,2); prod=cell(sh,r,3); hrs=cell(sh,r,4)
        if isinstance(op,float) and op!=0:
            rows.append((int(op), typ, hrs, prod, pct))
    return rows
for bk,lbl in [(book,"FINAL"),(xlrd.open_workbook(BASE+'ProsimTable(Week3).xls'),"WEEK3"),(nb,"NELSON")]:
    rows=results_pred(bk,lbl)
    roster=sorted(r[0] for r in rows)
    print(f"  {lbl}: pred roster={roster}")
    for wk in (12,13,14):
        if sorted(rept[wk]['ops'])==roster:
            print(f"     == same operator set as REPT{wk}")

# ---------- Week Sumary pasted actuals (final & week3) - which week? ----------
print("\n"+"="*90)
print("'Week Sumary' pasted-actual production (per version) — find matching REPT")
def week_sumary(book,label,name="Week Sumary"):
    sh=book.sheet_by_name(name)
    rows=[]
    for r in range(7,16):
        op=cell(sh,r,0); typ=cell(sh,r,1); sched=cell(sh,r,2); act=cell(sh,r,3); prod=cell(sh,r,4); rej=cell(sh,r,5)
        if isinstance(op,float) and op!=0:
            rows.append((int(op),typ,sched,act,prod,rej))
    return rows
for bk,lbl,nm in [(book,"FINAL","Week Sumary"),(xlrd.open_workbook(BASE+'ProsimTable(Week3).xls'),"WEEK3","Week Sumary")]:
    rows=week_sumary(bk,lbl,nm)
    print(f"  {lbl} last-week actuals: roster={sorted(x[0] for x in rows)}")
    for op,typ,sched,act,prod,rej in rows:
        print(f"     op{op:>2} {typ} sched{sched} acthrs{act} produced{prod:.0f} rej{rej:.0f}")
    for wk in (12,13,14):
        if sorted(x[0] for x in rows)==sorted(rept[wk]['ops']):
            print(f"     == same roster as REPT{wk}")
