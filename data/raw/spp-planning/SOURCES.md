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
