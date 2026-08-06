# FINDING — ercot-174: the unit-attributed partial extract is BUILT and PROVEN, and it REFUTES the premise of the successor it was built for — the window and partial layers share units at **94–96 %** of both-active bin-hours, so the unit-scoped composition IS the rejected blanket arm (ρ = 0.94/0.96/0.96). Pre-registered STOP fired; **NO LP RUN**

**Session ercot-174, 2026-08-06.** Charter: the ercot-173-named successor — the
UNIT-ATTRIBUTED partial-outage extract, the route to (a) the 2024 event-cap
ceiling defect and (b) the ercot-167 SOC re-gate. Decision rules, the
composition rule, the proofs, the predictions and the **stop rules** were
pre-registered and pushed **before the derive was built**
(`docs/PRECOMMIT-ercot174-unit-attributed-partial-outage-2026-08-06.md`); the
kill gates are `PRECOMMIT-ercot172` §5 inherited verbatim. Keeper **UNCHANGED**
at `2026-08-05-run168b-year-curves`. **No run was solved, so none is
registered** — the pre-registered AT-2 stop rule fired before the solve, which
is exactly the contingency the handoff anticipated ("if the measured movement
approaches the ercot-173 blanket numbers the unit attribution is wrong, stop").

---

## 0. Verdict

| | |
|---|---|
| **PHASE A** (unit-attributed derive) | **DELIVERED and PROVEN** — BE-1/BE-2/BE-3 all PASS |
| **PHASE B** (unit-scoped composition) | **BUILT**, one default-off gate, zero fitted scalars, seam-proven inert at its default |
| **AT-2 (pre-solve STOP RULE)** | **FIRED in all three years** — ρ = **0.9381 / 0.9585 / 0.9606** against a 0.5 stop bar |
| **LP A/B** | **NOT RUN**, as pre-registered |
| **ercot-167 SOC re-gate** | **STAYS UNMET** — nothing landed (identical to ercot-173) |
| **`FINDING-ercot173` §3 premise** | **REFUTED by measurement** |

---

## 1. PHASE A — the extract exists, and the grain is the only change

`scripts/data/derive_partial_outages.py --emit-units` writes
`data/raw/campd-partial-outages-units.csv` from the **same detection pass** as
the plant-grain file: same plateaus, same `derate_factor`s, now carrying which
CAMPD units carry each one, their `unit_capacity_mw`, `capacity_source`, and
the unit's own measured `ceiling_ratio`. The detector's frozen identification
constants (`_MIN_DAYS`, `_SMOOTH_DAYS`, `_CEILING_FRAC`, `_RUN_FLOOR_CF`,
`_BASELOAD_CF`) are **imported verbatim and never re-valued** (rule 23
`[R-FROZEN-DERIVE]`); the carry test is the plant detector's own
depressed-ceiling test evaluated on the unit's own series, so **zero** new
scalars enter.

**The byte-equivalence proof (all three PASS):**

* **BE-1** — the unmodified deriver reproduces the committed extract over
  2018–2026, sha256 `8d6f049e…c736b5`.
* **BE-2** — with the attribution code in place, the plant-grain file the same
  run writes is **sha256-identical** to the committed extract (same hash).
* **BE-3** — projecting the companion onto the seven committed columns and
  de-duplicating reproduces the plant-grain frame **exactly**: 501 plateaus
  round-trip, same order, same values. Asserted **inside the deriver** (a
  failure is stop-the-line) and again in
  `tests/unit/data/test_outages.py::UnitScopedEventCapCompositionTest`.

909 unit-attributed rows; **498 of 501** plateaus resolve to at least one
carrying unit. Coverage is per year 2018–2026, applied consistently across the
whole span (rule 22's 2026-08-06 amendment: *data is never held out; only the
score is*). Emitted at 2018–2026 because that is the committed extract's own
span and BE-2/BE-3 are only meaningful over it.

**The attribution is exact, not approximate.** Limestone 2024 is the
canonical case, and it verifies the construction end to end: the window layer
carries `LIM1 2024-01-01 → 01-08` (a 893.0 MW full stop of an 1,849.8 MW
plant); the partial layer carries a `2024-01-01 → 01-09` plateau at
`derate_factor 0.416` — and the attribution assigns it to **LIM1**, alone
(`n_units_carrying = 1`), date-aligned to the day. **They are the same event,
measured twice.** The incumbent product holds the plant at
`0.5172 × 0.4160 = 0.2152` of nameplate while LIM2 — 51.7 % of the plant — ran
normally.

---

## 2. PHASE B — the mechanism, built and seam-proven

`ScenarioConfig.ercot_dam_availability_event_cap_unit_scoped`, **default off**,
one gate, zero fitted scalars, registered in the cache-key default-drop list
and in the matrix in the same PR. Inside the existing ERCOT-148/149 cap block
(no second layer, rule 19 `[R-ONE-MECH]`), per scoped bin `b` and hour `t`:

```
ceil(b,t) = min(f_window, f_partial)   if  U_window(b,t) ∩ U_partial(b,t) ≠ ∅
            f_window × f_partial       otherwise
```

with both unit sets routed through the **same** `_unit_outage_target` the
factors themselves use, and ids matched after normalisation. An unattributed
plateau leaves the set empty ⇒ product ⇒ incumbent (fail-safe). The rejected
ercot-173 blanket gate is **kept at default-off with its `R` verdict intact**
(a boolean structural gate, not a fitted knob — the
`ercot_storage_rt_offer_surface` precedence); the unit-scoped gate takes
precedence when both are set.

**Seam proof — a 2024 capture TRIPLE off the ercot-173 control recipe (A =
gate at default, B = both event caps off, R = armed), all five PASS**
(`scripts/probes/ercot174_seam_proof.py`):

| | result |
|---|---|
| **SP-1** | arm `== min(B, ceil_unit_scoped)` on every layered scoped tranche, max dev **2.9e-08** |
| **SP-2** | **600** out-of-scope tranches byte-identical A vs R |
| **SP-3** | C1 inert on all **20** partial-extract bins |
| **SP-4** | gate at its DEFAULT reproduces the incumbent product exactly, `A == min(B, product)`, max dev **2.7e-08**, on all **158** layered scoped tranches |
| **SP-5** | `product ≤ unit-scoped ≤ min` pointwise and the ceiling is two-valued — **158** layered bins, **154** carrying a shared unit |

*(SP-1 needs the PRE-CAP capture B, not A: the unit-scoped ceiling restores, so
`min(A, ceil)` collapses to `A` and would be a vacuous check. The first
formulation of this probe made that error and it was caught by the proof
failing, not by inspection.)*

Measured seam movement, 2024: **150** tranches changed, max **+0.2500**, min
**0.0000** — the restore-only property of §3c holds empirically, the arm never
removes more than the control anywhere.

---

## 3. THE RESULT — AT-1/AT-2, and what they refute

`scripts/probes/ercot174_attribution_check.py` →
`results/calibration/ercot174_attribution_check.json`. No LP; read straight
from the loaders the cap block itself uses.

| year | both-layers-active bin-hours | **min()-composed (AT-1)** | share | **AT-2 ρ** | stop bar 0.5 |
|---|---|---|---|---|---|
| 2023 | 22,128 | 20,904 | **94.47 %** | **0.9381** | **FIRED** |
| 2024 | 27,958 | 26,806 | **95.88 %** | **0.9585** | **FIRED** |
| 2025 | 28,173 | 27,093 | **96.17 %** | **0.9606** | **FIRED** |

ρ is the share of the **rejected** ercot-173 blanket arm's total ceiling lift
that survives unit scoping. At ρ ≈ 0.95 the unit-scoped arm is not a refinement
of the blanket arm — **it is the blanket arm**, and the pre-registration is
unambiguous: *"If ρ ≥ 0.5 in any year, STOP before the solve … Report as an
attribution failure, do not solve, do not promote."*

**Robustness — REPORTED, explicitly NON-SELECTING** (a pure reprojection of the
extract's own `ceiling_ratio`; the frozen `_CEILING_FRAC` remains the
mechanism). The verdict does not depend on the threshold anywhere in its range:

| carry test | 2023 | 2024 | 2025 |
|---|---|---|---|
| frozen `< 0.65` | 0.9381 | 0.9585 | 0.9606 |
| `< 0.50` | 0.9322 | 0.9414 | 0.9606 |
| `< 0.30` | 0.8949 | 0.9414 | 0.9606 |
| `< 0.10` | 0.8686 | 0.9282 | 0.9606 |
| `< 0.02` (unit essentially dead all window) | **0.8686** | **0.9174** | **0.9606** |

Even demanding the unit be **dead through the entire plateau**, ρ stays
0.87–0.96. Looser tests need no measurement — attribution is monotone, so ρ can
only rise. **No attribution threshold exists that separates this arm from the
rejected one**, and none was hunted for: the band is reported, never selected
on.

### 3a. What is refuted

`FINDING-ercot173` §3 read the blanket rejection as: the layers "measure the
SAME units' downtime at some overlaps … and **DIFFERENT** units' downtime at
**most others** (there the product is right and `min()` under-removes)." That
inference was made at *composition* grain, because no unit attribution existed.
Now that one does, it is **measured, and it is false**: the layers share units
at **94–96 %** of the hours where both are active.

The reason is structural and, in hindsight, mechanical. The partial detector
runs on **plant-aggregate** CF. When one unit of a multi-unit plant goes down
for ≥ 5 days, the window layer catches it at unit grain **and** the plant's
aggregate ceiling collapses, which the partial detector re-reads as a plateau —
**the same outage, detected twice, by two instruments, from one CEMS record**.
That is not an edge case at ERCOT's multi-unit baseload fleet; it is the normal
case.

### 3b. What this means for the object — the collision, surfaced not decided

The double-count ercot-172 named is **real and pervasive**, now quantified.
Every admissible way of removing it — blanket `min()` (ercot-173), unit-scoped
`min()` (this session), or the finer-grain variant noted below — restores
**1–2.7 TWh/yr** of coal above the ERCOT-148/149 product ceiling, because
94–96 % of the composition *is* the double-count. So:

> **The ERCOT-148/149 product ceiling and the removal of the double-count
> cannot both stand.** They are not reconcilable by any choice of composition
> rule, and no unit-grain refinement changes that — which is precisely what
> this session was built to test, and what it has now settled.

That is an **owner adjudication**, not a mechanism choice, and it is surfaced
here, not taken. G-COAL148 has done its job twice: it exists to force exactly
this collision into the open rather than let a session quietly repeal a prior
adjudication, and it is not argued past here.

Two further facts belong to that adjudication:

* **`min()` is not even the right reconciliation at a shared-unit hour.** Where
  both instruments measure the same unit, the **finer-grained** one should win,
  not the numerically deeper one — the window layer resolves LIM1 exactly
  (893.0/1,849.8) while the partial layer estimates it from the plant aggregate
  (0.416). `min()` picks the coarser estimate. The correct variant is *more*
  restorative than `min()`, so it moves G-COAL148 further the same way; it is
  named here and **not built**.
* **Neither composition closes the ercot-172 object.** At h2827 W A Parish the
  unit-scoped ceiling is 0.3630 against a same-hour CEMS of **0.7843** —
  ercot-172 fault 3 (a multi-week flat plateau used as an hourly ceiling) is
  untouched by any composition rule, exactly as ercot-172 predicted of C2
  ("C2 helps but does not close the object alone").

### 3c. P-2024 / P-NULL — the pre-registered falsifier, resolved

**P-NULL did NOT fire**: the ercot-172 named plants *are* shared-unit overlaps,
so the arm is far from inert. At h2827 (2024-04-28 19:00) the shared-unit test
is TRUE at W A Parish (0.2539 → 0.3630), Martin Lake (0.3347 → 0.5020),
J K Spruce (0.0791 → 0.2080) and Guadalupe (0.2410 → 0.4820) — the ercot-173
restorations reproduce. At h3067 only Martin Lake (0.1673 → 0.3333) and two CC
plants move. **P-2024's mechanism prediction is confirmed and the arm would
very likely have cleared G-SHED again** — but that is not the question the
session turns on: the *fleet-wide* behaviour is the rejected arm's, so its
G-COAL148 / G-SPAN / G-C3c failures would reproduce at ~95 % strength. No solve
was needed to know that, and none was spent.

---

## 4. Gates and the ercot-167 re-gate

The `PRECOMMIT-ercot172` §5 gates were inherited verbatim and are **not
adjudicated**, because no arm was solved: G-SPAN, G-SHED, G-SPUR, G-C3c,
G-COAL148, G-D2 and LOYO all require a solved A/B pair and are recorded
**NOT REACHED**. Two are decidable without one and both **PASS**: **G-DOF**
(zero new fitted scalars — the attribution imports the detector's frozen
constants and the composition adds none) and **G-BIT**, declared **N/A
pre-solve** with its reason recorded (a year-agnostic rule ⇒ G-SPAN replaces
it, per §3c(a)). **G-NEUT** is not reached: no event-window population is
restricted.

**ercot-167 SOC re-gate: STAYS UNMET.** `FINDING-ercot167` §3's reopen
condition is *"after the 2024 defect's fix LANDS"*, and **nothing landed** —
identical to ercot-173. RG-1/RG-2 are not re-scored here (that needs a solved
pair). What ercot-173 established stands unchanged: the kills *do* clear when
the 2024 ceiling defect is corrected; what this session establishes is that
**no unit-scoped correction can be the thing that corrects it**, so the
discharge path the handoff named is **CLOSED**.

---

## 5. Governance

Rule 15/16: **no run was solved, so none is registered** — stated explicitly so
the absence is not read as a skipped registration. Rule 22: no solve at all,
and no out-of-training year scored or registered; the derive spans 2018–2026 as
**data prep**, which the 2026-08-06 amendment places outside the spend gate
("prep it, apply it to every year, keep it consistent"). Rule 23: the derive
change is **grain only**, proved by BE-1/2/3; no identification constant
re-valued. Rule 24: the new gate is a registered `ScenarioConfig` field,
cache-key-dropped at its default. Rule 25: ERCOT-scoped. Rule 26: §2 — the
rejected blanket gate is a boolean structural gate, not a fitted knob, and is
kept at default-off with its `R` verdict (precedent
`ercot_storage_rt_offer_surface`). Rule 27: every push blob-verified. Rule 28:
the new field's matrix row lands in the same PR; §5.1 gains **item 17**; the
`ercot_dam_availability_event_cap_reconciliation` cell, both event-cap cells
and the `ercot_storage_as_soc_reserve` cell are re-stamped with this outcome.

**No new curated datatype** was minted: the companion is read from raw exactly
like its siblings `campd-unit-outages-short-<ISO>.csv` and
`campd-partial-outages-<ISO>.csv`, so the schema/clean contract is not engaged.

**Tests**: `UnitScopedEventCapCompositionTest` (5 cases — per-hour AND
semantics, fail-safe on an absent side, normalised id matching, unit-set /
factor-layer consistency, and BE-3 on the committed files). Pre-existing
failure `NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty`
re-verified pre-existing by stash (fails on unmodified code), as at ercot-173.

**DO-NOT-REDO honoured in full** — the blanket `min()` composition stays `R`
and was not re-opened; no depth lever; no coal offer lane; no storage offer
surface; no aggregate or per-hour telemetered-HSL cap; West/Panhandle topology
stayed closed; ercot-172's C3 not attempted; the CC-headroom crosswalk stays
FILED-UNLICENSED; no `--year` outside 2023–2025 (and in the event, no solve).

**Surfaced, NOT decided:**

1. **The ERCOT-148/149 ↔ double-count collision** (§3b) — now quantified at
   94–96 % and unavoidable by any composition rule. Owner adjudication.
2. **The finer-grain-wins variant** at shared-unit hours (§3b), named and not
   built; it is strictly more restorative than `min()`.
3. **ercot-172 fault 3** — the multi-week flat plateau used as an hourly
   ceiling — is the residual defect no composition rule reaches, and is the
   only remaining structural route to the 2024 object.
4. **The run168b keeper does not reproduce at current main** (ercot-173 §5,
   carried forward untouched): C3a-2023 −28.48 % vs committed −29.88 %, 2023
   spurious 10 vs ledgered 3, tail 66 vs 61, a fifth 2023 shed hour. Re-key vs
   re-solve at HEAD is a governance question for the owner.

**Not a keeper candidate.** No arm was solved; the pre-registered stop fired
first. The deliverable is the extract, the proof that its grain is the only
change, the mechanism, and the measurement that closes the route.

**Next shorthand: ercot-175.**
