# FINDING — caiso-190: the silent-partition no-op class is closed on **both** solve paths, and a bundle can finally say **which seam cap it solved against**

**Outcome: ORCHESTRATION + PROVENANCE only. No LP formulation change, no solve, no
calibration edit, no `ScenarioConfig` field, no default moved.** Keeper **UNCHANGED** at
`2026-08-09-caiso-188-d1-micseam`; no keeper/status/attestation file touched. Behaviour
with the partitions **present** is unchanged and pinned by a test that now actually
exercises that path (it did not before — §4). **2023–2025 only**; no out-of-training year
was solved, scored, read or registered.

**No PRECHECK was written and none is owed.** A PRECHECK fixes an identification before a
value exists, so a measurement cannot be steered by its own result. This session measures
nothing about the market: it wires an existing guard onto the lanes that actually solve,
adds output provenance, and adds tests. There is no arm, no gate, no band and no number
that could have been tuned. **C3a was never read**, in either direction.

**Rule 28 `[R-MECH-MATRIX]` statement, as required.** The **CAISO lever queue is EMPTY,
with every cell adjudicated** (caiso-185, re-confirmed caiso-188/191). **This session is
off-queue by design**: it is rule-14 / rule-20 provenance-integrity work on the solve
path — **not a lever, not a mechanism, no solve.** **No matrix cell changes**; §5.2 gains
a session note only.

Verified against `origin/main` at **`6b87c9d`** (the campaign brief cites `767b29c3`; main
had advanced — see §6 C-0).

---

## §1 — STEP 1: the solve-path map, verified first-hand

`run_energy_solve` is the single door to the LP. It has exactly **three** call sites, and
`tests/unit/pipeline/test_p1_prep_wiring.py` already pins that count:

| # | module | lane | status at `6b87c9d` |
|---|---|---|---|
| 1 | `scripts/run_calibration.py:5064` (`run_year`) | **backcast / calibration — production** | guard **WIRED** (caiso-188) |
| 2 | `src/market_sim/runner.py:2870` (`run_scenario_iso`) | **forecast — production** | guard **ABSENT** |
| 3 | `src/market_sim/pipeline/year.py:372` (`run_year_solve`) | **DEAD** | guard wired, never runs |

**`pipeline/year.py::run_year_solve` is still dead and is NOT deleted here.** Re-verified
this session: `grep -rn "run_year_solve(" src/ scripts/` returns **no caller** outside its
own definition — only the `pipeline/__init__.py` façade re-export and
`tests/regression/test_pipeline_facade_shims.py`, which asserts that re-export. It is the
orchestrator-unification lane's landing site (refactor-consolidation plan §5) and deleting
it would break the façade-shim guard, so its status is **documented, not changed**. It
keeps its guard call, which is now consistent with the invariant in §4 rather than the
sole instance of it.

The flag → data resolution sites read this session:

- **Interchange seam** — `model/interchange/spec.py::apply_interchange_topology`, the
  `capacity_deliverability_limits` branch. Resolves the published MIC through
  `data/clean/capacity-deliverability/` (gitignored, disposable, built by no solve) and
  falls through to the baked `WECC_import_simultaneous` scalar when it does not resolve.
- **Hydro RoR** — `data/hydro_modes.py::load_hydro_shapeable`, returning `None` + a warning
  when `data/clean/hydro-plant-modes/<ISO>` is absent; the LP is then simply unchanged.
- **CAMPD outage overlay** — `data/outages.py::unit_outage_csv_for_iso` →
  `_load_unit_outage_events`, returning `None` → `{}` derate factors when the extract is
  missing. `scripts/lib/outage_detect.py` is the detector, not a loader (the brief's
  `outage_detect.py` path is `scripts/lib/`, not `src/market_sim/data/`).

Run-config writers: `pipeline/persist.py::write_run_config` (backcast, aliased by
`run_calibration_full.py:2562`, called at `:5726`) and `scripts/lib/run_record.py::
write_run_config` (forecast/hindcast records). This session extends the **backcast**
writer, which is the one that produces calibration bundles.

## §2 — STEP 2: the guard, wired to the real lanes with per-flag severity

`market_sim.data.input_completeness` gains three things. It still carries **no
ScenarioConfig field, no threshold and no tunable** — `strict` is a property of the calling
lane, not a knob a scenario can set — so it remains a pure config-vs-disk assertion.

**(a) The registry is now a typed, additive list.** `PartitionRequirement` carries
`flag`, `datatype`, `location`, `build_command`, an `absent(iso)` probe, an optional
`armed(config)` predicate, and — the severity switch — `fallback: str | None`. A new
mechanism appends one entry and inherits the whole guard on both lanes with no call-site
change.

| requirement | armed by | data | fallback | missing ⇒ |
|---|---|---|---|---|
| `capacity_deliverability_limits` | flag truthiness | `data/clean/capacity-deliverability/<ISO>` | the baked simultaneous-import scalar (**fitted**) | **strict: FAIL** · non-strict: loud WARN + recorded |
| `hydro_ror_split` | flag truthiness | `data/clean/hydro-plant-modes/<ISO>` | **none** — the classifier *is* the mechanism | **FAIL, every lane** |
| `outage_source == "historic"` | `armed` predicate (string axis, not a bool) | `data/raw/campd-unit-outages-<ISO>.csv` | statistical availability | **strict: FAIL** · non-strict: loud WARN + recorded |

**(b) Both production lanes call it.** The forecast orchestrator
(`runner.py::run_scenario_iso`) now calls it on the **resolved** config — after
`apply_iso_scenario_defaults`, so an ISO default that arms a mechanism is checked too —
and before any LP input is built. The backcast lane's existing call now states
`strict=True` explicitly.

**(c) Strict is the DEFAULT, and the calibration lane keeps it.** This is the polarity
that matters: a caller must opt *out*. `scripts/run_calibration.py` — the lane
`run_calibration_full.py` drives and the only lane keepers are promoted from — passes
`strict=True`, so **its behaviour is byte-for-byte what caiso-188 left**. Nothing is
loosened anywhere; the forecast lane, which had *no* guard at all, gains one at
`strict=False`.

> **Why the forecast lane is not strict.** No keeper is promoted from it, and with §3 the
> value it degraded to is recoverable from the bundle. A mechanism with **no** declared
> fallback still fails fast there, because "warn and continue" would mean advertising a
> mechanism that provably did not run.

## §3 — STEP 3: `resolved_inputs`, and why it is RECORDED rather than re-derived

`run_config.json` gains a top-level `resolved_inputs` block (schema `1`), built by the new
`market_sim.data.resolved_inputs`. Contract documented at
`docs/backcast-artifact-contract.md` §2.2.1.

```
resolved_inputs.seam_import_cap.by_year.<year> = {
    cap_mw, source, delivery_year, season, import_zone, flag_armed
}
resolved_inputs.hydro_plant_modes  = {flag_armed, partition_present,
                                      classified_plants, shapeable_plants}
resolved_inputs.campd_unit_outages = {armed, path, present, sha256, bytes}
```

`source` is the load-bearing field and its three values are the whole point:

- **`mic_partition`** — Part A resolved; the LP solved on the published per-area MIC sum.
- **`baked_fallback`** — the flag was **ARMED** and the partition did not resolve, so the
  fitted scalar governed. **This is the caiso-188 state**, now self-identifying.
- **`flag_off`** — never armed, so the baked value is the declared limit, not a
  degradation.

**The value is recorded at resolution time, not re-derived at record time.**
`apply_interchange_topology` resolves through the single shared
`resolve_seam_import_cap()` and calls `record_seam_resolution()`, so what lands in the
bundle is the value the LP was handed. A second derivation at record time could disagree
with the first — which is exactly the defect class this session exists to close
(caiso-188 §7 item 5: *check the DATA the gate resolves through*). The resolution logic
itself moved statement-for-statement: same delivery year and season, same per-area
aggregation, same **truthiness** test, so a `0.0` still falls through to the baked cap as
it always did. `TestSpecResolvesThroughHelper` statically fails a future re-inlining.

Where no solve in the writing process resolved a seam — a meta-only writer, or a
`--reuse-solved` bundle whose years were copied — `status` reads **`unrecorded`** rather
than being back-filled. An honest gap beats a plausible re-derivation.

**Cache-key and registry-parity guards are unaffected, as assumed and now checked.**
`git diff src/market_sim/config/scenarios.py` is **empty** — no `ScenarioConfig` field was
added, so the rule-28 CI guard's duty (c) does not fire; `scripts/check_mechanism_matrix.py`
runs clean (integrity OK, anchors OK, keeper stamps OK). The block is **top-level, outside
`scenario_config`**, and the `--reuse-solved` comparator
(`run_calibration_full.py:2782-2800`) canonicalises and diffs **only** `scenario_config`,
so no reuse decision moves. No golden asserts a `run_config.json` key set.

## §4 — a second defect, found while testing: the guard treated an UNREADABLE partition as healthy

`check_clean_partitions` wrapped each probe in `except Exception: continue` — "a probe must
never be the reason a solve dies". That is the same silent-no-op reasoning the module
exists to refute: **a partition that is present but unparseable degrades the mechanism
exactly as an absent one does**, so swallowing the probe's exception lets the solve
proceed on an unverified input.

It was not hypothetical. `tests/unit/data/test_input_completeness.py::
test_present_partitions_pass` — the one test asserting the partitions-present path —
**passed for the wrong reason**: its fixtures wrote bare `to_parquet`, the reader rejected
them for having no embedded `market_sim.datatype` metadata, **both** probes raised
`SchemaError`, and the guard swallowed both. Measured this session by running that test
with `--log-cli-level=WARNING`: two `SchemaError` tracebacks, then `PASSED`. The
partition-present leg of the guard had never been exercised.

Both halves repaired:

- Fixtures moved to `write_clean` in `test_input_completeness.py` **and** the new
  `test_resolved_inputs.py`, so the present-path assertions now read real partitions
  (re-measured: **zero** `SchemaError` lines).
- A raising probe is now collected as **unverifiable** and **fails closed in strict mode**
  — the same discipline rule 22 applies to an unrecognised holdout year — while staying
  loud but non-fatal on the forecast lane.

## §5 — STEP 4: tests and lanes

**23 new tests**, all passing. `ruff check` and `ruff format --check` clean across
`src/`, `scripts/`, `tests/`.

- `tests/unit/data/test_resolved_inputs.py` (**17 new**) — the three resolution states;
  the applied cap and the recorded cap agreeing; per-year recording across a 3-year
  bundle; hydro presence/count; CAMPD sha; `resolved_inputs` landing in a written
  `run_config.json` with `scenario_config` unpolluted; and two static guards —
  `TestEverySolvePathIsGuarded` (**every module that calls `run_energy_solve` must also
  call `check_clean_partitions`**, plus the strict/non-strict posture asserted at each
  call site) and `TestSpecResolvesThroughHelper`.
- `tests/unit/data/test_input_completeness.py` (**6 new**, 7 existing still green and now
  meaningful) — strict-by-default; declared fallback warns when non-strict; no-fallback
  mechanism raises even when non-strict; the strict failure names the lane; the CAMPD
  entry armed/unarmed on both severities; unreadable partition fails closed in strict.

**Fast lane** (`pytest -n auto -m "not slow and not integration and not fulldata"`),
measured **in this container, both arms, same session**:

| arm | failed | passed | errors |
|---|---|---|---|
| baseline (`git stash`, clean `6b87c9d`) | 669 | 5,863 | 53 |
| with caiso-190 | 669 | **5,886** | 53 |

**Delta: +23 passed, +0 failed, +0 errors.**

The 669/53 are **pre-existing and environmental, not the README's 2**: the campaign's
sparse-checkout recipe (`data/dictionary data/raw/reference`) is cone-mode, so `data/raw/`
materialises its 68 top-level files but **none** of its subdirectories — `_processed-legacy/`,
`eia-860/`, `campd-unit-level/`, `fleet-egrid/`, `eia-930/` are all absent, and the
failures are `FileNotFoundError` on those paths. The brief's **6,620/2** baseline assumes
the full `data/raw` tree; it is **not reproducible under the campaign's own checkout
recipe**, so the delta above — measured against a stashed baseline in the same container —
is the honest comparison. Widening to the full tree was not attempted: `data/raw` is large
enough that a CI checkout of it exhausted the runner disk during caiso-189
(`FINDING-caiso189` §8), and the delta answers the question the baseline was for.

## §6 — CONTRADICTIONS (reported, not silently resolved)

**C-0 — base commit.** The brief pins context to `main@767b29c3`; `origin/main` was at
**`6b87c9d`** when this session cloned (2026-08-11). A `--depth=1` clone cannot resolve
`767b29c3`, so ancestry was not verifiable. Everything below was re-verified at `6b87c9d`.

**C-1 — the guard is NOT dead on the backcast lane; it was already wired.** The brief
states `check_clean_partitions` "HAS NEVER RUN IN A SOLVE: its only call site is
`pipeline/year.py::run_year_solve`". At `6b87c9d` that is **false for the backcast lane**:
`scripts/run_calibration.py:4600` calls it, under a comment naming caiso-188 as the wiring
session. `FINDING-caiso188` §6 says so itself ("`scripts/run_calibration.py` now calls
`check_clean_partitions(config, iso)` on the solve path"). The brief's bullet describes the
**pre-caiso-188** state; its *next* bullet correctly scopes what remains owed. **The
forecast half of the claim holds and is fixed here.** No behaviour was changed on the
backcast lane as a result — `strict=True` preserves it exactly.

**C-2 — the CAMPD unit-outage extract is COMMITTED, not a gitignored partition.**
`data/raw/campd-unit-outages{,-<ISO>}.csv` are tracked (`git ls-files` confirms, ERCOT's
bare file included), so absence there is an environment condition — a sparse checkout —
not the caiso-157 "no solve auto-builds it" class. It is registered as requested, with a
**declared fallback**, and its identity is recorded; the brief's framing of it as a
disposable partition does not match the tree.

**C-3 — `outage_detect.py` is at `scripts/lib/`, not `src/market_sim/data/`.** The brief
locates the CAMPD overlay loader in "`outages.py` / `outage_detect.py`"; only the former
is under `src/market_sim/data/`, and it is the loader. `scripts/lib/outage_detect.py` is
the derive-side detector.

**C-4 — the caiso-189 sentinel was already on `origin/main`.** `scripts/gen_caiso189_
attestation.py` exists at `6b87c9d`, so no polling was needed and the log/matrix edits are
authorized. **No LOGDRAFT block is included** — the real entries are in this PR
(`docs/calibration-log/caiso.md`, `docs/mechanism-testing-matrix.md` §5.2).

**C-5 — a sibling session already references this work.** The caiso-191 entry at the log's
tail records "caiso-190's `resolved_inputs` is not on origin/main" as a live contradiction,
and its Wave-2 control recipe fixes "capacity-deliverability partition materialized
(log-verified, caiso-188 §7 item 5) and `hydro_ror_split` explicitly False". This PR
supplies exactly that interface. **caiso-191 is numerically later but merged first**, so
the log entry here is appended at the tail *after* it (per the brief's shared-file rule)
while the matrix §5.2 note is placed in that section's own newest-first session order.

**C-6 — the partitions-present test passed for the wrong reason.** §4. Not previously
recorded anywhere.

## §7 — DO-NOT-REDO (new, binding)

1. **Do not "fix" `pipeline/year.py::run_year_solve` by deleting it.** It has no
   production caller and that is known; `tests/regression/test_pipeline_facade_shims.py`
   asserts the `pipeline.run_year_solve` re-export, and it is the orchestrator-unification
   landing site. Its status is documented in §1. Deleting it is a refactor decision for
   that lane, not a provenance fix.
2. **Do not re-derive the seam cap at record time.** `resolved_inputs` records what
   `apply_interchange_topology` resolved, deliberately. A convenience re-derivation in the
   record writer would reintroduce exactly the drift this closes, and
   `TestSpecResolvesThroughHelper` + `TestEverySolvePathIsGuarded` will fail if it is
   attempted.
3. **Do not relax `strict=True` on the calibration lane to make a run go through.** The
   fix for a strict failure is to build the partition the message names, never to pass
   `strict=False`. A keeper that solved on a declared fallback is the caiso-188 defect
   with extra steps.
4. **Do not read `resolved_inputs` as evidence a mechanism *worked*** — only that it
   *resolved*. `source: "mic_partition"` says the published cap reached the topology
   step; whether the resulting constraint binds is a separate measurement (caiso-133 §3/§4
   against the correct cap, per caiso-188 §7 item 4).
5. **`resolved_inputs` does not retro-fill.** Bundles registered before this PR have no
   block, and `status: "unrecorded"` on a copied `--reuse-solved` year is not a defect.
   Which cap those bundles solved against is still inferable only the way caiso-188 did it
   — from `hourly/class_hourly_<year>.parquet` pins.

---

SESSION-REPORT caiso-190 solvepath-integrity
STATUS: COMPLETE — orchestration/provenance only; no LP change, no solve, no calibration edit; keeper untouched
GUARD WIRED: backcast? **already wired at caiso-188 (contradiction C-1)** — now `strict=True` explicitly, behaviour unchanged · forecast? **YES, new** (`runner.py::run_scenario_iso`, `strict=False`, on the resolved config before any LP input) · strict mode? **YES, and it is the DEFAULT** (callers opt out); declared fallback ⇒ fatal in strict, loud WARN + recorded otherwise; no-fallback mechanism (`hydro_ror_split`) ⇒ fatal on every lane; registry additive and now covers capacity-deliverability + hydro-plant-modes + the CAMPD unit-outage extract
PROVENANCE: `run_config.resolved_inputs` = `{schema_version, iso, seam_import_cap{status, by_year.<year>{cap_mw, source∈{mic_partition, baked_fallback, flag_off}, delivery_year, season, import_zone, flag_armed}}, hydro_plant_modes{flag_armed, partition_present, classified_plants, shapeable_plants}, campd_unit_outages{armed, path, present, sha256, bytes}}` — top-level, additive; recorded at resolution time by `apply_interchange_topology`, never re-derived; `docs/backcast-artifact-contract.md` §2.2.1. Cache-key/registry-parity unaffected (zero `scenarios.py` diff; `check_mechanism_matrix.py` clean; reuse comparator reads only `scenario_config`)
TESTS: **23 added, all passing** (17 `test_resolved_inputs.py` incl. two static wiring guards, 6 `test_input_completeness.py`). Fast lane in-container both arms: baseline 669F/5,863P/53E → with changes 669F/**5,886P**/53E = **+23 passed, +0 failed, +0 errors**. The 669/53 are pre-existing sparse-checkout `FileNotFoundError`s (cone mode omits every `data/raw/` subdirectory); the brief's 6,620/2 is not reproducible under the campaign's own checkout recipe — see §5. ruff check + format clean
FILES PUSHED + PR: see §8
CONTRADICTIONS: **six** — C-0 base commit `767b29c3`→`6b87c9d`; **C-1 the backcast guard was already wired (caiso-188), so the brief's "never run in a solve" is the pre-caiso-188 state**; C-2 the CAMPD extract is committed, not a gitignored partition; C-3 `outage_detect.py` is `scripts/lib/`; C-4 the caiso-189 sentinel was already on main; C-5 caiso-191 merged first and already cites this work; **C-6 NEW — the partitions-present test passed only because both probes raised `SchemaError` and the guard swallowed them, so a malformed partition was silently treated as healthy on the solve path** (§4)
LOGDRAFT: **not included, and not owed** — the caiso-189 sentinel is on `origin/main`, so the real `docs/calibration-log/caiso.md` entry and the matrix §5.2 note are in this PR
OPEN ITEMS / HANDOFF: (1) **`hydro_ror_split` is still unproven as a mechanism** — this session makes its engagement *observable* (`classified_plants` in the bundle) but arms nothing; the A/B is caiso-194's, gated by `GATESPEC-caiso194-hydro-ror-split-2026-08-11.md`, and its four-leg engagement proof can now read the committed block instead of re-deriving. (2) **No CAISO bundle carries `resolved_inputs` yet** — the block appears on the next solve; the caiso-175→188 lineage stays diagnosable only via `hourly/` pins. (3) The **forecast** run-record writer (`scripts/lib/run_record.py::write_run_config`) does **not** carry the block — only the backcast writer does; filed, not absorbed. (4) `pipeline/year.py::run_year_solve` remains dead code with a live guard call (§1, DO-NOT-REDO 1). (5) The campaign's sparse-checkout recipe cannot run the documented fast lane — either the recipe or the 6,620/2 baseline needs updating for future sessions.
