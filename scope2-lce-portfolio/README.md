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
docs/                 design docs, decision log (ADRs), planning-session prompts, prompt packs
src/lce_portfolio/    the package (config, resources, intake, profiles, lp, sweep, outputs, cli)
  vendored/           copied market-sim logic (kept standalone; re-sync notes)
data/lcoe/            resource cost table (low/mid/high)
data/sample/          synthetic inputs for the demo & tests
tests/                pytest (trivial-case-first)
examples/             runnable examples
```

## Status

Waves 0–2 complete (PP-00 through PP-08, 147 tests passing). Full capabilities:
real data intake (load, LMP, fossil-avg CO₂ rate), NREL ATB 2024 resource pricing (capex/CRF),
split-storage (LDES, hydrogen), hydro monthly budgets, additionality accounting, gas CC+CCS
resources with CCS threshold matching credit and 45Q net VOM, residual CO₂ tracking (grid +
resource), optional storage charge-provenance policy (`--storage-charge-policy
excess_clean_only`: charge only on excess contracted clean generation, no grid arbitrage;
ADR 0017). Decisions: PS-01 through PS-12 → ADRs 0004–0015 (ratified 2026-07-02); ADR 0017
(storage audit, 2026-07-04).
Next: PP-09 (reporting deliverable, in flight). Start with `PLAN.md`, then
`docs/00-overview.md` and `docs/01-lp-formulation.md`.
