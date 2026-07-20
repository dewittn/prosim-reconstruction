#!/usr/bin/env python3
"""Fine-grained 512-byte sliding window entropy scan across the ENTIRE tail of both
files, to locate any genuinely low order-0-entropy 512B block (the brief described one
in prosim.xtc at ~4.1 bits/byte -- confirm exact location, since the literal last 512
bytes measured at 7.38 bits/byte, not 4.1)."""
import math
from collections import Counter

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}
with open(FILES["prosim.xtc"], "rb") as f:
    d0 = f.read()
with open(FILES["prosim1.xtc"], "rb") as f:
    d1 = f.read()

def shannon_entropy(data):
    if not data:
        return 0.0
    c = Counter(data)
    n = len(data)
    return -sum((v/n) * math.log2(v/n) for v in c.values())

def scan(data, window, step, tail_start=0):
    out = []
    for i in range(tail_start, len(data) - window + 1, step):
        out.append((i, shannon_entropy(data[i:i+window])))
    return out

for name, data in [("prosim.xtc", d0), ("prosim1.xtc", d1)]:
    print(f"\n=== {name}: 512-byte window, step 64, whole file ===")
    res = scan(data, 512, 64)
    res_sorted = sorted(res, key=lambda x: x[1])
    print("10 lowest-entropy 512B windows:")
    for o, e in res_sorted[:10]:
        print(f"  offset {o:6d} (ends {o+512}, {len(data)-(o+512)} bytes before EOF): entropy={e:.3f}")
    print("Entropy exactly at file end (offset len-512):")
    print(f"  offset {len(data)-512}: entropy={shannon_entropy(data[-512:]):.3f}")
