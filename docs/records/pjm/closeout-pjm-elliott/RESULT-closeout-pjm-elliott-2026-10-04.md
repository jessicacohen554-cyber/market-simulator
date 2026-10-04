# RESULT — closeout-PJM-elliott: the hourly measured Elliott overlay clears 2022 C3a/C3b (probe; promotion requested)

Lane `closeout-PJM-w2` on branch `claude/closeout-pjm-elliott`, owner ruling R-64. Bars:
`PRECOMMIT-closeout-pjm-elliott-2026-10-04.md`, committed `e7aa98ff` before any build or solve and not re-read.
Build pin: **`fa9c04599a5115e6169bc01416a84677cd93fd1b`**. Probe **`2026-10-04-closeout-pjm-elliott`**, bundle
`results/calibration/closeout_pjm_elliott_span`. The registration stays on transport branch
`claude/closeout-pjm-elliott-probe`, off `main` (E13). The keeper is unchanged: `2026-10-03-closeout-pjm-nuc-keeper`.

## Verdict

**Every bar passes and both kills hold.** **C3a 2022 and C3b 2022 go FAIL→PASS**. There is
no C1 PASS→FAIL. The other six years reproduce the keeper exactly. PJM stays **NOT-YET**, on C1 COAL_BIT 2019–21,
C1 CC_REGULAR 2022 and C3a/C3b 2025, but failing records fall from 8 to 6.

| bar | reading | result |
|---|---|---|
| R1 C3a 2022 within ±10 % | −16.7 % → **−6.4 %** (model $74.30 vs RT lw $79.37) | **PASS** |
| R2 C3b 2022 ≤ 0.20 | 0.293 → **0.183** | **PASS** |
| R3 Dec 23–24 mean ≥ $800 | $113.02 → **$1,259.32** (real $1,010.37); 29 h > $800; max $1,945 | **PASS** |
| R4 other years within noise | 2019/20/21/23/24/25: every class Δ **0.000 TWh**; C3a, C3b and slack identical to the keeper | **PASS** |
| R5 no C1 PASS→FAIL | none. CC_REGULAR 2022 FAIL +8.96 → +8.59; COAL_BIT 2022 PASS +6.97 → +6.89 | **PASS** |
| K1 no change outside rows 8544–8615; no new slack outside | `cap_mw` byte-identical outside the window (26.6 M unit-hours compared); slack outside the window 0 MWh | **holds** |
| K2 unserved in window ≤ 100,000 MWh | **55,952 MWh** | **holds** |

## Readings

- **Overlay.** The 2022 log shows all four fuels withdrawn over the 72 event hours, and nothing outside them. The
  six other legs log no overlay line.
- **2022 energy (all in-window).** CC_REGULAR −0.37, CT_PEAKER +0.35, oil +0.09, COAL_BIT −0.08, nuclear −0.04,
  CC_CHP −0.01, ST_GAS +0.01 TWh.
- **C3c 2022 (reported).** Hours above $200 go from 2 to **32**, against 92 real. It moves from 0.02× to 0.35× of
  actual and stays outside the [0.5×, 2×] band. That is still a C3c miss, ledgered as before.
- **Probe-only C3c rows.** On the unattested probe, C3c 2019/2021 read FAIL only because no attestation carries the
  keeper's ledgered C3c entry. Their magnitudes are identical to the keeper's (5 h / 0 h).
- **HEAD drift since the keeper's pin 8c3ea461** (eGRID reader, EIA-930 envelopes and demand, `pipeline/solve.py`)
  is **inert** for PJM. Six legs solved at the new pin reproduce the keeper to the MWh.

## Disclosed against interest

1. **Unserved energy.** In the 18 deepest hours the LP sheds up to about 6 GW at VOLL ($2,000), 55,952 MWh in all.
   Real PJM shed no firm load: it got through on emergency procedures (DR, maximum-generation emergency, emergency
   imports from NYISO), which this LP does not represent. The price outcome is close to real (PJM printed $3,700
   shortage intervals), but it is reached through load shed rather than emergency supply. This is a representation
   boundary, not a fitted effect.
2. **Phase-0 estimate missed.** The PRECOMMIT's "upper" unserved estimate (44,655 MWh) was not an upper bound: the
   solve is 25 % above it. The estimator ignored the P0→P1 commitment response. K2's 100,000 MWh cap was set with
   about 2× margin and holds.
3. **Digitisation uncertainty.** About ±104 MW per bar (±1 px; check bar +0.27 %). At 6 GW of shed, that cannot move
   any gate.

## Bundles (rule 34)

| year | leg branch @ sha | shard (archived) |
|---|---|---|
| 2019 | `claude/closeout-pjm-elliott-2019` @ 760bdea2 | session_013Pygex1XSnotzoaRWfZdhA |
| 2020 | `claude/closeout-pjm-elliott-2020` @ 9c2519eb | session_01SMeuULtp8CPJGHXiobh7bM |
| 2021 | `claude/closeout-pjm-elliott-2021` @ 09d69e2b | session_016po86VF9JwQS1jNzfvzKpM |
| 2022 | `claude/closeout-pjm-elliott-2022` @ d4ea021f | session_01UYu74KVYdAbG9dMz476VoB |
| 2023 | `claude/closeout-pjm-elliott-2023` @ 3f199fb9 | session_01ApRSGGhKzuodUzpjdMWu6H |
| 2024 | `claude/closeout-pjm-elliott-2024` @ 7cb9f97f | session_01QtcxKjMncmYPHXpy8HK66v |
| 2025 | `claude/closeout-pjm-elliott-2025` @ 512324fe | session_01JiQ7fXsAAKruHLS44sHDhp |

- **Legs.** Each has 18 files including `dispatch/<Y>_P1.parquet` and `hourly/unit_marginal_<Y>.parquet`, verified
  with `git ls-tree` and extracted locally.
- **Composite.** `_pjmnext26_compose_span.py --declared-delta pjm_elliott_measured_outage_overlay=true` (the
  composer gained that flag in this lane) confirmed: the recipe is the keeper plus the one declared field in every
  leg, with one solve-surface fingerprint and one pin.
- **Promotion cost.** One `promote_keeper.py` run from the probe branch (94 MB slim layer, 53 files). Its
  attestation carries forward the keeper's exceptions ledger, with C3c 2022 re-measured at 32 h vs 92 h. The
  dispatch parquets stay on the leg branches.

## Matrix

`pjm_elliott_measured_outage_overlay` PJM: U, with evidence stamped "probe scored; beats the keeper on structure;
promotion requested". It goes to K only on promotion.
