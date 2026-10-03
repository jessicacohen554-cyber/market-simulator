# RESULT — NWPP-NEXT-26: CAISO_NEVP priced only after Harry Allen–Eldorado, 2019–2025

- PRECOMMIT: `PRECOMMIT-nwppnext26-nevp-hae-2019-2025-2026-10-03.md`.
- Phase 0: `FINDING-nwppnext26-nevp-hae-phase0-2026-10-03.md`.
- Probe run `2026-10-03-nwpp-next-26-nevp`; bundle `results/calibration/nwppnext26_span`, composed from seven legs.
- Control: keeper `2026-10-03-nwpp-next-25-served`, read from its committed bundle.

## Legs (pin `30c0e01790f3ee4085042193be816d47cc704c31`, branch `claude/nwppnext26-pin`)

| year | leg SHA | branch |
|---|---|---|
| 2019 | `b56a5adfe98f94b1466a5a9c1fc83456dfcaf6c4` | `claude/nwppnext26-2019` |
| 2020 | `b79bd4e51f1e5aeb1571eab1bf136115fa8d7fef` | `claude/nwppnext26-2020` |
| 2021 | `166e43819d761cab71c19cd7723b668ee307327d` | `claude/nwppnext26-2021` |
| 2022 | `6d9390019e1e9d1c6049a723e7b65a5febae38cc` | `claude/nwppnext26-2022` |
| 2023 | `b0e505f19088b8be5a17e1fb83a31bdb40c90cff` | `claude/nwppnext26-2023` |
| 2024 | `498ab569b5fd0587bfbcbd538bf98d8a0ef28d79` | `claude/nwppnext26-2024` |
| 2025 | `ec80119c8bef250cc2b494c9167a62be741cfa57` | `claude/nwppnext26-2025` |

- **Parents.** Six legs sit on the pin. The 2024 leg's parent is the prompt commit `915ecb11`. Its tree differs from
  the pin only under `docs/records` (`git diff 30c0e017 915ecb11 -- src scripts tests data configs` is empty), so the
  solve code is identical.
- **Checks re-run by the parent on each leg's own bytes:**
  - the `scenario_config` diff against the keeper's year config is exactly
    `[('nwpp_seam_in_service_vintage', None, True)]`;
  - zonal P1 demand matches the PRECOMMIT table to 0.01 TWh;
  - in 2019 the net NEVP seam flow is 0.00 MW in every hour, and in 2020 it is 0.00 MW in all 5,351 hours before
    2020-08-12.
- **Controls.** In 2021–2025, class energy and every hourly zonal price equal the keeper's to 0.0000. These five legs
  are exact controls.

## What moved (P1, TWh, NEXT-26 against the keeper)

| | 2019 | 2020 |
|---|---|---|
| CC_REGULAR | 62.70 → 57.59 (−5.12) | 59.06 → 53.94 (−5.12) |
| CT_PEAKER | −2.27 | −1.30 |
| COAL_BIT | −1.38 | −0.07 |
| CC_CHP | −0.71 | −0.43 |
| ST_GAS | −0.32 | −0.02 |
| NEVP seam export | 10.47 → **0.00** (measured −0.30) | 11.98 → **4.85** (measured 3.11) |
| COI export | 11.13 → 12.06 (measured 7.03) | 13.99 → 14.40 (measured 15.26) |
| SNV gas | 29.58 → **24.17** (NEVP EIA-930 22.2) | 27.74 → **22.84** (22.8) |
| NW / OR gas | 18.78 / 10.85 → 17.38 / 9.55 | 13.44 / 11.35 → 12.25 / 10.91 |
| demand-weighted price, $/MWh (unscored, R-9) | 29.47 → 28.02 | 23.87 → 23.19 |

- **The over-export leaves.** The 10.5 TWh the keeper exported through a path that did not exist is gone. Of it,
  0.9 TWh (2019) and 0.4 TWh (2020) re-routes through COI. The rest comes off SNV gas and the coal margin.
- **SNV gas lands on the measured NEVP series.** In 2020 it is within 0.04 TWh.
- **The prediction held.** The PRECOMMIT predicted CC_REGULAR −4…−9 TWh in 2019 and −2…−5 TWh in 2020. Both years
  moved −5.12 TWh, which sits at the top of the 2020 range.

## Gate (b): verdict diff against keeper `2026-10-03-nwpp-next-25-served`

Both runs were scored on the same bench render. No bench part changed, because 2021–2025 are byte-identical.

Both determinations are NOT-YET. **FAIL records 8 → 7; one flip, FAIL → PASS.**

| record | keeper | NEXT-26 | |
|---|---|---|---|
| **C1 CC_REGULAR 2019** | +12.73 TWh, +3.5 pp FAIL | **+7.61 TWh, +2.4 pp PASS** | **flip** (band ±8.00, so 0.39 TWh of margin) |
| C1 CC_REGULAR 2020 | +7.51 PASS | +2.39 PASS | margin regained |
| C4 gas 2019 | r 0.649 / NRMSE 0.359 FAIL | r 0.669 / 0.267 FAIL | improves (r still under the 0.70 floor) |
| C4 gas 2020 | r 0.752 / 0.281 | r 0.822 / 0.190 | improves |
| **C4 coal 2019** | r 0.799 / 0.197 | **r 0.754 / 0.209** | **regression r −0.045** (PASS) |
| **C4 coal 2020** | r 0.781 / 0.184 | **r 0.762 / 0.188** | **regression r −0.019** (PASS) |
| **C1 COAL_BIT 2019** | −1.38 | **−2.76** | **regression 1.38 TWh** (PASS) |
| **C1 CT_PEAKER 2019** | +0.52 | **−1.75** | **regression: \|err\| +1.23 TWh** (PASS) |
| **C1 CT_PEAKER 2020** | +0.48 | **−0.82** | **regression: \|err\| +0.34 TWh** (PASS) |
| **C1 ST_GAS 2019** | −0.82 | **−1.14** | **regression 0.32 TWh** (PASS) |
| **C1 CC_CHP 2020** | −0.67 | **−1.10** | **regression 0.43 TWh** (PASS) |
| C1 CC_CHP 2019 | +0.36 | −0.35 | no change in \|err\| |

- **Unchanged FAIL records:**
  - CC_REGULAR 2024 +12.77;
  - C3a 2024 −25.3 %;
  - C3b 2023 0.209 and 2024 0.772;
  - C4 gas 2023 (r 0.533) and 2024 (r 0.797, NRMSE 0.316).
- **Seam regression.** COI 2019 export moves 0.93 TWh further above its measured level (12.06 against 7.03).

## Gate (c): rule 20 and legitimacy

- **D-2.** Forced share is 0 in every class-year. PASS.
- **D-1.** Failures rise from 16 to 17 class-years (17 → 18 failure lines). This is a regression.
  - **New:** 2019 CT_PEAKER off-peak CV ratio 0.426.
  - **Worse:** 2019 COAL_BIT profile r 0.798 → 0.613; 2019 COAL_PRB r 0.722 → 0.717.
  - **Better:** 2019 COAL_WC r −0.373 → −0.331; 2020 COAL_BIT r 0.681 → 0.689; 2020 COAL_WC r −0.520 → −0.509.
- **C6 governance.** PASS. The attestation comes from `scripts/gen_nwppnext26_attestation.py`, which is the NEXT-25
  generator plus this key, with zero new free parameters.

## Reading and recommendation

The arm removes a priced path that did not physically exist before 2020-08-12. FERC ER20-1514 and the measured
EIA-930 step date the Harry Allen–Eldorado intertie to that day. Each counterparty is now priced or served by the
hour, never both (rule 19), and the change adds no number.

- **Gains.**
  - The 2019 CC_REGULAR over-run flips from FAIL to PASS.
  - SNV gas lands on measured NEVP.
  - The NEVP seam matches the measured leg in 2019.
  - C4 gas improves in 2019 and 2020.
- **Regressions, at full magnitude.**
  - C4 coal 2019 r −0.045 and 2020 r −0.019.
  - COAL_BIT 2019: 1.38 TWh more under.
  - CT_PEAKER: it moves from over to under, \|err\| +1.23 TWh in 2019 and +0.34 TWh in 2020.
  - ST_GAS 2019 −0.32 TWh and CC_CHP 2020 −0.43 TWh.
  - COI 2019: +0.93 TWh further from measured.
  - D-1 rises from 16 to 17.
  - All of these are within their bands.

Under the owner's standing ruling (promote if structural integrity improves, even if a gate regresses), this run is a
**promotion candidate**.

## Bundles and cost of a promotion

- Each leg's full bundle, including `dispatch/<Y>_P1.parquet` and `hourly/unit_hourly_<Y>.parquet`, is on its shard
  branch listed above. The parent holds the bytes.
- The composed span carries every `hourly/` sidecar.
- A promotion is one `promote_keeper.py --iso NWPP --bundle results/calibration/nwppnext26_span`. It prunes the
  `2026-10-03-nwpp-next-25-served` stores, which means `gen_nwppnext25_attestation.py` stays because the NEXT-26
  generator imports it.

## §Promotion (2026-10-03)

- **Ruling.** Owner card "Promote". The close-out desk (session_01ERkBTm23ZAP4CTZnJVD9Ss) was told about the slot
  request.
- **Merge.** `origin/main` (8e4b87ab) was merged into `claude/nwppnext26`. It brought one new key on the backcast path,
  `zonal_loss_demand_reconciliation` (model/loss_demand.py, pipeline/solve.py). The key is gated, default off and not
  armed by NWPP, so it is INERT for this bundle.
- **Promotion run.** `promote_keeper.py --iso NWPP --bundle results/calibration/nwppnext26_span`, after the staged legs
  were moved out of `results/calibration`:
  - `keepers/NWPP.json` and the `program-status.json` gate-(a) marker re-keyed to `2026-10-03-nwpp-next-26-nevp`;
  - status rebuilt (NOT-YET);
  - audit run with only E13 tolerated;
  - `2026-10-03-nwpp-next-25-served` / `nwppnext25_span` pruned;
  - strict audit clean;
  - parity OK (9 runs, 9 bundle dirs).
- **Not deleted.** `scripts/gen_nwppnext25_attestation.py` and its NEXT-24 parent stay, because
  `gen_nwppnext26_attestation.py` imports them.
