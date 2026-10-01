# PRECOMMIT — nyiso-233: replace D-2's ROW-COUNT plant-class vote with a CAPACITY-WEIGHTED vote

**Session** nyiso-233 · **Date** 2026-09-13 · **ZERO LP** (rule 32 `[R-SHARD]` (a): the parent never
solves; every number here comes from committed bundle artifacts plus `run_year(fleet_only=True)`
fleet rebuilds, which build no LP).

**AUTHORISATION.** This is a **SHARED SCORER** change reaching every ISO column, which rule 25
`[R-ISO-SCOPE]` forbids a NYISO lane from deciding on its own. It is made under an **explicit owner
ruling given in this session**, answering the question nyiso-232 pre-registered and left open
(`docs/RESULT-nyiso232-st-gas-deleak-screen-2026-09-13.md` §11.5): *measure every ISO, then land the
capacity-weighted vote.* The ruling also settled the disposition of any verdict change elsewhere:
**a C8 move in another ISO is a CORRECTION, not a regression — the current number is the artifact.**

---

## 1. THE DEFECT (established, not re-litigated)

`scripts/legitimacy_diagnostics.py::aggregate_floors_by_plant` labels each plant with its **most
common non-empty unit group counted in LP ROWS**. How many rows a class contributes to a plant is a
property of the **offer curve's band structure**, not of the plant — so any mechanism that collapses
or expands a class's tranche ladder can move a whole site's dispatch between class denominators with
no physical change at all.

Proved and committed by nyiso-232:
`docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md`, probe
`scripts/probes/_nyiso232_d2_plant_class_vote.py`. **That finding is not re-opened here** (rule 28(a)
DO-NOT-REDO); this PRECOMMIT only governs the repair.

The docstring's stated rationale for voting at all is **sound and is preserved**: a plant frequently
mixes classified units with an unbinned component, and taking the first unit's group let a lone empty
label capture the whole plant (#1488). Empty groups are excluded before the vote and stay excluded.
**The fix for #1488 was right; the WEIGHT is the bug.**

## 2. THE CONSTRUCTION

**Weight each class's claim on a plant by the capacity (`pmax`) its rows carry, not by how many rows
they are.**

```
        nonempty rows of plant p          ->  group g wins iff  sum(pmax[r] for r in p, group(r)==g)
                                              is maximal  (ties: first in sorted order, unchanged)
```

**Why capacity and not something else** — recorded now so the choice cannot be re-read later as
fitted:

* **Band-invariant by construction.** The bands of a plant-class partition that class's capacity
  however many bands there are, so the vote cannot move when a ladder collapses. That is the exact
  property the defect violates, so it is the property the repair must have.
* **Solve-invariant.** It depends on no dispatch outcome, so a plant's class denominator is a
  property of the plant, full stop. **Energy-weighting was considered and REJECTED for this reason**:
  it is measurable from the committed dispatch parquet with no fleet rebuild at all, and it *is*
  band-invariant — but it re-introduces instability under a mechanism change through a different
  door, because the arm and control would legitimately label a plant differently when dispatch moves.
* **Zero free parameters, zero new literals, no DOF entry** (rules 21 `[R-DOF]`, 24 `[R-REGISTRY]`).
  It is a change of weight in an existing accumulator, not a tunable.
* **It is not selected by what it does to NYISO.** The justification is structural (rule 1
  `[R-STRUCT]`): a physical class label cannot depend on tranche count. It is landed whichever way
  any ISO's C8 moves, NYISO's included — see §5.

## 3. THE ONE REAL ENGINEERING PROBLEM, AND HOW IT IS HANDLED

**`floors/<year>_<pass>.npz` does not carry `pmax`.** Measured on all 10 committed npz: the keys are
`min_gen, mechanism, unit_ids, plant_code, plant_group`. So the weight is not available from the
artifact the scorer prefers to read.

Handled in three parts, and the third is the one that matters:

1. **Both writers gain `pmax`** — `scripts/run_calibration_full.py::_save_floor_arrays` (solve-time)
   and `legitimacy_diagnostics.load_or_rebuild_floors` (the `_rebuilt.npz` cache). Future bundles
   carry it.
2. **Old npz are BACKFILLED, exactly and at zero LP**, by joining the committed npz's `unit_ids`
   to a `run_year(fleet_only=True)` rebuild's `pmax`. `pmax` is a fleet property that no P0/P1 pass
   changes, so the backfill is exact — and crucially the **floors themselves stay the committed real
   P1 floors**, so nothing about the numerator is reconstructed. Measured on NYISO 2022: rebuild
   24.9 s, **715/715 npz unit_ids resolve, 0 missing**; the join is BY `unit_id` because the orders
   differ (`identical order=False`) — positional alignment would be silently wrong.
3. **There is NO silent fallback.** If `pmax` cannot be obtained the vote falls back to row count
   **and records `plant_class_vote_basis` in the diagnostics JSON**, so no run can ever be scored on
   the defective basis without saying so. A recorded basis is the difference between a fallback and
   a hidden dependence.

## 4. WHAT WILL BE MEASURED (declared before the numbers are read)

Every bundle in the repository carrying a committed `floors/<year>_P1.npz`, on **both** bases:

| ISO | bundle | years | status |
|---|---|---|---|
| NYISO | `nyiso232_deleak_span` | 2022–2025 | **the designated keeper** |
| CAISO | `caiso279_ablate_dswcouple_span` | 2023–2025 | not CAISO's keeper |
| SPP | `soco15_spp_arm` | 2023–2025 | not SPP's keeper |

Reported per ISO-year: mixed plants, label flips row→capacity, D-2 `class_total_twh` per class on
each basis, and the **C8 forced share** of every class the rule-20 `[R-FORCED-BUDGET]` materiality
floor gates, against its 30 % (peakers 15 %) cap.

**ERCOT, PJM, MISO and NEISO carry no committed `floors/*.npz` anywhere reachable** (checked on
`main` and on all four live `claude/soco-15-*` branches). They are **UNMEASURED, not shown to be
clean**, and that is reported as a limit of this measurement rather than as an absence of effect.

## 5. THE DECISION RULE (pre-registered — this is what stops the conclusion being fitted)

**LAND unless a stop condition below fires.** The direction any ISO's C8 moves is **not** a
criterion, in either direction, for NYISO or anyone else. In particular: **that the repair restores
NYISO's own determination is NOT evidence for it**, and would not be quoted as such.

**STOP conditions** — any one blocks the landing and is reported as the session's result:

* **S1 — the partition premise fails.** If a plant-class's band `pmax` do not partition that class's
  capacity (e.g. bands overlap, or `pmax` is zero for a material share of floored rows), capacity is
  not band-invariant and the construction is wrong.
* **S2 — the #1488 fix regresses.** If any plant that today gets a non-empty label would fall back
  to `''` under capacity weighting, the repair has broken what the vote exists to do.
* **S3 — the backfill is not exact.** If npz `unit_ids` do not resolve into the rebuilt fleet, or a
  resolved `pmax` disagrees with the solve's, the weight is reconstructed rather than measured and
  rule 13 `[R-MEASURED]` is engaged.
* **S4 — blast radius beyond D-2/D-4.** If the plant label feeds any consumer outside the D-2/D-4
  diagnostics (a price, a dispatch, a determination path other than C8), this stops being a
  diagnostics repair and needs its own screen.

## 6. WHAT THIS DOES *NOT* DO

* It does **not** re-score any historical run on a corrected basis retroactively. NYISO's keeper is
  re-scored because **the scorer changed**, which is scoring on the current scorer — not the
  forbidden move of re-reading an old verdict through a basis this lane invented.
* It does **not** touch the mechanism attribution, the floor-energy convention, the
  `FloorClassMatrix` per-hour class, or the empty-label imputation. **One weight in one vote.**
* It does **not** change any ISO's offer curve, any `ScenarioConfig` field, or any solve path. No
  mechanism-matrix cell moves on account of it (rule 28) — it is a scorer repair, not a mechanism.
* It arms nothing and it is not an authorized price-tuning channel (rules 1/13): it cannot move a
  price at all.

## 7. RULES

1 `[R-STRUCT]` structure over residual — the repair is justified by what a class label must be.
13/14 `[R-MEASURED]`/`[R-ACCURATE]` — capacity is measured, the accurate basis is preferred, the
inaccurate one is reported not buried. 19 `[R-ONE-MECH]` — one weight, one phenomenon.
21/24 `[R-DOF]`/`[R-REGISTRY]` — zero free parameters. 25 `[R-ISO-SCOPE]` — the owner ruling is what
authorises a cross-ISO change; no ISO's fitted number is transferred. 31 `[R-RETAIN]` — nothing is
deleted. 32 `[R-SHARD]` — zero LP in the parent.
