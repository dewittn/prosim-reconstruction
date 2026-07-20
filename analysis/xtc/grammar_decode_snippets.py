#!/usr/bin/env python3
"""Decode specific byte snippets as floats/ints to understand recurring patterns."""
import struct

def f32(bs):
    return struct.unpack("<f", bytes(bs))[0]

def i32(bs):
    return struct.unpack("<i", bytes(bs))[0]

def u32(bs):
    return struct.unpack("<I", bytes(bs))[0]

def show(label, hexstr):
    bs = bytes.fromhex(hexstr.replace(" ", ""))
    print(f"{label}: hex={hexstr}  len={len(bs)}")
    # try as sequence of floats if divisible by 4
    if len(bs) % 4 == 0:
        floats = struct.unpack(f"<{len(bs)//4}f", bs)
        print(f"   as floats: {floats}")
    # try skipping leading bytes to align to 4
    for skip in range(1, 4):
        rem = bs[skip:]
        if len(rem) % 4 == 0 and len(rem) > 0:
            floats = struct.unpack(f"<{len(rem)//4}f", rem)
            print(f"   skip {skip} byte(s), as floats: {floats}  (skipped={bs[:skip].hex()})")
    print()

# Recurring header float pattern
show("header trailing '3a 33 40' variants", "06 3a 33 40")
show("header 'a0 3a 33 40'", "a0 3a 33 40")
show("'15 a0 3a 33 40'", "15 a0 3a 33 40")

print("=" * 60)
# gap=13 pattern (candidate distinct record, first 8 bytes constant)
show("gap13 prefix (2 floats)", "70 2e 4f 3f a3 00 0f 3f")
show("gap13 full (pos223, prosim.xtc)", "15 70 2e 4f 3f a3 00 0f 3f 71 5f 20 46")
show("gap13 full (pos376)", "15 70 2e 4f 3f a3 00 0f 3f 71 f7 6e 46")
show("gap13 full (pos648)", "15 70 2e 4f 3f a3 00 0f 3f b9 bb 82 46")

print("=" * 60)
# gap=7 pattern
show("gap7 full (pos172)", "15 6b 9e 51 3f 55 55")
show("gap7 full (pos342)", "15 6b 9e 51 3f 55 55")

print("=" * 60)
# gap=10 pattern
show("gap10 full (pos179)", "15 3f bd 5a 2a 46 56 6d fa 44")
show("gap10 full (pos349)", "15 3f 5e e5 80 46 ab 06 52 45")

print("=" * 60)
# gap=4 pattern
show("gap4 full (pos236)", "15 f7 87 45")
show("gap4 full (pos389)", "15 37 8d 45")

print("=" * 60)
# gap=26 pattern with embedded tag 0x12
show("gap26 full (prosim1 pos818)", "15 61 b3 4e 3f da e9 11 3f 22 5d 83 46 f2 f3 8e 45 12 1e 39 33 40 06 3a 33 40")
show("gap26 tail after second 0x15-record (tag 0x12 + payload)", "12 1e 39 33 40 06 3a 33 40")

print("=" * 60)
# canonical 17-byte record (tag 0x15 + 4 floats) from header area / early body
show("canonical 17B record sample1", "15 a0 3a 33 40 06 3a 33 40")  # only 9 bytes shown, need more context
