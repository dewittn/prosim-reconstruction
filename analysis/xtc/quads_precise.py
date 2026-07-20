#!/usr/bin/env python3
"""Dump the 44-record table with full float precision on f1/f2 to check whether
apparent 'n=8' style identity groups are really 2 distinct near-identical operators
merged by 3-decimal rounding, or genuinely 8 occurrences of ONE identity."""
import struct

def extract(path, base=87, stride=17, count=44):
    with open(path, 'rb') as f:
        data = f.read()
    recs = []
    off = base
    for i in range(count):
        f1, f2, f3, f4 = struct.unpack('<ffff', data[off+1:off+17])
        recs.append({'idx': i, 'offset': off, 'f1': f1, 'f2': f2, 'f3': f3, 'f4': f4})
        off += stride
    return recs

def main():
    files = {
        'prosim.xtc': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc',
        'prosim1.xtc': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc',
    }
    for name, path in files.items():
        recs = extract(path)
        print(f"=== {name} ===")
        # sort by f1 to cluster visually
        for r in sorted(recs, key=lambda r: (r['f1'], r['f2'])):
            print(f"idx={r['idx']:3d} f1={r['f1']:.6f} f2={r['f2']:.6f} f3={r['f3']:14.3f} f4={r['f4']:12.3f}  prof_est(f1*1.088)={r['f1']*1.088:.4f}")
        print()

if __name__ == '__main__':
    main()
