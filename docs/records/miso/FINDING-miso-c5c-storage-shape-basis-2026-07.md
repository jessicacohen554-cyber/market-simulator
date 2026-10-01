# FINDING — MISO C5c storage dispatch shape (2025 r=0.469 FAIL): the "shape" being scored is the battery fleet's COD ramp on a basis the model doesn't share — ledgered exception, no mechanism

**Date:** 2026-07-12. **Lane:** miso-60 handoff item 5 (2025 price side, storage-shape leg).
**Question (handoff):** C5c-2025 FAILs at r=0.469 (floor 0.50). "FIRST adjudicate the basis
(battery-only EIA-930 series vs the model's PS-dominated fleet; same family as the ledgered
C5b exception — MISO publishes no PS series). Basis-broken → ledgered exception with its own
FINDING, not a mechanism; real → rides the repaired LMP body."

**Verdict: basis-broken, same family as C5b and one confound worse — ledgered exception for
(storage_shape, 2025); no mechanism, no scorer change this session.** No solve was run for
this adjudication (measured data only).

## 1. What C5c-2025 actually compares

- **Model side** (`monthly_net_gwh`, miso-60 payload): BAT + pumped-storage discharge pooled —
  and the fleet is ~93% PS by throughput (C5b FINDING §1: 2,417 MW Ludington/Taum Sauk vs
  802 MW batteries). Shape: summer-peaked arbitrage (Jul max, 512 GWh; winter ~150-200).
- **Actual side** (bench `storage.monthly_net_gwh`, from EIA-930 `NG: BAT`): battery-ONLY
  (MISO reports no PS series — all-null in every scored year, C5b FINDING §1), and the series
  begins Feb-2025. Vector: [7.2, 11.3, 10.9, 11.2, 13.6, 21.4, 22.5, 26.2, 30.7, 28.4, 31.1,
  30.3] GWh — near-monotone RISING through the year.

## 2. The actual's "seasonal shape" is the fleet-growth ramp, not dispatch

The 2025 MISO battery fleet quadrupled IN-YEAR: EIA-860 operable (Balancing Authority Code =
MISO, 36 units, 803.9 MW total — matching the C5b finding's 801.9) has month-end cumulative
nameplate of 198 MW (Jan) → 412 (Mar) → 627 (Jun) → 804 MW (Dec); 660 MW carry 2025
Operating Months.

| comparison (2025, monthly) | pearson r |
|---|---|
| actual GWh vs cumulative in-service battery MW (the COD ramp) | **0.934** |
| actual GWh vs model BAT+PS GWh (= the scored C5c) | 0.469 |
| actual GWh **per average in-service MW** vs model | **0.02** |

Normalizing the actual by in-service MW removes essentially all of its variance: the per-MW
utilization shape has **CV = 0.175** (per-MW-per-day 0.201) — BELOW the scorer's own C5c
degeneracy floor (`STORAGE_SHAPE_MIN_CV = 0.25`), i.e. by the rubric's own standard there is
**no seasonal dispatch shape in the 2025 actual to correlate against** once the ramp is
removed. The raw vector passes the degeneracy guard only because the COD ramp itself
manufactures CV (0.424). So the scored r=0.469 measures "does PS summer arbitrage look like
a battery build-out schedule" — it cannot measure dispatch-shape skill in either direction.

## 3. Why this is not repairable by a mechanism this session

- The composition half is C5b's documented basis break (model BAT+PS vs actual BAT-only;
  MISO publishes no PS series) — already a ledgered exception carried since miso-48.
- The ramp half has a real, admissible model-side lever — `storage_vintage_ramp` (measured
  EIA-860 Operating Month availability, the CAISO COD-ramp analogue; C5b FINDING §3 already
  names it) — but with the keeper's storage payload pooled BAT+PS, enabling it cannot make
  C5c meaningful: the model vector would still be ~93% PS arbitrage vs a battery-only
  actual. The honest fix is the C5b FINDING §4 scorer-infrastructure split (score model
  battery-only vs `NG: BAT`, PS separately vs the eGRID net-energy band), which is owned by
  the rubric lane and needs owner sign-off — not a calibration mechanism (and per rule 1,
  no mechanism may be added just to move a scored residual).

## 4. Disposition

- **(storage_shape, 2025) enters the exceptions ledger** as an ACCEPTED MEASURED-INPUT
  LIMITATION (benchmark basis mismatch), citing this FINDING — implemented in the miso-61
  attestation alongside the carried C5b entry. Ledgered caveats then total 2 of the
  budgeted 3 (`MAX_LEDGERED_CAVEATS`).
- **Flagged to the rubric-infrastructure lane** (same flag as C5b FINDING §4): when the
  BAT-vs-BAT split lands, C5c should ALSO normalize by in-service MW per month (or gate on
  the per-MW CV) so a build-out year cannot manufacture a scoreable "shape"; and
  `storage_vintage_ramp` + `battery_dispatch_adder` become scoreable on the aligned basis.
- 2023/2024 need no entry: EIA-930 has no BAT series before Feb-2025, so C5c SKIPs those
  years on its own.

## 5. Rule-13 admissibility note

EIA-860 Operating Months and the EIA-930 BAT series are used here only to adjudicate the
benchmark (is there a real shape miss? unmeasurable on this basis) — no model input, bound,
or adder is set from them. The per-MW normalization would regenerate for a forward year from
forward drivers (fleet COD schedule × dispatch), and is cited for diagnosis only.
