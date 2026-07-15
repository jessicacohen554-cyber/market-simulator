# PJM M-1 input-clock repair — apply + completion handoff (2026-07-15)

This branch was produced in a memory- and API-constrained sandbox that
**cannot push large or binary files** (the direct GitHub Data API is
policy-blocked for writes, and `mcp__github__push_files` carries only small
text emitted inline). So the M-1 change ships here as an applyable patch plus
this handoff. The change itself is complete and verified — see below.

## What M-1 is

Value-preserving per-family clock repair of the committed PJM EIA-930 wide
extract + the three PJM DataMiner loaders. See
`docs/DIAGNOSIS-pjm-2025-phase-drift-and-zonal-structure-2026-07.md` §6 and
`data/raw/eia-930-hourly/README.md` (already on this branch).

- **2023 region family −1 h** (extract hour-beginning/hour-ending mix-up).
- **2024 fueltype family +1 h** (EIA-930 source ran 1 h early through 2024).
- `pjm_net_interchange` / `pjm_zonal_interchange` / `parse_pjm_shares` switched
  `datetime_beginning_ept` → `datetime_beginning_utc` on the model's fixed-EST
  clock.

## Apply on the origin machine

```bash
# 1. Apply the code diff (all 4 files: eia_loader.py, curate_zonal_shares.py,
#    extend_eia930_hourly_from_balance.py, run_calibration_full.py)
git apply patches/pjm-m1-code.patch

# 2. Regenerate the corrected wide parquet FROM the committed pre-fix parquet.
#    Run EXACTLY ONCE (it shifts committed values; a second run double-shifts).
python scripts/extend_eia930_hourly_from_balance.py --rebuild-pjm-input-clock

# 3. Verify the source-anchored gates (all PASS in the sandbox):
#    demand daily-peak mode-0 vs hrl_load_metered  2023 96.4% / 2024 96.7% / 2025 97.0%
#    July solar centroid in [11.5,12.3]            2023 11.90 / 2024 11.93 / 2025 12.03
#    wind & gas diff-lag 0 vs the PJM UTC feed     all years
python scripts/probes/_pjm2025_phase_drift.py     # checks B (centroid) + C (demand vs meter)
python scripts/probes/_pjm2025_wind_anchor.py     # wind/gas diff-lag + solar centroid
```

## Re-solve + register the pjm-112 bundle (origin has RAM)

The sandbox solved the pjm-110 recipe at the corrected inputs and scored it —
**verdict IDENTICAL to pjm-110: NOT-YET on C3c, every other criterion PASS,
zero flips** (`results/calibration/pjm112_input_clock/metrics.json`, on this
branch). The bundle's 80 MB/year dispatch parquets are gitignored and local to
the sandbox, so the dashboard payload could not be pushed. To register on the
live dashboard, re-solve on the origin machine (identical recipe + corrected
inputs → byte-identical dispatch) and register:

```bash
# fetch the DataMiner virtual-bid corpus the recipe's pjm_da_virtual_bids leg needs
python scripts/fetch_pjm_da_virtuals.py --years 2023 2024 2025 --feeds hrl_da_incs_decs
# re-solve all three years, one bundle (origin machine — no per-year OOM workaround needed)
python scripts/run_calibration_full.py --replay-bundle results/calibration/pjm110_bench_hygiene \
    --out-dir results/calibration/pjm112_input_clock --year 2023 2024 2025 \
    --note "pjm 112 input-clock M-1"
python scripts/legitimacy_diagnostics.py --bundle results/calibration/pjm112_input_clock \
    --iso PJM --json-out results/calibration/pjm112_input_clock/legitimacy_diagnostics.json
python scripts/dashboard_add_run.py --label "pjm 112 input-clock" \
    --bundle results/calibration/pjm112_input_clock
# retention: prune the oldest PJM run (2026-07-12-pjm-99-offer-surface) sidecar + payload
python scripts/build_manifest.py
# push the bundle + sidecar + runs/<id>.js + bench via the origin ci_api_upload path
```

Keeper CANDIDATE only — do NOT touch `keepers.json` (owner promotes).

## Calibration-log

The 894 KB `docs/calibration-log.md` could not be pushed from the sandbox.
Fold `docs/_pjm112_input_clock_log_entry.md` (this branch) as the newest entry
under `## Runs`, above the already-present `docs/_pjm_phase_drift_log_entry.md`
(the Fable diagnostic stub), then delete both stubs.

## Notes for the memory workaround (informational)

The sandbox (15 GB) OOMs on a single-process 3-year PJM co-opt solve
(accumulated prior-year state peaks ~16 GB). The `run_replay_bundle`
`--reuse-solved` forward (in the patch) let it solve one fresh year per process
and chain the identical recipe — a resume, byte-identical to a fresh solve. The
origin machine with more RAM does not need this; a plain 3-year invocation
works.
