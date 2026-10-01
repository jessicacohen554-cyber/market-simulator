# PRECOMMIT R-NWPP: re-solve NWPP 2019–2025 on corrected backcast inputs (2026-09-24)

**Charter:** `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.5. Owner instruction
(2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage, plant-specific heat rates,
and granular CAMPD outage data. **Precondition met:** F1 (#6572) and F2 (#6569) are merged; the lane is cut from
`9210075392a128d14a5efb168ab1f9955a9b6946`.
**Parent:** zero LP (rule 32(a)). **Control:** keeper `2026-09-24-nwpp-49-ror-split`
(`results/calibration/nwpp49_ror_span`, basis `c2d5991c`), rule 29(b) form 4 for 2023–2025. 2019/2021/2022 have
no control, because NWPP has never solved them.
**Probes (committed):** `scripts/probes/_rnwpp_census.py` → `results/calibration/_rnwpp_census.json`; the mid-vintage
carry census → `results/calibration/_rnwpp_midvintage_census.json`.

## 0. In one line

**Six year-isolated shards: 2019, 2021, 2022, 2023, 2024, 2025. 2020 is DATA-BLOCKED.** EIA's own BALANCE archive
has no PSEI demand for 8,659 of 8,784 hours of 2020. The recipe is the keeper's recipe with the F1 flags pinned ON,
the F2 short-coal and unit-partial families armed, short-gas left OFF, and `mid_vintage_exit_carry` armed. The
offer-curve multipliers are unchanged (sha256 below).

## 1. Registered years (rules 34(c) / 35(b))

The union of `years` over every NWPP registry sidecar is **{2023, 2024, 2025}**. There is one sidecar,
`2026-09-24-nwpp-49-ror-split`, and no touchpoint folded to it. The target is 2019–2025.

## 2. Phase 0 found that NWPP could not solve 2019–2022 at all. Zero-LP intake landed here

| gap (pre-lane) | effect on a 2019–22 solve | fix in this lane (zero LP) |
|---|---|---|
| The 17 member `<BA> hourly.parquet` extracts covered 2023–25 only. | `load_demand` **raises** ("No EIA-930 data for ISO 'NWPP' in year 2019"). | Re-ran `build_nwpp_ba_hourly_from_balance.py --all-nwpp --force --year 2019..2025` from the **committed** BALANCE archive. Every BA-year reconciles with zero residual, raw and `(Adjusted)`. **Every committed 2023–25 row is byte-identical** (all 17 files, row-for-row). The pool reproduces the keeper peaks of 49,290 / 52,564 / 50,953 MW. |
| `GRID interchange hourly.parquet` covered 2023+ only. | `nwpp_grid_carried_wind_served` reads 0.0 for the Southwest legs **with no warning**, so served export is off by about 2 TWh/yr. | `fetch_eia930_interchange.py --ba GRID --source bulk --years 2019..2022 --merge` (keyless). 97,921 rows added; the committed 2023–26 rows are byte-identical. |
| `CALIBRATION_YEARS_BY_ISO["NWPP"] = (2023, 2024, 2025)` | No 2019–22 benchmark block, so the scorer reads `{}`. | Set to `(2019, 2021, 2022, 2023, 2024, 2025)`, then `build_calibration_reference.py --isos NWPP`. NWPP 2023–25 blocks, every other ISO's block and `egrid_benchmark` are byte-identical. |
| **F1's NWPP measured heat-rate artifacts were derived without the F2 raw CAMPD** for WA/OR/UT/WY/ID 2019–22. Only NV/MT plants had 2019–22 rows (coal 4 of 12, CC 7 of 22, CT 4 of 10, ST 3 of 6). | Every other plant fell back in 2019–22 to a pooled row built from 2023–25 hours only. | Re-ran the four derives `derive_campd_{ct,coal,cc,gas_st}_heat_rates.py --iso NWPP`. **Rule 23 data change:** F2's raw landing (commit `d9cf24a2`). Now every plant has a row in every year 2019–25 (coal 13 incl. Boardman, CC 22, CT 10–11, ST 6). CT / coal / CC 2023–25 per-year rows are byte-identical. ST 2023–25 rows move slightly, because the ST capacity pairing is identified once on the pooled hours (F1 design); for example Jim Bridger's pooled rate goes 10.35 → 9.99. The CHP artifact re-derives identically (0 diffs) and was not rewritten. |

**The same F1 artifact gap applies to SOCO** (AL/GA 2019–22). That is routed to R-SOCO and not touched here.

## 3. Census (fleet-only `run_year`, keeper recipe; `pre` = F1 flags at the keeper's recorded values, `arm` = §4)

`class-table` uses the audit's §3a heuristic (loaded rate equals a `HEAT_RATE_BINS` value). The **exact** residual is
F1's: Payson 7408 (9.2 MW, no eGRID rate in any vintage) and U. Montana CHP 69880 in 2025. The heuristic's
other hits are simple-cycle floor-clamp coincidences: Port Westward 2 (reciprocating engines, 224 MW) and
Yellowstone County (2024+).

| year | EIA-860 source (arm) | thermal MW pre → arm | class-table MW (share) pre → arm | std win / GWh | short-coal | partial | short-gas (NOT armed) |
|---|---|---|---|---|---|---|---|
| 2019 | vintage_2019 | 27,645 → 27,492 | 419 (1.52 %) → 251 (0.91 %) | 691 / 38,988 | 112 / 2,792 | 32 / 1,793 | 1,603 / 9,875 |
| 2020 | vintage_2020 | 27,645 → 25,565 | 419 (1.52 %) → 248 (0.97 %) | 708 / 48,128 | 86 / 2,071 | 31 / 1,572 | 1,647 / 9,925 |
| 2021 | vintage_2021 | 27,649 → 26,171 | 424 (1.53 %) → 234 (0.89 %) | 658 / 34,694 | 104 / 2,504 | 43 / 1,740 | 1,638 / 8,729 |
| 2022 | vintage_2022 | 27,645 → 26,528 | 419 (1.52 %) → 234 (0.88 %) | 731 / 41,405 | 95 / 2,360 | 18 / 661 | 1,913 / 10,116 |
| 2023 | vintage_2023 | 27,645 → 26,529 | 419 (1.52 %) → 234 (0.88 %) | 719 / 38,206 | 70 / 1,215 | 52 / 1,396 | 1,114 / 6,658 |
| 2024 | vintage_2024 | 27,645 → 27,065 | 419 (1.52 %) → 404 (1.49 %) | 790 / 41,029 | 61 / 1,068 | 37 / 1,029 | 1,053 / 7,253 |
| 2025 | canonical 2025ER | 27,644 → 27,644 | 418 (1.51 %) → 418 (1.51 %) | 761 / 52,591 | 78 / 1,885 | 22 / 824 | 622 / 5,830 |

**What moves** (capacity-weighted loaded heat rate, pre → arm):

* **CT_PEAKER: 8.90 → 10.7–11.1 MMBtu/MWh in every year.** This is the largest offer-side change. The measured
  CT rates replace eGRID.
* CC_REGULAR: 7.35 → 7.31–7.40.
* COAL: ±0.05.
* ST_GAS: 12.01 → 11.19–12.69.

**Retirements are now present:**

* **Colstrip 1–2** (+614 MW) are in 2019 only. CAMPD confirms the last generation on 2020-01-02/03.
* **Centralia 1** (+656 MW) is in 2019.
* **Jim Bridger 1–2** are coal through 2023. This is NWPP-51's fuel switch.
* **North Valmy 1** is coal through 2024.

**Boardman** (retired 2020-10-15) is carried by `mid_vintage_exit_carry` (§4) in 2020.

**Hermiston Power 55328** (629 MW CC) is outside NWPP in 2019–2020. Its BA was `CSTO` in those EIA-860 vintages
and became `GRID` from 2021. The EIA-923 benchmark keys on the same year-native `ba_code`, so the fleet and the
benchmark agree. Its output enters the model as measured interchange. Nothing is changed.

## 4. The recipe (per shard; offer curves UNCHANGED, rule 1(c))

```
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/replay_keeper.py results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/rnwpp_<Y> --years <Y> \
  --set eia860_vintage_tracks_solve_year=true \
  --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true \
  [<Y> in 2019, 2021, 2022 ONLY:] --set hydro_backfill_year=null
```

* **F1 flags are pinned explicitly**, never read from the ambient default. That way the recorded `run_config` states
  them.
* **Short-coal and unit-partial are armed.** Both cells are U, and both F2 files are non-empty in every year (table
  above).
* **Short-gas is NOT armed** (the F2 lane note). The detector's merit guard separates **nothing** on NWPP's panel:
  * `campd-unit-outages-layup-shortgas-NWPP.csv` is **header-only**, so zero of 9,590 windows were booked as
    economic layup across all seven years. The same companion carries 358 (CAISO), 529 (PJM) and 2,760 (SPP)
    windows elsewhere.
  * **Clark (2322) is 6,488 of 9,590 windows (68 %)**, about 50 windows per unit per year on 24 small units. That
    is the signature of daily economic cycling in a hydro-dominated system, not forced outage.
  * The 2019–22 → 2023–25 fall (1,600–1,900 → 600–1,100) tracks Clark's own count (1,186 / 1,090 / 1,179 / 1,431
    → 748 / 648 / 206).
  * Arming it would remove about 7–10 TWh/yr of gas availability on the say-so of a guard that has not
    discriminated. The cell stays U and gets this evidence.
* **`mid_vintage_exit_carry` is armed** (the SPP keeper's K mechanism, zero DOF). It completes the vintage
  channel: a vintage operable sheet is a year-end snapshot and drops a plant that retired **during** the year.
  * Measured NWPP footprint: 2020 Boardman +3.93 TWh available and eBay +0.04 TWh; 2021 Alden Bailey +0.07 TWh;
    **2019 / 2022 / 2023 / 2024 zero**.
  * SPP-48's "zero NWPP exposure" pre-dated F1's NWPP retiree-channel repair.
* **`hydro_backfill_year=None` for 2019 / 2021 / 2022** (rule 14).
  * The keeper's `2024` backfill injects every plant that reported in 2024 but not in year Y, at its 2024 energy:
    38 / 310 / 156 GWh. Before 2023 that includes plants not yet built.
  * The field exists for the 2025 early-release file.
  * 2023–25 keep the keeper's value, so the recipe differs by year on this one input field only.
  * `stamp_config_partition.py` records the partition at composition.
* **2019 carries a 192-hour PSEI demand bridge.** 384 missing hours in 4 runs are linearly interpolated by the pool
  frame's own member fill, about 0.2 % of the year's demand. This is reported, not repaired.
* **The hydro cascade is INERT in 2019 / 2021 / 2022.** `nwpp_hydro_cascade_monthly.csv` is 2023–25, and the loader
  logs "mechanism INERT". Restoring it needs a CROHMS 2019–22 fetch plus edits to two builders with hard-coded
  years (`build_nwpp_hydro_budget.py:86`, `build_nwpp_hydro_cascade.py:156/175`). That is a separate intake lane,
  stated here rather than hidden: **2019/21/22 therefore run the keeper's hydro structure minus the Columbia/Snake
  coupling.** Envelope, min-flow floor and RoR split read own-year data.

**Offer-curve band multipliers:** `offer_curve_by_group` sha256
`ac3344c3ef16e3ae63673a92886aa2873fc7090543eb04e6d6abf89fb52c73c2` (keeper `run_config_2023.json`). Must be identical
in every leg. `authorized_price_tuning`: NONE (price unscored, rubric v3.8).

## 5. G-DRIFT (keeper `c2d5991c` → `92100753`), rule 29(b)

* **INERT for NWPP:**
  * `coal_fuel_inventory*` (miso-268: default-off, absent from the recipe).
  * `campd_dark_unit_year_windows` (SOCO-61: default-off, needs `campd_per_unit_attribution`).
  * `forecast_parity_registry.py` (forecast-only).
  * PJM RGGI 2020–22 (`capacity_market.py`, `fuel_trajectories.py`; another ISO's branch).
  * `lp/model.py` (an import-cycle refactor, no numeric change).
  * `storage_compare.py` (report-only).
  * `campd.ISO_MERIT_PANEL_STATES` (deriver-only, SPP/SOCO).
  * `runner.py` (forecast path).
* **LIVE by design (this lane's object):**
  * The F1 hunks: `egrid.py` year-matched join, `fleet/eia860.py`, `fleet/campd_bins.py` per-year reader,
    `chp.py`, `heat_rate_years.py`, the `scenarios.py` defaults and coercion, the `cache.py` epoch, and the F1 CLI
    plumbing in `run_calibration*.py`.
  * The F1 data: the canonical EIA-860 `heat_rate` is now eGRID 2024, and every vintage is rejoined.
  * The F2 extract extensions (2019–22 rows only; 2023–25 identical).
  * This lane's intake (§2).
* **Consequence:** 2023–25 are not a pure A/B against the keeper. The eGRID-2024 canonical rejoin moves heat rates
  even at the keeper's flag values. This is why §3 reports `pre` at HEAD rather than claiming keeper identity.

## 6. Shard hard stops (each shard checks; any miss = STOP, no push)

1. `git rev-parse HEAD` equals the pinned SHA.
2. The input sha256 matches:

   | file | sha256 |
   |---|---|
   | `campd-unit-outages-NWPP.csv` | `73f1b0e8…` |
   | `-short-NWPP` | `d53d6c7b…` |
   | `campd-partial-outages-NWPP.csv` | `e5060145…` |
   | `campd_ct_heat_rates_NWPP.csv` | `b5c09a91…` |
   | `_coal_` | `5181a733…` |
   | `_st_` | `b4a74339…` |
   | `_cc_` | `ca5c43bf…` |
   | `chp_power_only_heat_rates_NWPP.csv` | `71beb192…` |
   | `PSEI hourly.parquet` | `545e8df5…` |
   | `BPAT hourly.parquet` | `47a23eeb…` |
   | `GRID interchange hourly.parquet` | `c7ef6c41…` |

   The full hashes are in the shard prompt.
3. After the solve, `run_config_<Y>.json` `scenario_config` shows the §4 flags true and
   `unit_outage_short_windows_gas` false. `hydro_backfill_year` is null for 2019/21/22 and 2024 for 2023–25. The
   `offer_curve_by_group` sha256 is as above.
4. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/`, `metrics.json`, `run_config_<Y>.json`, `meta.json`,
   `legitimacy_diagnostics.json`.

## 7. Reported, never gated

* C1–C8 per year against the keeper (2023–25).
* Class TWh deltas.
* Coal r.
* The 2023 CC_REGULAR C1 row (keeper −7.213 vs ±8.00). NWPP-51 predicts that the JB coal restoration pushes it
  toward FAIL, on the open demand-basis gap (FINDING-nwpp-45 §8).
* Price is UNSCORED (rubric v3.8).

**Overlap noted:** NWPP-51 (vintage-only A/B, 2023–25) is a strict subset of this arm. Neither result is selected by
the other.

## 8. Cost and retrievability

* Six shards in parallel, about 60–100 min each (FINDING-nwpp-50 §3), so about 1.5–2 h wall.
* Each shard pushes its full bundle to its own branch (rule 34(a)).
* The parent composes and registers what must survive on `main` (rule 33(f)).
* 2020 needs a measured PSEI 2020 hourly load, for example FERC Form 714, before it can be solved.
