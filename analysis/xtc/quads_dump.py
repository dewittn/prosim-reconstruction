#!/usr/bin/env python3
"""Dump all quads in order with gap-from-previous and flags, for manual inspection."""
import json

def main():
    for name in ['prosim_quads.json', 'prosim1_quads.json']:
        path = '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/' + name
        with open(path) as f:
            quads = json.load(f)
        print(f"=== {name} === ({len(quads)} quads)")
        prev_off = None
        for idx, q in enumerate(quads):
            gap = q['offset'] - prev_off if prev_off is not None else 0
            prev_off = q['offset']
            flag = ''
            if abs(q['f1'] - 2.8) < 0.5 and abs(q['f2'] - 2.8) < 0.5:
                flag = ' <2.8-TYPE>'
            print(f"[{idx:3d}] off={q['offset']:6d} gap={gap:4d}  f1={q['f1']:9.4f} f2={q['f2']:9.4f} f3={q['f3']:14.3f} f4={q['f4']:12.3f}{flag}")
        print()

if __name__ == '__main__':
    main()
