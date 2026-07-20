# CAISO-105 handoff — both re-charters MEASURED to conclusion: belly storage-conduct enumeration CLOSED (price-basis wedge too small, wrong trend), evening+belly Q1 both land on the hub-anchored intertie supply; floor→$0-bid refused on evidence; DAM crosswalk committed; keeper UNCHANGED

**Session 2026-07-20 (CAISO-105) outcome:** (1) **Belly DA/RT price-basis
wedge MEASURED and the family CLOSED** — charge-weighted DA−RT in the belly
is +3.6/+1.1/−0.3 (IFM; RTD and model weights within ±1) against the
+6.0/+6.6/+4.3 residual: wrong magnitude, wrong year-shape (wedge → 0 by
2025, smallest in 2024 where the residual peaks). NO mechanism filed
(derive-first). All three storage-conduct families are now closed
(bid-cost caiso-100/101, allocation caiso-104, price-basis caiso-105).
(2) **Pin-aware Q1 re-decomposition executed with the LP's true bounds**
(floors npz + fleet_only caps): the EVENING Q1 price-setter is the elastic
hub-equalized import rung (CA λ = a WECC node λ in 76/100/97 % of Q1 hours;
thermal marginal MW negligible; battery envelope not binding; λ 10-12 $
below CT entry), and the BELLY over-price Q1 is import-propped (model
imports 3.3-4.2 GW vs measured 0.5-1.8 GW in exactly those hours, import
tranche interior 78-91 %, measured RT < 0 in 22-56 % of them). UNIFIED
DIAGNOSIS: the WECC intertie supply is hub-anchored and too elastic in both
directions. (3) **floor→$0-bid NOT filed** — pinned firm blocks are never
marginal; their negative-λ forced MWh sit behind a bound corridor
(CA-inert) except a small DSW belly slice whose curtailment would worsen
the belly over-price. (4) **DAM-outage crosswalk stage DONE** (139 thermal
resources → 88 plants, 10 EIA-860-verified pins, 6 excludes). Keeper:
`2026-07-19-caiso-102-hourfix` (NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)})
— UNCHANGED. Full record:
`results/calibration/FINDING-caiso105-basis-pin-decomp-2026-07-20.md`;
log: `docs/calibration-log/caiso.md` 2026-07-20 CAISO-105 entry.

## Open lanes for CAISO-106 (priority order)

1. **THE intertie-elasticity ask (both lanes' shared root).** Draft the
   owner ask for a measured, condition-derived intertie depth/direction
   structure: reality's belly conduct is export-leaning/surplus-collapsed
   (measured RT ≤ 0 in up to 56 % of the model's worst over-price hours
   while the model imports 3-4 GW at hub-linked prices), and reality's
   evening RT intertie margin is exhausted/inelastic (RT 8-40 $ ABOVE the
   hubs while the model stays hub-equalized). The WEIM clean-transfer
   tranches already carry condition-scoping (surplus-trigger / overnight /
   daytime-trigger-OFF); the missing piece is the tight-evening and
   deep-surplus-belly states. Rule-1 guardrail: measured WEIM/e-tag depths
   conditioned on an observable state, regenerable forward — NEVER a fitted
   throttle/haircut (import throttling is on the refused list). Derive
   first: measure the state-conditioned depth (and export-side conduct)
   before proposing the LP form.
2. **DAM-outage intake completion** (owner-directed, rule 14): schema-first
   clean_io intake of the per-MRID windows, rule-19 scope (EXCLUDE
   AMBIENT_DUE_TO_TEMP — owned by temp_dependent_derate; keep PLANT_TROUBLE
   / PLANT_MAINTENANCE / etc.), unit-level DAM-before-CAMPD precedence in
   `data.outages` (CAMPD stays fallback), single-delta A/B vs a fresh
   `caiso102_repro_A`. Crosswalk is DONE
   (`data/raw/reference/caiso-dam-resource-crosswalk.csv`).
3. **#2546** ($5 battery_dispatch_adder fallback): delete + re-gate in one
   dedicated session (unchanged recommendation).
4. Housekeeping (other lanes' owners): nyiso-65 / neiso-60
   sidecar-payload parity gaps flagged by `check_registry_payload_parity`.

## Paste-ready next-session prompt

```
<<<CAISO-106 — INTERTIE-ELASTICITY MEASUREMENT + ASK DRAFT>>>
MODEL ASSIGNMENT: Opus or Fable (core-infra scope; CLAUDE.md rule 26).

STATE (2026-07-20, post-CAISO-105): keeper = 2026-07-19-caiso-102-hourfix
(UNCHANGED), NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}; ladder belly
+6.0/+6.6/+4.3, evening -5.8/-4.9/-1.1, overnight +0.8/-0.0/+1.4.
CAISO-105 closed the belly storage-conduct enumeration (price-basis wedge
+3.6/+1.1/-0.3 vs residual — too small, wrong trend; bid-cost and
allocation already refuted) and re-decomposed both windows pin-aware:
EVENING Q1 λ is set by the hub-EQUALIZED import rung (76/100/97 % of
hours); BELLY over-price Q1 is import-propped (model +3.3-4.2 GW vs
measured +0.5-1.8; import tranche interior 78-91 %; measured RT<0 in
22-56 % of those hours). The firm blocks are pinned and never marginal;
floor->$0-bid was refused on evidence. FINDING-caiso105 has the full
record.

DO (priority):
1. INTERTIE ELASTICITY, derive-first: measure the state-conditioned
   intertie conduct — (a) deep-surplus belly: measured corridor
   depth/direction (EIA-930 + WEIM transfer data) conditioned on the
   surplus state the model can observe (net-load / hub-negative /
   trigger), incl. the EXPORT side; (b) tight evening: measured intertie
   depth exhaustion vs the hubs (the 8-40 $ hub separation). NO mechanism
   without an owner ask; the ask must be a measured condition-derived
   depth (rule 1 — import throttling / fitted haircuts are refused).
2. Draft the owner ask with pre-registered gates (both windows, all 3
   years, one bundle) once (1) supports a specific LP form.
3. DAM-outage intake completion per caiso-105 handoff §2 (schema,
   rule-19 ambient exclusion, DAM-before-CAMPD precedence, A/B) — as
   capacity allows; crosswalk is committed.
4. #2546 delete+re-gate remains a dedicated-session item.

GUARDRAILS: all 3 years one bundle (rule 16); NO twin (rule 21);
SEQUENTIAL solves (~8 min/year, 15 GB box); solves IN-SESSION only
(billed CI). Step 0 fresh container: .venv/bin/python
scripts/regenerate_clean.py (~15 min), confirm
data/clean/confirmed-retirements/CAISO/ exists.

DO NOT REDO (caiso-105 + prior): ANY storage-charge conduct mechanism
(all three families closed — bid-cost, allocation, price-basis); the
caiso-105 measurements (wedge, pin-aware decompositions, belly
import-gap); the floor->$0-bid swap (refused — CA-inert/adverse); any
battery bid-cost adder; charge-allocation variants; tightening the
caiso-99 envelope; re-arming caiso_storage_as_reservation; M3/SOC term;
CT_PEAKER floor (caiso-91b); a FITTED import throttle (the intertie work
must be measured+conditioned, rule 1); touching the caiso-73 firm SHAPE
artifact; the frozen caiso-94/96/97/99/101 mechanisms; any year outside
2023-2025 (rule 22 — no CAISO calibration-complete marker).

GIT: main advances fast -> git fetch origin main + rebase BEFORE push
(automation may also advance the session branch itself mid-session —
re-fetch before every push); append docs/calibration-log/caiso.md at
BOTTOM; keeper shards are per-ISO (keepers/CAISO.json + status/CAISO.js)
— only on a swap. Push via the environment's configured push path and
blob-verify >=300-line sources by SHA against the remote (rule 27).
<<<END>>>
```
