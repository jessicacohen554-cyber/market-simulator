# capacity-market-elcc (raw)

Published Effective Load Carrying Capability (or equivalent
capacity-accreditation) ratings per ISO, by resource class and — where an ISO
publishes a genuine marginal-ELCC study — installed-penetration level. Feeds
CR-3.1 (penetration-indexed accreditation curves).

## Layout

One subdirectory per ISO; each holds a single **unified CSV** named
`<iso>.csv` with exactly the canonical columns:

```
iso,resource_class,study_vintage,penetration_pct,penetration_unit,elcc_pct,elcc_type,source_doc,source_page
```

`scripts/curate_capacity_market_elcc.py` reads each subdir and writes the
clean partition `data/clean/capacity-market-elcc/<ISO>/…parquet`.

- `resource_class` ∈ {wind, solar, wind_offshore, hybrid_solar_storage,
  storage_2hr, storage_4hr, storage_6hr, storage_8hr, storage_10hr,
  storage_ldes, nuclear, coal, gas_cc, gas_ct, gas_ct_dual_fuel, diesel,
  oil_ct, steam, waste_to_energy, other}. The thermal buckets (nuclear
  through waste_to_energy) capture PJM's post-2025/26-CIFP-reform thermal
  ELCC class ratings — see `pjm/README.md`.
- `penetration_pct` / `penetration_unit` are populated only where the ISO
  publishes a genuine multi-point ELCC-vs-penetration curve (MISO is the
  strongest public example); left blank — never guessed — where the ISO
  publishes only a single current-fleet-average class rating (PJM, most
  others today). The per-ISO `README.md` states which shape landed.
- `elcc_type` ∈ {class_average, marginal, incremental}.
- Leave `elcc_pct` blank rather than guess; valueless rows are dropped at
  intake.

## Per-ISO status & sources

| ISO | subdir | construct | status |
|-----|--------|-----------|--------|
| PJM | `pjm/` | ELCC Class Ratings (annual, single point per class) | see `pjm/README.md` |
| NYISO | `nyiso/` | ICAP/UCAP conversion factors (CATF) | see `nyiso/README.md` |
| ISO-NE | `isone/` | seasonal-claimed-capability / ELCC-based accreditation | see `isone/README.md` |
| MISO | `miso/` | wind/solar marginal ELCC by penetration (Accreditation Reform) | see `miso/README.md` |
| CAISO | `caiso/` | NQC / CPUC-commissioned ELCC studies | see `caiso/README.md` |
| ERCOT | — | — | **excluded** (energy-only, no capacity market) |
