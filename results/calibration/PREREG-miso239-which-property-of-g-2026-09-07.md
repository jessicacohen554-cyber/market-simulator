# PREREG miso-239 — WHICH PROPERTY of the merit ladder `g` carries the PJM seam's spurious own-net-load response? Queue item 1, on one exact zero-DOF decomposition

**Pushed BEFORE any adjudicating quantity is computed.** miso-234 did not push a
pre-registration and correctly forfeited its right to close or re-open anything on its own
numbers; miso-235, miso-236, miso-237 and miso-238 each did, and each closed a queue leg on its
own rule. This session follows them.

**Keeper `2026-09-07-miso-233-spp-hourly`** (bundle `results/calibration/miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF 41/2. **MISO HAS NO FAILING
GATE**, and there is no rubric failure anywhere in the program, so nothing here targets one.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and no out-of-training
year is solved, scored or registered. MISO carries exactly ONE registered run (rule 15).

**ZERO LP IS PLANNED.** No `ScenarioConfig` field is created or armed, no bundle is produced, no
run is registered or pruned, the keeper is not replayed and not touched.

---

## 0. State of the predecessor's record — STATED FIRST, AGAINST INTEREST, BEFORE ANY NUMBER

### 0a. miso-238's FINDING and its phase-0 JSON ARE NOT ON `main`

This session's handoff quotes miso-238's published numbers as settled. Read at
`origin/main` = `8377e878` (2026-09-07), the record is **incomplete**:

| miso-238 deliverable (its PREREG §6) | on `main`? |
|---|---|
| `PREREG-miso238-pjm-seam-channel-attribution-2026-09-07.md` | **YES** (`0deffdb9`) |
| `ADDENDUM-miso238-gate-repair-and-the-partial-coefficient-2026-09-07.md` | **YES** (`6937a251`) |
| `scripts/probes/_miso238_pjm_seam_channel_attribution_phase0.py` | **YES** (`6937a251`) — but see §0b |
| `results/calibration/_miso238_pjm_seam_channel_attribution_phase0.json` | **NO** |
| `results/calibration/FINDING-miso238-*.md` | **NO** |
| MISO matrix-shard evidence append / `§5.4` stamp / `docs/calibration-log/miso.md` entry | **NO** |

`git log --all -- scripts/probes/_miso238_*.py` returns exactly one commit (`6937a251`) and no
branch carries the missing files. **No number quoted in this session's handoff from miso-238 is
reproducible from a committed artifact today.** This is disclosed here, before anything is
computed, and it sets §1's gate: this session reproduces miso-238's published column from
scratch and **publishes it**, or it stops.

### 0b. The committed miso-238 probe is the PRE-REPAIR version — it fails its own committed gate

`ADDENDUM-miso238` §0 records that leg **G-P2 FAILED at 457.126 MW/z against a 0.5 MW/z bar**
because the PREREG named a simple covariance where miso-237's `own_net_load_coef_resid_model` is
the **partial** OLS slope on `z_own_net_load` in `r ~ [1 | z_own_net_load | z_own_VRE]`; §2 then
declared the repair (*"`γ` becomes miso-237's estimator, byte-for-byte"*) plus a
`gamma_marginal_mw_per_z` disclosure column. **The probe pushed in that same commit still carries
the un-repaired estimator** (`_miso238_…phase0.py:139-144`, `cov(r, z_nl)`), and carries no
marginal column. So the committed instrument contradicts its own committed ADDENDUM and cannot
publish.

**Declared here, before it is run:** this session applies **exactly and only** miso-238 ADDENDUM
§2's repair to that probe — the partial-OLS estimator plus the declared
`gamma_marginal_mw_per_z` disclosure column — and regenerates
`_miso238_pjm_seam_channel_attribution_phase0.json`. **No bar, floor, gating seam, channel
definition or decision rule of miso-238 is touched**, and the repair's correctness is not
asserted, it is *verified*: G-P2 must clear 0.5 MW/z (§1). This is the execution of a repair a
predecessor declared in advance in a committed document; it is **not** the authoring of a
predecessor's FINDING, and this session claims no miso-238 verdict as its own. Where a miso-238
verdict is relied on below it is cited as the handoff's, corroborated by §1's own reproduction.

### 0c. Basis discipline (carried from miso-234 §0a / miso-235 §0b / miso-236 §0b / miso-237 §0b / miso-238 §0b — it bit a first draft)

* **Indiana-hub RT** — `_miso224_floor_anatomy_phase0.actual_zone_price(year)["MISO-Indiana"]`,
  `values="rt"`. The lane's scored basis. Builds the finite-hour `ok` mask byte-identically to
  miso-236/237/238, so the hour set is the predecessors', and is the alignment price `P`.
* **Indiana-hub DA** — the basis `MISO_SEAM_LADDER_BY_YEAR` was Q-Q derived against, and the
  basis of **every regressor and every merit signal** below.

They correlate only +0.402 / +0.424 / +0.553 and are never interchanged. miso-232's measured
decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here.

### 0d. What was established BEFORE this PREREG was written — CODE READING and PUBLISHED PREDECESSOR NUMBERS only

No adjudicating quantity is among them.

1. **On PJM the export leg is identically zero, in all three channels.** miso-238 (handoff,
   verbatim): *"every export sub-channel is exactly 0.00 in both statistics and all three years,
   because MISO_external never falls below the export ladder's first rung ($12.34/$11.32/$18.36)
   in ANY of 8,760 hours"*. Code reading confirms the mechanism: with `q_k(t) ≡ 0` for every `k`
   and hour, `q̃_k ≡ 0` and `q̄_k = 0`, so `MERIT_export = ENVELOPE_export = INTERACT_export = 0`
   identically. **This is GATED, not assumed** (§1, G-X0).
2. **Therefore, on PJM and exactly,** with `b̄_k` the annual-mean band weights and
   `s(t) = p_bus(t) − p_border(t)` the model's own merit spread:

       MERIT(t)  =  Σ_k ( 1[s(t) > δ_k] − m̄_k ) · b̄_k  =  g(s(t)) − ḡ,
       g(x) = Σ_k b̄_k · 1[x > δ_k],   K = SEAM_FLOW_TRANCHES = 8.

   `g` is a **monotone non-decreasing, bounded, 8-step** function of the spread — the handoff's
   object. `g(x) ∈ [0, G₇]` with `G_k = Σ_{j≤k} b̄_j`.
3. **The merit signal and the pre-registered regressor are DIFFERENT SPREADS.** The ladder clears
   on `s = p_bus − p_border` (the **model's** MISO_external price against the PJM border), while
   `ols_resid(·, p1)` removes `p1 = da − p_border` (the **measured** Indiana-hub DA against the
   same border) — `_miso238_…phase0.py:388-393` vs `:400-407`. A code fact stated in advance,
   recorded because §2's `LINEAR` channel is exactly the part of `g`'s response that this
   mismatch leaves behind. **It is not a defect claim and nothing here proposes changing it.**
4. **`γ` is a linear functional of the residual series.** `γ(r) = e₁ᵀ(XᵀX)⁻¹Xᵀ r` with
   `X = [1 | z_own_nl | z_own_VRE]` fixed (miso-238 ADDENDUM §2). So `γ` decomposes **exactly and
   additively** across any additive split of the series **and across any partition of the hours**
   (`γ(r) = Σ_t w_t r_t` for a fixed weight vector `w`). Both facts are used in §2 and §3 and
   neither is an assumption about the data.
5. **The ladder is frozen.** `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"]`
   is derived, frozen and pinned to its derive by test (rule 23 `[R-FROZEN-DERIVE]`); the
   `(month × hod)` deliverability envelope is a measured input (rule 14 `[R-ACCURATE]`). §5.2
   forbids touching either **whatever this session measures**.

---

## 1. The provenance gate — reproduce the PREDECESSOR before reading anything new

Fixed ex ante. **Nothing in §2–§4 is read or published unless all six legs clear.** miso-238's
four-leg gate is the template *and* the cautionary tale (it fired on its own instrument); this
session adds two legs because it must also reproduce miso-238 itself.

* **(G-P1)** miso-235's `sigma_measured_mw` and `sigma_resid_measured_mw`, 4 seams × 3 years
  (24 values), agree with the committed `_miso235_…json` to **≤ 0.5 MW**.
* **(G-P2)** miso-237's `own_net_load_coef_resid_model` and `…_measured`, 4 × 3 (24 values),
  agree with the committed `_miso237_…json` to **≤ 0.5 MW/z**, computed with miso-237's own
  **partial-OLS** estimator (miso-238 ADDENDUM §2's repair). This is the object this session
  decomposes, reproduced in the predecessor's own metric first.
* **(G-P3)** miso-237 ADDENDUM §A's alignment column (4 × 3 × 4 = 48 values) agrees with the
  same committed JSON to **≤ 0.001**.
* **(G-P4) — miso-238's PUBLISHED column, reproduced from scratch.** Because §0a's artifacts are
  missing, the reference values are the ones this session's handoff quotes, restated here
  verbatim **before** they are recomputed, and the bars are fixed here:

  | miso-238 quantity (PJM, 2023 / 2024 / 2025) | handoff value | bar |
  |---|---|---|
  | `gamma_model_mw_per_z` | −866.18 / −1043.37 / −843.45 | ≤ 0.5 MW/z |
  | `share_of_model.MERIT` | 1.005 / 0.892 / 0.938 | ≤ 0.005 |
  | `share_envelope_plus_interact` | −0.005 / +0.108 / +0.062 | ≤ 0.005 |
  | `a_by_channel_purged_mw.MERIT` | −278.2 / −226.7 / −213.9 | ≤ 0.5 MW |
  | `a_model_purged_mw` | −327.0 / −263.3 / −242.0 | ≤ 0.5 MW |
  | `a_measured_purged_mw` | −256.0 / −119.5 / −205.4 | ≤ 0.5 MW |
  | `sat_share` | 0.1740 / 0.0068 / 0.0000 | ≤ 0.0005 |
  | `sat_share_top_decile_own_net_load` (2023) | 0.0297 | ≤ 0.0005 |
  | `mean_bands_in_merit` | 5.848 / 4.585 / 3.535 | ≤ 0.005 |
  | `corr_env_import_own_net_load` | +0.3063 / −0.0843 / +0.3638 | ≤ 0.0005 |
  | `by_leg.MERIT_export`, PJM | 0.00 / 0.00 / 0.00 | exact 0 |

* **(G-X0) — the export leg is identically zero on PJM.** `max_t |exp(t)| = 0` exactly, in all
  three years. If it is not, `MERIT ≠ g(s) − ḡ` and **this session's entire object is
  mis-specified**; the instrument is declared BROKEN and nothing is read.
* **(G-ID) — this session's own decomposition identity.**
  `max_t | (LINEAR + CURVE + STEP)(t) − MERIT(t) | ≤ 1e-6 MW`, per year. If it does not hold to
  machine precision the decomposition is not exact and nothing may be attributed with it.

**If any leg fails, the instrument is declared BROKEN, the failure is published, and NOTHING in
§2–§4 is read.** This is miso-238 §0's discipline, adopted whole.

## 2. THE DECOMPOSITION — fixed here, before any number, with zero free parameters

Everything below is on **PJM**, per year, over the `ok` hours. Write `n(t) = Σ_k 1[s(t) > δ_k] ∈
{0,…,8}` for the band count, and `G_k = Σ_{j≤k} b̄_j` (so `G₇` is `g`'s cap and `0` its floor).

### 2a. Three counterfactual responses to the SAME realized spread series

| object | definition | zero-DOF because |
|---|---|---|
| **`g_step`** | `g(s(t))` — the actual ladder. Discrete, quantile-placed, bounded. | it *is* the committed reconstruction |
| **`g_lin`** | `α + β·s(t)`, `β` the OLS slope of `g_step` on `s` over the `ok` hours | an OLS projection is not a tunable |
| **`g_cont`** | the **piecewise-linear interpolant through the ladder's own realized level-set knots** `(x̄_n, g_n)`, `n = 0…8`, where `x̄_n` = mean of `s` over the hours with band count `n` and `g_n` = `g`'s value there (`g_0 = 0`, `g_8 = G₇`); clamped at `0` below `x̄_0` and at `G₇` above `x̄_8` | every knot is determined by the frozen ladder and the realized spread; nothing is fitted, chosen or swept |

`g_cont` is continuous and monotone and **shares `g`'s exact bounds and threshold placement**;
what it does *not* share is `g`'s **discreteness**. That is the whole design: it isolates
property (b) from properties (a) and (c).

### 2b. The three channels

    LINEAR(t) = β·( s(t) − s̄ )
    CURVE(t)  = ( g_cont(t) − ḡ_cont ) − LINEAR(t)
    STEP(t)   = ( g_step(t) − ḡ_step ) − ( g_cont(t) − ḡ_cont )

    MERIT(t)  =  LINEAR(t) + CURVE(t) + STEP(t)      (exact; G-ID verifies it)

| channel | the handoff's candidate property it isolates |
|---|---|
| **LINEAR** | **(d) the regressor is confounded** — `g`'s *linear* response to the model's own merit spread `s`, in the part of `s` that removing the measured spread `p1` does **not** remove (§0d(3)). If this dominates, the carrier is not `g`'s nonlinearity at all. |
| **CURVE** | **(a) boundedness** + **(c) `δ_k` placement** — the shape of a *continuous* ladder with the same bounds and thresholds. Separated into (a) and (c) by §3b's hour partition. |
| **STEP** | **(b) K=8 step granularity** — precisely "`g` against its own continuous interpolant", the handoff's own test for (b). |

**Every statistic is `γ`, which §0d(4) proves is linear in the series, so each channel's `γ`
sums EXACTLY to `γ_MERIT`. Zero free parameters: no threshold, no weight, no sweep.**

**THIS IS A DIAGNOSTIC DECOMPOSITION OF A COMMITTED RECONSTRUCTION, NOT A PROPOSED MECHANISM.**
`g_lin` and `g_cont` are measurement instruments evaluated on the committed series — exactly as
miso-237's purge was a diagnostic projection and miso-238's MERIT/ENVELOPE/INTERACT split was a
diagnostic algebra. **Nothing here proposes replacing, smoothing, re-deriving, damping or
re-weighting the ladder, and §5.2 forbids a successor from doing so on these numbers.**

### 2c. Declared robustness twin — fixed here, reported, NEVER gating

The `LINEAR` / (`CURVE`+`STEP`) split is **choice-free**: it depends on `β` alone. Only the
`CURVE` ↔ `STEP` subdivision depends on which continuous interpolant is used. So a twin is
declared in advance and reported beside the primary:

> **`g_cont′`** — the piecewise-linear interpolant through the **ladder's own thresholds**,
> knots `(δ_k, G_{k−1} + b̄_k/2)` for `k = 0…7` (the standard mid-jump value of a staircase) plus
> the endpoint knots `(min s, 0)` and `(max s, G₇)`.

If the primary and the twin disagree on the §3a sub-verdict in any year, **the sub-verdict is
published as FRAGILE and closes nothing.** The top-level §3a verdict is unaffected by the twin
by construction, and this is stated before the numbers.

## 3. Q-A — WHICH PROPERTY? The decision rule, fixed ex ante

`γ(r)` = the **partial** OLS coefficient on `z_own_net_load` in `r ~ [1 | z_own_net_load |
z_own_VRE]`, `r = ols_resid(·, p1)` — miso-237's estimator via miso-238 ADDENDUM §2, in MW per
z-score. Shares `σ_LIN = γ_LINEAR/γ_MERIT`, `σ_CURVE`, `σ_STEP`; they sum to 1 exactly.

**GATED SEAM: PJM only** — the only seam where `MERIT = g(s) − ḡ` holds (G-X0) and the only one
above miso-238's floors. SPP, South and Manitoba are **not gated and carry no verdict**: their
export legs are live, so `MERIT` is a difference of two ladders there and this session's object
does not exist for them; anything reported for them is labelled as such and is never quoted.

### 3a. The verdict ladder — read in this order, all three years, or MIXED

1. **REGRESSOR-CONFOUNDED — property (d)** iff `σ_LIN ≥ 0.50` in **all three years**.
   ⇒ the carrier is not `g`'s nonlinearity but the mismatch between the merit spread `s` and the
   regressor `p1`; the successor question moves to the model's own MISO_external price formation.
2. **LADDER-NONLINEARITY** iff `σ_CURVE + σ_STEP ≥ 0.50` in **all three years**. Then, and only
   then, the sub-verdict:
   * **DISCRETENESS — property (b)** iff `σ_STEP / (σ_CURVE + σ_STEP) ≥ 0.50` in all three years;
   * else **SHAPE**, sub-adjudicated on `γ_CURVE` by §3b's hour partition:
     * **BOUNDEDNESS — property (a)** iff `(γ_CURVE|FLOOR + γ_CURVE|CAP) / γ_CURVE ≥ 0.50` in all
       three years;
     * **PLACEMENT — property (c)** iff `γ_CURVE|INTERIOR / γ_CURVE ≥ 0.50` in all three years;
     * else **MIXED-SHAPE**.
3. **MIXED** otherwise — reported as mixed, closing and licensing nothing.

**ABSOLUTE FLOORS, fixed here so a ratio of two negligible numbers cannot decide anything** (the
role miso-238's `|γ| ≥ 200` played):
* the top-level rule is read only where `|γ_MERIT| ≥ 200` MW/z in all three years;
* the **sub**-verdict at step 2 is read only where `|γ_CURVE + γ_STEP| ≥ 100` MW/z in all three
  years, and the SHAPE sub-verdict only where `|γ_CURVE| ≥ 100` MW/z in all three years.
Below a floor the corresponding verdict reads **NOT MEANINGFUL** and nothing attaches.

### 3b. The hour partition — exact, and used only inside step 2

Because `γ(r) = Σ_t w_t r_t` for a fixed `w` (§0d(4)), `γ` splits **exactly** over any partition
of the `ok` hours. Partition by band count:
**FLOOR** `n = 0` · **CAP** `n = 8` · **INTERIOR** `1 ≤ n ≤ 7`, with the full 9-row profile
reported. FLOOR and CAP are exactly the hours where `g` is **clipped by its own bounds**, which
is what "boundedness" means in the reconstruction; INTERIOR is where only `δ_k` placement and
granularity can act.

## 4. Q-C — property (d), second limb: the spread entered NON-PARAMETRICALLY

The handoff's own test for (d): *"re-running gamma with the spread entered non-parametrically
(miso-237's P2 block) instead of linearly."* Adopted verbatim.

`γ_np = γ( resid( MERIT | [1 | ventile dummies of p1] ) )`, with miso-237's
`ventile_dummies(·, bins=20)` — 19 dummies, the same non-parametric price class miso-237's P2
used. **GATED on PJM**, decision rule fixed here:

* **SURVIVES** iff `|γ_np| ≥ 0.50 · |γ_MERIT|` in all three years ⇒ the response is **not** a
  functional-form misspecification of the measured spread `p1`, and (d) is not closed by this
  limb.
* **COLLAPSES** iff `|γ_np| ≤ 0.25 · |γ_MERIT|` in all three years ⇒ it is.
* **MIXED** otherwise.

**Two tautology checks, REPORTED, that validate the framing rather than adjudicate it:**
`γ` of `resid(MERIT | [1 | band-count dummies])` must be **exactly 0** (`MERIT` is measurable
w.r.t. `n(t)` by §0d(2)); and `γ` of `resid(MERIT | [1 | ventile dummies of s])` is reported
beside it. Neither can move a verdict and both are labelled.

**Census, REPORTED and NEVER GATED** (miso-238 §3a's discipline): the band-count histogram, the
level-set knot table `(x̄_n, g_n)`, `b̄_k`, `G_k`, `δ_k`, `β`, `σ(g_step)`, `σ(g_cont)`,
`σ(g_lin)`, and `γ_marginal` beside every `γ_partial` (miso-238 ADDENDUM §2's disclosure).

## 5. What this session cannot do, stated before the numbers

1. **No lever is proposed and none can be licensed here.** A verdict names which *property of a
   frozen, committed step function* carries a measured response. It does not charter a mechanism,
   size one, name a field, or arm anything.
2. **NOTHING HERE LICENSES TOUCHING THE LADDER — WHATEVER THE ANSWER.** The PJM and SPP `δ_k`
   ladders are derived, frozen and pinned to their derives by test (rule 23
   `[R-FROZEN-DERIVE]`); the `(month × hod)` deliverability envelope is a measured input (rule 14
   `[R-ACCURATE]`). **No re-derive, no damping factor, no smoothing of the steps, no change of
   `K`, no re-spacing of `δ_k`, no envelope change** — a factor swept against any residual is the
   rule 1 `[R-STRUCT]` fitted mechanism, and "the attribution landed on the ladder" is
   **not** a licence, exactly as miso-238 PREREG §5.2 fixed **in advance for exactly the outcome
   it got**. This binds whatever §3 and §4 return and it is fixed here before the numbers.
   In particular a **DISCRETENESS** or **PLACEMENT** verdict is *not* a licence to raise `K` or
   re-derive `δ_k`, and a **BOUNDEDNESS** verdict is *not* a licence to raise the interface limit
   or the envelope.
3. **Nothing here is a tuning target.** No successor may size, scale, tune or select any
   mechanism to make a modelled `γ`, share or channel value land on a number produced by this
   session (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`) — the restriction miso-236 ADDENDUM §A,
   miso-237 PREREG §4 and miso-238 PREREG §5.3 fixed for theirs. miso-236's 328.6 / 341.7 /
   207.5 MW sizing stays **un-targetable** and is not re-quoted as a target.
4. **No re-test of an adjudicated cell** (rule 28(a) DO-NOT-REDO). The saturation hypothesis is
   **REFUTED** (miso-238) and is not re-tested — §3b's FLOOR/CAP partition is a partition of
   `γ_CURVE`, a different object from miso-238's ENVELOPE/INTERACT channels, and it cannot and
   does not re-open that verdict. Also untouched: `miso_south_firm_export_block` **G**,
   `miso_south_export_ladder_rt_tail` **R**, `internal_congestion_split` **G**,
   `vre_reference_rate_curtailment_grossup` **K**, `measured_interface_limits` **R**,
   `miso_rdt_measured_limit` **R**, `miso_south_gas_delivered_cost_basis` **R**; South's
   neighbour-state route stays **CLOSED**, Manitoba stays **CLOSED as already-armed**, the
   item-1 form question stays **ANSWERED** and its SPP object stays **NOT CHARTERED**; the
   `(month × hod)` template hypothesis stays **REMOVED**; the PJM import/export signal asymmetry
   stays **CLOSED FOR PJM** and is not re-opened as a PJM question (§0d(1) *uses* that closure,
   it does not re-litigate it).
5. **No cell verdict moves in either direction.** This session tests no mechanism, so rule 28(b)
   attaches only in its **evidence-appending** form (the miso-206 / miso-234 / miso-235 /
   miso-236 / miso-237 / neiso-100 / caiso-206 no-solve precedent). Evidence is appended to
   `seam_neighbour_hourly_ladder` and `seam_flow_envelopes` in **MISO's shard only** (rule 25).
6. **No promotion, no decertification.** MISO is CALIBRATED today and this session does not trade
   a passing gate for anything (miso-227 promotion rule).
7. **C3c is untouched** and stays the designated frontier (2026-07-20). No LP is authorized there
   under this handoff and none is sought.
8. **The model side is a RECONSTRUCTION** (miso-235's four-seam form, harness
   `corr(recon, committed)` +0.9845 / +0.9745 / +0.9839) and is labelled as one everywhere. 2024
   remains the loosest year and every 2024 reading is reported with that stated.
9. **This session claims no miso-238 verdict as its own** (§0b). It republishes miso-238's column
   as its own §1 provenance leg, with the missing-artifact disclosure attached.

## 6. Deliverables

* miso-238 ADDENDUM §2's declared repair applied to
  `scripts/probes/_miso238_pjm_seam_channel_attribution_phase0.py`, and
  `results/calibration/_miso238_pjm_seam_channel_attribution_phase0.json` regenerated (§0b).
* `scripts/probes/_miso239_merit_ladder_property_attribution_phase0.py` →
  `results/calibration/_miso239_merit_ladder_property_attribution_phase0.json`.
* `results/calibration/FINDING-miso239-*.md` carrying **every number this session will ever
  cite**.
* Evidence appended to MISO's matrix shard + the `§5.4` queue stamp (rule 25, rule 28(b)
  evidence form).
* `docs/calibration-log/miso.md` entry.

## 7. Governance declared in advance

Rule 1 `[R-STRUCT]`: no mechanism is judged by a residual; nothing is proposed or selected, and
every number this session produces is declared un-targetable in §5.3 before it is computed.
Rule 12 `[R-PARALLEL]`: no LP is solved; nothing runs on CI. Rule 13 `[R-MEASURED]`: measurement
only — no input changes and no measured outcome enters any solve. Rule 14 `[R-ACCURATE]`: no
input changed; §5.2 forbids touching the measured envelope. Rule 15 `[R-DASHBOARD]`: no run
produced, so nothing registered or pruned; MISO keeps exactly one registered run and the
keeper's `hourly/` sidecars stay committed. Rule 17 `[R-FLOOR-WINDOW]`: no floor added. Rule 19
`[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged; the decomposition
carries **zero** free parameters. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO holds no
`complete` marker. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run, and §5.2 forbids one whatever
the verdict. Rule 24 `[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO's shard,
section and lane only. Rule 27 `[R-PUSH]`: every pushed blob verified against local; the
miso-238 probe repair is an Edit-tool change to on-disk bytes, not a regenerated full-file push.
Rule 28: queue item 1 named in §0/§2; evidence-append form only. Rule 29 `[R-SCREEN]`: clause 0
in full — zero-LP phase 0 first, and this session is that phase 0.
