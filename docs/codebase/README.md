# Codebase Documentation

Comprehensive, code-derived reference for the **market-sim** electricity market
dispatch and policy simulator. Every page in this directory was written by reading
the actual source under `src/market_sim/` — function signatures, constraint
assembly, and data flow are described as *implemented*, not as specified. Where the
narrative methodology documents (`model-methodology-spec.md`, `docs/*.md`) and the
code diverge, **this set follows the code.**

> Scope note: this is engineering reference documentation (what the code does and
> how the pieces fit). For the economic/market-design rationale behind a given
> mechanism, see `model-methodology-spec.md`. For the numeric provenance of any
> constant, see `docs/parameter-citations.md`.

## What the simulator is

A pure-LP (no MIP) hourly economic-dispatch and capacity-expansion model for U.S.
ISOs, run forward 2026→2050 with a historical-backcast mode (2021–2025 for
ERCOT; 2023–2025 for the other multi-year ISOs) for
calibration. The solver is HiGHS via `highspy`; **prices are recovered as the LP
duals on the energy-balance constraints** — there is no separate pricing model.
Nine registered regions share one ISO-agnostic LP: ERCOT (the calibrated
reference), CAISO, PJM, MISO, NYISO, NEISO, SPP, NWPP and SOCO. Every name in
the code says "ISO"; the last two are not — **NWPP** is a pool of ~17 balancing
authorities and **SOCO** is a single balancing authority. Both registered
2026-09-14 and neither has a keeper yet.

## Reading order

| # | Page | Covers |
|---|------|--------|
| 1 | [`01-architecture.md`](01-architecture.md) | The end-to-end pipeline, package layout, the multi-year solve loop, key design rules |
| 2 | [`02-lp-dispatch.md`](02-lp-dispatch.md) | The LP core: variable layout, vectorized constraint assembly, objective, duals→prices, HiGHS interface, warm-start |
| 3 | [`03-capacity-and-commitment.md`](03-capacity-and-commitment.md) | One-pass capacity evolution (6 steps), the P0→P1→P2 commitment screen, storage, transmission, ancillary services |
| 4 | [`04-data-layer.md`](04-data-layer.md) | Fleet construction (CAMPD binning, tranche offer curves), fuel, renewables, outages, hydro, ownership, zone assignment |
| 5 | [`05-policy.md`](05-policy.md) | IRA credits, RPS, carbon pricing, EACs, scarcity overlays (ERCOT ORDC, NYISO RCPF, PJM) |
| 6 | [`06-results-and-calibration.md`](06-results-and-calibration.md) | Parquet caching, result serialization, emissions, plant financials, calibration diagnostics |
| 7 | [`07-runner-and-cli.md`](07-runner-and-cli.md) | Orchestration, CLI subcommands, sweeps, weather ensembles, calibration scripts |
| 8 | [`08-config-reference.md`](08-config-reference.md) | `ScenarioConfig` field reference, per-ISO topology, the constants catalogue, path resolution |

## The one-paragraph mental model

A `ScenarioConfig` (YAML → pydantic dataclass) selects an ISO, a mode
(`forecast`/`backcast`), a weather year, and a set of policy/forecast levers. The
runner loads weather-fixed inputs once (zonal demand, wind/solar capacity factors,
transmission topology), then walks years sequentially. Each year it (1) builds or
evolves the generator fleet, (2) flattens it into a struct-of-arrays
(`FleetArrays`), (3) assembles per-hour marginal costs, (4) builds a single 8760-hour
LP via vectorized sparse-matrix construction, and (5) solves up to three times
(P0 base cost → P1 startup-markup pricing → optional P2 commitment screen).
Energy prices are the duals on the per-zone energy-balance rows. Results are cached
one Parquet per scenario-year; prices feed the next year's capacity-economics
screens. Backcast runs additionally score the result against EIA-930/CAMPD/EIA-923
actuals.

## Conventions used throughout

- File:line references point at the source as of this writing — treat them as a
  starting point, not a guarantee against drift.
- "the LP" = the single annual 8760-hour dispatch program built in
  `model/dispatch.py`.
- Variable shorthand follows the code: `t`=hour, `g`=generator, `z`=zone,
  `s`=storage, `l`/`ln`=transmission link.
</content>
</invoke>
