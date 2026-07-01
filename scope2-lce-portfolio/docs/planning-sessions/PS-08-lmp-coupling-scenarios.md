# PS-08 — LMP Coupling & Scenario Selection

**Goal:** define the contract by which the market-sim BAU LMPs feed this tool, and
which scenario/vintage to use.

## Why it matters

The premium is measured against these LMPs, so *which* BAU run, year, and mode
(forecast vs backcast) we use materially changes results. The tool consumes an
LMP file (never `import market_sim`); this session fixes the export and selection.

## Questions to decide

1. **Which BAU case.** Forecast (2026–2050) or backcast year? Which scenario
   (gas-price path, carbon price)? A single year or a multi-year trajectory?
2. **Export contract.** Confirm the LMP file schema (`hour, iso, lmp`) and where
   the market-sim export writes it. Zone→ISO aggregation: LMP is per-ISO here, but
   the market sim is zonal — how are zonal LMPs collapsed to one ISO price
   (load-weighted average)? Document the reconciliation.
3. **Price escalation.** If matching a future year against a base-year LMP, apply
   an escalation? Or always use the LMP for the modeled year.
4. **Consistency.** Should the clean build feed back and change LMPs? (No — this
   tool is a price-taker by design; note the limitation.)
5. **Multiple ISOs / years.** Batch sweep spec.

## Inputs to review

- `cli.load_lmp`, `docs/02-data-inputs.md`, the market-sim results/export modules
  (read-only, for the export contract) — but **do not import** them.

## Deliverable

- ADR fixing the BAU case, the zonal→ISO LMP reconciliation, and escalation rule.
- An export contract note (what the upstream export must produce) for PP-01.
- Confirmation of the price-taker limitation in `docs/00-overview.md`.
