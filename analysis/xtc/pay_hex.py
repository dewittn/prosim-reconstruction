#!/usr/bin/env python3
"""Utility: dump hex of a payload given (file, n), or dedup group index."""
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_anchor import FILES, chain_walk, get_payloads
from collections import defaultdict

def hexdump(b, width=16):
    lines = []
    for i in range(0, len(b), width):
        chunk = b[i:i+width]
        hexs = " ".join(f"{c:02x}" for c in chunk)
        asci = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
        lines.append(f"{i:5d}  {hexs:<{width*3}}  {asci}")
    return "\n".join(lines)

def get_payload(tag, n):
    cfg = FILES[tag]
    data = open(cfg["path"], "rb").read()
    markers = chain_walk(data, cfg["pk_start"], cfg["maxn"])
    payloads = dict(get_payloads(data, markers, len(data)))
    return payloads[n]

def leb128(data, off, maxbytes=6):
    result = 0
    shift = 0
    start = off
    for i in range(maxbytes):
        if off >= len(data):
            return None, off
        b = data[off]
        result |= (b & 0x7f) << shift
        off += 1
        if not (b & 0x80):
            return result, off
        shift += 7
    return None, off  # too long

if __name__ == "__main__":
    tag = sys.argv[1]
    n = int(sys.argv[2])
    p = get_payload(tag, n)
    print(f"payload ({tag},{n}) len={len(p)}")
    print(hexdump(p))
