# PRECOMMIT — closeout-MISO-w3c: mustrun_chp_btm_holdout stacked on the seam-full-span probe, seven legs, scored as a structure-vs-gates result

Written and pushed **before any solve**. Chartered by the desk on 2026-10-04 to give the owner MISO's scored numbers for a cross-ISO ruling; SOCO's version of the same rule-14 correction goes to the owner as promote-on-structure. **This is not a slot request.**

```
CONTROL : probe 2026-10-04-closeout-miso-w3-seam (keeper recipe + miso_seam_neighbour_hourly_full_span=true)
ARM     : control + mustrun_chp_btm_holdout=true (one field, default off, registered; cell O)
LEGS    : 2019-2025, one shard per year (rules 32/34/36), replay of closeout_miso_nuc_span with both --set flags
EVIDENCE: FINDING-closeout-miso-w3b-remaining-rows-2026-10-04.md §1 (footprint + static walk)
```

**Mechanism.** chp=Y biomass/OTHER rows are partitioned out of the injected grid must-run at the `_eia923_frame` seam, the one seam both the bench and the injection read.
- **Driver (rule 14):** EIA-930 OTH telemetry is 4.5 TWh against 18.9 TWh injected (2023, miso-253).
- **Forward story (rule 13):** EIA-923 publishes the CHP flag per plant and vintage.
- Zero DOF.
- **Footprint:** 14.52 / 13.11 / 13.31 / 13.77 / 12.51 / 10.50 / 9.73 TWh (2019–2025).

## Predictions (fixed now; static walk × the seam arm's realised 0.53 static→LP ratio)

| record | control | predicted |
|---|---:|---:|
| C1 COAL_PRB 2019 | +6.01 PASS | ≈ +8.7 **FAIL (declared PASS→FAIL)** |
| C1 ST_GAS 2019 | −8.42 FAIL | ≈ −8.04 (FAIL; a PASS is not expected) |
| C3a 2020 | +10.3 % FAIL | ≈ +12.9 % |
| C3a 2019 / 2023 | +6.4 / +4.8 % | ≈ +8.5 / +7.1 % |
| C3a 2021 / 2022 | −4.9 / −3.7 % | ≈ −1.6 / +3.6 % |
| C1 CC_REGULAR 2019–2024 | — | each up by ≈ 1.5–3.4 TWh |
| C1 COAL_PRB 2020 / 2021 / 2023 | +4.70 / +4.99 / −0.10 | ≈ +6.5 / +6.9 / +1.6 |

**Also declared as possible PASS→FAIL:**
- C1 COAL_PRB 2021 (≈ +6.9, margin 1.1 TWh)
- C1 CC_REGULAR 2024 (+2.61 + ≈ 1.5, in band)
- C3a 2019 (≈ +8.5 %, margin 1.5 pt)

## Reading rule (structure-vs-gates; no promotion bar)

The RESULT reports every scored record that moves, keeper → control → arm, at full magnitude. It also reports:
- the prediction error for each row above;
- the realised static→LP ratio, against the 0.53 assumption;
- the injected "other" against EIA-930 OTH;
- C8 / D-2 on the composite.

**Stop conditions** (each stops the lane and is reported; none of them is a gate on promotion):
- a shard fails;
- a 2023–2025 leg shows a move outside the holdout's own footprint, a G-DRIFT question. The pin is the lane head; G-DRIFT against the control pin 381ee26c covers docs/probe-only commits.

A prediction missed by more than 2× in either direction is reported as a model-of-the-model failure, not as a gate.
