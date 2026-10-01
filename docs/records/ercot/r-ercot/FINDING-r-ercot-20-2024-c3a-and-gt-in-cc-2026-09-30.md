# FINDING — R-ERCOT-20 phase 0: the 2024 C3a deficit, the econ-vs-DAM test, and simple-cycle GTs binned inside CCs

Date 2026-09-30. Keeper `2026-09-30-r-19-eia-923` (bundle `results/calibration/r_ercot19a_span`). **Zero LP.**
Per-plant reads use the keeper's own 2024/2025 legs (provenance SHAs `adfb6b34` / `29adb883`; their `system_<Y>.parquet` is byte-identical to the keeper bundle's).

Probes and records:

| Probe | Record |
|---|---|
| `scripts/probes/_r_ercot20_c3a_decomp.py` | `r_ercot20_phase0.json` |
| `scripts/probes/_r_ercot20_marginal_setter.py` | `r_ercot20_marginal_setter.json` |
| `scripts/probes/_r_ercot20_econ_vs_dam.py` | `r_ercot20_econ_vs_dam.json` |
| `scripts/probes/_r_ercot20_cc_gt_census.py` | printed (below) |

## 1. Task 1 — where the 2024 C3a gap lives

The probe reproduces the scorer: model 27.84 vs actual 31.18 $/MWh, gap −3.35 (−10.7 %).

**Zones carry none of it.** On the scorer's basis (each zone weighted by its own demand on both sides), the zonal-spread component is identically zero. The gap is 100 % system-level. The per-zone split below only shows where load sits relative to the actual zonal premia (actual LZ_WEST +$6.3 over the system; model spread ≈ 0 in every zone), so it is not a C3a lever.

**By actual system price (2024):**

| Band | Hours | Load share | Model $ | Actual $ | Contribution $/MWh | Share of gap |
|---|---|---|---|---|---|---|
| ≤ $15 | 2,232 | 22.7 % | 16.36 | 8.44 | **+1.80** | −54 % |
| $15–25 | 3,458 | 39.7 % | 23.70 | 20.10 | **+1.42** | −43 % |
| $25–40 | 1,928 | 23.2 % | 31.05 | 30.79 | +0.06 | −2 % |
| $40–100 | 950 | 11.8 % | 42.97 | 58.43 | **−1.83** | 55 % |
| > $100 | 192 | 2.6 % | 93.46 | 277.13 | **−4.80** | 143 % |

- Capped at $100 on both sides, the 2024 gap becomes **+$0.94** (model above actual).
- By hour of day, 16–20 h carries −$4.18 (125 %); every other window is positive (+$0.15 to +$0.31).
- By month: May −$1.32, Aug −$0.79 and Nov −$0.66 carry most of it.
- 2025 has the same shape: ≤ $40 +$2.46, $40–100 −$2.63, > $100 −$3.41. 2022 too: > $100 −$12.10.

**Who sets the P1 price.** The setter is the partly-loaded unit whose mc is within $0.50 of the price.

| Setter (2024) | Hours | Contribution $/MWh |
|---|---|---|
| non-thermal (storage / reserve-coupled dual) | 895 | **−2.89** |
| ST_GAS econ ramp | 1,148 | −0.82 |
| CC_REGULAR econ ramp | 2,673 | **+0.41** |
| CC_CHP econ ramp | 693 | +0.20 |

In hours above $100, 47 % are set by non-thermal duals. In troughs (≤ $15), CC_REGULAR econ sets 39 % of hours. The actual SCED marginal fuel is not measurable from committed data.

**Hypotheses:**

- **(a) Over-committed CCs depress shoulder prices — REFUTED on sign.** CC-set hours are over-priced (+$0.41). The $25–40 band is on (+$0.06). Troughs are too *high*, not too low.
- **(b) A tight-hour deficit — CONFIRMED as dominant, but it is not new.** It is the compressed-distribution object R-ERCOT-12 closed (C3b/C3c; scarcity exhaustion ercot-95…231). The new decomposition (non-thermal setters, the 16–20 h window) adds no admissible zero-DOF lever. **Not re-opened.**
- **(c) A fuel-basis level issue — REFUTED.** The gas-marginal $25–40 band is within $0.26 (0.9 %).

**Task 1 closes with no arm.**

## 2. Task 2 — model econ tranche vs 60-Day DAM at the same loading point

- **Method.** For each plant-month, compare the price at loading fraction f of capacity: the model's CC_REGULAR tranches against the summed DAM step curves of the plant's CC configurations (online hours, monthly median).
- **Sites.** The accepted crosswalk has 13 CCs. Six name- and QSE-evident sites were added for this diagnostic only (THW_CC1/2, SANDHSYD_CC1, B_DAVIS_CC1, RAYBURN_CC1, SILASRAY_CC1). They are not added to the crosswalk.
- **Matched:** 10 plants in 2024, 9 in 2025.

| f | corr(HR, model offer rel. to fleet median) | corr(HR, DAM offer rel. to fleet median) |
|---|---|---|
| 0.6 (econ mid), 2024 | 0.80 | 0.80 |
| 0.6 (econ mid), 2025 | 0.68 | 0.71 |
| 0.4, 2024 | 0.73 | 0.48 |

**At the econ segment the model scales with heat rate as reality does.** There is no robust HR-dependent discrepancy on the econ tranche. The sample is thin (one plant has HR > 9), so this is not carded as a design. **Task 2's object is not an offer-shape defect.** What it is follows in §3.

## 3. The actual object — simple-cycle GTs binned inside CC_REGULAR plants (rule 14)

The single largest 2024 over-runner is **T H Wharton (3469)**: model 5.33 TWh, EIA-923 0.67 TWh (7.96×).

- ERCOT registers it as two CC configurations, THW_CC1/CC2 (665 MW HSL), **plus six simple-cycle GTs** THWGT51–56 (~360 MW).
- CAMPD types units 51–56 as "Combustion turbine". EIA-860 prime mover is GT (526 MW nameplate).
- The model bins **all 985 MW as one CC_REGULAR plant** (= CAMPD CC + GT max-load sum). The GTs are therefore priced on the CC econ ramp (~0.70 × the plant's eGRID base HR of 10.43).

**Census** (EIA-860 2024 prime movers of every plant the keeper bins as CC_REGULAR):

| Plant | Model cap MW | GT nameplate MW | Model TWh 2024 | EIA-923 CC TWh | EIA-923 GT TWh |
|---|---|---|---|---|---|
| 3469 T H Wharton | 985 | 526 | 5.33 | 0.557 | 0.115 |
| 7900 Sand Hill | 577 | 308 | 2.89 | 1.669 | 0.466 |
| 56350 | 502 | 74 | 3.19 | 2.378 | 0.053 |
| 3559 Silas Ray | 123 | 61 | 0.44 | 0.064 | 0.039 |
| **Total** | | **969** | **11.85** | **4.67** | **0.67** |

- 2025: three plants, 908 MW GT; model 10.88 TWh vs 4.35 + 0.64 TWh.
- EIA-923 GT generation at these plants is 0.41–0.82 TWh/yr, 2019–2025.
- **The bench already books those GT rows as CT_PEAKER** (`classFull` classifies row by row). The model books the same capacity's dispatch as CC_REGULAR, so C1 compares mismatched boundaries at these four plants.
- **Precedent.** This is the same defect class as R-ERCOT-11 (Parish) and 49392 (Barney Davis): a mixed plant whose second technology needs its own split-child row (`scripts/tag_mixed_plants.py` convention `code*10+3` for CT).
- **Prior status.** The measured_ct_heat_rates lane recorded Wharton among 9 mixed-facility CT plants "for the class-composition ruling". That lane was surfaced, never run. No matrix cell is R/I/G.
- **Out of scope.** The ST_GAS mixed plants (Braunig 3612, 3628, 6243, 3576) are murkier (model ST caps sit below ST nameplate), so they are left out of scope and routed.

**Direction, predicted before any build.**

- The GT MW leave the CC econ ramp for the CT_PEAKER stack (measured CT heat rates, class CT offers). Shoulder and peak supply get dearer.
- Expected: 2023–2025 C3a moves up (toward the band); 2019/2021 C3a (already positive) worsens.
- CC_REGULAR model energy falls by the GT share of these plants' dispatch, minus back-fill by efficient CCs that under-run today (0.8–0.9×). **2022 C1 CC_REGULAR (−7.69 vs ±8.00) is the named risk.**
- This is a rule-14 boundary correction with zero DOF. It is argued on accuracy, not on the residual.
