#!/usr/bin/env python3
"""Greedy TLV parser for the structured record area using confirmed tags:
  0x15 -> 4 x float32 (17 bytes total: tag+16)
  0x12 -> 2 x float32 (9 bytes total: tag+8)
Starts right after the header (offset determined per-file) and walks forward,
consuming known tags. On an unrecognized byte, it records a parse failure and
tries a simple resync (advance 1 byte) so we can see how much of the file this
grammar explains and where it breaks down.
"""
import struct
from collections import Counter

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

# header lengths determined by manual walk (see grammar_header.py / grammar_context_dump.py)
HEADER_END = {
    "prosim.xtc": 78,   # tag 0x12 begins the body proper at 78 in our walk (see analysis)
    "prosim1.xtc": 78,
}

TAGS = {
    0x15: 16,  # payload bytes after tag
    0x12: 8,
}

def load(path):
    with open(path, "rb") as f:
        return f.read()

def f32(bs):
    return struct.unpack("<f", bs)[0]

for name, path in FILES.items():
    data = load(path)
    start = HEADER_END[name]
    print(f"=== {name}: parsing from offset {start} to {len(data)} ===")
    pos = start
    records = []
    failures = []
    while pos < len(data):
        tag = data[pos]
        if tag in TAGS:
            plen = TAGS[tag]
            if pos + 1 + plen > len(data):
                failures.append((pos, tag, "truncated"))
                break
            payload = data[pos+1:pos+1+plen]
            records.append((pos, tag, payload))
            pos += 1 + plen
        else:
            failures.append((pos, tag, "unknown tag"))
            pos += 1  # resync by 1 byte

    total_bytes = len(data) - start
    consumed = sum(1 + TAGS[t] for (_, t, _) in records)
    print(f"Records parsed: {len(records)}   Failure bytes (resync steps): {len(failures)}")
    print(f"Bytes accounted for by records: {consumed} / {total_bytes} = {100*consumed/total_bytes:.2f}%")

    tag_census = Counter(t for (_, t, _) in records)
    print(f"Tag census: {dict((hex(k), v) for k, v in tag_census.items())}")

    # sub-classify 0x15 records by float1/float2 pattern
    proficiency_like = 0
    constant28_like = 0
    other15 = 0
    for (p, t, payload) in records:
        if t == 0x15:
            f1, f2, f3, f4 = struct.unpack("<4f", payload)
            if 2.7 < f1 < 2.9 and 2.7 < f2 < 2.9:
                constant28_like += 1
            elif 0.55 < f1 < 1.1 and 0.45 < f2 < 0.75:
                proficiency_like += 1
            else:
                other15 += 1
    print(f"0x15 sub-classification: proficiency-like(f1 in [0.55,1.1], f2 in [0.45,0.75])={proficiency_like}, "
          f"constant~2.80 pair={constant28_like}, other={other15}")

    # where do failures cluster? print first 20 failure positions and surrounding bytes
    print(f"First 20 failure positions:")
    for (p, tag, reason) in failures[:20]:
        context = data[max(0,p-4):p+20]
        print(f"  pos={p:6d} byte=0x{tag:02x} reason={reason} context={' '.join(f'{b:02x}' for b in context)}")

    # find where failures start becoming dense (transition into unstructured/tail region)
    # compute density of failures in windows of 500 bytes
    print("\nFailure density per 1000-byte window (from start to end):")
    window = 1000
    fail_positions = [p for (p, t, r) in failures]
    for wstart in range(start, len(data), window):
        wend = min(wstart+window, len(data))
        cnt = sum(1 for p in fail_positions if wstart <= p < wend)
        print(f"  [{wstart:6d},{wend:6d}): failures={cnt}")

    print()
    print("=" * 80)
    print()
