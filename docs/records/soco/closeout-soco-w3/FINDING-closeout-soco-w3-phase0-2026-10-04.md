# FINDING closeout-SOCO-w3 phase 0 — SOCO injects 6–8 TWh/yr of behind-the-meter mill cogeneration as grid supply

Lane closeout-SOCO-w3, 2026-10-04. Zero LP. Chartered by the backcast close-out desk under the owner direction of
2026-10-04 ("Why are you not still running uncalibrated ISOs").

**Object.** Keeper `2026-10-03-closeout-soco-3-coalpile` (bundle `results/calibration/closeout_soco_3_span`),
rubric v3.20. SOCO is NOT-YET on one row: C1 CC_REGULAR 2019 (+3.97 TWh, share +3.2 pp; bar 3.0 pp). The 2022
C3a (−13.7 %) and C3b (NRMSE 0.282) rows are scoped ledgered caveats that still downgrade (R-8). Frontier row
SOCO-F1 signs CC 2019 as DATA-LIMITED ("when the obligated coal burns").

**Probe.** `scripts/probes/_closeout_socow3_btm_reach.py` writes `btm_footprint.csv` and `btm_reach.csv`.

## 1. Decomposition of the failing records

### C1 CC_REGULAR 2019 has two parts

| Part | Size | How measured |
|---|---|---|
| (a) Share denominator: the model generates less than the bench | **1.68 pp** of the 3.24 pp | m_gen 245.6 vs a_gen 254.8 TWh (`calibration_verdict._gen_totals`); CC share at the actual denominator reads +1.56 pp |
| (b) Night CC over-run against a flat coal deficit | the remaining 1.56 pp | CC model − CEMS by hour of day: **+1.55 GW at 00–04h**, +0.3–0.5 GW at 11–19h; COAL_BIT −1.0 to −1.5 GW in every hour (closeout-SOCO-2 §b, re-measured on this keeper) |

Part (b) is the frontier row's object (every route to night coal commitment is G/R in `SOCO.js`). Part (a) is
not in any record. It is new.

### Part (a): where the 9.2 TWh goes

The LP serves EIA-930 SOCO demand, so its total generation equals EIA-930 net generation (2019: 245.1 vs 930 NG
245.1 TWh). The bench is EIA-923 plant generation (fossil CHP host share removed). The two differ by
4.4–8.8 TWh of fossil every year, and the difference sits in the **injected must-run residual classes**:

| Year | Injected biomass + OTHER (EIA-923, keeper) | EIA-930 "Other" (telemetry) | Phantom grid supply | Model fossil − 930 fossil |
|---|---|---|---|---|
| 2019 | 9.73 | 2.12 | **7.61** | −4.4 |
| 2020 | 10.14 | 2.69 | 7.45 | −4.8 |
| 2021 | 10.12 | 2.70 | 7.42 | −5.1 |
| 2022 | 9.84 | 2.71 | 7.13 | −4.8 |
| 2023 | 8.94 | 2.54 | 6.40 | −3.7 |
| 2024 | 9.49 | 2.47 | 7.02 | −4.8 |
| 2025 | 8.58 | 1.88 | 6.70 | −4.6 |

**EIA-930 "Other" is exhaustive for SOCO.** Its fuel split reconciles to its own reported net generation:
2019 Σfuels 245.11 vs NG 245.12 TWh; 2023 0.000 %, 2024 −0.4 %, 2025 −0.01 %. So the grid sees 1.9–2.7 TWh of
"other" a year, and the model injects 8.6–10.1 TWh of it into the energy balance as price-insensitive supply.

**Why.** `run_calibration_full._must_run_profiles` injects each residual class's EIA-923 net generation with no
host-steam carve-out. SOCO's biomass is Georgia/Alabama pulp-mill black-liquor and wood-waste cogeneration:
**88–90 % of it is chp=Y** (8.55 of 9.49 TWh in 2019). Every fossil cogen class already holds its host share out
(`classify_plant` → `*_CHP`, `data.chp.chp_btm_pct`); biomass and OTHER never received that partition.

**The fix exists.** `ScenarioConfig.mustrun_chp_btm_holdout` (miso-253, default off) drops chp=Y rows from the
injected classes at the single seam both the injection and the bench read (`_eia923_frame`), so bench and model
move in lockstep. SOCO's cell is **U** (seed text only; never measured). MISO's cell is O (its screen OOM'd, no
verdict); no other ISO has measured it. Nothing transfers (rule 25); everything below is SOCO's own number.

| Year | Held out (TWh) | Injection after | EIA-930 Other | Residual error after (TWh) |
|---|---|---|---|---|
| 2019 | 8.79 | 0.94 | 2.12 | −1.18 |
| 2020 | 8.70 | 1.44 | 2.69 | −1.24 |
| 2021 | 8.53 | 1.58 | 2.70 | −1.12 |
| 2022 | 8.27 | 1.56 | 2.71 | −1.15 |
| 2023 | 7.38 | 1.56 | 2.54 | −0.98 |
| 2024 | 8.01 | 1.49 | 2.47 | −0.98 |
| 2025 | 7.12 | 1.49 | 1.88 | −0.39 |

The flag is a partition, not an export model: some chp=Y mills export surplus, so it over-removes by about
1 TWh/yr. It still cuts the injection error from 6.4–7.6 TWh to 0.4–1.2 TWh, every year, on SOCO's own telemetry
(rule 14: the measured partition beats the un-partitioned estimate; the remaining 1 TWh is stated, not tuned).

## 2. Reach (zero LP, the closeout-SOCO-w2 restack)

Method: hourly removed MW from `_must_run_profiles` with and without the holdout (≈1.0 GW flat within month);
copperplate restack of the keeper's econ/peak tranches at E and E + ΔD (hydro, committed/must-run tranches and
floor-bound coal held at keeper MW); delta method onto the payload; bench biomass/OTHER reduced by the held-out
energy (the lockstep seam); scored with `calibration_verdict`. Restack validity (±5 % load-weighted price,
r ≥ 0.85) passes 2019/2020/2022/2023; fails narrowly 2021 (+5.97 %), 2024, 2025, where C1 is not read.

| Row | Keeper | Reach |
|---|---|---|
| **C1 CC_REGULAR 2019** | FAIL +3.97 TWh / +3.2 pp | **PASS +4.84 TWh / +2.0 pp** |
| C1 COAL_BIT 2019 | CAVEAT −7.82 TWh (vol band 7.64) | **PASS −6.63 TWh / −2.7 pp** |
| C1 CT_PEAKER 2019 / 2023 | +0.4 / +0.9 pp | +2.0 / **+2.8 pp** (thin) |
| C1, any PASS → FAIL | — | none |
| **C3a 2022** | −13.7 % (ledgered) | **−6.5 % PASS** |
| C3b 2022 | 0.282 (ledgered) | 0.247 |
| C3a 2019 / 2020 | +8.7 / +8.4 % | **+15.9 / +19.1 % (FAIL)** |
| C3b 2020 | 0.113 | 0.218 (FAIL) |
| C3a 2021 / 2023 / 2024 / 2025 | −6.7 / −0.4 / −6.0 / −4.7 % | +1.7 / +7.9 / +1.8 / +3.1 % |

Where the added ~1 GW goes (2019 restack): CT_PEAKER 4.1, COAL_PRB 1.7, COAL_BIT 1.2, CC_REGULAR 0.9, ST_GAS 0.7
TWh. The CC row passes on the denominator (part a), not on CC energy.

**The price cost is the night premium the frontier row already names.** The keeper's 2019 price premium over λ
is concentrated at night (+5.5 $/MWh at 00–02h vs +1.5–2.0 at 13–17h; 2020 the same shape). The phantom
7.6 TWh of must-run was holding the night price down. With it gone, the night margin climbs onto coal and CT.
Under rule 14 that is a discovered bug elsewhere (the night CC/coal commitment of SOCO-F1), not a reason to keep
the phantom supply.

The restack holds hydro at its keeper timing and holds every floor fixed, so it is an upper bound on the price
move. The LP can re-time hydro and the coal pile within the month.

## 3. Other candidates enumerated

| Candidate | Status in `SOCO.js` | New evidence? | Reach on failing rows | Disposition |
|---|---|---|---|---|
| **`mustrun_chp_btm_holdout`** | U | yes (§1) | C1 2019 FAIL→PASS; C3a 2022 →PASS | **Candidate 1: solve** |
| EIA-930-reconciled partial holdout (inject the telemetered "Other", ~1 TWh more than the flag) | no row | follows from §1 | ~85 % of candidate 1 | new field; only if candidate 1's over-removal matters in the solve |
| Coal commitment state on the energy path (port of the SPP/ERCOT posture) | `gas_commitment_bridge` R, `tranche_startup_amortization` G, coal-cycler routes G/R | no | night CC (part b) | not new evidence; the frontier row stands |
| Wansley 2019 floor hole (no Y−1 contract → no pile floor; 0.10 vs 1.81 TWh) | `coal_monthly_pile_measured_receipts` K | no (closeout-SOCO-3 §195 recorded it) | — | no |
| Coal at spot replacement price | not built (K3) | no | C3a 2022 ≤ 1 pp | closed (w2) |
| `benchmark_membership_vintage_union` | O | no | immaterial (SPP-49 census) | no |

## 4. Verdict

Candidate 1 is a rule-14 input correction with an independent grid-side check (EIA-930 telemetry), zero fitted
parameters, an existing default-off field, and no src edit. It reaches the one failing C1 row and the ledgered
C3a 2022 row. It is predicted to push C3a 2019/2020 out of band; that cost is declared in the PRECOMMIT before
the solve, not discovered after it.
