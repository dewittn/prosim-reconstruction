#!/usr/bin/env python3
"""Stride scan from base=87, stride=17, WITHOUT requiring marker==0x15 -- just track
marker byte value and plausibility, to find the true end of the contiguous record array."""
import struct

def is_plausible(f1, f2, f3, f4):
    if abs(f1) > 1e6 or abs(f2) > 1e6 or abs(f3) > 1e7 or abs(f4) > 1e7:
        return False
    return True

def main():
    files = {
        'prosim.xtc': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc',
        'prosim1.xtc': '/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc',
    }
    for name, path in files.items():
        with open(path, 'rb') as f:
            data = f.read()
        n = len(data)
        off = 87
        print(f"=== {name} ===")
        idx = 0
        bad_run = 0
        while off + 17 <= n:
            marker = data[off]
            chunk = data[off+1:off+17]
            f1, f2, f3, f4 = struct.unpack('<ffff', chunk)
            plaus = is_plausible(f1, f2, f3, f4)
            flag = '' if plaus else ' <BAD>'
            print(f"[{idx:3d}] off={off:6d} marker=0x{marker:02x}({marker:3d})  f1={f1:9.4f} f2={f2:9.4f} f3={f3:14.3f} f4={f4:12.3f}{flag}")
            if not plaus:
                bad_run += 1
                if bad_run >= 4:
                    print("  -- stopping after sustained implausible run --")
                    break
            else:
                bad_run = 0
            off += 17
            idx += 1
        print()

if __name__ == '__main__':
    main()
