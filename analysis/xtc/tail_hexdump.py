#!/usr/bin/env python3
"""Hex dump around the boundary where 0x15 records stop, and near the end, for both files."""

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

def hexdump(data, start, length, width=16):
    lines = []
    end = min(start + length, len(data))
    for off in range(start, end, width):
        chunk = data[off:off+width]
        hexs = " ".join(f"{b:02x}" for b in chunk)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{off:6d}: {hexs:<48} {asc}")
    return "\n".join(lines)

with open(FILES["prosim.xtc"], "rb") as f:
    d0 = f.read()
with open(FILES["prosim1.xtc"], "rb") as f:
    d1 = f.read()

print("### prosim.xtc around last 0x15 hit (895) to 2048 ###")
print(hexdump(d0, 880, 2048 - 880))
print()
print("### prosim.xtc tail (last 640 bytes) ###")
print(hexdump(d0, len(d0) - 640, 640))
print()
print("### prosim1.xtc around last 0x15 hit (1338) to 2048 ###")
print(hexdump(d1, 1320, 2048 - 1320))
print()
print("### prosim1.xtc tail (last 640 bytes) ###")
print(hexdump(d1, len(d1) - 640, 640))
