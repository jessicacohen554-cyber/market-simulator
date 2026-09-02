# MISO PRA clearing-price provenance

Primary MISO auction-summary PDFs were blocked by the session network
allowlist when this file was first assembled (misoenergy.org /
cdn.misoenergy.org returned HTTP 403), so the figures in
`miso_pra_clearing_prices_2023-2026.csv` were transcribed from public
secondary reporting of the official results.

**That block has since lifted: `cdn.misoenergy.org` fetches succeed as of
2026-08-30** (capx S-123 session). Two primary PDFs were fetched and
hand-read that session (payloads NOT committed — the corpus posture for
publication PDFs; re-fetch and verify against the identity records below):

| Document | sha256 | bytes |
|---|---|---|
| PY 2025/26 PRA Results Posting (05/29/2025, corrections) | `4c8db42dabc340bc6747a178d446a4fc6ca37eb21897b36700e6c64905e9ad9b` | 1,498,304 |
| Indicative DLOL Results PY 2025-2026 (`https://cdn.misoenergy.org/Indicative%20DLOL%20Results%20PY%202025-2026667100.pdf`) | `3306d58e6d036403475bc9c405c8622946fb230a3bee856d87e50cf0940aeb83` | 445,239 |

The PRA posting's p.18 Summer zonal table reproduces the committed
PY 2025-26 summer rows of `capacity-market/auction-price/miso/miso.csv`
to the digit (verified in-session). The posting additionally sources the
adequacy-registry operands intaken by capx S-123
(`ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"]` — p.22 Summer trend table,
External Resources cleared 3,505.9 MW ZRC;
`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["MISO"]` — Demand Resources
cleared 9,004.4 over Initial PRMR 135,213.4; see
`src/market_sim/config/capacity_market.py` citation blocks).

**capx D31 (2026-09-02): all three primary postings fetched, sha256-recorded
and intaken.** The Q24-funded intake fetched the three URLs below directly
from `cdn.misoenergy.org` (open from this environment class since
2026-08-30); the PY2025-26 sha is byte-identical to the S-123 record above.
Identity records: `SHA256SUMS.txt` in this directory (payloads NOT
committed — corpus posture). What was transcribed from them:

- pp.22-25 offered/cleared category trend + pp.16-21 seasonal System/
  subregional PRMR-and-commitment ledgers →
  `data/raw/capacity-market/auction-supply/miso/miso.csv`
  (the `capacity-market-auction-supply` datatype; capacity_market.py's
  `ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO` identification source).
- pp.4/15/16/17 subregional RBDC chart polylines (digitized via
  `scripts/data/digitize_miso_rbdc_charts.py`) →
  `data/raw/capacity-market/demand-curve/miso/miso.csv` curve_point rows
  (the published-shape replacement for the first-order RBDC x-positions).

Primary sources (verified live 2026-09-02):
- PY 2023/24: https://cdn.misoenergy.org/2023%20Planning%20Resource%20Auction%20(PRA)%20Results628925.pdf
- PY 2024/25: https://cdn.misoenergy.org/2024%20PRA%20Results%20Posting%2020240425632665.pdf
- PY 2025/26: https://cdn.misoenergy.org/2025%20PRA%20Results%20Posting%2020250529_Corrections694160.pdf

Secondary sources transcribed (source-id -> URL):
- utilitydive-650727: https://www.utilitydive.com/news/miso-capacity-planning-resource-auction/650727/
- utilitydive-714403: https://www.utilitydive.com/news/miso-capacity-pra-auction-missouri/714403/
- utilitydive-746576: https://www.utilitydive.com/news/miso-capacity-auction/746576/
- enelnorthamerica-2024: https://www.enelnorthamerica.com/insights/blogs/miso-2024-capacity-auction-results
- enelnorthamerica-2025: https://www.enelnorthamerica.com/insights/blogs/miso-2025-capacity-auction-results
