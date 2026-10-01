# FINDING — R-ERCOT-21 phase 0: the 2022 CC_REGULAR under-run, and the Wharton CC heat rate

Date 2026-10-01. Keeper `2026-09-30-r-20-gt-split` (bundle `results/calibration/r_ercot20_span`). **Zero LP.**

- Per-plant reads use the keeper's own legs (provenance only, rule 33(d)): 2022 `d7f8082b`, 2024 `0bc8822a`.
- The benchmark frames were rebuilt at zero LP with `run_calibration_full.build_benchmark_frames` on the 2022 leg.
- Probe: `scripts/probes/_r_ercot21_cc2022_decomp.py` → `r_ercot21_cc2022_decomp.json`.

## 1. Task 1: where the 2022 CC_REGULAR −8.83 TWh lives

### 1.1 It is not a CC object. CC is the mirror of coal.

Scorer basis (`apply_other_fossil_scoring` on both sides, VRE on EIA-930):

| Class | Model TWh | Actual TWh | Δ |
|---|---|---|---|
| CC_REGULAR | 123.76 | 132.59 | **−8.83** |
| COAL_PRB | 60.17 | 54.18 | **+5.99** |
| COAL_LIGNITE | 17.70 | 17.07 | +0.63 |
| CC_CHP | 26.74 | 25.65 | +1.09 |
| wind + solar | 132.39 | 131.05 | +1.34 |
| CT_PEAKER / ST_GAS / nuclear | | | −0.95 / −0.67 / −0.52 |
| **Total generation** | 429.13 | 430.46 | **−1.33** |

The CC deficit is offset by coal (+6.62), CC_CHP and VRE. Total generation misses by only −1.3 TWh.

### 1.2 By plant: broad, every efficient merchant CC

- All 42 model CC_REGULAR plants match an EIA-923 row. None is missing.
- Under-runners sum to −17.5 TWh, over-runners to +6.8. The largest under-runners are Freestone −1.86, Guadalupe −1.55, Temple −1.50, Bosque −1.39, Forney −1.25 and Rio Nogales −1.18 TWh.
- **Availability does not bind.** Model available 208.1 TWh against 123.8 dispatched and 134.5 actual. Only one plant's actual exceeds its model availability: Lost Pines (§3).

**Coal, by plant (model − EIA-923):**

| Plant | Δ TWh | Note |
|---|---|---|
| Martin Lake 6146 | **+4.16** | |
| Coleto Creek 6178 | **+1.72** | |
| W A Parish 3470 | +1.08 | |
| Limestone 298 | +0.81 | |
| Sandy Creek 56611 | +0.74 | |
| Fayette 6179 | **−2.84** | runs on 58 % of its availability |

### 1.3 By month and hour class: summer, and both peak and off-peak

Monthly CC Δ (GWh, gross of BTM): `−345 −593 +165 +276 −493 −1975 −1708 −1920 −2120 −956 −234 −533`. **June–September carry −7.7 of the −10.7 TWh gross.** Coal over-runs most in the same months (+1.35 / +1.00 / +0.69 / +0.91 TWh).

| Season × time | CC Δ TWh | Coal Δ TWh | CC headroom in merit | CC headroom out of merit |
|---|---|---|---|---|
| summer on | −4.05 | +2.10 | 0.53 | 11.6 |
| summer off | −1.84 | +1.91 | 0.57 | 11.9 |
| shoulder on | −1.55 | +0.07 | 1.06 | 17.9 |
| shoulder off | −1.08 | +0.58 | 0.53 | 14.1 |
| winter on / off | −1.32 / −0.60 | +1.27 / +0.69 | 0.91 / 0.40 | 16.4 / 9.3 |

- **Not a shoulder-hour object.** It is summer, and spread across load quartiles: −2.75 / −2.57 / −1.97 / −3.16.
- **CC is priced out, not short of capacity or commitment.** Undispatched CC capacity whose offer is in merit (mc ≤ price + $0.50) totals 4.0 TWh all year; out-of-merit headroom is 81 TWh. No CC availability or commitment lever has room to act.

### 1.4 The coal object is offer and cycling conduct (FENCED)

Martin Lake, summer 2022, mean MW by hour of day:

| Hour | Actual (CEMS) | Model | Available |
|---|---|---|---|
| 00 | 853 | 2,123 | 2,265 |
| 04 | 840 | 2,097 | 2,264 |
| 08 | 906 | 2,150 | 2,264 |
| 12 | 1,716 | 2,208 | 2,280 |
| 16 | 1,896 | 2,222 | 2,280 |
| 20 | 1,621 | 2,186 | 2,275 |

- Actual p95 reaches full capacity in every month, so the units were available. Martin Lake cycled about 1 GW off overnight; the model runs it flat. Its offer mc (p50 $22) is in merit in 100 % of hours.
- Coleto shows the same pattern, plus whole offline days (summer p05 = 0).
- This is the object R-ERCOT-10 already named ("static coal offers vs $6.45 gas"). The coal offers are measured on 2024–25 SCED and carry no 2019–22 conduct. **Coal offers are fenced, and the owner data decision on the 2019–22 SCED key is CLOSED.**
- **Task 1 closes with no admissible arm.** Per R-ERCOT-19/20, any CC-dispatch lever would trade 2022 C1 against 2024 C3a.

### 1.5 Display-only defect (routed)

The bench's per-plant display rows (`bench.plants`) omit 7512, 55501 and 55545: 10.04 TWh of 2022 CC_REGULAR that `classFull` does count. The scorer is unaffected (`classFull` is correct), but the Run Explorer's plant panel under-shows actual CC. Routed to the dashboard lane.

## 2. Task 2: Wharton CC heat rate (rule 14)

### 2.1 The EIA-923 CC-only identity rate

Total fuel / net generation over CT + CA + CS prime movers is what `derive_campd_cc_heat_rates.eia923_identity_rates` already computes (R-CAISO-3). For Wharton 3469:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| EIA-923 CC identity | 9.76 | 9.85 | 9.18 | 9.27 | 9.88 | 9.55 | 9.68 |
| eGRID PLHTRT (applied today) | 11.68 | 11.67 | 11.51 | 11.84 | 10.59 | 10.43 | 10.43 |

The eGRID value is a plant average that includes the simple-cycle GTs. It is the wrong boundary for the CC-only parent since R-ERCOT-20.

### 2.2 Two facts the card must carry

**(a) The committed ERCOT artifact is stale against its own deriver.** `campd_cc_heat_rates_ERCOT.csv` predates R-CAISO-2/3. Re-running the HEAD derive changes 14 applied rows: `ok` rows whose CAMPD gross reads below EIA-923 net are re-priced at the identity rate.

| Plant | Change (MMBtu/MWh) |
|---|---|
| Silas Ray 2022/23 | −2.6 / −3.1 |
| Sam Rayburn 2020/21 | −0.8 / −1.9 |
| Bosque, every year | −0.4 to −0.8 |
| Wise County 2019/21/22 | −0.3 to −0.5 |
| Tenaska Gateway 2024 | −0.26 |
| Gregory 2021 | −0.7 |

The HEAD derive also **drops Jack Fusco 55357** (all 8 rows). It is DAM-membership-admitted (EIA-860 BA MISO), and the derive's EIA-860 fleet does not apply the admission. A regen therefore needs that seam fixed first, or Fusco silently loses its measured rate.

**(b) Extending the identity to `steam_not_metered` rows** adds one key to `_EIA923_IDENTITY_REFUSALS`. It is zero DOF and the same mechanism (rule 19).

| Plant | Change (MMBtu/MWh) |
|---|---|
| Wharton | −2.57 (2022), −0.88 (2024) |
| Cedar Bayou 4 | +0.26 (2022), **+1.01** (2024) |
| Sam Rayburn | +0.98 / +0.94 |
| Gregory | −0.24 / −0.36 |
| Lost Pines | +0.16 |
| T C Ferguson | +0.05 / +0.09 |

Where the identity is higher than eGRID (Cedar Bayou 4, Sam Rayburn), the CEMS heat input sits below EIA-923 fuel. That is the signature of an un-metered HRSG or duct-burner stack.

**Dispatch-weighted mean change:** −0.055 (2022) and −0.023 (2024) MMBtu/MWh, over about 17 TWh of plants. It is a per-plant reshuffle with a near-zero level shift.

### 2.3 The accurate input moves Wharton the wrong way, so it does not fix the over-run

- Wharton's CC half runs 3.17 TWh in 2024 against 0.56 actual. Its offer mc (p50 $25.0) sits level with Lost Pines' ($24.4), a 2001 CC.
- The identity lowers Wharton's base rate, so it would run **more**. Rule 14 still says take the accurate input.
- The over-run's root cause is the **class** CAMPD marginal-HR multipliers (CC_REGULAR p50: committed 0.674, econ-low 0.825, econ-high 0.95; n = 120 units, mostly 2000s F-class) applied to a 1974 plant.
- Wharton's own marginal curve cannot be measured from CAMPD, because its steam turbine is not metered (`steam_not_metered`). **No measured per-plant input exists today.** Routed: a per-plant marginal-HR estimator for steam-not-metered CCs would be a new derive. It is not built.

## 3. New rule-14 finding: Lost Pines 1 (55154) is modelled as a CHP. It is not one.

- **The sheet row.** CC_REGULAR, `Bin_Label SC_CHP3`, `Turbine_Class "E-class (CHP)"`, `Pct_Must_Run 60` (the only CC_REGULAR row with a must-run share). Non-coal must-run is treated as host steam and **removed from the LP** (`assembly.py`). The LP therefore sees 244 of 609 MW.
- **The bench nets the same share out.** It subtracts that 60 % of its EIA-923 output as BTM (1.88 TWh 2022, 1.64 TWh 2024).
- **EIA-860 (2022 plant file).** Sector 1 (Electric Utility, LCRA), **FERC Cogeneration Status N**, grid 345 kV, 2 × 202.5 MW CT + 204 MW CA (a 2×1, though the sheet says 1×1). It has no steam host.
- **Effect.** C1 is neutral to first order, because both sides net the same 60 %. The LP, however, is short about 365 MW of efficient CC supply in every year (eGRID 7.1). Correcting it **lowers** prices in all years.
- **Measured committed %.** Lost Pines is absent from `cc_committed_pct.csv`, so a corrected row needs a declared tuple.

## 4. Predictions if both §2(b) and §3 are built (zero LP, before any solve)

| Item | Prediction |
|---|---|
| 2022 C1 CC_REGULAR | −8.83 → −8.9 to −7.9. Lost Pines model +1.5 to +2.2 vs bench +1.88; Wharton / Bosque cheaper, +0.3 to +0.9. **Crossing to PASS is possible, not expected.** |
| 2024 C3a | −9.9 % → −10.4 to −9.9 %. 365 MW of cheap CC is added and Wharton gets cheaper. **2024 is likely to flip to NOT-YET** (0.1 pp margin). |
| 2025 C3a | −8.2 → −8.8 to −8.2 %. |
| 2019 / 2020 C3a | (+25.7 / +7.1 %): −0.2 to −0.7 pp (favourable). |
| Wharton 2024 | 3.17 → 3.3 to 3.8 TWh (moves away from the 0.56 actual, §2.3). |

This is the trade R-ERCOT-19/20 recorded: anything that adds cheap CC supply helps 2022 C1 and costs the 2024 C3a edge. Both corrections are argued on rule 14 accuracy, not on the residual.
