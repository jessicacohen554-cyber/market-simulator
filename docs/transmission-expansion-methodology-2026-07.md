# Transmission-expansion forward channel — methodology & grounding (FF-G1)

**Date:** 2026-07-19 · **Session:** transmission-expansion-grounding (handoff:
`docs/handoffs/transmission-expansion-grounding-2026-07.md`) · **Status:**
landed, GATED default-off (`ScenarioConfig.transmission_expansion_enabled`)

The forecast's network topology was frozen at base-year statics: `ttc` was
computed once before the year loop and reused for all 25 forecast years, so
board-committed builds (NECEC, the ERCOT 765 kV program, MISO LRTP) were
invisible to 2026–2050 dispatch, congestion, and zonal basis. This document is
the standing reference for the channel that fixes that: what the registry
holds, how deltas are grounded and mapped onto the reduced topology, how the
channel applies them, what the field does, and what is deliberately excluded.

## 1. Design

- **Registry datatype** `transmission-expansion` (schema:
  `data/dictionary/schema/transmission-expansion.schema.yaml`; raw:
  `data/raw/transmission-expansion/<iso>.csv` + README + sha256-pinned `md/`
  sources; curation `scripts/data/curate_transmission_expansion.py` with live
  topology-resolvability validation; lib
  `scripts/lib/transmission_expansion/`). One row per (project, affected model
  element). Closed vocabularies: `status_tier ∈ {energized,
  under_construction, approved_funded}` (roadmap/planned excluded by
  construction — the confirmed-retirements announced-exclusion convention),
  `target_kind ∈ {link, interface, import_tranche, intra_zonal}`,
  `capacity_basis`, `mapping_confidence`.
- **Admissibility (rule 13).** A registry row is a *reproducible market/physical
  input*: a board/regulator instrument with a date and an in-service year
  regenerates for any forward year and responds to changed conditions (a
  cancellation supersedes the row — see the Serrano–Del Amo–Mesa audit row).
  Nothing here is fitted to any residual; where an instrument publishes **no
  MW**, the row carries `delta_mw = 0.0` and is dispatch-inert (rule 5:
  numbers are never guessed).
- **Delta convention (rule 14).** Every delta is *additive to the ISO's
  base-static vintage* (`data.transmission_expansion.TRANSMISSION_BASE_STATIC_VINTAGE`; table in
  the raw README). The loader admits a row only when `in_service_year` is
  strictly after the vintage, so projects already embedded in a measured base
  (NYISO AC Transmission inside the 2024-25 Central-East mean) never
  double-count. Where the published figure sits on a different basis than the
  model's static (ERCOT's 12.7 GW WTX-export *rating* vs. the model's
  10.0 GW *measured-median* statics; MISO's Future-1-2040 CIL table vs. the
  PY2025-26 LOLE base), the **delta** is transferred, never the level, and the
  row's mandatory `mapping_note` documents the reconciliation.
- **Consumption seam.** `market_sim.data.transmission_expansion`:
  `load_transmission_expansions(iso, required=…)` (fail-loud W2-E/G12
  contract cloned from `data.confirmed_retirements` — with the gate on in
  forecast mode, a never-curated checkout raises rather than silently running
  the frozen-topology forecast) → per solve year,
  `apply_transmission_expansion(iso_config, iso, year, rows)` adds the
  cumulative in-service deltas to matching `TransferLink.ttc_mw` (exact
  listed orientation first, so a one-way pair's legs are targeted
  independently; reversed orientation otherwise) and named
  `InterfaceLimit.cap_mw` (+ `reverse_cap_mw` only where the limit declares
  one), `validate_topology()` on change, and **returns the same object when
  nothing applies** — the byte-identity guarantee. Wiring:
  `runner.run_scenario_iso` per-year `year_ttc` seam (the CAISO
  per-year-import-caps pattern); when an interface cap moved, the
  declared-limit groups are rebuilt and any corridor extension groups
  re-appended verbatim.
- **Gate.** `transmission_expansion_enabled: bool = False`, member of
  `_CACHE_KEY_OPTIONAL_FIELDS` (default-off drops from the hash → every
  existing cache key byte-stable; ON is a distinct scenario key), coerced off
  in backcast **and** hindcast in `__post_init__` (V1 has no RC-1B
  `instrument_date` information gate — a 2021-vintage hindcast must not know
  about a 2024 board approval, so the harness is excluded rather than wrong).
  CLI: `scripts/run_full_horizon.py --transmission-expansion`.

## 2. Survey — how the field treats forward transmission (plan §4 house style)

| Model / practice | Treatment | Verdict here |
|---|---|---|
| **EPA IPM (Post-IRA 2023)** | Inter-region bulk TTCs from NERC/ITCS assessments, held largely static; announced builds added exogenously when firm | **Adopted**: exogenous committed-build deltas on static inter-zone limits |
| **NREL ReEDS** | Base inter-BA limits + *endogenous* transmission investment as a decision variable (cost-optimized GW-mi) | **Rejected** for V1: endogenous expansion is a co-optimization the LP does not carry; committed-registry exogenous deltas first (an endogenous screen would be its own chartered mechanism) |
| **EIA NEMS/EMM** | 25-region firm limits, updated per cycle from NERC filings; committed projects folded into reference case | **Adopted** (per-cycle registry refresh = rule-23 trigger) |
| **GenX / PLEXOS-LT / Aurora practice** | Study-defined: committed projects in the base network; speculative expansion only as scenario | **Adopted**: committed-only base evolution; speculative = watchlist, never rows |
| **ISO planning practice** (RTEP/MTEP/TPP/RSP/PBRP) | The instruments themselves — board approvals with cost allocation are the commitment line | **Adopted** as the status-tier bar (mirrors the confirmed-retirements instrument standard) |

The channel therefore sits squarely in the mainstream exogenous-committed
pattern; endogenous/economic transmission expansion is explicitly out of scope
(a future L-CAP-adjacent charter if ever wanted).

## 3. Sources intaken

Pinned copies + page-marked markdown conversions live in
`data/raw/transmission-expansion/md/` with the generated sha256 table
`md/README-SOURCES.md` (fetch:
`scripts/data/fetch_transmission_expansion_sources.py --to-markdown`).
Fetched & pinned (7): CAISO SWIP-North decision (Dec 2023), CAISO 2025-26 and
2023-24 TPP decision decks, PJM board whitepapers Dec 2023 / Feb 2025 /
Feb 2026, ERCOT PBRP Study July 2024 (RTO Insider mirror of the PUCT 55718
filing). **MANUAL DOWNLOAD NEEDED (4)**: the two MISO documents
(`cdn.misoenergy.org` bot-walls the sandbox proxy — MTEP21-Addendum Tranche 1
Report [the Table 7-3 CIL deltas], Tranche 2.1 fact sheet) and the two ERCOT
December 2025 board items (exact `ercot.com/files/docs` filenames unverified);
their numbers were transcribed from the research agents' fetched pages (URLs
per row) and must be re-verified against pinned copies by a browser-access
session — the `verified=0`-style caveat of the capacity-cost intake.

## 4. Per-ISO grounding tables (2026-07-19 intake)

**Applied rows** (nonzero delta, `link`/`interface`) — the complete list:

| ISO | Row | Element (base) | Δ MW | Year | Instrument | Confidence |
|-----|-----|----------------|------|------|-----------|------------|
| NEISO | necec--hq_north | HQ_import→North link (900) | +1,200 | 2026 | MA 83D + HQ TSA; energized 2026-01-16 | exact |
| NEISO | necec--hq_simultaneous | HQ_import_simultaneous cap (3,850) | +1,200 | 2026 | same | reconciled |
| CAISO | swip-north--wecc_simultaneous | WECC_import_simultaneous cap (7,500) | +1,117.5 | 2028 | CAISO Board Addendum 1 (2023-12-14) N→S ISO entitlement; IPUC CPCN | reconciled |
| MISO | lrtp-t1--cil_west | MISO_CIL_West cap (6,025) | +658 | 2030 | MISO Board MTEP21-Addendum (2022-07-25), Table 7-3 | reconciled |
| MISO | lrtp-t1--cil_plains | MISO_CIL_Plains cap (9,635) | +1,443 | 2030 | same (LRZ3 +1,391 + LRZ5 +52) | reconciled |
| MISO | lrtp-t1--cil_illinois | MISO_CIL_Illinois cap (8,649) | +492 | 2030 | same | reconciled |
| MISO | lrtp-t1--cil_indiana | MISO_CIL_Indiana cap (8,650) | +166 | 2030 | same | reconciled |
| MISO | lrtp-t1--cil_east | MISO_CIL_East cap (7,949) | +2,327 | 2030 | same (LRZ2 +1,035 + LRZ7 +1,292) | reconciled |
| ERCOT | step-backbone--west_north | West↔North link (7,300) | +2,555 | 2032 | ERCOT Board 25RPG022/25 (2025-12-09): WTX export GTC 12.7→16.2 GW, split 8:3 per the WESTEX convention | reconciled |
| ERCOT | step-backbone--west_south_central | West↔South_Central link (2,700) | +945 | 2032 | same | reconciled |

Notable **documentation rows** (0-delta or recorded-not-applied): ERCOT
PBRP 765 import paths (+2,105 MW combined N-1 Permian import — recorded 0.0:
an import-direction increment cannot land on the export-basis symmetric WESTEX
links without double-counting the STEP export re-rate; §6), STEP
Watermill–Martin Lake vs the NE_LOB pair, RGV + SASR (South), PJM's six RTEP
corridors (no published interface MW anywhere in PJM board documents), NYISO
CHPE (import_tranche into NYC, 1,250 MW) + Propel NY (no published TTC; also
needs a Long_Island–Lower_Hudson path the topology lacks), CAISO
Gates–Los Banos No. 3 series comp (Path 15, no published MW),
IV–NoSONGS/NoSONGS–Serrano (2032-33 SDGE/LA_BASIN boundary rework, no
published import-cap delta), SunZia/Ten West/TransWest/NG-IV2
(WECC supply-side), Humboldt OSW (intra-NP15), Smart Path Connect
(intra-Upstate_West), and the superseded Serrano–Del Amo–Mesa cancellation
audit row.

## 5. Consumption seam (exact)

`runner.run_scenario_iso`: expansions loaded once pre-loop under
`mode=="forecast" and not hindcast and transmission_expansion_enabled`
(`required=True` → fail-loud). Per year, after the CAISO per-year import-cap
block: `apply_transmission_expansion(_year_iso_config, iso, year, rows)`;
if changed → `year_ttc = get_ttc_array(...)`, and if `interface_limits`
changed → `build_interface_groups(...) + corridor-extension groups`;
`DispatchSpec(ttc=year_ttc, interface_groups=year_interface_groups or None)`.
Incidence and `link_bidirectional` are topology-order-only and never change.

## 6. Known gaps / V1 exclusions (each a named follow-up, none silent)

1. **Import-tranche energy depth** — `import_tranche` rows (CHPE 1,250 MW into
   NYC, SunZia/TransWest/Ten West/NG-IV2 behind WECC_import) are
   recorded-not-applied: the priced import fleet is built once pre-loop
   (`IMPORT_TRANCHES`) with no per-year seam. Follow-up: a per-year
   import-tranche depth channel at the same seam.
2. **ERCOT import-direction representation** — the PBRP +2,105 MW Permian
   import increment needs a one-way-pair split of the West links (the NE_LOB
   recipe) before it can be applied without loosening the export envelope;
   deliberately deferred (also keeps this channel disjoint from the WP-A
   backcast topology charter — see the README re-mapping trigger).
3. **Hindcast information gate** — the channel is coerced off under
   `hindcast=True`; an RC-1B-style `instrument_date <= as_of` gate would let
   T1-H legs use it honestly.
4. **No-published-MW corridors** — PJM RTEP (all six rows), Propel NY,
   Gates–Los Banos No. 3, IV–NoSONGS: re-rate when the ISO posts measured
   transfer limits / LCT rows post-COD (the PJM path deliberately converges
   with the existing measured `transfer-interface-limits` intake).
5. **MISO Tranche 2.1 quantification** — no public per-LRZ CIL table; the
   lrtp-t21 row stays 0.0 until the MTEP24 appendix is intaken (README
   re-query item). FERC EL25-109 risk noted on the row.
6. **SWIP-North vs. advisory MIC tension** — CAISO's advisory RA MIC series
   (~15.3–16.0 GW flat to 2036) holds new branch groups at 0 until import
   history exists, while the board-approved 1,117.5 MW ISO entitlement is a
   deliverability acquisition; the registry applies the entitlement to the
   *fitted* 7,500 MW simultaneous default (audit C-5 fallback — forecast
   mode). Runs with `capacity_deliverability_limits` on (backcast MIC mode)
   never reach this path (backcast coercion). Revisit when CAISO publishes a
   MIC-expansion decision (rule-23 trigger).
7. **Topology-missing paths** — STEP Martin Lake–Hillje (Northeast–Houston)
   and Propel's Long_Island–Lower_Hudson ties have no model link to uplift;
   documented in row notes, candidates for a topology charter if their
   corridors start binding in actuals.
8. **In-service risk is not modeled** — `in_service_year` is the committed
   projection at intake (schedule-risk notes per row: ERCOT 765 route cases,
   PJM CPCN fights); a slipped COD is a registry *data update* (rule 23:
   re-derive on source change), not a scenario knob.

## 7. Verification record (2026-07-19)

- Unit/integration: `tests/test_transmission_expansion.py` +
  `tests/test_curate_transmission_expansion.py` (32 tests: loader filters,
  fail-loud contract, cumulative stacking, COD gating, orientation rules,
  same-object no-op identity, unmatched-element skip, config
  coercions, cache-key membership/stability) — green; full suite green.
- Cache keys: `ScenarioConfig().cache_key()` byte-identical with the field at
  default; ON produces a distinct key.
- Byte-identity A/B: NEISO 2026 single-year forecast, pre-change code
  (e87bf7d snapshot) vs. changed code with the flag off — result frames
  `equals()=True`, objective values exactly equal; the only parquet byte
  differences are wall-clock `build_time` metadata (never byte-stable) and
  the path-embedded cache-key directory (handoff §4).
- T0 smoke ON + same-code OFF attribution leg (NEISO 2026–2028 each, ≤5
  solve-years per invocation — plan §2.1b): 2026+ applies
  `HQ_import→North 900→2,100` and `HQ_import_simultaneous 3,850→5,050`;
  measured effect = HQ flows re-route onto the new wires (HQ→Boston mean
  1,612→1,930 MW, HQ→CT 1,118→1,430) while total HQ import stays
  import-tranche-depth-bound (1,987.6 MW mean, both legs) — §6.1 observed
  live; load-weighted prices identical OFF vs ON all years. The smoke's
  `I4 FAIL (2028 coal 54 MW)` + `I12 WARN (2027 RM)` reproduce identically
  on the flag-OFF leg — pre-existing base-path findings, not this channel's
  (handoff §5).

## 8. Maintenance rules

- **Rule 23:** rows change only on *instrument/source* changes (a new board
  approval, a cancellation, a published re-rate, a COD slip in the sponsor's
  filings) — never on a residual. Commit messages cite the instrument.
- Registry admission bar = the closed `status_tier` vocabulary; watchlist
  promotions (ISO-NE LTTP RFP selection ~Sep 2026, CAISO Trout Canyon–Lugo
  sponsor selection ~late 2026) enter as new rows with their instruments.
- Any topology change (WP-A, new links) re-runs curation — unresolvable rows
  hard-fail there by design (the re-mapping tripwire).
- The gate stays default-off until a chartered FF probe (T1-F A/B) grades its
  effect and the owner flips it; this document and the run_config record the
  provenance either way.
