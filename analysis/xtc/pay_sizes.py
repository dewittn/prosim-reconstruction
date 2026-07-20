#!/usr/bin/env python3
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_extract import chain_walk, FILES

for tag, (path, start, maxn) in FILES.items():
    data = open(path, "rb").read()
    markers = chain_walk(data, start, maxn)
    print(f"=== {tag} ===")
    for idx, (n, moff, pstart) in enumerate(markers):
        pend = markers[idx+1][1] if idx+1 < len(markers) else len(data)
        payload = data[pstart:pend]
        print(f"  n={n:3d} moff={moff:6d} pstart={pstart:6d} pend={pend:6d} len={len(payload):5d}")
