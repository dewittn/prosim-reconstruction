#!/usr/bin/env python3
"""Count 0x15-delimited operator-like records in the body of both files, to
independently test whether the count of operator records equals the
header byte-9 value (9 / 13), which would corroborate 'operator count'
over 'week number' for that byte -- or vice versa."""
import struct

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}

for name, path in FILES.items():
    with open(path, "rb") as f:
        data = f.read()

    # total occurrences of 0x15 byte anywhere in file
    total_15 = data.count(0x15)
    total_15_body = data[87:].count(0x15)

    # records where float1,float2 both look like plausible efficiency/proficiency (0.1-2.0)
    plausible = []
    all_records = []
    for i, byte in enumerate(data):
        if byte == 0x15 and i + 9 <= len(data):
            try:
                float1 = struct.unpack('<f', data[i+1:i+5])[0]
                float2 = struct.unpack('<f', data[i+5:i+9])[0]
                all_records.append((i, round(float1, 4), round(float2, 4)))
                if 0.1 < float1 < 2.0 and 0.1 < float2 < 2.0:
                    plausible.append((i, round(float1, 4), round(float2, 4)))
            except Exception:
                pass

    unique_pairs = set((r[1], r[2]) for r in plausible)

    print(f"=== {name} ===")
    print(f"total 0x15 bytes in file: {total_15}  (in body only: {total_15_body})")
    print(f"0x15 positions with valid float32 pair read (any value): {len(all_records)}")
    print(f"0x15 positions with PLAUSIBLE efficiency-range float pair (0.1-2.0): {len(plausible)}")
    print(f"UNIQUE plausible float pairs: {len(unique_pairs)}")
    print(f"header byte 9 value: {data[9]}")
    print(f"header byte 44 value: {data[44]}")
    print()
    print("First 20 plausible records (offset, float1, float2):")
    for r in plausible[:20]:
        print(f"  {r}")
    print()
