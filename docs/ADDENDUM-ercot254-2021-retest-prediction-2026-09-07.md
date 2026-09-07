# ADDENDUM — the 2021 re-test PREDICTION, registered before the solve (ercot-254)

> `RESULT-ercot253` §1 records that **every price prediction that session
> registered was wrong, one of them in sign**. That is the reason this document
> exists and is committed *before* the 2021 arm is solved: a prediction written
> after the fact is not a test. Rule 22 — **2021 is a validation touchpoint and
> this is step 4 of the touchpoint loop (re-test), never step 3 (identify).**
> Nothing below was or will be tuned on 2021; the repair being re-tested was
> identified entirely from the input file's within-year distribution and screened
> on 2025 (`PRECOMMIT-ercot254` §2, its G-1 addendum, and the gate results).

## 1. The arm

`results/calibration/ercot253_2021_touchpoint` replayed with the **single delta**
`ercot_ep_gas_basis_monthly=true`. Replaying that bundle (rather than the merged
keeper) is deliberate: the ERCOT keeper is a **two-config** keeper, and the merged
`meta.json` carries only the FORWARD config — the 2021 and 2022 touchpoints both ran
the **carve-out** config (`ercot_offer_swcap_clip=true`, CC_REGULAR `peak` 151.008 vs
the forward 4.576). Replaying run253 itself is the only way to hold every other
input fixed. The comparator is the **committed run253 bundle** (G-CTRL form 4), which
this session can now support empirically rather than by assertion: the 2025 screen
control measured HEAD drift against the committed keeper at **+0.0293 $/MWh** on the
system load-weighted LMP, an order of magnitude below the mechanism's own +0.2974.

## 2. The pre-solve arithmetic (zero-LP, from the input file alone)

2021 monthly-minus-annual level correction, $/MMBtu, Jan..Dec:

```
-5.191  +49.098  -4.943  -4.804  -4.889  -4.936  -4.784  -4.777  -5.073  -4.788  -4.691  -0.223
```

Hour-weighted mean **excluding February: −4.459**. February alone: **+49.098**.
At each class's capacity-weighted p50 heat rate that is:

| class | hr | ex-Feb offer change | February offer change |
|---|---|---|---|
| CC_REGULAR | 7.29 | **−$32.50/MWh** | +$358/MWh |
| ST_GAS | 11.83 | **−$52.74/MWh** | +$581/MWh |
| CT_PEAKER | 14.59 | **−$65.05/MWh** | +$716/MWh |

Two structural consequences follow *before* any solve, and they are the test:

1. **The eleven non-Uri months get cheaper**, by tens of dollars per MWh on every
   gas class.
2. **The CT−CC spread WIDENS by ~$32.5/MWh ex-February**, because a flat $/MMBtu
   level term multiplies through each unit's heat rate and removing it therefore
   relieves the highest-heat-rate units most. The committed 2021 spread is **$6.30**;
   the arithmetic puts the repaired one near **$39**, against $23.18 in 2023 and
   $30.93 in 2022.

## 3. THE PREDICTIONS

Registered now, with honest bands. The **directions** are the test; the magnitudes
are estimates and will be reported at full magnitude whatever they are.

| # | quantity | committed run253 | **PREDICTED** | confidence |
|---|---|---|---|---|
| **P1** | ex-February (11 mo) model mean LMP | $83.30 (actual $34.15, **+144.0 %**) | **falls to $45–$60**, bias **+30 % to +75 %** — still a miss, far smaller | high on direction, medium on band |
| **P2** | February model mean LMP | $1,295.03 (actual $1,521.84, **−14.9 %**) | **RISES**; bias turns **positive**, central **0 % to +60 %** | high on direction, LOW on band |
| **P3** | annual C3a | +28.2 % | **direction genuinely uncertain** — a large February rise nets against a large ex-February fall. I decline to call the sign, and record that as a limit of the prediction rather than hedging after the fact | — |
| **P4** | CC_REGULAR energy | 98.45 TWh (actual 114.47, **−16.02 TWh**) | **RISES** — the miss shrinks; central **−6 to −13 TWh**, and I do **not** predict it closes | high on direction |
| **P5** | CT_PEAKER energy | 11.19 TWh (actual 5.19, **+115.5 %**) | **FALLS** — central **+40 % to +90 %**, still a miss | high on direction |
| **P6** | ST_GAS energy | 17.11 TWh (actual 12.34, **+38.6 %**) | **FALLS** | medium |
| **P7** | West/Panhandle rows | — | **EXACTLY INERT** (the net-load shape owns their level; measured 0.0 delta on 2025) | certain |

**What this arm CANNOT fix, stated in advance.** The `data/raw/ercot_zonal_gas_hub.csv`
2021 per-zone SPREAD is contaminated the same way and is **not touched** here
(`FINDING-ercot254` §1a: North/Northeast +6.12, South_Central +6.30, South +4.36
against Houston's flat cited −0.15 and no West row at all). That is a mean-zero
dispersion defect worth a 6.45 $/MMBtu range against 1.95 in 2023, and it will still
be there after this arm. So **P4/P5 are predicted to improve, not to close**, and a
residual C1 miss is the expected outcome, not a surprise to be explained afterwards.

## 4. What the result may and may not do

The 2021 rung is validation tier. Under rule 22 it is **iterable model-selection
evidence and never a certified out-of-sample skill number**, and under rule 30(c) it
**cannot certify or decertify ERCOT** in either direction — ERCOT's determination is
the train-tier verdict and stays CALIBRATED whatever this returns. Nothing here may
be tuned on: if a prediction misses, the successor is identified on 2023–2025 and
re-tested, exactly as this one was.
