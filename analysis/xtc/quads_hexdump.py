#!/usr/bin/env python3
"""Hexdump a byte range of a file for manual structural inspection."""
import sys

def hexdump(path, start, end):
    with open(path, 'rb') as f:
        f.seek(start)
        data = f.read(end - start)
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hexpart = ' '.join(f'{b:02x}' for b in chunk)
        ascpart = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"{start+i:6d}: {hexpart:<48s}  {ascpart}")

if __name__ == '__main__':
    path = sys.argv[1]
    start = int(sys.argv[2])
    end = int(sys.argv[3])
    hexdump(path, start, end)
