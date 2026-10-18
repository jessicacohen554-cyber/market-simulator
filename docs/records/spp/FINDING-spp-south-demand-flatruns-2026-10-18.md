# FINDING — SPP zonal demand flat runs (lane UC-SPP-DEMAND, 2026-10-18)

Chartered by UC-DESK under owner ruling R21 (`docs/uc-milp-program-plan-2026-10.md` §8.1; desk r19; main `4dc8d97d`).
Zero LP, no `src/` or `data/` change. DATA PROFILE: spp (+shared). Flag: UC-5-SPP RESULT (PR #7282) — all 2025 SPP
unserved sits in a 155-h stretch where SPP-South demand is flat at 18,597 MW.

## 0. Answer

**The flats are in EIA-930's own SWPP data, not in our fill.** For stretches of hours EIA-930 repeats one stale
snapshot for the whole SWPP record: system `Demand`, `Net generation`, `Total interchange`, every `NG:` fuel column
and all 17 sub-BA demands freeze together (the `Demand forecast` column keeps moving). Our pipeline passes them
through unchanged. SPP's own measured load — `HOURLY_LOAD` by the same 17 sub-BA tokens, and the MTLF
`Averaged Actual` — varies normally through every one of these hours. In the 2025-12 stretch the stale value
overstates SPP-South load by 2.5 GW on average against SPP's own load (up to 4.5 GW in the overnight troughs).

## 1. Trace (the series the solve reads)

| Step | Where | What happens in the flat hours |
|---|---|---|
| raw system | `data/raw/eia-930-hourly/SWPP hourly.parquet` | `Demand` 37,455, `Net generation` 37,677, `Total interchange` 273, `NG: WND` 15,786 … identical for every hour from 2025-12-15 13:00 to 12-21 (local); forecast column varies |
| raw sub-BA | `data/raw/zone-specific-demand/SPP/spp_subba_demand_*.csv` (EIA-930 sub-region six-month files) | rows **present**, all 17 sub-BAs frozen at one value (e.g. CSWS 6,473, OKGE 5,273, SPS 4,308) |
| system demand | `eia930/demand.py::_load_spp_hourly_demand` → `_eia_hourly_frame_filled` | passed through (only the >2.5× spike screen; it does not catch repeats) |
| interchange | `eia930/envelopes.py::spp_net_interchange` | passed through (frozen) |
| zonal weights | `scripts/data/curate_zonal_shares.py::parse_spp_shares` (`.ffill().bfill()` only fills absent rows, not used here) | frozen shares |
| zonal demand | `eia930/demand.py::load_demand`: `weights × (Demand + interchange)` | `0.4929 × (37,455 + 273)` = **18,596.6 MW** South, 19,131.4 North |

Verified on the keeper bundle `results/calibration/closeout_spp_nuc_span/hourly/system_<year>.parquet` (the demand
the solve actually used). The keeper itself carries **zero slack** in every year; the unserved appeared under
UC-5's commitment, where the inflated South trough load is not available as cheap headroom.

## 2. Inventory — flat runs ≥ 4 h in solve zonal demand (2019–2025)

North and South flat on the same hours in every year (the whole record freezes).

| Year | Runs | Hours | Longest | Runs ≥ 24 h (local start, length, South MW) |
|---|---|---|---|---|
| 2019 | 22 | 828 | 96 | 03-29 71 h @11,901 · 04-05 56 h · 11-22 → 12-31: 14 runs of whole-day repeats (24–96 h) cycling between two values, 13,990 and 12,825 |
| 2020 | 2 | 34 | 19 | — |
| 2021 | 7 | 141 | 62 | 08-17 62 h @15,144 · 08-22 24 h · 08-23 24 h |
| 2022 | 1 | 9 | 9 | — (sub-BA + net gen frozen; `Demand` not) |
| 2023 | 4 | 32 | 12 | — |
| 2024 | 11 | 324 | 119 | 02-12 59 h · **03-01 119 h @15,350** · 03-06 24 h · 10-17 28 h |
| 2025 | 18 | 669 | 155 | 02-18 · 03-23 · 04-10 34 h · 04-14 38 h · **05-19 109 h** · 05-26 · 06-16 · 07-10 · **10-07 82 h** · 10-11 · **12-15 155 h @18,597** · 12-22 |

Per-column freeze counts (hours in runs ≥ 4 h). The union of zonal-flat and `Demand`-flat hours is the repair mask.

| Year | zonal | `Demand` | `Total interchange` | `NG: WND` | union (mask) |
|---|---|---|---|---|---|
| 2019 | 828 | 828 | 844 | 828 | 828 |
| 2020 | 34 | 47 | 47 | 46 | 47 |
| 2021 | 141 | 142 | 142 | 142 | 142 |
| 2022 | 9 | 0 | 0 | 0 | 9 |
| 2023 | 32 | 36 | 36 | 33 | 36 |
| 2024 | 324 | 396 | 435 | 261 | 510 |
| 2025 | 669 | 698 | 702 | 671 | 698 |

Short runs (2–3 h) add ≤ 5 h/yr. SPP's own `HOURLY_LOAD` has **zero** flat runs ≥ 4 h in any zone-year.

## 3. Measured alternatives

| Source | On disk | Boundary | Check against EIA-930 sub-BA in non-flat hours |
|---|---|---|---|
| SPP `HOURLY_LOAD-YYYYMM.csv` (`data/raw/spp-hourly-load/`, 2019–2025) | yes, all 12 months each year; NaN 0–11 h/yr | **same 17 sub-BA tokens** (`CSWS` … `WR`), `MarketHour` = UTC interval end | lag 0 is best (lag ±1 roughly 5× worse); median abs. diff South 53–78 MW; solve/HL ratio 1.000–1.018 (the gap is the interchange leg plus EIA's basis) |
| SPP MTLF `Averaged Actual` (`load-forecast-vintages`, latest vintage per hour) | yes, 2019–2025 | SPP BA system | equals Σ HOURLY_LOAD to a median 0.25 MW in every year: one measurement, published twice |
| EIA-930 SWPP | — | — | frozen in the flat hours (the defect) |

**Rule 14 boundary clause:** not triggered. HOURLY_LOAD uses the very sub-BA partition `_SPP_SUBBA_ZONE_GROUPS`
maps, so the North/South split comes straight from measured data; no reconciliation is needed for the load
leg. The West/East partition (`_SPP_SUBBA_ZONE_GROUPS_WEST_EAST`) maps the same tokens.

**The interchange leg has no clean measured replacement.** SWPP's own per-neighbour EIA-930 interchange is
*absent* (not frozen) in these hours. Counterparty-reported flows are on disk only for MISO (2019–25) and ERCOT
(2023–25), about 37 % of mean |flow| (AECI 553, MISO 487, ERCO 230, SPA 220 … MW mean |flow| by neighbour).

2025-12-15 13:00 → 155 h stretch, means:

| | Solve (now) | SPP HOURLY_LOAD | Proposed |
|---|---|---|---|
| South MW | 18,597 (flat) | 16,077 | 16,389 (14,480–19,266) |
| North MW | 19,131 (flat) | — | 18,336 |
| System load MW | 37,455 (EIA, flat) | 34,060 (= MTLF actual) | — |
| Interchange MW | 273 (flat) | — | 664 (interpolated) |
| Energy Δ | | | South −342 GWh, North −123 GWh |

## 4. PROPOSAL (not landed; changes keeper inputs → owner via desk)

**Fix A (recommended, minimal).** A stale-snapshot repair at the SPP demand seam, flagged hour by hour (same
pattern as the `demand-profile` `repaired` column):

1. **Detect** (`eia930/demand.py`, a new `_screen_stale_runs` called from `load_demand` for SPP, or at
   curation): mark an hour when SWPP `Demand` or the 17-sub-BA vector repeats exactly for ≥ 4 consecutive hours.
   The threshold is structural, not tuned: a real 17-sub-BA load vector cannot repeat to the MW for 4 h, and
   SPP's own series never does (§2).
2. **Load leg:** in masked hours, zone load = Σ HOURLY_LOAD over the zone's sub-BAs (mapped with
   `_spp_utc_to_local_hoy`); zonal weights also come from HOURLY_LOAD. Needs a curated reader for
   `spp-hourly-load` (new datatype or extend `zone-specific-demand`; `data-intake` skill).
3. **Interchange leg:** owner choice — (a) linear interpolation across the run from the bracketing good hours.
   This is an estimate and must be labelled as one; flows are smaller than the load error (all-year median |TI|
   678 MW against a 1–4 GW mean masked-hour load error). Or (b) measured: −Σ counterparty-reported flows. That needs EIA-930 interchange intake for AECI,
   SPA, WACM, SIKE, PSCO, WAUW, SPC, PNM, EPE (MISO and ERCO are already on disk). Recommend (b), with (a) only as a
   labelled interim.
4. Re-key: the surface fingerprint moves for SPP only; every SPP year re-solves (rule 16). Re-check the rule-36 legs
   per year.

**Alternative B:** move SPP's whole load leg to HOURLY_LOAD (SPP's own metered data, all hours). It is cleaner in
principle but moves every hour (by the 53–78 MW basis) and needs a basis audit against the benchmark series.
Out of scope for this flag.

**Effect, Fix A with 3(a), zero LP** (before = keeper bundle demand; after = repaired, masked hours only):

| Year | Zone | Masked h | Energy TWh before → after | ΔGWh | Peak MW before → after | Mean / max \|Δ\| in masked hours (MW) |
|---|---|---|---|---|---|---|
| 2019 | North | 828 | 139.1 → 139.3 | +278 | 26,385 → 26,385 | 1,379 / 7,357 |
| 2019 | South | 828 | 132.7 → 133.2 | +520 | 25,487 → 25,487 | 1,302 / 7,711 |
| 2020 | North | 47 | 135.4 → 135.5 | +45 | 25,954 → 25,954 | 1,282 / 2,796 |
| 2020 | South | 47 | 127.1 → 127.2 | +59 | 24,035 → 24,035 | 1,421 / 3,620 |
| 2021 | North | 142 | 140.9 → 141.3 | +440 | 27,455 → 27,455 | 4,156 / 11,701 |
| 2021 | South | 142 | 128.8 → 129.0 | +269 | 24,686 → 24,686 | 3,227 / 9,344 |
| 2022 | North | 9 | 149.2 → 149.2 | +2 | 27,584 → 27,584 | 481 / 1,032 |
| 2022 | South | 9 | 138.8 → 138.8 | +3 | 25,999 → 25,999 | 689 / 1,056 |
| 2023 | North | 36 | 146.5 → 146.5 | +9 | 28,552 → 28,552 | 1,558 / 4,260 |
| 2023 | South | 36 | 138.0 → 138.1 | +11 | 26,755 → 26,755 | 1,507 / 4,975 |
| 2024 | North | 510 | 149.2 → 149.4 | +158 | 27,844 → 27,844 | 1,036 / 3,753 |
| 2024 | South | 510 | 141.7 → 141.8 | +77 | 26,323 → 26,323 | 1,153 / 4,798 |
| 2025 | North | 698 | 153.9 → 153.8 | −176 | 29,509 → 29,509 | 1,493 / 8,153 |
| 2025 | South | 698 | 147.9 → 147.6 | −319 | 27,837 → 27,837 | 1,947 / 6,829 |

Annual energy moves ≤ 0.4 % and no peak moves (no stale run falls on a peak). The hourly error is the material part:
mean 1–4 GW in the masked hours, with signs that differ run by run (stale-high in the 2025-12 troughs, stale-low
elsewhere).

## 5. Same defect, other consumers (scope note for the desk)

The frozen frame is the same `_eia_hourly_frame_filled("SWPP")` that feeds SPP wind and solar CF and the e930
benchmark actuals. `NG: WND` is frozen in 33–828 h/yr (§2), so the LP's wind bound and the scored generation
benchmark are also stale in these hours. SPP's own `GenMix_<year>.csv` (5-min, on disk under `spp-genmix/`) is the
measured alternative. Not quantified here; it needs its own lane.

## 6. Reproduce

Scratch scripts (not committed): load the keeper `system_<year>.parquet` demand, `_load_spp_hourly_demand`,
`spp_net_interchange`, `HOURLY_LOAD` monthly CSVs and zips (UTC → local hour-of-year via
`curate_zonal_shares._spp_utc_to_local_hoy`), `load_vintages("SPP", area="SPP")` with `lead_hours < 0`, latest vintage
per interval. Run detection: exact equality of consecutive hourly values, run length ≥ 4.
