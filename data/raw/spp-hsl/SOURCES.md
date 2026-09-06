# `spp-hsl` — SOURCES

All URLs verified **2026-09-06** by lane SPP-12. No value in this directory came
from memory; every row of `spp_wind_curtailment_annual.csv` carries its own
`source_doc` + `source_page` and, where it is a quote, the verbatim sentence.

## Primary — SPP MMU Annual State of the Market reports (`www.spp.org`, HTTP 200)

| Edition | URL | Pages used |
|---|---|---|
| 2025 | <https://www.spp.org/Documents/76798/2025_Annual_State_of_the_Market_Report.pdf> | printed p. 50 (wind capacity/generation), p. 54 (curtailments) |
| 2024 | <https://www.spp.org/Documents/73953/2024_Annual_State_of_the_Market_Report.pdf> | printed p. 43 (wind capacity), p. 47 (curtailments) |
| 2023 | <https://www.spp.org/Documents/71645/2023%20Annual%20State%20of%20the%20Market%20report%20v2.pdf> | printed p. 48 (wind capacity), p. 55 (curtailments) |

Payloads are **not tracked** (6.1–6.4 MB each); full text transcriptions are at
`data/raw/spp-planning/transcriptions/ASOM_{2023,2024,2025}.txt` and checksums at
`data/raw/spp-planning/SHA256SUMS.txt`. Re-fetch from the URLs above is the
recovery route.

Found via the document tree at
`https://www.spp.org/spp-documents-filings/?id=18512` ("Annual State of the Market
Reports"), which lists **every edition 2009–2025** plus the stakeholder
presentations — so the 2019–2022 back-series is available in one place if a
rule-22 intake later needs it. The site's keyword search does **not** surface these
(it is date-sorted); walk the tree.

Printed-page numbers were read off each page's own footer
(`State of the Market <year>  <n>`), not inferred from the PDF page index — the
two differ by a front-matter offset of 12–14 pages depending on edition.

## Blocked — `portal.spp.org` (the product that would supersede all of the above)

- **Landing page:** <https://portal.spp.org/pages/ver-curtailments>
- **Listing:** `GET https://portal.spp.org/file-browser-api/?fsName=ver-curtailments&path=&type=folder`
- **Download:** `GET https://portal.spp.org/file-browser-api/download/ver-curtailments?path=<path>`
- **Probed 2026-09-06:** listing HTTP **200** `[]` · download HTTP **404** · `isPublic` **true** · requires `X-SPP-UI-Token`
- SPP's own description: *"VER curtailment data in 5 minute intervals for SPP total VER curtailment (not per resource)"*

Also blocked and needed for the denominator:
`generation-mix-historical` (see `data/raw/spp-genmix/SOURCES.md`).

The unblocked route not yet tried, for both: the **FTP** access described in SPP's
"SPP Public Data Access" guide — see
`data/raw/spp-planning/spp-system-interfaces-stakeholder-reference-guide.pdf`,
Public Data Specifications.
