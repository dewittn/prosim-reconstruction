#!/usr/bin/env python3
"""Known-plaintext transform hunt over XTC packed-payload interiors.

For each of RAW / XOR(1..255) / nibble-swap / bit-reverse / delta-decode /
high-bit-strip / base-128-VLQ, search for encodings of known plaintext values
(own-record f1..f4, f3 deltas, per-identity V1/V2, and global constants) inside
each record's packed payload. Reports structurally-consistent finds (same
relative offset recurring across multiple records) vs. chance expectation.
"""
import sys
import json
import math
from collections import defaultdict

sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
import t4m_lib as L
from t4m_targets import build_records, GLOBAL_CONSTS, IDENTITY_ROWS

REPORT_PATH = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/t4m_hits.csv"


# ---------------- core encoding variant builder (the "6 encodings") ----------------
def encode_float_variants(v, include_bcd_int=True):
    """All variants for a float-ish known value v."""
    out = {}
    e32 = L.mbf32_encode(v)
    if e32:
        out["mbf32"] = e32
    e64 = L.mbf64_encode(v)
    if e64:
        out["mbf64"] = e64
    ec = L.vb_currency_encode(v)
    if ec:
        out["vbcurrency"] = ec
    out.update(L.scaled_int_variants(v))
    out.update(L.fixed_point_variants(v))
    if include_bcd_int:
        iv = int(round(v))
        if abs(iv - v) / max(abs(v), 1e-9) < 0.02 and iv >= 0:
            for k2, v2 in L.bcd_variants(iv).items():
                out[k2] = v2
    return out


def encode_int_variants(v):
    """Variants for a known-integer value (V1/V2, weeks, rates)."""
    out = encode_float_variants(float(v), include_bcd_int=True)
    return out


# ---------------- generic search over one buffer with one set of variants ----------------
def search_variants(buf, variants):
    """Return {variant_name: [offsets]} for hits of each pattern in buf."""
    hits = {}
    for name, pat in variants.items():
        if not pat:
            continue
        offs = L.find_all(buf, pat)
        if offs:
            hits[name] = (offs, len(pat))
    return hits


def apply_pattern_transform(pat, transform, k=None):
    if transform == "raw":
        return pat
    if transform == "xor":
        return L.xor_bytes(pat, k)
    if transform == "nibble_swap":
        return L.nibble_swap(pat)
    if transform == "bit_reverse":
        return L.bit_reverse(pat)
    return pat


def apply_data_transform(data, transform):
    if transform == "delta_decode":
        return L.delta_decode(data)
    return data


PATTERN_SIDE_TRANSFORMS = ["raw", "xor", "nibble_swap", "bit_reverse"]
DATA_SIDE_TRANSFORMS = ["delta_decode"]


def main():
    all_records = {}
    blobs = {}
    for fkey in ("a", "b"):
        name, data, records, n_body, n_packed = build_records(fkey)
        all_records[fkey] = records
        blob_start = records[0]["payload_start"]
        blob_end = records[-1]["payload_end"]
        blobs[fkey] = data[blob_start:blob_end]
        print(f"[{fkey}] {name}: {len(records)} records aligned, packed blob len={len(blobs[fkey])}")

    # rows: transform, k, file, value_type, scope, variant, patlen, n_records_hit, mode_offset, mode_count, detail
    rows = []

    # ============ PART 1: own-record values (f1,f2,f3,f4, f3_delta) ============
    # Precompute base (untransformed) patterns ONCE per (record, field, variant); the
    # per-k XOR only re-XORs the tiny pattern bytes, not the whole payload/variant set.
    for fkey, records in all_records.items():
        base = []  # (record_idx, payload, fname, {vname: base_pattern})
        n_available = defaultdict(int)
        for r in records:
            if r["tag"] != 0x15:
                continue
            field_vals = {"f1": r["f1"], "f2": r["f2"], "f3": r["f3"], "f4": r["f4"]}
            if r["f3_delta"] is not None:
                field_vals["f3_delta"] = r["f3_delta"]
            for fname, fval in field_vals.items():
                n_available[fname] += 1
                variants = encode_float_variants(fval, include_bcd_int=(fname in ("f3", "f4", "f3_delta")))
                base.append((r["idx"], r["payload"], fname, variants))

        for pattern_transform in PATTERN_SIDE_TRANSFORMS:
            xor_range = range(1, 256) if pattern_transform == "xor" else [None]
            for k in xor_range:
                agg = defaultdict(list)
                for ridx, payload, fname, variants in base:
                    for vname, pat in variants.items():
                        tpat = apply_pattern_transform(pat, pattern_transform, k)
                        offs = L.find_all(payload, tpat)
                        for o in offs:
                            agg[(fname, vname, len(tpat))].append((ridx, o))
                for (fname, vname, patlen), hitlist in agg.items():
                    off_counter = defaultdict(set)
                    for ridx, o in hitlist:
                        off_counter[o].add(ridx)
                    best_off, best_records = max(off_counter.items(), key=lambda kv: len(kv[1]))
                    n_hit_records = len(best_records)
                    n_avail = n_available[fname]
                    if n_hit_records < 2:
                        continue
                    p = 1.0 / (256 ** patlen)
                    expected = n_avail * p
                    rows.append(dict(
                        transform=pattern_transform, k=k, file=fkey, value_type=f"own_{fname}",
                        scope="per_record", variant=vname, patlen=patlen,
                        n_records_hit=n_hit_records, n_available=n_avail,
                        mode_offset=best_off, expected_by_chance=expected,
                    ))

    print(f"Part 1 (own-value, pattern-side transforms) done: {len(rows)} candidate rows so far")

    # ============ PART 2: per-identity V1/V2 constants ============
    rows2_start = len(rows)
    for fkey, records in all_records.items():
        by_identity = defaultdict(list)
        for r in records:
            if r["identity_row"] is not None:
                by_identity[r["identity_row"]["identity"]].append(r)
        for ident, recs in by_identity.items():
            v1 = recs[0]["identity_row"]["v1"]
            v2 = recs[0]["identity_row"]["v2"]
            base_variants = {"v1": encode_int_variants(v1), "v2": encode_int_variants(v2)}
            for pattern_transform in PATTERN_SIDE_TRANSFORMS:
                xor_range = range(1, 256) if pattern_transform == "xor" else [None]
                for k in xor_range:
                    for fname, variants in base_variants.items():
                        off_counter = defaultdict(set)
                        for vname, pat in variants.items():
                            tpat = apply_pattern_transform(pat, pattern_transform, k)
                            for r in recs:
                                offs = L.find_all(r["payload"], tpat)
                                for o in offs:
                                    off_counter[(vname, len(tpat), o)].add(r["idx"])
                        # group by (vname, patlen) to find best offset per variant
                        by_variant = defaultdict(dict)
                        for (vname, patlen, o), ridxs in off_counter.items():
                            by_variant[(vname, patlen)][o] = ridxs
                        for (vname, patlen), offmap in by_variant.items():
                            best_off, best_records = max(offmap.items(), key=lambda kv: len(kv[1]))
                            n_hit = len(best_records)
                            n_avail = len(recs)
                            if n_hit < 2:
                                continue
                            p = 1.0 / (256 ** patlen)
                            expected = n_avail * p
                            rows.append(dict(
                                transform=pattern_transform, k=k, file=fkey, value_type=f"{fname}_{ident}",
                                scope="per_identity", variant=vname, patlen=patlen,
                                n_records_hit=n_hit, n_available=n_avail,
                                mode_offset=best_off, expected_by_chance=expected,
                            ))
    print(f"Part 2 (V1/V2 per identity) done: {len(rows) - rows2_start} candidate rows added")

    # ============ PART 3: global constants (sentinel, weeks, rates) on full blob ============
    rows3_start = len(rows)
    for fkey, blob in blobs.items():
        for cname, cval in GLOBAL_CONSTS.items():
            base_variants = encode_float_variants(float(cval)) if isinstance(cval, float) else encode_int_variants(cval)
            for pattern_transform in PATTERN_SIDE_TRANSFORMS:
                xor_range = range(1, 256) if pattern_transform == "xor" else [None]
                for k in xor_range:
                    for vname, pat in base_variants.items():
                        tpat = apply_pattern_transform(pat, pattern_transform, k)
                        offs = L.find_all(blob, tpat)
                        if not offs:
                            continue
                        patlen = len(tpat)
                        p = 1.0 / (256 ** patlen)
                        expected = L.chance_hits(len(blob), patlen)
                        rows.append(dict(
                            transform=pattern_transform, k=k, file=fkey, value_type=f"global_{cname}",
                            scope="global", variant=vname, patlen=patlen,
                            n_records_hit=len(offs), n_available=1,
                            mode_offset=offs[0] if len(offs) == 1 else -1, expected_by_chance=expected,
                        ))
    print(f"Part 3 (global consts) done: {len(rows) - rows3_start} candidate rows added")

    # ============ PART 4: delta_decode (data-side transform) — own values + V1/V2 + global ============
    rows4_start = len(rows)
    for fkey, records in all_records.items():
        agg = defaultdict(list)
        n_available = defaultdict(int)
        for r in records:
            if r["tag"] != 0x15:
                continue
            dpayload = L.delta_decode(r["payload"])
            field_vals = {"f1": r["f1"], "f2": r["f2"], "f3": r["f3"], "f4": r["f4"]}
            if r["f3_delta"] is not None:
                field_vals["f3_delta"] = r["f3_delta"]
            for fname, fval in field_vals.items():
                n_available[fname] += 1
                variants = encode_float_variants(fval, include_bcd_int=(fname in ("f3", "f4", "f3_delta")))
                for vname, pat in variants.items():
                    offs = L.find_all(dpayload, pat)
                    for o in offs:
                        agg[(fname, vname, len(pat))].append((r["idx"], o))
        for (fname, vname, patlen), hitlist in agg.items():
            off_counter = defaultdict(set)
            for ridx, o in hitlist:
                off_counter[o].add(ridx)
            if not off_counter:
                continue
            best_off, best_records = max(off_counter.items(), key=lambda kv: len(kv[1]))
            n_hit_records = len(best_records)
            n_avail = n_available[fname]
            if n_hit_records < 2:
                continue
            p = 1.0 / (256 ** patlen)
            expected = n_avail * p
            rows.append(dict(
                transform="delta_decode", k=None, file=fkey, value_type=f"own_{fname}",
                scope="per_record", variant=vname, patlen=patlen,
                n_records_hit=n_hit_records, n_available=n_avail,
                mode_offset=best_off, expected_by_chance=expected,
            ))
    print(f"Part 4 (delta_decode) done: {len(rows) - rows4_start} candidate rows added")

    # write CSV of all candidate rows (raw data for follow-up, not just the filtered leads)
    import csv
    with open(REPORT_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["transform", "k", "file", "value_type", "scope", "variant",
                                           "patlen", "n_records_hit", "n_available", "mode_offset",
                                           "expected_by_chance"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} candidate rows to {REPORT_PATH}")

    # ============ significance filter: report only rows that beat chance meaningfully ============
    print()
    print("=" * 100)
    print("SIGNIFICANT FINDS (n_records_hit >= 3 and n_records_hit >> expected_by_chance)")
    print("=" * 100)
    sig = []
    for row in rows:
        exp = row["expected_by_chance"]
        nhit = row["n_records_hit"]
        if nhit >= 3 and (exp < 0.05 or nhit >= max(3, 20 * exp)):
            sig.append(row)
    sig.sort(key=lambda r: (-(r["n_records_hit"] - r["expected_by_chance"]), r["transform"]))
    for row in sig[:100]:
        print(f"  [{row['file']}] {row['transform']}"
              + (f"(k={row['k']:#04x})" if row['k'] is not None else "")
              + f" {row['value_type']:20s} variant={row['variant']:16s} patlen={row['patlen']} "
              + f"hit={row['n_records_hit']}/{row['n_available']} off={row['mode_offset']:5d} "
              + f"chance~{row['expected_by_chance']:.2e}")
    print(f"\ntotal significant rows: {len(sig)} / {len(rows)} candidates")


if __name__ == "__main__":
    main()
