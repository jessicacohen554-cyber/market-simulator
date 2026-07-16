# Declared capacity-emergency event windows (raw)

Hand-curated, per-ISO registries of **publicly declared capacity-emergency
instruments** — the M-1 datatype of the MISO price-formation lane
(`docs/handoffs/miso-price-formation-design-2026-07.md` §3/M-1). One row per
(declaration, region) at or above the lowest capacity-ladder rung; for MISO the
pre-2026 ladder is Capacity Advisory → Maximum Generation Alert → Maximum
Generation Warning → Maximum Generation Event Steps 1–5 (2023 MISO SOM p.10
enumerates each level's pricing/capacity effects; MISO's 3-step simplification
takes effect 2026-06-01, KA-01551, outside this registry's 2023–2025 window).

Each ISO's rows live in `<iso>/<iso>.csv` in the canonical schema
(`data/dictionary/schema/maxgen-events.schema.yaml`), with window endpoints in
the ISO's **operating time** (`start_local`/`end_local`; MISO market operations
run on EST = UTC−5 year-round — Tariff Module A "Eastern Standard Time"
convention, and the IMM quarterly's own hour lists are stated in EST). The
curation parser converts to UTC via the per-ISO registry spec
(`scripts/lib/maxgen_events/`).

## F4 discipline (pre-declared, absolute)

**A window with no primary document does NOT enter the registry.** Windows are
never reconstructed from price spikes or from a model residual
(design §M-1/§5-F4). Rows record exactly what the primary document declares:
level, region scope, and endpoints — with `declared_precision='day'` when the
document scopes only the day, never hours invented to fit anything.

## Source ladder (primary, durable)

1. MISO OASIS `Capacity_Emergency_Historical_Information.pdf`
   (`oasis.oati.com/woa/docs/MISO/MISOdocs/`) — the standing declaration
   record. **STILL UNREACHABLE from the session egress (CONNECT 502, policy
   denial) as of 2026-07-16**; when it lands, upgrade SOM-sourced rows in
   place (same windows, better endpoint precision) and cite it.
2. MISO monthly Operations Reports / Informational Forum decks
   (`cdn.misoenergy.org`) — **403-blocked** from the session egress.
3. Potomac Economics (IMM) State of the Market reports + quarterly IMM
   reports — **reachable**, and the current provenance for every committed
   row. The IMM is MISO's independent market monitor; its SOM/quarterly event
   accounts are primary at the event level (the M-1 findings memo already
   treated "the 2023 SOM emergency table" as sufficient for the 2023 window).

MISO's live notification feed deletes after 30 days — NOT a source.

## Documented ABSENCES (adjudicated, deliberately no row)

- **Jan 14–17 2024 (Winter Storm Heather):** the 2024 MISO SOM (p.10) states
  MISO "effectively managed the system without recourse to Emergency
  operations"; the only instrument was **Conservative Operations on Jan 14**
  (bad transmission-flow data, SOM p.11 Fig 7 annotation) — below the ladder.
  All 24 of 2024's DA tail hours fall in this window: the 2024 C3c gap is NOT
  an emergency-window phenomenon (winter fuel-supply/derate/congestion lane).
- **Jan 2025 (Winter Storm Enzo):** no declaration — operators raised DA/RT
  STR requirements instead (2025 SOM p.iii). The raised requirements are
  already the model's measured-reserve-requirements channel.
- **Feb 20–21 / Sep 29 2025 tail hours:** no capacity declaration found in the
  2025 SOM or quarterlies. Sep 16 2025 carried a **Local Transmission
  Emergency** (500 kV outage, MISO South, 2025 SOM p.43) — a transmission
  instrument, outside this registry's capacity ladder.
- Conservative Operations days (Jun 22/25, Jul 15 2025; Aug 23–27 2024) and
  the Jul 30 2025 Severe Weather Alert are below/outside the capacity ladder.
- Alerts preceding the Aug 26 2024 Warning: the 2024 SOM says alerts "escalated"
  to the Warning but states no dates — not registrable per F4.

## DATA NEEDED

- OASIS `Capacity_Emergency_Historical_Information.pdf` (2023–2025 vintage) —
  owner access item; upgrades endpoint precision of day-level rows and
  confirms/extends ladder coverage (esp. sub-Event levels the SOMs summarize
  only in figures).
- Other ISOs: no analog rows yet; the registry is additive per ISO (a new
  `<iso>/` subdir + a registered spec) when another ISO's lane needs one.
