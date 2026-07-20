#!/usr/bin/env python3
"""Basic recon: hex dump chunks, byte histogram, ASCII string scan, entropy profile."""
import struct
import math
from collections import Counter

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
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

def rolling_entropy(data, window=256, step=128):
    out = []
    for i in range(0, len(data) - window + 1, step):
        out.append((i, entropy(data[i:i+window])))
    return out

def ascii_strings(data, minlen=4):
    out = []
    cur = []
    start = 0
    for i, b in enumerate(data):
        if 32 <= b < 127:
            if not cur:
                start = i
            cur.append(chr(b))
        else:
            if len(cur) >= minlen:
                out.append((start, "".join(cur)))
            cur = []
    if len(cur) >= minlen:
        out.append((start, "".join(cur)))
    return out

for name, path in FILES.items():
    data = load(path)
    print(f"=== {name} ({len(data)} bytes) ===")
    print("First 128 bytes hex:")
    for i in range(0, 128, 16):
        chunk = data[i:i+16]
        hexs = " ".join(f"{b:02x}" for b in chunk)
        print(f"  {i:5d}: {hexs}")
    print()
    print("Byte histogram (top 20):")
    hist = Counter(data)
    for b, cnt in hist.most_common(20):
        print(f"  0x{b:02x} ({b:3d}) count={cnt}")
    print()
    print("ASCII strings (len>=4):")
    for off, s in ascii_strings(data):
        print(f"  {off:6d}: {s!r}")
    print()
    print("Rolling entropy (window=256, step=256):")
    for off, e in rolling_entropy(data, 256, 256):
        bar = "#" * int(e * 4)
        print(f"  {off:6d}: {e:.3f} {bar}")
    print()
