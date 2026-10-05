# RESULT closeout-SOCO-w3p: SOCO measured running parasitic factors, structure vs gates

Lane closeout-SOCO-w3, 2026-10-05. The bars were fixed ex ante in `PRECOMMIT-parasitic-closeout-soco-w3p-2026-10-05.md`,
which was pushed before any shard launched.

## Verdict: structure improves, gates do not move

- **No record changes status** against the holdout control: zero FAIL→PASS, zero PASS→FAIL.
- Every move is in the declared direction.
- Every move is **smaller than the ex-ante band**: coal −0.25 to −0.94 TWh against a declared −0.5 to −2.0; CC
  +0.12 to +0.38 TWh against a declared +0.3 to +1.5.
- **Structure:** measured data replaces two estimates for 14 plants: the HR derives' class default, and the
  gross-as-net 1.0 fallback the tranche derives and the benchmark used. Per rule 14, the small worsening of fit is
  more evidence for SOCO-F1 (coal conduct), not a reason to keep the estimate.
- **Not promoted by this lane.** The owner rules.

## Run

| item | value |
|---|---|
| recipe | keeper `closeout_soco_3_span` + `mustrun_chp_btm_holdout=true` (the holdout recipe); no new ScenarioConfig field |
| pin | `6b83dc2ca7b1017eb070e486090814ed18829b3a` on `claude/closeout-soco-w3p`; branch-only data; parasitic parquet sha256 `636fbe53…` |
| data at the pin | 14 SOCO `measured_running` pooled rows; coal / CC / ST HR rebased; OOM level re-derived; tranche ratio transplant (PRECOMMIT §2) |
| legs (rule 36) | 2019 `720deef1`, 2020 `36e623eb`, 2021 `c05d7e0e`, 2022 `62196c51`, 2023 `2e17c87c`, 2024 `3a295aac`, 2025 `0235a1d4` (branches `claude/closeout-soco-w3p-<Y>`); each 18 files, P1 dispatch present, arm live, descends from the pin; all 7 shards archived |
| composed span | `results/calibration/closeout_soco_w3p_span` (`_closeout_socow3_compose.py`, pinned 6b83dc2c) |
| control | holdout probe `closeout_soco_w3_span` (pin 487bfdb8) |
| bench | rebuilt at the pin. The CEMS→net conversion for the 14 plants moves C4 only; C1 actuals are EIA-923 net and do not move. |
| kills | none fired: unserved energy 0, arm live, recipe as declared, all legs at the pin |

## Class deltas, probe − control (TWh, P1; `parasitic_class_deltas.csv`)

| Year | coal | of which PRB | CC_REGULAR | CT_PEAKER | ST_GAS |
|---|---|---|---|---|---|
| 2019 | −0.94 | −0.86 | +0.15 | +0.60 | +0.18 |
| 2020 | −0.44 | −0.39 | +0.21 | +0.17 | +0.06 |
| 2021 | −0.38 | −0.32 | +0.29 | +0.10 | −0.01 |
| 2022 | −0.25 | −0.20 | +0.20 | +0.05 | +0.01 |
| 2023 | +0.06 | +0.06 | +0.12 | −0.18 | +0.01 |
| 2024 | −0.43 | −0.38 | +0.22 | +0.15 | +0.07 |
| 2025 | −0.42 | −0.33 | +0.38 | +0.05 | +0.00 |

- The coal loss is the PRB plants Miller and Scherer, whose must-run and committed shares moved from gross to net.
- Bowen's running factor equals the old 0.93 default, so its heat rate does not move; only its tranche shares move
  (gross → net).

## Records, control → probe (`parasitic_score.csv`, rubric v3.20)

| Record | Control | Probe |
|---|---|---|
| C1 CC_REGULAR 2021 | FAIL +8.63 TWh | FAIL +8.93 |
| C1 CC_REGULAR 2023 | FAIL +7.57 | FAIL +7.69 |
| C1 COAL_BIT 2019 | FAIL −7.47 | FAIL −7.55 |
| C1 CC_REGULAR 2019 / 2024 | PASS +6.23 / +6.48 | PASS +6.38 / +6.70 |
| C1 COAL_PRB 2019 / 2024 | PASS +1.96 / −1.11 | PASS +1.10 / −1.49 |
| C3a 2019 / 2020 (mean) | FAIL +14.3 % / +14.5 % | FAIL +15.1 % / +14.7 % |
| C3a 2021–2025 | PASS | PASS, every year within 0.2 pp |
| C3b 2022 (monthly NRMSE) | FAIL 0.259 | FAIL 0.260 |
| C3b other years | PASS | PASS, within 0.008 |
| C4 coal r, 2019–2024 | PASS | PASS, −0.002 to −0.006 (2025 +0.003) |
| C4 gas | PASS | PASS, within 0.003 |
| C8 forced share, ST_GAS | 30.5–49.2 % | 28.8–48.6 % (lower every year; the gas-steam floor binds slightly less) |

## Against the ex-ante declaration

- **Direction:** confirmed for every declared item. Coal falls; CC rises; CC 2021/2023 deepen; COAL_BIT 2019
  deepens; C3a moves by about 1 %.
- **Magnitude:** about half the declared band. The must-run cut (−190 to −230 MW) is partly offset because the lost
  floor energy is economic in many hours, and peakers and ST take part of it (2019 CT +0.60).
- **The declared possible new CC FAIL in 2019 or 2024 did not happen:** 2019 is +6.38 and 2024 +6.70 TWh, both in
  band.

## Disposition and what it means

- **Structure-vs-gates card to the owner.** The correction is measured and parameter-free under the rule-14
  reconciled form (desk ruling B), and it moves no gate status. Promoting it would carry the 14 rows and the cascade
  (PRECOMMIT §2) onto main with the keeper. That needs the owner's ruling, because main's SOCO keeper replay
  otherwise drifts.
- **Kept off main until then:**
  - the data;
  - the bundle (`results/calibration/closeout_soco_w3p_span`, pushed with its local scoring registration to
    `claude/closeout-soco-w3p-reg`);
  - the pin branch.
- **Main receives:** the rebase script and its test, the transplant probe, the PRECOMMIT, this RESULT and the CSVs.
- **Cross-ISO:**
  - The derive's running-slope / fleet-scope / measured-only modes went to the all-ISO backfill lane (PR #7205),
    which reproduced the SOCO rows exactly.
  - The `factors.get(code, 1.0)` gross-as-net fallback in the tranche-family derives remains a cross-ISO
    inconsistency, recorded for that lane.
- **Still pending the owner:** the holdout promotion (A); this card stacks on it.
