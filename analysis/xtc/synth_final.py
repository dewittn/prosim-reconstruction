#!/usr/bin/env python3
import struct
from fractions import Fraction
from collections import defaultdict

FILES = {
    "prosim.xtc":  "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}
def walk(data, start=87):
    pos=start; recs=[]
    while pos<len(data):
        t=data[pos]
        if t==0x15 and pos+17<=len(data):
            recs.append((pos,0x15,struct.unpack("<4f",data[pos+1:pos+17]))); pos+=17
        elif t==0x12 and pos+9<=len(data):
            recs.append((pos,0x12,struct.unpack("<2f",data[pos+1:pos+9]))); pos+=9
        else: break
    return recs
lbl={}; nxt=[1]
def L(f1):
    if 2.7<f1<2.9: return "SENT"
    k=struct.pack("<f",f1).hex()
    if k not in lbl: lbl[k]=f"ID%02d"%nxt[0]; nxt[0]+=1
    return lbl[k]

allrec=defaultdict(list)   # id -> list of (file, f2, f3, f4)
for name,path in FILES.items():
    for off,tag,fl in walk(open(path,"rb").read()):
        if tag!=0x15: continue
        f1,f2,f3,f4=fl
        if 2.7<f1<2.9: continue
        allrec[(round(f1,6))].append((name,L(f1),f2,f3,f4))

# 1. Cumulative test: per operator, are f3 / f4 bounded & growing wk9->wk13?
print("=== f3/f4 RANGES per operator, wk9 vs wk13 (cumulative check) ===")
print(f"{'ID':5s}{'f1':>10s}  {'f3_wk9':>18s}  {'f3_wk13':>18s}  {'f4_wk9':>18s}  {'f4_wk13':>18s}")
for f1 in sorted(allrec):
    rs=allrec[f1]
    idn=rs[0][1]
    w9=[r for r in rs if r[0]=="prosim.xtc"]
    w13=[r for r in rs if r[0]=="prosim1.xtc"]
    def rng(rr,i):
        vs=[r[i] for r in rr]
        return f"{min(vs):8.0f}-{max(vs):8.0f}" if vs else "        -        "
    print(f"{idn:5s}{f1:10.6f}  {rng(w9,3):>18s}  {rng(w13,3):>18s}  {rng(w9,4):>18s}  {rng(w13,4):>18s}")

# 2. f4 / f1 and f4 / (f1*f2): do we get round hours*rate ?
print("\n=== f4 decomposition (unique f4 values per op, divided by f1 and f1*f2) ===")
for f1 in sorted(allrec):
    rs=allrec[f1]; idn=rs[0][1]
    f4s=sorted(set(round(r[4],1) for r in rs))
    print(f"  {idn} f1={f1:.5f}: sample f4/f1 -> " +
          ", ".join(f"{v/f1:.0f}" for v in f4s[:5]))

# 3. Float2 exhaustive: f2 as fraction, and best (a/b) with b<=120; also 1/f2, f2*f1, f2/f1, 1-f2
print("\n=== FLOAT2 CANDIDATE DECOMPOSITIONS ===")
f2set=sorted(set(round(r[2],6) for rs in allrec.values() for r in rs))
for f2 in f2set:
    fr=Fraction(f2).limit_denominator(120)
    print(f"  f2={f2:.6f}  ~{fr}  1/f2={1/f2:.4f}  1-f2={1-f2:.5f}  f2*40={f2*40:.3f}  f2*51={f2*51:.3f}  f2*60={f2*60:.3f}")

# 4. Does f2 relate to a productive/scheduled or good/standard ratio ~ 'percent efficiency'?
#    REPT percent-of-efficiency weekly values for context:
print("\n=== REPT 'Percent of Efficiency' (weekly, cumulative) for context ===")
print("  wk12: 54.29 / 59.47   wk13: 58.62 / 61.75   wk14: 54.86 / 60.25   (week1.txt: 64.7)")
print("  f2 range:", f"{min(f2set):.3f} - {max(f2set):.3f}", "(excluding 1.014 outlier: %.3f-%.3f)"%(min(f2set), sorted(f2set)[-2]))

# 5. Same-game test: identity set intersection between files
print("\n=== SAME-GAME / SHARED-CONSTANTS TEST ===")
in9=set(); in13=set()
for name,path in FILES.items():
    for off,tag,fl in walk(open(path,"rb").read()):
        if tag!=0x15: continue
        f1,f2,f3,f4=fl
        if 2.7<f1<2.9: continue
        (in9 if name=="prosim.xtc" else in13).add((round(f1,6),round(f2,6)))
print("  (f1,f2) identities in wk9 :", len(in9))
print("  (f1,f2) identities in wk13:", len(in13))
print("  shared exactly           :", len(in9&in13))
print("  only wk9 :", sorted(in9-in13))
print("  only wk13:", sorted(in13-in9))

# 6. Department-team hypothesis: within first group of prosim.xtc, list the operator
#    sequence to show 4-parts + 5-assembly repeating structure
print("\n=== OPERATOR SEQUENCE, prosim.xtc group0 (dept-team structure) ===")
recs=walk(open(FILES["prosim.xtc"],"rb").read())
seq=[]
for off,tag,fl in recs:
    if tag==0x12: break
    f1=fl[0]
    seq.append("SENT" if 2.7<f1<2.9 else L(f1))
print("  "+" ".join(seq))
