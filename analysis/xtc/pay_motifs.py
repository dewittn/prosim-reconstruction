#!/usr/bin/env python3
"""Find repeated n-grams and zero-runs in a given payload (identify motifs)."""
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_hex import get_payload
from collections import Counter
import re

def main():
    tag, n = sys.argv[1], int(sys.argv[2])
    p = get_payload(tag, n)
    print(f"payload ({tag},{n}) len={len(p)}")

    for gram in (2, 3, 4):
        c = Counter()
        for i in range(len(p) - gram + 1):
            c[bytes(p[i:i+gram])] += 1
        top = [(k, v) for k, v in c.items() if v >= 3]
        top.sort(key=lambda kv: -kv[1])
        print(f"  {gram}-grams occurring >=3x: {len(top)}")
        for k, v in top[:10]:
            print(f"    {k.hex()} x{v}")

    # zero runs
    print("  zero runs (len>=2):")
    for m in re.finditer(rb"\x00{2,}", bytes(p)):
        print(f"    offset={m.start()} len={m.end()-m.start()}")

if __name__ == "__main__":
    main()
