#!/usr/bin/env python3
"""Decode candidate sub-records in the header (offsets 10-86) as
tag+length+payload groups, compute float32/int interpretations of each
payload, and diff the two files field-by-field to identify the 'swap'."""
import struct

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

data = {}
for name, path in FILES.items():
    with open(path, "rb") as f:
        data[name] = f.read()

def f32(b, off):
    return struct.unpack('<f', b[off:off+4])[0]

def u16(b, off):
    return struct.unpack('<H', b[off:off+2])[0]

def i16(b, off):
    return struct.unpack('<h', b[off:off+2])[0]

def u32(b, off):
    return struct.unpack('<I', b[off:off+4])[0]

def i64(b, off):
    return struct.unpack('<q', b[off:off+8])[0]

print("=" * 100)
print("BYTE-BY-BYTE DIFF: bytes 0-86, both files")
print("=" * 100)
b1 = data["prosim.xtc"][:87]
b2 = data["prosim1.xtc"][:87]
for i in range(87):
    same = "SAME " if b1[i] == b2[i] else "DIFF "
    print(f"{i:3d}: {same}  prosim={b1[i]:#04x}({b1[i]:3d})   prosim1={b2[i]:#04x}({b2[i]:3d})")

print()
print("=" * 100)
print("CANDIDATE FLOAT32 at each offset 0-83 (LE), flag plausible ranges")
print("=" * 100)
for name in FILES:
    b = data[name]
    print(f"--- {name} ---")
    for off in range(0, 84):
        try:
            val = f32(b, off)
        except Exception:
            continue
        if val == val and abs(val) < 1e7 and val != 0:  # not NaN, reasonable magnitude
            # flag plausible business values
            flag = ""
            if 0.1 < abs(val) < 5:
                flag = "  <-- small factor/ratio range"
            elif 10 < abs(val) < 3000:
                flag = "  <-- plausible $ or hours/qty range"
            print(f"  off {off:3d}: {val:20.6f}{flag}")
    print()

print("=" * 100)
print("CANDIDATE VB CURRENCY (int64 LE / 10000) at each offset 0-79")
print("=" * 100)
for name in FILES:
    b = data[name]
    print(f"--- {name} ---")
    for off in range(0, 79):
        try:
            val = i64(b, off) / 10000.0
        except Exception:
            continue
        if 0 < abs(val) < 100000:
            print(f"  off {off:3d}: {val:14.4f}")
    print()
