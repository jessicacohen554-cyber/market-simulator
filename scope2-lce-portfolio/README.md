# Scope 2 Hourly LCE Portfolio Optimization Tool

A self-contained decision tool that selects a portfolio of **clean & low-carbon
energy (LCE)** resources plus storage to match a company/facility **8760 load**
hour-by-hour, at the **lowest cost premium above wholesale energy prices**.

Given a business-as-usual (BAU) hourly LMP series and a load profile, it answers:

> *"How hourly-matched with carbon-free energy can we get for a $1 / $2 / $5 / $7 /
> $10 / $20 premium — and with what mix of wind, solar, nuclear, geothermal,
> hydro, batteries, LDES and hydrogen?"*

## Relationship to the market simulator (isolation boundary)

This tool lives entirely under `scope2-lce-portfolio/` and is **fully
standalone**: there is **no `import market_sim` anywhere**. It *consumes* the
market simulator's output (BAU hourly LMPs) as an input file, and any loader
logic it reuses is **copied** into `src/lce_portfolio/vendored/` with re-sync
notes. The market LP solver in `src/market_sim/` is never modified or imported.
The only in-repo pointer is `docs/scope2-lce-portfolio.md`.

## What it does

- **Intake:** an 8760 load dataset, possibly facility-level and multi-ISO;
  aggregated to one hourly vector per ISO. Optional load-growth parameter.
- **Resources:** all clean/low-carbon supply (existing & new nuclear, on/offshore
  wind, solar, geothermal, hydro) plus storage (4/8/12h batteries, LDES,
  hydrogen), each at **low/mid/high** cost. Per-resource **capacity caps**.
- **LMP coupling:** consumes the BAU hourly LMP; grid purchases and excess sales
  are valued at LMP, so the optimizer naturally targets expensive hours to
  minimize the premium.
- **Two modes:** *premium-cap → max matching %* (default) and
  *matching-target → min premium*.
- **Output:** a matching%-vs-premium frontier and the selected build mix per
  setpoint, as Parquet + a text summary.

## Quick start

```bash
# from scope2-lce-portfolio/ , using the repo's virtualenv
../.venv/bin/python examples/run_sample_sweep.py          # synthetic end-to-end demo
../.venv/bin/python -m pytest tests/ -q                    # tests

# on your own data (run_portfolio.py puts src/ on the path — no install needed):
../.venv/bin/python run_portfolio.py \
    --load data/inputs/my_load.csv --lmp data/inputs/bau_lmp.csv \
    --iso ERCOT --deltas 1 2 5 7 10 20 --out-dir data/outputs
```

Or `pip install -e .` and use the `lce-portfolio` console script (equivalently
`PYTHONPATH=src ../.venv/bin/python -m lce_portfolio ...`).

## Layout

```
docs/                 design docs, decision log (ADRs), validation memos
docs/handoff/         handoff package: finalization prompts HP-01..HP-05 + status
src/lce_portfolio/    the package (config, resources, intake, profiles, lp, sweep, outputs, report, launcher, cli)
  vendored/           copied market-sim logic (kept standalone; re-sync notes)
launcher/             double-click desktop launcher (run_lce.sh / run_lce.bat → local HTML UI)
data/lcoe/            resource cost table (low/mid/high)
data/templates/       draft input templates (8760 load by ISO+facility; hourly or annual-average LMP)
data/sample/          synthetic inputs for the demo & tests
results/              committed results store (one dir per run: parquet + report.html + metadata)
tests/                pytest (trivial-case-first)
examples/             runnable examples
```

## Status

Waves 0–2 and the standalone handoff-prep waves are complete (PP-00 through
PP-08, HP-01 through HP-05, 328 tests passing). Full capabilities:
real data intake (load, LMP, fossil-avg CO₂ rate), NREL ATB 2024 resource pricing (capex/CRF),
split-storage (LDES, hydrogen), hydro monthly budgets, additionality accounting, gas CC+CCS
resources with CCS threshold matching credit and 45Q net VOM, residual CO₂ tracking (grid +
resource), optional storage charge-provenance policy (`--storage-charge-policy
excess_clean_only`: charge only on excess contracted clean generation, no grid arbitrage;
ADR 0017) — with an always-on `divert_backfill_mwh` diagnostic and a stricter
`excess_headroom_only` variant whose iterative LP cut loop eliminates
divert-and-backfill (ADR 0018). Decisions: ADRs 0004–0019 (see
`docs/decisions/DECISIONS.md`). Reporting (ADR 0014), the desktop launcher
(ADR 0016), and six-ISO 2024 backcast validation sweeps are all done; 328
tests passing (2026-07-06).

**Finalization for standalone handoff is complete** (the HP-01..HP-05 prompts
in `docs/handoff/`: annual-average LMP mode, bundled pull-out data, launcher
results browser, docs site, final extraction QA — see
`docs/handoff/SIGNOFF.md`). Start with
`PLAN.md`, then `docs/how-it-works.md` (the single narrative mechanics doc),
then `docs/00-overview.md` and `docs/01-lp-formulation.md`. There's also a
self-contained HTML explainer site at
[`docs/site/index.html`](docs/site/index.html) — open it directly in a
browser, no server required.
