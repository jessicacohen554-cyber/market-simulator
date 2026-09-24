# market-sim

LP-based electricity market dispatch and policy simulator. Forecasts hourly
(8760) generation, prices, emissions and capacity evolution across U.S. ISOs
from 2026→2050, with a historical-backcast mode for calibration against EIA-930,
CAMPD, eGRID and EIA-923 actuals.

- **Solver:** HiGHS via `highspy` (pure LP, no MIP). Prices are LP duals.
- **Regions:** ERCOT (calibrated reference) plus CAISO, PJM, MISO, NYISO, NEISO,
  SPP, the NWPP pool (17 WECC balancing authorities) and the SOCO balancing authority.
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

> **Test status:** run `uv run python -m pytest -q` for the current suite; the
> authoritative pass/fail signal is the CI test job (this README deliberately
> does not track an exact count, which drifts). The formerly known-failing
> set (`test_eia_loader` zonal-share cases, the NEISO committed-artifact
> determinism check) was cleared by the 2026-07/08 data completions and the
> 2026-08 debug sweep — a clean **full** checkout now passes the fast tier
> (`-m "not slow and not integration and not fulldata"`) with zero expected
> failures. The fast tier hard-requires `data/raw` (see the ci.yml header);
> on a data-less/partial checkout, `data/raw`-reading tests fail by design,
> and `integration`-marked tests additionally need the derived `data/clean`
> regenerated (`scripts/regenerate_clean.py`). If the fast tier is red on a
> full checkout, that's a regression to fix, not ambient noise to ignore.

> **Single-year runs are smoke tests only.** `--year 2024` above is for
> quickly checking the environment works. Rule 16 (`CLAUDE.md`) requires
> every registered calibration keeper to solve and register **all**
> available years for that ISO in one bundle (e.g. `--year 2023 2024 2025`
> for CAISO/PJM/MISO/NYISO/NEISO) — a single-year bundle is never a keeper.

### Which install path?

`uv` + `pyproject.toml`/`uv.lock` (above) is the **canonical** way to install
and run this project — it's what CI uses and what dependency versions are
pinned against. `run-simulator.sh` (and its Windows counterpart
`run-simulator.bat`) is a **convenience launcher only**: it bootstraps a
plain `venv` + `pip install -e .` on first run and opens the desktop
launcher UI (`tools/launcher.py`) for users who don't have `uv` installed.
Prefer `uv` for development, calibration runs, and anything you'll debug;
use the launcher script only for a quick local UI session.

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
├── configs/             # Scenario/sweep/uncertainty YAML configs (scenario_matrix.yaml,
│                        #   uncertainty_ercot.yaml, scenarios/) consumed by the CLI.
├── data/                # Input datasets — raw/ (sources), dictionary/ (schema docs).
│                        #   Read-only at runtime; see data/README.md.
├── scripts/             # Core runners, scoring, dashboard & governance tooling
│                        #   (see scripts/README.md).
├── tests/               # pytest suite (unit + regression against golden baselines).
├── docs/                # Methodology notes, calibration logs, cleanup/reorg plans.
├── frontend/            # Static explainer site (HTML/CSS/JS, parameter views) and
│                        #   backcast-dashboard payloads (frontend/data/backcast/). The
│                        #   deployable dashboard is the codebase-site pages
│                        #   docs/codebase-site/{backcast-runs,calibration-status}.html
│                        #   (data auto-built at deploy from those payloads).
├── learning-hub/        # Scrollytelling explainers (LP dispatch, storage, zones…).
├── tools/               # Desktop launcher UI (tools/launcher.py).
├── results/             # Cached run outputs and golden baselines, incl. hindcast/
│                        #   (forecast-validation year-loop caches — see
│                        #   docs/forecast-validation-plan.md).
├── scope2-lce-portfolio/ # Standalone Scope-2 hourly clean-energy-matching
│                         #   portfolio tool; consumes this simulator's LMP
│                         #   output but is a separate project (see
│                         #   docs/scope2-lce-portfolio.md).
└── context/             # Reference-model summaries for the reviewer agent
                         #   (placeholder — see context/README.md).
```

## Further reading

- [`docs/README.md`](docs/README.md) — the documentation index (start here; the
  four-layer information architecture over everything below).
- [`model-methodology-spec.md`](model-methodology-spec.md) — the full model
  methodology (LP formulation, pricing, capacity evolution, calibration).
- [`docs/codebase/README.md`](docs/codebase/README.md) — the code-derived
  engineering reference (what the code actually does, page by page).
- [`docs/multi-iso/README.md`](docs/multi-iso/README.md) — the nine-region topology
  and per-ISO addition protocol.
- [`docs/forecast-development-plan-2026-07.md`](docs/forecast-development-plan-2026-07.md)
  — the forecast program (tier ladder, lanes, waves, prompt pack).
- [`docs/calibration-determination-rubric.md`](docs/calibration-determination-rubric.md)
  and [`docs/forecast-determination-rubric.md`](docs/forecast-determination-rubric.md)
  — how a calibration/forecast run is judged.
- The dashboard —
  [`docs/codebase-site/backcast-runs.html`](docs/codebase-site/backcast-runs.html)
  (run explorer) and
  [`docs/codebase-site/calibration-status.html`](docs/codebase-site/calibration-status.html)
  (keeper summary) — for live results.
- [`CLAUDE.md`](CLAUDE.md) — working instructions and repo conventions for
  contributors and agents; [`docs/data-licensing.md`](docs/data-licensing.md)
  for dataset licensing.

Docs are kept in sync with the code via the `/sync-docs` skill — run it at the
end of a session once an approach has settled.
