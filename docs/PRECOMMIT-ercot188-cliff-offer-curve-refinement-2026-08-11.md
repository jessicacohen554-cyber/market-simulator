# PRECOMMIT — ercot-188: the (c2) cliff-resolving offer-curve refinement, BUILT as a structural-fidelity purchase

**Session ercot-188, 2026-08-11, opened at HEAD `d542a28` (origin/main).
ERCOT ONLY (rule 25).** Pushed **BEFORE any measurement, any derive, any build,
any solve**. Nothing below is renegotiated after a number is seen.

**Authorization: OWNER DECISION — option (B) BUILD ANYWAY of
`docs/MEMO-ercot184-cliff-resolution-costing-2026-08-09.md` §8, taken as a
STRUCTURAL-FIDELITY purchase under rule 1 `[R-STRUCT]`.**

> **The memo's own recommendation was (A) CLOSE THE LANE, and that
> recommendation is NOT rewritten, softened, or re-argued here.** The memo
> measured (c2)'s reach at **+$1.99/MWh against a +$14.44/MWh bar (13.8 %)**,
> failing its own pre-registered **G-REACH bar of +$5.00 by 2.5×**, and
> recommended against paying 1.4–5.6× LP columns and the P0 bit-identity proof
> for it. The owner weighed that costing and elected (B) anyway. **This lane is
> the owner's purchase of structural fidelity over the memo's mechanical
> recommendation, recorded as such** — the same posture ercot-185 was promoted
> under, where the mechanical verdict stood unrewritten and the promotion rested
> openly on the owner's standing structural standard.

---

## 0. THE RECORD THIS BUILDS AGAINST

**Precondition, verified at session open: ercot-186 HAS LANDED**
(PR **#3847**, merge `b09aa35`; commits `2e8f879` precommit → `ed3a860` repair +
seam proof → `8be326b` FINDING/matrix/log → `6865f79`). **ercot-187 has also
landed** (PR **#3848**, merge `5c4dc88`; `9568611` → `402a2c2` → `8ac5b8b`).
Neither moved the keeper:

* **ercot-186** confirmed the rule-18 grain defect, merged its repair
  **default-off and inert at default**, and then **honoured its own
  pre-registered STOP (SP-1 fired) — no A/B solved, nothing registered.** Its
  new field `ercot_faststart_pool_plant_physics` (default `False`) is in both
  cache-key registries and stays at default throughout this lane.
* **ercot-187** was hygiene: it fixed a leap-day row-alignment defect in
  `derive_ercot_faststart_pool.py` (**fail-closed; no committed artifact ever
  went through the buggy path, and none was regenerated**) and regenerated
  `tests/golden/fleet_arrays_ercot_2023.json`, attributing 100 % of the drift to
  the owner-adopted `6a8f285c` CAMPD guard correction of **2026-07-26** — i.e.
  **before** the keeper was solved. **ERCOT-185 was exonerated by direct
  measurement.** No run artifact and no offer/pool ladder moved.

**THE KEEPER THIS LANE BUILDS AGAINST — named per the charter:**

> **`2026-08-09-ercot185-shaped-partial`**, bundle
> `results/calibration/ercot185_shapedarm_B` (`meta.timestamp`
> 2026-08-09T21:15:20, `years [2023, 2024, 2025]`,
> `curve_smoothing {"offer_curve_smoothing_mid": 0.35}`, so
> `offer_curve_smoothing_n` sits at its ScenarioConfig default **6**).
>
> Determination **NOT-YET**, fail set **{C3a-2023, C3b-2023}** (C3b-2024 CLOSED
> at ercot-185, 0.205 → 0.160). Per-year **C3a −32.5 / +1.4 / −7.9 %**;
> **C3b 0.602 / 0.160 / 0.101**; model tail > $200 **61 / 23 / 3** vs actual
> **181 / 53 / 31**; **shed 4 / 2 / 0**.

**ERCOT holds NO `complete` and NO `final` marker.** Every solve is
`--year 2023 2024 2025`, ONE invocation per member, years **sequential**
(rules 12/16). No year outside {2023, 2024, 2025} is solved, scored, read or
registered.

**BASELINE DISCIPLINE (inherited, and it binds every gate below).** The ERCOT
keeper is known **not to reproduce byte-for-byte at current main** (ercot-173
§5, carried through ercot-174 / ercot-185 / ercot-186's attestation generator).
**Every gate in §4 is therefore adjudicated CONTROL-vs-ARM on the same-HEAD
pair, never against the committed keeper's ledgered numbers.** The keeper's
ledgered values above are the *nominal* baseline; the control's own values are
the *operative* one. **Both are reported, and any control-vs-keeper drift is
stated at full magnitude** rather than absorbed.

---

## 1. WHAT THIS LANE IS, AND WHAT IT IS NOT

### 1.1 It is NOT chartered to close C3a-2023, and a result near +$1.99/MWh is the EXPECTED outcome

The memo measured the ceiling **across the whole family of MW-preserving
re-slicings** — not one parameterization — at **+$1.99/MWh**, because the LP
clears at ladder position ~0.70 and re-slicing moves that by only **+0.055**
(ceiling **0.833** against reality's **0.9976**). **That measurement is not
re-opened and not re-litigated by this lane.**

> **A result near +$1.99/MWh IS THE EXPECTED OUTCOME AND IS NOT A FAILURE OF
> THIS LANE.** It will not be reported as a disappointment, and the memo's
> ceiling will not be re-derived, re-argued, or quietly widened to make the
> build look better-justified.

### 1.2 It IS a structural-fidelity purchase, on the item-23 precedent

Today the model's supply-curve top is a **6-block equal-width approximation that
cannot express a cliff**: the finest within-plant position it can quote is 1/6 of
the econ ramp, and only **33 econ rows** in the whole 2023 fleet reach the
measured ladders' top decile (memo §4.3). After this build it can express one —
**382 rows above `rel` 0.9, reaching `rel` 0.9904 and 145.1× delivered gas** at
R1's own measured geometry. That is the purchase. Item 23
(`ercot_offer_surface_position_tail`, FINDING-ercot181 item 23) is the governing
precedent: a structurally-right mechanism **promoted on fidelity with an honest
measured outcome of INERT-ON-THE-OBJECT (+$0.0004/MWh)**.

### 1.3 The one thing that would falsify the build itself

If the solve returns a reach **materially above** the memo's ceiling, **that is
not a win to bank** — it is evidence the build does not match what was costed.
Pre-registered band and stop rule in §5.

---

## 2. THE BUILD — SCHEME R1, FIXED HERE, EX ANTE

### 2.1 The object

`src/market_sim/data/offer_curves.py::_econ_curve_steps` slices each plant's
economic ramp into `offer_curve_smoothing_n = 6` **equal-width MW blocks**
(`slice_cap = curve_cap / n`), each priced at its own **midpoint**
`t = (k + 0.5)/n` on the ramp's position axis. The keeper also carries
`offer_curve_smoothing_mid = 0.35`, so the ramp's **PRICE** axis already rises
1.857× faster in its top half. **This lane refines the WIDTH axis only. The
price-axis shape function `f(t)` is untouched.**

### 2.2 R1, stated as an exact construction

**The top 1/6 of the econ ramp split six ways; lower blocks unchanged; total
curve MW preserved.** With `n = offer_curve_smoothing_n`:

| | breakpoints on the ramp's position axis | slices | width each | midpoint |
|---|---|---:|---|---|
| **body** | `0, 1/n, …, (n−1)/n` | `n − 1` | `1/n` | `(k + 0.5)/n`, `k = 0…n−2` |
| **top** | `(n−1)/n + j/n²`, `j = 0…n` | `n` | `1/n²` | `(n−1)/n + (j + 0.5)/n²` |

Total slices `2n − 1` = **11** at `n = 6`. Body total `(n−1)/n = 5/6`; top total
`n · 1/n² = 1/6`; **sum exactly 1**. The body's midpoints `(k + 0.5)/n` and caps
`curve_cap/n` are **the coarse form's own first `n − 1` slices, expression for
expression** — so the body is byte-identical by construction, not by
verification, and the entire delta is confined to the top block. Suffixes stay
`econc{k:02d}`, `k = 0…10`, ascending in price.

This is **exactly** `scheme_top_refined(6, 6)` as the costing probe measured it
(`scripts/probes/ercot184_cliff_resolution_costing.py:287`), with the probe's
`t_new = 0.5·(xb[:-1] + xb[1:])` midpoint rule. **Row count 1,780 → 2,500
(×1.39 LP columns), predicted by memo §3.2.**

### 2.3 Why R1 and no other scheme, and why no sweep

R1 is chosen because the memo measured it as **BOTH the cheapest and the
highest-reach** scheme. R2 (uniform 60) reaches **less** at **3.8× more** cost;
R3 (geometric top 24) is **~16 GB — over this box's budget**; and reach
**SATURATES THEN DECLINES** with slice count (11 → +$1.99, 65 → +$1.66), so
"more slices" is already measured and is worse.

> **NO SWEEP. The slice count and the split point are NOT swept, tuned, or
> varied. If R1 proves infeasible, this lane STOPS and reports — it does not
> substitute a scheme.**

### 2.4 RULE 23 `[R-DOF]` — THE CRUX OF THIS LANE

A non-uniform slicing scheme **has a shape, and a shape is a degree of freedom
unless it is pinned structurally.** R1 is pinned so that it introduces **NO NEW
NUMERIC PARAMETER AT ALL**:

* **The split point is not a number I chose.** It is `1 − 1/n`, **the boundary
  the ramp is already sliced at** — the top coarse block's own lower edge, under
  the already-registered, already-identified `offer_curve_smoothing_n`.
* **The sub-slice count is not a number I chose.** It is `n`, **the same
  registered value**: the scheme is "apply the existing slicing rule once more
  to the one block that reaches the cliff."
* Therefore `n_free` (the DOF ledger's free-parameter count) **does not grow**,
  and the keeper's DOF ledger is carried **verbatim** — which is itself the
  G-DOF evidence, the ercot-186 attestation-generator pattern.

**The structural justification, from the MEASURED object and NEVER from the
residual** (both facts are pre-existing measurements in memo §4, taken before
this lane opened, and neither is a fit to anything):

1. **The top coarse block is where the model's own marginal row most often
   sits.** Memo §4.2: among the 33 econ-marginal object hours the marginal slice
   is `k = 5` — the top block — in **14**, more than any other slice.
2. **The top coarse block is the ONLY block that reaches the region where the
   measured ladder's truncation and reality's cliff both live.** Memo §4.3: the
   econ ramp spans a median **61.8 %** of its plant's stack, so its top slice
   reaches within-plant share **0.9625** → ladder `rel` **0.9427**; every lower
   block sits below `rel` 0.9 by construction and **cannot carry a cliff at
   all**. Reality's marginal price forms at `q_act` p50 **0.9976**.

> **If at any point a split is chosen because it scored better, that is a fitted
> parameter, the lane has FAILED rule 23, and this document commits me to saying
> so in those words.**

### 2.5 The gate — SCOPE HAZARD, and the mandatory containment

**`_econ_curve_steps` lives in `offer_curves.py` and is called from
`fleet/assembly.py` on the ISO-AGNOSTIC assembly path. There is no ISO gate
anywhere in it, and ALL SIX KEEPERS SHARE `n = 6`** (memo §6). An ungated change
**silently re-slices every ISO's fleet**. Containment, all of it mandatory:

* **ONE new `ScenarioConfig` field: `ercot_econ_curve_top_refine: bool = False`.**
  Default **OFF**, **ERCOT-gated** at the call site (`config.iso == "ERCOT"`),
  so the field cannot fire outside ERCOT even if set.
* **Cache-key registered dropped-at-default in BOTH registries
  (`_CACHE_KEY_OPTIONAL_FIELDS` and the default-source-text map) IN THE SAME
  COMMIT AS THE FIELD** — the nyiso-119 discipline. **The pinned default key
  must not move**; the armed key must be distinct.
* **Matrix row in the SAME PR as the field** (rule 28(c)), plus the cell verdict
  in this session (rule 28(b)).
* **The committed-band call site is NOT armed.** `_econ_curve_steps` is *also*
  the committed-band slicer when `committed_ramp_spread > 0` (memo §6 item 3 —
  the dormant coupling). All six keepers run `0.0`, but the refinement is passed
  **`False` explicitly at that call site**, so an ISO that later arms
  `committed_ramp_spread` can never silently inherit it.
* The ≥ 99-slice `_coal_tranche_rank` ceiling (memo §3.3 item 1) is **not
  approached**: `2n − 1 = 11` → ranks 2.00…2.10, well below `econhi`'s 3.0.

### 2.6 SEAM PROOF — required, and its assertions fixed now

Written to `results/calibration/ercot188_topfine_seamproof.json`, run **before**
any solve:

* **SP-1 (gate-off inertness, ERCOT).** With the field at default, ERCOT's
  composed fleet — every tranche row's `(suffix, cap, heat_rate, vom_mult,
  min_run, min_down, startup)` — is **BYTE-IDENTICAL** to the same build at
  pre-edit HEAD. *Falsifier: any row differs.*
* **SP-2 (cross-ISO inertness, gate ON).** With the field **armed**, **every
  non-ERCOT ISO's composed fleet is BYTE-IDENTICAL to control.** *Falsifier: any
  row of any of the five other ISOs differs.* **This is the charter's mandatory
  seam proof and a STOP-THE-LINE assertion.**
* **SP-3 (MW preservation).** Per plant-group and fleet-wide,
  `|Σ caps_arm − Σ caps_control| ≤ 1e-9 × Σ caps_control`. The **exact measured
  max deviation is reported in the FINDING at full magnitude**, not asserted
  away.
* **SP-4 (body byte-identity).** Every plant's first `n − 1` econ slices are
  byte-identical in **cap AND heat rate** between control and arm; the delta is
  confined to the top block's `n` sub-slices. *Falsifier: any body row moves.*
* **SP-5 (row census).** `econc` rows per plant-group 6 → 11; total fleet rows
  and LP columns reported against the memo's ×1.39.
* **SP-6 (committed band untouched).** The committed call site receives `False`;
  with `committed_ramp_spread = 0` it is unreached, asserted both ways.
* **SP-7 (cache key).** The pinned default key is **verified unmoved**; the
  armed key is distinct.

**Any SP falsifier ⇒ STOP, report, register nothing.** (The ercot-186 precedent:
a pre-registered stop that fires is honoured, and an unsolved lane is a
deliberate outcome, not a skipped registration.)

---

## 3. THE P0 SEAM — a known, accepted, permanently-recorded cost

**This is not a discovered problem. It is the cost the memo priced and the owner
accepted, and it is recorded here so it is never papered over.**

`_econ_curve_steps` writes heat rates into the **base fleet**, i.e. into
`mc_base`, which **is the P0 objective**. Every ERCOT offer-surface mechanism
since ERCOT-86 is applied at the `mc_bid_adjust` seam so P0 stays bit-identical
and each arm can be *proved* not to disturb commitment. **A row-count change
breaches that seam by construction.** Consequences, all accepted in advance:

1. **The offer-surface family's P1-only seam is BREACHED and its bit-identity
   proof is FORFEITED.** The ercot-181 seam proof's byte-identity assertions
   (SP-α1/α2/α3/α5) **have no analogue here**. Every control-vs-arm difference is
   confounded with commitment-side motion, so **the mechanism cannot be isolated
   by proof, only by argument** — in a lane whose last two rejections turned
   entirely on decomposing a headline number.
2. **~16.5 GW of committed gas is repriced through the commitment channel**
   (122 `committed` rows: CC_REGULAR 9,238 MW, ST_GAS 3,915, CT_PEAKER 3,392),
   because P0's dispatch feeds `compute_monthly_markup(...)`, which sets the P1
   startup amortization.

**MANDATORY MEASUREMENT AND REPORTING (not optional, and a FINDING section of
its own):** the P0 delta is measured **explicitly** — P0 objective, P0 total
generation, P0 run-length distribution, and the resulting P1 startup-markup
delta on those 122 committed rows — and the FINDING states **what moved and why
it is the INTENDED consequence of re-slicing rather than an incidental one.**

> **The forfeited bit-identity proof is carried as a NAMED, PERMANENT LIMITATION
> in both the FINDING and the keeper note.** It is not time-limited and it does
> not expire when a later gate passes.

---

## 4. KILL GATES — pre-registered verbatim, NEVER renegotiated after the solve

Both members are full-span `--year 2023 2024 2025` in ONE bundle each, and
**BOTH runs are registered whatever the outcome** (rules 15/16). Baselines are
the **control's own same-HEAD values** (§0); the keeper's ledgered values are
shown for reference.

* **G-SHED (PRIMARY).** **No year's shed count may rise above control.**
  Reference baseline **4 / 2 / 0**. The ercot-48/49 manufactured-shortage
  signature has killed this object **twice**. The memo aimed G-SHED at R1 and it
  **missed cleanly** — 100 % genuine offer formation, **zero** shed-exposed
  hours in every hour of 2023 (memo §4.6). **So a shed rise here means THE BUILD
  DIVERGES FROM WHAT WAS COSTED, and it is a REJECT.**
* **G-OWNER.** **C3a-2024 keeps PASS and C3b-2024 stays ≤ 0.20** — this protects
  a criterion-year ercot-185 has just won. **C3a-2025 not beyond −9.1 %.**
* **G-C3c.** The ledgered tail counts **61 / 23 / 3** (vs actual 181 / 53 / 31)
  must not degrade.
* **G-COAL148.** Coal dispatch above the measured product ceiling rises by
  **≤ +0.5 TWh in ANY year** (instrument: `scripts/probes/ercot185_coal148.py`).
* **G-SPUR.** The C3c spurious mid-band tail-hour count must not increase in any
  year.
* **G-DOF.** **Zero new fitted scalars; `n_residual` does not grow.**
* **G-COST.** Measured **peak RSS** and **column count** reported against the
  memo §3.2 estimate of **×1.39** (1,780 → 2,500 rows). **If it exceeds the box,
  STOP — do NOT drop years** (rule 16).
* **Rule-22 LOYO** across 2023–2025 **before any promotion.**

> **FAILING A GATE = REJECTED-AS-ARMED, and the run is REGISTERED ANYWAY**
> (rules 15/16), with the verdict reported at full magnitude.
>
> **Promotion on structural fidelity over a rejected mechanical verdict is the
> OWNER'S standard to apply and is recorded as the owner's — it is not a
> re-score, and it is NOT mine to assume.** This session does not promote on its
> own authority; it reports the verdict and the structural case and leaves the
> promotion to the owner.

---

## 5. PREDICTIONS AND THE RECONCILIATION STOP — fixed before measurement

* **P-1 (expected reach).** The arm's C3a-2023 annual load-weighted price rises
  by **≈ +$1.99/MWh**, i.e. C3a-2023 moves from ≈ −32.5 % to ≈ **−29 %**, still
  far outside the ±10 % band. **This is the expected, chartered outcome.**
* **P-2 (determination).** ERCOT's determination stays **NOT-YET
  {C3a-2023, C3b-2023}**. No determination change is predicted or sought.
* **P-3 (clearing position).** The refined slices become marginal in a
  meaningful share of object hours **and still read ladder position ≤ ~0.83** —
  memo §4.4's central finding, reproduced by a real LP rather than a merit-order
  mirror. *Falsifier: any object hour clearing at `rel` > 0.9.* A falsification
  here would be a genuine surprise and is reported as one.
* **P-4 (shed).** Zero new shed hours in any year (memo §4.6 measured zero
  shed-exposed hours in all of 2023). *Falsifier: any rise ⇒ G-SHED REJECT.*

**THE RECONCILIATION STOP, pre-registered with its band.** The arm's measured
annual load-weighted price delta for 2023 must land in
**[−$1.00/MWh, +$4.00/MWh]**.

* The **+$4.00** ceiling is ~2× the costed reach and sits **below the +$5.00
  G-REACH bar the memo already adjudicated FAIL** — so any result above it would
  be within reach of overturning the memo's own verdict, which is precisely the
  case where banking the number would be wrong.
* **Outside the band ⇒ STOP. Reconcile against memo §4 BEFORE registering
  anything**, by decomposing the delta into (i) the **ladder/offer-formation**
  channel the memo measured at fixed quantity and (ii) the **P0/commitment**
  channel the memo explicitly did **not** measure (§3.3) and named as the real
  cost. A divergence attributable to (ii) is an **expected source of difference,
  not a refutation of the memo** — but it must be *shown*, by argument and
  decomposition, since §3 has already forfeited the ability to prove it. Only
  after that reconciliation is written does anything get registered.

---

## 6. EXECUTION

1. **Build** the field + gate + R1 construction; run the seam proof (§2.6).
   `offer_curves.py` (1,099 lines) and `fleet/assembly.py` (1,734 lines) are
   **≥ 300-line core files: rule 27 applies — edited LOCALLY with the Edit tool,
   pushed as exact on-disk bytes, and blob-verified against the REMOTE after
   every such push, before the next commit.**
2. **ONE A/B pair** via `scripts/replay_keeper.py` on
   `results/calibration/ercot185_shapedarm_B`:
   * **control** → `results/calibration/ercot188_topfine_ctl_A` (gate at
     default),
   * **arm** → `results/calibration/ercot188_topfine_arm_B`
     (`--set ercot_econ_curve_top_refine=true`).
   **STRICTLY SEQUENTIAL** — ~6.6 GB RSS and ~20 min/year each *before* this
   lane's ×1.39; two concurrent ERCOT per-plant solves OOM a 15 GB box.
3. `legitimacy_diagnostics` + attestation on **both** bundles **before**
   scoring; then `calibration_verdict.py`.
4. **Register BOTH runs, all three years, whatever the outcome**, on the backcast
   dashboard (rules 15/16), then FINDING, matrix cell + citation **in this
   session** (rule 28(b)), and the calibration-log entry recording that this is
   **owner option (B) over the memo's recommended (A)**.

**Retention (top-15 per ISO).** ERCOT currently holds exactly **15** registered
runs. Adding 2 evicts the **2 oldest by (date, id)**:
**`2026-08-04-run162a-storage-rt`** and **`2026-08-04-run162b-storage-rt`** — a
matched A/B pair, so the eviction removes a complete pair rather than orphaning
one half. Stated here in advance, as the charter requires.

---

## 7. DO-NOT-REDO (rule 28(a)) — fences confirmed CLOSED before pre-registration

None of these is re-opened by this lane, and none is re-tested:

* **No offer-side C3a-2023 LEVEL lever** — matrix items 21–23 exhausted.
* **ORDC / RTORPA / reserve LEVEL** — CLOSED on measurement (ercot-177 §3).
* **Quantity and capability faces** — CLOSED (ercot-177 §6, ercot-181 §7 I-3).
* **Outcome pins** — rule-13 `[R-MEASURED]` forbidden.
* **(c1) sub-hourly** — REFUSED on scale; not revisited.
* **The West/Panhandle topology split** — CLOSED
  (`DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§7–10).
* **The memo's own +$1.99 ceiling measurement** — **NOT re-opened, NOT
  re-litigated** (§1.1).

This lane's cell is **new**: no ERCOT cell has adjudicated an offer-curve
*resolution* mechanism. Items 21–23 worked the conditioning-grain (hour axis)
and the position axis at **level**; this is the position axis at **width**.

---

## 8. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — the purchase is structural fidelity; the memo's
  mechanical recommendation (A) is recorded as **overridden by the owner**, not
  rewritten. No mechanism is stretched to reach a band.
* **Rule 12 / 16** — one invocation per member, all three years, sequential.
* **Rule 13 `[R-MEASURED]`** — no measured outcome enters any mechanism; R1's
  shape is pinned to the registered `offer_curve_smoothing_n`, not to data.
* **Rules 15 / 16** — both members registered, all three years, whatever the
  outcome; hourly sidecars committed for a keeper.
* **Rule 22 `[R-HOLDOUT]`** — ERCOT holds no `complete`/`final` marker; every
  year is inside {2023, 2024, 2025}; LOYO before any promotion.
* **Rule 23 `[R-DOF]`** — **zero new scalars** (§2.4); DOF ledger carried
  verbatim.
* **Rule 24 `[R-REGISTRY]`** — one `ScenarioConfig` field, both cache-key
  registries, same commit; the armed state appears in the run's config record.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT-gated; SP-2 proves the five other ISOs are
  byte-identical with the gate ON. No other ISO's files, bundle, keeper shard or
  matrix column is touched.
* **Rule 27 `[R-PUSH]`** — both edited files are ≥ 300 lines: local Edit only,
  exact on-disk bytes pushed, **blob-verified against the remote after every
  such push**.
* **Rule 28 `[R-MECH-MATRIX]`** — matrix row in the same PR as the field (c);
  cell verdict + citation in this session (b); DO-NOT-REDO checked before
  pre-registration (a) — §7.
* **GitHub Actions** — nothing offloaded; every build, seam proof, solve, score
  and registration runs in-session.
* **Keeper** — `2026-08-09-ercot185-shaped-partial` is **not promoted, demoted,
  re-keyed or edited by this session on its own authority** (§4).

**Next shorthand: ercot-189.**
