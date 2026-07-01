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

**DATA NEEDED:** `pjm.csv` not yet committed.
