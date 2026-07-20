#!/usr/bin/env python3
"""Extract packed-region records via chain-walk: marker [n][0x0a], n=1,2,3,...
Payload = bytes between end of marker n and start of marker n+1 (or EOF for last).
"""
import struct

FILES = {
    "a": ("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc", 912, 49),
    "b": ("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc", 1355, 76),
}

def chain_walk(data, start, maxn):
    """Find markers [n][0x0a] for n=1..maxn, earliest occurrence after previous marker end."""
    markers = []  # (n, marker_offset, payload_start)
    pos = start
    for n in range(1, maxn + 1):
        # search for byte==n, next byte==0x0a, starting at pos
        found = None
        i = pos
        while i < len(data) - 1:
            if data[i] == (n & 0xFF) and data[i + 1] == 0x0a:
                found = i
                break
            i += 1
        if found is None:
            print(f"  n={n}: NOT FOUND from pos={pos}")
            break
        markers.append((n, found, found + 2))
        pos = found + 2
    return markers

def main():
    results = {}
    for tag, (path, start, maxn) in FILES.items():
        data = open(path, "rb").read()
        print(f"=== file {tag}: {path} len={len(data)} start={start} maxn={maxn} ===")
        markers = chain_walk(data, start, maxn)
        print(f"  found {len(markers)} markers")
        payloads = []
        for idx, (n, moff, pstart) in enumerate(markers):
            if idx + 1 < len(markers):
                pend = markers[idx + 1][1]  # up to next marker byte
            else:
                pend = len(data)
            payload = data[pstart:pend]
            payloads.append((n, moff, payload))
        results[tag] = payloads
        print(f"  payload size range: {min(len(p) for _,_,p in payloads)}-{max(len(p) for _,_,p in payloads)}")
    return results

if __name__ == "__main__":
    main()
