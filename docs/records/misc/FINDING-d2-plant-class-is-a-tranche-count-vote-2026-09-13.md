# FINDING — **D-2's plant class is decided by a ROW-COUNT VOTE over LP tranches**, so any offer-curve band change can move TWh between class denominators and flip C8. Measured on NYISO; **SPP/SOCO is the most exposed ISO**

**Session** nyiso-232 · **Date** 2026-09-13 · **ZERO LP** (every number is read from committed
bundle artifacts and one on-recipe `fleet_only` rebuild).
**Owner of the affected code: whoever owns `scripts/legitimacy_diagnostics.py`. This lane does NOT
land the fix** — the blast radius reaches at least three ISOs and a NYISO lane cannot measure or
authorise that (rule 25 `[R-ISO-SCOPE]`).

---

## 1. THE DEFECT, in one sentence

`aggregate_floors_by_plant` assigns each plant the **"most common non-empty unit group"** among its
LP rows. The number of LP rows a class contributes to a plant is a property of the **offer curve's
band structure**, not of the plant's physics — so a mechanism that changes how many tranches a class
is split into can **flip a mixed plant's entire dispatch** from one class's D-2 denominator into
another's, with no change to the plant, its capacity, or its floors.

The docstring is explicit that the rule was chosen deliberately, and its stated rationale is sound —
*"a single plant frequently mixes classified units with an unbinned component … taking the first
unit's group let that lone empty label capture the whole plant"* (#1488). **The fix for that was
right; the weight is the bug.** Counting *rows* solved the empty-label problem and introduced a
dependence on tranche count.

## 2. MEASURED, on a real mechanism, with the flip identified to the row

nyiso-232 screened `nyiso_st_gas_econ_bands_deleaked`, whose declared and intended effect is to make
NYISO's `ST_GAS` econ ramp **flat** — which collapses its 6-slice `econc00..05` smoothing ladder to
`econlo`/`econhi`, i.e. **8 LP bands per ST unit → 4**. Nothing else about any plant changes.

**Two NYISO plants flip their D-2 class, and one is decided by a single row:**

| plant | control row counts | control label | arm row counts | arm label |
|---|---|---|---|---|
| **2500** (Ravenswood, the ~2.5 GW mixed NYC CC+ST site) | `ST_GAS` **8** vs `CC_REGULAR` **7** | **`ST_GAS`** | `ST_GAS` **4** vs `CC_REGULAR` **7** | **`CC_REGULAR`** |
| **2511** | `ST_GAS` **8** vs `CT_PEAKER` **4** | **`ST_GAS`** | `ST_GAS` **4** vs `CT_PEAKER` **4** | **`CT_PEAKER`** (tie) |

**Ravenswood's vote was 8–7.** One row.

**The consequence, in the committed diagnostics of both bundles:**

| D-2 `class_total_twh`, 2022 | control | arm | Δ |
|---|---:|---:|---:|
| `ST_GAS` | 8.571 | **5.705** | **−2.87** |
| `CC_REGULAR` | 35.986 | 38.414 | +2.43 |
| `CT_PEAKER` | 2.766 | 3.308 | +0.54 |

Roughly conserved (+0.10) — the energy is **moved between denominators**, not created.

**Meanwhile the physics went the other way.** Every dispatch-side measurement of ST_GAS energy shows
it **RISING**, because the mechanism makes ST_GAS cheaper and it runs more:

| ST_GAS 2022 energy, TWh | control | arm |
|---|---:|---:|
| `class_hourly` (P1) | 6.6384 | **7.3090** |
| `class_band_hourly` (P1) | 6.7047 | **7.3845** |
| `dispatch/2022_P1.parquet`, `klass` | 6.6384 | **7.3090** |
| dispatch joined by `unit_id` to the rebuilt fleet's `plant_group` | 6.7047 | **7.3845** |
| **D-2 `class_total_twh`** | **8.571** | **5.705** ← the only one that falls |

## 3. IT FLIPS C8, WHICH IS PROTECTIVE TIER AND HAS A ZERO CAVEAT BUDGET

The **numerator barely moves** — forced energy 1.9803 → 1.9187 TWh (**−3 %**) — while the
**denominator moves −33 %**. So:

| basis for the plant-class vote | control | arm |
|---|---|---|
| **row count (CURRENT)** | 1.980 / 8.571 = **23.1 % pass** | 1.919 / 5.968 = **32.2 % FAIL** |
| **capacity-weighted (STABLE)** | 1.980 / 8.571 = **23.1 % pass** | 1.919 / 9.232 = **20.8 % pass** |

*(The row-count reimplementation reproduces the committed control diagnostics exactly — 8.571 TWh,
23.1 % — which is what validates it. On the control the two bases agree to the digit, because no
plant's label differs there.)*

**A spurious C8 FAIL is expensive.** C8 is protective tier and the protective-caveat budget is
**zero**, so a run tripping it reads **NOT-YET** whatever else it does. Here the mechanism's real
effect on forced share is an **improvement** — 23.1 % → 20.8 %, because the same floors are a
smaller share of a class that now runs more — and the scorer reports it as a 30 %-cap breach.

## 4. FRAGILITY CENSUS — this is not a NYISO problem

Counted over every committed `floors/<year>_P1.npz` in the repository. **"Flippable"** = halving the
winning class's row count (the measured ladder-collapse effect) loses it the vote:

| bundle · year | plants | mixed | margin ≤ 2 | **flippable** |
|---|---:|---:|---:|---:|
| `soco15_spp_arm` 2023 | 293 | 23 | 23 | **23** |
| `soco15_spp_arm` 2024 | 294 | 25 | 25 | **25** |
| `soco15_spp_arm` 2025 | 313 | 23 | 23 | **23** |
| `nyiso231_anchor_span` 2022–2025 | ~285 | 7 | 3 | **7** |
| `caiso279_ablate_dswcouple_span` 2023–2025 | ~357 | 1 | 0 | **1** |

**SPP/SOCO is by far the most exposed**: every one of its 23–25 mixed plants sits at a margin of
≤ 2 rows, so *any* offer-curve band change in that lane can move class denominators. NYISO has 7
flippable of which 3 are within 2 rows. CAISO has 1.

*(The census covers only bundles whose `floors/` npz is committed — 10 files across 3 ISOs. ERCOT,
PJM, MISO and NEISO are **unmeasured here**, not shown to be clean.)*

## 5. THE PROPOSED FIX, and why this lane is not landing it

**Weight the vote by something physical and band-invariant — capacity (`pmax`) is the natural
choice.** The bands partition the same plant capacity however many of them there are, so a
capacity-weighted vote is invariant to tranche count by construction, while still solving the
original #1488 empty-label problem (empty groups are already excluded before the vote). It is a
one-line change to the accumulator in `aggregate_floors_by_plant`.

**This lane does not land it, for reasons that are about authority, not effort:**

* it is a **shared scorer** reaching all eight ISO columns, and §4 shows the effect is **not inert** —
  SPP/SOCO would very likely see real denominator moves;
* a NYISO lane cannot measure another ISO's verdict change (it has neither their data profile nor
  their keepers' context), and rule 25 `[R-ISO-SCOPE]` exists precisely to stop one lane deciding
  another's numbers;
* nyiso-232 **pre-registered this disposition before the investigation ran**
  (`PRECOMMIT-nyiso232-st-gas-deleak.md` Addendum A.5, outcome (i): *"the repair is the scorer's, it
  is reported and handed to whoever owns `legitimacy_diagnostics.py`, and C8 is re-scored on the
  corrected basis"*), so the conclusion cannot have been fitted to what it does for this lane.

**What the owning lane should do**, in order: land the capacity-weighted vote behind a measurement of
every ISO's D-2 rows before/after; expect **SPP/SOCO to move**; treat any C8 verdict change there as
a correction, not a regression — the current number is the artifact.

## 6. WHAT THIS FINDING DOES NOT CLAIM

It does **not** claim D-2 is wrong in general: the mechanism attribution, the floor-energy
convention, the `FloorClassMatrix` per-hour class, and the empty-label imputation are all untouched
and all sound. The defect is **one weight in one vote**.

It does **not** re-score any registered run. NYISO's nyiso-232 keeper is reported with the C8 result
its **current** scorer gives, at full magnitude, beside this demonstration — the official verdict is
the scorer's, not this document's.

It does **not** rest on the arm being a good mechanism. The flip is a property of the **band
structure**, and would occur identically for any change that collapses or expands a class's econ
ladder, including one nobody wants.

## 7. RULES

1 `[R-STRUCT]` — the defect is identified by what the mechanism would have to be (a physical class
label cannot depend on tranche count), never by what it does to a residual; the finding is reported
even though it favours this session's own arm. 13/14 `[R-MEASURED]`/`[R-ACCURATE]` — every number is
measured on committed artifacts; the accurate basis is preferred and the inaccurate one is not buried.
19 `[R-ONE-MECH]` — one weight, one phenomenon. 25 `[R-ISO-SCOPE]` — the reason this lane reports
rather than fixes. 28 `[R-MECH-MATRIX]` — no mechanism verdict rests on this. 32 `[R-SHARD]` — zero LP.
