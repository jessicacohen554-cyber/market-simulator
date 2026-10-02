# STUDY — R-4: the C1 coal benchmark basis, EIA-923 vs EIA-930-aligned, every registered ISO-year (ZERO LP)

Lane **closeout-D** from the Backcast close-out desk, owner card **R-4** (`docs/backcast-closeout-plan-2026-10.md` §5.0: *"study across all nine ISOs first"*; §2 W5; consumers §3.4 SPP 0a and §3.6 PJM C1).
Base `origin/main` `4d459da3c81cbf07a0f0022c7625c50e51caa2c4`. **No LP, no shard, no scorer change, no rubric change, no tuning, nothing deleted.**

| artifact | what |
|---|---|
| `scripts/probes/_closeout_d_coal_basis.py` | the probe (`frames <scratch> <ISO>`, then `study <scratch> <out>`) |
| `STUDY-r4-coal-basis-2026-10.csv` (beside this record) | the full dual-basis C1 table: **450 records**, every gated C1 class in all **61 registered ISO-years** (9 ISOs, 11 runs) |
| `STUDY-r4-coal-basis-2026-10.json` (beside this record) | per-ISO-year family levels, hourly fits, 2024 rebuild parity, Final-2025 deltas, every determination |

Inputs, all read, nothing replayed: the 11 registry sidecars and their committed payloads (model `gmModel`), the committed bench parts `frontend/data/backcast/bench/<ISO>/<year>.json.gz`, the keeper shards, `data/raw/campd-unit-level/*_<Y>.parquet` (CEMS gross), and the bench builder's own EIA-923 / EIA-930 frames (`run_calibration_full.build_benchmark_frames`, run zero-LP on each keeper's `meta.json` recipe). EIA-923 for 2025 is the **Final 2025** release landed by PR #7015.

## 0. Headline

1. **The BAs do not all book coal the same way, and the data says which way each one does.** The hourly OLS of EIA-930 coal on the CEMS gross of each ISO's own 923 coal plants (coal units only; the SPP-87 method, which this probe reproduces exactly for SPP) gives three groups:
   - **SPP books coal at gross.** Slope 0.97–1.04 every year; EIA-930 sits +4.4 to +9.2 TWh above 923 net, at or inside the measured gross bound (station service 7.3–9.0 TWh) in every year.
   - **ERCOT and SOCO book net.** EIA-930 is within +0.1 to +1.5 TWh of 923 net in all 14 ISO-years; slope 0.93–0.96, negative intercept.
   - **MISO and NWPP's 930 coal cell is below 923 net** in 13 of 14 ISO-years (MISO −6 to −16 TWh, NWPP −0.3 to −10.5): an incomplete cell, not a metering basis (as the reconcile docstring and SCORER-COAL-1 already found).
   - **PJM sits between the bounds and is not identified.** EIA-930 is +3.3 to +12.5 TWh above net and below the gross bound in every year, but the slope is 0.90–0.96 with a **+0.5 to +1.7 GW intercept**: either partial gross booking or a constant non-coal block in PJM's coal feed (PJM-NEXT-21 found the same +3.4 to +12.5 and could not name its cause).
   - CAISO, NEISO, NYISO carry ≤ 0.6 TWh of coal; immaterial.
2. **Coal flips, 923 → 930-aligned: five, all FAIL → PASS, all in SPP and PJM** (§4): SPP COAL_PRB 2021, 2022, 2025; PJM COAL_BIT 2019, 2025. **No coal record moves PASS → FAIL anywhere.** On the coal leg alone (`930c`, gas untouched) four of them flip; SPP COAL_PRB 2021 stays FAIL on the share leg (3.14 pp vs 3.0) because its gas is not trimmed. Coal still fails on every basis in PJM COAL_BIT 2020/2021 (+8.8/+8.6), ERCOT COAL_PRB 2019/2020 (−10.6/−12.0) and SOCO COAL_BIT 2019 (−10.9).
3. **The gas metering-coverage leg (SPP-88 style) is real but not ready for a ruling.** EIA-930 gas is below 923 grid gas in most ISO-years (ERCOT −3.7 to −10.1 every year, NWPP −7 to −12, PJM up to −12.3, SOCO up to −5.5). In NWPP 2020–24, PJM 2024–25, SOCO 2019–20 and SPP 2019 the gap is **larger than the whole CHP block**, so it is not only host cogeneration. Which classes carry it is not measured: booking it CHP-first flips 4 gas records, booking it pro rata flips 8 *different* ones (§5). Plant attribution is a separate intake.
4. **Independent of the basis question: the EIA-923 Final 2025 release moves determinations by itself.** The committed 2025 bench parts and `completeness/eia923_2025.json` are still the preliminary vintage, so every 2025 C1 record is SKIPPED today. Gated on the Final (a complete vintage), the **923 basis adds five 2025 FAILs**: NWPP CC_REGULAR +9.5, NYISO CC_REGULAR +4.4 (share 3.25 pp), PJM CC_REGULAR −8.1, PJM COAL_BIT +11.2, SPP COAL_PRB +10.2. **NYISO falls CALIBRATED → NOT-YET on any basis** (C1 2025, and C3c then loses its lone-failure guard, rule 22). **SPP's train scope falls CALIBRATED → NOT-YET on the 923 basis only.** On the Final, the uniform reconcile now fires in 2025 for ERCOT (×0.967, the first ERCOT year it ever fires), NWPP (×0.939), SPP (×1.059) and CAISO (×1.051).
5. **ISO determinations are identical on every basis** once 2025 is on the Final (§6). The basis moves one scope: SPP's train tier 2023–25 is CALIBRATED on the 930-aligned coal basis and NOT-YET on 923. It also moves which years are on the failing lists: PJM drops 2019, and NWPP fuelmix moves between 2021/22 and 2025 depending on the gas leg.
6. **Recommendation (card §8, option A): adopt the 930-aligned coal leg for every ISO, keep gas on 923 + the current reconcile, and route gas coverage to attribution.** The case is structural, not fit (rule 1). The model serves EIA-930 demand, so the benchmark should sit on the BA's own metering basis, bounded by two measured quantities. Where the BA books net, the construction does nothing. The PJM half rests on an unidentified position between the bounds; that is stated, not hidden.

## 1. The two bases, stated once for every ISO (rule 25: no per-ISO knob)

**923 (the current scorer basis).** The committed `classFull`: EIA-923 grid-delivered by class (BTM CHP removed), with `render_calibration_html.reconcile_vintage_classes` (one uniform factor k on every fossil class when combined 923 fossil is outside ±3 % of EIA-930). For 2019–2024 this is the committed part exactly: max |rebuilt − committed| = 0.0005 TWh, and 0 status differences across all 386 non-2025 records. **2025** is rebuilt on the Final release, and the same reconcile is then re-applied: the builder's EIA-923 frame (`build_benchmark_frames` on the keeper's recipe, `apply_other_fossil_scoring`), each fossil class × (1 − the committed part's BTM share for that class). Parity of that construction on the complete 2024 vintage: every coal and gas class within 0.05 TWh in every ISO, except NEISO CT_PEAKER at 0.066. 2025 is scored as a complete vintage (all classes gated).

**930a (EIA-930-aligned, gross/net reconciled, SPP-88 gas-coverage correction).** Built from the **pre-reconcile** 923 classes (k undone), with each family set separately:

- **Coal:** `L_c = clamp(T_c, N_c, N_c + SS)`.
  - `T_c` = the EIA-930 coal cell.
  - `N_c` = 923 net coal.
  - `SS` = Σ over CEMS-metered coal plants of max(0, CEMS gross − 923 net), where CEMS gross is `grossLoad × opTime` of coal units (`CAMPD_UNIT_PLANT_REMAP` applied). This is the SPP-87 §1 construction. CEMS covers 94–100 % of 923 coal in every ISO-year.

  The BA's own metering decides where the benchmark sits between net and gross, and it can never leave those two measured bounds. Coal classes are scaled pro rata; routing is verified clean (SPP-87 §1).
- **Gas:** `L_g = clamp(T_g, G − H, G)`.
  - `T_g` = EIA-930 gas, minus the geo/biomass fold-in (`benchmark_semantics.gas_foldin_deflation`), plus (930 oil − 923 residual oil) where the BA reports an oil cell. That is the reconcile's own family rule.
  - `G` = 923 grid gas.
  - `H` = 923 grid CHP (CC_CHP + CT_CHP + ST_CHP).

  Gas the BA's telemetry does not carry is removed, bounded by and booked against the host-served cogeneration block (SPP-88 §2 candidates; PJM-NEXT-20 Hopewell). Gas is never raised above 923, because gas station service is ~2 %, and the charter's gross/net question is coal's.

Two variants isolate the legs:
- **930c** is the coal leg alone: 930a coal classes, with every other class exactly on the 923 basis, so gas keeps the committed reconcile. **This is what R-4 asks.**
- **930p** is 930a with the gas cut booked pro rata over all gas classes instead of CHP-first, to test sensitivity to the allocation.

Scoring is `calibration_verdict.score_fuelmix`, unchanged, on each basis's `classFull`. Determinations come from `calibration_verdict.iso_determination` per ISO, with `load_artifacts` patched in memory to substitute each basis. No file is written outside the record.

## 2. Coal: where each BA's EIA-930 sits (TWh; hourly fit = EIA-930 coal on CEMS gross, MW)

Net basis would read slope ≈ 923 net ÷ CEMS gross ≈ 0.89–0.93 with an intercept near zero; gross basis ≈ 1.0.

| ISO-year | 923 net | station service SS | gross bound | EIA-930 coal | 930 − net | hourly slope / intercept MW / r | 930a coal (side) |
|---|---|---|---|---|---|---|---|
| ERCOT 2019 | 78.1 | 6.0 | 84.1 | 78.2 | +0.1 | 0.96 / -302 / 0.999 | 78.2 (930) |
| ERCOT 2020 | 68.4 | 6.0 | 74.4 | 68.7 | +0.3 | 0.96 / -294 / 1.000 | 68.7 (930) |
| ERCOT 2021 | 74.5 | 6.3 | 80.9 | 75.1 | +0.5 | 0.95 / -212 / 1.000 | 75.1 (930) |
| ERCOT 2022 | 71.3 | 6.3 | 77.5 | 71.9 | +0.7 | 0.95 / -226 / 0.999 | 71.9 (930) |
| ERCOT 2023 | 61.0 | 6.3 | 67.3 | 62.3 | +1.2 | 0.95 / -216 / 1.000 | 62.3 (930) |
| ERCOT 2024 | 57.7 | 6.0 | 63.6 | 58.8 | +1.1 | 0.95 / -173 / 1.000 | 58.8 (930) |
| ERCOT 2025 | 62.3 | 6.3 | 68.6 | 63.4 | +1.1 | 0.95 / -176 / 1.000 | 63.4 (930) |
| MISO 2019 | 254.8 | 20.9 | 275.7 | 238.9 | -15.9 | 0.90 / -465 / 0.969 | 254.8 (net) |
| MISO 2020 | 201.6 | 19.4 | 221.0 | 191.7 | -9.9 | 0.94 / -1290 / 0.988 | 201.6 (net) |
| MISO 2021 | 249.5 | 23.1 | 272.6 | 239.1 | -10.4 | 0.92 / -638 / 0.992 | 249.5 (net) |
| MISO 2022 | 223.4 | 22.5 | 245.9 | 217.1 | -6.3 | 0.93 / -668 / 0.997 | 223.4 (net) |
| MISO 2023 | 186.1 | 18.9 | 205.1 | 174.9 | -11.2 | 0.93 / -1428 / 0.997 | 186.1 (net) |
| MISO 2024 | 176.9 | 18.8 | 195.7 | 167.1 | -9.9 | 0.91 / -918 / 0.998 | 176.9 (net) |
| MISO 2025 | 203.5 | 20.1 | 223.6 | 192.1 | -11.4 | 0.91 / -1099 / 0.997 | 203.5 (net) |
| NWPP 2019 | 65.1 | 5.8 | 70.8 | 54.6 | -10.5 | 0.69 / +746 / 0.966 | 65.1 (net) |
| NWPP 2020 | 52.4 | 4.9 | 57.3 | 51.9 | -0.5 | 0.68 / +1541 / 0.953 | 52.4 (net) |
| NWPP 2021 | 53.8 | 5.0 | 58.8 | 50.1 | -3.7 | 0.84 / +136 / 0.984 | 53.8 (net) |
| NWPP 2022 | 53.1 | 5.0 | 58.1 | 49.4 | -3.7 | 0.85 / +47 / 0.972 | 53.1 (net) |
| NWPP 2023 | 44.9 | 4.7 | 49.7 | 42.3 | -2.7 | 0.87 / -40 / 0.989 | 44.9 (net) |
| NWPP 2024 | 37.8 | 4.0 | 41.8 | 38.3 | +0.5 | 0.92 / +25 / 0.973 | 38.3 (930) |
| NWPP 2025 | 42.5 | 4.5 | 47.0 | 42.3 | -0.3 | 0.95 / -224 / 0.979 | 42.5 (net) |
| PJM 2019 | 182.3 | 18.2 | 200.6 | 194.8 | +12.5 | 0.93 / +1685 / 0.985 | 194.8 (930) |
| PJM 2020 | 147.7 | 16.0 | 163.7 | 151.0 | +3.3 | 0.90 / +888 / 0.973 | 151.0 (930) |
| PJM 2021 | 174.2 | 17.9 | 192.1 | 183.5 | +9.3 | 0.95 / +802 / 0.997 | 183.5 (930) |
| PJM 2022 | 157.9 | 18.9 | 176.8 | 167.4 | +9.5 | 0.96 / +481 / 0.995 | 167.4 (930) |
| PJM 2023 | 112.8 | 14.8 | 127.7 | 121.0 | +8.1 | 0.93 / +739 / 0.990 | 121.0 (930) |
| PJM 2024 | 115.6 | 17.2 | 132.7 | 122.4 | +6.8 | 0.90 / +908 / 0.990 | 122.4 (930) |
| PJM 2025 | 139.0 | 14.8 | 153.8 | 145.9 | +6.9 | 0.94 / +998 / 0.996 | 145.9 (930) |
| SOCO 2019 | 55.5 | 6.3 | 61.8 | 56.2 | +0.7 | 0.93 / -136 / 0.993 | 56.2 (930) |
| SOCO 2020 | 38.4 | 4.8 | 43.2 | 39.1 | +0.8 | 0.93 / -97 / 0.997 | 39.1 (930) |
| SOCO 2021 | 48.8 | 5.2 | 54.0 | 50.3 | +1.5 | 0.94 / -27 / 0.992 | 50.3 (930) |
| SOCO 2022 | 45.5 | 5.7 | 51.2 | 46.9 | +1.4 | 0.93 / -62 / 0.993 | 46.9 (930) |
| SOCO 2023 | 37.5 | 3.9 | 41.4 | 38.3 | +0.8 | 0.94 / -51 / 0.993 | 38.3 (930) |
| SOCO 2024 | 40.3 | 4.0 | 44.3 | 40.4 | +0.2 | 0.94 / -135 / 0.992 | 40.4 (930) |
| SOCO 2025 | 43.4 | 4.8 | 48.2 | 44.1 | +0.7 | 0.93 / -84 / 0.990 | 44.1 (930) |
| SPP 2019 | 89.7 | 8.3 | 98.1 | 94.1 | +4.4 | 0.97 / -47 / 0.946 | 94.1 (930) |
| SPP 2020 | 77.0 | 7.4 | 84.4 | 82.7 | +5.7 | 1.04 / -456 / 0.994 | 82.7 (930) |
| SPP 2021 | 90.9 | 8.2 | 99.1 | 97.0 | +6.2 | 1.01 / -179 / 0.992 | 97.0 (930) |
| SPP 2022 | 90.8 | 8.4 | 99.2 | 96.8 | +6.0 | 1.00 / -168 / 0.998 | 96.8 (930) |
| SPP 2023 | 72.0 | 7.3 | 79.3 | 78.4 | +6.4 | 1.03 / -272 / 0.991 | 78.4 (930) |
| SPP 2024 | 65.2 | 7.9 | 73.1 | 72.4 | +7.2 | 1.00 / +71 / 0.982 | 72.4 (930) |
| SPP 2025 | 78.5 | 9.0 | 87.5 | 87.7 | +9.2 | 0.97 / +379 / 0.958 | 87.5 (gross) |


CAISO, NEISO and NYISO (coal ≤ 0.6 TWh/yr) are in the CSV and omitted here.

## 3. Gas: EIA-930 vs EIA-923 grid gas (TWh; k = the factor committed in the part, preliminary for 2025)

| ISO-year | k (committed) | 923 grid gas G | CHP block H | EIA-930 gas equiv. T | T − G | coverage cut |
|---|---|---|---|---|---|---|
| CAISO 2019 | 0.888 | 57.6 | 11.6 | 51.1 | -6.5 | 6.5 |
| CAISO 2020 | 0.935 | 63.5 | 10.7 | 59.3 | -4.2 | 4.2 |
| CAISO 2021 | 0.970 | 67.5 | 10.9 | 65.4 | -2.1 | 2.1 |
| CAISO 2022 | 1.000 | 68.0 | 10.6 | 69.8 | +1.8 | 0.0 |
| CAISO 2023 | 1.000 | 67.2 | 9.9 | 75.3 | +8.0 | 0.0 |
| CAISO 2024 | 1.000 | 59.3 | 8.8 | 72.4 | +13.1 | 0.0 |
| CAISO 2025 | 0.992 | 48.4 | 8.2 | 66.0 | +17.6 | 0.0 |
| ERCOT 2019 | 1.000 | 182.3 | 33.2 | 178.7 | -3.7 | 3.7 |
| ERCOT 2020 | 1.000 | 176.0 | 33.9 | 170.2 | -5.8 | 5.8 |
| ERCOT 2021 | 1.000 | 165.6 | 33.5 | 161.9 | -3.8 | 3.8 |
| ERCOT 2022 | 1.000 | 185.1 | 31.7 | 180.9 | -4.2 | 4.2 |
| ERCOT 2023 | 1.000 | 205.4 | 34.3 | 200.2 | -5.2 | 5.2 |
| ERCOT 2024 | 1.000 | 210.8 | 35.8 | 203.5 | -7.2 | 7.2 |
| ERCOT 2025 | 1.000 | 209.2 | 36.1 | 199.1 | -10.1 | 10.1 |
| MISO 2019 | 0.965 | 176.1 | 35.0 | 176.9 | +0.8 | 0.0 |
| MISO 2020 | 1.000 | 181.3 | 34.5 | 184.3 | +3.0 | 0.0 |
| MISO 2021 | 1.000 | 169.1 | 30.4 | 168.4 | -0.7 | 0.7 |
| MISO 2022 | 1.000 | 192.3 | 31.5 | 195.4 | +3.1 | 0.0 |
| MISO 2023 | 1.000 | 216.9 | 34.9 | 228.1 | +11.3 | 0.0 |
| MISO 2024 | 1.000 | 227.8 | 35.3 | 240.3 | +12.6 | 0.0 |
| MISO 2025 | 1.043 | 209.3 | 32.2 | 222.3 | +13.0 | 0.0 |
| NEISO 2019 | 1.000 | 47.3 | 2.5 | 46.6 | -0.7 | 0.7 |
| NEISO 2020 | 1.000 | 49.7 | 2.4 | 48.8 | -0.8 | 0.8 |
| NEISO 2021 | 1.000 | 54.2 | 2.3 | 53.6 | -0.6 | 0.6 |
| NEISO 2022 | 1.000 | 54.7 | 2.4 | 53.5 | -1.2 | 1.2 |
| NEISO 2023 | 1.000 | 55.4 | 2.0 | 54.3 | -1.0 | 1.0 |
| NEISO 2024 | 1.000 | 59.7 | 2.0 | 58.7 | -1.0 | 1.0 |
| NEISO 2025 | 1.045 | 60.5 | 2.1 | 59.7 | -0.8 | 0.8 |
| NWPP 2019 | 0.868 | 70.8 | 8.5 | 63.4 | -7.4 | 7.4 |
| NWPP 2020 | 0.916 | 68.6 | 7.8 | 58.9 | -9.7 | 7.8 |
| NWPP 2021 | 0.886 | 74.7 | 8.6 | 63.7 | -11.0 | 8.6 |
| NWPP 2022 | 0.891 | 69.6 | 7.3 | 60.0 | -9.7 | 7.3 |
| NWPP 2023 | 0.899 | 80.4 | 8.4 | 70.4 | -10.0 | 8.4 |
| NWPP 2024 | 0.911 | 85.0 | 9.3 | 73.5 | -11.5 | 9.3 |
| NWPP 2025 | 1.000 | 78.8 | 8.0 | 71.7 | -7.1 | 7.1 |
| NYISO 2021 | 1.000 | 60.3 | 18.5 | 60.1 | -0.2 | 0.2 |
| NYISO 2022 | 1.000 | 66.0 | 18.6 | 65.0 | -1.0 | 1.0 |
| NYISO 2023 | 1.000 | 62.0 | 18.5 | 63.0 | +1.1 | 0.0 |
| NYISO 2024 | 1.000 | 66.1 | 20.1 | 68.0 | +1.8 | 0.0 |
| NYISO 2025 | 1.081 | 68.4 | 21.5 | 70.2 | +1.8 | 0.0 |
| PJM 2019 | 1.000 | 300.1 | 9.3 | 292.4 | -7.7 | 7.7 |
| PJM 2020 | 1.000 | 319.7 | 10.1 | 310.5 | -9.3 | 9.3 |
| PJM 2021 | 1.000 | 313.5 | 9.3 | 312.4 | -1.1 | 1.1 |
| PJM 2022 | 1.000 | 332.6 | 9.6 | 334.7 | +2.1 | 0.0 |
| PJM 2023 | 1.000 | 366.6 | 10.2 | 363.3 | -3.4 | 3.4 |
| PJM 2024 | 1.000 | 384.5 | 11.4 | 372.2 | -12.3 | 11.4 |
| PJM 2025 | 1.000 | 382.5 | 10.7 | 371.5 | -11.1 | 10.7 |
| SOCO 2019 | 1.000 | 130.8 | 4.3 | 125.3 | -5.5 | 4.3 |
| SOCO 2020 | 1.000 | 130.6 | 4.0 | 125.5 | -5.1 | 4.0 |
| SOCO 2021 | 1.000 | 122.9 | 4.0 | 121.0 | -1.9 | 1.9 |
| SOCO 2022 | 1.000 | 132.1 | 4.3 | 130.4 | -1.8 | 1.8 |
| SOCO 2023 | 1.000 | 128.7 | 3.8 | 129.4 | +0.7 | 0.0 |
| SOCO 2024 | 1.000 | 126.8 | 4.0 | 125.6 | -1.2 | 1.2 |
| SOCO 2025 | 1.000 | 126.7 | 4.2 | 125.2 | -1.5 | 1.5 |
| SPP 2019 | 1.000 | 71.7 | 3.0 | 67.6 | -4.1 | 3.0 |
| SPP 2020 | 1.000 | 71.0 | 3.2 | 68.5 | -2.5 | 2.5 |
| SPP 2021 | 1.000 | 54.7 | 3.0 | 52.7 | -2.0 | 2.0 |
| SPP 2022 | 1.000 | 60.9 | 3.0 | 59.1 | -1.8 | 1.8 |
| SPP 2023 | 1.039 | 75.9 | 3.4 | 75.3 | -0.6 | 0.6 |
| SPP 2024 | 1.054 | 81.2 | 3.4 | 81.9 | +0.7 | 0.0 |
| SPP 2025 | 1.081 | 74.9 | 3.4 | 74.8 | -0.1 | 0.1 |


Reading: the gap is near zero where BAs meter what EIA-923 reports (MISO 2019–22, NYISO, SPP 2023–25, SOCO 2021–25). It is negative and persistent in ERCOT (3.7 → 10.1 TWh, rising), NWPP (a 17-BA pool), CAISO 2019–21 and PJM 2019/20/24/25. It is positive in CAISO 2022–25 (the corrupted CISO NG cell, `EIA930_NG_CELL_CORRUPT`) and MISO 2023–25. Where T − G exceeds −H, the CHP-only bound binds and the coverage gap is evidently not only cogeneration.

## 4. The dual-basis C1 table, coal classes (every coal class ≥ 0.5 TWh; bold = verdict differs between bases)

Band: volume min(max(2 % load, 3 % actual gen), 8 TWh) AND share ±3.0 pp (rubric, unchanged). The gas classes, and every class in CAISO/NEISO/NYISO, are in the CSV (`status_923`, `status_930a`, `status_930c`, `status_930p`, `flip`).

| ISO | year | class | model | bench 923 | bench 930a | Δ 923 | Δ 930a | share pp 923 / 930a | 923 | 930a |
|---|---|---|---|---|---|---|---|---|---|---|
| ERCOT | 2019 | COAL_PRB | 50.8 | 61.3 | 61.4 | -10.5 | -10.6 | -2.60 / -2.77 | FAIL | FAIL |
| ERCOT | 2019 | COAL_LIGNITE | 16.5 | 16.8 | 16.8 | -0.3 | -0.4 | -0.05 / -0.09 | PASS | PASS |
| ERCOT | 2020 | COAL_PRB | 38.9 | 50.7 | 50.9 | -11.8 | -12.0 | -2.93 / -3.17 | FAIL | FAIL |
| ERCOT | 2020 | COAL_LIGNITE | 16.5 | 17.7 | 17.8 | -1.2 | -1.2 | -0.24 / -0.32 | PASS | PASS |
| ERCOT | 2021 | COAL_PRB | 56.4 | 58.1 | 58.5 | -1.7 | -2.1 | -0.31 / -0.54 | PASS | PASS |
| ERCOT | 2021 | COAL_LIGNITE | 16.9 | 16.4 | 16.6 | +0.5 | +0.4 | +0.15 / +0.09 | PASS | PASS |
| ERCOT | 2022 | COAL_PRB | 60.0 | 54.2 | 54.7 | +5.8 | +5.3 | +1.44 / +1.22 | PASS | PASS |
| ERCOT | 2022 | COAL_LIGNITE | 17.7 | 17.1 | 17.2 | +0.6 | +0.4 | +0.17 / +0.10 | PASS | PASS |
| ERCOT | 2023 | COAL_PRB | 43.5 | 45.7 | 46.6 | -2.2 | -3.1 | -0.40 / -0.70 | PASS | PASS |
| ERCOT | 2023 | COAL_LIGNITE | 16.7 | 15.3 | 15.7 | +1.4 | +1.1 | +0.34 / +0.24 | PASS | PASS |
| ERCOT | 2024 | COAL_PRB | 42.7 | 43.7 | 44.6 | -1.0 | -1.9 | -0.11 / -0.41 | PASS | PASS |
| ERCOT | 2024 | COAL_LIGNITE | 15.2 | 13.9 | 14.2 | +1.2 | +1.0 | +0.31 / +0.21 | PASS | PASS |
| ERCOT | 2025 | COAL_PRB | 51.3 | 46.1 | 48.5 | +5.2 | +2.8 | +1.07 / +0.58 | PASS | PASS |
| ERCOT | 2025 | COAL_LIGNITE | 15.3 | 14.1 | 14.8 | +1.2 | +0.4 | +0.24 / +0.09 | PASS | PASS |
| MISO | 2019 | COAL_PRB | 161.4 | 155.0 | 160.7 | +6.4 | +0.8 | +1.17 / +0.89 | PASS | PASS |
| MISO | 2019 | COAL_LIGNITE | 9.4 | 8.4 | 8.7 | +1.0 | +0.7 | +0.18 / +0.16 | PASS | PASS |
| MISO | 2019 | COAL_BIT | 81.5 | 82.5 | 85.5 | -0.9 | -3.9 | -0.10 / -0.25 | PASS | PASS |
| MISO | 2020 | COAL_PRB | 130.5 | 126.9 | 126.9 | +3.6 | +3.6 | +1.09 / +1.09 | PASS | PASS |
| MISO | 2020 | COAL_LIGNITE | 9.7 | 8.4 | 8.4 | +1.3 | +1.3 | +0.27 / +0.27 | PASS | PASS |
| MISO | 2020 | COAL_BIT | 61.8 | 66.4 | 66.4 | -4.5 | -4.5 | -0.56 / -0.56 | PASS | PASS |
| MISO | 2021 | COAL_PRB | 169.4 | 163.7 | 163.7 | +5.7 | +5.7 | +1.64 / +1.61 | PASS | PASS |
| MISO | 2021 | COAL_LIGNITE | 9.0 | 8.4 | 8.4 | +0.6 | +0.6 | +0.14 / +0.13 | PASS | PASS |
| MISO | 2021 | COAL_BIT | 76.9 | 77.3 | 77.3 | -0.4 | -0.4 | +0.27 / +0.26 | PASS | PASS |
| MISO | 2022 | COAL_PRB | 155.2 | 149.9 | 149.9 | +5.3 | +5.3 | +1.09 / +1.09 | PASS | PASS |
| MISO | 2022 | COAL_LIGNITE | 6.6 | 6.5 | 6.5 | +0.1 | +0.1 | +0.03 / +0.03 | PASS | PASS |
| MISO | 2022 | COAL_BIT | 72.7 | 67.0 | 67.0 | +5.7 | +5.7 | +1.01 / +1.01 | PASS | PASS |
| MISO | 2023 | COAL_PRB | 119.2 | 121.9 | 121.9 | -2.7 | -2.7 | -0.14 / -0.14 | PASS | PASS |
| MISO | 2023 | COAL_LIGNITE | 6.6 | 7.1 | 7.1 | -0.5 | -0.5 | -0.06 / -0.06 | PASS | PASS |
| MISO | 2023 | COAL_BIT | 55.6 | 57.1 | 57.1 | -1.5 | -1.5 | -0.11 / -0.11 | PASS | PASS |
| MISO | 2024 | COAL_PRB | 116.4 | 116.7 | 116.7 | -0.3 | -0.3 | +0.15 / +0.15 | PASS | PASS |
| MISO | 2024 | COAL_LIGNITE | 6.1 | 6.5 | 6.5 | -0.5 | -0.5 | -0.06 / -0.06 | PASS | PASS |
| MISO | 2024 | COAL_BIT | 53.1 | 53.7 | 53.7 | -0.6 | -0.6 | -0.01 / -0.01 | PASS | PASS |
| MISO | 2025 | COAL_PRB | 137.6 | 140.0 | 140.0 | -2.5 | -2.5 | -0.07 / -0.07 | PASS | PASS |
| MISO | 2025 | COAL_LIGNITE | 5.8 | 5.9 | 5.9 | -0.1 | -0.1 | -0.00 / -0.00 | PASS | PASS |
| MISO | 2025 | COAL_BIT | 58.8 | 57.6 | 57.6 | +1.2 | +1.2 | +0.32 / +0.32 | PASS | PASS |
| NWPP | 2019 | COAL_PRB | 38.2 | 33.0 | 38.0 | +5.2 | +0.2 | +1.93 / +0.63 | PASS | PASS |
| NWPP | 2019 | COAL_BIT | 22.2 | 22.9 | 26.3 | -0.7 | -4.2 | -0.21 / -1.11 | PASS | PASS |
| NWPP | 2019 | COAL_WC | 0.2 | 0.6 | 0.7 | -0.4 | -0.5 | -0.14 / -0.16 | PASS | PASS |
| NWPP | 2020 | COAL_PRB | 31.2 | 27.3 | 29.8 | +3.9 | +1.4 | +1.29 / +0.52 | PASS | PASS |
| NWPP | 2020 | COAL_BIT | 20.8 | 20.2 | 22.0 | +0.7 | -1.2 | +0.20 / -0.37 | PASS | PASS |
| NWPP | 2020 | COAL_WC | 0.1 | 0.5 | 0.6 | -0.4 | -0.4 | -0.14 / -0.15 | PASS | PASS |
| NWPP | 2021 | COAL_PRB | 29.8 | 26.4 | 29.8 | +3.4 | -0.0 | +1.17 / +0.20 | PASS | PASS |
| NWPP | 2021 | COAL_BIT | 25.2 | 20.6 | 23.3 | +4.6 | +1.9 | +1.57 / +0.82 | PASS | PASS |
| NWPP | 2021 | COAL_WC | 0.4 | 0.6 | 0.7 | -0.2 | -0.3 | -0.08 / -0.10 | PASS | PASS |
| NWPP | 2022 | COAL_PRB | 33.2 | 27.4 | 30.8 | +5.8 | +2.5 | +1.95 / +1.03 | PASS | PASS |
| NWPP | 2022 | COAL_BIT | 23.3 | 19.3 | 21.6 | +4.0 | +1.6 | +1.33 / +0.69 | PASS | PASS |
| NWPP | 2022 | COAL_WC | 0.6 | 0.6 | 0.7 | -0.0 | -0.1 | -0.01 / -0.03 | PASS | PASS |
| NWPP | 2023 | COAL_PRB | 28.6 | 25.2 | 28.1 | +3.4 | +0.5 | +1.19 / +0.33 | PASS | PASS |
| NWPP | 2023 | COAL_BIT | 19.4 | 14.6 | 16.2 | +4.8 | +3.2 | +1.72 / +1.22 | PASS | PASS |
| NWPP | 2023 | COAL_WC | 0.3 | 0.6 | 0.6 | -0.2 | -0.3 | -0.08 / -0.10 | PASS | PASS |
| NWPP | 2024 | COAL_PRB | 24.5 | 21.0 | 23.4 | +3.5 | +1.1 | +1.20 / +0.44 | PASS | PASS |
| NWPP | 2024 | COAL_BIT | 11.5 | 12.8 | 14.3 | -1.3 | -2.7 | -0.45 / -0.91 | PASS | PASS |
| NWPP | 2024 | COAL_WC | 0.2 | 0.6 | 0.6 | -0.4 | -0.5 | -0.14 / -0.16 | PASS | PASS |
| NWPP | 2025 | COAL_PRB | 23.5 | 22.4 | 23.8 | +1.1 | -0.3 | +0.30 / -0.18 | PASS | PASS |
| NWPP | 2025 | COAL_BIT | 13.1 | 17.1 | 18.2 | -4.0 | -5.1 | -1.36 / -1.72 | PASS | PASS |
| PJM | 2019 | COAL_PRB | 6.3 | 7.4 | 7.9 | -1.1 | -1.6 | -0.14 / -0.20 | PASS | PASS |
| PJM | 2019 | COAL_BIT | 188.2 | 169.5 | 181.1 | +18.7 | +7.1 | +1.94 / +0.64 | **FAIL** | **PASS** |
| PJM | 2019 | COAL_WC | 5.7 | 5.5 | 5.8 | +0.2 | -0.1 | +0.02 / -0.02 | PASS | PASS |
| PJM | 2020 | COAL_PRB | 3.3 | 3.2 | 3.3 | +0.0 | -0.0 | +0.00 / -0.01 | PASS | PASS |
| PJM | 2020 | COAL_BIT | 151.6 | 139.7 | 142.8 | +11.9 | +8.8 | +1.30 / +0.77 | FAIL | FAIL |
| PJM | 2020 | COAL_WC | 3.7 | 4.7 | 4.8 | -1.0 | -1.1 | -0.14 / -0.15 | PASS | PASS |
| PJM | 2021 | COAL_PRB | 10.5 | 9.4 | 9.9 | +1.1 | +0.6 | +0.12 / +0.07 | PASS | PASS |
| PJM | 2021 | COAL_BIT | 176.1 | 159.0 | 167.5 | +17.1 | +8.6 | +1.86 / +1.02 | FAIL | FAIL |
| PJM | 2021 | COAL_WC | 6.3 | 5.8 | 6.1 | +0.5 | +0.2 | +0.05 / +0.02 | PASS | PASS |
| PJM | 2022 | COAL_PRB | 10.8 | 10.2 | 10.8 | +0.6 | -0.0 | +0.05 / -0.01 | PASS | PASS |
| PJM | 2022 | COAL_BIT | 147.7 | 140.9 | 149.4 | +6.8 | -1.7 | +0.48 / -0.35 | PASS | PASS |
| PJM | 2022 | COAL_WC | 6.4 | 6.7 | 7.1 | -0.3 | -0.7 | -0.05 / -0.09 | PASS | PASS |
| PJM | 2023 | COAL_PRB | 3.5 | 3.5 | 3.8 | -0.0 | -0.3 | -0.00 / -0.03 | PASS | PASS |
| PJM | 2023 | COAL_BIT | 103.6 | 103.4 | 110.8 | +0.3 | -7.2 | -0.07 / -0.91 | PASS | PASS |
| PJM | 2023 | COAL_WC | 4.9 | 5.9 | 6.3 | -1.0 | -1.5 | -0.13 / -0.18 | PASS | PASS |
| PJM | 2024 | COAL_PRB | 4.2 | 4.4 | 4.7 | -0.2 | -0.4 | -0.02 / -0.05 | PASS | PASS |
| PJM | 2024 | COAL_BIT | 106.3 | 105.4 | 111.6 | +0.9 | -5.3 | +0.11 / -0.71 | PASS | PASS |
| PJM | 2024 | COAL_WC | 5.0 | 5.7 | 6.0 | -0.7 | -1.0 | -0.08 / -0.13 | PASS | PASS |
| PJM | 2025 | COAL_PRB | 7.0 | 6.1 | 6.4 | +0.9 | +0.6 | +0.11 / +0.07 | PASS | PASS |
| PJM | 2025 | COAL_BIT | 137.1 | 125.9 | 132.2 | +11.2 | +5.0 | +1.34 / +0.55 | **FAIL** | **PASS** |
| PJM | 2025 | COAL_WC | 5.6 | 7.0 | 7.3 | -1.3 | -1.7 | -0.15 / -0.19 | PASS | PASS |
| SOCO | 2019 | COAL_PRB | 34.5 | 32.4 | 32.8 | +2.1 | +1.7 | +1.35 / +1.00 | PASS | PASS |
| SOCO | 2019 | COAL_BIT | 12.6 | 23.1 | 23.4 | -10.6 | -10.9 | -3.96 / -4.21 | FAIL | FAIL |
| SOCO | 2020 | COAL_PRB | 24.2 | 24.2 | 24.6 | +0.0 | -0.4 | +0.41 / +0.07 | PASS | PASS |
| SOCO | 2020 | COAL_BIT | 8.5 | 14.2 | 14.5 | -5.7 | -6.0 | -2.23 / -2.43 | PASS | PASS |
| SOCO | 2021 | COAL_PRB | 33.5 | 31.4 | 32.4 | +2.1 | +1.1 | +1.17 / +0.74 | PASS | PASS |
| SOCO | 2021 | COAL_BIT | 13.3 | 17.4 | 18.0 | -4.1 | -4.7 | -1.57 / -1.81 | PASS | PASS |
| SOCO | 2022 | COAL_PRB | 36.6 | 30.9 | 31.9 | +5.7 | +4.8 | +2.56 / +2.17 | PASS | PASS |
| SOCO | 2022 | COAL_BIT | 16.4 | 14.6 | 15.0 | +1.8 | +1.4 | +0.86 / +0.68 | PASS | PASS |
| SOCO | 2023 | COAL_PRB | 22.8 | 23.7 | 24.2 | -0.9 | -1.4 | -0.31 / -0.48 | PASS | PASS |
| SOCO | 2023 | COAL_BIT | 9.2 | 13.8 | 14.1 | -4.6 | -4.9 | -1.86 / -1.96 | PASS | PASS |
| SOCO | 2024 | COAL_PRB | 24.1 | 26.9 | 27.0 | -2.8 | -3.0 | -0.91 / -1.00 | PASS | PASS |
| SOCO | 2024 | COAL_BIT | 10.0 | 13.4 | 13.4 | -3.3 | -3.4 | -1.22 / -1.27 | PASS | PASS |
| SOCO | 2025 | COAL_PRB | 32.2 | 28.4 | 28.8 | +3.8 | +3.4 | +1.75 / +1.54 | PASS | PASS |
| SOCO | 2025 | COAL_BIT | 15.6 | 15.0 | 15.3 | +0.5 | +0.3 | +0.33 / +0.22 | PASS | PASS |
| SPP | 2019 | COAL_PRB | 79.9 | 76.9 | 80.7 | +3.0 | -0.8 | +1.12 / -0.11 | PASS | PASS |
| SPP | 2019 | COAL_LIGNITE | 11.0 | 12.7 | 13.4 | -1.7 | -2.3 | -0.63 / -0.83 | PASS | PASS |
| SPP | 2020 | COAL_PRB | 65.7 | 66.1 | 71.0 | -0.4 | -5.3 | -0.37 / -1.92 | PASS | PASS |
| SPP | 2020 | COAL_LIGNITE | 9.0 | 10.8 | 11.6 | -1.8 | -2.6 | -0.73 / -0.98 | PASS | PASS |
| SPP | 2021 | COAL_PRB | 93.5 | 80.3 | 85.8 | +13.2 | +7.8 | +4.45 / +2.90 | **FAIL** | **PASS** |
| SPP | 2021 | COAL_LIGNITE | 9.4 | 10.5 | 11.2 | -1.1 | -1.8 | -0.45 / -0.65 | PASS | PASS |
| SPP | 2022 | COAL_PRB | 91.3 | 78.1 | 83.3 | +13.2 | +8.0 | +4.15 / +2.76 | **FAIL** | **PASS** |
| SPP | 2022 | COAL_LIGNITE | 13.0 | 12.6 | 13.5 | +0.4 | -0.5 | +0.06 / -0.16 | PASS | PASS |
| SPP | 2023 | COAL_PRB | 68.7 | 65.4 | 68.5 | +3.3 | +0.2 | +1.16 / +0.05 | PASS | PASS |
| SPP | 2023 | COAL_LIGNITE | 8.0 | 9.4 | 9.8 | -1.4 | -1.9 | -0.49 / -0.65 | PASS | PASS |
| SPP | 2024 | COAL_PRB | 63.6 | 60.0 | 63.3 | +3.6 | +0.4 | +1.21 / +0.05 | PASS | PASS |
| SPP | 2024 | COAL_LIGNITE | 6.6 | 8.7 | 9.1 | -2.1 | -2.5 | -0.71 / -0.88 | PASS | PASS |
| SPP | 2025 | COAL_PRB | 84.6 | 74.3 | 78.2 | +10.2 | +6.4 | +3.39 / +2.10 | **FAIL** | **PASS** |
| SPP | 2025 | COAL_LIGNITE | 6.5 | 8.8 | 9.3 | -2.3 | -2.8 | -0.78 / -0.93 | PASS | PASS |


## 5. Every record that fails on any basis (gas and coal)

| ISO | year | class | model | 923 | 930a | 930c | 930p | Δ 923 | Δ 930a | 923 | 930a | 930c | 930p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CAISO | 2019 | CC_REGULAR | 46.8 | 36.1 | 40.6 | 36.1 | 36.0 | +10.8 | +6.2 | FAIL | FAIL | FAIL | FAIL |
| CAISO | 2019 | CC_CHP | 8.9 | 7.1 | 3.5 | 7.1 | 7.1 | +1.7 | +5.3 | PASS | FAIL | PASS | PASS |
| CAISO | 2020 | CC_REGULAR | 60.7 | 43.1 | 46.1 | 43.1 | 43.1 | +17.6 | +14.6 | FAIL | FAIL | FAIL | FAIL |
| CAISO | 2021 | CC_REGULAR | 59.3 | 49.2 | 50.7 | 49.2 | 49.1 | +10.2 | +8.6 | FAIL | FAIL | FAIL | FAIL |
| ERCOT | 2019 | CC_REGULAR | 141.0 | 132.2 | 132.2 | 132.2 | 129.5 | +8.9 | +8.9 | FAIL | FAIL | FAIL | FAIL |
| ERCOT | 2019 | COAL_PRB | 50.8 | 61.3 | 61.4 | 61.4 | 61.4 | -10.5 | -10.6 | FAIL | FAIL | FAIL | FAIL |
| ERCOT | 2020 | CC_REGULAR | 138.0 | 127.8 | 127.8 | 127.8 | 123.6 | +10.2 | +10.2 | FAIL | FAIL | FAIL | FAIL |
| ERCOT | 2020 | COAL_PRB | 38.9 | 50.7 | 50.9 | 50.9 | 50.9 | -11.8 | -12.0 | FAIL | FAIL | FAIL | FAIL |
| ERCOT | 2022 | CC_REGULAR | 124.4 | 134.5 | 134.5 | 134.5 | 131.4 | -10.1 | -10.1 | FAIL | FAIL | FAIL | PASS |
| MISO | 2019 | ST_GAS | 8.4 | 16.4 | 17.0 | 16.4 | 17.0 | -8.0 | -8.6 | FAIL | FAIL | FAIL | FAIL |
| NWPP | 2021 | CC_REGULAR | 51.7 | 53.8 | 60.8 | 53.8 | 53.8 | -2.1 | -9.1 | PASS | FAIL | PASS | PASS |
| NWPP | 2022 | CC_REGULAR | 46.3 | 50.3 | 56.5 | 50.3 | 50.6 | -4.0 | -10.2 | PASS | FAIL | PASS | PASS |
| NWPP | 2025 | CC_REGULAR | 65.9 | 56.4 | 60.1 | 56.4 | 54.7 | +9.5 | +5.8 | FAIL | PASS | FAIL | FAIL |
| NYISO | 2025 | CC_REGULAR | 35.8 | 31.3 | 31.3 | 31.3 | 31.3 | +4.4 | +4.4 | FAIL | FAIL | FAIL | FAIL |
| PJM | 2019 | CC_REGULAR | 275.1 | 268.8 | 268.8 | 268.8 | 261.9 | +6.3 | +6.3 | PASS | PASS | PASS | FAIL |
| PJM | 2019 | COAL_BIT | 188.2 | 169.5 | 181.1 | 181.1 | 181.1 | +18.7 | +7.1 | FAIL | PASS | PASS | PASS |
| PJM | 2020 | CC_REGULAR | 293.3 | 283.5 | 283.5 | 283.5 | 275.3 | +9.8 | +9.8 | FAIL | FAIL | FAIL | FAIL |
| PJM | 2020 | COAL_BIT | 151.6 | 139.7 | 142.8 | 142.8 | 142.8 | +11.9 | +8.8 | FAIL | FAIL | FAIL | FAIL |
| PJM | 2021 | CT_PEAKER | 11.2 | 20.8 | 20.8 | 20.8 | 20.7 | -9.6 | -9.6 | FAIL | FAIL | FAIL | FAIL |
| PJM | 2021 | COAL_BIT | 176.1 | 159.0 | 167.5 | 167.5 | 167.5 | +17.1 | +8.6 | FAIL | FAIL | FAIL | FAIL |
| PJM | 2022 | CC_REGULAR | 308.9 | 298.0 | 298.0 | 298.0 | 298.0 | +10.9 | +10.9 | FAIL | FAIL | FAIL | FAIL |
| PJM | 2023 | CC_REGULAR | 334.2 | 325.7 | 325.7 | 325.7 | 322.7 | +8.5 | +8.5 | FAIL | FAIL | FAIL | FAIL |
| PJM | 2024 | CC_REGULAR | 334.8 | 335.6 | 335.6 | 335.6 | 325.7 | -0.8 | -0.8 | PASS | PASS | PASS | FAIL |
| PJM | 2025 | CC_REGULAR | 322.8 | 330.9 | 330.9 | 330.9 | 321.6 | -8.1 | -8.1 | FAIL | FAIL | FAIL | PASS |
| PJM | 2025 | COAL_BIT | 137.1 | 125.9 | 132.2 | 132.2 | 132.2 | +11.2 | +5.0 | FAIL | PASS | PASS | PASS |
| SOCO | 2019 | CC_REGULAR | 112.9 | 110.6 | 110.6 | 110.6 | 107.0 | +2.3 | +2.3 | PASS | PASS | PASS | FAIL |
| SOCO | 2019 | COAL_BIT | 12.6 | 23.1 | 23.4 | 23.4 | 23.4 | -10.6 | -10.9 | FAIL | FAIL | FAIL | FAIL |
| SOCO | 2021 | CC_REGULAR | 111.4 | 107.2 | 107.2 | 107.2 | 105.5 | +4.2 | +4.2 | PASS | PASS | PASS | FAIL |
| SPP | 2021 | CC_REGULAR | 24.9 | 34.6 | 34.6 | 34.6 | 33.3 | -9.6 | -9.6 | FAIL | FAIL | FAIL | FAIL |
| SPP | 2021 | COAL_PRB | 93.5 | 80.3 | 85.8 | 85.8 | 85.8 | +13.2 | +7.8 | FAIL | PASS | FAIL | PASS |
| SPP | 2022 | CC_REGULAR | 24.9 | 35.8 | 35.8 | 35.8 | 34.7 | -10.8 | -10.8 | FAIL | FAIL | FAIL | FAIL |
| SPP | 2022 | COAL_PRB | 91.3 | 78.1 | 83.3 | 83.3 | 83.3 | +13.2 | +8.0 | FAIL | PASS | PASS | PASS |
| SPP | 2025 | COAL_PRB | 84.6 | 74.3 | 78.2 | 78.2 | 78.2 | +10.2 | +6.4 | FAIL | PASS | PASS | PASS |


### 5.1 The flip list (ISO-year-class whose C1 verdict differs between the 923 and 930a bases)

| # | ISO-year | class | 923 → 930a | Δ 923 → Δ 930a (TWh) | leg | on 930c | on 930p |
|---|---|---|---|---|---|---|---|
| 1 | SPP 2021 | COAL_PRB | FAIL → PASS | +13.2 → +7.8 (share 4.45 → 2.90 pp) | coal (gross basis) | FAIL (share 3.14 pp) | PASS |
| 2 | SPP 2022 | COAL_PRB | FAIL → PASS | +13.2 → +8.0 (share 4.15 → 2.76 pp) | coal | PASS | PASS |
| 3 | SPP 2025 | COAL_PRB | FAIL → PASS | +10.2 → +6.4 | coal (+ k 1.059 undone) | PASS | PASS |
| 4 | PJM 2019 | COAL_BIT | FAIL → PASS | +18.7 → +7.1 | coal (unidentified position) | PASS | PASS |
| 5 | PJM 2025 | COAL_BIT | FAIL → PASS | +11.2 → +5.0 | coal (unidentified position) | PASS | PASS |
| 6 | CAISO 2019 | CC_CHP | PASS → FAIL | +1.7 → +5.3 (share 3.06 pp) | gas coverage, CHP-first | PASS | PASS |
| 7 | NWPP 2021 | CC_REGULAR | PASS → FAIL | −2.1 → −9.1 | k (0.886) undone; gap > CHP block | PASS | PASS |
| 8 | NWPP 2022 | CC_REGULAR | PASS → FAIL | −4.0 → −10.2 | k (0.891) undone; gap > CHP block | PASS | PASS |
| 9 | NWPP 2025 | CC_REGULAR | FAIL → PASS | +9.5 → +5.8 | k (0.939) undone | FAIL | FAIL |

930p flips a different gas set against 923: ERCOT 2022 CC_REGULAR FAIL→PASS, PJM 2025 CC_REGULAR FAIL→PASS, and PJM 2019, PJM 2024, SOCO 2019 and SOCO 2021 CC_REGULAR PASS→FAIL. That instability is why the gas leg is not ruled on here.

Rows 1–5 are the R-4 answer. Rows 6–9 come from the gas leg, and from removing the uniform k, which 930a replaces with per-family levels. In NWPP the k was carrying the 930 gas gap across both families. Undoing it raises CC_REGULAR's target, because the CHP-first bound cannot absorb a gap larger than the CHP block. Rows 7–8 measure that construction choice, not the model.

**Effect on the open coal objects.**
- **SPP §3.4 step 0a** ("CC 2021 ≥ −8.0; PRB 2021/22 within ±8.0"): PRB 2021/22 pass on 930a, and PRB 2022 passes on 930c. PRB 2021 misses on 930c by 0.14 pp of share. **CC_REGULAR 2021/22 stay FAIL on every basis (−9.6/−10.8).** This confirms SPP-87 §0.5: the CC deficit is not a benchmark artifact.
- **PJM §3.6:** COAL_BIT 2019 and 2025 pass on 930a/930c. 2020 and 2021 still fail (+8.8/+8.6), so L1 is still needed. On 930a, 2023/24 COAL_BIT move to −7.2/−5.3, which is still PASS but on the other side. CC 2023 (+8.5) is unchanged on every coal-side basis, as PJM-NEXT-21 found.
- **The construction does not favour the model.** It widens SPP COAL_PRB 2020 (−0.4 → −5.3), ERCOT COAL_PRB 2019/20 (−10.5/−11.8 → −10.6/−12.0), NWPP COAL_BIT 2019 (−0.7 → −4.2) and PJM COAL_BIT 2023/24.

## 6. What each basis does to every determination (rubric v3.13, `iso_determination`, worst-of over scopes)

2025 on the Final for every column except "committed".

| ISO | committed (2025 prelim, SKIPPED) | 923 (Final 2025) | 930c (coal leg) | 930a (coal + gas CHP-first) | 930p (coal + gas pro rata) |
|---|---|---|---|---|---|
| CAISO | NOT-YET (2022–25 CAL; 2019–21 NY) | same | same | same | same |
| ERCOT | NOT-YET | same | same | same | NOT-YET (validation loses fuelmix 2022) |
| MISO | NOT-YET (train CAL) | same | same | same | same |
| NEISO | **CALIBRATED** | CALIBRATED | CALIBRATED | CALIBRATED | CALIBRATED |
| NWPP | NOT-YET (dispatch_corr 2023) | NOT-YET (+ fuelmix 2025) | NOT-YET (+ fuelmix 2025) | NOT-YET (+ fuelmix 2021/22) | NOT-YET (+ fuelmix 2025) |
| NYISO | **CALIBRATED** | **NOT-YET** (fuelmix 2025 + price_tail 2023–25) | NOT-YET | NOT-YET | NOT-YET |
| PJM | NOT-YET (fuelmix 2019–23) | NOT-YET (fuelmix 2019–23, 2025) | NOT-YET (fuelmix 2020–23, 2025) | NOT-YET (fuelmix 2020–23, 2025) | NOT-YET (fuelmix 2019–24) |
| SOCO | NOT-YET (budget) | same | same | same | NOT-YET (+ fuelmix 2019/21) |
| SPP | NOT-YET (**train CAL**) | NOT-YET (**train NOT-YET**: fuelmix 2025 + price_tail 2023–25) | NOT-YET (**train CAL**) | NOT-YET (train CAL) | NOT-YET (train CAL) |

- **ISO-level determinations do not depend on the basis.** All four Final-2025 columns agree on all nine ISOs.
- **The Final-2025 re-gate is what moves an ISO:** NYISO CALIBRATED → NOT-YET on every basis. NYISO CC_REGULAR 2025 is +4.4 TWh / +3.25 pp against the Final; the preliminary part's ×1.08 up-scale was carrying it at 33.6 TWh.
- **The basis moves one scope:** SPP train 2023–25 is CALIBRATED on any 930-aligned coal basis and NOT-YET on 923 once 2025 gates. MISO's train scope stays CALIBRATED on every basis.

## 7. Limits

- **PJM's coal position is not identified.** The clamp puts PJM on its EIA-930 cell. That cell sits inside [net, gross] in every year, but with a positive intercept that a pure gross-booking BA would not show. If part of it is non-coal output booked as coal, the PJM flips (rows 4–5) overstate the alignment. A unit-level PJM fuel-mix reconciliation (the NEXT-20 card 2 method, applied to coal) would settle it.
- **MISO and NWPP sit on the net floor** because their 930 coal cell is incomplete. The aligned basis there is 923 net by construction, not by evidence that they book net.
- **2025 is rebuilt, not re-rendered.** The probe takes the bench builder's Final-2025 EIA-923 frame and applies the committed part's per-class BTM shares. A full regeneration (`run_calibration_full.py --rebuild-benchmark` + `dashboard_add_run.py` + `audit_eia923_completeness.py`) is the owner-path refresh; its numbers can differ by the BTM re-sizing on the Final (≤ the 2024 parity of 0.05 TWh per class is the expectation, not a guarantee).
- **Gas-leg attribution** (which plants the BA does not meter) needs registration data per ISO (SPP-88 successor 2). This study bounds the leg; it does not attribute it.
- Model numbers are the committed P1 `gmModel` of each registered run. Nothing was re-solved, so none of this tests the model; it tests the benchmark.

## 8. DECISION CARD — owner (R-4)

**Question:** what should the C1 coal benchmark be measured against, for every ISO?

**Separately and regardless of this card:** the EIA-923 Final 2025 release is on `main`, while the committed 2025 bench parts and completeness part are preliminary. Regenerating them makes NYISO NOT-YET under every option below. That refresh is data housekeeping (rules 14 and 23: a source-release change), not this ruling. The desk should schedule it.

| | Option | What changes | Determinations (2025 on the Final) |
|---|---|---|---|
| **A** | **Adopt the 930-aligned coal leg everywhere (930c) (Recommended)** | C1 coal classes scored at clamp(EIA-930 coal, 923 net, 923 net + CEMS station service), one rule for all nine ISOs; gas stays on 923 + the existing combined reconcile; gas coverage routed to a plant-attribution intake. Scorer + rubric bump + bench regeneration in a governance lane; supersedes PJM-NEXT-21's "Keep EIA-923" for **coal only** | All nine ISO determinations as under B. **SPP train scope stays CALIBRATED** (PRB 2025 passes); PJM COAL_BIT 2019/2025 pass (PJM still NOT-YET on 2020–23, 2025 CC); SPP PRB 2022 passes, 2021 misses on share by 0.14 pp; ERCOT/SOCO coal targets move ≤ +1.5 TWh, MISO/NWPP ~0 |
| B | Keep EIA-923 (status quo) | Nothing. SPP-87 Q1, SPP 0a and the PJM coal question close as "benchmark stays net"; SPP's 2021/22/25 PRB and PJM's 2019/25 COAL_BIT remain model misses | NYISO NOT-YET; **SPP train scope NOT-YET** (PRB 2025 +10.2); PJM fuelmix adds 2025; the rest unchanged |
| C | Dual-report | Gate on 923 (as B); C1 publishes the 930c coal column and the 930a gas column as report-only beside each record, so the basis gap is visible without moving a verdict | As B |
| D | Full 930-aligned (coal + CHP-first gas coverage, 930a) | As A, plus the gas metering-coverage leg | ISO determinations as A; NWPP fuelmix moves to 2021/22 (from 2025); CAISO 2019 CC_CHP fails; not recommended — the gas leg's allocation flips 4 vs 8 different records (§5.1) |

**Why A:**
- **Structure, not fit (rules 1 and 14).** The model serves the BA's EIA-930 demand, and its coal is dispatched on gross-capable capacity (SPP-87 §0.2). A net benchmark is therefore a boundary misalignment, which is exactly the case where rule 14 allows a reconciled form of the real data.
- **No free parameter, no per-ISO knob.** The construction has zero free parameters and both bounds are measured. It is neutral wherever a BA books net (ERCOT, SOCO), and it falls back to net wherever a BA's coal cell is incomplete (MISO, NWPP).
- **It moves misses in both directions** (§5.1).
- **What argues against it:** PJM's position between the bounds is not identified (§7). If that weighs heavily, C is the fallback that loses nothing.

Not decided here, and not to be decided by the card: any rubric text, the 2025 regeneration, and the gas-coverage leg.
