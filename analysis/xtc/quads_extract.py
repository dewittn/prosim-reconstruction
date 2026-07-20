#!/usr/bin/env python3
"""Extract all 0x15 + 4x float32 (LE) quad records from an XTC file, in file order.
No value filtering. Report total counts and dump raw list.
"""
import struct
import sys
import json

def extract_quads(path):
    with open(path, 'rb') as f:
        data = f.read()
    quads = []
    n = len(data)
    for i in range(n):
        if data[i] == 0x15:
            if i + 17 <= n:
                chunk = data[i+1:i+17]
                try:
                    f1, f2, f3, f4 = struct.unpack('<ffff', chunk)
                except struct.error:
                    continue
                quads.append({
                    'offset': i,
                    'f1': f1, 'f2': f2, 'f3': f3, 'f4': f4,
                })
    return quads, n

def main():
    files = [
        '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc',
        '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc',
    ]
    for path in files:
        quads, n = extract_quads(path)
        print(f"=== {path} ===")
        print(f"file size: {n} bytes")
        print(f"total 0x15+4float quads found: {len(quads)}")
        out_path = path.replace('/archive/data/', '/analysis/xtc/').replace('.xtc', '_quads.json')
        out_path = '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/' + \
            path.split('/')[-1].replace('.xtc', '_quads.json')
        with open(out_path, 'w') as f:
            json.dump(quads, f, indent=1)
        print(f"wrote {out_path}")
        print()

if __name__ == '__main__':
    main()
