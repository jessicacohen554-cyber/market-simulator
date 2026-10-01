# PRECOMMIT — R-ERCOT-22: the scarcity-tail sensitivity (zero LP) and the PUCT 48551 ORDC shift vintage

- **Date:** 2026-10-01.
- **Keeper (control):** `2026-10-01-r-21-lostpines-ccid`. Its bundle `results/calibration/r_ercot21_span` (2019–2025) is the control under rule 29(b) form 4. No control solve is run.
- **Phase-0 probe:** `scripts/probes/_r_ercot22_ordc_shift_id.py`, which writes `r_ercot22_phase0.json`. It runs zero LP.

## 1. Task 1: why 365 MW of CC moved the tail

All reads below are on the committed hourlies: r-21 on `main`, r-20 at `dfbbf599`.

**The ORDC side did not move. The energy dual carries the whole drop.** The table covers the hours r-20 priced above $200.

| Year | ΔLW from those hours | Energy-dual part | ORDC-adder part | Reserve families (dual / held / shortfall) |
|---|---|---|---|---|
| 2019 | −2.38 | −2.76 | **+0.38** | ORDC-total identical (784.5 / 4,231 / 4,997); AS families flat |
| 2023 | −3.10 | −3.28 | **+0.18** | ORDC-total identical (155.2 / 4,702 / 3,223) |
| 2024 | −0.03 | −0.04 | +0.00 | identical |

- **Why the reserve side cannot move.** Reserve supply is capped at ERCOT's **measured** RTOLCAP (+RTOFFCAP), so the ORDC reserve level is exogenous in the backcast. That is by design: G1, `ercot_reserve_supply_cap`.
- **Where the 365 MW went.** About 280 MW of Lost Pines dispatch, on CC committed/econ tranches, displaced the top of the stack: CT econ c04/c05, oil, CC_CHP peak, and the upper CC econ tranches.
- **What happened to λ.** The energy dual fell from about $1,000–1,500 to $300–900 in individual hours with **zero slack**. The margin moved down the measured position-tail / top-refine offer surface (K cells `ercot_offer_surface_position_tail`, `ercot_econ_curve_top_refine`).
- **What this means.** The knife-edge is the *position* of the model on a steep, measured top-of-stack offer curve. It is not an ORDC slope defect. No lever follows from this read alone.

**2024 C3a (−11.1 %).** The probe's proxy reproduces the scored value: −11.6 % here, and −24.9 % (2023) and +18.2 % (2019) for the other years.

- Every dollar of the 2024 gap sits in the **energy λ** of the 192 hours ERCOT priced above $100: −5.1 $/MWh, of which the adder side is −0.0.
- In ERCOT's 55 hours between $200 and $1k, the model's λ averages $67 against an actual $296. In the 12 hours above $1k it is $141 against $1,563.
- This is the R-ERCOT-12 / R-ERCOT-20 compressed-distribution object, which is **CLOSED**. Nothing here is new evidence on it, and nothing is re-opened.
- **ORDC response is not the 2024 cause:** the model's adder is within $0.14/MWh of measured RTORPA in every 2024 band.

**What the decomposition does find: in 2019 and 2021 the model's ORDC adder runs above measured RTORPA.**

| Year | Adder gap in the > $200 actual hours ($/MWh, LW) |
|---|---|
| 2019 | +5.5 |
| 2021 | +22.5 |

## 2. Identification: the published RTORPA formula on ERCOT's own measured reserves

`results.scarcity.ordc_adder` is the published two-term formula. Here it is evaluated on measured RTOLCAP, RTOFFCAP and system λ, with year VOLL/MCL, μ = 0 and σ = 1,400. The result is compared with measured RTORPA (Σ, with r).

| Year | Actual Σ | Keeper curve (0.5σ all year) | Published shift in force (0 → 0.25σ on 2019-03-01; 0.25 → 0.5σ on 2020-03-01) |
|---|---|---|---|
| **2019** | 54,424 | 88,984 (**1.635×**, r 0.989) | 56,557 (**1.039×**, r **0.997**) |
| 2020 | 16,407 | 23,770 (1.45×) | 23,543 (1.43×) |
| 2021 | 61,156 | 97,327 (1.59×) | same |
| 2022 | 45,373 | 49,142 (1.08×) | same |
| 2023 | 8,281 | 9,038 (1.09×) | same |
| 2024 | 1,777 | 1,590 (0.89×) | same |

- **The 2019 overstatement is the shift, exactly.** PUCT Project 48551 ordered two 0.25σ steps, effective 2019-03-01 and 2020-03-01. The shipped `ordc_lolp_shift_sigma = 0.5` is the post-2020-03-01 value.
- **The 2020 and 2021 residuals are not the shift and are not addressed here.** The candidate is the per-year published μ/σ tables (NP6-576). The committed `ercot_ordc_lolp_params.csv` overstates by 2–4× in every year, so it is not that table. This is routed.

## 3. The change (rule 14; zero DOF; one seam, rule 19)

1. `ordc_lolp_shift_sigma` joins `constants.ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR`, which already vintages `ordc_voll` / `ordc_mcl_mw` (ercot-253) through `pipeline/backcast_config.py`.
   - 2019 is set to 0.25.
   - 2020–2025 are set to 0.5, the shipped value.
2. **Year grain is a declared rule-14 time-aggregation reconciliation.** The in-LP ORDC curve is one curve per solve year.
   - 2019's Jan–Feb (0.0 in force) holds **0.04 %** of that year's RTORPA.
   - 2020's Jan–Feb (0.25 in force) holds **0.94 %**.
3. **Only 2019 changes.** 2020–2025 resolve to the shipped value, so their LP inputs are byte-identical.
4. **Solve-surface ledger.** The table's row is left undeclared, so ERCOT re-keys. The cause block is in `test_persisted_identity.py`.
5. No new ScenarioConfig field and no new mechanism row. The ERCOT matrix cell for `ercot_multiproduct_as` / ORDC is updated with this evidence.

## 4. G-DRIFT (rule 29(b)), keeper `bc5069cd` → `9c2cdf9a`

- Scope: 21 files, +1,842 / −210.
- Verdict: **ALL INERT** for an ERCOT backcast.
  - The five new flags are default-off and absent from all seven `run_config_<Y>.json`. Their parent flags are off too.
  - The PJM gas bridge returns None unless iso is PJM.
  - SPP MMU is SPP-only.
  - The captive-coal and measured oil-burn paths are flag-gated.
  - `ISO_BA_JOINS` has no ERCOT entry.
  - `actual_lmp.json` changes touch MISO keys only.
- **Consequence:** the keeper's committed 2020–2025 legs stand. One shard re-solves **2019 only** (rule 36: its own container).
- The span is then recomposed from the new 2019 leg plus the r-21 2020–2025 legs, fetched from `claude/r-ercot21-arm-<Y>` (full bundles with `dispatch/`).

## 5. Predictions, fixed before the solve (by hour band, per the R-ERCOT-21 lesson)

| Quantity (2019) | r-21 | Prediction | Basis |
|---|---|---|---|
| dw ORDC adder $/MWh | 16.48 | **10.5 – 12.5** | zero-LP step ratio at model-held reserve (11.76) |
| LW $/MWh | 55.59 | **49.5 – 52.0** | adder −4.7; the energy dual may also fall where headroom couples, so the range is skewed low |
| C3a | +19.4 % | **+5 % to +12 %** (likely PASS, ±10 band) | proxy +18.2 → +8.2 % |
| C3b | 0.446 | **0.36 – 0.43, still FAIL** | the tail hours lose about a third of their adder; the shape is otherwise unchanged |
| C3c h > $200 | 121 | **105 – 121** | adder-borne hours near $200 drop out |
| h > $1k | 39 | **30 – 38** | |
| C1 CC_REG / COAL_PRB / ST_GAS | +8.85 / −10.48 / +3.29 | **each within ±0.3 TWh** | the in-LP reserve curve moves held reserve only where the cap does not bind |
| Slack MWh | 0 | **≤ 50** | |
| C8 ST_GAS | 17.6 % | **±1 pp** | |
| 2019 determination | NOT-YET | **NOT-YET** (C3b, C1 CC_REG and COAL_PRB remain) | |
| 2020–2025 | — | **byte-identical** (recomposed) | |
| ISO | NOT-YET | **NOT-YET** | |

**Promotion test.** The owner's standing instruction is "Is it an improvement? Then promote". It is an improvement if 2019 C3a and C3b move toward the band and no criterion regresses past a band. If C1 moves more than ±0.5 TWh, the in-LP coupling is larger than assumed and is reported at full magnitude.
