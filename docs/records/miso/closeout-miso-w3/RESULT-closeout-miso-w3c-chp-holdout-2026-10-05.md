# RESULT — closeout-MISO-w3c: `mustrun_chp_btm_holdout` on the seam-full-span probe, seven legs, scored as structure vs gates

**Structure vs gates, not a slot request.** The holdout fixes C1 ST_GAS 2019, breaks C1 COAL_PRB 2019 (declared ex ante), and worsens C3a 2020 by 3.0 points. Every gas class moves toward measured in every year. With the attestation carried forward, the failing-criteria count is the same as the control (2 vs 2), but the failing records swap.

```
LANE      : closeout-MISO-w3c (desk charter 2026-10-04: give the owner MISO's SCORED numbers for the cross-ISO CHP/BTM ruling)
PRECOMMIT : PRECOMMIT-closeout-miso-w3c-chp-holdout-2026-10-04.md (pushed before any solve)
PIN       : c000c0e7ac47971b17611338deed4fd3a5c145eb = the control's code (381ee26c) + docs only: zero code drift vs the control
ARM       : keeper recipe + miso_seam_neighbour_hourly_full_span=true + mustrun_chp_btm_holdout=true
CONTROL   : probe 2026-10-04-closeout-miso-w3-seam (the seam-full-span probe; claude/closeout-miso-w3-probe)
PROBE     : run 2026-10-04-closeout-miso-w3c-chp, bundle results/calibration/closeout_miso_w3c_span
            (7 year-isolated legs; all 11 shared-input refs equal the keeper's; registered on claude/closeout-miso-w3c-probe only)
```

## Legs

| year | shard commit | note |
|---|---|---|
| 2019 | 38d27afa | — |
| 2020 | 679fe206 | — |
| 2021 | 36814a91 | — |
| 2022 | 6f77e7b3 | relaunched with a 150-min budget after the 90-min budget expired (P0 cold 2,935 s, P1 warm 3,452 s) |
| 2023 | 95f5104b | — |
| 2024 | 3b076683 | unserved 14.5 GWh vs the control's 8.4 GWh |
| 2025 | 46592d0f | — |

Every leg ran at c000c0e7 with both flags confirmed in `run_config.json`, and every shard is archived.

## Scored records: control (seam probe) → arm, with the PRECOMMIT prediction

| record | control | arm | predicted |
|---|---:|---:|---:|
| **C1 ST_GAS 2019** | −8.42 **FAIL** | −7.67 **PASS** | ≈ −8.04 (FAIL) |
| **C1 COAL_PRB 2019** | +6.01 PASS | +8.73 **FAIL** | ≈ +8.7 FAIL (declared) |
| C3a 2020 | +10.3 % FAIL | +13.3 % FAIL | ≈ +12.9 % |
| C3a 2019 / 2023 / 2024 | +6.4 / +4.8 / +2.5 % | +9.0 / +7.5 / +5.0 % | ≈ +8.5 / +7.1 / — |
| C3a 2021 / 2022 / 2025 | −4.9 / −3.7 / −3.7 % | −1.5 / −0.3 / −1.3 % | ≈ −1.6 / +3.6 / — |
| C3b 2019 / 2020 / 2021 / 2022 / 2023 / 2024 / 2025 | .089 / .142 / .177 / .088 / .078 / .082 / .085 | .110 / .169 / .167 / .073 / .096 / .097 / .076 | — |
| C1 CC_REGULAR 2019 / 2020 / 2021 / 2022 / 2023 / 2024 | +0.67 / −3.10 / −6.41 / −2.70 / −0.87 / +2.61 | +4.61 / +0.81 / −1.21 / +3.27 / +2.49 / +5.23 | each up by ≈ 1.5–3.4 |
| C1 COAL_PRB 2020 / 2021 / 2022 / 2023 | +4.70 / +4.99 / +5.43 / −0.10 | +6.62 / +6.43 / +5.55 / +1.27 | ≈ +6.5 / +6.9 / — / +1.6 |
| C1 ST_GAS 2020 / 2021 / 2022 / 2023 / 2024 | −6.79 / −5.00 / −5.19 / −1.48 / −2.43 | −5.75 / −4.46 / −4.31 / −0.24 / −1.28 | — |
| C1 CC_CHP / CT_PEAKER, every year | — | all move toward measured | — |

Prediction error: every row that was predicted sits within about 0.5 TWh or 0.5 pt of its prediction, except two:
- ST_GAS 2019 does better than predicted.
- C3a 2022 lands at −0.3 % against a predicted +3.6 %.

No prediction misses by 2× or more.

## Determination

| | criteria FAIL | failing records | grade (scored / target / ledgered / fails) |
|---|---|---|---|
| keeper | fuelmix, price_mean, price_shape | 4 | 8 / 4 / 1 / 3 |
| control (seam probe), attested | fuelmix (ST_GAS 2019), price_mean (2020) | 2 | 8 / 5 / 1 / 2 |
| **arm, attested** | fuelmix (**COAL_PRB 2019**), price_mean (2020, **+3.0 pt**) | 2 | 8 / 5 / 1 / 2 |

"Attested" means the keeper's attestation is carried forward locally and not committed; it is the form a promotion would score. As registered, both probes read C3c FAIL and C6 UNATTESTED. C2, C4 and C8 PASS on the seven-year composite.

## Structure vs gates, for the owner

**For promotion on structure (rule 14, rule 13):**
- **Grid telemetry.** EIA-930 OTH, which reconciles to MISO's own net generation, is 4.5 TWh against about 19 TWh of injected chp=Y biomass/OTHER. The holdout removes 9.7–14.5 TWh/yr of host-steam generation that never reaches the grid.
- **Gas classes.** Every gas class moves toward measured in every year: CC_CHP, CT_PEAKER, ST_GAS, and CC_REGULAR 2021/2022.
- **ST_GAS 2019 passes.** That row is the long-standing MISO-F1 (VLR) row, so part of that residual was the injected must-run.
- **Price records toward measured.** C3a 2021 / 2022 / 2025 move to −1.5 / −0.3 / −1.3 %, and C3b 2021 / 2022 / 2025 improve.

**Against:**
- **COAL_PRB 2019 newly fails** (+8.73 TWh, 0.73 TWh over the band).
- **C3a 2020 worsens** from +10.3 to +13.3 %, the low-load level shift (MISO-F3). C3a 2019 moves to +9.0 %, which leaves 1.0 pt of margin.
- **C3b worsens** in 2019, 2020, 2023 and 2024, though every year stays within band.
- **2024 unserved energy** rises from 8.4 to 14.5 GWh.
- **Seam pick-up.** The hourly seam picks up part of the removed must-run: 2020 net import is 58.8 TWh against 56.6 for the control and 56.4 measured.

**Reading.** As on SOCO, this is a rule-14 input correction that is fit-negative on the price level in low-gas years. In those years the removed must-run was masking the over-high low-load price (MISO-F3). The correction is structurally sound, and the gates register it as one failing record traded for another.

## Also reported

- **Self-scored classes.** The holdout partitions the injected classes. The benchmark's biomass/OTHER totals in the payload still read the pre-holdout values (20.9 TWh in 2019 against 7.0 injected). Those classes are not gated, but they enter the C1 share-leg denominator. This is the self-scored validation gap the field's own docstring names (FINDING-miso252 §2).
- **Solve cost.** 2022 needed about 113 min of LP on a 4-cpu / 13.4 GiB box: P0 cold 49 min, P1 warm 58 min. That is about 2.8× the control's 2022 leg.

## Bundles

- **Arm:** composed bundle and registration on branch `claude/closeout-miso-w3c-probe`. The legs stay on `claude/closeout-miso-w3c-20{19..25}` until this lane's PR merges.
- **Control:** stays on `claude/closeout-miso-w3-probe`.
- **Promotion cost** (if the owner rules promote-on-structure): zero solves. Arm both fields in the MISO recipe and carry the attestation forward. The fit cost is the rows in the table above.
