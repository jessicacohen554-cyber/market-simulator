# MISO capacity-market-elcc (wind/solar marginal ELCC by penetration)

Drop the retrieved unified CSV here as **`miso.csv`**. MISO is the strongest
public candidate for a genuine multi-point ELCC-vs-penetration curve — try
hard to capture several `penetration_pct` points per `resource_class`, not
just the current single accreditation percentage. Note per-zone coverage here
if MISO publishes zonal curves (record the zone in `source_page`).

## Authoritative sources

- MISO Resource Adequacy Subcommittee (RASC) wind/solar capacity-credit and
  Accreditation Reform materials: https://www.misoenergy.org/committees/
  (search "RASC" and "Accreditation Reform")

**STATUS:** `miso.csv` committed — MISO is confirmed the strongest public
penetration-curve source: a 15-year historical wind ELCC-vs-penetration series
(2005-2019, both raw annual marginal ELCC and the smoothed/adopted "MISO
Capacity Credit" class-average, by % of peak load) from the 2019 Wind & Solar
Capacity Credit Report, plus current seasonal wind ELCC at fixed installed MW
for PY2023-24 and PY2025-26. Solar has no probabilistic ELCC curve at MISO —
only flat seasonal defaults (50% non-winter / 5% winter) for resources with
&lt;30 days of metered data. No MISO storage-ELCC-by-duration report was
located in this pass. See `docs/handoffs/capacity-market-intake-2026-07.md`.
