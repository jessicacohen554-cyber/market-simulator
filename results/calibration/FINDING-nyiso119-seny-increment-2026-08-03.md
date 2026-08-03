# FINDING — nyiso-119: the published SENY $40 increment tier, armed and promoted

**Date:** 2026-08-03 · **ISO:** NYISO · **Years:** 2023, 2024, 2025 · **Keeper at
session start:** `2026-08-03-nyiso-118-seny-span` · **Keeper at session end:**
`2026-08-03-nyiso-119-seny-increment`
**Pre-registration:** `results/calibration/PREREG-nyiso119-seny-increment-2026-08-03.md`
(committed and pushed **before** either solve).

---

## §1 — headline

`nyiso_seny_rcpf_increment_step` — the **SENY LEVEL/STEP mechanism** nyiso-118
deliberately did not fold in (rule 19 `[R-ONE-MECH]`) and named as its open
successor — was **armed, solved against a mandatory same-HEAD zero-delta
control, and PROMOTED**. Determination **CALIBRATED-WITH-CAVEATS**, C3c the sole
ledgered caveat, **unchanged**. **All 18 scored numeric fields are EQUAL to the
control's.** DOF ledger **32 → 33** entries with **n_residual UNCHANGED at 6**.

**The promotion rests on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`.** A
published tier of a published demand curve belongs in the model because it is
**real**, not because of what it does to the residual.

| arm | run id | bundle |
|---|---|---|
| CONTROL | `2026-08-03-nyiso-119-control-zerodelta` | `nyiso119_control` |
| TREATMENT | `2026-08-03-nyiso-119-seny-increment` | `nyiso119_seny_increment` |

## §2 — what the mechanism is: a tier the model never carried

The NYISO SOM states the SENY 30-minute product as **two** tiers, and
`NYISO_RCPF_LOCATIONAL` carried only the first:

1. a **base** of "at least **1,300 MW** for all hours" at **$500/MW**;
2. an **additional condition-varying increment**, binding a subset of hours, at
   **$40/MW** — the requirement **above** that base.

The **2023 SOM p. A-132** prints the pair as one object — **"SENY $500+$40"** —
as the as-enforced 2022–2023 curves. **That transcription already existed in the
codebase**, in `NYISO_RCPF_EAST_FAMILIES`' provenance block, before this session.

`nyiso_dynamic_reserve_requirements` — armed on the keeper since well before
nyiso-118 — has **always ENFORCED** that increment: the measured #1344 series
runs 1,300 MW HB0–5, 1,550 MW HB6, **1,800 MW HB7–21**, 1,550 MW HB22, 1,300 MW
HB23, zero in Thunderstorm Alerts. **Nothing ever PRICED it.** The whole
shortfall was charged against the base curve, whose very first rung
($500 / 8 = **$62.50**) already sat above the **entire** measured
$23.92 / $30.37 / $40.00 SENY envelope. That is exactly why nyiso-118 was a
partial: it re-spanned the **widths**, and the RCPF penalties are
requirement-**independent**, so the $62.50 first rung survived.

This is a rule 14 `[R-ACCURATE]` **omission** of the same class as nyiso-83/84's
missing Long Island and East families.

### §2.1 — it clears the NYC-precedent bar: NO new number

| quantity | source | already in repo? |
|---|---|---|
| **$40/MW** increment RCPF | ASM §6.8 **item 12**: "Eastern, **Southeastern**, New York City, or Long Island 30-Minute Reserves … shall be $40/MW" — the clause **names Southeastern explicitly**; July-2021 vintage, spans all of 2023–2025 | **yes** — identical value and citation already pinned for `east_30min_total` |
| **1,300 MW** breakpoint | published SENY base | **yes** — read from `NYISO_RCPF_LOCATIONAL`, never re-typed |
| hourly requirement | measured #1344 series | **yes** — already on the balance row |
| **$500** base, `critical_mw = 0`, `n_ramp = 8` | **UNTOUCHED** | — |

**No parameter is fitted to a residual and no free parameter is added.**

### §2.2 — the BASE tier keeps its ramp, deliberately

The posted-price instrument identifies the **increment** tier (an atom at exactly
$40.00 in 52 hours of 2025, zero hours above it in any year) and says **nothing**
about the base tier's shape — the $500 base is never reached in 26,301 hours.
Per nyiso-115's own discipline, **an unidentified shape is left alone**. This
flag adds a tier; it re-levels and re-shapes nothing. Rule 23 holds.

### §2.3 — rule 19 reconciled by SUBSTITUTION, never stacking

`nyiso_ordc_measured_step_span` is armed on the keeper and scales SENY's widths
by `requirement[t] / 1300`. The two-tier construction carries the hourly
requirement **natively**, in the increment band — which is what the requirement
above the base physically **is** — so span-scaling on top would double-count and
break the identity nyiso-118 restored. **SENY therefore takes the two-tier branch
INSTEAD of the span branch**, exactly as `li_30min_total`'s family-scoped ladder
already opts itself out of the global flag. The span flag's behaviour on every
other family, and on SENY with this flag off, is **untouched**.

## §3 — the scope and coupling questions were settled EX ANTE, on CONSTRUCTION

`scripts/probes/_nyiso119_seny_increment_construction_probe.py` builds the NYISO
`ReserveDesign` **twice at one HEAD** on the keeper's reserve flags and diffs
every family's `requirement`, `ordc_penalties` and `ordc_step_widths` — **no LP,
no dual**. `dual` and `held_mw` are solved co-optimization outputs, and gating
byte-identity on them can only pass when the mechanism does nothing (the
nyiso-115 G2 error; nyiso-118 is the live proof that a provably-unchanged curve
still moves its dual through general equilibrium).

| family | widths | requirement | penalties | reachable price |
|---|---|---|---|---|
| `seny_30min_total` | **changed** | IDENTICAL | **changed** | **CHANGED (max Δ $147.50)** |
| the other **eight** | IDENTICAL | IDENTICAL | IDENTICAL | **IDENTICAL ($0.000)** |

All three years. **The blast radius is exactly ONE family** — so K-A (scope leak)
and K-B (frozen NYC / LI disturbance) were discharged before a solve was spent,
and the rule-23 freezes hold. The instrument is not one that can only pass by
doing nothing: it separates SENY (max Δ $147.50) from eight families at $0.000.

## §4 — gates: all eight PASS, K-A…K-G all silent

| id | gate | result |
|---|---|---|
| G1 | increment tier live | **PASS** — steps **8 → 9**, first rung **$62.50 → $40.00**, base-ramp penalties **byte-identical**, increment width == `max(0, req−1300)` and base total == `min(1300, req)` **exactly** in every hour; band positive in **6,061/6,027/6,115** h |
| G2 | the nyiso-118 identity **survives** | **PASS** — total width == `requirement_mw` at **0/0/0** violating hours in **both** arms, incl. zero-requirement TSA hours |
| G3a | scope, on construction | **PASS** — eight non-SENY families byte-identical in all three vectors |
| G3b | frozen NYC pair + LI undisturbed | **PASS** — reachable price $0.000 |
| G3c | ORDC step count, from the solve log | **PASS** — **59 → 60**, exactly **+1** in exactly one family, every pass and year |
| G4 | the tier prices at the published $40 | **PASS** (re-specified — see §5) |
| G5 | LP row identity | **PASS** |
| G6 | no feasibility damage | **PASS** — zero slack, zero dump, both arms |

## §5 — G4 as pre-registered FAILED, and that is recorded, not redefined

**The pre-registered G4 demanded an exact $40.00 dual for every hour with
shortfall in the CLOSED interval `(0, band]`. It failed. The failure is the
GATE's, not the mechanism's.**

The specification was **asymmetric**: it excluded the **lower** kink (`s > 0`)
while **including** the upper one (`s == band`). At either kink the LP is
degenerate and the dual is legitimately anywhere between the adjacent bands'
prices — which is exactly why the zero-shortfall hours price at $7.75 / $17.31
rather than $0, and the pre-registered form **already tolerated that**.

Re-specified onto what K-G actually asks — the **strict interior** must price at
the published increment, and the band **edge** must be **bracketed** by the two
adjacent band prices. Both hold:

| year | binding | strictly inside band | at exactly $40.00 | at band edge | deeper than band |
|---|---|---|---|---|---|
| 2023 | 2 | 2 | **2** | 0 | 0 |
| 2024 | 0 | 0 | 0 | 0 | 0 |
| 2025 | 8 | 4 | **4** | 1 (**$57.28** ∈ [$40.00, $62.50]) | 1 ($62.50, the first base rung — correct) |

Following nyiso-115's G2 and nyiso-117's G2a, the mis-specification is
**recorded rather than quietly redefined**. The mechanism is unchanged; only the
gate's boundary handling is.

## §6 — structural corroboration from the solve itself

In the treatment's deepest 2025 hour the LP stops holding SENY reserve at
**exactly `held_mw = 1300.0` — the published base** — because past that point the
$40 increment tier no longer justifies holding more. In the control it stopped at
**1575.0**, which is 1800 minus one control band width and has **no market
meaning**.

**The published demand curve's own breakpoint is now where the dispatch stops.**
That is not something the gates asked for; it is the mechanism being right.

## §7 — measured effect, stated precisely

* **SENY max dual: 62.50 → 40.00 (2023), no binding hours (2024), 87.07 → 62.50
  (2025)**; binding hours 2→2 / 0→0 / 8→8.
* **S-OVER is NARROWED — reported, not gated** (rule 1). Of **10** binding hours:
  those above the year's **measured** ceiling go **8 → 4**; those above the
  **published $40** increment go **8 → 2**.
* **It is NOT closed, and is not reported as closed.** 2023/2024's *realized*
  ceilings ($23.92 / $30.37) sit **below** the published $40 cap — the market
  never drove those years to full band saturation — so pricing **at** the
  published cap is still above them. That residual is an **incidence/depth**
  question, not a curve-construction one.
* The NYC pair's max dual stays at exactly **$25.00** in every year with its own
  curve provably unchanged; incidence shifts by one hour each in 2025. That is
  co-optimization **general equilibrium** — reported (G3d), never gated.

**A correction to my own pre-registration.** PREREG §5 said the result would put
SENY "inside the measured envelope for the first time." That is right for **2025
only**, whose measured ceiling *is* $40.00. The precise claim, which is what §7
states, is that the model now prices **at the published $40 cap and never above
it** in any hour strictly inside the band, where before its **floor** was $62.50.

**Why the ISO-scope effect is nil.** All 18 scored fields are equal to the
control because **SENY binds in 2/0/8 hours** — a demand curve can only price
where there is a shortfall. Pre-registered in PREREG §6 as the likely null.

## §8 — C3c: the pre-registered null held

**C3c is UNCHANGED.** Pre-registered (PREREG §6), not discovered afterwards. The
mechanism moves the SENY reserve price **down**, so it cannot add tail hours by
construction. C3c remains closed as a lever lane with an exhausted queue; its
re-open condition is a `Capital_Hudson` → Zone-F/Zone-G **topology split** under
its own owner charter, never a mechanism flag. This does **not** reach
nyiso-110's everyday-reserve-formation gap and is **not** reported as closing it.

## §9 — TASK 2: the cross-ISO queue

NYISO's transfer queue is **empty** and its matrix column **closed**; re-confirmed
and nothing else touched. `mechanism_matrix_gap_sweep.py --iso NYISO`: **41
family fields, 0 absent, 0 prose-only, 0 armed-no-cell, 0 shared-gap**, sole
exclusion the declared `weather_year`. **The 40 → 41 is this session's own new
field and its matrix row, not drift.** The MISO (17), PJM (18), ERCOT (14) and
CAISO (5) shared-field backlogs are **their lanes' work** (rule 25 / 28(d)) and
were not adjudicated here.

## §10 — governance

* **Rule 15** — both arms registered on the dashboard in this session.
* **Rule 16** — 2023, 2024, 2025 in ONE bundle per arm.
* **Rule 19** — reconciled by substitution (§2.3); no second mechanism folded in.
* **Rule 21 `[R-DOF]`** — ledger 32 → 33, n_residual unchanged at 6.
* **Rule 22** — holdout freeze **ACTIVE** and untouched; no year outside
  2023–2025 solved, scored or read. NYISO's `complete` entry re-keyed with the
  determination **re-verified from committed artifacts, no solve** (D-5(b)):
  identical to the superseded keeper on all 18 fields, all 9 criterion verdicts
  and the grade summary — nothing worse, so the promotion proceeded.
* **Rule 23** — the SENY $500 base, `critical_mw = 0`, `n_ramp = 8`, the span
  flag, the NYC $25/MW RCPF and the LI levels/calendar were **not** re-derived.
* **Rule 27** — every push touching a file ≥ 300 lines blob-verified.
* **Rule 28(b)/(c)** — the matrix row was added **with the field**, and its cell
  moved `U` → `K` in this session.

## §11 — what a later session should NOT redo

* **Do not re-screen SENY.** The measurement is now done three times over
  (`nyiso117_seny_rcpf_curve_screen.json` posted prices,
  `nyiso118_span_construction_probe.json` span construction,
  `nyiso119_seny_increment_construction_probe.json` tier construction).
* **Do not re-test, re-level or re-scope this flag.** It is armed, solved, gated
  and keeper. The $40, the 1,300 MW breakpoint and the untouched $500 base are
  frozen under rule 23.
* **Do not re-open the NYC curve or the span flag.** Both are provably
  undisturbed by this mechanism ($0.000 reachable price delta; identity intact).
* **Do not gate a reserve scope question on a dual**, and **do not write a
  price gate on a closed interval at a band edge** — this session's own G4 is the
  demonstration.
* **The remaining SENY question is INCIDENCE/DEPTH, not curve construction:**
  2023/2024's realized ceilings sit below the published cap, so the model's few
  binding hours saturate the band where the market did not. That is a
  reserve-*formation* question and belongs with nyiso-110's open peak-half lane,
  which is **pending an owner amplitude-criterion call** — not a curve lever.
