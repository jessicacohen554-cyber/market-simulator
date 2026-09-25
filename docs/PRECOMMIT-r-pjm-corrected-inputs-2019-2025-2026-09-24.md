# PRECOMMIT — R-PJM: re-solve PJM 2019–2025 on corrected backcast inputs (2026-09-24)

Written and pushed **before any solve**. The seven shards pin to this commit's full SHA.

**Charter:** `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.7 (owner
instruction 2026-09-24: every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates, and granular CAMPD outage data). **Precondition met:** F1 (#6572) and F2
(#6569) are merged; this branch is cut from `9210075392a128d14a5efb168ab1f9955a9b6946`.
**Rules:** 1, 13, 14, 16/34(c), 19, 21, 23, 25, 28, 29(b), 31–36.

**Incumbent (control):** `2026-09-23-pjm-h19-dbs-span` (2023–25, CALIBRATED) + folded
`2026-09-23-pjm-h19-dbs-touchpoint` (2020–22, NOT-YET). Bundles
`results/calibration/pjm_h19_dbs_{span,touchpoint}`, every leg solved at `2d57aa20`. The two
bundles' `meta.json` differ only in `years` / `gas_prices` / `shared_inputs` / `timestamp` /
`composed_from` — **one recipe** across all six years.

## 1. Registered year set (rule 34(c) / 35(b)) — written down before anything else

| run | years | bundle |
|---|---|---|
| `2026-09-23-pjm-h19-dbs-span` (keeper) | 2023, 2024, 2025 | `pjm_h19_dbs_span` |
| `2026-09-23-pjm-h19-dbs-touchpoint` (stamped to the keeper) | 2020, 2021, 2022 | `pjm_h19_dbs_touchpoint` |

Union = **2020–2025**. This lane solves **2019–2025** (adds 2019, the charter's target) — the
incoming bundle covers the union, so rule 35(c) is satisfiable.

## 2. The recipe — incumbent + the F1 defaults, made explicit

Everything in the incumbent `meta.json` is replayed unchanged (`scripts/replay_keeper.py`). The ONLY
deltas are the six F1 backcast inputs, passed explicitly with `--set` so the recipe is
self-describing rather than riding a default:

| field | incumbent | this lane | source |
|---|---|---|---|
| `eia860_vintage_tracks_solve_year` | False | **True** | F1 default (backcast) |
| `measured_ct_heat_rates` | True | True | unchanged (now per-year rows) |
| `measured_chp_heat_rates` | True | True | unchanged (now per-vintage) |
| `measured_coal_heat_rates` | False | **True** | F1 default (backcast) |
| `measured_st_heat_rates` | False | **True** | F1 default (backcast) |
| `measured_cc_heat_rates` | False | **True** | F1 default (backcast) |

Plus the F1 data changes that reach every year regardless of flags (year-matched eGRID join into
`vintage_<Y>` / canonical (eGRID 2024) / the retiree parquet; per-year measured-HR artifact rows).

**`offer_curve_by_group` / `offer_curve_overrides` UNCHANGED** — this is an input correction, not a
re-tune (rule 1(c)): `authorized_price_tuning.used` carries the incumbent's value, no multiplier moves,
and no gate result will be answered by moving one.

### Outages (the incumbent's three armed families, unchanged files)

| family | file | sha256 | 2019 coverage |
|---|---|---|---|
| std (≥5 d, merit-guarded) | `campd-unit-outages-PJM.csv` | `312a11b8…3924312` (= incumbent) | ✔ (2018–26) |
| short-coal | `campd-unit-outages-short-PJM.csv` | `a27a8330…f2b543` | ✔ (2018–26) |
| short-gas (merit-guarded) | `campd-unit-outages-shortgas-PJM.csv` | `bcb8448c…3db030` | ✔ **new — F2 extended 2019 (+246)**; 2020–25 byte-identical |

**Unit partial-derate (`unit_partial_outage_windows`): NOT ARMED — screened at zero LP and found
structurally EMPTY at HEAD.** The HEAD deriver (`derive_campd_unit_outages.py --iso PJM --years
2019..2025 --partial-windows`) finds **155 raw plateaus across 246 baseload-coal unit-years** and
emits **0**: every one is removed by the shared revealed-availability filter
(`scripts/lib/outage_detect.filter_revealed_outages`), which drops any span in which the unit *ran*
(cf ≥ `REAL_RUN_CF`) through ≥ 6 high-net-load hours. A partial derate is by definition a unit that is
running, so the full-stop filter (ERCOT-79's fix, correct for full stops) deletes the whole family.
The committed file's 43/24/9 rows (2023–25 only) predate that filter and cannot be reproduced, so
arming it would be a stale, 2023–25-only input. Arming either version is not an input correction;
the fix is a detector change (a partial-appropriate revealed-availability test), which is a mechanism
decision outside this lane. **Reported, not armed** — the cell is recorded with this evidence.

### F2 drift routed to R-PJM — measured, NOT installed

F2 §3 findings 1–2 route the std and short-coal extracts to this lane. The HEAD re-derive (same
deriver, frozen constants, `--years 2018..2026`) moves them:

| file | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| std windows (committed → HEAD) | 1255→1227 | 1118→1129 | 1379→1351 | 1321→1247 | 1372→1282 | 1364→1291 | 1271→1207 |
| std MW-days (M) | 11.00→10.15 | 11.55→10.86 | 11.78→10.75 | 11.84→10.84 | 13.06→11.40 | 11.39→10.09 | 10.60→9.93 |
| short-coal windows | 113→113 | 87→85 | 125→123 | 134→136 | 94→91 | 85→89 | 106→104 |

The std shrink is dominated by the seven ST_GAS plants pjm-d4-2 added to `ST_GAS_PEAKER_PLANTS`
(which `outages.py` does not re-filter at load). Overwriting the committed measured-input files in
place was **refused by this session's permission classifier**, so the re-solve runs on the
**incumbent's committed files**; the install is an owner decision, reported in the RESULT with these
numbers. (2018 raw CAMPD is no longer in the repo, so a re-derive cannot regenerate 2018 rows; no
committed 2018 window ends in 2019, so they reach no backcast year.)

## 3. Phase 0 census (zero LP)

### 3a. EIA-860 vintage and class-table heat rate (F1 census at this HEAD, backcast default)

`docs/handoffs/f1/census.py --iso PJM --posture backcast-default`, re-run in this session —
reproduces F1's table exactly.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| EIA-860 source | vintage_2019 | vintage_2020 | vintage_2021 | vintage_2022 | vintage_2023 | vintage_2024 | canonical 2025ER |
| thermal nameplate at class table (exact) | 0.20 % | 0.19 % | 0.20 % | 0.20 % | 0.21 % | 0.05 % | 0.65 % |
| incumbent's source (canonical 2025ER, eGRID 2023 join; audit §3a heuristic) | 2.5 % every year | | | | | | |
| retiree class-table MW / online | 905 / 18,993 | 871 / 13,920 | 327 / 11,599 | 327 / 10,467 | 320 / 6,316 | 6 / 1,268 | — |
| pre-F1 retiree class-table MW | 13,391 | 8,317 | 6,717 | 5,584 | 1,434 | 309 | — |

Residual class-table plants (no in-window eGRID rate in ANY vintage 2018–2024, F1 census): Dickerson
65284 (coal 519 MW), Joliet 9 874 (gas_st 314), Lebanon 2921 (oil 30.6), FirstEnergy Eastlake 2837
(oil 24), North Wales Diesel 64983 (oil 6), Akron Recycle 54265 (gas_st 4), Shelby 2943 (oil 3),
Saint Francis Hospital 50952 (gas_ct 1.6), Woodridge Greene Valley 54987 (gas_ct 1.5), New Knoxville
7898 (oil 1). (The measured CAMPD overlay then covers any of these it has hours for.)

### 3b. Operable nameplate by fuel (EIA-860 vintage resolved = solve year)

| MW | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| coal | 49,487 | 46,399 | **48,993** | 42,214 | 37,387 | 36,594 | 35,434 |
| gas_cc | 50,100 | 51,316 | 53,779 | 55,937 | 59,061 | 59,039 | 58,819 |
| gas_ct | 26,023 | 25,803 | 26,121 | 25,795 | 26,182 | 26,550 | 26,402 |
| gas_st | 8,815 | 10,361 | 7,920 | 9,357 | 8,762 | 8,753 | 9,493 |

**2021 coal = 48,993 MW** against the charter's ~48.7 GW expectation (pjm-167 measured the incumbent's
canonical+ramp at ~9,986 MW / 39 % below it). The incumbent's 2021 coal fleet is therefore restored by
~10 GW in this re-solve; the charter's question — does coal run to its rail with correct heat rates —
is answered in the RESULT at full magnitude against EIA-923/CEMS, and is a finding about offers, never
a reason to switch the vintage off (rules 1/14).

### 3c. Measured CAMPD heat-rate coverage (F1 artifacts, plants with an `ok` row)

| class | pooled | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| CT | 77 | 61 | 65 | 72 | 62 | 62 | 67 | 69 |
| coal | 45 | 45 | 44 | 42 | 41 | 34 | 31 | 29 |
| ST | 12 | 9 | 10 | 9 | 10 | 10 | 10 | 10 |
| CC | 72 | 61 | 63 | 66 | 68 | 68 | 68 | 69 |

(rows per year include plants with that year's own steady-state hours; others fall to the pooled row,
then eGRID.)

### 3d. Outage windows by family and start year (armed files)

| family | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| std (windows / MW-days M) | 1255 / 11.00 | 1118 / 11.55 | 1379 / 11.78 | 1321 / 11.84 | 1372 / 13.06 | 1364 / 11.39 | 1271 / 10.60 |
| short-coal | 113 | 87 | 125 | 134 | 94 | 85 | 106 |
| short-gas | **246** | 283 | 291 | 409 | 317 | 323 | 236 |
| partial (not armed) | 0 at HEAD | 0 | 0 | 0 | 0 (43 committed) | 0 (24) | 0 (9) |

### 3e. 2019 input availability (zero LP)

The historical 2019 blockers (`docs/calibration-log/pjm.md` B1–B3, 2026-08) re-checked item by item at
this HEAD: EIA-930 demand loads for PJM 2019 (8×8760; the demand-balance screen repairs hours 8031 /
8296); `calibration_reference.json` carries a PJM 2019 block; `PJM_2019_renewable_capacity.csv`
exists; `PJM_SEAM_LADDER_BY_YEAR` carries 2019; `actual_lmp_hourly_PJM.parquet` carries 2019 RT/DA;
CAMPD raw extracts cover 2019; `curate_transfer_interface_limits.py --isos PJM` writes a 2019
partition (87,600 rows, 10 interfaces). A full `run_year(fleet_only=True)` 2019 rebuild reached the
interface-limit and ramp-capability loaders and stopped on clean partitions not yet regenerated in this
container (the full `regenerate_clean.py` pass is slow and was not waited on); **stated, not hidden** —
the 2019 shard is the end-to-end proof, and a 2019 input failure there is a hard stop reported back.
DA virtuals 2019 are fetched by the shard (step 5); a failed fetch is a hard stop. The 2019 benchmark
is built at registration by the same path as every other year. **Stated limit:** the load-weighted C3a
basis (`rt_lw`) for 2019 exists only if the bench build produces it; the RESULT states which basis each
year scored on.

## 4. G-DRIFT `2d57aa20` → this pin (rule 29(b)) — zero LP

`git diff 2d57aa20 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` (26 files), classified by commit:

| commit / hunk | PJM verdict |
|---|---|
| **F1** `59ba7ca9` / `ca208aa9` — `data/egrid.py`, `fleet/eia860.py`, `fleet/campd_bins.py`, `chp.py`, `runner.py`, `scenarios.py` defaults + coercion, `run_calibration*.py` CLI, `heat_rate_years.py`, `results/cache.py`; data: `vintage_2018..2024` + canonical + retiree parquets re-joined, `campd_*_heat_rates_PJM` + CHP artifacts re-derived | **LIVE by design** — the treatment |
| **F2** `4efebee0` `campd.ISO_MERIT_PANEL_STATES` (SPP/SOCO pins); data: `shortgas-PJM` +246 rows in 2019 | pins INERT (SPP/SOCO scope, deriver-only). shortgas file **LIVE for 2019 only**, 2020–25 byte-identical |
| Y-28 `bb749a94` cache-key registration; Y-29 `9c99bd47` gate re-key; Y-30 import-cycle / ruff | INERT: keying / governance / no-semantic |
| `6831b110` storage comparison payload | INERT: report-only |
| pjm-h22 `da9fc148` RGGI tables (`capacity_market.py`, `fuel_trajectories.py`) | INERT: read only under `pjm_rggi_allowance_pricing` (off in this recipe) |
| soco-61 `4263d602` `campd_dark_unit_year_windows` (`outages.py`, `arrays.py`, `resolved_inputs.py`) | INERT: default off, needs `campd_per_unit_attribution` (false) |
| miso-268 `79aa52c5` `coal_fuel_inventory_plant_grain` (`lp/rows.py`, `lp/model.py`, `spec.py`, `coal_fuel_inventory.py`) | INERT: default off, MISO-gated |
| soco60b `f560408f` SOCO BA recode / `benchmark_semantics` SOCO fold | INERT: SOCO-keyed |

The only LIVE hunks are the F1/F2 inputs this lane exists to apply. Form 4 holds: **the committed
incumbent bundles are the control**; no control solve is spent. The arm registers with
`--rebuild-benchmark`; the incumbent is re-scored on the same rebuilt benchmark for 2020–25.

## 5. Gates and predictions — declared before any solve

Decided on structure (rule 1). A failed gate does not kill the arm; a passed gate does not promote it.

- **G1 liveness (shard hard stop).** The written `run_config.json` shows
  `eia860_vintage_tracks_solve_year: true` and all five `measured_*_heat_rates: true`;
  `resolved_inputs.campd_unit_outages.sha256 = 312a11b8…`; the solve log names the year's
  `vintage_<Y>` (2019–2024) / canonical (2025) EIA-860 source.
- **G2 directional predictions.**
  - 2019–2022 coal capacity rises (vintage restores retired coal, e.g. 2021 +~10 GW vs incumbent);
    COAL_BIT energy rises in 2020–22, where the incumbent already over-runs (+25.5 / +19.2 TWh
    2020/21 per pjm-h22 §5) — so **C1 coal 2020–22 is expected to WORSEN**. That is the pjm-168
    finding re-measured on correct heat rates: an offers question, reported, not repaired here.
  - The measured coal/ST/CC overlay changes individual plants' positions in the stack; its net sign
    on coal energy is not predicted (no zero-LP offer-array delta was computed for it).
  - 2023–25: fleet source changes only via vintage_2023/2024 vs canonical (small) and the measured
    coal/ST/CC overlay; expect |Δ class TWh| ≤ ~5 and C3a within a few points of the incumbent.
  - Determination: span 2023–25 may lose CALIBRATED (C1 coal or C3a); 2019–22 expected NOT-YET.
- **G3 no silent breakage:** full rubric C1–C8, every year, vs the control on the same benchmark;
  D-1/D-2/D-4 once on the composite.

## 6. DOF (rule 21)

Zero new free parameters. The six flags are measured-input switches (identification: EIA-860 / eGRID /
CAMPD). The offer-curve multiplier block is carried unchanged from the incumbent with its existing
ledger entry.

## 7. Shards (rules 32 / 34 / 36)

Seven, **one per year 2019…2025**, each its own container, pinned to this commit's full SHA. Out-dir
`results/calibration/rpjm_inputs_<y>`, branch `claude/rpjm-inputs-<y>`. Control for `--years <y>`:
`pjm_h19_dbs_touchpoint` for 2019–2022, `pjm_h19_dbs_span` for 2023–2025 (identical recipe).
Command:

```
.venv/bin/python scripts/replay_keeper.py results/calibration/<control> --years <y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_ct_heat_rates=true \
  --set measured_coal_heat_rates=true --set measured_st_heat_rates=true \
  --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --out-dir results/calibration/rpjm_inputs_<y> --note "R-PJM corrected inputs, <y>"
```

**Retrievability (rule 34(e)):** every shard pushes its full bundle incl. `dispatch/<y>_P1.parquet`
to its own branch; the parent fetches, composes one 2019–2025 bundle and lands it on `main` before this
lane's PR merges. Shard SHAs are provenance only.

## 8. Lane note — pjm-h22 (RGGI Card E, PR #6573)

pjm-h22 is solving `pjm_rggi_allowance_pricing = true` on the SAME incumbent, on its own pinned SHA
(`d58121c3`). No file collision (its PR carries only its own shard bundle). If pjm-h22 is promoted
before this lane composes, the two are **orthogonal deltas on the same base**: this lane's result
answers "the incumbent on corrected inputs", and a promoted RGGI keeper would need the same six flags
applied on top (a one-flag re-solve of this recipe, or of theirs). Recorded in the RESULT either way.
