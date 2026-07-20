#!/usr/bin/env python3
"""Emit the corrected 11-real-identity table (ID03 split into ID03a/ID03b using f2,
since build_identity_labeler in map_common.py keys only on f1 and collides two
distinct operators that happen to share an identical float32 f1 bit pattern).
Adds a department column derived from the tag byte (0x87=Parts, 0x86=Assembly,
confirmed by the 4/5 machine-count match in prosim/config/defaults.py SIMULATION).
"""
import csv

ROWS = [
    dict(identity="ID01", f1=0.8508557677268982, f2=0.6103542447090149, v1=410, v2=327, tag="0x87", dept="Parts", p1="0xe2fe", p2="0xe2ff"),
    dict(identity="ID02", f1=0.8074246048927307, f2=0.5699745416641235, v1=165, v2=141, tag="0x86", dept="Assembly", p1="0xe18a", p2="0xe18b"),
    dict(identity="ID03a", f1=0.818823516368866, f2=0.5833333134651184, v1=304, v2=212, tag="0x87", dept="Parts", p1="0xe2b8", p2="0xe2b9"),
    dict(identity="ID03b", f1=0.818823516368866, f2=0.5490196347236633, v1=336, v2=388, tag="0x86", dept="Assembly", p1="0xe0ea", p2="0xe0eb"),
    dict(identity="ID04", f1=0.6397058963775635, f2=0.6637036800384521, v1=228, v2=178, tag="0x87", dept="Parts", p1="0xe070", p2="0xe071"),
    dict(identity="ID05", f1=0.8093023300170898, f2=0.5586034655570984, v1=303, v2=320, tag="0x86", dept="Assembly", p1="0xe08a", p2="0xe08b"),
    dict(identity="ID06", f1=0.7750557065010071, f2=0.6170799136161804, v1=373, v2=383, tag="0x86", dept="Assembly", p1="0xe248", p2="0xe249"),
    dict(identity="ID07", f1=0.9666666388511658, f2=0.5941644310951233, v1=282, v2=196, tag="0x87", dept="Parts", p1="0xe2b2", p2="0xe29f (NON-CONSECUTIVE)"),
    dict(identity="ID09", f1=0.9086161851882935, f2=0.5551425218582153, v1=264, v2=239, tag="0x86", dept="Assembly", p1="0xe12a", p2="0xe12b"),
    dict(identity="ID08", f1=1.03125, f2=0.6777609586715698, v1=111, v2=114, tag="0x82", dept="UNKNOWN (non-standard scheme)", p1="0xfe09", p2="0x93f8 (NON-CONSECUTIVE)"),
    dict(identity="ID10", f1=1.0192307233810425, f2=1.0144927501678467, v1=85, v2=135, tag="0x84", dept="UNKNOWN (non-standard scheme)", p1="0xf8a7", p2="0x3e29 (NON-CONSECUTIVE)"),
]

OUT = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/c2_constants_corrected.csv"
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(ROWS[0].keys()))
    w.writeheader()
    w.writerows(ROWS)
print(f"Wrote {len(ROWS)} rows to {OUT}")
