# ADDENDUM miso-238 — the provenance gate FIRED on its own instrument, and the repair is declared BEFORE the repaired numbers are computed

Extends `PREREG-miso238-pjm-seam-channel-attribution-2026-09-07.md` (pushed `0deffdb9`).
On the miso-233 / miso-235 / miso-236 / miso-237 addendum pattern.

**NO PRE-REGISTERED DECISION RULE IS TOUCHED.** The channel definitions (PREREG §2), the
gating seam (PJM), the Q-A and Q-B bars (`≥ 0.50` in all three years), the absolute floors
(`|γ| ≥ 200` MW/z, `|a| ≥ 100` MW), the basis discipline (§0b) and every §5 restriction stand
exactly as pushed. Zero LP, as the PREREG declared. Keeper unchanged at
`2026-09-07-miso-233-spp-hourly` (CALIBRATED, C3c the single ledgered caveat, DOF 41/2).

---

## 0 — STATED FIRST, AGAINST INTEREST: the gate rejected this session's own instrument

`PREREG-miso238` §1 fixed a four-leg provenance gate and said *"If any leg fails, the
instrument is declared BROKEN and NOTHING below is read or published."* On the first run of
`scripts/probes/_miso238_pjm_seam_channel_attribution_phase0.py`, **leg G-P2 FAILED** and the
probe refused to publish, exiting non-zero with only the gate's own deltas printed:

| leg | bar | measured on the first run | verdict |
|---|---:|---:|---|
| **G-P1** — miso-235's σ column, 24 values | ≤ 0.5 MW | **0.048 MW** | PASS |
| **G-P2** — miso-237's own-net-load coefficients, 24 values | ≤ 0.5 MW/z | **457.126 MW/z** | **FAIL** |
| **G-P3** — miso-237 ADDENDUM §A's alignment column, 48 values | ≤ 0.001 | **0.00005** | PASS |
| **G-ID** — the decomposition identity | ≤ 1e-6 MW | **9.095e-13 MW** | PASS |

**No adjudicating quantity has been read.** The probe's own control flow returns before any
Q-A, Q-B or census value is printed, and this addendum is written with nothing but the four
numbers above in hand. That is the entire point of putting the gate first.

## 1 — The cause, which is a defect in THIS session's statistic and not in the predecessor's

PREREG §3 defined `γ(r) = cov(r, z_own_nl)` and asserted it *"is miso-237's
`own_net_load_coef_resid_model` exactly (G-P2 proves it)"*. **G-P2 disproves it.** Reading
`scripts/probes/_miso237_price_representation_vs_state_phase0.py` (lines 543–558), miso-237's
coefficient is

    np.linalg.lstsq(_design(s_own, n), r, rcond=None)[0][1]

i.e. the **PARTIAL (multivariate) OLS coefficient** on `z_own_net_load` in the regression of
`r` on `[1 | z_own_net_load | z_own_VRE]` — the own-state block's **first** slope, holding own
VRE fixed. A simple covariance is the **marginal** coefficient and holds nothing fixed. The two
differ whenever MISO's own net load and own VRE are correlated, which they are; the 457 MW/z
worst-case gap is the size of that difference, not a reconstruction error. G-P1, G-P3 and G-ID
all passing says the reconstruction, the residuals, the alignment column and the channel
algebra were right on the first run and only the named statistic was wrong.

## 2 — THE REPAIR, fixed here before the repaired numbers are computed

**`γ` becomes miso-237's estimator, byte-for-byte: the partial OLS coefficient on
`z_own_net_load` in `r ~ [1 | z_own_net_load | z_own_VRE]`.** Nothing else changes.

**The repair costs the decomposition nothing, and this is the reason it is admissible rather
than a convenience.** PREREG §2's exactness rests on the decomposed statistic being **linear in
the residual series**. The partial OLS coefficient is `e₁ᵀ(XᵀX)⁻¹Xᵀ r` with `X = [1 | S_own]`
fixed across channels — **linear in `r`**, exactly as a covariance is. So
`γ_MERIT + γ_ENVELOPE + γ_INTERACT = γ_model` still holds identically, and G-ID still verifies
the underlying series identity to machine precision. The bar stays **≤ 0.5 MW/z**; it is not
moved, widened or re-scoped.

**DISCLOSURE, declared here before it is computed:** the marginal statistic (the simple
covariance the PREREG named) is **also reported** beside the partial one, per seam and year, as
`gamma_marginal_mw_per_z`, so a reader can see the size of the difference this addendum is
correcting rather than take §1 on faith. **It is REPORTED, NOT GATED** and no bar attaches to
it; every §3 and §4 verdict is read on the **partial** coefficient, which is the predecessor's
object.

## 3 — What this addendum explicitly does NOT do

1. **It does not move a bar.** Every threshold, floor and gating seam in PREREG §1, §3 and §4 is
   unchanged. Had the repair required a looser tolerance, the honest outcome would have been to
   publish the failure and stop; it does not.
2. **It does not change what is being attributed.** The object is still miso-237's
   `own_net_load_coef_resid_model` (−866.2 / −1043.4 / −843.5 MW per z-score on PJM) and
   miso-237 ADDENDUM §A's alignment column. The repair makes this session compute them, rather
   than something adjacent to them.
3. **It does not license anything.** PREREG §5 stands entire — no lever is proposed, no
   `delta_k` ladder is re-derived, the measured `(month × hod)` deliverability envelope is not
   touched, and **every number this session produces remains un-targetable** (rules 1
   `[R-STRUCT]` / 13 `[R-MEASURED]`).
4. **It does not re-test anything adjudicated.** Rule 28(a) DO-NOT-REDO holds unchanged; the
   half of item 3 miso-237 completed, miso-236's `(month × hod)` template removal and
   miso-237's item-1 form answer are all left exactly where they are.

## 4 — Governance

Rule 1 `[R-STRUCT]`: nothing is judged by a residual and nothing is proposed; §2's repair is a
statistic definition, selected by the predecessor's committed code and not by any result.
Rule 12 `[R-PARALLEL]`: no LP; nothing on CI. Rule 13 `[R-MEASURED]`: measurement only; no
input changes. Rule 14 `[R-ACCURATE]`: no input changed. Rule 15 `[R-DASHBOARD]`: no run
produced. Rule 19 `[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged; the
decomposition still carries zero free parameters. Rule 22 `[R-HOLDOUT]`: 2023–2025 only.
Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run. Rule 24 `[R-REGISTRY]`: no field created.
Rule 25 `[R-ISO-SCOPE]`: MISO only. Rule 28(b): evidence-append form; no cell verdict moves.
Rule 29 `[R-SCREEN]`: still clause 0, zero LP.
