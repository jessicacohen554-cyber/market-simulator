# caiso-curtailment — raw

`productionandcurtailmentsdata_<year>.xlsx` (2023–2025) — CAISO's published
"Production and curtailments data" workbook (5-minute interval), issued
alongside the daily Renewables and Curtailments reports.

**Source:** <https://www.caiso.com/library/production-curtailments-data>
(direct file pattern: `https://www.caiso.com/documents/productionandcurtailmentsdata_<year>.xlsx`
— the previously-cited `library/managing-oversupply` URL now 404s, corrected
2026-07-10). **CAISO discontinued this report as of 2025-06-01** (stated on
the library page itself: "As of 6/1/2025 the ISO is no longer publishing
this report. Curtailment data can be found in the daily renewables
reports."), so no 2026 workbook exists or ever will at this URL pattern —
confirmed by direct fetch, not just absence.

**2018–2022 (rule-22 holdout intake, 2026-07-10):** all five years verified
fetchable at the URL pattern above and committed here — full Jan1–Dec31
workbooks (30MB / 21MB / 22MB / 22MB / 23MB respectively), same
`Read_me`/`Production`/`Curtailments` sheet layout as 2023–2025. Committed
via a direct `git push` (a scoped exception to CLAUDE.md's API-only push
rule — this session's GitHub API tools cannot transport binary content
without corruption; see `data/raw/caiso-hsl/README.md` for the byte-level
evidence and the derived-series build outcome per year: 2019-2021 clean,
2018 flagged as an `eia_loader` artifact, 2022 genuinely unavailable).

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
