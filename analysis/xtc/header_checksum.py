#!/usr/bin/env python3
"""Test checksum / counter hypotheses for header bytes 1-3 (LE uint24)."""
import struct

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

for name, path in FILES.items():
    with open(path, "rb") as f:
        data = f.read()
    b1, b2, b3 = data[1], data[2], data[3]
    uint24 = b1 | (b2 << 8) | (b3 << 16)
    uint16_12 = b1 | (b2 << 8)  # just bytes 1-2

    total_len = len(data)
    sum_all = sum(data)
    sum_from4 = sum(data[4:])  # sum of everything after the candidate checksum field
    sum_from1_excl123 = sum(data[0:1]) + sum(data[4:])
    sum_mod_65536 = sum_all % 65536
    sum_mod_2_24 = sum_all % (2**24)

    print(f"=== {name} ===")
    print(f"file length: {total_len}")
    print(f"byte0: {data[0]:#04x}")
    print(f"bytes1-3 LE uint24: {uint24}  (hex {uint24:#08x})")
    print(f"bytes1-2 LE uint16: {uint16_12}")
    print(f"sum of ALL bytes in file: {sum_all}  (mod 2^24: {sum_all % (2**24)}, mod 65536: {sum_all%65536})")
    print(f"sum of bytes[4:] (everything after field): {sum_from4} (mod 2^24: {sum_from4%(2**24)})")
    print(f"sum of bytes[87:] (body only, excluding header): {sum(data[87:])}")
    print(f"file_length - 4: {total_len-4}")
    print(f"file_length in hex: {total_len:#x}")
    print()

# cross check: is uint24 close to file length, or a multiple of record size?
print("--- ratio checks ---")
for name, path in FILES.items():
    with open(path, "rb") as f:
        data = f.read()
    b1, b2, b3 = data[1], data[2], data[3]
    uint24 = b1 | (b2 << 8) | (b3 << 16)
    print(f"{name}: uint24={uint24}, file_len={len(data)}, uint24/file_len={uint24/len(data):.4f}, file_len - 87 (body len) = {len(data)-87}, uint24 - body_len = {uint24 - (len(data)-87)}")
