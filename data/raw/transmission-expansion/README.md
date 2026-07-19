# transmission-expansion — committed transmission-expansion registry

One hand-curated CSV per ISO (`<iso>.csv`, canonical columns of
`data/dictionary/schema/transmission-expansion.schema.yaml`), holding every
transmission project bound by an enforceable public instrument (ISO board /
RTO plan approval with cost allocation, state-regulator order, executed state
contract, or physical construction/energization) that changes — or documents a
committed change adjacent to — the model's reduced zonal topology from 2026
on. Curated by `scripts/data/curate_transmission_expansion.py` into
`data/clean/transmission-expansion/<ISO>/`; consumed forecast-forward-only by
`market_sim.data.transmission_expansion` under
`ScenarioConfig.transmission_expansion_enabled` (default off). Research record:
`docs/transmission-expansion-methodology-2026-07.md` (grounding tables, field
survey, delta ledger, V1 exclusions) and
`docs/handoffs/transmission-expansion-grounding-2026-07.md` (session record).

Status vocabulary is CLOSED: `energized | under_construction |
approved_funded`. Roadmap / study / recommended-but-unapproved projects are
NEVER rows — they live on the watchlist below (the confirmed-retirements
announced-exclusion convention, CLAUDE.md rule 13). Where an instrument is
committed but NO transfer-capability MW is published, the row carries
`delta_mw = 0.0` with a `mapping_note` explaining (rule 5: numbers are never
guessed) — the project is documented, dispatch-inert, and re-rated when the
ISO publishes a rating.

## Delta convention (read before editing ANY row)

Every `delta_mw` is ADDITIVE to the ISO's **base-static vintage** — the year
whose measured/published limits the static `config/iso_configs.py` TTCs and
InterfaceLimit caps embed
(`data.transmission_expansion.TRANSMISSION_BASE_STATIC_VINTAGE`):

| ISO | vintage | base statics it protects |
|-----|---------|--------------------------|
| ERCOT | 2024 | measured 2023-24 NP6-86 GTC medians (WESTEX 7,300+2,700; PNHNDL 2,680; NE_LOB 1,300/1,788) + interior estimates |
| CAISO | 2023 | WECC Path Rating Catalog (P15 5,400 / P26 4,000 / COI 4,800 / WOR 10,623) + LCT-2023 pocket caps + fitted 7,500 simultaneous |
| MISO | 2025 | PY2025-26 LOLE CIL/CEL groups + JOA RDT 3,000/2,500 |
| PJM | 2024 | 2024 transfer-limits/flows postings |
| NYISO | 2025 | measured 2024-25 DAM Central-East mean (2,850 — ALREADY post-AC-Transmission Segment A/B) |
| NEISO | 2023 | RSP interface limits + 3,850 ICR tie-benefit cap (pre-NECEC) |

The loader admits a row only when `in_service_year` is STRICTLY AFTER the
vintage, so a project embedded in a measured base (NYISO AC Transmission,
Smart Path Connect's phased 2025 energizations) can never double-count.
Each row's `mapping_note` states what its delta is additive to.

**Re-mapping trigger (WP-A):** if the ERCOT West/Panhandle topology split
(`docs/handoffs/ercot-vre-curtailment-topology-scope-2026-07.md` WP-A) ever
lands — a Far_West zone + re-cut West links — every ERCOT row keyed
`(West, North)` / `(West, South_Central)` must be re-mapped before the channel
is used on the new topology (curation hard-fails on unresolvable pairs, which
is the intended tripwire).

## Sources (sha256-pinned)

`scripts/data/fetch_transmission_expansion_sources.py` re-downloads the pinned
primary documents into `md/` (PDF → page-marked markdown via pdfplumber,
`--to-markdown`). `md/README-SOURCES.md` carries the generated sha256 table +
MANUAL DOWNLOADS NEEDED rows (proxy/bot-walled primaries are
documentation-only until fetched — never transcribed from memory). Committed:
the sha256 table + the CAISO SWIP-North decision-deck conversion (the one
fetched primary behind an applied nonzero delta). NOT committed (regenerate
locally with the fetch script; the sha256 pins are the integrity anchor): the
source PDFs/`.ashx` binaries and the other conversions (PJM whitepapers ×3,
ERCOT PBRP study, CAISO TPP decks — none backs an applied nonzero delta; the
applied MISO/ERCOT deltas' primaries are the four MANUAL rows).

## Watchlist (NOT committed — do not add rows until an instrument exists)

- **ERCOT**: 765 kV CCN ROUTE orders all pending as of 2026-07-19 (PUCT abated
  Docket 59029 June 2026; Dinosaur-Longshore decision anticipated Aug 2026;
  legislator amicus urging deferral) — plan-level approval stands, watch for
  route orders and 2028-2030 COD slippage. STEP expansions beyond the Core
  Plan (2025 RTP "potential future 765 kV expansions"). CPS Bexar reactive
  projects (voltage support, not transfer).
- **MISO**: Tranche 2.2 + South LRTP scoping starts 2026 (any future RDT /
  Midwest-South transfer change comes from these — the RDT 3,000/2,500 has NO
  committed change). JTIQ 5-project seam portfolio (boards approved Dec 2024,
  DOE GRIP $464.5M) is **subscription-contingent with no fixed CODs** — never
  model as firm until the 24,310 MW generator-subscription trigger is met.
  RE-QUERY: MISO Tranche 2.1 per-LRZ CIL/transfer table (MTEP24 report
  appendix — not in public summaries; the lrtp-t21 row stays 0.0 until found).
  Risk: five-state FERC complaint EL25-109 vs the T2.1 MVP basis (pending).
- **NYISO**: Clean Path NY Tier 4 contract mutually terminated 2024-11-27
  (dead). NYC OSW PPTN public-policy need rescinded 2025-07-17 (terminated).
  RE-QUERY: NYISO LI interface transfer-limit postings once Propel NY re-rates
  them (the propel-ny row stays 0.0 until published).
- **NEISO**: ISO-NE Longer-Term Transmission RFP #1 (Maine wind / North-South
  relief): bids closed 2025-09-30, preferred-solution selection expected
  ~Sep 2026 — promotes to a row (North-Central uplift) when selected + funded.
  Twin States Clean Energy Link: dead (National Grid withdrew 2024-03).
  RE-QUERY: next ICR tie-benefit study for a published post-NECEC
  simultaneous-import cap (rule-23 trigger on the necec--hq_simultaneous row).
- **CAISO / WECC**: Trout Canyon-Lugo 500 kV (2025-26 TPP approved, Phase 3
  sponsor bid window closes 2026-09-25 — promotes to `approved_funded` on
  sponsor selection; the largest committed-track change to the import
  topology). Path 15 Whirlwind/Windhub-Tesla concept + Path 26 S-N RAS
  (deferred to the 2026-27 TPP cycle). Greenlink North (BLM issues; ~2028).
  B2H + Greenlink West (PNW/NV internal, deeper WECC — supply-side context
  only). PDCI capacity-increase studies (BPA/LADWP, study-stage). Advisory RA
  MIC 2027-2036 stays ~15.3-16.0 GW flat — no committed MIC uplift published
  (methodology §6 documents the SWIP-North entitlement tension).

## Row counts (2026-07-19 intake)

ERCOT 9 (2 applied: STEP WTX-export split +2,555/+945 @2032) · MISO 6
(5 applied: Tranche 1 CIL uplifts @2030) · NYISO 3 (0 applied) · NEISO 2
(2 applied: NECEC +1,200 link + simultaneous @2026) · PJM 6 (0 applied) ·
CAISO 9 incl. 1 superseded audit row (1 applied: SWIP-North simultaneous
+1,117.5 @2028). "Applied" = `link`/`interface` rows with nonzero delta
admitted by the loader; every other row is documentation (0-delta or
recorded-not-applied `import_tranche`/`intra_zonal`).
