# MISO capacity-market-auction-supply (PRA offered/cleared + requirement ledger)

`miso.csv` — MISO Planning Resource Auction supply-side accounting,
PY2023-24 through PY2025-26, transcribed by capx D31 (2026-09-02) from the
three primary PRA Results Posting PDFs (payloads NOT committed — the corpus
posture for publication PDFs; sha256 identity records and re-fetch URLs in
`data/raw/miso-pra/SOURCES.md` / `SHA256SUMS.txt`):

- **Category rows** (`metric` = offered | cleared, `unit` = mw_zrc):
  the PY2025-26 posting's "Seasonal Supply Offered and Cleared Comparison
  Trend" tables (pp.22-25), which carry all three planning years per season
  for the five categories (Generation / External Resources / Behind-the-Meter
  Generation / Demand Resources / Energy Efficiency) plus Total. Category
  sums reproduce the published totals to ≤0.3 MW (transcription check run at
  intake). The Summer-2025 External Resources cleared row (3,505.9) and
  Demand Resources cleared row (9,004.4) are the capx S-123 registry
  operands (`ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"]`,
  `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["MISO"]`) — this file is their
  full-series home.
- **System ledger rows** (`unit` = mw_sac, `area` = System): each posting's
  own seasonal "PRA Results by Zone" System column — the vertical-era single
  `prmr` (PY2023-24 / PY2024-25, where committed ≡ PRMR by design: the
  auction cleared exactly the fixed requirement, to ≤3 MW rounding) and the
  RBDC-era `initial_prmr` / `final_prmr` pair (PY2025-26, where final PRMR =
  the cleared curve-intersection quantity), plus offer_submitted / frap /
  self_scheduled / non_ss_offer_cleared / committed where transcribed.
- **Subregional `initial_prmr` rows** (PY2025-26, North/Central + South):
  the RBDC curve-normalization operands for the digitized subregional curves
  in `../../demand-curve/miso/miso.csv`.

Cross-checks run at intake: the PY2025-26 posting's trend values reproduce
the older postings' own System rows exactly (e.g. Summer-2023
offer-submitted 139,373.9 appears identically in the 2023 posting p.17 and
the 2025 posting p.22).

Licensing note: MISO's redistribution terms are unverified (site terms pages
403 to automated fetch) — see `docs/data-licensing.md` §7.
