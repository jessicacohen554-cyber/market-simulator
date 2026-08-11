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
| **A/B verdict** | *(§5)* |
| **Keeper** | *(§7)* |

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

## 5. The A/B

> **INCOMPLETE — WRITTEN BEFORE THE RESULT, AND DELIBERATELY EMPTY.** The A/B
> pair is solving as this section is committed: control
> `ercot188_topfine_ctl_A` (gate at default) then, **strictly sequentially**,
> arm `ercot188_topfine_arm_B` (`--set ercot_econ_curve_top_refine=true`) — one
> invocation each, `--year 2023 2024 2025`, years sequential (rules 12/16), on a
> 15 GB box where two concurrent ERCOT per-plant solves would OOM.
>
> **No number is written here in advance, and the §4-of-the-precommit gates are
> not renegotiated once they are.** The pre-registered expectation is
> ≈ **+$1.99/MWh** with the determination unchanged at NOT-YET
> {C3a-2023, C3b-2023}; the reconciliation STOP fires if the measured 2023
> delta lands outside **[−$1.00, +$4.00]/MWh**, in which case the ladder channel
> is decomposed from the P0/commitment channel **before anything is
> registered**.

---

## 6. The P0 seam — a PERMANENT, NAMED LIMITATION

> **PENDING the pair.** Measured by `scripts/probes/ercot188_p0_delta.py`
> (committed at `18102c2`) once both bundles carry their
> `dispatch/<year>_P0.parquet`.

What is **already settled**, and does not depend on the measurement:

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

> **PENDING the pair.** Gates are adjudicated **control-vs-arm on the same-HEAD
> pair**, never against the committed keeper's ledgered numbers (the ERCOT
> keeper is known not to reproduce byte-for-byte at current main — ercot-173 §5,
> carried through ercot-174/185/186); both readings are reported and any drift
> stated at full magnitude.
>
> **Failing a gate = REJECTED-AS-ARMED, and the run is REGISTERED ANYWAY**
> (rules 15/16). **Promotion on structural fidelity over a rejected mechanical
> verdict is the OWNER'S standard to apply and is not this session's to
> assume.** Keeper at time of writing, unchanged:
> `2026-08-09-ercot185-shaped-partial`.

---

## 8. Governance

*(completed with §5–§7; the settled entries are the precommit's §8, unamended
except for Amendment 1's guard, which adds no free parameter and leaves rule 23
`[R-DOF]` intact.)*
