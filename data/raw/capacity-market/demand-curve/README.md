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

## Forward-vintage backlog — MANUAL DOWNLOADS NEEDED (FF-G3, 2026-07-20)

The newest published forward vintages per ISO, researched for FF-G3
(`docs/capacity-price-forward-methodology-2026-07.md`) but **not yet encoded**:
the machine-readable sources are bot-walled in the build environment (standard
fetch empty; the report PDFs' net-CONE tables are images; the Planning-Parameters
XLSX / FERC eLibrary attachments return JS shells), and rule 13 forbids encoding
an unverified number. Each row needs a manual download on a non-bot-walled host,
a byte-verified intake through `curate_capacity_market_demand_curve.py`, and a
`MARKET_DESIGN_VINTAGES` entry with a `test_capacity_demand_curve.py`
reconciliation. `sha256` is pinned for the PDFs that WERE obtained so a
re-download can be verified byte-identical.

| ISO | delivery yr | metric | researched value | source (needs manual DL) | sha256 (if obtained) |
|-----|-----------|--------|------------------|--------------------------|----------------------|
| PJM | 2028/2029 | net-CONE RTO (UCAP) | 325.69 $/MW-day (=118.88 $/kW-yr); Gross ICAP 223,800; E&AS 129,887 $/MW-yr; collar cap/floor 325.00/175.00 (ER26-1556) | 2028/2029 RPM BRA Planning Period Parameters (posted 2026-04-29) `.../rpm-auction-info/2028-2029/2028-2029-bra-report.pdf` (net-CONE Table 3 is an IMAGE) + the Planning-Parameters XLSX (VRR point a/b/c; the 2028/29 VRR equation changed) | report PDF `ee5375b6e26a09b11fc41d1122b546c358a3d24645faa178682bc11305b641aa` |
| NYISO | 2026-2027 | NYCA Annual Reference Value | NOT RETRIEVED (annual-update sheet posted ~Nov 2025; document-library URL not locatable) | nyiso.com → ICAP Market → Reference Documents → "Demand Curve Reset Annual Updates" 2025 folder | — |
| MISO | PY2026-2027 | per-LRZ Net CONE + seasonal RBDC points | N/C aggregate ≈ 81.0 $/kW-yr (South ≈ 76.1); per-LRZ Net CONE in Attachment C | FERC eLibrary ER26-139-000 (filed 2025-10-15) Attachment C; RASC/BPM-011 RBDC posting | — |
| ISO-NE | 2028-2029 | FCA 19 Net CONE (**regime-superseded**) | 9.614 $/kW-mo (=115.37 $/kW-yr); Gross 14.759 @ 8.96% ATWACC | Nov-2023 MOPR-elimination filing (`adj_to_certain_fcm_parameters...pdf`); FCM terminating → prompt/seasonal successor (CAR-PD ER26-925 accepted 2026-03-30; CAR-SA params unpublished) | MOPR filing `7a69dd08f8cfa7345faee79a8847db96fff8a6b2f8572ec3d705bcffc4ecd16e` |
