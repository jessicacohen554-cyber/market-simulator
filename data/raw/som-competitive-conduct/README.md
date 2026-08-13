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
