# FINDING — ercot-188: the (c2) cliff-resolving offer-curve refinement is BUILT, SEAM-PROVEN and SOLVED — a structural-fidelity purchase the owner chose over the memo's own recommendation to close

**Session ercot-188, 2026-08-11, opened at HEAD `d542a28`. ERCOT only (rule
25).** Pre-registration:
`docs/PRECOMMIT-ercot188-cliff-offer-curve-refinement-2026-08-11.md`, pushed at
`b73e383` **BEFORE** any measurement, derive, build or solve, plus its
**pre-solve Amendment 1** (the minimum-tranche feasibility guard, §4 below).

**Authorization: OWNER DECISION — option (B) BUILD ANYWAY** on the
`docs/MEMO-ercot184-cliff-resolution-costing-2026-08-09.md` §8 card, taken as a
**structural-fidelity purchase under rule 1 `[R-STRUCT]`**.

> ### The memo's own recommendation was (A) CLOSE THE LANE, and it is NOT rewritten
>
> ercot-184 measured (c2)'s reach **across the entire family of MW-preserving
> re-slicings** at **+$1.99/MWh against a +$14.44/MWh bar (13.8 %)**, failing its
> own pre-registered **G-REACH bar of +$5.00 by 2.5×**, and recommended against
> paying 1.4–5.6× LP columns and the P0 bit-identity proof for it. The owner
> weighed that costing and elected (B). **This lane is the owner's purchase of
> structural fidelity over the memo's mechanical recommendation, recorded as
> such** — the ercot-185 pattern, where the mechanical verdict stood unrewritten
> and the promotion rested openly on the owner's standing structural standard.
>
> **A result near +$1.99/MWh is this lane's EXPECTED outcome and is not a
> failure of it.** The memo's ceiling is not re-opened, re-derived or
> re-litigated here.

**Precondition, verified at session open:** **ercot-186 HAS LANDED** (PR #3847,
merge `b09aa35`) — it confirmed the rule-18 grain defect, merged the repair
default-off, and then honoured its own pre-registered STOP, so no A/B was solved
and the keeper did not move. **ercot-187 also landed** (PR #3848, merge
`5c4dc88`) — hygiene: a fail-closed leap-day derive fix that regenerated **no**
committed artifact, and the ERCOT golden-hash drift attributed 100 % to the
owner-adopted 2026-07-26 CAMPD guard correction, exonerating ERCOT-185.

**Keeper this lane builds against, at session start:**
**`2026-08-09-ercot185-shaped-partial`** (bundle
`results/calibration/ercot185_shapedarm_B`), determination **NOT-YET**, fail set
**{C3a-2023, C3b-2023}**.

---

## 1. Headline

| | result |
|---|---|
| **Mechanism** | `ercot_econ_curve_top_refine` — SCHEME R1: the econ ramp's **top block re-sliced `n` ways**, body untouched, total curve MW preserved |
| **Free parameters added** | **ZERO** — the split point is `1 − 1/n` and the sub-count is `n`, both the already-registered `offer_curve_smoothing_n` |
| **Seam proof** | `ercot188_topfine_seamproof.json` — **ALL_ASSERTIONS_PASS** (SP-1…SP-7) |
| **Cross-ISO blast radius** | **NONE** — all five non-ERCOT ISOs byte-identical with the gate **ARMED** |
| **What it buys** | the supply-curve top stops being a 6-block equal-width approximation that cannot express a cliff |
| **Cost** | LP columns **×1.295**; the offer-surface family's **P0 bit-identity proof is PERMANENTLY FORFEITED** |
| **A/B verdict** | **REJECTED-AS-ARMED** on the pre-registered **G-C3c** kill (7 of 8 gates PASS); both members registered (rules 15/16) |
| **The result** | **C3a-2023 −$0.21/MWh — a SIGN FLIP against the memo's +$1.99 ceiling**, inside the pre-registered band, and it localizes the cause |
| **Determination** | **NOT-YET {C3a-2023, C3b-2023}** in both members — UNCHANGED |
| **Keeper** | **`2026-08-09-ercot185-shaped-partial`, NOT moved by this session** (§7) |

---

## 2. The build — SCHEME R1, fixed ex ante and not swept

`offer_curves._econ_curve_steps` cuts each plant's economic ramp into
`offer_curve_smoothing_n = 6` **equal-width** MW blocks priced at their
midpoints, so the finest within-plant position the model can express is **1/6 of
the ramp** — while reality's marginal price forms inside the top **0.24 %** of
the marginal resource's own submitted curve (`q_act` p50 0.9976, ercot-180).
`offer_curve_smoothing_mid = 0.35` already shapes the ramp's **price** axis;
this lane refines its **width** axis.

**R1, exactly:** with `n = offer_curve_smoothing_n`, the body is `n − 1` slices
of width `1/n` at midpoints `(k + 0.5)/n` — **the coarse form's own first
`n − 1` slices, expression for expression** — and the top block becomes `n`
sub-slices of width `1/n²` at midpoints `(n−1)/n + (j + 0.5)/n²`. At `n = 6`:
**11 slices, top sliver 2.778 % of the ramp**, total exactly 1. This is
`scheme_top_refined(6, 6)` as `scripts/probes/ercot184_cliff_resolution_costing.py`
measured it, with the same midpoint rule.

**R1 and no other scheme, and no sweep.** The memo measured R1 as **both the
cheapest and the highest-reach** member: R2 (uniform 60) reaches less at 3.8×
the cost, R3 (~16 GB) is over this box's budget, and reach **saturates then
declines** with slice count (11 → +$1.99, 65 → +$1.66). The slice count and
split point were not swept.

### 2.1 Rule 23 `[R-DOF]` — the crux, and why R1 carries no shape parameter

A non-uniform slicing scheme has a shape, and a shape is a degree of freedom
unless it is pinned structurally. **R1 introduces no numeric parameter at all:**

* the **split point** is `1 − 1/n` — **the boundary the ramp is already sliced
  at**, under the already-identified `offer_curve_smoothing_n`;
* the **sub-slice count** is `n` — the same registered value. The scheme is
  "apply the existing slicing rule once more to the one block that reaches the
  cliff."

So the shape **follows `n`** rather than carrying a value of its own, `n_residual`
does not grow, and the keeper's DOF ledger is carried verbatim — which is itself
the G-DOF evidence.

**The structural grounding is two measurements that PREDATE this build and are
not fits to anything** (MEMO §4.2/§4.3): the top coarse block is the marginal
one in **14 of the 33** econ-marginal object hours — more than any other slice —
and it is the **only** block that reaches the measured ladders' top decile (the
econ ramp spans a median 61.8 % of its plant's stack, so its top slice reaches
ladder `rel` 0.9427, while every lower block sits below 0.9 by construction and
can carry no cliff at all).

### 2.2 The scope hazard, and the containment

`_econ_curve_steps` lives in `offer_curves.py` and is called from
`fleet/assembly.py` on the **ISO-agnostic** assembly path, with no ISO gate
anywhere in it — and **all six keepers share `n = 6`** (MEMO §6). An ungated
change would silently re-slice every ISO's fleet. Containment, all of it in the
same commit:

* one `ScenarioConfig` field, **default OFF**, **ERCOT-gated** in
  `bins_to_fleet` (`config.iso == "ERCOT"`);
* **cache-key registered dropped-at-default in BOTH registries**;
* matrix row in the same PR (rule 28(c));
* `top_refine=False` passed **explicitly** at the committed-band call site, so an
  ISO that later arms `committed_ramp_spread` cannot inherit the refinement
  (MEMO §6 item 3, the dormant coupling).

---

## 3. The seam proof — ALL_ASSERTIONS_PASS

`scripts/probes/ercot188_topfine_seamproof.py` →
`results/calibration/ercot188_topfine_seamproof.json`. Real reconstructed keeper
fleets, no LP built.

| | assertion | result |
|---|---|---|
| **SP-1** | gate-off ERCOT composed fleet **byte-identical to pre-edit HEAD** | **PASS** ×3 years (`mc_base` sha + full row table) |
| **SP-2** | **gate ARMED ⇒ every non-ERCOT ISO byte-identical** | **PASS** ×5 |
| **SP-3** | MW preservation | **PASS** — fleet deviation **1.5e-11 / 2.9e-11 / 2.9e-11 MW** on ~80,745 MW |
| **SP-3b** | CHP steam floor redistributed, never created/destroyed | **PASS** — max group deviation **5.7e-14 MW** |
| **SP-4** | body's `n−1` slices byte-identical in cap AND heat rate | **PASS** ×3 |
| **SP-5** | slice counts exactly `{6, 11}` | **PASS** ×3 |
| **SP-6** | committed band unrefined | **PASS** |
| **SP-7** | pinned default cache key unmoved, armed key distinct | **PASS** — `603c2498bf71d21d` unmoved, armed `613cd5243fd84f20` |

**SP-2 is the charter's mandatory assertion and it is not vacuous.** Each ISO is
reconstructed from its own committed bundle and each carries real `econc` rows:
CAISO `caiso188_d0_control` (1,808 rows / 128 econ plant-groups), PJM
`pjm158_novirt_B` (3,279 / 227), NYISO `nyiso133_cod_control` (851 / 45), NEISO
`neiso87_control_A` (816 / 38), MISO `miso148_basis_A` (3,092 / 147). All are
**read-only**; no other ISO's files, bundle, keeper shard or matrix column was
modified.

### 3.1 The row census and G-COST

| year | rows | LP columns | factor | groups refined | econ MW refined |
|---|---|---|---|---|---|
| 2023 | 1,780 → **2,320** | 16,057,080 → **20,787,480** | **×1.2946** | 108 / 144 | 35,873.4 / 36,115.0 = **99.331 %** |
| 2024 | 1,778 → 2,318 | 16,039,560 → 20,769,960 | ×1.2949 | 108 / 144 | **99.331 %** |
| 2025 | 1,767 → 2,307 | 15,943,200 → 20,673,600 | ×1.2967 | 108 / 144 | **99.331 %** |

The control's own 2023 census — **1,780 rows, 80,744.6 MW, 144 econ
plant-groups, econ ramp 36,115.0 MW** — reproduces MEMO §3.1's census exactly,
which is independent evidence that this build re-slices the same object the memo
costed.

**G-COST comes in UNDER the memo's ×1.39 estimate** (×1.295), because Amendment
1's guard leaves 36 small plant-groups at the coarse form. Peak RSS and
wall-clock are reported in §5.

---

## 4. AMENDMENT 1 — the seam proof caught a real defect, and it is reported, not quietly fixed

**The first build FAILED its own SP-3 / SP-3b / SP-5 in all three years.** The
pre-registered falsifier fired before any LP was solved, which is what it was
for.

| | measured on the first build |
|---|---|
| rows | 1,780 → **2,284**, not 2,500 (×1.275) |
| per-plant slice counts, armed | **`[5, 11]`** — not `[11]` |
| max per-group MW deviation | **exactly 1/6** |
| fleet capacity **deleted** | **40.27 MW** every year |
| CHP steam floor **deleted** | **2.75 MW** of 3,539.95 |

**The cause is not the scheme.** `bins_to_fleet` has long dropped any stepped
tranche of **≤ 0.5 MW** so rounding dust never becomes an LP row. R1's
sub-slices are `curve_cap / n²`, so a plant whose econ ramp is under
`0.5 × n² = 18 MW` had **every one of its six sub-slices dropped** — losing not
the refinement but **the entire top sixth of its ramp**. That is **36 of 144**
ERCOT plant-groups, and it is why the counts read `5`.

**A build that silently deletes capacity while claiming to refine a curve is not
the mechanism that was costed**, and it contradicts the precommit's own §2.2
("total curve MW preserved"). Shipping it would have made every downstream
number un-interpretable.

**The guard.** `assembly._top_refine_ok(curve_cap, n, enabled)` applies R1 to a
plant **only when every sub-slice would clear the assembly's own minimum tranche
capacity**; otherwise that plant keeps the coarse equal-width form
**byte-identically**. Admissible slice counts become exactly `{6, 11}`, and MW is
conserved to floating-point dust.

* **NOT the forbidden sweep.** The slice count and split point are unchanged.
  This is a *feasibility precondition* on where an unchanged scheme applies,
  discovered by a pre-registered falsifier — **and nothing had been solved when
  it was written, so it cannot have been chosen against a residual.**
* **NO free parameter.** The threshold is `MIN_TRANCHE_CAPACITY_MW = 0.5`, the
  assembly's **pre-existing** tranche floor — named as a constant in the same
  commit (rule 5 `[R-NO-MAGIC]`, value unchanged) and now referenced by both the
  filter and the guard so the two cannot drift.
* **The coverage cost, stated:** R1 reaches **108 of 144 plant-groups —
  99.331 % of econ MW**. The 36 excluded groups hold **241.6 MW (0.669 %)** and
  are small by construction (econ ramp < 18 MW), so they are not plausible
  marginal units in the object hours; the memo's costing remains the right
  comparison.

---

## 5. The A/B — the reach is NEGATIVE, and that is the finding

One pair, `scripts/replay_keeper.py` on the keeper bundle, **strictly
sequential**: control `ercot188_topfine_ctl_A` (gate at default) then arm
`ercot188_topfine_arm_B` (`--set ercot_econ_curve_top_refine=true`). One
invocation each, `--year 2023 2024 2025`, years sequential (rules 12/16). Single
delta, verified from both `run_config.json`s: `ercot_econ_curve_top_refine`
`False` → `True`, every other field identical.

| | control | arm | Δ |
|---|---|---|---|
| **C3a-2023** mean LMP | **−32.5 %** ($43.44 vs actual $64.32) | **−32.8 %** ($43.23) | **−$0.21/MWh** |
| C3a-2024 | +1.4 % ($31.43) | +1.2 % ($31.35) | −$0.08/MWh, **PASS kept** |
| C3a-2025 | −7.9 % ($33.41) | −8.0 % ($33.38) | −$0.03/MWh, **PASS kept** |
| **C3b-2023** | 0.602 | 0.608 | +0.006 |
| C3b-2024 | 0.160 | **0.158** | −0.002, **stays under 0.20** |
| C3b-2025 | 0.101 | 0.102 | +0.001 |
| C3c tail (model vs actual 181/53/31) | 61 / 23 / 3 | **58** / 23 / 3 | −3 h in 2023 |
| shed hours | 4 / 2 / 0 | 4 / 2 / 0 | **0** |
| C1 / C2 / C4 / C6 / C8 | PASS | PASS | — |
| **determination** | NOT-YET {C3a, C3b} | NOT-YET {C3a, C3b} | **unchanged** |

Run ids: `2026-08-11-run188-ctl-topfine-control`,
`2026-08-11-run188-arm-topfine-cliff`.

### 5.1 The sign flip, and why it is the result rather than a disappointment

ercot-184 measured R1's reach at **+$1.99/MWh** — a ceiling over the entire
family of MW-preserving re-slicings. **The real LP delivers −$0.21/MWh.**

That is **inside** the precommit's pre-registered reconciliation band
**[−$1.00, +$4.00]**, so the STOP does **not** fire and the result is banked as
measured. But the sign flip is not noise, and this FINDING does not treat it as
such: **it isolates exactly the channel MEMO-ercot184 §3.3 said it could not
measure and named as the real cost of the build.**

The memo's instrument was **invariant-quantity repricing**: it held the cleared
quantity `Q_h` FIXED and asked what the refined stack charges at that quantity.
That is a pure measurement of the **ladder channel**, and on that channel R1 is
worth about +$2/MWh — the memo's number is not overturned. What the IQR could
not see, and said so, is that a row-count change **also moves P0**, because the
slicer writes heat rates into `mc_base`, which *is* the P0 objective. The real
LP carries both channels at once.

**The P0 channel is measured, not inferred** (§6): **73 of the 132 committed
rows — 12,474 MW — carry a different P0 commitment pattern under the arm**, with
8 fewer starts and 96 more committed on-hours, and the gas commitment bridge
(which detects its floors from the P0 run pattern) moves in **every** year.

> **So (c2) is not merely too small: at solve grain the ladder gain does not
> survive to the annual level, and the P0 channel its own seam breach opens is
> demonstrably live across half the committed fleet.** §6.2 is careful about how
> far that can be pushed — the start-amortization *arithmetic* is measured and
> far too small to carry the offset, and nothing here apportions the ≈ $2.2/MWh
> between ladder and commitment, because **no counterfactual separates them.**
> That inability is precisely the cost MEMO §3.3 priced. MEMO §8's reading is
> reinforced, not overturned: you cannot reach a price by adding rows above
> where the market clears.

### 5.2 What the mechanism DID do, stated plainly

The build works exactly as specified. The model's supply-curve top went from a
6-block equal-width approximation carrying **33** econ rows in the measured top
decile to **382 rows above ladder `rel` 0.9**, quoting up to **145× delivered
gas**, with capacity conserved to 1.5e-11 MW. **The model can now express a
cliff; it still does not clear on one** — the same conclusion item 23 reached
from the opposite direction, now reproduced by a real LP rather than a
merit-order mirror.

---

## 6. The P0 seam — measured, and a PERMANENT NAMED LIMITATION

`scripts/probes/ercot188_p0_delta.py` → `ercot188_p0_delta.json`. Because a
bundle persists only the **P1** dispatch frame, the probe replays each member
through the **same entry point the A/B used** with `compute_monthly_markup`
spied, capturing the real `r0.dispatch` and the real markup array and aborting
before P1. What follows is the A/B's own P0, 2023.

| | control | arm | Δ |
|---|---|---|---|
| LP rows | 1,780 | 2,320 | +540 |
| **P0 total energy** | 303.47655 TWh | 303.47657 TWh | **+2.8e-05 TWh** |
| P0 econ-ramp energy | 130.2676 TWh | 130.2564 TWh | −0.0111 TWh |
| P0 committed energy | 82.3717 TWh | 82.3891 TWh | +0.0174 TWh |
| **committed rows whose commitment MOVED** | — | — | **73 of 132 (55.3 %) — 12,474 MW** |
| committed starts | 10,949 | 10,941 | **−8** (max per row 4) |
| committed on-hours | 494,683 | 494,779 | **+96** (max per row 13) |
| P1 startup markup, cap-wtd mean | $3.7789/MWh | $3.7769/MWh | **−$0.0020/MWh** |
| …cap-wtd mean **absolute** per-row move | — | — | **$0.0150/MWh** (max row $0.845) |

### 6.1 What this establishes, and what it does NOT

**The seam breach is real, and it is large in the dimension that matters.**
**73 of 132 committed rows — 12,474 MW, over half the committed fleet and the
same order as the 16.5 GW MEMO §3.3 sized — have a DIFFERENT P0 commitment
pattern under the arm.** Eight starts disappear and 96 committed on-hours
appear. This is not a residual effect at the edge of the fleet; the commitment
state of the capacity sitting directly beneath the object hours' marginal rows
is genuinely different. Confirmed independently at solve grain in all three
years by the gas commitment bridge, which detects its floors from the P0 run
pattern: floored unit-hours **12,375 → 12,309** (2023), **6,164 → 6,160**
(2024), **13,326 → 13,287** (2025).

**Two things the numbers do NOT support, stated so they are not over-read:**

1. **P0 energy is conserved** — total P0 generation moves by 2.8e-05 TWh on 303
   TWh. The refinement redistributes ~0.011 TWh from the econ ramp into the
   committed band; it does not change how much the thermal stack produces. What
   moved is *which units are on when*, not *how much runs*.
2. **The startup-amortization sub-channel is SMALL.** The capacity-weighted mean
   P1 startup markup on the committed rows moves **−$0.0020/MWh**, and even the
   mean *absolute* per-row move is **$0.0150/MWh** (largest single row $0.845).
   **That is roughly two orders of magnitude too small to account for the
   −$0.21/MWh annual price delta on its own.** The arithmetic of the start
   amortization is therefore *not* the explanation, and this FINDING does not
   claim it is.

### 6.2 The honest attribution — and why the inability IS the finding

Chaining what is measured: ercot-184's invariant-quantity mirror priced the
**ladder** channel at **+$1.99/MWh** *holding cleared quantity fixed*; the real
LP delivers **−$0.21/MWh**. The ≈ $2.2/MWh difference is, by construction, the
part the IQR could not see — the LP re-optimizing quantity and commitment. §6's
measurement localizes that to the **merit-order/clearing side** (which row is
marginal, given a materially different commitment state across 12.5 GW) rather
than to the **bid-level** start-cost arithmetic, which is measured and small.

**But it does not go further than that, and it cannot.** There is no
counterfactual in which the ladder moves and the commitment does not: they are
the same code change. Every control-vs-arm difference here is confounded with
commitment-side motion, so **the mechanism is isolated by argument, never by
proof** — which is exactly what §3 of the precommit said would be the largest
cost of this build, and this probe is what turns that from a prediction into a
measured fact.

> **Correction of record.** Before this decomposition landed, this session's
> matrix cell, lever-queue item and calibration-log entry each stated that the
> ladder gain is *"CONSUMED by the commitment channel."* That over-attributed:
> the commitment channel is demonstrably live, but the startup-markup sub-channel
> is too small to carry the offset, and no measurement here apportions the
> ≈ $2.2/MWh between the two. All three records are corrected to the statement
> above rather than left standing.

### 6.3 What is settled independently of any measurement

**This lane BREACHES the offer-surface family's P1-only seam and PERMANENTLY
FORFEITS its bit-identity proof.** Every ERCOT offer-surface mechanism since
ERCOT-86 is applied at the `mc_bid_adjust` seam so that P0 stays bit-identical
and each arm can be *proved* not to disturb commitment. `_econ_curve_steps`
writes heat rates into the **base** fleet, i.e. into `mc_base`, which **is** the
P0 objective — so a row-count change moves P0 **by construction** and the seam
does not apply. The ercot-181 seam proof's byte-identity assertions
(SP-α1/α2/α3/α5) **have no analogue here**: every control-vs-arm difference is
confounded with commitment-side motion, so the mechanism can be isolated **only
by argument, never by proof**. In a lane whose last two rejections turned
entirely on decomposing a headline number into its real and artefactual parts,
that is the single largest cost being paid.

**It is not time-limited and it does not expire when a later gate passes.** It
was costed at MEMO-ercot184 §3.3, accepted by the owner as the price of the
structural fidelity, and is carried in the keeper note as well as here.

One concrete instance is already visible in the control's own 2023 log, before
any comparison: `ercot_gas_commitment_bridge` floors **12,375 unit-hours
(1.69 TWh) across 1,942 bridged gaps**, and it detects those floors from the
**P0** run pattern — so it sits directly downstream of the row-count change.
Its arm-vs-control delta is reported here with the rest.

---

## 7. Verdict, gates and keeper

Gates are adjudicated **control-vs-arm on the same-HEAD pair**, never against the
committed keeper's ledgered numbers (the ERCOT keeper is known not to reproduce
byte-for-byte at current main — ercot-173 §5, carried through
ercot-174/185/186). The control reproduces the keeper's ledgered readings
closely: C3a −32.5 / +1.4 / −7.9 %, C3b 0.602 / 0.160 / 0.101, tail 61/23/3,
shed 4/2/0 — **identical to the keeper's record on every one of them**, so no
drift needs stating this round.

### 7.1 The eight pre-registered gates, adjudicated verbatim

| gate | bar (pre-registered) | measured | verdict |
|---|---|---|---|
| **G-SHED** (PRIMARY) | no year's shed count may rise | 4/2/0 → **4/2/0** | **PASS** |
| **G-OWNER** | C3a-2024 keeps PASS; C3b-2024 ≤ 0.20; C3a-2025 not beyond −9.1 % | +1.2 % PASS; **0.158**; −8.0 % | **PASS** |
| **G-C3c** | 61/23/3 must not degrade | **58**/23/3 — 2023 **3 h further from actual 181** | **FAIL** |
| **G-COAL148** | ≤ +0.5 TWh any year | max rise **−0.0 TWh** (−0.0007/−0.0017/−0.0) | **PASS** |
| **G-SPUR** | spurious mid-band hours must not increase | 10→**9**, 11→11, 1→1 | **PASS** |
| **G-DOF** | zero new fitted scalars; `n_residual` does not grow | zero; ledger carried verbatim | **PASS** |
| **G-COST** | report columns/RSS vs ×1.39; STOP if over the box | **×1.295**; peak **12.71 GB** vs control 10.20; no year dropped | **PASS** |
| **Rule-22 LOYO** | leave-one-year-out before promotion | §7.2 | **PASS** |

> ### VERDICT: REJECTED-AS-ARMED on G-C3c. Seven of eight gates PASS.
> Both members are **REGISTERED anyway**, all three years (rules 15/16), and the
> gates are **not renegotiated after the solve**.

**G-SHED deserves its own line, because it was the PRIMARY falsifier.** The
ercot-48/49 manufactured-shortage signature has killed this object twice. The
memo aimed G-SHED at R1 build-free and measured **zero shed-exposed hours in
every hour of 2023** (§4.6). **That result is now confirmed at SOLVE grain: not
one shed hour was added in any year.** Whatever else is true of (c2), it is not
the ercot-48/49 failure mode — its motion is genuine offer formation, which is
the one thing it does better than every prior candidate in this lane, and it
still does not save the mechanism.

**G-C3c, at full magnitude.** The 2023 model tail moves **61 → 58** against an
actual of **181**, i.e. **3 hours further from actual** on the already-ledgered
model-class caveat; 2024 and 2025 are unchanged at 23 and 3. This is a small
number and it is still a fail: the gate said "must not degrade" and it degraded.
It is also *directionally coherent* with §5.1 rather than anomalous — a mechanism
whose net effect on the annual level is −$0.21/MWh is a mechanism that lowered
prices slightly, and a slightly lower price set produces slightly fewer hours
over $200.

### 7.2 LOYO (rule 22)

**R1 identifies no parameter** — its split point and sub-slice count are both the
already-registered `offer_curve_smoothing_n`, and nothing is fitted to any year.
Leave-one-year-out is therefore **N/A on the same ground as ercot-181 and
ercot-185, and per-year deltas stand in its place** (the ercot-173 precedent).
Those deltas are **C3a −0.21 / −0.08 / −0.03 $/MWh** — **uniformly slightly
negative across all three years**. There is no year in which the arm gains and
another in which it degrades, so there is no in-sample gain bought with held-out
degradation. The mechanism is consistently, mildly negative everywhere.

### 7.3 Keeper

**`2026-08-09-ercot185-shaped-partial` is NOT moved by this session.** No
promotion, no demotion, no re-key, no keeper-shard edit. ERCOT holds no
`complete` and no `final` marker, so no `calibration-complete.json` re-key
applies.

**A structural-fidelity promotion over this rejected verdict remains available
to the OWNER and is expressly not assumed here.** The precedent exists — item 23
was promoted INERT-ON-THE-OBJECT, and ercot-185 was promoted over a
REJECTED-AS-ARMED verdict — but in both of those the mechanism was, respectively,
free (zero LP columns, bit-identical P0) and residual-improving. Here the
purchase costs ×1.295 columns, forfeits the family's P0 bit-identity proof
permanently (§6), and the residual moves slightly the wrong way. **That is the
trade the owner would be accepting, stated plainly rather than smoothed over,
and it is the owner's call, not this session's.**

---

## 8. Governance

* **Rule 1 `[R-STRUCT]`** — the build is a structural-fidelity purchase the
  **owner** chose; the memo's own recommendation (A) CLOSE is recorded as
  **overridden, not rewritten**, and its +$1.99 ceiling is neither re-derived
  nor widened. The measured outcome is reported at full magnitude including the
  sign flip against this lane's own expectation, and the mechanism is **not**
  retained by arguing the residual — the verdict stands REJECTED-AS-ARMED.
* **Rule 12 / 16 `[R-PARALLEL]` / `[R-ALLYEARS]`** — one invocation per member,
  `--year 2023 2024 2025`, years sequential; the two members strictly sequential
  (peak 12.71 GB on a 15 GB box). No year dropped.
* **Rule 13 `[R-MEASURED]`** — no measured outcome enters the mechanism. A
  slicing rule is pure construction; R1's shape is pinned to the registered
  `offer_curve_smoothing_n`, and it regenerates identically for a forecast year.
* **Rules 15 / 16 `[R-DASHBOARD]`** — **both** members registered, all three
  years, on a REJECTED verdict. Retention evicted exactly the two runs the
  precommit named in advance (`2026-08-04-run162a-storage-rt` and
  `-run162b-storage-rt`, a matched pair). `legitimacy_diagnostics.json` and
  `calibration_attestation.json` were generated **before** scoring, on both.
* **Rule 22 `[R-HOLDOUT]`** — ERCOT holds no `complete`/`final` marker; every
  year touched by every solve, probe and score is inside {2023, 2024, 2025}.
  LOYO adjudicated in §7.2.
* **Rule 23 `[R-DOF]`** — **zero new fitted scalars.** R1's split point and
  sub-slice count are both the registered `offer_curve_smoothing_n`; Amendment
  1's guard uses the assembly's pre-existing 0.5 MW tranche floor, named as a
  constant with its value unchanged. `n_residual` does not grow; the DOF ledger
  is the keeper's, verbatim.
* **Rule 24 `[R-REGISTRY]`** — one `ScenarioConfig` field, both cache-key
  registries in the same commit, default key `603c2498bf71d21d` verified
  unmoved; the armed state appears in the arm's `run_config.json`.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT-gated at the call site, with **SP-2
  proving all five non-ERCOT ISOs byte-identical with the gate ARMED**. No other
  ISO's files, bundle, keeper shard, status part or matrix column was modified;
  the five cross-ISO bundles were read only. Their matrix cells stay `U`.
* **Rule 27 `[R-PUSH]`** — `scenarios.py` (13,093 lines), `assembly.py` (1,801)
  and `offer_curves.py` (1,142) were edited **locally** with the Edit tool and
  pushed as exact on-disk bytes; **all three blob-verified against a fresh
  remote fetch** (line count + hash) before the next commit.
* **Rule 28 `[R-MECH-MATRIX]`** — DO-NOT-REDO checked before pre-registration
  (a); the cell stamped `O → R` with its citation **in this session** (b); the
  row landed in the same PR as the field (c); the other five ISOs stay `U` (d).
  Lever-queue item 26 added.
* **GitHub Actions** — nothing offloaded. Every build, seam proof, solve, probe,
  score and registration ran in-session.
* **Data provisioning note.** Three gitignored `data/clean` partitions
  (`transfer-interface-limits`, `ramp-capability`, `capacity-deliverability`,
  `nyiso-interface-flows`) were **regenerated from committed raw** so the SP-2
  panel could run each ISO's *own recorded config* rather than a disarmed one.
  No raw data was fetched and no config was overridden for any ISO.
* **Keeper** — `2026-08-09-ercot185-shaped-partial`, untouched.

**Next shorthand: ercot-189.**
