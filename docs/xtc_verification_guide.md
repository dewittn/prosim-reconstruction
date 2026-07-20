# XTC Verification Guide

This document describes the binary format of the PROSIM XTC game-state files and the methodology used to verify the two-component operator efficiency model against them.

> **Major revision (July 2026)**: A multi-agent forensic re-analysis (exhaustive
> byte-accounting parse, cross-file diffing, REPT cross-reference) corrected
> several claims in the original December 2025 analysis. Key changes:
>
> - Byte 9 of the header is the **week number**, not the operator count
> - `0x15` is a record **tag**, not a delimiter; a second record type (`0x12`
>   period separators) exists and the original extraction missed all records
>   after the first separator
> - The two files are saves of the **same game** (weeks 9 and 13), and the
>   operator log **grows** in ~4-week shipping-period blocks
> - Float3/Float4 are period-to-date and lifetime accumulators respectively
> - Float2 is a **fixed per-operator coefficient** (0.55–0.68 band); the
>   "training level" and "tier factor" hypotheses are dead
> - Over 95% of each file is a "packed region" — its structure was
>   subsequently decoded (see Discovery #15 and the packed-region section
>   below); payload internals remain partially open
>
> See `key_discoveries.md` Discovery #14 for the full evidence trail.
> Analysis scripts are preserved in `analysis/xtc/`.

## Overview

The PROSIM simulation uses a two-component efficiency model:

```
Combined_Efficiency = Time_Efficiency × Proficiency
```

Where:
- **Time Efficiency**: Determined by training matrix lookup `TRAINING_MATRIX[tier][level]`
- **Proficiency**: Fixed multiplier assigned at operator hire

The XTC files store two fixed per-operator constants (Float1, Float2) plus two
accumulators (Float3, Float4), providing independent binary evidence for the
two-component model.

---

## Prerequisites

### Required Files

| File | Location | Purpose |
|------|----------|---------|
| `prosim.xtc` | `archive/data/` | Week 9 save (instructor's game) |
| `prosim1.xtc` | `archive/data/` | Week 13 save (same game, later point) |
| `ProsimTable.xls` | `archive/spreadsheets/` | Reverse-engineered spreadsheet |
| `Operators-Table 1.csv` | `archive/spreadsheets/ProsimTable CVS Export/` | Operator efficiency data |
| REPT12/13/14.DAT | `archive/data/` | Ground-truth rosters (student games) |

### Required Knowledge

- IEEE 754 float32, little-endian
- Basic Python/hex analysis
- The training matrix in `prosim/config/defaults.py`

---

## File Format (verified July 2026)

Both files share this layout:

| Region | prosim.xtc | prosim1.xtc | Content |
|--------|-----------|-------------|---------|
| Preamble | 0–16 | 0–16 | Fixed-width fields (see below) |
| Header TLV | 16–78 | 16–78 | ASCII-digit-tagged records |
| Operator log | 78–912 | 78–1355 | `0x15` operator records + `0x12` separators |
| Packed region | 912–EOF | 1355–EOF | High-entropy per-week log, **undecoded** |

### Preamble fields

| Offset | prosim.xtc | prosim1.xtc | Meaning |
|--------|-----------|-------------|---------|
| 0 | 0x00 | 0x00 | constant |
| 1–2 (u16 LE) | 38031 | 58268 | unknown (checksum theory tested and refuted) |
| 3–5 | `01 1d 04` | `01 1d 04` | constant (version/magic?) |
| 6 | 234 | 254 | unknown counter (+5/week) |
| 7 | 10 | 10 | constant |
| 8 | 132 | 236 | unknown counter (+26/week) |
| **9** | **9** | **13** | **WEEK NUMBER** (confirmed via REPT cross-reference) |
| 40 | 24 | 24 | max simulation weeks, inside static config block (bytes 34–42) |
| 44 | 9 | 8 | unknown — NOT a week counter (old claim refuted) |

The old "byte 9 = number of operators" claim arose because week number and
assumed headcount coincided in both files (9/9, 13/13). REPT12–14 show the
actual roster held at 8–9 active operators and never reached 13.

### Header TLV records (offsets 16–78)

Tag (1 ASCII-digit byte) + length + payload. Tags `'5'`, `'2'`, `'3'`, `'8'`.
Two record pairs are byte-identical between the two saves but appear in
**exactly reversed order** — a recency/sort reordering on save whose rule is
undetermined (needs a third save to disambiguate). Tag `'8'` contains a
float32 `+Infinity` placeholder. These tag bytes do NOT recur as tags
elsewhere in the file; they are header-local framing.

### Operator log records (offset 78 → 912/1355)

Two record types only:

**`0x15` + four float32 LE (17 bytes) — operator record:**

| Field | Range | Meaning (confidence) |
|-------|-------|----------------------|
| Float1 | 0.64–1.03 | Fixed per-operator proficiency/speed coefficient (medium-high) |
| Float2 | 0.549–0.678 (one outlier ≈1.0145) | Fixed per-operator second coefficient — quality/yield axis (medium) |
| Float3 | 0–~18k | Period-to-date accumulator, resets ~every 4 weeks (medium) |
| Float4 | ~1.9k–22.8k | Lifetime cumulative accumulator, monotonically grows (medium-high) |

**`0x12` + two float32 (9 bytes) — period separator:** both floats ≈2.80
(sentinel value). These delimit shipping-period blocks.

Record counts: prosim.xtc = 48 records in runs `[45, 3]`;
prosim1.xtc = 73 records in runs `[44, 7, 9, 13]`. The log grows as the game
advances; blocks correspond to ~4-week shipping periods (2 → 4 boundaries
between week 9 and week 13), matching the "Demand This Month" concept in the
weekly reports.

Records within a block group into department teams (4 Parts + 5 Assembly
slots). Records with `f1=f2≈2.80` are idle-slot sentinels (present at week 9,
filled by week 13).

**Identity**: the pair (Float1, Float2) identifies an operator. All 11
identities appear byte-identically in both files. Float1 alone is NOT unique —
0.818824 is shared by two operators with different Float2 values (0.549020 vs
0.583333).

### Extraction pitfalls (learned the hard way)

1. **Do not scan for 0x15 bytes naively** — 0x15 occurs inside float mantissas
   of genuine records and throughout the packed region. Walk the file from
   offset 87 with tag dispatch: `0x15` → consume 17 bytes, `0x12` → consume
   9 bytes, anything else → end of log (both files terminate at byte `0x1e`).
2. **Do not value-filter floats** (the original `0.1 < f < 2.0` filter
   discarded Float3/Float4 and all records after the first separator).
3. Reference extraction: `analysis/xtc/synth_full_table.csv` (all 125
   records, both files, with block indices and identity labels).

```python
def walk_operator_log(data, start=87):
    """Correct extraction: tag-dispatch walk, no value filtering."""
    import struct
    records, blocks, block = [], [], 0
    i = start
    while i < len(data):
        tag = data[i]
        if tag == 0x15:
            f1, f2, f3, f4 = struct.unpack('<4f', data[i+1:i+17])
            records.append((block, i, f1, f2, f3, f4))
            i += 17
        elif tag == 0x12:
            block += 1
            i += 9
        else:
            break  # end of structured region (0x1e in both files)
    return records, i  # i = boundary of packed region
```

### The packed region (912/1355 → EOF) — structure decoded July 2026

Over 95% of each file. Structure (see `key_discoveries.md` #15 for evidence):

- **Preamble** (a: 912–1350, b: 1355–2111): undecoded dense varint-like data;
  not shared between saves.
- **Numbered records**: marker `[n][0x0a]`, n = 1..49 (a) / 1..76 (b),
  complete gap-free chains. **Aligned 1:1 with the operator-log entries**
  (operator records and separators, in order) — verified at 100% identity
  match rate on payload contents.
- **Payload anatomy**: `[n][0x0a]` + two LEB128 varints (per-identity
  constants, meaning unknown) + tag `0x86`/`0x87` + two big-endian uint16
  (usually consecutive values) + dense identity template + transient
  queue-like suffix + event-tail tokens (`0x0d`/`0x1a`/`0x09`) ending in
  sentinel `0x17`.
- Payloads are **identity-keyed templates**: byte-identical for the same
  (f1,f2) identity while its state is unchanged, regardless of week or
  accumulator values (the body floats are NOT encoded in the payload).
  Changes between occurrences are append/remove at the payload end
  (queue behavior), template alternation (assignment changeover), or
  transient spikes (event processing). All body `0x12` separators carry the
  event-tail decoration — a deterministic signature.
- **Cross-save**: each save is a full re-serialization with dynamic ordering;
  record number n is a within-save key only. Compare per-identity, never
  positionally.

Chain-walk extraction: for n = 1, 2, 3…, find the earliest offset past the
previous marker where `byte[i] == n and byte[i+1] == 0x0a`. Reference
implementation: `analysis/xtc/map_common.py`; full alignment table:
`analysis/xtc/map_alignment.csv`.

**Remaining unknowns**: queue/suffix contents, preamble encoding, the two
per-identity head varints, event-tail token semantics, cross-save ordering
rule.

---

## Verification: Float1 vs Proficiency

The original headline claim was `Float1 × 1.088 ≈ proficiency`. Status after
re-analysis: **exact for Operator 3 only** (1.03125 × 1.088 = 1.1220 vs
documented 1.122); the same scale factor does not reproduce the other derived
proficiencies. Treat Float1 as a proficiency-*like* fixed constant whose exact
relationship to the REPT-derived values is still open.

```python
# Proficiency values derived from ProsimTable.xls Week 16 data
DERIVED_PROFICIENCY = {
    1: 1.039, 2: 1.097, 3: 1.122, 4: 1.093, 5: 1.028,
    6: 0.836, 7: 0.934, 8: 0.850, 9: 0.900,
}
```

The training-matrix correlation (XTC values 64.0% → Tier 2 Level A,
80.7% → Tier 1 Level B, 103.1% → Tier 0 Level F, avg error 0.2%) remains valid
as evidence that XTC floats live on the training-matrix scale.

---

## Float2 Status

### What is now known (July 2026)

- **Fixed at hire**: identical for every operator across the week-9 and
  week-13 saves → NOT training progress (old Hypothesis B dead)
- **Not a training-matrix cell** and not tier-derived via any simple ratio
  (old Hypothesis A dead): best-fit rationals share no common denominator, so
  it is a computed value, not a table constant
- **Range matches PROSIM's "Percent of Efficiency"** band (54–65% in REPT
  data); the one outlier (≈1.0145) pairs with the also-anomalous f1≈1.0192
- **Interpretation**: the quality/yield axis of the two-component model —
  the second fixed operator constant complementing Float1's speed axis

### What would resolve it completely

1. **A matched XTC + REPT pair from the same game** — regress Float2 against
   scheduled/productive hours, rejects, and reported efficiency
2. **A third XTC save** from the same game (any other week) — confirms Float4
   monotonicity, pins the Float3 reset period, disambiguates the header
   record reordering, and tests the preamble counters (+5/wk, +26/wk)
3. **Decoding the packed region** — likely contains per-week operator state
   that would over-determine the formula
4. **Original documentation** — the PROSIM III textbook (ISBN 978-0256214352)
   or Instructor's Manual (ISBN 978-0256214369); see `key_discoveries.md`
   Discovery #13 action items

---

## Reproducing the Analysis

All scripts from the July 2026 re-analysis are in `analysis/xtc/`:

| Prefix | Focus |
|--------|-------|
| `grammar_*` | Region boundaries, record grammar, exhaustive byte-accounting parse |
| `quads_*` | Quad extraction, identity mapping, time series |
| `tail_*` | Packed-region statistics, repeated-block discovery |
| `header_*` | Preamble/TLV field map, checksum tests, claim adjudication |
| `synth_*` | Full-table re-extraction (`synth_full_table.csv`), Float2/block analysis |
| `lead_tiling.py` | Packed-region repeat/literal tiling (found the numbered-record structure) |
| `map_*` | Packed↔body alignment (`map_common.py` = reference walkers, `map_alignment.csv`) |
| `pay_*` | Payload field decoding, varint analysis, preamble characterization |

---

## References

- `prosim/config/defaults.py` — Training matrix and operator profiles
- `prosim/models/operators.py` — Two-component efficiency implementation
- `docs/algorithms.md` — Full algorithm documentation
- `docs/key_discoveries.md` — Discovery #6 (original) and #14 (re-analysis)
- `archive/spreadsheets/ProsimTable.xls` — Original analysis spreadsheet

---

*Document created: December 2025*
*Major revision: July 2026 (multi-agent forensic re-analysis)*
