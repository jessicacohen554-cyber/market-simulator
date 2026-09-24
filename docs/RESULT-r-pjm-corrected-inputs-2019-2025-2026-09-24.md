# RESULT — R-PJM: PJM 2019–2025 re-solved on corrected backcast inputs (2026-09-24)

**Run:** `2026-09-24-pjm-r-pjm-corrected` · bundle `results/calibration/rpjm_inputs_span` (2019–2025, one
bundle) · PRECOMMIT `docs/PRECOMMIT-r-pjm-corrected-inputs-2019-2025-2026-09-24.md`, pinned
`8e2993a9a81f005ddfaf3615c549824683766532` · charter: audit §5.3.7.
**Incumbent (control, rule 29(b) form 4):** `2026-09-23-pjm-h19-dbs-span` (2023–25) + folded
`2026-09-23-pjm-h19-dbs-touchpoint` (2020–22). **Both re-scored on the SAME rebuilt benchmark** (the
benchmark's plant→class map follows the fleet, and the year-matched EIA-860 re-classes plants such as
Montour 3149 and Martins Creek 3148, so all 2020–25 bench parts moved; every "old" number below is the
incumbent on the new benchmark).

## 1. Determination

| years | incumbent | R-PJM |
|---|---|---|
| **2023–2025 (training span)** | **CALIBRATED** | **CALIBRATED** — zero criterion status changes |
| 2019 | (not run) | NOT-YET — C1 (CC_REGULAR −13.94, COAL_BIT +8.87 TWh) |
| 2020 | NOT-YET (C1, C3a) | NOT-YET (C1, C3a) |
| 2021 | NOT-YET (C1) | NOT-YET (C1) |
| 2022 | NOT-YET (C1, C3a, C3b) | NOT-YET (C1, C3a, C3b) |
| whole 2019–2025 bundle | — | NOT-YET (fuelmix, price_mean, price_shape — all from 2019–22) |

Per rule 30(c) the ISO headline is the 2023–25 verdict: **unchanged, CALIBRATED**.

## 2. Per-year scorecard, incumbent → R-PJM (same benchmark)

| year | C3a mean LMP vs RT | C3b NRMSE | C4 r gas / coal | C2 | C1 fails |
|---|---|---|---|---|---|
| 2019 | — → **+7.3 % P** | — → 0.100 P | — → 0.926 / 0.934 | P | — → 2 |
| 2020 | +14.5 % F → **+12.4 % F** | 0.155 → 0.136 | 0.930/0.841 → 0.928/0.846 | P | 1 → 1 |
| 2021 | +0.1 % P → **−4.7 % P** | 0.104 → 0.112 | 0.930/0.942 → 0.929/0.941 | P | 2 → **3** |
| 2022 | −10.4 % F → −10.9 % F | 0.242 F → 0.254 F | 0.935/0.944 → 0.933/0.935 | P | 1 → 1 |
| 2023 | +0.6 % → +0.3 % | 0.113 → 0.115 | 0.947/0.921 → 0.948/0.926 | P | 0 → 0 |
| 2024 | −3.0 % → −5.3 % | 0.124 → 0.134 | 0.943/0.933 → 0.943/0.922 | P | 0 → 0 |
| 2025 | −6.8 % → −8.1 % | 0.143 → 0.149 | 0.944/0.944 → 0.943/0.948 | S (prelim 923) | 0 → 0 |

C3c: CAVEAT (ledgered model-class) in 2019/2021/2022 as before. C6 PASS (attestation carried; zero free
parameters added; offer-curve block verified byte-equal on every leg). C8: every material class passes;
ST_GAS 2025 becomes material and passes at 6.9 % forced. CO2 (reported only): +0.1 … +5.6 %, all PASS.

## 3. Class energy, incumbent → R-PJM (TWh, P1 model dispatch)

| year | all coal | CC_REGULAR | CT_PEAKER | ST_GAS |
|---|---|---|---|---|
| 2019 | — → 210.3 | — → 264.4 | — → 9.6 | — → 5.1 |
| 2020 | 164.0 → 169.8 (+5.8) | 285.6 → 283.6 (−2.0) | 15.5 → 13.6 | 7.4 → 7.2 |
| 2021 | 190.3 → **214.0 (+23.7)** | 290.2 → **277.7 (−12.5)** | 12.8 → 10.1 | 6.5 → 3.1 |
| 2022 | 161.2 → 161.4 | 319.2 → 319.1 | 16.8 → 17.1 | 9.3 → 9.7 |
| 2023 | 111.6 → 111.5 | 329.5 → 329.7 | 20.4 → 20.6 | 11.3 → 11.6 |
| 2024 | 112.3 → 117.0 (+4.7) | 336.3 → 335.6 | 25.6 → 23.1 | 12.0 → 13.2 |
| 2025 | 145.5 → 147.1 | 333.3 → 330.6 | 30.2 → 28.2 | 14.8 → **19.8 (+5.0)** |

**COAL_BIT vs EIA-923 (C1):** 2019 +8.87 · 2020 +25.50 → **+17.27** · 2021 +19.23 → **+21.89** · 2022
+2.72 → +0.07 · 2023 +0.73 → +0.67 · 2024 −1.62 → +3.17 TWh.

## 4. The charter's questions, answered at full magnitude

- **2021 coal registry: 48,993 MW** (operable, vintage_2021), matching the ~48.7 GW the pjm-167/168
  census expected.
- **Does coal still run to its rail on correct heat rates? Yes, in 2021.** The restored ~10 GW is
  spent: all-coal energy +23.7 TWh, COAL_BIT over-run grows +19.23 → +21.89 TWh, and CC_REGULAR drops
  −12.5 TWh, turning 2021 C1 CC from PASS (+0.82) to FAIL (−11.65). Year-matched eGRID plus measured CAMPD
  heat rates do **not** change the pjm-168 conclusion: 2021 is not coal-capacity-bound, and the object is
  the coal-vs-gas offer ordering. This is a finding about offers. The vintage stays on (rules 1/14). The
  pjm-168 R was re-opened on contaminated inputs; this run re-earns the same answer on clean ones, while
  the cell stays O pending the owner's ruling.
- **2020 improves** (COAL_BIT −8.2 TWh of over-run, C3a +14.5 → +12.4 %), because the 2020 vintage has
  less coal than the canonical+ramp reconstruction (46.4 GW).
- **2023–2025 are essentially invariant** (|Δ class| ≤ 5 TWh, zero status changes). The largest move
  is 2025 ST_GAS +5.0 TWh from the measured ST rates.

## 5. Census deltas (phase 0, PRECOMMIT §3)

Thermal nameplate at class-table heat rates: canonical 2025ER source (audit heuristic 2.5 %) → 0.05–0.65 %
exact per year. Retirees at class HR: 2019 13,391 → 905 MW, 2020 8,317 → 871, 2021 6,717 → 327. Short-gas
outage windows: +246 in 2019 (F2), 2020–25 byte-identical. Std / short-coal extracts unchanged (sha
`312a11b8` / `a27a8330`).

## 6. Not done, and why

- **Unit partial-derate: not armed.** At HEAD it emits 0 windows: `filter_revealed_outages` drops every
  partial plateau (155 raw, 0 kept) because the unit runs through tight hours. That needs a detector
  change; routed, not built.
- **F2 findings 1–2 (std / short-coal drift): measured, not installed.** A HEAD re-derive cuts std
  MW-days 7–13 %/yr (seven ST_GAS plants on `ST_GAS_PEAKER_PLANTS`, pjm-d4-2), and short-coal moves by a
  few windows. Overwriting the committed input files was refused by this session's permission
  classifier. **Owner decision:** install them (then one more 7-shard re-solve), or leave them.
- **pjm-h22 (RGGI, PR #6573):** orthogonal to this lane, on the same base. If it is promoted, the six F1
  flags apply on top of its recipe.

## 7. Provenance and retrievability (rules 33(d) / 34(e))

Legs, each one year, one container, all at pin `8e2993a9`. The SHAs are provenance only; shard branches
are transport and vanish when this PR merges:

| year | shard commit |
|---|---|
| 2019 | `f46c0784f75f716f6609a6a51a7974bc6c6bbfa9` |
| 2020 | `3b69f4781efec21299dbb722589c0b75ef274109` |
| 2021 | `a1ee58efd5fd8bf52e7c20cd914c33b77f98b136` |
| 2022 | `c66fbcf6aef5bb573ecc7bcd5148ba9b57ef4c85` |
| 2023 | `a8273d162ddd0dc9f01e6361fb526abe3558ad7e` |
| 2024 | `55b2e095a5b8e2cebdcdb88a0420deb3f996d5fd` |
| 2025 | `8213586daa0c38ae9665b78c3cbcf767cc225c67` |

**On `main` after merge:** the composite `results/calibration/rpjm_inputs_span` in the rule-15 keeper shape
(attestation, diagnostics, metrics, meta, per-year run_configs, hourly sidecars; 21 MB), its registry
sidecar and its run payload. That is everything a promotion needs (no re-solve). The per-plant
`dispatch/` parquets follow the repo-wide `.gitignore`, the same as the incumbent. Any later question
that needs them costs a re-solve of ~7 shard-hours (~20–50 min wall with all seven in parallel). All
seven shard sessions are archived.

## 8. Recommendation

**Promote.** It is the structurally correct input set the owner instructed: year-matched EIA-860,
plant-specific heat rates, and 2019 added to the keeper's year set. The training span keeps CALIBRATED
with zero status changes. The 2021 coal over-run it exposes is a true finding (offers), not a regression
to be tuned away. The 2021 C1 CC PASS → FAIL is the cost, reported at full magnitude.
