#!/usr/bin/env python3
"""Explore the body region: locate 0x15 tag positions, gaps, and what other tag
bytes appear at the 'gap' boundaries, to build a tag/length table."""
import struct
from collections import Counter, defaultdict

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

def load(path):
    with open(path, "rb") as f:
        return f.read()

def hx(b):
    return " ".join(f"{x:02x}" for x in b)

HEADER_END = 87  # approx, will refine

for name, path in FILES.items():
    data = load(path)
    print(f"=== {name} ({len(data)} bytes) ===")
    positions = [i for i, b in enumerate(data) if b == 0x15 and i >= HEADER_END]
    print(f"0x15 occurrences (>= offset {HEADER_END}): {len(positions)}")
    gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
    gap_hist = Counter(gaps)
    print("Gap histogram (top 20):")
    for g, c in gap_hist.most_common(20):
        print(f"  gap={g:4d} count={c}")
    print()

    # For each 0x15 position, check byte at pos+17 (hypothesized next record start if this is a 17-byte record)
    print("Byte value at pos+17 (byte immediately after hypothesized 17-byte 0x15 record):")
    next_byte_hist = Counter()
    for p in positions:
        if p + 17 < len(data):
            next_byte_hist[data[p+17]] += 1
    for b, c in next_byte_hist.most_common(15):
        print(f"  0x{b:02x} count={c}")
    print()

    # For 0x15 positions where gap to NEXT 0x15 is NOT 17, print what's between
    print("Sample non-17 gaps (first 15), showing bytes between consecutive 0x15 tags:")
    shown = 0
    for i in range(len(positions)-1):
        g = positions[i+1] - positions[i]
        if g != 17 and shown < 15:
            p = positions[i]
            between = data[p:p+min(g, 60)]
            print(f"  pos={p:6d} gap={g:4d} bytes={hx(between)}")
            shown += 1
    print()
    print("=" * 80)
    print()
