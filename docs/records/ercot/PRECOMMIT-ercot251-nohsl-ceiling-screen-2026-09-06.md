# PRECOMMIT — the no-HSL curtailment-gate repair, screened on 2023 (ercot-251)

> **Committed BEFORE the arm is solved.** Every gate, threshold and prediction below is fixed
> at this commit; a result that arrives after it may not move any of them. Rule 29
> `[R-SCREEN]`: this is a **screen**, so it is a STOP gate only — it may KILL the arm, it may
> never promote one, it contributes to no determination, and it is **never gated on a target
> residual**. Rule 22 `[R-HOLDOUT]`: **2022 is not touched by this screen** — not solved, not
> scored, not read as a gate.

## 1. Object

`docs/FINDING-ercot251-nohsl-curtailment-gate-2026-09-06.md`: in an ERCOT backcast year with
no measured HSL parquet, the renewable bound is `forecast_uncurtailed` (delivered × the 2025
reference curtailment rate) but `scripts/run_calibration.py` L2687/L2805 skip **both**
curtailment mechanisms on the premise that renewables "ride delivered-as-CF". The gross-up is
applied and nothing takes it back.

**Question this screen asks — structural, not residual:** does the reference-rate gross-up WITH
the ceilings armed reproduce what the measured-HSL bound produces on the same year and recipe?

## 2. Arm, control and the drift audit

**ARM (one solve).** ERCOT **2023** — a TRAINING year — on the carve-out recipe
`results/calibration/ercot236_k33_clip` (2023's designated config), with:

* the 2023 HSL parquet **withheld** (moved aside; tracked, `git checkout` restores), so the
  bound falls to `forecast_uncurtailed` — verified before this commit:
  `renewable_bound_provenance("ERCOT", 2023, {wind,solar}) -> forecast_uncurtailed`;
* the **repaired predicate**, so the ceilings arm;
* `--no-p1-basis-seed` (see the drift audit).

**CONTROL / REFERENCE.** No control solve is spent (rule 29(b)). Two fixed references:

| reference | wind | solar | total | basis |
|---|---|---|---|---|
| **2023 actual** (EIA-930, `bench/ERCOT/2023.json.gz`) | 107.988 | 31.868 | **139.856** | ground truth, drift-immune |
| keeper committed 2023 (`ercot248_two_config_keeper`, measured HSL + ceilings armed) | 107.353 | 32.684 | **140.037** | +0.18 TWh vs actual |

**The load-bearing gate is scored against ACTUALS, not against the keeper** — deliberately, so
no code drift since the keeper's solve can move it. The keeper row is reported as context and
is flagged drift-exposed.

**G-DRIFT (rule 29(b)), recorded before the solve:**

* **LIVE, and neutralized:** `bf37a0dc` (2026-09-06) seeds the cold-rebuilt P1 from the same
  year's P0 basis, **default ON in the calibration CLIs**, and ERCOT's keeper carries a
  P1-native floor bridge — exactly the route it seeds. ercot-249/250 §5.1 declined warm-starting
  P1 because it "can land on a different degenerate vertex and move the duals, which are the
  prices these arms are scored on". **Mitigation: the arm passes `--no-p1-basis-seed`**, the
  opt-out that commit ships, restoring the pre-commit solve path.
* **INERT:** `e0d55a5b` eGRID/EIA-860 memo (content-addressed, self-invalidating disk cache —
  same values); `9440f17d` malloc_trim removal (memory only); `110e9d99`/`bf1964bf` ruff
  format; every `caiso-*`/`nyiso-*`/`miso-*`/`neiso-*` commit (other-ISO branches); every
  `capx D*` and `SCN-*` commit (forecast lane — capacity evolution / capacity market, which a
  `mode="backcast"` run never enters).
* **DISCLOSED LIMITATION:** the keeper's own solve sha does **not resolve in this clone** (the
  2026-08-16 history rewrite / squash-merged branches), so a hunk-by-hunk diff against it is
  impossible and this audit is a commit-level classification over 2026-09-05→HEAD layered on
  ercot-249/250 §6's audit of 2026-08-25→2026-09-05. This is why G-3 is scored against actuals:
  the gate that decides the arm does not depend on the audit being complete.

## 3. Pre-solve predictions (zero-LP census, computed at this commit)

Reconstruction of the HSL-withheld 2023 fleet (`bundle_fleet.reconstruct_bundle_fleet`, no LP)
with the recipe's own frozen coefficients (`unpooled`, `panhandle_owner=share`,
depth_wind 0.1354, depth_solar 0.1614):

| quantity | wind | solar | total |
|---|---|---|---|
| grossed-up bound | 116.215 | 33.601 | **149.816** |
| **injected excess** over actual | +8.227 | +1.733 | **+9.960** |
| ceiling removes from the bound | 4.515 | 1.071 | **5.586** (56 % of the injection) |
| bound after ceiling | 111.700 | 32.530 | **144.230** (+4.374 vs actual) |

The LP then curtails further on its own (2022 measured that endogenous claw-back at ~2.5 % of
potential). **Predicted arm landing: 141–144 TWh renewable**, i.e. +1.2 to +4.4 over actual,
against a no-ceiling counterfactual of ≈146 TWh (+6.2) — which is the defect reproduced on a
known-truth year, and is NOT solved (its magnitude is arithmetic, not a claim).

## 4. Pre-registered gates — ALL must pass; any FAIL is a STOP

**G-1 PLUMBING.** The solve log does **not** emit either
`"has no measured HSL potential … skipped"` warning, and the bundle's D-10 rows read
`forecast_uncurtailed` for wind and solar. *A FAIL here is a wiring bug: fix and re-run; it is
not evidence about the repair.*

**G-2 CONFINEMENT.** The ceiling is confined to the rows it claims: multipliers are exactly 1.0
for every zone except West and Panhandle (verified pre-solve; re-verified from the arm's zonal
output). Any non-corridor zone's renewable energy moving is a FAIL.

**G-3 LOAD-BEARING — does the ceiling recover the injection?** The arm's grid-delivered
wind + solar must recover **at least half** the +9.960 TWh the gross-up injected:

> **PASS iff arm renewable ≤ 144.836 TWh** (excess over the 139.856 actual ≤ +4.980).
> **FAIL otherwise.**

The threshold is half the injected excess — arithmetic from §3, fixed here, not tuned to any
criterion. It is discriminating by construction: full translation of the ceiling lands at
144.230 (pass by 0.6 TWh), so material overlap with the LP's own curtailment fails it.

**G-4 DISPATCH RESPONSE.** The arm's CC_REGULAR must land within the C1 band (±8.00 TWh) of the
keeper's committed 2023 CC_REGULAR of 144.761 TWh:

> **PASS iff arm CC_REGULAR ≥ 136.761 TWh.**

**G-5 NO COLLATERAL FLIP.** No non-target load-bearing criterion (C2, C3a, C3b) may flip
PASS → FAIL relative to the keeper's committed 2023 verdict.

## 5. STOP rules — what a FAIL does NOT license

* **The depths are FROZEN** (`ercot_wtx_curtail_depth_wind/solar`, rule 23
  `[R-FROZEN-DERIVE]`). A G-3 miss is reported as a miss. **Re-running with different depths,
  a different `panhandle_owner`, or a different predicate variant to make G-3 pass is the
  fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, and is refused.**
* **One arm, one solve.** No sweep, no second arm chosen after seeing this one.
* A G-3 FAIL does **not** retract §1: the gate premise is still false and the repair is still a
  correctness fix. It would mean the ceiling **alone** does not recover the reference-rate
  gross-up, and that the honest posture for a no-HSL year is the FINDING's first-order route
  (obtain measured HSL) rather than the code repair.

## 6. What this screen may never do

Promote anything; contribute to any determination; be registered on the dashboard (rule 29(2):
a screen bundle is a throwaway diagnostic probe); be scored on, or read against, **2022**; or
change a keeper, a recipe, a matrix cell or the ERCOT partition. The screen bundle is
**deleted before this PR merges** (rule 29(c), owner ruling R-AV) — every number it produces is
carried by the FINDING/this doc, and git history is the record.

## 7. Reversal checklist (state this session must restore)

1. `data/raw/ercot-hsl/ercot_2023_hsl_hourly.parquet` — moved aside; restore before commit.
2. The predicate change in `scripts/run_calibration.py` — screen-only; reverted unless the
   owner admits the repair on its merits.
3. `results/calibration/ercot251_screen_*` — deleted before merge.
