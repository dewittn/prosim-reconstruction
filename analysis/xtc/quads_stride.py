#!/usr/bin/env python3
"""Step through the file at fixed 17-byte stride starting from offset 87 (first 0x15 marker),
treating the record region as a contiguous array of 17-byte records: 1 marker byte + 4 float32 LE.
This avoids false '0x15 inside float bytes' matches from the naive scan.
Stop when records clearly become garbage (huge/nan-like floats) for a stretch.
"""
import struct
import json

def is_plausible(f1, f2, f3, f4):
    # operator-ish or 2.8-type or small-magnitude sensible floats
    if abs(f1) > 1e6 or abs(f2) > 1e6 or abs(f3) > 1e7 or abs(f4) > 1e7:
        return False
    return True

def stride_scan(path, base=87, stride=17, max_records=2000):
    with open(path, 'rb') as f:
        data = f.read()
    n = len(data)
    records = []
    off = base
    while off + 17 <= n and len(records) < max_records:
        marker = data[off]
        chunk = data[off+1:off+17]
        f1, f2, f3, f4 = struct.unpack('<ffff', chunk)
        records.append({'offset': off, 'marker': marker, 'f1': f1, 'f2': f2, 'f3': f3, 'f4': f4,
                         'plausible': is_plausible(f1, f2, f3, f4)})
        off += stride
    return records, n

def main():
    files = {
        'prosim.xtc': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc',
        'prosim1.xtc': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc',
    }
    for name, path in files.items():
        records, n = stride_scan(path)
        print(f"=== {name} (size {n}) === stride records from base=87: {len(records)}")
        # find where plausibility breaks down for a sustained run
        run_bad = 0
        cutoff_idx = None
        for i, r in enumerate(records):
            if not r['plausible']:
                run_bad += 1
                if run_bad >= 3 and cutoff_idx is None:
                    cutoff_idx = i - run_bad + 1
            else:
                run_bad = 0
        print(f"first sustained-implausible run starts at index: {cutoff_idx}")
        for i, r in enumerate(records[:max(cutoff_idx or 0, 0)+5] if cutoff_idx else records[:100]):
            marker_hex = hex(r['marker'])
            flag = '' if r['plausible'] else '  <IMPLAUSIBLE>'
            print(f"[{i:3d}] off={r['offset']:6d} marker={marker_hex}  f1={r['f1']:9.4f} f2={r['f2']:9.4f} f3={r['f3']:14.3f} f4={r['f4']:12.3f}{flag}")
        print()

if __name__ == '__main__':
    main()
