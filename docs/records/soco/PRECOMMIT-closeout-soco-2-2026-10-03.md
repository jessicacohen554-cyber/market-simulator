# PRECOMMIT closeout-SOCO-2 — SOCO nuclear availability 2019–2022 at measured monthly CF

Lane `claude/closeout-soco-2`, 2026-10-03. This document was written **before any
LP**, and every reading below was fixed before a number exists. The evidence is
`FINDING-closeout-soco-2-2026-10-03.md` (zero LP).

## 1. Change (one, admissible)

**What changes.** `constants.NUCLEAR_MONTHLY_CF_BY_YEAR["SOCO"]` gains 2019–2022
rows, produced by the frozen `scripts/data/derive_nuclear_monthly_cf.py --isos
SOCO`. `--check` reproduces the 2023–25 rows byte-for-byte.

**What it replaces.** The forecast fallback `NUCLEAR_MONTHLY_CF["SOCO"] × (1 −
EFORD)`, a flat ~0.889 fleet CF that every 2019–2022 leg reads today.

**Why it is admissible:**
- Rule 14: the input was an estimate where measured data was on disk.
- Rule 19: it replaces the fallback rather than stacking on it.
- Rule 13: it is the same input the 2023–25 legs already read.
- Rule 23: it is an initial derivation for years the table never carried, not a
  re-derivation. Precedent: ercot-253's ERCOT 2021 row.

**What it is not.** It is not a `ScenarioConfig` field, so there is no new matrix
row. It moves no tuned value and adds no DOF.

**Cache key.** SolveEpoch `2026-10-03a` (backcast SOCO) re-keys the bundle,
because the SOCO row of this table is undeclared in the solve surface.

**Recipe.** The keeper recipe (`w0_soco_span` replay), with no `--set`, at the lane
SHA.

**Shards.** Seven, one per year 2019–2025, under rule 36. 2023–25 are byte-inert to
this change. They are re-solved so the bundle comes from a single SHA:
- The G-DRIFT hunks since `25da6022` that touch SOCO are soco-100 and soco-101.
  Both are default-off seam blocks, and every backcast year is tabulated, so they
  are INERT.
- The EIA-923 Final 2025 refresh of the F923 fuel overlay is **LIVE for 2025**.
  Every 2025 number in the RESULT carries that drift label.

## 2. The desk's bar (verbatim) and the pre-fixed reading

| Gate | Bar | Zero-LP reading (greedy, FINDING §b′) | Expected |
|---|---|---|---|
| B1 | 2019 CC_REGULAR back inside C1 (±3.0 pp) | 3.64 → 3.41 pp | **FAIL** |
| B2 | 2021 CC_REGULAR back inside C1 | 3.58 → 2.78 pp | **PASS** |
| B3 | No passing (year, criterion) leaves its band | no status flip in any class-year | PASS |
| B4 | C3a no worse by > 1 pp in any year | 2019 −1.0 pp better; 2020 −0.8 better; 2021 \|−4.3\| → \|−6.5\| (**2.2 pp worse**, still inside ±10 %); 2022 0.2 worse | **FAIL** (2021) |

**The desk's bar is expected to fail on B1 and B4.**

- **B1 residual.** The 2019 residual is the mirror of the ledgered 2019 COAL_BIT
  self-commitment. Its routes are adjudicated:
  - take-or-pay: G;
  - take floor: G;
  - coal campaign floor: refused;
  - startup amortization: G;
  - replacement-cost coal: spot ≥ blended at SOCO's BIT plants in 2019/2021.
- **B4 2021 cost.** The 2021 C3a cost is the price of measured nuclear displacing
  in-merit CC, and C3a stays PASS.

## 3. The repair's own pass/fail (rule 1: structure first)

These are fixed now. Each gate is scored on the composed bundle.

| Gate | Pass condition |
|---|---|
| S1 (the repair works) | Model nuclear 2019 / 2020 / 2021 / 2022 is within ±2.0 % of EIA-923 (47.7 / 47.6 / 48.9 / 47.1 TWh). Today it misses by −5.2 / −4.6 / −6.9 / −3.2 %. |
| S2 (inert where it should be) | 2023 and 2024 class totals are within 0.05 TWh of the keeper, every class. 2025 is reported with the EIA-923 2025 drift label and is not gated. |
| S3 (no collateral) | No C1/C2 (class, year) flips PASS → FAIL. No C3a year flips PASS → FAIL. C8 forced shares move by ≤ 2 pp. |
| S4 (direction) | CC_REGULAR 2021 share falls by ≥ 0.5 pp. CC_REGULAR 2019 share falls by ≥ 0.1 pp. |

**Decision rule, set ex ante:**
- **If S1–S4 all pass:** recommend promotion on structure (rules 1 and 14), with
  the B1/B4 shortfall recorded as a determination cost. CC 2019 stays FAIL, so SOCO
  stays NOT-YET unless the desk routes the 2019 CC row to the existing 2019
  self-commitment ledger row.
- **If S1 fails:** the repair does not do what it claims. Hold, and root-cause it.
- **If S2 fails:** stop and classify the drift before any promotion.
- **If S3 fails:** report it, with no promotion recommendation.

## 4. Not done here (recorded so nobody repeats it)

- **R-3 coal take ceiling for SOCO** (`coal_fuel_inventory`, SOCO U). The FINDING
  §c census shows it closes the coal exit-carry over-run cross-ISO, but it pushes
  SOCO CC **up**. It is a separate lane, which also reaches Scherer 2022.
- **`coal_marginal_replacement_pricing`** (plan §3.8 row 2). For CC it is wrong-way
  or inert, because spot ≥ blended at SOCO BIT in 2019/2021. It stays a 2022-only
  question.
- **The E.1 excess over CEMS-demonstrated capability** (1.1–1.9 TWh, four plants).
  No admissible construction is identified.
- **The DO-NOT-REDO list in the charter** is respected.
