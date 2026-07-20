#!/usr/bin/env python3
"""TEST 1 & 2 (decisive): bit-level cross-correlation between payload pairs.
Pure-Python big-integer implementation (no numpy available for /usr/bin/python3).

Test 1: within an identity that has multiple template lengths, is the longer
payload = the shorter one with an inserted BIT-substring (not byte-aligned)?
If so, some relative bit shift (1-16) should yield very high (>>50%) bit
agreement over the overlap, far above chance and far above the shift=0
(byte-aligned) baseline.

Test 2: do different identities' payload cores share long bit-substrings at
non-byte-aligned relative offsets? Same metric, applied across identity pairs
instead of within an identity.

Both bit orders (MSB-first / LSB-first per byte) and both anchor points
(from the start of the payload, from the end) are tested, since byte-level
diffs showed lcs>0 (tails sometimes match at the byte level) suggesting
insertions may sit near the front.
"""
import sys
import random
from collections import defaultdict

sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_anchor import FILES, parse_body, chain_walk, get_payloads

REV = [int(format(b, "08b")[::-1], 2) for b in range(256)]


def load_identity_map():
    id_to_records = defaultdict(list)  # (f1,f2) -> [(tag,n,payload)]
    for tag, cfg in FILES.items():
        data = open(cfg["path"], "rb").read()
        body = parse_body(data, cfg["body_start"], cfg["body_end"])
        markers = chain_walk(data, cfg["pk_start"], cfg["maxn"])
        payloads = get_payloads(data, markers, len(data))
        assert len(body) == len(payloads)
        for (kind, fl), (n, payload) in zip(body, payloads):
            if kind != "15":
                continue
            f1, f2, f3, f4 = fl
            key = (round(f1, 6), round(f2, 6))
            id_to_records[key].append((tag, n, bytes(payload)))
    return id_to_records


def bit_int(data, order="big", anchor="start"):
    """Return (value, nbits) representing the payload's bit sequence, forward
    order, under the given per-byte bit order and start/end anchor."""
    base = data if order == "big" else bytes(REV[c] for c in data)
    if anchor == "end":
        base = bytes(REV[c] for c in reversed(base))
    return int.from_bytes(base, "big"), len(base) * 8


def suffix(val, nbits, s):
    """Drop the first s bits (from the front / MSB side)."""
    if s >= nbits:
        return 0, 0
    new_nbits = nbits - s
    return val & ((1 << new_nbits) - 1), new_nbits


def bitagree(valA, nbitsA, valB, nbitsB):
    """% agreement over the overlapping FRONT n bits of two bit sequences."""
    n = min(nbitsA, nbitsB)
    if n == 0:
        return 0.0, 0
    topA = valA >> (nbitsA - n)
    topB = valB >> (nbitsB - n)
    xor = topA ^ topB
    matches = n - bin(xor).count("1")
    return matches / n, n


def best_shift_agreement(A, B, max_shift=16):
    """Search both bit orders x both anchors x both shift-directions x
    shift 0..max_shift. Return best (pct, n_overlap, shift, detail)."""
    best = (0.0, 0, 0, "")
    for order in ("big", "little"):
        for anchor in ("start", "end"):
            valA, nbA = bit_int(A, order, anchor)
            valB, nbB = bit_int(B, order, anchor)
            for shift in range(0, max_shift + 1):
                # A shifted ahead of B
                sA, snbA = suffix(valA, nbA, shift)
                pct, n = bitagree(sA, snbA, valB, nbB)
                if n >= 64 and (pct, n) > (best[0], best[1]):
                    best = (pct, n, shift, f"{order}/{anchor}/A-ahead")
                # B shifted ahead of A
                sB, snbB = suffix(valB, nbB, shift)
                pct, n = bitagree(valA, nbA, sB, snbB)
                if n >= 64 and (pct, n) > (best[0], best[1]):
                    best = (pct, n, shift, f"{order}/{anchor}/B-ahead")
    return best


def shift0_baseline(A, B):
    valA, nbA = bit_int(A, "big", "start")
    valB, nbB = bit_int(B, "big", "start")
    return bitagree(valA, nbA, valB, nbB)


def main():
    id_to_records = load_identity_map()

    print("=" * 100)
    print("TEST 1: within-identity, cross-template-length bit-shift agreement")
    print("=" * 100)
    multi_len_ids = []
    for key, recs in id_to_records.items():
        lens = sorted(set(len(p) for _, _, p in recs))
        if len(lens) >= 2:
            multi_len_ids.append(key)

    print(f"identities with >=2 distinct payload lengths: {len(multi_len_ids)}\n")

    within_results = []
    for key in sorted(multi_len_ids):
        recs = id_to_records[key]
        by_len = defaultdict(list)
        for tag, n, p in recs:
            by_len[len(p)].append((tag, n, p))
        lens = sorted(by_len.keys())
        for i in range(len(lens)):
            for j in range(i + 1, len(lens)):
                lenA, lenB = lens[i], lens[j]
                tagA, nA, A = by_len[lenA][0]
                tagB, nB, B = by_len[lenB][0]
                base_pct, base_n = shift0_baseline(A, B)
                best_pct, best_n, best_shift, detail = best_shift_agreement(A, B)
                flag = " <<< HIGH" if best_pct >= 0.90 else ""
                print(f"id={key} len {lenA}({tagA}n{nA}) vs {lenB}({tagB}n{nB}): "
                      f"shift0_baseline={base_pct*100:5.1f}% (n={base_n})  "
                      f"BEST shift={best_shift:2d} pct={best_pct*100:5.1f}% (n={best_n}) [{detail}]{flag}")
                within_results.append((key, lenA, lenB, base_pct, best_pct, best_shift, detail))

    hi = [r for r in within_results if r[4] >= 0.90]
    print(f"\n-> {len(hi)}/{len(within_results)} within-identity pairs exceed 90% bit agreement at some shift.")

    print()
    print("=" * 100)
    print("CONTROL: chance baseline via random unrelated payload pairs (different identities)")
    print("=" * 100)
    all_payloads = []
    for key, recs in id_to_records.items():
        for tag, n, p in recs:
            all_payloads.append((key, tag, n, p))
    random.seed(42)
    control_results = []
    tries = 0
    while len(control_results) < 20 and tries < 200:
        tries += 1
        (k1, t1, n1, p1), (k2, t2, n2, p2) = random.sample(all_payloads, 2)
        if k1 == k2:
            continue
        best_pct, best_n, best_shift, detail = best_shift_agreement(p1, p2)
        control_results.append(best_pct)
        print(f"  control pair id={k1}/{t1}n{n1}(len{len(p1)}) vs id={k2}/{t2}n{n2}(len{len(p2)}): "
              f"BEST pct={best_pct*100:5.1f}% at shift={best_shift} [{detail}]")
    if control_results:
        print(f"\n  control mean best-of-search agreement: {100*sum(control_results)/len(control_results):.1f}%  "
              f"max: {100*max(control_results):.1f}%  "
              f"(chance ceiling given we searched {2*2*2*17} shift/order/anchor/direction combos)")

    print()
    print("=" * 100)
    print("TEST 2: cross-identity core sharing at bit level (non-byte-aligned)")
    print("=" * 100)
    cores = {}
    for key, recs in id_to_records.items():
        by_len_count = defaultdict(int)
        by_len_example = {}
        for tag, n, p in recs:
            by_len_count[len(p)] += 1
            by_len_example.setdefault(len(p), (tag, n, p))
        common_len = max(by_len_count.items(), key=lambda kv: kv[1])[0]
        cores[key] = by_len_example[common_len]

    keys = sorted(cores.keys())
    cross_results = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            k1, k2 = keys[i], keys[j]
            t1, n1, p1 = cores[k1]
            t2, n2, p2 = cores[k2]
            base_pct, base_n = shift0_baseline(p1, p2)
            best_pct, best_n, best_shift, detail = best_shift_agreement(p1, p2)
            flag = " <<< HIGH" if best_pct >= 0.90 else ""
            cross_results.append((k1, k2, base_pct, best_pct, best_shift, detail))
            print(f"core {k1}(len{len(p1)}) vs {k2}(len{len(p2)}): "
                  f"shift0={base_pct*100:5.1f}%  BEST shift={best_shift:2d} pct={best_pct*100:5.1f}% [{detail}]{flag}")

    hi2 = [r for r in cross_results if r[3] >= 0.90]
    print(f"\n-> {len(hi2)}/{len(cross_results)} cross-identity core pairs exceed 90% bit agreement at some shift.")


if __name__ == "__main__":
    main()
