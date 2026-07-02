# PS-12 — Forecast LMP Selection (years, scenario, readiness, rollout)
**DECIDED → [ADR 0015](../decisions/0015-forecast-lmp-selection.md) (2026-07-02)**

**Goal:** decide, ahead of need, exactly which market-sim forecast output feeds
this tool when the forecast side becomes production-ready — so that the day the
PLAN.md §10 hold lifts, the export is one command with zero new decisions.

## Why it matters

ADR 0011 fixed the *contract* (long-form `(hour, iso, lmp)` CSV, load-weighted
zonal collapse, no escalation, forecast run for the modeled year) and the
exporter exists (`scripts/export_lce_lmp.py`, market-sim repo root). But the
contract deliberately left the *selection* open: which modeled year(s), which
exact `ScenarioConfig` identity counts as BAU, what makes a forecast trustworthy
enough to drop `--dummy`, and in what order the six ISOs come online. Forecast
runs are on hold (PLAN.md §10, stakeholder 2026-07-02); this session pins those
selections now so no decision-making happens under time pressure later.

## Questions decided (stakeholder, 2026-07-02)

1. **Modeled year(s).** Single 2030, a small set, or a trajectory?
   → **Five study years: 2030, 2035, 2040, 2045, 2050**, each its own export
   file and its own portfolio sweep (tool `config.year` set to match). One
   full-horizon forecast solve per ISO caches every year, so the five exports
   share one upstream run.
2. **Scenario.** Base BAU `ScenarioConfig()` or a named variant?
   → **Base `ScenarioConfig()` as-is** (no scenario YAML): `mode="forecast"`,
   `gas_price_path="mid"`, `carbon_price=0.0` + `carbon_price_path="zero"`,
   `weather_year=2024`, canonicalized per-ISO by the exporter's
   `resolve_bau_config` (ISO `default_scenario_overrides` applied exactly as
   `run_scenario_iso` does). The recorded identity is the canonicalized
   `cache_key` in the provenance sidecar.
3. **Readiness criterion.** What lifts the hold?
   → **Per-ISO, two conditions**: (a) the ISO has a current calibrated backcast
   keeper on the dashboard covering all its scoreable years, and (b) explicit
   stakeholder sign-off that the forecast side is production-ready for that
   ISO, recorded by checking it off in PLAN.md §10. Only then may `--dummy` be
   dropped for that ISO.
4. **Rollout order.** → **Readiness-driven**: whichever ISO passes the gate
   first exports first. Expected/preferred sequence is ERCOT (calibrated
   reference) → PJM → the rest, but a later ISO (e.g. NEISO) that becomes
   ready sooner goes ahead of the queue. Portfolio runs proceed on the ready
   subset; the export re-runs with the expanded `--iso` list as ISOs join.

## Inputs reviewed

- ADR 0011 + `docs/04-lmp-export.md` (contract, provenance sidecar rule).
- `scripts/export_lce_lmp.py` (market-sim root): args `--iso` (repeatable),
  `--year` (default `START_YEAR` 2026), `--scenario` (YAML, default base
  config), `--allow-backcast`, `--dummy`, `--out`; refuses backcast mode
  without the flag; skips (never solves) missing caches.
- `src/market_sim/config/scenarios.py` — the BAU-relevant knobs and defaults
  listed above.
- Tool `config.year` default = 2030 (`src/lce_portfolio/config.py`).
- PLAN.md §10 hold text; ADR 0013 (companion hourly fossil-average CO₂-rate
  export rides the same cached solve).

## Deliverable

- [ADR 0015](../decisions/0015-forecast-lmp-selection.md) — accepted; execution
  stays on hold until the readiness gate is met per ISO.
- Selection appended to the status section of `../04-lmp-export.md`.
