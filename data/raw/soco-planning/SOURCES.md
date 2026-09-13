# `soco-planning` — exact source URLs, re-fetch commands, and every host probe

Fetched **2026-09-13** by lane SOCO-12. Every URL below returned the stated
status from this session's egress on that date. Checksums: `SHA256SUMS.txt`.

## 1. Georgia Power 2025 Integrated Resource Plan — Georgia PSC Docket 56002

The Georgia PSC's docket browser is a JS app; its document list comes from a JSON
endpoint that **requires an XHR header** (a bare GET returns HTTP 200 with a
zero-byte body, which reads like a block and is not one):

```
curl -sL -H "X-Requested-With: XMLHttpRequest" \
  -H "Referer: https://psc.ga.gov/search/facts-docket/?docketId=56002" \
  "https://psc.ga.gov/search/service-facts-docket/?docketId=56002&sortDirection=ASC&sortColumn=Filed&searchText=&pageSize=50&pageNumber=1"
```

209 documents. The two this corpus uses:

| Doc ID | Filed | Description | Payload |
|---|---|---|---|
| **221233** | 2025-01-31 | 2025 Integrated Resource Plan PD | `2025_irp_public_disclosure.zip`, **103,717,722 B** |
| **223496** | 2025-07-31 | ORDER ADOPTING STIPULATION | `223496(f).pdf` 12,807,543 B **and** `56002  56003 2025 IRP Order (F).docx` |

Download URLs (the human-readable page is
`https://psc.ga.gov/search/facts-document/?documentId=<id>`):

```
# the IRP filing (zip)
curl -sSL -o 2025_irp_public_disclosure.zip \
  "https://services.psc.ga.gov/api/v1/External/Public/Get/Document/DownloadFile/221233/102406"
# the approving order — pdf (first 8 pages are scanned, no text layer) and docx (full text)
curl -sSL -o ga_2025irp_order.pdf  "https://services.psc.ga.gov/api/v1/External/Public/Get/Document/DownloadFile/223496/104726"
curl -sSL -o ga_2025irp_order.docx "https://services.psc.ga.gov/api/v1/External/Public/Get/Document/DownloadFile/223496/104728"
```

**Use the `.docx`, not the `.pdf`, for the order** — the PDF's first eight pages
carry no text layer, and every ordering paragraph this corpus cites comes from
the docx.

Zip members transcribed into `transcriptions/` (paths verbatim from the zip):

| Zip member | → transcription |
|---|---|
| `Main Document/2025 IRP Main Document.pdf` (3,038,316 B, 167 pp.) | `GPC_2025_IRP_Main_Document.txt` |
| `Technical Appendix Volume 1 PUBLIC DISCLOSURE/1 Load and Energy Forecast PUBLIC DISCLOSURE/B2025 Load and Energy Forecast PUBLIC DISCLOSURE.docx` (1,015,977 B) | `B2025_Load_and_Energy_Forecast.txt` |
| `Technical Appendix Volume 1 PUBLIC DISCLOSURE/2 Reserve Margin Study PUBLIC DISCLOSURE/2024 Reserve Margin Study PUBLIC DISCLOSURE.docx` (2,208,843 B) | `2024_Reserve_Margin_Study_Southern_Company_System.txt` |
| `Technical Appendix Volume 1 PUBLIC DISCLOSURE/4 Unit Retirement Study PUBLIC DISCLOSURE/2025 IRP Unit Retirement Study PUBLIC DISCLOSURE.docx` (307,832 B) | `GPC_2025_IRP_Unit_Retirement_Study.txt` |

Two zip members are **numeric sources, not transcribed here** because they feed
other directories: `Technical Appendix Volume 2 …/2 Resource Mix Study PUBLIC
DISCLOSURE/GPC and System IRP Summary Data - 2025 IRP PUBLIC DISCLOSURE.xlsx`
(37,778 B → `../load-forecast/soco/soco.csv` and this README §1) and
`Technical Appendix Volume 1 …/1 Load and Energy Forecast PUBLIC DISCLOSURE/
Hourly Load Profile Data.xlsx` (777,022 B — measured GPC hourly load for 2021,
2022 and 2023; **SOCO-11/SOCO-32's input**, flagged not landed).

Georgia Power's own IRP landing page, which is where the docket ids come from:
`https://www.georgiapower.com/about/company/filings/irp.html` (2022 IRP = docket
**44160**, 2023 IRP Update = **55378**, 2025 IRP = **56002**). Note
`https://www.georgiapower.com/company/plants-and-facilities/integrated-resource-plan.html`
**404s** — it is the stale path and redirects nowhere.

## 2. Southern Company Form 10-K (SEC EDGAR)

SEC requires a descriptive `User-Agent`. CIK **0000092122**.

```
UA="market-sim research <contact>"
curl -sL -H "User-Agent: $UA" \
  "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000092122&type=10-K&dateb=&owner=include&count=10"
curl -sL -H "User-Agent: $UA" "https://www.sec.gov/Archives/edgar/data/92122/<accession-nodash>/index.json"
curl -sSL -H "User-Agent: $UA" -o so-<YYYY>1231.htm \
  "https://www.sec.gov/Archives/edgar/data/92122/<accession-nodash>/so-<YYYY>1231.htm"
```

| FY | Accession | Primary document | Size |
|---|---|---|---|
| 2022 | 0000092122-23-000012 | `so-20221231.htm` | 19,675,562 B |
| 2023 | 0000092122-24-000009 | `so-20231231.htm` | 15,223,021 B |
| 2024 | 0000092122-25-000018 | `so-20241231.htm` | 15,365,895 B |
| 2025 | 0000092122-26-000006 | `so-20251231.htm` | 15,639,198 B |

These are **combined** filings (Southern Company + Alabama Power + Georgia Power
+ Mississippi Power + Southern Power + Southern Company Gas), which is why one
document carries every Operating Company's fleet total and the System peak.
Targeted extracts only: `transcriptions/Southern_Company_10-K_extracts_FY2022-FY2025.txt`.

## 3. SEEM (Southeast Energy Exchange Market)

Host `southeastenergymarket.com` is a WordPress site. **`WebFetch` returns HTTP
403 from this egress; `curl` returns 200** — use curl. The page list is readable
without auth via the WP REST API, which is how the empty informational-report
pages were established:

```
curl -sL "https://southeastenergymarket.com/wp-json/wp/v2/pages?per_page=50&_fields=id,slug,link,title"
curl -sL "https://southeastenergymarket.com/wp-json/wp/v2/pages/<id>"
```

| Page | id | Status on 2026-09-13 |
|---|---|---|
| `/reports/` "Public Data" | 1225 | **`"This content is restricted."`** — free registration required |
| `/public-hourly-informational-reports/` | 1171 | **"No reports available at this time."** |
| `/public-daily-informational-reports/` | 1166 | **"No reports available at this time."** |
| `/publicmonthlyinforeports/` | 1144 | **"No reports available at this time."** |
| `/auditor-reports/` "Public Monthly Auditor Reports" | 1433 | **public, no login** — monthly **2022-11 → 2026-07** plus annual 2023 / 2024 / 2025 |
| `/faq/` | 51 | public |
| `/newsroom/` | 48 | public |

Direct payload URLs (pattern `https://southeastenergymarket.com/wp-content/uploads/<name>.pdf`):

| File | Landed as |
|---|---|
| `SEEM-Audit-Report-Annual-Rpt-2023FINAL.pdf` | `transcriptions/SEEM_Auditor_Annual_Report_2023.txt` |
| `SEEM-Audit-Report-Annual-2024-F.pdf` | `transcriptions/SEEM_Auditor_Annual_Report_2024.txt` |
| `SEEM-Audit-Report-Annual-2025-Final.pdf` | **tracked** `SEEM_Auditor_Annual_Report_2025.pdf` + transcription |
| `SEEM-Audit-Report-2026_7.pdf` | `transcriptions/SEEM_Auditor_Monthly_Report_2026-07.txt` |
| `FERC-Accepts-Southeast-Energy-Exchange-Market-Settlement.pdf` | **tracked** `SEEM_FERC_Settlement_Press_Release_2026-01-12.pdf` + transcription |

## 4. SERC and NERC

```
curl -sSL -o serc_risk_report.pdf \
 "https://www.serc.org/wp-content/uploads/docs/default-source/program-areas/reliability-assessment/reliability-assessments/2024-2026-serc_regional_risk_report_final.pdf"
curl -sSL -o NERC_LTRA_2025.pdf \
 "https://www.nerc.com/pa/RAPA/ra/Reliability%20Assessments%20DL/NERC_LTRA_2025.pdf"
```

`www.serc1.org` **301s to `www.serc.org`** — follow redirects. The SERC report is
6,536,018 B / 88 pp.; the NERC LTRA 7,847,418 B / 182 pp., of which only the
SERC-Southeast panel (PDF pp. 120–125) is landed.

## 5. NRC — see `../nuclear-license-status/soco.csv`

Per-reactor info-finder pages `https://www.nrc.gov/info-finder/reactors/<slug>`
with slugs `far1 far2 hat1 hat2 vog1 vog2`; **Vogtle 3 and 4 are NOT under
`/info-finder/reactors/`** — they are Part 52 COL units at
`https://www.nrc.gov/reactors/new-reactors/large-lwr/col-holder/vog{3,4}.html`.
SLR status:
`https://www.nrc.gov/reactors/operating/licensing/renewal/subsequent-license-renewal.html`
and the plant page
`https://www.nrc.gov/reactors/operating/licensing/renewal/applications/hatch-subsequent.html`.
Every URL in that CSV's `source_url` column was fetched on 2026-09-13.

## 6. Hosts probed — including the ones that did NOT yield

| Host / URL | Result | Consequence |
|---|---|---|
| `psc.ga.gov` docket + `services.psc.ga.gov` download API | 200 | the Georgia IRP route; **needs the XHR header** on the JSON endpoint |
| `www.sec.gov` EDGAR | 200 | needs a descriptive `User-Agent` |
| `southeastenergymarket.com` | 200 via **curl**, **403 via `WebFetch`** | use curl for this host |
| `www.serc1.org` → `www.serc.org` | 301 → 200 | follow redirects |
| `www.nerc.com` | 200 | LTRA reachable |
| `www.nrc.gov` | 200 | all eight reactors reachable |
| `www.eia.gov/dnav/ng/hist_xls/` | 200 | the key-free gas route (`../gas-prices/SOURCES_soco_gas.md`) |
| `api.eia.gov` v2 | **no key in this container** (`EIA_API_KEY` unset, no `.env`) | key-free dnav route used instead |
| `www.georgiapower.com/company/plants-and-facilities/integrated-resource-plan.html` | **404** | stale path; use `/about/company/filings/irp.html` |
| `www.alabamapower.com/our-company/about-us/resource-planning.html` | **404** | no such page — and see the next row |
| `psc.alabama.gov` + `/electricity/` | 200 | **no IRP requirement is described anywhere on it** — README §5 |
| `www.pscpublicaccess.alabama.gov/pscpublicaccess/page/psc-searches/portal.aspx` | 200 | Alabama PSC full-text document search exists (ASPX app); **NOT swept by SOCO-12** — open item |
| Mississippi PSC | **not probed** | Mississippi Power's 2024 IRP is cited by the 10-K but was not retrieved — open item |
| `www.eia.gov/naturalgas/weekly/` · `www.eia.gov/todayinenergy/prices.php` | 200 | swept for a Southeast gas hub; **neither carries one** (`../gas-prices/SOURCES_soco_gas.md`) |

## 7. Tooling note

`pypdf`, `pdfminer.six`, `openpyxl`, `xlrd` and `pandas` were **not importable in
a default container** on 2026-09-13: the system `cryptography` fails with
`ModuleNotFoundError: No module named '_cffi_backend'`, which takes `pypdf` down
with it through `pypdf._crypt_providers`. `pip install cffi` repairs it (this is
the same class of block SPP-13 hit when "pdfminer would not import in the
session"). No repo dependency was changed.
