# 0011 — LMP coupling & scenario selection

- **Status:** accepted (stakeholder-decided 2026-07-01)
- **Date:** 2026-07-01
- **Session:** PS-08 (LMP Coupling & Scenario Selection)
- **Implemented by:** PP-01

## Context

The premium is measured against BAU LMPs, so which market-sim run (forecast vs
backcast), year, and scenario we use materially changes results. The tool
consumes an LMP file (never `import market_sim`); the export contract and
scenario selection must be explicit and reproducible.

## Options considered

1. **Forecast-year LMP** — use the calibrated market-sim forecast run for the
   modeled year; consistent with forward-looking portfolio design (chosen).
2. **Backcast validation** — backcast LMPs available for retrospective studies
   only; not the default.
3. **Escalated LMP** — apply forward cost escalation to a base-year LMP; rejected
   as it introduces an extra degree of freedom and obscures which year's market
   structure is being modeled.

## Decision

**Default BAU LMP series = the calibrated market-sim forecast run for the
modeled year** (single year, matching the portfolio study year). Backcast years
are usable for validation studies only. **Export contract:** CSV/Parquet with
columns (hour, iso, lmp) — one price per ISO-hour. Zonal→ISO reconciliation
happens on the market-sim side or in intake: load-weighted average of zonal LMPs
(weights = zonal hourly load). Reconciliation is documented, deterministic, and
reproducible. **No escalation** applied — always use the LMP vintage for the
modeled year. **Price-taker limitation:** the clean build does NOT feed back
into LMPs (known limitation, documented in README and outputs metadata).

## Consequences

- New loader in `cli.py` expects (hour, iso, lmp) CSV format from market-sim
  forecast export.
- Zone→ISO LMP averaging documented in data-inputs guide; validated on read.
- Backcast-LMP usage documented as diagnostic-only in outputs.
- Price-taker assumption noted in README and every result summary.
