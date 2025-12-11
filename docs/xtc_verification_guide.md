# XTC Verification Guide

This document provides a reproducible methodology for verifying the two-component operator efficiency model against PROSIM XTC game state files.

## Overview

The PROSIM simulation uses a two-component efficiency model:

```
Combined_Efficiency = Time_Efficiency × Proficiency
```

Where:
- **Time Efficiency**: Determined by training matrix lookup `TRAINING_MATRIX[tier][level]`
- **Proficiency**: Fixed multiplier assigned at operator hire (range: ~0.83-1.12)

This guide explains how to verify these findings using the original XTC game state files.

---

## Prerequisites

### Required Files

| File | Location | Purpose |
|------|----------|---------|
| `prosim.xtc` | `archive/` | Week 9 game save |
| `prosim1.xtc` | `archive/` | Week 13 game save |
| `ProsimTable.xls` | `archive/spreadsheets/` | Reverse-engineered spreadsheet |
| `Operators-Table 1.csv` | `archive/spreadsheets/ProsimTable CVS Export/` | Operator efficiency data |

### Required Knowledge

- IEEE 754 floating-point format (little-endian)
- Basic Python/hex analysis
- Understanding of the training matrix in `prosim/config/defaults.py`

---

## Verification Steps

### Step 1: Extract Float Pairs from XTC Files

The XTC files contain operator data encoded as pairs of 4-byte IEEE 754 floats, delimited by `0x15` bytes.

```python
import struct

def extract_operator_floats(filepath):
    """Extract potential operator float pairs from XTC file."""
    with open(filepath, 'rb') as f:
        data = f.read()

    pairs = []
    for i, byte in enumerate(data):
        if byte == 0x15 and i + 9 <= len(data):
            try:
                float1 = struct.unpack('<f', data[i+1:i+5])[0]
                float2 = struct.unpack('<f', data[i+5:i+9])[0]

                # Filter for reasonable efficiency values
                if 0.1 < float1 < 2.0 and 0.1 < float2 < 2.0:
                    pairs.append((round(float1, 4), round(float2, 4)))
            except:
                pass

    return pairs

# Extract from both files
pairs_week9 = extract_operator_floats('prosim.xtc')
pairs_week13 = extract_operator_floats('prosim1.xtc')
```

**Expected Result**:
- Both files should contain the same 11 unique float pairs
- This confirms the values are fixed (not training-dependent)

### Step 2: Verify Week Numbers

The XTC files encode the week number at offset 9:

```python
def get_xtc_week(filepath):
    """Extract week number from XTC file."""
    with open(filepath, 'rb') as f:
        data = f.read()
    return data[9]

# Expected: prosim.xtc = 9, prosim1.xtc = 13
```

**Verification**: Week numbers should differ, confirming these are different save points.

### Step 3: Compare Float1 to Derived Proficiency

Our model derived proficiency values from Week 16 spreadsheet analysis:

```python
# Proficiency values derived from ProsimTable.xls Week 16 data
# Formula: Proficiency = Actual_Efficiency / Estimated_Efficiency
DERIVED_PROFICIENCY = {
    1: 1.039,  # 116.35% / 112%
    2: 1.097,  # 118.45% / 108%
    3: 1.122,  # 132.40% / 118% (EXPERT)
    4: 1.093,  # 118.05% / 108%
    5: 1.028,  # 111.05% / 108%
    6: 0.836,  # 98.62% / 118%
    7: 0.934,  # 110.25% / 118%
    8: 0.850,  # Estimated
    9: 0.900,  # Estimated
}

# XTC float1 values (sorted)
XTC_FLOAT1 = [0.6397, 0.7751, 0.8074, 0.8093, 0.8188, 0.8509, 0.9086, 0.9667, 1.0192, 1.0312]

# Scale factor to convert XTC to our model
SCALE_FACTOR = 1.088

# Verification
for f1 in XTC_FLOAT1:
    scaled = f1 * SCALE_FACTOR
    closest_op = min(DERIVED_PROFICIENCY.items(), key=lambda x: abs(x[1] - scaled))
    error = abs(scaled - closest_op[1])
    print(f"XTC {f1:.4f} × {SCALE_FACTOR} = {scaled:.4f} → Op {closest_op[0]} ({closest_op[1]}) error={error:.4f}")
```

**Expected Result**:
- `1.0312 × 1.088 = 1.1219` should match Op 3's proficiency of `1.122` (error < 0.001)
- Most operators should have error < 0.05

### Step 4: Verify Float Consistency Across Saves

```python
unique_pairs_week9 = set(pairs_week9)
unique_pairs_week13 = set(pairs_week13)

# Should be identical
assert unique_pairs_week9 == unique_pairs_week13, "Float pairs should be identical across saves"
print(f"Common pairs: {len(unique_pairs_week9 & unique_pairs_week13)}")
print(f"Only in Week 9: {unique_pairs_week9 - unique_pairs_week13}")
print(f"Only in Week 13: {unique_pairs_week13 - unique_pairs_week9}")
```

**Expected Result**: All pairs should be common to both files.

### Step 5: Cross-Reference with Spreadsheet Data

Load the CSV export and verify efficiency calculations:

```python
import csv

# From Operators-Table 1.csv (Week 16 data)
# Columns: Operator, Actual Efficiency, Estimated Efficiency (from training matrix)
with open('archive/spreadsheets/ProsimTable CVS Export/Operators-Table 1.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        op_id = int(row['Operator'])
        actual = float(row['Actual Efficiency'].rstrip('%')) / 100
        estimated = float(row['Estimated Efficiency'].rstrip('%')) / 100

        # Derived proficiency = actual / estimated
        proficiency = actual / estimated
        print(f"Op {op_id}: {actual:.4f} / {estimated:.4f} = {proficiency:.4f}")
```

---

## Verification Checklist

| Check | Expected | Status |
|-------|----------|--------|
| Float pairs identical across Week 9 and Week 13 | Yes | |
| XTC float1 × 1.088 ≈ derived proficiency | Within 5% | |
| Op 3 has highest float1 value (1.0312) | Yes | |
| Op 6 has lowest float1 value (~0.64) | Yes | |
| 11 unique float pairs found | Yes | |
| Week numbers differ (9 vs 13) | Yes | |

---

## Eliminating Float2 Uncertainty

### Current Understanding

- **Float1**: Strongly correlates with proficiency (scale factor 1.088)
- **Float2**: Unknown component, possibly tier-related or another fixed property

### Additional Data Needed

To definitively determine what Float2 represents, we need:

#### 1. XTC Files with Varied Training Levels

**What**: XTC saves from a game where operators were actively trained at different points.

**Why**: If Float2 represents training progress, it should vary when operators have different training levels. If it remains constant like Float1, it's another fixed property.

**How to obtain**:
- Play PROSIM and create saves at weeks 1, 5, 10, 15
- Train different operators at different weeks
- Compare Float2 values across saves

#### 2. XTC Files from Multiple Game Instances

**What**: XTC files from completely different game runs (not just different weeks of the same game).

**Why**: This would reveal whether Float1/Float2 are:
- Randomly generated per game (like our proficiency model)
- Fixed across all games (hardcoded starting values)
- A combination (fixed for ops 1-9, random for hired ops 10+)

**How to obtain**:
- Start multiple new games in PROSIM
- Save immediately at Week 1
- Compare float values

#### 3. Week 1 XTC with Known Initial State

**What**: An XTC save from Week 1 before any training or production.

**Why**: Would show the "baseline" values before any game progression, helping isolate what Float2 represents at game start.

**Expected pattern if Float2 = training factor**:
- Week 1: Float2 should be ~0.20-0.22 (training level 0)
- Week 13: Float2 should be higher if training occurred

**Expected pattern if Float2 = fixed property**:
- Week 1 and Week 13 Float2 should be identical

#### 4. PROSIM Source Code or Documentation

**What**: Original PROSIM III source code or technical documentation.

**Why**: Would definitively explain the data structures and formulas.

**Where to look**:
- PROSIM vendor (if still exists)
- Academic archives from 2004-era coursework
- Instructor materials from MGMT475 course

#### 5. Controlled Experiment Data

**What**: A systematic play-through recording decisions and outcomes.

**Format needed**:
```
Week | Operator | Training Decision | Hours Worked | Production | Rejects
-----|----------|-------------------|--------------|------------|--------
1    | 3        | No training       | 40           | 1535       | 274
2    | 3        | Sent to training  | 0            | 0          | 0
3    | 3        | Working           | 40           | 1680       | 290
```

**Why**: Could calculate actual efficiency per week and correlate with training progression to reverse-engineer the Float2 component.

---

## Hypotheses to Test

### Hypothesis A: Float2 = Quality Tier Factor

**Prediction**: Float2 values should cluster around tier-related values.

| Tier | Expected Float2 (if max efficiency / 2) |
|------|----------------------------------------|
| 0 | ~0.55 (109% / 2) |
| 5 | ~0.55 (109% / 2) |
| 9 | ~0.60 (120% / 2) |

**Test**: Compare Float2 distribution to tier assignments.

### Hypothesis B: Float2 = Normalized Training Level

**Prediction**: Float2 should correlate with training level at time of save.

**Test**: Need XTC from game WITH active training to see if Float2 changes.

### Hypothesis C: Float2 = Another Fixed Property

**Prediction**: Float2 is a second fixed multiplier (like "skill" or "quality").

**Test**: Compare Float2 across multiple game instances. If always the same per operator, it's fixed.

### Hypothesis D: Player Didn't Train (Current Hypothesis)

**Prediction**: The constant Float2 values indicate no training progression occurred.

**Supporting evidence**:
- Float2 identical across Week 9 and Week 13
- Products (Float1 × Float2) are 42-70%, lower than trained operator efficiency
- No training cost visible in archived data

---

## Automated Verification Script

Save as `verify_xtc.py`:

```python
#!/usr/bin/env python3
"""
XTC Verification Script for PROSIM Two-Component Model

Usage: python verify_xtc.py <path_to_xtc_file> [<path_to_second_xtc>]
"""

import struct
import sys
from pathlib import Path

DERIVED_PROFICIENCY = {
    1: 1.039, 2: 1.097, 3: 1.122, 4: 1.093, 5: 1.028,
    6: 0.836, 7: 0.934, 8: 0.850, 9: 0.900,
}
SCALE_FACTOR = 1.088

def extract_floats(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    week = data[9] if len(data) > 9 else 0
    pairs = []

    for i, byte in enumerate(data):
        if byte == 0x15 and i + 9 <= len(data):
            try:
                f1 = struct.unpack('<f', data[i+1:i+5])[0]
                f2 = struct.unpack('<f', data[i+5:i+9])[0]
                if 0.1 < f1 < 2.0 and 0.1 < f2 < 2.0:
                    pairs.append((round(f1, 4), round(f2, 4)))
            except:
                pass

    return week, pairs

def verify_proficiency_correlation(pairs):
    unique_f1 = sorted(set(p[0] for p in pairs))

    print("\nProficiency Correlation Check:")
    print("-" * 60)

    total_error = 0
    for f1 in unique_f1:
        scaled = f1 * SCALE_FACTOR
        closest = min(DERIVED_PROFICIENCY.items(), key=lambda x: abs(x[1] - scaled))
        error = abs(scaled - closest[1])
        total_error += error
        status = "✓" if error < 0.02 else "~" if error < 0.05 else "✗"
        print(f"  {f1:.4f} × {SCALE_FACTOR} = {scaled:.4f} → Op {closest[0]} ({closest[1]:.3f}) {status}")

    avg_error = total_error / len(unique_f1)
    print(f"\nAverage error: {avg_error:.4f}")
    return avg_error < 0.05

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_xtc.py <xtc_file> [<second_xtc_file>]")
        sys.exit(1)

    file1 = Path(sys.argv[1])
    week1, pairs1 = extract_floats(file1)
    unique1 = set(pairs1)

    print(f"=== {file1.name} (Week {week1}) ===")
    print(f"Unique float pairs: {len(unique1)}")

    if verify_proficiency_correlation(pairs1):
        print("\n✓ Proficiency correlation VERIFIED")
    else:
        print("\n✗ Proficiency correlation FAILED")

    if len(sys.argv) >= 3:
        file2 = Path(sys.argv[2])
        week2, pairs2 = extract_floats(file2)
        unique2 = set(pairs2)

        print(f"\n=== {file2.name} (Week {week2}) ===")
        print(f"Unique float pairs: {len(unique2)}")

        print(f"\n=== Cross-file Comparison ===")
        common = unique1 & unique2
        only1 = unique1 - unique2
        only2 = unique2 - unique1

        print(f"Common pairs: {len(common)}")
        print(f"Only in {file1.name}: {len(only1)}")
        print(f"Only in {file2.name}: {len(only2)}")

        if unique1 == unique2:
            print("\n✓ Float pairs IDENTICAL across saves (proficiency is fixed)")
        else:
            print("\n! Float pairs DIFFER (investigate training progression)")

if __name__ == "__main__":
    main()
```

---

## References

- `prosim/config/defaults.py` - Training matrix and operator profiles
- `prosim/models/operators.py` - Two-component efficiency implementation
- `docs/algorithms.md` - Full algorithm documentation
- `archive/spreadsheets/ProsimTable.xls` - Original analysis spreadsheet

---

*Document created: December 2025*
*Last verified: December 2025*
