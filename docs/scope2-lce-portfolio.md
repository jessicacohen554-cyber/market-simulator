# Scope 2 Hourly LCE Portfolio Tool — pointer

> This is a **pointer doc**. The tool itself is a **separate, self-contained
> project** and is the *only* place its code lives. The market LP solver in
> `src/market_sim/` is **not** part of it and must stay untouched.

## What it is

`scope2-lce-portfolio/` is a standalone decision tool that selects a portfolio of
clean & low-carbon energy resources + storage to match a company/facility 8760
load hour-by-hour, at the lowest cost **premium above wholesale**. It consumes the
market simulator's business-as-usual hourly LMP output and sweeps a "clean
premium" ($1, $2, $5, $7, $10, $20, …) to report how high hourly carbon-free
matching can go at each premium, per ISO — with per-resource capacity caps and
low/mid/high costs.

## Where it lives

Top-level directory: [`scope2-lce-portfolio/`](../scope2-lce-portfolio/).
Start with its [`PLAN.md`](../scope2-lce-portfolio/PLAN.md) and
[`README.md`](../scope2-lce-portfolio/README.md). The finalization work to
make the folder fully pull-out-able is staged as ready-to-run prompts in
[`scope2-lce-portfolio/docs/handoff/`](../scope2-lce-portfolio/docs/handoff/README.md)
(HP-01..HP-05).

## Isolation boundary (important)

- The tool is **fully standalone**: there is **no `import market_sim`** anywhere
  in it. Any reused loader logic is **copied** into
  `scope2-lce-portfolio/src/lce_portfolio/vendored/` with re-sync notes.
- It **consumes** the market sim's LMP output as a data file; it does not modify,
  import, or depend on `src/market_sim/`.
- Nothing in `src/market_sim/` should ever import from the tool.
- This file is the only market-sim-repo artifact that references the tool.

## Why it's separate

It solves a different problem (corporate 24/7-CFE procurement / portfolio
selection) from the market dispatch simulator, on a different LP. Keeping it in
its own project prevents the calibration-focused core from being contaminated by
procurement-tool concerns, and lets a separate owner iterate on it independently.
