# PRECOMMIT — SPP-42: the commitment-feasibility clip (card R-be, open half)

**Lane** SPP-42 · **Date** 2026-09-14 · **Base** `d54cd9c571359b85cb1a8e1cd5cab68c080a6b0c`
**Keeper (control)** 11 = `2026-09-13-spp-38-vintage-cache`, bundle `results/calibration/spp38_span`,
`git_sha` `760012f7`.
**Arm** exactly one new `ScenarioConfig` gate: `mustrun_commitment_feasibility_clip = True`.

This document is written **before any LP is spent**. Every number in §1–§3 is zero-LP.

---

## 1. The object, re-diagnosed rather than inherited

Keeper 11's **D-4 off-window binding FAILS**: 10 rows over 71 in the committed
`legitimacy_diagnostics.json`, every one `st_gas_mustrun_per_plant × ST_GAS`, on plants
1230 / 1235 / 1271 / 3008. The class-level *window* leg PASSES (`offwindow_share` 0.0000 —
the declared window is `h0-23`, so it is vacuous); the failures are all the **per-unit
conduct rider**, whose test is `median measured output over the plant's own binding hours
≤ 0`.

### 1a. What selects the floor's hours today — established exactly, not inferred

`data/fleet/arrays.py::_compose_min_gen_floors`, the `cc_mustrun_any` block:

- **Level** = `cc_mustrun_pmin_mw`, the committed tranche's own capacity
  (`committed_pct × nameplate`, the tranche artifact's **P5-of-online** loading).
- **Count** `k = round(online_frac × 8760)`, `online_frac` **pooled over the derive
  window** from `data/raw/_processed-legacy/thermal_tranches_SPP.csv`.
- **Selection** — keeper 11 arms `mustrun_window_commitment_grain`, so the window is the
  top `round(k/24)` **whole operating days ranked by day-mean SYSTEM LOAD**
  (`_commitment_day_order` → `_mustrun_window_hours`). **The ranking is identical for
  every plant.** The plant's own record enters ONLY through the count and the level.
- **Clip** — the global `np.minimum(min_gen, pmax × availability)` at the end of the
  composer.

**Verified on the rebuilt arrays** (`run_year(..., fleet_only=True)` through the sanctioned
`replay_keeper.run_year_kwargs` + `derived_run_year_inputs` path): the placed day set is a
**subset of the top-N day-mean-load days for all 21 floored plants**, N matching
`round(online_frac × 8760 / 24)` exactly; shortfalls are the availability clip.

### 1b. The phase-0 confusion matrix (2023, floored hours vs the plant's own CAMPD hourly)

Same measured series the D-4 rider reads (`frontend/data/backcast/bench/SPP/2023.json.gz`,
plant-level view). `F` = floored, `U` = unfloored, `on` = meter > 0.

| plant | ct_only | flr_h | on_h | F&on | F&off | U&on | U&off | precision | day prec | within-day prec | median over floored |
|------:|:-------:|------:|-----:|-----:|------:|-----:|------:|----------:|---------:|----------------:|--------------------:|
| **1230** | False | 1440 | 839 | 595 | 845 | 244 | 7076 | **0.413** | **0.483** | 0.855 | **0.0** |
| 1233 | False | 1176 | 1654 | 1166 | 10 | 488 | 7096 | 0.991 | 1.000 | 0.992 | 44.7 |
| **1235** | False | 1200 | 1033 | 544 | 656 | 489 | 7071 | **0.453** | **0.500** | 0.907 | **0.0** |
| **1271** | False | 912 | 665 | 386 | 526 | 279 | 7569 | **0.423** | **0.500** | 0.847 | **0.0** |
| 1416 | False | 2880 | 8079 | 2880 | 0 | 5199 | 681 | 1.000 | 1.000 | 1.000 | 337.9 |
| 1417 | False | 1896 | 2390 | 1645 | 251 | 745 | 6119 | 0.868 | 0.911 | 0.952 | 50.2 |
| 2226 | False | 240 | 942 | 240 | 0 | 702 | 7818 | 1.000 | 1.000 | 1.000 | 24.0 |
| 2446 | **True** | 6672 | 7631 | 6402 | 270 | 1229 | 859 | 0.960 | 0.975 | 0.984 | 59.5 |
| 2951 | **True** | 3984 | 4837 | 2935 | 1049 | 1902 | 2874 | 0.737 | 0.837 | 0.880 | 92.4 |
| 2952 | False | 2904 | 4457 | 2676 | 228 | 1781 | 4075 | 0.921 | 0.959 | 0.961 | 435.5 |
| 2956 | False | 3576 | 5318 | 3479 | 97 | 1839 | 3345 | 0.973 | 0.980 | 0.993 | 441.9 |
| 2964 | False | 6216 | 7915 | 5982 | 234 | 1933 | 611 | 0.962 | 0.985 | 0.978 | 91.8 |
| 2965 | False | 3480 | 5271 | 3040 | 440 | 2231 | 3049 | 0.874 | 0.903 | 0.967 | 31.3 |
| **3008** | False | 2424 | 2107 | 1183 | 1241 | 924 | 5412 | **0.488** | 0.812 | **0.601** | **0.0** |
| 3476 | False | 2640 | 3773 | 2493 | 147 | 1280 | 4840 | 0.944 | 0.973 | 0.971 | 80.6 |
| 3478 | False | 6720 | 6193 | 4939 | 1781 | 1254 | 786 | 0.735 | 0.761 | 0.966 | 88.2 |
| 3482 | False | 7008 | 7609 | 6522 | 486 | 1087 | 665 | 0.931 | 0.976 | 0.954 | 158.4 |
| 3484 | False | 8184 | 8106 | 7688 | 496 | 418 | 158 | 0.939 | 0.980 | 0.959 | 95.0 |
| 3485 | False | 5640 | 6036 | 4297 | 1343 | 1739 | 1381 | 0.762 | 0.826 | 0.923 | 68.5 |
| 4940 | False | 2616 | 4107 | 2616 | 0 | 1491 | 4653 | 1.000 | 1.000 | 1.000 | 283.6 |
| 7013 | False | 264 | 259 | 174 | 90 | 85 | 8411 | 0.659 | 0.727 | 0.906 | 15.0 |

**The `ct_only` guard is re-verified per plant and it holds**: 1230 / 1235 / 1271 / 3008 all
read `ct_only = False`, i.e. these are plants the benchmark **does** trust. The two plants
the rider skips (2446, 2951) are flagged and are not in the failing set.

**The failures split into two different defects.** 1230 / 1235 / 1271 are a **DAY**-selection
miss (day precision 0.48–0.50, within-day precision 0.85–0.91, and a flat hour-of-day
profile ~0.40 across all 24 hours — no diurnal structure at all). 3008 is a **WITHIN-DAY**
miss (day precision 0.81, within-day 0.60, a clean daytime-cycling profile: 0.22 overnight
→ 0.80 at h11–17 → 0.27 by h23) — the one measured two-shifter SPP-27 already named.

### 1c. THE RE-DIAGNOSIS — the "day-selection" reading is largely wrong

About half of each failing plant's floored hours carry a **dated ≥ 5-day CAMPD full-stop
outage**, and the floor **survives it as a fraction of the plant's own minimum online
level**:

| plant | units | minimum online level (MW) | median floor over its floored-and-metered-off hours | as % of that level |
|------:|------:|--------------------------:|----------------------------------------------------:|-------------------:|
| 1230 | **1** | 21.6 | **1.33** | 6.2 % |
| 1235 | **1** | 24.0 | **4.00** | 16.7 % |
| 1271 | **1** | 17.0 | **1.68** | 9.9 % |
| 3008 | 3 | 41.9 | 16.91 | 40.4 % |

For contrast, the plants that pass sit at 73–92 % of their own level in the same statistic
(2952 319/348.8, 3476 69/75.6, 2446 33/36.4).

**The model already knows these plants are out** — the dated-outage factor inside those
windows reads 0.040 / 0.182 / 0.108 / 0.297. What it does with that knowledge is the defect.
Because a committed tranche's `cc_mustrun_pmin_mw` **is** its own `pmax`, the global clip
reduces to *exactly* `tranche pmax × availability`: the asserted **commitment** inherits the
availability derate **linearly**. A commitment is not linear. A single-unit 50 MW steam
plant cannot be "committed" at 1.33 MW; where available capacity is below the plant's own
minimum online level, **no configuration it has ever operated is feasible**, and
`np.minimum` silently substitutes a smaller, equally infeasible commitment instead of none.

## 2. The arm

`ScenarioConfig.mustrun_commitment_feasibility_clip` (bool, default **False**), registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at that declared default in the same commit as the field
(nyiso-119 discipline). In `_compose_min_gen_floors`, immediately after the global clip and
before `clear_where_unfloored`: the floor is **zeroed** in any hour where the plant-group's
own available capacity (`Σ pmax × availability` over its rows) is below the committed level
it asserts (`Σ cc_mustrun_pmin_mw` over its floored rows). Every other hour keeps the
incumbent clip untouched. Masked on the two per-plant commitment mechanism ids, so no other
floor is reachable.

- **Rule 21 `[R-DOF]`** — **ZERO free parameters and zero new inputs.** No threshold, share,
  multiplier, length, artifact, loader or CLI flag. The test is the plant's own committed
  level against its own available capacity, on the **same basis the incumbent clip already
  uses**.
- **Rule 18 `[R-PHYSICS]`** — eligibility is unit physics (can this plant carry the
  configuration the floor asserts), never a class tuple, plant list or conduct statistic.
  Deliberately **not** `mustrun_plant_exclusions`, which miso-170 warns "would bury that
  error inside a membership list".
- **Rule 13 `[R-MEASURED]`** — **nothing measured enters.** Both operands are arrays the LP
  already holds, so the rule is **forward-native** (not registered in
  `_BACKCAST_ONLY_OVERLAY_FIELDS`) and responds in a forecast year to that year's own
  EFOR/maintenance envelope. It selects no hours from any meter — the shape SPP-46 declared
  inadmissible is not reached.
- **Rule 19 `[R-ONE-MECH]`** — the ONE floor's clip is **replaced** in the infeasible hours;
  nothing is stacked. The committed D-2 attribution confirms `st_gas_mustrun_per_plant` is
  the **sole** mechanism flooring SPP ST_GAS (one row per year: 2.4998 / 2.4402 / 2.1752 TWh).
  Membership, window size, placement and the lay-up mask are four other orthogonal
  properties of the same floor and all stay off.
- **Rule 25 `[R-ISO-SCOPE]`** — default off, so every other ISO's keeper is byte-identical;
  no per-ISO number exists to transfer. Every shard's matrix cell is seeded `U`.
- **Scope** — the committed-tranche seam only. The `st_gas_mustrun_p25_level` swap keeps its
  incumbent clip (its level is the p25-of-online rather than the P5 minimum, and its
  cheapest-first tranche distribution is a different feasibility statement): a declared
  boundary, not an oversight. SPP has that gate off, so the change is complete for SPP.

### 2a. Two sibling routes KILLED at zero LP in the same phase 0

1. **`mustrun_layup_window_mask` (miso-173) alone is a rule-19 DOUBLE-SUBTRACTION on SPP.**
   The gate presumes the merit-order guard has already removed lay-up windows from the
   availability envelope. Measured: keeper 11 runs `campd_outage_merit_order_guard = False`,
   no `campd-unit-outages-perunitmerit-SPP.csv` exists, and **1089 of 1089** rows in
   `campd-unit-outages-layup-SPP.csv` are already present in the
   `campd-unit-outages-SPP.csv` the keeper reads. Availability inside those windows is
   already 0.040 / 0.182 / 0.108 / 0.297 on the four plants, and **zero** lay-up hours are
   left underated. Arming it would subtract the identical measured window twice.
2. **The blunt variant — zero the floor wherever ANY dated outage is present — is wrong.**
   It removes 1.15 TWh fleet-wide and destroys **correct** floors on multi-unit plants
   (2964: 4,326 of its 4,560 zeroed hours are hours the meter says it *was* running).

## 3. The zero-LP prediction, engine-verified

The armed field reproduces the hand computation **row for row** (2023: −0.0009 / −0.0026 /
−0.0009 / −0.0004 TWh on 1230 / 1235 / 1271 / 3008; total −0.1428 TWh; every precision and
median identical). **Rule 19 machine check on the rebuilt arrays: every moved cell carries
mechanism id 16 (`ST_GAS_MUSTRUN_PER_PLANT`) and no other id appears** (6,720 cells, 2023).

Predicted movement of the D-4 rider's own failing statistic (median measured output over the
plant's floored hours), all ten failing plant-years:

| plant | 2023 | 2024 | 2025 |
|------:|-----:|-----:|-----:|
| 1230 | 0.0 → **22.8** | (passes) | 0.0 → **24.8** |
| 1235 | 0.0 → **27.8** | 0.0 → **32.7** | 0.0 → **26.1** |
| 1271 | 0.0 → **18.0** | 0.0 → **17.1** | 0.0 → **17.1** |
| 3008 | 0.0 → **13.8** | 0.0 → **4.6** | 0.0 → **36.7** |

Placed ST_GAS floor falls **0.1428 / 0.1154 / 0.0465 TWh** (3.5 % / 2.8 % / 1.3 % of the
4.07 TWh mechanism).

### 3a. BOUNDED HONESTLY — what this prediction is NOT

The prediction is over **PLACED** hours; the D-4 rider scores **BINDING** hours (dispatch at
the floor). These are different sets — this document's own table shows 1230's 2025 placed
median reading 0.0 where the committed rider reads 24.163 and passes. So the **direction is
established and no 0.000-crossing claim is proven** until a solve and the real scorer say so.
This is the exact bound SPP-39 was caught by, and its withdrawal of an absolute claim built
on a non-reproducing reconstruction is the precedent being respected here.

### 3b. EXPECTATIONS SET AT THE GATE, not discovered afterwards

- **C1 / C3a / C3b will not move materially, and this lane is not sold as if they will.**
  The misallocated energy is ~0.06 TWh/yr against ~300 TWh of SPP load.
- **C1 is expected to get marginally WORSE.** SPP ST_GAS is already under-produced
  (2023 −6.03 TWh, share_pp −2.12) and this arm **removes** floor. If C1 nonetheless flips
  PASS → FAIL, gate G5 kills the arm.
- **One plant degrades and is reported rather than hidden**: 2952 precision 0.921 → 0.908
  (2023) and 0.885 → 0.880 (2024), carrying the largest single energy cost (−0.101 / −0.110
  TWh). It is a 3-unit plant with an unusually high committed fraction (LSL/pmax 0.357), so
  the feasibility test trips more often there than anywhere else.
- **This is a structural-integrity lane.** The deliverable is D-4 rows that bind where their
  own driver says the plant was running, and a C8 floor defensible on the held-out years.
  Per rule 1 `[R-STRUCT]` a structurally-correct mechanism stays in even if the residual does
  not move, and is never rejected because it did not.

## 4. Control: G-DRIFT says form 4 is VOID and a control solve is EARNED

`git diff 760012f7 d54cd9c5 -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
returns **49 changed files, +4,751 / −146**. The audit does not need to classify all 49,
because a **LIVE** hunk sits on the exact path under test:

> `src/market_sim/data/fleet/arrays.py` — the COD-ramp seam moved from
> `effective_cod` / `monthly_online_mask` to `cod_ramp.generator_online_mask` (SOCO-15, card
> S12), and its own comment records the behavioural change: **`min_gen` (the hard must-run
> floor) is now "scaled by the same mask" where it was previously "zeroed in offline
> months"**. That is a change to the must-run floor path, it is not gated on any ISO, and it
> is live for a `mode="backcast"` SPP run.

Rule 29(b): *"A LIVE hunk is the only thing that earns a control solve, and then only for
the years the screen needs."* So **the screen is a same-base A/B**: control (gate off) and
arm (gate on) solved in the **same shard, same construction**, on the screen year only.
Keeper 11's committed numbers are **not** used as the control for this arm.

## 5. Screen year — NAMED BEFORE THE SCREEN RUNS

**2023.** Chosen on the **mechanism's own largest measured footprint** from step 0 — placed
floor released **0.1428 TWh (2023)** against 0.1154 (2024) and 0.0465 (2025) — and
demonstrably **not** the residual year: 2025 carries the largest C3a miss (+5.17 %) and 2024
the largest ST_GAS C1 gap (−7.42 TWh). Rule 29(1).

## 6. Pre-registered STRUCTURAL STOP gates — STOP-ONLY, and NONE reads the target

The target is the D-4 per-unit conduct rider, so **no gate below reads D-4, any per-unit
conduct statistic, or the target residual**. A screen may kill this arm; it may never promote
it (rule 29). All comparisons are **arm vs control at the same base**.

| id | gate | pass condition |
|----|------|----------------|
| **G1** | **FIRING** | The arm logs `mustrun_commitment_feasibility_clip ARMED`, and the ST_GAS placed-floor energy falls by **0.1428 ± 0.005 TWh** — the zero-LP pre-solve prediction. A firing that misses its own arithmetic is a plumbing failure. |
| **G2** | **CONFINEMENT** | Exactly **one** differing `scenario_config` key between the legs; `offer_curve_by_group` byte-identical (whole-mapping `json.dumps(sort_keys=True)` SHA-256 `090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65`); in the committed `legitimacy_diagnostics.json` **no class other than ST_GAS** changes its D-2 forced energy. |
| **G3** | **MAGNITUDE / DIRECTION** | ST_GAS gross generation **falls** (floor was removed), by **no more than 3× the released floor energy (≤ 0.4284 TWh)**. A larger move means the LP responded to something other than the released floor. |
| **G4** | **NO NEW UNSERVED ENERGY** | `slack` and `dump` do **not increase** versus the control leg. (Deliberately *not* "slack == 0.0000": SPP-32 generalised a one-year accident into a gate the designated keeper itself does not meet — keeper 11 carries 370.1017 MWh in 2024. For 2023 both legs are expected at 0.0000; the gate is the *comparison*.) |
| **G5** | **NO NON-TARGET LOAD-BEARING FLIP** | No load-bearing criterion (C1 / C2 / C3a / C3b) flips PASS → FAIL on 2023; C3a stays within ±10 %, C3b within 0.20. |

**A gate is not re-read after its number is seen** (rule 1 `[R-STRUCT]` (c)). If a gate fails
as written, the arm is STOPPED and the defect reported — the SPP-32 precedent.

## 7. If the screen clears

Full span as **two registrable runs**, per rules 16 `[R-ALLYEARS]` / 32(b) `[R-SHARD]` /
34(c) `[R-SHARD-PROMOTABLE]`. SPP's registered year set enumerated from
`frontend/data/backcast/registry/*.json` **before** anything is pruned (rule 35(b)):

- `2026-09-13-spp-38-vintage-cache` → **2023, 2024, 2025** (keeper 11)
- `2026-09-13-spp-40-holdout-span` → **2019, 2020, 2021, 2022** (stamped `holdout.keeper`)

**Seven years, and a promotion re-keys all seven.** So: one shard `--years 2023 2024 2025`
(one bundle) and one shard `--years 2019 2020 2021 2022` (one bundle), each pushing its own
bundle including `dispatch/<year>_P1.parquet` (rule 34(a)). No year is deliberately omitted.
If it promotes: enumerate the year union first, promote, `audit_keepers.py --iso SPP`
(E1/E13), then `prune_iso_runs.py --iso SPP` — **SPP only** (rule 35(a); the two pre-existing
parity-RED bundles `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` are not this lane's
and are not pruned).

## 8. Records

- `scripts/probes/_spp42_floor_hour_selection_phase0.py` — the selection census and confusion matrix.
- `scripts/probes/_spp42_layup_mask_phase0.py` — the lay-up route's control/arm rebuild and its kill.
- `docs/codebase-site/data/mechanism-matrix.js` + all nine ISO shards — row added with the
  field in the same commit (rule 28(c)); SPP seeded `O`, every other ISO `U`.
- `tests/unit/data/test_mustrun_commitment_feasibility_clip.py` — 6 tests: default-off is the
  incumbent linear clip, armed zeroes the infeasible hours, feasible hours byte-identical, a
  partial derate that still carries the level is untouched, no other mechanism reachable, and
  the cache-key registration at the declared default.
