# RESULT — MISO: the measured monthly gas LEVEL, PROMOTED; and an unmeasured HEAD drift found in the process

**Session:** `miso-fuelvintage-1` · **Date:** 2026-09-09 · **ISO: MISO only.**
**PRECOMMIT:** `docs/PRECOMMIT-miso-fuelvintage-ep-level-2026-09-09.md` (written before any LP).
**Base:** `origin/main` @ `9dc1c694`. **Control:** `results/calibration/miso248_fullspan_K`
(`2026-09-09-miso-248-spp-ladder`) — **not** the `miso247_fullspan_K` the handoff names (§1).

---

## 0. The census number first, as the handoff asks

> **100.000 % of MISO's gas capacity-hours are F923 print-derived, in 2023, 2024 AND 2025** —
> every one of 1,609 / 1,616 / 1,614 gas rows, all 8,760 hours. `apply_plant_monthly_fuel_prices`
> runs **after** the seam and overwrites every gas cell, so the seam's level never survives into
> `fuel_prices`. **The arm is INERT — measured, not inferred: 0 differing cells of ~28.3 M in the
> delivered-fuel array, 0 across the entire pre-LP state, and 0 across every hourly artifact of a
> real solve.** It is **promoted anyway**, on the owner's ruling of 2026-09-09.

| | |
|---|---|
| **Promotion** | **DONE.** `gas_electric_power_monthly_level` is ARMED in MISO's keeper recipe, full span 2023-2025, one bundle, registered. |
| **The arm's measured effect on the LP** | **EXACTLY ZERO.** Arm vs control at HEAD: identical simplex iteration count (388,398), identical objective (4,777,088,612.6964), **0 differing cells** in `system` / `class_hourly` / `class_band_hourly` / `reserve_family` / `storage`. |
| **What the seam DOES reach** | The ISO-level `_gas_series` only: 2023 annual 2.839 → **3.019** (+0.179, Jan **+1.000**); 2024 2.489 → **2.558** (+0.069, Jan **+1.551**) — reproducing `FINDING-xiso` §3's MISO rows to three decimals. **2025 is inert by coverage** (basket 0.400) and byte-identical, as pre-registered. Every `_gas_series` consumer is OFF on MISO's keeper. |
| **THE UNPLANNED FINDING, and it is cross-ISO** | Two changes this program asserted have **"ZERO effect on 2023-2025 by construction"** DO perturb the 2023-2025 LP solution — **not through capacity, which is exactly 0 MW, but through LP degeneracy.** §4. |
| **The successor** | **EIA-923 Schedule-5**, and it is already evidenced. §6. |

---

## 1. TWO CORRECTIONS TO THE HANDOFF, both made before any LP was spent

1. **MISO's keeper is not `miso247_fullspan_K`.** `miso-248` (`e4247c73`, 04:41 UTC) landed after
   the handoff was written and promoted MISO's keeper to **`2026-09-09-miso-248-spp-ladder` /
   `results/calibration/miso248_fullspan_K`**; `miso247_fullspan_K` was pruned under rule 15's
   keeper-only retention and does not exist at `origin/main`. Everything here uses the current
   keeper. *(This also corrects `FINDING-miso249` §1, which states "the keeper did not move at
   miso-248, which was a screen" — it did move; miso-249 committed three minutes after the
   promotion and raced it.)*
2. **The 2025 coverage drop-outs are LA and MI, not MN and MS.** The handoff says "basket 0.40 —
   MN and MS drop out". Measured, the states that fail the all-twelve-months test in 2025 are
   **LA .238 · MI .147 · MN .076 · AR .068 · MS .046 · MO .017 · KY .008** = 0.600 of MISO's gas
   capacity. Louisiana and Michigan dominate; MN and MS together are 0.122.

## 1a. THE PREDECESSOR RACE — `miso-249` did this census, and its disposition is SUPERSEDED

`PR #5746`, from this same branch name, merged **`7577449a` "miso-249: the measured monthly gas
LEVEL is provably inert on MISO's keeper"** at **04:44 UTC**, disposing: *"keep BUILT and
DEFAULT-OFF for MISO."* The owner's ruling recorded in **`ff3afcf3` at 05:25 UTC** — *"these
should be promoted as keepers on both 860 and gas shape counts regardless of inertness"* —
**postdates it by 41 minutes** and explicitly overrides "the disposition guidance in PROMPT 1-5
and in §A2, which told each lane to report an inert arm as its result and not spend the span."
miso-249 acted on guidance that was correct when written and superseded 41 minutes later. This
session executes the ruling.

**miso-249's measurements are independently reproduced here** on a different harness and against
the *current* keeper: print share 1.000/1.000/1.000, `_gas_series` 2.8392→3.0187 and
2.4893→2.5580, 2025 byte-identical. Two independent measurements, same numbers.

---

## 2. Phase 0 — the census (rule 29 `[R-SCREEN]` clause (0)), ZERO LP

### 2a. Admission, declared ex ante in the module and never swept

| year | basket coverage | admitted |
|---|---|---|
| 2023 | **1.000** (15 states) | ADMIT |
| 2024 | **1.000** (15 states) | ADMIT |
| 2025 | **0.400** (IA IL IN MT ND SD TX WI) | **refused — inert** |

### 2b. Reach

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| gas rows / capacity | 1,609 / 69,078.8 MW | 1,616 / 69,189.7 MW | 1,614 / 68,613.4 MW |
| **print-derived share of gas capacity-hours** | **1.000** | **1.000** | **1.000** |
| gas rows whose delivered price moves | 0 | 0 | 0 |
| **max \|Δ\| delivered gas, any unit, any hour** | **0.0** | **0.0** | **0.0** |
| max \|Δ\| any NON-gas fuel | **0.0** | **0.0** | **0.0** |
| `_gas_series` annual, control → arm | 2.839 → 3.019 (+0.179) | 2.489 → 2.558 (+0.069) | 3.819 → 3.819 (0.000) |
| `_gas_series` max monthly move | +1.000 (Jan) | +1.551 (Jan) | 0.000 |

### 2c. The rule-19 `[R-ONE-MECH]` answer (PROMPT 2 card 0(d)), settled before the solve

MISO's keeper carries `gas_plant_monthly_fuel_pricing = True`. In `resolve_fuel_prices` the seam
sets `gas_price_hourly`; `apply_plant_monthly_fuel_prices` then runs **after** it and overwrites
every gas cell with that plant's own F923 monthly print (or the nearby/class-aware pool, or —
under `f923_gas_price_plausibility_screen` — the plant's own `N3045<ST>3` state reference).
**Yes, it overwrites this seam per plant, and yes, that makes the arm inert.**

The surviving reach is `_gas_series`, whose only consumers are `coal_passthrough_series`
(`coal_prb/bit_passthrough_sigmoid` **False** — returns the flat scalar without calling it),
`prb_follower_passthrough_series` (`coal_prb_passthrough_tiered` **False**) and `runner.py`'s
MISO offer surface (`miso_offer_surface_measured` **False**). `miso_zonal_gas_basis` is a
**mean-zero spread**, orthogonal to a level.

**A rule-19 note the module should carry, recommended not applied** (it is the shared seam, not
MISO's file): the docstring's declared ordering is *national annual < state-average monthly <
measured hub index*. The **per-plant F923 print** is a fourth, more-local measured level that
supersedes the state-average monthly, and the ordering omits it. `FINDING-miso249` names the same
omission independently.

### 2d. Pre-LP identity, and the proof that the zero is a measurement

Whole pre-LP state (`fuel_prices`, `mc_base`, `demand`, CFs, capacities, every `FleetArrays`
field): worst \|Δ\| = **0** in 2023, 2024 and 2025.

**Positive controls on the same harness, 2023, one field at a time:**

| perturbation | worst \|Δ\| |
|---|---|
| `gas_plant_monthly_fuel_pricing = False` | `fuel_prices` 13.875, **`mc_base` 292.467** |
| `coal_plant_monthly_pricing = False` | `fuel_prices` 3.091, **`mc_base` 60.855** |
| `f923_gas_price_plausibility_screen = False` | `fuel_prices` 200.991, **`mc_base` 2,730.599** |

The first *is* the mechanism: with the print path off, the trajectory the seam moves reaches the
merit order at 292 $/MWh of `mc_base`. With it on — the keeper — it does not.

---

## 3. The screen and the A/B (rule 29 `[R-SCREEN]`)

Screen year **2024**, named in the PRECOMMIT before the screen ran, on the mechanism's **largest
measured footprint** (Jan +1.551 vs 2023's +1.000) — never on a residual.

| gate | result |
|---|---|
| **G-1** delivered gas moves as the pre-solve arithmetic implies (**0.0**) | **PASS** |
| **G-2** non-gas fuels move exactly 0.0 | **PASS** |
| **G-3** rule 19: armed level == `iso_electric_power_monthly_level('MISO',2024)` exactly, replaced not blended | **PASS** |
| **G-4** no non-target load-bearing criterion flips PASS → FAIL | **PASS** (§5 — nothing moves) |
| **G-5** slack and dump stay 0.0 | **PASS** (dump 0.0; slack identical arm↔control) |
| **G-0** (this session's own) screen reproduces the **committed keeper** bit-identically | **FAIL** — §4 |

**The A/B, measured on real solves, not inferred:**

| comparison | differing cells (system / class / band / reserve / storage) | worst \|Δ\| |
|---|---|---|
| **ARM vs CONTROL, both at HEAD** | **0 / 0 / 0 / 0 / 0** | **0** |
| CONTROL vs committed keeper | 6,989 / 4,850 / 8,729 / 1,097 / 1,946 | 4,678.426 |
| ARM vs committed keeper | 6,989 / 4,850 / 8,729 / 1,097 / 1,946 | 4,678.426 |

The last two rows are **identical cell for cell**. The decomposition is exact: **100 % of the
deviation from the committed keeper is HEAD drift and 0 % is the arm.** Both P1 solves reported
the same simplex iteration count (**388,398**) and the same objective
(**4,777,088,612.6964**).

---

## 4. THE UNPLANNED FINDING — "zero MW" is not "zero effect", and four sibling lanes pre-registered the wrong STOP

G-0's miss earned the control solve my PRECOMMIT pre-registered (rule 29(b): a LIVE hunk, and
only for the year the screen needs). It bought a clean root cause.

### 4a. G-DRIFT found two changes, neither in the keeper's tree

`git merge-base --is-ancestor <c> 70493448` (the keeper's base) is **NO** for both:

1. **`7934e92c`** — the retiree-window artifact widened 477 → 1,094 rows
   (`data/raw/eia-860/eia860_generator_retired_within_window.parquet`). **This is the xiso
   program's own Card A**, and it is a `data/raw/eia-860/` change that the handoff's prescribed
   G-DRIFT path list **does not cover**.
2. **`43edf7b1`** — ercot-261's `_PARTIAL_EXIT_WINDOW_START` 2023 → 2019, live for MISO because
   its keeper carries `partial_plant_exit_carry = True`.

### 4b. The fleet effect is exactly zero MW — measured, not asserted

For channel 2, rebuilding MISO's fleet at both values through the real `run_year(fleet_only=True)`
path, keyed on stable `unit_ids`:

| year | `n_gen` | rows ADDED | rows REMOVED | added nameplate | **max effective MW any hour** | max `min_gen` | max `pmin` | shared-row fleet Δ | shared-row `mc_base` Δ |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 3,427 → 3,598 | 171 | 0 | 3,298.899 MW | **0.000000000** | 0.0 | 0.0 | **0** | **0** |
| 2024 | 3,415 → 3,586 | 171 | 0 | 3,298.899 MW | **0.000000000** | 0.0 | 0.0 | **0** | **0** |
| 2025 | 3,395 → 3,566 | 171 | 0 | 3,298.899 MW | **0.000000000** | 0.0 | 0.0 | **0** | **0** |

98 COAL, 32 CC_REGULAR, 15 CT_PEAKER, 2 ST_CHP, 1 CT_CHP, 23 unclassed, across all six zones.
Every one is COD-masked offline before 2023-01-01 — the per-unit ageing of ADDENDUM §A9 working
exactly as it says. Their `ramp10` is nonzero (564.208 MW over 160 rows) but every reserve cap is
availability-scaled, so they supply zero reserve.

### 4c. But the LP solution moves anyway — this is DEGENERACY, not capacity

171 extra fixed-at-zero columns change HiGHS's path through a degenerate optimum. Measured,
control at HEAD vs committed keeper, 2024:

| quantity | value |
|---|---|
| zonal price cells differing | **6,920 of 70,080 (9.87 %)** |
| mean price Δ | **−0.008560 $/MWh** (MAE 0.010464, max **8.1215**) |
| mean price | 31.8792 vs 31.8878 (**−0.027 %**) |
| **max \|class-hour delta\|** | **854.720 MW** (`import`; CC_REGULAR 715.281, COAL_PRB 639.173) |
| class-hour cells differing | 4,850 of 157,680 (3.08 %) |
| total energy | 645.49506 vs 645.49481 TWh (**+0.000244 TWh, +0.000038 %**) |
| largest class annual Δ | COAL_PRB **+0.0734 TWh (+0.066 %)**; CT_PEAKER −0.0260; import −0.0204 |
| **slack total** | **19,566.9151 both — identical**, but 4,678.43 MW *reallocated between zones* in 13 hours |
| **dump** | 0.0 both |

**This directly contradicts a STOP condition pre-registered in the PJM, NYISO, NEISO and CAISO
prompts**, each of which requires *"max |class-hour delta| = 0.000000 MW vs the committed keeper,
all three years. A nonzero delta is a STOP."* For MISO it is **854.720 MW**, and the cause is
**not** "capacity-denominated code reading retired units" — that is measured at exactly 0 MW.
A lane that treats its nonzero delta as the pre-registered STOP will halt on a non-defect.

**The right disposition, and rules 1 / 14 support it:** the widened window is the more accurate
input and **stays**. The keeper's committed numbers are simply **stale at HEAD**, by ~0.03 % of
mean price and ~0.00004 % of energy. Every ISO's keeper needs a HEAD re-solve for this reason
alone — which, for MISO, this session has now done. Recommended for the charter's task-3 wording:
replace "max |class-hour delta| = 0.000000 MW" with a **capacity** identity (added rows carry
0.000000 MW of effective capacity and `min_gen`, and every shared row is byte-identical) plus a
**bounded** dispatch tolerance, because an exact-zero dispatch identity is not achievable across a
fleet-row-count change and never was.

**A governance observation, reported not acted on** (ERCOT's lane's change, out of scope):
`_PARTIAL_EXIT_WINDOW_START` is a bare module constant — no `ScenarioConfig` field, and
`data/fleet/eia860.py` is not one of the seven `solve_surface.py` `SURFACE_MODULES` — so a
fleet-composition change of this class **moves no cache key** in any ISO that arms
`partial_plant_exit_carry`. Rule 24 `[R-REGISTRY]` is about exactly this channel.

---

## 5. CRITERIA AT FULL MAGNITUDE

*(filled from the scored full-span bundle — §5 table below.)*

<!-- CRITERIA_TABLE -->

---

## 6. THE SUCCESSOR — recommended with evidence, NOT built (PROMPT item 2)

The handoff scopes the EIA-923 Schedule-5 daily blend **out** ("that is a new mechanism … do not
build it") and asks for a recommendation with evidence. Here it is.

**RECOMMENDED.** The handoff's own §3 states MISO's Feb-2021 defect is *"NOT fixable from this
source and NOT solvable by you"* because EIA prints no `N3045LA3` month in 2019-2021. **That is
right about N3045 and wrong about the quantity.** The corroborator's second instrument —
**EIA-923 Schedule-5 quantity-weighted plant receipts** — measures the same delivered gas price,
is already on disk (`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`, 68,919 rows)
and is **already read on every MISO solve** by the print path that makes this session's arm inert.

**Month coverage, every MISO footprint state, independently re-derived here:**

| year | AR | IA | IL | IN | KY | **LA** | MI | MN | MO | MS | MT | ND | SD | TX | WI | footprint coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019-2025, each year | 12 | 12 | 12 | 12 | 12 | **12** | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | **1.000** |

against N3045's 0.30-0.34 in 2019-2021 and 0.40 in 2025. Blended on the **same** MISO
gas-capacity weights the seam already uses (zero new parameters):

| year | annual $/MMBtu | monthly cv | Jan | **Feb** |
|---|---|---|---|---|
| 2019 | 2.7268 | 0.1433 | 3.5929 | 3.1263 |
| 2020 | 2.2847 | 0.1374 | 2.2913 | 2.1414 |
| **2021** | **4.9897** | **0.5709** | 2.9975 | **13.9023** |
| 2022 | 6.5996 | 0.1698 | 5.2115 | 5.3837 |
| 2023 | 3.1582 | 0.1543 | 4.4694 | 3.8112 |
| 2024 | 2.6107 | 0.2264 | 4.2094 | 2.5773 |
| 2025 | 3.7753 | 0.1525 | 4.8437 | 4.6031 |

**It prices Uri**: MISO Feb-2021 = **13.9023 $/MMBtu** against the model's 4.42 — a 9.48 $/MMBtu
gap, ~71 $/MWh at a 7.5 MMBtu/MWh CC heat rate. This table reproduces `FINDING-miso249` §7 **to
four decimals on all seven years** from an independent implementation.

**Prior art to build it on:** ercot-261's corroborated monthly gas LEVEL
(`data/raw/ercot_gas_corroborator_monthly.csv`,
`scripts/data/derive_ercot_gas_corroborator.py`, `src/market_sim/data/fuel/basis/ercot.py`) — the
same second instrument, same estimator, ISO-scoped.

**Three conditions, without which the recommendation is dishonest:**

1. **It must be DAILY, never monthly.** A monthly form reproduces `RESULT-ercot254` §3b exactly:
   13.90 $/MMBtu applied flat to all 672 February-2021 hours when the real spike lasted ~5 days,
   which is precisely the within-month smearing that broke C3c there (234 → 688 h vs 258 actual).
   Note that ercot-261's corroborator is an **admissibility filter** — it needs a printed month to
   test — so it solves "the print is not a price", not "there is no print"; it is the wrong tool
   for the coverage hole and the right prior art for the construction.
2. **MISO cannot score the year it would fix.** MISO holds no `complete` marker, so 2021 is
   refused at the launch gate, the registration gate and `audit_keepers`.
3. **There is little for it to do in 2023-2025.** §2 measures the paid price as 100 % F923
   print-derived already; the value is entirely in 2019-2022.

---

## 7. What this session did NOT do, deliberately

- **No `--holdout-authorized`, no out-of-training year, no marker file touched.** MISO holds no
  `complete` marker. Only 2023, 2024 and 2025 were solved.
- **No national `N3045US3` backfill** to reach MISO's Louisiana hole — it would put a national
  number back into exactly the state-months where the local price departs most from national.
- **No EIA-923 Schedule-5 mechanism built** (§6 — recommended, out of scope).
- **No re-litigation of the plant-356 "COD defect"** (ADDENDUM §A9). It is measured closed, and
  this session independently confirms the mechanism: the 171 injected rows age out per unit, at
  0.000000000 effective MW.
- **No other ISO's shard, keeper, status file or calibration log touched** (rule 25).
- **No sibling session interrupted.** The four live lanes are mid-solve and past the point §4
  would redirect; the finding is left in the repository record, which they pick up on rebase.
