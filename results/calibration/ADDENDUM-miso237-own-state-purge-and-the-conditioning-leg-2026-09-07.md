# ADDENDUM miso-237 — two supplementary measurements declared BEFORE they are computed, and one conditioning disclosure stated against interest

Extends `PREREG-miso237-price-representation-or-quantity-channel-2026-09-07.md`
(pushed `887c7cad`). On the miso-233 / miso-235 / miso-236 addendum pattern.

**No pre-registered decision rule is touched and NO PRE-REGISTERED VERDICT CAN MOVE.** The
PREREG's provenance gate, Q-1, Q-2 and Q-3 values are already computed and committed in
`results/calibration/_miso237_price_representation_vs_state_phase0.json`, and they stand exactly
as measured whatever this addendum finds. Nothing here can arm a mechanism, charter a lever, move
a matrix cell, or touch the keeper (`2026-09-07-miso-233-spp-hourly`, CALIBRATED, C3c the single
ledgered caveat, DOF 41/2). Zero LP, as the PREREG declared.

---

## 0 — A CONDITIONING DISCLOSURE, stated against interest before anything else

**The PREREG's `ΔR²_S|P1` is NOT miso-236's `ΔR²_A`, and this addendum says so before it is read
that way.** PREREG §2b defines `ΔR²_S|P = R²(x on P ∪ S) − R²(x on P)` for a state block `S`, and
lists `S_nbr` and `S_own` as **two separate blocks**. So `ΔR²_nbr|P1` is the neighbour block's
increment over **price alone** — it does **not** condition on MISO's own state, whereas miso-236's
`ΔR²_A` is the neighbour block's increment over **Block B (MISO's own state)** on the
single-spread residual. The two are different quantities and this session never presents one as
the other.

**This is a disclosure, not a defect, and it does not weaken the gated verdict**, for a reason
fixed here: the gated statistic is the **ratio** `rho = ΔR²_S|P3 / ΔR²_S|P1`, in which the state
block, the rows and the denominator are all held fixed and **only the price block varies**. That
is precisely the form question, and it is well-posed under either conditioning. What the
disclosure requires is §B below, which measures `rho` under miso-236's conditioning too so the
reader does not have to take that on faith.

**The predecessor's own object is separately reproduced, not approximated:** the PREREG's
provenance leg **G-P2** recomputes miso-236's `delta_r2_A_nohydro` in miso-236's own metric for
all nine PJM/SPP/South × year cells and agrees to **≤ 0.005** by the bar it fixed ex ante.

---

## A — the OWN-STATE PURGE test on PJM's unexplained price-alignment defect (declared HERE, before it is computed)

**Why it is worth a number.** miso-235 §4b measured the model's PJM seam residual as **2.5–4.6×
more price-aligned** than the measured seam's at 0.95–1.07× the magnitude, and named no cause.
miso-236 tested the handoff's one named explanation — the deterministic `(month × hod)` envelope
template — and **REMOVED it**, leaving the defect open with **no named cause at all** (handoff
item 3). The PREREG's Q-2(c) sign leg is already computed and is pre-registered as REPORTED, NOT
GATED. If the model's residual carries an own-net-load response the real seam does not, then —
because MISO net load is the dominant driver of MISO's price — that response **is** a spurious
price alignment, and item 3 would have a candidate cause. That is a hypothesis, and this addendum
tests it rather than asserting it.

**The measurement, fixed here.** With `P` the **Indiana-hub RT** price (the scored basis, and the
same series miso-235 §4b used for its alignment column) and `S_own` the PREREG's own-state block:

    r_purged = r - proj_{S_own}(r)          (OLS residual of r on [1 | S_own])
    alignment(r) = |corr(r, P)|

computed for **both** sides — `r_model` and `r_measured` — so the comparison is like-for-like, and
reported per seam and year for all four seams. The **movement fraction** on the model side is

    phi = ( alignment(r_model) - alignment(r_model_purged) )
          / ( alignment(r_model) - alignment(r_measured) )

i.e. how far purging the own-state block moves the model's alignment **toward the measured seam's**,
as a fraction of the whole gap.

**DECISION RULE, fixed here, GATED ON PJM ONLY (the seam item 3 names):**

* **CANDIDATE CAUSE IDENTIFIED** iff `phi >= 0.50` in **all three years**.
* **REFUTED AS THE CAUSE** iff `phi < 0.20` in **any** year.
* **PARTIAL** otherwise, reported as partial and closing nothing.

The other three seams are **reported, not gated**.

**RULE, fixed here, and it binds whatever the verdict:** a CANDIDATE CAUSE verdict **names an
object for a successor's charter and charters nothing**. It does not arm a mechanism, name a
field, size anything, or license a re-derive or a damping factor on the PJM or SPP `delta_k`
ladders, which stay derived, frozen and pinned to their derives by test (rule 23
`[R-FROZEN-DERIVE]`); a factor swept against this alignment is the rule 1 `[R-STRUCT]` fitted
mechanism, exactly as PREREG §5.2 already fixed. And `phi` is **never a tuning target**: no
successor may size, scale or tune any mechanism to make a modelled alignment land on a value
here (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`), the same restriction miso-236's ADDENDUM §A
fixed for its sizing number.

**Stated in advance so it cannot be argued afterwards:** the model side is a **reconstruction**
number (miso-235's four-seam form, harness `corr(recon, committed)` +0.9845 / +0.9745 / +0.9839)
and is labelled as one wherever it appears. And a purge is a **diagnostic projection, not a
proposed mechanism** — nothing here proposes removing a term from the model.

## B — `rho` under miso-236's CONDITIONING (declared HERE, before it is computed)

Per §0, the PREREG's blocks are unconditional on each other. This leg recomputes the **same
ratio** with the *other* state block held in **every** price base:

    rho_nbr_given_own = [ R2(x on P3 u S_own u S_nbr) - R2(x on P3 u S_own) ]
                        / [ R2(x on P1 u S_own u S_nbr) - R2(x on P1 u S_own) ]

and its mirror `rho_own_given_nbr`, both on dof-ADJUSTED `R²` with rank-based `k`, exactly as
PREREG §2a fixed. The numerator and denominator of `rho_nbr_given_own` are miso-236's `ΔR²_A`
object (up to the denominator, which cancels in the ratio).

**RULE, fixed here: REPORTED, NOT GATED, and it CANNOT change any pre-registered verdict.** The
gated verdict is the PREREG's `rho` on the unconditional blocks and stays exactly as committed,
whatever this leg shows. It is a **robustness disclosure** answering §0's own objection, not a
second adjudication, and no bar attaches to it. Reported alongside the pre-registered value for
every seam-year that has both blocks.

## C — governance

Rule 1 `[R-STRUCT]`: nothing is judged by a residual and nothing is proposed; §A's `phi` is
declared un-targetable before it is computed. Rule 13 `[R-MEASURED]`: measurement only; no
measured outcome enters any solve, and the PREREG §2c inadmissible-forms list binds here unchanged.
Rule 15 `[R-DASHBOARD]`: no run produced. Rule 19 `[R-ONE-MECH]`: no mechanism added. Rule 21
`[R-DOF]`: 41/2, unchanged. Rule 22 `[R-HOLDOUT]`: 2023–2025 only. Rule 23 `[R-FROZEN-DERIVE]`: no
derive re-run; §A restates the freeze and binds itself to it. Rule 24 `[R-REGISTRY]`: no field
created. Rule 25 `[R-ISO-SCOPE]`: MISO only. Rule 28(b): evidence-append form; no cell verdict
moves. Rule 29 `[R-SCREEN]`: still clause 0, zero LP.
