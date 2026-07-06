# How it works

The single narrative doc to read after `README.md`. It explains what the tool
does end to end and points into the detail docs rather than repeating them.
See also the [HTML explainer site](site/index.html) for a visual walkthrough
of the same material.

## What it answers, for whom

A company or facility that wants **24/7 carbon-free energy (hourly matching)**
needs to know what portfolio of clean generation + storage gets them there,
and what it costs. Given an hourly (or annual-average) load and the prevailing
wholesale price (BAU LMP), this tool answers:

> *How hourly-matched with clean energy can we get for a given cost premium
> above wholesale — and with what mix of wind, solar, nuclear, geothermal,
> hydro, gas CC+CCS, batteries, LDES and hydrogen?*

It sweeps a premium ladder (or a matching-target ladder) and reports the
matching %, cost, resource mix, and residual carbon at each point. It is
built for whoever picks up this handoff — a developer or analyst extending
the model, not an end user filling in a spreadsheet — and it is a **planning**
tool: single node per ISO, price-taker, no unit commitment (see Limits below).

## Architecture walkthrough

One pipeline, six stages, run once per ISO per sweep:

```
intake → profiles → resources → lp → sweep → outputs → report → launcher
```

| Stage | Module | Contract |
|---|---|---|
| **Intake** | `src/lce_portfolio/intake.py` | Reads the load file (`prepare_load`, facility-level auto-aggregated to one ISO vector via `aggregate_by_hour_iso`, ADR 0010), the LMP file (`prepare_lmp`, hourly or annual-average schema, ADR 0011/HP-01), and the optional fossil-avg CO₂-rate file (`prepare_emission_rate`, ADR 0013). Every reader hard-fails on missing/duplicate hours or an unknown ISO — never a silent zero-fill. |
| **Profiles** | `src/lce_portfolio/profiles.py` | Builds the `(n_resource, 8760)` capacity-factor matrix, `build_cf_matrix(resources, iso, year, *, profiles_dir=None, required=False)`. Reads real per-ISO Parquet under `data/profiles/` when present; falls back to a deterministic synthetic shape (or hard-errors) when `required=True` — see `profile_shape_year` below. |
| **Resources** | `src/lce_portfolio/resources.py` | Loads `data/lcoe/resource_costs.csv` + `data/caps/resource_caps.csv`, applies the `lcoe_sensitivity` (low/mid/high) column, computes annualized fixed cost via CRF, assembles gas CC+CCS effective VOM (fuel + 45Q credit), and returns struct-of-arrays `ResourceArrays` — no Pydantic objects reach the LP builder. |
| **LP** | `src/lce_portfolio/lp.py` | Builds and solves the capacity-choice + hourly-operation LP via HiGHS (`highspy`), vectorized (`scipy.sparse`, no Python loop over hours). One solve per sweep setpoint. See "The LP" below. |
| **Sweep** | `src/lce_portfolio/sweep.py` | `run_sweep` drives one LP solve per premium delta (Mode A) or matching target (Mode B) and collects `PortfolioResult` rows into a `SweepResult`. |
| **Outputs** | `src/lce_portfolio/outputs.py` | `write_outputs` writes `<iso>_frontier.parquet`, `<iso>_build_mix.parquet`, a text summary, and (by default) the ADR 0014 report; `write_report` combines multiple ISOs' sweeps into one report. |
| **Report** | `src/lce_portfolio/report.py` | `build_report_payload` + `render_report`: a versioned JSON payload rendered into one self-contained HTML file (inline CSS/JS/SVG, no CDN) — provenance, frontier chart, build-mix, cost breakdown, residual CO₂, multi-ISO comparison, and an hourly heatmap/SOC view. |
| **Launcher** | `src/lce_portfolio/launcher.py` | Double-click desktop entry point — see "The launcher" below. |

`src/lce_portfolio/cli.py` (`run_one_iso`, `main`) is the orchestrator that
calls intake → profiles → resources → sweep → outputs in that order for one
or all ISOs in a load file; the launcher calls this same `cli.main()`
in-process rather than re-implementing any of it.

`src/lce_portfolio/vendored/` holds the one piece of market-sim logic this
tool reuses (`renewable_shapes.py`, for building CF profiles from EIA-930
data) — copied, not imported, with a re-sync header pinning the upstream
commit (ADR 0001). There is no `import market_sim` anywhere in `src/`.

## The LP, in plain language

Full math and the constraint-by-constraint derivation lives in
[`docs/01-lp-formulation.md`](01-lp-formulation.md) — this section is the
one-paragraph version plus the variable/constraint inventory so you know what
to look up.

The LP is a **capacity-choice + hourly-operation** problem over a single
aggregated node per ISO, the full 8760 hours, solved once per sweep setpoint.
It chooses how much of each clean resource and storage tech to build
(`build_mw`, plus `build_energy` for split-power/energy storage), then
dispatches them hour by hour against the fixed load and LMP series, buying
any shortfall from the grid (`grid_buy`) and selling any surplus
(`excess`) at LMP. Because both settle at the hourly price, the optimizer
naturally spends its premium budget covering the **most expensive** hours
first — the mechanism the tool is built around, not a heuristic layered on
top.

**Decision variables:** `build_mw[r] | gen[r,t] | chg[s,t] | dis[s,t] |
soc[s,t] | grid_buy[t] | excess[t] | build_energy[k] | exc_ex[t]` (the last
only when `additionality_only` is on).

**Constraints:** energy balance (per hour), generation ceiling
(`gen ≤ cf·build_mw`), cyclic storage SOC dynamics with duration/energy
bounds, a fleet-shared hydro monthly energy budget, and — for the two
opt-in `storage_charge_policy` settings — a storage-charge-provenance row
(`Σchg + excess ≤ Σgen`, ADR 0017) with an iterative headroom cut loop
(ADR 0018) that eliminates divert-and-backfill.

**Two objectives:** Mode A (`premium_cap`, default) minimizes `Σ grid_buy`
(= maximizes matching) subject to the premium staying under a cap δ, with a
flat build-size tiebreak (ADR 0019) to avoid a degenerate build once matching
saturates. Mode B (`matching_target`) minimizes net cost subject to matching
≥ a target (annual or strict per-hour).

Solver: HiGHS interior-point (crossover off) for speed on the long temporal
storage coupling, with a one-time crossover-on retry when the fast path
doesn't return `Optimal` (see the LP doc's "Solver notes" for why).

## Data contracts

Full detail: [`docs/02-data-inputs.md`](02-data-inputs.md) and
[`data/templates/README.md`](../data/templates/README.md). Summary:

- **Load** — CSV/Parquet, long form, columns `hour, iso, load_mwh[, facility]`.
  Facility-level rows are auto-summed within each `(iso, hour)`
  (`intake.aggregate_by_hour_iso`, ADR 0010) — supply as many facility rows
  per hour as you like; the `facility` column is optional. Every `(iso,
  hour)` for `0..8759` must be present; missing hours are a hard error.
- **LMP — two formats, same file position, schema-detected:**
  - *Hourly* (`hour, iso, lmp`, ADR 0011) — the preferred, shape-aware
    contract. Premiums and matching frontiers reflect the real price shape,
    since the optimizer targets expensive hours.
  - *Annual-average* (`iso, annual_avg_lmp`, no `hour` column, HP-01) —
    intake detects the missing `hour` column and expands each ISO's single
    value to a flat 8760 vector (`np.full`). **Caveat:** this makes the run
    an annual-average-price *comparison*, not a shape-aware one — hourly
    price shape/covariance value is deliberately excluded, since a flat
    price gives the optimizer no expensive-hour signal to target. The run's
    `lmp_kind` metadata field and the report's provenance section both read
    `annual_average_flat` so this is never confused with a real hourly run.
  - Both formats are schema-validated the same way (duplicate row, missing
    ISO, non-finite/negative price are all hard errors).
- **Fossil-average CO₂ rate** (optional) — `hour, iso, fossil_avg_co2_rate`
  (ADR 0013), the market simulator's hourly fossil-only average emission
  intensity. Missing file just turns off residual-carbon reporting.
- **Templates** — `data/templates/` ships three small, human-readable example
  CSVs (one per schema above) plus a README describing the contracts;
  `scripts/make_input_templates.py` generates full 8760-row fillable
  skeletons into the gitignored `data/templates/skeletons/`.
- **Bundled data inventory** (committed, for standalone pull-out — HP-02/HP-02b):
  - `data/profiles/<ISO>_<year>.parquet` — real per-ISO 2024 capacity-factor
    shapes for all six ISOs, built from market-sim EIA-930 data via the
    vendored renewable-shape logic. **Committed** (HP-02) — deterministically
    reproducible with `scripts/build_profiles.py`, but shipped so a pulled-out
    copy has real shapes without the parent tree.
  - `data/bundled/lmp/<ISO>_2024_bau_lmp.csv` + `.provenance.json` sidecar —
    real 2024 backcast BAU LMP exports for all six ISOs, each naming its
    source calibration keeper (a 2024-only bridge re-solve, backcast-validation
    carve-out only per ADR 0015 — never a registered dashboard keeper). **Committed.**
  - `data/emissions/<ISO>_2024_fossil_avg_co2_rate.parquet` + `.provenance.json`
    sidecar — matching hourly fossil-avg CO₂-rate files for all six ISOs, from
    the same bridge solve as the sibling LMP bundle (ADR 0013). **Committed.**
  - `data/reference/reference_load_100mw.csv` — a stylized 100 MW facility
    load, generated on demand by `scripts/make_reference_load.py`.
    **Gitignored** (regenerated deterministically, no RNG).
  - `data/lcoe/resource_costs.csv`, `data/caps/resource_caps.csv`,
    `data/hydro/monthly_budgets.csv`, `data/fuel/gas_prices.csv` — small
    reference tables, all **committed**.
  - What regenerates vs. ships: the CF profiles, LMP bundles and CO₂-rate
    bundles all **ship** as committed data — the LMP/emissions bundles are the
    product of a market-sim solve this tool cannot reproduce on its own (so
    they carry a provenance sidecar), and the profiles are committed too so a
    pulled-out copy is self-sufficient. Only the stylized reference load and
    the template skeletons **regenerate** — gitignored, rebuilt deterministically
    on demand from committed scripts (`make_reference_load.py`, the templates
    step), no RNG.

## Matching, premium, and residual-carbon semantics

Pointers into the ADRs that decided each:

- **Matching (ADR 0007)** is *volumetric hourly matching*: clean energy
  counts toward matching only up to that hour's load
  (`matched_t = load_t − grid_buy_t`); surplus is excluded. The annual score
  is `1 − Σ grid_buy / Σ load` — percentage of *load energy* matched at
  hourly granularity, not "% of hours at 100%".
- **Premium (ADR 0005)** is `(net_cost − BAU) / Σ load`, where surplus sales
  are credited at `f × LMP` (ratified `f = 1.0`, full LMP credit).
- **Gas CC+CCS matching credit (ADR 0012)** is threshold-full: a resource
  counts fully toward matching iff `capture_rate > 0.90` and
  `emission_rate_ton_mwh < 0.050`; residual stack emissions are still tracked
  and reported separately, never intensity-discounted.
- **Residual carbon (ADR 0013)** attributes grid purchases at the market
  simulator's hourly fossil-only *average* emission rate (attributional,
  superseding ADR 0007's marginal-rate approach), plus gas CC+CCS resource
  emissions — reported as separate `grid_co2_tons` / `resource_co2_tons`.
- **Storage charge provenance (ADR 0017 / ADR 0018)** — optional
  `storage_charge_policy`: default `arbitrage` lets storage buy low/sell high
  at LMP; `excess_clean_only` restricts charging to the portfolio's own
  contracted clean generation (no grid trading); `excess_headroom_only`
  additionally runs an iterative LP cut loop that eliminates
  divert-and-backfill (charging in the same hour as a grid purchase).
- **Mode A build tiebreak (ADR 0019)** — a flat per-MW epsilon on `build_mw`
  breaks the degenerate tie that appears once matching saturates below a
  resource's cap (found on CAISO's onshore-wind build drifting to its 20 GW
  cap with no cost signal to stop it).

## The launcher

Implements ADR 0016. Flow: **form → queue → CLI → results store → cached
report.**

1. `launcher/run_lce.sh` / `run_lce.bat` resolve a usable Python (repo
   `../.venv` first, else a version/import-checked `python3`/`python` on
   `PATH`) and start `python -m lce_portfolio.launcher`, which binds a
   stdlib `ThreadingHTTPServer` to `127.0.0.1` on an ephemeral port and opens
   the browser on a self-contained HTML launch page (inline CSS/JS, ADR
   0016 §2).
2. The page's **Add to queue** / **Submit queue** buttons `POST
   /api/run`. `LauncherState` holds one background daemon worker thread that
   drains a `Queue` of runs **sequentially** — LP solves never overlap
   regardless of how many browser tabs or batches submit.
3. For each queued run, `build_argv` composes an argv (always including
   `--results` + `--run-id`) and the worker calls `lce_portfolio.cli.main()`
   **in-process** — the same CLI entry point you'd use from a terminal,
   never a forked subprocess or reimplemented solve path. `cli.main` runs
   intake → profiles → resources → sweep → outputs, persisting into
   `results/<run-id>/` (an atomic-ish swap: writes to `<run-id>.tmp/` and
   renames on success, ADR 0014 §5).
4. `write_outputs`/`write_report` emit `report.json` + `report.html` next to
   the Parquet outputs — a run's report is a cached file, not
   re-rendered per view. The launcher serves it back through
   `/reports/<run_id>/report.html`, and the "Past runs" panel lists every
   `results/<run_id>/` directory with a valid `<iso>_run_metadata.json`.
5. Every finished run appends one line to `launcher/run_log.jsonl`
   (run id, params, status, wall time, error summary on failure) —
   gitignored, machine-local, an append-only history distinct from the
   results store itself. The "Run log" panel shows its last 20 entries.

**Security posture, in three bullets:**

- **Loopback-only, unauthenticated.** The server binds `127.0.0.1` and there
  is deliberately no `--host` flag (ADR 0016 §2) — it must never be reachable
  from another machine.
- **Bounded, whitelisted inputs.** Request bodies are capped
  (`MAX_REQUEST_BYTES`, 1 MiB) and rejected over that limit; the file-path
  dropdowns only ever list four whitelisted directories (`data/inputs/`,
  `data/bundled/lmp/`, `data/templates/`, the bundled reference load) — never
  arbitrary filesystem browsing — and results-store run ids are validated
  against a single-path-component pattern before being used to compose or
  delete a directory.
- **No raw tracebacks reach the browser.** Every user-facing error path
  (validation, an unexpected exception mid-solve, a malformed request) is
  caught and rendered as a short, friendly message; the real traceback (if
  any) only ever prints to the terminal running the server.

## Pulling the folder out and running it standalone

`scope2-lce-portfolio/` is designed to be copied out of this repo and run on
its own — no parent-repo access, no `import market_sim`. The documented
procedure is `scripts/verify_standalone.sh`, which:

1. Copies the tool to a fresh temp directory *outside* the parent repo (a
   plain recursive copy, not `git archive`, so gitignored-but-committed data
   like `data/profiles/` and the LMP/emissions bundles come along).
2. Greps the copy for any real `import market_sim` / `from market_sim`
   statement and fails if one is found.
3. Builds a fresh virtualenv from `requirements.txt` alone.
4. Runs `pytest -q`, the synthetic `examples/run_sample_sweep.py` demo, a
   real-ISO CLI run against the committed bundled data only (load, LMP,
   emissions), and a launcher smoke test (starts the server, checks `/`
   returns HTTP 200).

Run it yourself with `scope2-lce-portfolio/scripts/verify_standalone.sh`
(optionally `VERIFY_ISO=CAISO scripts/verify_standalone.sh` to pick a
different bundled ISO). A clean run is the acceptance test for "the folder
is truly pull-out-able."

## Limits & non-goals

- **Single aggregated node per ISO** — no intra-ISO transmission/nodal
  detail; a zonal/nodal LMP series is collapsed to one ISO-level price
  before it reaches this tool.
- **Price-taker** — the portfolio's build/dispatch decisions never feed back
  into the LMP series; it consumes the market simulator's BAU output as a
  fixed input.
- **No unit commitment** — resources are continuous capacity-choice + LP
  dispatch, not a MIP; this mirrors the market simulator's own P1 no-commitment
  main run, not an omission specific to this tool.
- **The market-sim forecast LMP path is on hold** (ADR 0015, stakeholder
  decision 2026-07-02): the exporter's `--dummy` synthetic mode and the
  backcast-validation carve-out (2024 bridge re-solves, bundled under
  `data/bundled/lmp/`) are the only working LMP sources today. When an ISO's
  forecast is blessed, ADR 0015 already pins the years (2030/2035/2040/2045/2050),
  scenario, and rollout order — zero new decisions needed at that point.
