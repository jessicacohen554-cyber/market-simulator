# PJM capacity-deliverability (CETO / CETL by LDA)

Drop the retrieved unified CSV here as **`pjm.csv`** (canonical columns; see the
parent `README.md`). Native metric labels `ceto`/`cetl` are accepted and mapped
to `requirement`/`import_limit` by `scripts/lib/capacity_deliverability/pjm.py`.

- **area_type:** `lda` (RTO-level rows use `rto`).
- **delivery_year:** planning-year label, "2025/2026" (June 1 – May 31).
- **areas:** MAAC, EMAAC, SWMAAC, PSEG, PS-NORTH, DPL-SOUTH, PEPCO, ATSI,
  ATSI-Cleveland, COMED, BGE, PL, DAY, DOM, DEOK (+ any others a year lists),
  plus RTO.

## Authoritative sources

RPM Base Residual Auction "Planning Period Parameters" PDFs carry the full
CETO/CETL-by-LDA tables; BRA Reports and the CETO/CETL DESTF deck cross-check.

- 2025/2026 params: https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2025-2026/2025-2026-planning-period-parameters-for-base-residual-auction-pdf.pdf
- 2026/2027 params: https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2026-2027/2026-2027-planning-period-parameters-for-base-residual-auction-pdf.pdf
- 2027/2028 params: https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2027-2028/2027-2028-planning-period-parameters-for-base-residual-auction-pdf.pdf
- 2024/2025 BRA report: https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2024-2025/2024-2025-base-residual-auction-report.ashx
- CETO/CETL & Load Deliverability (methodology): https://www.pjm.com/-/media/DotCom/committees-groups/task-forces/destf/2024/20240819/20240819-item-04---ceto-cetl-and-load-deliverability-test.pdf

Required years (backcast): 2023/2024, 2024/2025, 2025/2026. Nice-to-have
(forecast): 2026/2027, 2027/2028.

**STATUS:** `pjm.csv` committed — DY 2023/24–2027/28, 155 rows (80 `requirement`
+ 75 `import_limit`). `ceto`/`cetl` given as canonical `requirement`/`import_limit`.

## Provenance & method

CETO/CETL taken from PJM's **detailed planning-parameters spreadsheets** (each
year's `…planning-parameters….xlsx`, sheet "Planning Parameters", table "LDA
CETO/CETL Data…"), which carry the true CETO — distinct from the PDFs' published
*Reliability Requirement* (`Reliability Requirement = CETO + Internal UCAP`, per
the DESTF deck). Every modeled-LDA CETL was cross-checked against the Planning
Period Parameters PDF Table 2 and matches to the MW for 2023/24–2026/27. `xlsx`
URLs by year:

- 2023/24: `.../2023-2024/2023-2024-planning-period-parameters-for-base-residual-auction.xlsx`
- 2024/25: `.../2024-2025/2024-2025-rpm-bra-planning-parameters.xlsx`
- 2025/26: `.../2025-2026/2025-2026-planning-period-parameters-for-base-residual-auction.xlsx`
- 2026/27: `.../2026-2027/2026-2027-planning-period-parameters-for-base-residual-auction.xlsx`
- 2027/28: `.../2027-2028/2027-2028-planning-period-parameters-for-base-residual-auction.xlsx`

## Caveats (do not silently "fix")

- **Blank/omitted CETL (import_limit) rows** for DOM (2023/24, 2024/25) and JCPL
  (2023/24, 2024/25, 2025/26): PJM published CETL there only as a lower bound
  (LDA not import-constrained / not separately modeled), not a clean number —
  DOM ">989.0" then ">3,231.5"; JCPL ">3,496.0", ">3,530.5", ">4,345.9". Omitted
  per "don't guess"; the CETO (`requirement`) rows are exact. DOM becomes a
  modeled LDA from 2025/26, JCPL from 2026/27.
- **2027/28 MAAC/SWMAAC/DOM CETL are the 11/4/2025 revision** (Chanceford–Doubs
  500 kV line removed): MAAC 3013→2598, SWMAAC 7319→6698, DOM 6441→6598. The CSV
  carries the revised values, so the original-PDF YoY narrative (MAAC +298, DOM
  −933 vs 2026/27) no longer holds against them (revised: MAAC −117, DOM −776) —
  a real revision, not a transcription error. `source_page` flags these rows.
- **DPL-SOUTH 2024/25 = 2009** from the year-of-record 2024/25 workbook; the
  2025/26 PDF comparison column restates it as 1962 (47 MW lower).
- **MAAC 2024/25 & 2025/26 CETL** (5965, 3222) come from the workbook summary
  block; the detailed table shows "*" (adequate internal resources). Both match
  PDF Table 2.
- **RTO rows** carry no CETO/CETL (construct is sub-RTO) → not emitted.
