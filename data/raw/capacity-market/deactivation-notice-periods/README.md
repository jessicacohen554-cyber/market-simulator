# deactivation-notice-periods (raw)

Cited RTO tariff/protocol/manual provisions governing how much advance notice a
generator must give before deactivating, retiring, mothballing, or suspending
a resource, for PJM, ERCOT, and MISO -- plus each RTO's Reliability-Must-Run
(RMR) / System-Support-Resource (SSR) extension mechanism where a citable
timeline was found.

## Purpose

This is a **standalone citation dataset produced by a research-only session.
No code was edited or wired this session** -- `src/market_sim/` was not
touched, no LP was run, nothing was committed/pushed.

It exists to back (or correct) the currently-uncited code comment on
`staged_oversupply_thinning` in `src/market_sim/config/scenarios.py`, which
attributes the mechanism's multi-year exit-staging logic to "RTO
deactivation-notice periods (ERCOT §3.14 / PJM ~90-day + RMR study),
decommissioning lead time, and coal rail/take-or-pay wind-down." That comment
was written without a primary citation; this dataset is the citation
groundwork for a **future session** to correct it (the figures below both
confirm parts of the original claim and materially update others -- see
"Headline findings" below).

A second, later consumer is RC-0B's threshold-identification work (the
`staged_thinning_max_gw_per_year` GW/yr/fuel-class exit-budget cap, currently
a flat 3.0 GW default -- see the code comment for that field) -- these
notice-period figures are raw ingredients for grounding *how many years* a
large exit should plausibly be staged over, not a threshold themselves.
**Neither consumer has been wired this session.**

## Headline findings (see `notice_periods.csv` for full citations)

- **ERCOT** Nodal Protocols Section 3.14.1.1 confirms a **150-day** standard
  notice (retirement/indefinite suspension >180 days) and a **90-day** notice
  for seasonal mothballing -- both read directly from the current (2026-07-11)
  protocols document. The repo comment's "§3.14" is correct as a section
  reference; the informal "~90 days" framing is only the *seasonal-mothball*
  case, not the general 150-day rule.
- **PJM**: the commonly-repeated "~90-day" figure traces only to PJM's own
  plain-language blog/marketing copy (2019), not to a verbatim tariff quote
  this session could confirm (agreements.pjm.com's eTariff viewer is a
  JavaScript SPA this session could not render). More importantly, **PJM's
  process changed**: the current PJM Manual 14D (Revision 70, effective
  2025-12-17) codifies a materially different *quarterly filing/processing
  cadence* with a stated minimum lead of roughly 3-6 months, which PJM's own
  April-2026 fact sheet paraphrases as "at least two quarters." The repo
  comment's "~90-day" is likely stale.
- **PJM RMR study timeline**: Manual 14D Section 9.1.3 gives an actual, citable,
  current sequence (30 / 45 / 60 days) for PJM's reliability-issue
  determination process -- this is the concrete analogue to the repo
  comment's "+ RMR study" that was previously uncited.
- **MISO**: notice period increased from 26 weeks to (per consistent secondary
  sourcing) roughly a year / "four quarterly study periods," per FERC Docket
  No. ER23-630 (order 2023-02-10). MISO also has its own RMR-equivalent (a
  System Support Resource / SSR agreement, reportedly filed 60 days before
  the suspension date if reliability mitigation fails) -- see the low-confidence
  caveat on that row.
- **Coal rail/take-or-pay wind-down**: not researched this session (out of
  scope for the RTO-tariff research requested); still uncited.

## File

`notice_periods.csv` -- one row per distinct notice provision (an RTO with
multiple notice types, e.g. an initial notice and an extension/RMR-triggered
notice, gets multiple rows).

Columns: `rto, instrument, notice_period_value, notice_period_unit,
trigger_event, citation_section, effective_date, source_url, source_doc,
accessed, notes`

- `rto`: PJM | ERCOT | MISO
- `notice_period_value`/`notice_period_unit`: a single confirmed (or
  best-available, clearly flagged) number. **No field in this CSV is a
  fabricated or estimated figure** -- every value is either read directly off
  a primary document this session rendered itself, or is flagged in `notes`
  as sourced only from secondary corroboration (with the access blocker
  logged) when the primary text could not be rendered.
- `notes`: carries every nuance that doesn't fit the tabular schema --
  verbatim quotes, discrepancies found in the source itself, and (for MISO)
  explicit "not independently confirmed" flags.

Row count by RTO: ERCOT 5, PJM 5, MISO 3 (13 total).

## Sources actually rendered this session (primary)

- **ERCOT Nodal Protocols, Section 3** (Management Activities for the ERCOT
  System), dated 2026-07-11:
  `https://www.ercot.com/files/docs/2025/09/01/03-071126_Nodal.docx`. Fetched
  as a .docx (WebFetch cannot summarize it directly -- downloaded with `curl`
  and the body text extracted from `word/document.xml` with a small Python/regex
  script, since neither `pdftotext`/`pandoc`/`python-docx` nor `soffice
  --headless --convert-to txt` were usable in this environment for this file;
  unzip + regex over the OOXML `<w:t>` runs worked cleanly). Section 3.14.1
  ("Reliability Must Run") through 3.14.1.9 read in full.
- **PJM Manual 14D: Generator Operational Requirements**, Revision 70,
  effective 2025-12-17: `https://www.pjm.com/-/media/DotCom/documents/manuals/m14d.pdf`
  (230 pages; downloaded with `curl`, text extracted with `pymupdf`/`fitz`).
  Section 9 ("Generator Deactivations") read in full.
- **PJM Generation Deactivation Fact Sheet**, dated 2026-04-20 (PJM's own,
  most-current plain-language summary, confirms the Manual 14D quarterly
  cadence independently): `https://www.pjm.com/-/media/DotCom/about-pjm/newsroom/fact-sheets/generation-deactivation-fact-sheet.pdf`

## Sources rendered this session (quasi-primary / PJM-authored secondary)

- Monitoring Analytics (PJM's own Independent Market Monitor), memo to the
  Deactivation Enhancements Senior Task Force (DESTF), "IMM State of the
  Market Report discussion of Part V (RMR) issues," 2023-10-12:
  `https://www.monitoringanalytics.com/reports/Presentations/2023/IMM_DESTF_Memo_re_RMR_20231012.pdf`.
  Cites OATT §§113.1, 113.2, 114, 115, 117, 118, 119 and Attachment DD
  §6.6(g) directly, but does not itself quote day-counts for §113.1.
- PJM DESTF stakeholder materials (2024-2026): the DESTF Issue Charge
  (2024-07-24, revised 2025-03), the "DESTF Solution Package Overview"
  (2025-01-23, MRC/MC-endorsed "Package D" -- states "Units that plan to
  participate in RPM must provide at least 12 months' notice prior to desired
  deactivation date" as an *endorsed stakeholder proposal*, distinct from
  what Manual 14D's body text actually codifies), and two "FOR DISCUSSION
  PURPOSES ONLY" pro-forma RMR Service Agreement working drafts
  (2025-09-18, 2025-10-21) that confirm PJM is actively formalizing a named
  RMR contract construct that does not yet appear as a defined term in the
  OATT itself (per the IMM memo: "RMR is not defined in the PJM tariff").
- PJM Inside Lines (PJM's own blog), "What Happens When an Owner Wants to
  Close Its Power Plant?", 2019-06-11 -- source of the informal "~90 days"
  figure; likely superseded, see above.

## Sources NOT rendered this session (secondary only, corroborated but unconfirmed)

All MISO figures. See "MANUAL DOWNLOADS NEEDED" below.

## MANUAL DOWNLOADS NEEDED (blocked this session)

- **`https://agreements.pjm.com/oatt/*` and
  `https://agreements.pjm.com/eTariff/transformedTariffs/oatt/Sections/*.html`
  for OATT Part V (Sections 113-122).** Error: the `oatt/<id>` route is a
  client-rendered Angular SPA (curl returns an 844-byte shell with an empty
  `<title>`); the `.../Sections/<id>.html` route *does* serve fully
  server-rendered static HTML (confirmed working on several other section
  ids, e.g. `37226.html` for Attachment DD.6.8), but this session could not
  find the numeric document id that maps to Part V/Section 113 -- PJM's
  eTariff ids are assigned per-filing, not per-section-number, and no site
  search/sitemap endpoint was found (`sitemap.xml`, a guessed `/api/tariffs/oatt`,
  and a guessed `oatt.json` all fall back to the same 844-byte SPA shell).
  A session with either a working PJM eTariff full-text search or a
  known-good Section-113 document id could confirm the literal §113.1 clause
  text and settle the Manual-14D-revision-history discrepancy noted in the
  CSV.
- **`https://www.misoenergy.org/legal/rules-manuals-and-agreements/tariff/`**
  and every `cdn.misoenergy.org/*.pdf` / `docs.misoenergy.org/*.pdf` Attachment
  Y URL tried. Error: **HTTP 403** on every attempt -- direct `curl` (default
  and browser User-Agent), `WebFetch` (both the tariff hub page and the
  "Improvements to the Attachment Y Retirement Process" stakeholder dashboard
  page), and a Wayback Machine `archive.org/wayback/available` lookup (zero
  snapshots indexed for the wildcard tried). This matches the MISO-403
  pattern already logged in `docs/handoffs/capacity-market-intake-2026-07.md`
  ("PY2026-27 PRA Results Posting ... returned HTTP 403 on 6 repeated
  attempts"). All three MISO rows in the CSV are secondary-sourced only
  (FERC commissioner-concurrence pages and WebSearch syntheses of MISO's own
  dashboard copy) and flagged as such.
- **`https://www.ferc.gov/news-events/news/commissioner-clements-concurrence-...`**
  and **`https://www.ferc.gov/media/er23-630-000`**. Error: **HTTP 403** via
  both `curl` and `WebFetch` -- ferc.gov's news pages appear to block this
  session's automated access entirely; only WebSearch's own synthesis of
  that page's content (not a self-rendered fetch) was obtainable. The actual
  FERC order PDF for Docket No. ER23-630-000 (which would carry the verbatim
  accepted Attachment Y tariff redline) was not located/fetched.
- **`https://etariff.ferc.gov/TariffBrowser.aspx?tid=1162`** (FERC's own
  eTariff browser for MISO). Returned HTTP 200 but is itself a JS
  application shell with no server-rendered tariff text at that entry URL;
  not pursued further (would need the specific record/section deep-link,
  not just the browser root).

## Caveats / gaps

- **Coal rail / take-or-pay wind-down timing** (the third driver named in the
  original `staged_oversupply_thinning` comment) was out of scope for this
  RTO-tariff-focused research pass and remains entirely uncited.
- **Decommissioning lead time** (physical demolition/site-restoration
  timelines, as opposed to the market/reliability notice process covered
  here) was likewise out of scope and remains uncited.
- The PJM Manual-14D revision-history "12 month deactivation notification
  period" vs. the quarterly-cadence body text is a genuine, unresolved
  discrepancy in PJM's own published document -- flagged, not resolved, in
  the CSV `notes` field for the affected row. A future session should not
  silently pick one figure without re-checking whether a newer Manual 14D
  revision (>70) has since reconciled it.
- No figure in this dataset should be read as an endorsement of any specific
  value for `staged_thinning_max_gw_per_year` -- these are notice-period
  citations, not exit-rate-cap citations. Connecting the two (if warranted)
  is exactly the "future session" work this dataset is staged for, and is
  explicitly not done here.
