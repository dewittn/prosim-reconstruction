#!/usr/bin/env python3
"""Round 2, Task 1: build the exact (identity -> f1, f2, V1, V2, tag, P1, P2) table
from both XTC files. Verify constancy of V1/V2/tag/P1/P2 per identity (keyed by f1,
per build_identity_labeler), and separately check whether f2 is actually constant
per identity (earlier brief assumed it was; raw data shows it may not be).
"""
import struct
import csv
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from map_common import FILES, load, body_walk, packed_chain_walk, build_identity_labeler

OUT_CSV = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/c2_constants.csv"


def read_varint(data, off):
    result = 0
    shift = 0
    start = off
    while True:
        b = data[off]
        result |= (b & 0x7F) << shift
        off += 1
        shift += 7
        if not (b & 0x80):
            break
    return result, off, data[start:off].hex()


def decode_head(payload):
    """payload[0] = n (marker byte), payload[1] = 0x0a, then varint V1, varint V2,
    then tag byte (0x86/0x87), then u16be P1, u16be P2."""
    if len(payload) < 2 or payload[1] != 0x0A:
        return None
    off = 2
    try:
        v1, off, v1_hex = read_varint(payload, off)
        v2, off, v2_hex = read_varint(payload, off)
        if off >= len(payload):
            return None
        tag = payload[off]
        off += 1
        if off + 4 > len(payload):
            return None
        p1 = struct.unpack_from(">H", payload, off)[0]
        p2 = struct.unpack_from(">H", payload, off + 2)[0]
        off += 4
        return {
            "v1": v1, "v1_hex": v1_hex, "v2": v2, "v2_hex": v2_hex,
            "tag": tag, "p1": p1, "p2": p2, "head_len": off,
        }
    except (IndexError, struct.error):
        return None


L = build_identity_labeler()

# per-identity accumulation: identity -> list of dicts (one per occurrence, across both files)
records = {}

for fkey in ("a", "b"):
    name, data = load(fkey)
    body, log_end = body_walk(data)
    packed = packed_chain_walk(data, log_end)
    packed_by_n = {p["n"]: p for p in packed}
    for idx, entry in enumerate(body):
        n = idx + 1
        ident = L(entry)
        if ident in ("SEP", "SENT"):
            continue
        p = packed_by_n.get(n)
        if p is None:
            continue
        head = decode_head(p["payload"])
        rec = {
            "file": name, "n": n, "identity": ident,
            "f1": entry["f1"], "f2": entry["f2"],
            "f3": entry["f3"], "f4": entry["f4"],
            "payload_size": p["size"],
        }
        if head:
            rec.update(head)
        else:
            rec.update({"v1": None, "v2": None, "tag": None, "p1": None, "p2": None, "head_len": None})
        records.setdefault(ident, []).append(rec)

# --- constancy check ---
print("=" * 100)
print("PER-IDENTITY CONSTANCY CHECK (V1, V2, tag, P1, P2, and f1/f2)")
print("=" * 100)

rows_out = []
for ident in sorted(records, key=lambda x: int(x[2:])):
    occs = records[ident]
    f1_set = sorted(set(round(o["f1"], 6) for o in occs))
    f2_set = sorted(set(round(o["f2"], 6) for o in occs))
    v1_set = sorted(set(o["v1"] for o in occs))
    v2_set = sorted(set(o["v2"] for o in occs))
    tag_set = sorted(set(o["tag"] for o in occs))
    p1_set = sorted(set(o["p1"] for o in occs))
    p2_set = sorted(set(o["p2"] for o in occs))
    n_occ = len(occs)
    files_seen = sorted(set(o["file"] for o in occs))

    print(f"\n{ident}: n_occurrences={n_occ} files={files_seen}")
    print(f"  f1: {f1_set}  {'CONSTANT' if len(f1_set) == 1 else 'VARIES!!'}")
    print(f"  f2: {f2_set}  {'CONSTANT' if len(f2_set) == 1 else 'VARIES!!'}")
    print(f"  V1: {v1_set}  {'CONSTANT' if len(v1_set) == 1 else 'VARIES!!'}")
    print(f"  V2: {v2_set}  {'CONSTANT' if len(v2_set) == 1 else 'VARIES!!'}")
    print(f"  tag: {[hex(t) if t is not None else None for t in tag_set]}  "
          f"{'CONSTANT' if len(tag_set) == 1 else 'VARIES!!'}")
    print(f"  P1: {[hex(p) for p in p1_set]}  {'CONSTANT' if len(p1_set) == 1 else 'VARIES!!'}")
    print(f"  P2: {[hex(p) for p in p2_set]}  {'CONSTANT' if len(p2_set) == 1 else 'VARIES!!'}")

    rows_out.append({
        "identity": ident,
        "n_occurrences": n_occ,
        "f1": f1_set[0] if len(f1_set) == 1 else "|".join(str(x) for x in f1_set),
        "f1_constant": len(f1_set) == 1,
        "f2": f2_set[0] if len(f2_set) == 1 else "|".join(str(x) for x in f2_set),
        "f2_constant": len(f2_set) == 1,
        "v1": v1_set[0] if len(v1_set) == 1 else "|".join(str(x) for x in v1_set),
        "v1_constant": len(v1_set) == 1,
        "v2": v2_set[0] if len(v2_set) == 1 else "|".join(str(x) for x in v2_set),
        "v2_constant": len(v2_set) == 1,
        "tag": hex(tag_set[0]) if len(tag_set) == 1 else "|".join(hex(t) for t in tag_set),
        "tag_constant": len(tag_set) == 1,
        "p1": hex(p1_set[0]) if len(p1_set) == 1 else "|".join(hex(p) for p in p1_set),
        "p1_constant": len(p1_set) == 1,
        "p2": hex(p2_set[0]) if len(p2_set) == 1 else "|".join(hex(p) for p in p2_set),
        "p2_constant": len(p2_set) == 1,
    })

with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
    w.writeheader()
    w.writerows(rows_out)
print(f"\n\nWrote {len(rows_out)} identity rows to {OUT_CSV}")

# --- full occurrence dump for identities where anything varies, for manual inspection ---
print("\n" + "=" * 100)
print("FULL OCCURRENCE DUMP (for any identity with a VARIES flag)")
print("=" * 100)
for ident in sorted(records, key=lambda x: int(x[2:])):
    occs = records[ident]
    v1_set = set(o["v1"] for o in occs)
    v2_set = set(o["v2"] for o in occs)
    tag_set = set(o["tag"] for o in occs)
    p1_set = set(o["p1"] for o in occs)
    p2_set = set(o["p2"] for o in occs)
    f2_set = set(round(o["f2"], 6) for o in occs)
    if len(v1_set) > 1 or len(v2_set) > 1 or len(tag_set) > 1 or len(p1_set) > 1 or len(p2_set) > 1 or len(f2_set) > 1:
        print(f"\n--- {ident} ---")
        for o in occs:
            print(f"  file={o['file']:14s} n={o['n']:3d} f1={o['f1']:.6f} f2={o['f2']:.6f} "
                  f"v1={o['v1']} v2={o['v2']} tag={hex(o['tag']) if o['tag'] is not None else None} "
                  f"p1={hex(o['p1']) if o['p1'] is not None else None} "
                  f"p2={hex(o['p2']) if o['p2'] is not None else None} "
                  f"payload_size={o['payload_size']} head_len={o['head_len']}")
