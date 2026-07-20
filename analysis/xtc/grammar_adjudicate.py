#!/usr/bin/env python3
"""Adjudicate conflicting claims about the 0x15 record table by doing an
exact, no-shortcuts byte walk from offset 87, reporting every tag, every gap,
and flagging any byte that is NOT 0x15 or 0x12 as a potential 'other tag'."""
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
    print(f"=== {name} (size {len(data)}) ===")
    pos = 87  # first confirmed 0x15 record start
    record_log = []  # (offset, tag, ok)
    while True:
        if pos >= len(data):
            print(f"  Reached EOF at {pos}")
            break
        tag = data[pos]
        if tag == 0x15:
            if pos + 17 > len(data):
                print(f"  0x15 at {pos} truncated at EOF")
                break
            record_log.append((pos, 0x15))
            pos += 17
        elif tag == 0x12:
            if pos + 9 > len(data):
                print(f"  0x12 at {pos} truncated at EOF")
                break
            record_log.append((pos, 0x12))
            pos += 9
        else:
            print(f"  STOP: byte 0x{tag:02x} at offset {pos} is neither 0x15 nor 0x12 -- structured walk ends here")
            break

    tag_counts = Counter(t for (_, t) in record_log)
    n15 = tag_counts.get(0x15, 0)
    n12 = tag_counts.get(0x12, 0)
    print(f"  Total records walked: {len(record_log)}  (0x15={n15}, 0x12={n12})")
    print(f"  First record offset: {record_log[0][0]}  Last record offset: {record_log[-1][0]}")
    last_off, last_tag = record_log[-1]
    end_offset = last_off + (17 if last_tag == 0x15 else 9)
    print(f"  Structured region ends at offset {end_offset} (byte immediately after last record)")

    # Print the full ordered tag sequence with offsets, and explicitly mark gaps
    # between consecutive entries (should always be 17 or 9 by construction, so
    # instead report the position of every 0x12 relative to surrounding 0x15 runs).
    print(f"  Ordered tag sequence (offset:tag):")
    seq_str = " ".join(f"{off}:{'15' if t==0x15 else '12'}" for off, t in record_log)
    print(f"    {seq_str}")

    # Identify runs of consecutive 0x15 and where 0x12 interrupts them
    print(f"  Run breakdown (0x15-run length, then interrupting 0x12 offset if any):")
    i = 0
    run_lengths = []
    while i < len(record_log):
        off, t = record_log[i]
        if t == 0x15:
            run_start = i
            while i < len(record_log) and record_log[i][1] == 0x15:
                i += 1
            run = record_log[run_start:i]
            run_lengths.append(len(run))
            print(f"    0x15 run: {len(run)} records, offsets {run[0][0]}..{run[-1][0]}")
        else:
            print(f"    0x12 separator at offset {off}")
            i += 1
    print(f"  0x15 run lengths in order: {run_lengths}  sum={sum(run_lengths)}")
    print()

    # Explicit gap-of-26 check: for each pair of consecutive 0x15 occurrences across
    # the WHOLE tag sequence (including jumping over a 0x12), report the raw offset delta.
    all15_offsets = [off for off, t in record_log if t == 0x15]
    gaps26 = []
    for a, b in zip(all15_offsets, all15_offsets[1:]):
        if b - a != 17:
            gaps26.append((a, b, b - a))
    print(f"  Non-17 gaps between consecutive 0x15 records: {gaps26}")
    print()
    print("=" * 100)
    print()
