#!/usr/bin/env python3
"""Task 1: Find where 0x15-tagged float records stop, in both files."""
import struct

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

def is_plausible_float(b4):
    try:
        v = struct.unpack("<f", b4)[0]
    except struct.error:
        return False
    if v != v:  # NaN
        return False
    av = abs(v)
    if av == 0:
        return True
    return 1e-6 <= av <= 1e8

def scan_015_records(data):
    """Find all offsets where byte==0x15 followed by 4 plausible float32s (16 bytes total: 1 tag + 4*4? or just 4 floats)."""
    hits = []
    n = len(data)
    i = 0
    while i < n - 17:
        if data[i] == 0x15:
            floats = []
            ok = True
            for k in range(4):
                off = i + 1 + k * 4
                b4 = data[off:off+4]
                if len(b4) < 4 or not is_plausible_float(b4):
                    ok = False
                    break
                floats.append(struct.unpack("<f", b4)[0])
            if ok:
                hits.append((i, floats))
        i += 1
    return hits

for name, path in FILES.items():
    with open(path, "rb") as f:
        data = f.read()
    print(f"=== {name} (size={len(data)}) ===")
    hits = scan_015_records(data)
    print(f"Total 0x15+4-float hits: {len(hits)}")
    if hits:
        # find contiguous run structure: print offsets and gaps
        offsets = [h[0] for h in hits]
        print("First 5 hits:", offsets[:5])
        print("Last 5 hits:", offsets[-5:])
        # find largest gap to identify end of dense record region
        gaps = [(offsets[i+1] - offsets[i], offsets[i], offsets[i+1]) for i in range(len(offsets)-1)]
        gaps.sort(reverse=True)
        print("Top 10 largest gaps between consecutive 0x15 hits (gap, start_offset, next_offset):")
        for g in gaps[:10]:
            print("  ", g)
        # typical record stride (mode of small gaps)
        from collections import Counter
        c = Counter(g[0] for g in gaps)
        print("Most common gaps:", c.most_common(10))
        print(f"Last hit offset: {offsets[-1]}, file size: {len(data)}, tail after last hit: {len(data) - offsets[-1]}")
    print()
