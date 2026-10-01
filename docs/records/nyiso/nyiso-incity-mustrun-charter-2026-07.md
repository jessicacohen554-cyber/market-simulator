# NYISO in-city (Zone J / Zone K) load-pocket must-run — lane charter (nyiso-76)

**Date:** 2026-07-26 · **Produced by:** nyiso-75 keeper-promotion session ·
**Chartered by:** owner ("promote and charter", 2026-07-26) ·
**Diagnosis it implements:** `results/calibration/FINDING-nyiso-stgas-underrun-diagnosis-2026-07-23.md` ·
**Status:** CHARTER ONLY — no mechanism code, no config flag, no intake performed in this
session. Nothing here is authorized to run until the data question in §3 is answered.
**§3 EXECUTED AND CONCLUDED (2026-07-26, nyiso-83) — THE MECHANISM IS BUILT AND
THE SUBSTITUTION IS REFUTED. This lane's §0 question is now ANSWERED: for Zone J
and Zone K alike, no published instrument reproduces the in-city steam
commitment, and the §3 "documented NO, not a mechanism" branch is the outcome.**
Do not re-open it by re-probing the reserve ladders.

Three arms, 2024, each against a same-HEAD zero-delta control:

| arm | LI reserve-dual h >\$0 | ST_GAS TWh | C3c h >\$300 |
|---|--:|--:|--:|
| control | 6 | 8.710 | 0 |
| published LI ladder alone | 6 | 8.710 | 0 |
| + in-city commitment obligation | **7,003** | **5.810** | 0 |

1. **The published ladder alone is inert** — idle-allowed families are satisfied
   free by Zone-K idle capacity every hour.
2. **The online gate is the entire effect** and it works (6 → 7,003 h binding).
3. **C3c is ceiling-blocked**: the published J/K demand curves are **\$25/MW**
   (ASM §6.8 items 9/10/14/15), so a load-pocket family can never reach the
   \$300 gate. The C3c tail must come from NYCA/East (\$750/\$775).
4. **The rule-19 substitution fails**: replacing the eight NYC/LI `ST_GAS` floor
   limbs costs **−2.90 TWh** of steam (displaced exactly onto CC/CT), because
   the obligation is written on the **pocket**, not on **steam** — the LP meets
   620 MW with the cheapest in-pocket online capacity. Shape improves
   (evening/overnight 1.905 → 2.449) but level collapses: shape-faithful,
   level-insufficient. **The floor stays.**

Per §2 this is decisive: the lane required *replacement*, replacement has been
tested, and it does not act on the class it had to replace. Per §3's own terms
the correct outcome is the **documented NO** — the gap is an accepted
representation limit of the full-SRMC LP, because the real driver is the
non-public Con Edison load-pocket procedure the MMU itself cannot see (41–42 %
of NYC reliability commitments "unverified"). Both mechanisms remain in the
codebase, default-off, as the recorded evidence.
Full evidence: `docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md`
§§4/4a/4b; log: `docs/calibration-log/nyiso.md` 2026-07-26 nyiso-83.

**§3 ADJUDICATED (2026-07-26, nyiso-83 session) — THE GATE IS OPEN.** The owner
ruled **YES, full J/K reopen**: the closed C3a "reserve" lever was closed as a
*pricing* lever (measured Δ$0.00, nyiso-71) and does not extend to a
commitment-obligation reading. Mechanism built, commit `fa9fc78`:
`nyiso_li_locational_reserve` (the published Zone-K ladder, which the model
carried **nowhere** — a rule-14 omission, not a new assumption) and
`nyiso_incity_commitment_obligation` (the published NYC+LI 10-minute families
re-classed onto an ONLINE-GATED in-pocket class, auto-superseding the NYC/LI
`ST_GAS` floor limbs per §2). Both default-off and byte-inert.
Vintage pin resolved from disk evidence: the v2021 regime spans all of
2023–2025, so NYC 500/1,000 is already correct and **unchanged**; 625/1,250 is
a 2026 event. The LI on/off-peak `DATA NEEDED` is closed from the tariff (MST
§2.15). **Zone K: documented-NO recorded** — the current ARR table is behind
MyNYISO ("Log into MyNYISO to view the Application of Reliability Rules") and
Manual 12's Table B.5 is now only a pointer to that walled page, so the
units-in-service genre is unobtainable; the LI limb rests on the published
reserve ladder instead. Details:
`docs/handoffs/nyiso-incity-instrument-survey-2026-07.md` §2a.

**§3 UPDATE (2026-07-26, nyiso-82 session):** the Step-1 search is DONE — see
`docs/handoffs/nyiso-incity-instrument-survey-2026-07.md`. Zone J: documented-NO supported
(operative Con Ed procedure parameters are non-public, invisible even to the MMU) UNLESS
the owner adjudicates that the closed "reserve" C3a lever — closed as a *pricing* lever —
may be reopened as a *commitment obligation* driver on the published J/K locational
reserve ladders (the one instrument that passes rule 13 outright). Zone K: one live
thread — retrieve the current login-walled ARR table (the 2008 vintage's ARR 22 proves
the units-in-service genre for Northport/Port Jefferson) — before the same NO is recorded.
Mechanism work remains UNAUTHORIZED pending those two items.

## 0. Owner intent in one paragraph

NYISO under-generates steam-gas (`ST_GAS`) by **−1.83 / −3.02 / −5.12 TWh** in
2023 / 2024 / 2025, and the gap **grows every year**. As of the nyiso-75 keeper this is no
longer cosmetic: it costs a scored **C1 2024** cell (−3.021 TWh against a ±3.01 TWh band)
and will cost 2025 as well once that EIA-923 vintage finalizes — today the 2025 cell is
*skipped*, not passed (3/10 ST_GAS plants reporting), which is the only reason C1 ever read
14/14. The 2026-07-23 diagnosis **ruled out the two cheap explanations**: it is not an
economic/heat-rate error (the model's `Plant_Avg_HR` is byte-identical to the EIA-860 design
HR, which matches the CEMS operating HR) and it is not a pricing error (the model already
prices the Long Island pocket *above* the steam's marginal cost — $47 evening vs mc $45–51).
Reality runs downstate steam **out of merit for local reliability**; a full-SRMC LP plus a
p25 availability floor structurally cannot reproduce that. This lane's job is to represent
that obligation **as a real, published, forward-regenerating requirement** — or to conclude,
on the record, that no such instrument exists in a usable form and that the gap is an
accepted representation limit.

## 1. Why the existing mechanisms cannot close it (all empirically probed — do not re-run these)

| Lever | Result | Verdict |
|---|---|---|
| Correct the ST_GAS heat rate | Model HR **is** the EIA-860 design HR (Danskammer 11.282, Northport 10.887, …), and design ≈ CEMS operating HR | No rule-11 [R-ACCURATE] fix exists — nothing to correct |
| Raise the reliability floor toward bench volume | 2023 replay: ST_GAS 7.40 → 8.34 TWh but the volume lands **flat/overnight** (evening 1003 → 1116 vs bench 1441); C7 D-1 `cv_ratio` **0.483 → 0.422**, C8 pushed further over cap | Rejected — wrong instrument (adds flat volume, reality's is evening-shaped), and setting it to the observed level is a rule-13 [R-MEASURED] residual-fit |
| Lower the floor (nyiso-71) | ST_GAS → 6.93 / 7.92 / 10.83; **breaks C1** | Rejected probe — floor is pinned from below too |
| Re-price / offer-surface levers | Model price already ≥ reality's in the pocket | Cannot add out-of-merit volume by pricing |

**The floor is pinned from both sides.** That is the whole reason this needs a *new*
mechanism rather than a parameter move.

## 2. The binding constraint: rule 19 [R-ONE-MECH]

`reliability_floor` (`data/raw/reference/reliability_floor_coeffs_NYISO.csv`) **already
floors this exact class in these exact zones** — NYC and Long_Island `ST_GAS` carry a
persistent 24 h base limb plus a 14–21 h evening ramp, and D-2 already attributes
**26–40 %** of ST_GAS energy to it (2024 = 41.7 %, passing C8 only via the rubric-v2.2
grounded-above-budget escalation).

> Any mechanism this lane produces **MUST REPLACE OR RECONCILE WITH** the NYC/LI `ST_GAS`
> limbs of `reliability_floor`. **Stacking a second floor on the unexplained residual of the
> first is forbidden** (rule 19), and would in any case breach the C8 forced-energy budget.

The likely correct shape is therefore *substitution*: where a published in-city obligation
exists, it **supersedes** the p25-derived floor for that zone/class; the p25 floor remains
only where no obligation is published.

## 3. THE OPEN DATA QUESTION — this lane cannot start until it is answered

The diagnosis names the forward lever as "a published NYISO Zone-J / Zone-K minimum in-city
generation requirement". **That instrument is not yet identified on disk, and the obvious
candidate is the wrong shape:**

`data/raw/capacity-deliverability/nyiso/nyiso.csv` holds the published NYISO **LCR** (Locality
Capacity Requirement) for NYC / Long Island / G-J — but as a **peak-capacity ratio**
(`value_pu` 1.052 / 1.053 / 1.065 for Zone K), sourced from the NYSRC Reliability Rule A.2
compliance submittals and the annual LCR reports. This is a **MW-at-peak installed-capacity
obligation**, not an **hourly energy obligation**. Using it directly would require inventing
the hour-to-hour translation — which is precisely the fitted step rule 13 forbids. This is
the same misalignment already recorded as the open root cause on the
`NYISO_LOCAL_SELFSUPPLY_FRAC['Long_Island']` DOF entry (audit C-17 / B-NYI-1).

**Step 1 of this lane is a search, not a build.** Candidate instruments to evaluate, in
descending order of promise:

1. **NYSRC Local Reliability Rules** for the NYC load pocket — the in-city minimum-generation
   / minimum-units-in-service rules (historically the "80 % in-city" family) and the Con
   Edison load-pocket rules they reference. These are *operating* requirements and so are the
   right **shape**; the question is whether a machine-readable, per-hour-resolvable form is
   published.
2. **NYISO Gold Book / Reliability Needs Assessment** local transmission-security limits for
   Zones J and K.
3. **NYISO Local Reliability Rule / SRE (Supplemental Resource Evaluation)** and RMR
   determinations naming specific downstate units and their required availability windows.

**Admissibility test each candidate must pass before any code is written (rule 13
[R-MEASURED]):** *could this same quantity be produced for a forward year from forward
drivers, and would it respond to changed conditions?* An obligation that regenerates from
published load-pocket requirements + fleet composition **passes**. An "obligation"
back-derived from observed CAMPD generation **fails** — that is the observed outcome, not the
requirement, and is exactly the rule-13 violation the diagnosis warns against.

**If no candidate passes, the correct outcome of this lane is a documented NO, not a
mechanism.** Record the gap as an accepted representation limit of the full-SRMC LP and
leave the residual open. Do not fall back to fitting the floor to the bench.

## 4. Scope boundaries

- **In scope:** the search of §3; if and only if an instrument passes, a curated datatype +
  per-ISO registry module under the `data-intake` skill's contract, and a
  local-reliability-commitment mechanism that supersedes the NYC/LI `ST_GAS` floor limbs.
- **Out of scope / explicitly closed — do not reopen:** ST_GAS heat rates; the overnight
  ST_GAS floor (nyiso-71, rejected probe); `interchange_shaping` (rule-13 forbidden as a
  keeper mechanism); the closed NYISO C3a levers (reserve, `cc_intermediate_split`, per-plant
  gas, zonal gas basis, reliability floor level, offer markup, ERCOT-63 gas bridge,
  net-revenue margin form); hydro (owned by the nyiso-74 lane).
- **Not this lane's residual:** the 2023 C3a mean-LMP miss (+17.9 %) is a separate
  energy-LEVEL residual and is **not** expected to move here. The diagnosis is explicit that
  even a perfect ST_GAS fix leaves C3a failing, so the determination stays NOT-YET either
  way. Do not judge this lane by C3a.

## 5. Acceptance criteria

A mechanism from this lane is promotable only if **all** of:

1. **Provenance** — a cited published instrument, with the rule-13 forward-regeneration test
   answered in writing in the attestation. No CAMPD-derived obligation levels.
2. **Rule 19** — it **replaces** (not stacks on) the NYC/LI `ST_GAS` floor limbs; the D-2
   attribution shows one mechanism owning the class, not two.
3. **Shape, not just level** — the added energy is **evening-concentrated**, matching the
   measured gap (2023: overnight gap 44 MW mean vs **evening gap 438 MW**). A fix that adds
   flat overnight volume is the floor-up probe again and is a fail. C7 D-1 `cv_ratio` must not
   regress.
4. **C8** — forced share stays within budget, or clears the rubric-v2.2 grounded-above-budget
   escalation on D-1 shape **and** a cited `D4_WINDOWS` entry in
   `scripts/legitimacy_diagnostics.py`.
5. **Rule 16 [R-ALLYEARS]** — solved and registered across **2023 2024 2025 in one bundle**.
   No 2024-only keeper.
6. **Leave-one-year-out** within 2023–2025 before promotion (rule 22 [R-HOLDOUT]); holdout
   years stay quarantined — NYISO carries **no** calibration-complete marker, so 2022 / 2019 /
   H1-2026 must not be solved, scored, or registered.

## 6. Expected scored effect (set expectations honestly)

Closing the full gap would move 2024 ST_GAS from −3.02 TWh toward zero and restore the C1
cell, and would matter more in 2025 (−5.12 TWh) once that benchmark finalizes. It would
**not** change the determination on its own: C3a / C3b / C3c fail independently. The value of
this lane is structural fidelity and the C1/C7 recovery, not a determination flip.

## 7. Session assignment

Rule 27 [R-PUSH]: this lane writes `src/market_sim/` and `scripts/`, so it is **Opus or Fable,
never Sonnet**. A pure data-intake-only sub-session (new files under `data/raw/` + this doc)
would be Sonnet-eligible, but only if it writes no engine code.
