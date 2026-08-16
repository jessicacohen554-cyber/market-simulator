# scripts/ — layout

Reorganized 2026-07-18 so the operational surface is separable from data
tooling and retired one-offs. References in code, tests, CI, and docs were
updated mechanically in the same change; paths quoted in frozen run records
(`results/calibration/`, `frontend/data/backcast/`) and in session logs that
predate the reorg refer to the old flat layout — the file content is unchanged,
only the directory moved.

| Location            | What lives there |
|---------------------|------------------|
| `scripts/` (top)    | Core entry points and standing tooling: calibration/backcast (`run_calibration_full.py`, `run_calibration.py`, `replay_keeper.py`), hindcast (`run_capacity_hindcast.py`, `register_hindcast.py`), the forecast program (`run_full_horizon.py`, `forecast_verdict.py`, `export_forecast_bands.py`, PB-5 assembly), scoring/verdicts (`calibration_verdict.py`, `score_*.py`, `legitimacy_diagnostics.py`), dashboard/site (`dashboard_add_run.py`, `build_manifest.py`, `build_status.py`, `render_*.py`, `check_site_sri.py`), governance (`build_dof_ledger.py`, `regression_gate.py`, `capture_*_goldens.py`, `verify_holdout_intake.py`, `generate_parameter_registry.py`, `check_mechanism_matrix.py`, `mechanism_matrix_gap_sweep.py`), and per-ISO gate reporters. |
| `scripts/data/`     | Data fetching and processing — everything between an external source and the model's inputs: `fetch_*` (raw downloads), `curate_*`/`process_*`/`convert_*`/`parse_*` (raw → `data/clean` per the schema contract), `derive_*` (measured-behaviour parameter derivation; CLAUDE.md rule 23 — frozen against residuals), and per-source builders (`build_*_hsl.py`, LMP references, AS withholding, …). Not core engine. |
| `scripts/archive/`  | Retired one-offs that are no longer part of the backcast, hindcast, or forecast paths: superseded per-run drivers (`run_pjm51`–`98`, `run_ercot_21`–`46`, `run_159`–`166`, …), per-run attestation generators, one-shot diagnostics/probes/analyses, completed intake/landing scripts, dead CI-upload tooling. Kept for the historical record; **not maintained**. See `scripts/archive/README.md`. |
| `scripts/lib/`      | Shared helpers imported by scripts (`clean_io.py`, `bundle_io.py`, per-datatype registries). One deliberate exception carries an argparse main — see "`keeper_store.py`'s CLI" below. |
| `scripts/probes/`   | Per-run probe scripts, named `_<iso><run>_*` — the historical record of calibration probes (frozen). |
| `scripts/probes/artifacts/` | The probes' non-Python repro artifacts (`.patch` / `.xz.b64` chunks, `_<iso><run>_chain.sh` drivers, chunked-patch land dirs), segregated 2026-07-26 so the probe scripts stand alone — same frozen record, content untouched; paths quoted in pre-move records refer to the old flat `probes/` layout. |
| `scripts/diagnostics/` | Standing measurement harnesses that profile or diff the engine rather than run the programs: `bench_highs_parallel.py` (HiGHS thread-scaling bench), `profile_lp_memory.py` (LP build-vs-solve peak-RSS split), `diff_warmstart_bundles.py` (per-plant cold-vs-warm bundle diff; invoked by `regression_gate.py`), `repro_eia860_vintage_leak.py` (the 2026-07-27 bisect record + standing regression detector for the EIA-860 vintage process-global leak that was the fast-tier order-dependent pollution family) — plus scratch diagnostics. |

Classification rule used (and to use going forward): a script stays at top
level if it is part of a *standing* workflow — invoked by CI, a skill, tests,
the calibration/forecast/hindcast programs, or governance rules. A script tied
to one specific superseded run belongs in `archive/`; anything that fetches or
transforms data belongs in `data/`.

**Keeper rotation:** a superseded keeper's per-run scripts — its
`gen_<run>_attestation.py`, its `run_<run>_*` driver, and any
`<run>_*validate` helper — move to `archive/` when the ISO's next keeper
registers (`git mv` + mechanical reference rewrite, the PR #2486 discipline;
repo-root path math re-anchored for the extra directory level). The current
keeper's and any in-flight run's scripts stay at top level; a rejected
probe's scripts rotate as soon as the rejection is adjudicated. (First
applied 2026-07-26: the miso-73 rejected-probe trio rotated; miso-72 — the
standing keeper — and the in-flight miso-74 stayed.)

**Backlog rotation, 2026-08-15 (BLOAT-B-4, `docs/bloat-removal-plan-2026-08.md`
§6 items D1/D2).** The rule had accumulated a backlog: 83 top-level
`gen_*_attestation.py` against 6 ISOs. 86 scripts rotated to `archive/` in one
pass — 79 attestation generators, `gen_nyiso130_keeper_ledger.py` (superseded
nyiso-128/130 lineage; NYISO's keeper is nyiso-132), the miso-72 lineage
(`gen_miso72_attestation.py`, `miso72_perzone_validate.py`,
`run_miso72_winter_probe.py`), the miso-74/75 probe drivers, `run_foresight_ab.py`
and `run_calibration_eia930.py`. The **keep-set was re-derived at execution time**
from `frontend/data/backcast/keepers/<ISO>.json` plus each generator's docstring
and is **4**, one per ISO that has a top-level generator for its *current* keeper:
`gen_ercot192_attestation.py`, `gen_miso148_attestation.py`,
`gen_caiso189_attestation.py` (writes the **caiso-188** keeper's C6 attestation)
and `gen_pjm153_collapse_attestation.py` (the **pjm-152** keeper arm's). NYISO's
keeper has no top-level generator, and NEISO's keeper (neiso-93, promoted
2026-08-14) is a `replay_keeper` re-solve whose attestation was written by
`build_dof_ledger.py` plus hand-authored sections — so `gen_neiso87_attestation.py`
rotated with the superseded neiso-87 lineage. `gen_ercot193_attestation.py`
rotated because the in-flight hold expired: the ercot-193 SOC re-gate was
**executed and discharged** (RG-PASS, keeper unchanged) and ERCOT has since run
to ercot-202. `run_ces_leg.py` was checked and **stays at top level** — it is the
standing FF-3F CES premium-ladder harness, imported by
`tests/unit/policy/test_run_ces_leg.py` and listed as a standing entry point in
`tests/regression/test_run_record_provenance.py`, with `run_full_horizon.py`
re-exporting `assert_schedulable` for it. `scripts/data/regen_caiso_bench_cems.py`
needed no action — it was already in `archive/`, which is why
`scripts/data/derive_caiso_supply_consistent_demand.py` already cites the
`archive/` path.

## Bootstrap & shared CLI helpers

`market_sim` is always importable (editable install), but the `scripts`
package is only importable with the repo root on `sys.path`. Every
`scripts.*`-importing tool uses the same **canonical three-line bootstrap** at
the top of the file, before any `from scripts.…` import:

```python
import sys
from market_sim.config.paths import REPO_ROOT
sys.path.insert(0, str(REPO_ROOT))
```

after which `from scripts.lib.cli import add_iso_arg` (etc.) resolves
regardless of the script's depth or the process's working directory. Do **not**
hand-roll `Path(__file__).resolve().parents[N]` repo-root math or insert
`REPO / "scripts"` — the bootstrap above is depth-independent. `scripts.lib.cli`
also exposes `repo_root()` (a re-export of `config.paths.REPO_ROOT`) and the
canonical argparse builders `add_iso_arg` / `add_years_arg` (its help text
documents the rule-22 holdout gate) / `add_out_dir_arg` / `add_bundle_arg`;
`--iso` is constrained to `iso_configs.SUPPORTED_ISOS`, so a new ISO propagates
everywhere without touching a hardcoded tuple.

Exception: the stdlib-only dashboard-deploy trio (`build_manifest.py`,
`build_codebase_site_backcast.py`, `register_hindcast.py`) runs on a bare
`python3` with no installed deps and keeps its own stdlib bootstrap — it must
not import `scripts.lib.cli` (which imports `market_sim`).

**Never reach a sibling script with `importlib.util.spec_from_file_location`.**
That form executes the target a *second* time under a synthetic module name, so
the caller gets a private copy whose module-level state can drift from the
canonical `scripts.*` entry every other importer shares. Import the package
instead — `from scripts.data import derive_ordc_overlay as ordc`. The
conversion is COMPLETE as of 2026-07-26: zero live call sites remain outside
the frozen `archive/`/`probes/` record (the former tail — `regression_gate.py`,
`export_tranche_config.py`, `bench_warmstart_xyear.py`,
`scripts/data/build_offer_curve_overrides.py`,
`scripts/data/derive_caiso_supply_consistent_demand.py` — was converted with
every consumed attribute verified identical across both import paths first).
Do not add new ones. The related bare-top-level-name smell (`import
run_calibration_full as rcf`, `from run_calibration import run_year`) creates
the same second-copy hazard whenever the canonical `scripts.*` name is also
loaded in-process; always spell sibling imports `from scripts import …` /
`from scripts.data.… import …` in new code. The **solve-entry cluster is
CLOSED as of 2026-07-27**: an AST re-census of the recorded "~10" found 13
live files bare-importing the `run_calibration` / `run_calibration_full` /
`replay_keeper` / `derive_pjm_ordc_overlay` family (the recorded nine plus
`knob_jacobian.py`, `negative_control.py`, `lib/bundle_fleet.py`, and
`run_calibration_full.py`'s own two deferred `import replay_keeper` sites —
the last three compelled into the same change: converting only their callers
would have *created* mixed bare+canonical copies in one process). All 13 were
converted after a both-paths harness verified every consumed attribute
byte-identical across the two import forms; the in-function
`sys.path.insert(0, REPO / "scripts")` shims that existed solely to feed the
bare form went with them. One recorded side effect: the frozen probe
`probes/pjm123_composite_precheck.py` bare-imports `run_calibration` itself
while also calling the now-canonical `lib/bundle_fleet.py`, so a re-run of
that probe would hold both names (identical code; frozen record, left as-is).
The **residue is the wider sibling web, re-measured 2026-08-16 at 56 bare
sites across 34 live files** (down from the 2026-07-27 census's 105/91 —
the intervening lanes' conversions are real; the census is now re-runnable
any time with `python scripts/ci_refactor_guards.py --sibling-census`, an
advisory mode, so the recorded number can be re-derived instead of trusted).
The 2026-08-14 reading was 74/50; the single site that left before the
batch conversions was `gen_caiso166_attestation.py`, which rotated to
`archive/` in the 2026-08-15 keeper rotation above. **Two chartered batches
converted 2026-08-16** (DEBUG-manager reissue; 73/49 → 56/34): batch 1 the
seven-file CAISO derive cluster (`derive_caiso_import_tranches` /
`derive_ordc_overlay` consumers), batch 2 the top-level cluster
(`dashboard_add_run.py`, `build_ffr3a3_scorecard.py`,
`generate_parameter_registry.py`, the two `*_zonal_sufficiency.py`,
`validate_ercot_online_capacity.py`, `diagnostics/scratchpad_diag_evening.py`,
`score_crossover.py`) — each under the full per-file protocol below, with
one test rig repaired off its own second-copy pattern
(`test_dashboard_add_run_sidecar.py` injected a `spec_from_file_location`
copy of `calibration_verdict` under the bare name; it now stubs the
canonical module). The remaining web is overwhelmingly `scripts/data/`
derive/build/fetch helpers importing each other by bare name
(same-directory sites resolvable only because `sys.path[0]` is the script's
own directory — the big ERCOT derive cluster), plus
`lib/sced_corpus_instruments.py` deferred-importing probe modules and the
deploy trio (`register_forecast_run.py` / `register_hindcast.py` /
`pb5_assemble.py`). Converting the rest is open work —
per-file, with the same both-paths verification (structural code equality,
NOT marshal bytes: marshal's back-ref sharing varies with string interning
across two loads of one file and false-flags equal code), PLUS a direct-run
check per converted file: the canonical `from scripts.… import` form needs
the repo root on `sys.path`, where the bare form needed only the script's
own directory, so any file meant to run as `python scripts/data/foo.py` must
carry (or gain) the repo-root bootstrap before conversion. Note the deploy
trio (`register_hindcast.py` et al.) runs on bare `python3` in a sparse
checkout, so any conversion there must keep its stdlib bootstrap
self-sufficient.

### `keeper_store.py`'s CLI — the sanctioned exception (adjudicated 2026-07-26)

`scripts/lib/keeper_store.py` is the only module under `lib/` with an argparse
main (`--list` / `--set <ISO> <RUN_ID>` / `--note`). The refactor plan's
"move the argparse mains out of `lib/`" does **not** apply to it, and the
recommendation is that it stays put:

* Keeper promotion is a governance-critical write, and
  `python scripts/lib/keeper_store.py --set <ISO> <run-id>` is the invocation
  quoted by the keeper governance doc (`frontend/data/backcast/keepers/README.md`).
* A separate `scripts/` entry point would create a **second** documented way to
  perform one governance operation, which is the failure mode rule 19
  `[R-ONE-MECH]` exists to prevent. The CLI here *is* the reference
  implementation of the shard write that ~10 importers share.
* The cost of keeping it is one stdlib `import argparse` in an otherwise
  stdlib-only module — nil. The module stays fully importable
  (`from scripts.lib import keeper_store`); the main is guarded by
  `if __name__ == "__main__"`.

If a future owner does want it moved, the move is a coordinated change: a thin
`scripts/set_keeper.py` that imports `keeper_store` and re-exposes the same
three flags, **plus** the same-PR update of `keepers/README.md` and any session
prompt quoting the old path. Do not move it without that.

Bare `from lib import …` is likewise retired: the canonical spelling is
`from scripts.lib import …` on top of the bootstrap above. As of 2026-07-26 no
live script uses the bare form; the only five remaining users
(`_ercot84_outage_override_audit.py`, `_neiso65_overcount_rootcause.py`,
`_pjm_aswh_merge.py`, `_pjm_coalbit_shape_cmp.py`, `_reldeploy_compare.py`) all
live under `scripts/probes/`, which is frozen calibration history and is left
exactly as-is.

## Dashboard retention (top-15 per ISO, all three stores)

The backcast dashboard keeps the **top 15 runs per ISO** (user-set 2026-06-21,
superseding the earlier 10-run rule). A registered run lives in **three stores**
that must stay in lockstep:

1. `frontend/data/backcast/registry/<id>.json` — the manifest sidecar.
2. `frontend/data/backcast/runs/<id>.js` — the run payload.
3. `results/calibration/<bundle>/` — the solved bundle (the sidecar's `bundle`
   field).

`scripts/dashboard_add_run.py` **governs all three**: after registering a run it
runs `prune_iso`, which keeps the 15 newest runs for that ISO (by date, then id)
and deletes the sidecar, payload **and** mapped bundle dir of every displaced
oldest run *together*. Two protections are never pruned regardless of age: any
current keeper in the sharded keeper store (`keepers/<ISO>.json`), and any run referenced by a surviving
sidecar's `ablation_twin`/`ablation_of` link. Pass `--no-prune` to register
without sweeping (used by the one-time backfill/cleanup operations); the caller
stages the deletions with the rest of the commit. (Keepers live in the sharded
per-ISO store `frontend/data/backcast/keepers/<ISO>.json` — 2026-07-19, via
`scripts/lib/keeper_store.py` — so keeper promotions in different ISOs commit
disjoint files; the monolithic `keepers.json`/`status.js` are retired.)

`scripts/check_registry_payload_parity.py` is the CI gate for this invariant and
checks **both directions**: a sidecar with no payload (invisible in the Run
Explorer) *and* an **orphan payload** with no sidecar (a dead `runs/<id>.js`
left behind if a sidecar were ever pruned without its payload). Run it before
every dashboard push. Bundles no longer referenced by any sidecar are swept in
the owner-signed one-time bundle sweep, not by `prune_iso` (which only touches
the bundle of a run it is actively pruning).
