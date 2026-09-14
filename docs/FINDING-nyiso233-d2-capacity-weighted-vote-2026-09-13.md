# FINDING — the D-2 plant-class vote is now CAPACITY-WEIGHTED. Measured on every ISO with committed floors: **NYISO's C8 artifact corrected, CAISO byte-identical, SPP no verdict change**

**Session** nyiso-233 · **Date** 2026-09-13 · **ZERO LP** (rule 32 `[R-SHARD]` (a)). Every number
below is read from committed bundle artifacts plus `run_year(fleet_only=True)` fleet rebuilds, which
build a fleet and stop.

**Authorisation.** A shared scorer reaches every ISO column, which rule 25 `[R-ISO-SCOPE]` forbids a
NYISO lane from deciding alone. Landed on an explicit owner ruling given in this session: *measure
every ISO, then land the capacity-weighted vote* — and, on the disposition of a verdict change
elsewhere, *the current number is the artifact*. Pre-registration, construction and stop conditions:
`results/calibration/PRECOMMIT-nyiso233-d2-capacity-weighted-vote.md`, written **before** any number
here was read.

---

## 1. WHAT CHANGED — one weight in one vote

`scripts/legitimacy_diagnostics.py::aggregate_floors_by_plant` labelled each plant by its **most
common non-empty unit group counted in LP ROWS**. Row count is a property of the **offer curve's
band structure**, not of the plant, so a mechanism that collapses or expands a class's tranche ladder
could move a whole site's dispatch between class denominators and flip C8 — protective tier, zero
caveat budget — with no physical change at all. Defect, fragility census and the identification to
the row: `docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md` (nyiso-232).

The vote is now weighted by **capacity (`pmax`)**. Bands partition a class's capacity however many of
them there are, so the vote is **band-invariant by construction**; and `pmax` depends on no dispatch
outcome, so a plant's class denominator is a property of the plant rather than of the solve. Energy
weighting is also band-invariant and would have needed no fleet rebuild — it was **rejected** for
that second reason, since arm and control would legitimately label a plant differently whenever
dispatch moved.

**Zero free parameters, zero new literals, no DOF entry** (rules 21 `[R-DOF]`, 24 `[R-REGISTRY]`).

## 2. THE CASE THAT NAMES THE DEFECT

Ravenswood (plant 2500), the ~2.5 GW mixed NYC site, in the NYISO keeper — **identical in all four
years**:

| basis | `ST_GAS` | `CC_REGULAR` | label |
|---|---:|---:|---|
| LP rows | 4 | 7 | **`CC_REGULAR`** |
| **capacity (MW)** | **1724.8** | **268.5** | **`ST_GAS`** |

**6.4:1 on capacity, and the row count pointed the other way.** An 87 %-steam site was labelled
`CC_REGULAR`, and its whole dispatch was counted against the wrong class denominator. Plant 2517 is
the same shape at 4.7:1 (385.0 MW `ST_GAS` vs 82.7 MW `CT_PEAKER`) on a 4–4 row tie broken
alphabetically.

The clearest statement of why row count cannot be the weight comes from SPP plant 165, where the two
classes are within 2 MW of each other and the vote is decided **entirely by `COAL` happening to carry
a `mustrun` band that `CC_REGULAR` does not**:

```
COAL_SPP-South_p165_{mustrun,committed,econlo,econhi,peak}   5 rows   478.9 MW
CC_REGULAR_SPP-South_p165_{committed,econlo,econhi,peak}     4 rows   480.7 MW
```

## 3. CROSS-ISO MEASUREMENT — a controlled A/B, identical inputs, only the weight differs

Both arms were run through the **same code path on the same committed artifacts**, the control by
monkeypatching the `pmax` backfill to identity. Every bundle in the repository carrying a committed
`floors/<year>_P1.npz` is covered: **10 bundle-years, 3 ISOs, 11,328 floor rows**.

**Harness validation, so the A/B can be read at all:**

* The refactored accumulator reproduces the superseded row-count labels **bit-for-bit on all 10
  bundle-years** when no `pmax` is supplied (0 label differences) — so what follows is a basis
  change, not a code change.
* The control arm reproduces the **committed** `legitimacy_diagnostics.json` on **all D-2 numerics,
  0 diffs across 17 rows**.

### 3.1 Verdict changes

| ISO | bundle | mixed plants | label flips | D-2 gate | verdict changes |
|---|---|---:|---:|---|---|
| **NYISO** | `nyiso232_deleak_span` (the keeper) | 7 | **6**, every year | **FAIL → PASS** | **3** — `ST_GAS` 2022/2023/2024 |
| **CAISO** | `caiso279_ablate_dswcouple_span` | 1 | **0** | PASS → PASS | **0** — byte-identical on every row |
| **SPP** | `soco15_spp_arm` | 23–25 | 5–6 | PASS → PASS | **0** |

### 3.2 NYISO — the numerator never moves, only the denominator

| year | forced TWh | class total TWh | forced share | verdict |
|---|---|---|---|---|
| 2022 | 1.9187 → **1.9187** | 5.7046 → **9.2318** | 33.63 % → **20.78 %** | FAIL → **pass** |
| 2023 | 1.9955 → **1.9955** | 5.8134 → **13.4962** | 34.33 % → **14.79 %** | FAIL → **pass** |
| 2024 | 2.3764 → **2.3764** | 6.4861 → **11.5421** | 36.64 % → **20.59 %** | FAIL → **pass** |
| 2025 | 2.2003 → **2.2003** | 7.7309 → **12.1256** | 28.46 % → **18.15 %** | pass → pass |

**Every numerator is bit-identical to four decimal places in all 20 rows, in every ISO.** The floors
are the committed real P1 floors; nothing about the forced energy is reconstructed. Only the
denominator each class is measured against moves.

These reproduce nyiso-232's independently-computed prediction of **20.8 / 14.8 / 20.6 / 18.1 %** to
the second decimal, and all four sit **below the superseded keeper's** 23.1 / 16.5 / 21.4 / 19.0 % —
which is what physics demands, since the same floors are a smaller share of a class that now runs
more.

**The pass is not vacuous.** `ST_GAS` is **material on both arms** (`immaterial: false`, load share
11.2–13.1 % on the control and 15.9–18.8 % on the arm, against the rule-20 `[R-FORCED-BUDGET]`
materiality floor of 2 %). The class did not pass by being reclassified as too small to gate.

### 3.3 SPP — not inert, just not verdict-changing

The distinction matters and is not blurred. SPP's denominators **do** move — `COAL` 68.83 → 72.44 TWh
and `CC_REGULAR` 45.04 → 42.01 TWh in 2023, from flips like plant 2079 (`COAL` 562 MW vs
`CC_REGULAR` 236 MW, 3.6:1, row count said `CC_REGULAR`) and plant 2952 (`ST_GAS` 977 MW vs `COAL`
521 MW, 1.9:1, row count said `COAL`). `ST_GAS`'s forced share improves slightly in each year
(20.01 → 19.35 / 18.73 → 18.27 / 15.00 → 14.31 %). **No verdict moves.**

**The fragility census over-stated SPP's exposure, and the correction is recorded rather than
quietly dropped.** nyiso-232 counted 23–25 SPP plants as "flippable", meaning a hypothetical halving
of the winner's row count would lose it the vote. Under the actual capacity repair only **5–6**
flip. "Flippable" measured fragility to an arbitrary band change; it was never a prediction of what
this repair does, and it should not be read as one.

## 4. THE PRE-REGISTERED STOP CONDITIONS — all four clear

| | condition | measured |
|---|---|---|
| **S1** | capacity must discriminate | **0** classified plants with all-zero `pmax`, in all 10 bundle-years |
| **S2** | the #1488 empty-label fix must not regress | **0** plants lose a non-empty label to `''` |
| **S3** | the backfill must be exact | **11,328 / 11,328** floor rows resolved; 0 missing |
| **S4** | blast radius must stay inside D-2/D-4 | `aggregate_floors_by_plant` has **one** non-test call site, feeding `klass_by_pid` and `build_plant_matrices` only — no price, no dispatch, no determination path but C8 |

## 5. HOW `pmax` REACHES THE SCORER

`floors/<year>_<pass>.npz` did not carry `pmax`; the keys were
`min_gen, mechanism, unit_ids, plant_code, plant_group`. Three parts:

1. **Both writers now persist it** — `run_calibration_full._save_floor_arrays` (solve-time) and
   `legitimacy_diagnostics.load_or_rebuild_floors` (the `_rebuilt.npz` cache).
2. **Pre-existing npz are backfilled exactly**, by joining their `unit_ids` to a `fleet_only`
   rebuild. `pmax` is a fleet property no P0/P1 pass changes, so this is a recovery, not a
   reconstruction — and **the floors themselves are untouched**. The join is **by `unit_id`, never
   positional**: on the NYISO keeper the npz and the rebuilt fleet share every unit but not their
   order (715 rows resolving into an 829-row fleet), so a positional alignment would be silently
   wrong.
3. **There is no silent fallback.** Where `pmax` cannot be obtained the vote reverts to row count
   **and the artifact records it** — `plant_class_vote_basis` is now a top-level field of
   `legitimacy_diagnostics.json`, reading `"capacity"` or `"row_count_fallback"` per year. A
   recorded basis is the difference between a fallback and a hidden dependence.

## 6. WHAT THIS DOES NOT CLAIM

* It does **not** re-score a historical run on a basis this lane invented. NYISO's keeper is
  re-scored because **the scorer changed**; every other registered run re-scores on the same current
  scorer, and CAISO's and SPP's numbers above say what that does.
* It does **not** touch the mechanism attribution, the floor-energy convention, the
  `FloorClassMatrix` per-hour class, or the empty-label imputation. One weight, one vote (rule 19
  `[R-ONE-MECH]`).
* It arms nothing, moves no `ScenarioConfig` field, changes no solve path and **cannot move a
  price**. No mechanism-matrix cell moves on account of it.
* **ERCOT, PJM, MISO and NEISO carry no committed `floors/*.npz`** — checked on `main` and on all
  four live `claude/soco-15-*` branches. They are **UNMEASURED, not shown to be clean**. Each will
  re-score on the capacity basis the next time its lane regenerates diagnostics, through the same
  backfill; the honest statement is that nobody has measured what that does. Their per-year
  `plant_class_vote_basis` will say which basis they actually got.
* A handful of flips are decided by narrow capacity margins (NYISO plant 2493 at 309.4 vs 305.9 MW;
  SPP plant 165 at 480.7 vs 478.9 MW). These remain close calls — but they are close calls **on a
  physical quantity**, which is the whole of the claim.

## 7. RULES

1 `[R-STRUCT]` — the repair is justified by what a class label must be, never by what it does to a
residual; that it restores NYISO's own determination is **not** offered as evidence for it.
13/14 `[R-MEASURED]`/`[R-ACCURATE]` — capacity is measured; the inaccurate basis is reported at full
magnitude beside the accurate one. 19 `[R-ONE-MECH]`. 21/24 — zero free parameters.
25 `[R-ISO-SCOPE]` — the owner ruling is what authorises a cross-ISO change; no ISO's fitted number
is transferred. 28 `[R-MECH-MATRIX]` — no mechanism verdict rests on this. 31 `[R-RETAIN]` — nothing
deleted. 32 `[R-SHARD]` — zero LP.

Probe: `scripts/probes/_nyiso233_d2_capacity_vote_measure.py` (`equiv` / `labels` / `stop`).
