#!/usr/bin/env python3
"""Dump wider context around specific offsets to resolve ambiguous record boundaries."""
import struct

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

def load(path):
    with open(path, "rb") as f:
        return f.read()

def hx(b):
    return " ".join(f"{x:02x}" for x in b)

def dump(data, start, length, label):
    print(f"{label} @ {start} (len {length}):")
    chunk = data[start:start+length]
    for i in range(0, len(chunk), 16):
        row = chunk[i:i+16]
        print(f"  {start+i:6d}: {hx(row)}")
    print()

data9 = load(FILES["prosim.xtc"])
data13 = load(FILES["prosim1.xtc"])

# gap13 case at pos=223 in prosim.xtc: dump 40 bytes from 220
dump(data9, 215, 60, "prosim.xtc around pos=223 (gap13 case)")
# next one at pos=376
dump(data9, 370, 60, "prosim.xtc around pos=376 (gap13 case)")

# gap7 at pos=172
dump(data9, 165, 40, "prosim.xtc around pos=172 (gap7 case)")

# gap10 at pos=179
dump(data9, 175, 40, "prosim.xtc around pos=179 (gap10 case)")

# gap4 at pos=236
dump(data9, 225, 40, "prosim.xtc around pos=236 (gap4 case)")

# gap26 in prosim1 at 818
dump(data13, 810, 60, "prosim1.xtc around pos=818 (gap26 case)")

# a clean run of gap=17 x N (from gap histogram, e.g. positions in prosim.xtc where 0x15 spaced by 17 repeatedly) -
# let's find a run programmatically
positions = [i for i, b in enumerate(data9) if b == 0x15 and i >= 87]
run_start = None
best_run = []
cur_run = [positions[0]]
for i in range(1, len(positions)):
    if positions[i] - positions[i-1] == 17:
        cur_run.append(positions[i])
    else:
        if len(cur_run) > len(best_run):
            best_run = cur_run
        cur_run = [positions[i]]
if len(cur_run) > len(best_run):
    best_run = cur_run
print(f"Longest run of consecutive 17-byte-spaced 0x15 tags in prosim.xtc: {len(best_run)} records starting at {best_run[0] if best_run else None}")
if best_run:
    dump(data9, best_run[0], min(17*6, len(data9)-best_run[0]), f"prosim.xtc 17-byte run starting at {best_run[0]}")
