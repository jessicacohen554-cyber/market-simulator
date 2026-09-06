# `spp-planning` — SOURCES

Every URL below was fetched successfully on **2026-09-06** by lane SPP-12.
`www.spp.org` is **fully reachable** from a session — no login, no allowlist
problem. Checksums: `SHA256SUMS.txt`. Nothing in this directory was written from
memory.

## Host

`www.spp.org` (`spp.org` serves the same content). HTTP 200 throughout.

## How these were found (reproducible)

SPP's document tree is browsable without JS at
`https://www.spp.org/spp-documents-filings/?id=<folder-id>`; the page embeds both
its subfolder links (`?id=…`) and its file links (`/Documents/<n>/<name>`). The
site's keyword search (`https://www.spp.org/search?q=<query>&t=Documents&p=<n>`)
is **date-sorted, not relevance-sorted**, so it buries older titles under recent
FERC filings — walk the tree instead. Folder ids used:

| Folder id | Name |
|---|---|
| `20196` | Technical Reference Documents |
| `18162` | Governing (Tariff, Bylaws, Articles, Criteria, Membership/Seams Agreements, Market Protocols, Business Practices) |
| `18338` | Market Monitoring Documents |
| `18512` | Annual State of the Market Reports |
| `18516` | Offer Cap Calculation |
| `31491` | ITP Postings |
| `86112` | Resource Adequacy (empty as of 2026-09-06) |

## Tracked documents

### SPP Planning Criteria v5.0A — manifest row 12 (PRM)

- <https://www.spp.org/Documents/77092/SPP%20Planning%20Criteria%20v5.0A.pdf>
- Local: `SPP_Planning_Criteria_v5.0A.pdf` · text: `transcriptions/SPP_Planning_Criteria_v5.0A.txt`
- Found via: search `Planning Criteria`, title-filtered across 8 result pages.
- Version note: **v5.0A** is the newest of the versions the site lists
  (v4.4A, v4.5, v4.5A, v4.6, v4.7, v4.7A, v5.0, v5.0A). v5.0 is at
  `/Documents/77091/SPP Planning Criteria v5.0.pdf`; the "A" suffix is SPP's
  clean/redline pairing, so v5.0A is the one to cite.
- Used for: §4 Planning Reserve Margin table, README §1.

### SPP System Interfaces Stakeholder Reference Guide — the access-route reference

- <https://www.spp.org/media/2598/spp-system-interfaces-stakeholder-reference-guide.pdf>
- Local: `spp-system-interfaces-stakeholder-reference-guide.pdf` · text: `transcriptions/` (not extracted — small, read the PDF)
- Found via: Stakeholder Center > User Guides, APIs & Integrations.
- Why it matters: its **Public Data Specifications** section is what identifies
  the **"SPP Public Data Access"** guide — *"Reference guide for accessing public
  data via the SPP Portal and FTP"* — and states that SPP *"supports … FTP for the
  programmatic retrieval of Public Data."* That FTP route is the most promising
  unblocked path to every `portal.spp.org` product this lane could not fetch, and
  it has **not** been tried.

### Long Term PRM Policy Paper

- <https://www.spp.org/Documents/73056/Long%20Term%20PRM%20Policy%20Paper.pdf>
- Local: `Long_Term_PRM_Policy_Paper.pdf`
- Found via: Engineering > Resource Adequacy page.
- Background on the direction of SPP's PRM policy; the binding numbers are in the
  Planning Criteria, not here.

## Untracked payloads — re-fetch is the recovery route

### 2025 ITP Assessment Report v1.0 — manifest rows 11 and 13

- <https://www.spp.org/Documents/75483/2025%20ITP%20Report%20v1.0.pdf> (14.3 MB)
- Text: `transcriptions/2025_ITP_Report_v1.0.txt`
- Found via: Engineering > Transmission Planning page, which also lists the
  scopes and the older editions:
  `/Documents/70584/2023 ITP Assessment Report v1.0.pdf`,
  `/Documents/73086/2024 ITP Assessment Report v1.0.pdf`,
  `/Documents/77209/ITP Manual Version 3.3.pdf`,
  `/Documents/69814/2022 20-Year Assessment Report v1.0.pdf`.
- Used for: Figure 2.1 coincident peak (README §4 → `load-forecast/spp/`).
- **Does NOT contain** the N↔S transfer capability / SPS tie ratings manifest row
  11 expects — see README §5 for what was searched and where to look next.

### SPP MMU Annual State of the Market Reports — manifest row 10

- 2025: <https://www.spp.org/Documents/76798/2025_Annual_State_of_the_Market_Report.pdf> (6.1 MB)
- 2024: <https://www.spp.org/Documents/73953/2024_Annual_State_of_the_Market_Report.pdf> (6.4 MB)
- 2023: <https://www.spp.org/Documents/71645/2023%20Annual%20State%20of%20the%20Market%20report%20v2.pdf> (6.2 MB)
- Text: `transcriptions/ASOM_{2023,2024,2025}.txt`
- Found via: folder `18512`, which lists every edition **2009–2025** plus the
  stakeholder presentations — the full back-series is available if a rule-22
  intake later needs 2019–2022.
- Used for: the wind-curtailment series in `data/raw/spp-hsl/`.

### Integrated Marketplace Protocols 119 (Active Version) — manifest row 12

- <https://www.spp.org/Documents/77252/Integrated%20Marketplace%20Protocols%20119%20-%20Active%20Version.zip> (8.3 MB)
- Text: `transcriptions/Integrated_Marketplace_Protocols_119.txt` (from the PDF
  inside the zip; the zip also carries the same document as `.docx`)
- Version 119, stamped *SPP Public Information 7/17/2026*. The revision `119a` is
  at `/Documents/77253/Integrated Marketplace Protocols 119a.zip`.
- Found via: folder `18162`.
- Used for: §8.2.5 offer caps and floors, and Exhibit 4-1 VRL values
  (README §§2–3). **Note this is the RTO Integrated Marketplace document** — not
  `SPP Markets+ Protocols` (`/Documents/77528/SPP MarketsPlus Protocols 2.0a.zip`),
  which governs the separate Markets+ western market and must not be substituted.

## Not found on this host

| Item | Status |
|---|---|
| N↔S transfer capability / SPS tie MW ratings (row 11) | **open** — not in the 2025 ITP Report; candidates listed in README §5 |
| A published SPP wind-curtailment **percentage** (row 10) | **does not exist** in the ASOMs — they publish average hourly MW; see `data/raw/spp-hsl/` |
| SPP long-term load forecast as a standalone LTLF edition (row 13) | **partial** — the ITP peak series stands in; see `data/raw/load-forecast/spp/SOURCES.md` |

---

## Appended 2026-09-06 by lane SPP-13 — the FTP-route reference and the row-11 sweep

Every URL below was fetched successfully on **2026-09-06** by lane SPP-13 (`www.spp.org`,
HTTP 200 after one 301 to the lower-cased path). Checksums: `SHA256SUMS.txt`. Nothing here
came from memory. FINDING: `docs/handoffs/FINDING-spp-13-2026-09-06.md`.

### Where the "SPP Public Data Access" guide actually lives (reproducible)

Folder walk from Technical Reference Documents `?id=20196` → **Technical Specifications
`?id=20954`** → **Public Data `?id=21005`** (the CUF tree — not the Stakeholder Center
menu path the System Interfaces guide describes). `?id=21005` holds the access guide plus
three subfolders: `?id=21074` Current Public Data Tech Specs (v35 guide zip, Settlements
guide v2.11, Transoutage spec, WEIS guides), `?id=21073` Archived (every Markets guide
v3…v33 back to 2013), `?id=21075` Future (empty 2026-09-06).

### SPP Public Data Access, v3.0 (July 2023) — THE FTP route reference

- <https://www.spp.org/Documents/28853/SPP%20Public%20Data%20Access%2020230707.pdf>
- Local: `SPP_Public_Data_Access_20230707.pdf` · text: `transcriptions/SPP_Public_Data_Access_20230707.txt`
- 5 pages. Printed p. 1: UI access = `https://portal.spp.org` (MTE `https://portal-mte.itespp.org`).
  Printed p. 2, verbatim: *"Programmatic (API) access to public data is via FTP."*
  Production **`ftp://pubftp.spp.org`**, Member Test **`ftp://pubftp-mte.itespp.org`**.
  The document states no credential.

### SPP Markets Public Data Guide and Samples v35 — the FTP path layout + every product's schema

- <https://www.spp.org/Documents/75871/SPP%20Markets%20Public%20Data%20Guide%20and%20Samples%20v35.zip> (82.6 MB, **NOT tracked**)
- The zip's guide, `SPP Markets Public Data Guide--v35.docx`, is tracked here byte-identical as
  `SPP_Markets_Public_Data_Guide_v35.docx`; plain text (document.xml stripped, paragraph per line):
  `transcriptions/SPP_Markets_Public_Data_Guide_v35.txt`.
- **FTP Site Access** (guide p. 11), verbatim: *"User: anonymous · Password: 'Leave blank here' ·
  When accessing the ftp site programmatically use the following: User: anonymous · Password:
  <use an email address>"* — i.e. **anonymous FTP; no Marketplace credential is required.**
- The guide's "Data Locations Summary" (its pp. 8–10) gives every product's Portal page AND FTP
  folder; the per-product file-name grammar follows (pp. 12–22). The folders this program needs are copied
  into each `data/raw/spp-*/SOURCES.md`.
- The 71 sample files are real SPP publications (dated Sep 2025 – Feb 2026). Three are full-span
  payloads and were landed raw: `GenMix_2024_SPP.csv`, `GenMixYTD_SPP.csv` → `../spp-genmix/`;
  `Peak_Load_by_Month.csv` → `../spp-hourly-load/`. The rest are one-day/one-interval schema
  samples and are recorded as schema rows only.

### Row 11 sweep — the four candidate documents, all fetched

| Document | URL | Local | N↔S / SPS-tie MW figure? |
|---|---|---|---|
| ITP Manual v3.3 (76 pp.) | <https://www.spp.org/Documents/77209/ITP%20Manual%20Version%203.3.pdf> | `ITP_Manual_v3.3.pdf` + txt | **No** — methodology only; the constraint list it defines (§10) is posted to GlobalScape |
| 2022 20-Year Assessment Report v1.0 (102 pp.) | <https://www.spp.org/Documents/69814/2022%2020-Year%20Assessment%20Report%20v1.0.pdf> | txt only (5.3 MB, NOT tracked) | **No** — project portfolio; N–S flow is discussed qualitatively (§5.3.9 Potter–Tolk, printed p. 84) with no MW rating |
| 20-Year Assessment Manual (17 pp.) | <https://www.spp.org/Documents/59716/20_Year_Assessment_Manual.pdf> | `20_Year_Assessment_Manual.pdf` + txt | **No** — states only that constraint ratings come from powerflow Rating A/B (printed p. 12) |
| ITP Postings folder (781 documents) | <https://www.spp.org/spp-documents-filings/?id=31491> | two transmittals tracked | **No public MW** — see the two constraint-assessment transmittals below |
| 2025 ITP Constraint Assessment for Approval (12-02-2024) | <https://www.spp.org/Documents/72772/2025%20ITP%20Constraint%20Assessment%20for%20Approval%20(12-02-2024).pdf> | `2025_ITP_Constraint_Assessment_for_Approval_2024-12-02.pdf` + txt | Names the interfaces **`SPPSPSTIES`** and **`SPSNMTIES`** (p. 1) whose ratings were "relaxed"; the ratings workbook is on GlobalScape, NDA/CEII |
| 2026 ITP Constraint Assessment Posting (02-04-2026) | <https://www.spp.org/Documents/75904/2026%20ITP%20Constraint%20Assessment%20for%20Review%20(02-04-2026).pdf> | `2026_ITP_Constraint_Assessment_for_Review_2026-02-04.pdf` + txt | Same: workbook `2026 ITP Constraint Assessment_02042026.xlsx` under GlobalScape ITP → NCD (CEII, RSD) → NDA |

The 20-Year Assessment Manual's real filename was recovered from the Transmission Planning
page (`https://www.spp.org/engineering/transmission-planning/`), which also lists the 2022
20-Year Assessment Scope (`/Documents/63932/`) and Report Addendum (`/Documents/69815/`) —
neither fetched; both are scope/addendum documents of the same project-portfolio kind.

### Appended 2026-09-06 by lane SPP-14 — three measured members of the v35 guide zip, landed raw (SPP-DESK addendum r#4 am.1)

- Source: the same zip as the SPP-13 row above,
  <https://www.spp.org/Documents/75871/SPP%20Markets%20Public%20Data%20Guide%20and%20Samples%20v35.zip>
  (82,643,996 B; re-fetched 2026-09-06 over HTTPS after a 301 to the lower-cased path
  `/documents/75871/spp%20markets%20public%20data%20guide%20and%20samples%20v35.zip`; sha256
  `e2e8478bc8b0fd5fba8201b4c1f4197a4983d88a2406d710cba2fe230cdebee7`, byte-identical to SPP-13's).
- Members extracted unmodified (`zipfile`, no re-encoding): `SL_to_Pnode_to_Zone_with_Area.csv`,
  `Hub_Definitions.csv`, `TieFlows_Sep2025.csv`. Checksums in `SHA256SUMS.txt`; schema and row
  counts in `README.md` §"Appended 2026-09-06 by lane SPP-14".
- Licence: SPP's Terms & Conditions (<https://www.spp.org/terms-conditions/>, read 2026-09-06),
  verbatim: *"Permission is implicitly granted to copy and distribute (via computer network or
  printed form) in whole or in part (with appropriate citation) EXCEPT when such materials will be
  used, in whole or in part, within a commercial publication (printed or otherwise) or when the
  author(s) or SPP will be quoted in commercial materials, forums or publications. Any commercial
  use of these materials requires prior, express written authorization from the author(s) or a
  duly authorized officer of SPP."*
