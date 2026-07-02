# PP-11 — Run-Report Restyle (codebase-site design system)

**Upstream:** ADR 0014 (reporting deliverable), PP-09 (renderer).
**Targets:** `src/lce_portfolio/report.py` (the `_CSS`/`_JS` chrome and section
markup only).
**Status:** done (2026-07-02).

## What was done

Pure re-skin of the ADR 0014 HTML run report onto the parent repo's
codebase-exploration site design system ("Observatory" tokens,
`docs/codebase-site/css/shared.css` / `bc-pages.css`). No payload or behavior
change: the §3 payload contract and `payload_version` are untouched,
`render_report()` remains a pure function of the payload (same payload →
byte-identical HTML), and `outputs.py` report assembly was not touched.

- **Tokens.** The site's palette is vendored inline as CSS custom properties:
  page `#F8F9FC`, white cards on `--border-light #E5E7EB` with the site's
  radius/shadow scale, text `#000` / `#1E293B` / `#566370`, navy
  `#1A2744`/`#0F1A2E` dark surfaces.
- **Header band.** The report title + §2.1 provenance now live in a navy
  gradient band (the site's dark-section idiom) with on-dark text colors, a
  glass provenance card, and the solar→wind→hydro→nuclear energy-divider
  accent. The `.solve`/`.solve-bad` chips are restyled as the site's pill
  badges (green/red tints with AA-safe on-dark text).
- **Series colors.** Resources map onto the site fuel palette (solar
  `#F59E0B`, wind `#22C55E`, hydro `#0EA5E9`, nuclear `#6366F1`, gas
  `#6B7280`, storage `#E67E22`, ccs `#26A69A`, hydrogen `#10B981`) via a
  keyword rule table with categorical fallback slots; per-ISO series use the
  site ISO palette. The §2.7 heatmap ramp and SOC trace colors moved onto the
  same system (bc-pages `.color-ramp` blue→red ramp; fuel-mapped SOC lines,
  mirrored in the inline JS).
- **Tables.** Data-table idiom (navy uppercase header row, zebra stripes,
  tabular numerals), each table inside its own `overflow-x:auto` `.table-wrap`
  so the page body never scrolls sideways at mobile widths.
- **Self-containment (ADR 0014 §1/§6).** The site's Google Fonts `@import`
  was deliberately NOT copied — the report uses the same font-family stacks
  with local/system fallbacks only, and a new smoke test asserts the emitted
  HTML contains no `http://`, `https://`, `@import`, or `//fonts.` reference.

## Acceptance

- Full suite green (172 tests), including the new
  `test_report_html_has_no_external_references` smoke test and the
  byte-stable regeneration test against the re-rendered committed sample run
  (`results/SAMPLE_premium_cap_20260702-171842/report.html`).
- Standalone check clean (no `market_sim` import); the report has no view-time
  dependency on `docs/codebase-site/` or `frontend/` files.
- Verified visually at desktop and 390-px mobile widths (no horizontal page
  scroll; AA-safe text on both light cards and the navy band), including the
  conditional §2.5/§2.6 views and the non-optimal solve flag.
