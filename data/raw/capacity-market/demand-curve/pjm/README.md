# PJM capacity-market-demand-curve (VRR curve, Net CONE, IRM)

Drop the retrieved unified CSV here as **`pjm.csv`** (canonical columns; see
the parent `README.md`). One curve per delivery year (no locality split — the
VRR curve is RTO-wide).

- **metric:** `net_cone`, `irm`, `forecast_pool_requirement`, `price_cap`,
  `price_floor`, `curve_point` (or native alias `vrr_point`).
- **delivery_year:** planning-year label, e.g. "2026/2027".
- **y_unit:** PJM publishes Net CONE and curve prices in $/MW-day (Net CONE
  also in $/MW-yr, ICAP basis, in every vintage committed so far).

## Authoritative sources

RPM Base Residual Auction "Planning Period Parameters" filings (narrative PDF
+ a companion "Planning Parameters" XLSX workbook) carry Net CONE, IRM, FPR,
and the VRR curve's defining points.

- 2021/2022 params (PDF): https://learn.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2021-2022/2021-2022-rpm-bra-planning-parameters-report.ashx
- 2021/2022 params (XLSX): https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2021-2022/2021-2022-bra-planning-period-parameters.xlsx
- 2022/2023 params (PDF): https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2022-2023/2022-2023-planning-period-parameters-for-base-residual-auction-pdf.pdf
- 2022/2023 params (XLSX): https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2022-2023/2022-2023-planning-period-parameters-for-base-residual-auction.xlsx
- 2023/2024 params (PDF): https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2023-2024/2023-2024-planning-period-parameters-for-base-residual-auction-pdf.pdf
- 2023/2024 params (XLSX): https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2023-2024/2023-2024-planning-period-parameters-for-base-residual-auction.xlsx
- 2024/2025 params (XLSX only — see STATUS): https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2024-2025/2024-2025-rpm-bra-planning-parameters.xlsx
- 2025/2026 params: https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2025-2026/2025-2026-planning-period-parameters-for-base-residual-auction-pdf.pdf
- 2026/2027 params: https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2026-2027/2026-2027-planning-period-parameters-for-base-residual-auction-pdf.pdf
- PJM Markets & Operations "Capacity Market (RPM)" hub (VRR curve figures):
  https://www.pjm.com/markets-and-operations/rpm

**STATUS:** `pjm.csv` committed — Net CONE ($/MW-day + $/MW-yr), IRM, price cap/floor (ICAP + UCAP basis), and Manual 18 formula curve points for delivery years 2025/2026–2027/2028, from the RPM BRA Planning Period Parameters filings + PJM Manual 18 Rev. 62. VRR curve prices at points (a)/(b) and (1)/(2) are formula-defined by PJM (not published as standalone numbers) — recorded with x_value only, y_value left null per the no-guessing rule; the zero-price point is populated.

**2026-07-15 addition — the four pre-CIFP vintages (2021/2022, 2022/2023, 2023/2024, 2024/2025), 28 rows.** Net CONE (ICAP $/MW-Year *and* UCAP $/MW-Day, both directly published — same dual-basis PJM has used since at least 2021/2022, not a post-2025/26 invention), IRM, FPR, and all three VRR curve points, from each year's own Planning Period Parameters PDF (2021/2022–2023/2024) and/or its companion "Planning Parameters" XLSX workbook (all four years; 2024/2025's XLSX is the sole source — see below). 2024/2025's Net CONE is published only in $/MW-Day terms for *both* ICAP and UCAP bases (no $/MW-Year figure exists for that vintage); the ICAP-basis row reuses the `usd_per_mw_day_icap` unit (originally scoped to price_cap/price_floor) since that is the correct physical unit, not `usd_per_mw_yr`.

Findings on the two open questions this addition was scoped to resolve:

- **FPR basis vocabulary.** PJM published a "Forecast Pool Requirement (FPR)" by that exact name in all four pre-reform years — the *concept* is not new. What changed at the CIFP/capacity-accreditation reform is the *formula*: pre-reform, `FPR = (1 + IRM) x (1 - Pool-Wide 5-Year Average EFORd)` (an outage-rate derate), giving FPR **> 1** (1.0868–1.0901 across these four years) because the EFORd derate is small relative to the IRM add-on. Post-CIFP (2025/2026 on), `FPR = (1 + IRM) x Reference-Resource-Accredited-UCAP-Factor` (an ELCC/risk-based accreditation factor), giving FPR **well under 1** (0.917–0.938). Both eras' FPR is dimensionally the same ratio (UCAP-MW reliability requirement ÷ ICAP-MW forecast peak load — matches the schema's `fraction_of_peak_ucap` description exactly in both cases), so both are recorded under the same `forecast_pool_requirement` metric/unit; the >1-to-<1 flip across the reform boundary is itself a citable, striking magnitude marker of how much the accreditation reform tightened effective capacity credit. No row was omitted for any of the four years — PJM's own filings gave a clean FPR figure in every case.
- **Price cap / price floor.** None of the four pre-reform vintages had a separately-published price cap or price floor — confirmed both negatively (no "cap"/"floor" terminology anywhere in any of the four years' PDF or XLSX text) and affirmatively via a PJM/Monitoring-Analytics-reported quote: "For the first time since the introduction of the RPM capacity market design, the 2026/2027 BRA used a VRR curve with both a defined maximum price and a defined minimum price. The VRR curve has always had a maximum price but never a minimum price greater than zero." The explicit price-collar mechanism (FERC Docket ER25-1357, a PJM/Pennsylvania-Governor's-Office settlement) is scoped to 2026/2027 and 2027/2028 only and was **not** applied to 2025/2026 either — matching this repo's own already-committed data, which likewise carries no price_cap/price_floor row for 2025/2026. No price_cap/price_floor rows were added for any of the four new vintages.

A third, unprompted finding: **pre-reform VRR curve points were published as literal (level-MW, price-$/day) pairs directly in each year's Planning Parameters XLSX** ("Point (a)/(b)/(c) UCAP Price, $/MW-Day" and "... UCAP Level, MW" rows) — unlike the post-CIFP curve (2025/2026+), which is formula-defined with only the x-position public (see the existing STATUS paragraph above). So the four new vintages' `curve_point` rows carry real, non-null `y_value` throughout, with `x_unit=mw` (an absolute reserve level, as PJM itself published it) rather than `pct_of_requirement`. Net CONE's ICAP/UCAP dual-basis publication (Table 3 of each PDF, mirrored in each XLSX's "Net CONE" sheet) is also present in every one of these four years, not just 2025/2026+.

2024/2025 is a compressed-schedule vintage (BRA held ~17 months, not the usual 3 years, before the delivery year, and later re-executed per FERC Docket ER23-729-002) — no standalone narrative "Planning Period Parameters" PDF report was located for it (direct URL guesses at the standard `<year>-planning-period-parameters-for-base-residual-auction-pdf.{pdf,ashx}` pattern both 404, and the PJM RPM auction-info hub page links only the XLSX for this vintage), so all 2024/2025 rows cite the XLSX workbook alone.

See `docs/handoffs/capacity-market-intake-2026-07.md` for the original (2025/2026–2027/2028) gaps, and the intake session report (2026-07-15) for this addition's manual-download list.

**2026-07-16 addition (RC-1A) — requirement/EE rows + the 2025/2026 published point prices, 18 rows + the five source workbooks committed alongside this README.** For each of 2021/2022–2025/2026: `reliability_requirement` (RTO, UCAP MW), `reliability_requirement_frr_adj` (adjusted for FRR — the RPM-market requirement the VRR curve is drawn against), and `ee_addback` (UCAP MW), all from the same Planning Period Parameters workbooks already cited above (local copies `pjm-<year>-planning-parameters.xlsx`). Finding: the VRR point UCAP MW levels divided by **(Reliability Requirement adjusted for FRR + EE Addback)** reproduce PJM's own Manual-18 `pct_of_requirement` fractions to ≤0.1 % in every vintage (verified against the committed 2025/2026 pct rows: 0.98912/1.01583/1.06726 vs 0.989/1.016/1.068) — so the pre-CIFP vintages' normalized curve shapes are now derivable from purely published rows (consumed by `MARKET_DESIGN_VINTAGES`, reconciled in `tests/test_capacity_demand_curve.py`). Additionally, the 2025/2026 **workbook** publishes the VRR point prices the narrative PDF leaves formula-defined (Point (a) 451.61, (b) 171.61 $/MW-day UCAP); they are recorded as `curve_point_ucap` rows (absolute UCAP Level MW + Price) so the committed Manual-18 pct-basis `curve_point` rows for that vintage stay unique on the datatype key.
