#!/usr/bin/env python3
"""Precisely isolate the swapped sub-records, decode their payloads under
several interpretations, and search the rest of each file for recurrence
of the header's tag bytes (0x35, 0x32/33/38, 0x12, 0x0f) to test whether
they form a real recurring tag-length grammar or are coincidental."""
import struct

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}
data = {name: open(path, "rb").read() for name, path in FILES.items()}


def hexs(b):
    return " ".join(f"{x:02x}" for x in b)


def show_record(b, start, end, label):
    chunk = b[start:end]
    print(f"  {label} [{start}:{end}] len={end-start}: {hexs(chunk)}")
    tag, ln = chunk[0], chunk[1]
    payload = chunk[2:]
    print(f"    tag=0x{tag:02x} len_byte={ln} payload={hexs(payload)} (payload_len={len(payload)})")
    # try float32 at every alignment within payload
    for off in range(0, len(payload) - 3):
        try:
            v = struct.unpack('<f', payload[off:off+4])[0]
        except Exception:
            continue
        print(f"      float32@payload+{off}: {v}")
    # try uint16 at every alignment
    for off in range(0, len(payload) - 1):
        v = struct.unpack('<H', payload[off:off+2])[0]
        print(f"      uint16@payload+{off}: {v}")


print("=" * 100)
print("SWAPPED '0x35'-tagged records (offsets 16-33)")
print("=" * 100)
for name, b in data.items():
    print(f"--- {name} ---")
    # find 0x35 tag positions in range 14-36
    tags = [i for i in range(14, 36) if b[i] == 0x35]
    print(f"  0x35 tag positions: {tags}")
    for i, t in enumerate(tags):
        end = tags[i+1] if i+1 < len(tags) else 43  # section ends where the 32/33/38 section begins
        show_record(b, t, end, f"record@{t}")
    print()

print("=" * 100)
print("SWAPPED '0x32/0x33/0x38'-tagged records (offsets 43-65)")
print("=" * 100)
for name, b in data.items():
    print(f"--- {name} ---")
    tags = [i for i in range(41, 67) if b[i] in (0x32, 0x33, 0x38)]
    print(f"  tag positions: {[(i, hex(b[i])) for i in tags]}")
    for i, t in enumerate(tags):
        end = tags[i+1] if i+1 < len(tags) else 66
        show_record(b, t, end, f"record@{t} tag=0x{b[t]:02x}")
    print()

print("=" * 100)
print("Region offsets 66-86 (post 0x38 record through end of header)")
print("=" * 100)
for name, b in data.items():
    print(f"--- {name} --- {hexs(b[66:87])}")

print()
print("=" * 100)
print("TAG RECURRENCE SEARCH: how often do 0x35, 0x32, 0x33, 0x38, 0x12, 0x0f appear in the WHOLE file")
print("(and with what byte follows, to see if a small 'length' value follows consistently)")
print("=" * 100)
for name, b in data.items():
    print(f"--- {name} (file len {len(b)}) ---")
    for tagval in (0x35, 0x32, 0x33, 0x38, 0x12, 0x0f):
        positions = [i for i in range(len(b)) if b[i] == tagval]
        print(f"  tag 0x{tagval:02x} ('{chr(tagval) if 32<=tagval<127 else '?'}'): {len(positions)} occurrences total in file")
        # show first 10 with next byte context
        sample = positions[:10]
        for p in sample:
            nxt = b[p+1] if p+1 < len(b) else None
            print(f"      at {p}: next_byte={nxt:#04x}" if nxt is not None else f"      at {p}: (EOF)")
    print()
