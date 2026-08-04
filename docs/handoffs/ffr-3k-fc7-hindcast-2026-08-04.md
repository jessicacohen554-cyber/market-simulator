# FFR-3K — FC-7 fixed for the T1-H / T1-X tiers (hindcast `run_config.json`), 2026-08-04

**One-line result:** `run_capacity_hindcast.py` now emits the `run_config.json`
FC-7 row 1 reads, through the SAME writer `run_full_horizon.py` uses — moved to
`scripts/lib/run_record.py`, one implementation, zero solve impact (all seven
reference cache keys byte-identical before/after; `git diff origin/main -- src/`
empty; no keeper moved).

Landed as an **instrument change BEFORE the next battery** (the FFR-3D
sequencing that made its T1-F fix admissible). Base: `origin/main 292f577e`.
Branch: `claude/fc7-hindcast-config-m18g1f`.

---

## 1. The defect and the fix

`run_capacity_hindcast.py` (this HEAD: L1419) wrote only
`config.to_yaml_full(out_dir / "run_config.yaml")`. `forecast_verdict.score_fc7`
row 1 requires `run_config.json`; absent, the row FAILs *"run_config.json
absent"*. So **every T1-H, T1-X and T1-FF leg FAILed FC-7 by construction** —
the unfixed analogue of the defect FFR-3D fixed at `34c2f25` in
`run_full_horizon.py` only (call-site binding fixed at `ea7cd5d`; both
inherited here, not re-implemented).

The fix, per the prompt's "reuse its writer" directive:

| File | Change |
|---|---|
| `scripts/lib/run_record.py` (373 → 458 lines) | `write_run_config` moved here VERBATIM from `run_full_horizon.py` (docstring notes the move; `market_sim.pipeline.persist.git_state`/`environment_block` lazy-imported per the module's `config_field_names` precedent). The FFR-3R record module is the natural home: `run_config.json` is a run record whose `scenario_config` block is solved-sourced by construction (read verbatim from the bundle's own `config.yaml` — the RESOLUTION `results.cache.save_result` wrote — never a re-dump of the pre-solve request). |
| `scripts/run_full_horizon.py` (903 → 833 lines) | Local def deleted; imports the shared writer. Call site unchanged. The now-unused `pipeline.persist` import dropped. |
| `scripts/run_capacity_hindcast.py` (1427 → 1448 lines) | After the meta write, calls `write_run_config(args.out_dir, bundle, iso=…, cache_key=…, solved_years=…, bridged_years=…, kind=…)` — `bundle` passed ONLY positionally (the `ea7cd5d` binding contract). Artifact lands at the bundle root beside `meta.json`, exactly where the scorer's documented invocation reads it (`--run-config results/hindcast/<run_id>/run_config.json`). One write site serves all three kinds (`hindcast` / `crossover` / `full_forward`), so T1-H, T1-X and T1-FF are all covered. |

**`run_config.yaml` is KEPT** (checked before deciding): it is the request-side
dump `build_forecast_dof_ledger._load_run_config` still falls back to, and the
FFR-3A-3 §6.3 scorer observation is written against it. Note the provenance
asymmetry now on record: the `.json` is the RESOLUTION (bundle `config.yaml`
verbatim), the `.yaml` remains a pre-solve REQUEST dump. Readers should prefer
the `.json`; the DOF-ledger builder already does.

Distinct same-named function, untouched: `pipeline.persist.write_run_config`
(the BACKCAST bundle's `run_config.json`, used by `run_calibration_full.py`) is
a different artifact on a different lane and was not consolidated — collapsing
the two shapes is not this lane's business.

## 2. Solve-inertness proof (the FFR-3R form)

`cache_key(ScenarioConfig())` = `603c2498bf71d21d` before and after, as are all
six per-ISO 2023 backcast keys (`ERCOT df386bca96a1d288`, `PJM
9834b2018b598423`, `CAISO a9afddae291525c1`, `MISO 2a1252c3acae89e9`, `NYISO
fd15030b3ee60f11`, `NEISO 5b1633171fead559`) — all seven also byte-identical to
the values FFR-3R printed, which cross-validates the probe itself
(`ScenarioConfig(iso=…, mode="backcast", start_year=2023, end_year=2023)`).
`git diff origin/main -- src/` is **empty**: not one line of the model changed.
Artifact emission happens strictly AFTER the solve returns. No keeper moved.

## 3. ⚠ Every committed pre-fix T1-H / T1-X FC-7 verdict is an INSTRUMENT ARTIFACT

Stated plainly, per the lane charter: **every FC-7 verdict on every committed
T1-H and T1-X leg predating this fix — including all six legs of FFR-3A-2 and
FFR-3A-3 — is an artifact of the instrument, not a leg-quality signal.** FC-7
was FAIL on every leg by construction and differentiates nothing in those
scorecards. The same holds for any pre-fix T1-FF leg scored through
`forecast_verdict`. Those artifacts are **not retro-edited**: no
`run_config.json` was hand-authored into any already-scored bundle, and no
committed leg was re-scored to pick up the fix (rubric §4 — the artifact is
authored by the RUN, before any score exists). The next battery's legs produce
the artifact at run time and their FC-7 becomes meaningful.

## 4. Census: no third instance (scope item 4)

Every producer of a bundle `forecast_verdict` FC-7-scores, and where its
`run_config.json` comes from:

| Producer | FC-7-scored lane | `run_config.json` |
|---|---|---|
| `run_full_horizon.py` | T1-F | ✓ FFR-3D (now via the shared lib writer) |
| `run_ces_leg.py` | CES legs | ✓ inherits `solve_and_summarize` |
| `run_capacity_hindcast.py` | T1-H / T1-X / T1-FF | ✗ → ✓ **this fix** |
| `golden_forecast_bands.py` | T3 golden | ✓ own writer (`ercot_2026_2040.run_config.json`; fed by explicit `--run-config` path, so the name difference is inert) |

Not FC-7-scored, so no gap: `run_calibration_full.py` (backcast lane; its
`run_config.json` comes from `pipeline.persist`), `run_driver_battery.py` /
`run_equilibrium_battery.py` / `run_foresight_ab.py` /
`run_sensitivity_tornado.py` (diagnostic rigs whose outputs feed OTHER FC rows
or reports, never a scored leg bundle), `run_isos_concurrent.py` (orchestration),
`run_miso7*_probe.py` (backcast probes). **Verdict: two instances of this defect
class existed — FFR-3D fixed one, this fixes the other; the sweep found no
third.**

One watch item, no action taken: `run_equilibrium_battery.solve_overbuild`
writes a `full_horizon_summary.json`-shaped summary into its out-dir with no
`run_config.json`. Its bundle is an off-registry diagnostic probe and is never
a scored leg today; if T2 scoring ever points `--summary` at an overbuild
bundle, this becomes instance three. Left unfixed deliberately (small lane).

## 5. The regression test (scope item 2)

`tests/scoring/test_hindcast_run_config_artifact.py` (5 tests). Both historical
instances shipped green because no test exercised the RUNNER'S OWN TAIL (the
FFR-3D suite called the writer with a test-invented kwarg shape — `ea7cd5d`'s
crash is exactly what that missed). This suite drives `main()` end to end —
argparse → `build_config` → guards → meta → write site — with only the solve
seam stubbed, parametrized over all three modes (plain hindcast, `--crossover`,
`--forward-from-base`), and asserts:

* `run_config.json` exists at the bundle root, parses, and carries
  `solved_years` / `bridged_years` / `cache_key` / `kind` / `run_dir`;
* its `scenario_config` is sourced VERBATIM from the bundle's resolved
  `config.yaml` (a sentinel key planted only in the on-disk resolution must
  surface in the payload — a re-dump of the request cannot pass);
* `run_config.yaml` still exists (pins the keep decision — removal goes loud);
* for the two named tiers, `score_fc7` row 1 **PASSes when fed the artifact
  through the scorer's own loader** (`FV._load_config` → `score_fc7`, tier
  `t1h` and `t1x`).

**Negative control:** with the runner change stashed (pre-fix state), all 5
tests FAIL — 3 on artifact absence, 2 on FC-7 row 1 — confirming the suite
catches the original bug, not just decorating the fix.

Suites run green at this head: the new suite (5), FFR-3D's
`test_full_horizon_instruments` + FFR-3R's `test_run_record_provenance`
(33 passed, 62 subtests), and the hindcast-adjacent
`test_full_forward_hindcast` / `test_crossover_harness` /
`test_capacity_clearing_posture` / `test_forecast_posture` (77 passed), plus
`test_forecast_verdict` / `test_forecast_verdict_t2` / `test_score_crossover` /
`test_forecast_dof_ledger` / `test_schedulable_guard` /
`test_pipeline_facade_shims` / `test_recorded_cfg_fidelity`. Pre-existing at
clean `origin/main` and unrelated: 4 failures in
`tests/scoring/test_ff_readiness_battery.py` (reproduced identically with this
change stashed; environment/state-dependent, not touched by this lane).

## 6. Notes for successors

* **`scripts/_ff2d_emit_run_config.py` is now needed for HISTORICAL bundles
  only.** New hindcast/full-horizon bundles carry a producer-written
  `run_config.json`. The helper will silently OVERWRITE a producer artifact
  with a `meta.json`-reconstructed one (a provenance downgrade) if run on a
  post-fix bundle — do not run it there. Its hindcast arm also still reads
  `meta.json` rather than `run_config.yaml` (FFR-3R §6.1, still open). A
  refuse-if-exists guard would be a 3-line follow-up for whoever next touches
  that helper.
* **Rule 28:** no mechanism-matrix cell was touched — this session added no
  mechanism, no `ScenarioConfig` field, no calibration CLI flag; it is an
  instrument/record change only, solve-inert by §2.
* Pack/sitting-ledger status lines for FFR-3K (`ffr-owner-sitting-2026-08-02.md`
  §H.5 item 3 / L1429; `forecast-readiness-prompt-pack-2026-07.md`) still say
  "never dispatched" — left to the workstream manager per the FFR-3R
  convention (its handoff did not edit the pack either).
