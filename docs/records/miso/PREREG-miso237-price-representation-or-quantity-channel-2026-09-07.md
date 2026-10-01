# PREREG miso-237 — is the seam-state channel a PRICE-REPRESENTATION deficiency or a QUANTITY-SIDE channel? The form question miso-236 named, and the unused own-state input, on ONE instrument

**Pushed BEFORE any adjudicating quantity is computed.** miso-234 did not push a
pre-registration and correctly forfeited its right to close or re-open anything on its own
numbers; miso-235 and miso-236 each did, and each closed a queue leg on its own rule. This
session follows miso-235/236.

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

This session takes the handoff's **item 1's FIRST QUESTION** — which the handoff states is *"still
zero-LP and it is a FORM question, not a data question"* — together with its **item 2**, because
**one instrument answers both**: each asks what channel a seam's measured state-driven variation
actually travels through, on the same nested decomposition of the same committed artifacts.

The handoff's instruction on item 1 is the charter and is quoted so it binds:

> *"THE FIRST QUESTION IS STILL ZERO-LP AND IT IS A FORM QUESTION, NOT A DATA QUESTION: what
> admissible MECHANISM does this license? Read miso-236 §6.3 before answering — 'non-price' is
> defined OPERATIONALLY there (orthogonal to a single hub-pair spread), NOT as economically
> non-price, and neighbour net load plausibly moves the tie through the neighbour's OWN scarcity
> and internal congestion. So the candidate may be a BETTER NEIGHBOUR PRICE REPRESENTATION rather
> than a new non-price input, and assuming the latter is the error miso-236 exists to prevent.
> Settle the form at zero LP before proposing."*

And on item 2:

> *"MISO'S OWN STATE IS AN UNUSED INPUT, NOT A MISSING ONE … This is CHEAPER than item 1 — it
> needs no new data at all — and it has never been attributed. Do it at zero LP first."*

**§2 settles item 1's form question and §3 attributes item 2, on one nested-block instrument.**
Handoff items 3 (PJM residual price alignment), 4 (Manitoba determinism), 5 (the C3c charter) and
6 (CC_REGULAR shape) are **not** taken and stay where they are filed.

### 0a. Why this question comes BEFORE any candidate — the miso-236 §6.3 trap, stated exactly

miso-236's `ΔR²_A` is the share of the measured seam flow's variation that neighbour state explains
**over and above a SINGLE LINEAR hub-pair spread**. "Non-price" there is an *operational* label for
"orthogonal to that one regressor", and miso-236 §6.3 says so against its own interest. It is
therefore **not yet established** that the channel is economically non-price. Two mechanism classes
are consistent with the same number and they are **not interchangeable**:

* **A QUANTITY-SIDE channel** — the neighbour's state moves the tie through something no price
  representation can reach (reserve deployment, non-economic schedules, tie limits), so an
  admissible mechanism is a new measured quantity-side input.
* **A PRICE-REPRESENTATION deficiency** — the neighbour's state moves the tie *through the
  neighbour's own price*, and the single linear spread simply cannot express it (the response is
  non-linear, or the two legs of the spread act differently, or the neighbour's scarcity shows in
  its price level rather than in the difference). Then the admissible mechanism is a **better price
  representation**, and building a quantity-side input would be **fitting a proxy for a price the
  model already has access to** — the rule 1 `[R-STRUCT]` error of reaching a number through a
  mechanism that is not the real one.

**This session distinguishes them, and it does so BEFORE anything is proposed.** Nothing here
charters either.

### 0b. Basis discipline (carried from miso-234 §0a / miso-235 §0b / miso-236 §0b — it bit a first draft)

* **Indiana-hub RT** — `_miso224_floor_anatomy_phase0.actual_zone_price(year)["MISO-Indiana"]`,
  `values="rt"`. The lane's scored basis. Used here **only** to build the finite-hour `ok` mask,
  byte-identically to miso-236, so the hour set is the predecessor's.
* **Indiana-hub DA** — the basis `MISO_SEAM_LADDER_BY_YEAR` was Q-Q derived against, and the basis
  of **every regressor** below, exactly as miso-235 §3 and miso-236 fixed it.

They correlate only +0.402 / +0.424 / +0.553 and are never interchanged. miso-232's measured decile
column (+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here.

### 0c. What was established BEFORE this PREREG was written — disclosed, not claimed

Two facts, both **code reading** of a committed probe and committed source. **No adjudicating
quantity is among them**, and none is a statistic about a seam:

1. `scripts/probes/_miso236_neighbour_state_residual_phase0.py` already loads, on one code path,
   every series this session needs: the four-seam measured flows and the four-seam model
   reconstruction from the keeper's committed `hourly/` sidecars; the Indiana-hub DA (`da`) and the
   PJM border price (`pjm_border`) from `derive_miso_seam_ladders.load_joined`; the measured SPP
   NORTH hub DA from `measured_miso_spp_hub_prices`; and the EIA-930 BALANCE state blocks. This
   session's probe reuses those loaders unchanged, which is what makes §1's provenance gate
   meaningful rather than decorative.
2. The model's seam merit test (`spec.py`, reproduced in miso-236's probe) clears band `k` iff
   `p_bus(t) − p_neighbour(t) > delta_k` — i.e. the model's price representation of a seam is
   **already a monotone step function of the spread**, weighted by the measured `(month × hod)`
   deliverability envelope. It is **not** a single linear term. That is why §2's ladder-equivalent
   block `P2` exists and is measured separately from `P1`: attributing to "price" only what a
   single linear regressor can express would overstate the non-price residual, and this session
   refuses to do that.

**What the model's price representation CANNOT express, by construction, is also fixed here before
any number:** the seam clears on the **difference** `p_bus − p_neighbour` only, so the two legs
cannot act with different gains, and the neighbour's own price **level** cannot enter except
through that difference. `P3` is exactly the block that removes both restrictions.

---

## 1. The provenance gate — reproduce the predecessor before reading anything new

Fixed ex ante, and nothing in §2–§4 is read or published unless **both** legs clear:

* **(G-P1)** miso-235's `sigma_measured_mw` and `sigma_resid_measured_mw`, all four seams × three
  years, recomputed on this session's code path, agree with the committed
  `_miso235_seam_variance_decomposition_phase0.json` to **≤ 0.5 MW**.
* **(G-P2)** miso-236's **gated** `delta_r2_A_nohydro` — PJM, SPP and South × three years,
  recomputed here **in miso-236's own metric** (the increment on the single-spread residual, with
  that residual's variance as denominator) — agrees with the committed
  `_miso236_neighbour_state_residual_phase0.json` to **≤ 0.005**.

**If either leg fails, the instrument is declared BROKEN and NOTHING below is read or published.**
A repair measured against itself is the miso-235 §1 / miso-236 §0 standard and this session holds
itself to it.

## 2. Q-1 — THE FORM QUESTION. Does the neighbour-state increment survive the best available price representation?

### 2a. The blocks, fixed here

All on the measured seam flow `x_s(t)` (import-positive), on miso-236's `ok` mask, per seam and
year. Every price block is built from the **DA basis** of §0b.

* **`P1` — the model's regressor as miso-236 used it.** One linear term: PJM ← Indiana DA − PJM
  border; SPP ← Indiana DA − SPP NORTH hub DA; South ← Indiana DA (level); Manitoba ← Indiana DA
  (level). Unchanged from miso-235 §3 and miso-236 §1.
* **`P2` — LADDER-EQUIVALENT.** `P1`'s series entered **non-parametrically**: 19 dummies for its
  20 sample-quantile bins (ventiles), plus the linear term. This is the class of response the
  model's band ladder can already express — a monotone-or-not step function of the spread — so
  variation `P2` explains beyond `P1` is **inside the model's existing price representation**, not
  outside it.
* **`P3` — RICH PRICE.** `P2`, plus the **same ventile construction applied separately to each leg
  of the spread**: the Indiana-hub DA level and the neighbour hub price level. This removes both
  restrictions named in §0c: the two legs may act with different gains and non-linearly, and the
  neighbour's price level may enter on its own. **`P3` is this session's upper bound on what ANY
  price representation of the available series could reach.**
  * **Declared data boundary, fixed here:** South and Manitoba have **no neighbour price series**
    (SOCO/TVA are not organised markets and publish no hub; MHEB publishes none), so for those two
    seams `P3 ≡ P2` by construction. This is stated in advance so it is not read later as a result.

* **`S_nbr` — NEIGHBOUR STATE.** The miso-236 **gated no-hydro pair**, unchanged: covered-DIBA
  `Σ(Demand − Wind − Solar)` and `Σ(Wind + Solar)` from EIA-930 BALANCE, z-scored. The weak hydro
  limb stays excluded, exactly as miso-236 fixed it.
* **`S_own` — MISO'S OWN STATE.** MISO's own `Demand − Wind − Solar` and `Wind + Solar` from the
  same source, z-scored — the information the keeper **already has**.

**Degrees of freedom.** `P3` carries ~57 columns on ~8,760 rows and its legs are collinear by
construction (`spread = DA − neighbour`). Every `R²` below is therefore reported **raw and
dof-ADJUSTED**, `1 − (1 − R²)(n − 1)/(n − k − 1)`, with `k` the **numerical rank** of the design
matrix (`np.linalg.matrix_rank`), never its nominal column count. **The gated statistic is the
ADJUSTED one.** Fixed here so the choice cannot be made after seeing either.

### 2b. The statistic and the decision rule

For a state block `S` and a price block `P`, `ΔR²_S|P = R²(x on P ∪ S) − R²(x on P)`, both
dof-adjusted, both on the same rows and the same denominator `Var(x)`. The **survival ratio** is

    rho_S(s, year) = dR2_S|P3 / dR2_S|P1

which is denominator-invariant, so it is directly comparable to miso-236 whatever metric that used.

**GATED SEAM: SPP only** — the one seam reading ADMISSIBLE in miso-236, and therefore the only one
whose form question is live. PJM (MIXED) and South (route already CLOSED as predominantly
idiosyncratic) are **reported, not gated**; Manitoba has no `S_nbr` block at all.

**DECISION RULE for `S_nbr` on SPP, all three years, fixed ex ante:**

* **QUANTITY-SIDE FORM** iff `rho_nbr >= 0.50` in **all three years** **AND**
  `dR2_nbr|P3 >= 0.05` in **all three years** (an absolute floor, so a ratio of two negligible
  increments cannot confirm anything).
* **PRICE-REPRESENTATION FORM** iff `rho_nbr < 0.25` in **all three years**.
* **MIXED** otherwise — reported as mixed, closing and licensing nothing.

**What each verdict means for a successor, fixed here before the numbers so it cannot be written to
fit one:**

* **QUANTITY-SIDE** ⇒ miso-236 §5.1's object survives as a *quantity-side* measured input, and a
  successor's charter may be written for one. It does **not** charter it, size it, or name a field.
* **PRICE-REPRESENTATION** ⇒ miso-236 §5.1's object is a **price** object, the "new non-price
  input" reading is the miso-236 §6.3 error, and a successor's charter should be written against
  the seam's **price representation** instead. Also fixed in advance: such a charter is subject to
  rule 23 `[R-FROZEN-DERIVE]` — the SPP and PJM `delta_k` ladders are derived, frozen and pinned to
  their derives by test, and **nothing this session can measure licenses a re-derive or a damping
  factor**, whatever §2 or §4 says.
* **MIXED** ⇒ neither charter is written and the object stays exactly where miso-236 left it.

### 2c. Admissibility, stated BEFORE the numbers (rule 13 `[R-MEASURED]`)

`S_nbr` and `S_own` carry miso-236 §2c's admissibility argument unchanged and it is not re-litigated
here: neighbour and own net load and VRE are produced for a forward year by the **identical
construction the model already performs for its own zones** (weather-year load shape × growth, VRE
capacity × CF) — drivers, not outcomes. The neighbour **hub price** in `P3` carries the same
admissibility the PJM border price already has in the armed keeper (`miso_seam_neighbour_hourly_*`,
K): a published market price with a forward analogue.

**What is INADMISSIBLE and is named here so no successor mistakes it for this**, carried verbatim in
substance from miso-236 §2c: the measured DIBA **interchange series itself** (the outcome the LP
computes); neighbour **Net Generation (Adjusted)** as a whole (tied to the neighbour's demand by its
own total interchange, which contains the MISO tie); and **any noise term, variance inflator, damping
factor or scalar tuned to this σ or to any residual**, whatever this session measures. Nothing below
can license any of those. **`P2`/`P3` are MEASUREMENT INSTRUMENTS, not proposed mechanisms** — a
ventile dummy block is not a candidate and this session does not propose one.

## 3. Q-2 — item 2, the UNUSED own-state input, attributed for the first time

Three legs, all on the same instrument.

**(a) THE GATED LEG — the same form question for `S_own`.** `rho_own = dR2_own|P3 / dR2_own|P1`, the
same bars and the same verdict vocabulary as §2b, **GATED on the three seams miso-236 measured
Block B for and found non-trivial: PJM, SPP, South.** Manitoba is **reported, not gated** (its
miso-236 `R²_B` swings 0.0717 / 0.2556 / 0.0033 across the three years, so no stable object is being
tested). This asks whether MISO's own state reaches its own seams through a channel a price
representation can express — which, if it does, means the model's *price* is the seam of the defect,
not a missing input.

**(b) THE TRANSMISSION CHECK — REPORTED, NOT GATED.** The model's seam flow is a function of the
model's own solved bus price, and that bus price is itself driven by MISO's own net load. So own
state **should** reach the seam through price. Reported per seam-year: `R²(model bus price on
S_own)`, dof-adjusted. A high value with a surviving own-state increment in the measured seam is the
precise statement of item 2's defect — own state acting on the real tie **orthogonally** to the
price index the model transmits it through.

**(c) THE MODEL-SIDE SHARE AND THE SIGNS — REPORTED, NOT GATED.** `R²(r_model on S_own)` beside
`R²(r_measured on S_own)` for every seam-year, quantifying the handoff's claim that *"the model
reproduces NONE of it"* rather than restating it; and the **sign** of the own-net-load coefficient on
each side, against the structural expectation that MISO net load ↑ ⇒ MISO imports ↑ (positive,
import-positive). The model side is a **reconstruction** number (miso-235's four-seam form, harness
`corr(recon, committed)` +0.9845 / +0.9745 / +0.9839) and is labelled as one everywhere.

## 4. Q-3 — how much a better price representation would reach at all (REPORTED, NOT GATED)

`dR2_price = R²(x on P3) − R²(x on P1)`, dof-adjusted, per seam-year, with `R²(x on P2) − R²(x on
P1)` reported beside it to separate *what the model's ladder can already express* from *what only a
richer representation could*.

**RULE, fixed here: REPORTED, NOT GATED, and NEVER A TARGET.** Exactly as miso-236's ADDENDUM §A
fixed for its sizing number, and for the same reason (rules 1 `[R-STRUCT]` and 13 `[R-MEASURED]`
both bite): **a successor may not size, scale, tune or select any mechanism to make a modelled
statistic land on this number.** It says whether a route is worth chartering at all, never what value
to give anything. It moves no pre-registered verdict.

## 5. What this session cannot do, stated before the numbers

1. **No lever is proposed and none can be licensed here.** A verdict names which *class* of object a
   successor's charter should be written against; it does not charter one, size one, name a field, or
   arm anything.
2. **No damping factor, no re-derive.** The PJM and SPP `delta_k` ladders are derived, frozen and
   pinned to their derives by test (rule 23 `[R-FROZEN-DERIVE]`). A factor swept against any residual
   is the rule 1 `[R-STRUCT]` fitted mechanism. **This binds even if §2 returns
   PRICE-REPRESENTATION** — that verdict would name a class of object, not authorise re-fitting a
   frozen ladder, and §2b says so in advance.
3. **No re-test of an adjudicated cell** (rule 28(a) DO-NOT-REDO): `miso_south_firm_export_block`
   **G**, `miso_south_export_ladder_rt_tail` **R**, `internal_congestion_split` **G**,
   `vre_reference_rate_curtailment_grossup` **K**, `measured_interface_limits` **R**,
   `miso_rdt_measured_limit` **R**, `miso_south_gas_delivered_cost_basis` **R**. Where a number here
   touches one it **corroborates** it; the standing adjudication remains the finding. South's
   neighbour-state route stays **CLOSED** (miso-236 D-4) and Manitoba stays **CLOSED as already-armed**
   (miso-235 §3); neither is re-opened.
4. **No cell verdict moves in either direction.** This session tests no mechanism, so rule 28(b)
   attaches only in its **evidence-appending** form (the miso-206 / miso-234 / miso-235 / miso-236 /
   neiso-100 / caiso-206 no-solve precedent). Evidence is appended to `seam_flow_envelopes` and
   `seam_neighbour_hourly_ladder` in **MISO's shard only** (rule 25).
5. **No promotion, no decertification.** MISO is CALIBRATED today and this session does not trade a
   passing gate for anything (miso-227 promotion rule).
6. **C3c is untouched** and stays the designated frontier (2026-07-20). Its charter needs a new
   admissible measured identification and an owner ruling; no LP is authorized there under this
   handoff and none is sought.

## 6. Deliverables

* `scripts/probes/_miso237_price_representation_vs_state_phase0.py` →
  `results/calibration/_miso237_price_representation_vs_state_phase0.json`.
* `results/calibration/FINDING-miso237-*.md` carrying **every number this session will ever cite**.
* Evidence appended to MISO's matrix shard + the §5.4 queue stamp (rule 25, rule 28(b) evidence form).
* `docs/calibration-log/miso.md` entry.

## 7. Governance declared in advance

Rule 1 `[R-STRUCT]`: no mechanism is judged by a residual; nothing is proposed or selected, and §4's
number is declared un-targetable before it is computed. Rule 12 `[R-PARALLEL]`: no LP is solved;
nothing runs on CI. Rule 13 `[R-MEASURED]`: measurement only — no input changes, no measured outcome
enters any solve, and §2c fixes the admissibility argument and the named inadmissible forms in
advance. Rule 14 `[R-ACCURATE]`: no input changed. Rule 15 `[R-DASHBOARD]`: no run produced, so
nothing registered or pruned; MISO keeps exactly one registered run and the keeper's `hourly/`
sidecars stay committed. Rule 19 `[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2,
unchanged. Rule 22 `[R-HOLDOUT]`: 2023–2025 only. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run.
Rule 24 `[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO's shard, section and lane
only. Rule 27 `[R-PUSH]`: every pushed blob verified against local. Rule 28: queue item named in §0;
evidence-append form only. Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP phase 0 first, and this
session is that phase 0.
