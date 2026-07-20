#!/usr/bin/env python3
"""Round 2, Task 2-5: relation hunt for V1, V2, P1 against f1, f2, rates, training
matrix, etc. Uses the CORRECTED 11-identity table (ID03 split into two real
identities distinguished by f2, since build_identity_labeler in map_common.py keys
only on f1 and collides them). Excludes decorated-record parse artifacts by using
the modal (most common) head values per identity rather than raw per-occurrence
values (already established as constant in c2_constants.py's clean occurrences).
"""
# Hand-verified from c2_constants.py output: modal / constant head per real identity.
# ID03 split into ID03a/ID03b using f2 to disambiguate the f1-collision.
IDENTITIES = {
    "ID01": dict(f1=0.8508557677268982, f2=0.6103542447090149, v1=410, v2=327, tag=0x87, p1=0xe2fe, p2=0xe2ff),
    "ID02": dict(f1=0.8074246048927307, f2=0.5699745416641235, v1=165, v2=141, tag=0x86, p1=0xe18a, p2=0xe18b),
    "ID03a": dict(f1=0.818823516368866, f2=0.5833333134651184, v1=304, v2=212, tag=0x87, p1=0xe2b8, p2=0xe2b9),
    "ID03b": dict(f1=0.818823516368866, f2=0.5490196347236633, v1=336, v2=388, tag=0x86, p1=0xe0ea, p2=0xe0eb),
    "ID04": dict(f1=0.6397058963775635, f2=0.6637036800384521, v1=228, v2=178, tag=0x87, p1=0xe070, p2=0xe071),
    "ID05": dict(f1=0.8093023300170898, f2=0.5586034655570984, v1=303, v2=320, tag=0x86, p1=0xe08a, p2=0xe08b),
    "ID06": dict(f1=0.7750557065010071, f2=0.6170799136161804, v1=373, v2=383, tag=0x86, p1=0xe248, p2=0xe249),
    "ID07": dict(f1=0.9666666388511658, f2=0.5941644310951233, v1=282, v2=196, tag=0x87, p1=0xe2b2, p2=0xe29f),
    "ID09": dict(f1=0.9086161851882935, f2=0.5551425218582153, v1=264, v2=239, tag=0x86, p1=0xe12a, p2=0xe12b),
    "ID08": dict(f1=1.03125, f2=0.6777609586715698, v1=111, v2=114, tag=0x82, p1=0xfe09, p2=0x93f8),
    "ID10": dict(f1=1.0192307233810425, f2=1.0144927501678467, v1=85, v2=135, tag=0x84, p1=0xf8a7, p2=0x3e29),
}

TRAINING_MATRIX = {
    0: [20, 61, 79, 89, 96, 100, 103, 106, 108, 109, 109],
    1: [21, 63, 81, 91, 98, 103, 106, 109, 111, 112, 112],
    2: [21, 64, 82, 93, 100, 104, 108, 110, 112, 114, 114],
    3: [21, 64, 83, 94, 101, 106, 109, 112, 114, 116, 116],
    4: [21, 65, 84, 95, 102, 107, 110, 113, 115, 117, 117],
    5: [22, 66, 85, 96, 103, 108, 111, 114, 116, 118, 118],
    6: [22, 66, 85, 96, 104, 108, 112, 115, 117, 118, 118],
    7: [22, 66, 86, 97, 104, 109, 112, 115, 117, 119, 119],
    8: [22, 67, 86, 97, 104, 109, 113, 116, 118, 120, 120],
    9: [22, 67, 87, 98, 105, 110, 113, 116, 118, 120, 120],
}
TM_CELLS = [(t, l, v) for t, row in TRAINING_MATRIX.items() for l, v in enumerate(row)]

RATES = [40, 50, 60]
SCALES = [100, 128, 255, 256, 400, 1000]


def pct_err(a, b):
    if b == 0:
        return None
    return abs(a - b) / abs(b)


def hunt_scalar_transforms(target_name, target_val_fn):
    """For each identity, compute candidate scalar values from f1/f2, compare to
    target_val_fn(identity_dict). Report (label -> list of per-identity errors)."""
    labels_hits = {}
    for name, d in IDENTITIES.items():
        f1, f2 = d["f1"], d["f2"]
        target = target_val_fn(d)
        candidates = {
            "f1": f1, "f2": f2, "f1*f2": f1 * f2,
            "1/f1": 1 / f1, "1/f2": 1 / f2,
            "f1/f2": f1 / f2, "f2/f1": f2 / f1,
            "f1+f2": f1 + f2, "f1-f2": f1 - f2,
        }
        for scale in SCALES:
            for base_label in ["f1", "f2", "f1*f2", "1/f1", "1/f2", "f1/f2", "f2/f1"]:
                candidates[f"{base_label}*{scale}"] = candidates[base_label] * scale
        for rate in RATES:
            candidates[f"{rate}*f1*f2"] = rate * f1 * f2
            candidates[f"{rate}*f1"] = rate * f1
            candidates[f"{rate}*f2"] = rate * f2
            candidates[f"{rate}*f1/f2"] = rate * f1 / f2
            candidates[f"{rate}*f2/f1"] = rate * f2 / f1
            for r2 in RATES:
                candidates[f"{rate}*{r2}*f1*f2/1000"] = rate * r2 * f1 * f2 / 1000
        for label, val in candidates.items():
            e = pct_err(val, target)
            if e is not None and e < 0.02:
                labels_hits.setdefault(label, []).append((name, target, val, e))
    return labels_hits


def report_hunt(title, target_fn):
    print("=" * 100)
    print(title)
    print("=" * 100)
    hits = hunt_scalar_transforms(title, target_fn)
    universal = {lbl: v for lbl, v in hits.items() if len(v) == len(IDENTITIES)}
    partial = {lbl: v for lbl, v in hits.items() if len(v) != len(IDENTITIES)}
    print(f"\n-- Relations holding for ALL {len(IDENTITIES)} identities (err<2%) --")
    if not universal:
        print("  NONE")
    for lbl, v in universal.items():
        print(f"  {lbl}:")
        for name, target, val, e in v:
            print(f"      {name}: target={target} candidate={val:.3f} err={e*100:.2f}%")
    print(f"\n-- Partial matches (< all {len(IDENTITIES)}, useful only if the SUBSET is meaningful) --")
    # only show partial matches hitting >=4 identities (to filter noise)
    shown = 0
    for lbl, v in sorted(partial.items(), key=lambda kv: -len(kv[1])):
        if len(v) < 4:
            continue
        shown += 1
        names = [x[0] for x in v]
        print(f"  {lbl}: matches {len(v)}/{len(IDENTITIES)} -> {names}")
    if shown == 0:
        print("  (none with >=4 identities matching)")
    print()


report_hunt("V1 vs f1/f2 scalar transforms", lambda d: d["v1"])
report_hunt("V2 vs f1/f2 scalar transforms", lambda d: d["v2"])
report_hunt("V1+V2 vs f1/f2 scalar transforms", lambda d: d["v1"] + d["v2"])
report_hunt("V1-V2 vs f1/f2 scalar transforms", lambda d: d["v1"] - d["v2"])
report_hunt("V1*V2 vs f1/f2 scalar transforms (large; expect no simple hit, sanity)", lambda d: d["v1"] * d["v2"])

print("=" * 100)
print("V1/V2 ratio vs f1/f2 ratio")
print("=" * 100)
for name, d in IDENTITIES.items():
    r_v = d["v1"] / d["v2"]
    r_f = d["f1"] / d["f2"]
    print(f"  {name}: V1/V2={r_v:.4f}  f1/f2={r_f:.4f}  diff%={abs(r_v-r_f)/r_f*100:.2f}%")

print()
print("=" * 100)
print("V1, V2 vs TRAINING MATRIX CELLS (all 110 values, tol=2%, also exact int match)")
print("=" * 100)
for name, d in IDENTITIES.items():
    v1, v2 = d["v1"], d["v2"]
    exact_v1 = [(t, l, v) for t, l, v in TM_CELLS if v == v1]
    exact_v2 = [(t, l, v) for t, l, v in TM_CELLS if v == v2]
    if exact_v1 or exact_v2:
        print(f"  {name}: V1={v1} exact_matches={exact_v1}  V2={v2} exact_matches={exact_v2}")
print("(if nothing printed above, no V1/V2 equals any raw training-matrix cell)")

print()
print("=" * 100)
print("P1 investigation: P1 - 0xe000, low byte, 14-bit value, vs V1/V2/f1/f2")
print("=" * 100)
for name, d in IDENTITIES.items():
    p1 = d["p1"]
    p2 = d["p2"]
    print(f"  {name}: P1=0x{p1:04x} P1-0xe000={p1-0xe000:5d} low_byte=0x{p1 & 0xff:02x} "
          f"14bit=0x{p1 & 0x3fff:04x}  P2=0x{p2:04x} P2-P1={p2-p1}")

print()
print("=" * 100)
print("Tag byte vs V1>V2 and payload-size-class (department correlation already found separately)")
print("=" * 100)
for name, d in IDENTITIES.items():
    print(f"  {name}: tag=0x{d['tag']:02x} V1={d['v1']:4d} V2={d['v2']:4d} V1>V2={d['v1']>d['v2']}")
