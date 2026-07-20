#!/usr/bin/env python3
"""Analyze the clean structured-region records: group 0x15 records by their
(float1,float2) 'identity' pair, count occurrences per identity, and see how
0x12 records partition the sequence into blocks. Correlate against known
quantities: 9 vs 13 operators, weeks (9 vs 13), 3 products."""
import struct
from collections import Counter, defaultdict, OrderedDict

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

HEADER_END = 78
TAGS = {0x15: 16, 0x12: 8}

def load(path):
    with open(path, "rb") as f:
        return f.read()

def round_pair(f1, f2, nd=3):
    return (round(f1, nd), round(f2, nd))

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

    print(f"=== {name}: {len(records)} records in [{HEADER_END},{boundary}) ===")

    # Identify blocks separated by 0x12 records
    blocks = []
    cur_block = []
    for (p, t, payload) in records:
        if t == 0x12:
            if cur_block:
                blocks.append(cur_block)
            cur_block = []
            f1, f2 = struct.unpack("<2f", payload)
            print(f"  [0x12 separator @ {p}: ({f1:.4f}, {f2:.4f})]")
        else:
            f1, f2, f3, f4 = struct.unpack("<4f", payload)
            cur_block.append((p, f1, f2, f3, f4))
    if cur_block:
        blocks.append(cur_block)

    print(f"\nNumber of 0x15-blocks between/after 0x12 separators: {len(blocks)}")
    for bi, block in enumerate(blocks):
        pairs = Counter(round_pair(f1, f2) for (p, f1, f2, f3, f4) in block)
        print(f"\n  Block {bi}: {len(block)} records, {len(pairs)} distinct (f1,f2) identities")
        for pair, cnt in sorted(pairs.items(), key=lambda kv: -kv[1]):
            print(f"    identity {pair}: {cnt} occurrence(s)")

    # Global identity census across ALL 0x15 records (ignoring block boundaries)
    all15 = [(p, f1, f2, f3, f4) for (p, t, payload) in records if t == 0x15
             for f1, f2, f3, f4 in [struct.unpack("<4f", payload)]]
    global_pairs = Counter(round_pair(f1, f2) for (p, f1, f2, f3, f4) in all15)
    print(f"\nGlobal distinct (f1,f2) identities across all 0x15 records: {len(global_pairs)}")
    for pair, cnt in sorted(global_pairs.items(), key=lambda kv: -kv[1]):
        print(f"    identity {pair}: {cnt} occurrence(s)")

    print()
    print("=" * 100)
    print()
