#!/usr/bin/env python3
"""Tasks 2-6: separator-vs-operator size stats, payload<->identity match rate,
cross-file record-n comparison, per-identity change timelines, decoration catalog."""
import sys, struct, statistics
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from map_common import load, body_walk, packed_chain_walk, build_identity_labeler

L = build_identity_labeler()

state = {}
for fkey in ("a", "b"):
    name, data = load(fkey)
    body, log_end = body_walk(data)
    packed = packed_chain_walk(data, log_end)
    idents = [L(e) for e in body]
    state[fkey] = dict(name=name, data=data, body=body, log_end=log_end,
                        packed=packed, idents=idents,
                        packed_by_n={p["n"]: p for p in packed})

print("#" * 70)
print("TASK 2: separator-position vs operator-position packed record sizes")
print("#" * 70)
for fkey in ("a", "b"):
    s = state[fkey]
    sep_sizes = []
    op_sizes = []
    for idx, e in enumerate(s["body"]):
        n = idx + 1
        p = s["packed_by_n"].get(n)
        if p is None:
            continue
        (sep_sizes if e["tag"] == 0x12 else op_sizes).append(p["size"])
    print(f"\n-- {fkey} ({s['name']}) --")
    print(f"  operator-position sizes: n={len(op_sizes)} "
          f"mean={statistics.mean(op_sizes):.0f} median={statistics.median(op_sizes):.0f} "
          f"min={min(op_sizes)} max={max(op_sizes)}")
    print(f"  separator-position sizes: {sep_sizes}")

print()
print("#" * 70)
print("TASK 3: payload-sharing vs identity match rate")
print("#" * 70)
# group all packed records (both files) by payload sha1; check whether members
# of a group share the same body identity
from collections import defaultdict
groups = defaultdict(list)  # sha1 -> list of (fkey, n, identity)
for fkey in ("a", "b"):
    s = state[fkey]
    for idx, e in enumerate(s["body"]):
        n = idx + 1
        p = s["packed_by_n"].get(n)
        if p is None:
            continue
        groups[p["sha1_8"]].append((fkey, n, s["idents"][idx]))

multi = {h: v for h, v in groups.items() if len(v) > 1}
total_pairs = 0
match_pairs = 0
mismatched_examples = []
for h, members in multi.items():
    idents_here = set(m[2] for m in members)
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            total_pairs += 1
            if members[i][2] == members[j][2]:
                match_pairs += 1
            else:
                if len(mismatched_examples) < 15:
                    mismatched_examples.append((h, members[i], members[j]))

print(f"  distinct payload-sha1 groups (size>1): {len(multi)}")
print(f"  total same-payload pairs: {total_pairs}")
print(f"  pairs with matching identity: {match_pairs} "
      f"({100*match_pairs/total_pairs:.1f}%)" if total_pairs else "  (no repeated payloads)")
if mismatched_examples:
    print("  mismatched examples (sha1, (file,n,ident), (file,n,ident)):")
    for ex in mismatched_examples:
        print("   ", ex)

# also: are SEP-position payloads ever shared with each other or with operator payloads?
sep_hashes = defaultdict(list)
for h, members in groups.items():
    for fkey, n, ident in members:
        if ident == "SEP":
            sep_hashes[h].append((fkey, n))
print("\n  SEP payload sha1 groups:")
for h, members in groups.items():
    if any(ident == "SEP" for _, _, ident in members):
        print(f"   sha1={h} members={members}")

print()
print("#" * 70)
print("TASK 4: cross-file record-n comparison (file a n=1..49 vs file b n=1..49)")
print("#" * 70)
a, b = state["a"], state["b"]
equal_ns, diff_ns = [], []
for n in range(1, 50):
    pa = a["packed_by_n"].get(n)
    pb = b["packed_by_n"].get(n)
    if pa is None or pb is None:
        continue
    same = pa["sha1_8"] == pb["sha1_8"] and pa["payload"] == pb["payload"]
    (equal_ns if same else diff_ns).append(n)
print(f"  equal payloads:   {equal_ns}")
print(f"  different payloads: {diff_ns}")
print(f"  equal size ratio: {len(equal_ns)}/{len(equal_ns)+len(diff_ns)}")

print("\n  body floats a[n] vs b[n] (identity + f3/f4) for n=1..49:")
for n in range(1, 50):
    ea = a["body"][n-1]
    eb = b["body"][n-1]
    ida = a["idents"][n-1]
    idb = b["idents"][n-1]
    same_ident = ida == idb
    tagmatch = ea["tag"] == eb["tag"]
    flag = "" if (same_ident and tagmatch) else "  <-- IDENTITY/TAG MISMATCH"
    if ea["tag"] == 0x15 and eb["tag"] == 0x15:
        print(f"   n={n:2d} a_id={ida:5s} f3={ea['f3']:.1f} f4={ea['f4']:.1f}  |  "
              f"b_id={idb:5s} f3={eb['f3']:.1f} f4={eb['f4']:.1f}{flag}")
    else:
        print(f"   n={n:2d} a_tag={hex(ea['tag'])} id={ida:5s}  |  b_tag={hex(eb['tag'])} id={idb:5s}{flag}")

print()
print("#" * 70)
print("TASK 5: per-identity change timeline (within each file)")
print("#" * 70)
for fkey in ("a", "b"):
    s = state[fkey]
    print(f"\n-- {fkey} ({s['name']}) --")
    by_ident = defaultdict(list)
    for idx, e in enumerate(s["body"]):
        n = idx + 1
        ident = s["idents"][idx]
        if ident in ("SEP", "SENT"):
            continue
        p = s["packed_by_n"].get(n)
        by_ident[ident].append((n, p["sha1_8"] if p else None, p["size"] if p else None))
    for ident in sorted(by_ident):
        occ = by_ident[ident]
        changes = []
        for i in range(1, len(occ)):
            changes.append("=" if occ[i][1] == occ[i-1][1] else "CHANGE")
        seq = " ".join(f"n{n}({sha})" for n, sha, sz in occ)
        print(f"  {ident}: {seq}")
        print(f"        transitions: {changes}")

print()
print("#" * 70)
print("TASK 6: decoration byte catalog (oversized-gap positions)")
print("#" * 70)
CANDIDATE_NS = {
    "a": [2,7,14,23,32,37,38,46],
    "b": [52,53,58,63,68],
}
for fkey in ("a", "b"):
    s = state[fkey]
    data = s["data"]
    print(f"\n-- {fkey} ({s['name']}) --")
    for p in s["packed"]:
        n = p["n"]
        marker = p["marker_offset"]
        # look at bytes preceding the marker back to previous record's marker+its own single byte len? we scan back up to 24 bytes before marker
        lookback = 24
        start = max(0, marker - lookback)
        chunk = data[start:marker]
        # try to detect decoration: any of bytes 0x17, 0x0d, 0x1a, 0x09 present shortly before marker
        deco_flag = any(b in chunk[-16:] for b in (0x17, 0x0d, 0x1a, 0x09))
        gap_from_prev = None
        idx = s["packed"].index(p)
        if idx > 0:
            gap_from_prev = marker - s["packed"][idx-1]["marker_offset"]
        tagline = ""
        if deco_flag:
            tagline = "  DECO?"
        print(f"  n={n:3d} marker@{marker:6d} prev_gap={gap_from_prev} "
              f"preceding_bytes={chunk.hex(' ')}{tagline}")
