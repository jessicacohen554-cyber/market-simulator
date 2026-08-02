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

## Forward-vintage backlog — status after the FFR-2C re-anchor (2026-08-02)

**Two of the four rows below are CLOSED.** The bot-wall FF-G3 hit on 2026-07-20
was not permanent: the PJM Planning-Parameters XLSX and the NYISO
document-library posting are both retrievable from this environment now, so
those two vintages are intaken from their machine-readable primary sources and
encoded in `MARKET_DESIGN_VINTAGES` with reconciliation tests
(`tests/unit/model/test_capacity_demand_curve.py`). The other two are **not**
data-retrieval failures — they are genuine publication states, and both are
owner decisions rather than intake work:

| ISO | delivery yr | status | detail |
|-----|-----------|--------|--------|
| PJM | 2028/2029 | **CLOSED 2026-08-02** | Net CONE 325.69 $/MW-day UCAP (= 118.877 $/kW-yr), +34.3 % over 2027/2028. Gross UCAP 776.14, forward net E&AS UCAP 450.448; IRM 20.0 %, FPR 0.9401; four collared VRR points under FERC ER26-1556 (cap/floor 325.00/175.00 UCAP). New gross-CONE basis: ER26-455, approved 2026-01-21. Workbook committed locally (`pjm/pjm-2028-2029-planning-parameters.xlsx`, sha256 `b1863615…7ca09`); the narrative report re-downloaded byte-identical to FF-G3's pinned `ee5375b6…b641aa`. See `pjm/README.md`. |
| NYISO | 2026-2027 | **CLOSED 2026-08-02** | NYCA Annual Reference Value 57.70 $/kW-Year (+14.1 % over 50.55); Gross CONE 131.94, Net EAS Revenues 74.24; summer reference point 6.53 / max clearing 22.41 $/kW-Month; Demand Curve Length 12 % (unchanged). Source: "Demand Curve Parameters CY 2026-2027" (sha256 `713560dc…207cc`), linked from the nyiso.com Installed Capacity Market page — FF-G3's "URL not locatable" is resolved. See `nyiso/README.md`. |
| MISO | PY2026-2027 | **OPEN — partly published, deliberately NOT encoded** | See the MISO note below. The per-LRZ Net CONE **is** on disk (ER26-139-000 Attachment C, intaken 2026-07-15); what is missing is the PY2026-27 **seasonal RBDC**, and encoding an annual-only vintage would silently drop MISO from its seasonal grain. |
| ISO-NE | 2028-2029 | **OPEN — no newer vintage EXISTS (not a retrieval failure)** | FCA 18 (2027/2028, on disk) remains the last forward auction ever held. FCA 19 is delayed to February 2028 and the FCM is being replaced by the prompt/seasonal design: CAR-PD accepted by FERC 2026-03-30 (ER26-925), CAR-SA expected Q4 2026 with its parameters still unpublished. The FCA-19 paper Net CONE (9.614 $/kW-mo = 115.37 $/kW-yr, from the Nov-2023 MOPR-elimination filing, sha256 `7a69dd08…cd16e`) clears no auction. How to represent ISO-NE past 2027/2028 is **owner decision FF-G3 D4**, not an intake. |

### MISO PY2026-2027 — what is proven, and the one thing that blocks it

The FF-G3 backlog row estimated an "N/C aggregate ≈ 81.0 $/kW-yr". That estimate
is now **proven exactly**, from published values only, by two independent checks —
recorded here so a later session does not redo the work:

1. **MISO's North/Central aggregation IS the LRZ 1–7 arithmetic mean.** On
   PY2025-26, mean(LRZ 1–7 gross CONE) = 127,361.43 $/MW-yr, and MISO's own
   published North/Central *seasonal* CONE annualizes to
   1384.36 $/MW-day × 92 days = 127,361.1 — agreement to 0.0003 %.
2. **The E&AS offset is a single per-Planning-Area value, exactly as the tariff
   says.** ER26-139-000 (filed 2025-10-15) describes Net CONE as the LRZ-specific
   CONE minus one *Planning-Area* Inframarginal Rent. The on-disk PY2026-27 rows
   prove it arithmetically: gross − net is **identical at 52,735 $/MW-yr for every
   one of LRZ 1–7** (First Planning Area) and **47,938 for LRZ 8/9/10** (Second).

Together those give North/Central Net CONE for PY2026-27 =
mean(LRZ 1–7 gross) 133,767.14 − 52,735 = **81,032.14 $/MW-yr = 81.03 $/kW-yr**,
+1.5 % over the held PY2025-26 anchor of 79.8 — a **derivation from published
values on MISO's own construction, not an interpolation**.

**Why it is still not encoded.** The shipped MISO vintage carries the seasonal
RBDC (`seasonal_rbdc=MISO_SEASONAL_RBDC`) and the pricing seam evaluates the
seasonal grain — the market's own Σ ACP_season × days settlement. A PY2026-27
vintage carrying only an annual anchor would silently drop MISO back to the
annual approximation the RC-1C seasonal work replaced: a **fidelity regression
bought for a +1.5 % level correction**. The PY2026-27 seasonal RBDC parameters
live in the PRA Results Posting
(`cdn.misoenergy.org/2026 PRA Results Posting 20260428754715.pdf`), which returns
**S3 `AccessDenied`** from this environment while the 2023/2024/2025 postings on
the same CDN return 200 — so it is that one object's ACL, not a general block.
The seasonal caps could be *reconstructed* from the days-identity
(seasonal_gross_daily × days = annual gross CONE, which reproduces PY2025-26
exactly), but that would be inventing published numbers for a table whose shape
may have changed — refused under rule 13. **Blocked on one document, and the
whole stake is 1.5 %.**

