# RESULT — nyiso-223 promotion shard, year 2024

**Shard:** `nyiso223-promo-2024` · **Date:** 2026-09-10 · **HEAD:** `7689d59ad5ef1343e44c3dae3544e7f8bba415c5`

Owner has RULED PROMOTE on the nyiso-223 hub-daily unpriced-day gap fill
(`nyiso_hub_gap_month_level=true`). This shard regenerated the **2024** leg and
staged its slim artifacts for the parent to compose and register. A previous
shard solved this same year and lost the bundle with its container; the artifact
push is therefore the deliverable, not the numbers.

## Provenance

| item | value |
|---|---|
| base bundle (control) | `results/calibration/nyiso_fuelvintage_A` (years 2023/2024/2025) |
| arm command | `replay_keeper.py … --years 2024 --set nyiso_hub_gap_month_level=true` |
| out-dir | `results/calibration/nyiso223_gapfill_2024` |
| solve wall time | 404.7 s (data_prep 49.7 · P0 164.6 · markup 7.3 · P1 172.0 · write 11.1); peak RSS 5.68 GB |
| staged to | `shard-artifacts/nyiso223/2024/` (**not** `results/calibration/`, so the Class-E parity sweep cannot see it) |

## Hard stops and gates — all PASS

- HEAD sha matches the pinned SHA. No `pull`/`rebase`/`sync` performed.
- `nyiso_fuelvintage_A/meta.json` present, `iso == NYISO`.
- `grep -c nyiso_hub_gap_month_level src/market_sim/config/scenarios.py` = 4 (≥ 4).
- **Pre-solve zero-LP gate**: `2.7969 2.7969 3.877 4.061 5880` — exact match to expected.
- **Post-solve signature**: `nyiso_hub_gap_month_level=True`; `offer_curve_by_group.CC_REGULAR.peak=2.25`,
  `.pct_peaking=8.0`; `nyiso_gas_commitment_bridge=True`; `nyiso_dynamic_reserve_requirements=True`;
  `iso=NYISO`, `years=[2024]` — exact match.

## 1. Annual mean LMP (5 load-carrying zones; `NYISO_external` excluded, zero demand)

Per-zone, arm:

| zone | equal-hour mean price ($/MWh) | annual demand (TWh) |
|---|---:|---:|
| Upstate_West | 35.9420 | 52.0950 |
| Capital_Hudson | 39.0790 | 20.6295 |
| Lower_Hudson | 39.8091 | 8.4654 |
| NYC | 40.4089 | 49.5759 |
| Long_Island | 40.8662 | 19.7509 |

Three bases, arm vs control, both computed here from the two bundles' own
`hourly/system_2024.parquet`:

| basis | control (`nyiso_fuelvintage_A`) | arm | Δ |
|---|---:|---:|---:|
| **zone-level LW** — `Σ(p̄_z · D_z)/Σ D_z`, `p̄_z` = zone equal-hour mean | **38.6334** | **38.7069** | **+0.0735** |
| equal-hour — unweighted mean of the 5 zone means | 39.1571 | 39.2210 | +0.0639 |
| hourly LW — `Σ_{z,t}(p·d)/Σ_{z,t} d` (the dashboard payload's basis) | 40.1499 | 40.2188 | +0.0689 |

**Reproduction note (flagged, per the shard brief).** The prior solve of this
arm/year reported LW **38.7081** vs keeper **38.6332**; this shard gets
**38.7069** vs **38.6334** on the zone-level basis. The control side reproduces to
0.0002 — pure display rounding. The arm side differs by **0.0012 (0.003 %)**, and
the arm−control delta reproduces to 0.0014 (+0.0735 here vs +0.0749 prior). That
is the same order as the control's rounding gap, so this is read as a reporting
precision difference and **not** a solve difference — but it is not a bit-exact
reproduction and is called out here rather than smoothed over.

For the record, the registered payload of `2026-09-09-nyiso-221-fuelvintage-span`
stores each zone's `p` as its *hourly load-weighted* price, so its cross-zone LW is
40.1506 — matching the third row above (40.1499), not the 38.6332 figure. Neither
38.6332 nor 38.7081 comes from that payload; both are on the zone-level basis.

## 2. December, on the **model 365-day calendar**

2024 is a leap year in reality but the model runs 365 days, so December is hours
8016–8759 and the Dec-21/22 cut is hour **8520**. (A previous shard sliced this on a
366-day calendar and got it wrong.)

| window | model hours | equal-hour mean price ($/MWh) |
|---|---:|---:|
| Dec 1–21 | 8016–8519 (504 h) | **53.2448** |
| Dec 22–31 | 8520–8759 (240 h) | **54.3192** |
| delta (22–31 − 1–21) | | **+1.0744** |

This is the window the mechanism targets: the gap fill lifts the unpriced late-December
days from the 3.877 → 4.061 $/MMBtu hub level measured in the pre-solve gate.

## 3. C3c price tail / scarcity

| measure | value |
|---|---:|
| hours load-weighted price > $300 | **0** |
| hours any zone > $300 | **0** |
| model max zonal price | **$217.6742** |
| hours LW > $100 | 134 |
| hours any zone > $100 | 196 |

0 h and ≈ $217.7 — as expected. C3c remains the ledgered model-class limitation
(rule 22 `[R-C3C]`); nothing here changes that.

## 4. C1 per-class TWh

**Basis:** `hourly/class_hourly_2024.parquet`, pass `P1` (the only pass present),
`sum(mw)` over all 8760 hours and all zones ÷ 1e6. Hourly MW summed over hourly
intervals is MWh, so this is grid-delivered energy.

| class | TWh |
|---|---:|
| CC_REGULAR | 36.9470 |
| nuclear | 26.9532 |
| hydro | 26.7390 |
| import | 20.7058 |
| CC_CHP | 19.5467 |
| ST_GAS | 8.5777 |
| wind | 6.0116 |
| OTHER | 2.2014 |
| CT_CHP | 1.2047 |
| ST_CHP | 1.1350 |
| biomass | 0.7597 |
| solar | 0.5861 |
| oil | 0.4419 |
| CT_PEAKER | 0.3676 |
| COAL_BIT | 0.0000 |
| COAL_PRB | 0.0000 |
| **TOTAL** | **152.1775** |

## 5. Legitimacy diagnostics

| diagnostic | verdict |
|---|---|
| D-1 diurnal shape | **PASS** |
| D-2 forced-energy attribution | **PASS** |
| D-4 off-window binding | **FAIL** (2 rows — see below) |
| D-5 forecast/backcast parity | **PASS** |
| D-9 overlay quarantine | **PASS** |
| D-10 free-class-only rescore | **PASS** |

### Failing D-4 rows (both **pre-existing in the control**, not introduced by this arm)

| floor × class | plant | floored TWh | off-window share | binding h | measured median MW | verdict |
|---|---|---:|---:|---:|---:|---|
| `reliability_floor` × ST_GAS | 2480 | 0.0002 | 0.0001 | 23 | 0.0 | FAIL |
| `nyiso_gas_commitment_bridge` × CC_REGULAR | 54574 | 0.0021 | 0.0172 | 70 | 0.0 | FAIL |

The identical two rows fail in `nyiso_fuelvintage_A` for 2024 (plant 2480:
0.0002 TWh / 23 h, identical; plant 54574: 0.0029 TWh / 0.0254 / 89 h). The arm is
**marginally better** on the second row — 0.0021 vs 0.0029 TWh, 70 vs 89 binding
hours. So D-4's failure is inherited from the control, and the gap fill does not
worsen it.

D-1: both gated classes pass — CT_PEAKER `profile_r` 0.978 / `cv_ratio` 1.534;
ST_GAS `profile_r` 0.963 / `cv_ratio` 1.511.
D-2 mechanisms above 5 % of class: `nuclear_mustrun` 0.7737, `hydro_min_flow`
0.2869, `chp_steam`×ST_CHP 0.2821, `firm_import` 0.2263, `reliability_floor`×ST_GAS
0.2056 — all within the D-2 caps for their exemption status.

## 6. Files staged and pushed

`shard-artifacts/nyiso223/2024/` — 1,787,414 bytes total:

| path | bytes |
|---|---:|
| `meta.json` | 14,764 |
| `run_config.json` | 43,063 |
| `legitimacy_diagnostics.json` | 21,207 |
| `btm.parquet` | 3,339 |
| `hourly/system_2024.parquet` | 864,666 |
| `hourly/class_hourly_2024.parquet` | 447,301 |
| `hourly/class_band_hourly_2024.parquet` | 249,192 |
| `hourly/storage_2024.parquet` | 93,179 |
| `hourly/reserve_family_2024.parquet` | 50,703 |

**Not staged, because a single-year `replay_keeper.py` does not score:**
`metrics.json` and `calibration_attestation.json` were never written by the run.
The parent scores the composite. Nothing was skipped for size — the largest staged
file is 865 KB.

Left in the bundle and deliberately not staged (bulk, not on the slim list):
`hourly/unit_hourly_2024.parquet` (18.4 MB), `hourly/network_2024.parquet` (358 KB),
`dispatch/2024_P1.parquet` (20.9 MB), `flows.parquet`, `storage.parquet`,
`system.parquet`, `floors/2024_P1.npz`.

## Retention (rule 31 `[R-RETAIN]`)

**Nothing was deleted.** The full bundle `results/calibration/nyiso223_gapfill_2024/`
(~41 MB) sits on this container's local disk, gitignored, and **will not survive
container reclamation**. The staged 1.79 MB in `shard-artifacts/` is pushed and is
what the parent must rely on. If the parent needs `unit_hourly` or `dispatch` for
unit-level questions, it must say so before this container is reclaimed — otherwise
that costs a ~7 minute re-solve of this year.
