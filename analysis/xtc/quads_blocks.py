#!/usr/bin/env python3
"""Group extracted quads into blocks: a block = run of quads at exact 17-byte spacing."""
import json

def load(path):
    with open(path) as f:
        return json.load(f)

def group_blocks(quads):
    blocks = []
    cur = [quads[0]]
    for prev, q in zip(quads, quads[1:]):
        if q['offset'] - prev['offset'] == 17:
            cur.append(q)
        else:
            blocks.append(cur)
            cur = [q]
    blocks.append(cur)
    return blocks

def main():
    for name in ['prosim_quads.json', 'prosim1_quads.json']:
        path = '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/' + name
        quads = load(path)
        blocks = group_blocks(quads)
        print(f"=== {name} ===")
        print(f"total quads: {len(quads)}, total blocks (17-byte runs): {len(blocks)}")
        for i, b in enumerate(blocks):
            start = b[0]['offset']
            end = b[-1]['offset']
            print(f" block {i}: size={len(b):3d}  offsets {start:6d}-{end:6d}")
        print()

if __name__ == '__main__':
    main()
