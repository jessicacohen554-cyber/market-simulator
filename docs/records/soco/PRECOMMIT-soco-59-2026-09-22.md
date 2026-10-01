# PRECOMMIT — SOCO-59 (2026-09-22): the "Scherer is priced as bituminous" lead is a name swap; the 2025 hydro hole is real, and SOCO's EIA-930 hydro folds pumped-storage discharge

**Lane** SOCO-59 · **DATA PROFILE** soco · **Model** Opus (rule 27 — scope writes `src/` and `scripts/`).
**Control of record** `2026-09-22-soco58-warm-committed` (`results/calibration/soco58_warm_committed`),
rule 29 `[R-SCREEN]` (b) **form 4** — no control solve.
**Written and pushed BEFORE any LP is solved.**

---

## 0. HEADLINE, EX ANTE

1. **The object — 2024 `CC_REGULAR`, +10.42 TWh / +4.03 pp — IS NOT REACHED BY THIS LANE.** Both named
   candidates were measured at zero LP. Candidate (1) does not exist (§1). Candidate (2) is real but is
   2025-only by construction (§2). Candidate (3) still has no admissible input in this repo. **No lever
   in reach can close the −2.95 TWh the row needs, and this lane does not pretend otherwise.**
2. **The arm is taken on rule 14 `[R-ACCURATE]` alone, and it buys NO gate** — every 2025 C1 row is
   SKIPPED on the preliminary EIA-923 vintage. *If the only argument for this arm were that a 2025 row
   improves, it would not be taken; no scored row is expected to change status.*

---

## 1. CANDIDATE (1) — CLOSED: THE LEAD RESTS ON A PLANT-NAME SWAP IN FINDING-soco-58's TABLES

`FINDING-soco-58` §1/§4.4/§7 label **plant 703 "Scherer"** and **plant 6257 "Bowen"**. Every primary
source says the opposite (`scripts/probes/_soco59_phase0.py coal`):

| id | EIA-923 Sch.5 `Plant Name` | CAMPD `facilityName` | model tranche `name` | coal received 2019–2024 | 2024 delivered |
|---|---|---|---|---|---|
| **703** | **Bowen** | Bowen | Bowen | **100 % BIT** (IL / IN / PA / KY, rail) | **$5.084/MMBtu** |
| **6257** | **Scherer** | Scherer | Scherer | **100 % SUB** (WY, rail) | **$3.119/MMBtu** |
| 26 | E C Gaston | E C Gaston | — | 100 % BIT (AL / KY, rail) | $6.529 |

- **Scherer (6257) IS the PRB plant, is classed `COAL_PRB`, and is priced at $3.12** — matching the
  model's $3.117. **Bowen (703) burns bituminous**, is classed `COAL_BIT`, and is priced at $5.08 against
  the model's $5.099. Gaston's $6.53 matches the model's $6.547.
- 703's rank has been 100 % BIT in every year 2019–2024; its delivered cost rose $2.86 → $5.08 with the
  2022 Illinois-Basin/App price spike, not with a reclassification.
- **Class and price are correct at all six plants to ≤ $0.02/MMBtu. There is no rule-14 repair.**
  The published SOCO-58 tables carry the swap; the FINDING doc is a historical record and is corrected
  by reference in SOCO-59's FINDING, not rewritten.

## 2. CANDIDATE (2) — THE 2025 HYDRO HOLE, AND WHAT PHASE 0 FOUND UNDERNEATH IT

### 2.1 The hole

The keeper's 2025 hydro budget is **0.3275 TWh over 5 plants** (the preliminary EIA-923 vintage),
against **5.926 TWh** measured by EIA-930 (spike-repaired loader) — SOCO's 42-plant, 3,314 MW fleet
simply did not report yet. The registered instruments are the NEISO / MISO keeper construction:
`hydro_backfill_year=2024` (per-plant coverage) + `hydro_eia930_monthly=True` (2025's OWN measured
monthly level and shape).

### 2.2 The admissibility question — SOCO's pre-split EIA-930 hydro FOLDS PUMPED-STORAGE DISCHARGE

`hydro_eia930_monthly` would pin EVERY year. EIA publishes SOCO's hydro as the combined
**"Hydropower and Pumped Storage"** column until the 2024-07-15 taxonomy cut-over, and SOCO's `NG: PS`
filing is continuous only from 2025-01-06 (soco-data-audit §3.3). That audit left SOCO off the fold
registries because the pre-split column never goes negative — **which excludes folded PUMPING only**.
NEISO's fold (neiso-72) was discharge-only too. Measured on SOCO's own data (`_soco59_phase0.py pssplit`):

| test (neiso-72 numbering) | pre-split column 2021 / 2022 / 2023 | 2025 clean hydro | 2025 hydro + PS discharge |
|---|---|---|---|
| (i) hours above SOCO's 3,317.6 MW conventional nameplate | **6 / 29 / 6** (max 3,873 MW) | **0** | 3 |
| (ii) diurnal swing, hourly-mean max/min | **2.84 / 3.12 / 3.82×** | 2.13× | **3.77×** |
| (iii) level vs the 42-plant EIA-923 HY census | 2023: 8.446 vs 6.815 = **+1.63 TWh** | — | PS gross discharge **1.963 TWh** |

**The pre-split column is conventional hydro PLUS pumped-storage discharge.** SOCO's PS is endogenous
storage (1,306.6 MW), so pinning a pre-split year would double-count its discharge.

### 2.3 The construction — the neiso-72 design D, registered for SOCO

`EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] = 2025` (`constants.py`, cited). 2023 and 2024 then **refuse**
the pin and stay on EIA-923 HY; 2025 pins to its own clean series. Measured (`_soco59_phase0.py hydro`):

| year | control budget | **arm budget** | units | unit-grain identical? |
|---|---|---|---|---|
| 2023 | 6.8150 TWh | **6.8150** | 42 → 42 | **yes, byte-identical** |
| 2024 | 6.3015 | **6.3015** | 42 → 42 | **yes, byte-identical** |
| 2025 | 0.3275 | **5.9258** | 5 → 42 | no — the repair |

**Rule 19 `[R-ONE-MECH]`, keyed by `unit_id`** (`_soco59_rule19.py`, `fleet_only` rebuilds): 2023 and 2024
— same 327 units, `fuel_prices` / `mc_base` / `pmax` / `availability` / `heat_rate` **exactly
0.000000000000, 0 keys moved**. 2025 — **37 units added, all `hydro`**, 0 removed, **0 of 290 shared keys
moved on any grain**. It is an energy-budget input and touches no thermal offer.

**All-grains-zero in 2023/2024 is the REQUIRED signature (the SOCO-58 §3 case), not an inert arm.**
What separates an armed 2023 leg from a control is (a) `meta.json` `hydro_backfill_year=2024` /
`hydro_eia930_monthly=true` and (b) the leg's recorded solve surface carrying SOCO's new registry row —
**184 rows against the keeper's 183**. `scripts/probes/soco59_compose_span.py` asserts both, verified
to accept a control offered as control and refuse it offered as arm.

**Rules 21 / 24 / 25.** Zero free parameters; zero new `ScenarioConfig` fields; the registry row is
SOCO's own measurement and no other ISO's row moves. **SOCO's cache key does not move** (the row has no
frozen declaration, so `moved_rows` leaves it out — measured: backcast `601ee1d28826efa1`, default
`7244772ac3674160`, identical on `main` and here).

**The forward half, stated.** The same registry line moves SOCO's FORECAST hydro climatology off the
PS-folded EIA-930 window onto the EIA-923 HY basis: **7.089 → 7.571 TWh/yr**. It is the same rule-14
repair (a folded window contaminates the climatology exactly as it contaminates the pin) and it
un-arms itself once the window holds only split years. **No SOCO forecast result exists on disk or in
the repo**, so the absent key move can stale-serve nothing today; it is recorded as a limitation of
the D79 fingerprint for a first-time per-ISO row, not fixed here.

## 3. CHECK A — THE DISTANCE, AND WHY IT CANNOT REACH THE OBJECT

The arm moves **zero** energy in 2024. The row needs −2.95 TWh. **This lane cannot cross it — said ex
ante.**

What the 2025 water displaces, greedy re-stack under the two allocations that bracket where an LP puts
energy-limited water (`_soco59_phase0.py restack --alloc peak|flat`; dearest above-floor MW first,
floors from the committed sidecar):

| class | `peak` (top-price hours) | `flat` (even) |
|---|---|---|
| CT_PEAKER | −3.163 | −1.462 |
| CC_REGULAR | −0.663 | −2.806 |
| ST_GAS | −0.894 | −0.339 |
| COAL (PRB+BIT) | **−0.853** | **−0.976** |
| other | −0.024 | −0.014 |
| **added water** | **5.598** | **5.598** |

**A CORRECTION TO THE INHERITED CLAIM.** SOCO-58 §2(3)/§7 said correcting hydro "would push 2025 coal
DOWN by up to ~5.7 TWh." That is the arithmetic ceiling, not the merit order: SOCO's coal is
inframarginal in most hours, so the water displaces CT_PEAKER and CC first and **coal falls only
~0.85–0.98 TWh** under either allocation. The 2025 coal overshoot SOCO-58 left (+4.65 PRB / +2.47 BIT)
is **mostly NOT a hydro artifact**, and this lane will not absorb it.

## 4. CHECK D — EVERY SCORED ROW THE ARM CAN TOUCH

Only 2025 rows can move, and in 2025 only **C4** and **C8** are scored (C1/C2 2025 are SKIPPED).
Every 2023/2024 row — including the thin 2023 `ST_GAS` (0.13 pp) — is byte-identical by §2.3.

| row | keeper | margin | projection |
|---|---|---|---|
| C4 2025 coal | r 0.883 / NRMSE 0.206 (reproduced here at 0.883 / 0.205) | 0.094 | NRMSE 0.195–0.205, r 0.871–0.882 |
| C4 2025 gas | r 0.949 / NRMSE 0.083 | 0.117 | gas family −4.6…−4.7 TWh (≈ −3.6 % level) |
| C8 2025 ST_GAS | forced 0.680 / 3.728 = 0.182 | 0.118 | 0.20–0.24; crossing 0.30 needs ST_GAS −1.46 TWh above floor, **1.6× the greedy's worst case** |
| C8 2025 hydro | 0.000, immaterial | — | 0.000 (every hydro unit has `pmin 0`), becomes material |

**Check E (allocation, 2025 coal, EIA-923 per-plant basis):** Σ|model−actual| **8.157 → 7.567–7.795
TWh**, the largest cut at **Scherer (6257)** — run 2.205 TWh over its own actual, trimmed −0.52…−0.57.
Miller (6002) and Gaston (26) do not move.

## 5. PREDICTIONS — EX ANTE, BANDED SYMMETRICALLY (±2× both ways on the greedy, per SOCO-58 §5)

| # | prediction | falsifier |
|---|---|---|
| **P1** | 2023 and 2024 legs: `class_hourly`, `system`, `class_band_hourly`, `storage` **byte-identical** to the keeper's committed sidecars | any byte differs AND any class moves ≥ 0.001 TWh |
| **P2** | 2025 hydro 0.327 → **5.90–5.93 TWh** | outside |
| **P3** | 2025 non-hydro supply (thermal + storage net + dump) falls by **5.2–5.9 TWh** | outside |
| **P4** | 2025 class Δ: CT_PEAKER −0.73…−6.33; CC_REGULAR −0.33…−5.61; COAL_PRB+COAL_BIT −0.43…−1.95; ST_GAS −0.17…−1.79. **Direction of the CT-vs-CC split is NOT predicted** (re-commitment; the two allocations disagree) | any class outside its band, or any of the four moves UP |
| **P5** | 2025 Scherer (6257) −0.26…−1.15 TWh, the largest coal-plant cut; Miller (6002) \|Δ\| < 0.5 | outside |
| **P6** | C4 2025 coal NRMSE **0.185–0.215**, r **0.86–0.90**, PASS | outside, or FAIL |
| **P7** | C4 2025 gas r ≥ 0.90, NRMSE 0.07–0.13, PASS | outside, or FAIL |
| **P8** | C8 2025 ST_GAS forced share **0.18–0.26**, PASS (~10 % chance of crossing 0.30) | outside |
| **P9** | C8 2025 hydro forced share 0.000 | > 0 |
| **P10** | determination `NOT-YET`; C1 13/14 · free 9/10; **2024 CC_REGULAR unchanged at +10.42 / +4.03**; `grade_summary` 5 / 4 / 1 | any status change |
| **P11** | 2025 coal allocation Σ\|m−a\| 8.157 → **7.2–8.1** | outside |
| **P12** | DOF 7 entries / 1 residual, `n_scalars 0` | any change |
| **P13** | no peer ISO key moves (`solve_surface_register --diff`: SOCO 1, all others 0) | any other ISO |

## 6. RULE 1 / RULE 14 — WHY IT IS TAKEN WHATEVER THE RESIDUAL DOES

The input is wrong by 5.6 TWh — **94.5 % of the year's water missing** — because a preliminary survey
had not yet collected 37 plants, and the correction is the year's own measured series from a column
shown clean by the same three tests that justified NEISO's registration. The admissibility guard is
not optional: without it the same flag would inject ~1.6 TWh of pumped-storage discharge into 2023.
Rule 13's forward story holds unchanged — the forecast path uses `hydro_forecast_budget`, never the
930 pin (the two are mutually exclusive in `build_hydro_fleet`).

## 7. THE SOLVE — THREE SHARDS, ONE YEAR EACH (rule 36 (a)), parent LP cost ZERO

Pinned to this PRECOMMIT's commit SHA. Each shard recovers its CONTROL leg at zero LP and replays it:

```
git fetch origin <leg sha> && git checkout <leg sha> -- results/calibration/soco58_arm_<Y>/
python3 scripts/replay_keeper.py results/calibration/soco58_arm_<Y> --years <Y> \
  --out-dir results/calibration/soco59_arm_<Y> \
  --set hydro_backfill_year=2024 --set hydro_eia930_monthly=true \
  --note "SOCO-59 ARM <Y>: hydro_backfill_year=2024 + hydro_eia930_monthly=true with EIA930_PS_SPLIT_COMPLETE_FROM[SOCO]=2025 (2025 hydro 0.33 -> 5.93 TWh on its own clean EIA-930 series; 2023/2024 refuse the PS-folded pin), year-isolated (rule 36)"
```

Control leg SHAs (SOCO-58 §8): 2023 `6ad08eed8ea3289ad76301831a90b35cb81a4f9a`, 2024
`605be037f0caf0bd71a22ffe57bcdbc6182e7e46`, 2025 `74a1802e6492b34f13818e3a63decabdb0a423fe`.
Hard stops: pinned SHA · dependency asserts · **post-solve** config signature (six inherited postures
resolved, `coal_prb_sigmoid_overrides` null, `meta.json` hydro keys, `solve_surface.rows == 184`) ·
foreground solve · `--note`. The parent repairs `_shared/SOCO/` with `--rebuild-benchmark` after
composition.

## 8. WHAT THIS LANE DOES NOT TOUCH

1. **2024 `CC_REGULAR`** — no admissible lever. The over-dispatched CC tail (Tenaska Lindsay Hill,
   Central Alabama, Ratcliffe, E B Harris) still has no input in this repo.
2. **The 2025 coal overshoot** — §3 shows it is mostly not hydro. Barry (3) at 6.2× its own 2025 actual
   is the largest per-plant piece (SOCO-56 §3 fleet row, untouched).
3. **NEW — SOCO's C1 BENCHMARK hydro row for 2023 / 2024 reads the PS-folded EIA-930 column** (8.447 /
   7.080 TWh against the model's 6.815 / 6.301 EIA-923 HY). Unscored today (hydro is not a free C1
   class), so it moves no gate; it is a benchmark-side rule-14 defect routed, not fixed.
4. The governance boundary on `tranche_startup_amortization` (SOCO-58 §6) — not ruled on, not re-litigated.

---

## ADDENDUM A — written after the shards launched, BEFORE any leg was fetched or read

**§8 item 3 is WITHDRAWN as stale.** The benchmark reads the same registry
(`run_calibration_full.py::_hydro_benchmark_is_923_only`, gov-hydro-seam-1), so this lane checked
whether registering SOCO moves SOCO's benchmark — which could shift every C1 **share** leg, the
0.13 pp 2023 `ST_GAS` margin included. Measured with `build_benchmark_frames` on the keeper bundle,
registry row ON vs popped: **`eia923`, `eia930` and `campd` frames are all BYTE-IDENTICAL.** SOCO's
benchmark hydro at HEAD is already the EIA-923 HY census — **6.815 / 6.301 TWh** in 2023 / 2024
(44 rows each) and the EIA-930 swap **6.012** in 2025 (1 row) — not the folded 8.447 / 7.080 that
SOCO-31/40's tables quote from an older benchmark. There is no benchmark-side defect to route, and
the registration moves no scored denominator.

**P14 (added).** `--rebuild-benchmark` on the composite produces an `eia923` frame identical to the
keeper's; 2025 benchmark hydro stays 6.012, so the arm's 2025 hydro lands ~0.09 TWh under it
(5.926 modelled; unscored).

---

## ADDENDUM B — POST-HOC, written AFTER the legs landed and the run was registered. It CORRECTS Addendum A.

**Addendum A is WRONG and is kept, not deleted, so the error is on the record.** Its A/B built the
benchmark twice in ONE process, popping the SOCO row between calls. `_hydro_benchmark_is_923_only`
is `@lru_cache`d (`run_calibration_full.py:2908`), so the second call returned the first call's
answer — the A/B compared a cached result to itself. Found at registration, when the rebuilt bench
parts differed from the keeper's committed ones in exactly one leaf per year. Re-run in a **fresh
process** with the row removed before the first call:

| year | benchmark `classFull/hydro`, row absent (keeper's committed part) | **row present (HEAD)** |
|---|---|---|
| 2023 | 8.4465 TWh (EIA-930 swap, PS-folded) | **6.815** (EIA-923 HY census) |
| 2024 | 7.0798 | **6.3014** |
| 2025 | 6.0123 | 6.0123 (unchanged — 2025 is a clean year) |

**The registration therefore repairs BOTH ends of the same comparison** — the LP's hydro input and the
benchmark's hydro actual — exactly as gov-hydro-seam-1 designed the one registry to do. This is the
correct direction under rule 14 (the folded figure counted pumped-storage discharge the model carries
as storage), but it was NOT predicted, and it moves scored denominators.

**Decomposition, measured by scoring each run against each bench part:**

| row | keeper, old bench | **arm, old bench** (dispatch effect) | arm, new bench (+ benchmark effect) |
|---|---|---|---|
| 2023 `ST_GAS` share | −2.87 pp | **−2.87** | **−2.90** (margin 0.13 → 0.10 pp) |
| 2023 volume band | ±7.18 TWh | ±7.18 | ±7.13 (ST_GAS margin 0.32 → 0.27) |
| 2023 `CC_REGULAR` share | +2.28 | +2.28 | +1.97 |
| **2024 `CC_REGULAR`** | **+10.42 TWh / +3.97 pp** | **+10.42 / +3.97** | **+10.42 / +3.84** (volume margin −2.95 → −2.98) |
| 2024 `ST_GAS` share | −2.56 | −2.56 | −2.57 |

**The arm's dispatch moves no scored C1 row (all 14 identical to 0.01 pp).** Every movement in the last
column is the benchmark repair, it changes no status, and — because the bench part is shared per
ISO-year — it applies to any SOCO run displayed after this lands, the current keeper included.

**Prediction scoring affected:** P14 is **FALSIFIED** (the `eia923` frame is not identical to the
keeper's). P10 is **PARTIAL** (every status, the determination and `grade_summary` hold; the 2024
`CC_REGULAR` share leg moves +3.97 → +3.84 pp on the benchmark side, not unchanged as predicted).
