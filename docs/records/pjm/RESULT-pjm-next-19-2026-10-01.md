# RESULT — PJM-NEXT-19: the real offer stack is not the year lever; CC 2023 is a zonal offset plus benchmark drift (zero LP)

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`). Run-level, training tier 2023–2025 and ISO (v3.13) all read **NOT-YET**. Same 10 failing cells.

**Solves:** none. No PRECOMMIT (nothing reached card 3). Probes and artifacts:

| probe | artifact | card |
|---|---|---|
| `scripts/probes/_pjmnext19_cc_vs_coal_stack.py` | `results/phase0/pjm/_pjmnext19_cc_vs_coal_stack.json` | 1 |
| `scripts/probes/_pjmnext19_coalset_balance.py` | `results/phase0/pjm/_pjmnext19_coalset_balance.json` | 1b |
| `scripts/probes/_pjmnext19_cc2023_tracking.py` | `results/phase0/pjm/_pjmnext19_cc2023_tracking.json` | 2 |

**Offers corpus:** a declared seasonal sample, Jan/Apr/Jul/Oct of 2019, 2020, 2021, 2023, 2024 and 2025 (24 month-files, DataMiner2 throttled to ~1 page/min/process). 2022 was not fetched: it is neither a COAL_BIT miss year nor a fit-year control.

## 1. Card 1 — real offers vs the model in model-coal-set hours

The offers feed carries no fuel. Its CC_LIKE physics bucket (min-run 2–16 h, ecomin > 20 %) also captures coal and gas-steam units, so it is not a CC identity. Two consequences:
- Real offered thermal MW exceeds the model's available MW by ~45 GW (units on outage still post offers). **Only shares are comparable.**
- A gas-tracking tag (unit's daily mid-curve offer correlated ≥ 0.6 with delivered gas) is a diagnostic identity, reported at 0.5/0.6/0.7 in the JSON.

Share of each side's offered thermal MW below the hour's price (coal-set hours in the sampled months):

| | 2019 | 2020 | 2021 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| hours scored | 941 | 694 | 437 | 380 | 557 | 299 |
| below model coal offer: model / real | .644 / .674 | .669 / .692 | .656 / .678 | .678 / .681 | .677 / .713 | .670 / .760 |
| **real − model** | +.030 | +.023 | +.022 | +.002 | **+.036** | +.090 |
| below actual RT: real − model | +.054 | +.042 | +.068 | +.022 | **+.086** | +.183 |
| CC MW at ≤ 6.5 × gas: model / real gas-tracking | .455 / .575 | .457 / .477 | .443 / .479 | .390 / .349 | .346 / .498 | .348 / .541 |

**Reading.** The real stack is modestly cheaper than the model's in every year. The gap is as large in fit year 2024 as in the miss years 2019–2021. **Not year-discriminating; not the COAL_BIT lever.**

## 2. Card 1b — where the coal over-run sits

Model − CAMPD-bench (rescaled to EIA-923), TWh:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| coal, coal-set hours | +4.7 | +2.1 | +2.6 | +2.6 | +0.1 | −0.2 | +1.7 |
| CC_REGULAR, coal-set hours | +2.4 | +2.7 | +0.5 | +1.9 | +0.8 | −0.3 | −0.9 |
| **coal, other hours** | **+11.9** | **+8.0** | **+14.4** | +7.4 | −1.1 | −0.1 | +12.5 |
| CT_PEAKER, other hours | −4.5 | −4.5 | −8.1 | −5.3 | −1.9 | +0.5 | +3.4 |

- Most of the over-run is in hours where coal is **inframarginal**, and in coal-set hours CC over-runs too. It is not CC↔coal merit-order displacement.
- This matches NEXT-10 audit (a) ("response, not price") and NEXT-17 (model price level in sub-$25 hours). In 2019–2021 coal and CC costs sit within ~$3 (NEXT-16), so the same low-end price-level error moves far more coal volume than in 2023/24, when coal is out of merit in both model and reality. **Hypothesis for NEXT-20, not tested here.**

## 3. Card 2 — CC_REGULAR 2023

**(a) Zonal offset.** Model − EIA-923 by zone, TWh:

| | 2023 | 2024 |
|---|---|---|
| Dominion | **−12.7** | −4.1 |
| EMAAC | **+9.0** | −1.4 |
| Central PA | +5.1 | +4.5 |
| ComEd | +5.6 | +5.0 |
| CC offer, cap-weighted $/MWh, Dominion / EMAAC | **42.0 / 27.3** | 31.9 / 32.9 |

**(b) Gas operand.** Dominion's 7 CCs price from their own EIA-923 receipts. Against IMM Platts eastern spot:

| $/MMBtu | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Henry Hub | 2.57 | 2.03 | 3.91 | 6.42 | 2.54 | 2.19 | 3.53 |
| IMM eastern spot | 2.52 | 1.74 | 3.58 | 7.28 | 2.13 | 2.25 | 3.99 |
| Dominion EIA-923 | 3.41 | 2.68 | 4.07 | 7.31 | **3.76** | 3.11 | 4.16 |

Same object as NEXT-8 / NEXT-9 (corridor recorded as limit, `internal_congestion_split` G) and NEXT-13 (`pjm_replacement_cost_fuel` R). Eastern spot is not Dominion's supply point (Transco Z5, no series in repo), so this is not new evidence under that R. Recorded on `zonal_gas_basis` (stays K).

**(c) Benchmark drift, 2023 → 2024** (NEXT-16 energy identity, differenced): classFull +28.45 vs model gen +21.61 TWh; U_a −7.58. Per-plant EIA-923 and CAMPD both show PJM gas plants +17–18 TWh (EIA-930 gas +7.6), so the benchmark growth is physically real per CEMS. The model cannot follow it given EIA-930 demand and exports.

**Verdict:** no admissible, year-discriminating, zero-DOF mechanism. **OPEN, not a limit.**

## 4. Next (NEXT-20)

1. Test the §2 hypothesis directly: in 2019–2021 inframarginal-coal hours, the model's local price vs actual RT, and real coal's own-curve output at actual vs model price (NEXT-11's D/E vs Dm/E, at hour grain, coal only). If the coal response to the low-end price gap is what separates the years, the next card is what forms the real low end (sub-CC-cost clearing, 5.3–5.7 × gas).
2. U_a: identify the non-benchmark supply serving PJM load (pseudo-tied units, non-923 plants) whose 2023 → 2024 fall drives the CC 2023 tracking gap.

**Retrievability:** no bundles; the offers sample is gitignored raw (`fetch_pjm_energy_offers.py --years <y> --months 1 4 7 10`).
