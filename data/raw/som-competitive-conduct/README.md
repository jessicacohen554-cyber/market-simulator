# som-competitive-conduct — raw home

Hand-transcribed market-monitor (Potomac Economics) competitive-conduct
statistics: the State-of-the-Market price-cost mark-up, economic-withholding
output gap, and the coal commitment-conduct decomposition (economic-offer vs
must-run/self-commit start shares, regulated vs merchant, with net revenues).

## Layout

- `som_competitive_conduct.csv` — the transcription, one row per
  `(iso, year, period, fleet_segment, metric)`; schema
  `data/dictionary/schema/som-competitive-conduct.schema.yaml`. Every row
  carries `source_doc` (PDF filename) + `source_page` (PDF pagination,
  1-based) so each number is re-checkable against the primary document.
- Source PDFs live in the ISO's raw dir (`data/raw/MISO/` for the MISO
  reports, mirroring the NYISO SOM PDFs under `data/raw/NYISO/`).

## Authoritative sources (ERCOT)

All from potomaceconomics.com (ERCOT Independent Market Monitor), PDFs
committed under `data/raw/ERCOT/`. Seeded 2026-08-05 for the FFR-6A
retirement-screen margin-gap decomposition — the SOM Net Revenue Analysis
(new-CT/CC net revenue $/kW-yr, energy vs reserves stack), CONE, and the
existing-unit (coal/nuclear) cost benchmarks:

- 2023 SOM: `2023-State-of-the-Market-Report_Final_060624.pdf`
  (wp-content/uploads/2024/05/…) — §Resource Adequacy A "Net Revenue
  Analysis" (PDF p.108, printed p.76; Figures 45/46 PDF p.109) and
  B "Net Revenues of Existing Units" (PDF p.110).
- 2024 SOM: `2024-State-of-the-Market-Report.pdf`
  (wp-content/uploads/2025/06/…) — §Resource Adequacy B/C/D (PDF
  pp.117-120, printed pp.78-82; Figure 56 PDF p.118).
- 2025 SOM: `2025-State-of-the-Market-Report-for-ERCOT.pdf`
  (wp-content/uploads/2026/06/…) — §Resource Adequacy C/D (PDF
  pp.123-125, printed pp.100-103; Figure 56 PDF p.124; summary bullets
  PDF p.119).

## Authoritative sources (MISO)

All from potomaceconomics.com (MISO Independent Market Monitor):

- 2023 SOM: `2023-MISO-SOM_Report_Body-Final.pdf`
  (wp-content/uploads/2024/06/…) — Table 7 "Coal-Fired Resource Operation
  and Profitability" (PDF p.67, printed p.43); Competitive Assessment §VIII.B
  (PDF p.112).
- 2024 SOM: `2024-MISO-SOM_Report_Body_Final.pdf`
  (wp-content/uploads/2025/06/…) — Table 7 (PDF p.71, printed p.45);
  Competitive Assessment (PDF p.120). Appendix
  `2024-MISO-SOM_Appendix_Final.pdf` (wp-content/uploads/2025/07/…) —
  Table A10 commitment-screen methodology (PDF pp.67-68) and the
  price-cost mark-up methodology (PDF pp.150-151).
- 2025 IMM quarterlies (`IMM-Quarterly-Report_{Spring,Summer,Fall}-2025*.pdf`,
  summary table PDF p.3): low-threshold output-gap MW/hr — the only free
  2025 conduct evidence until the 2025 SOM publishes (~June 2026).

## Holdout posture (CLAUDE.md rule 22, owner clarification 2026-08-06)

The former text here quarantined 2018-2022 "pending explicit owner
authorization". That is SUPERSEDED and had it backwards: **what is held out
is the SCORE, never the DATA.** Data intake needs no per-ISO/per-window
authorization and no marker; only solving, scoring or registering an
out-of-training year is the spend.

**ERCOT net-revenue anchors 2019-2022 transcribed 2026-08-13** (session
ercot-195, L-SCAR-SCREEN-2) as the identification source for the screen
scarcity-rent lane (`docs/DECISION-CARD-lscar-screen-revenue-2026-08-13.md`
§2.2; its V0 gate needs >=5 anchor vintages). Their PDFs are committed under
`data/raw/ERCOT/` alongside the 2023-2025 set. No year was solved or scored.

- 2019 SOM: `2019-State-of-the-Market-Report.pdf`
  (wp-content/uploads/2020/06/…) — Net Revenue Analysis, PDF p.97.
- 2020 SOM: `2020-ERCOT-State-of-the-Market-Report.pdf`
  (wp-content/uploads/2021/06/…) — PDF p.93.
- 2021 SOM: `2021-State-of-the-Market-Report.pdf`
  (wp-content/uploads/2022/05/…) — PDF p.114. Winter Storm Uri year; the
  monitor's own ex-Uri counterfactual is transcribed alongside the headline.
- 2022 SOM: `2022-State-of-the-Market-Report_Final_060623.pdf`
  (wp-content/uploads/2023/05/…) — PDF p.108, cross-checked against the
  Waha/Katy appendix values on p.110.
The 2017 SOM (`.../uploads/2018/05/2017-State-of-the-Market-Report.pdf`) exists
in the library but is deliberately NOT committed: outside the 2019-2025 working
span and not transcribed. It is named here only because it is half the evidence
that 2018 is genuinely missing rather than mis-named — 2017 and 2019 are both
published, 2018 is not.

**A transcription limit worth knowing before planning any similar intake:**
the SOM prints its multi-year net-revenue *history* only as **bar charts
with no data labels**. A year's value is therefore transcribable only from
the vintage that reports that year as its own subject year (in prose), never
read off a later report's history figure. The **2018** ERCOT SOM is absent
from the Potomac document library (2017 and 2019 are both present), so 2018
has no prose source; it is outside the program's 2019-2025 working span in
any case.

Still not transcribed: the Winter-2026 quarterly (Dec-2025..Feb-2026)
conduct rows, and the ERCOT SOM *conduct* sections (price-cost mark-up,
output gap) for every vintage.

DATA NEEDED: 2025 MISO SOM (expected ~June 2026, not yet published as of
2026-07-10) — will supply the 2025 annual coal Table-7 conduct shares and
the 2025 price-cost mark-up; its publication is the rule-23 re-derive
trigger for anything grounded on the 2024 values (the MISO coal offer
level carries 2024's mark-up ≈ 0 forward into 2025 until then).
DATA NEEDED (extension): NYISO / ISO-NE SOM conduct sections, to extend
the datatype further when their offer structures are examined. (ERCOT
net-revenue/CONE rows seeded 2026-08-05; the ERCOT SOM *conduct* sections
— price-cost mark-up, output gap — remain untranscribed.)

## Authoritative sources (SPP) — added 2026-09-25 by lane SPP-80

SPP Market Monitoring Unit annual State of the Market reports, 2019-2025, all
from `www.spp.org` (anonymous HTTPS, fetched 2026-09-25). **The PDFs are NOT
committed** (charter: commit the numbers, not the PDFs); each row's
`source_doc` + `source_page` (PDF pagination, 1-based) re-checks against the
PDF identified by the sha256 below.

| Year | URL | sha256 |
|---|---|---|
| 2019 | <https://www.spp.org/documents/62150/2019%20annual%20state%20of%20the%20market%20report.pdf> | `1eb25ba14a50ab3e65c130662acea5b66841493e1c68f2deb40fae88c6f5e770` |
| 2020 | <https://www.spp.org/documents/65161/2020%20annual%20state%20of%20the%20market%20report.pdf> | `5a0d3e10b662c8a9ccc6879f40c09b7c2c82718c8b3265b939ff11536ac95f29` |
| 2021 | <https://www.spp.org/documents/67104/2021%20annual%20state%20of%20the%20market%20report.pdf> | `c636aae8e237847984625145ed0810f1e59f7ca03cadedb9baaa7291ec5d862a` |
| 2022 | <https://www.spp.org/documents/69330/2022%20annual%20state%20of%20the%20market%20report.pdf> | `e5f9aff1c0badde3d8ee042a2456611df9f2ca0f2e695fb4ccac4e2737b5f327` |
| 2023 | <https://www.spp.org/documents/71645/2023%20annual%20state%20of%20the%20market%20report%20v2.pdf> | `87ca19c5b4e58e0a49dc5e9c4f3f7c43696feb2100c73382bceab29cd834824b` |
| 2024 | <https://www.spp.org/documents/73953/2024_annual_state_of_the_market_report.pdf> | `16fd07233b8dad8d1277c3a490341940a80b9ea4a10ce48a97578eb3aaebe149` |
| 2025 | <https://www.spp.org/documents/76798/2025_annual_state_of_the_market_report.pdf> | `752bd068980c2d39f7772f7333c5f984e161aa1a1e46cb61ed21710fd62b192d` |

What is transcribed (`iso == SPP`): on-/off-peak marginal-resource offer
markup ($/MWh — SPP's construct, market-based minus mitigated offer, NOT
MISO's fractional price-cost mark-up), coal and wind markups, DA+RT
congestion payments, RT scarcity-interval totals, and annual DA/RT average
prices. Restatements by a later vintage are in `note`.

**Two transcription limits, stated rather than hidden.**
- The SPP SOM prints 2021 (full year) and 2022 annual markups **only as a
  chart marker with no data label**. Those four rows carry `_digitized_` in the
  metric code: read from the PDF's vector geometry (marker centre against the
  axis-tick fit), then bias-corrected against the same chart's printed years
  (+0.25 to +0.57 $/MWh). **The 2022 and 2023 vintages disagree on 2022
  on-peak** (+6.35 vs +12.03 $/MWh); both are recorded in the note, and no
  value was chosen to fit anything.
- From 2022 the SOM reports scarcity per product as monthly charts, with no
  annual total. `rt_scarcity_intervals` therefore stops at 2021; the SPP-80
  FINDING counts scarcity for every year directly from the landed RTBM MCPs
  (`data/raw/spp-or-mcp/`).

Scarcity-design dates (SPP MMU's own statements): ramp capability product
implemented **2022-03-01** (2022 SOM PDF p.122); fast-start pricing **May 2022**
(2022 SOM p.91); uncertainty product FERC-approved mid-August 2022 (2022 SOM
p.170) and implemented **2023-07-06** (2023 SOM p.120); uncertainty design
enhancement **October 2024** (2024 SOM p.226). The landed RTBM MCP data agrees:
the first non-zero ramp-up MCP is 2022-03-01, and the first non-zero uncertainty
MCP is 2023-10-09.

### Added 2026-09-25 by lane SPP-81 (same seven PDFs, same sha256)

- `rt_marginal_interval_share_digitized` (unit `fraction`, fleet_segment `wind` /
  `coal` / `gas_combined_cycle` / `gas_simple_cycle` / `other`): the annual bars of
  the SOM figure "Generation on the margin, real-time" (share of RT intervals each
  technology was marginal and price-setting). The figure prints no data labels, so
  every value is digitized: 2019–2023 vintages from the PDF vector geometry
  (bar-segment height over the stacked total), 2024–2025 vintages from the embedded
  raster (pixel runs at the bar centre, classified to the legend colours). Each year
  is taken from the **latest** vintage that charts it; every other vintage's reading
  is in `note`. Checks: digitized values reproduce every share the SOM prints in
  prose to within 0.4 pt, and overlapping vintages agree to within 0.4 pt except
  2022, which the 2023 SOM **restated** (gas simple-cycle 21.5 → 24.1 %). The 2025
  SOM prose states gas simple-cycle / combined-cycle *decreased* 5 / 6 pts from DA to
  RT, which contradicts its own chart (RT 23.1 / 20.4 vs DA 18 / 14); the chart is
  recorded and the contradiction noted.
- `rt_implied_heat_rate` (unit `btu_per_kwh`, fleet_segment `system`): the MMU's
  annual RT implied heat rate ((RT price − representative VOM) / gas price), as
  printed in prose, 2020–2025. The 2024 SOM restates 2023 (nearly 11,000 → over
  12,600); both are in `note`.
- `gas_hub_price_annual_avg` (unit `usd_per_mmbtu`; segments `panhandle_eastern` /
  `southern_star` / `henry_hub`): the SOM's printed annual hub averages, 2019–2025
  ("Fuel price indices and energy prices"). The only public Mid-Continent hub series
  this lane found; SPP-81 uses it to test whether spot gas at SPP's own hubs ran above
  the EIA-923 delivered price.
- Consumer: `scripts/probes/_spp81_residual_upper_tercile.py` /
  `docs/handoffs/FINDING-spp-81-residual-upper-tercile-2026-09-25.md`.
