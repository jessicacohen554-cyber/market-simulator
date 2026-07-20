# CAISO-104 handoff — M1 built and REFUTED (allocation family closed), M-EVE-1 adjudicated INERT (evening lane re-chartered), DAM-outage corpus intaken; keeper UNCHANGED

**Session 2026-07-20 (CAISO-104) outcome:** (1) **M1 executed and REFUTED** —
the owner-granted DA charge-allocation schedule was fully built
(`caiso_charge_allocation_schedule` + rule-23 derive + per-day LP rows via
exact S[d] elimination) and solved twice: v1 collapsed to zero charge on a
composition defect (trace shares in caiso-99-envelope-zero hods; support
rule ≥0.5 % fixed a priori), v2 was conduct-faithful (floors bind 50-65 %,
volume holds within 3.5-6.1 %) yet **belly λ inert** (+6.0→+5.9 / +6.6→+6.6
/ +4.3→+4.1) — REJECTED on pre-registered gates 1+3. The measured DA bundle
is ~72 % belly, so allocation cannot decouple the belly price from the
charge volume's margin. Both legs registered
(`2026-07-20-caiso-104-m1-v1/-v2`, PROBE). (2) **M-EVE-1 adjudicated INERT
with no solve**: the caiso-77 must-flow floor is LIVE in the keeper
(`caiso_firm_import_selfschedule=True`; pin-check 1.0000 all years), the
granted bid swap is provably byte-inert, and the caiso-103 "withheld GW"
attribution was a p99-proxy artifact. Owner ruling: re-charter the evening
lane. The pre-measurement stands: firm conduct CURTAILS in negative-hub
hours (5/6 corridor-years) → any successor bid constant is $0. (3)
**DAM-outage intake opened** (owner-directed): 1,094/1,096 daily reports
committed + per-MRID windows parquet; crosswalk/loader stages remain. (4)
**#2546**: recommendation recorded (defer as-is; delete + re-gate follow-up).
Keeper: `2026-07-19-caiso-102-hourfix` (NOT-YET, fail {C3c, C4, C5a(2024
CAVEAT)}) — UNCHANGED. Full record:
`results/calibration/FINDING-caiso104-m1-meve1-execution-2026-07-20.md`;
log: `docs/calibration-log/caiso.md` 2026-07-20 entry.

## Open lanes for CAISO-105 (priority order)

1. **Belly re-charter — measure the DA-vs-RT price basis** (FINDING §3b):
   both conduct families are now refuted (bid-cost caiso-100/101;
   allocation caiso-104). The remaining hypothesis is the PRICE BASIS: the
   real fleet's charge clears at DA prices while the backcast scores RT λ.
   Measure the charge-weighted DA−RT belly wedge (actuals: `actual_lmp`
   da/rt columns; model-charge hours vs measured-charge hours) BEFORE any
   mechanism design; any mechanism goes to an owner ask.
2. **Evening re-charter — pin-aware Q1 decomposition**: redo the caiso-103
   §3 margin attribution with bounds from the bundle's own `floors/*.npz` +
   `run_year(fleet_only=True)` caps (never the unit-year p99 proxy). Who
   sets Q1 λ one rung below CT entry with the firm blocks pinned? The
   floor→$0-bid replacement (measured conduct: curtail below $0;
   `_caiso104_firm_negative_hub.py`) is a candidate mechanism — it
   un-promotes part of caiso-77, so it needs its own ask + gates.
3. **DAM-outage intake completion** (owner-directed, rule 14): RESOURCE ID →
   ORIS crosswalk (name-match + hand-verify the thermal fleet; the top
   non-ambient resources are recognizable — Ormond Beach, Alamitos, Los
   Medanos, Pastoria), rule-19 scope decision (EXCLUDE `AMBIENT_DUE_TO_TEMP`
   — owned by `temp_dependent_derate`; keep PLANT_TROUBLE / PLANT_MAINTENANCE
   / etc.), schema-first clean_io intake, unit-level DAM-before-CAMPD
   precedence in the outage loader (CAMPD fallback stays), single-delta A/B
   vs a fresh `caiso102_repro_A`. Corpus + consolidation are DONE
   (`data/raw/caiso-dam-outages/`).
4. **#2546 follow-up**: delete the $5 fallback literal + re-gate the CAISO
   baseline in one dedicated session.
5. Housekeeping (any lane): `check_registry_payload_parity.py` flags
   pre-existing sidecar/payload gaps in NYISO/NEISO lanes (nyiso-65,
   neiso-60 keeper) — repair belongs to those lanes.

## Paste-ready next-session prompt

```
<<<CAISO-105 — BELLY DA/RT BASIS MEASUREMENT + EVENING PIN-AWARE RE-DECOMPOSITION>>>
MODEL ASSIGNMENT: Opus or Fable (core-infra scope; CLAUDE.md rule 26).

STATE (2026-07-20, post-CAISO-104): keeper = 2026-07-19-caiso-102-hourfix
(UNCHANGED), NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}; ladder belly
+6.0/+6.6/+4.3, evening -5.8/-4.9/-1.1, overnight +0.8/-0.0/+1.4. CAISO-104
REFUTED the belly ALLOCATION family (M1 v2: conduct-faithful, lambda-inert
— the DA bundle is ~72% belly) after caiso-100/101 refuted the bid-cost
family; M-EVE-1 was adjudicated INERT (the caiso-77 must-flow floor is LIVE
— pin-check 1.0000; the caiso-103 withheld-GW attribution was a p99-proxy
artifact); the DAM-outage corpus is committed (crosswalk/loader pending).
FINDING-caiso104 has the full record + re-charter pointers.

DO (priority):
1. BELLY: measure the DA-vs-RT price-basis wedge (FINDING-caiso104 §3b) —
   charge-weighted DA lambda vs RT lambda in measured-charge and
   model-charge hours, per window per year (actual_lmp da/rt; the storage
   report IFM layer for measured charge). Derive-first: NO mechanism
   without an owner ask.
2. EVENING: pin-aware Q1 re-decomposition on a fresh caiso102_repro_A
   (bounds from floors/*.npz + run_year(fleet_only=True) caps — NEVER the
   unit-year p99 interior proxy). Identify the actual Q1 price-setter; if
   the evidence supports the floor->$0-bid replacement of the caiso-77
   firm floor (measured conduct: curtailment in negative-hub hours,
   _caiso104_firm_negative_hub.py — bid constant $0 is already fixed),
   file it as a NEW ask with gates; it un-promotes part of caiso-77.
3. DAM-outage intake completion per the caiso-104 handoff §3 (crosswalk,
   rule-19 ambient exclusion, clean_io schema, DAM-before-CAMPD precedence,
   single-delta A/B) — as capacity allows.
4. #2546 delete+re-gate remains a dedicated-session item; do NOT fold it
   into an A/B session.

GUARDRAILS: all 3 years one bundle (rule 16); NO twin (rule 21); SEQUENTIAL
solves (~8 min/year, 15 GB box); solves IN-SESSION only (billed CI). Step 0
fresh container: .venv/bin/python scripts/regenerate_clean.py (~15 min),
confirm data/clean/confirmed-retirements/CAISO/ exists.

DO NOT REDO (caiso-104 + prior): any battery bid-cost adder (refuted
family); any charge-allocation schedule variant (refuted family — M2
window-bands included, same ~72%-belly bundle objection); the caiso-104
measurements (negative-hub conduct, pin-check); tightening the caiso-99
envelope; re-arming caiso_storage_as_reservation; M3/SOC term (deferred);
CT_PEAKER floor (caiso-91b); import throttling; touching the caiso-73 firm
SHAPE artifact; the frozen caiso-94/96/97/99/101 mechanisms; any year
outside 2023-2025 (rule 22 — no CAISO calibration-complete marker).

GIT: main advances fast -> git fetch origin main + rebase BEFORE push (this
session's branch was merged mid-session — restart from latest main); append
docs/calibration-log/caiso.md at BOTTOM; keeper shards are per-ISO
(keepers/CAISO.json + status/CAISO.js) — only on a swap. Push via the
environment's configured push path and blob-verify >=300-line sources by
SHA against the remote (rule 27).
<<<END>>>
```
