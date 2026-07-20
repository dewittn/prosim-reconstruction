#!/usr/bin/env python3
"""Characterize the preamble between body-log end and packed-region start
(i.e. between last body entry and marker [1][0x0a])."""
import sys, math
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_anchor import FILES, chain_walk
from collections import Counter

def entropy(b):
    if not b:
        return 0.0
    c = Counter(b)
    n = len(b)
    return -sum((v/n) * math.log2(v/n) for v in c.values())

def main():
    preambles = {}
    for tag, cfg in FILES.items():
        data = open(cfg["path"], "rb").read()
        body_end = cfg["body_end"]
        pk_start = cfg["pk_start"]
        markers = chain_walk(data, pk_start, 1)  # just find marker 1
        m1_offset = markers[0][1]
        preamble = data[body_end:m1_offset]
        preambles[tag] = preamble
        print(f"=== {tag}: preamble = data[{body_end}:{m1_offset}]  len={len(preamble)} ===")
        print(f"  entropy: {entropy(preamble):.3f} bits/byte (max 8.0)")
        zero_count = preamble.count(0)
        print(f"  zero bytes: {zero_count}/{len(preamble)} ({100*zero_count/len(preamble):.1f}%)")
        ones_bits = sum(bin(b).count('1') for b in preamble)
        total_bits = len(preamble) * 8
        print(f"  bit density (1s): {ones_bits}/{total_bits} ({100*ones_bits/total_bits:.1f}%)")
        print(f"  hex (first 128 bytes):")
        for i in range(0, min(128, len(preamble)), 16):
            chunk = preamble[i:i+16]
            print(f"    {i:4d}  {chunk.hex(' ')}")

    a, b = preambles["a"], preambles["b"]
    print()
    print(f"a in b? {a in b}")
    print(f"b starts with a? {b.startswith(a)}")
    print(f"a starts with b[:len(a)]? {a == b[:len(a)]}")
    # find longest common prefix
    lcp = 0
    for x, y in zip(a, b):
        if x == y:
            lcp += 1
        else:
            break
    print(f"longest common prefix(a,b): {lcp} / {len(a)}")
    if lcp < len(a):
        print(f"  divergence: a[{lcp}:{lcp+16}]={a[lcp:lcp+16].hex(' ')}")
        print(f"              b[{lcp}:{lcp+16}]={b[lcp:lcp+16].hex(' ')}")
    # try common suffix
    lcs = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x == y:
            lcs += 1
        else:
            break
    print(f"longest common suffix(a,b): {lcs}")

if __name__ == "__main__":
    main()
