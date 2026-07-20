#!/usr/bin/env python3
"""Parse the 'operator log' / body log: 0x15 float-quad records and 0x12 separators,
in order, starting at offset 87, up to the packed-region start (912 for a, 1355 for b).
Each 0x15 record: tag(1)=0x15, then 4 floats (f1,f2,f3,f4) -- need to determine exact
byte layout (float32 LE most likely = 1+16=17 bytes, or could include extra ints).
We'll first just scan for 0x15 and 0x12 tag bytes and try float32 decode after each.
"""
import struct

FILES = {
    "a": ("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc", 87, 912),
    "b": ("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc", 87, 1355),
}

def try_floats(data, off, n=4):
    if off + 4*n > len(data):
        return None
    return struct.unpack_from("<" + "f"*n, data, off)

def main():
    for tag, (path, start, end) in FILES.items():
        data = open(path, "rb").read()
        print(f"=== {tag}: scanning {start}-{end} ===")
        pos = start
        count15 = 0
        count12 = 0
        entries = []
        while pos < end:
            b = data[pos]
            if b == 0x15:
                fl = try_floats(data, pos+1, 4)
                entries.append(("0x15", pos, fl))
                count15 += 1
                pos += 1 + 16
            elif b == 0x12:
                entries.append(("0x12", pos, None))
                count12 += 1
                pos += 1
            else:
                pos += 1
        print(f"  0x15 count={count15}  0x12 count={count12}")
        for kind, off, fl in entries:
            if kind == "0x15":
                print(f"  off={off:5d} 0x15 floats={fl}")
            else:
                print(f"  off={off:5d} 0x12 (sep)")

if __name__ == "__main__":
    main()
