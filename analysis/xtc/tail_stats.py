#!/usr/bin/env python3
"""Tasks 2,3,5,7: entropy profiling, bit-width symbol scan, numeric reinterpretation,
and detailed look at prosim.xtc's final 512-byte low-entropy block."""
import math
import struct
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

def sliding_entropy(data, window=256, step=128):
    out = []
    for i in range(0, len(data) - window + 1, step):
        w = data[i:i+window]
        out.append((i, shannon_entropy(w)))
    return out

print("=== Sliding-window entropy (window=256, step=128) ===")
for name, data in [("prosim.xtc", d0), ("prosim1.xtc", d1)]:
    print(f"\n-- {name} --")
    se = sliding_entropy(data, 256, 128)
    # print only where entropy dips notably (< 6.5) or at start/end
    low = [(o, e) for o, e in se if e < 6.5]
    print(f"Windows with entropy < 6.5 bits/byte: {len(low)} of {len(se)}")
    for o, e in low:
        print(f"  offset {o:6d}: entropy={e:.3f}")

print("\n=== Final 512 bytes of prosim.xtc: detailed entropy in 64-byte sub-windows ===")
tail512 = d0[-512:]
for i in range(0, 512, 64):
    w = tail512[i:i+64]
    print(f"  rel {i:3d} (abs {len(d0)-512+i}): entropy={shannon_entropy(w):.3f}  hex={w[:16].hex()}...")

print("\n=== Byte histogram of prosim.xtc final 512 bytes (top 20) ===")
c = Counter(tail512)
for b, cnt in c.most_common(20):
    print(f"  0x{b:02x}: {cnt}")

print("\n=== Does prosim1.xtc have an equally low-entropy final block anywhere? ===")
se1 = sliding_entropy(d1, 256, 64)
se1.sort(key=lambda x: x[1])
print("10 lowest-entropy 256B windows in prosim1.xtc:")
for o, e in se1[:10]:
    print(f"  offset {o:6d}: entropy={e:.3f}")

# Bit-width symbol scan
def bits_from_bytes(data, msb_first=True):
    bits = []
    for b in data:
        if msb_first:
            bits.extend((b >> (7-k)) & 1 for k in range(8))
        else:
            bits.extend((b >> k) & 1 for k in range(8))
    return bits

def symbol_entropy_for_width(bits, width):
    n = len(bits) // width
    syms = []
    for i in range(n):
        v = 0
        chunk = bits[i*width:(i+1)*width]
        for bit in chunk:
            v = (v << 1) | bit
        syms.append(v)
    c = Counter(syms)
    tot = len(syms)
    ent = -sum((v/tot) * math.log2(v/tot) for v in c.values())
    return ent, c, syms

print("\n=== Bit-width symbol entropy scan on prosim.xtc final 512-byte block ===")
for order_name, msb in [("MSB-first", True), ("LSB-first", False)]:
    bits = bits_from_bytes(tail512, msb)
    print(f"\n-- bit order: {order_name} --")
    for width in range(3, 13):
        ent, c, syms = symbol_entropy_for_width(bits, width)
        max_possible = math.log2(min(len(c), 2**width)) if c else 0
        print(f"  width={width:2d}: symbol-entropy={ent:.3f} bits (max={width}), unique_symbols={len(c)}, most_common={c.most_common(5)}")

print("\n=== Numeric reinterpretation of prosim.xtc final 512-byte block ===")
def frac_plausible_float32(data):
    n = 0
    total = 0
    for i in range(len(data) - 3):
        total += 1
        v = struct.unpack("<f", data[i:i+4])[0]
        if v == v and 1e-3 <= abs(v) <= 1e7:
            n += 1
    return n, total

def frac_plausible_double(data):
    n = 0
    total = 0
    for i in range(len(data) - 7):
        total += 1
        v = struct.unpack("<d", data[i:i+8])[0]
        if v == v and 1e-3 <= abs(v) <= 1e7:
            n += 1
    return n, total

def frac_plausible_u16(data):
    n = 0
    total = 0
    for i in range(len(data) - 1):
        total += 1
        v = struct.unpack("<H", data[i:i+2])[0]
        if 0 <= v <= 5000:
            n += 1
    return n, total

n, t = frac_plausible_float32(tail512)
print(f"float32 (LE) plausible fraction: {n}/{t} = {n/t:.3f}")
n, t = frac_plausible_double(tail512)
print(f"double (LE) plausible fraction: {n}/{t} = {n/t:.3f}")
n, t = frac_plausible_u16(tail512)
print(f"uint16 (LE, 0-5000) plausible fraction: {n}/{t} = {n/t:.3f}")

# compare against a truly random baseline for reference
import os
rnd = os.urandom(512)
n, t = frac_plausible_float32(rnd)
print(f"[baseline random] float32 plausible fraction: {n}/{t} = {n/t:.3f}")
