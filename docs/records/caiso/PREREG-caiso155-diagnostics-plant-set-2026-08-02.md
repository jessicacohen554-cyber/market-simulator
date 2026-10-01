# PRE-REGISTRATION — caiso-155: the diagnostics-harness PLANT-SET defect (caiso-151 §F). Census populations, fix design, acceptance gates and stop rules, committed BEFORE any gate-relevant number is computed

**Session:** caiso-155 (CAISO/cross-ISO calibration). **Date:** 2026-08-02.
**Lane:** the caiso-151 §F filed defect — "the diagnostics harness scores a
plant-aggregated matrix built from CAMPD plant ids; the intertie tranches carry
`plant_code = 0` and an empty `plant_group`, so they are dropped from the matrix
that D-1, D-2 and D-4 all score" — carried unowned through caiso-152/153/154 §I.

**This is an AUDIT / SCORER fix, not a mechanism lever** (stated per rule 28a).
It re-tests NO adjudicated matrix cell, arms NO mechanism, adds NO
`ScenarioConfig` field, tunes NO parameter, and changes NO solve (the scorer is
diagnostic metadata only — `floor_mechanisms.py` module docstring: "nothing in
the LP build reads it"). Its matrix vehicle is a NEW cross-cutting audit row
(`diagnostics_plant_set_census`, the xiso-2 `outage_artifact_provenance` /
xiso-3 `forced_share_d4_census` pattern), not any ISO's lever queue.

**LP budget: ZERO.** No solve, no dashboard registration, no rule-22 marker.
Floors are reconstructed through the STANDING G-06 reconstruction path
(`run_year(fleet_only=True)` from each bundle's own `meta.json` — the exact
fallback `diagnose_bundle` and CI's D-2 recompute already use; it exits before
any LP is constructed). That is not a keeper replay. Holdout: only 2023–2025 is
touched; the spend freeze (`holdout-freeze.json`) stays untouched and outranks
everything.

Keepers at entry (from `frontend/data/backcast/keepers/*.json`, this session):
ERCOT `2026-08-01-ercot149-gas-event-cap`, CAISO `2026-07-31-caiso153-reid-b`,
PJM `2026-07-31-pjm-143b-hy-level`, MISO `2026-07-31-miso-109b-hy-level`,
NYISO `2026-08-01-nyiso109-zonal-margin-anchor`, NEISO
`2026-07-31-neiso-72-hy-window`.

---

## 1. The defect, restated precisely (from code at HEAD, before any measurement)

Two drop sites in `scripts/legitimacy_diagnostics.py`, one structural absence:

1. **Floors side** — `aggregate_floors_by_plant`: `keep = plant_code > 0`
   drops every unit-row with `plant_code <= 0` from the plant aggregation that
   supplies D-2/D-4 their `floors`/`mechs`/`klass` matrices.
2. **Dispatch side (parquet path)** — `diagnose_bundle`:
   `sub = frame[frame["plant_code"] > 0]` drops the same rows from
   `model_plants_plant`.
3. **Dispatch side (payload path)** — `load_payload_plants` is keyed by CAMPD
   bench plant ids BY CONSTRUCTION, so interchange pseudo-units can never
   appear there at all.

Consequence: every floor riding on a `plant_code <= 0` pseudo-unit —
`MECH_FIRM_IMPORT` (CAISO RA/LTC firm blocks, MISO Manitoba + the PJM-seam
firm floor, NYISO HQ) — is invisible to D-2 and D-4, including the
`(MECH_FIRM_IMPORT, None): (0, 24)` `D4_WINDOWS` row caiso-151 added
(necessary but not sufficient — its §F correction). D-1 is NOT defective for
these rows: it is a model-vs-CAMPD shape comparison and a boundary tranche has
no CAMPD actual to compare against (scoped out below, with this reason).

## 2. Pre-registered census populations (measured BEFORE the fix, with the HEAD scorer)

Per keeper bundle × year (all six ISOs × 2023/2024/2025):

* **P1 — floors-side dropped rows:** rows in the bundle's floor source with
  `plant_code <= 0` AND max-over-hours `min_gen` > `D2_FLOOR_MIN_MW` (1.0 MW).
  Floor source = committed `floors/<year>_*.npz` when present, else the G-06
  rebuild (none of the six bundles commits floors — verified by `ls` this
  session — so all go through the rebuild). Reported per row: `unit_id`,
  `plant_group`, mechanism ids present, hours floored, mean/max floored MW,
  annual floor energy in TWh (Σ `min_gen` over floored hours).
* **P2 — dispatch-side structural fact:** the payload carries no pseudo-unit
  series (asserted: no P1 `unit_id` resolves to any payload plant key);
  `dispatch/*.parquet` is gitignored-absent in every committed keeper bundle
  (asserted per bundle). Recorded, not per-unit-measured.
* **P3 — the complement (control):** count of `plant_code <= 0` rows carrying
  NO floor > 1 MW (import bands never floored, export sinks, seam rows) — the
  population the fix must NOT drag into the matrices.
* **P4 — class-label guard:** the `plant_group` of every P1 row. Expected
  `""` for all. See stop rule S2.
* **P5 — D-4 coverage:** mechanisms appearing in P1 rows without a
  class-applicable `D4_WINDOWS` entry (expected none: `firm_import` has its
  all-hours row since caiso-151). Any other mechanism found on P1 rows is
  REPORTED as a rule-12 declaration gap — no `D4_WINDOWS` entry is minted in
  this session (the xiso-3 discipline: "a rule-17 declaration needs its own
  per-ISO driver evidence").

The census probe (`scripts/probes/_caiso155_plant_set_census.py`) additionally
asserts, against the HEAD scorer, that P1 keys are ABSENT from
`aggregate_floors_by_plant`'s output (the defect reproduced) — the
falsifiable premise. If P1 is empty for every ISO, the defect is vacuous at
current keepers: FILE AND STOP, no scorer change ships.

## 3. Pre-registered fix design (committed before the census numbers exist)

ISO-generic; no per-ISO branch anywhere (rule 25 governs parameters — shared
scorer structure stays shared):

1. **`aggregate_floors_by_plant`**: rows with `plant_code > 0` aggregate to
   plants exactly as today (byte-identical output for them). Rows with
   `plant_code <= 0` AND a positive floor (> `D2_FLOOR_MIN_MW` in any hour)
   each become their own pseudo-plant row keyed `"u:<unit_id>"` (the `u:`
   prefix cannot collide with numeric plant keys), class = the row's own
   `plant_group`, mechanism = the row's own stamps. Unfloored `plant_code <= 0`
   rows (P3) stay excluded — they contribute no floor and must not perturb
   any denominator.
2. **`diagnose_bundle`**: the dispatch matrix build is UNCHANGED on both paths
   (`plant_code > 0` parquet filter; CAMPD-keyed payload). Floors-side pseudo
   keys enter `all_pids`; their dispatch rows are set to their own floor row
   (`disp := min_gen`), their `npl` to 0, on EVERY path.

   **Pre-registered semantics — the floor-energy convention:** for pseudo-unit
   rows the committed artifact reports the MANDATED FLOOR ENERGY (`min_gen`
   itself), not dispatch-at-floor. Rationale, fixed ex ante: (a) the committed
   keeper bundles carry no per-tranche dispatch (P2), so at-floor dispatch is
   not computable from committed data; (b) using the floor on every path keeps
   the artifact PATH-INDEPENDENT — the same bundle scores identically whether
   the gitignored `dispatch/*.parquet` happens to exist (the #1488/G-06
   path-divergence lesson); (c) the floor energy is the quantity the floor
   MANDATES — the right budget number for a boundary tranche — and for CAISO
   it is exactly the caiso-151 §C exposure statistic (forced→clipped), giving
   an external anchor (gate A4). The true at-floor statistic (e.g. caiso-151
   §F's 15.4689 TWh, CAISO 2024) remains a probe-level measurement on
   unaggregated LP rows; the two numbers are DIFFERENT STATISTICS and the
   FINDING states both definitions. A per-year note in the D-2/D-4 results
   names every pseudo-unit key scored under this convention.
3. **D-1**: untouched. Its plant set is the bench∩model pairing by definition
   (model-vs-CAMPD shape); a boundary tranche has no CAMPD actual, so there is
   nothing to shape-test. Stated in the module docstring.
4. **Gate arithmetic invariance (expected, verified by A2/A3):** new D-2 rows
   carry class `""` (never summarized/gated — `run_d2` excludes `""`) and
   mechanism `firm_import` ∈ `NON_THERMAL_MECHS` (excluded from
   `forced_gated`) and ∈ `calibration_verdict.FORCED_EXEMPT_MECH_NAMES`
   (excluded from C8 escalation); new D-4 rows ride the existing all-hours
   `firm_import` window (off-window share ≡ 0 ⇒ pass by construction). So the
   fix ADDS VISIBILITY ROWS and flips no gate — that is the prediction this
   pre-registration commits to, and gates A2/A3 test it rather than assume it.
5. Docstrings updated; new unit tests for the pseudo-row path (synthetic
   fleet with a `plant_code = 0` floored tranche: appears in D-2 rows and D-4;
   absent from D-2 summary; a `plant_code > 0` control unchanged).

## 4. Acceptance gates (ex ante)

* **A1 — reproduction baseline:** per affected keeper bundle, the HEAD
  (pre-fix) scorer regenerates the artifact in-session; diff vs the committed
  `legitimacy_diagnostics.json` on D-1 rows, D-2 rows/summary, D-4 rows. Drift
  beyond G-06's documented reconciliations (`ra_mustoffer_bridge` absence in
  rebuilt floors; per-class share jitter ≤ `D2_VERIFY_SHARE_TOL` = 2.5 pp on
  material classes) is reported and diagnosed BEFORE proceeding; the A2 diff
  is then taken against the same-session pre-fix regen (same environment,
  same data), never against stale bytes.
* **A2 — additivity:** post-fix regen vs pre-fix regen, same bundle: every
  pre-existing row and summary entry IDENTICAL; the delta is ADDITIONS only
  (new D-2 rows with class `""`/exempt mechanisms; new D-4 rows; notes). Any
  modified pre-existing value = a defect in the fix; stop and fix before any
  re-gate.
* **A3 — gate invariance through the production rubric:** re-score each
  affected keeper with the xiso-3 instrument
  (`scripts/probes/_xiso3_forced_share_d4_census.py`, which reads the live
  keeper shards and scores through `calibration_verdict` itself) before and
  after the artifact regen. Criterion profile and determination must be
  IDENTICAL. Any flip → stop rule S1.
* **A4 — external magnitude anchor (CAISO only):** the regenerated
  `firm_import` floor energy for CAISO 2023/2024/2025 must land within ±5 %
  of the caiso-151 §C clipped-floor exposure (17.938 / 22.684 / 22.494 TWh)
  — the keeper (`caiso153-reid-b`) carries the caiso-151 recipe, and the §C
  numbers were computed pre-arm from the same injection path. MISO/NYISO
  magnitudes have no pre-registered external anchor; they are census OUTPUTS
  reported with their config provenance (Manitoba block + the MISO–PJM seam
  firm floor 2615/1710/1135 MW; `NYISO_FIRM_IMPORT_FLOOR_FRAC`), not gates.
* **A5 — suite health:** `pytest tests/scoring/test_legitimacy_diagnostics.py`
  green (plus the new tests); `ruff format --check` clean on touched files;
  `scripts/check_mechanism_matrix.py` green after the matrix edit. The two
  PRE-EXISTING failures (`test_clean_io.py::TestRegenerateEntrypoint::
  test_datatype_list_matches_schemas`,
  `test_consume_phase3d.py::EgridZoneAssignmentParity::
  test_zone_lookup_matches_raw`) are known clean-origin (reproduced at
  caiso-152) and out of scope.

## 5. Stop rules (ex ante)

* **S1 — verdict flip:** if ANY keeper's criterion profile or determination
  changes under A3, STOP: no demote/promote, no keeper-shard edit, no matrix
  keeper-header restamp; surface to the owner with the full diff (re-gating
  three ISOs' keepers is owner-visible). Leave-one-year-out scoring within
  2023–2025 precedes any keeper motion in the follow-up, per rule 20/22.
* **S2 — non-empty class label on a P1 row:** a `plant_code <= 0` floored row
  carrying a NON-empty `plant_group` would enter a GATED class's denominator
  under the fix. If the census finds one, that row family is EXCLUDED from
  the shipped fix (kept dropped), reported in the FINDING with its identity,
  and the inclusion decision escalated — never silently included or excluded.
* **S3 — blocked rebuild:** if an ISO's floors rebuild fails on a
  gitignored-absent raw input (the documented PJM `pjm-da-virtuals` class of
  hazard), that ISO is censused statically (meta flags + config provenance),
  marked BLOCKED, and its artifact is NOT regenerated this session.
* **S4 — empty defect:** if P1 is empty at every ISO, file the census and
  ship NO scorer change (the premise would be refuted).

## 6. Deliverables (unchanged by outcomes)

Probe + transcript, `FINDING-caiso155-*.md` with its own DO-NOT-REDO, the
regenerated `legitimacy_diagnostics.json` per affected keeper (additive diff
only, A2/A3 passing), matrix audit row `diagnostics_plant_set_census` +
§5.7 entry + per-ISO `ev` citations in the same session (rule 28b),
`docs/calibration-log/caiso.md` entry + cross-ref stubs in each touched ISO's
log. NO dashboard registration (no LP — the caiso-136/143/144/149/150/152/154
pattern), NO rule-22 marker for any ISO.

DO-NOT-REDO carried: ALL of FINDING-caiso154 §H, caiso-153 §G, caiso-152 §H,
caiso-151 §H (including: the D4_WINDOWS entry is NOT evidence of visibility —
this session is the visibility fix), caiso-150 §H, caiso-149 §G, caiso-148 §G,
caiso-147 §G, caiso-146 §G, caiso-144 §G, caiso-143 §H/§I, caiso-142 §K,
caiso-141, caiso-138 §G, caiso-137b §6, caiso-131 §10; pjm-141 D-BIN; the two
CAISO ledgered caveats (C3a-2025 / C3c) are not touched.
