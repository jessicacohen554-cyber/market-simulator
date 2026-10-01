# XISO-6 — the thermal-tranche vintage sidecar + arm-over-gap guard (xiso-5's named cheapest unblock, LANDED)

**Date:** 2026-08-25 · **Determination:** IMPLEMENTED — **NO LP, no solve, no
scoring, no registration, no keeper changed in any ISO, no cell verdict
minted, and NO artifact regenerated** (rule 23 `[R-FROZEN-DERIVE]`: no
source-data change is cited, so none is licensed — enforced below by
byte-identity hashes).

**Charter:** close the coverage trap xiso-5 diagnosed
(`FINDING-xiso5-thermal-tranche-coverage-2026-08-04.md`), by the fix that
finding's §6 names as option 4 and `docs/mechanism-testing-matrix.md` §5.7
names verbatim as the "recommended cheapest unblock": stamp the deriver's
`_ONLINE_FRAC_GROUPS` + schema generation into a sidecar, so one read answers
"which groups was this file's vintage emitting?" — the question that cost
xiso-5 its whole §3.

> **Session label.** xiso-1 … xiso-5 are spent
> (`results/calibration/FINDING-xiso{1..5}-*.md`); this session is recorded
> as **xiso-6**. The branch keeps the harness slug.

---

## §1 — What landed (four deliverables, no keeper-visible byte moved)

1. **Sidecar emitter** — `scripts/data/derive_thermal_tranches.py` now writes
   `thermal_tranches_<ISO>.meta.json` next to every CSV it emits
   (`write_tranche_sidecar`): the sidecar schema version, the CSV's sha256 /
   row count / column order, a per-column per-group `status="ok"` coverage
   census, the deriver identity, and a `vintage` block carrying the group
   sets in force at emit time (`_ONLINE_FRAC_GROUPS`, `_CHP_GROUPS`,
   `_PEAKING_GROUPS`, `_THERMAL_GROUPS`) plus the derive invocation. A
   **sidecar, not an in-file header**: `campd_bins.thermal_tranche_overrides`
   is called ungated (`campd_bins.py` / `model/reserves/spec.py`) and reads
   `committed_pct`/`mustrun_pct` unconditionally, so ANY change to the CSV
   bytes is a keeper-moving change in that ISO (xiso-5 §4.3(ii)). The JSON is
   deterministic — sorted keys, no timestamps — so re-running the same derive
   reproduces the same sidecar bytes.
2. **Five descriptive backfills** — `--backfill-sidecar` (new mode, reads the
   CSV bytes only, no CAMPD, no derivation) run once per committed artifact
   (CAISO/MISO/NEISO/NYISO/PJM). Provenance `"backfill-descriptive"`; the
   vintage group sets are recorded as **null = UNKNOWN** — they are not
   recoverable from the files' bytes, and the sidecar records that honestly
   instead of inferring what HEAD would emit. The observed column set and
   per-group populated counts (the xiso-5 §1 census, now machine-readable)
   are what a backfill records.
3. **Arm-over-gap guard** —
   `campd_bins.assert_thermal_tranche_coverage(iso, config)`, called at the
   top of `assembly.bins_to_fleet` (the one seam every CAMPD-binned fleet
   build passes through). For each of the seven artifact-reading gates
   (`cc_mustrun_per_plant`, `st_gas_mustrun_per_plant`,
   `coal_sync_srmc_tranche`, `coal_mustrun_online_pmin`,
   `st_gas_mustrun_p25_level`, `cc_peaking_per_plant`,
   `chp_steam_floor_p25`) the running config ARMS, it raises `ValueError` —
   naming the ISO, gate, group, column and row counts — when the consumed
   column is absent from the ISO's artifact or blank in any `status="ok"`
   row of the mechanism's target groups. Rule-24 precedent: armed without
   the resolved map is a hard error, never a silent fallback.
4. **Census probe extended** —
   `scripts/probes/_xiso5_thermal_tranche_coverage.py` reads the sidecars
   (new `sidecar_census()` + a `VINTAGE SIDECARS` section and a `sidecars`
   JSON key): provenance, recorded emit groups (or UNKNOWN), and a
   **staleness check** (sidecar `artifact_sha256` vs current CSV bytes), so
   a CSV moved without a re-stamp is caught by the one-command census.

Tests: `tests/unit/data/test_thermal_tranche_guard.py` (12 synthetic
trivial-first cases + 5 committed-artifact integration cases) and
`tests/curation/test_derive_thermal_tranches_sidecar.py` (4 writer cases).
All pass; the full `tests/unit/data/` lane passes except 20 pre-existing
failures in `test_firm_import_{shape,selfschedule}.py` that reproduce
identically on clean `origin/main` in this environment (missing `tzdata`
module — environment gap, not this change).

## §2 — Byte-identity proof (rule 23): the five CSVs before and after

sha256, measured before any edit and re-measured after the backfill run.
**Identical in every ISO — no artifact regenerated, no CSV byte moved.**

| ISO | sha256 (before AND after — identical) | rows |
|---|---|---|
| CAISO | `4ed8ae722473634768483b47b5fd58425116905c90baafed2da21e94c91de3c3` | 156 |
| MISO | `31949ee5e13475db7611c2c6f15175626e17d414df534fab9179be66614280d8` | 282 |
| NEISO | `2667ab9641b906113e7d4f0c8e2dcbc7909ce350de471a9dfea7aa857fdb2ad7` | 76 |
| NYISO | `0dae176b8a46e24f0a887df9f730ee7bc6e1170c0719e036c440927d34bf497f` | 78 |
| PJM | `497c4844eb0c8f057848dca082cf3d40c26212c60cac9a1364c04bbaee367cd5` | 256 |

The same hashes are frozen into each ISO's committed sidecar
(`artifact_sha256`), which is how the probe's staleness check binds sidecar
to CSV from now on.

## §3 — What the guard now catches that `campd_bins.py:1287` used to swallow

The loaders skip a blank row silently, so before this change every one of the
following configurations would have **run to completion with the mechanism
engaged on nothing** and read as inert on the merits — the false negative
rule 26's DO-NOT-REDO discipline would then have made permanent (xiso-5
§4.3(i)). Each is now a hard error at fleet build, measured in this session
against the committed artifacts:

| armed at | gate | what fires |
|---|---|---|
| CAISO | `cc_mustrun_per_plant` | `online_frac` blank in 23/23 ok CC_REGULAR rows |
| CAISO | `st_gas_mustrun_per_plant` | blank in 3/3 ok ST_GAS rows |
| PJM | `st_gas_mustrun_per_plant` | blank in 10/10 ok ST_GAS rows (the §3 vintage proof's population) |
| PJM | `chp_steam_floor_p25` | `steam_level_cf`/`p25_allhr_cf` COLUMN ABSENT (10 ok CHP rows) |
| NYISO / NEISO | any `online_frac` gate | COLUMN ABSENT (47 / 39 ok emitting-group rows) |
| NYISO / NEISO | `coal_mustrun_online_pmin` | `mustrun_online_pct` COLUMN ABSENT (where COAL ok rows exist) |
| ERCOT (or any artifact-less ISO) | any guarded gate | NO ARTIFACT — per-plant artifact gates cannot arm there |

What can **never** fire, by construction (the guard's target groups mirror
each consumer's own group gate):

* the by-design CHP `online_frac` blanks — no `online_frac` gate targets a
  CHP group ("their floor is the steam host", rule 19 `[R-ONE-MECH]`; xiso-5
  §2, CLOSED — this session does not re-open it);
* the by-design non-CC `peaking_pct` blanks and non-CHP `steam_level_cf`
  blanks;
* blank non-`ok` rows (`eia923_cf`, `rarely_online`, `chp_floor_only`) — the
  deriver's own skip, not a vintage gap;
* a target group with zero `ok` rows — a class CEMS cannot see is the
  self-targeting design, not a gap.

**Measured a no-op at all six current keepers**: each ISO's designated
keeper gate set (read from its own committed `run_config.json`) passes the
guard against its own committed artifact
(`test_thermal_tranche_guard.py::TestCommittedArtifacts::test_no_op_at_every_current_keeper`),
which is xiso-5 §4.3(i)'s "zero silent no-ops today" re-verified as an
executable invariant. MISO — the census's clean control arm — passes even
with **all** guarded gates armed at once.

## §4 — Rule compliance

* **Rule 23 `[R-FROZEN-DERIVE]`** — no regeneration: §2's hashes are the
  proof. The backfill mode derives nothing (CSV bytes read, hashed, left
  identical); the emitter fires only inside a real (future, separately
  licensed) derive run.
* **Rule 25 `[R-ISO-SCOPE]`** — structurally safe here, as xiso-5 §4.3
  established: the artifact family is per-ISO by construction and no
  solve-path reader pools across ISOs, so nothing in this session can reach
  another ISO's keeper. That reassurance licensed **no** regen anyway.
* **Rule 26 `[R-MECH-MATRIX]`** — no mechanism tested, no cell verdict
  moved; the `thermal_tranche_artifact_coverage` audit row (cells `.OOIOO`,
  unchanged) gains evidence citations only, in this session. **No new
  `ScenarioConfig` field** — duty (c) does not fire; the guard reads only
  existing registered gates.
* **Rules 5/11 `[R-NO-MAGIC]`/`[R-DOCSTRING]`** — every new constant cited
  and commented; module + public-function docstrings on everything added.
* **Rule 27 `[R-PUSH]`** — the four edited ≥300-line files
  (`derive_thermal_tranches.py`, `campd_bins.py`, `assembly.py`, the probe)
  were edited locally and pushed as on-disk bytes, blob-verified after push.
* **Rule 22 `[R-HOLDOUT]`** — no year solved, scored or registered; only
  committed bytes read.
* **Rule 19 `[R-ONE-MECH]`** — the CHP closure is honoured, not revisited:
  the guard is built so the CHP blanks are unreachable (§3).

## §5 — What this session deliberately did NOT do

* **No regeneration of any `thermal_tranches_<ISO>.csv`** — the 166-row gap
  is still there and still owner-gated per-ISO (miso-95 `PROVENANCE-BLOCKED`
  → xiso-5 §6(b)/(c)). The sidecar records the state; the guard makes
  arming over it loud; **only that ISO's own pre-registered keeper-grade
  A/B may close it.**
* **No PJM ST_GAS "fix"** — vintage, code-proven, recorded (xiso-5 §3); the
  guard now refuses to let it masquerade as inertness.
* **No new ScenarioConfig field, no CLI calibration flag, no workflow.**
* **No keeper, registry, status, bench or calibration file touched.**

## §6 — Reproduce

```
# the one-command census, now sidecar-aware (staleness check included)
python scripts/probes/_xiso5_thermal_tranche_coverage.py

# re-stamp a descriptive sidecar (reads bytes only; CSV untouched)
python scripts/data/derive_thermal_tranches.py --iso PJM --backfill-sidecar

# the guard + sidecar test set
pytest tests/unit/data/test_thermal_tranche_guard.py \
       tests/curation/test_derive_thermal_tranches_sidecar.py -q
```

**DO-NOT-REDO:** the vintage question is now answered by the sidecar +
probe; do not re-derive xiso-5 §3's code proof, and do not re-open the CHP
closure. A future real re-derivation writes a `provenance="derived"` sidecar
automatically and needs no manual stamp.
