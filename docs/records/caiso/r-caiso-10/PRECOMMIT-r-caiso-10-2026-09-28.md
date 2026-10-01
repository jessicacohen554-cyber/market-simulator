# PRECOMMIT — R-CAISO-10: disarm the RA bridge's `startup_aware` run screen (2026-09-28)

Written and pushed **before** any shard is launched. Every gate and direction below is fixed here.

## 0. Owner ruling

Decision card, this session, verbatim option chosen: **"Test disarm, 7 shards"** — keeper recipe +
`caiso_ra_bridge_startup_aware=false`, one shard per year 2019–2025, promote only if structurally
sound, report every criterion move at full magnitude.

This answers the admissibility question caiso-287 §8 left open ("an owner admissibility question
under rules 1/13, not a residual to tune"). No value is tuned: the arm removes one screen.

## 1. The arm

- **Keeper:** `2026-09-28-caiso-r9-sd-floor` (bundle `rcaiso9_A_span`, 2022–25; fold
  `2026-09-28-caiso-r9-fold`, bundle `rcaiso9_A_tp_2019_2021`).
- **Delta (the only one):** `caiso_ra_bridge_startup_aware: true → false`, through
  `replay_keeper.py --set` (the `prb_overrides` channel the keeper records it in).
- **Also passed:** `--persist-p0-dispatch`. This is write-only and byte-identical (caiso-287 §1). It
  lets the parent attribute each midday gap to a gate afterwards.
- **Mechanism accounting (rule 19 `[R-ONE-MECH]`):**
  - Removes a screen inside the existing `caiso_ra_mustoffer` bridge. It adds no floor.
  - D-2 attribution stays `ra_mustoffer_bridge`.
- **Rule 17 `[R-FLOOR-WINDOW]`:** the driver, window and forward story are the bridge's, unchanged.
  - Driver: RA must-offer.
  - Window: gaps between two detected P0 runs, within `[min_down, 24 h]`, subject to the restart
    inequality and the surplus decommit screen.
  - Forward: regenerates from the forecast year's own P0.
- **DOF (rules 20/21):** 0 new parameters.
- **Structural basis:**
  - The screen's anchor test prices a run off the model's **own** P0 duals: Σ(LMP_P0 − MC)·P/pmax
    ≥ startup cost.
  - It drops 42–60 % of detected runs (caiso-287).
  - This is the circularity `scenarios.py` already refused for ERCOT.
  - What the screen was built against, P0 phantom micro-runs chopping the belly, remains a real
    risk. The disarm will show its size.

## 2. G-DRIFT (rule 29(b), zero LP)

`git diff 980f2ed6 a6ac7dcf -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/replay_keeper.py scripts/lib data/raw/_validation-source data/raw/reference`

- Result: one hunk, `src/market_sim/data/renewables.py` (`_spp_wind_year_own_curtailment_rate`
  docstring).
- Classification: **INERT** for CAISO (docstring only, SPP branch).
- `data/raw` changes since the pin are SPP/SOCO only.
- The five shard input hashes (hard stop 2) re-measured at HEAD: identical to R-CAISO-9's.
- ⇒ form 4 is valid: the keeper's committed bundles are the control. No control solve.

## 3. Zero-LP evidence that motivated the arm

`scripts/probes/_rcaiso10_object1_census.py` → `results/calibration/_rcaiso10/object1_census.json`.
It reads the keeper legs, extracted from their R-CAISO-9 shard commits.

Midday (h9–16) CC_REGULAR plant-hours that CEMS shows on and the model has off, by the model's
same-day pattern:

| year | CEMS-on / model-off, MW | model ran before AND after (unfloored gap) | of which CEMS on all 24 h | RA floor held midday, MW |
|---|--:|--:|--:|--:|
| 2022 | 605 | 527 (87 %) | 436 | 837 |
| 2023 | 942 | 781 (83 %) | 701 | 795 |
| 2024 | 1,164 | 1,009 (87 %) | 882 | 751 |
| 2025 | 946 | 781 (83 %) | 721 | 959 |

- 2025 reproduces R-CAISO-9's −947 MW.
- Outages explain none of it: `UNAVAIL` = 0 in every year.
- Unit-level ceiling: flooring every whole-midday gap bracketed by same-day runs at 0.26 × available
  cap adds **275 / 344 / 380 / 534 MW** of mean midday output in 2022–25.
  - This is an upper bound on the arm's direct effect.

## 4. Pre-registered directions

| quantity | direction | note |
|---|---|---|
| CC_REGULAR midday (h9–16) mean MW | **up** in every year | ≤ §3 ceiling + displacement |
| RA floor (mech 7) midday MW | **up** in every year | |
| C4 gas NRMSE 2025 (0.299) | down | not a gate (rule 1) |
| C1 CC_REGULAR TWh | up | 2019–21 already +22.9 / +25.1 / +10.4 over. It will worsen there; reported, not a reason to reject. |
| C8 CC_REGULAR forced share (6.0–8.5 %) | up | must stay < 30 % or clear D-4 + D-1 |
| midday SP15 price | down or flat | more min-load energy |

## 5. Promotion rule (fixed now)

- **Promote** if both hold:
  - the 2022–2025 span re-scores **CALIBRATED**: no criterion newly FAILS, and C3c stays the single
    ledgered caveat;
  - C8 passes.
- **Owner decision card** if the span would read CALIBRATED-WITH-CAVEATS or NOT-YET.
  - A NOT-YET promotion withdraws the complete marker.
  - This session never takes that trade itself.
- The fold (2019–21) never decides (rule 30(c)).
- C4 improving is **not** a promotion reason, and C4 worsening is **not** a rejection reason
  (rule 1). The basis is the §1 structural argument.

## 6. Solve recipe

- One shard per year, 2019–2025 (rules 34(c), 35(c), 36). Template:
  `docs/records/caiso/r-caiso-10/shard-prompt.md`.
  - `{SRC}` = `rcaiso9_A_tp_2019_2021` for 2019–21 and `rcaiso9_A_span` for 2022–25.
  - `{SDCAP}` as in R-CAISO-9.
- Parent seam: `rcaiso_compose_span.py --require caiso_import_cap_floor_static
  caiso_intertie_partial_year_measured`, then:
  - legitimacy diagnostics;
  - registration;
  - attestation;
  - fold stamp.
- Labels: span `…caiso-r10-nosa`, fold `…caiso-r10-nosa-fold`. The shorthands differ.
