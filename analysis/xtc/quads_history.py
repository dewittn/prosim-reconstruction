#!/usr/bin/env python3
"""Build the final quads_history.csv: the clean 44-record table (+ terminator) for
both files, with an assigned identity label per unique (f1,f2) pair (exact match,
not rounded) and array position preserved. This is NOT claimed to be strict
chronological order -- see findings report for caveats."""
import struct
import csv

def extract(path, base=87, stride=17, count=45):
    """count=45 to include the 0x12 terminator record right after the 44-slot table."""
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
        'prosim.xtc': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc',
        'prosim1.xtc': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc',
    }

    # Build a global identity map across both files, keyed by exact (f1,f2), so the
    # same identity gets the same label in both files (useful since several exact
    # f1 values recur identically across both independently-played games).
    all_recs = {}
    for name, path in files.items():
        all_recs[name] = extract(path)

    identity_map = {}
    next_id = 1
    for name, recs in all_recs.items():
        for r in recs:
            if r['marker'] != 0x15:
                continue  # terminator / non-table record, labeled separately below
            key = (r['f1'], r['f2'])
            if key not in identity_map:
                if abs(r['f1'] - 2.8) < 0.5 and abs(r['f2'] - 2.8) < 0.5:
                    identity_map[key] = 'SENTINEL_2.8'
                else:
                    identity_map[key] = f'ID{next_id:02d}'
                    next_id += 1

    out_path = '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/quads_history.csv'
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['file', 'array_idx', 'byte_offset', 'marker_hex', 'identity',
                    'f1', 'f2', 'f3', 'f4', 'prof_est_f1x1.088'])
        for name, recs in all_recs.items():
            for r in recs:
                if r['marker'] == 0x15:
                    key = (r['f1'], r['f2'])
                    identity = identity_map[key]
                elif r['marker'] == 0x12:
                    identity = 'TERMINATOR_0x12'
                else:
                    identity = 'UNKNOWN'
                w.writerow([name, r['idx'], r['offset'], hex(r['marker']), identity,
                            f"{r['f1']:.6f}", f"{r['f2']:.6f}", f"{r['f3']:.3f}", f"{r['f4']:.3f}",
                            f"{r['f1']*1.088:.4f}"])
    print(f"wrote {out_path}")
    print(f"total identities found (excluding terminator/sentinel): {sum(1 for v in identity_map.values() if v.startswith('ID'))}")
    print(f"identity map: {identity_map}")

if __name__ == '__main__':
    main()
