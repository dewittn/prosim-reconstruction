# PROSIM Reconstruction - Calibration Report

## Overview

This document summarizes the calibration findings from Phase 3 of the PROSIM reconstruction project. The calibration was performed by analyzing original simulation output files (REPT12.DAT, REPT13.DAT, REPT14.DAT) and comparing them against the documented case study values.

## Summary of Accuracy

| Category | Target | Achieved | Notes |
|----------|--------|----------|-------|
| Production Rates | Verified | 100% | Rates match documentation |
| Reject Rates | Variable | Documented | 15.14% of gross at $750, varies with quality budget down to a ~1.5% floor (corrected Jul 2026 per Discovery #19; the old 11.85%-17.8% range mixed net- and gross-basis figures) |
| Cost Parameters | Verified | 100% | All verified costs match |
| Operator Efficiency | Variable | Documented | 58% - 100% observed |
| Lead Times | Verified | 100% | Match documentation |

## Detailed Findings

### 1. Production Rates (Verified)

Production rates match the case study documentation exactly:

**Parts Department:**
- X': 60 parts per productive hour
- Y': 50 parts per productive hour
- Z': 40 parts per productive hour

**Assembly Department:**
- X: 40 products per productive hour
- Y: 30 products per productive hour
- Z: 20 products per productive hour

**Production Formula (Verified):**
```
Productive Hours = (Scheduled Hours - Setup Time) * Operator Efficiency
Gross Production = Productive Hours * Production Rate
Rejects = Gross Production * Reject Rate
Net Production = Gross Production - Rejects
```

### 2. Reject Rate Calibration

> **Corrected Jul 2026 per Discovery #19**: the "observed reject rate" figures below
> were computed as `rejects / net_output` (the REPT "Production" column is NET good
> units), not `rejects / gross_output`. The week-14 figure (17.8%) is exactly the
> net-basis form of the verified $750 anchor (15.14% of gross); the week-12/13 rows
> likely reflect different quality budgets and/or the same net-vs-gross conflation,
> not a distinct week-to-week drift model. The `adjusted_rate` calibration model
> below predates this correction and should not be used — see
> `prosim/config/defaults.py:calculate_reject_rate()` for the current, REPT14-anchored
> logarithmic formula (base_rate 0.1514 at $750, applied to GROSS output).

Reject rates vary by week, strongly suggesting they are influenced by quality budget or other factors:

| Week | Observed Reject Rate (net-basis) | Quality Budget |
|------|---------------------|----------------|
| 12 | ~11.85% | ~$750 |
| 13 | ~15.0% | Unknown |
| 14 | ~17.8% | Variable |

**Calibration Model (superseded — see note above):**
```python
adjusted_rate = base_rate + (optimal_budget - quality_budget) * sensitivity
```

Where:
- `base_rate` = 0.1185 (at $750 quality budget)
- `optimal_budget` = $750
- `sensitivity` = 0.0001

### 3. Operator Efficiency Calibration

**Documented Ranges:**
- Trained operators: 95% - 100%
- Untrained operators: 60% - 90%

**Observed Ranges:**
- Week 1: 83.25% - 100% (parts: 83-93%, assembly: 90-100%)
- Week 14: 58% - 100%

**Finding:** Observed minimum efficiency (58%) falls below the documented 60% minimum. This suggests either:
1. New hires have lower initial efficiency
2. Documentation represents average rather than absolute minimum
3. Additional factors affect efficiency

### 4. Cost Parameters (Verified)

All cost parameters from week1.txt have been verified:

| Parameter | Value | Status |
|-----------|-------|--------|
| Labor (hourly) | $10.00, on SCHEDULED hours + 1.5x overtime >40h | Verified (corrected Jul 2026 per Discovery #19; was productive-hours basis) |
| Equipment (hourly) | ~$21.05, per SCHEDULED hour (8000/380 in REPT14) | Verified (corrected Jul 2026 per Discovery #19; was $20.00 on productive hours) |
| Machine Repair | $400.00/incident | Verified |
| Hiring Cost | $2,700.00/new hire | Verified |
| Layoff Cost | $200.00/week | Verified |
| Termination Cost | $400.00 | Verified |
| Fixed Expense | $1,500.00/week | Verified |
| Training Cost | $1,000.00/session | Estimated |

### 5. Lead Times (Verified)

| Order Type | Lead Time | Status |
|------------|-----------|--------|
| Regular Raw Materials | 3 weeks | Verified |
| Expedited Raw Materials | 1 week (+$1,200) | Verified |
| Purchased Parts | 1 week | Verified |

### 6. Stochastic Elements

**Machine Repair:**
- Probability: ~10-15% per machine per week
- Cost: $400 per repair (verified)
- Model: Random event based on probability

**Demand Variance:**
- Standard deviation varies by weeks until shipping
- 4 weeks out: σ = 300
- 3 weeks out: σ = 300
- 2 weeks out: σ = 200
- 1 week out: σ = 100
- Shipping week: σ = 0 (actual revealed)

## Test Coverage

The calibration is supported by 343 tests with 89% code coverage:

- **Calibration Tests:** 43 tests covering all calibration functions
- **Validation Tests:** 43 tests comparing against original files
- **Integration Tests:** 27 tests for full simulation workflow
- **Unit Tests:** 230+ tests for individual modules

## Known Discrepancies

1. ~~**Reject Rate Variation:** The 17.8% reject rate from the case study appears to be a maximum or reference value. Actual rates vary based on quality budget.~~ **RESOLVED (Discovery #19, Jul 2026):** 17.8% was `rejects / net_output`; the true quality-budget-driven rate is 15.14% of GROSS output at $750, and the logarithmic curve anchored on that point reproduces all 9 REPT14 operators exactly.

2. **Untrained Efficiency Lower Bound:** Observed efficiency (58%) can fall below documented 60% minimum.

3. **REPT File Independence:** Original REPT12, REPT13, REPT14 are from different simulation runs/players, but are NOT unrelated — corrected Jul 2026 per Discovery #19: all three share exact beginning inventories and descend from one instructor-distributed saved state (divergent branches of a common scenario, not independent runs). Cumulative costs still don't increase across the files because they are different branches, not sequential weeks of one game.

## Configuration

The calibration module provides utilities for creating calibrated configurations:

```python
from prosim.engine.calibration import create_calibrated_config

# Create config with dynamic reject rate
config = create_calibrated_config(
    quality_budget=750.0,
    use_dynamic_reject_rate=True
)
```

## Reproducibility

All stochastic elements support random seed configuration for reproducible simulations:

```python
from prosim.engine.simulation import Simulation

simulation = Simulation(config=config, random_seed=42)
```

## Conclusion

The PROSIM reconstruction achieves high accuracy against the original simulation:

- All verified parameters match documentation exactly
- Variable parameters (reject rate, efficiency) have documented ranges
- Stochastic elements are properly modeled with reproducibility support
- Comprehensive test coverage validates the implementation

The 97% accuracy target from the case study is achievable when using calibrated parameters appropriate for the specific simulation scenario. **Note (Jul 2026, Discovery #17):** the remembered "97%" figure is best explained as the cumulative in-game efficiency score (0.949 at the last saved snapshot, trending toward ~0.97 in the final weeks), not a literal forecast-accuracy metric — 2004 spreadsheet forecasts scored 89% per-operator / 93% on net output, while the underlying production mechanics reproduce game output exactly (100%) when given correct inputs (Discovery #19).
