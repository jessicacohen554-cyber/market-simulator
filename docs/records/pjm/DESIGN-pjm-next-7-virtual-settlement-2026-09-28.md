# DESIGN — PJM-NEXT-7: settle the DA virtual position financially (2026-09-28)

Owner ruling 2026-09-28: *"Design card: settle financially"*. Keeper `2026-09-28-pjm-next-6-f2`
(`results/calibration/pjmnext6_sp_span`). **Zero LP.** Census: `scripts/probes/_pjmnext7_settlement_census.py`.

## 1. The structural fact that decides the design

- PJM gates C3a/C3b/C3c on **RT** (`rt_lw` exists every year, 2019–2025; `calibration_verdict.score_price_mean`:
  *"the model is structurally a real-time analogue"*). C1/C2 are RT-physical (EIA-923).
- In PJM a cleared INC/DEC is **liquidated in RT**. RT physical generation serves RT physical load. Virtuals touch RT
  only **through the DA schedule** (which units are committed, when).
- The keeper does the opposite: one LP, virtuals in its physical balance, its dual gated as RT.
  pjm-158 already measured the consequence: the DA−RT basis alone is +4.6 to +6.6 TWh of phantom energy (2023–25).
- `virtual_bids.py:5-10` justifies the layer with *"the backcast is scored against DA clearing prices"*. That is
  stale since rubric v2.4.

## 2. Candidate constructions

| | Construction | Price-forming? | Physical-forming? | Extra LP | DOF | Verdict |
|---|---|---|---|---|---|---|
| **A′** | **DA-commit / RT-dispatch on the existing P0→P1 seam.** P0 = DA stage (virtuals in); P1 = RT stage (virtual bounds zeroed via `run_energy_solve(p1_fleet_prep=…)`). P0's run lengths set P1's startup markup, which is the DA-commitment channel | DA stage only (P0 duals are base cost, not reported); the RT price feels virtuals only via the DA commitment, **as in PJM** | No | **0** | 0 | **Recommended** |
| A | Full two-settlement: current P1 (virtuals in) kept as the DA solve and reported as the DA diagnostic price; a second P1 without virtuals is the scored RT | Yes (DA diagnostic, non-gated) | No | +1 per year (~+7–15 min) | 0 | Same gated physics as A′; pays an LP for a non-gated number |
| b | Net-zero per hour: INC and DEC cleared only against each other | **No.** The virtuals clear at their own λ0 and never touch the energy-balance dual | No | 0 | 0 | **Rejected.** In LP terms it is identical to disarming |
| c | Existing seam search (`model/lp`, `pipeline`) | — | — | — | — | The only price/physical separation available is P0→P1, which is A′ |

A pure LP with no integer commitment has no coupling between a DA and an RT balance other than what P0 hands P1.
So A and A′ produce the same gated outputs up to the startup-markup channel, and both are close to `pjm_da_virtual_bids=false`
for the scored numbers. That arm was solved for 2023–25 by **pjm-158**:
- C1 moves toward actual.
- C3a and the hourly MAE worsen: 9.20→9.94, 10.50→11.82 and 13.97→15.24 $/MWh.
- C3c-2025 fails.

## 3. Zero-LP census: remove the net virtual position from the physical balance

Method: a merit-order envelope per year × month over the keeper's own P1 hourlies.
- Class MW and load-weighted price are each fit as a running mean against responsive supply S.
- The counterfactual evaluates those fits at S − v_t.
- It is **an estimate, not a solve**.
- Check against a measured solve: the envelope gives CC_REGULAR +4.9 / +4.9 / +2.4 TWh for 2023–25. pjm-158's measured disarm (earlier keeper) gave +5.2 / +6.8 / +2.7.

Model − actual after the change (TWh; band ±8). **Bold** = a gate flips.

| year | net virt (keeper) | CC_REGULAR now → est | COAL_BIT now → est | CT_PEAKER now → est | mean price now → est vs RT actual ($/MWh) |
|---|---|---|---|---|---|
| 2019 | +0.9 DEC | +6.1 → +7.3 | +17.3 → +17.4 | −4.4 → −6.1 | 28.1 → 27.9 vs 26.5 |
| 2020 | +2.3 DEC | +12.8 → +14.1 | +4.8 → +4.4 | −1.0 → −3.4 | 25.0 → 24.5 vs 21.2 (C3a +18 % → +16 %) |
| 2021 | +9.7 DEC | +4.6 → +2.3 | +18.9 → +16.4 | −5.8 → **−9.1** | 41.0 → 39.6 vs 38.5 |
| 2022 | +9.3 DEC | +11.3 → +12.0 | +9.7 → **+6.6** | −1.8 → −7.3 | 68.4 → 66.3 vs 74.1 |
| 2023 | −5.8 INC | +4.6 → **+9.5** | −0.5 → +0.6 | −1.8 → −2.8 | 31.0 → 31.1 vs 29.6 |
| 2024 | −4.8 INC | −4.9 → 0.0 | −0.3 → +0.6 | +2.6 → +1.0 | 31.0 → 30.7 vs 31.4 |
| 2025 | −2.3 INC | −10.4 → −8.0 | +9.9 → +11.4 | +7.4 → +5.0 | 44.9 → 44.0 vs 45.9 |

What this means:
- **The pre-2023 C1 rows mostly do not clear.** The net-DEC energy comes off **peakers first**, because DEC is peak-heavy, not off CC.
  - Only COAL_BIT 2022 flips to pass.
  - CC_REGULAR 2020 and 2022 get slightly worse.
  - CT_PEAKER 2021 risks a new fail.
  - The "18–60 % of the over-run" in the card-2 finding measured *volume*, not *which class* carries it.
- **The training span is at risk.**
  - CC_REGULAR 2023 is estimated at +9.5, which fails.
  - pjm-158 measured C3c-2025 failing and C3a worsening under the equivalent arm.
  - 2023–25 would likely go from CALIBRATED to NOT-YET.
- **C3a:** 2020 improves a little but still fails. 2022 moves away from actual.

## 4. Rules

- **Rule 1 `[R-STRUCT]`.** A′ is the real market's sequence: DA with virtuals commits units, and RT physical dispatch runs without virtuals. The current layer serves financial demand with physical fuel, a mechanism that is not real for RT. The census says the fit gets worse. Rule 1 says that is not a reason to keep the unreal mechanism, and the owner has said a structural gain with gate regressions may still be a keeper.
- **Rule 13 `[R-MEASURED]`.** It regenerates forward: the forecast has no virtual layer (the surface is unwired), so the forecast RT LP is already virtual-free. A′ makes backcast and forecast dispatch the *same* physical problem, which strengthens the rule-13 test.
- **Rule 19 `[R-ONE-MECH]`.** It replaces the layer's physical role and does not stack a second mechanism. `pjm_da_virtual_bids` remains the single flag, and a new sub-gate `pjm_da_virtual_settle_financial` (default False, requires the parent flag) scopes it to P0.
- **Rule 21 `[R-DOF]`.** Zero new free parameters. **Rule 24:** one `ScenarioConfig` bool plus a CLI flag plus a matrix row.
- **Rule 29(b).** The control is the keeper's committed bundle, audited with G-DRIFT.

## 5. Recommendation

**A′.** It is the most structurally faithful option, costs zero extra LP and zero DOF, and is honest about what it cannot fix.
- Expect the training span to regress. The pre-2023 C1 rows mostly do not clear.
- If it is promoted on structure, the pre-2023 CC and coal residual is then a clean, virtual-free physical question for card 3 (coal availability and commitment vs CAMPD).
- If it is not promoted, the solve still retires the virtual confound from every future C1 diagnosis.
