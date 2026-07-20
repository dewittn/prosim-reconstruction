#!/usr/bin/env python3
"""Task 1: re-derive body walk + packed chain walk for both files, sanity check
against the claims in the brief, and emit map_alignment.csv."""
import csv
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from map_common import FILES, load, body_walk, packed_chain_walk, build_identity_labeler

OUT_CSV = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/map_alignment.csv"

L = build_identity_labeler()

results = {}
for fkey in ("a", "b"):
    name, data = load(fkey)
    body, log_end = body_walk(data)
    packed_start = log_end
    packed = packed_chain_walk(data, packed_start)
    first_marker = packed[0]["marker_offset"] if packed else None
    last_n = packed[-1]["n"] if packed else 0
    print(f"=== {fkey} ({name}) ===")
    print(f"  body entries: {len(body)}  (log ends at offset {log_end})")
    print(f"  packed region: start={packed_start}  first_marker={first_marker}  "
          f"preamble_bytes={ (first_marker - packed_start) if first_marker else None }")
    print(f"  packed chain: n=1..{last_n}  ({len(packed)} records)")
    results[fkey] = {"name": name, "data": data, "body": body, "log_end": log_end,
                      "packed_start": packed_start, "packed": packed}

# sanity checks against brief
assert len(results["a"]["body"]) == 49, len(results["a"]["body"])
assert len(results["b"]["body"]) == 76, len(results["b"]["body"])
assert results["a"]["log_end"] == 912
assert results["b"]["log_end"] == 1355
assert results["a"]["packed"][0]["marker_offset"] == 1350
assert results["b"]["packed"][0]["marker_offset"] == 2111
assert results["a"]["packed"][-1]["n"] == 49
assert results["b"]["packed"][-1]["n"] == 76
print("\nAll brief sanity checks PASSED.")

# emit map_alignment.csv
rows = []
for fkey in ("a", "b"):
    r = results[fkey]
    body = r["body"]
    packed_by_n = {p["n"]: p for p in r["packed"]}
    for idx, entry in enumerate(body):
        n = idx + 1  # 1:1 hypothesis
        ident = L(entry)
        p = packed_by_n.get(n)
        rows.append({
            "file": r["name"],
            "n": n,
            "body_tag": hex(entry["tag"]),
            "f1": entry["f1"], "f2": entry["f2"],
            "f3": entry["f3"] if entry["f3"] is not None else "",
            "f4": entry["f4"] if entry["f4"] is not None else "",
            "identity": ident,
            "packed_offset": p["marker_offset"] if p else "",
            "packed_size": p["size"] if p else "",
            "packed_payload_sha1_8": p["sha1_8"] if p else "",
        })

with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["file", "n", "body_tag", "f1", "f2", "f3", "f4",
                                      "identity", "packed_offset", "packed_size",
                                      "packed_payload_sha1_8"])
    w.writeheader()
    w.writerows(rows)
print(f"\nWrote {len(rows)} rows to {OUT_CSV}")
