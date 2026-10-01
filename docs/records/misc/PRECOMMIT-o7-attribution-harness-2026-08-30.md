# PRECOMMIT — O7 Phase 1: the attribution harness construction, fixed ex ante

**Date:** 2026-08-30 · **Lane:** O7 attribution harness (the §5 partial the
owner chose at the 2026-08-30 director sitting, over both accept-as-limitation
and keeper-moving restoration) · **Branch:**
`claude/o7-ercot-attribution-harness-aa7yeu` · **Base:** `origin/main` @
`67f1557` · **Charter:** `docs/FINDING-o7-p0-seam-restoration-2026-08-26.md` §5
+ `docs/PRECOMMIT-o7-p0-seam-restoration-2026-08-30.md`.

This document fixes, BEFORE the harness solves anything, (a) the exact
de-laddering construction — including the composition details finding §5 limit
(iv) says "the Phase-1 precommit must fix ex ante" — and (b) the predictions
the real-year exercise will be scored against, with the stop-rule falsifier.
**Solves run before this document was pushed: ZERO.** Unit tests on synthetic
toy systems (the trivial-first ladder of `docs/testing.md`) are construction
validation, not the measurement, and are the only executions permitted between
this push and the real-year legs.

The ruling's boundary, restated as a hard constraint on everything below:
**nothing here may change the CALIBRATED two-config ERCOT keeper's registered
numbers, bounds, or artifacts.** The keeper bundles
(`results/calibration/ercot236_k33_clip`, `ercot234_eastex_identity`), the
dashboard, the keeper shard and the mechanism cell verdicts are read, never
written, by the harness. The forfeiture re-verification and the 73/132-row /
12,474 MW P0-delta measurement are already on record (finding §1, §4 — citing
`results/calibration/ercot188_p0_delta.json`); this lane cites them and does
not re-derive them.

---

## 1. The construction

**The harness is one probe script,** `scripts/probes/o7_attribution_harness.py`
(pattern: `scripts/probes/ercot188_p0_delta.py`), plus its unit test. **Zero
`src/` edits, zero `ScenarioConfig` fields, zero CLI flags on the calibration
entry points.** It replays members through the SAME entry point the A/Bs use —
`replay_keeper.build_kwargs(meta.json)` → `run_calibration_full.solve_and_persist`
into throwaway directories — with `MARKET_SIM_WARMSTART_XYEAR=0` pinned (the
188-probe / replay_keeper reproducibility pin: no disk-basis seed, no
cross-year apply, every leg's P0 a cold deterministic solve).

Three legs per compared year, run sequentially (rule 12; one 15 GB box):

* **Leg A — keeper arm:** the keeper recipe exactly as recorded, wrapper in
  capture-only mode.
* **Leg C — control:** the keeper recipe with
  `ercot_econ_curve_top_refine=False` through the `prb_overrides` channel (the
  only channel the field rides — it has no `solve_and_persist` kwarg, so the
  ERCOT-65 kwarg-over-prb stomp class cannot occur). The wrapper additionally
  saves the coarse fleet's `(unit_ids, pmax, mc_base)` capture for leg L.
* **Leg L — de-laddered arm (finding §5 "Leg 2"):** the keeper recipe exactly
  as recorded, with ONE additive `(n_gen, T)` component `Δmc` merged into the
  composed `mc_bid_adjust` argument of `run_energy_solve`
  (`pipeline/solve.py`), which the seam applies at `solve.py:314–315` —
  strictly after `r0 = model.solve(mc=mc_base)`. P0 never sees it.

The wrapper is a monkey-patch of `scripts.run_calibration.run_energy_solve`
(the module-global name `run_year`'s call sites resolve at call time), applied
only inside the probe process. Nothing in the repo's runtime path changes; see
§3 on disarmed inertness.

### 1.1 Δmc — the fleet-diff form (the finding's formula, computed by the
pipeline's own builder)

Finding §5 gives `Δmc(g,t) = (hr_coarse(g) − hr_refined(g)) ×
(fuel_price + carbon·ef + …)(g,t)` on the top sub-slice rows only, and limit
(iv) requires it to "reproduce every heat-rate-linked term in `mc_base`". The
harness computes exactly that quantity by **row-wise difference of the two
fleets' `mc_base` matrices as captured at the `run_energy_solve` seam**:

```
Δmc[row, :] = mc_base_coarse[parent_top_row, :] − mc_base_refined[row, :]
```

on each refined plant's top sub-slice rows, zero everywhere else. Because both
matrices are produced by the pipeline's own `assemble_mc` + downstream
mc_base-resident mechanisms (EAC credits, coal tranche fuel fractions, the
`gas_offer_net_revenue_margin` markup — which `run_calibration.py:3879` writes
INTO `mc_base`, i.e. into the P0 objective — the cc-committed margin, measured
interchange injections), the fleet-diff reproduces every heat-rate-linked term
AND every other mc_base-resident rung-keyed term exactly, with no re-derived
formula to drift. Leg L's P1 therefore clears the coarse top-block **base
cost** on the refined geometry — the finding's construction, with its "…"
closed by construction rather than by enumeration.

### 1.2 Row mapping (from `_econ_curve_steps` geometry, verified at run time)

Rows key as `prefix = unit_id.rpartition("_")[0]` (the
`{group}_{zone}_p{plant_code}` plant-bin identity, `assembly.py:675`) and
`suffix = unit_id.rpartition("_")[2]`; candidate rows are those whose suffix
fullmatches `econc\d{2}` (`_econ_curve_steps`, `offer_curves.py:322`). Per
prefix, with `m` coarse candidates and `m′` refined candidates:

* `m′ == m` → refinement did not fire for this plant (`_top_refine_ok`
  refusal, or no smoothing ramp): Δmc rows are zero; the paired rows must be
  bitwise-equal in `mc_base` and equal in `pmax` (assert).
* `m′ == 2m − 1` (with `m ≥ 2`) → SCHEME R1 fired: body rows `k ∈ [0, m−2]`
  must be bitwise-equal in `mc_base` and equal in `pmax` (assert — the
  slicer's "expression-for-expression identical" body); sub-slice rows
  `k ∈ [m−1, 2m−2]` take Δmc against the coarse `econc{m−1}` parent row.
  Capacity conservation asserts: each sub-slice `pmax == parent/m` and their
  sum equals the parent top block (atol 1e-6 MW).
* any other `(m, m′)` → hard error. That is a stop-report condition, not a
  fallback.

Non-candidate rows (every `mustrun`/`committed*`/`peak*`/`econlo`/`econhi`/
non-econ row) must appear in BOTH fleets with identical `unit_id`, bitwise-
equal `mc_base` rows and equal `pmax` (assert) — the internal control that the
two builds differ by the refinement alone.

### 1.3 Composition details fixed ex ante (finding §5 limit iv)

* **SWCAP clip** (`ercot_offer_swcap_clip`, armed in the 2023 keeper): the
  seam clips `mc_base` to `voll − ε` BEFORE P0 (`solve.py:255–257`) and the
  fully-assembled bid AFTER every adjustment (`solve.py:342–343`). The wrapper
  captures `mc_base` as passed INTO `run_energy_solve` — pre-clip — so Δmc is
  computed on unclipped values and the P1-half clip then bounds the assembled
  de-laddered bid exactly as it bounds the keeper's. The harness asserts that
  every econc candidate row in both fleets sits strictly below the clip level
  in every hour (predicted margin ≥ order 10×: VOLL = 5000 vs econ-band costs
  of order $10–300/MWh), so the pre-P0 clip is a no-op on every row Δmc
  touches and the composed semantics are exact.
* **Startup markup:** untouched by construction. Econ slices carry zero
  startup cost (`_econ_curve_steps` emits `min_run 0, min_down 0, startup
  0.0`), so their markup rows are zero; the harness asserts
  `markup[target_rows] == 0` and discloses loudly if a future recipe breaks
  that.
* **The two-pass adaptive recipe:** both keepers arm
  `ercot_storage_adaptive_expectation` (with `ercot_adaptive_fixed_point`
  False), so `run_energy_solve` fires exactly TWICE per year — the ercot-221
  incumbent pass and the scored pass 2, sharing `mc_base`, the composed
  offer-surface adjust, and the fleet; pass 2 adds only the P1-only
  `p1_storage_discharge_cost` derived from pass-1's P1 result. Δmc merges into
  BOTH calls (the recipe's `mc_bid_adjust` is the same object at both call
  sites); leg L's pass-2 storage floor responds to leg L's own pass-1
  de-laddered prices — that is the recipe held fixed, responding to the
  instrument's prices, and is part of the pricing channel as defined. P0
  bit-identity is asserted PER CALL INDEX.
* **P0-conditioned hooks** (the armed `ercot_gas_commitment_bridge` fleet
  prep; any `p1_bid_adjust_prep`): every input they read — `r0`, `mc_base`,
  the fleet — is bit-identical between legs A and L by construction, so their
  outputs (the detected min-gen floors above all) are identical. The harness
  proves rather than argues this: it hashes `p1_fleet_arrays.min_gen` and the
  markup per call and requires equality (§2 HP-1).
* **`p1_bid_max_target`:** None on both keeper recipes
  (`ercot_offline_commit_offer` False, `pjm_ct_measured_max_reprice` PJM-only),
  so the max() seam is inert here. The harness records the fact; if a future
  recipe arms it, the harness reports where the target re-floors de-laddered
  rows instead of silently absorbing it.
* **Residual rung structure, disclosed:** P1-only adjust components keyed to a
  row's own multiplier (the conditional / cleared-share / fast-start-pool
  offer surface) are keeper machinery HELD FIXED in leg L — Δmc de-ladders
  `mc_base` only, per the finding's formula. The harness measures and reports,
  at full magnitude, the residual per-plant spread of the assembled `mc_bid`
  across each refined plant's sub-slices in leg L (annual mean/max), so "how
  completely the ladder is flattened in the P1 objective" is a reported
  number, never an assumption.

### 1.4 What is measured and reported

Per leg and call: content-addressed SHA-256 over canonical serializations
(shape + dtype + C-order bytes) of the P0 solution — `r0.dispatch`,
`r0.prices`, `objective_value` (bit-exact via `float.hex()`), and a composite
over every P0 array the result carries — plus the markup, the P1 floors
(`p1_fleet_arrays.min_gen`), and `mc_base`; the 188-style committed-row run
stats (starts / on-hours per committed row) so commitment fixedness is also
stated in physical terms; and from the scored pass-2 P1: the annual
load-weighted price (system and per-zone), hourly system price quantiles
(p50/p95/p99/max), price-spike hour counts, total slack (shed) MWh, and total
dispatch by suffix class. The decomposition, on any scored scalar `s`:

```
pricing channel        = s(A) − s(L)      (bit-identical-P0 pair)
whole-solve A/B        = s(A) − s(C)
commitment + interaction = s(L) − s(C)   (= the A/B minus the pricing channel)
```

The identity `(A−C) = (A−L) + (L−C)` is exact by arithmetic; `L − C` is
reported as "commitment channel **plus interaction**, at full magnitude" —
finding §5 limit (iii)'s honesty clause — never as a pure commitment number.

**Object year and bundle: 2023 on `ercot236_k33_clip`** — the CALIBRATED 2023
keeper and the hardest composition case (swcap clip + bridge + margin + the
adaptive two-pass all armed). One year, inside {2023, 2024, 2025} (rule 22).
A single-year identity probe is a throwaway diagnostic under rule 16 — never
registered, never a keeper.

## 2. Predictions — fixed now, never renegotiated

* **HP-1 (bit-identity, the charter's precommitted prediction).** For each
  energy-solve call index k ∈ {1, 2}: leg L's P0 hashes equal leg A's — the
  `r0.dispatch` hash, the `r0.prices` hash, the objective bits, and the full
  P0 composite — and the markup hash and the P1 min-gen floors hash equal
  likewise, so the commitment scaffolding is provably the keeper's. The
  committed-row run stats are equal row-for-row. **Falsifier:** ANY of those
  hashes differing. Per the charter's stop-rule the response to the falsifier
  is a stop-report against this precommit — never a widened seam, never a
  fallback construction.
* **HP-2 (instrument sensitivity).** Leg L's scored-pass P1 differs from leg
  A's: the ladder's pricing channel is nonzero. Expected order, transported
  from FINDING-ercot188 §6.2's quantity-fixed IQR arithmetic (+$1.99/MWh at
  the 188-era recipe): `lw(A) − lw(L)` positive at order +$1–3/MWh on the 2023
  annual load-weighted price. The order and sign are stated as context and are
  NOT a gate — the harness reports whatever it measures at full magnitude
  (rule 1: the verdict never keys on fit direction). A measured ≈ 0 pricing
  channel with HP-1 intact would itself be a finding (the ladder pricing out
  entirely through commitment), reported, not suppressed.
* **HP-3 (control-side reproduction).** Leg C's P0 differs from leg A's (the
  inherent P0 exposure, finding §2) — the harness records the C-vs-A committed
  fleet commitment delta at the 236 recipe as fresh context. No numeric
  prediction is transported: the finding says 188-era magnitudes do not carry
  to the 236/234 recipes; the only prediction is that the delta is NONZERO
  (were it zero, the forfeiture story itself would need re-examination — a
  surprise this precommit would have to report against the charter, not
  absorb).

## 3. Governance

* **Rule 1 `[R-STRUCT]`:** the harness is measurement scaffolding and is
  provably inert when disarmed: it adds NO line to `src/` or to any
  calibration entry point — the disarmed path is HEAD itself. Verification
  recorded with the proof: `git diff origin/main..HEAD -- src/` empty at the
  harness-run commit, and the probe's captures record the `git` tree state it
  ran at. Leg A is additionally a live inertness check: the wrapper in
  capture-only mode must reproduce a keeper-recipe replay exactly (it computes
  nothing and passes every argument through unchanged).
* **Rules 5/20/24 `[R-NO-MAGIC]/[R-DOF]/[R-REGISTRY]`:** zero new tunables,
  zero fields, zero env-var knobs (the one env write is the existing
  `MARKET_SIM_WARMSTART_XYEAR=0` reproducibility pin the replay/probe lane
  already uses). Rule 26 duty (c) does not fire (no ScenarioConfig field);
  duty (b) evidence-trail stamping is done by this session on completion, per
  finding §5/§8.
* **Rule 13 `[R-MEASURED]` / finding §5 limit (ii):** leg L is an instrument,
  not a market state — a synthetic-adder config if it were ever registered.
  It is not registered, not dashboarded, not scored against actuals; the probe
  writes its decomposition JSON to `results/calibration/` (committed, like
  `ercot188_p0_delta.json`) and its solve directories are temporary.
* **Rule 22 `[R-HOLDOUT]`:** every solve year ∈ {2023}; nothing outside
  training is touched.
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT-only throughout (the probe hard-asserts
  `iso == "ERCOT"` on the replayed meta).
* **Rule 27 `[R-PUSH]`:** all pushes are new files or small doc edits over
  `git push` on a fresh-fetched base; any ≥300-line file is blob-verified
  after push.

## 4. Disclosure

Written after reading the committed record (the two O7 charter docs, the two
keeper bundles' `run_config.json`/`meta.json`, FINDING-ercot188 §5–§6 and its
probe, and the live seam code: `pipeline/solve.py`, `pipeline/year.py`,
`scripts/run_calibration.py` lines cited above, `scripts/replay_keeper.py`,
`data/offer_curves.py::_econ_curve_steps`, `data/fleet/assembly.py`) and
before running any solve. The thing HP-1 predicts — bit-identity of the P0
pair under an `mc_bid_adjust`-seam merge on THIS recipe — has never been
measured by anyone; it is the finding's one precommitted prediction, inherited
here as the harness's acceptance condition.
