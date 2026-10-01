# scripts/ — layout

| Location | What lives there |
|---|---|
| `scripts/` (top) | Standing entry points: calibration/backcast (`run_calibration_full.py`, `replay_keeper.py`), hindcast, the forecast program (`run_full_horizon.py`, `forecast_verdict.py`, PB-5 assembly), scoring (`calibration_verdict.py`, `score_*.py`, `legitimacy_diagnostics.py`), dashboard/site (`dashboard_add_run.py`, `promote_keeper.py`, `render_*.py`), governance and CI checks (`audit_keepers.py`, `build_dof_ledger.py`, `check_*.py`), shard tooling (`shard_prompt.py`), and the current keepers' attestation generators. |
| `scripts/data/` | Source → model inputs: `fetch_*`, `curate_*`, `derive_*` (rule 23, frozen against residuals), `build_*`. |
| `scripts/lib/` | Shared helpers (`cli.py`, `bundle_io.py`, `keeper_store.py`, per-datatype registries). |
| `scripts/probes/` | Probes live code names, and active-lane probes (first added ≤ 14 days ago). |
| `scripts/diagnostics/` | Standing measurement harnesses (HiGHS thread bench, LP memory profile, warm-start bundle diff). |

## Classification rule

- A script **stays** if it is part of a standing workflow: invoked by CI, a skill,
  tests, `src/`, another standing script, the RUNBOOK / testing / codebase docs,
  or its docstring names it a standing entry point of a program.
- A script tied to **one run** is **deleted** once that run is superseded or
  rejected — its `gen_<run>_attestation.py`, drivers and helpers alike. Nothing
  is archived; `git log` is the record. The committed `calibration_attestation.json`
  inside each keeper bundle is the attestation record.
- Data fetching or transformation belongs in `scripts/data/`.

**Sweep tool:** `python3 scripts/lib/probe_census.py` classifies every probe as
`KEEP-ref` / `KEEP-recent` / `DELETE` (`--list DELETE` for paths). Deepen a
shallow clone past the 14-day window first, or every file reads as recent.

## Kept attestation generators (2026-10-01)

Current keepers' generators plus their import closure:

- NEISO `gen_neiso119` · CAISO `gen_rcaiso20` (span + touchpoints) · SPP `gen_spp100` · PJM `gen_pjmnext16`
- NWPP `gen_nwppnext14`, imported chain `gen_nwppnext13 → 12 → 10 → 8 → 7 → 6 → 5 → 4 → 3 → 2 → gen_nwppnext`, base `gen_rnwpp`
- SOCO (soco96 chain): `gen_soco60b → gen_soco_h4 → gen_soco58`, `gen_rsoco`, `gen_rsocob`
- Standing: `gen_touchpoint` (rule-30 touchpoint attestation)

MISO, NYISO and ERCOT keepers have no top-level generator.

## Conventions

- **Bootstrap.** `scripts.*` imports need the repo root on `sys.path`:
  `import sys; from market_sim.config.paths import REPO_ROOT; sys.path.insert(0, str(REPO_ROOT))`.
  The stdlib-only deploy trio (`build_manifest.py`, `build_codebase_site_backcast.py`,
  `register_hindcast.py`) keeps its own stdlib bootstrap.
- **Sibling imports** are spelled `from scripts import …` / `from scripts.data import …`;
  never `importlib.util.spec_from_file_location`, never bare `import run_calibration`.
- **`keeper_store.py`'s CLI** is the one argparse main under `lib/`
  (`--list` / `--set <ISO> <RUN_ID>`), quoted by `frontend/data/backcast/keepers/README.md`.
- **Three stores in lockstep** (registry sidecar, run payload, bundle):
  `check_registry_payload_parity.py` is the CI gate; run it before every dashboard push.
- **Key provenance:** `check_key_provenance.py` gates non-reproducing `cache_key`s
  against `docs/governance/key-provenance-exceptions.json`. A new mismatch is a FINDING, not a list entry.
