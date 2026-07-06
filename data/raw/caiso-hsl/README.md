# caiso-hsl — raw

`caiso_<year>_hsl_hourly.parquet` (2023–2025) — CAISO's "uncurtailed
potential" (HSL) series: **derived**, not a raw download.

`HSL = EIA-930 CISO delivered wind/solar generation + reported curtailment`
(from `data/raw/caiso-curtailment/`).

**Regeneration:** `python scripts/build_caiso_hsl.py` (see
`data/raw/caiso-curtailment/README.md` for its input). Matches the
`renewables._HSL_COLUMNS` schema.

**Consumer:** `scripts/curate_renewables.py` (`market_sim.data.renewables`
reads this in preference to the CAMPD-derived proxy when present).
