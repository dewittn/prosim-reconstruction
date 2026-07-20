#!/usr/bin/env python3
"""Task 6: find shared substrings >=16 bytes between the two tail regions, and pin down
the exact shared block spotted visually near the end of both files."""

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

with open(FILES["prosim.xtc"], "rb") as f:
    d0 = f.read()
with open(FILES["prosim1.xtc"], "rb") as f:
    d1 = f.read()

TAIL0_START = 895  # last 0x15 float-record hit in prosim.xtc
TAIL1_START = 1338  # last 0x15 float-record hit in prosim1.xtc

t0 = d0[TAIL0_START:]
t1 = d1[TAIL1_START:]

# Build a set of all 16-byte substrings of t1 -> positions
K = 16
index1 = {}
for i in range(len(t1) - K + 1):
    index1.setdefault(t1[i:i+K], []).append(i)

matches = []
i = 0
while i < len(t0) - K + 1:
    key = t0[i:i+K]
    if key in index1:
        # extend match as far as possible
        for j in index1[key]:
            L = K
            while i + L < len(t0) and j + L < len(t1) and t0[i+L] == t1[j+L]:
                L += 1
            matches.append((i, j, L))
        i += K  # skip ahead a bit to avoid too much overlap spam
    else:
        i += 1

# dedupe/merge: keep longest matches, sort by length desc
matches.sort(key=lambda m: -m[2])
print(f"Found {len(matches)} raw match seeds (>=16 bytes). Top 20 by length:")
seen_ranges = []
count = 0
for (i, j, L) in matches:
    # skip if fully contained in an already reported (i,j) region
    contained = any(i >= si and i + L <= si + sl and j - i == sj - si for (si, sj, sl) in seen_ranges)
    if contained:
        continue
    seen_ranges.append((i, j, L))
    abs0 = TAIL0_START + i
    abs1 = TAIL1_START + j
    print(f"  len={L:4d}  prosim.xtc[{abs0}:{abs0+L}]  <->  prosim1.xtc[{abs1}:{abs1+L}]")
    print(f"       bytes: {t0[i:i+min(L,40)].hex()}{'...' if L>40 else ''}")
    count += 1
    if count >= 20:
        break

print()
print(f"prosim.xtc length: {len(d0)}, tail from {TAIL0_START} is {len(t0)} bytes")
print(f"prosim1.xtc length: {len(d1)}, tail from {TAIL1_START} is {len(t1)} bytes")
print(f"prosim.xtc tail ends at absolute offset {len(d0)}")
print(f"prosim1.xtc tail ends at absolute offset {len(d1)}")

# Also check distance from end of file for the biggest match
if seen_ranges:
    seen_ranges.sort(key=lambda m: -m[2])
    i, j, L = seen_ranges[0]
    abs0 = TAIL0_START + i
    abs1 = TAIL1_START + j
    print()
    print(f"Longest match: {L} bytes")
    print(f"  In prosim.xtc: offset {abs0}-{abs0+L}, that's {len(d0)-(abs0+L)} bytes before EOF, {abs0} bytes from start of file")
    print(f"  In prosim1.xtc: offset {abs1}-{abs1+L}, that's {len(d1)-(abs1+L)} bytes before EOF, {abs1} bytes from start of file")
    print(f"  Full matching bytes: {t0[i:i+L].hex()}")
