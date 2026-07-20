#!/usr/bin/env python3
"""Task 6 (precise): find the exact 0x0d _ 0x1a _ 0x09 _ 0x17 decoration run
immediately preceding each packed marker, and correlate with body structure."""
import sys, re
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from map_common import load, body_walk, packed_chain_walk, build_identity_labeler

L = build_identity_labeler()

# strict regex: 0d, any byte, 1a, any byte, 09, any byte, 17, any byte  (8 bytes total)
PATTERN = re.compile(rb"\x0d.\x1a.\x09.\x17.", re.DOTALL)

for fkey in ("a", "b"):
    name, data = load(fkey)
    body, log_end = body_walk(data)
    packed = packed_chain_walk(data, log_end)
    idents = [L(e) for e in body]
    sep_ns = set(i + 1 for i, e in enumerate(body) if e["tag"] == 0x12)

    print(f"\n=== {fkey} ({name}) ===")
    deco_ns = []
    for idx, p in enumerate(packed):
        n = p["n"]
        marker = p["marker_offset"]
        window = data[max(0, marker - 12):marker]  # bytes right before [n][0x0a]
        m = PATTERN.search(window)
        if m:
            deco_bytes = m.group()
            gap = marker - packed[idx - 1]["marker_offset"] if idx > 0 else None
            deco_ns.append(n)
            body_idx = n - 1
            ident = idents[body_idx] if body_idx < len(idents) else "?"
            is_sep_here = n in sep_ns
            is_sep_next = (n + 1) in sep_ns
            print(f"  n={n:3d} deco={deco_bytes.hex(' ')}  prev_gap={gap}  "
                  f"ident(n)={ident}  is_sep_n={is_sep_here} is_sep_n+1={is_sep_next}")
    print(f"  --> decorated n's: {deco_ns}  (count={len(deco_ns)})")
