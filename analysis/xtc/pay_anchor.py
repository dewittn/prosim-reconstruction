#!/usr/bin/env python3
"""Align body-log entries (0x15 float-quad + 0x12 sep, in order from offset 87) with
packed-region payloads (n=1..maxn), then search each payload for float32/int encodings
of that record's f3/f4 accumulator values.
"""
import struct

FILES = {
    "a": {
        "path": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
        "body_start": 87, "body_end": 912,
        "pk_start": 912, "maxn": 49,
    },
    "b": {
        "path": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
        "body_start": 87, "body_end": 1355,
        "pk_start": 1355, "maxn": 76,
    },
}

def parse_body(data, start, end):
    pos = start
    entries = []
    while pos < end:
        b = data[pos]
        if b == 0x15:
            fl = struct.unpack_from("<4f", data, pos+1)
            entries.append(("15", fl))
            pos += 17
        elif b == 0x12:
            entries.append(("12", None))
            pos += 1
        else:
            pos += 1
    return entries

def chain_walk(data, start, maxn):
    markers = []
    pos = start
    for n in range(1, maxn + 1):
        found = None
        i = pos
        while i < len(data) - 1:
            if data[i] == (n & 0xFF) and data[i + 1] == 0x0a:
                found = i
                break
            i += 1
        if found is None:
            break
        markers.append((n, found, found + 2))
        pos = found + 2
    return markers

def get_payloads(data, markers, eof):
    out = []
    for idx, (n, moff, pstart) in enumerate(markers):
        pend = markers[idx+1][1] if idx+1 < len(markers) else eof
        out.append((n, data[pstart:pend]))
    return out

def search_float(payload, target, tol=0.02):
    hits = []
    for off in range(0, len(payload) - 3):
        v = struct.unpack_from("<f", payload, off)[0]
        if abs(v - target) <= tol * max(1, abs(target)):
            hits.append((off, "f32le", v))
    for off in range(0, len(payload) - 3):
        v = struct.unpack_from(">f", payload, off)[0]
        if abs(v - target) <= tol * max(1, abs(target)):
            hits.append((off, "f32be", v))
    return hits

def search_int_scaled(payload, target):
    hits = []
    candidates = {
        "round": round(target),
        "round/10": round(target/10),
        "round*10": round(target*10),
        "round*100": round(target*100),
        "trunc": int(target),
    }
    for label, val in candidates.items():
        if val == 0:
            continue
        for width, fmt in [(2, "<h"), (2, ">h"), (2, "<H"), (2, ">H"),
                            (4, "<i"), (4, ">i"), (4, "<I"), (4, ">I")]:
            for off in range(0, len(payload) - width + 1):
                try:
                    v = struct.unpack_from(fmt, payload, off)[0]
                except struct.error:
                    continue
                if v == val:
                    hits.append((off, label, fmt, val))
    return hits

def main():
    for tag, cfg in FILES.items():
        data = open(cfg["path"], "rb").read()
        body = parse_body(data, cfg["body_start"], cfg["body_end"])
        markers = chain_walk(data, cfg["pk_start"], cfg["maxn"])
        payloads = get_payloads(data, markers, len(data))
        print(f"=== FILE {tag}: body_entries={len(body)} payloads={len(payloads)} ===")
        assert len(body) == len(payloads), f"MISMATCH {len(body)} vs {len(payloads)}"
        for (kind, fl), (n, payload) in zip(body, payloads):
            if kind == "12":
                continue
            f1, f2, f3, f4 = fl
            fhits3 = search_float(payload, f3)
            fhits4 = search_float(payload, f4)
            ihits3 = search_int_scaled(payload, f3)
            ihits4 = search_int_scaled(payload, f4)
            if fhits3 or fhits4 or ihits3 or ihits4:
                print(f"  n={n:3d} len={len(payload):4d} f3={f3:.2f} f4={f4:.2f}")
                if fhits3: print(f"      f3 float hits: {fhits3}")
                if fhits4: print(f"      f4 float hits: {fhits4}")
                if ihits3: print(f"      f3 int hits: {ihits3[:6]}{'...' if len(ihits3)>6 else ''}")
                if ihits4: print(f"      f4 int hits: {ihits4[:6]}{'...' if len(ihits4)>6 else ''}")

if __name__ == "__main__":
    main()
