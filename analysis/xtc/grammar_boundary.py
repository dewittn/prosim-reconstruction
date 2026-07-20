#!/usr/bin/env python3
import struct, math
from collections import Counter

FILES = {
    "prosim.xtc": ("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc", 912),
    "prosim1.xtc": ("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc", 1355),
}

def load(path):
    with open(path, "rb") as f:
        return f.read()

def entropy(block):
    if not block:
        return 0.0
    c = Counter(block)
    n = len(block)
    return -sum((v/n) * math.log2(v/n) for v in c.values())

def hx(b):
    return " ".join(f"{x:02x}" for x in b)

for name, (path, boundary) in FILES.items():
    data = load(path)
    print(f"=== {name} (boundary={boundary}) ===")
    print(f"Bytes around boundary ({boundary-8}..{boundary+40}):")
    print(" ", hx(data[boundary-8:boundary+40]))
    print()
    print(f"Entropy [78,{boundary}) structured region: {entropy(data[78:boundary]):.3f} bits/byte")
    print(f"Entropy [{boundary}, end) post-boundary region: {entropy(data[boundary:]):.3f} bits/byte")
    print(f"Entropy [0,78) header preamble: {entropy(data[0:78]):.3f} bits/byte")
    print()
    # first 16-byte preamble decode attempt
    pre = data[0:16]
    print(f"Preamble bytes[0:16]: {hx(pre)}")
    for i in range(0, 15, 2):
        val = struct.unpack_from("<H", pre, i)[0]
        print(f"  u16 @ [{i}:{i+2}] = {val}")
    print()
    print("=" * 90)
