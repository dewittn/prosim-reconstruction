#!/usr/bin/env python3
"""Parse ONLY the clean structured region (from header end until the first
resync failure) using tags 0x15 (17B: tag+4 floats) and 0x12 (9B: tag+2 floats).
Report exact boundary, full record list with decoded floats, tag census, and
classification of 0x15 records by float1/float2 pattern.
"""
import struct
from collections import Counter

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

HEADER_END = 78
TAGS = {0x15: 16, 0x12: 8}

def load(path):
    with open(path, "rb") as f:
        return f.read()

for name, path in FILES.items():
    data = load(path)
    pos = HEADER_END
    records = []
    while pos < len(data):
        tag = data[pos]
        if tag not in TAGS:
            break
        plen = TAGS[tag]
        if pos + 1 + plen > len(data):
            break
        payload = data[pos+1:pos+1+plen]
        records.append((pos, tag, payload))
        pos += 1 + plen
    boundary = pos
    print(f"=== {name}: clean structured region {HEADER_END} .. {boundary} (len {boundary-HEADER_END}), "
          f"file size {len(data)}, structured = {100*(boundary)/len(data):.2f}% of file ===")
    print(f"Total clean records: {len(records)}")
    tag_census = Counter(t for (_, t, _) in records)
    print(f"Tag census: 0x15={tag_census.get(0x15,0)}  0x12={tag_census.get(0x12,0)}")
    print()

    print("Full record dump with decoded floats:")
    for (p, t, payload) in records:
        n = len(payload) // 4
        floats = struct.unpack(f"<{n}f", payload)
        floats_str = ", ".join(f"{v:.4f}" for v in floats)
        print(f"  off={p:6d} tag=0x{t:02x} floats=[{floats_str}]")
    print()
    print("=" * 100)
    print()
