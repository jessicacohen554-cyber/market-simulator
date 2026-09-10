# RESULT — nyiso-223 promo shard, 2022

**Shard:** `nyiso223-promo-2022` · **ISO:** NYISO · **Year solved:** 2022 (one year, this shard's whole scope)
**Pinned SHA:** `7689d59ad5ef1343e44c3dae3544e7f8bba415c5` (verified at start; no pull/rebase/sync performed)
**Date:** 2026-09-10

The owner **ruled PROMOTE**. This shard exists to regenerate the 2022 bundle and push its
artifacts so the parent can compose and register a keeper — a previous shard solved this same
year and lost the bundle with its container. **The artifact push is the deliverable.**

## 1. Provenance

Replay of the designated NYISO keeper recipe with the arm flag set:

```
scripts/replay_keeper.py results/calibration/nyiso_fuelvintage_A \
  --years 2022 --set nyiso_hub_gap_month_level=true \
  --out-dir results/calibration/nyiso223_gapfill_2022 \
  --note "nyiso-223 hub-daily unpriced-day gap fill (arm)"
```

Solve exit code 0. Wall time ~4 min (04:31:30 → 04:35:39 UTC).

## 2. Hard stops — all PASS

| Stop | Expected | Observed | |
|---|---|---|---|
| `git rev-parse HEAD` | `7689d59a…415c5` | `7689d59ad5ef1343e44c3dae3544e7f8bba415c5` | PASS |
| `nyiso_fuelvintage_A/meta.json` | exists, `iso == NYISO` | exists, `NYISO` | PASS |
| `grep -c nyiso_hub_gap_month_level scenarios.py` | ≥ 4 | 4 | PASS |

## 3. Pre-solve gate (zero LP) — EXACT MATCH

Expected `8.4431 8.4431 8.049 8.949 4440`; observed **`8.4431 8.4431 8.049 8.949 4440`**.

Reading: the gap fill is annual-mean-neutral (8.4431 both arms), lifts the Dec 22–31 hub daily
gas price **8.049 → 8.949 $/MMBtu** (+0.900), and touches **4,440** hourly cells.

Setup note: fresh container had no `data/clean`. Two curations were sufficient —
`curate_capacity_deliverability.py --isos NYISO` (35 rows) and `curate_nyiso_interface_flows.py`
(9 partitions). No third datatype was named by the solve; `regenerate_clean.py` was not run.

## 4. Post-solve signature — ALL MATCH

| Field | Expected | Observed |
|---|---|---|
| `nyiso_hub_gap_month_level` | true | **true** |
| `offer_curve_by_group.CC_REGULAR.peak` | 2.25 | **2.25** |
| `offer_curve_by_group.CC_REGULAR.pct_peaking` | 8.0 | **8.0** |
| `nyiso_gas_commitment_bridge` | true | **true** |
| `nyiso_dynamic_reserve_requirements` | true | **true** |
| `iso` / `years` | NYISO / [2022] | **NYISO / [2022]** |

## 5. Numbers

Zones in `system_2022.parquet`: the 5 load zones + `NYISO_external` (import node, excluded from
the load-zone aggregates below).

### 5.1 Annual mean LMP (2022)

| Basis | $/MWh |
|---|---|
| Load-weighted over the 5 load zones (energy-weighted, all 8760 h) | **69.8215** |
| Equal-hour mean of the hourly load-weighted ISO price | **65.1949** |
| Equal-hour, equal-zone (simple mean over 5 zones × 8760 h) | **72.9797** |

### 5.2 December split (365-day calendar, cut at hour 8520)

| Window | Hours | Equal-hour LW ISO | Equal-hour equal-zone |
|---|---|---|---|
| Dec 1–21 | 8016–8519 (504 h) | **69.3913** | 75.9127 |
| Dec 22–31 | 8520–8759 (240 h) | **66.6838** | 73.5004 |

**Stated plainly:** the Dec 22–31 window prices **below** Dec 1–21 (−2.71 $/MWh LW) even though
the arm raises that window's hub gas by +0.900 $/MMBtu. This shard solved **only the arm**, so it
carries no 2022 control to difference against — the sign of the arm's *effect* on the December
split is **not** established here, only the arm's level. Any effect claim needs the parent's
comparison against the committed control numbers (rule 29 `[R-SCREEN]` form 4).

### 5.3 C3c price tail

| Metric | Value |
|---|---|
| Hours load-weighted ISO price > $300 | **8** |
| Hours any load zone > $300 | **10** |
| Max zonal price (5 load zones) | **2000.0000** |
| Max zonal price (all zones incl. `NYISO_external`) | **2000.0000** |

### 5.4 C1 per-class TWh

**Basis, explicitly:** `hourly/class_hourly_2022.parquet`, **P1 pass only**, summed over all 8760
hours and aggregated across all zones; `mw` is an hourly-average MW so MWh = MW × 1 h, ÷ 1e6 → TWh.

| Class | TWh | | Class | TWh |
|---|---|---|---|---|
| CC_REGULAR | 36.9308 | | CT_CHP | 2.0827 |
| import | 27.8487 | | ST_CHP | 1.4878 |
| nuclear | 26.7531 | | biomass | 1.0615 |
| hydro | 25.6101 | | COAL_PRB | 0.6546 |
| CC_CHP | 13.4303 | | oil | 0.5059 |
| ST_GAS | 6.5321 | | solar | 0.1093 |
| wind | 4.7044 | | COAL_BIT | 0.0000 |
| CT_PEAKER | 4.2932 | | **TOTAL** | **154.1906** |
| OTHER | 2.1861 | | *(load, 5 zones)* | *152.6817* |

### 5.5 Legitimacy diagnostics

| Diagnostic | Verdict | Failures |
|---|---|---|
| D-1 diurnal shape | **PASS** | 0 |
| D-2 forced-energy attribution | **PASS** | 0 (max merchant share CC_REGULAR 0.0026 vs 0.30 limit) |
| D-4 off-window binding | **FAIL** | **3** |
| D-5 forecast/backcast parity | **PASS** | 0 |
| D-9 overlay quarantine | **PASS** | 0 |
| D-10 free-class-only rescore | **PASS** | 0 (wind + solar `delivered_pinned` → advisory-only, excluded from skill claims) |

**The three failing D-4 rows** — all `unit-conduct`, none a `window` row (every window-level row
passed):

| Floor | Plant | floored TWh | off-window share | binding h | measured median MW | measured zero share |
|---|---|---|---|---|---|---|
| `reliability_floor × ST_GAS` | 2480 | 0.0005 | 0.0003 | 151 | 0.0 | 0.9801 |
| `reliability_floor × ST_GAS` | 8006 | 0.0037 | 0.0019 | 70 | 0.0 | 0.6143 |
| `nyiso_gas_commitment_bridge × CC_REGULAR` | 52056 | 0.0050 | 0.0534 | 228 | 0.0 | 0.8070 |

Each is the rule 17 `[R-FLOOR-WINDOW]` signature: a floor binding on a unit whose own measured
CEMS conduct is mostly zero in those hours. Combined floored energy is 0.0092 TWh (~0.006 % of the
154.19 TWh total). D-4's own notes record that the per-unit conduct rider **skipped 4 floored
plants** carrying the benchmark's CT-only CEMS flag (EIA-923 net > 1.1× CAMPD gross ⇒ scored on
EIA-923 monthly, hourly CAMPD incomplete), and that one interchange pseudo-unit row
(`u:NYISO_external_HQ_hydro`) is scored under the floor-energy convention as an upper bound.

This is **reported, not adjudicated**. It is a pre-existing property of the keeper recipe's floors,
not something the gap-fill arm introduces, and the promotion decision is the owner's (rule 31
`[R-RETAIN]`). Adjudication belongs to the parent at composition.

## 6. Artifacts pushed

Staged to `shard-artifacts/nyiso223/2022/` — **deliberately not** `results/calibration/`, so the
Class-E registry-payload parity sweep (which scans committed `results/calibration/*` bundle dirs)
cannot go red on this. The parent moves them into the composite and deletes the staging copy in
the registration commit.

| File | Bytes |
|---|---|
| `meta.json` | 14,764 |
| `run_config.json` | 43,063 |
| `legitimacy_diagnostics.json` | 22,058 |
| `btm.parquet` | 3,339 |
| `hourly/class_hourly_2022.parquet` | 469,054 |
| `hourly/system_2022.parquet` | 869,422 |
| `hourly/reserve_family_2022.parquet` | 55,719 |
| `hourly/class_band_hourly_2022.parquet` | 265,942 |
| `hourly/storage_2022.parquet` | 110,186 |
| **Total** | **~1.8 MB** |

`metrics.json` and `calibration_attestation.json` were **not** copied — `replay_keeper.py` does not
emit them into a replay bundle, so they do not exist for this run. Nothing was skipped for size;
no file came near the ~90 MB ceiling.

**Retained on local disk, not deleted** (rule 31 `[R-RETAIN]`): the full bundle
`results/calibration/nyiso223_gapfill_2022/` — including `unit_hourly_2022.parquet` (17.4 MB),
`network_2022.parquet`, `flows.parquet`, `system.parquet`, `storage.parquet`, and the `dispatch/`
and `floors/` subdirectories — which are **not** in the slim push. That path is gitignored, so it
cannot reach `main` or turn the parity gate red, and nothing was removed. **It does not survive
container reclamation**: if the parent needs any of it, it must be pulled before this session ends.

## 7. Scope discipline

No edits under `src/` or `scripts/`. No `git add -A` / `git add .`. Nothing under `results/` or
`frontend/data/backcast/**` committed. No `dashboard_add_run.py`, `build_manifest.py`,
`build_status.py`, or `prune_iso_runs.py` run — registration is the parent's job, once, at the end.
No pull request opened. No result deleted.
