# PRECOMMIT closeout-CAISO wave 1, arm 3 (runs first): `caiso_ra_min_load_frac` 0.26 → 0.570 measured (2026-10-02)

Written before any solve. Plan §3.7 step 3; owner rulings R-11 (retire residual free parameters; "CAISO min-load
0.26 → 0.570 … promoted only if nothing regresses") and R-14 ("re-solve `caiso_ra_min_load_frac` at the measured
0.570"). **SOLVES HELD** until the W0 foundation lane merges and the desk releases this lane. **Runs FIRST** (desk ruling 2026-10-02, after the W0 merge `306f2c00`). Arm 2 follows sequentially and stacks on this
arm's keeper if it promotes.

## 1. Mechanism, driver, forward story (rule 13)

- **Mechanism.** `caiso_ra_min_load_frac` is the minimum stable load (fraction of available capacity) at which the
  CAISO RA must-offer bridge holds a gas CC/CT across a midday idle gap shorter than its physical min-down time
  (`model/commitment.py::caiso_ra_mustoffer_min_gen`, via `pipeline/commitment.py`; P0→P1 seam). It is a per-leg
  sub-scalar of the `gas_commitment_bridge` matrix row.
- **Measured value 0.570.** CEMS per-unit p05 of `grossLoad / pmax` over fully-online hours (`opTime == 1.0`),
  cap-weighted p50 across CC units with ≥ 500 op hours. It reads 0.565 / 0.570 / 0.570 for 2023–25, stable to 1 %.
  ERCOT's independent 60-Day-DAM analogue reads 0.574 (`docs/calibration-log/caiso.md:1153–1160`, caiso-119).
- **Why 0.26 goes.** The incumbent 0.26 sits below any physical CC turn-down. It is not in the keeper's DOF ledger:
  `calibration_attestation.json` lists 9 free parameters and this field is not one of them. caiso-119 found its
  "CEMS-measured" description inaccurate.
  - The `pipeline/backcast_config.py:1650` comment still cites a 0.259 capacity-weighted `committed_pct` from
    `thermal_tranches_CAISO.csv`. That is a committed-tranche share, not a turn-down limit.
  - The log rules: "It is never tuned back toward 0.26 (rules 13/18/25 — that is how 0.26 got there)" (`:1179`).
- **What blocked it before is gone.** The 2026-07 arm (caiso-121) failed C3a-2025 at +11.3 %, but its same-HEAD
  control failed worse (+11.49 %). The incumbent keeper now passes C3a-2025 at +6.6 % (3.4 pt margin).
- **Forward story.** A physical turn-down limit of the fleet, re-measured from CEMS when the fleet changes. It is not
  a price or volume fit.

## 2. Exact config delta

- One field: `--set caiso_ra_min_load_frac=0.570`. Nothing else moves.
- Recipe (control): the post-W0 CAISO keeper (W0 step 4). The recipe resolves on `306f2c00`: a fleet-only rebuild
  gives `caiso_ra_min_load_frac=0.57`. The incumbent `rcaiso20_*` bundles are not
  usable as control (FINDING §4: the 2025 fleet drift is LIVE).
- If this arm promotes, the same PR updates the `pipeline/backcast_config.py` CAISO value 0.26 → 0.570 and its
  comment. Under rule 26 the stale 0.259 `committed_pct` justification is deleted, not kept beside the new value.

## 3. Zero-LP footprint

D-2 rows of the incumbent bundles (`legitimacy_diagnostics.json`), `ra_mustoffer_bridge` on CC_REGULAR:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|--:|--:|--:|
| forced TWh at 0.26 | 3.68 | 3.30 | 3.71 | 4.19 | 4.18 | 4.53 | 4.89 |
| forced share of class | 7.9 % | 5.4 % | 6.3 % | 7.7 % | 8.0 % | 9.7 % | 12.2 % |
| **upper bound** at 0.570 (× 0.570/0.26) | 17.2 % | 11.9 % | 13.7 % | 17.0 % | 17.6 % | 21.2 % | **26.8 %** |

The upper bound assumes every floored cell binds at the floor. The measured elasticity is far smaller. In caiso-119
(`floors/<year>_P1.npz`), +119 % on the fraction moved floored MW +0.7 % per cell, because the bridge level is
capped and owns 1.8 % of floored cells. **Expected: C8 moves < 1 pt; the bound stays under the 30 % cap in every
year.**

## 4. Shards (rules 32, 34, 36)

Seven shards, one per year, pinned to the full 40-char release SHA, two `shard_prompt.py --all-years` calls (span and
fold bundles of the recipe above):

```bash
python3 scripts/shard_prompt.py --iso CAISO --all-years --sha $SHA --lane closeout-caiso-w1-a3 \
    --bundle results/calibration/<recipe span|fold> --set caiso_ra_min_load_frac=0.570 \
    --note "closeout-caiso-w1 arm 3: measured CC min-load 0.570 (R-11/R-14)"
```

- Extra hard stop (THE ARM): each bundle's `run_config.json` must record `"caiso_ra_min_load_frac": 0.57`.
- G-DRIFT as arm 2 §3.
- Compose, score and diagnose as arm 2.

## 5. Pre-fixed readings and decision rule

| Gate | Bar |
|---|---|
| C3a every scored year | \|Δ\| ≤ 1.0 pp; **C3a 2025 ≤ +10 %** (no new FAIL) |
| C4 2025 | NRMSE ≤ 0.30 |
| C1 CC_REGULAR 2022–25 | \|Δ\| ≤ 0.5 TWh, still PASS |
| C8 CC_REGULAR forced share | ≤ 30 % every year (expected < +1 pt) |
| span determination | stays CALIBRATED, no new caveat |

- **PROMOTE** iff every bar holds. This is R-11's "promoted only if nothing regresses", with the fold's movement
  reported. The DOF ledger then loses one unledgered residual-identified value (rule 21) and gains no parameter.
- **If any bar fails**, do not promote. The RESULT puts the owner card R-11 anticipates:
  - (a) keep 0.26 and ledger it in the DOF ledger as residual-identified, with the regression as its identification
    source (rule 21: an open root-cause issue); or
  - (b) accept the regression under rule 14 and root-cause it.
  0.26 is never re-tuned toward any other value (log `:1179`).
