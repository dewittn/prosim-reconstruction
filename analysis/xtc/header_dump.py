#!/usr/bin/env python3
"""Dump raw header bytes from both XTC files and confirm hex matches the
hand-transcribed hex given in the task, catching any transcription errors."""
import struct

FILES = [
    "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
]

HEADER_LEN = 87

for path in FILES:
    with open(path, "rb") as f:
        data = f.read()
    header = data[:HEADER_LEN]
    print(f"=== {path} (total {len(data)} bytes) ===")
    print(" ".join(f"{b:02x}" for b in header))
    print()

    # offsets 0..86 annotated
    for i, b in enumerate(header):
        print(f"{i:3d}: 0x{b:02x} ({b:3d}) {repr(chr(b)) if 32<=b<127 else ''}")
    print()
