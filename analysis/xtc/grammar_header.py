#!/usr/bin/env python3
"""Attempt to parse the header region (~first 90 bytes) as tag+len+payload records."""
import struct

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

def load(path):
    with open(path, "rb") as f:
        return f.read()

def hx(b):
    return " ".join(f"{x:02x}" for x in b)

for name, path in FILES.items():
    data = load(path)
    print(f"=== {name} ===")
    print("Bytes 0..90:")
    print(hx(data[0:90]))
    print()

    # Hypothesis: starting at some offset, records are TAG(1 ascii digit-ish byte) LEN(1 byte) PAYLOAD(LEN bytes)
    # We saw candidates at offset ~43 (0x32 '2'), ~54 (0x33 '3'), ~64 (0x38 '8')
    # Let's scan for byte values in ASCII digit range 0x30-0x39 and check if [pos+1] as length makes
    # pos+2+length land on another ASCII-digit byte (chaining hypothesis)
    print("Scanning offsets 0..120 for ASCII-digit tag bytes (0x30-0x39):")
    for i in range(0, 120):
        b = data[i]
        if 0x30 <= b <= 0x39:
            if i + 2 <= len(data):
                length = data[i+1]
                nxt = i + 2 + length
                nxt_byte = data[nxt] if nxt < len(data) else None
                marker = ""
                if nxt_byte is not None and 0x30 <= nxt_byte <= 0x39:
                    marker = "  <-- chains to next digit tag!"
                print(f"  off={i:3d} tag=0x{b:02x} ({chr(b)!r}) len_byte(+1)=0x{data[i+1]:02x}({data[i+1]}) "
                      f"payload_end={nxt} next_byte={nxt_byte if nxt_byte is None else hex(nxt_byte)}{marker}")
    print()

    # Try explicit chain starting at first digit tag found >= offset 40
    print("Attempting explicit chain parse from offset 43:")
    pos = 43
    for _ in range(10):
        if pos >= len(data):
            break
        tag = data[pos]
        if not (0x30 <= tag <= 0x39):
            print(f"  STOP at off={pos}: byte 0x{tag:02x} not ascii-digit")
            break
        length = data[pos+1]
        payload = data[pos+2:pos+2+length]
        print(f"  off={pos:3d} tag='{chr(tag)}' len={length:3d} payload={hx(payload)}")
        # try float interpretation of trailing 4-byte chunks
        if len(payload) >= 4 and len(payload) % 4 == 0:
            floats = struct.unpack(f"<{len(payload)//4}f", payload)
            print(f"           as floats: {floats}")
        pos = pos + 2 + length
    print()
