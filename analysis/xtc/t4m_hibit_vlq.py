#!/usr/bin/env python3
"""High-bit-stripped 7-bit stream (scaled-int/BCD/ASCII-digit) and base-128 VLQ
(MIDI-style: [0x80|x][0x80|y][z<0x80] -> (x<<14)|(y<<7)|z) searches.
"""
import sys
import struct
from collections import defaultdict

sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
import t4m_lib as L
from t4m_targets import build_records, GLOBAL_CONSTS


def small_int_variants_7bit(v):
    """scaled-int (x1/x10/x100, u16/u32 LE/BE) + BCD, using the SAME encoders but
    with each output byte additionally bit7-masked (since we compare against a
    stream that already had bit7 stripped -- apples to apples)."""
    out = {}
    for name, pat in L.scaled_int_variants(v).items():
        out[name] = L.high_bit_strip(pat)
    for name, pat in L.bcd_variants(int(round(v))).items() if v >= 0 else []:
        out[name] = L.high_bit_strip(pat)
    return out


def ascii_digit_variants(v):
    iv = int(round(v))
    if iv < 0:
        return {}
    s = str(iv)
    return {"ascii": s.encode("ascii")}


def main():
    findings = []
    for fkey in ("a", "b"):
        name, data, records, n_body, n_packed = build_records(fkey)
        blob_start = records[0]["payload_start"]
        blob_end = records[-1]["payload_end"]
        blob = data[blob_start:blob_end]
        stripped = L.high_bit_strip(blob)

        targets = list(GLOBAL_CONSTS.items())
        seen_ident = {}
        for r in records:
            if r["identity_row"] is not None and r["identity_row"]["identity"] not in seen_ident:
                seen_ident[r["identity_row"]["identity"]] = r["identity_row"]
        for ident, row in seen_ident.items():
            targets.append((f"v1_{ident}", row["v1"]))
            targets.append((f"v2_{ident}", row["v2"]))

        for cname, cval in targets:
            # 7-bit scaled-int / BCD, searched in the high-bit-stripped stream
            for vname, pat in small_int_variants_7bit(float(cval)).items():
                offs = L.find_all(stripped, pat)
                patlen = len(pat)
                # chance model: each byte of a genuine 7-bit-space pattern has 128
                # possible values once we've committed to comparing masked bytes
                p = 1.0 / (128 ** patlen)
                expected = L.chance_hits(len(stripped), patlen) * (256.0 / 128.0) ** patlen \
                    if patlen else 0
                # (equivalently: expected = len(stripped)*p, using 128^patlen space)
                expected = len(stripped) * p
                if offs:
                    findings.append(dict(file=fkey, kind="7bit_scaled_or_bcd", value=cname,
                                          variant=vname, patlen=patlen, n_hits=len(offs),
                                          expected=expected, offsets=offs[:5]))
            # ASCII digits, both raw blob and stripped stream
            for vname, pat in ascii_digit_variants(float(cval)).items():
                for label, buf in (("raw", blob), ("stripped", stripped)):
                    offs = L.find_all(buf, pat)
                    if offs:
                        patlen = len(pat)
                        expected = L.chance_hits(len(buf), patlen)
                        findings.append(dict(file=fkey, kind=f"ascii_{label}", value=cname,
                                              variant=vname, patlen=patlen, n_hits=len(offs),
                                              expected=expected, offsets=offs[:5]))

        # --- VLQ base-128 (MIDI-style): scan RAW payload for [0x80|x][0x80|y][z<0x80] ---
        vlq_hits = []
        for i in range(len(blob) - 2):
            b0, b1, b2 = blob[i], blob[i + 1], blob[i + 2]
            if (b0 & 0x80) and (b1 & 0x80) and not (b2 & 0x80):
                val = ((b0 & 0x7f) << 14) | ((b1 & 0x7f) << 7) | b2
                vlq_hits.append((i, val))
        print(f"[{fkey}] VLQ 3-byte candidates found in blob: {len(vlq_hits)} "
              f"(blob len={len(blob)}, positions with b[i]&0x80 and b[i+1]&0x80 and not b[i+2]&0x80)")
        # compare decoded values against known targets (V1/V2, weeks, rates, and
        # rounded f3/f4/deltas), exact integer match only (VLQ encodes integers cleanly)
        target_ints = defaultdict(list)
        for cname, cval in targets:
            target_ints[int(round(cval))].append(cname)
        for r in records:
            if r["tag"] == 0x15:
                for fname in ("f3", "f4"):
                    target_ints[int(round(r[fname]))].append(f"{fname}@rec{r['idx']}")
                if r["f3_delta"] is not None:
                    target_ints[int(round(r["f3_delta"]))].append(f"f3_delta@rec{r['idx']}")
        vlq_matches = [(off, val, target_ints[val]) for off, val in vlq_hits if val in target_ints]
        print(f"   VLQ decoded values matching ANY known target (exact int): {len(vlq_matches)} / {len(vlq_hits)}")
        for off, val, labels in vlq_matches[:20]:
            print(f"     off={off} val={val} matches={labels}")

    print()
    print("=== high-bit-strip 7-bit-stream + ASCII-digit findings ===")
    findings.sort(key=lambda f: (-f["n_hits"] / max(f["expected"], 1e-12), f["file"]))
    for f in findings:
        ratio = f["n_hits"] / max(f["expected"], 1e-12)
        flag = " <<<< BEATS CHANCE" if (f["patlen"] >= 3 and ratio > 20 and f["n_hits"] >= 2) else ""
        print(f"  [{f['file']}] {f['kind']:16s} value={f['value']:14s} variant={f['variant']:14s} "
              f"patlen={f['patlen']} n_hits={f['n_hits']:4d} expected={f['expected']:.3e} ratio={ratio:.1f}{flag}")


if __name__ == "__main__":
    main()
