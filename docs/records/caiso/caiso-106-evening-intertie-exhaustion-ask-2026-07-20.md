# CAISO-106 owner ask — the measured EVENING intertie-exhaustion ceiling (the evening under-price fix)

**Status: WITHDRAWN by the pre-registered binding check (same session,
2026-07-20) — the ceiling is inert for the evening.** The single-year 2024
binding check (FINDING §5, `_caiso106_binding_analysis.py`) fired this ask's
own KILL condition #1 (§4): the model imports +4165 MW mean in the evening
(p95 +5745) — LESS than measured (+4557) and far below the measured p95
exhaustion depth (~7-7.6 GW) — so a volume ceiling never binds. The evening
under-price is a PRICE / merit-order defect (the marginal import prices at the
hub-equalized level, 10-12 $ below reality's marginal supply), not an
import-volume-exhaustion defect; the correct lever is an inelastic exhaustion
PREMIUM, not a quantity cap. The volume ceiling DOES bind in the BELLY (model
over-imports +2.6 GW), but that arm's depth is not year-stable (FINDING §3).
No mechanism filed. Re-charter in §7 below. Original ask text preserved
unchanged for the record.

---

**Status: PENDING owner ruling.** No mechanism built or solved; measured
derivation in `results/calibration/FINDING-caiso106-intertie-elasticity-2026-07-20.md`
§2 (`scripts/probes/_caiso106_intertie_elasticity.py`, pure raw-data, gated).
The BELLY arm of the caiso-105 intertie diagnosis is explicitly NOT in this
ask — its measured conduct is not year-stable on any CAISO-observable state
(FINDING §3); it needs a west-wide observable and is held as a follow-on
measurement lane.

## 1. The measured defect (one paragraph)

The model's WECC intertie supply is priced as a flat, hub-linked, ELASTIC
supply curve (the `IMPORT_TRANCHES` rungs at hub LMP × basis, up to the
~15.4 GW corridor TTC). In the evening (hod 17-21) CA λ is hub-EQUALIZED to a
WECC node in 76/100/97 % of the deepest under-price quartile and sits 10-12 $
BELOW the model's own CT entry (FINDING-caiso105 §2): the model fills the
evening margin with elastic hub-priced import instead of climbing to the
domestic rung, and prices the evening −5.8/−4.9/−1.1 $/MWh too cheap. The
measured reality is the opposite of elastic: the corridor net import
**exhausts**. Measured TOTAL net import (EIA-930 CISO interchange) climbs to a
plateau of ~5.1-5.4 GW (p50) / ~7.6-8.6 GW (p95) around net-load 20-30 GW and
then **declines** to ~4.5 GW (p50) / ~6.6-7.0 GW (p95) in the tightest band
[30,45) GW — the West is ramping/tight at CAISO's own sunset peak, so the
import margin is spent, not available. That is the rung behind
FINDING-caiso103 §1 (actual RT clears at/above the measured hubs while model λ
sits 8-40 $ below them): the import cannot grow to serve the margin, so
reality's price climbs and the model's does not.

Measured evening exhaustion envelope (FINDING §2 table), year-stable, gated:

| net-load band (GW) | p50 net import (MW) 23/24/25 | CV | p95 (MW) 23/24/25 | CV |
|---|---|---|---|---|
| [15,20) | 3244/4309/4510 | 0.14 | 6229/7008/6644 | 0.05 |
| [20,25) | 5124/5084/5437 | 0.03 | 7752/7580/8584 | 0.06 |
| [25,30) | 5130/5169/5338 | 0.02 | 7169/7586/8573 | 0.08 |
| [30,45) | 4199/4558/4502 | 0.04 | 6883/6973/6644 | 0.02 |

## 2. Proposed mechanism (M-EVE-EXH-1): measured evening net-import exhaustion ceiling

Gate `ScenarioConfig.caiso_evening_import_exhaustion` (default off; the CAISO
backcast recipe arms it on approval). Add ONE aggregate deliverability
constraint on the CAISO import node, active only in the evening window, capping
NET import at the measured net-load-conditioned exhaustion depth:

    Σ_corridors ( import_flow[t] − export_flow[t] )  ≤  D_eve( ñ[t] )     ∀ t ∈ evening

where
* `ñ[t]` = the **build-time** POTENTIAL net-load = demand[t] − available wind
  (cf×cap) − available solar (cf×cap). A fixed per-hour input constant, NOT the
  endogenous dispatched net-load — so `D_eve(ñ[t])` is a precomputed per-hour
  RHS vector (vectorized, no hour loop — rule 2), the same class as the MISO
  (month×hod) measured seam envelope.
* `D_eve(·)` = the measured pXX TOTAL net import by net-load band (§1 table),
  interpolated across bands. **Candidate percentile p95** (the exhaustion
  ceiling — the max the corridor typically delivers in that state); the
  binding check (§5) informs whether p95 binds or a lower percentile is needed.
* The cap is on NET import above the existing firm/clean floors — it NEVER
  forces the firm blocks (`CAISO_FIRM_IMPORT_TRANCHES`, caiso-73 shape) or the
  WEIM clean tranches below their availability: where a band's measured depth
  is below the firm+clean floor the constraint is simply slack, not a forced
  curtailment (a CEILING forces nothing — rule 8 / C8 is trivially clean).

**Effect direction (toward measured):** in evening hours where the model would
elastically import past the measured exhaustion depth, the ceiling trims the
excess hub-priced import; the marginal rung shifts from the hub-equalized
import to the domestic CC/CT rung 10-12 $ above (FINDING-caiso105 §2), raising
λ toward the measured level and closing the −5.8/−4.9/−1.1 under-price. Belly
and overnight are untouched (evening-scoped window).

## 3. Why this is rule-1 admissible (a measured envelope, NOT a throttle)

* **Measured**, not fitted: `D_eve` is the measured EIA-930 net-transfer depth
  by net-load band — never tuned to the price residual (its value is set by the
  flow record, not by where λ needs to land).
* **Observable, forward-reproducible state**: potential net-load regenerates
  from forward demand / wind-CF / solar-CF in a forecast year and responds to
  changed conditions (different net-load → different cap), so the dispatch
  validated in backcast is the dispatch forecast (rule 13).
* **Year-stable** (the estimation gates below already PASS): a revealed
  deliverability envelope, not a per-year fit.
* It is the **deliverability-envelope class** the model already uses on the
  MISO/PJM/NEISO seams (measured (month×hod) envelopes) and the rule-14
  "measured data over a crude representation" principle: the flat hub-priced
  elastic supply overstates the available net transfer that the measured record
  shows exhausts. This is NOT import throttling (a residual-tuned haircut, the
  refused class) — it is the measured available transfer.

## 4. Pre-registered gates (both windows, all 3 years, one bundle; NO twin — rule 21)

**Estimation (ALREADY PASS, FINDING §2):** per-band CV ≤ 0.20 and LOYO
mean-of-others ≤ 25 % on `D_eve` across 2023-2025. If the owner selects a
percentile the derive re-prints its gates for that percentile before any solve.

**Solve A/B** — single delta (`caiso_evening_import_exhaustion=True`) vs a
fresh same-machine `caiso102_repro_A`, all three years in one bundle
(rule 16), sequential (rule 12):
* **PRIMARY (pass):** evening demand-weighted resid −5.8/−4.9/−1.1 moves toward
  0 in all three years, and does NOT overshoot past +2.0 $/MWh (over-correction
  = the ceiling too tight → fail).
* **GUARD — belly:** belly over-price +6.0/+6.6/+4.3 must not worsen by > +0.5
  $/MWh (evening-scoped; a belly regression signals cross-window leakage — fail).
* **GUARD — overnight:** +0.8/−0.0/+1.4 unchanged (±0.5).
* **C-gates:** C3c / C4 / C5a(2024) not regressed; forced-energy C8 trivially
  clean (a ceiling forces nothing).
* **Rule 22:** leave-one-year-out structural scoring within 2023-2025 before
  any promotion (in-sample gain with held-out degradation = overfit, refuse).

**Pre-registered KILL conditions (refuse + file, no re-sweep):**
1. the ceiling does not bind (model evening import < `D_eve` — §5 binding check
   returns NO) → the evening defect is not over-import; refuse and re-charter;
2. evening resid does not move toward 0, OR overshoots past +2.0;
3. any belly/overnight guard or C-gate regresses.

## 5. Binding check (does the ceiling bind?) — the go/no-go for this ask

The load-bearing precondition: the model's evening TOTAL net import must exceed
`D_eve` for the ceiling to raise λ. Measured in a single-year (2024) diagnostic
keeper repro (`scripts/probes/_caiso106_binding_2024.py`, un-registered):

<!-- FILLED AFTER THE 2024 SOLVE: model evening TOTAL net import (GW) vs the
measured p50 ~5.0 / p95 ~7.6 GW @ net-load [20,25); BINDS at pXX = ... -->

## 6. Scope notes

* The BELLY intertie over-elasticity (model imports +3-4 GW at hub prices while
  reality reverses to export in deep surplus) is REAL but its measured depth is
  not year-stable on CAISO net-load (west-wide state dependence, FINDING §3) —
  held as a follow-on measurement lane (candidate observable: the Palo Verde /
  Malin hub LEVEL, which prices the neighbor surplus). NOT in this ask.
* This mechanism composes with, and does not touch, the frozen caiso-73 firm
  shape, the caiso-87/93/94 clean-depth tranches, or the caiso-77 must-flow
  floor — it is an upper bound on net import, orthogonal to the priced supply
  rungs below it.

## 7. Re-charter (post-binding-check, 2026-07-20) — two separate lanes, neither ready to file

The binding check (§5 of the FINDING) split the caiso-105 unified
"too-elastic-both-directions" diagnosis into two mechanistically DISTINCT
defects that the drafted single volume ceiling cannot both serve:

1. **EVENING = a PRICE defect (measured exhaustion PREMIUM lane).** The model's
   evening import VOLUME is fine (≈ measured); it prices the marginal MW at the
   hub-equalized level, 10-12 $ below reality's marginal supply. Candidate LP
   form: an inelastic exhaustion premium that lifts the marginal tight-hour
   import offer above the hub by the MEASURED RT-over-hub separation in the
   tight state — a measured re-pricing (the MISO/NEISO Q-Q measured-ladder
   class), NOT a quantity cap and NOT a residual-tuned adder. NEXT STEP: measure
   the tight-evening RT-over-hub premium and run its CV/LOYO gates before any
   ask (derive-first — do not reuse this withdrawn ask's gates for a different
   mechanism).

2. **BELLY = a VOLUME defect (the volume ceiling is correct, the depth is not).**
   The model over-imports +2.6 GW in deep surplus; a net-import ceiling is the
   right mechanism and it BINDS. The blocker is identification: the depth is not
   year-stable on any CAISO-observable state (FINDING §3, west-wide dependence).
   NEXT STEP: measure the belly net-transfer conduct conditioned on the Palo
   Verde / Malin hub LEVEL (the observable that prices the neighbor surplus) and
   test whether that state stabilizes the depth; only then draft the ceiling ask.

Neither lane is filed this session — both need a fresh measurement first
(derive-first). The withdrawn §2 volume-ceiling form stays on record as the
tested-and-refuted evening candidate.
