# PRECOMMIT — SPP-49 (2026-09-19): the benchmark-membership defect

**Base:** `8cb4d9c9184376bb328d64123fd5a3a07e611fb9` (the SPP-48 PROMOTION branch
`claude/spp-mid-vintage-retiree-gap-vv07l6`, checked and found **NOT** an ancestor of
`origin/main` at `995f7b7e` — so it is this lane's base, per the handoff's instruction).
**Lane branch:** `claude/spp-benchmark-membership-defect-4yqm2f`.
**Keeper:** `2026-09-16-spp-42-commitment-feasibility` (`spp42_span_a`, 2023–2025) — **UNTOUCHED,
and proven un-movable by this mechanism.** 2019–2022 rung: `2026-09-19-spp-48-midvintage-exit`.
**Object:** the successor SPP-48 §4 filed — *the model and the actual disagree about which plants
exist*.

**Everything below is ZERO LP.** No solve was run in this session (rule 32(a): the parent never
solves). Nothing is armed; nothing is registered; no keeper moved.

---

## 0. Headline

1. **SPP-48's measurement reproduces exactly, and the mechanical cause is now pinned to one line.**
   `zone_assignment._EIA860_PLANT_PATH` is a **module-level constant bound at import** to the
   canonical `EIA_860_DIR`, never to `paths.active_eia860_dir()` — so the benchmark's EIA-860
   supplement *cannot* follow `eia860_vintage_tracks_solve_year`, whatever a run's config says.
2. **The blast radius is far larger than SPP, and it is not one defect but two.** A cross-region
   census over all nine registered regions finds plants missing from every one of them. **PJM is
   the largest by an order of magnitude — 857 plants, 8.8 TWh absent from its 2025 ACTUAL, a live
   keeper year — for a *different* reason: PJM is not in `_EIA860_SUPPLEMENT_ISOS` at all.**
3. **The repair shape was chosen on measurement, and the obvious variant was refused.** A
   year-matched **REPLACE** deletes real metered generation in **7 of 9** regions (SOCO 2024
   −7,275.9 GWh). The **ADDITIVE UNION** is monotone and cannot. Rules 13/14.
4. **Built, gated default-OFF, and proven byte-identical off** — the flag-off rebuild reproduces
   SPP-48's HEAD hash `eia923-78357736757d` **exactly**.
5. **SPP's keeper years are INERT at row grain**, so arming SPP cannot move keeper 12 — pinned by
   a test as a stop-the-line tripwire.
6. **A second, independent defect is reported and NOT folded in:** `rebuild_benchmark` does not
   reproduce the solve path's own benchmark for a config that changes the fleet.

---

## 1. Phase 0.1 — the measurement, reproduced and then explained

`scripts/probes/_spp48_benchmark_membership.py`, one interpreter per vintage, re-run at this
lane's base:

| vintage | active dir | n_plants | plant 127? |
|---|---|---|---|
| none | `eia-860` | 830 | False |
| 2019 | `vintage_2019` | 830 | False |
| 2020 | `vintage_2020` | 830 | False |
| 2021 | `vintage_2021` | 830 | False |
| 2022 | `vintage_2022` | 830 | False |
| 2023 | `vintage_2023` | 830 | False |

Membership **invariant across vintages: True**. Plant 127 absent from **every** one.

**Why**, measured rather than inferred — and this is what SPP-48 did not yet have:

```
_EIA860_PLANT_PATH  = data/raw/eia-860/eia860_plant.parquet
canonical EIA_860_DIR = data/raw/eia-860          BOUND TO CANONICAL: True
eGRID 2023: 12,612 rows, plant 127 present: False   (eGRID SWPP plants: 661)
```

| EIA-860 plant file | plant 127 | BA | SWPP rows |
|---|---|---|---|
| canonical (2025 ER) | **ABSENT** | — | 828 |
| vintage_2018 | **PRESENT** | SWPP | 634 |
| vintage_2019 | **PRESENT** | SWPP, lat 34.0825 / lon −99.1753 | 654 |
| vintage_2020 | **PRESENT** | SWPP | 687 |
| vintage_2021–2024 | ABSENT | — | 704 / 724 / 739 / 807 |

So the data has been there the whole time. **The supplement reads the wrong file** — and, because
the constant binds at import, no config can redirect it.

### 1.1 The asymmetry, stated as the defect

The **LP fleet** has a fallback-zone path for a plant eGRID lacks (`"N of M SPP generators not in
eGRID lookup — assigned fallback zone"`). The **benchmark** applies a hard `isin` with **none**.
A mid-window retiree is therefore **in the model and out of the actual at the same time**, and C1
reads a miss that is partly an artifact of two different membership rules.

### 1.2 There are TWO membership gates, and only one of them is broken

| gate | what decides it | follows the year? |
|---|---|---|
| 1. `_iso_plant_ids` → `build_zone_lookup` — the `isin` on EIA-923 | eGRID-2023 + canonical-bound supplement | **NO** |
| 2. `group_by_code` → `_fleet_group_by_code` — the CAMPD backfill | the model **fleet** for that year | yes |

Gate 2 already tracks the fleet. Gate 1 tracks nothing. That asymmetry *is* the object.

---

## 2. Phase 0.2 — the blast-radius census, EVERY registered region

`results/calibration/_spp49_membership_census.json`. Plants in the ISO's EIA-860 BA footprint in
some committed vintage but **absent from `build_zone_lookup`**, with the EIA-923 generation they
carry:

| ISO | lookup | vintage union | missing | GWh by year |
|---|---|---|---|---|
| CAISO | 1,989 | 2,071 | 82 | 2022 175.0 · 2023 24.5 · 2024 144.6 · 2025 1,259.1 |
| ERCOT | 1,406 | 1,442 | 37 | 2021 1.5 · 2022–25 0.0 |
| MISO | 2,861 | 3,001 | 143 | 2020 8,037.0 · 2021 4,524.8 · 2022 4,449.1 · 2023 1,628.5 · 2024 1,745.2 · 2025 1,176.3 |
| NEISO | 1,561 | 1,606 | 45 | 2020 358.0 · 2021 326.8 · 2022 152.5 · 2023–25 0.0 |
| NWPP | 1,083 | 1,125 | 43 | 0.0 every year |
| NYISO | 1,257 | 1,284 | 28 | 2022 134.2 · 2023–25 0.0 |
| **PJM** | **1,727** | **2,584** | **857** | **2020 10,131.7 · 2021 9,185.3 · 2022 5,145.6 · 2023 169.9 · 2024 2,597.0 · 2025 8,991.2** |
| SOCO | 413 | 423 | 12 | 2023 1,128.1 · 2024 1,433.0 · 2025 1,137.6 |
| SPP | 830 | 850 | 20 | 2019 2,668.5 · 2020 1,127.3 · 2021 4.2 · 2022 0.5 · 2023 0.7 · 2024 0.2 |

### 2.1 PJM is a SECOND defect, not a bigger instance of this one

`_EIA860_SUPPLEMENT_ISOS = {ERCOT, CAISO, NYISO, NEISO, MISO, SPP, NWPP, SOCO}` — **PJM is not a
member.** Its benchmark membership is therefore **eGRID-2023 only**, with no EIA-860 supplement of
any kind. That is why its gap is 857 plants rather than a few dozen, and why it is live in 2024
and 2025 (post-eGRID new build) as well as in the retiree years.

**8,991.2 GWh absent from PJM's 2025 ACTUAL, on `2026-09-11-pjm-d4-4-gasoutage`'s own scored
span.** This lane does not touch it: it is PJM's to decide, and the right repair there may simply
be adding PJM to the supplement set — a different object with a different blast radius. Recorded
so it is not rediscovered.

### 2.2 The sub-classes the census separates

* **Mid-window retirees** (the SPP-48/49 object): SPP 127, PJM 6019/2840/8226, MISO 856/1060.
* **Post-eGRID new build**: PJM's 2024/2025 cohort — a supplement gap, not a retiree gap.
* **BA-switchers**: MISO 57623 / 61344 (MISO in vintage_2018 only, PJM thereafter, still ~1.18 TWh
  in 2025); MISO∩SPP 56013 / 56478 / 56859. These are the double-count hazard, and they are why a
  **year-agnostic** union is wrong.

---

## 3. Phase 0.3 — the repair shape, decided on measurement

### 3.1 Option (a) — "give the benchmark the same fallback the fleet has" — REJECTED as a category error

The fleet's fallback assigns a **zone** to a plant already known to be in the ISO. The benchmark's
`isin` decides **membership** over *national* EIA-923. There is no "fallback membership": the
analogue would be admitting every US plant, which is the exact leak `_iso_plant_ids`' docstring
exists to prevent (PRB coal would read the ~639 TWh national figure). Rejected on construction,
not on a residual.

### 3.2 Option (c) — "union the retiree record" — SUBSUMED

The retiree sheet is one source of plants absent from canonical, but it carries no BA code and no
year. The vintage **plant file** carries both, so (b) does (c)'s job and more.

### 3.3 Option (b) STRICT (year-matched REPLACE) — BUILT AND REFUSED ON MEASUREMENT

| ISO | year | STRICT would DELETE |
|---|---|---|
| SOCO | 2024 / 2025 | **−7,275.9 / −6,168.9 GWh** |
| PJM | 2020 | **−9,077.7 GWh** |
| ERCOT | 2024 / 2025 | −599.9 / −564.0 GWh |
| SPP | 2019–2023 | −893.1 / −879.7 / −828.8 / −892.6 / −537.5 GWh |
| MISO | 2020 / 2022 | −6.3 / −0.3 GWh |

Seven of nine regions lose real metered generation. SOCO is the sharpest case: plant 55242
generates 1.13–1.43 TWh/yr **through 2025** but carries a SOCO BA code only in vintage_2018–2021,
so a tidy year-matched rule would erase it. That is "rescaling an input so the model's output
lands on the actuals" (rule 13 `[R-MEASURED]`) and "burying the error back inside an inaccurate
input" (rule 14 `[R-ACCURATE]`) — **the same refusal SPP-48 made of a HEAD rebuild.** Refused.

### 3.4 Option (b) ADDITIVE — CHOSEN

For benchmark year `y`, membership = `build_zone_lookup(iso)` **UNION** the plants BA-coded to the
ISO in the vintage covering `y` (hold-last to canonical past the final committed vintage).

Four properties, each measured rather than asserted:

1. **Monotone.** The union never removes a plant, so it can only ever *add* real metered
   generation. This is the whole rules-13/14 safety argument.
2. **It cannot invent generation.** An admitted plant contributes exactly what EIA-923 reports for
   that year; a retiree with no rows in the scored year adds nothing.
3. **Config-independent.** Driven by the run's *year*, not by `eia860_vintage_year` — so the
   benchmark stays a pure function of `(iso, year)` and the reference data, the property
   `rebuild_benchmark`'s own docstring relies on.
4. **No double count with gate 2.** The CAMPD backfill's firing test skips any plant whose mapped
   class EIA-923 already reports at or above `_CAMPD_BACKFILL_MIN_MWH` = 50,000 MWh. Oklaunion
   clears it (2,601,923 MWh in 2019; 1,103,627 in 2020), so the two gates **compose** rather than
   stack (rule 19 `[R-ONE-MECH]`).

Property 4 has one sharp edge, found by a failing test rather than by reading: the skip depends on
`_coal_supply_class` agreeing with `_classify_f923`. For a real plant in the coal-supply registry
it does (`_coal_supply_class(127) = COAL_PRB = _classify_f923('SUB','ST',…)`); for a synthetic id
it does not (`_coal_supply_class(7) = COAL`), and the backfill then *would* add on top. The test
now uses the real ORIS code, so it pins the real mechanism.

---

## 4. What was built

`ScenarioConfig.benchmark_membership_vintage_union: bool = False` — registered in
`_CACHE_KEY_OPTIONAL_FIELDS`, its declared-default map and `TIER_TAGS`, all **in the same commit as
the field** (the nyiso-119 discipline). `check_cache_key_registration.py`: *ok, 855 fields, 310
registered, all resolve; 310 declared defaults all match HEAD.*

One new seam plus one resolver in `scripts/run_calibration_full.py`:

* `_eia860_vintage_ba_plants(iso, year)` — reads `vintage_<year>/eia860_plant.parquet`, holding
  last to canonical, under the **same** admission predicate `zone_assignment` applies (the ISO's
  own BA codes; for NWPP the BA-plus-WECC rule). It widens *which vintage is read* and nothing
  else.
* `_iso_plant_ids(iso, year=None, vintage_union=False)` — returns the base set unchanged when off.

Threaded so bench and injection cannot split basis (rule 19): `_eia923_frame`,
`_vintage_completeness`, `_reconciled_mustrun_class`, `_backfill_renewables_eia930`,
`_plant_class_shares`, `_must_run_profiles`, `_benchmark_eia923_frame`, both solve-path and
P2 call sites, and the `rebuild_benchmark` recovery (meta first, then `run_config`, mirroring
`mustrun_chp_btm_holdout`). Armed via the documented generic `prb_overrides` channel and
`--benchmark-membership-vintage-union`.

**Default OFF and not armed in `_spp_config`** — `zone_assignment.py` and `run_calibration_full.py`
are shared cross-ISO seams and the census proves more than SPP moves (rule 25 `[R-ISO-SCOPE]`).

---

## 5. Measured effect — `--rebuild-benchmark` on the bundle's OWN settings

Per the handoff's trap (c), the frames were produced by `--rebuild-benchmark`, never hand-rolled.
Two copies of the SPP 2019–2022 rung bundle differing only in the flag:

| leg | frame written |
|---|---|
| flag OFF | `eia923-78357736757d` — **exactly SPP-48's HEAD hash.** Byte-identity off, proven. |
| flag ON | `eia923-73cf57c92f07` |

**Plant 127 restored:** 2019 `COAL_PRB` 2,595,886 MWh + `oil` 6,037; 2020 `COAL_PRB` 1,100,658 +
`oil` 2,969.

| ON − OFF (TWh) | | ON − COMMITTED (TWh) | |
|---|---|---|---|
| 2019 COAL_PRB | **+2.5959** | 2019 COAL_PRB | +2.5959 |
| 2019 CT_PEAKER / oil / wind | +0.0253 / +0.0060 / +0.0412 | 2020 COAL_PRB | **−0.1085** |
| 2020 COAL_PRB | **+1.1007** | 2021 / 2022 ST_GAS | +0.2591 / +0.2527 |
| 2020 CT_PEAKER / oil / wind | +0.0063 / +0.0030 / +0.0174 | | |
| **NET** | **+3.7960** | **NET** | +3.0987 |

**Every per-class delta against OFF is positive** — the additive property confirmed empirically,
not merely argued.

2020 `COAL_PRB` actual: **65.8489 (OFF) → 66.9496 (ON)**, against the committed **67.0581**.

### 5.1 What it does to C1 — and the framing corrected

The *actual* moves in both directions (2019 up 2.5959 TWh; 2020 down 0.1085 TWh against the
committed frame). At **criterion** level, measured like-for-like against the same HEAD baseline,
the load-bearing `COAL_PRB` row gets **WORSE in both live years** — see the RESULT doc §2 for the
table. Only against the *committed* frame does 2020 improve, and that improvement is entirely the
CAMPD→EIA-923 basis shift of §5.2, not a dispatch gain.

**That is the expected and acceptable outcome, not a reason to revert.** Rule 1 `[R-STRUCT]`: a
real market behaviour stays in even when it makes the fit worse. Rule 14 `[R-ACCURATE]`: a worse
fit from an accurate input is a *discovered bug* — here, that the model is ~8.9 TWh short of SPP's
2019 PRB coal, which is the coal↔CC elasticity SPP-47 filed as "Object A".

### 5.2 The one number that goes down, and why it is not a deletion

The −0.1085 TWh is the single place this repair lowers a committed value, so it is named rather
than averaged away. It is a **basis normalisation, not a deletion**: the committed 1,209,201 MWh
was **CAMPD CEMS net** booked by the backfill (gate 2, because the solving fleet carried the
plant); the repaired 1,100,658 MWh is the plant's **own EIA-923 survey value**. Both are real
measurements of the same plant. Preferring the survey where it reports adequately, and reserving
CAMPD for genuine under-reporting, **is** the benchmark's documented convention — which the plant
now follows for the first time, because it is finally a member. The owner should judge it
knowing that; this lane does not bury it.

### 5.3 A separate defect, found on the way and NOT folded in

The committed frame carries plant 127 for **2020 only**, at the CAMPD value — yet
`_fleet_group_by_code('SPP', iso_config, y)` contains 127 in **no** year under defaults. The
committed row therefore came from a **solve path** whose fleet carried the plant, while
`rebuild_benchmark` rebuilds `group_by_code` from `iso_config` **defaults** and cannot reproduce
it. So SPP-48 §A.1's "the benchmark is invariant to the fleet repair" is true **of
`rebuild_benchmark`**, and true only because the rebuild ignores the bundle's own fleet config —
on the solve path the benchmark is *not* invariant. **A rebuild does not reproduce a
fleet-changing config's own benchmark.** Filed, not fixed: it is a different seam, and fixing it
inside this lane would widen the change beyond what the census covers.

Also visible above: 2021/2022 `ST_GAS` differ from the committed frame by +0.2591/+0.2527 TWh with
**zero** flag effect — pre-existing HEAD-vs-committed drift this lane neither caused nor touches.

---

## 6. Blast radius of the ARM, at ROW grain — the stop-the-line enumeration

A zero-MWh row still changes the frame's bytes, so this is measured in **rows**, not GWh:

| ISO | inert years (0 rows, frame byte-identical) | live years (added rows / MWh) |
|---|---|---|
| **SPP** | **2023, 2024, 2025** | 2019 (11 / 2,668,406) · 2020 (8 / 1,127,316) · 2021 (2 / 0) · 2022 (3 / 275) |
| CAISO | 2023, 2024, 2025 | 2022 (12 / 148,026) |
| ERCOT | 2023, 2024, 2025 | 2021 (3 / 1,538) · 2022 (1 / 0) |
| MISO | 2024, 2025 | 2020 (77 / 6,756,889) · 2021 (37 / 3,243,948) · 2022 (20 / 3,030,903) · 2023 (1 / 0) |
| NEISO | 2024, 2025 | 2020 (38 / 358,009) · 2021 (34 / 326,799) · 2022 (20 / 142,990) · 2023 (1 / 0) |
| NYISO | 2024, 2025 | 2022 (6 / 134,213) · 2023 (1 / 0) |
| NWPP | 2023, 2024, 2025 | none |
| SOCO | 2025 | 2023 (7 / 0) · 2024 (2 / 403) |
| **PJM** | none | **every year**, incl. 2024 (138 / 2,452,964) and 2025 (47 / 8,804,034) |

**The answer to the handoff's item 4 is "more than SPP", so the gate is DEFAULT-OFF.**

**SPP's keeper years are INERT** — arming SPP cannot move keeper 12. A test asserts exactly this
and fails loudly if it ever stops being true.

---

## 7. Governance

* **Rules 1 / 13 / 14** — the basis is the correctness of the membership, never the residual. The
  repair was built, gated and measured before any LP, it moves C1 in both directions, and the
  REPLACE variant was refused *because* it would have shrunk a failing criterion by deleting real
  metered generation.
* **Rules 21 / 24** — zero free parameters: a union over EIA's own published per-vintage BA codes.
  No threshold, no tolerance, nothing selected against a residual.
  `check_cache_key_registration.py` passes.
* **Rule 19 `[R-ONE-MECH]`** — one seam (`_iso_plant_ids`) reached by bench, injection,
  class-shares and the completeness probe alike; it **composes** with the fleet-keyed backfill
  gate rather than stacking on it, verified by rebuild.
* **Rule 25 `[R-ISO-SCOPE]`** — shared seam, default off, armed per ISO by explicit recipe. No
  ISO's number crosses a boundary: every BA code is that plant's own published field.
* **Rule 28 `[R-MECH-MATRIX]`** — row added plus a cell in **all nine** ISO shards, same commit.
  `check_mechanism_matrix.py --base` passes (integrity, anchors, keeper stamps, all four ratchets).
* **Rule 32(a)** — the parent ran **no LP**.
* **Rule 31 `[R-RETAIN]`** — nothing deleted. The promotion question is in the RESULT.

### 7.1 Pre-existing failures on the base — reported, not patched

SPP-48 §5.1 records four tests already red at `4583e70b` (ERCOT `FleetArrays` golden, NYISO
solve-surface pin, capacity-evolution soundness e2e, NEISO Mystic retiree). Any of those still red
here are inherited, not caused by this lane; the suite result is reported in the RESULT doc with
that separation made explicit.

---

## 8. What this lane does NOT claim

* **It closes nothing.** SPP's failing set stays `{C1, C3a, C3b, C4}` on the committed run; no run
  was solved under the arm, so no gate moved in either direction.
* **It does not repair PJM**, which is the largest exposure and a different defect.
* **It does not fix the rebuild/solve `group_by_code` split** (§5.3).
* **It does not adjudicate BA-switchers** — the year-aware union avoids double-counting them, but
  where a plant's BA coding lapses while it still generates (SOCO 55242, CAISO 61168/61169), the
  additive union simply leaves the status quo alone rather than deciding the provenance question.
