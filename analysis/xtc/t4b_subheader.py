#!/usr/bin/env python3
"""TEST 4: sub-header segmentation. Split packed-payload interiors at
[0x80-0x87][0xF8-0xFE] two-byte marker boundaries; treat the run of bytes
between one marker and the next as a "segment". Test whether the 3 variable
bits of the marker pair ((b0 & 0x07), (b1 & 0x07)) correlate with the length
of the segment that follows (a correlation would indicate the marker encodes
a length/type field for what follows).
"""
import sys
from collections import defaultdict

sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_anchor import FILES, parse_body, chain_walk, get_payloads


def load_distinct_payloads():
    seen = {}
    for tag, cfg in FILES.items():
        data = open(cfg["path"], "rb").read()
        body = parse_body(data, cfg["body_start"], cfg["body_end"])
        markers = chain_walk(data, cfg["pk_start"], cfg["maxn"])
        payloads = get_payloads(data, markers, len(data))
        for (kind, fl), (n, payload) in zip(body, payloads):
            if kind != "15":
                continue
            p = bytes(payload)
            seen.setdefault(p, (tag, n))
    return seen


def find_markers(payload):
    """Return list of (offset, b0, b1) for every [0x80-0x87][0xF8-0xFE] pair."""
    out = []
    for i in range(len(payload) - 1):
        b0, b1 = payload[i], payload[i + 1]
        if 0x80 <= b0 <= 0x87 and 0xF8 <= b1 <= 0xFE:
            out.append((i, b0, b1))
    return out


def main():
    distinct = load_distinct_payloads()
    print(f"distinct payloads: {len(distinct)}")

    all_segments = []  # (b0_3bit, b1_3bit, seg_len)
    per_payload_marker_counts = []

    for payload, (tag, n) in distinct.items():
        marks = find_markers(payload)
        per_payload_marker_counts.append(len(marks))
        for idx, (off, b0, b1) in enumerate(marks):
            seg_start = off + 2
            seg_end = marks[idx + 1][0] if idx + 1 < len(marks) else len(payload)
            seg_len = seg_end - seg_start
            all_segments.append((b0 & 0x07, b1 & 0x07, seg_len, tag, n, off))

    print(f"total sub-header markers found across all distinct payloads: {len(all_segments)}")
    if per_payload_marker_counts:
        avg_gap = sum(per_payload_marker_counts) / len(per_payload_marker_counts)
        print(f"avg markers per payload: {avg_gap:.1f}  "
              f"(matches expected ~20-90 byte spacing given payload sizes)")

    print()
    print("=" * 100)
    print("Segment length distribution by 3-bit field (b0&7, b1&7)")
    print("=" * 100)
    by_field = defaultdict(list)
    for b0_3, b1_3, seg_len, tag, n, off in all_segments:
        by_field[(b0_3, b1_3)].append(seg_len)

    for field, lens in sorted(by_field.items()):
        lens_sorted = sorted(lens)
        n = len(lens)
        mean = sum(lens) / n
        median = lens_sorted[n // 2]
        print(f"  field b0&7={field[0]} b1&7={field[1]}: n={n:4d} mean_len={mean:7.2f} "
              f"median={median:4d} min={min(lens):4d} max={max(lens):4d}")

    # overall correlation check: does b0&7 alone predict length? does b1&7 alone?
    print()
    print("-- marginal on b0&7 only --")
    by_b0 = defaultdict(list)
    for b0_3, b1_3, seg_len, *_ in all_segments:
        by_b0[b0_3].append(seg_len)
    for k, lens in sorted(by_b0.items()):
        print(f"  b0&7={k}: n={len(lens):4d} mean={sum(lens)/len(lens):7.2f} "
              f"min={min(lens)} max={max(lens)}")

    print()
    print("-- marginal on b1&7 only --")
    by_b1 = defaultdict(list)
    for b0_3, b1_3, seg_len, *_ in all_segments:
        by_b1[b1_3].append(seg_len)
    for k, lens in sorted(by_b1.items()):
        print(f"  b1&7={k}: n={len(lens):4d} mean={sum(lens)/len(lens):7.2f} "
              f"min={min(lens)} max={max(lens)}")

    # simple correlation coefficient between (b0*8+b1) and seg_len
    xs = [b0 * 8 + b1 for b0, b1, *_ in all_segments]
    ys = [seg_len for _, _, seg_len, *_ in all_segments]
    n = len(xs)
    if n > 2:
        mx = sum(xs) / n
        my = sum(ys) / n
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
        sx = (sum((x - mx) ** 2 for x in xs) / n) ** 0.5
        sy = (sum((y - my) ** 2 for y in ys) / n) ** 0.5
        r = cov / (sx * sy) if sx > 0 and sy > 0 else 0.0
        print()
        print(f"Pearson r between combined field value (b0*8+b1) and segment length: {r:.4f}  (n={n})")
        print("(|r| near 0 => no length-encoding relationship; |r| > ~0.3 with this n would be notable)")


if __name__ == "__main__":
    main()
