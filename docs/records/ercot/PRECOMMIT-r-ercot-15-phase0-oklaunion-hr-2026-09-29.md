# PRECOMMIT — R-ERCOT-15: phase 0 on the 2019/2020 residuals, and one zero-DOF arm (Oklaunion measured heat rate)

Date 2026-09-29. Keeper `2026-09-28-r-14-oklaunion-swcap` (bundle `results/calibration/r_ercot14_span`, 2019–2025). DATA PROFILE: ercot. Written before any solve.

## 1. 2020 C3b decomposition (zero LP, keeper's committed hourlies)

C3b = RMSE of the 12 load-weighted monthly means / mean actual = 6.04 / 25.0 = **0.242** (band ≤ 0.20 needs RMSE ≤ 5.0, i.e. squared error ≤ 300 of today's 438).

| Month | Model | Actual | Δ | Share of SSE |
|---|---|---|---|---|
| Feb | 18.75 | 25.45 | −6.70 | 0.10 |
| Mar | 22.91 | 31.06 | −8.15 | 0.15 |
| Jun | 21.31 | 16.12 | +5.19 | 0.06 |
| Jul | 29.21 | 21.43 | +7.78 | 0.14 |
| Aug | 55.98 | 42.01 | +13.97 | **0.45** |
| other 7 | | | | 0.10 |

- **August**: level + tail. Capped-at-$200 mean 37.6 vs 33.2 (+4.4); median 25.1 vs 18.4; excess-over-$200 per hour 10.9 vs 7.7.
- **Feb/Mar**: actual carries spikes the model lacks (7 / 6 h > $200 vs 1 / 2); medians are close (−2).
- **Jun/Jul**: pure level (medians +3.5 / +5.3).
- **The level is system-wide and year-invariant.** JJAS median model − actual is +4 to +6 $/MWh in **every zone** (no congestion in median hours) and in 2019, 2020, 2023 and 2024 alike. Mid-distribution (p20–p80) bias by year: 2019 +3.72, 2020 +4.16, 2021 +8.92, 2022 +4.23, 2023 +2.60, 2024 +2.22, 2025 +0.88. It is the offer level — the owner-held channel (rule 1(c); 2023 k=33 hold) — not an input on the wrong vintage.

## 2. Vintage identification anchor — REJECTED at phase 0 (zero LP)

`gas_offer_margin_zonal_anchor_vintage` / `gas_offer_margin_anchor_vintage` (both `U` for ERCOT). ERCOT's zone anchors are frozen 2023–2025 means (North 2.7178). Per-year anchors measured as the median gas row of each year's own solve fuel array (7 no-LP fleet rebuilds of the keeper, the derive's `SOLVE_FUEL_ARRAY_ISOS` construction):

| Year | West | North | Houston | S_Central | South |
|---|---|---|---|---|---|
| 2019 | 2.16 | 2.31 | 2.01 | 2.33 | 3.57 |
| 2020 | 1.64 | 1.63 | 1.49 | 2.24 | 5.13 |
| 2021 | 6.94 | 7.78 | 6.79 | 7.96 | 6.02 |
| 2022 | 5.86 | 6.41 | 5.55 | 6.36 | 7.20 |
| 2023 | 1.99 | 2.47 | 2.19 | 2.90 | 3.57 |
| 2024 | 1.15 | 2.26 | 1.81 | 2.50 | 2.68 |
| 2025 | 2.74 | 3.60 | 2.56 | 3.05 | 3.76 |
| frozen | 1.96 | 2.72 | 2.31 | 2.76 | 3.28 |

If the frozen anchor were the defect, the mid-distribution bias would run at about −markup_hr × (year anchor − frozen), ≈ −3 $/MWh per $/MMBtu on CC (markup_hr 3.3–5.3). **It does not**: bias vs North gap over 2019–2025 excl. Uri 2021 has slope **+0.11, r² 0.02**; 2022 (gap +3.69) sits **+4.23 over** where the mechanism predicts ≈ −11. ERCOT's markups are fuel-invariant across years, which is the frozen anchor's own hypothesis. Arming would cut 2020 CC offers 2.2–4.3 $/MWh (North/Houston/South_Central) and add ≈ +10–15 in 2021–2022. Verdict `R`, both cells (matrix updated this session).

Side record (no action, rule 23): averaging this keeper's 2023–2025 zone medians does not reproduce the frozen table (North 2.78 vs 2.72; Houston 2.19 vs 2.31); the table was identified on the ercot149 fuel path.

## 3. Two input anomalies found — ROUTED, not armed

- **South 2020 F923 basis = HH + 3.53** (3 plants, 5M MMBtu; South_Central 13 plants, 151M MMBtu, reads +0.64). Applied to ~4.3 GW of South gas. A thin-sample rule needs a threshold, which is a new free parameter; it does not move the median (§1: zone-uniform). Owner/data question.
- **No West/Panhandle Waha row before 2022.** EIA TIE id=53919 cites 2019 Waha at **HH − 1.66**; EIA publishes no 2020/2021 annual figure, and the West net-load shape also needs a 2019 `neg_day_freq` with no citation found. Half an input is not armed. Data intake for a later lane.

## 4. Routed ERCOT-own zero-DOF corrections

- **(a) Sandy Creek commission year** — `COAL_PLANT_COMMISSION_YEAR` keyed 56257; the sheet uses 56611, so the age model fell back to 2010. Re-keyed to 56611. **Byte-inert, measured**: the 2020 fleet rebuilt with and without the fix has identical availability, mc and pmin (COAL outage parameters are flat over ages 6–15). No solve.
- **(b) Oklaunion measured heat rate — THE ARM.** `derive_campd_coal_heat_rates.py` built its population from the BA-filtered EIA-860 fleet, so bin-sheet plant 127 (EIA-860 SWPP) fell through to eGRID. The derive now also measures every curated-sheet coal plant (ERCOT only, `CURATED_SHEET_ISOS`). Re-derived because the **population** changed (rule 23). Every existing row reproduces value-for-value; the diff is +3 rows:

| Row | Measured (net) | eGRID today | Steady hours |
|---|---|---|---|
| 127 pooled | 11.6821 | 11.90 | 9,384 |
| 127 2019 | 11.7713 | 11.90 | 6,292 |
| 127 2020 | 11.4738 | 11.70 | 3,092 |

(Parasitic factor 0.93 is the derive's committed class default; 127 is not in the per-plant factor map.)

## 5. G-DRIFT (rule 29(b)) — keeper SHA `edbfdad5235eae5bacc2e8b0248024cae625a503` → HEAD

13 solve-path files changed. **All INERT**, established empirically as well as by reading: the 2019 and 2020 fleets rebuilt at the keeper's SHA (code) and at HEAD (before this arm's CSV) are **byte-identical** in mc, availability, pmin, pmax, heat rate, fuel prices, demand and unit ids, with the pre-solve versions of the three drifted data files restored in the old tree. The one LP-row hunk (`model/lp/rows.py`) is the coal-yard budget, gated on `coal_fuel_inventory` (off in the keeper). New `ScenarioConfig` fields are all default-off and absent from the recipe. **Form 4 is valid: the keeper's committed 2019/2020 legs are the control; no control solve.**

## 6. Arm and predictions

Two shards, 2019 and 2020 (rule 36), each `replay_keeper.py results/calibration/r_ercot14_span --years <Y>` with no overrides — the recipe is unchanged and the only delta is the committed CSV. 2021–2025 are untouched by construction (127 exits 2020-10-01) and are recomposed from the keeper's own legs (B-2021 `9a8f3408…`, R-ERCOT-12 2022–2025), all verified fetchable with `dispatch/<y>_P1.parquet` this session.

Predictions (written before solving):
- Oklaunion offer falls ≈ 0.13 × fuel (2019) and 0.23 × fuel (2020) $/MWh — well under $1/MWh.
- Oklaunion P1 TWh rises by 0 to +0.15 TWh per year; COAL_PRB C1 gap narrows by at most that.
- C3a moves < 0.5 pp, C3b < 0.01, C3c hour counts ± a few. **No determination flips.** 2020 C3b stays FAIL (the object is §1's offer level).
- 2021–2025 byte-identical.

## 7. Decision rule

Rule 14 governs; the correction is kept on its identity, never its scores. No train year can move. If nothing flips and the prediction holds → recommend promote (owner's standing instruction "Is it an improvement? Then promote"), with the size stated honestly: it is a data-hygiene promotion, not a calibration move. DOF ledger unchanged (12).

## 8. Arm fleet delta (zero LP, measured before solving)

Rebuilding 2019/2020 with the re-derived CSV moves exactly four rows, `COAL_North_p127_{mustrun,committed,econ,peak}`: heat rate 11.70 → 11.47 (2020; 11.90 → 11.77 in 2019), mean mc −0.34 $/MWh (2020) / −0.21 (2019). Availability, pmin, pmax and fuel prices are unchanged on every row.
