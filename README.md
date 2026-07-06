# market-sim

LP-based electricity market dispatch and policy simulator. Forecasts hourly
(8760) generation, prices, emissions and capacity evolution across U.S. ISOs
from 2026→2050, with a historical-backcast mode for calibration against EIA-930,
CAMPD, eGRID and EIA-923 actuals.

- **Solver:** HiGHS via `highspy` (pure LP, no MIP). Prices are LP duals.
- **ISOs:** ERCOT (calibrated reference) plus CAISO, PJM, MISO, NYISO, NEISO.
- **Methodology:** see [`model-methodology-spec.md`](model-methodology-spec.md).
- **Working instructions / conventions:** see [`CLAUDE.md`](CLAUDE.md) and
  [`CONVENTIONS.md`](CONVENTIONS.md).

## Quickstart

The project is built and run with [`uv`](https://docs.astral.sh/uv/) (Python
3.11+); exact dependency versions are pinned in `uv.lock`.

```bash
# 1. Clone
git clone https://github.com/jessicacohen554-cyber/market-simulator.git
cd market-simulator

# 2. Install the locked environment (creates .venv from pyproject.toml + uv.lock)
uv sync

# 3. Run a historical backcast (ERCOT, 2024) — calibrates against actuals.
#    ERCOT runs the full plant-level diagnostic; other ISOs run energy-only.
uv run python scripts/run_calibration_full.py --iso ERCOT --year 2024

# 4. Run the test suite
uv run python -m pytest -q
```

The installed console script exposes the scenario runner directly:

```bash
uv run market-sim --help                 # subcommands: run, sweep, ensemble
uv run market-sim run --config <scenario.yaml> [--iso ERCOT]
uv run market-sim sweep --sweep <sweep.yaml> [--workers N]
```

> **Test status:** the suite collects ~1900 tests (1937 as of this writing). A
> handful of *known, pre-existing* failures are tied to optional local data and
> are unrelated to setup — the four `test_eia_loader` CAISO/NYISO zonal-share
> fallback cases, plus a NEISO committed-artifact determinism check. A clean
> checkout reports almost all passing / 2 skipped alongside these. Don't chase
> them as part of a docs or environment change.

### Without `uv`

`pyproject.toml` + `uv.lock` are the single source of truth for dependencies.
A generated, fully-pinned `requirements.txt` is provided as a **pip fallback
only** for environments where `uv` is unavailable (`pip install -r
requirements.txt`); regenerate it from the lockfile rather than hand-editing
(see the header in that file).

## Repo layout

```
market-simulator/
├── src/market_sim/      # The simulator package: config, data loaders, LP model,
│                        #   policy, results, and the runner CLI entry point.
├── data/                # Input datasets — raw/ (sources), dictionary/ (schema docs).
│                        #   Read-only at runtime; see data/README.md.
├── scripts/             # Calibration backcasts, data builders, and analysis/probe
│                        #   tooling (e.g. run_calibration_full.py).
├── tests/               # pytest suite (unit + regression against golden baselines).
├── docs/                # Methodology notes, calibration logs, cleanup/reorg plans.
├── frontend/            # Static explainer site (HTML/CSS/JS, parameter views) and
│                        #   backcast-dashboard payloads (frontend/data/backcast/). The
│                        #   deployable dashboard is the codebase-site pages
│                        #   docs/codebase-site/{backcast-runs,calibration-status}.html
│                        #   (data auto-built at deploy from those payloads).
├── learning-hub/        # Scrollytelling explainers (LP dispatch, storage, zones…).
├── tools/               # Desktop launcher UI (tools/launcher.py).
├── results/             # Cached run outputs and golden baselines.
└── context/             # Reference-model summaries for the reviewer agent
                         #   (placeholder — see context/README.md).
```

## Further reading

- [`model-methodology-spec.md`](model-methodology-spec.md) — the full model
  methodology (LP formulation, pricing, capacity evolution, calibration).
- [`CLAUDE.md`](CLAUDE.md) — working instructions, architecture overview, and
  repo conventions for contributors and agents.
- [`docs/data-reorg-plan.md`](docs/data-reorg-plan.md) — the data-layout
  reorganization plan (`data/raw` → `data/clean`, dictionary).
- [`docs/code-docs-cleanup-plan.md`](docs/code-docs-cleanup-plan.md) — the
  documentation/code cleanup plan this front-door work is part of.
- [`docs/data-licensing.md`](docs/data-licensing.md) — source, license terms,
  and redistribution status for every dataset committed under `data/raw/`.

Docs are kept in sync with the code via the `/sync-docs` skill — run it at the
end of a session once an approach has settled.
