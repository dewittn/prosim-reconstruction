#!/usr/bin/env python3
"""Supplementary sweep: report EVERY hit (even isolated singles) for the
high-length encodings (patlen>=4: mbf32, mbf64, vb_currency, fixed-point,
u32/i32 scaled-int) across RAW / XOR(1-255) / nibble_swap / bit_reverse /
delta_decode. For own-f1/f2 targets, dedupes by DISTINCT IDENTITY (not raw
record count) since payload content is a deterministic function of (f1,f2)
identity -- records sharing an identity share byte-identical payloads, so a
"hit repeated across N records of the same identity" is really N=1
independent event, not N independent trials. This corrects the inflated
significance seen in t4m_search.py's naive per-record counting.
"""
import sys
from collections import defaultdict

sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
import t4m_lib as L
from t4m_targets import build_records, GLOBAL_CONSTS

PATTERN_SIDE_TRANSFORMS = ["raw", "xor", "nibble_swap", "bit_reverse"]


def big_variants(v):
    """Only patlen>=4 encodings: mbf32, mbf64, vb_currency, fixed_point, u32/i32 scaled."""
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
    for name, pat in L.scaled_int_variants(v).items():
        if len(pat) >= 4:
            out[name] = pat
    out.update(L.fixed_point_variants(v))
    return out


def apply_pt(pat, transform, k):
    if transform == "raw":
        return pat
    if transform == "xor":
        return L.xor_bytes(pat, k)
    if transform == "nibble_swap":
        return L.nibble_swap(pat)
    if transform == "bit_reverse":
        return L.bit_reverse(pat)
    return pat


def main():
    findings = []

    for fkey in ("a", "b"):
        name, data, records, n_body, n_packed = build_records(fkey)
        blob_start = records[0]["payload_start"]
        blob_end = records[-1]["payload_end"]
        blob = data[blob_start:blob_end]

        # --- own f1/f2 deduped by distinct identity (use first record of each identity) ---
        seen_ident_keys = {}
        for r in records:
            if r["tag"] != 0x15:
                continue
            key = (round(r["f1"], 6), round(r["f2"], 6))
            if key not in seen_ident_keys:
                seen_ident_keys[key] = r  # first occurrence representative

        n_distinct_identities = len(seen_ident_keys)
        for key, r in seen_ident_keys.items():
            payload = r["payload"]
            for fname, fval in (("f1", r["f1"]), ("f2", r["f2"])):
                variants = big_variants(fval)
                for vname, pat in variants.items():
                    for pt in PATTERN_SIDE_TRANSFORMS:
                        krange = range(1, 256) if pt == "xor" else [None]
                        for k in krange:
                            tpat = apply_pt(pat, pt, k)
                            offs = L.find_all(payload, tpat)
                            for o in offs:
                                findings.append(dict(
                                    file=fkey, category="own_f1f2_by_identity", value_type=fname,
                                    identity_key=key, transform=pt, k=k, variant=vname,
                                    patlen=len(tpat), offset=o, paylen=len(payload),
                                    n_distinct_identities_tested=n_distinct_identities,
                                ))

        # --- own f3/f4/delta: these DO vary per record within an identity (real independent trials) ---
        for r in records:
            if r["tag"] != 0x15:
                continue
            payload = r["payload"]
            fields = {"f3": r["f3"], "f4": r["f4"]}
            if r["f3_delta"] is not None:
                fields["f3_delta"] = r["f3_delta"]
            for fname, fval in fields.items():
                variants = big_variants(fval)
                for vname, pat in variants.items():
                    for pt in PATTERN_SIDE_TRANSFORMS:
                        krange = range(1, 256) if pt == "xor" else [None]
                        for k in krange:
                            tpat = apply_pt(pat, pt, k)
                            offs = L.find_all(payload, tpat)
                            for o in offs:
                                findings.append(dict(
                                    file=fkey, category="own_f3f4delta_per_record", value_type=fname,
                                    identity_key=None, transform=pt, k=k, variant=vname,
                                    patlen=len(tpat), offset=o, paylen=len(payload),
                                    record_idx=r["idx"],
                                ))

        # --- V1/V2: search WHOLE blob (not just same-identity records), since it's a global constant ---
        by_identity = {}
        for r in records:
            if r["identity_row"] is not None:
                by_identity[r["identity_row"]["identity"]] = r["identity_row"]
        for ident, row in by_identity.items():
            for fname, fval in (("v1", row["v1"]), ("v2", row["v2"])):
                variants = big_variants(float(fval))
                for vname, pat in variants.items():
                    for pt in PATTERN_SIDE_TRANSFORMS:
                        krange = range(1, 256) if pt == "xor" else [None]
                        for k in krange:
                            tpat = apply_pt(pat, pt, k)
                            offs = L.find_all(blob, tpat)
                            for o in offs:
                                findings.append(dict(
                                    file=fkey, category="v1v2_global_blob", value_type=f"{fname}_{ident}",
                                    identity_key=None, transform=pt, k=k, variant=vname,
                                    patlen=len(tpat), offset=o, paylen=len(blob),
                                ))

        # --- global consts on blob (delta_decode of full blob too) ---
        dblob = L.delta_decode(blob)
        for cname, cval in GLOBAL_CONSTS.items():
            variants = big_variants(float(cval))
            for vname, pat in variants.items():
                for pt in PATTERN_SIDE_TRANSFORMS:
                    krange = range(1, 256) if pt == "xor" else [None]
                    for k in krange:
                        tpat = apply_pt(pat, pt, k)
                        offs = L.find_all(blob, tpat)
                        for o in offs:
                            findings.append(dict(
                                file=fkey, category="global_const", value_type=cname,
                                identity_key=None, transform=pt, k=k, variant=vname,
                                patlen=len(tpat), offset=o, paylen=len(blob),
                            ))
                # delta_decode data-side (no pattern transform)
                offs = L.find_all(dblob, pat)
                for o in offs:
                    findings.append(dict(
                        file=fkey, category="global_const", value_type=cname,
                        identity_key=None, transform="delta_decode", k=None, variant=vname,
                        patlen=len(pat), offset=o, paylen=len(dblob),
                    ))

        # --- delta_decode data-side for own f1/f2 (by identity) and f3/f4/delta (per record) ---
        for key, r in seen_ident_keys.items():
            dpayload = L.delta_decode(r["payload"])
            for fname, fval in (("f1", r["f1"]), ("f2", r["f2"])):
                for vname, pat in big_variants(fval).items():
                    offs = L.find_all(dpayload, pat)
                    for o in offs:
                        findings.append(dict(
                            file=fkey, category="own_f1f2_by_identity", value_type=fname,
                            identity_key=key, transform="delta_decode", k=None, variant=vname,
                            patlen=len(pat), offset=o, paylen=len(dpayload),
                            n_distinct_identities_tested=n_distinct_identities,
                        ))
        for r in records:
            if r["tag"] != 0x15:
                continue
            dpayload = L.delta_decode(r["payload"])
            fields = {"f3": r["f3"], "f4": r["f4"]}
            if r["f3_delta"] is not None:
                fields["f3_delta"] = r["f3_delta"]
            for fname, fval in fields.items():
                for vname, pat in big_variants(fval).items():
                    offs = L.find_all(dpayload, pat)
                    for o in offs:
                        findings.append(dict(
                            file=fkey, category="own_f3f4delta_per_record", value_type=fname,
                            identity_key=None, transform="delta_decode", k=None, variant=vname,
                            patlen=len(pat), offset=o, paylen=len(dpayload),
                            record_idx=r["idx"],
                        ))

    print(f"Total raw (unfiltered) hits across all patlen>=4 encodings/transforms: {len(findings)}")

    # chance rate context
    print("\nPattern-length -> chance of a single hit in an ~20000-byte buffer (uniform-random model):")
    for patlen in (4, 8):
        print(f"  patlen={patlen}: chance/position=1/{256**patlen:.3e}  "
              f"expected hits in 20000 bytes = {20000/(256**patlen):.3e}")

    print("\n=== all findings (patlen>=4) ===")
    findings.sort(key=lambda f: (f["patlen"], f["file"], f["category"]))
    for f in findings:
        print(f)

    if not findings:
        print("  NONE FOUND -- clean negative across all patlen>=4 encodings tested "
              "(mbf32, mbf64, vb_currency, fixed-point 16.16/8.24, u32/i32 scaled x1/x10/x100), "
              "under raw/xor(1-255)/nibble-swap/bit-reverse/delta-decode.")


if __name__ == "__main__":
    main()
