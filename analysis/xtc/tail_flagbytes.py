#!/usr/bin/env python3
"""Test the LZ-control-byte hypothesis suggested by visual inspection: bytes like
0x82/0x83/0x84/0x85 followed by 0xf8/0xfc/0xfe/0xf0/0xe8 recur throughout the tail.
Characterize spacing between high-byte (>=0x80) tokens and check for a 15-17 byte
cadence (matching the float-record stride and the lag-9/14 autocorrelation signal)."""
from collections import Counter

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}
with open(FILES["prosim.xtc"], "rb") as f:
    d0 = f.read()
with open(FILES["prosim1.xtc"], "rb") as f:
    d1 = f.read()

for name, data, tail_start in [("prosim.xtc", d0, 895), ("prosim1.xtc", d1, 1338)]:
    tail = data[tail_start:]
    print(f"\n=== {name} tail (len={len(tail)}) ===")
    # candidate "control bytes": 0x82-0x85 (low nibble structure), followed 2 bytes later by 0xf0/0xf8/0xfc/0xfe
    positions = [i for i in range(len(tail)-1) if 0x82 <= tail[i] <= 0x85]
    print(f"Bytes in [0x82,0x85]: {len(positions)} occurrences, density 1 per {len(tail)/max(1,len(positions)):.1f} bytes")
    gaps = [positions[i+1]-positions[i] for i in range(len(positions)-1)]
    gc = Counter(gaps)
    print(f"Top 15 gaps between successive 0x82-0x85 bytes: {gc.most_common(15)}")

    # what's the byte 2 positions later, for these candidate control bytes?
    followers = Counter()
    for p in positions:
        if p+2 < len(tail):
            followers[tail[p+2]] += 1
    print(f"Byte 2 positions after 0x82-0x85 (top 10): {followers.most_common(10)}")

    # overall high-bit-set byte density and gap structure
    hi = [i for i in range(len(tail)) if tail[i] >= 0x80]
    print(f"Bytes >=0x80: {len(hi)} of {len(tail)} ({100*len(hi)/len(tail):.1f}%, random expectation 50%)")
    hgaps = [hi[i+1]-hi[i] for i in range(len(hi)-1)]
    hgc = Counter(hgaps)
    print(f"Top 10 gaps between successive high-bit bytes: {hgc.most_common(10)}")
