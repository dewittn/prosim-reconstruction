#!/usr/bin/env python3
"""Timeline v2: identity keyed on exact (f1,f2), department from the consts
table, group segmentation by f4 plateau jumps. Tests: are groups
department-uniform? do group counts match weeks? what do f3/f4 do per group?"""
import sys, struct, csv
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from map_common import body_walk, packed_chain_walk, load

# dept per (f1,f2) from c2_constants_corrected.csv
DEPT = {}
with open("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc/c2_constants_corrected.csv") as f:
    for row in csv.DictReader(f):
        key = (round(float(row["f1"]), 6), round(float(row["f2"]), 6))
        dept = {"Parts": "P", "Assembly": "A"}.get(row["dept"], "H")  # H = hired/variant
        DEPT[key] = (row["identity"], dept)

for fkey, pstart in (("a", 912), ("b", 1355)):
    name, data = load(fkey)
    body, _ = body_walk(data)
    packed = packed_chain_walk(data, pstart)

    # segment into groups on f4 plateau jumps (threshold: |delta f4| > 400)
    print(f"\n=== {fkey} ({name}) groups (f4-jump segmentation) ===")
    group, gid, last_f4 = [], 0, None
    rows = []
    for entry, rec in zip(body, packed):
        if entry["tag"] == 0x12:
            rows.append(("SEP", None, None, None, rec["n"]))
            continue
        key = (round(entry["f1"], 6), round(entry["f2"], 6))
        ident, dept = DEPT.get(key, (f"?{entry['f1']:.4f}/{entry['f2']:.4f}", "?"))
        rows.append((ident, dept, entry["f3"], entry["f4"], rec["n"]))

    groups = []
    cur = []
    prev_f4 = None
    for r in rows:
        if r[0] == "SEP":
            continue  # separators don't break f4 grouping by themselves
        if prev_f4 is not None and abs(r[3] - prev_f4) > 400:
            groups.append(cur)
            cur = []
        cur.append(r)
        prev_f4 = r[3]
    if cur:
        groups.append(cur)

    print(f"{len(groups)} groups")
    for gi, g in enumerate(groups):
        depts = "".join(x[1] for x in g)
        idents = ",".join(x[0] for x in g)
        f4s = [x[3] for x in g]
        f3s = [x[2] for x in g]
        d3 = [f"{b-a:+.0f}" for a, b in zip(f3s, f3s[1:])]
        print(f"  g{gi:>2} n={g[0][4]:>2}-{g[-1][4]:>2} dept={depts:<9} f4~{sum(f4s)/len(f4s):8.0f} "
              f"f3 {f3s[0]:8.0f}->{f3s[-1]:8.0f} steps[{' '.join(d3)}]")
        print(f"       ids: {idents}")
