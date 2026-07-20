#!/usr/bin/env python3
"""The 66-byte 'core' block recurs at MULTIPLE offsets in both files (not just near EOF).
Find every occurrence, in order, in both files, and inspect spacing / context to test
whether it's a per-week or per-entity repeating template."""

FILES = {
    "prosim.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc",
    "prosim1.xtc": "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc",
}
with open(FILES["prosim.xtc"], "rb") as f:
    d0 = f.read()
with open(FILES["prosim1.xtc"], "rb") as f:
    d1 = f.read()

core = bytes.fromhex("54ad1e8fa3d1f4924a8f47d369bcb25b349ad02832e97cc263349acea77349ace273349acea77369bcda6f2e97a6d374aa564ca6625d2f0994cc12a95812a9580000")
print(f"Core block length: {len(core)}")

def find_all(hay, needle):
    out = []
    start = 0
    while True:
        idx = hay.find(needle, start)
        if idx == -1:
            break
        out.append(idx)
        start = idx + 1
    return out

occ0 = find_all(d0, core)
occ1 = find_all(d1, core)
print(f"prosim.xtc occurrences: {occ0}")
print(f"  gaps: {[occ0[i+1]-occ0[i] for i in range(len(occ0)-1)]}")
print(f"prosim1.xtc occurrences: {occ1}")
print(f"  gaps: {[occ1[i+1]-occ1[i] for i in range(len(occ1)-1)]}")

# also try a shorter, more sensitive anchor to catch partial/fuzzy repeats (just "349a" motif)
motif = bytes.fromhex("349a")
c0 = d0.count(motif)
c1 = d1.count(motif)
print(f"\nCount of motif 349a: prosim.xtc={c0}, prosim1.xtc={c1}")

# internal repetition check within the 66-byte core: look at it as sequence of bytes,
# check for repeated N-grams
print("\nCore block hex, spaced for inspection:")
print(" ".join(f"{b:02x}" for b in core))

# Look at what's immediately before each occurrence (16 bytes) to see if there's a
# distinguishing prefix (e.g. a length field or tag) that varies meaningfully
print("\nContext before each occurrence in prosim.xtc:")
for o in occ0:
    print(f"  offset {o}: ...{d0[max(0,o-16):o].hex()} | CORE | {d0[o+len(core):o+len(core)+16].hex()}...")
print("\nContext before each occurrence in prosim1.xtc:")
for o in occ1:
    print(f"  offset {o}: ...{d1[max(0,o-16):o].hex()} | CORE | {d1[o+len(core):o+len(core)+16].hex()}...")
