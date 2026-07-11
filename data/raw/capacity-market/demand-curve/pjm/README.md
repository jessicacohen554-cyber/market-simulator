# PJM capacity-market-demand-curve (VRR curve, Net CONE, IRM)

Drop the retrieved unified CSV here as **`pjm.csv`** (canonical columns; see
the parent `README.md`). One curve per delivery year (no locality split — the
VRR curve is RTO-wide).

- **metric:** `net_cone`, `irm`, `price_cap`, `curve_point` (or native alias
  `vrr_point`).
- **delivery_year:** planning-year label, e.g. "2026/2027".
- **y_unit:** PJM publishes Net CONE and curve prices in $/MW-day.

## Authoritative sources

RPM Base Residual Auction "Planning Period Parameters" filings (PDF + detailed
XLSX workbook) carry Net CONE, IRM, and the VRR curve's defining points.

- 2025/2026 params: https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2025-2026/2025-2026-planning-period-parameters-for-base-residual-auction-pdf.pdf
- 2026/2027 params: https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2026-2027/2026-2027-planning-period-parameters-for-base-residual-auction-pdf.pdf
- PJM Markets & Operations "Capacity Market (RPM)" hub (VRR curve figures):
  https://www.pjm.com/markets-and-operations/rpm

**STATUS:** `pjm.csv` committed — Net CONE ($/MW-day + $/MW-yr), IRM, price cap/floor (ICAP + UCAP basis), and Manual 18 formula curve points for delivery years 2025/2026–2027/2028, from the RPM BRA Planning Period Parameters filings + PJM Manual 18 Rev. 62. VRR curve prices at points (a)/(b) and (1)/(2) are formula-defined by PJM (not published as standalone numbers) — recorded with x_value only, y_value left null per the no-guessing rule; the zero-price point is populated. See `docs/handoffs/capacity-market-intake-2026-07.md` for gaps.
