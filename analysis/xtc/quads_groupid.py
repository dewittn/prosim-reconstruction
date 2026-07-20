#!/usr/bin/env python3
"""Extract the clean 44-record marker=0x15 array (stride 17 from base 87) for each file,
group records by rounded (f1,f2) identity, and show per-identity f3/f4 sequences in file order."""
import struct
from collections import OrderedDict

def extract(path, base=87, stride=17, count=44):
    with open(path, 'rb') as f:
        data = f.read()
    recs = []
    off = base
    for i in range(count):
        marker = data[off]
        f1, f2, f3, f4 = struct.unpack('<ffff', data[off+1:off+17])
        recs.append({'idx': i, 'offset': off, 'marker': marker, 'f1': f1, 'f2': f2, 'f3': f3, 'f4': f4})
        off += stride
    return recs

def main():
    files = {
        'prosim.xtc (week9, 9 ops)': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc',
        'prosim1.xtc (week13, 13 ops)': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc',
    }
    for name, path in files.items():
        recs = extract(path)
        print(f"=== {name} === ({len(recs)} records)")
        groups = OrderedDict()
        for r in recs:
            key = (round(r['f1'], 3), round(r['f2'], 3))
            groups.setdefault(key, []).append(r)
        print(f"unique identity groups: {len(groups)}")
        for key, items in groups.items():
            f3s = [round(it['f3'], 2) for it in items]
            f4s = [round(it['f4'], 2) for it in items]
            idxs = [it['idx'] for it in items]
            print(f"  id={key}  n={len(items)}  idxs={idxs}")
            print(f"      f3 seq: {f3s}")
            print(f"      f4 seq: {f4s}")
        print()

if __name__ == '__main__':
    main()
