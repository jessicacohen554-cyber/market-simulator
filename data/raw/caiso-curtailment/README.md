# caiso-curtailment — raw

`productionandcurtailmentsdata_<year>.xlsx` (2023–2025) — CAISO's published
"Production and curtailments data" workbook (5-minute interval), issued
alongside the daily Renewables and Curtailments reports.

**Source:** <https://www.caiso.com/library/managing-oversupply>

**Regeneration:** `scripts/build_caiso_hsl.py` reads these workbooks and
combines them with EIA-930 CISO delivered generation to build
`data/raw/caiso-hsl/`. A year whose curtailment sheet does not reach
December is skipped rather than partially built.

Not used for the `generation` clean datatype — `scripts/curate_generation.py`
explicitly does not read this source (its curtailment buckets don't map onto
the canonical fuel vocabulary).

**Licensing note:** CAISO's redistribution terms are unclear/conditional —
see `docs/data-licensing.md` §6.

**Consumers:** `scripts/build_caiso_hsl.py`, `scripts/curate_renewables.py`,
`scripts/caiso_shape_probe.py`.
