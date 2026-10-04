# FINDING — closeout-MISO-w3b: on the seam-full-span probe, no admissible lever reaches the two remaining rows; the CHP/BTM holdout fails on reach and the 2021/22 import drift is a price transducer

```
LANE     : closeout-MISO-w3 (continuation, desk direction 2026-10-04: "keep going on the two remaining failures, stacked on the
           seam-full-span probe recipe with the probe as control")
CONTROL  : probe 2026-10-04-closeout-miso-w3-seam (results/calibration/closeout_miso_w3_span; legs closeout_miso_w3_<y>)
LP       : none
PROBE    : scripts/probes/_closeout_miso_w3b_chp_holdout_phase0.py -> results/phase0/miso/_closeout_miso_w3b_chp_holdout_phase0.json
```

Remaining failing rows on the control: **C1 ST_GAS 2019 −8.42 TWh** (band 8.00, so 0.42 TWh over) and **C3a 2020 +10.3 %** (0.3 pt over).

## 1. `mustrun_chp_btm_holdout` (cell O): admissible, but it fails on reach

**Footprint.** `_eia923_frame` with and without the chp=Y row partition. The holdout removes chp=Y biomass + OTHER from grid must-run:

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| TWh removed | 14.52 | 13.11 | 13.31 | 13.77 | 12.51 | 10.50 | 9.73 |

**Static merit-stack walk on the control.** The removed energy is spread flat within each month and filled from undispatched headroom above the control price:

| year | ΔP static ($/MWh) | pick-up (TWh) |
|---|---:|---|
| 2019 | +1.08 | PRB 5.07, CC 4.33, BIT 2.81, CC_CHP 0.93, **ST_GAS 0.72** |
| 2020 | +1.21 | CC 4.78, PRB 3.39, ST_GAS 1.32, CC_CHP 1.24, BIT 1.15 |
| 2021 | +2.28 | CC 4.50, PRB 3.55, BIT 1.95 |
| 2022 | +4.82 | CC 6.44, CC_CHP 1.91, CT 1.57 |
| 2023 | +1.36 | CC 3.97, PRB 3.17, ST_GAS 1.74 |

Reading at the seam arm's own realised static-to-LP ratio (0.53: 2021 static +$2.59 became +$1.36 solved):

| record | control | after the holdout | crosses its band? |
|---|---:|---:|---|
| C3a 2020 | +10.3 % | ≈ +12.9 % | already FAIL; +2.6 pt, past the +2 pt limit this lane used |
| C3a 2019 | +6.4 % | ≈ +8.5 % | no |
| C3a 2023 | +4.8 % | ≈ +7.1 % | no |
| C1 COAL_PRB 2019 | +6.01 TWh | ≈ +8.7 TWh | **yes, new FAIL** |
| C1 ST_GAS 2019 | −8.42 TWh | ≈ −8.04 TWh | still FAIL |

It trades no failing row for at least one new FAIL. **Not chartered for a solve in this lane.**
- It remains a rule-14 candidate on its own grounds. EIA-930 OTH telemetry is 4.5 TWh against the 18.9 TWh injected (miso-253), so promotion on structure with fit-negative accepted is an owner question, not this lane's. The desk should note that SOCO found real structure on the same flag.
- Cell stays O, with this evidence added.

## 2. C3a 2020 on the control: the residual is the two adjudicated objects

Load-quintile decomposition, control vs MISO hub RT:

| | q1 | q2 | q3 | q4 | q5 |
|---|---:|---:|---:|---:|---:|
| control $/MWh | 19.15 | 21.66 | 23.88 | 25.93 | 28.24 |
| actual hub RT | 17.11 | 19.88 | 22.14 | 24.16 | 28.74 |
| share of hours < $15, actual / control | 34 % / 3 % | 14 % / 0.2 % | 7 % / 0 | 3 % / 0 | 0 / 0 |

- **Hub vs zonal basis.** The control's annual gap is +$1.24 against the hub, but the scorer uses the zonal load-weighted basis ($21.97 actual against a $22.99 hub). The ~$1 difference between the two is the West/Plains separation: `internal_congestion_split` **G** (MISO-F3).
- **Low-load margin.** CC_REGULAR sets 40 % of the q1–q2 margin, at a median $19.3. That is the EIA-923 delivered-print-over-hub object (`gas_marginal_commodity_pricing` / `gas_variable_transport` **R**, miso-298…300).
- The seam full span repriced the seam rows (21 % of the low-load margin, at $21.4), but the annual mean barely moved (+$0.02).
- **Conclusion:** no admissible lever remains for C3a 2020. MISO-F3 stands as signed.

## 3. C1 ST_GAS 2019 −8.42

The seam full span moved it toward measured (+0.29 TWh). The rest of the row is MISO-F1: MISO-South VLR commitment, whose pocket MW is unpublished. It is DATA-LIMITED, routed by R-15, and deferred by R-17/R-65. The only lever in reach is the CHP holdout above, and it fails on COAL_PRB 2019. Nothing new is admissible.

## 4. The desk's lead: the 2021/22 net-import drift

Per-seam net flow (TWh, import positive), keeper → probe vs EIA-930 measured:

| year | PJM | SPP | South | Manitoba |
|---|---|---|---|---|
| 2021 | 34.64 → 30.42 vs 36.84 | 2.26 → 1.83 vs 2.15 | −7.61 → −7.04 vs −7.66 | 1.61 → 1.93 vs 2.89 |
| 2022 | 27.66 → 21.57 vs 31.15 | 0.52 → 0.77 vs 2.98 | −15.05 → −14.57 vs −12.89 | 4.81 → 5.68 vs 8.45 |

- **The drift is the PJM seam.** Under the hourly anchor, PJM band k clears iff `MISO(t) − border(t) > δ_k`, with δ_k drawn from the measured MISO-DA − border spread. When the model's MISO price sits below actual, the bands clear less often (C3a 2021 −4.9 %, 2022 −3.7 %; and 2022 PJM border DA averages $65.20 against MISO RT $63). This is the miso-262 transducer: seam volume tracks the host price bias.
- **2022 is larger than the transducer alone predicts.** miso-262's 0.46 TWh/pp slope gives about −1.7 TWh, but the measured shortfall is about −17.5 TWh. The keeper already ran −13 TWh there, so this predates the arm.
- **Not a lever for either remaining row.**
- **Recorded as a successor object:** the 2022 PJM/Manitoba shortfall (PJM −9.6, Manitoba −2.8 TWh). Leads to check: the 2022 seam deliverability envelope (`inject_miso_seam_flow_limit`, measured month × hod), and the Manitoba firm block (`resolve_miso_manitoba_firm_import_mw`).

## Ledger state after this lane

| row | state |
|---|---|
| C1 CC_REGULAR 2021 | **PASS** on the probe (MISO-F2 C1 half inert on promotion) |
| C3b 2021 | **PASS** on the probe (MISO-F2 C3b half inert on promotion) |
| C1 ST_GAS 2019 | MISO-F1 DATA-LIMITED, unchanged; CHP holdout reach fails (§1) |
| C3a 2020 | MISO-F3 MODEL-CLASS, unchanged; the residual is G congestion + R gas print (§2) |

**The candidate list for the two remaining rows is exhausted with reasons.** Re-open sources are unchanged from the signed frontier rows. One addition: an owner ruling to promote `mustrun_chp_btm_holdout` on structure with fit-negative accepted, which would cost COAL_PRB 2019 and C3a 2020 by about 2.6 pt.
