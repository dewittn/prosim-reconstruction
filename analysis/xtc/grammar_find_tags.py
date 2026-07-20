#!/usr/bin/env python3
"""Search for candidate tag bytes in the 'failure' region (after the known 0x15/0x12
grammar stops matching cleanly). For each byte value 0..255, look at its occurrences
in a given region and score how 'tag-like' it is: consistency of gaps (mode gap
frequency), and total occurrence count. We already confirmed 0x15 (17B) and 0x12 (9B)
work great in [78, ~900). This script looks at [REGION_START, end) to find what
(if anything) structures the rest of the file.
"""
import struct
from collections import Counter

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

def load(path):
    with open(path, "rb") as f:
        return f.read()

for name, path in FILES.items():
    data = load(path)
    print(f"=== {name} ===")
    for region_start, region_end, label in [(78, 1000, "early/structured"), (1400, len(data), "post-1400 region")]:
        print(f"--- region [{region_start},{region_end}) ({label}) ---")
        region = data[region_start:region_end]
        scores = []
        for b in range(256):
            positions = [i for i, x in enumerate(region) if x == b]
            if len(positions) < 5:
                continue
            gaps = [positions[i+1]-positions[i] for i in range(len(positions)-1)]
            gap_counter = Counter(gaps)
            mode_gap, mode_count = gap_counter.most_common(1)[0]
            consistency = mode_count / len(gaps) if gaps else 0
            scores.append((consistency, len(positions), b, mode_gap, mode_count))
        scores.sort(reverse=True)
        print(f"Top 15 candidate tag bytes by gap-consistency (min 5 occurrences):")
        for consistency, occ, b, mode_gap, mode_count in scores[:15]:
            print(f"  byte=0x{b:02x} occurrences={occ:4d} mode_gap={mode_gap:4d} "
                  f"mode_count={mode_count:3d} consistency={consistency:.2%}")
        print()
    print("=" * 80)
