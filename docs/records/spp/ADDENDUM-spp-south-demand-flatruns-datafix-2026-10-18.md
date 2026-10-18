# ADDENDUM — SPP flat runs: the R22 / R23 repair as landed (lane UC-SPP-DATAFIX, 2026-10-18)

To `FINDING-spp-south-demand-flatruns-2026-10-18.md` (#7284). Full record: `RESULT-uc-spp-datafix-2026-10-18.md`.

**§4 Fix A landed with interchange option 3(b), measured.** The owner chose it (R22); R23 extends the same screen to wind and solar.

- **Mask:** reproduces §2 exactly (828 / 47 / 142 / 9 / 36 / 510 / 698 h).
- **Load leg:** reproduces §4 to the GWh. Every zone-year is exact except 2021 South, +268 vs +269 (rounding).
- **Counterparty intake:** all ten EIA-930 counterparties that report a leg with SWPP: AECI, EPE, ERCO, MISO, PNM, PSCO, SIKE, SPA, WACM, WAUW. §3's list of missing counterparties is closed.
- **SPC (SaskPower) cannot be recovered:** it is not an EIA-930 respondent, so its leg exists only in SWPP's own submission.

**Residuals, by desk ruling (measured beats stale beats estimated; never interpolate):**

| Gap | Hours | Treatment | Bound |
|---|---|---|---|
| SPC leg, both sides absent | 336 / 24 / 179 (2019 / 2024 / 2025) | omitted, flagged | ≤ 150 MW/h, ≤ 0.05 TWh/yr; expected ≈ 6 / 1 / 12 GWh |
| MISO leg, both sides absent, 2019-12-14 01:00Z | 1 | EIA's stale SWPP TI kept, flagged | not tie-bounded |
| GenMix blank, 2019-03-29 09:00–16:00Z | 8 | EIA's stale wind / solar kept, flagged | wind 8,676 → 6,469 MW vs stale 9,493; solar 0 → 202 vs 0 |

**Rule-14 basis gaps:**
- The counterparty-leg sum runs +25 to +76 MW/h above the BA `Total interchange`. Hourly correlation is 0.994–0.997 (2019–23), 0.96 (2024) and 0.76 (2025, driven by SWPP's own SPC / WACM impossible prints).
- GenMix solar reads 2–10 % above `NG: SUN`. GenMix wind is within 1 %.

**§5 answered.** GenMix replaces frozen `NG: WND` in 828 / 46 / 142 / 0 / 33 / 261 / 671 h. Wind energy moves −2.50 TWh in 2019 and ≤ 0.6 TWh in every other year.
