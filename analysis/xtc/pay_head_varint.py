#!/usr/bin/env python3
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_anchor import FILES, parse_body, chain_walk, get_payloads
from collections import defaultdict

def leb128_stream(data, n=12):
    """Decode n sequential LEB128 varints from start of data, return list of (value, nbytes, raw_hex)."""
    out = []
    off = 0
    for _ in range(n):
        if off >= len(data):
            break
        result = 0
        shift = 0
        start = off
        while True:
            if off >= len(data):
                out.append((None, off - start, data[start:off].hex()))
                return out
            b = data[off]
            result |= (b & 0x7f) << shift
            off += 1
            shift += 7
            if not (b & 0x80):
                break
        out.append((result, off - start, data[start:off].hex()))
    return out

def main():
    id_to_core = {}
    id_to_records = defaultdict(list)
    for tag, cfg in FILES.items():
        data = open(cfg["path"], "rb").read()
        body = parse_body(data, cfg["body_start"], cfg["body_end"])
        markers = chain_walk(data, cfg["pk_start"], cfg["maxn"])
        payloads = get_payloads(data, markers, len(data))
        for (kind, fl), (n, payload) in zip(body, payloads):
            if kind != "15":
                continue
            f1, f2, f3, f4 = fl
            key = (round(f1, 6), round(f2, 6))
            id_to_records[key].append(bytes(payload))

    for key, plist in sorted(id_to_records.items()):
        core = min(plist, key=len)
        f1, f2 = key
        varints = leb128_stream(core, 8)
        print(f"id=(f1={f1:.6f}, f2={f2:.6f})  core_len={len(core)}")
        print(f"   raw head: {core[:20].hex(' ')}")
        print(f"   varints: {varints}")
        # check simple scalings
        for label, val in [("f1*100", f1*100), ("f2*100", f2*100), ("f1*1000", f1*1000),
                            ("f2*1000", f2*1000), ("1/f1*100", 100/f1 if f1 else 0),
                            ("1/f2*100", 100/f2 if f2 else 0), ("f1*f2*1000", f1*f2*1000)]:
            print(f"     {label} = {val:.2f}")
        print()

if __name__ == "__main__":
    main()
