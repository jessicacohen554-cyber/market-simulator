# PRE-REGISTRATION — nyiso-113: `nyiso_li_locational_reserve`, the published Zone-K reserve ladder

**Date:** 2026-08-02 · **Session:** nyiso-113 · **ISO:** NYISO · **Years:** 2023, 2024, 2025
(one bundle per arm, rule 16 `[R-ALLYEARS]`) · **Keeper under test:**
`2026-08-02-nyiso112-ramp-plus-peaker` (bundle `results/calibration/nyiso112_combined_D`).

**Committed and pushed BEFORE either arm solved.**

---

## §1 — the lever, and why it is off-queue with cause

The §5.5 NYISO lever queue holds no peak-half lever: nyiso-110 declared the in-LP
reserve-**formation** family exhausted and moved `diurnal_price_amplitude` NYISO
`O → G`. This session's task-1 matrix-gap sweep (rule 28(c), the nyiso-112
standing lesson generalised) found **25 `nyiso_*` ScenarioConfig fields with no
matrix row at all**, and `nyiso_li_locational_reserve` is one of them: a
solve-affecting, NYISO-live field, **never armed in any bundle on disk**, with
**no rejection anywhere in the record**. Like 227-3 at nyiso-112 it was invisible
rather than adjudicated.

The mechanism is the **published NYISO Long Island (Zone K) locational reserve
ladder** — the LI rows of the same "Locational Reserve Requirements" posting that
already grounds the model's NYC and East families
(`data/raw/NYISO-AS/requirements/nyiso_locational_reserve_requirements.csv`,
`region=LI`; regime v2021 spans all of 2023–2025):

| family | requirement | class | demand-curve value | source |
|---|---|---|---|---|
| `li_10min_total` | 120 MW, all hours | 1 (quick-start) | $25/MW | ASM §6.8 item 10 |
| `li_30min_total` | 270 MW off-peak / 540 MW on-peak | 0 (full thermal) | $25/MW | ASM §6.8 item 15 |

The model **carries no Zone-K family at all**. That is a rule 14 `[R-ACCURATE]`
omission of a published requirement, not a new modelling assumption — the same
omission class nyiso-83/84 fixed one tier up.

## §2 — the rule-19 precondition, DISCHARGED BY MEASUREMENT (no LP)

The brief's binding constraint: a locational requirement is a new lever **only
if it can be shown to bind where the NYCA aggregate does not**, measured before
any solve. `scripts/probes/_nyiso113_locational_reserve_screen.py` →
`results/calibration/_nyiso113_locational_reserve_screen.json`:

**(a) It is not dominated.** A family row is
`Σ_{z∈region} R[c,z] + shortfall ≥ requirement`, so an armed family with the
same reserve class, a **subset** region and a requirement **at least as large**
forces the candidate's row slack. Both LI families survive: no armed family is
scoped to Long Island (the smallest armed regions containing Zone K are SENY
`{Lower_Hudson, NYC, Long_Island}` and East `{+Capital_Hudson}`, whose R-sums
run over strictly more zones). By the *same* algebra the sibling candidate
`nyiso_east_reserve_families` is **provably inert** and is NOT armed here —
`east_10min_spin` (330 MW, class 1) is dominated by `nyc_10min_total`
(500 MW, class 1, NYC ⊂ East) by 170 MW and by `east_10min_total` (1,200 MW) by
870 MW; `east_30min_total` (1,200 MW, class 0) is dominated by
`seny_30min_total` (1,300 MW, class 0, SENY ⊂ East) by 100 MW.

**(b) The nyiso-110 §10 refutation cannot reach a Zone-K row.** nyiso-110's root
cause was that reserve-eligible **hydro**'s own capability keeps the aggregate
rows slack in every hour (the keeper carries `nyiso_hydro_reserve_eligible=True`,
unioning hydro into both the full and quick-start classes). Measured by model
zone: NYISO hydro is **Upstate_West 4,094.9 / 4,035.2 / 4,035.2 MW +
Capital_Hudson 554.3 / 551.9 / 551.9 MW**, and **Long Island carries exactly
0.0 MW of hydro in all three years**. Upstate Niagara/St-Lawrence hydro is
physically incapable of supplying a Zone-K requirement, so the resource that
makes the aggregate slack provably cannot satisfy this row.

**(c) No locational family has EVER bound in the keeper.** Per-zone
`reserve_price` on the keeper's own sidecars: the reserve dual is > 0 in
17 / 6 / 36 hours of 8,760 and the **max cross-zone spread is exactly 0.0 in
every hour of every year** — a locational family that binds prices its member
zones above the non-members, so only the NYCA-wide families have ever bound.

**(d) Zone-K headroom can physically collapse.** Long Island total thermal
capacity is **5,146.5 MW** (quick-start 4,334.0 MW) against an LI peak demand of
**5,054 / 4,925 / 5,537 MW** — i.e. 2025 peak demand *exceeds* Zone-K nameplate
thermal before any availability derate, and the 227-3 overlay removes a further
145.5 MW of Zone-K quick-start inside the ozone window (4,334.0 → 4,188.5 MW).
Zone-K reserve headroom therefore goes to near zero in exactly the summer peak
hours where nyiso-92 dated the measured RT tail and nyiso-94 measured every model
`>$300` hour.

## §3 — the arms

| arm | config | bundle |
|---|---|---|
| **A control** | zero delta on the keeper recipe, solved at THIS HEAD | `results/calibration/nyiso113_control_A` |
| **B** | `nyiso_li_locational_reserve=true` — the single delta | `results/calibration/nyiso113_lilocational_B` |

Single-delta discipline: arm B differs from arm A in **exactly one**
`ScenarioConfig` field. The control is required because this branch is rebased
on a `main` later than the one nyiso-112 solved at, so the committed keeper
bundle is not a same-HEAD comparator.

## §4 — CONSTRUCTION GATES (all must pass, else the arm is not promotable)

* **K1 — one delta.** `run_config.scenario_config` diff between arms A and B is
  exactly `{nyiso_li_locational_reserve: false → true}`.
* **K2 — control integrity.** Arm A reproduces the committed keeper
  `nyiso112_combined_D` on every class-hour of all three years to within the
  strict byte basis; any non-zero delta is reported, not absorbed, and a
  material one invalidates the attribution.
* **K3 — LIVENESS (routes to INERT).** The two LI families must be constructed
  AND bind: the Long-Island reserve dual must exceed the non-LI zones' in
  **≥ 1 hour per year**. If the cross-zone spread stays 0.0 — the measured state
  of every prior keeper — the arm is **INERT**, recorded as such, and NOT
  promoted. A structurally-correct-but-inert published requirement is an honest
  `I` cell, never a keeper claim.
* **K4 — SCOPING FIDELITY.** The families are Zone-K-scoped, so any reserve-dual
  change must appear in **Long_Island only**. A non-zero reserve-dual delta in
  Upstate_West, Capital_Hudson, Lower_Hudson, NYC or NYISO_external is a
  construction error and fails the arm.
* **K5 — span.** `[2023, 2024, 2025]` in one bundle per arm (rule 16). The
  holdout spend freeze is ACTIVE and untouched: **no year outside 2023–2025**
  is solved, scored or read (rule 22 `[R-HOLDOUT]`).
* **K6 — DOF.** **Zero new free parameters.** Both requirement levels (120 MW;
  270/540 MW), the $25/MW demand-curve value and the on/off-peak boundary
  (NYISO MST §2.15 On-Peak: 07:00–23:00 EPT Mon–Fri excluding NERC holidays) are
  published constants or a published calendar rule. The DOF ledger goes
  29 → 30 entries with `n_residual` unchanged at 6.

## §5 — KILL GATES (any one fires ⇒ the arm is rejected, not repaired)

* **P1 — C3a band breach.** C3a outside ±10 % in ANY of the three years. The
  keeper sits at +7.572 / −0.591 / −9.563 %, so 2025 has ~0.44 pp of headroom;
  a breach kills the arm outright rather than being traded against C3c.
* **P2 — C1 regression.** All-class or free-class C1 falls below the keeper's
  14/14 and 10/10.
* **P3 — feasibility.** Any non-zero load-shed slack or dump in any zone-hour.
* **P4 — C7/C8 regression.** Any material class's diurnal-shape (C7) or
  forced-share (C8) verdict moves PASS → FAIL.
* **P5 — FORCING SIGNATURE.** A reserve requirement must hold *headroom*, not
  force *energy*. If Zone-K peaker energy rises in hours where the LI families
  do **not** bind, the arm is producing the nyiso-84 forcing signature and is
  killed regardless of what it does to C3c.

## §6 — NO-TUNING CLAUSE (binding)

The LI requirement levels (120 MW; 270 MW off-peak / 540 MW on-peak), the
$25/MW demand-curve value, the reserve-class assignment, and the MST §2.15
On-Peak calendar are **the published record**. They may **not** be re-levelled,
re-scoped, partially applied, re-derived, or swapped for a different vintage in
response to this arm's result — not to rescue an INERT verdict, not to enlarge a
C3c movement, not to recover a P1 breach. If the arm lands INERT, the verdict is
INERT. If it breaches a kill gate, the verdict is R. The only admissible
follow-up to a disappointing result is a **different mechanism** under its own
pre-registration.

Rule 1 `[R-STRUCT]` governs the promotion decision: this family belongs in the
model because NYISO publishes it and the model omits it, **not** because of what
it does to the residual — and equally, a C3c movement is not on its own grounds
for promotion if any construction gate fails.

## §7 — what is NOT being tested here

`nyiso_east_reserve_families` (adjudicated **provably inert** ex-ante in §2(a) —
no solve spent), `nyiso_synchronised_reserve` and
`nyiso_incity_commitment_obligation` (both mutually exclusive with other armed
mechanisms and both class-2 online-gate constructions of the family nyiso-110
exhausted), and `measured_ramp_capability` (screened inert ex-ante: the NYISO
reserve-eligible fleet's total 10-minute deliverable ramp is **12,318.4 MW =
18.8×** the 655 MW NYCA spinning requirement, so a per-asset ramp qualifier
cannot bind the aggregate row).
