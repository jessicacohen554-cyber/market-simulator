# RESULT — SPP EIA-930 stale-snapshot repair (lane UC-SPP-DATAFIX, 2026-10-18)

Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) under owner rulings **R22** (demand, zonal weights,
interchange) and **R23** (wind, solar), desk log r20. Base `main` `564cc5e0`. **Zero LP.** DATA PROFILE: spp + shared.
Evidence: `FINDING-spp-south-demand-flatruns-2026-10-18.md` (#7284), `ucmilp/FINDING-spp-south-scarcity-2026-10-18.md` (#7285).

## 0. Answer

- **Mask.** Exact-repeat runs of ≥ 4 h (`SPP_STALE_RUN_MIN_HOURS`) in SWPP `Demand` or the 17-sub-BA vector. Count: **828 / 47 / 142 / 9 / 36 / 510 / 698 h** in 2019–2025, identical to FINDING §2.
- **Measured replacements** in those hours, each a new curated datatype:
  - load and zonal weights ← SPP HOURLY_LOAD (`iso-area-load`);
  - interchange ← seam legs from both reporting sides (`counterparty-interchange`);
  - wind / solar ← SPP GenMix (`iso-genmix`), on each column's own frozen hours.
- **Load leg reproduces FINDING §4.** 13 of 14 zone-years exact; 2021 South +268 vs +269 GWh (rounding).
- **"Before" equals the keeper bundle's demand** to 0.000 MW in every zone-hour.
- **No measured replacement exists in 545 hours. Desk rulings apply there** (UC-DESK, inside R22 / R23: measured beats stale beats estimated; never interpolate). Each is declared in `constants.py` and flagged per hour in `data/uc_spp_datafix_2026_10_18/stale_snapshot_provenance.csv`. Details in §5.
  - SPC leg omitted: 336 / 24 / 179 h (2019 / 2024 / 2025).
  - SWPP's stale TI kept: 1 h (2019, MISO leg unreported on both sides).
  - EIA's stale wind / solar kept: 8 h (2019, GenMix blank).
  - Any other gap raises.

## 1. What changed

| Piece | Where |
|---|---|
| Detector (exact-repeat runs; a vector freezes only when every column does) | `src/market_sim/data/stale_runs.py` |
| Threshold, cited to FINDING §0/§2 (a detector definition, not a knob) | `constants.SPP_STALE_RUN_MIN_HOURS = 4` (declared, moves no key) |
| Repair registry (`STALE_SNAPSHOT_SPECS = {"SPP": …}`, identity for any other ISO) | `src/market_sim/data/stale_snapshot.py` |
| Hooks | `_load_spp_hourly_demand`, `load_zone_weights`, `spp_net_interchange`, `load_eia_hourly_renewable_gen`, `commitment_demand.forecast_and_actual_mw` (the UC actual) |
| Datatypes (schema, per-ISO registry `scripts/lib/<dt>/spp.py`, `curate_<dt>.py`, `regenerate_clean` + SPP solve profile) | `iso-area-load`, `counterparty-interchange`, `iso-genmix` |
| Raw intake (keyless EIA bulk, one pass, DIBA = SWPP) | `data/raw/eia-930-interchange/SWPP counterparty interchange hourly.parquet`; producer `scripts/data/fetch_eia930_counterparty_interchange.py` |
| Effect probe (zero LP) | `scripts/probes/spp_stale_snapshot_effect.py` |

**Fuel-mask rule.** A frozen `NG: WND` / `NG: SUN` run is masked when its value is nonzero, or when it falls inside the demand mask.
- Why the exception: night solar is a real 0 MW for ≥ 4 h, so a plain exact-repeat screen would flag every night.
- Why the demand-mask condition: inside a whole-record freeze, a frozen zero is the snapshot's own value.

**Interchange rule.** For each counterparty and hour, use the counterparty-reported leg; if absent, use SWPP's own.
- A leg that neither side reports, counted from its first report onward, is a residual.
  - A ruled-omittable leg (`SPP_STALE_OMITTED_LEGS = ("SPC",)`) is left out and flagged.
  - In a ruled hour (`SPP_STALE_KEPT_INTERCHANGE_HOURS_UTC`), SWPP's stale TI is kept and flagged.
  - Any other residual raises. Nothing is estimated.
- SIKE has no leg before 2025-06-01 because it was not yet a BA. That is structural, not a residual.

**GenMix gaps.** A masked hour with blank GenMix keeps EIA's stale value only inside a ruled window (`SPP_STALE_KEPT_RENEWABLE_WINDOWS_UTC`). Anywhere else it raises.

**Commitment-demand consistency.** The UC increment (MTLF − actual) now uses the repaired actual. Without this, the 2025-12-21 slack hours would pair a repaired P1 load with an increment of −4.4 to −5.9 GW, which is MTLF against the frozen 37,455 MW. Repaired, the increment is +0.16 to +0.31 GW.

## 2. Effect table (zero LP; before = keeper inputs, after = this PR)

Demand = `load_demand("SPP", y)` (weights × (load + interchange)). Interchange is the measured legs, with residual legs left out.

| Year | Zone | Masked h | Energy TWh before → after | ΔGWh | Peak MW before → after | Mean / max \|Δ\| in masked h (MW) |
|---|---|---|---|---|---|---|
| 2019 | North | 828 | 139.1 → 139.1 | +46 | 26,385 → 26,385 | 1,286 / 6,504 |
| 2019 | South | 828 | 132.7 → 133.0 | +310 | 25,487 → 25,487 | 1,186 / 6,868 |
| 2020 | North | 47 | 135.4 → 135.5 | +39 | 25,954 → 25,954 | 1,144 / 2,682 |
| 2020 | South | 47 | 127.1 → 127.2 | +54 | 24,035 → 24,035 | 1,280 / 3,432 |
| 2021 | North | 142 | 140.9 → 141.3 | +431 | 27,455 → 27,455 | 4,071 / 11,193 |
| 2021 | South | 142 | 128.8 → 129.0 | +260 | 24,686 → 24,686 | 3,150 / 9,143 |
| 2022 | North | 9 | 149.2 → 149.2 | +3 | 27,584 → 27,584 | 532 / 1,164 |
| 2022 | South | 9 | 138.8 → 138.8 | +4 | 25,999 → 25,999 | 744 / 1,244 |
| 2023 | North | 36 | 146.5 → 146.5 | +14 | 28,552 → 28,552 | 1,472 / 4,047 |
| 2023 | South | 36 | 138.0 → 138.1 | +15 | 26,755 → 26,755 | 1,433 / 4,739 |
| 2024 | North | 510 | 149.2 → 149.4 | +158 | 27,844 → 27,844 | 991 / 3,588 |
| 2024 | South | 510 | 141.7 → 141.8 | +77 | 26,323 → 26,323 | 1,125 / 4,954 |
| 2025 | North | 698 | 153.9 → 153.7 | −239 | 29,509 → 29,509 | 1,549 / 7,930 |
| 2025 | South | 698 | 147.9 → 147.5 | −383 | 27,837 → 27,837 | 1,925 / 7,181 |

**Load-leg check against FINDING §4** (§4 method: load leg repaired, interchange interpolated across each run). ΔGWh North / South, this PR vs FINDING:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| this PR | +278 / +520 | +45 / +59 | +440 / +268 | +2 / +3 | +9 / +11 | +158 / +77 | −176 / −319 |
| FINDING | +278 / +520 | +45 / +59 | +440 / +269 | +2 / +3 | +9 / +11 | +158 / +77 | −176 / −319 |

Interchange is mean MW in masked hours. Wind and solar use each column's own masked hours.

| Year | Interchange before → after | Residual legs (h) | Wind masked h | Wind TWh (ΔGWh) | Solar masked h | Solar TWh (ΔGWh) |
|---|---|---|---|---|---|---|
| 2019 | +139 → +71 | SPC 336 omitted; stale TI kept 1 h | 828 (8 stale kept) | 77.03 → 74.53 (−2,503) | 1,186 (8 stale kept) | 0.53 → 0.49 (−43) |
| 2020 | +105 → −48 | — | 46 | 82.03 → 81.96 (−74) | 98 | 0.56 → 0.56 (+3) |
| 2021 | +41 → +628 | — | 142 | 92.86 → 93.47 (+613) | 279 | 0.54 → 0.54 (+0) |
| 2022 | +908 → +1,053 | — | 0 | 107.44 → 107.44 (0) | 45 | 0.54 → 0.54 (+0) |
| 2023 | +307 → +800 | — | 33 | 103.05 → 103.11 (+64) | 92 | 0.59 → 0.59 (−2) |
| 2024 | +265 → +494 | SPC 24 | 261 | 109.32 → 109.51 (+191) | 613 | 1.20 → 1.20 (−1) |
| 2025 | +72 → +277 | SPC 179 | 671 | 110.46 → 110.62 (+167) | 1,264 | 2.35 → 2.10 (−250) |

- **Wind** masked hours equal FINDING §2's `NG: WND` column.
- **Solar** masked hours exceed the demand mask. The extra hours are EIA's constant small night prints (1–12 MW) and genuine solar-only freezes (e.g. 245 MW held for ~10 days in 2025). The 2025 −250 GWh is mostly the December freeze, which carries a 13:00 solar value through the nights.
- **2019 wind / solar** keep EIA's stale value in the 8 GenMix-blank hours (ruling iii, §5).

No peak moves in any zone-year. Annual demand energy moves ≤ 0.4 %. What matters is the hourly error in the masked hours: a mean of 0.5–4.1 GW.

## 3. Rule 14 — boundary and basis

Ratios are measured in hours outside the mask.

| Series | Replacement / EIA-930 | Note |
|---|---|---|
| Load (Σ 17 HOURLY_LOAD areas vs SWPP `Demand`) | 1.000–1.003 (2023 reads 0.988 only because the raw frame keeps the 3.6 TW 2023-06-12 unit slip; excluding that hour gives ≈ 1.000); median \|Δ\| 64–101 MW | Same 17 tokens as `_SPP_SUBBA_ZONE_GROUPS`. No reconciliation needed (FINDING §3). |
| Interchange (−Σ counterparty legs + own SPC vs BA `Total interchange`) | +25 to +76 MW mean above TI; corr 0.994–0.997 (2019–23), 0.96 (2024), 0.76 (2025, from SWPP's own impossible SPC/WACM prints) | EIA's BA TI is imbalance-adjusted. Sum-of-legs is the measured seam flow. The basis gap is stated, not reconciled. |
| Wind (GenMix Market + Self vs `NG: WND`) | 0.999–1.010 | Both are the SPP Eastern BAA. |
| Solar (GenMix vs `NG: SUN`) | 1.02–1.10 | GenMix solar reads 2–10 % above EIA's. The absolute is small (0.5–2.4 TWh/yr). Applied only in masked hours. Stated as a basis misalignment. |

## 4. Rule 23 — derived profiles that read these series

| Profile | Reads | Action |
|---|---|---|
| `data/raw/reference/spp_curtailment_share.csv` (`derive_spp_curtailment_share.py`) | `load_demand` + renewable gen (net-load deciles, 2023–25) | **Re-derived in this PR.** The source change is this repair. `--check` with the repair unregistered reproduces the committed table exactly (max \|Δ\| 0). With the repair, 856 cells (was 866), max \|Δ\| 0.177. Not read by the keeper (`spp_curtailment_ceiling: false`). Its level `spp_curtail_depth_wind = 0.288137` was centred on the old shape and is **not** re-fitted here; that belongs to whichever lane arms the ceiling. |
| `zonal-shares` clean partition | sub-BA demand | Not re-derived. The repair applies downstream, in `load_zone_weights`, so clean and raw-fallback paths are both repaired once. |
| `load-forecast-error` SPP forward profile (`derive_load_forecast_error.py`) | `forecast_and_actual_mw` | Re-derives on regenerate (gitignored, in no key); epoch 2026-10-18b covers it. |
| `demand-profile` clean (`load_demand_meta`) | `load_demand` | Re-derives on regenerate (gitignored). |
| `campd-partial-outages-netloadmask-SPP.csv`, `scripts/lib/outage_detect.py` | the **raw** SWPP frame | Unchanged: these read the raw frame, not the repaired loaders, so their source did not change. Stated as a residual consumer (0 rows today). |
| e930 benchmark actuals (`load_eia_hourly_benchmark`) | raw frame | Unchanged. Scoring is untouched (rule 37). Re-basing the benchmark is a desk / rubric question. |

## 5. Desk rulings applied (UC-DESK, inside R22 / R23)

Principle: measured beats stale beats estimated; never interpolate. Each ruling is a declared gap in `constants.py`, and any other gap raises.

| | Hours | Treatment | Stated bound / error range |
|---|---|---|---|
| (i) SPC (SaskPower) leg unreported on both sides | 336 / 24 / 179 (2019 / 2024 / 2025) | leg omitted from the sum; flagged | ~150 MW DC tie (SWPP-reported \|SPC\| p99 105–158 MW): ≤ 150 MW/h, ≤ 0.05 TWh/yr; expected ≈ 6 / 1 / 12 GWh |
| (ii) MISO leg unreported on both sides, 2019-12-14 01:00Z | 1 | EIA's stale SWPP total interchange kept; flagged | not tie-bounded (neighbours +566 / +432 MW), so not omitted |
| (iii) GenMix blank, 2019-03-29 09:00–16:00Z | 8 | EIA's stale wind and solar kept; flagged | wind: GenMix bracket 8,676 → 6,469 MW vs stale 9,493; solar: 0 → 202 MW vs stale 0 |

- The 2019 SPC count is 336, not 337: in the MISO hour the whole stale TI is kept, so SPC is not separately omitted.
- Provenance (every masked hour: demand / interchange / wind / solar source, omitted legs): `docs/records/spp/data/uc_spp_datafix_2026_10_18/stale_snapshot_provenance.csv`.
- **DOF-ledger note:** `scripts/build_dof_ledger.py::data_qa_entries` writes it for any SPP bundle solved under epoch 2026-10-18b. It covers the residuals above and the rule-14 basis gaps (§3). The current keeper's ledger is unchanged (`--check`: current).

## 6. Re-key and G-DRIFT

- **SolveEpoch `2026-10-18b`**, `isos=("SPP",)`, both modes. Ledger entry in `results/cache.py`.
  - The clean partitions are in no key; the epoch carries the change.
  - Forecast configs are included because a forecast reads history-year inputs. Over-invalidation is the fail-safe side.
  - The new constant is declared at its landing hash and moves no key.
- **G-DRIFT.**
  - The SPP keeper (`closeout_spp_nuc_span`) is **LIVE**: its demand, zonal weights, interchange and wind/solar inputs change in the masked hours. A promotion needs a full-span re-solve (rule 16 / 29).
  - **Every other ISO is INERT.** The registry holds SPP only; each repair returns its input object unchanged for any other ISO (tested). Every hook is a registry lookup, with no `if iso ==` branch.

## 7. Tests

| File | Covers |
|---|---|
| `tests/unit/data/test_stale_runs.py` (12) | trivial cases; 3 / 4 / 5-h boundaries; first-hour counting; NaN breaks a run; partial-vector freeze not flagged |
| `tests/unit/data/test_stale_snapshot.py` (26) | masks; sub-BA-only trigger; night-zero carve-out; demand / weights / interchange (counterparty first, own fallback, pre-existence) / renewable repairs; ruled omission, ruled stale-kept hour and ruled GenMix window, each flagged in the provenance; an unruled residual, a missing partition and a masked hour without replacement each raise; 8 other ISOs bit-identical |
| `tests/scoring/test_build_dof_ledger_stale_snapshot.py` (2) | the DOF note appears only for an SPP bundle under epoch 2026-10-18b |
| `tests/test_curate_stale_snapshot_sources.py` (8) | tmp-CLEAN_DIR curation of all three datatypes: zip-over-CSV dedupe, local-year partitions, sign flip, fall-back-hour localization, interval-end hourly means |

## 8. Reproduce

```
uv run python scripts/data/fetch_eia930_counterparty_interchange.py --diba SWPP --years 2019 2020 2021 2022 2023 2024 2025
uv run python scripts/regenerate_clean.py --solve-profile SPP
uv run python -m scripts.probes.spp_stale_snapshot_effect --out /tmp/effect.json --provenance /tmp/provenance.csv
PYTHONPATH=.:src uv run python scripts/data/derive_spp_curtailment_share.py --check
```
