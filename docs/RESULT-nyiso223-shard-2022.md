# RESULT — nyiso-223 shard, 2022 hub-daily unpriced-day gap fill (arm)

- **Shard**: `nyiso223-y2022` (session nyiso-223, NYISO)
- **Pinned SHA**: `ce4779ecd62db3c732e0d0cd7b910b80bc23ed99` (verified; no pull/rebase)
- **Base keeper**: `results/calibration/nyiso_fuelvintage_A` (`2026-09-09-nyiso-221-fuelvintage-span`)
- **Arm**: `nyiso_hub_gap_month_level=true`, `--years 2022`
- **Bundle**: `results/calibration/nyiso223_gapfill_2022/` (gitignored, local disk only — NOT committed, NOT registered)

## Hard stops & gates

| check | expected | observed | verdict |
|---|---|---|---|
| `git rev-parse HEAD` | `ce4779ec…ed99` | `ce4779ec…ed99` | PASS |
| `nyiso_fuelvintage_A/meta.json` iso | NYISO | NYISO | PASS |
| `grep -c nyiso_hub_gap_month_level` | ≥ 4 | 4 | PASS |

**Pre-solve gate (zero LP)** — matched the PRECOMMIT to the digit:

| quantity | PRECOMMIT | observed |
|---|---|---|
| annual mean off → on | 8.4431 → 8.4431 | 8.4431 → 8.4431 |
| Dec 22–31 off → on | 8.049 → 8.949 | 8.049 → 8.949 |
| hours moved | 4440 | 4440 |

The mean-preservation identity holds exactly.

**Post-solve config signature** (from `run_config.json → scenario_config`):

| field | required | observed |
|---|---|---|
| `nyiso_hub_gap_month_level` | true | **true** |
| `offer_curve_by_group.CC_REGULAR.peak` | 2.25 | **2.25** |
| `offer_curve_by_group.CC_REGULAR.pct_peaking` | 8.0 | **8.0** |
| `nyiso_gas_commitment_bridge` | true | **true** |
| `nyiso_dynamic_reserve_requirements` | true | **true** |
| iso / years | NYISO / [2022] | NYISO / [2022] |

Solve: P0 + P1, P1 cold rebuild on floored fleet, matrix 2.153 s, simplex 266,840 iterations, objective 5,552,492,054.70.

## 6. THE ARM'S OWN TARGET WINDOW (equal-hour mean, load-weighted across the 5 load zones)

| window | keeper | **arm** | actual | arm − keeper |
|---|---|---|---|---|
| **Dec 22–31** (n=240) | 63.87 | **66.68** | 187.19 | **+2.81** |
| **Dec 1–21** (n=504) | 71.83 | **69.39** | 72.39 | **−2.44** |

**This is the headline: the arm moves its own target window by +$2.81 against a
$123 gap, closing ~2.3 % of it, and simultaneously moves Dec 1–21 $2.44 the
wrong way (away from a window the keeper already matched to within $0.56).**
The +0.90 $/MMBtu the gap fill adds to Dec 22–31 delivered gas (8.049 → 8.949)
translates to only ~$2.8/MWh of price, and the mean-preserving offset removes a
comparable amount from the rest of December, where the keeper was already right.

## 1. C3a — mean LMP

- Model load-weighted annual mean LMP: **69.8215 $/MWh**
- Model equal-hour mean of the load-weighted ISO price: **65.1949 $/MWh**
- % error vs actual: **NOT COMPUTABLE IN THIS SHARD** — see "Actual-side gap" below.

## 2. C3b — monthly shape

Actual-side NRMSE **NOT COMPUTABLE IN THIS SHARD** (same gap). Model monthly
means of the load-weighted ISO price ($/MWh), Jan→Dec:

```
102.74  57.39  47.67  46.90  64.89  61.34  86.10  97.29  67.08  41.45  38.73  68.52
```

## 3. C3c — price tail / scarcity

| quantity | value |
|---|---|
| model hours, load-weighted ISO price > $300 | **8** |
| model hours, ANY zone > $300 | **10** |
| actual hours > $300 (PRECOMMIT) | **101** |
| **model maximum zonal price** | **2000.00 $/MWh** (NYC, hour 3616) |

The model reproduces 8–10 of 101 tail hours. C3c is the known model-class
limitation already ledgered as a standing caveat for NYISO (rule 22 `[R-C3C]`).

## 4. C1 — per-class TWh (P1, grid-delivered dispatch)

| class | model TWh | keeper 2022 | actual |
|---|---|---|---|
| **CC_REGULAR** | **36.931** | 36.553 | 31.564 |
| import | 27.849 | | |
| nuclear | 26.753 | | |
| hydro | 25.610 | | |
| **CC_CHP** | **13.430** | | |
| **ST_GAS** | **6.532** | | |
| wind | 4.704 | | |
| CT_PEAKER | 4.293 | | |
| OTHER | 2.186 | | |
| CT_CHP | 2.083 | | |
| ST_CHP | 1.488 | | |
| biomass | 1.061 | | |
| COAL_PRB | 0.655 | | |
| oil | 0.506 | | |
| solar | 0.109 | | |
| COAL_BIT | 0.000 | | |
| **TOTAL** | **154.191** | | |

**CC_REGULAR moves the WRONG WAY**: 36.553 (keeper) → **36.931** (arm),
i.e. **+0.378 TWh** further ABOVE the 31.564 actual. The over-generation gap
widens from +4.989 to **+5.367 TWh**.

(Class totals differ slightly from the D-2 `class_total_twh` column, which is
computed on the diagnostics' own basis: CC_REGULAR 35.647, ST_GAS 8.563,
CC_CHP 13.529.)

## 5. C8 — forced share by class (D-2)

| class | forced share | limit | material | verdict |
|---|---|---|---|---|
| CC_REGULAR | 0.0026 | 0.30 | yes | pass |
| COAL | 0.0000 | 0.30 | yes | pass |
| CT_PEAKER | 0.0000 | 0.15 | yes | pass |
| **ST_GAS** | **0.2264** | 0.30 | yes | **pass** |
| hydro | 0.0000 | 0.30 | yes | pass |

**ST_GAS = 0.2264**, under its 0.30 budget. Its forcing is
`reliability_floor` 1.9323 TWh (0.2257 of class) plus
`nyiso_gas_commitment_bridge` 0.0064 TWh (0.0008).
Gas bridge overall: 27,904 unit-hours floored, 4.54 TWh floor volume,
583 segments (min_run extension ON).

## 7. Determination

**The run-level determination CANNOT be produced by this shard, and no
determination should be inferred from the numbers above.**

`scripts/calibration_verdict.py` scores from *committed* artifacts — the
registry sidecar, the run payload and the per-(ISO, year) benchmark parts. A
screen bundle is deliberately never registered (rule 29 `[R-SCREEN]` clause 2),
so those inputs do not exist for it. `replay_keeper.py` writes the bundle and
`legitimacy_diagnostics.json` but no `metrics.json`. Scoring is the parent's
job at composition time.

What this shard CAN state, from the committed-in-bundle diagnostics:

| diagnostic | verdict |
|---|---|
| D-1 diurnal shape | **PASS** |
| D-2 forced-energy attribution (C8) | **PASS** |
| **D-4 off-window binding** | **FAIL** |
| D-5 forecast/backcast parity | PASS |
| D-9 overlay quarantine | PASS |
| D-10 free-class-only rescore | PASS |

The solve emitted: `WARNING: legitimacy diagnostics gate FAIL on the replayed
bundle`. **D-4 fails on 3 unit-conduct rows** totalling 0.0092 TWh of floored
energy — floors binding in hours the units' own CAMPD conduct says they were
offline:

| floor | plant | floored TWh | binding h | measured median MW | measured zero-share |
|---|---|---|---|---|---|
| reliability_floor × ST_GAS | 2480 | 0.0005 | 151 | 0.0 | 0.980 |
| reliability_floor × ST_GAS | 8006 | 0.0037 | 70 | 0.0 | 0.614 |
| nyiso_gas_commitment_bridge × CC_REGULAR | 52056 | 0.0050 | 228 | 0.0 | 0.807 |

**This D-4 failure is not attributable to the arm** on the evidence available
here: the gap fill is a delivered-gas-price change and touches no floor window,
and no keeper-recipe 2022 control bundle exists in this container to difference
against. The parent should treat D-4 as an open 2022 question, not as an arm
effect.

## Actual-side gap — what this shard could not compute, and why

C3a % error and C3b NRMSE need the actual price series. The `lmp` clean
partition **cannot be built in this container**: `curate_lmp` aborts with
`KeyError: 'MGHG'`, a pre-existing curation defect unrelated to this arm.
Repairing it would be infrastructure work, which a shard must not do, so it was
left alone. `generation` / `validation` were likewise unavailable. The parent
scores both criteria from the committed benchmark parts at registration, where
this gap does not apply.

Actual anchors quoted above (101 tail hours; Dec 22–31 $187.19; Dec 1–21
$72.39; CC_REGULAR 31.564 TWh) are the PRECOMMIT's own figures, not recomputed
here.

## Data regeneration performed (no `src/`, no `scripts/`, no code edits)

The container's `data/clean` tree was empty. Two datatypes were regenerated
through the project's documented entrypoint, each named by the error that
demanded it:

1. `capacity-deliverability` — the NYISO 2022/2023 Long Island
   `transfer_security_limit` (940 MW) that `nyiso_li_lcr_tsl` requires.
2. `nyiso-interface-flows` — required by `nyiso_seam_par_attribution` for 2022.

Both are derived, gitignored and disposable. No source file was modified.

## Recommendation (advisory — the promotion decision is the owner's, rule 31)

On this single year the arm does **not** deliver what it was screened for: it
closes ~2.3 % of its own target-window gap, degrades the adjacent in-month
window, and widens the CC_REGULAR over-generation that is NYISO 2022's larger
defect. Under rule 29 `[R-SCREEN]` the structural screen is a **STOP gate that
may kill an arm and may never promote one**, so this is reported as evidence,
not as a verdict.

**RULE 31 `[R-RETAIN]` NOTICE — the bundle is on local disk, is gitignored, and
will NOT survive container reclamation. It has not been deleted. The promotion
question is open and belongs to the owner.**
