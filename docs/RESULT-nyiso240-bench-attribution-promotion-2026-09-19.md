# RESULT — nyiso-240: NYISO's keeper is re-based on a repaired benchmark. ZERO LP, identical dispatch, and the row that was 0.05 pp from failing now has 1.07 pp

**Session** nyiso-240 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **the parent ran ZERO LP and launched NO shard**).
**Date** 2026-09-19. **Base** `origin/main` at `5017c360`.
**Owner ruling** (2026-09-19, verbatim): *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper.."*
**Phase-0 evidence** `docs/FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md`, merged to `main` as PR **#6285 BEFORE this rebuild**; probe `scripts/probes/nyiso240_c1_margin_bench_phase0.py` → `results/calibration/_nyiso240_c1_margin_bench_phase0.json`.

> ## HEADLINE
> 1. **NYISO keeper → `2026-09-17-nyiso240-bench-attribution`** (bundle
>    `results/calibration/nyiso240_benchfix_span`), all four registered years 2022–2025, superseding
>    `2026-09-17-nyiso239-bench-oil-basis`, **pruned in this session** (rule 35 `[R-PROMOTE]` (a)).
> 2. **ZERO LP WAS SPENT AND THE DISPATCH IS BIT-FOR-BIT THE SUPERSEDED KEEPER'S.** nyiso-239's four
>    per-year shard bundles were re-fetched by **full SHA**, re-composed and re-rendered with
>    `--rebuild-benchmark`. No solve was re-entered, so that keeper's gate G-1 replay fidelity is
>    preserved **by construction** rather than re-argued. `solve_surface.fingerprint`
>    **`bd2b4657f9b5df7e`**, unchanged. **Zero `ScenarioConfig` fields move.**
> 3. **What changed is the ruler, twice — and both repairs reproduced their pre-registered
>    magnitudes.** R1 added **0.880 TWh** to `CC_REGULAR` 2022 against a phase-0 prediction of
>    879.6 GWh (**0.4 GWh**); R2 moved **1.668 TWh** against a prediction of 1,668.3 GWh (**exact**).
>    The predictions were committed to `main` before the code that produced them existed.
> 4. **DETERMINATION UNCHANGED: `CALIBRATED`, grade 7, fails 0, C3c the lone ledgered caveat — and
>    ZERO C1 rows change status.** The gain is **MARGIN**, which is what the session was aimed at:
>    2022 `CC_REGULAR` **+2.95 → +1.93 pp** of a ±3.0 pp band, i.e. headroom **0.05 → 1.07 pp**.
> 5. **Rule 25 `[R-ISO-SCOPE]` was discharged BEFORE landing** — every ISO's designated keeper
>    re-scored against a repaired copy of its own bench: **42 C1 rows move ≥ 0.05 pp, ZERO change
>    status, ZERO of the eight determinations flip.**
> 6. **It does NOT close the object, and the owner's "gates may regress" clause was not needed:
>    nothing regressed to a FAIL.** What did move the wrong way is reported in §5 at full magnitude.

---

## 1. WHAT WAS PROMOTED

| | |
|---|---|
| **keeper** | `2026-09-17-nyiso240-bench-attribution` |
| bundle | `results/calibration/nyiso240_benchfix_span` |
| years | 2022, 2023, 2024, 2025 |
| supersedes | `2026-09-17-nyiso239-bench-oil-basis` (pruned this session, rule 35 (a)) |
| `solve_surface.fingerprint` | `bd2b4657f9b5df7e` — **unchanged** |
| `authorized_price_tuning` | **NONE** |
| free parameters | **zero new**; the 14-entry DOF ledger carries over byte-identical |
| LP spent | **zero** |

**Why the run id reads `2026-09-17`**: the id is derived from the bundle's own date, and the bundle's
**dispatch is the 2026-09-17 solve**. Dating it 09-19 would claim a solve that did not happen. The
promotion is 09-19 and says so everywhere it is recorded.

### 1.1 The retrieval, which is the whole reason this cost nothing

nyiso-239 §7 predicted a ~18 min four-shard re-solve would be needed, because a bench part
regenerates only from a bundle's `dispatch/` + `system.parquet` and the committed keeper carries
neither. **That assumption is falsified.** All four SHAs recorded in `.gitignore:2400` still resolve:

| year | commit | files |
|---|---|---|
| 2022 | `5802986acd77b69cfeb13720a8f0167f6ccb80a7` | 17 |
| 2023 | `0f03dd49b1daee41a1fd0244474e6c4cea7c0c9b` | 17 |
| 2024 | `ce299f37da628cf7299cba5422f52f4ab05765bb` | 17 |
| 2025 | `9859790c33415e9c6dc54ecfb1c799ecc8fb76da` | 17 |

`git fetch origin <sha>` → `git checkout <sha> -- results/calibration/nyiso239_bench_<yr>` →
`scripts/probes/nyiso238_compose_span.py` → `run_calibration_full.py --rebuild-benchmark`. The
composer independently confirmed the legs agree: *"solve_surface fingerprint: bd2b4657f9b5df7e
(identical across legs)"*. **This is the general lesson, not a NYISO one: a bench-construction
repair never needs a re-solve if the lane's shard SHAs were recorded.**

---

## 2. THE TWO REPAIRS, AND WHY THEY ARE RULE 14 AND NOT THE RESIDUAL

Both land in the **shared** bench path of `scripts/run_calibration_full.py`, **after** the
annual-floor CAMPD backfill, and **neither changes which plants that backfill reaches** (its firing
test is untouched).

### 2.1 R1 — `_backfill_eia923_missing_months`

EIA-923 drops months a respondent withheld, and **EIA's own published annual** — the form's
*"Net Generation (Megawatthours)"* column — **is the sum of the months filed**. So a withheld month is
absent from the **annual class benchmark**, not merely from its shape.
`_backfill_eia923_with_campd` cannot see this: it gates on a **50 GWh annual floor**, and
**ten good months hide two missing ones.**

Instance: **Bethlehem Energy Center (2539)**, a 750 MW NYISO combined cycle, filed **no February and
no November 2022**; CAMPD meters **596.0 GWh** there. Scaled by the plant's own measured ten-month
`Σe923 / ΣCAMPD` ratio of **1.476** — CEMS meters only the two CT stacks of this 2×1 CC, and the
unstacked steam turbine is 34 % of net — the repair adds **0.880 TWh**.

Zero free parameters: the ratio is measured from the same plant in the same year, and it is the
identical *"scale CAMPD's shape to a measured target"* arithmetic `_book()` already performs. Census
over every committed bench part: **67 plant-years across nine BAs**.

### 2.2 R2 — `_reattribute_dual_fuel_oil`

`_classify_f923` routes **100 %** of DFO / RFO / JF / KER / WO / PC to the `oil` class, because
EIA-923 books MWh under the fuel **burned**. The LP does not: `dual_fuel_switching` prices a
dual-fuel unit at `min(gas, oil)` and the unit keeps dispatching **in its own class**. Verified at
the unit layer: the model's **entire** oil-fuel fleet in NYISO 2022 is **11.1 GWh across four
plants**, against an `oil` class benchmark of **1,843.7 GWh**. The repair moves **1.668 TWh**; the
residual `oil` class is the plants **not in the model fleet**, which is the right place for it.

This is the nyiso-239 misalignment **one layer lower** — there at `reconcile_vintage_classes`'
*target*, here in the 923 class split itself. Rule 14 `[R-ACCURATE]`'s misalignment case: the
benchmark class is defined on a **fuel** boundary and the model class on a **unit** boundary.

---

## 3. THE MEASURED EFFECT — incumbent vs new, each on its own bench

| | incumbent (old bench) | **new (repaired bench)** |
|---|---|---|
| determination | CALIBRATED | **CALIBRATED** |
| grade | 7 | **7** |
| failing criteria | 0 | **0** |
| caveats | C3c (ledgered) | **C3c (ledgered)** |
| C1 status flips | — | **ZERO** |

| yr | class | actual before | actual after | pp before | **pp after** | Δ |
|---|---|---:|---:|---:|---:|---:|
| **2022** | **CC_REGULAR** | 33.259 | **34.806** | **+2.95** | **+1.93** | **−1.02** |
| 2022 | ST_GAS | 8.106 | 8.883 | −0.61 | **−1.17** | −0.56 |
| 2022 | CC_CHP / CT_PEAKER / ST_CHP | | | ≤ 0.6 | ≤ 0.6 | ≤ 0.02 |
| **2023** | **ST_GAS** | 8.141 | 8.325 | **+2.85** | **+2.70** | −0.15 |
| 2023 | CC_REGULAR | 33.012 | 33.061 | +0.70 | +0.66 | −0.04 |
| **2024** | **CC_REGULAR** | 34.060 | 34.094 | **+2.46** | **+2.44** | −0.02 |
| 2025 *(SKIPPED, preliminary vintage)* | CC_REGULAR | 33.080 | 33.555 | +1.94 | +1.58 | −0.36 |
| 2025 *(SKIPPED)* | ST_GAS | 13.522 | 14.080 | −2.74 | **−3.15** | −0.41 |

**The headline row**: the keeper that was **0.05 pp of a ±3.0 pp band** from NOT-YET now has
**1.07 pp** — a 21× improvement in headroom on the only row that was ever close, and the largest
single row move in any ISO.

---

## 4. RULE 25 — THE CENSUS RAN BEFORE LANDING, NOT AFTER

nyiso-239 §7 recorded *"I have **not** measured the other 11 cells' verdict impact; doing so needs
each ISO's hydrated profile and is a cross-lane job."* **It does not.** Every ISO's keeper payload
and every bench part are committed, so the census runs in-process at zero LP. Each ISO's designated
keeper was re-scored through `calibration_verdict.determine()` against a repaired copy of its own
bench:

| ISO | base | R1 | R1+R2 |
|---|---|---|---|
| CAISO | CALIBRATED 7/0 | same | same |
| ERCOT | CALIBRATED 7/0 | same | same |
| MISO | NOT-YET 4/3 | same | same |
| NEISO | CALIBRATED 7/0 | same | same |
| NYISO | CALIBRATED 7/0 | same | same |
| PJM | CALIBRATED 8/0 | same | same |
| SOCO | NOT-YET 4/1 | same | same |
| SPP | CALIBRATED 7/0 | same | same |

"same" = identical determination, grade, failing-criteria set and failing C1 rows.
**42 C1 rows move ≥ 0.05 pp; 0 change status; 0 determinations flip.** MISO's two failing C1 rows
both move slightly *toward* passing (+0.08, +0.09 pp) without flipping.

**What other lanes should expect** (they are not surprised by this — it is the same mechanic
nyiso-239 §4.1 recorded): a bench part only carries the repair once its ISO **re-renders**. Every
ISO's committed parts are unchanged by this commit; the next lane to run `--rebuild-benchmark` picks
both repairs up. Measured at this promotion: **the only bench bytes that moved anywhere are NYISO's
four.** Bench freshness across the repo went from 34 stale parts to **31** — NYISO's four now
reproduce at HEAD.

---

## 5. WHAT REGRESSED, AND WHAT IS STILL OPEN — at full magnitude

The owner's *"if structural integrity improves but gates regress that may still be a keeper"* clause
**was not needed**: nothing regressed to a FAIL, and no criterion or C1 row changed status. What did
move the wrong way, reported because the determination does not excuse it:

* **R2 moves `ST_GAS` AWAY from its actual in two years** — 2022 −0.61 → **−1.17 pp**, and 2025
  −2.74 → **−3.15 pp** (SKIPPED on the preliminary vintage, so ungated). It also moves `ST_GAS` 2023
  *toward* its actual. **The repair was not selected on that mixed record** (rule 1 `[R-STRUCT]`):
  the selecting evidence is a class-membership identity measured at the unit layer and a cold-months
  burn shape, neither of which is a fit statistic.
* **+2.26 TWh of the 2022 `CC_REGULAR` over-run is REAL** and remains this lane's open object. Two
  of the three tight rows — 2023 `ST_GAS` (+2.70) and 2024 `CC_REGULAR` (+2.44) — are barely moved.
* **The D-4 unit-conduct gate reads `False` BOTH BEFORE AND AFTER**, on an identical row set
  (2480 and 8006 under `reliability_floor × ST_GAS`). **Pre-existing, not a regression at this
  promotion**, and it routes through rule 20 `[R-FORCED-BUDGET]`'s conditional-pass path exactly as
  it did for the incumbent. C8 PASSES.
* **The G2 hydro energy loss** (−55.2 / −25.5 GWh in 2022 / 2023) carries over **unchanged as a
  LEDGERED OPEN ROOT-CAUSE ISSUE** (rule 21 `[R-DOF]`), **not** an accepted limitation. Untouched.
* **C3c** stays the ledgered, non-downgrading energy-only-LMP model-class limitation: model
  7 / 0 / 0 / 3 h > $300 against 101 / 10 / 13 / 42 actual.

**SUCCESSOR OBJECT** (`FINDING` §7): `CT_PEAKER` collapses out of merit from 2023 — model 2.43 →
0.25 / 0.30 / 0.77 TWh against a flat ~2.1–2.8 TWh actual, with **capacity intact** (~2,000 MW peak
every year), so it is economic, not availability. The displaced energy is exactly 2023 `ST_GAS`
+3.40 and 2024 `CC_REGULAR` +2.94 — **the two rows these repairs do not touch.** Recommended lever:
`ct_peaker_committed_measured` (cell **U**; NYISO's own measured `phys_committed` **0.843** against
the transferred band **1.35**, the largest ratio in the model, resting on a three-way NYISO↔CAISO↔NEISO
citation ring in which no ISO cites a measurement). `nyiso_ct_peaker_bands_measured` stays **R** and
was not re-tested.

---

## 6. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — `authorized_price_tuning` **NONE**; zero offer-curve multipliers, zero
  mechanisms armed, zero `ScenarioConfig` fields moved. The determination is reported as a
  consequence, never as the selection criterion; §5 reports the adverse rows at full magnitude.
* **Rule 13 / 14 `[R-MEASURED]` / `[R-ACCURATE]`** — both repairs prefer the accurate measurement
  over a silently truncated one. R1's scale is the plant's own measured same-year ratio; R2 is rule
  14's misalignment case, remedied with the reconciled version rather than a guess.
* **Rule 21 `[R-DOF]` / 24 `[R-REGISTRY]`** — **zero free parameters, zero new literals**; the
  existing `_CAMPD_BACKFILL_MIN_MWH` deadband and the annual firing test are untouched. The 14-entry
  DOF ledger carries over byte-identical.
* **Rule 25 `[R-ISO-SCOPE]`** — §4, run **before** landing. No ISO's number is fitted or transferred.
* **Rule 27 `[R-PUSH]`** — Opus session; `run_calibration_full.py` (14,611 → 14,868 lines) edited
  **with the Edit tool**, never regenerated, and every pushed blob verified against local.
* **Rule 28 `[R-MECH-MATRIX]`** — **no cell moves** (a bench construction has no matrix row); the
  promoting-session stamp is landed in `mechanism-matrix/NYISO.js` **and** the §5.5 prose header, and
  `check_mechanism_matrix.py` is green on both (*"keeper stamps match"*, *"§5.x prose headers match"*).
  The DO-NOT-REDO set was honoured throughout.
* **Rule 29 `[R-SCREEN]`** — clause (0) zero-LP phase 0 answered the question; no screen owed, none
  spent. **Rule 32 `[R-SHARD]`** — the parent ran no LP and launched no shard. **Rule 33
  `[R-SHARD-ARCHIVE]`** — nothing to archive.
* **Rule 31 `[R-RETAIN]`** — trigger (i) is met for the outgoing keeper: **the owner ruled on
  promotion.** Nothing else was deleted; the four retrieved nyiso-239 legs stay on disk, gitignored.
* **Rule 35 `[R-PROMOTE]`** — executed **in order**: year union `{2022, 2023, 2024, 2025}` enumerated
  from the registry **before** the prune (b) and covered exactly by the incoming bundle (c);
  registered and verified with `audit_keepers --iso NYISO` (e) — which reported **exactly** the E13
  "superseded run left behind" it is meant to, confirming the check was live — **then** the outgoing
  keeper's three stores deleted via `prune_iso_runs.py --iso NYISO --force-uncite` (a, d).
  `audit_keepers` after: **PASS, 0 failures, 1 warning** — the E11 lineage warning inherent to
  keeper-only retention once the former bundle is gone, identical to the one nyiso-239's promotion
  left. **E11 declaration**: the only kwarg-surface difference is `meta.json`'s `composed_from`,
  which is provenance, not physics.
* **Rule 16 `[R-ALLYEARS]`** — one bundle, all four registered years.

### Reported, not fixed — all pre-existing and none NYISO's

* **`tests/scoring` carries 20 failures on clean `main`.** This session's only code change is two new
  bench-path functions and their two call sites; the failure set is unchanged. **Nobody owns this.**
* **31 of 44 committed bench parts are STALE at HEAD** (down from 34 — NYISO's four now reproduce).
  Each is its own lane's to regenerate.
* **Class-E parity**: `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` remain pre-existing
  unmapped REDs and are not NYISO's. This session's four retrieved leg dirs also appear **locally**,
  which is exactly the corrected rule-31 clause — the gate walks the filesystem, CI checks out only
  what is committed and stays green.
* **`dashboard_add_run.py`'s docstring still describes `enforce_registration_marker_gate`**, removed
  with `[R-HOLDOUT]` on 2026-09-09. Harmless but stale.

---

# ADDENDUM A — the MARGINAL-CARBON CONTROL ARM (owner instruction, 2026-09-19)

**Result: G-DRIFT form 4 is CONFIRMED EMPIRICALLY, at BYTE IDENTITY.** The keeper's dispatch was
solved at `3edb8ad8`; `git diff 3edb8ad8 HEAD` over the solve path is **14 files / +3,176 lines**.
Replayed at HEAD, **`dispatch/<yr>_P1.parquet` is byte-identical by sha256 in all four years**, and
so is `hourly/unit_hourly_<yr>.parquet`. The only differences anywhere in the bundle are **ADDED
COLUMNS**. That is a far stronger statement than "two numbers agree": it says the drift is inert.

## A.1 Why this lane owed a control at all

The owner's instruction exempts a session whose **arm** becomes the keeper, on the grounds that
*"your arm's own bundle will carry the column."* **That premise fails here, and the exemption with
it.** This session's arm was promoted at **zero LP** — the keeper's dispatch is nyiso-239's
2026-09-17 solve at `3edb8ad8`, which predates the emissions dual
(`2ec096633f5624585eb9db1728ebc7c8ca5ccbdf`, 2026-09-18). Measured before launching:
`nyiso240_benchfix_span/hourly/system_2022.parquet` carries
`['year','pass','zone','hour','price','slack','dump','demand','reserve_price']` and **no
`marginal_emission_rate`**. NYISO therefore had no marginal-carbon data and the control was owed.

## A.2 Shape — per-year fan-out, on the owner's instruction, and it is rule-legal

The owner directed *"launch one shard per year then compile."* This is **rule-32(b)-legal here, not
an exception to it.** Rule 32 `[R-SHARD]` (b) bans fanning out **a run that must come back together
FOR REGISTRATION** — its stated failure modes are registration-path ones (`build_payload` reading
the bundle-root `system.parquet`; the per-plant D-1/D-2 diagnostics falling back to the registered
payload and passing vacuously). It then names the carve-out this control sits in: *"Subdividing …
remains available for DIAGNOSTIC work that will never be registered."* **This control is never
registered** — the owner's own instruction says so. My earlier single-span framing was the more
cautious reading of the rule, not the correct one.

Four shards, all pinned to the full immutable SHA `1fdcc69c1b6a1e5e0859edd135f3c3d7d476f15d` (this
lane's own branch head, because the promotion had not yet auto-merged and `origin/main` carried
neither the new keeper bundle nor the bench repairs), each `replay_keeper.py … --years <YR>` with no
`--set` and no `--reuse-solved`. The initially-launched single-span shard was interrupted and
archived. **Wall clock ~15 min instead of ~45.**

## A.3 RETRIEVABILITY — the bundle paths and their FULL IMMUTABLE SHAs

*(A marginal-abatement page is being built against these. Branch names are deleted within days;
these SHAs are the durable handle. Rule 34 `[R-SHARD-PROMOTABLE]` (d) verified — `git ls-tree -r`
returned **17 files** for every leg **before** any shard was archived.)*

| year | leg bundle | **commit** | files |
|---|---|---|---|
| 2022 | `results/calibration/nyiso_mer_2026-09-19_2022` | `93eb1aa918c039a01d6e5ba6265eedd7f69fdb03` | 17 |
| 2023 | `results/calibration/nyiso_mer_2026-09-19_2023` | `24a75c15f0b08ccb51c59107f1f36163a02a5fef` | 17 |
| 2024 | `results/calibration/nyiso_mer_2026-09-19_2024` | `0573d6382a2526cb482d544567c967767f50556e` | 17 |
| 2025 | `results/calibration/nyiso_mer_2026-09-19_2025` | `5633d28698ee5bd07a2afccab63e02d2d8b70382` | 17 |

**Composed span**: `results/calibration/nyiso_mer_2026-09-19` (153 MB; the four
`hourly/system_<yr>.parquet` that carry the MER series are **3.7 MB** of that), built with
`scripts/probes/nyiso238_compose_span.py`. The composer independently reported
*"solve_surface fingerprint: bd2b4657f9b5df7e (identical across legs)"*. Recovery commands are in
`.gitignore` beside the ignore lines.

**OPEN, AND THE OWNER'S CALL — stated rather than left to be discovered.** The control is
**unregistered by instruction**, so the composed bundle and its legs are **gitignored and live only
on shard branches**. A branch deleted or garbage-collected takes them with it. If the
marginal-abatement page needs this data **durably**, it needs either a registration decision or a
`KEEP_REQUIRED_UNMAPPED_BUNDLES` allowlist entry — committing an unregistered bundle dir to `main`
turns `check_registry_payload_parity.py` RED (Class-E point 4). **I have not invented a third
route.** Re-solve cost if the branches are lost: ~15 min wall, four parallel shards.

## A.4 THE G-DRIFT EVIDENCE, measured

| layer | keeper vs replay |
|---|---|
| `dispatch/<yr>_P1.parquet` | **byte-identical (sha256), all four years** |
| `hourly/unit_hourly_<yr>.parquet` | identical |
| `hourly/class_hourly_<yr>.parquet` | max \|Δ\| class-total **0.000e+00 TWh**; max \|Δ\| hourly **0.000e+00 MW**; 16 classes × 4 years |
| `hourly/system_<yr>.parquet` | shared columns **identical**; max \|Δ price\| **0.000e+00** |
| `hourly/class_band_hourly_`, `reserve_family_` | byte-identical |
| `hourly/storage_<yr>.parquet` | shared columns **identical**; **+2 new columns** `soc_mwh`, `energy_cap_mwh` |
| legitimacy diagnostics | **every verdict tuple identical** across D1 / D2 / D4 / D5 / D9 / D10 |

**The only differences anywhere are additive**: `marginal_emission_rate` in `system`, and
`soc_mwh` / `energy_cap_mwh` in `storage` (another lane's column, landed since `3edb8ad8`).

## A.5 THE MARGINAL EMISSION RATE — what NYISO's dual actually says

Per zone-hour, P1, tCO2/MWh, over 52,560 zone-hours per year (5 zones × 8,760 h):

| year | load-wtd mean | p10 | median | p90 | max | zone-hours at exactly 0.0 | NaN |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022 | 0.4508 | −0.0000 | 0.4584 | 0.6897 | 1.8095 | 10.92 % | 0 |
| 2023 | 0.4753 | 0.3695 | 0.4498 | 0.6791 | 4.9220 | 5.29 % | 0 |
| 2024 | 0.5219 | 0.3667 | 0.5027 | 0.8210 | 5.8836 | 3.82 % | 0 |
| 2025 | 0.5310 | 0.3712 | 0.5272 | 0.8073 | 1.8304 | 1.27 % | 0 |

**Two sanity checks that the series is physical, not plumbing.** (1) The load-weighted mean sits at
**0.45–0.53 tCO2/MWh**, which is a gas combined cycle at the margin (7–9 MMBtu/MWh × 0.0585
tCO2/MMBtu ≈ 0.41–0.53) — and it is *far above* NYISO's average grid intensity, exactly as it must
be in a system whose average is diluted by nuclear and hydro that are almost never marginal.
(2) The zero share falls monotonically **10.92 % → 1.27 %** across the span: those are hours where
the marginal resource carries no carbon. **Reported, not interpreted** — whether that trend is the
fleet or the model is a question for the lane that uses this series, not a claim this control makes.
2022 carries a p10 of −0.0000 (a handful of very small negative duals, the sign convention at
zero-carbon-marginal hours).

## A.6 A SEPARATE FINDING — `legitimacy_diagnostics.py` is NOT reproducible at the 3rd decimal

Nine diagnostic rows differ between the keeper's committed artifact and the replay's: seven D-1 rows
(`actual_offpeak_cv`, and `profile_r` / `cv_ratio` derived from it) and two D-4 rows (plant 2500
Ravenswood, `measured_median_mw` 99.494 → 99.737 and 78.417 → 78.457).

**This is NOT drift, and I checked rather than assumed.** Re-running
`legitimacy_diagnostics.py` **on the identical keeper bundle, twice**, reproduces **exactly the same
nine rows with exactly the same wobble**. The diagnostic is nondeterministic on its **measured**
columns; every **model** column (`model_offpeak_cv`) is stable, and the dispatch it reads is
byte-identical.

**Reported, not fixed** — a scorer change is outside this lane (rule 25), and no verdict moves
today. But it is a real reproducibility defect in a **gating** artifact: C8 and rule 20
`[R-FORCED-BUDGET]`'s conditional-pass path both read this file, so a row that today wobbles at the
3rd decimal could in principle straddle a gate threshold on some future run. **It wants an owner.**

## A.7 GOVERNANCE

* **Not a new run.** No dashboard id was minted, the keeper bundle was not overwritten, nothing was
  re-registered. A replay that reproduces the keeper is not a run (owner instruction).
* **Rule 32 `[R-SHARD]`** — the parent ran ZERO LP: it launched, fetched, composed, diffed. (a) held
  throughout. The per-year fan-out is (b)'s diagnostic carve-out, per §A.2.
* **Rule 34 `[R-SHARD-PROMOTABLE]`** — every leg pushed its full bundle to its own branch via
  `.gitignore` negation + plain `git add`; `git ls-tree` verified 17 files per leg **before** any
  archive; (e) retrievability is §A.3, including what it costs if the branches go.
* **Rule 33 `[R-SHARD-ARCHIVE]`** — all five shards (four legs + the superseded single-span one)
  archived only after fetch + checkout + verify. Recovery recorded by full SHA, never branch name.
* **Rule 31 `[R-RETAIN]`** — nothing deleted. The legs and the composed span are **gitignored, not
  removed**, and §A.3 asks the durability question rather than pre-empting it.
* **Memory** — the dual's cost at per-plant scale was flagged UNVALIDATED in every shard prompt, with
  an instruction that an OOM is a finding about the dual and not a model regression. **No shard was
  OOM-killed**; all four completed inside their budget.
