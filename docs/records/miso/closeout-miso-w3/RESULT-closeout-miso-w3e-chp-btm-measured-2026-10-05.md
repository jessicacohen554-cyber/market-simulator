# RESULT — closeout-MISO-w3e: `miso_chp_btm_measured` on the seam-full-span probe, seven legs, scored as structure vs gates on three bench bases

**Headline: the reconciled basis** (PR #7210 head: the measured CHP artifact plus the refuted MISO gas fold). On it, the arm fails **one** criterion against the control's two and the incumbent keeper's three.

| run | failing criteria | failing records |
|---|---|---:|
| keeper | fuelmix, price_mean, price_shape | 10 |
| control (seam probe) | fuelmix, price_mean | 8 |
| **arm** | **fuelmix** | **5** |

- **price_mean** passes: C3a 2020 moves from +10.3 % to +8.0 %.
- **CC_CHP** passes in 2020, 2021, 2023 and 2024.
- **Declared costs:** CC_REGULAR 2021 and ST_GAS 2020 go PASS→FAIL.
- **Remaining CC_CHP misses:** 2019 and 2022 improve but still fail. They trace to the model's merchant cogens still under-delivering against their own Sched 6/7 sales.
- **Status:** structure vs gates, not a slot request. #7210 is held as a draft for owner decision #20.

```
LANE      : closeout-MISO-w3e (desk charter 2026-10-05)
PRECOMMIT : PRECOMMIT-closeout-miso-w3e-chp-btm-measured-2026-10-05.md + GDRIFT (pushed 43797896, before any solve)
PIN       : 437978965a951eddad79aa923e0b436ebc83c9e6
ARM       : keeper recipe + miso_seam_neighbour_hourly_full_span=true + miso_chp_btm_measured=true
CONTROL   : probe 2026-10-04-closeout-miso-w3-seam (claude/closeout-miso-w3-probe), re-scored zero-LP on each bench basis
BUNDLE    : results/calibration/closeout_miso_w3e_span (7 legs composed; all shared-input refs rebuilt; registered LOCALLY only)
```

## Legs

Every leg was solved at 43797896, and each `run_config.json` shows both flags. Every shard was fetched, verified and archived.

| year | shard commit | dispatch P1 | unserved | note |
|---|---|---:|---:|---|
| 2019 | 2617a9bd | 81.3 MB (zstd-9) | 0 | |
| 2020 | 8a9b9793 | 72.3 MB (zstd-9) | 0 | |
| 2021 | b5d045c0 | 66.0 MB (zstd-9) | 0 | |
| 2022 | 0abaf2fc | 62.0 MB (zstd-9) | 0 | P0 1,917 s, P1 1,333 s |
| 2023 | d1d09078 | 99.3 MB | 0 | |
| 2024 | 07c4cb14 | 98.7 MB | 4.1 GWh | the control had 8.4 |
| 2025 | 2c5e22fc | 96.9 MB | 0 | |

## Three bench bases (zero LP; control and keeper re-scored on each)

The bases are defined in FINDING-closeout-miso-w3e-bench-reconciliation:
- **original** — the sector-default CHP share, with the MISO gas fold applied;
- **measured** — the Sched 6/7 artifact, with the fold still applied;
- **reconciled** — the artifact, with the fold refuted. This is #7210.

| basis | run | failing criteria | failing records |
|---|---|---|---|
| original | keeper | fuelmix, price_mean, price_shape | ST_GAS19, CC_REG21, C3a20, C3b21 |
| original | control | fuelmix, price_mean | ST_GAS19, C3a20 |
| original | arm | fuelmix | ST_GAS19, ST_GAS20, CC_REG21, **CC_CHP24 (+9.25, over)** |
| measured | keeper | fuelmix, price_mean, price_shape | CC_CHP19–24, COAL_PRB19–22, ST_GAS19, C3a20, C3b21 (13) |
| measured | control | fuelmix, price_mean | CC_CHP19–24, COAL_PRB19–22, C3a20 (11) |
| measured | arm | fuelmix | ST_GAS19, COAL_PRB19–22, CC_CHP22 (6) |
| **reconciled** | keeper | fuelmix, price_mean, price_shape | CC_CHP19–24, ST_GAS19, CC_REG21, C3a20, C3b21 (10) |
| **reconciled** | control | fuelmix, price_mean | CC_CHP19–24, ST_GAS19, C3a20 (8) |
| **reconciled** | **arm** | **fuelmix** | **CC_CHP19, CC_CHP22, ST_GAS19, ST_GAS20, CC_REG21 (5)** |

**Scope of these counts:**
- price_tail (C3c) and governance (C6) are left out: a probe carries no attestation.
- The keeper's C3c ledger carries forward at promotion, as in w3/w3c.
- sysvol, price_shape (for the probes), dispatch_corr and forced_share (C8) PASS for both the control and the arm on every basis.

**Two readings:**
- On the original basis, the arm over-delivers CC_CHP against a bench that still subtracts the default share (2024 +9.25). This is the mismatched pair the PRECOMMIT excluded.
- The measured-only basis carries the spurious fold scale-down: COAL_PRB 2019–22 FAIL is the `reconcile_vintage_classes` channel.

## Reconciled basis: records against the PRECOMMIT predictions (lower bound)

| record | control | arm | predicted | |
|---|---:|---:|---:|---|
| C3a 2020 | +10.3 % | **+8.0 %** | ≈ +8.3 % | FAIL→PASS (declared) |
| C3a 2019 / 2021 / 2022 / 2023 / 2024 / 2025 | +6.4 / −4.9 / −3.7 / +4.8 / +2.5 / −3.7 % | +4.7 / −6.8 / −5.5 / +2.8 / +0.2 / −6.4 % | +4.5 / −6.4 / −5.6 / +3.1 / +0.5 / −5.9 % | all in band |
| C1 CC_CHP 2019 | −17.84 | −9.70 | ≈ −8.96 | FAIL (declared) |
| C1 CC_CHP 2020 / 2021 | −15.61 / −14.72 | −7.08 / −7.88 | −6.56 / −7.65 | FAIL→PASS |
| C1 CC_CHP 2022 | −15.97 | −9.03 | ≈ −8.00 (on the line) | FAIL (declared) |
| C1 CC_CHP 2023 / 2024 | −14.65 / −12.66 | −5.08 / −2.01 | −4.18 / −0.95 | FAIL→PASS |
| C1 CC_REGULAR 2021 | −6.41 | **−9.52** | ≈ −9.15 | PASS→FAIL (declared) |
| C1 ST_GAS 2020 | −6.79 | **−8.01** | ≈ −8.60 | PASS→FAIL (declared; 0.01 TWh over) |
| C1 ST_GAS 2019 | −9.01 | −9.83 | ≈ −9.76 | FAIL deepens (declared) |
| C1 COAL_PRB 2019 / 2020 / 2021 | +0.42 / +4.70 / +4.99 | −1.53 / +3.24 / +4.26 | — | toward measured |

**Prediction error.** The per-class LP reach landed within about 0.5 TWh of the static walk in every class and year. CC_CHP 2023/2024 came in 0.8–1.1 TWh under. ST_GAS gave up less than predicted (2019: −0.87 vs −1.33). No prediction missed by 2× or more.

**Realised static→LP price ratio.** 0.48 / 0.61 / 0.69 / 0.52 / 0.62 / 0.60 / 0.64 for 2019–2025, against the 0.53 assumed.

## Reported against interest

1. **CC_CHP 2019 and 2022 still fail.** The carve now matches the filings, but the model's grid CHP tranche still dispatches below the plants' own Sched 6/7 grid sales:

   | plant | control 2019 (GWh) | arm 2019 | sold 2019 | arm 2023 | sold 2023 |
   |---|---:|---:|---:|---:|---:|
   | Midland | 3,799 | 6,036 | 8,602 | 7,041 | 9,505 |
   | Dearborn | 1,804 | 2,588 | 5,355 | 4,480 | 5,176 |
   | Taft | 1,200 | 2,506 | 4,361 | 3,045 | 4,690 |

   This is the next object: CHP grid-tranche economics or availability, through `chp_btm_floor_pct` / chp steam-following conduct. It is not a carve error.
2. **ST_GAS forced share (C8) rises in every year.** The arm displaces ST_GAS's economic energy while the floored energy stays.
   - 2021: 0.295 → 0.316, but that year is ungated (immaterial: 1.7 % of load).
   - Gated years stay under 0.30; 2019 is the closest at 0.287.
   - C8 PASSES on the composite.
   - CT_PEAKER stays GROUNDED ABOVE BUDGET, as in the control.
3. **2019 bench deadband.** `reconcile_vintage_classes` does not fire in 2019 on the reconciled basis, by 0.0367 TWh (FINDING §3a). The arm's own render reproduces the same margin.
4. **2024 unserved energy** is 4.1 GWh, against 8.4 for the control.

## Promotion cost (if the owner rules land + promote)

- **Code and bench:** #7210 lands (artifact, field, fold refutation). The incumbent keeper's basis moves: CC_CHP 2019–24 go PASS→FAIL on re-render.
- **Solves:** none. The seven legs are promotable as they stand: bundle `closeout_miso_w3e_span`, legs on `claude/closeout-miso-w3e-20{19..25}`.
- **Recipe:** arm `miso_seam_neighbour_hourly_full_span` + `miso_chp_btm_measured`. Carry forward the attestation; C3c is re-measured.
- **Determination on the reconciled basis:** MISO stays NOT-YET on fuelmix:
  - CC_CHP 2019 and 2022 — the CHP-tranche dispatch object;
  - ST_GAS 2019 and 2020 — MISO-F1 VLR;
  - CC_REGULAR 2021 — the arm's declared cost.
