#!/usr/bin/env python3
"""Follow-up: (a) find ALL occurrences of the 414-byte repeating block within each file
and across files (not just top-20 truncated list), (b) verify+extend the ~66-byte
near-EOF shared block precisely, (c) check for a larger periodic structure (per-week
record size) via autocorrelation at large lags."""

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}
with open(FILES["prosim.xtc"], "rb") as f:
    d0 = f.read()
with open(FILES["prosim1.xtc"], "rb") as f:
    d1 = f.read()

# (a) all occurrences of the specific 414-byte block within each file
block = d0[3243:3657]
print(f"Block length: {len(block)}")

def find_all(hay, needle):
    out = []
    start = 0
    while True:
        idx = hay.find(needle, start)
        if idx == -1:
            break
        out.append(idx)
        start = idx + 1
    return out

occ0 = find_all(d0, block)
occ1 = find_all(d1, block)
print(f"Occurrences of the 414-byte block in prosim.xtc: {occ0}")
print(f"Occurrences of the 414-byte block in prosim1.xtc: {occ1}")

# is the block itself internally repetitive (smaller period)?
# check autocorrelation of the block against itself at small shifts
print("\nBlock self-similarity (does the 414B block have an internal repeat period?):")
for period in range(1, 60):
    matches = sum(1 for i in range(len(block) - period) if block[i] == block[i+period])
    total = len(block) - period
    if matches / total > 0.3:
        print(f"  period={period}: match rate={matches/total:.3f}")

# (b) exact ~66 byte near-EOF shared block: extend match precisely
# visually spotted around prosim.xtc offset ~18371 vs prosim1.xtc ~28912
a_start_guess = 18323
b_start_guess = 28896  # from hexdump we found "54 ad 1e 8f a3" starting here roughly
# search precisely: find the substring "54 ad 1e 8f a3 d1 f4 92 4a 8f 47 d3 69 bc b2 5b" in both
needle = bytes.fromhex("54ad1e8fa3d1f4924a8f47d369bcb25b")
i0 = d0.find(needle)
i1 = d1.find(needle)
print(f"\nAnchor 16-byte needle found at prosim.xtc offset {i0}, prosim1.xtc offset {i1}")
if i0 != -1 and i1 != -1:
    L = 16
    while i0+L < len(d0) and i1+L < len(d1) and d0[i0+L] == d1[i1+L]:
        L += 1
    print(f"Extended exact match length from anchor: {L} bytes")
    print(f"  prosim.xtc[{i0}:{i0+L}] = {d0[i0:i0+L].hex()}")
    print(f"  Ends {len(d0)-(i0+L)} bytes before EOF of prosim.xtc (file len {len(d0)})")
    print(f"  Ends {len(d1)-(i1+L)} bytes before EOF of prosim1.xtc (file len {len(d1)})")
    print(f"  Next 40 bytes after match in prosim.xtc: {d0[i0+L:i0+L+40].hex()}")
    print(f"  Next 40 bytes after match in prosim1.xtc: {d1[i1+L:i1+L+40].hex()}")
    # also check bytes BEFORE the anchor for how far back the match extends
    L2 = 0
    while i0-L2-1 >= 0 and i1-L2-1 >= 0 and d0[i0-L2-1] == d1[i1-L2-1]:
        L2 += 1
    print(f"  Match extends backward {L2} bytes before anchor too")
    print(f"  Full match: prosim.xtc[{i0-L2}:{i0+L}] <-> prosim1.xtc[{i1-L2}:{i1+L}], total length {L+L2}")
    print(f"  Bytes: {d0[i0-L2:i0+L].hex()}")
