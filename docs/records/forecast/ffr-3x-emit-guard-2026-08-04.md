# FFR-3X — emit-helper refuse-if-exists guard; FFR-3R §6.1 closed, 2026-08-04

**One-line result:** `scripts/_ff2d_emit_run_config.py` now REFUSES to overwrite an
existing `run_config.json` (loud `SystemExit` naming the bundle; no override flag),
and its hindcast arm sources the bundle's own `run_config.yaml` — the harness's full
ScenarioConfig dump — instead of `meta.json`, closing FFR-3R §6.1. Solve-inert:
`cache_key(ScenarioConfig())` = `603c2498bf71d21d` before and after; `git diff
origin/main -- src/` empty. Branch: `claude/ffr-3x-emit-guard-oopa3b`, base
`origin/main` @ `6d24a84d`.

## 1. The guard (FFR-3K §6's follow-up)

Post-FFR-3K bundles carry a producer-written `run_config.json`
(`scripts/lib/run_record.py::write_run_config`, the solved-config RESOLUTION). Run on
such a bundle, the old helper silently overwrote it with a reconstruction — a
provenance downgrade, the FFR-3R defect class. Measured before fixing (pre-fix helper,
subprocess, fixture bundle with a producer artifact): **exit 0, file overwritten,
output meta-shaped** — invisible on both channels.

Now: the helper checks its write target FIRST, before reading any source, in both arms
(`summary` and `hindcast`), and refuses with a message naming the bundle and the reason.
It never skips quietly — a silent skip and a silent overwrite are both invisible, and
only one of them is safe, so the safe one is made loud.

**No override flag, deliberately.** The only overwrite uses nameable are (a) bulk
re-emission over historical helper-written artifacts — the "normalize" pattern this
lane's charter forbids — and (b) re-emitting over an already-scored artifact, which is
verdict-affecting and needs its own lane (FFR-3R §6.1's own re-scoring caveat). Neither
deserves an in-band switch. If a future lane authorizes re-emission, deleting the file
first is the explicit, visible act it should take; the refusal message says exactly
that, and the test suite pins that no flag is advertised.

## 2. FFR-3R §6.1 closed: the hindcast arm's source

Old: `run_config.json = {**meta, "mode": "forecast", "hindcast": True}` — a ~30-key
harness meta scored as THE ScenarioConfig (`forecast_verdict._scenario_config` sees
top-level `iso`), the FFR-2E propagation channel, with the omission edge that FC-2
row 4 (`"reserve_margin_build_enabled" in sc`) and FC-7 row 1 (`len(sc) >= 20`) read
absence as fact.

New: the arm reads the bundle's `run_config.yaml`
(`run_capacity_hindcast.py:1431`, `config.to_yaml_full`) VERBATIM — ~679 fields,
carrying `mode="forecast"` and `hindcast=True` natively from `build_config`
(L553–554), so the helper no longer hand-adds literals (a mirrored literal is
itself the FFR-3R defect). A bundle with NO `run_config.yaml` is refused loudly:
meta reconstruction is not a fallback (rubric §4 — unknown, not assumed). Output
stays flat, matching the summary arm and `_scenario_config`'s no-wrapper branch.

Provenance asymmetry, stated honestly (FFR-3K §1): `run_config.yaml` is the pre-solve
REQUEST dump, while a producer `run_config.json` is the RESOLUTION — which is precisely
why the guard protects the producer artifact: the helper's best output is still the
weaker artifact. The summary arm's source (the cache `run_dir/config.yaml`, the
resolution) is unchanged.

## 3. Test

`tests/scoring/test_ff2d_emit_run_config.py` — 7 tests, no solve. Guard: both arms
refuse an existing artifact with the bytes byte-untouched (sha256 compared), the
refusal names the bundle, and no override flag is advertised. Source: the emitted
config carries a sentinel planted only in `run_config.yaml`, the real
`reserve_margin_build_enabled` field, no meta-only keys (`bundle`/`cache_key`/
`solved_years`), ≥ the FC-7 full-surface floor, and PASSes FC-7 row 1 through the
scorer's own loader (`FV._load_config` → `score_fc7`, tier `t1h`); a dump-less bundle
is refused with nothing written. **Negative control:** with the fix stashed, the suite
fails wholesale (the pre-fix module is top-level argv code — collection aborts), and
the subprocess measurement in §1 shows the silent overwrite the guard prevents.

Adjacent suites green at this head: `test_hindcast_run_config_artifact` +
`test_forecast_verdict` (86 passed total with the new suite). `ruff check` and
`ruff format --check` clean on both changed files.

## 4. Solve-inertness and rule 28

`cache_key(ScenarioConfig())` = `603c2498bf71d21d` before and after (matches the
FFR-3R/FFR-3K printed value, cross-validating the probe); `git diff origin/main --
src/` is empty — not one model line changed. **Rule 28: no matrix cell is due, stated
explicitly** — this session adds no mechanism, no `ScenarioConfig` field, no
calibration CLI flag; it is a scorer-side instrument guard, solve-inert by the above.

## 5. Not done, deliberately

No committed bundle retro-edited; no historical bundle re-emitted or "normalized"
(that is the overwrite at scale); `run_record.py` untouched (built beside it, not
rewritten); the pack/sitting-ledger status lines are left to the workstream manager
per the FFR-3R/FFR-3K convention.
