# RESULT — SCORER-COAL-1: the C1 fossil reconcile's coal allocation, measured across every keeper (ZERO LP)

Lane SCORER-COAL-1, from `HANDOFF-scorer-coal-reconcile-2026-09-29.md` (owner card "Route to scorer lane", NWPP-NEXT-11).
Base `origin/main` `0a5eb910`. No solve, no registration, no promotion, **no scorer change landed** (see §5).
Probe: `scripts/probes/_scorercoal1_reconcile_options.py` (reads committed bench parts, sidecars, payloads, attestations).

## 0. Headline

1. The uniform reconcile fires in **17 of 63** keeper ISO-years. In 12 of them coal is material: NWPP 2019–24, SPP 2023–25, MISO 2019 and MISO 2025.
2. **The combined EIA-930 gap sits on a different fuel in different ISOs.** No single ISO-agnostic coal rule is right everywhere:
   - **NWPP:** the gap is on **gas** (−10 to −12 TWh every year). 923 coal ÷ CEMS is stable at 0.917–0.928. Coal-at-923 is right here.
   - **SPP 2023–25:** the gap is on **coal**. SPP books coal in EIA-930 near CEMS **gross** (station service, 7.5–8.5 TWh; SPP-87 hourly fit, slope 0.97–1.04). Raw 923 gas and 930 gas agree within 0.8 TWh (SPP-88). Coal-at-923 moves coal's station service onto the gas targets.
   - **MISO 2019:** the gap is in EIA-930's coal cell (−15.9 TWh). That cell runs 17–21 TWh below CEMS in every MISO year, per the docstring. 930 gas matches 923 gas within 0.8 TWh. Coal-at-923 moves 15.9 TWh onto gas, which contradicts both sources.
3. **Determination moves.** Options (a) and (b) each flip **SPP's train-tier (2023–25) determination from CALIBRATED to NOT-YET**. The cause is the misattribution in item 2, not a model miss. Every other ISO's determination is unchanged under both options. NWPP's coal misses shrink by 2.5–5 TWh, with no status change.
4. **Recommendation: keep the status quo.** Route the attribution to the all-ISO gross/net and gas-coverage basis measurement that SPP-88 §4 already put in the queue. That measurement is what could decide, per family and on data, where the gap belongs.

## 1. Measurement (TWh; k = the applied uniform factor; ISO-years where k = 1 are omitted)

Parity: re-applying the status-quo reconcile to the recovered pre-reconcile frame reproduces every committed `classFull` to ≤ 0.0001 TWh. The one exception is CAISO 2025 (0.33 TWh on the CEMS-cap path, coal 0.08 TWh), which is immaterial to coal. The options in §3 are applied as deltas on the committed `classFull`, so the status quo is exact.

| ISO-year | k | 923 coal | 930 coal | 930−923 coal | 923 gas | 930 gas (defl.) | 930−923 gas | coal Δ from k |
|---|---|---|---|---|---|---|---|---|
| NWPP 2019 | 0.868 | 65.05 | 54.55 | −10.50 | 70.75 | 62.91 | −7.84 | **−8.58** |
| NWPP 2020 | 0.916 | 52.42 | 51.94 | −0.48 | 68.63 | 58.50 | **−10.13** | **−4.40** |
| NWPP 2021 | 0.886 | 53.79 | 50.14 | −3.65 | 74.71 | 63.27 | −11.44 | −6.14 |
| NWPP 2022 | 0.891 | 53.13 | 49.41 | −3.72 | 69.61 | 59.51 | −10.10 | −5.79 |
| NWPP 2023 | 0.899 | 44.92 | 42.27 | −2.66 | 80.40 | 69.94 | −10.46 | −4.53 |
| NWPP 2024 | 0.911 | 37.81 | 38.30 | +0.49 | 84.97 | 73.14 | **−11.83** | **−3.38** |
| SPP 2023 | 1.039 | 71.99 | 78.41 | **+6.43** | 75.93 | 75.17 | −0.76 | +2.82 |
| SPP 2024 | 1.054 | 65.24 | 72.44 | **+7.20** | 81.23 | 81.88 | +0.64 | +3.50 |
| SPP 2025ᵖ | 1.081 | 78.40 | 87.70 | **+9.30** | 72.25 | 75.13 | +2.88 | +6.35 |
| MISO 2019 | 0.965 | 254.78 | 238.93 | **−15.85** | 176.08 | 176.89 | +0.81 | −8.90 |
| MISO 2025ᵖ | 1.043 | 203.24 | 192.10 | −11.14 | 200.23 | 228.81 | +28.58 | +8.78 |
| CAISO 2019–21, 2025ᵖ | 0.89–0.99 | ≤0.09 | | | | | | ≤0.01 |
| NEISO 2025ᵖ, NYISO 2025ᵖ | 1.05 / 1.08 | ≤0.27 | | | | | | ≤0.01 |

ᵖ preliminary 923 vintage; coal records are SKIPPED in C1 there.

- **923 coal ÷ `coal_cems`** (complete vintages, mean) by ISO: ERCOT 0.980, MISO 0.953, NEISO 1.072, NWPP 0.923, PJM 1.018, SOCO 0.907, SPP 0.919. The ratio is stable within each ISO, so CEMS confirms each ISO's 923 coal is internally consistent. It cannot say which fuel owns a 930 gap, because `coal_cems` has its own coverage basis. That is why G-21b only ever uses it as a ratio.
- ERCOT, PJM and SOCO never fire. PJM's +7..+11 TWh coal mis-split in 930 offsets inside the combined band.

## 2. Options, as defined before any re-score

All three keep the status quo's **trigger** (the combined ±3 % band) and its **combined target** (CAISO cap included). They differ only in how the correction is split between coal and gas (+oil).

- **(c) Status quo.** Every fossil class takes the same factor k.
- **(a) Coal at 923.** Coal stays at its own 923 grid level. Gas (+oil) takes the whole correction: gas target = combined target − 923 coal.
- **(b) Coal at CEMS × k_coal.** Coal = `coal_cems` × the ISO's complete-vintage mean of (pre-reconcile 923 coal ÷ `coal_cems`), the G-21b construction with the circularity removed. Gas takes the remainder.

Tested against the handoff's two checks:
- **The docstring's reason for abandoning the per-family reconcile** was that it trusted 930's per-fuel split. (a) and (b) avoid that: they never read the 930 coal cell. They replace it with an equally ISO-agnostic assumption, that the gap is always gas's. SPP-87 falsified that assumption on hourly data, and MISO 2019 contradicts it (§0 item 2).
- **The preliminary-vintage up-scale path.** (b) repairs the limb the docstring names, where an incomplete 923 coal family would take a proportional up-scale. In practice the CEMS anchor puts MISO and SPP 2025 coal back at their 923 level (203.1 vs 203.2 and 78.3 vs 78.4). So SPP 2025's up-scale lands on gas again, which is the same SPP defect. Every 2025 coal record is SKIPPED, so this moves no status.

## 3. Re-score of every registered run (`calibration_verdict.determine_from_artifacts`, stdlib)

11 runs: 9 keepers plus the CAISO and NYISO folded touchpoints. Only records whose status moves are listed. Full per-record actuals are in the probe output.

| run | full-span (c / a / b) | train 2023–25 (c / a / b) |
|---|---|---|
| SPP `2026-09-28-spp-100-chp-scope` | NOT-YET / NOT-YET / NOT-YET | **CALIBRATED / NOT-YET / NOT-YET** |
| MISO `2026-09-28-miso-280-splitremap` | NOT-YET ×3 | CALIBRATED ×3 |
| NWPP `2026-09-29-nwppnext10-exit-month-routing` | NOT-YET ×3 | NOT-YET ×3 |
| CAISO, ERCOT, NEISO, NYISO (both runs), PJM, SOCO, CAISO touchpoints | unchanged | unchanged |

| option | ISO-year | record | status | miss (c → option) |
|---|---|---|---|---|
| a | SPP 2024 | CC_REGULAR | PASS → **FAIL** | −6.15 → −8.02 (band ±8.00) |
| a | SPP 2024 | ST_GAS | PASS → **FAIL** | −7.65 → −8.47 |
| b | SPP 2024 | ST_GAS | PASS → **FAIL** | −7.65 → −8.32 |
| a | MISO 2019 | CC_REGULAR | PASS → **FAIL** | +4.20 → +9.47 |
| a, b | MISO 2019 | ST_GAS | FAIL → **PASS** | −8.00 → −7.14 (a) / −7.40 (b) |

NWPP C1 coal misses (no status moves; every record stays PASS):

| NWPP | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| COAL_PRB (c → a) | +5.27 → +0.26 | +4.20 → +1.69 | +3.73 → +0.33 | +5.81 → +2.46 | +4.00 → +1.17 | +3.51 → +1.44 |
| CC_REGULAR (c → a) | +0.86 → **+7.84** (2.9 pp) | +0.75 → +4.36 | −2.66 → +2.33 | −4.34 → +0.36 | −2.25 → +1.27 | +4.61 → +7.10 |

Under (a) and (b), NWPP CC_REGULAR 2019 comes within 0.16 TWh and 0.1 pp of the C1 band.

Number of gated C1 records whose actual moves (a / b): NWPP 48, SPP 16, CAISO 10 (≤0.01 TWh), MISO 8. ERCOT, NEISO, NYISO, PJM and SOCO: 0.

## 4. Downstream artifacts

- **NWPP plant-basis demand** (`derive_nwpp_plant_basis_energy.py`) reads `classFull` by family. Under (a) or (b), 2019–24 would move **COL up by 3.4–8.6 TWh/yr and NG down by the same amount**. The combined fossil total is unchanged. That is a benchmark-basis change to a demand input, so rule 23 applies and it would have to be argued as a data change and re-derived by NWPP's own lane. Under (c), nothing moves.
- **The C2 G-21b fallback** reads `classFull` coal for k. It only feeds SKIPPED preliminary diagnostics, so no status moves.

## 5. Decision and status

The owner decides through a decision card. Nothing lands before the ruling. Rule 1 applies: the SPP flip is not the argument against (a) and (b). The argument is that SPP-87's metering evidence and MISO 2019's two-source agreement on gas falsify their shared assumption. The NWPP improvement is not an argument for them either.

## 6. Owner ruling (decision card, 2026-09-29): "Status quo + route (Recommended)"

- `reconcile_vintage_classes` is unchanged. No rubric bump, no bench re-render, no status rebuild, no keeper file touched. Every determination stands as committed.
- The NWPP plant-basis demand artifact is untouched, so rule 23 is not engaged.
- **Routed:** the all-ISO benchmark-basis measurement, meaning coal gross vs net per ISO, gas 923-vs-930 coverage, and coverage breaks (SPP-88 §4 successor 1). It is extended with this lane's question: on measured data, which family owns each fired year's combined gap. Handoff: `HANDOFF-benchmark-basis-all-iso-2026-09-30.md`.
- NWPP's COAL_PRB 2020 "+4.20 TWh" stays on the record as it is now. Per this table, ≈2.5 TWh of it is the reconcile factor (NWPP-NEXT-11 §1). This is reported, not rescored.
