# Week-13 Ending State (Nelson, company 2) — derived for the DECS14→REPT14 replay

Every value below is the week-14 *beginning* state, which equals week-13 *ending*.
Confidence: **derived-exact** (present verbatim in REPT14's own beginning columns),
**inferred** (reconstructed via an identity), **assumed** (no direct evidence).

## Inventories — derived-exact
REPT14's "Beginning Inventory" column is, by definition, week-13's ending inventory.
Corroborated: REPT12/REPT13 (different games) show the *identical* beginning
inventory block, i.e. all three reports were generated from one shared saved state.

| Item | Week-13 ending | Confidence |
|------|---------------:|------------|
| Raw materials | 0 | derived-exact |
| Parts X′ | 1139 | derived-exact |
| Parts Y′ | 492 | derived-exact |
| Parts Z′ | 1517 | derived-exact |
| Products X | 1472 | derived-exact |
| Products Y | 1032 | derived-exact |
| Products Z | 1317 | derived-exact |

Identity checks against REPT14 ending balances (all close within rounding):
- Parts X′: 1139 + 600 recd + 6469 produced(gross) − 4860 used = **3348** ✓ (rept 3348)
- Parts Y′: 492 + 500 + 1113 − 1883 = **222** ✓ (rept 223, ±1 rounding)
- Raw mat: 0 + 22000 − 10247 = **11753** ✓ (rept 11753)

## Cumulative costs through week 13 — derived-exact
The report's "cumulative" is a **2-week accounting-period total** (period = weeks
13–16, resets at week 13). So `cum14 = wk13 + wk14`, giving week-13 costs exactly.
Confirmed by overhead: cum quality 1500 = 750+750, cum maint 1100 = 600+500.

| Category | Week-13 total | Category | Week-13 total |
|----------|-------------:|----------|-------------:|
| Labor | 3600 | Parts carrying | 298 |
| Setup | 80 | Products carrying | 938 |
| Repair | 400 | Demand penalty | 0 |
| Raw materials | 12451 | **Product subtotal** | **34643** |
| Purchased parts | 8876 | Overhead subtotal | 10050 |
| Equipment | 8000 | **TOTAL wk13** | **44693** |

## Week-14 receipts — observed inputs (set by week ≤13 ordering decisions)
These arrive *in* week 14 but were ordered earlier; the engine would need its
order book seeded with them (they cannot be derived from DECS14, which orders
RM 10000 regular / 0 expedited and 0 purchased parts).

| Receipt | Amount | Confidence |
|---------|-------:|------------|
| Raw materials received | 22000 | derived-exact (REPT14 line 24) |
| Parts X′ received | 600 | derived-exact |
| Parts Y′ received | 500 | derived-exact |
| Parts Z′ received | 400 | derived-exact |

## Operator state — derived-exact (efficiency), inferred (tier/level)
Each operator's **effective efficiency multiplier** at week 14 is known exactly:
it is recorded in `ProsimTable(Nelson).xls` → Operators tab, and independently
re-derived from REPT14 via `efficiency = gross ÷ (productive_hours × base_rate)`.
Both sources agree to 4+ decimals for all 9 operators.

| Operator | Efficiency | Dept/type (wk14) | base rate |
|---------:|-----------:|------------------|----------:|
| 3 | 1.25208 | parts X′ | 60 |
| 5 | 0.65600 | parts Y′ | 50 |
| 2 | 0.91491 | parts X′ | 60 |
| 7 | 1.05583 | parts X′ | 60 |
| 4 | 0.67552 | assembly X | 40 |
| 6 | 0.92690 | assembly Y | 30 |
| 1 | 0.84000 | assembly X | 40 |
| 26 | 0.72170 | assembly Y | 30 |
| 18 | 0.67816 | assembly Y | 30 |

The engine's two-component model (`matrix[tier][level] × proficiency`) does **not**
factor cleanly to these values at any integer training level, so the exact
tier/level decomposition is *inferred/uncertain*; only the product (efficiency)
is derived-exact. The replay injects the exact efficiency as an oracle.

## Not recoverable from available data (assumed / flagged)
- **Week-13 machine→operator assignments** (needed to compute week-14 setup costs
  from part-type changes): unknown. Nelson's own week-13 DECS is not in the archive.
- **Productive (availability) hours** per operator in week 14: a stochastic input,
  taken as observed from REPT14 for the oracle run; the engine has no model for it.
- **Raw-material weighted-average unit price** ($1.1416 in wk14): a function of the
  full purchase-price history; taken as observed.
