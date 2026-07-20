#!/usr/bin/env python3
"""Q2 Task 1+3: isolate transient suffix spans and small-delta transitions for
every consecutive same-identity payload pair (per file), by computing the
longest-common-prefix / longest-common-suffix diff between the two payload
bodies (marker byte stripped). Writes q2_spans.csv.

Classification:
  - if the "changed" region on the SHORTER side of a pair is empty (i.e. the
    shorter payload is fully explained by shared prefix + shared suffix), the
    changed region on the longer side is a pure INSERTED SPAN (queue growth).
  - if both changed regions are short (<=6 bytes) and same length, it's a
    SMALL_DELTA (counter/flag tick).
  - otherwise it's OTHER (structural change, e.g. template swap).
"""
import csv
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from map_common import load, body_walk, packed_chain_walk, build_identity_labeler

OUT_CSV = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/q2_spans.csv"


def diff_regions(a: bytes, b: bytes):
    n = min(len(a), len(b))
    lcp = 0
    while lcp < n and a[lcp] == b[lcp]:
        lcp += 1
    max_lcs = n - lcp
    lcs = 0
    while lcs < max_lcs and a[len(a) - 1 - lcs] == b[len(b) - 1 - lcs]:
        lcs += 1
    changed_a = a[lcp:len(a) - lcs] if lcs else a[lcp:]
    changed_b = b[lcp:len(b) - lcs] if lcs else b[lcp:]
    return lcp, lcs, changed_a, changed_b


def main():
    L = build_identity_labeler()
    rows = []
    for fkey in ("a", "b"):
        name, data = load(fkey)
        body, log_end = body_walk(data)
        packed = packed_chain_walk(data, log_end)
        packed_by_n = {p["n"]: p for p in packed}
        idents = [L(e) for e in body]

        by_ident = {}
        for idx, e in enumerate(body):
            n = idx + 1
            ident = idents[idx]
            p = packed_by_n.get(n)
            if p is None:
                continue
            body_bytes = bytes(p["payload"][2:])  # strip [n][0x0a] marker
            by_ident.setdefault(ident, []).append((n, body_bytes))

        for ident, occ in sorted(by_ident.items()):
            for i in range(1, len(occ)):
                n_from, a_body = occ[i - 1]
                n_to, b_body = occ[i]
                if a_body == b_body:
                    continue  # unchanged, not interesting
                lcp, lcs, changed_a, changed_b = diff_regions(a_body, b_body)
                shorter_changed = changed_a if len(a_body) <= len(b_body) else changed_b
                longer_changed = changed_b if len(a_body) <= len(b_body) else changed_a
                if len(shorter_changed) == 0 and len(longer_changed) >= 7:
                    kind = "INSERTED_SPAN"
                elif len(changed_a) <= 6 and len(changed_b) <= 6:
                    kind = "SMALL_DELTA"
                else:
                    kind = "OTHER"
                rows.append({
                    "file": fkey,
                    "identity": ident,
                    "n_from": n_from,
                    "n_to": n_to,
                    "len_from": len(a_body),
                    "len_to": len(b_body),
                    "lcp": lcp,
                    "lcs": lcs,
                    "changed_a_len": len(changed_a),
                    "changed_b_len": len(changed_b),
                    "kind": kind,
                    "changed_a_hex": changed_a.hex(),
                    "changed_b_hex": changed_b.hex(),
                })

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} transition rows to {OUT_CSV}")
    print()
    from collections import Counter
    kinds = Counter(r["kind"] for r in rows)
    print("Kind counts:", dict(kinds))
    print()
    print("=== INSERTED_SPAN rows ===")
    for r in rows:
        if r["kind"] == "INSERTED_SPAN":
            print(f"  {r['file']} {r['identity']} n{r['n_from']}->n{r['n_to']} "
                  f"len {r['len_from']}->{r['len_to']} span_len={r['changed_b_len']}")
    print()
    print("=== SMALL_DELTA rows ===")
    for r in rows:
        if r["kind"] == "SMALL_DELTA":
            print(f"  {r['file']} {r['identity']} n{r['n_from']}->n{r['n_to']} "
                  f"len {r['len_from']}->{r['len_to']}  "
                  f"old={r['changed_a_hex']} new={r['changed_b_hex']}")
    print()
    print("=== OTHER rows ===")
    for r in rows:
        if r["kind"] == "OTHER":
            print(f"  {r['file']} {r['identity']} n{r['n_from']}->n{r['n_to']} "
                  f"len {r['len_from']}->{r['len_to']} lcp={r['lcp']} lcs={r['lcs']} "
                  f"changed_a_len={r['changed_a_len']} changed_b_len={r['changed_b_len']}")


if __name__ == "__main__":
    main()
