# capacity-market-demand-curve (raw)

Published net-CONE, IRM, price-cap, and sloped-demand-curve points for each
capacity-market ISO's current planning parameters. See the schema header
(`data/dictionary/schema/capacity-market-demand-curve.schema.yaml`) for the
full native-parameter -> canonical-metric map per ISO.

## Layout

One subdirectory per ISO; each holds a single **unified CSV** named
`<iso>.csv` with exactly the canonical columns:

```
iso,delivery_year,area,season,metric,point_index,x_value,x_unit,y_value,y_unit,vintage,source_doc,source_page
```

`scripts/curate_capacity_market_demand_curve.py` reads each subdir and writes
the clean partition `data/clean/capacity-market-demand-curve/<ISO>/…parquet`.

- `metric` ∈ {net_cone, irm, price_cap, curve_point, soft_offer_cap,
  ra_report_price}.
- `point_index` populated (0, 1, 2, ...) only for `metric=curve_point` rows,
  left-to-right along the curve; blank for scalar metrics.
- `x_unit` ∈ {pct_of_requirement, mw, pct_of_irm}; `y_unit` ∈
  {usd_per_mw_day, usd_per_mw_yr, usd_per_kw_month, usd_per_kw_yr, pct,
  multiple_of_net_cone}.
- `area` is blank for ISOs publishing one RTO/system-wide curve (PJM, ISO-NE,
  CAISO); populated for ISOs publishing locality/zonal curves (NYISO
  NYCA/NYC/LI/G-J, MISO LRZ).
- `season` is blank except for MISO's seasonal (summer/fall/winter/spring)
  reliability-based demand curve (PY2025-26+).
- Leave a value cell blank rather than guess an unpublished number; valueless
  rows are dropped at intake.

## Per-ISO status & sources

| ISO | subdir | curve construct | status |
|-----|--------|------------------|--------|
| PJM | `pjm/` | VRR curve + Net CONE + IRM | see `pjm/README.md` |
| NYISO | `nyiso/` | ICAP Demand Curve (per locality) | see `nyiso/README.md` |
| ISO-NE | `isone/` | FCA demand curve + Net CONE + MRI | see `isone/README.md` |
| MISO | `miso/` | seasonal PRA reliability-based demand curve + seasonal CONE | see `miso/README.md` |
| CAISO | `caiso/` | no curve — CPM soft-offer cap + CPUC RA report price (documented proxy) | see `caiso/README.md` |
| ERCOT | — | — | **excluded** (energy-only, no capacity market) |
