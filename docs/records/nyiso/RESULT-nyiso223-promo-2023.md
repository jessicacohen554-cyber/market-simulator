# RESULT — nyiso-223 promo shard, 2023

Shard `nyiso223-promo-2023`. One year: **2023**. NYISO only.
Pinned SHA `7689d59ad5ef1343e44c3dae3544e7f8bba415c5` (verified at start; no pull/rebase).

**Purpose:** the owner ruled PROMOTE on the nyiso-223 `nyiso_hub_gap_month_level` arm. A prior
shard solved this exact year and lost its bundle with its container. This shard regenerates the
2023 bundle and pushes its slim artifacts to `shard-artifacts/nyiso223/2023/` for the parent to
compose and register (rule 15 `[R-DASHBOARD]` registration is the parent's job, once, at the end).

## Provenance

- Base bundle: `results/calibration/nyiso_fuelvintage_A` (NYISO keeper span 2023–2025).
- Command: `scripts/replay_keeper.py results/calibration/nyiso_fuelvintage_A --years 2023
  --set nyiso_hub_gap_month_level=true --out-dir results/calibration/nyiso223_gapfill_2023
  --note "nyiso-223 hub-daily unpriced-day gap fill (arm)"`
- Solve bundle on local disk only, **gitignored, never committed** (rule 29 `[R-SCREEN]` (c) as
  amended by rule 31 `[R-RETAIN]`: keep it out of `main`, do not `rm` it).

## Pre-solve gate (zero LP) — PASS, exact

`3.3566 3.3566 3.919 3.683 4416` — matched the pre-registered expectation to every digit.
Annual hub-daily gas mean unchanged (3.3566 both arms); the Dec 22–31 window moves **down**
3.919 → 3.683 $/MMBtu; 4,416 hours repriced.

## Post-solve signature — PASS, exact

| field | value |
|---|---|
| `nyiso_hub_gap_month_level` | `True` |
| `offer_curve_by_group.CC_REGULAR.peak` | `2.25` |
| `offer_curve_by_group.CC_REGULAR.pct_peaking` | `8.0` |
| `nyiso_gas_commitment_bridge` | `True` |
| `nyiso_dynamic_reserve_requirements` | `True` |
| iso / years (`meta.json`) | `NYISO` / `[2023]` |

## 1. Annual mean LMP

Computed from `hourly/system_2023.parquet`, P1, over the **5 load-bearing zones**
(Capital_Hudson, Long_Island, Lower_Hudson, NYC, Upstate_West; `NYISO_external` carries zero
demand and is excluded). The keeper column is the incumbent bundle
`nyiso_fuelvintage_A/hourly/system_2023.parquet` recomputed **by the identical method**, so the
delta is like-for-like.

| basis | arm | keeper (same method) | delta |
|---|---|---|---|
| load-weighted, hour × zone (Σ p·d / Σ d) | **33.6521** | 33.6503 | **+0.0018** |
| load-weighted, zone-mean × zone-total-demand | **32.3715** | 32.3680 | **+0.0035** |
| equal-hour (mean over the 5 load zones) | **34.1307** | 34.1255 | +0.0052 |
| equal-hour (all 6 zones, incl. zero-load external) | 33.0200 | 33.0164 | +0.0036 |

**FLAG — the absolute LW level does not reproduce the number in the shard brief, though the
delta does.** The brief expected arm **32.3600** vs keeper **32.3557** (+0.0043). The closest
basis here (zone-mean × zone-total-demand) gives 32.3715 vs 32.3680 (+0.0035) — i.e. **both
sides are offset by the same ≈ +0.012**, so this is a basis/weighting difference in how the prior
shard formed the mean, not a divergence of the arm from the keeper. The direction, the order of
magnitude and the sign of the arm−keeper delta all reproduce. Two further data points that this
solve is the intended one, not a different configuration:

- the committed registered keeper payload
  (`frontend/data/backcast/runs/2026-09-09-nyiso-221-fuelvintage-span.js`) carries per-zone
  `p`/`d` for 2023 whose weighted mean is **33.6501** — matching the hour × zone basis above
  (33.6503), not 32.3557; so 32.3557 is on neither of the two bases this bundle can form;
- C3c below reproduces the brief's expected values **exactly** (2 hours, $326.4235).

The parent should form the headline on whatever basis it uses for the composite and difference
it against the keeper computed the same way.

## 2. December windows (equal-hour, 5 load zones, 365-day calendar)

| window | hours | arm | keeper | delta |
|---|---|---|---|---|
| Dec 22–31 | 8520–8759 | **34.9152** | 35.9609 | **−1.0457** |
| Dec 1–21 | 8016–8519 | **36.2071** | 35.6641 | +0.5430 |

The late-December window moves **down**, as the pre-solve gate's fuel delta predicted
(3.919 → 3.683 $/MMBtu over the same window). This is the mechanism's own footprint.

## 3. C3c — price tail / scarcity

| quantity | arm | expected | keeper |
|---|---|---|---|
| hours load-weighted > $300 | **0** | — | 0 |
| hours any zone > $300 | **2** | 2 | 2 |
| model max zonal price $/MWh | **326.4235** | 326.4235 | 326.4235 |

Exact reproduction of the pre-registered C3c signature.

## 4. C1 per-class energy (TWh)

Basis: `hourly/class_hourly_2023.parquet`, `pass == "P1"`, Σ mw / 1e6 over all 8,760 hours —
the model's own class dispatch, not a benchmark comparison (the C1 scored comparison is the
parent's, against EIA-923 − BTM per rule 15's committed-sidecar route).

| class | arm TWh | keeper TWh | delta |
|---|---|---|---|
| CC_REGULAR | 33.8082 | 33.7987 | +0.0096 |
| nuclear | 27.4871 | 27.4871 | 0.0000 |
| hydro | 26.6158 | 26.6158 | 0.0000 |
| import | 23.3326 | 23.3357 | −0.0031 |
| CC_CHP | 15.9044 | 15.9057 | −0.0012 |
| ST_GAS | 9.7969 | 9.8097 | −0.0128 |
| wind | 4.5907 | 4.5907 | 0.0000 |
| OTHER | 2.1973 | 2.1973 | 0.0000 |
| CT_CHP | 1.5357 | 1.5350 | +0.0007 |
| ST_CHP | 1.3732 | 1.3686 | +0.0046 |
| biomass | 0.8395 | 0.8395 | 0.0000 |
| CT_PEAKER | 0.3973 | 0.3967 | +0.0006 |
| solar | 0.2798 | 0.2798 | 0.0000 |
| oil | 0.1497 | 0.1497 | 0.0000 |
| COAL_BIT / COAL_PRB | 0.0000 | 0.0000 | 0.0000 |
| **total** | **148.3084** | **148.3100** | −0.0016 |

The response is confined to the gas-fired rows the repriced fuel reaches (CC_REGULAR up,
ST_GAS down — a merit-order rotation inside gas), with the free/renewable/nuclear/hydro rows
byte-identical. That is the footprint the mechanism claims.

## 5. Legitimacy diagnostics

| diagnostic | verdict |
|---|---|
| D-1 diurnal shape | **PASS** |
| D-2 forced-energy attribution | **PASS** (CC_REGULAR forced share 0.0112 vs 0.30 limit; CT_PEAKER 0.0) |
| D-4 off-window binding | **FAIL** (2 rows — see below) |
| D-5 forecast/backcast parity | **PASS** |
| D-9 overlay quarantine | **PASS** |
| D-10 free-class-only rescore | **PASS** (2/2 wind/solar rows delivered-pinned, advisory-only) |

Failing D-4 rows (both `reliability_floor × ST_GAS`, 2023):

1. **plant 2480** — floored for 0.0015 TWh (0.1% of the mechanism's forced energy); measured
   median output over the 157 hours the floor binds for it is 0.000 MW (100.0% at zero).
2. **plant 8906** — floored for 0.2404 TWh (12.6% of the mechanism's forced energy); measured
   median output over the 5,562 hours the floor binds for it is 0.000 MW (51.0% at zero).

**These are INHERITED, not introduced.** The incumbent keeper `nyiso_fuelvintage_A` carries the
same two rows for 2023, with the same plants, the same percentages and near-identical energies
(0.0015 TWh / 157 h and 0.2397 TWh / 5,551 h). The arm changes neither the mechanism nor its
window; the ~0.0007 TWh / 11-hour drift is the dispatch response to the repriced fuel. The
`legitimacy diagnostics gate FAIL` line in the solve log is this pre-existing D-4 condition,
which the keeper already carries — it is not a new defect of this arm.

## 6. Files pushed

Staged to `shard-artifacts/nyiso223/2023/` — deliberately **not** `results/calibration/`, so the
Class-E parity sweep (which scans committed `results/calibration/*` bundle dirs only) cannot go
red on an unregistered bundle dir. The parent moves these into the composite and deletes the
staging copy at registration.

| path | bytes |
|---|---|
| `shard-artifacts/nyiso223/2023/meta.json` | 14,764 |
| `shard-artifacts/nyiso223/2023/run_config.json` | 43,063 |
| `shard-artifacts/nyiso223/2023/legitimacy_diagnostics.json` | 21,948 |
| `shard-artifacts/nyiso223/2023/btm.parquet` | 3,339 |
| `shard-artifacts/nyiso223/2023/hourly/class_hourly_2023.parquet` | 464,127 |
| `shard-artifacts/nyiso223/2023/hourly/system_2023.parquet` | 859,292 |
| `shard-artifacts/nyiso223/2023/hourly/reserve_family_2023.parquet` | 49,008 |
| `shard-artifacts/nyiso223/2023/hourly/class_band_hourly_2023.parquet` | 251,018 |
| `shard-artifacts/nyiso223/2023/hourly/storage_2023.parquet` | 102,893 |

`metrics.json` and `calibration_attestation.json` **do not exist** in a `replay_keeper.py`
bundle and so were not copied — the brief anticipated this. Nothing was skipped for size; the
largest staged file is 859 KB. Not staged (not on the brief's list): `flows.parquet`,
`storage.parquet`, root `system.parquet` (a duplicate of `hourly/system_2023.parquet`),
`hourly/network_2023.parquet`, `hourly/unit_hourly_2023.parquet` (17.3 MB), and the `dispatch/`
and `floors/` directories — all still on the shard's local disk in
`results/calibration/nyiso223_gapfill_2023/`, which was **not deleted** (rule 31 `[R-RETAIN]`)
but does not survive this container.
