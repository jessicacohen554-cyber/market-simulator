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

## Appended 2026-09-06 by lane SPP-13 — the FTP route, and the wind denominator that did land

- **FTP folder (PRD):** `ftp://pubftp.spp.org/Operational_Data/VER_Curtailment/`, file `VER-Curtailments-YYYYMMDD.csv` — from `SPP Markets Public Data Guide v35` (`data/raw/spp-planning/SPP_Markets_Public_Data_Guide_v35.docx`); host from `SPP Public Data Access` v3.0 p. 2. Credential `anonymous` / email. **Probed 2026-09-06: egress-blocked** (`data/raw/spp-planning/README.md` §6). Sample schema (v35 `VER-Curtailments-20260128.csv`, 566 rows = 288 intervals × 2 BAAs, not landed), header verbatim: `LocalIntervalEnding,GMTIntervalEnding,WindRedispatchCurtailments,WindManualCurtailments,WindCurtailedForEnergy,SolarRedispatchCurtailments,SolarManualCurtailments,SolarCurtailedForEnergy,BAA` — MW per 5-min interval, one row per BAA (`SPP`, `SWPW`); sample row `01/28/2026 00:05:00.000000,01/28/2026 06:05:00.000000,1110.440,0.000,0.000,0.000,0.000,0.000,SPP`. Curtailment is split redispatch / manual / for-energy, so the ASOM's single "curtailment" figure needs a stated mapping onto these three columns before the two are compared.
- **Denominator now partly available:** `data/raw/spp-genmix/GenMix_2024_SPP.csv` (2024-02-15 →) and `GenMixYTD_SPP.csv` (2025 to 12-16) carry delivered wind in MW (`WIND_MKT + WIND_SELF`, 5-min). A derived curtailment share for 2025 (and a Feb-15-onward 2024) can now be built from two measured legs; it remains `derived=yes` with its formula, and the ASOM rows in `spp_wind_curtailment_annual.csv` are unchanged.
