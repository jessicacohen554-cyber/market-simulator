# RESULT — nyiso-223 promotion shard, year 2025

**Shard:** `nyiso223-promo-2025` · **ISO:** NYISO · **Year solved:** 2025 (only)
**Date:** 2026-09-10 · **HEAD:** `7689d59ad5ef1343e44c3dae3544e7f8bba415c5`

Regeneration of the 2025 leg of the nyiso-223 hub-daily unpriced-day gap-fill arm,
after the owner ruled PROMOTE and the prior shard's bundle was lost with its
container. **The deliverable is the pushed artifact set**, staged at
`shard-artifacts/nyiso223/2025/` for the parent to compose and register.

## Provenance

- Base keeper: `results/calibration/nyiso_fuelvintage_A`
  (run id `2026-09-09-nyiso-221-fuelvintage-span`, determination CALIBRATED, rubric v3.6)
- Command:
  ```
  scripts/replay_keeper.py results/calibration/nyiso_fuelvintage_A \
    --years 2025 --set nyiso_hub_gap_month_level=true \
    --out-dir results/calibration/nyiso223_gapfill_2025 \
    --note "nyiso-223 hub-daily unpriced-day gap fill (arm)"
  ```
- Solve exit code 0; wall time ~6.5 min.

## Hard stops and gates

| check | expected | observed | verdict |
|---|---|---|---|
| `git rev-parse HEAD` | `7689d59a…415c5` | identical | PASS |
| keeper `meta.json` iso | `NYISO` | `NYISO` | PASS |
| `grep -c nyiso_hub_gap_month_level scenarios.py` | ≥ 4 | 4 | PASS |
| pre-solve zero-LP fuel gate | `5.5602 5.5602 7.256 7.256 6552 7.587` | `5.5602 5.5602 7.256 7.256 6552 7.587` | PASS (exact) |

**Post-solve signature** (from `run_config.json → scenario_config`) — all exact:
`nyiso_hub_gap_month_level=True`, `offer_curve_by_group.CC_REGULAR.peak=2.25`,
`.pct_peaking=8.0`, `nyiso_gas_commitment_bridge=True`,
`nyiso_dynamic_reserve_requirements=True`; `meta.iso=NYISO`, `meta.years=[2025]`,
`mode=backcast`.

## 1. Annual mean LMP

Computed from `hourly/system_2025.parquet` (P1), over the five load-carrying zones
(`Capital_Hudson`, `Long_Island`, `Lower_Hudson`, `NYC`, `Upstate_West`;
`NYISO_external` carries zero demand and drops out of every weighting).

| basis | keeper (committed) | arm | delta |
|---|---|---|---|
| zone equal-hour mean × zone annual demand | 58.3896 | **58.5400** | **+0.1504** |
| hourly demand-weighted (all zone-hours) | 61.5983 | 61.7227 | +0.1244 |
| equal-hour, 5 load zones | 59.2440 | 59.3874 | +0.1434 |

**Reproduction: CONFIRMED on the delta.** The prior solve of this exact arm/year
reported LW 58.5074 against keeper 58.3573 — a delta of **+0.1501**, which this
solve reproduces at **+0.1504** (agreement to 3 × 10⁻⁴).

**Level caveat, stated rather than smoothed:** the absolute levels here sit
**+0.032 above** the prior shard's on both legs (keeper 58.3896 vs 58.3573; arm
58.5400 vs 58.5074). The offset is *constant across both legs*, so it is a
difference in metric basis, not in the solve. Reverse-engineering it was
attempted and not fully pinned: the in-zone demand-weighted construction used by
`scripts/probes/nyiso218_screen_gates.py::_year_block` yields 61.60/61.72, and
2-dp zone rounding shifts the zone-weighted basis by only +0.0002. The parent
should treat **the delta as the reproduced quantity** and re-derive the level on
its own scorer basis. No scorer or source file was modified to chase this.

## 2. Monthly equal-hour mean price (5 load zones)

| month | keeper | arm | delta |
|---|---|---|---|
| **January** | 96.8662 | 98.2681 | **+1.4019** |
| **November** | 54.6471 | 55.1355 | **+0.4884** |
| **December** (internal control) | 97.2256 | 97.2291 | **+0.0035** |

December behaves as the control predicts: its prints reach the 31st, so it has no
moved fuel hours, and it moves **+0.0035 ≈ 0**. The residual is second-order
coupling (cyclic storage SOC boundary), not a fuel-path move. January carries the
year's largest move, as the pre-solve gate implied. Every other month is within
±0.14; the full delta vector is Feb −0.0327, Mar −0.0120, Apr +0.0002,
May +0.0069, Jun −0.1320, Jul +0.0059, Aug −0.0775, Sep +0.0404, Oct +0.0052.

## 3. C3c price tail

| metric | keeper | arm | expected |
|---|---|---|---|
| hours load-weighted > $300 | 3 | **3** | 3 |
| hours any zone > $300 | 3 | **3** | 3 |
| model max zonal price | 323.5304 | **323.5304** | 323.5304 |

Matches the expectation exactly; the tail is unmoved by the arm.

## 4. C1 per-class TWh

From `hourly/class_hourly_2025.parquet` (P1), `Σ mw / 1e6` — grid-delivered basis.

| class | keeper | arm | delta |
|---|---|---|---|
| CC_CHP | 20.3967 | 20.3536 | −0.0431 |
| CC_REGULAR | 35.3355 | 35.2990 | −0.0364 |
| COAL_BIT | 0.0000 | 0.0000 | +0.0000 |
| COAL_PRB | 0.0000 | 0.0000 | +0.0000 |
| CT_CHP | 1.6839 | 1.6841 | +0.0001 |
| CT_PEAKER | 1.3179 | 1.3432 | +0.0253 |
| OTHER | 1.9483 | 1.9483 | +0.0000 |
| ST_CHP | 1.4469 | 1.4504 | +0.0035 |
| ST_GAS | 9.3331 | 9.3673 | +0.0342 |
| biomass | 0.6724 | 0.6724 | +0.0000 |
| hydro | 24.0589 | 24.0589 | +0.0000 |
| import | 19.3577 | 19.3677 | +0.0100 |
| nuclear | 28.3416 | 28.3416 | +0.0000 |
| oil | 1.2835 | 1.2859 | +0.0024 |
| solar | 0.9813 | 0.9813 | +0.0000 |
| wind | 7.0487 | 7.0487 | +0.0000 |
| **TOTAL** | **153.2063** | **153.2023** | **−0.0040** |

The footprint is confined to the gas/oil merit order — the fuel-price channel the
mechanism claims. Every zero-marginal-cost and pinned class (hydro, nuclear, wind,
solar, biomass, OTHER) is byte-identical, and total energy moves −0.004 TWh
(−0.003 %), i.e. balance is preserved.

**BTM basis** — from `btm.parquet`, which reports **model `btm_twh` against
`btm_bench_twh`**, not a grid-delivered class total: CC_CHP 1.417696 /
1.417696, CT_CHP 0.000000 / 0.000000, ST_CHP 0.338005 / 0.338005 — model equals
benchmark on all three rows. These are behind-the-meter carve-outs that sit
*outside* the grid-delivered class TWh tabulated above.

## 5. Legitimacy diagnostics

| diagnostic | arm | keeper | note |
|---|---|---|---|
| D-1 diurnal shape | **PASS** (6 rows, 0 failures) | PASS | — |
| D-2 forced-energy attribution | **PASS** (9 rows, 0 failures) | PASS | CC_REGULAR forced share 0.0046 vs 0.30 limit; CT_PEAKER 0.0000 vs 0.15 |
| D-4 off-window binding | **FAIL** (23 rows, 1 failure) | FAIL (5 failures) | inherited — see below |
| D-5 forecast/backcast parity | **PASS** (12 rows, 0 failures) | PASS | every overlay declared |
| D-9 overlay quarantine | **PASS** (5 rows, 0 failures) | PASS | — |
| D-10 free-class rescore | **PASS** (2 rows, 0 failures) | PASS | wind/solar delivered-pinned, advisory-only |

**The single failing D-4 row:**

> 2025 `reliability_floor × ST_GAS`: plant 8006 is floored for 0.0011 TWh (0.1 % of
> the mechanism's forced energy) while its own measured median output over the 19
> hours the floor actually binds for it (inside h0-23) is 0.000 MW (52.6 % of them
> at zero) — the meter says it is offline in at least half the hours the floor
> asserts it must be online (per-unit conduct rider).

**This is INHERITED, not arm-introduced.** The committed keeper carries the
identical plant-8006 `reliability_floor × ST_GAS` row for 2025 (0.0010 TWh, 17
binding hours, 58.8 % at zero), among 5 D-4 failures across its three years. The
arm neither creates nor repairs it; the row is a pre-existing per-unit conduct
rider on the reliability floor and is the parent's to carry forward or route.
The replay emitted `WARNING: legitimacy diagnostics gate FAIL on the replayed
bundle` for this reason — the artifact was still written, and C7/C8 score from its
contents.

## Judgement

The arm reproduces the prior solve on the quantity that identifies it (Δ LW price
+0.1504 vs +0.1501), its footprint is confined to the fuel-path classes it claims,
its internal December control moves ~0, its price tail is unmoved, and it
introduces no new diagnostic failure. **No structural objection to promotion from
this shard.** The parent owns composition, scoring, the config-partition check and
registration.

## Artifacts pushed

Staged at `shard-artifacts/nyiso223/2025/` — deliberately **not** under
`results/calibration/`, so the Class-E parity sweep (which scans only committed
`results/calibration/*` bundle dirs) cannot go red. The parent moves these into the
composite and deletes the staging copy at registration.

| file | bytes |
|---|---|
| `meta.json` | 14,764 |
| `run_config.json` | 43,063 |
| `legitimacy_diagnostics.json` | 21,248 |
| `btm.parquet` | 3,339 |
| `hourly/system_2025.parquet` | 874,454 |
| `hourly/class_hourly_2025.parquet` | 440,552 |
| `hourly/class_band_hourly_2025.parquet` | 245,273 |
| `hourly/storage_2025.parquet` | 98,640 |
| `hourly/reserve_family_2025.parquet` | 54,127 |
| **total** | **1,795,460 (1.80 MB)** |

`metrics.json` and `calibration_attestation.json` are **absent by construction** —
`replay_keeper.py` does not score, so it never writes them. Scoring is the
parent's step.

## Retention (rule 31 `[R-RETAIN]`)

The full solved bundle `results/calibration/nyiso223_gapfill_2025/` (~44 MB,
including `dispatch/2025_P1.parquet` at 21.2 MB, `hourly/unit_hourly_2025.parquet`
at 18.3 MB, `flows.parquet`, `storage.parquet`, `system.parquet` and
`floors/2025_P1.npz`) **remains on this shard's local disk — nothing was
deleted.** It does not survive container reclamation. The slim set above is what
survives, via this push. If the parent needs the unit-level or dispatch-level
artifacts for registration, it must say so before this container is reclaimed;
otherwise reproducing them costs a ~6.5-minute re-solve of this year.
