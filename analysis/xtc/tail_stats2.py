#!/usr/bin/env python3
"""Reconcile entropy of final 512B block with various methods; autocorrelation lags 1-64
over the WHOLE tail (not just final block); compression hypothesis tests (zlib, LZSS
flag-byte-every-9, RLE)."""
import math
import zlib
from collections import Counter

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}
with open(FILES["prosim.xtc"], "rb") as f:
    d0 = f.read()
with open(FILES["prosim1.xtc"], "rb") as f:
    d1 = f.read()

def shannon_entropy(data):
    if not data:
        return 0.0
    c = Counter(data)
    n = len(data)
    return -sum((v/n) * math.log2(v/n) for v in c.values())

print("=== Reconcile entropy of prosim.xtc final block, various window sizes ===")
for size in [128, 256, 384, 512, 768, 1024, 2048]:
    chunk = d0[-size:]
    print(f"  last {size:5d} bytes: entropy={shannon_entropy(chunk):.3f} bits/byte")

print("\n=== Whole-tail entropy for comparison (from offset 895 onward) ===")
print(f"  prosim.xtc tail (895:end): entropy={shannon_entropy(d0[895:]):.3f}")
print(f"  prosim1.xtc tail (1338:end): entropy={shannon_entropy(d1[1338:]):.3f}")

print("\n=== 4-bit nibble entropy of final 512 bytes (low nibble, high nibble separately) ===")
tail512 = d0[-512:]
lo = [b & 0xF for b in tail512]
hi = [b >> 4 for b in tail512]
print(f"  low nibble entropy: {shannon_entropy(lo):.3f} / 4")
print(f"  high nibble entropy: {shannon_entropy(hi):.3f} / 4")

# Autocorrelation over the WHOLE tail region, lags 1-64
print("\n=== Byte-level autocorrelation, lags 1-64 (fraction of matching bytes at lag) ===")
for name, data, tail_start in [("prosim.xtc", d0, 895), ("prosim1.xtc", d1, 1338)]:
    tail = data[tail_start:]
    print(f"\n-- {name} tail (len={len(tail)}) --")
    baseline = 1/256  # expected match rate for random bytes
    results = []
    for lag in range(1, 65):
        matches = sum(1 for i in range(len(tail) - lag) if tail[i] == tail[i+lag])
        total = len(tail) - lag
        rate = matches / total
        results.append((lag, rate))
    results.sort(key=lambda x: -x[1])
    print(f"  baseline random match rate ~ {baseline:.5f}")
    print("  Top 10 lags by match rate:")
    for lag, rate in results[:10]:
        print(f"    lag={lag:3d}: rate={rate:.5f} ({rate/baseline:.2f}x baseline)")

# Compression hypothesis tests
print("\n=== zlib/raw-deflate decompression attempts ===")
for name, data, tail_start in [("prosim.xtc", d0, 895), ("prosim1.xtc", d1, 1338)]:
    tail = data[tail_start:]
    found_any = False
    # try zlib header at every offset
    for i in range(min(len(tail), 4000)):
        try:
            out = zlib.decompress(tail[i:])
            print(f"  {name}: zlib.decompress SUCCESS at tail-relative offset {i}, output len {len(out)}")
            found_any = True
        except Exception:
            pass
        # raw deflate (no header)
        try:
            do = zlib.decompressobj(wbits=-15)
            out = do.decompress(tail[i:i+2000])
            if len(out) > 32:
                print(f"  {name}: raw-deflate produced {len(out)} bytes from offset {i} (first 32: {out[:32]})")
                found_any = True
        except Exception:
            pass
    if not found_any:
        print(f"  {name}: no zlib/raw-deflate success found in first 4000 bytes of tail")

# LZSS heuristic: does a flag byte appear every 9 bytes? test by checking, for each of first
# 9 phase offsets, how often byte at phase position has an unusually invariant bit-count pattern
print("\n=== LZSS flag-byte-every-9 heuristic ===")
for name, data, tail_start in [("prosim.xtc", d0, 895), ("prosim1.xtc", d1, 1338)]:
    tail = data[tail_start:]
    print(f"\n-- {name} --")
    for phase in range(9):
        vals = [tail[i] for i in range(phase, min(len(tail), phase + 9*200), 9)]
        c = Counter(vals)
        ent = shannon_entropy(bytes(vals))
        print(f"  phase {phase}: entropy={ent:.3f}, most_common={c.most_common(3)}")

# RLE structure check: run-length distribution of repeated bytes
print("\n=== Run-length distribution (consecutive identical bytes) ===")
for name, data, tail_start in [("prosim.xtc", d0, 895), ("prosim1.xtc", d1, 1338)]:
    tail = data[tail_start:]
    runs = Counter()
    i = 0
    while i < len(tail):
        j = i
        while j < len(tail) and tail[j] == tail[i]:
            j += 1
        runs[j-i] += 1
        i = j
    print(f"  {name}: run-length histogram (top 10): {runs.most_common(10)}")
