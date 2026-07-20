#!/usr/bin/env python3
"""Rigorous exact-match test for bytes 1-2 (LE uint16), now that byte 3 is
known to be a CONSTANT (0x01) across both files, not part of the varying
field. Tests: file length, body length, various 0x15-delimited record
counts, and simple arithmetic combinations, looking for an EXACT match
(not just 'close')."""
import struct

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}
data = {name: open(path, "rb").read() for name, path in FILES.items()}

for name, b in data.items():
    u16 = struct.unpack('<H', b[1:3])[0]
    file_len = len(b)
    body_len = file_len - 87

    total_15 = b.count(0x15)
    body_15 = b[87:].count(0x15)

    # stride-17 walk from offset 87: count how many consecutive 17-byte
    # records exist tagged with 0x15 at the start of each stride
    stride_count = 0
    i = 87
    while i < file_len and b[i] == 0x15:
        stride_count += 1
        i += 17

    # plausible operator float-pair record count (efficiency-range filter)
    plausible = 0
    for i in range(len(b)):
        if b[i] == 0x15 and i + 9 <= len(b):
            try:
                f1 = struct.unpack('<f', b[i+1:i+5])[0]
                f2 = struct.unpack('<f', b[i+5:i+9])[0]
                if 0.1 < f1 < 2.0 and 0.1 < f2 < 2.0:
                    plausible += 1
            except Exception:
                pass

    print(f"=== {name} ===")
    print(f"  uint16(bytes1-2) = {u16}")
    print(f"  file_len={file_len}  body_len={body_len}")
    print(f"  total 0x15 count (whole file) = {total_15}")
    print(f"  body 0x15 count = {body_15}")
    print(f"  stride-17-from-87 contiguous record count = {stride_count}")
    print(f"  plausible-operator-pair record count = {plausible}")
    print(f"  candidates: 2*file_len={2*file_len} (diff {u16-2*file_len})")
    print(f"  candidates: file_len+body_len={file_len+body_len} (diff {u16-(file_len+body_len)})")
    print(f"  candidates: body_15*250={body_15*250} (diff {u16-body_15*250})")
    print(f"  u16 / file_len = {u16/file_len:.6f}")
    print(f"  u16 / body_15 = {u16/body_15:.6f}" if body_15 else "")
    print(f"  u16 - file_len = {u16-file_len}")
    print(f"  u16 mod 256 = {u16 % 256}, u16 // 256 = {u16 // 256}")
    print()
