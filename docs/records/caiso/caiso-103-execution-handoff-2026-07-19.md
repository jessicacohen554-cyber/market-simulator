# CAISO-103 handoff — allocation stats measured, evening margin decomposed to the firm import blocks, caiso-92 re-derive byte-identical; TWO mechanism asks PENDING

**Session 2026-07-19 (CAISO-103) outcome:** (1) the belly ALLOCATION design
statistics MEASURED (`_caiso103_alloc_stats.py`): the DA-allocation shape is
fleet-size-invariant (r ≥ 0.994 across a 3.5× fleet), the overnight second
cycle and RD book are NOT fleet-scaled — mechanism M1 (DA-allocation-profile
charge schedule, volume-holding by construction) designed and owner-gated,
M3 (SOC term) measured-DEFERRED. (2) The evening Q1 margin DECOMPOSED
(`_caiso103_evening_margin.py` on the digit-for-digit keeper repro): the
FIRM IMPORT BLOCKS (PNW_hydro_base $28 / DSW_solar_PV $48) are price-setting
in 96-100 % of the deepest tight-evening hours with 1.7-2.5 GW withheld,
imports never saturate, Q1 λ stops one rung below CT entry, and reality
prices those hours at/above the measured hubs while the model sits 8-40 $
below — M-EVE-1 (price-taking firm blocks) ask filed. (3) The caiso-92
offer-surface re-derive (issue #2562 item 3) came back BYTE-IDENTICAL on
every consumed value (gates all PASS) — no B-leg, no keeper change, item
closed. NO mechanism was built or solved; keeper stays
`2026-07-19-caiso-102-hourfix` (NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}).
Issue #2546 carried (no ruling).

## Paste-ready next-session prompt

```
<<<CAISO-104 — EXECUTE THE RULED ASKS (belly M1 / evening M-EVE-1)>>>
MODEL ASSIGNMENT: Opus or Fable (core-infra scope; CLAUDE.md rule 26).

STATE (2026-07-19, post-CAISO-103): CAISO keeper = 2026-07-19-caiso-102-hourfix
(unchanged), NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}; ladder belly
+6.0/+6.6/+4.3, evening -5.8/-4.9/-1.1, overnight +0.8/-0.0/+1.4. CAISO-103
measured + designed but did NOT build: BOTH residual lanes are DA-fixed
volumes the LP re-optimizes at the RT margin (FINDING-caiso103). TWO asks
PENDING owner ruling:
  M1 (belly): DA-allocation-profile charge schedule
     (docs/handoffs/caiso-103-belly-allocation-ask-2026-07-19.md)
  M-EVE-1 (evening): price-taking firm import blocks
     (docs/handoffs/caiso-103-evening-firm-import-ask-2026-07-19.md)
caiso-92 re-derive CLOSED byte-identical (issue #2562 item 3). #2546 OPEN.

DO (priority):
1. Obtain owner rulings on M1 and M-EVE-1 (session question gate). For each
   GRANTED mechanism, execute per its ask doc: implement (derive script +
   ScenarioConfig gate + dispatch.py rows for M1; the -eps/$0 firm-block bid
   under a new gate for M-EVE-1 after the negative-hub-hours conduct
   measurement), pre-register gates in the FINDING BEFORE the solve, ONE
   single-delta B-leg each vs a fresh same-machine caiso102_repro_A
   (2023-2025 one bundle, sequential), score _caiso92_report + the caiso-103
   probes, register whatever results (rule 15), promotion on
   no-status-regression (owner call). If BOTH granted: solve SEPARATE
   single-delta legs first (attribution), composition leg only on owner ask.
2. M-EVE-1 pre-measurement (before its B-leg): the firm-flow conduct in
   negative-hub hours (fixes the bid constant -eps vs $0 a priori, no sweep).
3. DAM OUTAGE DATA (owner-directed 2026-07-19): use CAISO DAM-published
   outage/derate data as the backcast outage source WHERE AVAILABLE, with
   the existing CAMPD-inferred windows as the fallback for units/periods
   the DAM reports don't cover (rule 14: prefer measured over inferred —
   published outage schedules are the measured instrument, CAMPD windows
   are inference from emissions gaps; rule 13-admissible: physical
   availability events with a forward analogue, exactly like the existing
   CAMPD overlay). Path: data-intake protocol (schema-first, clean_io seam,
   per-ISO registry) -> extend the outage loader with the
   DAM-before-CAMPD precedence -> single-delta A/B on the keeper recipe vs
   caiso102_repro_A (2023-2025 one bundle), register whatever results
   (rule 15). Keep the precedence unit-level and documented; do NOT drop
   the CAMPD fallback (coverage gaps are real).
4. Issue #2546 ruling if carried.

GUARDRAILS: all 3 years one bundle (rule 16); NO twin (rule 21); SEQUENTIAL
solves (~8 min/year, 15 GB box OOMs on 2 concurrent); solves IN-SESSION only
(billed CI). Step 0 fresh container: .venv/bin/python scripts/regenerate_clean.py
(~15 min), confirm data/clean/confirmed-retirements/CAISO/ exists. The
caiso-92 corpus (data/raw/caiso-public-bids/zips) is gitignored — NOT needed
unless re-deriving the offer surface again.

DO NOT REDO (caiso-103 + prior): the caiso-103 measurements (alloc stats,
Q1 decomposition, hub separation — all in FINDING-caiso103); the caiso-92
re-derive (byte-identical, closed); any battery marginal bid adder
(volume-refuted family); tightening the caiso-99 envelope; re-arming
caiso_storage_as_reservation; M3/SOC term (measured-DEFERRED — the second
cycle does not fleet-scale); CT_PEAKER floor (caiso-91b); import throttling;
touching the caiso-73 firm shape artifact (M-EVE-1 changes only the BID);
the +1h frame fix or its gates (frozen); the caiso-94/96/97/99/101
mechanisms (frozen); any year outside 2023-2025 (rule 22 — no CAISO
calibration-complete marker).

GIT: main advances fast -> git fetch origin main + rebase BEFORE push; the
calibration log is now the per-ISO continuation docs/calibration-log/caiso.md
(append at BOTTOM, never the frozen archive); keepers.json has BOTH a
top-level ISO field AND a "keepers" array — update BOTH on any swap. Push
via mcp__github__push_files (API-only); blob-verify pushed sources >=300
lines by SHA (rule 27).
<<<END>>>
```
