# PREREG miso-238 — WHICH CHANNEL of the PJM seam carries the model's spurious own-net-load response, and which carries the REMAINDER of its excess price alignment? Queue items 3 and 2, on ONE exact decomposition

**Pushed BEFORE any adjudicating quantity is computed.** miso-234 did not push a
pre-registration and correctly forfeited its right to close or re-open anything on its own
numbers; miso-235, miso-236 and miso-237 each did, and each closed a queue leg on its own rule.
This session follows miso-235/236/237.

**Keeper `2026-09-07-miso-233-spp-hourly`** (bundle `results/calibration/miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF 41/2. **MISO HAS NO FAILING
GATE**, and there is no rubric failure anywhere in the program, so nothing here targets one.
Rule 22: 2023–2025 only; MISO holds no `complete` marker and no out-of-training year will be
solved, scored or registered. MISO carries exactly ONE registered run (rule 15).

**ZERO LP IS PLANNED.** No `ScenarioConfig` field is created or armed, no bundle is produced, no
run is registered or pruned, the keeper is not replayed and not touched. If a measurement below
licensed a screen, that screen would be chartered in a successor with its own PREREG — it is
**not** chartered here.

---

## 0. Lever-queue selection (rule 28(a))

This session takes the handoff's **item 3** together with its **item 2**, because the handoff
itself says they may be one object and licenses taking both on one instrument:

> **item 3:** *"THE PJM OVER-TRANSMISSION DEFECT, which miso-237 minted and nobody has
> attributed. The model's PJM seam residual carries a LARGE, STABLE, NEGATIVE own-net-load
> response (-866.2/-1043.4/-843.5 MW per z-score) that the real seam does not have
> (+47.4/-361.1/+271.5, sign-unstable and 2-18x smaller). WHY does the model's PJM tie fall in
> high-MISO-net-load hours after the linear spread is removed? The saturation hypothesis (the
> deliverability envelope binding in exactly those hours) is NAMED AND UNTESTED — test it at
> zero LP from the committed sidecars before anything else. This is the same seam as item 2 and
> may be one object; if you take both, say so and use one instrument."*

> **item 2:** *"THE OTHER HALF OF PJM'S PRICE-ALIGNMENT DEFECT … Roughly half is still
> unaccounted for. MEASURE THE REMAINDER, do not re-test the half that is done and do not
> re-test the (month x hod) template (miso-236 removed it). Zero-LP, and the miso-237 probe is
> the instrument — extend it, and keep its two-leg provenance gate."*

**They are taken as ONE OBJECT and answered by ONE decomposition**, stated in §2. Handoff items
1 (the SPP quantity-side charter), 4 (Manitoba determinism), 5 (CC_REGULAR shape) and 6 (the C3c
charter) are **not** taken and stay exactly where they are filed. In particular **nothing here
re-tests** the half of item 3 miso-237 already did (the own-state purge, `phi` PARTIAL), the
`(month × hod)` template hypothesis (miso-236 REMOVED it), or the item-1 form question
(miso-237 ANSWERED it).

### 0a. Why a CHANNEL decomposition is the right instrument, and why it can be exact

miso-236 removed the `(month × hod)` envelope template as the *explanation* for the model's
excess PJM residual price alignment by showing the **real** seam's residual is a template too.
miso-237 then supplied **half a cause** — purging MISO's own state removes 36 / 62 / 50 % of the
excess — and minted the object this session attributes: a **large, stable, negative** own-net-load
response in the model's PJM residual that the measured seam does not carry.

Neither predecessor asked **through which of the reconstruction's own terms** that response
arrives. The reconstruction has exactly two kinds of input and they are separable by algebra,
not by assumption (§0c) — so the question has an **exact, parameter-free** answer, and it
discriminates the handoff's NAMED hypothesis (the deliverability envelope binding) from its
unnamed alternative (the merit ladder's own saturation against the spread).

### 0b. Basis discipline (carried from miso-234 §0a / miso-235 §0b / miso-236 §0b / miso-237 §0b — it bit a first draft)

* **Indiana-hub RT** — `_miso224_floor_anatomy_phase0.actual_zone_price(year)["MISO-Indiana"]`,
  `values="rt"`. The lane's scored basis. Used here to build the finite-hour `ok` mask
  (byte-identically to miso-236/237, so the hour set is the predecessors') **and** as the price
  `P` of the alignment column in §3 — the same series miso-235 §4b and miso-237 ADDENDUM §A used.
* **Indiana-hub DA** — the basis `MISO_SEAM_LADDER_BY_YEAR` was Q-Q derived against, and the
  basis of **every regressor and every merit signal** below, exactly as miso-235 §3, miso-236 and
  miso-237 fixed it.

They correlate only +0.402 / +0.424 / +0.553 and are never interchanged. miso-232's measured
decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here.

### 0c. What was established BEFORE this PREREG was written — CODE READING only, disclosed not claimed

Four facts, all **code reading** of committed source and a committed probe. **No adjudicating
quantity is among them and none is a statistic about a seam**, which is the miso-237 §0c standard.

1. **The reconstruction's exact algebraic form** (`_miso237_price_representation_vs_state_phase0.py`,
   miso-235's four-seam form). With `K = SEAM_FLOW_TRANCHES = 8`,
   `w = interface_limit_mw / K` (PJM 7,300 / 8 = 912.5 MW):

       imp(t) = Σ_k  m_k(t) · b_k(t)          exp(t) = Σ_k  q_k(t) · c_k(t)
       model_net(t) = imp(t) − exp(t)

   `m_k(t) = 1[ merit_signal(t) > δ_k^imp ]`, `q_k(t) = 1[ p_bus(t) < λ_k^exp ]`,
   `b_k(t) = clip(env_i(t) − k·w, 0, w)`, `c_k(t) = clip(env_e(t) − k·w, 0, w)`.

2. **Every `m_k`, `q_k` is a pure function of PRICE; every `b_k`, `c_k` is a pure function of the
   ENVELOPE.** No term mixes them except by multiplication. That is what makes §2's split exact
   rather than a modelling choice.

3. **The envelope is a deterministic `(month × hod)` p90 TEMPLATE**
   (`data.eia930.envelopes.measured_seam_import_envelope`): 12 × 24 = 288 distinct values per
   seam per year, broadcast onto the fixed 8,760 grid. It carries no hour-specific information
   beyond its month and hour-of-day.

4. **THE IMPORT AND EXPORT LEGS CLEAR ON DIFFERENT SIGNALS, and this asymmetry is in the armed
   keeper.** Under `miso_seam_neighbour_hourly_ladder` (K, miso-232) and
   `miso_seam_neighbour_hourly_spp` (K, miso-233) the PJM and SPP **import** legs clear on the
   hourly **SPREAD** `p_bus − p_neighbour`; **every export leg, on every seam, still clears on the
   `p_bus` LEVEL** against the fixed Q-Q `MISO_SEAM_LADDER_BY_YEAR`, as do both legs of South and
   Manitoba. So `ols_resid(·, spread)` removes the import leg's own price signal and does **not**
   remove the export leg's. This is a **code fact stated in advance**, not a defect claim and not
   a proposed change; §3 measures whether it matters and §5.1 forbids proposing anything about it
   here.

---

## 1. The provenance gate — reproduce BOTH predecessors before reading anything new

Fixed ex ante, and nothing in §2–§4 is read or published unless **all four** legs clear. This is
the handoff's binding instruction ("BUILD A PROVENANCE GATE INTO ANY NEW INSTRUMENT, and make it
reproduce the PREDECESSOR's published quantity in the PREDECESSOR's OWN METRIC") and miso-237's
two-leg gate is the template.

* **(G-P1)** miso-235's `sigma_measured_mw` and `sigma_resid_measured_mw`, all four seams × three
  years (24 values), recomputed on this session's code path, agree with the committed
  `_miso235_seam_variance_decomposition_phase0.json` to **≤ 0.5 MW**.
* **(G-P2)** miso-237's `own_net_load_coef_resid_model` and `own_net_load_coef_resid_measured`,
  all four seams × three years (24 values), agree with the committed
  `_miso237_price_representation_vs_state_phase0.json` to **≤ 0.5 MW per z-score**. This is the
  object this session attributes, reproduced in miso-237's own metric before it is decomposed.
* **(G-P3)** miso-237's ADDENDUM §A alignment column — `alignment_model`,
  `alignment_model_purged`, `alignment_measured`, `alignment_measured_purged`, all four seams ×
  three years (48 values) — agrees with the same committed JSON to **≤ 0.001**.
* **(G-ID)** **THE DECOMPOSITION IDENTITY.** The three channels of §2 sum to `model_net` up to an
  additive constant, in every seam and year:
  `max_t | (MERIT + ENVELOPE + INTERACT)(t) − model_net(t) − κ | ≤ 1e-6 MW`, with
  `κ` the constant `Σ_k m̄_k b̄_k − Σ_k q̄_k c̄_k`. **If this does not hold to machine precision the
  decomposition is not exact and nothing may be attributed with it.**

**If any leg fails, the instrument is declared BROKEN and NOTHING below is read or published.**

## 2. THE DECOMPOSITION — fixed here, before any number

For each seam and year, on the `ok` mask, write each band-product as mean-plus-deviation
(`x̄` = the annual mean over the `ok` hours, `x̃ = x − x̄`):

    m_k b_k = m̄_k b̄_k  +  m̃_k b̄_k  +  m̄_k b̃_k  +  m̃_k b̃_k

and collect the three non-constant groups, import leg minus export leg:

| channel | definition | what it is |
|---|---|---|
| **MERIT** | `Σ_k m̃_k(t)·b̄_k − Σ_k q̃_k(t)·c̄_k` | a pure function of the two PRICES, at fixed annual-mean band weights. Carries the merit ladder's own shape — including its **saturation against the spread**, since `Σ_k m_k b̄_k` is a bounded monotone step function. |
| **ENVELOPE** | `Σ_k m̄_k·b̃_k(t) − Σ_k q̄_k·c̃_k(t)` | a pure `(month × hod)` TEMPLATE, at fixed annual-mean merit frequencies. Carries the deliverability envelope's own variation and nothing else. |
| **INTERACT** | `Σ_k m̃_k(t)·b̃_k(t) − Σ_k q̃_k(t)·c̃_k(t)` | the product of both deviations — the envelope **binding differently in different price hours**, which is the handoff's named hypothesis in its purest form. |

Each channel is additionally reported split into its **import** and **export** legs (six
sub-channels), because §0c(4) records that the two clear on different signals.

**Every statistic below is (i) computed from an OLS residual on the single linear price
regressor `p1` and (ii) a covariance with a fixed series.** Both operations are linear and both
annihilate additive constants, so **each statistic decomposes EXACTLY and ADDITIVELY across the
three channels**. G-ID verifies the identity numerically before anything is attributed.
**Zero free parameters**: the split has no tunable, no threshold and no fitted weight.

**This is a DIAGNOSTIC DECOMPOSITION OF A COMMITTED RECONSTRUCTION, not a proposed mechanism.**
Nothing here proposes adding, removing, damping or re-weighting any term in the model, exactly as
miso-237's purge was a diagnostic projection and its `P2`/`P3` were measurement instruments.

## 3. Q-A — ITEM 3. Which channel carries the model's spurious own-net-load response?

`γ(r) = cov(r, z_own_nl)` with `z_own_nl` the z-scored MISO own net load (`Demand − Wind − Solar`
from EIA-930 BALANCE, the miso-236/237 block's first member) and `r = ols_resid(·, p1)`, so `γ` is
in **MW per z-score** and is miso-237's `own_net_load_coef_resid_model` exactly (G-P2 proves it).
Reported per channel and per sub-channel, with `γ_MERIT + γ_ENVELOPE + γ_INTERACT = γ_model`.

**GATED SEAM: PJM only** — the seam item 3 names. SPP, South and Manitoba are **reported, not
gated**.

**DECISION RULE, fixed ex ante, on all three years:**

* **ENVELOPE-DRIVEN — the handoff's saturation hypothesis is CONFIRMED as the carrier** iff
  `(γ_ENVELOPE + γ_INTERACT) / γ_model ≥ 0.50` in **all three years**.
* **MERIT-DRIVEN — the saturation hypothesis is REFUTED as the carrier**, and the object is the
  merit ladder's own shape against the spread, iff `γ_MERIT / γ_model ≥ 0.50` in **all three
  years**.
* **MIXED** otherwise — reported as mixed, closing and licensing nothing.

**ABSOLUTE FLOOR, fixed here so a ratio of two negligible numbers cannot confirm anything** (the
role miso-237's `ΔR² ≥ 0.05` floor played): the rule is read only where
`|γ_model| ≥ 200 MW per z-score` in all three years; below that the seam reads
**NOT MEANINGFUL** and no verdict attaches.

**What each verdict means for a successor, fixed here before the numbers so it cannot be written
to fit one:**

* **ENVELOPE-DRIVEN** ⇒ the object is the measured `(month × hod)` deliverability envelope's
  interaction with the merit ladder on the PJM seam. It **names an object for a successor's
  charter and charters nothing** — no field, no size, no re-derive, no damping factor.
* **MERIT-DRIVEN** ⇒ the object is the ladder's own saturation/step shape against the spread. The
  same restriction applies with full force: the PJM and SPP `delta_k` ladders are derived, frozen
  and **pinned to their derives by test** (rule 23 `[R-FROZEN-DERIVE]`), and **nothing this
  session can measure licenses a re-derive or a damping factor**, exactly as miso-237 PREREG §5.2
  and ADDENDUM §A fixed and as this PREREG §5.2 restates.
* **MIXED** ⇒ neither object is named and item 3 stays exactly where miso-237 left it.

### 3a. The saturation census — REPORTED, NOT GATED, and it is evidence for the verdict's story, never for the verdict

Because "the envelope binds" has an exact meaning in the reconstruction — `imp(t) = env_i(t)` iff
**all `K = 8` import bands are in merit** — the following are reported per seam and year to make
whichever verdict lands legible. **No bar attaches to any of them and none can move a §3 verdict.**

* `sat_share` — the fraction of `ok` hours with all 8 import bands in merit.
* `mean z_own_nl` in saturated vs unsaturated hours, and `sat_share` restricted to the top decile
  of `z_own_nl`.
* `corr(env_i, z_own_nl)` and `corr(env_i, P_RT)` — whether the envelope template itself is low in
  high-own-net-load hours, which is the mechanism the word "saturation" is standing in for.
* `γ` and the alignment of the **export leg alone**, given §0c(4)'s asymmetry.

## 4. Q-B — ITEM 2. Which channel carries the REMAINDER of the excess price alignment?

miso-237 measured the model's PJM residual alignment `|corr(r_model, P_RT)|` at
0.3243 / 0.3143 / 0.2858, its own-state-purged value at 0.2530 / 0.1967 / 0.1750, and the measured
seam's purged value at 0.1745 / 0.0830 / 0.1404 — leaving roughly half the excess unaccounted.
**That remainder is this leg's object.** Nothing here re-computes `phi` as an adjudication or
re-tests the half miso-237 did; G-P3 reproduces its column only as a provenance leg.

The alignment **numerator** `a(r) = cov(r, P_RT) / σ(P_RT)`, in MW, is additive across channels
where `|corr|` is not, so `a` is the decomposed statistic and `|corr| = |a| / σ(r)` is reported
beside it as the published quantity. `a` is computed on **both** the raw residual and the
own-state-**purged** residual `r_purged = r − proj_{S_own}(r)` (miso-237 ADDENDUM §A's projection,
which is linear and therefore preserves the decomposition), for the model side **and** the
measured side.

**GATED SEAM: PJM only.** **DECISION RULE, fixed ex ante, on all three years, applied to the
PURGED model residual** (the remainder is what is left after miso-237's half):

* **ENVELOPE-DRIVEN REMAINDER** iff `(a_ENVELOPE + a_INTERACT)^purged / a_model^purged ≥ 0.50` in
  **all three years**.
* **MERIT-DRIVEN REMAINDER** iff `a_MERIT^purged / a_model^purged ≥ 0.50` in **all three years**.
* **MIXED** otherwise.

**ABSOLUTE FLOOR, fixed here:** read only where `|a_model^purged| ≥ 100 MW` in all three years;
below that the seam reads **NOT MEANINGFUL**.

**And a disclosure fixed in advance:** the measured seam's own purged alignment is the control and
is reported beside every model value, exactly as miso-237 ADDENDUM §A did — because the question
is which channel carries the model's **EXCESS**, and an excess is only visible against the
measured side. A channel share is never read as a defect on its own.

## 5. What this session cannot do, stated before the numbers

1. **No lever is proposed and none can be licensed here.** A verdict names which *channel* of a
   committed reconstruction carries a measured response; it does not charter a mechanism, size
   one, name a field, or arm anything. **Nothing about §0c(4)'s import/export signal asymmetry is
   proposed, and it is not a defect claim** — it is a code fact recorded so §3/§4's sub-channel
   split is legible.
2. **No damping factor, no re-derive, no envelope change.** The PJM and SPP `delta_k` ladders are
   derived, frozen and pinned to their derives by test (rule 23 `[R-FROZEN-DERIVE]`), and the
   `(month × hod)` deliverability envelope is a measured input (rule 14 `[R-ACCURATE]`). A factor
   swept against any residual is the rule 1 `[R-STRUCT]` fitted mechanism. **This binds whatever
   §3 and §4 return**, and it is fixed here before the numbers.
3. **Nothing here is a tuning target.** No successor may size, scale, tune or select any mechanism
   to make a modelled `γ`, `a`, `|corr|` or channel share land on a value produced by this session
   (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`), the same restriction miso-236 ADDENDUM §A and
   miso-237 PREREG §4 fixed for their numbers. miso-236's 328.6 / 341.7 / 207.5 MW sizing stays
   un-targetable and is not re-quoted as a target here.
4. **No re-test of an adjudicated cell** (rule 28(a) DO-NOT-REDO): `miso_south_firm_export_block`
   **G**, `miso_south_export_ladder_rt_tail` **R**, `internal_congestion_split` **G**,
   `vre_reference_rate_curtailment_grossup` **K**, `measured_interface_limits` **R**,
   `miso_rdt_measured_limit` **R**, `miso_south_gas_delivered_cost_basis` **R**. Where a number
   here touches one it **corroborates** it; the standing adjudication remains the finding. South's
   neighbour-state route stays **CLOSED** (miso-236 D-4), Manitoba stays **CLOSED as
   already-armed** (miso-235 §3), the item-1 form question stays **ANSWERED** (miso-237 §2) and
   its SPP object stays **NOT CHARTERED**; none is re-opened.
5. **No cell verdict moves in either direction.** This session tests no mechanism, so rule 28(b)
   attaches only in its **evidence-appending** form (the miso-206 / miso-234 / miso-235 /
   miso-236 / miso-237 / neiso-100 / caiso-206 no-solve precedent). Evidence is appended to
   `seam_flow_envelopes` and `seam_neighbour_hourly_ladder` in **MISO's shard only** (rule 25).
6. **No promotion, no decertification.** MISO is CALIBRATED today and this session does not trade
   a passing gate for anything (miso-227 promotion rule).
7. **C3c is untouched** and stays the designated frontier (2026-07-20). Its charter needs a new
   admissible measured identification and an owner ruling; no LP is authorized there under this
   handoff and none is sought.
8. **The model side is a RECONSTRUCTION** (miso-235's four-seam form, harness
   `corr(recon, committed)` +0.9845 / +0.9745 / +0.9839) and is labelled as one everywhere. 2024
   remains the loosest year and every 2024 reading is reported with that stated.

## 6. Deliverables

* `scripts/probes/_miso238_pjm_seam_channel_attribution_phase0.py` →
  `results/calibration/_miso238_pjm_seam_channel_attribution_phase0.json`.
* `results/calibration/FINDING-miso238-*.md` carrying **every number this session will ever cite**.
* Evidence appended to MISO's matrix shard + the §5.4 queue stamp (rule 25, rule 28(b) evidence
  form).
* `docs/calibration-log/miso.md` entry.

## 7. Governance declared in advance

Rule 1 `[R-STRUCT]`: no mechanism is judged by a residual; nothing is proposed or selected, and
every number this session produces is declared un-targetable in §5.3 before it is computed.
Rule 12 `[R-PARALLEL]`: no LP is solved; nothing runs on CI. Rule 13 `[R-MEASURED]`: measurement
only — no input changes and no measured outcome enters any solve. Rule 14 `[R-ACCURATE]`: no input
changed; the deliverability envelope is a measured input and §5.2 forbids touching it. Rule 15
`[R-DASHBOARD]`: no run produced, so nothing registered or pruned; MISO keeps exactly one
registered run and the keeper's `hourly/` sidecars stay committed. Rule 17 `[R-FLOOR-WINDOW]`: no
floor added. Rule 19 `[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged, and
the decomposition itself carries **zero** free parameters. Rule 22 `[R-HOLDOUT]`: 2023–2025 only;
MISO holds no `complete` marker. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run. Rule 24
`[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO's shard, section and lane only.
Rule 27 `[R-PUSH]`: every pushed blob verified against local. Rule 28: queue items named in §0;
evidence-append form only. Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP phase 0 first, and
this session is that phase 0.
