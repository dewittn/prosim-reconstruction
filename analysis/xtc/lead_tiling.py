#!/usr/bin/env python3
"""Tile the XTC packed regions into repeated blocks + literal gaps.

Greedy maximal-match tiling: at each position in each packed region, find the
longest match (>= MINLEN) against anywhere else in EITHER file (excluding
self-overlap), preferring earlier occurrences as the canonical block.
Assign block IDs by canonical (file, offset, len) so recurrences share an ID.
"""
from pathlib import Path
from collections import defaultdict

BASE = Path("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data")
A_START, B_START = 912, 1355
MINLEN = 48
K = 24  # seed gram

a = BASE.joinpath("prosim.xtc").read_bytes()[A_START:]
b = BASE.joinpath("prosim1.xtc").read_bytes()[B_START:]
corpus = {"a": a, "b": b}

# index K-grams across both files
idx = defaultdict(list)
for name, d in corpus.items():
    for i in range(len(d) - K + 1):
        idx[d[i:i+K]].append((name, i))

def longest_match(name, j):
    """Longest match for corpus[name][j:] elsewhere (excluding overlapping self)."""
    d = corpus[name]
    gram = d[j:j+K]
    best = None
    for oname, oi in idx.get(gram, []):
        if oname == name and abs(oi - j) < MINLEN:
            continue
        od = corpus[oname]
        L = K
        while j + L < len(d) and oi + L < len(od) and d[j+L] == od[oi+L]:
            L += 1
        if best is None or L > best[2]:
            best = (oname, oi, L)
    return best

def tile(name):
    d = corpus[name]
    segs = []  # (start, len, kind, ref)  kind: 'R' repeat / 'L' literal
    j = 0
    lit_start = 0
    while j < len(d) - K + 1:
        m = longest_match(name, j)
        if m and m[2] >= MINLEN:
            if j > lit_start:
                segs.append((lit_start, j - lit_start, "L", None))
            segs.append((j, m[2], "R", (m[0], m[1])))
            j += m[2]
            lit_start = j
        else:
            j += 1
    if lit_start < len(d):
        segs.append((lit_start, len(d) - lit_start, "L", None))
    return segs

# canonical block ids: group repeats by content hash
import hashlib
def content_id(name, start, length):
    h = hashlib.sha1(corpus[name][start:start+length]).hexdigest()[:8]
    return h

for name, start_abs in (("a", A_START), ("b", B_START)):
    segs = tile(name)
    print(f"\n=== {name} packed region tiling ({len(corpus[name])} bytes, {len(segs)} segments) ===")
    lit_total = sum(s[1] for s in segs if s[2] == "L")
    rep_total = sum(s[1] for s in segs if s[2] == "R")
    print(f"literal bytes: {lit_total}  repeat bytes: {rep_total}")
    counts = defaultdict(int)
    for s in segs:
        if s[2] == "R":
            counts[content_id(name, s[0], s[1])] += 1
    for st, ln, kind, ref in segs:
        if kind == "R":
            cid = content_id(name, st, ln)
            print(f"  @{st+start_abs:6d} len={ln:5d} REPEAT block={cid} (seen {counts[cid]}x in {name})")
        else:
            head = corpus[name][st:st+16].hex()
            print(f"  @{st+start_abs:6d} len={ln:5d} literal  head={head}")
