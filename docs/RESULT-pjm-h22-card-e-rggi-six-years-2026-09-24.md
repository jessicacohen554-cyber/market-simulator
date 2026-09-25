# RESULT — pjm-h22 Card E: RGGI allowance cost on the PJM keeper, all six years (2026-09-24)

Charter: `docs/PRECOMMIT-pjm-h22-card-e-rggi-six-years-2026-09-24.md` (pushed before any solve, pin
`d58121c34e0b79259ae3d4103fe4ee828080c79e`). Arm = keeper `2026-09-23-pjm-h19-dbs-span` +
`pjm_rggi_allowance_pricing=true`. One shard per year; zero LP in the parent.

## 1. Headline

| run | years | determination |
|---|---|---|
| keeper `2026-09-23-pjm-h19-dbs-span` (re-scored on the same rebuilt bench) | 2023–25 | CALIBRATED |
| **arm `2026-09-24-pjm-h22-rggi-span`** | 2023–25 | **NOT-YET** — one failure: C1 CC_REGULAR 2024 |
| arm `2026-09-24-pjm-h22-rggi-touchpoint` | 2020–22 | NOT-YET (keeper touchpoint also NOT-YET) |

The failing row: CC_REGULAR 2024, model **322.0** vs actual **335.6** TWh (−13.6; band 8). The
keeper passed at 336.3. Every other scored row passes.

## 2. Per-zone CC_REGULAR (model − actual, TWh, bench plants): keeper → arm

| zone | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **EMAAC** | +14.3 → **+6.0** | +13.2 → **+5.9** | +11.8 → **+2.4** | +13.8 → **−3.4** | +3.8 → **−8.2** |
| SWMAAC | −1.9 → −3.6 | −3.8 → −5.0 | −0.5 → −4.9 | −3.1 → −6.5 | −6.4 → −7.7 |
| **Dominion** | −4.4 → **−8.6** | −1.7 → −4.6 | −13.7 → **−15.5** | −12.3 → −9.9 | −4.0 → −2.9 |
| all bench CC | +9.9 → +2.2 | +20.2 → +12.0 | +3.6 → −7.8 | +0.9 → −13.4 | +2.6 → −7.8 |

`results/calibration/_pjm_h22_carde_result_zones.json` (`scripts/probes/pjm_h22_carde_result_zones.py`).

## 3. Scored rows, 2023–25, keeper → arm (same benchmark)

| criterion | 2023 | 2024 | 2025 |
|---|---|---|---|
| C1 CC_REGULAR TWh (actual 325.7 / 335.6 / 330.7) | 329.5 → 318.1 PASS | 336.3 → **322.0 FAIL** | 333.3 → 322.9 (skipped, prelim 923) |
| C1 COAL_BIT (103.4 / 105.4 / 125.8) | 104.1 → 106.3 | 103.8 → 105.6 | 133.4 → 133.2 |
| C1 CT_PEAKER (21.7 / 24.2 / 24.1) | 20.4 → 22.6 | 25.6 → 30.4 | 30.2 → 34.8 |
| C2 gas sysvol (364.7 / 382.6 / 377.0) | 370.8 → 362.8 | 383.4 → 375.6 | 387.6 → 383.9 |
| C3a mean $ (29.58 / 31.36 / 45.89) | 29.77 → 31.04 (+0.6 → +4.9 %) | 30.41 → **31.78** (−3.0 → +1.3 %) | 42.79 → **44.00** (−6.8 → −4.1 %) |
| C3b NRMSE | 0.113 → 0.119 | 0.124 → **0.115** | 0.143 → **0.129** |
| C3c tail count | 4 → 4 | 11 → 11 | 35 → 35 |

## 4. Touchpoint 2020–22, keeper → arm (same benchmark)

| criterion | 2020 | 2021 | 2022 |
|---|---|---|---|
| C1 CC_REGULAR (actual 283.4 / 289.4 / 308.0) | 285.6 → 278.1 PASS | 290.2 → 282.4 PASS | 319.2 → 310.9 **FAIL → PASS** |
| C1 COAL_BIT (131.5 / 156.6 / 141.1) | 157.0 → 160.7 FAIL | 175.8 → 179.0 FAIL | 143.8 → 146.2 PASS |
| C1 CT_PEAKER (18.7 / 21.5 / 19.7) | 15.5 → 16.7 | 12.8 → 12.9 FAIL | 16.8 → 18.0 |
| C3a mean $ (21.20 / 38.53 / 74.07) | 24.28 → 24.87 FAIL (+14.5 → +17.3 %) | 38.57 → 40.05 PASS | 66.36 → 67.98 **FAIL → PASS** (−10.4 → −8.2 %) |
| C3b NRMSE | 0.155 → 0.182 PASS | 0.104 → 0.107 | 0.242 → 0.235 FAIL |

Per-zone 2020: EMAAC CC +13.0 → +2.7, SWMAAC −2.7 → −4.6, Dominion −10.5 → −8.9 (VA not a member).

## 5. Predictions vs outcome (PRECOMMIT §3–4)

| prediction | outcome |
|---|---|
| G1 liveness: adder line with the right price, N > 0 | HELD in every landed leg (e.g. 2021 1036/3072 gens, $10.44) |
| G1 LMP rises every year | HELD 2023–25 (+$1.27 / +$1.37 / +$1.21) |
| EMAAC CC over-run shrinks every year; crosses to under in 2024–25 | HELD (−3.4 / −8.2 in 2024/25) |
| SWMAAC CC falls every year | HELD |
| Dominion worsens 2021–23 | HELD (−4.4 → −8.6, −1.7 → −4.6, −13.7 → −15.5) |
| C1 CC: 2022 FAIL → PASS; 2023, 2024 PASS → FAIL | 2022 FAIL → PASS held; 2024 FAIL held; **2023 did not fail** (−7.6, inside 8) |
| Span CALIBRATED → NOT-YET | HELD |
| Class CC Δ 2022 −12.8 (phase 0) | Smaller: −8.2 (linear price scaling overstated 2022) |

## 6. Legitimacy (D-1/D-2/D-4)

Arm span: 20 D-4 FAIL rows vs 27 on the keeper (4 new: 2398/2023, 50561/2024–25, 56963/2025;
11 gone). **Not a like-for-like comparison**: the keeper's committed diagnostics were computed on a
bundle without `dispatch/`, the arm's with it (the pjm-146 / caiso-155 plant-set caveat). Reported, not
claimed as an improvement.

## 7. Reading (rules 1 / 14)

The keeper's CC class total was right because EMAAC over-ran and Dominion under-ran by similar
amounts (pjm-h21). RGGI is a real, measured cost that the keeper left out, and it removes most of the
EMAAC error. Dominion's under-run (sub-zonal congestion, pjm-137) is untouched, and in 2021–23 it gets
worse because VA was taxed. So the class total goes short — which is the compensating error exposed,
not a new defect. Price improves in two of three training years.

## 8. Retrievability (rule 34(e))

Span composite registered and committed on this lane's branch (slim keeper shape + payload). Per-year
legs are gitignored in the parent. Provenance SHAs (rule 33(d)): 2020 `96708ab6`, 2021 `49270829`, 2022 `31804b43`,
2023 `e2d0c4a0`, 2024 `a2dcb262`, 2025 `d8dd91f1`. A leg not on `main` costs a ~15 min re-solve.

## 9. G-DRIFT after the pin

`main` gained F1's backcast heat-rate vintage work (`eia860.py`, `campd_bins.py`, `egrid.py`,
`runner.py`) after `d58121c3`. Arm and control were both solved without it, so the A/B stands. A
future keeper re-solve at HEAD picks it up.

## 10. Promotion — RULED and executed

Owner, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper.."* Recommended (§7) and **promoted** this session:
`keepers/PJM.json` and `calibration-complete.json` re-keyed to `2026-09-24-pjm-h22-rggi-span`,
`audit_keepers --iso PJM` E1 passed, the h19 pair pruned (`prune_iso_runs.py --iso PJM --keep
2026-09-24-pjm-h22-rggi-touchpoint --force-uncite`), audit 0 failures / 0 warnings, `status/PJM.js`
rebuilt. **PJM's headline moves CALIBRATED → NOT-YET** (C1 CC_REGULAR 2024). Year set unchanged: 2020–2025.

**Next lane (named successor):** the Dominion CC under-run (−3 to −16 TWh), now uncancelled, and the 2020/21
COAL_BIT over-run. `scripts/gen_pjm_h22_attestation.py` reads the pruned h19 attestation and is a record
now, not re-runnable.
