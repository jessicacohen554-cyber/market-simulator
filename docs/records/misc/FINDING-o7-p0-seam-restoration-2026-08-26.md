# FINDING — O7 Phase 0: the ERCOT P0 bit-identity restoration is scoped, and the answer is ESCALATE — every seam-restoring construction changes the CALIBRATED keeper's numbers, and the P0 exposure is INHERENT to the mechanism, not incidental to its wiring

**Date:** 2026-08-30 (charter issued on the owner's 2026-08-26 ruling; filename
carries the ruling date per the charter) · **Lane:** O7 restoration, Phase 0 ·
**Branch:** `claude/ercot-p0-bit-identity-o7-tuzrjm` · **Base:** `origin/main`
@ `4ed7cd3` · **Solves run: ZERO.** Every number in this finding is read from
committed artifacts; the one prediction it makes was pushed first as
`docs/PRECOMMIT-o7-p0-seam-restoration-2026-08-30.md` (commit `9513366`).

---

## 0. Headline

**Phase 1 is NOT entered.** The charter's own stop-rule fires: restoration is
not achievable without changing the keeper's results.

1. **The forfeiture is LIVE, re-verified** (§1): both current ERCOT keepers arm
   `ercot_econ_curve_top_refine: true`, and both also arm
   `ercot_gas_commitment_bridge: true` — whose min-gen floors are *detected
   from the P0 run pattern*, so P0 motion propagates into P1 bounds, not just
   P1 prices.
2. **The P0 exposure is INHERENT in mechanism terms** (§2): R1 is a
   fleet-representation (cost-model) change, not a bid-conduct change. Its
   entire object is LP column structure — width-axis resolution of the supply
   curve — and the architecture builds ONE `DispatchModel` whose columns P0 and
   P1 share, with an objective-only seam between them. A `(n_gen, T)` bid
   adjustment cannot create columns; only argument, not wiring, connects the
   flag to `mc_bid_adjust`, and the argument fails.
3. **Every construction that removes R1's P0 half reverts a MEASURED
   commitment channel** (§3–§4): ercot-188's own P0-delta probe recorded 73 of
   132 committed rows — 12,474 MW, 55.3 % of the committed fleet — changing
   commitment state, and bridge floor counts moving in all three years. The
   predicted keeper cost (precommit P-2) is **order +$1–3/MWh on the 2023
   annual load-weighted price (center ≈ +$2.2/MWh)** plus unpredictable motion
   in C3b/C3c/G-SHED. That is a mechanism change to a CALIBRATED keeper —
   **the charter says that ESCALATES, and this finding escalates it.**
4. **A cheaper partial EXISTS and is the recommended path** (§5): a
   decomposition probe harness at the existing `mc_bid_adjust` seam that makes
   the P1-ladder leg of any R1 A/B **bit-identical in P0 by construction**
   (hash-provable), isolating the pricing channel and, by subtraction, the
   commitment channel — restoring ATTRIBUTION, which is the practical benefit
   the forfeiture cost, with the keeper and the mechanism untouched.

**Owner decision required:** §6 (three doors; Door 2 recommended).

---

## 1. The live forfeiture, re-verified at HEAD (charter Q0)

Verified directly from the committed `run_config.json` of each keeper bundle,
not from the shard prose:

| | `ercot236_k33_clip` (CALIBRATED 2023 keeper) | `ercot234_eastex_identity` (3-year recipe) |
|---|---|---|
| `scenario_config.ercot_econ_curve_top_refine` | **true** | **true** |
| `calibration_flags.coal_prb_sigmoid_overrides.ercot_econ_curve_top_refine` | true | true |
| `ercot_gas_commitment_bridge` | **true** | **true** |
| `offer_curve_smoothing_n` / `_exp` / `_mid` | 6 / 1.0 / 0.35 | 6 / 1.0 / 0.35 |
| `ercot_offer_swcap_clip` | true | (field absent — predates the mechanism) |

The charter's urgency claim stands: this is not a historical artifact — the
designated CALIBRATED keeper runs with the seam breached, and with the bridge
armed the breach reaches P1 through TWO channels (startup markup AND detected
min-gen floors). The ScenarioConfig default is `False`
(`src/market_sim/config/scenarios.py:9238`; the charter cited :9228 — a
10-line drift from later edits, same field).

---

## 2. Charter Q1 — the full path from flag to P0, and the inherent/incidental verdict

### 2.1 The trace

1. **Flag:** `ScenarioConfig.ercot_econ_curve_top_refine` (`scenarios.py:9238`,
   default False).
2. **Gate:** `bins_to_fleet` resolves
   `curve_top_refine = flag AND config.iso == "ERCOT"`
   (`data/fleet/assembly.py:832` — the rule-25 containment; the slicer itself
   is ISO-agnostic).
3. **Per-plant feasibility:** `_top_refine_ok(curve_cap, n, enabled)`
   (`assembly.py:106`) — refuses plants whose sub-slices
   (`curve_cap / n²`) would fall under `MIN_TRANCHE_CAPACITY_MW = 0.5`
   (`assembly.py:103`) and be dropped, deleting capacity.
4. **Slicer:** `_econ_curve_steps(..., top_refine=True)`
   (`data/offer_curves.py:243`, geometry branch :309): the econ ramp's top
   block is re-sliced n ways — 6 slices become 11 (`2n−1`), the body's n−1
   blocks byte-identical, each new sub-slice carrying its own heat rate
   `base_hr × mult(t_j)`. Reached from all three econ-band call sites
   (`assembly.py:842` per-plant sheet, `:879` offer-curve band, `:906`
   standalone econ split); the committed-band call site (`assembly.py:994`)
   hard-passes `False`.
5. **Into the LP:** the slices become `Generator` rows → `FleetArrays` → (a)
   the column layout of the single `DispatchModel`
   (`pipeline/solve.py:259`) and (b) the heat rates inside `mc_base`.
6. **P0:** `r0 = model.solve(mc=mc_base)` (`solve.py:292`) — `mc_base` IS the
   P0 objective, and the refined rows ARE P0 columns.
7. **P0 → P1 propagation:** `compute_monthly_markup(fleet, …, r0.dispatch, …)`
   (`solve.py:297`) turns P0 run lengths into the startup amortization;
   `mc_bid = mc_base + markup` (`:308`); the offer-surface family's additive
   adjustments apply after that (`:314–315`); and — armed in both keepers —
   `ercot_gas_commitment_bridge` detects its min-gen floors from the P0 run
   pattern and injects them at the same seam.

So the exposure is **double**: the flag changes the P0 **objective** (refined
heat rates in `mc_base`) and the P0 **column geometry** (row count and
capacities). Either alone breaks bit-identity; together they also move run
lengths, markup, and bridge floors — the measured channel of §4.

### 2.2 Inherent, not incidental — the mechanism-terms argument

The offer-surface family rides `mc_bid_adjust` because its members adjust
**bid conduct**: prices quoted above an unchanged physical cost model, which by
the P0/P1 architecture belong only in the clearing pass. R1 is not that. R1
changes the **cost model itself** — the fleet's physical representation, the
resolution at which the supply curve can express within-plant positions. Two
consequences, each independently fatal to a P1-only wiring:

* **The object is column structure.** The refinement exists because a 6-block
  ramp "CANNOT express a cliff" (the slicer's own docstring): price formation
  inside the top 0.24 % of the marginal resource's submitted curve needs the
  top 2.78 % of the model ramp to price separately from its body. Separate
  pricing requires separate LP columns. The `mc_bid_adjust` seam is an
  `(n_gen, T)` additive array over **existing** columns — it can reprice a
  block, never subdivide one. P1 cannot carry finer columns than P0, because
  there is ONE model and the P0→P1 seam is objective-only (warm-start
  preserving; `solve.py` module contract). Column geometry is therefore shared
  with P0 **by architecture**, and the architecture is itself load-bearing
  (rule 2 vectorized build, the warm-start economics of minutes-long solves).
* **P0's function requires the base cost model.** P0 is the base-cost pass
  that discovers run lengths under the model's best estimate of TRUE costs.
  R1's ladder IS that best estimate (structurally grounded, measured,
  zero-DOF). Holding P0 to the coarse costs while P1 bids the ladder is not a
  cleaner wiring — it is deliberately running commitment discovery on a cost
  model the build itself says is worse, to preserve a proof instrument. Under
  rule 1 `[R-STRUCT]` that trades structure for measurability, which is the
  trade the rule forbids in both directions.

One sharpening that strengthens "inherent": under the keepers' own smoothing
config (`mid = 0.35`, so the ramp is piecewise-linear and the top block at
`t ≥ 5/6` lies entirely in the upper AFFINE segment), the refined ladder is
**capacity-weighted-mean-preserving over the top block** — the block's total
cost at full dispatch is unchanged, and only the within-block marginal
structure differs. The 12.5 GW commitment shift of §4 was produced by *that
alone*. The P0 motion is not a side effect of sloppy cost accounting the
wiring could have avoided; it is the width-resolution itself acting on
commitment discovery — i.e. **the mechanism doing its one job, in the pass
whose job is to read the supply function**.

**Verdict: INHERENT.** ercot-188's precommit §3 and finding §6.3 said this by
construction ("a row-count change breaches that seam by construction"); Phase 0
confirms it survives the search for an alternative wiring (§3).

---

## 3. Charter Q2 — the candidate P1-only constructions, adjudicated

Four constructions were assessed. None restores the proof without either
changing the keeper's numbers or destroying what the proof is for.

* **B — unconditional refined geometry, coarse-cost P0, ladder via
  `mc_bid_adjust`.** The only construction that literally restores
  control-vs-arm P0 bit-identity while keeping the refinement expressible:
  always build 11 rows, give the top sub-slices the coarse block heat rate in
  `mc_base` (identical supply function armed and unarmed), apply the ladder as
  a P1-only additive component. **Rejected on three grounds.** (i) Its armed
  P0 is supply-function-equivalent to the ercot-188 CONTROL, not to the
  keeper — it strips the keeper's P0 of the ladder, reverting the measured
  12.5 GW commitment channel (§4): keeper numbers move. (ii) It changes the
  flag-OFF path too: the SP-1 invariant (unarmed fleet byte-identical to
  pre-edit HEAD) is destroyed for every ERCOT run, and the ×1.3 row cost
  (G-COST) is paid unconditionally. (iii) It manufactures LP degeneracy — n
  identical-cost columns where control had one — inside the field of view of
  the run-length detector and the bridge's P0-pattern scan, so even its
  "control" equals the historic coarse fleet only by argument (precommit P-4):
  the construction degrades the instrument it exists to restore.
* **C — bake R1 in (un-flag it).** Make the refined geometry+ladder the
  unconditional ERCOT CAMPD base representation and delete the field. The
  armed path is byte-identical (same code path, gate constant-True), so the
  keeper does not move; and the offer-surface FAMILY's invariant is restored
  going forward ("every flagged offer-surface mechanism is P1-only"), because
  no flag moves the fleet any more. **But it does not restore R1's proof — it
  abolishes R1's off-state**, which is acceptance formalized, and the owner
  rejected accept-and-document. Also: recorded keeper `run_config.json`s carry
  the field, and HEAD replayability of committed configs would need a
  compatibility shim. Available only as an owner re-ruling (§6 Door 3).
* **D — P0-conditioned hour-wise repricing of the coarse top block** (via the
  existing `p1_bid_adjust_prep` hook): keep 6 rows, read the block's P0
  cleared position each hour, bid the block at the ladder price of that
  position. P0 bit-identity restored — **rejected as not the mechanism**: the
  block's single price would be *chosen by a rule keyed to P0's position*
  rather than discovered by the LP clearing within the block (P1's position
  responds to the bid the rule set from P0's — an internally inconsistent
  feedback heuristic), and it prices the block's cheap bottom at the sliver's
  cost. That is a synthetic conditional adder imitating structure — the class
  of construction rules 1/13 reject — and it changes keeper numbers anyway
  (P1 position ≠ P0 position whenever it matters).
* **E — P1 solves a refined fleet, P0 the coarse one** (a row-count-changing
  `p1_fleet_prep`). Architecturally excluded: `mc_bid`, the markup, the bridge
  floors, the swcap clip and the results frame are all `(n_gen, T)`
  row-aligned to the P0 fleet; a row-count swap at the seam desyncs every one
  of them, forfeits the warm start, and makes P0 discover run lengths on a
  fleet P1 does not clear — a strictly worse instrument. It also changes
  keeper numbers identically to B (the keeper's P0 currently runs refined).

**Answer to Q2: NO.** There is no construction in which the refinement affects
the P1 bid only *and* the keeper's P0 stays what the keeper was calibrated
with. The two halves are the same mechanism (FINDING-ercot188 §6.2: "there is
no counterfactual in which the ladder moves and the commitment does not: they
are the same code change") — Phase 0's addition is that no rewiring creates
that counterfactual either, except as an instrument (§5).

---

## 4. Charter Q3 — the predicted cost in keeper results (the decisive question)

**Prediction pushed before this finding** as
`docs/PRECOMMIT-o7-p0-seam-restoration-2026-08-30.md` (P-1…P-4). Summary:
restoration-by-B moves the CALIBRATED keeper by **order +$1–3/MWh on the 2023
annual load-weighted price (center ≈ +$2.2/MWh)**, reverses a commitment-state
change measured at **73 of 132 committed rows / 12,474 MW**, moves the armed
bridge's floored unit-hours in all three years, and moves C3b/C3c/G-SHED
unpredictably.

**Evidence base — committed, no new solve.** ercot-188's mandatory P0-delta
probe (`scripts/probes/ercot188_p0_delta.py` →
`results/calibration/ercot188_p0_delta.json`, reported in
`FINDING-ercot188-cliff-offer-curve-2026-08-11.md` §6) measured, control vs
arm, 2023: P0 total energy conserved to 2.8e-05 TWh while **55.3 % of the
committed fleet changed commitment pattern** (−8 starts, +96 on-hours; ~0.011
TWh moved from the econ ramp into the committed band); bridge floored
unit-hours 12,375→12,309 (2023), 6,164→6,160 (2024), 13,326→13,287 (2025);
startup-markup sub-channel small (−$0.0020/MWh cap-weighted mean, max row
$0.845). §6.2's attribution arithmetic: the IQR priced the ladder channel at
**+$1.99/MWh** quantity-fixed, the whole solve delivered **−$0.21/MWh**, so
**≈ $2.2/MWh** sits in the confounded commitment/re-optimization channel —
the channel every seam-restoring construction strips out of the keeper.

**Why no measurement was run in Phase 0.** Measuring Construction B's cost
requires building Construction B — a `src/` mechanism change to the fleet
assembly of a CALIBRATED keeper's ISO — and solving it. That is Phase-1 work
under exactly the condition the charter says escalates instead. The precommit
is on record so that an owner-ordered measurement can surprise it; the 188-era
magnitudes are disclosed as measured at the 188-era recipe (the 236/234
recipes differ — swcap clip, EASTEX identity, cleared-share RT — so magnitudes
would differ; the exposure mechanism is identical code).

**Consequence:** restoration is not a refactor. **It is a mechanism change to
the first CALIBRATED ERCOT keeper in program history, and it ESCALATES to the
owner.** Per rule 1, no part of this verdict rests on whether the move would
improve or worsen the fit (the naive sign — model −7.3 % low, predicted move
positive — would *improve* C3a-2023, and that is exactly the wrong reason to
build it).

---

## 5. Charter Q4 — the cheaper partial: a decomposition harness that restores ATTRIBUTION

**The construction.** A probe harness (pattern: `ercot188_p0_delta.py`, which
already replays members through `run_energy_solve` with spies), adding one
decomposition leg to any future R1-family A/B:

* **Leg 2 ("de-laddered arm"):** replay the keeper recipe exactly, with one
  additive `(n_gen, T)` component merged into the composed `mc_bid_adjust`:
  `Δmc(g,t) = (hr_coarse(g) − hr_refined(g)) × (fuel_price + carbon·ef + …)(g,t)`
  on the top sub-slice rows only — i.e. the keeper's P1 clears the coarse
  top-block price on the refined geometry, while **P0 is byte-identical to the
  keeper's P0 by construction** (the adjustment enters at `solve.py:314`,
  strictly after `r0`). Prove it, don't assert it: content-addressed hashes on
  the P0 dispatch/objective artifacts of both legs.
* **What it buys:** keeper-vs-leg-2 is a **bit-identical-P0 seam measurement
  of the ladder's pricing channel** given the keeper's real commitment state —
  the counterfactual FINDING-ercot188 §6.2 said "does not exist" now exists as
  an instrument. Full-A/B minus leg-2 bounds the commitment channel plus
  interaction. Attribution — the practical benefit the forfeiture cost, and
  the thing the last two rejections in this lane turned on — is restored **by
  construction**, with zero mechanism change, zero keeper motion, zero new
  ScenarioConfig fields (no rule-26 duty (c); a probe is not a registrable
  tuning channel, per the D-2/188-probe precedent).
* **Limits, stated honestly.** (i) It does NOT restore O7's literal object:
  R1's own arm-vs-off comparison stays whole-solve forever — that is §2's
  inherent verdict, and no harness changes it. (ii) Leg 2 is an instrument,
  not a market state; its numbers are decomposition evidence, never a
  registrable run (it would be a synthetic-adder config under rule 13 if ever
  registered — the harness must live in `scripts/probes/`, default-off by
  being a probe). (iii) The two legs do not sum exactly to the whole-solve
  delta (LP nonlinearity); the residual is the measured interaction term, and
  reporting it at full magnitude is part of the harness contract. (iv) The
  de-laddering array must reproduce every heat-rate-linked term in `mc_base`
  (fuel, carbon, NOx; and compose correctly under the swcap clip, which binds
  `mc_base` BEFORE P0 and the assembled bid in P1) — a construction detail
  the Phase-1 precommit must fix ex ante, not a blocker.
* **Cost:** one probe script + one replayed solve per compared year (the
  keeper leg reuses committed sidecars where the comparison allows; a
  same-HEAD pair costs two replays). Minutes per year, ERCOT profile data,
  no registration, no dashboard entry, no matrix cell (nothing is being
  mechanism-tested; if the owner orders the harness built and exercised, the
  executing session stamps the evidence trail then).

**On the merits this partial beats the purist restoration:** it recovers the
attribution the program actually lost, at probe cost, without touching a
CALIBRATED keeper — where the purist restoration moves the keeper, degrades
the instrument (precommit P-4), and pays an unconditional row-count tax.

---

## 6. What the owner must decide

The 2026-08-26 ruling chartered a restoration and rejected accept-and-document.
Phase 0 finds the chartered object, taken literally, costs a CALIBRATED
keeper. Three doors:

* **Door 1 — purist restoration (Construction B), owner-approved keeper
  change.** Proceed to Phase 1 knowing the keeper's numbers move (precommit
  P-1…P-3); requires an explicit owner mandate to re-open ERCOT calibration on
  the restored construction, full-span per rule 16, LOYO per rule 22 — and it
  should carry §3's grounds (ii)–(iii) as known costs: the off-path
  byte-identity invariant and the manufactured degeneracy. **Not
  recommended.**
* **Door 2 — the decomposition harness (§5).** O7 closes as: *attribution
  restored by construction (hash-proven bit-identical-P0 leg); bit-identity of
  R1's own arm/off comparison recorded as INHERENTLY forfeit — a property of
  the mechanism, not of its wiring — per this finding §2.* Keeper untouched.
  **Recommended.** Phase-1 scope if ordered: probe script + its own
  precommit + the hash proof, after the governance lane lands (§7).
* **Door 3 — bake R1 in (§3-C).** Restores the family-level seam invariant
  forward (no flag moves the fleet), keeper byte-identical, but abolishes
  R1's off-state — acceptance formalized, so it contradicts the 2026-08-26
  ruling unless the owner re-rules. Compatible with Door 2 (harness first,
  bake-in later, in that order the A/B evidence survives).

A Phase-0 finding that escalates IS the charter's named complete deliverable;
Phase 1 is deliberately not forced.

---

## 7. Phase-1 hold and lane collisions

Per the charter's collision clause: `claude/ercot-governance-rulings-0826` is
concurrently restructuring the ERCOT keeper (two-config form) and owns the
ERCOT keeper shard, status part, calibration log, mechanism-matrix ERCOT shard
and registry files this cycle. This session touched **none of them** — the
deliverables are two new `docs/` files on this branch, and no `src/` file was
edited. Any Phase-1 work (any door) should start only after that lane lands,
against the keeper designation it produces; §4's predictions would need
re-basing if the designated recipe changes.

## 8. Governance notes

* **Rules engaged:** rule 1 (verdict independent of fit direction, §4); rule
  19 (no construction stacks a correction on the P0 exposure — B/C/D/E all
  RELOCATE, D rejected partly for becoming a second mechanism); rules 5/21/24
  (zero new tunables in any assessed construction; Door 2 adds no field);
  rule 25 (ERCOT-only throughout; the rule-25 gate at `assembly.py:832` is
  part of why the wiring is already contained); rule 22 (no solve of any
  year; the one prediction concerns training years only); rule 27 (all pushes
  are new small docs; exact on-disk bytes; blob-verified).
* **Matrix duties:** none fired — no mechanism proposed, tested, or added; no
  ScenarioConfig field touched. The `ercot_econ_curve_top_refine` cell stays
  as adjudicated at ercot-188; the session executing any owner-ordered door
  updates it then (and owns the O7 row closure text in the audit doc — left
  untouched here since `docs/audit/third-party-audit-2026-08.md` is the audit
  lane's record).
* **Citation drift noted:** charter cited `scenarios.py:9228`; at this HEAD
  the field is `:9238`. `data/offer_curves.py:272` and
  `data/fleet/assembly.py:128`/`:833` resolve to the same objects cited here
  (`:272` in-docstring, `:243` the def; `:128` in-docstring, `:106` the def;
  `:833` inside the `:832` gate expression).
* **Evidence chain:** `results/calibration/{ercot236_k33_clip,ercot234_eastex_identity}/run_config.json`;
  `docs/PRECOMMIT-ercot188-cliff-offer-curve-refinement-2026-08-11.md`
  §2.6/§3/Amendment 1;
  `results/calibration/FINDING-ercot188-cliff-offer-curve-2026-08-11.md`
  §5–§6.3, §9; `docs/audit/third-party-audit-2026-08.md` row O7;
  `src/market_sim/{config/scenarios.py,data/offer_curves.py,data/fleet/assembly.py,pipeline/solve.py,pipeline/year.py}`
  at `4ed7cd3`.
