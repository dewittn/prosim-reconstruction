#!/usr/bin/env python3
"""Dedup payloads across both files; print distinct payloads grouped by size,
with which (file,n) they occurred at."""
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_anchor import FILES, parse_body, chain_walk, get_payloads
from collections import defaultdict

def main():
    groups = defaultdict(list)  # payload bytes -> list of (file, n)
    all_payloads = {}
    for tag, cfg in FILES.items():
        data = open(cfg["path"], "rb").read()
        markers = chain_walk(data, cfg["pk_start"], cfg["maxn"])
        payloads = get_payloads(data, markers, len(data))
        all_payloads[tag] = payloads
        for n, payload in payloads:
            groups[bytes(payload)].append((tag, n))

    print(f"total records: {sum(len(v) for v in groups.values())}, distinct payloads: {len(groups)}")
    # sort by size then first occurrence
    items = sorted(groups.items(), key=lambda kv: (len(kv[0]), kv[1][0]))
    for i, (payload, occ) in enumerate(items):
        print(f"[{i:2d}] len={len(payload):4d} count={len(occ):2d} occurs={occ[:6]}{'...' if len(occ)>6 else ''}")

if __name__ == "__main__":
    main()
