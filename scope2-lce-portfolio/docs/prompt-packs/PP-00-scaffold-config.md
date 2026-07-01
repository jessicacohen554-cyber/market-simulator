# PP-00 — Scaffold & PortfolioConfig

**Upstream:** ADR 0001 (standalone/vendored), 0002 (default mode).
**Targets:** `src/lce_portfolio/config.py`, package `__init__`, `pyproject.toml`.
**Status:** done (minimal). This pack documents it and lists extensions.

## Done

- Package skeleton under `src/lce_portfolio/`, standalone (no `market_sim`).
- `PortfolioConfig` dataclass: iso/year, mode, `premium_deltas`,
  `matching_targets`, `strict_hourly_matching`, `lcoe_sensitivity`,
  `active_resources`, `resource_caps_mw`/`resource_floors_mw`,
  `excess_sale_fraction`, `storage_epsilon`, load-growth fields.
- `pyproject.toml` (deps + console script `lce-portfolio`).

## Extensions to build (as decisions land)

- Add fields decided in PS-01 (`cost_representation`), PS-02 (curtailment/REC),
  PS-03 (storage cost mode), PS-04 (carbon reporting), PS-07 (per-facility
  growth). Keep the dataclass flat and typed; every field gets a docstring.
- Add a `from_yaml`/`from_json` loader so runs are config-file driven (mirror the
  market-sim scenario style) — optional but recommended for handoff.
- Validate: mode ∈ {premium_cap, matching_target}; fractions ∈ [0,1]; deltas > 0.

## Acceptance

`python -c "from lce_portfolio import PortfolioConfig; PortfolioConfig()"` works;
`test_config` covers validation and `with_overrides`.
