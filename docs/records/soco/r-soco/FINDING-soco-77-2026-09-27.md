# FINDING — SOCO-77 (2026-09-27): a start cost on the CT econ/peak tranches fixes the CT *level*, not the CT *plant split*. It needs an owner ruling. Zero LP, no solve.

**Lane** SOCO-77 · **DATA PROFILE** soco · **Model** Opus (rule 27).
**Keeper:** `2026-09-27-soco76-egrid-identity-hr` (the incumbent, unchanged). `origin/main` is at `93ca1555`, and PR #6778 is merged.
**Owner ruling on soco-75's two-sided coal mode:** none in `docs/calibration-log/soco.md`, so TASK 1 ran.
**Legs:** the seven soco-76 legs, fetched at the full SHAs in RESULT-soco-76 §6. They are gitignored and were not committed.
**Shared inputs:** restored with `run_calibration_full --restore-shared-inputs results/calibration/soco76_span`. All three were hash-verified.
**Probe:** `scripts/probes/_soco77_ct_start.py` (`conduct`, `markup`, `greedy`).
**Outputs:** `docs/handoffs/r-soco/soco77_ct_{conduct_units,plant_split,markup}.csv`, `soco77_ct_start_greedy.json`.

## 1. Headline

| question | answer |
|---|---|
| Does the CEMS record support a per-plant start cost that would reorder the CT fleet? | **No.** The over-runners are the plants that **start least**. Tenaska 55061 starts 10–21 times per unit-year in 2019–2020, while McIntosh 7813 starts 120–190. A start cost is $/MW-start, and a physical start costs roughly the same on every 7FA-class CT. What differs between plants is how often they start. That is an outcome, not a cost. |
| Is start fuel measurable per plant from hourly CEMS? | **No.** The first online hour's heat input is *below* the unit's steady-state heat rate × load at 16 of 20 plants (pooled −1.9 to +2.4 MMBtu/MW). At hourly grain, start fuel cannot be told apart from part-hour loading. SOCO-64's warm-up-to-LSL figure, **$3.6/MW** (CT class p50), is the only measured start fuel. |
| What carries a start cost today? | Only the CT `_committed` tranches, through the core P1 `compute_monthly_markup`: NREL $20/MW, p50 ≈ $5/MWh, max $20/MWh. Every CT `econ*`/`peak` tranche carries **$0** in all seven years (§3). Extending the start cost to those tranches is exactly `tranche_startup_amortization`'s scope, and that cell is `G`. |
| Reach (greedy, baseline-differenced) | **Large on the level, and roughly neutral on the ranking.** At NREL $20/MW, 2019 CT_PEAKER goes +2.29 → +0.31 pp. 2020 C4 coal goes 0.301 → 0.236 (FAIL → PASS). 2019 COAL_BIT goes −4.16 → −3.52 pp, and still FAILs. The per-plant error falls because every CT plant comes down, including the plants that already under-run. |
| Admissible without a ruling? | **No, for two reasons.** (a) This is a pure LP, so a cost in the P1 objective *is* the price dual. "Objective, not pricing" cannot be separated here, and the ruling kept this field's pricing use `G`. (b) The only construction with reach uses the published NREL table, not a SOCO-measured cost. The measured fuel-only start is 18 % of that and has about a third of the reach (§4, arm F). |

## 2. CT plant split and CEMS conduct (selected; full table in `soco77_ct_plant_split.csv`)

| plant | 2019 model / EIA-923 TWh | 2020 model / EIA-923 | CEMS starts/unit-yr 2019 / 2020 | median run h |
|---|---|---|---|---|
| 55061 Tenaska | **2.72 / 0.13** | **2.42 / 0.07** | 21 / 10 | 8.5 / 9.5 |
| 55409 Calhoun | 1.56 / 0.33 | 1.20 / 0.04 | 55 / 12 | 12 / 6 |
| 55128 Walton | 1.39 / 0.46 | 1.30 / 0.30 | 96 / 66 | 13 / 13 |
| 55267 Addison | 1.27 / 0.37 | 0.87 / 0.35 | 94 / 81 | 7 / 9 |
| 55332 | 1.08 / 0.22 | 0.72 / 0.22 | 36 / 18 | 12.5 / 11.5 |
| 55304 Baconton | 0.83 / 0.25 | 0.73 / 0.15 | 135 / 93 | 15 / 11.5 |
| 7813 McIntosh CT | 0.33 / 0.59 | 0.22 / 0.40 | **169 / 122** | 10 / 9 |
| 7916 | 0.37 / 0.49 | 0.15 / 0.47 | 135 / 114 | 8 / 9 |
| 7829 | 0.00 / 0.27 | 0.00 / 0.26 | **191 / 162** | 9 / 10.75 |
| 55141 | 0.36 / 0.56 | 0.24 / 0.62 | 121 / 137 | 13 / 12 |
| CT class total | 11.50 / 4.48 | 9.18 / 3.53 | | |

The model's CT merit order runs on heat rate: the cheapest CT tranches are the most-run. In the real fleet, the most-started CTs are the dearer, older, utility-owned plants. The cheap IPP-sited plants (Tenaska, Calhoun, 55332) start rarely. This inversion is not a start-cost object. Candidates for identification, all unscoped: offtake or tolling contracts, firm fuel/transport, dual-fuel limits, and dispatch-rights ownership.

## 3. The keeper's live start markup (solved `mc` − `fleet_only` `mc_base`, the SOCO-65 construction)

In every year 2019–2025, the `_committed` tranches (17–18 CT plants) have p50 $4.8–9.2/MWh, max $20/MWh, startup $20/MW. The `econhi`, `econlo` and `peak` tranches all carry exactly $0.

## 4. Reach — price-taker greedy on the soco-76 legs, arm minus baseline, scorer-exact C1 and C4

Arm **N** is the NREL $20/MW start on CT econ/peak, amortized over each tranche's own P1 monthly mean run (the v2 construction). Arm **V3** is arm N with the horizon capped at the plant's pooled 2019–2025 CEMS median run. Arm **F** is SOCO-64's measured fuel-only start, $3.6/MW, over the arm-N horizon.

| row | keeper | N | V3 | F |
|---|---|---|---|---|
| 2019 CT_PEAKER pp | +2.29 | +0.31 | −0.05 | +1.59 |
| 2019 ST_GAS pp | −1.87 | −1.25 | −1.16 | −1.56 |
| **2019 COAL_BIT pp** (FAIL) | **−4.16** | −3.52 FAIL | −3.40 FAIL | −3.88 FAIL |
| 2019 COAL_PRB pp | +0.86 | +1.56 | +1.70 | +0.97 |
| **2020 C4 coal NRMSE** (FAIL) | **0.3012** | **0.2358** | **0.2264** | **0.2748** |
| 2020 COAL_BIT pp | −2.32 | −1.48 | −1.38 | −2.03 |
| 2021 CT_PEAKER pp | −0.54 | **−1.17** | −1.24 | −0.86 |
| 2022 CT_PEAKER pp | −0.98 | **−1.57** | −1.60 | −1.17 |
| 2023 CT_PEAKER pp | +2.20 | +0.12 | +0.07 | +1.42 |
| 2023 C4 coal | 0.2674 | 0.1934 | 0.1904 | 0.2524 |
| 2024 CT_PEAKER pp | +1.48 | −0.39 | −0.48 | +0.66 |
| CT plant Σ\|model−923\| 2019 / 2020 / 2023 TWh | 9.50 / 8.67 / 9.14 | 6.37 / 4.00 / 4.95 | 5.67 / 3.69 / 4.84 | 8.73 / 6.75 / 7.62 |

- **No row turns worse from PASS to FAIL.** 2021 and 2022 CT_PEAKER move further under, from −0.54 to −1.17 and −0.98 to −1.57 pp. Both stay PASS, and both years were already under-running.
- **The ranking does not change.** In 2019 under arm N, Tenaska falls 2.72 → 1.60 TWh against 0.13 actual. McIntosh falls 0.33 → 0.14 against 0.59, and 7916 falls 0.37 → 0.14 against 0.49. The under-runners get worse. The split error falls only because the class total falls.
- **Screen caveat.** A price taker overstates displacement in hours where the CT is marginal, because the LP would raise the price by the markup. SOCO-64's greedy of the same scope was never solved, so this caveat has not been measured.

## 5. Owner question

**Q (SOCO-77).** SOCO's CT econ/peak tranches carry no start cost. The `_committed` anchor of the same plants carries the NREL $20/MW start through the core P1 markup. Should `tranche_startup_amortization` (optionally with `tranche_startup_measured_runs`, which needs a SOCO `campd_ct_run_lengths` derive) be armed for SOCO as the *cost-based start in the objective* under the 2026-09-27 ruling?

- In this LP that cost also sets the price, because the dual carries it.
- It fixes the CT **level** and passes 2020 C4 in the screen.
- It does **not** fix 2019 COAL_BIT.
- It does **not** fix the CT **plant split**.

The alternative is the measured fuel-only $3.6/MW. It has about a third of the reach and passes nothing in the screen.

**Lane recommendation:** do not arm it on these grounds alone. The mechanism is real and measured-direction. However, the ruling's text keeps this field's pricing use `G`, the reach comes from a table rather than SOCO's own measurement, and the dominant CT residual is the ranking, which this field cannot touch. The next zero-LP object is the identification in §2 (why SOCO's cheapest CTs start 10–20 times a year).

## 6. Retrievability (rule 34(e))

No solve; nothing to retrieve. The soco-76 legs this lane read are costed as a re-solve (~5–25 min of LP per year) if their refs are gone.
