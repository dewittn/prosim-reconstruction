#!/usr/bin/env python3
"""Test hypothesis: packed payload content is a pure function of body-log identity (f1,f2),
NOT of the record's own f3/f4 accumulators. Build (f1,f2) -> {payload bytes} mapping across
both files and check for a clean many-to-one correspondence.
"""
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_anchor import FILES, parse_body, chain_walk, get_payloads
from collections import defaultdict

def main():
    id_to_payloads = defaultdict(set)
    id_to_records = defaultdict(list)
    payload_to_ids = defaultdict(set)
    for tag, cfg in FILES.items():
        data = open(cfg["path"], "rb").read()
        body = parse_body(data, cfg["body_start"], cfg["body_end"])
        markers = chain_walk(data, cfg["pk_start"], cfg["maxn"])
        payloads = get_payloads(data, markers, len(data))
        for (kind, fl), (n, payload) in zip(body, payloads):
            if kind != "15":
                continue
            f1, f2, f3, f4 = fl
            key = (round(f1, 6), round(f2, 6))
            id_to_payloads[key].add(bytes(payload))
            id_to_records[key].append((tag, n, f3, f4, len(payload)))
            payload_to_ids[bytes(payload)].add(key)

    print(f"distinct (f1,f2) identities: {len(id_to_payloads)}")
    print()
    clean = 0
    dirty = 0
    for key, payset in sorted(id_to_payloads.items()):
        recs = id_to_records[key]
        if len(payset) == 1:
            clean += 1
            status = "CLEAN (1 payload)"
        else:
            dirty += 1
            status = f"MIXED ({len(payset)} distinct payloads)"
        lens = sorted(set(len(p) for p in payset))
        print(f"  id={key}  n_records={len(recs):2d}  {status}  payload_lens={lens}")
        for tag, n, f3, f4, plen in sorted(recs, key=lambda r: r[4]):
            print(f"      {tag} n={n:3d} f3={f3:10.2f} f4={f4:10.2f} len={plen}")
    print(f"\nclean identities: {clean}, mixed identities: {dirty}")

    print()
    print("payload -> identity count (checking payload uniquely determines identity):")
    multi_id_payloads = {p: ids for p, ids in payload_to_ids.items() if len(ids) > 1}
    print(f"  payloads shared by >1 identity: {len(multi_id_payloads)} / {len(payload_to_ids)}")
    for p, ids in list(multi_id_payloads.items())[:5]:
        print(f"    len={len(p)} ids={ids}")

if __name__ == "__main__":
    main()
