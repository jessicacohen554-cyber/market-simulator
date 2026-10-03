# PRECOMMIT-phase1 — closeout-SOCO-3: the take-or-pay pile on SOCO with full yard history (R-49 step 2), zero LP

Lane closeout-SOCO-3, 2026-10-03. This file was written and pushed **before** any phase-1 number was computed.

- **Owner ruling R-49** (relayed by the desk): option 1, "Charter the pile floor, data first". The same-year measured
  monthly pile (`coal_monthly_pile_measured_receipts`) may be tested on SOCO. The price form and the annual floor
  stay closed.
- **Control:** keeper `2026-10-03-closeout-soco-2-nuclear`.
- **Data:** EIA-923 Page 2 coal stocks 2015–2017, intaken in step 1 (PR #7134, branch `claude/closeout-soco-3b`
  at `065f38d1`). It is read locally from the raw CSVs, so this step does not depend on that merge.

## Construction (fixed)

- **Probe.** `scripts/probes/_closeout_soco3_pile_reach.py`, unchanged from the phase-0 FINDING except that it gains
  an `--displace` split (below). It reproduces `build_coal_monthly_pile` with the measured arm:
  - `floor(m) = max(0, (S_dec − S_max)·hc + cumContract_Y(m))`
  - `ceiling(m) = S_dec·hc + cumReceipts_Y(m)`
- **Inputs.**
  - S_dec = Dec(Y−1) stock.
  - **S_max = max month-end stock over every curated year ≤ Y−1, now 2015 onward.** This is exactly the field's
    construction. The phase-0 "full history" sensitivity, which read the future, is retired.
  - hc = Y−1 Page-5 heat content.
  - MMBtu → MWh at the plant's measured HR (CAMPD heat input / EIA-923 coal net, same year; conversion only).
- **Upper-bound conventions.** The floor is treated as hard, with no capacity clip. Added coal per plant-year =
  max_m(floor − keeper cumulative)⁺; cut = max_m(keeper cumulative − ceiling)⁺; net = added − cut. Coal energy is
  added to COAL_BIT or COAL_PRB by the plant's class (PRB: 6002, 6073, 6124, 6257).
- **Displacement split f.** A fraction f of each year's net coal comes out of (or, if negative, goes back into)
  CC_REGULAR. The remainder 1 − f is shared between CT_PEAKER and ST_GAS pro rata to their keeper annual model energy.
- **Scoring.** C1 is re-scored with `calibration_verdict.score_fuelmix` on the keeper payload
  `frontend/data/backcast/runs/2026-10-03-closeout-soco-2-nuclear.js`, over every class and every year 2019–2025.

## Bars (all three must clear for step 3; none moves after numbers are seen)

- **B1.** CC_REGULAR 2019 passes C1, both legs, at **f = 0.5**. The minimum passing f on a 0.05 grid is reported too.
- **B2.** No plant-year 2019–2025 has max_m(floor − actual cumulative coal energy) > **0.5 TWh**. Actual = CAMPD coal
  gross × plant EIA-923 net/gross, from the phase-0 census.
- **B3.** No C1 row (any class, any year 2019–2025) goes PASS → FAIL against the keeper, at **both f = 1.0 and
  f = 0.5**. A SKIPPED row (preliminary 2025 EIA-923) counts as neither.

Reported but not gating:
- COAL_BIT 2019 status;
- the per-plant added/cut table;
- the 2019 change against the phase-0 field construction (S_max from 2018).

## Outcomes

- **All three clear:** report to the desk and proceed to step 3 (verify R-49 on main, gate lift, PRECOMMIT for the
  solve, 7 shards).
- **Any bar fails:** a short RESULT note, the cell stays U, and the desk carries a card. No step 3.
