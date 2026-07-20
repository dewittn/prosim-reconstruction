"""Aggregate production-prediction accuracy.

production = hours * standard * efficiency, so per operator
   predicted_prod / actual_prod = estimated_eff / actual_eff.
Weight per-op errors by actual production (final Results 100% block) to get a
TOTAL output-prediction accuracy (errors partially cancel across operators)."""
import xlrd
BASE="/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/spreadsheets/"
book=xlrd.open_workbook(BASE+"ProsimTable.xls")
def cell(sh,r,c): return sh.cell_value(r,c)

# actual & estimated eff (Operators tab)
ops=book.sheet_by_name("Operators")
est={}; act={}
for r in [20,22,24,26,28,30,32,34,36]:
    op=int(cell(ops,r,3)); act[op]=cell(ops,r,4); est[op]=cell(ops,r,5)

# actual-eff production weights (Results 100% block col3, %-col1 = actual eff)
res=book.sheet_by_name("Results")
prod={}
for r in list(range(2,6))+list(range(7,12)):
    op=cell(res,r,0)
    if isinstance(op,float) and op!=0:
        prod[int(op)]=cell(res,r,3)

tot_act=0.0; tot_pred=0.0; tot_abs=0.0
print(f"{'op':>3} {'est_eff':>7} {'act_eff':>7} {'act_prod':>9} {'pred_prod':>9} {'err%':>6}")
for op in prod:
    ap=prod[op]
    pp=ap*est[op]/act[op]          # predicted production if he'd used estimated eff
    tot_act+=ap; tot_pred+=pp; tot_abs+=abs(pp-ap)
    print(f"{op:>3} {est[op]:>7.3f} {act[op]:>7.3f} {ap:>9.0f} {pp:>9.0f} {(pp-ap)/ap*100:>+6.1f}")
print("-"*50)
print(f"TOTAL actual prod   = {tot_act:.0f}")
print(f"TOTAL predicted prod= {tot_pred:.0f}")
print(f"Net total accuracy  = {(1-abs(tot_pred-tot_act)/tot_act)*100:.1f}%  (signed bias {(tot_pred-tot_act)/tot_act*100:+.1f}%)")
print(f"Mean-abs per-op accuracy (weighted) = {(1-tot_abs/tot_act)*100:.1f}%")
