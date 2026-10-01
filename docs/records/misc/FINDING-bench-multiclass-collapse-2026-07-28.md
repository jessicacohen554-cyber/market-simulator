# The bench multi-class collapse: characterized, fixed, and re-scored — no gate moves

**Session:** bench-multiclass-collapse (scorer-correctness lane) · **Date:** 2026-07-28
**Premise:** `docs/FINDING-nyiso88-peaker-heat-rate-2026-07-27.md` §5 (the defect),
`docs/FINDING-nyiso91-ct-start-frequency-2026-07-27.md` §0/§6 (why it blocked the
NYISO lane's interpretation), `docs/calibration-log/nyiso.md` nyiso-87…91.
**Mode:** scorer-only. No LP, no re-solve, no mechanism, no ScenarioConfig field.
**All six keepers UNCHANGED.** Characterization artifact:
`results/calibration/bench_multiclass_collapse.json` (produced BEFORE the fix was
applied, so the correction was known in advance — rule-24 discipline applied to a
scorer). Migration record: `results/calibration/bench_multiclass_migration_report.json`.

---

## 0. Summary

1. **The defect is real and was fixed.** `render_calibration_html.build_payload`
   keyed `mw_p` / `grp_p` by `plant_code` while iterating `(plant_code, klass)`
   groups: a plant spanning two model classes had its whole measured CAMPD /
   EIA-923 series attributed to its alphabetically-last class, and the model
   dispatch of every non-winning class was silently dropped from the run
   payload. Every per-plant artifact is now keyed by `(plant_code, klass)` —
   bare `"<code>"` for single-class plants (wire format unchanged),
   `"<code>:<KLASS>"` per class slice — and the measured series is split on a
   measured basis ladder (§3). Committed bench parts and the six keeper
   payloads were migrated in place with no re-solve (§4).

2. **The blast radius was larger than estimated for MISO and absent for
   ERCOT** (§1). MISO: 24–25 plants, 54–56 TWh/yr of benched CEMS energy
   (12–13 %) — whole coal plants with an on-site CT (Belle River, 6.5 TWh)
   were scored as `CT_PEAKER`, ±20–25 TWh/yr per class. NYISO: 7 plants,
   ~10–12 %. PJM: 9 plants, ~2.5 % (9 TWh/yr of CC energy scored as
   CT_PEAKER). CAISO/NEISO: ≤0.2 %. ERCOT: **zero** — its CAMPD per-plant
   binning books each plant under one class, so the collapse cannot occur.

3. **NYISO C1 was never scored through the defect.** The premise's central
   risk — C1's 0.156 TWh margin scored on a misattributing benchmark — does
   not materialize: C1's actual (`classFull`) is built from EIA-923
   per-(plant, prime-mover) rows via the canonical `classify_plant`, and its
   model side (`gmModel`) from the class-level dispatch. Neither ever passed
   through the collapsed per-plant grouping. Before and after the fix, NYISO
   2023 CC_REGULAR reads **model 32.513 / actual 35.297 / −2.78 TWh of a
   ±2.94 band — bit-identical** (§5). The thin margin is real, but it is
   measured at prime-mover granularity and was never contaminated.

4. **Re-scored on the corrected benchmark, NO gate moves anywhere.** All six
   keepers' determinations and every criterion and record status are
   unchanged (§5). The corrections are material exactly where the
   characterization predicted, and land inside the bands:
   - **MISO CT_PEAKER D-1 `cv_ratio` 2.26 → 1.01 / 2.03 → 0.87 / 2.10 → 0.84**
     (2023/24/25): the "model too peaky vs actual" signal was benchmark
     contamination — coal-baseload energy flattening the class's actual
     diurnal profile. Against its true CT-only actual the model's CT shape is
     essentially right.
   - C2's MISO G-21b coal anchor (`e930.coal_cems`) rises ~16.5 TWh (mixed
     plants' coal slices now count as coal); the 2025 C2 family actuals move
     ≤0.7 TWh, within PASS.
   - NYISO/PJM CT_PEAKER and MISO/NYISO ST_GAS `cv_ratio` move toward the
     model (e.g. NYISO CT_PEAKER 3.78 → 3.06), all pass→pass.

5. **One discovered signal (reported, not chased):** once East-of-the-mix
   contamination is removed, **MISO ST_CHP's model diurnal profile is
   anti-correlated with its true actual** (`profile_r` +0.45/+0.74/+0.58 →
   **−0.80/−0.75/−0.77**). The class is D-1-ungated and D-2-exempt (CHP), so
   nothing flips; it is a real shape defect previously masked by the mixed
   plants' CT slices sitting in the class actual. Left as a candidate for a
   future MISO lane — not this one (scorer-only guardrail).

---

## 1. Measured blast radius (from committed artifacts, before any fix)

Share of benched CEMS energy on multi-class plants, and TWh moved per class
(2023; 2024/2025 in `results/calibration/bench_multiclass_collapse.json`):

| ISO | plants | share of benched CEMS | largest per-class moves (2023, TWh) |
|---|--:|--:|---|
| MISO | 24–25 | 13.0 / 13.0 / 12.3 % | CT_PEAKER −25.4, COAL_PRB +11.2, COAL_BIT +5.3 (+COAL_LIGNITE ~+3), CC_REGULAR +16.3, ST_CHP −6.5, ST_GAS −5.9, CT_CHP +3.7 |
| NYISO | 7 | 11.6 / 9.8 / 10.2 % | CC_REGULAR +2.46, ST_GAS −2.24, CT_CHP +1.46, ST_CHP −1.46, CT_PEAKER −0.22 |
| PJM | 9 | 2.5 % (all years) | CC_REGULAR +9.0, CT_PEAKER −8.9 |
| CAISO | 0–1 | ≤0.2 % | CC_REGULAR +0.01 |
| NEISO | 1 | ≤0.2 % | CC_REGULAR +0.03..0.07 |
| ERCOT | 0 | 0 % | — (CAMPD binning: one class per plant by construction) |

Notes:
* `CT_PEAKER` is systematically the class alphabetical order hurt most: it
  wins every COAL/CC/CT_CHP mix and loses only to ST_*.
* The nyiso-88 §5 estimate ("MISO 9.2 %, ERCOT 8.8 %") measured CAMPD
  unitType spans; this lane measures **model-class** spans on each keeper's
  own reconstructed fleet (`bundle_fleet.reconstruct_bundle_fleet`, no LP),
  which is the population the scorer actually collapses. ERCOT's unitType
  spans are real but its fleet books whole plants to one class, so bench and
  model were already consistent there (a fleet-representation trait, not a
  scorer defect).
* nyiso-88 §5 assigned East River to CC_CHP per CAMPD unitType. This lane
  splits within the plant's MODEL classes (CT_CHP/ST_CHP) — the bench must
  attribute to classes the model dispatches, or D-1 pairing breaks. The
  CAMPD-says-CC / model-says-CT+ST disagreements (East River 2493, S A
  Carlson 2682 unit 20) are recorded as fleet-classification follow-ups.

## 2. What the defect never touched

* **C1.** `classFull` = EIA-923 per-(plant, prime-mover) class totals
  (`_eia923_frame` → canonical `classify_plant`), BTM-stripped; `gmModel` =
  class-level dispatch sums. Both are class-correct by construction.
* **C3a/C3b/C3c, C5a (except the CAISO anchor path), C6** — price, CO2
  (intensity is EIA-923-side), zonal volumes: no per-plant bench grouping in
  their inputs.
* **ERCOT entirely.**

What it did touch: the per-plant bench (`bench/<ISO>/<year>.json.gz` plant
entries) and run-payload plant entries → **D-1/C7 class shape actuals and
models**, D-2 materiality actuals and npl, the **C2 G-21b `coal_cems` anchor**
(MISO), the CAISO CEMS gas anchors (≤0.03 TWh — negligible), the C4-CAISO
CEMS-basis hourly gas actual, the per-plant capture/Δ diagnostics, and the
run-explorer per-plant and per-class tables.

## 3. The fix

`scripts/lib/bench_multiclass.py` (single home; the probe, the render and the
migration all import it — the characterization that predicted the correction
and the code that applies it cannot diverge), wired into
`render_calibration_html.build_payload` and `legitimacy_diagnostics`.

**Keying.** Every per-plant dict in the payload/bench is keyed by the
serialized `(plant_code, klass)`: bare `"<code>"` when the plant has one
scored class (all bytes unchanged), `"<code>:<KLASS>"` per class otherwise.
Consumers join bench↔payload by identical opaque keys (dashboard JS already
treats keys opaquely; `legitimacy_diagnostics` D-1 pairs slice keys directly,
D-2/D-4 consume a plant-level aggregation view — their floors-majority class
convention is deliberately independent and unchanged).

**The split basis (the real decision).** Measured bases only, most-measured
first (rule 14 [R-ACCURATE]); model outcomes are never a basis (splitting the
actual by the model's own dispatch would make the benchmark endogenous —
rule 13 [R-MEASURED]):

1. **CAMPD unit-level hourly gross-load shares** (`data/raw/campd-unit-level`),
   units mapped to the plant's classes by measured `unitType` technology
   family (CC / CT / boiler) with a coal-vs-gas branch on `primaryFuelInfo`.
   Hour-resolved — preserves each class's real diurnal shape, which is
   exactly what D-1 scores. Used for 15 of 24 MISO plants, 3–4 of 7 NYISO,
   all PJM CC/CT mixes. When CEMS units cover only a subset of classes (the
   `ct_only` shape), the facility series splits across the covered classes
   and the uncovered class's CEMS slice is genuinely zero (its actual lives
   in its EIA-923 slice).
2. **EIA-923 per-(plant, prime-mover) monthly shares**, flat within month —
   still measured, loses diurnal resolution. Used where the unit mapping is
   ambiguous (two classes in one technology family, or a CAMPD unitType that
   matches no model class — e.g. Ravenswood's CT0001 against a CC/ST model
   split).
3. **EIA-860 per-generator nameplate proration** (structural, not an
   outcome), flat. The documented last resort — in the applied migration it
   was needed for **one** plant-year (S A Carlson 2025, whose preliminary
   EIA-923 row is missing).

The EIA-923 side needs no proration at all: per-(plant, klass) annual and
monthly rows are assigned to the plant's model classes by exact name → family
→ largest-class mapping (single-class plants keep their whole-plant e923
bit-exactly). Slice `npl` prorates the committed plant nameplate by EIA-860
per-family nameplate, sum-preserving. Coal groups refine to the plant's
supply class (`_coal_supply_class`) exactly as the dispatch frame does, so
slice keys match the dispatch vocabulary (`COAL_PRB`, not `COAL`).

**Contract.** `docs/backcast-artifact-contract.md` §3.2/§3.3 updated; new
entries carry a `split` provenance field naming the basis.

**Pinned by** `tests/scoring/test_bench_multiclass_split.py`: a synthetic
two-class plant's energy lands in both classes in proportion to the stated
basis (hourly, monthly and capacity rungs, plus the zero-gross-hours annual
fallback), and the single-class byte-identity half: codec round-trip is
byte-identical and the migration passes single-class entries through
untouched (`assertIs`). The applied migration additionally asserted
byte-identity for every untouched ISO-year part (ERCOT ×3, CAISO 2023) and
verified single-class entries byte-equal in migrated parts.

## 4. Migration of committed artifacts (no re-solve)

`scripts/migrate_bench_multiclass.py`, driven by each keeper's own
reconstructed fleet composition (`run_year(fleet_only=True)` with every
recorded flag — the same no-LP path the floors rebuild uses):

* **Bench parts** (`bench/{CAISO,MISO,NEISO,NYISO,PJM}/{2023..2025}.json.gz`):
  multi-class entries replaced by per-class slices; slice sums equal the old
  plant totals exactly (verified); `classFull`, `co2`, `avgLMP`, `storage`
  untouched; `coal_cems` and the CAISO gas anchors recomputed from the
  corrected entries. NEISO 2022 (validation-holdout part) untouched.
* **Keeper payloads** (5 files): a multi-class plant's entry holds exactly
  the alphabetically-last class's dispatch, so it is re-keyed to that class's
  slice key and its r/NRMSE/capture recomputed against its own measured
  slice; the whole-plant CHP add-back is releveled to the slice e923 (flat,
  correlation-invariant). **The other classes' model dispatch is not
  recoverable from committed artifacts** — those slices carry a bench entry
  and no payload entry until the ISO's next registration re-renders from
  dispatch parquets with the fixed builder. Pre-fix non-keeper payloads keep
  bare keys: their multi-class plants drop out of the per-plant join
  (previously they joined mispaired); they re-join at each run's next
  render.
* **Committed `legitimacy_diagnostics.json` (5 keepers): D-1 replaced** with
  the corrected-bench recompute; D-2/D-4/D-5/D-9/D-10 keep their bundle-time
  dispatch-parquet provenance (the payload-path floors rebuild cannot
  reproduce the CAISO RA bridge, and D-2/D-4's bench dependence is only
  npl + materiality actuals — recomputed before/after with no verdict-level
  change). A `d1_provenance` field records the path change: the merged D-1's
  model side is the committed payload (quantized, surviving slices), not the
  original dispatch parquets.

## 5. Re-score: before vs after (same artifacts, same code path)

Protocol: BEFORE = current scorer on the committed artifacts as they stood;
AFTER = fixed scorer on the migrated artifacts; both verdict runs use the
committed payload + bench + diagnostics; both D-recomputes use the payload
path. (The committed bundle-time diagnostics used dispatch parquets, so they
differ from the payload-path BEFORE on MISO/PJM by up to ~0.5 in `profile_r`
— that difference is the DEFECT'S OWN model-side payload drop, not new
noise, and it is why the payload-path baseline is the honest comparator.)

**Determinations (unchanged, every ISO):** CAISO NOT-YET → NOT-YET, ERCOT
NOT-YET → NOT-YET, MISO NOT-YET → NOT-YET, NEISO CALIBRATED-WITH-CAVEATS →
CALIBRATED-WITH-CAVEATS, NYISO NOT-YET → NOT-YET, PJM NOT-YET → NOT-YET.
**No criterion status and no per-record status changed anywhere; no D-1/D-2/
D-4 row verdict changed.** The full per-record diff is empty except numeric
movement inside PASS:

| ISO | quantity | before → after |
|---|---|---|
| MISO | D-1 CT_PEAKER cv_ratio (23/24/25) | 2.262→1.006, 2.026→0.871, 2.097→0.840 |
| MISO | D-1 ST_GAS cv_ratio | 1.775→1.563, 1.484→1.298, 1.817→1.503 |
| MISO | D-1 ST_CHP profile_r (ungated) | +0.451→−0.795, +0.738→−0.751, +0.578→−0.765 |
| MISO | C2 coal_cems anchor | 176.0 → 192.5 TWh (2023; 2025 family actuals move ≤0.7 TWh) |
| NYISO | D-1 CT_PEAKER cv_ratio | 3.776→3.062, 3.762→2.914, 1.878→1.466 |
| NYISO | C1 CC_REGULAR 2023 | −2.78 TWh of ±2.94 — **bit-identical** (defect never in C1's path) |
| PJM | D-1 CT_PEAKER cv_ratio | 0.763→0.550, 1.279→0.873, 0.962→0.674 |
| CAISO/NEISO/ERCOT | all | no material movement |

Read on the lane's own terms: **the previous NYISO C1 pass was NOT an
artifact, and no keeper was passing (or failing) any gate on the strength of
the misattribution.** The defect's real damage was to the D-1 shape *actuals*
(and the MISO coal anchor), where it manufactured a spurious
"CT_PEAKER model too peaky" signal in MISO and understated actual CT
peakiness everywhere it collapsed a mix — corrected, the model's CT shape is
better than the old benchmark said.

## 6. Follow-ups discovered (owner scoping, not this lane)

1. **MISO ST_CHP model shape anti-correlation** (§0.5) — ungated today;
   candidate for the MISO lever queue as a diagnosis target.
2. **Fleet-classification disagreements with CAMPD unitType**: East River
   (2493) CT_CHP+ST_CHP vs CAMPD "Combined cycle"; S A Carlson (2682) unit 20
   likewise; Edwardsport (1004) modeled CC_REGULAR+COAL_BIT (IGCC). A fleet
   lane question (rule 14), NOT a bench question.
3. **Payload model slices lost to the defect** regenerate only at each ISO's
   next registration (dispatch parquets required); until then D-1's
   payload-path model side misses the non-surviving slices on both sides of
   the pairing (symmetric, no one-sided bias).
4. NYISO CT_PEAKER remains diagnosed-and-closed per nyiso-91 §6 (sub-zonal
   load-pocket commitment, needs owner scoping) — this lane's −0.22..−0.34
   TWh correction on its actual does not reopen it.

## 7. Governance

* Rule 1 [R-STRUCT]/13 [R-MEASURED]: no mechanism, no measured outcome fed
  back; split bases are measured inputs with forward analogues.
* Rule 14 [R-ACCURATE]: unit-level measured split preferred; proration used
  for exactly one plant-year, logged in the entry's `split` field.
* Rule 24-discipline (applied to a scorer): the full correction table was
  produced and written down before the scorer was touched; the fix's effect
  was known in advance and could not be chosen by what it did to any gate.
* Rule 22 [R-HOLDOUT]: 2023–2025 only; NEISO 2022 part untouched.
* Rule 26 [R-MECH-MATRIX]: no lever tested; no matrix cell changes.
* Keepers: none promoted, none de-designated; every movement reported here
  for the owner.
