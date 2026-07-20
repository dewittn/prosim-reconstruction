#!/usr/bin/env python3
import struct
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

# global identity labels by f1 bytes
lbl={}; nxt=[1]
def L(f1):
    if 2.7<f1<2.9: return "SENT"
    k=struct.pack("<f",f1).hex()
    if k not in lbl: lbl[k]=f"ID%02d"%nxt[0]; nxt[0]+=1
    return lbl[k]

for name,path in FILES.items():
    recs=walk(open(path,"rb").read())
    print(f"\n########## {name} ##########")
    g=0; gi=0
    for off,tag,fl in recs:
        if tag==0x12:
            print(f"  ---- 0x12 SEPARATOR  vals=({fl[0]:.4f},{fl[1]:.4f}) ---- end group {g}")
            g+=1; gi=0; continue
        f1,f2,f3,f4=fl
        print(f"  g{g} i{gi:2d} {L(f1):5s} f1={f1:.6f} f2={f2:.6f} f3={f3:12.3f} f4={f4:11.3f}")
        gi+=1

# Per identity, per file: list (group, f2, f3, f4) to see f2 variance and f3/f4 evolution
print("\n\n========== PER-IDENTITY TRAJECTORIES ==========")
for name,path in FILES.items():
    recs=walk(open(path,"rb").read())
    byid=defaultdict(list)
    g=0
    for off,tag,fl in recs:
        if tag==0x12: g+=1; continue
        f1,f2,f3,f4=fl
        if 2.7<f1<2.9: continue
        byid[L(f1)].append((g,f2,f3,f4))
    print(f"\n--- {name} ---")
    for idn in sorted(byid,key=lambda x:int(x[2:])):
        occ=byid[idn]
        f2s=sorted(set(round(o[1],6) for o in occ))
        print(f"  {idn}: n={len(occ)} f2variants={f2s}")
        for (g,f2,f3,f4) in occ:
            print(f"      g{g} f2={f2:.6f} f3={f3:11.3f} f4={f4:10.3f}")
