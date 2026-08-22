# ASSESSMENT nyiso-150 — frontier statement after the gradient/winter A/Bs and the queue disposition

Session nyiso-150, 2026-08-22, on the owner's in-session directive (verbatim):
*"Is NYISO at frontier? If not, please continue working thru and finalizing to
reach frontier."* This document supersedes
`ASSESSMENT-nyiso148-frontier-2026-08-21.md` as NYISO's live frontier
statement. Prereg for everything solved here:
`PREREG-nyiso150-gradient-winter-and-reserve-rearm-2026-08-22.md` (committed
and pushed before any arm solved, Amendment 1 included).

---

## 0. THE ANSWER

* **(a) NYISO was NOT at frontier at session start.** The frontier claim was
  cleared by the owner on 2026-08-06 (nyiso-130, recorded in
  `frontend/data/backcast/keepers/NYISO.json::frontier_cleared`); nyiso-148
  re-stated it NOT-YET; and the nyiso-149 promotion note names four open
  objects (the 2025 offer-level remainder, C3c, the zonal gradient, Flynn
  starts) plus the standing queue.
* **(b) This session worked the queue's two live arms and closed four
  standing items** — see §2–§4. The keeper at session start
  (`2026-08-22-nyiso-149-duty-curve`, CALIBRATED, audit 0/0) re-verified
  clean at HEAD before anything ran.
* **(c) The frontier verdict at session end: [FILLED IN §6 AFTER THE GATES].**

## 1. PHASE-0 — the 2025-level and the zonal gradient are ONE object, measured

The owner card `DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md`
(Q1, recommendation A: charter) called the 2025 offer-level object "the last
thing standing between NYISO and a frontier declaration". Phase 0
(`scripts/probes/_nyiso150_gradient_phase0.py`,
`_nyiso150_gradient_phase0.json`) measured, on the keeper's committed
hourlies:

1. **The model carries essentially no zonal gradient** — annual eqh max−min
   **$2.21 / $1.47 / $0.80** (2023/24/25) against actual **$15.73 / $9.17 /
   $14.83** — and every downstate zone under-prices monotonically toward
   Long Island (2025: CH −9.3 %, LH −8.9 %, NYC −13.9 %, LI −17.4 %) while
   Upstate_West over-prices (+23.6 % in 2023). The passing C3a system means
   are cancellation, exactly as nyiso-148 §2.3 warned.
2. **The 2025 downstate miss decomposes ~60–70 % into the winter event
   months** (Jan/Feb/Dec: NYC −44.3/−35.2/−2.7 $/MWh monthly errs, LI
   −40.3/−34.7/−15.2) **and ~30 % into the summer heat-wave months**
   (Jun/Jul: NYC −16.9/−17.9, LI −29.4/−24.9). In the winter event months the
   model is FLAT statewide (spread ≤ $2.6) against actual downstate−upstate
   spreads of $11–44.
3. **The summer half IS the ledgered C3c limitation seen in the monthly
   mean, measured:** the Jun 22–26 2025 heat wave alone carries **$24.0/MWh
   of the June system monthly mean** (event days $180.7 vs $36.5 other
   days); July's excess is likewise event-day-driven (Jul 1/25/28–30 at
   $103–177). The scarcity-formation limitation the owner ledgered under the
   rule-22 C3c STANDING RULE is what the summer monthly errors are made of —
   no second object hides there.
4. **The winter half has a built, measured, never-solve-tested mechanism**
   (`nyiso_iroquois_winter_spread`), and its construction content was
   mis-remembered: evaluating it at both flag settings shows (i) **NYC's
   delivered gas is bit-identical flag-on/off in every month** (the Iroquois
   monthly column is Transco-monthly + the annual spread, so the annual
   offset cancels exactly); (ii) **the flag-off construction gives
   Upstate_West phantom gas at both ends** (Jan-2025 $11.01/MMBtu vs the
   ~$3.5 measured Tenn Z4 world; summer-2025 $0.16–0.64, below any measured
   print) — the additive annual offset drags a Marcellus supply point up
   with the Iroquois winter blowout; (iii) flag-on replaces both with
   measured constructions (UW at its SOM annual on the HH shape; CH/LH/LI
   Algonquin-shaped winter with exact annual conservation). The model's
   statewide winter flatness at ~the upstate-actual level is thereby
   explained: phantom-dear upstate gas manufactures a single state-wide
   price that happens to sit near upstate's actual while suppressing the
   downstate premium.

## 2. THE TWO ARMS — [FILLED AFTER GATES]

### 2.1 ARM C′ — `cc_reserve_duty_split` re-arm (queue item 3, unblocked at nyiso-149)

[OUTCOME]

### 2.2 ARM W — `nyiso_iroquois_winter_spread` (the winter half of queue item 2)

[OUTCOME]

## 3. STANDING ITEMS CLOSED THIS SESSION (no solve needed)

* **The D-4 vintage guard (nyiso-145 queue item 3) — BUILT AND SHIPPED.**
  `ct_only` is a metering-configuration character of a plant, not a year
  property; a preliminary EIA-923 vintage collapses the flag's ratio to
  exactly 1.00 and silently un-flags it — which is what convicted plant 7314
  in 2025 alone. Measured at introduction: **ten NYISO plants lose the flag
  in 2025, zero gain it** (7314 and the ARM C′ cohort's 50744/54592/54593
  included). `scripts/legitimacy_diagnostics.py::ct_only_span_union` now
  unions the flag across the scored span before the per-unit conduct rider
  reads it — protective direction only (it can only ever SKIP a conviction),
  threshold-free, unit-tested
  (`tests/scoring/test_ct_only_bench_flag.py::TestCtOnlySpanUnion`).
  **Verified live on this session's control** (a bit-identical keeper
  replay): the regenerated D-4 fail set is the keeper's committed set MINUS
  exactly the 7314-2025 vintage-artifact row — {2480-2023, 2480-2024,
  54574-2024} vs the committed {…, 7314-2025} — with every other row
  byte-identical and the guard's own note naming the 9 plants extended in
  2025. The keeper's COMMITTED diagnostics carry the pre-guard row until next
  regeneration (the nyiso-148 §1.2 cosmetic class — no gated record moves:
  D-4 rows feed C8 only via the above-cap escalation, and NYISO's C8 is
  under cap in every year).
* **The `nyiso_iroquois_winter_spread` taxonomy hole (card nyiso-143 D1) —
  EXECUTED.** The field now has its own base row in
  `docs/codebase-site/data/mechanism-matrix.js` plus a cell line in every ISO
  shard (NYISO carrying the verdict, `.` elsewhere) — the ercot-177 remedy
  the card requested, so the A/B verdict has a cell to live in.
  `check_mechanism_matrix.py`: integrity OK. D2 (the checker leg that would
  catch the class generically) stays with its governance round, untouched.
* **The Astoria campus benchmark attribution (nyiso-145 queue item 4) —
  ADJUDICATED NON-BLOCKING, chartered as hygiene.** Verified from the
  committed bench parts: plant 55375 (Astoria Energy) carries both campuses'
  CEMS (~8.3/8.4/6.3 TWh, 2.03× its own EIA-923 net) and 57664 (Astoria
  Energy II) has no row — but **both campuses are CC_REGULAR × NYC**, so
  every class×zone benchmark total is invariant to the attribution split and
  no gated criterion (C1/C2/C3a/C3b/C4/C8) can move. The defect is
  plant-grain diagnostic hygiene (per-plant captures, D-row pairing), and the
  convicting direction is safe: the D-4 rider convicts on a measured median
  of ZERO, which an inflated meter cannot produce, and 57664 pairs as
  unmetered (skip). The repair (a facility→plant attribution split of the
  nyiso-141/142 class) keeps its own prereg when a lane takes it; it is not a
  frontier blocker.
* **Flynn's start-count excess — RE-MEASURED on this session's control, and
  the recorded premise no longer reproduces.** On the 149-keeper recipe Flynn
  (56234) UNDER-starts — **3 / 2 / 4 model starts vs 4 / 6 / 8 metered**, in
  months-long runs (median 3,000 / 3,132 / 1,980 h) — the opposite of the
  recorded "over-starting at correct run length (~3×)" (nyiso-146bc §3.2).
  The item stays open but RE-POINTED: a mild under-starting / over-long-run
  conduct residual on one plant, D-4-clean, not the recorded object. Measured
  in the same sweep: **Bethlehem (2539) reads 42 / 14 / 29 starts vs 6–7
  metered on this recipe** — the nyiso-146c start-count closure (recorded
  41/10/15 on its own bundle) has partially drifted under the CHP
  capacity+conduct arms in 2024/2025's merit order; still far from the
  pre-146 262–302, and recorded here so the CC start-count conduct object is
  carried as OPEN at its current, modest magnitude rather than silently
  claimed closed.

## 4. WHAT REMAINS OPEN AFTER THIS SESSION

| # | object | type | state |
|---|---|---|---|
| 1 | Summer downstate scarcity formation (the C3c face, §1.3) | model-class | **LEDGERED** (rule-22 standing rule; accepted by the owner, reported at full magnitude) |
| 2 | [ARM W outcome-dependent: the winter half — closed with keeper, or residual after rejection] | — | [FILL] |
| 3 | Flynn (56234) start-count excess | lane lever, untested | OPEN — its own identification + prereg |
| 4 | Hydro RAMP10 machine-capability seams: `withholding.py::_ramp10_capability` reconciles measured caps only `if frac > 0.0` (hydro's class frac is 0.0) and `scripts/lib/ramp_capability/` has no NYISO module — both re-verified at HEAD this session | lane code seams, untested | OPEN — precise spec stands (nyiso-145 §5) |
| 5 | `online_rho` identification (unblocks the `nyiso_synchronised_reserve` / `nyiso_incity_commitment_obligation` `U` pair; the 1.0 literal fallback governs at HEAD — nyiso-143) | lane identification | OPEN |
| 6 | `RHO_CLIP` band | owner ruling | card delivered (nyiso-145), pending |
| 7 | NYISO hydro 10-min AS certification + hour-by-hour water limit | owner-funded intake | pending |
| 8 | Astoria attribution repair | lane hygiene (non-blocking, §3) | chartered |

## 5. GOVERNANCE

* Holdout freeze ACTIVE and untouched; every year solved, scored or read is
  2023/2024/2025. `complete` marker handling per rule 22 D-5(b) [FILLED at
  promotion if any].
* Rule 15: every completed solve of this session is registered; rule 28(b)
  cells stamped in `docs/codebase-site/data/mechanism-matrix/NYISO.js` in
  this session.
* Rule 21: zero new free parameters introduced anywhere in this session.
* Rule 12: years sequential within each invocation; the two arm invocations
  ran concurrently (cap 2 for the plant-level LP).

## 6. THE FRONTIER VERDICT AT SESSION END

[FILLED AFTER GATES AND REGISTRATION]
