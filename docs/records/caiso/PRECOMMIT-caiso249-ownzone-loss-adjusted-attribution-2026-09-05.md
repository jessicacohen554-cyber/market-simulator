# PRECOMMIT — caiso-249: resolve the 53 % STORAGE bucket. The caiso-247/248 price match compared units to OTHER zones' duals across a live loss surface; replace it with OWN-ZONE complementarity plus the measured delivery-factor ratio. ZERO LP, NOTHING ARMED. Pushed BEFORE any measurement of the object.

**Session caiso-249, 2026-09-05.** Branch
`claude/caiso-backcast-calibration-247-zxaba3` off `main` `c234d4da`. Keeper
**`2026-09-05-caiso-246-b1-spot`** unchanged, NOT-YET, C3a +3.9 / +12.3 /
+11.4 %. Holdout freeze ACTIVE; **2023–2025 only**. **NOTHING WILL BE ARMED**
— no field, no flag, no solve, no promotion, whatever the result.

Pushed to `origin` **before the estimator is coded and before any cell of the
object is computed.** Nothing in §2 was measured first.

---

## §0 — THE OBJECT, AND WHY IT IS NOW RANKED FIRST

caiso-248's corrected decomposition leaves the C3a gap here:

| | DOM_GAS | STORAGE | HUB | DOM_OTHER | UNRESOLVED |
|---|--:|--:|--:|--:|--:|
| 2024 ($3.781/MWh) | 47.1 % | **43.2 %** | 4.0 % | 2.6 % | 3.2 % |
| 2025 ($3.151/MWh) | 40.2 % | **53.3 %** | 3.6 % | 1.0 % | 1.9 % |

`STORAGE` is not a measurement. It is the **residual label**: assigned when no
unit price-matched and storage happened to be cycling. It is now the single
largest 2025 cell, so **the lane cannot quote any DOM_GAS number** until it is
resolved. caiso-248 §7 ranks it first.

### §0.1 — The diagnosed cause, from the code, not from the residual

The keeper runs `caiso_zonal_loss_surface` (caiso-164), which splits the
internal CAISO links into one-way loss pairs. `build_caiso_link_loss` states
the resulting price relation exactly: for an interior uncongested flow
`x → y`,

```
lambda_y = lambda_x x (1 + dev_y,m) / (1 + dev_x,m)
```

with `dev_z,m` the measured monthly delivery-factor deviation from
`CAISO_loss_surface.csv` (`load_zone_month_deviation`). CAISO's deviations run
about −3 to −4 % (LA_BASIN Jan −0.0342), so **two zones' duals differ by ~1–4 %
— 0.4–1.5 $/MWh at CAISO price levels — even with nothing congested.**

caiso-247's estimator matched every domestic unit against **every** CA zone's
dual inside a 0.05 $/MWh window. A unit in NP15 was therefore compared to
SDGE's dual, which the loss surface guarantees it will miss. The zone-hours
whose own marginal unit sits in another zone fell through to `STORAGE`. That
is a defect of the estimator, not a property of the market.

### §0.2 — What replaces it

**Own-zone complementarity is exact and needs no loss adjustment at all.** A
unit strictly between its bounds in zone `z` must satisfy `mc = lambda_z` —
same zone, same dual, no delivery factor between them. The delivery-factor
ratio is then used only for the genuinely separate question of **which zone's
marginal unit sets a zone that has none of its own.**

### §0.3 — Admissibility

Nothing enters the model. `CAISO_loss_surface.csv` is a committed measured
input the keeper **already dispatches on**; this probe reads it to interpret
the keeper's own duals. The actual hourly RT LMP is used only as the scoring
comparator it already is. No parameter is derived, swept or fitted.

### §0.4 — HARD STOPS

1. **No arm, no solve, no field, no flag, no promotion — whatever the result.**
2. **2023 / 2024 / 2025 only.** No out-of-training year is read.
3. **The frozen caiso-247 taxonomy's HUB definition is not reopened.** Its
   verdict (CR 1.026 / 0.642) survived caiso-248 bit-identical and is not
   re-litigated here; this session may only *refine which zone-hours carry the
   hub label through an unbound path*, and must report the HUB cell both ways.
4. If the repair does not materially shrink `STORAGE`, that is the result and
   it is published as a negative.

### §0.5 — THE HAZARD

Two, both declared now. **(a)** Every reclassification moves gap share OUT of
an unattributed bucket and INTO a named one, so the estimator will look like
it is "explaining more" by construction; the guard is §1.4's G-CONSERVE — the
total gap is fixed and only its labelling moves — plus registering in §2 the
*direction and size* of the move before seeing it. **(b)** This session
follows one in which I withdrew my own headline. The temptation is to produce
a replacement headline. **The registered outcome that nothing new is named
(P-6) is a full result and will be published as one.**

### §0.6 — DO-NOT-REDO acknowledged

caiso-248 §8 (never rebuild a fleet with `run_year_kwargs` alone — splat
`derived_run_year_inputs`; never test injected must-run by flatness in a
non-leap month map; biomass never sets the CAISO price; never quote caiso-247
§4.4's 3.4 %), caiso-247 §8 (the hub-basis reading is CLOSED for 2024/2025;
caiso-244 §3.6's 18–23 % HOUR share is never a weight or gap share; never
quote the weight-basis term as a reduction of C3a), caiso-246 §8, caiso-245
§7, caiso-244 §7, caiso-243 §10, caiso-242 §9, caiso-241 §10, caiso-240 §7,
caiso-239 §8, caiso-230 §9 — read, none re-opened.

---

## §1 — THE ESTIMATOR, NAMED, AND ITS GATES

Built by extending `scripts/probes/_caiso247_residual_regime_anatomy.py`
(caiso-248 §9's repaired version, which splats `derived_run_year_inputs` so
the fleet is the fleet the solve dispatched). The gap decomposition, weights
and comparator are **unchanged** — caiso-131 §2 / caiso-140 §A common-weight
convention over zone-hours, rubric `rt_lw` weights on both sides. Only the
**labelling** changes.

### §1.1 — The three-pass label, FROZEN NOW

For each zone-hour `(z,t)`, in this order:

1. **OWN-ZONE.** A domestic unit **located in `z`**, available, with
   `|mc_g,t − lambda_z,t| <= TOL`. Label `DOM_GAS` if its family is a gas group,
   else `DOM_OTHER`. **Exact complementarity; no loss factor.**
2. **DF-IMPORT.** No own-zone match, but some zone `z'` HAS one and
   `|lambda_z,t − lambda_z',t x (1 + dev_z,m)/(1 + dev_z',m)| <= TOL` — the
   `build_caiso_link_loss` relation, i.e. an interior uncongested path from
   `z'` to `z`. Take the family of `z'`'s match; where several `z'` qualify,
   take the nearest in that residual, and record the multiplicity.
3. **HUB.** Unchanged from caiso-247 §1.3 (import-row complementarity at the
   WECC node with the corridor link unbound), except the landing-zone reach
   test also gets the delivery-factor ratio. `HUB_FITTED` / `HUB_MEASURED`
   split unchanged.
4. Then `STORAGE` (storage cycling), `SURPLUS` (`lambda <= 0.01` or dump),
   `UNRESOLVED`.

`TOL = 0.05 $/MWh`, the caiso-244 value, **reported not tuned**. `dev_z,m` from
`load_zone_month_deviation("CAISO", year)`, expanded on the model's non-leap
8760 month map — **the same map `build_caiso_link_loss` expands on**, so no
leap-calendar trap (caiso-248 §4).

**Ordering note, declared:** HUB now runs AFTER the domestic passes, the
reverse of caiso-247. That is deliberate — own-zone complementarity is the
stronger evidence — and the G-ORDER variant (HUB first, as caiso-247 had it)
is run and reported so the HUB cell is comparable to the published one.

### §1.2 — Gates

* **G-FLEET (NEW — the gate caiso-248 §5.2 says was missing).** The rebuilt
  fleet's class composition must reconcile with the committed
  `class_hourly` sidecar: every klass in the sidecar that is NOT an injected
  must-run class must have LP units in the rebuild, and every LP-unit family
  must appear in the sidecar. **FAIL → stop; the fleet is not the solve's.**
* **G-CONSERVE.** The regime cells still sum to `gap_hourly` exactly (max
  abs deviation < 1e-9 $/MWh), and `gap_hourly` is **unchanged from caiso-248's
  1.3071 / 3.7812 / 3.1507**. A labelling change cannot move the total.
* **G-BENCH / G-RECON / G-GAP** — unchanged, must still pass.
* **G-ORDER.** The HUB cell under the HUB-first variant reproduces caiso-247's
  published CR (1.026 / 0.642) to ±0.01. **FAIL → the two sessions are not
  comparable and the HUB cell is reported as changed, not confirmed.**
* **G-DF.** The DF-IMPORT pass must be *doing the work it claims*: report the
  share of DF-IMPORT zone-hours in which the implied ratio is within TOL while
  the RAW difference `|lambda_z − lambda_z'|` is NOT. If that share is small,
  the loss surface was not the barrier and §0.1's diagnosis is wrong — say so.

### §1.3 — Sensitivity, reported not frozen

The whole decomposition is repeated at `TOL_SENS = 0.75` (caiso-202 §C's own
rung tolerance), as in caiso-247. Primary numbers are the frozen 0.05 ones.

---

## §2 — PREDICTIONS, REGISTERED BEFORE ANY MEASUREMENT

Registered **wide** — caiso-247's windows were 3–5× wrong (§4.1 there) and
caiso-248 withdrew a headline. Every one is falsifiable; none is a gate.

| # | prediction | falsifier / meaning |
|---|---|---|
| **P-1** | **G-FLEET passes** in all three years | fail → stop, the fleet is still not the solve's |
| **P-2** | **G-CONSERVE holds** and `gap_hourly` is EXACTLY 1.3071 / 3.7812 / 3.1507 | any move → the change is not purely a relabelling and the estimator is wrong |
| **P-3** | **G-ORDER holds**: HUB-first CR reproduces 1.026 / 0.642 to ±0.01 | fail → the HUB cell is reported as changed |
| **P-4** | **STORAGE falls to 5–25 % of the 2025 gap** (from 53.3 %) and 5–25 % in 2024 (from 43.2 %) | **above 25 %** → the loss surface was NOT the main barrier and the residual is genuinely unattributed — a much worse position, and the honest one; **below 5 %** → the DF-IMPORT pass is over-claiming and G-DF must justify it |
| **P-5** | **DOM_GAS rises to 55–80 % of the 2025 gap** (from 40.2 %) and 60–85 % in 2024 (from 47.1 %) | outside → the reclassified hours are not gas-marginal, and whatever they are is the new object |
| **P-6** | **No NEW named object appears**: no regime outside {DOM_GAS, HUB, STORAGE} exceeds 10 % of the gap in either failing year. *Uncomfortable — it predicts this session produces no headline* | a regime above 10 % → name it, and it is the next object |
| **P-7** | **G-DF is material**: ≥ 60 % of DF-IMPORT zone-hours have the raw `|lambda_z − lambda_z'|` OUTSIDE TOL while the DF-corrected residual is inside | below 60 % → §0.1's diagnosis is wrong; the barrier was congestion or something else, and that is the finding |
| **P-8** | **The CC-hot / CT-cold split survives**: CC_REGULAR and CC_CHP keep positive mean residuals and CT_PEAKER stays negative in 2024 and 2025 | a sign flip → caiso-247 §4.7 is withdrawn too |
| **P-9** | At `TOL_SENS = 0.75` the corrected DOM_GAS share moves by **less than 15 points** from its 0.05 value (i.e. the repair makes the answer tolerance-INSENSITIVE, which is the point of it) | more → the estimator is still tolerance-driven and no DOM_GAS number may be quoted |
| **P-10** | **HUB stays ≤ 8 % of the gap** in both failing years under the frozen order | above → the domestic-first ordering materially changed the hub attribution and caiso-247's acquittal needs re-examination |

---

## §3 — STOP RULE

* **G-FLEET fails** → stop, claim nothing, report the failure.
* **G-CONSERVE fails** → stop; a relabelling that moves the total is a bug.
* **P-7 falsified (G-DF immaterial)** → the DF-IMPORT pass is reported as
  ineffective, the STORAGE bucket stays unexplained, and the session publishes
  that negative rather than reaching for another labelling rule.
* In every case the finding is published, the matrix evidence is appended, and
  **nothing is armed.** A negative result is the deliverable.

---

## §4 — DELIVERABLES

This PRECOMMIT; the extended probe
(`scripts/probes/_caiso249_ownzone_attribution.py`) + its artifact; a finding
scoring all ten predictions against interest; the calibration-log entry; and
an **evidence-only** append to the CAISO matrix shard (no cell verdict moves —
no mechanism is tested). No run registered (zero solves). Keeper unchanged.
C3a is not moved and no direction is claimed.
