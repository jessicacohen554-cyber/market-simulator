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

## Annual bc_HIST source mirrors (miso-76 A2(ii) — gitignored bulk)

`YYYY_<market>_bc_HIST.csv.gz` — verbatim gzip mirrors of MISO's annual
consolidated binding-constraints histories (ALL binding transmission
constraints: constraint name with embedded From/To control areas, interval,
preliminary shadow price, TCDC breakpoints — but **no MW limit and no
flow**), fetched by `scripts/data/fetch_miso_bc_hist.py` from

    https://docs.misoenergy.org/marketreports/YYYY_{da,rt}_bc_HIST.csv

These are the source mirrors behind the miso-76 congestion VALIDATION
layer (charter `docs/handoffs/miso-nc-price-separation-design-2026-07.md`
§2a/§7 A2(ii); first consumer `scripts/probes/_miso76_bc_boundary_rank.py`).
Rule 13: shadow prices are the ANSWER class — this record locates and
ranks measured congestion for validation only, NEVER an LP or derive
input, and it deliberately gets **no clean-datatype extension** (this
directory's curated `transfer-constraint-binding` schema stays
RDT-specific; validation consumers read the mirrors directly).

The mirrors are **gitignored** (~20-70 MB raw each; precedent
`data/raw/caiso-public-bids`) — the fetch script is the reproducibility
path. Verbatim-payload provenance (fetched 2026-07-19):

| file | raw bytes | lines | sha256 |
|---|---|---|---|
| 2023_da_bc_HIST.csv | 23,639,453 | 149,545 | 0bfded5a1af2a962a014b174f52f549ec544b3be67a8d595a2c4eaa6b04eca11 |
| 2023_rt_bc_HIST.csv | 69,220,611 | 408,201 | 518d0cb85cfa5149d9a95e0aa575d4601752af20216de208c0e3501eb31ae63e |
| 2024_da_bc_HIST.csv | 22,802,444 | 144,702 | 24cd84309aded690863d9e8fe3735edcab5d9078d5b8808ff7e321d3f7e42248 |
| 2024_rt_bc_HIST.csv | 70,321,121 | 421,108 | b65dea36c6d44ea29eaad372ec1a04c25330e9523653b6a229a8c4a5d8279ed9 |
| 2025_da_bc_HIST.csv | 19,454,384 | 122,036 | 201b3578ebf7d93b4a390fd8b78f97eb47271e4242dc7bf4677bba820443db40 |
| 2025_rt_bc_HIST.csv | 65,534,098 | 398,962 | aa13c2007deee7243b7c93921a078e9796b879a56274fd664ccb0d9dfa166586 |

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
