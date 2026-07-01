# PP-06 — Outputs & Reporting

**Upstream:** PS-02 (premium reporting), PS-04 (carbon).
**Targets:** `src/lce_portfolio/outputs.py`.
**Status:** done (frontier + build-mix Parquet, text summary).

## Build / deepen

1. **Premium reporting (PS-02).** Add columns decided in PS-02: total $/yr, %
   over BAU, surplus MWh and surplus revenue, avoided grid purchases.
2. **Carbon (PS-04).** If adopted, add residual tCO₂ and residual emissions rate
   per setpoint.
3. **Operational detail.** Optional per-hour dispatch export (gen by resource,
   storage SOC, grid_buy, excess) for a chosen setpoint — one Parquet, list-valued
   columns like the market-sim results (mirrored, not imported).
4. **Frontier plot.** A small matplotlib/plotly export of matching%-vs-premium and
   the build-mix stack (optional; keep plotting deps optional).
5. **Provenance.** Write a run-metadata JSON (config, table hash, solver status)
   alongside outputs for reproducibility.

## Acceptance

`test_outputs` round-trips the Parquet writers, checks column presence/schema, and
verifies `summarize` renders; new metric columns covered where added.
