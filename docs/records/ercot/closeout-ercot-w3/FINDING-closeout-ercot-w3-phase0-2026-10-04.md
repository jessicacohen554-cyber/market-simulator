# FINDING: ERCOT close-out w3, phase 0 (zero LP)

Lane `closeout-ERCOT-w3`, desk session_01ERkBTm23ZAP4CTZnJVD9Ss, 2026-10-04. Branch `claude/closeout-ercot-w3` from `main` 90cea720.
Keeper `2026-10-02-closeout-l1-coal-fuel` (bundle `results/calibration/closeout_ercot_l1_span`, solved at 106d6bb7), rubric v3.20.
Everything here is read from the keeper's committed sidecars (`hourly/unit_marginal_<Y>`, `system_<Y>`), `data/raw/_validation-source/actual_lmp_{hourly,zonal}_ERCOT.parquet`, EIA-923 and CAMPD.

## Headline

1. **New structural defect, measured: the coal per-plant offer curve is priced across its own cliff.** ERCOT-144 prices each coal committed/econ tranche at the capacity-weighted mean of the plant's measured SCED curve over the tranche's window. Fayette's curve offers 1,042 of 1,634 MW at $14–20 and the rest at $99–150. Its econ tranche window straddles that step, so the whole tranche (586 MW) is offered at **$80.13 in every year**. The ~30 % of it that was really offered at ~$17 never runs at the $17–80 prices that fill most hours. ERCOT-144 declared this as a bound (PRECOMMIT-ercot144 §5 item 3). Nobody has tested it. The matrix has no row for it.
2. **The plant record shows it.** Fayette under-runs EIA-923 in **every** year: −3.85 / −3.44 / −3.61 / −2.86 / −2.34 / −2.19 / −2.73 TWh (2019–2025). That includes 2024–25, when the curve is that year's own measured conduct. Sandy Creek has the same shape at a smaller scale (a $34.8 → $65 step inside its econ window, priced at $43.07).
3. **Candidate 1 (built): `coal_perplant_cliff_split`.** Split the econ tranche at the largest measured price step inside its window. The unchanged window construction then prices each side on its own side of the step. Zero parameters, no new data, same measured curve.
4. **The 2024 C3a decomposition is new evidence against the frontier text.** The −11.3 % is a load-zone-versus-hub basis spread over **every** zone, not only the West pocket. Against the zone-hub prices the model is −3.9 %. This needs a ruling, not a build (§3).

## 1. Failing records, decomposed

| Record | Keeper | What carries it |
|---|---|---|
| C1 2019 CC_REGULAR / COAL_PRB | +9.21 / −10.79 TWh (band ±8.0) | coal plants (model − EIA-923, TWh): Fayette −3.85, Martin Lake −3.23, Sandy Creek −1.95, Parish −0.95, Spruce −0.60, Oklaunion −0.46 |
| C1 2020 CC_REGULAR / COAL_PRB | +10.17 / −11.85 | Martin Lake −5.95, Fayette −3.44, Parish −1.61, Sandy Creek −1.40 |
| C3b 2019 / 2020 | 0.216 / 0.208 (≤ 0.20) | 2019: Aug +27.6 $/MWh (scarcity tail), Jul +8.5, Sep +7.4, Oct −7.8, Nov −5.3; 2020: Aug +9.1, Jul +6.3, Jun +5.6, Mar −8.8, Feb −6.7 |
| C3a 2024 | −11.3 % (model $27.65 vs LZ-load-weighted $31.17) | §3: hub-vs-LZ basis $2.40, energy level −$1.13 |

The 2019/20 coal under-run splits into two parts:

- **Year-specific: Martin Lake, Parish.** On their 2021–25 rows these plants are near zero or over. Their 2019/20 conduct is the R-32 DATA-LIMITED object (row ERCOT-F1). Nothing here re-opens it.
- **Persistent: Fayette (every year), Sandy Creek (2019–21).** These miss whatever the year's conduct was. That is a representation defect, and §2 sizes it.

## 2. The cliff (candidate 1)

The construction is in `legacy_bins._coal_perplant_levels`. Plant rows are stacked in tranche order, and each committed/econ window `[lo, hi]` maps onto the measured curve. The level is the capacity-weighted mean price over the window. On the keeper, Fayette's econ window is 50–95 % of plant capability, which is 817–1,552 MW of the 1,634 MW curve. It holds 225 MW at $17–20 and about 510 MW at $99–122. The level comes out at $80.13. Sandy Creek's econ window holds 70.6 % of its MW at $33.9 and 29.4 % at $65; its level is $43.07.

Zero-LP static reach. Split each econ row at the cliff. Dispatch each side wherever the keeper's own zonal price clears its side's level, on the keeper's hourly econ availability. Prices are held fixed, so this is an upper bound on MWh.

| Year | Fayette + Sandy Creek added coal TWh | Static re-clear ΔLW price (upper bound, $/MWh) |
|---|---|---|
| 2019 | +1.57 | −0.79 |
| 2020 | +1.40 | −0.83 |
| 2021 | +1.64 | n/a |
| 2022 | +1.59 | −0.24 |
| 2024 | +1.33 | −0.27 |
| 2025 | +1.52 | −0.26 |

The price column backs the added MW out of the top of each hour's dispatched stack. The stack includes floor-held units with high costs, so the column overstates the drop.

What this reaches:

- **C1 2019 CC_REGULAR:** +9.21 → about +7.8 (FAIL → PASS predicted).
- **C1 2019/20 COAL_PRB:** about −9.3 / −10.4 (closer, still FAIL).
- **C1 2020 CC:** about +8.8 (still FAIL).
- **Fayette's plant record** improves by +1.2 to +1.5 TWh in every year.

Declared risks: 2025 C3a (−9.2 %, $0.28 of headroom) and 2024 C3b (0.198) sit on their lines. 2024 C3a gets worse.

## 3. 2024 C3a: a load-zone basis, not only the West pocket (needs a ruling, not a build)

The C3a actual is LZ settlement prices weighted by zonal load (`derive_actual_lmp.ERCOT_MODEL_ZONE_TO_LZ`). Gap by model zone, 2024 ($/MWh contribution to the −3.53 load-weighted gap):

| Zone | Load share | Model | LZ actual | Contribution |
|---|---|---|---|---|
| West (LZ_WEST) | 0.151 | 26.43 | 35.51 | −1.37 |
| South_Central (AEN/CPS/LCRA) | 0.161 | 28.17 | 33.30 | −0.83 |
| South (LZ_SOUTH) | 0.081 | 27.45 | 34.17 | −0.54 |
| Houston | 0.267 | 27.45 | 29.21 | −0.47 |
| North | 0.308 | 28.20 | 29.26 | −0.33 |

In 2024 every LZ prices above HB_HUBAVG: West +8.88, South +3.58, LCRA +2.88, AEN +2.46, CPS +2.11 (annual means). 2025 has the same pattern (West +9.72, LCRA +5.08, AEN +3.44). The frontier row ERCOT-F2 attributes the miss to the West Permian pocket, but West carries only 39 % of it.

Against each model zone's own hub (Houston → HB_HOUSTON, North/Northeast → HB_NORTH, South/South_Central → HB_SOUTH, West → HB_WEST), the model reads −3.9 % in 2024 and −1.6 % in 2025. On that same basis, 2019/20 would read +11.0 / +11.4 %.

A one-bus-per-zone LP has no intra-zonal congestion, which is what puts load buses above hub buses. `internal_congestion_split` is G, so there is nothing to build. This is a reference-definition question for the owner (rule 14's aggregation-mismatch clause; under rule 37 it is a rubric matter). It goes to the desk as an ask, with the 2019/20 consequence stated.

## 4. Candidates ranked by reach on the failing records

| # | Candidate | Matrix | Reach | Disposition |
|---|---|---|---|---|
| 1 | `coal_perplant_cliff_split` (this lane) | new row, U | C1 2019 CC FAIL → PASS predicted; PRB 2019/20 −1.5 TWh closer; Fayette closer in every year | **BUILD** (PRECOMMIT) |
| 2 | Zone-hub reference for ERCOT C3a | rubric | 2024 C3a PASS; 2019/20 C3a FAIL | owner ask (rule 37), no build |
| 3 | Decker Creek ST / DeCordova CT membership gap (w2 FINDING §2) | Q5 (D-P2) | 2019/20 summer supply +1 GW; w2 static reach worsens 2019 C3a | owner-gated (Q5); unchanged |
| 4 | 2019–22 per-plant coal conduct (Martin Lake, Parish) | `coal_perplant_offer_level` K, R-7 | the year-specific half of C1 2019/20 | DATA-LIMITED (R-32/R-65) |
| 5 | Model low-price hours sit at CC econ $16–17 while actual clears $9–12 (2019: 1,558 h below $15, contribution +0.86 $/MWh; 2024: +2.01) | trough diagnosis §§7–10 | C3a/C3b in every year | adjudicated (`DIAGNOSIS-ercot-trough-price-formation`); no new driver |

Candidates 2–4 need the owner or data. Candidate 5 has no new evidence beyond the adjudicated trough record. The lane builds candidate 1.
