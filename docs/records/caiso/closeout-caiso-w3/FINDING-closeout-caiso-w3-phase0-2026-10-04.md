# FINDING closeout-CAISO-w3: phase 0 (zero LP), the 2020/21 CC over-run (2026-10-04)

**Charter.** Desk relay, 2026-10-04: owner direction *"Why are you not still running uncalibrated ISOs"*. Levers stack
on the w2 probe recipe (keeper + `caiso_dsw_daytime_lateevening_unprinted_arm`, R-63).

**Control.** The w2 probe `2026-10-04-closeout-caiso-w2-unprinted`:
- bundle `closeout_caiso_w2_a1_span`;
- legs `closeout_caiso_w2_a1_<y>`, solved at `e8570532`;
- registration on `claude/closeout-caiso-w2` @ `d292a159`.

**Branch.** `claude/closeout-caiso-w3`, cut from `90cea720`.

**Zero LP.**

**Remaining FAILs on the control:**
- C1 CC_REGULAR 2020 +5.39 (band ±4.60), 2021 +4.98 (band ±4.83);
- C4 gas NRMSE 2020 0.317, 2021 0.321 (bar 0.30).

## 1. Decomposition (w2 sidecars)

Probe `scripts/probes/_closeout_caiso_w3_cc_object.py`. It is the closeout-caiso-2 decomposition re-pointed at the w2
bundle; output `_cc_object_w2.json`.

| TWh, model − actual | 2020 | 2021 |
|---|--:|--:|
| CC_REGULAR (vs plant EIA-923) | +5.43 | +4.97 |
| … Jan–Mar | −0.66 | **+2.86** |
| … Jun–Sep | **+5.05** | +2.03 |
| … Dec | +1.04 | +0.52 |
| net imports, annual (EIA-930) | **−0.01** | −5.07 |
| net imports in the CC over-run hours | **−5.51** | −10.40 |
| other gas (CT_CHP + CT_PEAKER + ST_GAS) | −5.25 | −0.06 |
| hydro / solar | +1.11 / +1.30 | −0.02 / +1.40 |

DSW corridor error by month (w2 probe):
- 2020: Sep −1.71 and Dec −1.63. In JJAS it sits overnight (−1.61) and at hod 17–23 (−1.88).
- 2021: Jan −2.03, Feb −1.46, Mar −1.14 (all unprinted), then −0.3 to −0.8 per month Jun–Sep and Dec.
- The PNW corridor is over in winter and spring, as before (export-sink family DO-NOT-REDO).

**August 2020 heat event.** It is not the object: August is +1.28 TWh, no larger than June, July or September.

**2021 hydro drought.** Hydro is −0.02 TWh annual, so it is not mis-represented.

**What limits imports in the shortfall hours** (measured − model > 300 MW; probe inline, reported in the RESULT
appendix):

| TWh | 2020 | 2021 |
|---|--:|--:|
| shortfall | 8.15 | 11.67 |
| corridor binding | 0.04 | 0.04 |
| clean rung AT capability, corridor open | 0.29 | 1.48 |
| clean rung BELOW capability, corridor open (priced) | **7.83** | **10.15** |

The DSW clean rung is the marginal unit in most shortfall hours: its offer is within $1–3 of λ in 2020 and $5–12 in
Jan–Mar 2021. Imports are priced out, not depth- or ATC-limited.

**Root cause (2021 Jan–Mar).** In unprinted hours the formula prices Palo Verde on AZ's monthly delivered-to-power
gas. AZ February 2021 is **$10.28/MMBtu**, the Uri spike averaged over the month (Jan 3.39, Mar 3.41). Every February
hour is therefore priced at roughly $134/MWh, while CA plants burn the daily citygate, which spikes on 12–17 February
and is about $4 otherwise.

## 2. Levers (both rule-14 measured inputs; ranked by reach × admissibility)

| # | Lever | Field | First-order DSW import (TWh) | Admissibility |
|---|---|---|---|---|
| L2 | Within-month daily shape on the unprinted formula's gas: AZ/OR monthly level × measured CA citygate daily shape (flow-date staircase, month-mean preserving) | `caiso_intertie_unprinted_daily_gas_shape` | 2019 +1.51, 2020 **+2.11**, 2021 **+2.55** (Feb +2.17) | **Validated on printed days** (below) |
| L1 | 2021's own measured DSW clean depths | `caiso_dsw_clean_depth_own_year` | 2021 **+2.57** (surplus 0.73, overnight 0.75, daytime 0.99, late 0.11) | Measured year over pooled static (rule 14); each rung's own derive `--extra-years 2021` |

**L2 validation gate, fixed before computing.** On printed days the daily-shaped formula must beat the flat formula
against the measured hub daily mean, on BOTH r and RMSE, in ≥ 3 of 4 years 2022–25. Probe
`_closeout_caiso_w3_l2_validation.py`.

| Year | Palo Verde flat r / RMSE | Palo Verde shaped r / RMSE | Malin flat | Malin shaped |
|---|---|---|---|---|
| 2021 (May–Dec, reported) | 0.668 / 20.6 | 0.807 / 18.9 | 0.692 / 13.4 | 0.808 / 11.8 |
| 2022 | 0.846 / 44.7 | 0.941 / 36.3 | 0.843 / 37.8 | 0.948 / 23.9 |
| 2023 | 0.698 / 19.8 | 0.761 / 17.6 | 0.612 / 19.5 | 0.685 / 18.0 |
| 2024 | 0.700 / 15.4 | 0.874 / 11.4 | 0.655 / 20.9 | 0.921 / 14.5 |
| 2025 | 0.541 / 12.4 | 0.644 / 12.3 | 0.519 / 10.4 | 0.663 / 9.5 |

**PASS: 4 of 4 years at each hub.** This contrasts with w2 §1, where the electricity-shape alternative failed 0 of 4.

**L1 2021 depths:**

| MW | surplus | overnight | daytime | late-evening |
|---|--:|--:|--:|--:|
| measured 2021 | 6,644 | 6,892 | 7,426 | 7,288 |
| static now | 5,192 | 6,187 | 5,733 | 6,415 |

They stay report-only in each derive's committed sample, so the gates and statics are unchanged.

**Not proposed:**
- **PNW firm-block over-import:** export-sink family, DO-NOT-REDO.
- **2020 intra-gas substitution** (CC over CT_CHP / CT_PEAKER / ST_GAS, −5.25): the persistent CT_CHP / ST_GAS
  under-run is present in the passing years too (closeout-caiso-2 §2b) and is not a fold object.
- **Extending the daily shape to the ≤25 % 2023 gap fill:** a consistent follow-up, but it would make 2023 live. It
  is deferred and recorded here.

**Downloads:** none needed.
