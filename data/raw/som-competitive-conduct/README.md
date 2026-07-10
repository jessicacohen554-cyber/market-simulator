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

## Quarantine (CLAUDE.md rule 22)

Only train-window years (2023-2025) are transcribed. The SOM tables also
print 2018-2022 history and the Winter-2026 quarterly covers
Dec-2025..Feb-2026 (H1-2026 locked-test window): those values are
deliberately NOT transcribed and their PDFs (except the in-window ones
above) not committed, pending explicit owner authorization.

DATA NEEDED: 2025 MISO SOM (expected ~June 2026, not yet published as of
2026-07-10) — will supply the 2025 annual coal Table-7 conduct shares and
the 2025 price-cost mark-up; its publication is the rule-23 re-derive
trigger for anything grounded on the 2024 values (the MISO coal offer
level carries 2024's mark-up ≈ 0 forward into 2025 until then).
DATA NEEDED (extension): NYISO / ERCOT / ISO-NE SOM conduct sections, to
extend the datatype beyond MISO when their offer structures are examined.
