#!/usr/bin/env python3
"""Complete re-extraction of ALL body records from both XTC files under the
verified grammar (0x15 = 4xfloat32, 0x12 = 2xfloat32 separator), walking the
full block structure [45,3] / [44,7,9,13]. Writes synth_full_table.csv and
prints per-identity summaries."""
import struct, csv

FILES = {
    "prosim.xtc":  ("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim.xtc", 9),
    "prosim1.xtc": ("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data/prosim1.xtc", 13),
}
OUT = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/synth_full_table.csv"

def walk(data, start=87):
    """Return list of (offset, tag, floats-tuple)."""
    pos = start
    recs = []
    while pos < len(data):
        tag = data[pos]
        if tag == 0x15 and pos + 17 <= len(data):
            recs.append((pos, 0x15, struct.unpack("<4f", data[pos+1:pos+17])))
            pos += 17
        elif tag == 0x12 and pos + 9 <= len(data):
            recs.append((pos, 0x12, struct.unpack("<2f", data[pos+1:pos+9])))
            pos += 9
        else:
            break
    return recs

# Build a global identity map keyed by exact f1 bytes so labels are stable
# across files. Sentinels (f1~2.80) get their own label.
def f1_key(f1):
    return struct.pack("<f", f1).hex()

# First pass: collect all non-sentinel f1 keys in order of first appearance
identity_of = {}
next_id = [1]
def label_for(f1, f2):
    if 2.7 < f1 < 2.9:
        return "SENT"
    k = f1_key(f1)
    if k not in identity_of:
        identity_of[k] = f"ID%02d" % next_id[0]
        next_id[0] += 1
    return identity_of[k]

rows = []
per_file_records = {}
for name, (path, week) in FILES.items():
    data = open(path, "rb").read()
    recs = walk(data)
    per_file_records[name] = recs
    # assign block indices
    block_idx = 0
    idx_in_block = 0
    gidx = 0
    for (off, tag, fl) in recs:
        if tag == 0x12:
            rows.append(dict(file=name, week=week, block_index=block_idx,
                             index_in_block=-1, global_index=gidx, offset=off,
                             tag="0x12", f1=fl[0], f2=fl[1], f3="", f4="",
                             identity="SEP"))
            block_idx += 1
            idx_in_block = 0
            gidx += 1
            continue
        f1, f2, f3, f4 = fl
        lbl = label_for(f1, f2)
        rows.append(dict(file=name, week=week, block_index=block_idx,
                         index_in_block=idx_in_block, global_index=gidx, offset=off,
                         tag="0x15", f1=f1, f2=f2, f3=f3, f4=f4, identity=lbl))
        idx_in_block += 1
        gidx += 1

with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["file","week","block_index","index_in_block",
                                       "global_index","offset","tag","identity",
                                       "f1","f2","f3","f4"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

# ---- Report identity table (unique f1/f2 pairs) ----
print("=== IDENTITY CATALOG (unique f1 with their f2 variants) ===")
from collections import defaultdict
byf1 = defaultdict(lambda: defaultdict(int))
label_by_f1 = {}
for r in rows:
    if r["tag"] != "0x15" or r["identity"] == "SENT":
        continue
    byf1[round(r["f1"],6)][round(r["f2"],6)] += 1
    label_by_f1[round(r["f1"],6)] = r["identity"]
for f1 in sorted(byf1):
    variants = byf1[f1]
    vs = ", ".join(f"f2={v:.6f}(x{c})" for v,c in sorted(variants.items()))
    print(f"  {label_by_f1[f1]}: f1={f1:.6f}  prof=f1*1.088={f1*1.088:.4f}  ->  {vs}")

# which identities appear in which file
print("\n=== IDENTITY PRESENCE BY FILE ===")
present = defaultdict(set)
for r in rows:
    if r["tag"]=="0x15" and r["identity"]!="SENT":
        present[r["identity"]].add(r["file"])
for lbl in sorted(present, key=lambda x:int(x[2:])):
    print(f"  {lbl}: {sorted(present[lbl])}")

print("\nTotal rows written:", len(rows), "->", OUT)
