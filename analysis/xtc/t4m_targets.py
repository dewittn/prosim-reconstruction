#!/usr/bin/env python3
"""Build the known-plaintext target list: per-record own floats (f1-f4), per-record
f3 deltas vs. the previous same-identity record, per-identity V1/V2 constants, and
global constants (sentinel, week numbers, rates/hours). Aligns body-log entries 1:1
with packed-chain records (index i <-> marker n=i+1), per the established mapping.
"""
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from map_common import load, body_walk, packed_chain_walk

IDENTITY_ROWS = [
    dict(identity="ID01", f1=0.8508557677268982, f2=0.6103542447090149, v1=410, v2=327),
    dict(identity="ID02", f1=0.8074246048927307, f2=0.5699745416641235, v1=165, v2=141),
    dict(identity="ID03a", f1=0.818823516368866, f2=0.5833333134651184, v1=304, v2=212),
    dict(identity="ID03b", f1=0.818823516368866, f2=0.5490196347236633, v1=336, v2=388),
    dict(identity="ID04", f1=0.6397058963775635, f2=0.6637036800384521, v1=228, v2=178),
    dict(identity="ID05", f1=0.8093023300170898, f2=0.5586034655570984, v1=303, v2=320),
    dict(identity="ID06", f1=0.7750557065010071, f2=0.6170799136161804, v1=373, v2=383),
    dict(identity="ID07", f1=0.9666666388511658, f2=0.5941644310951233, v1=282, v2=196),
    dict(identity="ID09", f1=0.9086161851882935, f2=0.5551425218582153, v1=264, v2=239),
    dict(identity="ID08", f1=1.03125, f2=0.6777609586715698, v1=111, v2=114),
    dict(identity="ID10", f1=1.0192307233810425, f2=1.0144927501678467, v1=85, v2=135),
]

GLOBAL_CONSTS = {
    "sentinel_a": 2.80045,
    "sentinel_b": 2.80042,
    "week9": 9,
    "week13": 13,
    "rate40": 40,
    "rate60": 60,
}

KNOWN_F3_DELTAS = [416, 479, 487, 295, 539, 484, 468, 436, 354, 546, 469, 467, 386, 515]


def match_identity(f1, f2, tol=1e-6):
    for row in IDENTITY_ROWS:
        if abs(row["f1"] - f1) < tol and abs(row["f2"] - f2) < tol:
            return row
    return None


def build_records(fkey):
    """Returns (name, data, records) where each record dict has:
    idx, marker_n, payload (bytes), payload_start, payload_end,
    tag (0x15/0x12), f1,f2,f3,f4 (f3/f4 None for 0x12), identity_row (or None),
    f3_delta (float or None, vs previous record sharing this identity in this file)
    """
    name, data = load(fkey)
    body_entries, body_end = body_walk(data)
    packed = packed_chain_walk(data, body_end)
    n = min(len(body_entries), len(packed))
    last_f3 = {}
    records = []
    for i in range(n):
        be = body_entries[i]
        pk = packed[i]
        ident = None
        f3_delta = None
        if be["tag"] == 0x15:
            ident = match_identity(be["f1"], be["f2"])
            key = (round(be["f1"], 6), round(be["f2"], 6))
            if key in last_f3:
                f3_delta = be["f3"] - last_f3[key]
            last_f3[key] = be["f3"]
        rec = dict(
            idx=i, marker_n=pk["n"], payload=pk["payload"],
            payload_start=pk["payload_start"], payload_end=pk["payload_end"],
            tag=be["tag"], f1=be["f1"], f2=be["f2"], f3=be.get("f3"), f4=be.get("f4"),
            identity_row=ident, f3_delta=f3_delta,
        )
        records.append(rec)
    return name, data, records, len(body_entries), len(packed)


if __name__ == "__main__":
    for fkey in ("a", "b"):
        name, data, records, n_body, n_packed = build_records(fkey)
        print(f"=== {fkey} ({name}) === body_entries={n_body} packed_records={n_packed} aligned={len(records)}")
        n_15 = sum(1 for r in records if r["tag"] == 0x15)
        n_12 = sum(1 for r in records if r["tag"] == 0x12)
        n_ident = sum(1 for r in records if r["identity_row"] is not None)
        n_delta = sum(1 for r in records if r["f3_delta"] is not None)
        print(f"  tag15={n_15} tag12={n_12} identity_matched={n_ident} f3_delta_available={n_delta}")
        sizes = sorted(set(len(r["payload"]) for r in records))
        print(f"  payload size range: {sizes[0]}-{sizes[-1]}")
        # sanity print first few
        for r in records[:3]:
            print(f"  idx={r['idx']} n={r['marker_n']} tag=0x{r['tag']:02x} f1={r['f1']} f2={r['f2']} "
                  f"f3={r['f3']} f4={r['f4']} ident={r['identity_row']['identity'] if r['identity_row'] else None} "
                  f"f3_delta={r['f3_delta']} paylen={len(r['payload'])}")
