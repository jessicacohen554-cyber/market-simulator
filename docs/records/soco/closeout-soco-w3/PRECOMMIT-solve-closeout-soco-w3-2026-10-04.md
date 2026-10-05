# PRECOMMIT closeout-SOCO-w3 — candidate 1: the host-steam/BTM holdout of SOCO's injected biomass (7 shards)

Lane closeout-SOCO-w3, 2026-10-04. Written and pushed before any shard is launched. Phase 0:
`FINDING-closeout-soco-w3-phase0-2026-10-04.md`.

## 1. Mechanism, driver, forward story

- **Mechanism.** The existing `ScenarioConfig.mustrun_chp_btm_holdout` (miso-253; default off; already a cache-key
  optional field and a matrix row with a cell in every shard). It drops chp=Y rows from the injected must-run
  residual classes (biomass, OTHER) at `run_calibration_full._eia923_frame`, the one seam the injection and the
  bench both read.
- **Driver (measured).** EIA-923's per-plant, per-vintage CHP flag. SOCO's biomass is 88–90 % chp=Y pulp-mill
  cogeneration. The injection error it removes is checked against an independent instrument: EIA-930 SOCO
  "Other" (exhaustive: its fuel split reconciles to SOCO's reported net generation to 0.000–0.4 %). Injection vs
  telemetry: 8.6–10.1 vs 1.9–2.7 TWh/yr before, 0.9–1.6 vs 1.9–2.7 after.
- **Rules.** 14 (a measured partition replaces an un-partitioned estimate; the residual ~1 TWh/yr over-removal is
  stated, not tuned), 13 (EIA-923 carries the flag for every vintage, so the construction regenerates forward),
  19 (scoped to the injected classes; gas cogen is already partitioned through `*_CHP`, coal cogen through
  `coal_chp_overrides`; nothing else floors or injects biomass), 21/24 (zero free parameters, a registered field),
  25 (SOCO's own numbers; MISO's O cell transfers nothing).
- **Forward story.** A forecast year reads the same flag from the latest EIA-923 vintage; the field is not in
  `_BACKCAST_ONLY_OVERLAY_FIELDS`.

## 2. Config delta

Replay of the keeper recipe (`results/calibration/closeout_soco_3_span`) with exactly one override:
`--set mustrun_chp_btm_holdout=true`. No src edit, no new field, no data change. Pin = this branch's HEAD after
this commit (a full 40-char SHA, recorded in the RESULT). G-DRIFT keeper legs (`0629d795`) → pin:
`GDRIFT-closeout-soco-w3-keeper-to-pin-2026-10-04.md`. A LIVE hunk there stops the launch.

## 3. Solve

Seven year-isolated shards (rule 36), 2019–2025, prompts from `scripts/shard_prompt.py --all-years`, env
`env_016R8xUY4maDbppZ6TEns5V8`, ≤ 6 alive. Each pushes its full leg including `dispatch/<Y>_P1.parquet`
(zstd-9 if > 100 MB). Compose with the closeout-SOCO-3 composer pattern (recipe check: keeper + exactly this
field), then `calibration_verdict.py` and `legitimacy_diagnostics.py`.

## 4. Bars (fixed now)

**Target (the lane's charter).**

- T1: C1 CC_REGULAR 2019 FAIL → PASS (share ≤ 3.0 pp). Reach: +2.0 pp.
- T2: C3a 2022 improves by ≥ 2.0 pp (keeper −13.7 %). Reach: −6.5 %.

**Declared C1 status changes.** Predicted: CC_REGULAR 2019 FAIL → PASS; COAL_BIT 2019 CAVEAT → PASS. Predicted
PASS → FAIL: none. At risk: CT_PEAKER 2023 (reach +2.8 pp against a 3.0 pp bar). Any other C1 PASS → FAIL is
reported as an undeclared flip.

**Declared C3 regressions (predicted by the restack, an upper bound).** C3a 2019 +8.7 → up to +15.9 %, C3a 2020
+8.4 → up to +19.1 %, C3b 2020 0.113 → up to 0.218. Under the desk's bar ("C3a/C3b do not worsen beyond band")
a C3a/C3b year that leaves its band means the candidate **does not beat the keeper on the gates**. It is then
reported as a rule-1/rule-14 structure-vs-gates trade (a measured input correction that worsens fit, which rule
14 says reveals a bug elsewhere) for the desk to card to the owner. It is not promoted by this lane, and no
promotion slot is requested for it on gate grounds.

**Kills (structural, any one ends the candidate).**

- K1 unserved energy or dump > 0 in any year.
- K2 C8 forced-share FAIL (ST_GAS stays GROUNDED as in the keeper) or a new D-4 failure.
- K3 the composer's recipe check finds any field beyond `mustrun_chp_btm_holdout`.
- K4 the shard log does not show the holdout line (`must-run CHP/BTM holdout <Y> SOCO: dropping …`) with the
  footprint in FINDING §1 within 0.01 TWh (the arm was not live).
- K5 C2 sysvol FAIL in any year.

**Verdict rule.** T1 and T2 met, no undeclared C1 PASS → FAIL, every C3a/C3b year in band, no kill → the probe
beats the keeper; the lane sends the desk the scored flips and the promotion cost and requests the slot.
T1 met but a C3 year out of band → structure-vs-gates card (above). T1 not met → candidate recorded in
`SOCO.js` with the solve's numbers and the lane takes the next candidate.
