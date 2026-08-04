# FINDING — pjm-153: the PJM lever queue is CLEARED. Every remaining item reaches a terminal state; no LP solved, no keeper touched.

> **Session renumbered pjm-152 → pjm-153.** The `pjm-152` label is SPENT: a
> separate session (`claude/pjm-152-backcast-calibration-gaq8jv`, merged to main
> at `11d39ec0`/`3990b44f`/`0e1214e9`/`f67117a3`) already used it for the rule-26
> `pjm_seam_envelope_by_neighbor` collapse and for a Task-C item-15 scoping probe.
> `docs/calibration-log/pjm.md` still reads "Next shorthand: pjm-152" because that
> session logged nothing. Renumbering follows the nyiso-121 precedent
> (`a9be1528`, "renumber off the spent nyiso-120 label"). **The dispatch that
> opened this session named the deliverable `FINDING-pjm152-queue-clear-…`; it is
> this file.**

**Verdict: the PJM backcast lever queue is EMPTY. Zero LP solved, zero bundles
produced, zero years touched outside 2023–2025, keeper unchanged and
re-verified.** Keeper `2026-08-03-pjm-151-seam-envelope` re-verified at this
session's head from committed artifacts alone (`scripts/calibration_verdict.py
--run-id`, no solve): **CALIBRATED, 9/9, zero FAILs, zero CAVEATs**, C1 `all
16/16 · free 12/12`.

Instruments, all no-LP and committed with this finding:
`scripts/probes/pjm153_item15_ladder_attribution.py`,
`scripts/probes/pjm153_reserve_supply_cap_reachability.py`,
`scripts/probes/pjm153_queue_screens.py`; machine records
`_pjm153_item15_attribution.json`, `_pjm153_supply_cap_reachability.json`,
`_pjm153_queue_screens.json`.

---

## OWNER BLOCK — what needs a decision (answerable without scrolling)

**Decision 1 — `state_carbon_pricing` (PJM cell `O`, PENDING OWNER since
pjm-146). Nothing has changed and nothing is proposed. Three options.**

The RGGI allowance adder is built, solved, registered; **zero fitted parameters**
(published auction clearing means, exact EIA-860 state membership, the fleet's own
emission rates); **all five pre-registered gates PASS**; DOF 18 → 19 with
`n_residual` unchanged at 6; D-2 *improves* (all three CT_PEAKER forced-share FAILs
clear). It is left off for one reason: the determination goes **CALIBRATED →
NOT-YET** on **C1 CC_REGULAR −16.06 / −13.84 TWh**, which was **not licensed** — no
C1 magnitude gate was pre-registered for it.

* **Cost of arming:** PJM stops being a zero-caveat CALIBRATED ISO. The mechanism
  is right *in kind* (it reproduces RGGI leakage: member CC → non-member coal / CT
  / imports) and wrong in *magnitude* — ~13–16 TWh where reality moves less.
* **Named successor if you want the magnitude fixed first:** the **CC→coal
  substitution elasticity**, under its **own** charter, identified from PJM's own
  record. Explicitly **never** a haircut tuned onto the adder (rules 13/21/24).
* **What stays true if it is left off:** PJM keeps a CALIBRATED, zero-caveat
  keeper; the model carries **no carbon price at all** in the four PJM states that
  actually had one, so the gas/coal merit order in those states is knowingly
  mis-ordered. That is a disclosed accuracy gap, not a gate failure.

**This session did not arm it and did not flip the cell.** The dispatch forbade
both, and I agree with the forbidding: the C1 magnitude is a real, unlicensed
regression.

**Decision 2 — sign-off on the G-20b within-window tight-hour memo (item 5).**
The memo owed by `FINDING-guard-falseneg-audit-2026-07-27` §7.2 is **written and
committed** at
`results/calibration/MEMO-pjm153-g20b-within-window-tight-hour-2026-08-04.md`.
It asks exactly one question and answers none of it:

> the merit-order guard vetoes an outage window when **≥ 90 %** of its hours are
> out of merit (`MERIT_OOM_FRAC = 0.90`). The remaining **≤ 10 %** are, by
> construction, the hours the unit *was* in merit — i.e. the tight, high-price
> hours. Today the whole window leaves the availability envelope, so the unit is
> returned to the model as AVAILABLE through those hours too. Should it be?

The memo lays out the evidence **both ways** (it cuts both ways, and the audit's
own verdict is UNCHANGED: D2 population test clean 3/3 for PJM, D3 exceedance
mostly a window-LENGTH effect), states that **rule 19 `[R-ONE-MECH]` bars stacking
anything on the guard's lane without replacing it**, and pre-registers the kill
rules a follow-on charter would have to carry. **What is needed from you is a
yes/no on chartering that charter — not a fix.** Nothing is armed and no guard
parameter moved (rule 23).

**Decision 3 — `pjm_reserve_supply_cap`, newly adjudicated below (item H).** It
is **not** cosmetic and **not** a rule-26 delete candidate; it is a **rule 19
`[R-ONE-MECH]` enforcement gap**. Every other incompatible PJM reserve-scoping
pair raises `ValueError`; this one pair is accepted silently. Closing the gap
makes the **current keeper's own recorded config raise**, so it cannot be landed
by a calibration session. **Filed, not deleted** — see §7 for the exact one-line
guard and its consequence.

**Also filed, needing no decision:** the prior `pjm-152` session landed a rule-26
collapse in main whose own PREREG demanded an **E1 gate of `max |dMW| = 0.000000`
on every P1 class-hour of all three years**, and that gate was **never scored** —
no `pjm152_collapse_A` bundle exists and no FINDING was written. §9.

---

## §1 — scoreboard

| item | subject | terminal state |
|---|---|---|
| **A** | root cause (15-new), net-export level | **CLOSED — measured refutation.** Not an independent defect; it is the flat-stack amplitude defect measured on the seam, and the 2025 "long" clause is a benchmark artifact |
| **B** | item 5 / root cause (6b), G-20b guard | **ROUTED TO OWNER** — the §7.2 memo is written; sign-off pending |
| **C** | `state_carbon_pricing` | **ROUTED TO OWNER** — restated, not armed, cell unchanged at `O` |
| **D** | item 8, `st_gas_mustrun_p25_level` | **CLOSED — provably inert.** Cell PJM `U` → `I` |
| **E** | item 10, `winter_citygate_daily` | **CLOSED — premise refuted ex ante.** Cell PJM `U` → `R` |
| **F** | item 3, Dominion NoVA/Loudoun split | **BLOCKED-ON-DATA, re-confirmed** (and narrowed) |
| **G** | items 4 + 6, C8 and C3c | **RECLASSIFIED** out of the lever queue into the keeper watch list |
| **H** | `pjm_reserve_supply_cap` | **ADJUDICATED — rule 19 enforcement gap.** Filed for the owner, not deleted |
| — | D-2 attribution defect (route-only) | **ALREADY CLOSED at pjm-149.** Does NOT reproduce at head — the matrix paragraph routing it is stale. §8 |

**Nothing was manufactured.** Three items close with no successor at all, which is
the correct outcome on an owner-declared frontier (pjm-142) and follows the
pjm-142 / pjm-148 precedent.

---

## §2 — item A: root cause (15-new) is NOT a new root cause

Item 15 was opened at pjm-151 as OPEN with its own charter owed: modelled net
export short **12.48 / 12.22 TWh** in 2023–24 and **long 5.21 TWh** in 2025. Three
measurements close it, all from committed bytes.

### 2.1 The 2025 sign flip is a BENCHMARK artifact, not model behaviour

Item 15's residual is stated against the `interchange` family actual, which is
EIA-930 `Total interchange`. The scope file carries two independent checks on it:

| year | EIA-930 `Total interchange` | PJM settlement tie file | EIA-930's own `Net gen − Demand` | hourly r |
|---|---|---|---|---|
| 2023 | 39.983 | 39.974 | 39.990 | 0.976 |
| 2024 | 32.641 | 32.825 | 32.680 | 0.9735 |
| **2025** | **17.968** | **32.925** | **32.730** | **0.3732** |

In 2025 the benchmark **fails its own arithmetic by 14.762 TWh** and disagrees
with PJM's settlement-grade tie file by 14.957 TWh, with the hourly correlation
collapsing from ~0.97 to 0.37. Its own generation and demand columns agree with
PJM's tie file to 0.2 TWh; only the published `Total interchange` column does not.

Against PJM's own settlement record, and using **the keeper's own attested net
position** (`calibration_attestation.json`, free-parameter entry 14, which records
both series because the rule-13 admissibility note needs them):

| year | model net export | measured (tie file) | shortfall |
|---|---|---|---|
| 2023 | 30.41 | 39.98 | **−9.57** |
| 2024 | 23.66 | 32.83 | **−9.17** |
| 2025 | 27.53 | 32.93 | **−5.40** |

**The residual is one-signed in all three years: the model under-exports,
always.** The keeper note's "2025 runs 5.21 TWh long" clause is corrected here —
it is an artifact of a benchmark series that contradicts itself.

### 2.2 The envelope ceiling cannot bind — the rules-5/14/20/24 bar was right

Summing each seam's measured p90 export envelope over 8760 h gives the maximum
annual export the cap admits **at any price**:

| year | envelope export ceiling | measured net export | headroom | binds? |
|---|---|---|---|---|
| 2023 | 75.528 | 39.975 | **+35.553** | no |
| 2024 | 67.031 | 32.824 | **+34.207** | no |
| 2025 | 68.465 | 32.925 | **+35.540** | no |

Loosening the caps, tuning `PJM_TIE_NEIGHBOR` or the p90 percentile, or restoring
the zone-summed path would all have been not merely barred but **pointless**: the
cap has 34–36 TWh of unused headroom in every year.

### 2.3 The binding side is the model's own price duration curve

An export band is a negative-output pseudo-unit offered at `p_k`; it clears when
PJM's internal price sits **at or below** `p_k`. The ladder's identification is
exact — across all 40 bands and all three years the measured flow duration and
`P(actual LMP ≤ p_k)` agree to **≤ 0.0003** — so evaluating the same band sum at
the model's own price duration curve is apples-to-apples:

| year | export the model's price never clears | shortfall (§2.1) | share explained |
|---|---|---|---|
| 2023 | **−8.290 TWh** | −9.57 | **86.6 %** |
| 2024 | **−5.991 TWh** | −9.17 | **65.3 %** |
| 2025 | **−4.152 TWh** | −5.40 | **76.9 %** |

The deep bands simply never clear. MISO 2023 bands 6–8 have measured durations
0.277 / 0.126 / 0.035 against model durations 0.038 / 0.0006 / 0.000. And the
cause is visible directly in the low tail, remarkably stable across years:

| year | model p5 − actual p5 | model p25 − actual p25 |
|---|---|---|
| 2023 | **+$7.32** | +$5.23 |
| 2024 | **+$7.57** | +$4.84 |
| 2025 | **+$7.36** | +$4.43 |

**The model is too dear at the bottom of its own price distribution, so it never
gets cheap enough to export.** That is not a new defect — it is items 12–13, the
flat-stack amplitude defect (`+$6.82 / +$5.78 / +$3.40` too dear overnight),
measured on the seam instead of on the clock. Root cause (15-new) **collapses into
the already-diagnosed, owner-declared-frontier limitation** and gets **no charter
of its own**, because chartering it would be re-opening the frontier under a new
name.

### 2.4 Stated against interest

* The −8.29 / −5.99 / −4.15 TWh is an **accounting attribution on the ladder's own
  bands, not an LP counterfactual.** Clearing those bands would raise PJM's
  internal price (exports are load), which would then un-clear some of them. The
  feedback is stabilizing, so the true equilibrium recovery from fixing the price
  shape is **smaller** than these numbers — they bound the direction and the order
  of magnitude, not the delta from any fix.
* The model/measured net-export pairs in §2.1 come from the keeper's attestation
  (30.41 / 23.66 / 27.53 vs 39.98 / 32.83 / 32.93) and are **not** the same
  accounting as the `interchange` family row (27.50 / 20.42 / 23.18 vs 39.98 /
  32.64 / 17.97). Both are reported rather than reconciled; the sign conclusion
  holds on either model series, because the 2025 flip is driven entirely by the
  *actual* side.
* I initially expected item A to yield a charter. It does not. The dispatch
  allowed "a charter **or** a measured refutation"; the evidence gave the second.

---

## §3 — item D: `st_gas_mustrun_p25_level` is provably inert for PJM

The matrix says the item survives only "as a rule-23 `[R-FROZEN-DERIVE]`
re-derivation on its own source data". The ex-ante screen finds something
stronger.

`data/fleet/arrays.py` arms a plant only when **both** its p25 level and its
`online_frac` are positive (`if _level <= 0.0 or _frac <= 0.0: continue`). PJM's
committed artifact:

| ISO | COAL | CC_REGULAR | CT_PEAKER | **ST_GAS** |
|---|---|---|---|---|
| MISO | 44/44 | 39/39 | 79/79 | **16/16** |
| **PJM** | 29/29 | 69/69 | 70/70 | **0/10** |
| CAISO | 0/0 | 0/23 | 0/44 | 0/3 |
| NEISO / NYISO | *(no `online_frac` column)* | | | |

Every PJM ST_GAS plant is skipped, so the floor set is empty **however the flags
are set**. Three further blockers stack behind it:

1. **The host mechanism is not armed.** The keeper carries
   `st_gas_mustrun_per_plant = False`; the flag is a level *swap* for a floor PJM
   does not have. Its actual ST_GAS forcing owner is `gas_st_netload_drag = True`.
2. **No source-data change exists to cite.** Rule 23 requires one, and there is
   none. What is stale is the *artifact* relative to the deriver's own group set
   (`_ONLINE_FRAC_GROUPS` now includes `ST_GAS`; PJM's file predates that).
3. **Regenerating it is not free.** The same regeneration rewrites
   `committed_pct` / `online_frac` / `chp_pmin_cf` for COAL / CC_REGULAR /
   CT_PEAKER — columns the keeper's **armed** `cc_mustrun_per_plant` and
   `coal_mustrun_per_plant` floors read. That would move the keeper through a
   channel nobody chartered.

**CLOSED. Matrix cell PJM `U` → `I`**, on exactly the basis NYISO used to move the
same row `U` → `I` at nyiso-105 (identical blocker, measured on PJM's own
artifact per rule 25). pjm-146 triaged this and left the cell `U`; this session
adjudicates it.

**Routed, not fixed:** the cross-ISO tranche-artifact staleness (PJM ST_GAS
missing, CAISO missing all four groups, NEISO/NYISO missing the column) is real
and is **not** PJM's lane to repair, for reason 3 above.

---

## §4 — item E: `winter_citygate_daily` — the premise is false

The matrix keeps item 10 alive "on the winter LEVEL story alone, as a rule 14
`[R-ACCURATE]` correction — PJM's delivered winter basis is a real quantity the
model proxies with the HH+zonal-basis construction."

**The keeper does not proxy it.** It prices PJM gas off **measured EIA-923
delivered receipts**: `gas_monthly_actuals = True` *and*
`gas_plant_monthly_fuel_pricing = True`. Henry Hub enters only as
`gas_daily_shape`, whose factors are divided by each month's own staircase mean
and therefore **average exactly 1.0 within every month** — they carry no
month-to-month level at all. `pjm_zonal_gas_hub.csv` is **one row per (zone,
YEAR)** and is applied capacity-weighted **mean-zero**, so it carries neither
seasonality nor level. `gas_price_override = 2.54` is only the trajectory fallback
for months with no receipts.

The measured winter level the model actually runs on:

| year | DJF mean | annual mean | DJF / annual | January |
|---|---|---|---|---|
| 2023 | 4.425 | 3.265 | **1.355** | $4.97 |
| 2024 | 3.958 | 2.852 | **1.388** | $5.07 |
| 2025 | 5.622 | 3.937 | **1.428** | $6.79 |

A TETCO-M3 daily citygate series would therefore replace a **settlement-grade
measured delivered cost** with a **hub quote** — the opposite of what rule 14
asks — and would stack a second owner on a phenomenon that already has a sole
owner (rule 19). The intra-day cell was already dead (pjm-141: every thermal LP
row's within-day offer σ is $0.000000) and the day cell was already dead
(pjm-139/141).

**CLOSED at Phase 0, no data intake required. Matrix cell PJM `U` → `R`.**

---

## §5 — item F: the Dominion split stays BLOCKED, and the block is narrowed

Re-confirmed against the current published feed
(`data/raw/zone-specific-demand/PJM<year>_hrl_load_metered.csv`), all three
training years: **`DOM` resolves to exactly one `load_area` (`DOM`)**.

The standing framing — "PJM's metered-load feed stops at the transmission zone" —
is **too broad and is corrected here**: the feed *does* resolve below the zone for
six zones (`AE`, `AEP`, `ATSI`, `DPL`, `PEP`, `PL`), in every year. Dominion
simply is not one of them. So the block is specific to DOM rather than a general
property of the feed — which makes it a cleaner data ask if it is ever raised, and
does not weaken it at all: a sub-zonal NoVA/Loudoun load share would still be a
fitted scalar (rules 5/24).

**BLOCKED-ON-DATA, re-confirmed.** No basis invented. The zonal-congestion route
to the Dominion CT leg remains CLOSED BY MEASUREMENT at pjm-137 and no successor
is proposed.

---

## §6 — item G: items 4 and 6 are WATCH items, not levers

Both are re-measured at head and moved out of the lever queue into the keeper
note's watch list, so the queue stops reading as though they were actionable.

* **C8 `CT_PEAKER` forced share — 16.2 / 16.4 / 16.7 %** (not the 16.3/16.9/17.1
  the queue carried, which are the pjm-137 figures). Above the 15 % peaker cap and
  a **clean GROUNDED PASS** in all three years under rule 18: every binding
  mechanism clears D-4, profile r 0.927 / 0.962 / 0.974, off-peak CV ratio
  0.719 / 1.075 / 0.836.
* **C3c** passes with model tail hours **3 / 10 / 32 h**. Any future delta must
  still report its C3c effect explicitly — that duty is retained on the watch list.
* **Newly surfaced and added to the watch list: C8 2025 `ST_GAS` at 39.9 %**
  (6.109 of 15.298 TWh), above the 30 % cap. It passes twice over — the class is
  **immaterial** (load share 1.74 % < 2 % floor) *and* separately GROUNDED — but it
  was not on any watch list and now is.

---

## §7 — item H: `pjm_reserve_supply_cap` is a rule 19 enforcement gap

pjm-151 filed this as an observation and explicitly declined to rule (rule 28(d)).
This session rules, from `ast` rather than from comments.

**Read-site census (three, not the two the observation named):**
`model/reserves/spec.py`, `pipeline/commitment.py`, and
`results/scarcity.py::pjm_reserve_deliverable_supply_cap_mw`.

**Proof 1 — the pergen block dominates.** In `spec.py::_pjm_design`, the gate
`if getattr(config, "pjm_reserve_pergen", False):` at **:2148** returns on **every**
path (verified by an all-paths-return walk that is conservative by construction),
and the `supply_cap = pjm_reserve_deliverable_supply_cap_mw(...)` assignment at
**:2355** is a later sibling at the same nesting depth. The `ReserveDesign` the
pergen limb returns takes `balance_col_mask, eligible, families, pergen_col,
pergen_col_pool, pergen_gen_idx, pergen_ramp10, storage_eligible` — **no
`supply_cap`**. So the flag cannot reach the LP by that path.

**Proof 2 — the P1 prep is gated off.** `pipeline/commitment.py
::build_pjm_reserve_p1_prep` returns `(None, None)` on its
`pjm_reserve_commitment_scoped` guard at **:1374**, before its only
`pjm_reserve_supply_cap` read at **:1394**. The keeper sets that flag `False`.

> The pjm-151 observation's line anchors (`:2280`, `:2286`, `:2018`, `:1374`) are
> **stale except the last**; the true anchors are above. The
> `measured_ramp_capability` row's registration anchor
> (`scarcity.py:1686`) is stale too — the function is at **:1758**. Both corrected
> in the matrix this session.

**Blast radius:** all **15** committed PJM bundles that record the field —
pjm136 through pjm151 — carry `cap=True, pergen=True, scoped=False`, i.e. the flag
has been armed-and-unobservable across the entire current keeper line.

**The ruling.**

* **Not cosmetic.** The keeper records a solve-affecting field armed *away from
  its shipped `False` default* while it is provably unobservable — the caiso-161
  §5 "armed-looking but dead" shape.
* **Not a rule 26 `[R-DELETE]` candidate.** The mechanism is built, reachable and
  correct in its own (non-pergen) path. Rule 26 targets a *retired* mechanism's
  re-armable fitted residue, not a working mechanism. This is the same
  distinction pjm-151 drew for `pjm_reserve_online_rho`, reached from the other
  side: `online_rho` is unobservable **at its own default**, this one is
  unobservable **against** its default.
* **It IS a rule 19 `[R-ONE-MECH]` finding, of the enforcement kind.**
  `pjm_reserve_pergen` and `pjm_reserve_supply_cap` scope the **same** phenomenon
  — reserve supply bounded by the fleet's 10-minute deliverable ramp — and pergen
  does it at the finer per-pool grain (`R[r] ≤ Σ FleetArrays.ramp10 ×
  availability`, its own field docstring), silently superseding the aggregate row.
  Three other incompatible PJM reserve-scoping pairs raise `ValueError` with the
  words *"enable exactly one reserve-supply scoping (CLAUDE.md rule 19)"*. This
  pair alone is accepted in silence. The field's own docstring says it "Pairs with
  `pjm_reserve_online_gated`" — it never claims to pair with pergen.

**Filed, not landed.** The fix is one guard clause in the same style as the
existing three. Its consequence is that **the current keeper's own recorded config
would raise**, so it must be decided together with what the keeper's recorded flag
becomes. That is an owner call, not a calibration session's.

---

## §8 — the D-2 attribution defect does NOT reproduce at head

The dispatch asked me to confirm the pjm-148 side finding still reproduces, write
it up, and route it as a cross-ISO charter. **It does not reproduce, and it does
not need routing — it was fixed at pjm-149, one session after it was filed.**

D-2 row counts across the committed PJM corpus:

| bundle | D-2 rows | CC_CHP | `nuclear_mustrun` |
|---|---|---|---|
| pjm136 … pjm144 | 42–43 | yes | 3 rows (272.02 TWh) |
| **pjm146, pjm147** | **32** | **no** | **0** |
| **pjm150, pjm151 (keeper)** | **42** | **yes** | **3 rows** |

`scripts/legitimacy_diagnostics.py` now **unions every floored key** regardless of
dispatch-map coverage, substitutes an absent plant's own floor as a **one-sided
bound**, and stamps `lower_bound` / `upper_bound` on the affected class summary
rows — all of which the keeper's committed file carries.
`FINDING-pjm149-d2-floor-attribution-path-2026-08-03.md` records that the fix
shipped, that **no determination moved at any of the six ISOs**, and — pointedly —
that pjm-148's specific claim that PJM's 14 CC_CHP codes are payload-absent was
**REFUTED: all 14 are PRESENT** in the pjm-144/146/147 payloads alike.

**Action taken:** the stale routing paragraph in matrix §5.3 is struck and
re-stated. **No charter is opened and nothing is routed to the owner**, because
there is nothing left to route. I did not take the matrix's text at face value,
and it was wrong.

---

## §9 — filed: the prior pjm-152 collapse landed with its verification gate unscored

Not this session's scope to discharge, but it must not stay invisible.

`PREREG-pjm152-seam-flag-collapse-2026-08-04.md` (committed to main) deletes
`pjm_seam_envelope_by_neighbor` and the zone-summed branch, and declares **exactly
one substantive gate, absolute**:

> **E1 — max |dMW| = 0.000000 on every P1 class-hour of all three years**, against
> `results/calibration/pjm151_seam_B`. Anything else means the collapse changed
> behaviour and is a stop-the-line event.

The code change is merged. **No `pjm152_collapse_A` bundle exists, no FINDING was
written, and `_pjm153_*` shows no E1 score anywhere in
`results/calibration/`.** The scorer (`scripts/probes/pjm152_collapse_gates.py`)
and the stripped replay recipe were committed; the arm was not run.

The change is *expected* to be behaviour-neutral — the keeper armed the
per-neighbour path and the collapse makes it unconditional — but "expected" is
what the E1 gate exists to replace, and the keeper's recorded recipe now names a
field HEAD does not have. **Filed for the owner as an open verification debt.** It
needs a solve, and this session's dispatch is no-LP.

---

## §10 — rule compliance

* **Rule 1 `[R-STRUCT]`** — nothing judged by whether it improves the fit. Item A
  is judged on amplitude and direction, never the annual mean; §2.3 turns on the
  low tail, not the level. Three items close with **no successor**.
* **Rules 13 / 21 / 24** — no adder, haircut or scalar sized by any residual;
  nothing tuned; no free parameter added, so the DOF ledger is untouched (19
  entries, `n_residual` 6).
* **Rule 14 `[R-ACCURATE]`** — §4 turns on preferring the measured delivered
  series over a hub proxy, in the direction rule 14 points.
* **Rule 19 `[R-ONE-MECH]`** — §7 is a rule 19 finding; §3 and §4 both decline
  levers that would stack a second owner on an existing phenomenon.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only, in every mode. No 2022, no 2019, no
  H1-2026, no probe. PJM holds `complete`, is absent from `final`, and the
  **holdout spend freeze is ACTIVE and outranks both**; nothing was spent.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no deriver touched, no artifact regenerated;
  §3 declines a re-derivation precisely because no source-data change can be cited.
* **Rule 25 `[R-ISO-SCOPE]`** — every measurement is on PJM's own artifacts. The
  cross-ISO tables in §3 and §8 are *reported* for context; **no other ISO's cell
  is written**.
* **Rule 15 `[R-DASHBOARD]`** — no solve ⇒ no bundle ⇒ nothing to register
  (pjm-124…131, pjm-138, pjm-142, pjm-145, pjm-148, pjm-149 precedent).
* **Rule 28 `[R-MECH-MATRIX]`** — two cells adjudicated and stamped in this
  session with citations (`st_gas_mustrun_p25` PJM `U`→`I`,
  `winter_citygate_daily` PJM `U`→`R`); §5.3 re-stated; no `R`/`I`/`G` cell
  re-tested; no `ScenarioConfig` field added.
* **Rule 27 `[R-PUSH]`** — no existing source file ≥300 lines rewritten from
  response content; matrix edits are targeted `Edit` calls on exact on-disk bytes,
  blob-verified after push.

## Reproduction

```
PYTHONPATH=.:src python scripts/probes/pjm153_item15_ladder_attribution.py
PYTHONPATH=.:src python scripts/probes/pjm153_reserve_supply_cap_reachability.py
PYTHONPATH=.:src python scripts/probes/pjm153_queue_screens.py
python scripts/calibration_verdict.py --run-id 2026-08-03-pjm-151-seam-envelope
```
