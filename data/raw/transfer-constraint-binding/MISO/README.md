# MISO transfer-constraint binding record (RDT / sub-regional PBC)

Measured binding record for MISO's Regional Directional Transfer (RDT)
constraint — the ONLY public series for when/how hard the RDT bound.

## Source

Public daily market reports, no auth (fetched 2026-07-12):

    https://docs.misoenergy.org/marketreports/YYYYMMDD_da_pbc.csv
    https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_pbc.csv

"Day-Ahead / Real-Time Binding Sub-Regional Power Balance Constraints".
Filename date is the PUBLISH date (DA carries market date publish+1; RT
carries publish-1). Rows exist ONLY for intervals where a constraint
carried a nonzero preliminary shadow price — no row means "did not bind".
DA rows are hour-beginning EST (labels 00-23, verified over the full
archive); RT rows are 5-minute interval starts, EST (MISO market time is
EST year-round, no DST — the column is literally `MARKET_HOUR_EST`).

## Files

`miso_pbc_<market>_<year>.csv.gz` — verbatim source rows (deduplicated,
timestamp-sorted, market-date-year selected), one file per market run and
market-date year, produced by `scripts/fetch_miso_pbc.py`. Layout is the
posted 14-column CSV:

    MARKET_HOUR_EST, CONSTRAINT_NAME, PRELIMINARY_SHADOW_PRICE, CURVETYPE,
    BP1, PC1, BP2, PC2, BP3, PC3, BP4, PC4, OVERRIDE, REASON

Constraint names observed: `RDT_SO_MW (South_North)` and
`RDT_MW_SO (North_South)`. CURVETYPE is PERCENT — breakpoints are % of the
MODELED (operator-derated) limit, which is NOT published (the limit-MW
series remains unavailable: RT Data Broker RDT endpoint deprecated without
archive; Data Exchange key-gated; adjudicated 2026-07-11 and re-verified
2026-07-12). The live curve is constant across 2023-2025:
100%→$40, 102%→$500, 200%→$500 (DA adds a 999999 sentinel BP4) — the
published RDT TCDC (2024 MISO SOM §III.B). Exception: 3 RT rows in 2023
carry OVERRIDE=1 with a $3,000 emergency curve variant.

## Quarantine (CLAUDE.md rule 22)

Consolidated files cover market dates 2023-01-01..2025-12-31 ONLY (the
train window). The fetch script refuses out-of-train years without
`--allow-out-of-train` + session-logged owner authorization; edge
publish-window rows (e.g. the 2026-01-01 market date inside the RT file
published 2026-01-02) are dropped.

## Interpretation cautions

- The posted shadow price is the pbc constraint's OWN dual, capped by its
  demand-curve step ($40 while flow is in (100%,102%] of the modeled
  limit). The Reserve Procurement Enhancement (RPE) constraint's additive
  $200 lands on the subregional price SEPARATION, not on this dual, and
  the RPE has NO public binding record (2024 SOM §II.E/§III.B).
- The SOM's "RDT bound in more than one quarter of RT intervals" (2024)
  describes the RDT+RPE constraint FAMILY (IMM Summer-2025 quarterly p.29
  splits "Tx Only" / "Both Binding" / "RPE Only"); this file's RDT-proper
  RT record is ~7.5% of 2024 intervals. Same-basis comparisons only.

DATA NEEDED: hourly modeled-limit (derate) MW series — not published; the
IMM's derate-behavior chart (Summer-2025 quarterly p.30) is chart-only.
