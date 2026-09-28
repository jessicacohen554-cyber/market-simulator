# FINDING — R-ERCOT-11: where the ERCOT `classFull` benchmark exceeds EIA-930

**Session:** R-ERCOT-11, 2026-09-28. **Owner ruling:** *"Diagnose only (Recommended)"* (decision card 2 in `RESULT-r-ercot-10-parish-fuel-scope-2026-09-28.md`).
**Type:** report-only, zero LP. **No scorer or benchmark change is proposed.** Any change needs an owner ruling.
**Probe:** `scripts/probes/_r_ercot11_bench_vs_930.py` (about 90 s). Every number below comes from its JSON output.
**Keeper read:** `2026-09-27-r-10-parish-fuelscope` (bundle `results/calibration/r_ercot10_parish_span`, 2019–2025).

## How `classFull` is built (verified by reproduction)

- `classFull[class]` is the EIA-923 class total minus the BTM subtrahend. It is written in `scripts/render_calibration_html.py` (the `"classFull"` block, about L1877).
  - The EIA-923 frame comes from `run_calibration_full._benchmark_eia923_frame`. That function applies the ERCOT membership filter, the dual-fuel oil re-attribution, the CAMPD under-report backfill and the missing-month fill.
  - The BTM subtrahend is `btm.parquet`'s `btm_bench_twh`, which is `co2.btmClass` in the bench part.
- Wind and solar in `classFull` are the EIA-930 series themselves.
- The bench `e930` dict (`_eia930_frame`) holds 8760 hours of `ERCO hourly` with gaps interpolated. It carries **no hydro (WAT) and no battery**.
- The probe rebuilds the frame (`build_benchmark_frames`) and reproduces every committed fossil, hydro and other `classFull` value to within 2e-4 TWh (asserted). The gap below is therefore on the scorer's own basis.

## Headline

1. **The gap is not positive in every year.** On the quoted basis (Σ classFull − Σ bench e930) it is **+3.03 / +5.86 / +4.47 / +4.79 / +2.38 / +4.78 / −1.27 TWh** for 2019–2025.
2. **Two items explain about half of it, and both are measured.**
   - **Frontera Energy Center (55098)** is counted while it was not an ERCOT resource: 2.19–3.10 TWh/yr in 2019–22, and 0.26 TWh in Jan–Mar 2023.
   - **Hydro** sits in `classFull` but not in the bench's 930 dict: 0.35–0.85 TWh. This is a comparison artefact; hydro versus 930 WAT agrees within 0.05 TWh.
3. **Decker Creek (3548) is a genuine double count:** 0.65 / 0.66 / 0.63 / 0.07 TWh in 2019–22, via the CAMPD backfill.
4. **Jack Fusco (55357) is NOT an excess.** Its EIA-923 and EIA-860 BA is MISO, but ERCOT's own 60-Day DAM lists it (`BVE_CC1`) in every covered month from 2018 on. It stays in the benchmark, as R-ERCOT-8 established.
5. **What remains is a positive gas+OTHER residual of +1.5 to +5.5 TWh/yr (2019–24).** This is candidate (a), the CHP/BTM host share, plus (f), unexplained.
   - About 0.9 TWh/yr of it is OTHER-class (refinery-gas/purchased-steam) output at chp=Y plants. The BTM subtraction never reaches that output.
   - It cannot be split further per plant from the data on disk.
6. **Coal and nuclear in the benchmark run below 930** (coal −0.5 to −2.9 TWh). They offset part of the excess.

## Per-year decomposition (TWh; the columns sum exactly to the gap)

| Year | Gap (quoted) | Hydro not in 930 dict | (c) Footprint: Frontera | (c) Double count (multiclass) | Missing-month fill above CEMS | (d) Gross/net | (a)+(b)+(f) gas+OTHER residual | Coal (bench−930) | Nuclear |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | +3.032 | 0.852 | 3.100 | 0.683 | 0.037 | 0.000 | +1.489 | −2.935 | −0.194 |
| 2020 | +5.855 | 0.626 | 2.756 | 0.726 | 0.016 | 0.000 | +3.274 | −1.463 | −0.079 |
| 2021 | +4.467 | 0.530 | 2.193 | 0.676 | 0.000 | 0.000 | +1.874 | −0.547 | −0.259 |
| 2022 | +4.793 | 0.351 | 3.042 | 0.110 | 0.065 | 0.000 | +2.138 | −0.661 | −0.251 |
| 2023 | +2.382 | 0.349 | 0.260 | 0.071 | 0.384 | 0.000 | +3.168 | −1.620 | −0.229 |
| 2024 | +4.776 | 0.463 | 0.000 | 0.056 | 0.070 | 0.000 | +5.482 | −1.105 | −0.190 |
| 2025 | −1.274 | 0.017 | 0.000 | 0.000 | 0.000 | 0.043 | +0.203 | −1.111 | −0.426 |

- **(b) other/biomass is pooled with gas.** The OTHER, biomass and oil family alone runs +0.17 to +2.35 TWh above 930 `OTH`. ERCOT's 930 books OTHER-class (process-gas) generation inside `NG` (see the `load_ercot_other_gen` note), so the two families are only commensurable together.
- **(e) DC ties and imports contribute 0.**
  - The frame has no interchange rows. Its only non-positive plant ids are the builder's own 930 repair rows (hydro 2020, solar 2023–25, wind 2025).
  - 930 net interchange (−1.6 to +0.1 TWh) is outside generation on both sides.
  - The 930 `CFE` column is 0 in every year.
- **(d) Gross versus net contributes ≈ 0.**
  - The median EIA-923 ÷ CAMPD-net ratio over co-reporting plants is 0.998–1.003 in every year.
  - CAMPD-only volume outside the footprint item is 0 TWh in 2019–22 and 0.10 TWh in 2023 and 2024.
  - 2025 carries 20.7 TWh of CAMPD fill from the preliminary vintage, which is priced at 0.043.
- **The 930 hour convention** (the bench's 8760-hour, interpolated 930 minus raw local-year) moves gas+OTHER by −0.24 in 2020, −0.70 in 2024 and +1.08 in 2025. It is already inside the residual column.
  - On a raw local-year 930 basis the 2024 residual is +4.79 and the 2025 residual is −0.88.

## Candidate (a), CHP/BTM: context for the residual

| Year | CHP-class 923 net (CC/CT/ST_CHP) | BTM already subtracted | OTHER at chp=Y plants, at own host share (not subtracted) | Residual after that | Implied extra host share |
|---|---|---|---|---|---|
| 2019 | 63.48 | 30.30 | 0.905 | 0.585 | +0.9 pp |
| 2020 | 64.85 | 30.90 | 0.902 | 2.372 | +3.7 pp |
| 2021 | 64.96 | 31.47 | 0.897 | 0.977 | +1.5 pp |
| 2022 | 61.68 | 29.99 | 0.998 | 1.140 | +1.8 pp |
| 2023 | 66.57 | 32.28 | 0.894 | 2.273 | +3.4 pp |
| 2024 | 68.74 | 32.90 | 0.862 | 4.620 | +6.7 pp |
| 2025 | 60.96 | 28.31 | 0.757 | −0.554 | −0.9 pp |

- **The effective host share already applied is 46–49 % of CHP-class net.** It comes from the sector shares (merchant 35, industrial 70, commercial 65, ST_CHP 90). The merchant 35 % is the residual-identified value in `constants.py`.
- **The last column is an inference, not a measurement.** It is the residual expressed as extra host share, under the assumption that the whole residual is BTM. No ERCOT PUN net-export data is on disk to split (a) from (f).
- **An hourly regression of 930 NG on CEMS plant series was tried and is inconclusive.** The plant coefficients swing from −0.7 to +1.9 year to year. It is not used.

## Top 20 plants by contribution to (benchmark − plausible grid-delivered), 2019–2025

| # | Plant | Name | Kind | Class | TWh, 2019–25 | TWh, 2022 | Why |
|---|---|---|---|---|---|---|---|
| 1 | 55098 | Frontera Energy Center | footprint | CC_REGULAR | 11.350 | 3.042 | No EIA-923 row 2019–22; CAMPD backfilled the whole plant. ERCOT DAM `FRONT_EC_CC1` first appears 2023-04-13, and 2023 EIA-923 starts in June. |
| 2 | 55015 | Sweeny Cogen Facility | OTHER host share | OTHER | 2.118 | 0.275 | OG slice at a chp=Y plant counted gross; the plant's own share is 35 % (IPP CHP). |
| 3 | 3548 | Decker Creek | double count | CT_PEAKER | 2.014 | 0.073 | Backfill replaced the GT row with plant CAMPD, which meters the steam units, on top of EIA-923 ST_GAS (2019: 1.371 vs 0.692 EIA-923 / 0.717 CEMS). |
| 4 | 55299 | Channel Energy Center | OTHER host share | OTHER | 0.974 | 0.182 | OG slice, 35 % share. |
| 5 | 10298 | Bayou Cogen Plant | OTHER host share | OTHER | 0.823 | 0.201 | OG slice, 70 % share (industrial). |
| 6 | 50304 | Shell Deer Park | OTHER host share | OTHER | 0.811 | 0.133 | OG/PUR slice, 35 % share. |
| 7 | 6146 | Martin Lake | month fill above CEMS | COAL_PRB | 0.376 | 0 | 2023 withheld month filled from CAMPD. EIA-923 on the other 11 months runs above CEMS. This is not a double count. |
| 8 | 3559 | Silas Ray | double count | CT_PEAKER | 0.242 | 0 | CAMPD CT row on top of EIA-923 CA/CT/GT rows (2020–24). |
| 9 | 55313 | Ingleside Cogeneration | OTHER host share | OTHER | 0.216 | 0.030 | OG slice, 70 %. |
| 10 | 50150 | Union Carbide Seadrift Cogen | OTHER host share | OTHER | 0.210 | 0.040 | OG slice, 70 %. |
| 11 | 58870 | Rentech Nitrogen Pasadena | OTHER host share | OTHER | 0.178 | 0.023 | WH slice, 35 %. |
| 12 | 55470 | Green Power 2 | OTHER host share | OTHER | 0.165 | 0.028 | OG slice, 70 %. |
| 13 | 50153 | Texas City Plant Union Carbide | OTHER host share | OTHER | 0.162 | 0.021 | PUR slice, 35 %. |
| 14 | 10554 | Formosa Utility Venture | OTHER host share | OTHER | 0.157 | 0.000 | OG slice, 70 %. |
| 15 | 3441 | Nueces Bay | month fill above CEMS | CC_REGULAR | 0.111 | 0.041 | Withheld-month fill (2022, 2024). |
| 16 | 50229 | Texas Petrochemicals | OTHER host share | OTHER | 0.106 | 0.013 | OG slice, 90 %. |
| 17 | 50043 | Houston Chemical Complex Battleground | OTHER host share | OTHER | 0.102 | 0.017 | OG slice, 70 %. |
| 18 | 52065 | Houston Plant | OTHER host share | OTHER | 0.092 | 0.021 | WH slice, 35 %. |
| 19 | 10167 | Seadrift Coke LP | OTHER host share | OTHER | 0.081 | 0.016 | OG/PC slice. |
| 20 | 3559 | Silas Ray | double count | OTHER_FOSSIL | 0.067 | 0.037 | Same mechanism (2019, 2022 years). |

- **Not in the list, on evidence:** 55357 Jack Fusco. It carries 2.34–3.65 TWh/yr with BA label MISO. It is `ba_label_only` because ERCOT DAM lists `BVE_CC1` in every covered month.
- **No other footprint leak is found.**
  - The only other non-ERCO EIA-923 rows in the membership are wind plants (PYCO 61848 and Blue Cloud 60270, SWPP). They cannot enter `classFull` because wind is the 930 series.
  - There are no El Paso, SPS, Entergy Texas or pre-2021 Lubbock fossil rows.
- **The CHP gas classes (CC_CHP, CT_CHP, ST_CHP) have no per-plant measured excess.** Their share of the residual cannot be attributed plant by plant.

## Which C1 classes carry it

- **CC_REGULAR:** Frontera, the entire footprint item.
  - The model fleet also dispatches Frontera in 2019–22 (2.72 / 2.09 / 1.44 / 2.10 TWh) and 0.13 TWh in Jan–Mar 2023. The C1 CC_REGULAR effect is therefore only model − bench on that plant, −0.38 / −0.67 / −0.76 / −0.95 / −0.13 TWh (2019–23).
- **CT_PEAKER:** the Decker and Silas Ray double counts, +0.65 to +0.73 TWh in 2019–21.
- **OTHER / OTHER_FOSSIL:** the OTHER host-share slice. These classes are not C1-gated (`FUELMIX_EXCLUDED`).
- **The gas+OTHER residual has no class address.** If it is BTM (a), it sits in CC_CHP, which is gated, and CT_CHP, which is excluded.
- **Coal (COAL_PRB, COAL_LIGNITE) carries none of the excess.** The benchmark is below 930 coal.
- **The 2022 CC_REGULAR −9.72 C1 miss is mostly not a benchmark artefact.** The consistent repair (O1b) moves it to −8.77, which still FAILs.

## Candidate scorer options (neutral; measured on the keeper; NOT proposed)

C1 CC_REGULAR model − actual in TWh, with status. The band is ±8.00 TWh and ±3 pp in every scored year; 2025 is SKIPPED (preliminary EIA-923) under every option. COAL_PRB, COAL_LIGNITE, ST_CHP and ST_GAS status is unchanged under all options (O4 moves ST_GAS by ≤ +0.41 and CC_CHP by ≤ +0.84).

| Option | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| O0 committed | +8.17 F | +7.98 P | −2.60 P | −9.72 F | +2.39 P | −1.21 P |
| O1 drop Frontera from the benchmark only | +11.27 F | +10.73 **F** | −0.41 P | −6.67 **P** | +2.65 P | −1.21 P |
| O1b drop Frontera from the benchmark and the model | +8.55 F | +8.64 **F** | −1.84 P | −8.77 F | +2.51 P | −1.21 P |
| O2 drop the double counts (benchmark only) | CC unchanged; CT_PEAKER −4.38 → −3.73 P | CT −2.90 → −2.17 P | CT −0.13 → +0.55 P | CT −2.15 → −2.07 P | CT −1.43 → −1.36 P | CT −1.28 → −1.23 P |
| O3 = O1b + O2 | +8.55 F | +8.64 **F** | −1.84 P | −8.77 F | +2.51 P | −1.21 P |
| O4 scale the gas family to 930 NG | +10.32 F | +11.81 **F** | −0.74 P | −7.17 **P** | +3.99 P | +2.13 P |

- **Flips versus O0:**
  - O1 flips 2020 to FAIL and 2022 to PASS.
  - O1b and O3 flip 2020 to FAIL only.
  - O2 flips nothing.
  - O4 flips 2020 to FAIL and 2022 to PASS.
- **O1 is asymmetric.** The model still dispatches Frontera. O1b and O3 are the consistent forms, and they amount to a fleet-plus-benchmark boundary change (rule 19), not a scorer-only change.
- **O4 is a family re-scale.** It would need its own ruling under rule 14.

## Routed, not fixed here

- **Frontera 2019–22 and Jan–Mar 2023 are in the ERCOT fleet and benchmark while ERCOT's DAM record says they were not an ERCOT resource.** This is a membership or fleet item for an ERCOT lane under rule 19, with one boundary for fleet, benchmark and injection.
- **The Decker and Silas Ray backfill double count** is a builder item in `_backfill_eia923_with_campd`. The class row is replaced with whole-plant CEMS where the CEMS meter covers another class's units.
- **The residual (a)+(f), +1.5 to +5.5 TWh/yr,** would need ERCOT PUN net-output data or 923 Schedule-8 intake to split. Its sign and size are consistent with the merchant-CHP 35 % being low, but that is not measured.

Reproduce with `uv run python scripts/probes/_r_ercot11_bench_vs_930.py --out <file>.json`.
