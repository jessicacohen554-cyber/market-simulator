# scripts/ — layout

Reorganized 2026-07-18 so the operational surface is separable from data
tooling and retired one-offs. References in code, tests, CI, and docs were
updated mechanically in the same change; paths quoted in frozen run records
(`results/calibration/`, `frontend/data/backcast/`) and in session logs that
predate the reorg refer to the old flat layout — the file content is unchanged,
only the directory moved.

| Location            | What lives there |
|---------------------|------------------|
| `scripts/` (top)    | Core entry points and standing tooling: calibration/backcast (`run_calibration_full.py`, `run_calibration.py`, `replay_keeper.py`), hindcast (`run_capacity_hindcast.py`, `register_hindcast.py`), the forecast program (`run_full_horizon.py`, `forecast_verdict.py`, `export_forecast_bands.py`, PB-5 assembly), scoring/verdicts (`calibration_verdict.py`, `score_*.py`, `legitimacy_diagnostics.py`, `screen_collateral_gate.py` — rule-29 screen G-4 on an UNREGISTERED bundle), dashboard/site (`dashboard_add_run.py`, `build_manifest.py`, `build_status.py`, `render_*.py`, `check_site_sri.py`), governance (`build_dof_ledger.py`, `regression_gate.py`, `capture_*_goldens.py`, `verify_holdout_intake.py`, `generate_parameter_registry.py`, `check_mechanism_matrix.py`, `mechanism_matrix_gap_sweep.py`, `check_key_provenance.py`), and per-ISO gate reporters. |
| `scripts/data/`     | Data fetching and processing — everything between an external source and the model's inputs: `fetch_*` (raw downloads), `curate_*`/`process_*`/`convert_*`/`parse_*` (raw → `data/clean` per the schema contract), `derive_*` (measured-behaviour parameter derivation; CLAUDE.md rule 23 — frozen against residuals), and per-source builders (`build_*_hsl.py`, LMP references, AS withholding, …). Not core engine. |
| `scripts/lib/`      | Shared helpers imported by scripts (`clean_io.py`, `bundle_io.py`, per-datatype registries). One deliberate exception carries an argparse main — see "`keeper_store.py`'s CLI" below. |
| `scripts/probes/`   | Only the probe scripts that live code still imports or names (`derive_*` data scripts, `scripts/lib`, tests, standing docstrings). The record-only probes (1,229 files) and the whole `scripts/archive/` tree were DELETED 2026-09-05 on owner instruction — superseded per-run scripts are deleted, never archived; `git log` is the record. |
| `scripts/diagnostics/` | Standing measurement harnesses that profile or diff the engine rather than run the programs: `bench_highs_parallel.py` (HiGHS thread-scaling bench), `profile_lp_memory.py` (LP build-vs-solve peak-RSS split), `diff_warmstart_bundles.py` (per-plant cold-vs-warm bundle diff; invoked by `regression_gate.py`), `repro_eia860_vintage_leak.py` (the 2026-07-27 bisect record + standing regression detector for the EIA-860 vintage process-global leak that was the fast-tier order-dependent pollution family) — plus scratch diagnostics. |

Classification rule used (and to use going forward): a script stays at top
level if it is part of a *standing* workflow — invoked by CI, a skill, tests,
the calibration/forecast/hindcast programs, or governance rules. A script tied
to one specific superseded run is deleted once that run is superseded; anything that fetches or
transforms data belongs in `data/`.

**Keeper rotation (DELETE, since 2026-09-05):** a superseded keeper's per-run
scripts — its `gen_<run>_attestation.py`, its `run_<run>_*` driver, and any
`<run>_*validate` helper — are DELETED when the ISO's next keeper registers
(owner instruction 2026-09-05: "delete what's not needed anymore, don't
archive"). The current keeper's and any in-flight run's scripts stay at top
level; a rejected probe's scripts are deleted as soon as the rejection is
adjudicated. Before 2026-09-05 the rule rotated them into `scripts/archive/`;
that directory no longer exists and the paragraphs below describing rotations
into it are history.

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

**Keeper-only deletion, 2026-09-05.** Owner instruction: on the backcast side
only KEEPER run data is retained, and nothing is archived. 54 top-level
`gen_*_attestation.py` generators were deleted (every generator whose run is
not a current keeper), together with the whole `scripts/archive/` tree (292
retired one-offs) and the 1,229 probe scripts nothing in live code imports or
names; `regen_caiso_bench_cems.py` moved to `scripts/data/` and
`bench_cold_solve.py` to `scripts/diagnostics/` because live scripts still call
them. The surviving generators are the current keepers': `gen_caiso251`,
`gen_miso217`, `gen_neiso99`, `gen_nyiso189` and `gen_pjm163_inputclock`
(writes the pjm-162 keeper's attestation); ERCOT's two-config keeper
(ercot-248) has none. The same prune deleted every unmapped solve-output
bundle under `results/calibration/` and emptied
`check_registry_payload_parity.KEEP_REQUIRED_UNMAPPED_BUNDLES`, so a
generator's G-CONTROL leg is no longer recomputable against a control bundle —
the committed `calibration_attestation.json` in each keeper bundle is the
record.

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
The **wider sibling web is fully retired as of 2026-08-16: the census reads
0 bare sites across 0 live files** (down from the 2026-07-27 census's
105/91; re-runnable any time with
`python scripts/ci_refactor_guards.py --sibling-census`, an advisory mode,
so the recorded number can be re-derived instead of trusted — and any NEW
bare site shows up there). The 2026-08-14 reading was 74/50; the single
site that left before the batch conversions was
`gen_caiso166_attestation.py`, which rotated to `archive/` in the
2026-08-15 keeper rotation above. **Six chartered batches converted
2026-08-16** (DEBUG-manager reissue sessions; 73/49 → 56/34 → 0/0):
batch 1 the seven-file CAISO derive cluster
(`derive_caiso_import_tranches` / `derive_ordc_overlay` consumers),
batch 2 the top-level cluster (`dashboard_add_run.py`,
`generate_parameter_registry.py`, the two
`*_zonal_sufficiency.py`, `validate_ercot_online_capacity.py`,
`diagnostics/scratchpad_diag_evening.py`, `score_crossover.py`),
batch 3 the 19-file ERCOT `scripts/data/` derive/build/fetch web
(the `derive_ercot_dam_cleared_share` / `derive_ercot_sced_offer_wall` /
`build_ercot_as_withholding` / `build_ercot_hsl` dependency web plus
`derive_sced_coal_uppertail`'s frozen-probe imports), batch 4 the
`fetch_eia930_*` chain, the CAISO OASIS pair (`extract_caiso_hubs`,
`fold_caiso_oasis_grp_zips`) and the misc derive singles, batch 5
`lib/sced_corpus_instruments.py`'s six deferred probe/data imports
(now `scripts.probes.*` / `scripts.data.*`; its probes-dir shim went with
them), batch 6 the deploy trio (`register_forecast_run.py` /
`register_hindcast.py` / `pb5_assemble.py` — `register_hindcast` gained a
**stdlib-only** repo-root bootstrap because it runs on bare `python3` in
the Pages sparse checkout; verified by a deploy emulation on stock
`python3` with no third-party deps). Each file went through the full
per-file protocol: both-paths attribute verification FIRST (structural
code equality, NOT marshal bytes: marshal's back-ref sharing varies with
string interning across two loads of one file and false-flags equal code;
set/frozenset comparisons must be order-independent — repr order is
hash-seed dependent across processes), bare shims → repo-root bootstrap,
then a STRICT direct-run check (script's own dir as `sys.path[0]`, repo
root scrubbed from the ambient path, arbitrary cwd — a check run from the
repo root is vacuous), `--script-refs` green per batch. Three test rigs
were repaired off their own second-copy patterns along the way
(`test_dashboard_add_run_sidecar.py`, `test_dam_deriver.py` +
`test_ercot_clock_builders.py`, `test_export_forecast_bands.py`).
Recorded side effects, all the `pjm123_composite_precheck` shape (frozen
record, left as-is): the frozen probes `ercot90_stgas_shoulder_measure`
(bare-imports two `scripts/data` derive modules) and
`ercot136_coal_headroom_conduct` / `ercot138_coal_gas_ranking`
(bare-import `ercot123_coal_sced_reach`) self-shim their own directories,
so a process that loads them alongside the canonical spellings holds
those modules under both names — identical code, verified structurally.
Any future sibling import is spelled canonically from the start, with the
same protocol if it must coexist with a bare-era frozen record.

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

## Key provenance (`check_key_provenance.py` + the exception record)

A committed bundle's `cache_key` is **what that bundle actually solved under**.
When today's `ScenarioConfig.cache_key()` cannot recompute it, something moved
underneath the record — a field registered late, a default flipped before the
flips ledger existed, a relocated `MARKET_SIM_DATA_ROOT`, a writer that
serialized the request instead of the resolution. The honest repair is to
**derive** the literal, never to rewrite the artifact so it agrees with today
(capx D85 §5 refuses both a key rewrite and a de-registration for exactly that
reason).

`scripts/check_key_provenance.py` hashes every committed `run_config.json` and
gates the non-reproducing ones against the committed record
**`docs/governance/key-provenance-exceptions.json`**, which carries each one's
class, its executable recipe, its derivation and its citation. It prints
`N KNOWN, M UNKNOWN` and exits non-zero on any of five gates — an **unlisted**
mismatch (G1), a listed record that has started **reproducing** (G2 — a stale
exception is dead scaffolding, rule 26 `[R-DELETE]`), a recipe that does not
reproduce its literal (G3), a listed record whose bundle was pruned (G4), and a
mis-keyed entry (G5). `tests/regression/test_key_provenance_exceptions.py` is
the offline half and rides the blocking fast tier; the library both share is
`scripts/lib/key_provenance.py`.

**Two keys, always.** `cache_key` appends a `__solve_surface__` block for any ISO
whose `config/solve_surface.py` rows have moved off their frozen declaration, so
every row is hashed both ways and the summary names which construction matched.
A record that reproduces only **at declaration** is capx D79's *designed* re-key
("a re-derived registry table re-keys the ISOs whose rows moved") — reported,
never repaired here: re-declaring a moved row belongs to the ISO lane that
re-solves its frontier on the new table.

**A new mismatch is a FINDING, not a list entry.** Do not append to the
exception record to turn the gate green; stop and report it.
