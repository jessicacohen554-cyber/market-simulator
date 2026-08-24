# MISO regional (North/Central/South) hourly load & generation

The miso-183 South-seam measurement-basis substrate: the only public
sources found that resolve MISO's two non-contiguous footprints (Midwest =
North+Central; South = the post-2013 Entergy-footprint subregion) at hourly
grain. Diagnostic/validation corpus — **never an LP or derive input**
(rule 13 `[R-MEASURED]`: subregional actuals are the answer class for the
basis question; they enter no solve).

## Sources

Public daily market reports, no auth (fetched 2026-08-24 by
`scripts/data/fetch_miso_regional_balance.py`):

    https://docs.misoenergy.org/marketreports/YYYYMMDD_rf_al.xls
    https://docs.misoenergy.org/marketreports/YYYYMMDD_sr_gfm.xlsx

* `rf_al` — "Forecasted and Actual Load Report": hourly MTLF + actual load
  (MWh) for North / Central / South / MISO. Publish-day file carries market
  days publish−1 (complete) and publish (partial); market day D is
  consolidated from the publish D+1 file (fallback D+2..D+4).
* `sr_gfm` — "Real-Time State Estimator Generation Fuel Mix Report", sheet
  "RT Generation Fuel Mix": hourly generation MW by fuel
  (Coal/Gas/Nuclear/Hydro/Wind/Solar/Other/Storage + Total) for
  Central / North / South, plus the MISO Total block. Market date =
  publish − 1 exactly. (The workbook's second sheet, DA Cleared Generation
  Fuel Mix, is deliberately not consolidated — the RT State Estimator sheet
  is the physical-actuals record the basis question needs.)

Hour labels are Market Hour ENDING 1..24, **EST year-round, no DST** (MISO
market time; same convention verified over the full pbc archive —
`data/raw/transfer-constraint-binding/MISO/README.md`). Every market day
has exactly 24 rows.

## Files

    miso_regional_load_<year>.csv.gz    market_date, he_est, region, mtlf_mw, actual_mw
    miso_regional_genmix_<year>.csv.gz  market_date, he_est, region, fuel, mw

Unlike the pbc mirror next door, the sources are binary xls/xlsx, so these
are **deterministic PARSED extractions, not byte mirrors** — the daily
files under `_daily/` (gitignored, ~2,190 files / ~60 MB) are the staged
provenance and the fetch script is the reproducibility path. Region block
positions and fuel columns are read from each file's own header rows (the
South block layout drifts by one column across years; South carries no
Storage column in some vintages — absent columns are simply absent, never
zero-filled).

## Quarantine (CLAUDE.md rule 22)

Consolidated files cover market dates 2023-01-01..2025-12-31 ONLY (the
train window). The fetch script refuses out-of-train years without
`--allow-out-of-train` + session-logged owner authorization; publish-window
edge files (e.g. the 2026-01-01 publish carrying 2025-12-31) are fetched
but only in-window market dates are consolidated.

## Interpretation cautions

- `sr_gfm` is the **RT State Estimator** view (telemetered gen assigned to
  reporting regions by MISO); `rf_al` actual load is the settlement-grade
  regional load actual. The L−G identity across them carries a wedge
  (losses, behind-meter treatment, SE vs settlement basis) — miso-183
  calibrates that wedge at whole-MISO against the measured EIA-930 net
  interchange and carries it as an uncertainty band, never apportioned.
- Neither report carries the RDT flow itself. The aggregate Midwest↔South
  RDT flow series remains unpublished (RT Data Broker RDT endpoint
  deprecated — re-verified dead 2026-08-24, returns `{"error": "no data"}`;
  Data Exchange key-gated; no market report carries it under any probed
  name) — see FINDING-miso183 §2 for the full hunt record.
- No clean-datatype extension (the transfer-constraint-binding precedent):
  diagnostic consumers read these files directly.
