#!/usr/bin/env python3
"""Q2 Task 2: decode the isolated INSERTED_SPAN byte ranges from q2_spans.csv.
Try: (a) LEB128 varint stream, (b) periodicity via factor-candidate autocorrelation,
(c) float32/int16 scans. Report best guess per span.
"""
import csv
import struct

CSV = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/q2_spans.csv"


def factor(n):
    fs = []
    d = 2
    x = n
    while d * d <= x:
        while x % d == 0:
            fs.append(d)
            x //= d
        d += 1
    if x > 1:
        fs.append(x)
    return fs


def divisors(n):
    fs = set()
    for i in range(1, int(n ** 0.5) + 1):
        if n % i == 0:
            fs.add(i)
            fs.add(n // i)
    return sorted(fs)


def leb128_decode_stream(b):
    """Decode as many consecutive unsigned LEB128 varints as possible from b.
    Returns (values, bytes_consumed, ended_cleanly)."""
    vals = []
    pos = 0
    while pos < len(b):
        result = 0
        shift = 0
        start = pos
        ok = False
        while pos < len(b):
            byte = b[pos]
            result |= (byte & 0x7F) << shift
            pos += 1
            if not (byte & 0x80):
                ok = True
                break
            shift += 7
            if shift > 35:  # runaway
                break
        if not ok:
            pos = start
            break
        vals.append(result)
    return vals, pos, pos == len(b)


def autocorr_score(b, p):
    if p <= 0 or p >= len(b):
        return 0.0
    n = len(b) - p
    if n <= 0:
        return 0.0
    matches = sum(1 for i in range(n) if b[i] == b[i + p])
    return matches / n


def best_period(b, max_period=200):
    n = len(b)
    cand_periods = sorted(set(divisors(n)) | set(range(2, min(max_period, n // 2) + 1)))
    scored = []
    for p in cand_periods:
        if p >= n:
            continue
        s = autocorr_score(b, p)
        scored.append((s, p))
    scored.sort(reverse=True)
    return scored[:8]


def float_scan(b, ranges):
    """Scan for float32 LE values landing in any of the given (lo,hi) ranges."""
    hits = []
    for off in range(0, len(b) - 3):
        v = struct.unpack_from("<f", b, off)[0]
        for lo, hi in ranges:
            if lo <= v <= hi:
                hits.append((off, "f32le", round(v, 2)))
                break
    return hits


def int16_scan(b, ranges):
    hits = []
    for off in range(0, len(b) - 1):
        v_le = struct.unpack_from("<H", b, off)[0]
        v_be = struct.unpack_from(">H", b, off)[0]
        for lo, hi in ranges:
            if lo <= v_le <= hi:
                hits.append((off, "u16le", v_le))
            if lo <= v_be <= hi:
                hits.append((off, "u16be", v_be))
    return hits


# Game-quantity plausibility ranges (from prosim/config/defaults.py + week1.txt)
DEMAND_RANGE = [(2000, 9000)]
COST_RANGE = [(50, 15000)]
HOURS_RANGE = [(0, 50)]
UNITS_RANGE = [(50, 3000)]


def main():
    rows = list(csv.DictReader(open(CSV)))
    spans = [r for r in rows if r["kind"] == "INSERTED_SPAN" and int(r["changed_b_len"]) > 0]

    for r in spans:
        b = bytes.fromhex(r["changed_b_hex"])
        label = f"{r['file']} {r['identity']} n{r['n_from']}->n{r['n_to']} len={len(b)}"
        print("=" * 100)
        print(label)
        print(f"  factors of len: {factor(len(b))}")

        vals, consumed, clean = leb128_decode_stream(b)
        print(f"  LEB128 stream: {len(vals)} values, consumed={consumed}/{len(b)} clean={clean}")
        if vals:
            in_range = [v for v in vals if 0 < v < 50000]
            print(f"    sample values: {vals[:20]}")
            print(f"    plausible-range (0-50000) count: {len(in_range)}/{len(vals)}")

        periods = best_period(b, max_period=120)
        print(f"  top autocorrelation periods (score, period): {periods}")

        fhits = float_scan(b, DEMAND_RANGE + COST_RANGE)
        print(f"  float32 hits in game-plausible ranges: {len(fhits)}")
        if fhits:
            print(f"    sample: {fhits[:10]}")

        ihits = int16_scan(b, [(2000, 9000), (0, 50), (50, 3000)])
        print(f"  int16 hits in game-plausible ranges: {len(ihits)}")
        if ihits:
            print(f"    sample: {ihits[:10]}")

        # dump raw hex in chunks for manual inspection
        print("  hex dump (first 160 bytes):")
        for i in range(0, min(160, len(b)), 16):
            print(f"    {i:4d}  {b[i:i+16].hex(' ')}")


if __name__ == "__main__":
    main()
