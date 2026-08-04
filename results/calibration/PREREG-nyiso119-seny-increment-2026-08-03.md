# PRE-REGISTRATION — nyiso-119: arming `nyiso_seny_rcpf_increment_step` (the published SENY $40 increment tier)

**Date:** 2026-08-03 · **ISO:** NYISO · **Years:** 2023, 2024, 2025 (rule 16 — one
bundle per arm) · **Keeper at session start:** `2026-08-03-nyiso-118-seny-span`
(CALIBRATED-WITH-CAVEATS, C3c the sole ledgered caveat, 3/0/14) · **Committed and
pushed BEFORE either solve.**

---

## §1 — what this session is

This is the **named open successor** nyiso-118 deliberately did not fold in
(rule 19 `[R-ONE-MECH]`, FINDING-nyiso118 §5/§10). Both halves of the
measurement were already done and committed, and **neither is re-screened here**:

* **POSTED PRICES** (nyiso-117, `nyiso117_seny_rcpf_curve_screen.json`) — the
  isolated SENY-only 30-minute adder caps at **$23.92 / $30.37 / $40.00** in
  2023/24/25, with **52 hours of 2025 at exactly $40.00** and **zero hours above
  it in any year**; the modelled $500 base is never reached in 26,301 hours.
* **MODEL CONSTRUCTION** (nyiso-118, `nyiso118_span_construction_probe.json`) —
  SENY is a `critical_mw = 0` ramp with `n_ramp = 8` off a $500 max penalty, so
  its **first rung is $62.50**, already above the entire measured envelope.
  nyiso-118 re-spanned the widths; the penalties are requirement-independent and
  were measured unchanged, so the $62.50 first rung **survived**. That is
  precisely why nyiso-118 is a PARTIAL.

**This session arms exactly ONE flag**, `nyiso_seny_rcpf_increment_step`.

## §2 — the mechanism: a PUBLISHED TIER THE MODEL NEVER CARRIED

The NYISO SOM states the SENY 30-minute product as **two** tiers, and
`NYISO_RCPF_LOCATIONAL` carries only the first:

1. a **base** of "at least **1,300 MW** for all hours" at **$500/MW** — the
   `("seny_30min_total", 1300.0, 0.0, 500.0)` row the model has;
2. an **additional condition-varying increment**, binding a subset of hours, at
   **$40/MW** — the requirement **above** that base.

The **2023 SOM p. A-132** prints the pair as one object — **"SENY $500+$40"** —
in the same as-enforced-curve table that gives the NYCA 30-minute 9-step
$40..$750 curve. That transcription is **already in the codebase**, in
`NYISO_RCPF_EAST_FAMILIES`' provenance block, and predates this session.

`nyiso_dynamic_reserve_requirements` — armed on the keeper — already **enforces**
that increment: the measured #1344 hourly series runs 1,300 MW HB0–5, 1,550 MW
HB6, **1,800 MW HB7–21**, 1,550 MW HB22, 1,300 MW HB23, zero in Thunderstorm
Alerts. **Nothing has ever PRICED it.** The whole shortfall is charged against
the base curve, whose first rung sits above the measured ceiling. This is a rule
14 `[R-ACCURATE]` **omission** of the same class as nyiso-83/84's missing Long
Island and East families — a published tier the model did not carry.

### §2.1 — it clears the NYC-precedent bar: NO new number, NO fitted level

`nyiso_nyc_rcpf_step_curve` introduced no number — it set `critical == req` and
collapsed the ramp to a value `nyiso_rcpf_product_shortfall_steps` already
emitted. This flag is held to the same bar and clears it:

| quantity | source | already in repo? |
|---|---|---|
| **$40/MW** increment RCPF | ASM §6.8 **item 12**: "Eastern, **Southeastern**, New York City, or Long Island 30-Minute Reserves … shall be $40/MW" — the clause **names Southeastern explicitly**; July-2021 vintage, spans all of 2023–2025 | **yes** — the identical value and citation already pinned for `east_30min_total` |
| **1,300 MW** breakpoint | published SENY base | **yes** — read from `NYISO_RCPF_LOCATIONAL`, never re-typed |
| hourly requirement | measured #1344 series | **yes** — already on the balance row |
| **$500** base, `critical_mw = 0`, `n_ramp = 8` | **UNTOUCHED** | — |

**No parameter is fitted to a residual, and no free parameter is added.** If a
candidate had needed a fitted level it would be a rule 21 `[R-DOF]` open
root-cause issue rather than a parameter; it does not.

### §2.2 — the BASE tier keeps its ramp, deliberately

The posted-price instrument identifies the **increment** tier (an atom at
exactly $40.00) and says **nothing** about the base tier's shape — the $500 base
is never reached in 26,301 hours. Per nyiso-115's own discipline ("their curve
shape is UNIDENTIFIED by this instrument, so they keep the ramp"), **the base
tier is left exactly as it is**. This flag adds a tier; it re-levels and
re-shapes nothing. Rule 23 `[R-FROZEN-DERIVE]` is respected.

## §3 — arms

Both from the **designated keeper's** recipe over 2023, 2024, 2025 in one bundle
each (rule 16), launched concurrently (rule 12, 2-way cap):

| arm | bundle | delta |
|---|---|---|
| **CONTROL** | `results/calibration/nyiso119_control` | zero-delta replay of `nyiso118_seny_span` at THIS session's HEAD |
| **TREATMENT** | `results/calibration/nyiso119_seny_increment` | `--set nyiso_seny_rcpf_increment_step=true` |

**A same-HEAD control is MANDATORY.** Every attribution below is
treatment-vs-control at one HEAD, never treatment-vs-keeper. Provenance is
established by **comparing the dispatch**, never by inferring vintage from commit
ordering — `git merge-base --is-ancestor` exits **128** for an unfetched commit
and the ordinary `cmd && yes || no` idiom silently maps that to a plain negative
(nyiso-117 §9).

## §4 — the coupling hazard, DISCHARGED EX ANTE ON CONSTRUCTION

**The hazard, named before the solve.** `nyiso_ordc_measured_step_span` is
**armed on the keeper** and scales SENY's width vector by
`requirement[t] / 1300`. The two-tier construction carries the hourly
requirement **natively**, in the increment band — which is what the requirement
above the base physically IS — so span-scaling on top would **double-count** it
and break the total-width == requirement identity nyiso-118 restored. SENY
therefore takes the two-tier branch **instead of** the span branch (rule 19 by
**substitution**, never stacking), exactly as `li_30min_total`'s family-scoped
ladder already opts itself out of the global flag.

**MEASURED, before the solve, with no LP and no dual.**
`scripts/probes/_nyiso119_seny_increment_construction_probe.py` →
`results/calibration/nyiso119_seny_increment_construction_probe.json` builds the
NYISO `ReserveDesign` **twice at one HEAD** on the keeper's reserve flags and
diffs every family's `requirement`, `ordc_penalties` and `ordc_step_widths`.
This is deliberate: `dual` and `held_mw` are **solved co-optimization outputs**,
and gating byte-identity on them can only pass when the mechanism does nothing
(the nyiso-115 G2 error; nyiso-118 is the live proof that a provably-unchanged
curve can still move its dual through general equilibrium).

| family | widths | requirement | penalties | reachable price |
|---|---|---|---|---|
| `seny_30min_total` | **changed** | IDENTICAL | **changed** | **CHANGED (max Δ $147.50)** |
| `east_10min_total`, `li_10min_total`, `li_30min_total`, `nyc_10min_total`, `nyc_30min_total`, `nyca_10min_spin`, `nyca_10min_total`, `nyca_30min_total` | IDENTICAL | IDENTICAL | IDENTICAL | **IDENTICAL ($0.000)** |

All three years. **The blast radius is exactly ONE family.** Concretely:

* SENY steps **8 → 9**; first rung **$62.50 → $40.00**; the **base ramp's
  penalties are byte-identical** (`p_on[1:] == p_off`) — nothing re-levelled.
* Increment band width == `max(0, requirement[t] − 1300)` **exactly**; base band
  total == `min(1300, requirement[t])` **exactly**; the increment band is
  positive in **6,061 / 6,027 / 6,115** hours and reaches **500 MW**.
* **The nyiso-118 identity SURVIVES**: hours where total step width ≠
  `requirement_mw` = **0 in both arms**, all three years — including the
  zero-requirement Thunderstorm-Alert hours (`requirement_min_mw = 0.0`), where
  both bands clip to zero width.
* **Direction is MONOTONE downward** — `reachable_price_never_increases = True`
  at every probe point of every hour of every year. (nyiso-118's re-span was
  only *predominantly* downward; this one is strictly so, because adding a
  cheaper tier beneath the base can never raise the price at a given shortfall.)
* **LI is untouched** — `li_30min_total` byte-identical in all three vectors, so
  the span/ladder interaction does **not** fire.
* **The frozen NYC curve is untouched** — reachable price delta **$0.000**, 0
  hours, all three years. Rule 23 holds.

**Instrument power.** This probe is not a gate that can only pass by doing
nothing: it **separates** a re-priced family (SENY, max Δ $147.50) from eight
provably untouched ones ($0.000). The same instrument's discriminating power was
demonstrated independently at nyiso-118 on a different three-way split.

## §5 — the EX-ANTE PREDICTION, stated as a falsifiable number

Read from the **keeper's own committed sidecar**
(`nyiso118_seny_span/hourly/reserve_family_<year>.parquet`) — no solve:

> SENY binds in **2 / 0 / 8** hours of 2023/24/25. **Every one of those 10 hours
> sits at `requirement_mw = 1800.0`**, and the largest shortfall in any of them
> is **225.0 MW** — far inside the **500 MW** increment band that hour carries.

The construction probe evaluates the new curve at those exact shortfalls:

| year | shortfalls (MW) | priced OFF | priced ON |
|---|---|---|---|
| 2023 | 5.87, 61.31 | $62.50, $62.50 | **$40.00, $40.00** |
| 2025 | 0, 157.05, 48.92, 225.0, 0, 70.20, 199.91, 225.0 | $62.50 ×8 | **$40.00 ×8** |

**PREDICTION:** in the treatment, SENY's dual is **≤ $40.00 in every hour**
whose shortfall stays within `requirement[t] − 1300`, and its annual maximum is
**$40.00** unless general equilibrium produces a shortfall deeper than the
increment band (max observed on the keeper: 225 MW against a 500 MW band). **If
that holds, the model prices SENY inside the measured $23.92/$30.37/$40.00
envelope for the first time** — the S-OVER finding's actual defect.

**A shortfall deeper than the increment band would be a FINDING to report and
explain, not a kill** — it is a legitimate outcome of re-optimization.

## §6 — the C3c null, PRE-REGISTERED

**SENY is expected to leave C3c UNCHANGED at 3/0/14.** C3c is closed as a lever
lane (nyiso-115 §11, nyiso-116, nyiso-117 §5, nyiso-118 §7): both admissible
routes shut on measurement, the queue is exhausted, and the re-open condition is
a `Capital_Hudson` → Zone-F/Zone-G **topology split** requiring its own owner
charter — never a mechanism-flag lever. **This session does not re-open it.**
The mechanism moves the SENY reserve price **DOWN**, so it cannot add tail hours
by construction; a C3c move would be a finding to explain, not a success to
claim. This does **not** reach nyiso-110's everyday-reserve-formation gap and
will **not** be reported as closing it.

**The likely ISO-scope null is also pre-registered.** SENY binds in 2/0/8 hours.
A demand curve can only price where there is a shortfall, so a **correct**
mechanism may move almost nothing at ISO scope. Per rule 1 `[R-STRUCT]` that is
**not** grounds for rejection, and it is **not** grounds for claiming a win.

## §7 — GATES, each on an instrument that can observe what it claims

Reserve gates read `hourly/reserve_family_<year>.parquet` — the per-family dual,
requirement, held MW and ORDC shortfall. **Never** `system.parquet`'s
`reserve_price`, which is the cross-family SUM broadcast identically to every
zone and is inert by construction for any locational question (the nyiso-113
K3/K4 error). Any gate on curve **shape or level** reads the **construction**
artifact above plus the solve log's `%d ORDC steps` line, committed as each
bundle's `ordc_steps.log`.

**Byte-identity means float32 EXACT equality (`np.array_equal`).** The sidecar
columns are float32 with spacing 7.6e-06–6.1e-05 MW, so a 1e-6 MW tolerance is
unsatisfiable in principle (nyiso-116 G3/P4). No tolerance is used below.

| id | gate | pass condition |
|---|---|---|
| **G1** | the increment tier is LIVE | SENY carries **9** ORDC steps with first penalty **$40.00** and the base ramp's 8 penalties byte-identical to control; increment width == `max(0, req[t]−1300)` and base total == `min(1300, req[t])` in **every** hour of all three years (CONSTRUCTION) |
| **G2** | **the nyiso-118 identity SURVIVES (KILL leg)** | SENY's total step width == `requirement_mw` in every hour of both arms — the flag must not undo what nyiso-118 restored (CONSTRUCTION) |
| **G3a** | **scope — CONSTRUCTION (the KILL leg)** | every family except `seny_30min_total` has `requirement`, `ordc_penalties` **and** `ordc_step_widths` float32-EXACTLY identical between arms, all three years |
| **G3b** | **frozen-NYC + LI non-disturbance (KILL leg)** | the NYC pair's and `li_30min_total`'s **reachable price function** pointwise identical between arms (rule 23) |
| **G3c** | **scope — independent corroboration, no parquet** | the solve log's `%d ORDC steps` line goes **59 → 60** in both P0 and P1, all three years — exactly **+1 step in exactly one family** — copied into each bundle as `ordc_steps.log` |
| **G3d** | scope — **REPORTED, NOT a kill** | non-SENY `dual`, `held_mw`, `shortfall_mw` deltas reported; a change is a **finding to explain**, not a leak — they are co-optimization outputs and may move through general equilibrium even where the curve is provably untouched (nyiso-118's live demonstration) |
| **G4** | the §5 prediction, on the SOLVED sidecar | in the treatment, every hour with `0 < shortfall_mw ≤ requirement_mw − 1300` prices at **exactly $40.00**; hours with a deeper shortfall reported separately |
| **G5** | LP row identity | `held + shortfall ≥ requirement` everywhere, tight exactly where the family prices, both arms |
| **G6** | no feasibility damage | zero unserved-energy slack and zero dump in **both** arms, all three years |
| **G7** | span / holdout | 2023–2025 in one bundle per arm; **no** year outside 2023–2025 solved, scored or read (rule 22 — the holdout spend freeze is ACTIVE) |
| **G8** | scoring | `legitimacy_diagnostics.py` + `calibration_verdict.py` run per bundle; C1/C2/C3a/C3b/C3c/C4/C6/C7/C8 reported for BOTH arms against each other |

### §7.1 — KILLS, each discharged by MEASUREMENT

| id | kill | fires when |
|---|---|---|
| **K-A** | **scope leak** | any family outside `seny_30min_total` differs in `requirement`, `ordc_penalties` or `ordc_step_widths`. **Pre-discharged on construction (§4): $0.000, 8/8 families, all years.** |
| **K-B** | **frozen-NYC / LI disturbance** | the NYC pair's or LI's reachable price function differs between arms. **Pre-discharged on construction (§4).** |
| **K-C** | **the nyiso-118 identity is BROKEN** | any hour where SENY's total step width ≠ `requirement_mw` in the treatment — i.e. the increment tier double-counts against the span translation. **Pre-discharged on construction (§4): 0 hours, both arms, all years.** |
| **K-D** | **the base tier was re-levelled** | SENY's base-ramp penalties are not byte-identical to control, or a rung is added to / removed from the base ramp. **Pre-discharged on construction (§4): `base_ramp_penalties_unchanged = True`.** |
| **K-E** | **a fitted level was needed** | any number in the mechanism that is not the published $40 (ASM §6.8 item 12), the published 1,300 MW base, or the already-committed measured hourly series. **Pre-discharged: §2.1.** |
| **K-F** | **feasibility damage** | non-zero slack or dump appears in the treatment where the control had none |
| **K-G** | **the tier is not reachable** | the treatment's SENY dual sits on a base-ramp rung ($62.50+) in an hour whose shortfall is inside the increment band — the flag failed to do the one thing it exists to do |

**If a control degenerates (no power to discriminate), it is reported as
UNINFORMATIVE — never as a pass** (nyiso-117 §6.1). The §4 construction
instrument is demonstrated non-degenerate: it separates SENY (max Δ $147.50)
from eight families at $0.000.

## §8 — no-tuning clauses, binding

Nothing below is derived, re-derived, re-levelled or re-scoped in this session:

* the **SENY $500 base penalty**, its `critical_mw = 0`, and the `n_ramp = 8`
  discretization — the flag **adds a tier beneath them** and touches neither;
* the **NYC $25/MW RCPF and its NYC-pair scope** — frozen (rule 23), CLOSED,
  solved twice bit-identically;
* **`nyiso_ordc_measured_step_span`** — armed, keeper, and **not re-tested,
  re-spanned or re-scoped**; its behaviour on every other family is untouched
  and its behaviour on SENY with this flag OFF is untouched;
* the **LI reserve levels, $25 value and On-Peak calendar**;
* the **ramp envelope**, the **227-3 compliance file**, and the
  `nyiso_gas_bridge_*` measured min-load / min-run parameters.

## §9 — governance

* **Rule 15** — both arms registered on the dashboard in this session, keeper or
  not.
* **Rule 16** — 2023, 2024, 2025 in ONE bundle per arm; no single-year keeper.
* **Rule 19** — reconciled by **substitution**, not stacking (§4); no second
  mechanism is folded in.
* **Rule 22** — the holdout spend freeze is **ACTIVE**; no year outside
  2023–2025 is solved, scored or read, validation tier included.
* **Rule 23** — the frozen SENY base, NYC and LI parameters are not re-derived.
* **Rule 25 / 28(d)** — no other ISO's cell is adjudicated here.
* **Rule 27** — every push touching a file ≥ 300 lines is blob-verified; this
  scope writes `src/market_sim/`, so the session is Opus.
* **Rule 28(b)/(c)** — `nyiso_seny_rcpf_increment_step` gets its matrix row in
  the same PR as the field, and its cell moves to its measured verdict in
  **this** session.

## §10 — decision rule, fixed before the solve

* **All gates pass, no kill fires, and the increment tier prices** → the flag is
  a rule 14 `[R-ACCURATE]` **published-tier omission fix** and is a **promotion
  candidate on structure** (rule 1 `[R-STRUCT]`) — *not* on whether the residual
  improved. A worse fit does **not** reject it; a better fit does not by itself
  justify it. Cell **`U` → `K`**.
* **A kill fires** → **REJECTED**, recorded with the measurement that killed it.
  Cell **`R`**.
* **The construction changes but NOTHING observable moves** — SENY's duals
  identical to control in every hour of every year — → **INERT at ISO scope**,
  recorded as **`I`**, not as a pass. (Note the construction is already measured
  **not** to be a no-op, so this outcome would itself be a finding requiring an
  explanation.)
* **Scored numeric fields unchanged while SENY's duals DO move** → this is the
  nyiso-118 outcome and is **not** inert: it is a structural fix whose residual
  effect is bounded by how few hours the family binds. Reported as such, with
  the §6 nulls restated.
* **The residual moves and the gates pass** → reported as a structural result
  with the §6 nulls restated; it still does not close C3c or nyiso-110's
  reserve-formation gap.
