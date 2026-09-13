# `nwpp-planning` — exact source URLs

Every artifact in this directory, with the URL it was fetched from, the HTTP
status this session observed, and the fetch date. Landed **2026-09-13** by lane
**NWPP-12** (`docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-12,
manifest rows 7–11). FINDING: `docs/handoffs/FINDING-nwpp-12-2026-09-13.md`.

Checksums of every fetched artifact, tracked or not: `SHA256SUMS.txt`.
Which payloads are tracked and which are transcription-only: `README.md`.

All URLs below returned **HTTP 200** on **2026-09-13** from this session's
egress. Nothing here was fetched through an authenticated route; no credential
is required for any row.

## 1. WECC published path ratings (manifest row 7)

| Artifact | URL | Status |
|---|---|---|
| `transcriptions/2024_Path_Rating_Catalog_Public_v2.txt` (payload not tracked) | `https://www.wecc.org/sites/default/files/documents/meeting/2024/2024%20Path%20Rating%20Catalog%20Public_v2.pdf` | 200, 11,411,443 B, 83 pp. |

Landing page: `https://www.wecc.org/wecc-document/13326` ("2024 Path Rating
Catalog Public Version"). The document states its own provenance on printed
p. 6: *"This catalog was extracted from the CEII version of the Path Rating
Catalog and is a summary of that information to make a public version of the
Path Rating Catalog."*

**Route note.** `www.wecc.org`'s own site search (`/search?keys=…`) is a Drupal
AJAX view: the HTML shell returns 200 but carries **no result rows**, so a
`curl` of the search URL cannot find a document. The catalogue was located by
its direct `/sites/default/files/documents/…` path. A follow-up needing other
WECC documents should expect the same and go via direct file paths or the
`/wecc-document/<id>` landing pages.

## 2. WRAP / Western Power Pool (manifest row 8)

Index page for all of the below: `https://www.westernpowerpool.org/resources/wrap_bpms/`.
Note the path segment is `private-media` but **no authentication is used or
required** — every file below was fetched anonymously.

| Artifact | URL | Status |
|---|---|---|
| `WPP_BPM_101_Advance_Assessment_V2.0_2026-03.pdf` | `https://www.westernpowerpool.org/private-media/documents/V2.0_BPM_101_-_Advance_Assessment_-_March_2026.pdf` | 200, 654,508 B |
| `WPP_BPM_102_FS_Reliability_Metrics_V3.0_2026-03.pdf` | `https://www.westernpowerpool.org/private-media/documents/V3.0_BPM_102_-_Forward_Showing_Reliability_Metrics_-_March_2026_scKnP0V.pdf` | 200, 911,534 B |
| `WPP_BPM_103_FS_Capacity_Requirements_V4.0_2026-03.pdf` | `https://www.westernpowerpool.org/private-media/documents/V4.0_BPM_103_-_Forward_Showing_Capacity_Requirements_-_March_2026.pdf` | 200, 786,659 B |
| `WPP_BPM_108_FS_Submittal_Process_V4.0_2026-03.pdf` | `https://www.westernpowerpool.org/private-media/documents/V4.0_BPM_108_-_Forward_Showing_Submittal_Process_-_March_2026.pdf` | 200, 949,957 B |
| `WPP_BPM_109_Transition_Period_V3.0_2026-03.pdf` | `https://www.westernpowerpool.org/private-media/documents/V3.0_BPM_109_-_Transition_Period_-_March_2026.pdf` | 200, 729,710 B |
| `WPP_BPM_204_Holdback_Requirement_V3.0_2026-03.pdf` | `https://www.westernpowerpool.org/private-media/documents/V3.0_BPM_204_-_Holdback_Requirement_-_March_2026.pdf` | 200, 852,000 B |
| `WPP_BPM_210_Binding_NonBinding_Participation_V3.0_2026-03.pdf` | `https://www.westernpowerpool.org/private-media/documents/V3.0_BPM_210_-_Binding_and_Non-Binding_Participation_-_March_2026.pdf` | 200, 708,207 B |
| `WPP_Joint_WRAP_Statement_2025-09-29.pdf` | `https://www.westernpowerpool.org/private-media/documents/2025.9.29_Joint_WRAP_Statement_tTNMvkD.pdf` | 200, 42,731 B |

Participant roster read 2026-09-13 from the WRAP programme page
`https://www.westernpowerpool.org/about/programs/western-resource-adequacy-program`
(200, 83,175 B) — the 22 participant logos are enumerated in `README.md` §2.3.
The WRAP FAQ (`/news/wrap-faqs`) and the news item announcing the joint
statement (`/news/joint-statement-commitment-to-the-western-resource`) both
return 200 but state the binding date less precisely than BPM 109 does; BPM 109
is the citation used.

**404 recorded:** `https://www.westernpowerpool.org/about/program/wrap` (the
singular `program` path) — the live path is `/about/programs/…`.

## 3. Participant IRPs (manifest row 9)

| Artifact | URL | Status |
|---|---|---|
| `transcriptions/PacifiCorp_2025_IRP_Vol1.txt` (payload not tracked) | `https://www.pacificorp.com/content/dam/pcorp/documents/en/pacificorp/energy/integrated-resource-plan/2025-irp/2025_IRP_Vol_1.pdf` | 200, 14,075,881 B, 334 pp. |
| `transcriptions/PacifiCorp_2025_IRP_Update_2026-03-31.txt` (payload not tracked) | `https://www.pacificorp.com/content/dam/pcorp/documents/en/pacificorp/energy/integrated-resource-plan/2025-irp/2025_IRP_Update.pdf` | 200, 14,089,517 B, 272 pp. |
| `transcriptions/PGE_2023_CEP-IRP_REVISED_2023-06-30.txt` (payload not tracked) | `https://downloads.ctfassets.net/416ywc1laqmd/6B6HLox3jBzYLXOBgskor5/63f5c6a615c6f2bc9e5df78ca27472bd/PGE_2023_CEP-IRP_REVISED_2023-06-30.pdf` | 200, 16,719,556 B, 682 pp. |
| `IdahoPower_2025_IRP_Final.pdf` | `https://docs.idahopower.com/pdfs/AboutUs/PlanningForFuture/2025IRP/2025%20IRP%20Final.pdf` | 200, 4,155,417 B |
| `IdahoPower_2025_IRP_AppA_Sales_and_Load_Forecast.pdf` | `https://docs.idahopower.com/pdfs/AboutUs/PlanningForFuture/2025IRP/2025%20IRP%20Appendix%20A.pdf` | 200, 878,077 B |
| `IdahoPower_2025_IRP_AppD_System_Reliability.pdf` | `https://docs.idahopower.com/pdfs/AboutUs/PlanningForFuture/2025IRP/2025%20IRP%20Appendix%20D.pdf` | 200, 3,763,632 B |
| `transcriptions/Avista_2025_Electric_IRP.txt` (payload not tracked) | `https://www.myavista.com/-/media/myavista/content-documents/about-us/our-company/irp-documents/2025/2025-avista-electric-irp.pdf` | 200, 5,757,866 B, 365 pp. |
| `transcriptions/NorthWestern_2026_MT_IRP_public.txt` (payload not tracked) | `https://northwesternenergy.com/docs/default-source/default-document-library/about-us/erp-irp/2026-mt-irp-public.pdf` | 200, 7,834,733 B, 382 pp. |
| `PSE_2023_Electric_Progress_Report_Ch6_Demand_Forecasts.pdf` | `https://www.pse.com/-/media/PDFs/IRP/2023/electric/chapters/06_EPR23_Ch6_Final.pdf` | 200, 1,345,193 B |
| `PSE_2023_Electric_Progress_Report_Ch7_Resource_Adequacy.pdf` | `https://www.pse.com/-/media/PDFs/IRP/2023/electric/chapters/07_EPR23_Ch7_Final.pdf` | 200, 766,317 B |
| `NVEnergy_2024_Joint_IRP_Volume1.pdf` (transmittal + 29-volume index) | `https://www.nvenergy.com/publish/content/dam/nvenergy/brochures_arch/about-nvenergy/rates-regulatory/recent-regulatory-filings/irp/IRP-Volume-1.pdf` | 200, 1,392,524 B |
| `transcriptions/NVEnergy_2024_Joint_IRP_Volume6_LoadForecast.txt` (payload not tracked) | `https://www.nvenergy.com/publish/content/dam/nvenergy/brochures_arch/about-nvenergy/rates-regulatory/recent-regulatory-filings/irp/IRP-Volume-6.pdf` | 200, 8,815,109 B, 214 pp. |

**404s recorded** while locating the above (kept so a follow-up does not repeat them):

- `https://portlandgeneral.com/about/info/iso-and-regulatory/integrated-resource-planning` — **404**. The live path is
  `https://portlandgeneral.com/about/who-we-are/resource-planning/combined-cep-and-irp`.
- `https://www.pse.com/en/IRP/Current-IRP-Process` — **404**.
- `https://www.pse.com/en/pages/energy-supply/resource-planning` — **404**.

**Two publisher-state facts that are not blocks and must not be recorded as
ones** (detail and citations in `README.md` §4.6/§4.7):

- **PGE has no 2025/2026 IRP.** Its current acknowledged plan is the **2023
  CEP/IRP** (revised 2023-06-30) plus a Portfolio Analysis Refresh Addendum
  (`https://assets.ctfassets.net/416ywc1laqmd/E074bPlYZi0LF129vutf7/a6766ab7ba78c9cf28a51a2a0441a7c9/2023_CEP-IRP_Portfolio_Analysis_Refresh_Addendum.pdf`,
  not fetched).
- **PSE has no 2025 electric IRP.** Washington's 2024 statute replaced the
  separate gas and electric IRPs with one **Integrated System Plan**, PSE's
  first due **2027**; its most recent filed electric plan is the **2023 Electric
  Progress Report** (filed 2023-03-31), two chapters of which are landed here.

## 4. NRC — Columbia Generating Station (manifest row 10)

Not landed as a payload; transcribed straight into
`data/raw/nuclear-license-status/nwpp.csv`, which carries the URLs per row.

| Page | URL | Status |
|---|---|---|
| NRC info-finder reactor page, Columbia Generating Station | `https://www.nrc.gov/info-finder/reactors/wash2` | 200 |
| NRC list of power reactor units (the slug index) | `https://www.nrc.gov/reactors/operating/list-power-reactor-units.html` | 200 |
| NRC Status of Subsequent License Renewal Applications | `https://www.nrc.gov/reactors/operating/licensing/renewal/subsequent-license-renewal.html` | 200, 98,941 B |

**404 recorded:** `https://www.nrc.gov/info-finder/reactors/colu` — the
info-finder slug for Columbia Generating Station is **`wash2`** (the plant's
construction-era name, WNP-2), not a `colu`-style abbreviation. A follow-up
should take slugs from the list-of-power-reactor-units page, never guess them.

## 5. Fuel (manifest row 11 neighbours)

No payload landed in this directory. The NWPP gas and coal provenance notes are
`data/raw/gas-prices/SOURCES_nwpp_gas.md` and
`data/raw/coal-prices/SOURCES_nwpp_coal.md`; both rest on series already
committed elsewhere in `data/raw/` and cite them there.

## 6. Text extraction

`transcriptions/*.txt` are **`pypdfium2` `PdfDocument[...].get_textpage().
get_text_range()`** output, unedited, one file per PDF, page markers
`=====PDFPAGE n=====` where *n* is the **PDF** page. `pdfminer.six` and `pypdf`
were both unusable in this container (the installed `cryptography` wheel raises
`pyo3_runtime.PanicException` on import, which `pypdf`'s crypt-provider fallback
does not catch); `pypdfium2` has no such dependency. Every citation in
`README.md` gives the **printed** page and, where the two differ, the PDF page
as well.

**Known extraction limit, stated because it decides what is and is not
transcribable here:** `pypdfium2` recovers flowed text and simple ruled tables
but returns **nothing for a table rendered as an image**. Three tables this lane
wanted are image-only and are recorded as `partial` in the FINDING rather than
transcribed: PacifiCorp 2025 IRP Tables 1.2 / 6.2 / 6.3 (coal and gas unit end
dates), PacifiCorp Figure 8.3's bubble-to-bubble MW transfer capabilities, and
NV Energy Table LF-1 (annual native energy and peak, 2025–2044).
