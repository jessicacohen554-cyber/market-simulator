# miso-pra — raw

`miso_pra_clearing_prices_2023-2026.csv` — MISO Planning Resource Auction
(PRA) clearing prices by planning year / season / zone scope.

**Source and regeneration status: see `SOURCES.md` in this directory** —
primary MISO auction-summary PDFs are blocked by this environment's network
allowlist (`misoenergy.org`/`cdn.misoenergy.org` return HTTP 403), so the
figures were transcribed from public secondary reporting (Utility Dive, Enel
North America) with the primary `cdn.misoenergy.org` PRA-results PDF URLs
recorded for a future direct check. **Hand-assembled — no script reads or
regenerates this file** (`grep -rl "data/raw/miso-pra"` across `scripts/`
and `src/` finds nothing); refreshing it means re-doing the manual
transcription in `SOURCES.md` against the next auction cycle's results.

**Licensing note:** MISO's redistribution terms are unverified (site terms
pages 403 to automated fetch) — see `docs/data-licensing.md` §7.
