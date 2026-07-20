#!/usr/bin/env python3
import struct
from fractions import Fraction
from collections import defaultdict

FILES = {
    "prosim.xtc":  "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}
MATRIX = {
    0:[20,61,79,89,96,100,103,106,108,109,109],
    1:[21,63,81,91,98,103,106,109,111,112,112],
    2:[21,64,82,93,100,104,108,110,112,114,114],
    3:[21,64,83,94,101,106,109,112,114,116,116],
    4:[21,65,84,95,102,107,110,113,115,117,117],
    5:[22,66,85,96,103,108,111,114,116,118,118],
    6:[22,66,85,96,104,108,112,115,117,118,118],
    7:[22,66,86,97,104,109,112,115,117,119,119],
    8:[22,67,86,97,104,109,113,116,118,120,120],
    9:[22,67,87,98,105,110,113,116,118,120,120],
}

def walk(data, start=87):
    pos=start; recs=[]
    while pos < len(data):
        t=data[pos]
        if t==0x15 and pos+17<=len(data):
            recs.append((pos,0x15,data[pos+1:pos+17])); pos+=17
        elif t==0x12 and pos+9<=len(data):
            recs.append((pos,0x12,data[pos+1:pos+9])); pos+=9
        else: break
    return recs

# unique identities
ids={}
def key(f1): return struct.pack("<f",f1).hex()

records=[]
for name,path in FILES.items():
    for off,tag,payload in walk(open(path,"rb").read()):
        if tag==0x15:
            f1,f2,f3,f4=struct.unpack("<4f",payload)
            d1,d2=struct.unpack("<2d",payload)   # 2-double interpretation
            records.append((name,off,f1,f2,f3,f4,d1,d2))

# distinct f1 set
f1set=sorted(set(round(r[2],6) for r in records if not 2.7<r[2]<2.9))
print("=== DISTINCT f1 VALUES as rationals (small denom) ===")
for f1 in f1set:
    fr=Fraction(f1).limit_denominator(200)
    print(f"  f1={f1:.6f} ~ {fr}  ({fr.numerator}/{fr.denominator})  1-f1={1-f1:.6f}")

print("\n=== DISTINCT f2 VALUES as rationals ===")
f2set=sorted(set(round(r[3],6) for r in records if not 2.7<r[3]<2.9))
for f2 in f2set:
    fr=Fraction(f2).limit_denominator(200)
    print(f"  f2={f2:.6f} ~ {fr}  ({fr.numerator}/{fr.denominator})")

# For each (f1,f2) identity: test f1 and f2 against matrix cells (raw, /f1, /f2)
print("\n=== f1 vs MATRIX (raw f1*100 nearest cell) ===")
def nearest_cell(val):
    best=None
    for t in MATRIX:
        for l,c in enumerate(MATRIX[t]):
            e=abs(c-val)
            if best is None or e<best[0]:
                best=(e,t,l,c)
    return best
for f1 in f1set:
    e,t,l,c=nearest_cell(f1*100)
    print(f"  f1={f1:.6f} -> {f1*100:.3f}  nearest matrix[{t}][{l}]={c} (err {e:.3f})")

print("\n=== proficiency test: f1*1.088 and does f1 = actualEff/matrix? ===")
# Two-component: actual = matrix[t][l]*prof. If f1 = prof, then f1*matrix should hit a clean %
# Just report f1*1.088
for f1 in f1set:
    print(f"  f1={f1:.6f}  *1.088={f1*1.088:.4f}  *1.20={f1*1.2:.4f}  1/f1={1/f1:.4f}")

# f1*f2 composite
print("\n=== f1*f2 (composite?) and f2/f1 ===")
seen=set()
for name,off,f1,f2,f3,f4,d1,d2 in records:
    if 2.7<f1<2.9: continue
    k=(round(f1,6),round(f2,6))
    if k in seen: continue
    seen.add(k)
    print(f"  f1={f1:.6f} f2={f2:.6f}  f1*f2={f1*f2:.5f}  f2/f1={f2/f1:.5f}  f1-f2={f1-f2:.5f}")

# 2-double interpretation sanity
print("\n=== 2-DOUBLE interpretation of first few records ===")
for r in records[:6]:
    print(f"  {r[0]} off{r[1]}: floats=({r[2]:.4f},{r[3]:.4f},{r[4]:.2f},{r[5]:.2f})  doubles=({r[6]:.6e},{r[7]:.6e})")

# f4 vs 40*rate*f1*f2 and variants
print("\n=== f4 relation tests (first occurrence per identity) ===")
RATES=[60,50,40,30,20,100,80,10]
seen=set()
for name,off,f1,f2,f3,f4,d1,d2 in records:
    if 2.7<f1<2.9: continue
    k=round(f1,6)
    if k in seen: continue
    seen.add(k)
    print(f"  f1={f1:.4f} f2={f2:.4f} f4={f4:.2f}: f4/(f1*f2)={f4/(f1*f2):.1f}  f4/f1={f4/f1:.1f} f4/f2={f4/f2:.1f} f4/40={f4/40:.2f}")
