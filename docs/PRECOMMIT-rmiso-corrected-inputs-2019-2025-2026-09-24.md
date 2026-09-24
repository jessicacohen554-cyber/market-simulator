# PRECOMMIT — R-MISO: MISO 2019–2025 re-solved on corrected backcast inputs

```
LANE    : R-MISO (AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24 §5.3.3)
BASE    : main 92100753 (F1 #6572 + F2 #6569 merged — precondition MET)
KEEPER  : 2026-09-24-miso-268-coal-yard (results/calibration/miso268_yard_span, 2020-2025), git_sha bb31b95c
RECIPE  : keeper recipe + F1 backcast defaults + short-gas + unit-partial windows. Offer-curve multipliers UNCHANGED.
CONTROL : the keeper's committed bundle (rule 29(b) form 4). No control solve.
SHARDS  : seven, one per year 2019-2025 (rule 36), pinned to the SHA this document is pushed at.
DATA    : DATA PROFILE: miso
```

This is an **input correction**, not a lever (rule 1(c)): nothing is tuned, no multiplier
moves, and a gate that regresses is reported and root-caused, never re-tuned (rule 14).

## 1. Year set (rules 34(c) / 35(b))

Registered MISO runs at HEAD: one — the keeper, years **{2020, 2021, 2022, 2023, 2024, 2025}**;
nothing is stamped to it. This lane solves **{2019 … 2025}** (adds 2019, the owner's span).

Benchmarks per year, checked on disk:

| year | EIA-930 | EIA-923 gen | MISO hub LMP (DA/RT) | notes |
|---|---|---|---|---|
| 2019 | ✔ | ✔ | **landed this lane** (365/365 days) | see §2.3 |
| 2020–2022 | ✔ | ✔ | ✔ (chunks) | |
| 2023–2025 | ✔ | ✔ | ✔ (gzip) | |

## 2. Phase 0 (zero LP)

Probe: `scripts/probes/_rmiso_phase0_census.py` — `run_year(fleet_only=True)` on the exact
R-MISO recipe (keeper `meta.json` + the year's `config_partition_overrides` + the two arms),
every year.

### 2.1 Resolved posture (all seven years)

`eia860_vintage_tracks_solve_year` **True** → `vintage_<Y>/` for 2019–2024, canonical (eGRID 2024
join) for 2025; `measured_{ct,coal,st,cc,chp}_heat_rates` **all True**; `carry_operating_mothballs`,
`retiree_vintage_status_scope`, `partial_plant_exit_carry` True (keeper); outage family std
(unitroute) + short-coal + **short-gas** + **unit-partial** + maxgen all True;
`miso_measured_reserve_requirements` False 2019–2022 / True 2023–2025 (data-forced partition,
unchanged). `gas_offer_margin_anchor` reproduces the keeper's recorded per-year overlay exactly in
2020–2025 (2.329 / 4.019 / 6.588 / 3.019 / 2.558 / 3.819) and resolves **2.869** for 2019.

### 2.2 Heat rates — thermal MW at a `HEAT_RATE_BINS` class value (recipe fleet, LP arrays)

| year | thermal MW | class-table MW | share | by fuel |
|---|---:|---:|---:|---|
| 2019 | 120,938 | 530 | 0.44 % | oil 406, gas_st 114, coal 10 |
| 2020 | 122,508 | 561 | 0.46 % | oil 417, gas_st 133, coal 10 |
| 2021 | 121,603 | 474 | 0.39 % | oil 419, coal 34, gas_st 21 |
| 2022 | 120,397 | 469 | 0.39 % | oil 414, coal 34, gas_st 21 |
| 2023 | 114,527 | 367 | 0.32 % | oil 367 |
| 2024 | 111,950 | 387 | 0.35 % | oil 387 |
| 2025 | 128,154 | 838 | 0.65 % | oil 674, gas_st 124, coal 40 |

Pre-F1 on the same measure (F1 census, eGRID layer): 2019–2022 vintages **100 %** class-table;
2019 retirees 9,766 → **896** MW. The residual is plants with no eGRID rate in ANY vintage
2018–2024 and no CAMPD rate — F1 `census_summary.md` "MISO — 36 plants" (largest: Kenneth C
Coleman 443 MW coal, Taconite Harbor 155 MW coal, Riverside 117 MW gas_st; the rest small oil/CT).

**Rule 19 composition check (vintage × mothball carry × retiree channel):** for every year, 0 of
the injected retiree / partial-exit / mothball units duplicates an operable `vintage_<Y>` row
(19 / 33 / 53 / 65 / 0 / 0 / 233 injected, 2019→2025). No double carry.

### 2.3 2019 input gaps found and closed (all data intake, zero free parameters)

A 2019-vs-2020 diff of the fleet-only application log found exactly three mechanisms that armed in
2020 and silently no-opped in 2019 — all MISO seam mechanisms, all for missing measured data:

| mechanism | missing input | fix |
|---|---|---|
| `miso_import_sil_measured_envelope` | MISO BA-to-BA interchange 2019 | `fetch_eia930_interchange.py --ba MISO --source bulk --years 2019 --merge` — 11 DIBAs × 8,759 h; all 516,600 pre-existing rows byte-identical (+11 local-2020-01-01 00:00 rows) |
| `miso_seam_flow_limit` export/import envelope | same | same |
| `miso_seam_measured_ladder` | `MISO_SEAM_LADDER_BY_YEAR[2019]` | derived by the frozen `derive_miso_seam_ladders.py --years 2019` (rule 23: source data extended); 2020 re-derives unchanged at HEAD |

Also landed: **MISO 2019 hub LMPs** (`fetch_miso_hub_lmp.py --years 2019`, monthly route) →
`actual_lmp_hourly{,_zonal}_MISO.parquet` + `actual_lmp.json` (benchmark; pure additions), and
**EIA-923 2017 coal receipts** so the 2019 coal budget's delivery rate averages its full Y-2..Y-1
window (without it the builder silently averages 2018 alone).

### 2.4 Outage families (windows by start year; committed files, MISO)

| family | file | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| std ≥ 5 d | `-unitroute-MISO` | 1223 | 1392 | 1379 | 1253 | 1210 | 1255 | 1194 |
| short coal | `-short-MISO` | 121 | 91 | 146 | 138 | 109 | 75 | 106 |
| short gas (**armed now**) | `-shortgas-MISO` | 325 | 260 | 410 | 424 | 321 | 310 | 330 |
| unit partial (**armed now**) | `campd-partial-outages-MISO` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| maxgen | `-maxgen-unitroute-MISO` | 0 | 0 | **100** (was 0) | 0 | 473 | 466 | 1232 |

* **Short-gas** re-derives byte-identically at post-F1 HEAD, every year.
* **Maxgen 2021 (LIVE):** the deriver read only the gzip hub record, so the registry's 2021 (Uri,
  `maxgen_event_step2`, South) and 2022 declarations were dropped as "uncertifiable" on the lapsed
  ground that they sat outside the 2023–2025 training span. `da_hub_paths` now reads the chunked
  staging (same verbatim rows). 2021 certifies (18 h > $150) and adds 100 unit windows, 4.69 GW;
  both 2022 December warnings fail the deriver's own certificate (0 h > $150) and stay out;
  2023–2025 byte-identical.
* **Unit partial = 0 — ROOT-CAUSED, routed, not fixed here.** In 2023 the detector finds **55
  plateaus on 33 of 86 baseload coal units**, and every one is dropped by the shared
  `outage_detect.filter_revealed_outages`, which treats a span in which the unit *ran* (cf ≥
  `REAL_RUN_CF`) in ≥ 24 high-net-load hours as "revealed available". A partial derate runs by
  definition, so the full-stop filter is structurally wrong for this family. It is a cross-ISO
  deriver defect (SPP / NWPP / SOCO share it) and outside this lane (rule 25). The flag is armed
  per the charter and is **inert in MISO**; that is reported, not hidden.
* **std-unitroute and short-coal do NOT reproduce at HEAD** (F2 finding #4 / #6, re-measured
  post-F1 with identical drift: std 2023/24/25 −22/−19/−30 windows, New Ulm ST_CHP + Waterford
  ST_GAS; short-coal 2019–22 +11/+8/+3/+8). F1 does not cause it (same numbers pre-/post-F1), and no
  MISO source data changed, so rule 23 forbids re-deriving here: **left as committed**, both already
  span 2019–2025. Routed as an open finding.

## 3. Pinned inputs and G-DRIFT (rule 29(b))

`git diff bb31b95c <this SHA> -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`:

| hunk | class | reason |
|---|---|---|
| **F1** `59ba7ca9` / `ca208aa9`: `data/egrid.py`, `process_eia860` year-matched join, `fleet/eia860.py`, `campd_bins._measured_rate_map` per-year, `chp.py`, `scenarios.py` six backcast default flips, `run_calibration._measured_heat_rate_flags`, CLI flags, `results/cache.py` epoch | **LIVE, by design** | the correction this lane exists to solve on |
| this lane: `COAL_SIGMOID_DEFAULTS` MISO bituminous / PRB / follower | **LIVE** | rule 23 re-derive, source change = F1's eGRID-2024 `hr_coal` (PRB 10.60→10.62, BIT 10.75→10.42); floor 0.687→0.686, BIT 0.532/4.115/1.092 → 0.549/3.989/1.126 |
| this lane: `MISO_SEAM_LADDER_BY_YEAR[2019]`, interchange 2019, LMP 2019, coal receipts 2017 | LIVE for 2019 only | §2.3 (the interchange's +11 2020-01-01 00:00 rows touch 2020 by one hour) |
| this lane: `derive_campd_maxgen_outages.da_hub_paths` + maxgen extract | LIVE for 2021 only | §2.4 |
| this lane: `PJM_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[2019]["MISO"]` | INERT for MISO; PJM 2019 only | the PJM registry's full-coverage contract (`test_registry_reproduces_the_frozen_derivation`) failed the moment MISO 2019 LMPs landed; row is the frozen `derive_pjm_seam_ladders` output. No registered PJM run carries 2019; routed to R-PJM |
| pjm-h22 RGGI 2020–22 (`fuel_trajectories`, `capacity_market`, `runner`) | INERT | PJM-only rows |
| F2 `4efebee0` `campd.ISO_MERIT_PANEL_STATES` SPP/SOCO | INERT | deriver-only, other ISOs |
| soco-61 `campd_dark_unit_year_windows` | INERT | default-off flag absent from recipe |
| Y-28 cache-key registration; Y-29 governance; Y-30 import-cycle / lint | INERT | no solve behaviour |
| `6831b110` storage compare | INERT | report-only |

Every non-LIVE hunk is INERT ⇒ form 4 is valid; the keeper's committed bundle is the control for
2020–2025 (2019 has none — it is reported, never differenced).

Pinned input sha256s are in `scripts/probes/_rmiso_shard_check.py::INPUT_SHA` (outage families,
interchange, hub LMP, coal receipts 2017, sigmoid artifact); each shard verifies them.

### 3.1 Tests

Full suite at this SHA: 51 failures, **every one pre-existing on `main` 92100753** (solve-surface pins, golden manifests, key-provenance census, soundness/export end-to-end, readiness battery — F1/Y-28 carry-over) except the one this lane caused and fixed (the PJM seam-registry coverage test above). `test_derive_coal_sigmoid` now passes.

## 4. Predictions (fixed before any shard)

No zero-LP dispatch estimate is claimed; directions only.

* **Heat rates.** Per-year measured CAMPD coal / ST / CC rates replace eGRID-2023 plant averages;
  for 2019–2022 the fleet moves off a snapshot + COD ramp onto year-matched EIA-860 (PJM's
  analogue: 2021 coal +39 %). Expect the largest class-TWh moves in **2019–2022**, coal up where
  the vintage restores retired-later units, and CC_REGULAR composition moves everywhere.
* **Short-gas** (1.0–1.4 % of gas MW-hours) removes a little gas availability every year → small
  price up, CC_REGULAR down.
* **Maxgen 2021** removes 4.69 GW in MISO-South over the Uri window → 2021 February prices up; C3b
  2021 (0.309 FAIL, "February priced high on every day") may move **away**.
* **Sigmoid:** BIT gas_mid 4.115 → 3.989 makes bituminous coal slightly cheaper to offer at
  mid gas; PRB essentially unchanged.
* **Train tier 2023–2025:** CALIBRATED predicted, **not promised** — the vintage default does not
  touch 2023–2024 much (the vintage ≈ canonical there) but the measured heat rates do.
* **2019:** first MISO solve of the year; no prior number to predict against.

## 5. Decision rule (fixed now)

Recommend promotion iff every structural gate holds:

* **S-1** every leg passes `_rmiso_shard_check.py` (recipe = keeper + exactly §2.1's six flips;
  vintage = solve year; pinned inputs; hydro classifier; mechanism log lines).
* **S-2** slack = dump = 0 in every year, except slack the keeper already carries (2024:
  26.9 GWh, hours 5700–5706).
* **S-3** G-DRIFT: no LIVE hunk beyond §3's declared set.

Gates C1–C8 are reported both ways, per year, at full magnitude, and decide nothing (owner
standard: *"If structural integrity improves but gates regress that may still be a keeper"*).
**Escalate rather than recommend** if the train tier (2023–2025) leaves CALIBRATED. The promotion
decision is the owner's (rule 31).

## 6. How it is solved

Seven shards, one per year (rule 36):

```
python scripts/replay_keeper.py results/calibration/miso268_yard_span \
  --years <Y> --set unit_outage_short_windows_gas=true --set unit_partial_outage_windows=true \
  --out-dir results/calibration/rmiso_<Y> --note "R-MISO corrected inputs <Y>"
python scripts/probes/_rmiso_shard_check.py --leg results/calibration/rmiso_<Y> --year <Y> --log <log>
```

F1's defaults arrive by the replay passing `None` for the six fields (the keeper recorded none of
them as a kwarg), which the shard check verifies against the recorded config.
Prep: `uv sync`; `hydrate_data.py --profile miso`; `curate_coal_stocks.py`; `curate_coal_receipts.py`;
`curate_hydro_plant_modes.py --iso MISO`. Push: `.gitignore` negation for its own out-dir + a plain
`git add`, bundle incl. `dispatch/<Y>_P1.parquet` (rule 34(a)). Parent: fetch by SHA,
`git ls-tree` > 0, re-run the check, compose (`_rmiso_compose_span.py`), `stamp_config_partition
--check`, register, score vs the keeper, write the RESULT.

## 7. Launch record (appended after the pin; §1–§6 unchanged)

Launched 2026-09-24 19:15–19:17 UTC, all seven pinned to
`6a8d17947c9fb3da0eac081eaa10408cb581863a` (this document's commit). Tagged `r-miso`, `shard`;
auto-PR off. Each pushes its bundle (with `dispatch/<Y>_P1.parquet`) plus the
`results/calibration/_shared/MISO/` captures its `meta.json` names.

| year | shard session | branch | out-dir |
|---|---|---|---|
| 2019 | `session_01NU6w97UHvbLYSiYb54Q3Sv` | `claude/rmiso-2019` | `results/calibration/rmiso_2019` |
| 2020 | `session_01TegVbT2eiz7XMY99ZG9V6H` | `claude/rmiso-2020` | `results/calibration/rmiso_2020` |
| 2021 | `session_01C3xEiMxRDmRZrvkLyb5VX6` | `claude/rmiso-2021` | `results/calibration/rmiso_2021` |
| 2022 | `session_01FSntQEmqV27LX5p6cHVYMn` | `claude/rmiso-2022` | `results/calibration/rmiso_2022` |
| 2023 | `session_01RUkATQseefLk1mKTuWSvt2` | `claude/rmiso-2023` | `results/calibration/rmiso_2023` |
| 2024 | `session_01QSTednV5x2UFSUJMmSqk5c` | `claude/rmiso-2024` | `results/calibration/rmiso_2024` |
| 2025 | `session_01NkXi5Wuz5kCzJqYvXHUxoe` | `claude/rmiso-2025` | `results/calibration/rmiso_2025` |
