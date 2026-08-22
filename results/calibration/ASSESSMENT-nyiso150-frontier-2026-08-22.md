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
* **(c) The frontier verdict at session end: STILL NOT-YET — but the queue is
  materially shorter and sharper (§6).** Both live arms were tested and
  rejected on their own pre-registered gates, and each rejection is a
  measurement: the 2025-level/gradient object is now PROVEN LOCATIONAL by
  solve and typed blocked-on-identification (owner court), and the
  merit-order-inversion repair is down to ONE plant's duty story with a named
  successor. What keeps frontier NOT-YET is three testable lane items
  (the reserve-cohort graded duty, the hydro RAMP10 seams, the `online_rho`
  identification) plus the re-pointed Flynn residual.

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

## 2. THE TWO ARMS — both REJECTED-AS-ARMED on their own pre-registered gates, and both rejections are measurements

Control: the keeper recipe replayed at HEAD, **IDENT PASS — max |Δprice| = 0.0
over every zone-hour of all three years** (HEAD drift absent; each arm's delta
is its mechanism). Both arms registered per rule 15:
`2026-08-22-nyiso-150-reserve-rearm` and `2026-08-22-nyiso-150-winter-spread`
(gates record `_nyiso150_ab_gates.json`).

### 2.1 ARM C′ — `cc_reserve_duty_split` re-arm: REJECTED on Allegany ALONE; the nyiso-146b leg (b) is RESOLVED

* **C-K2 liveness FAILS on one plant.** Sterling (54592), Batavia (54593) and
  50744 collapse **93–98 %** of their phantom energy in the gated years;
  **Allegany 7784 falls only 70 % / 60 %** against the ≥80 % bar (was
  −64/−50 % at nyiso-146b — better on the new merit order, still short). The
  cohort's most efficient member (hr 7.5) needs a duty story stronger than
  the class peak band, exactly as the 146b record said.
* **Every other gate passes**: C-K1 exact single delta; C-K3 no-degrade
  (starts) PASS; C-K4 zero new D-4, escalation clears; **C-K5 —
  C1/C2/C3a/C3b/C4/C8 ALL PASS on the arm, C3a-2023 +5.2 % IN BAND**. The
  nyiso-146b rejection leg (b) — "+9.0 % → +11.3 %, blocked by a price level
  it could not explain" — is therefore **RESOLVED by the CHP
  capacity+conduct repair**, precisely as the queue conditioned it.
* 2025 (reported, preliminary vintage): the cohort floats 295–495 GWh even at
  the peak band in the dear-gas year.
* **Named successor**: the nyiso-149 graded-duty pattern applied to the
  reserve cohort — a measured per-plant price-conditional duty (its own
  prereg and artifact), not the class band. Cell record updated on
  `offer_curve_by_group` (matrix shard, this session).

### 2.2 ARM W — `nyiso_iroquois_winter_spread`: REJECTED, and the rejection PROVES the gradient object LOCATIONAL

The first solve test of the flag as a keeper arm (nyiso-82 tested it on the
pre-CHP keeper; nyiso-122 refused it ex ante as a C3a lever; the standalone
rule-14 case was the owner question this session's directive reached).

* **The level moves; the spread does not.** In every winter event month the
  whole state rises together: Dec-24 **47.8 → 61.9 statewide** with
  Upstate_West landing ~exact on its own actual (60.9); Feb-25 **UW exact
  (87.4 vs 87.1)** — while the downstate−upstate spread stays **≤ $1.1**
  against $11–27 actual. An **$8–13/MMBtu measured zonal gas spread produces
  < $1 of zonal price spread**: the LP prices the four mainland zones as ONE
  COUPLED BLOCK — the internal west→east cutset never binds — so no
  fuel-side mechanism can create the winter downstate premium. **The
  gradient object is LOCATIONAL, now proven at the LP** (nyiso-122's static
  read and nyiso-124's flow-side measurement, confirmed from the price side).
* Gate record: W-K3a recovery 0–4 % vs ≥30 %; W-K3b the annual gradient
  FALLS (1.47→1.27, 0.80→0.69); W-K3c UW-2023 WORSENS (+23.6→+23.8 % — the
  eastern winter premium leaks upstate through the coupling); W-K3d
  anti-relocation fires (2023, 2025); W-K4 two NEW D-4 conduct rows
  (54574-2023, 2500-2025); W-K5 **C1-2024 CC_REGULAR +3.63 TWh PASS→FAIL**.
* **Rule-14 disposition.** The flag-off construction's phantom UW gas (§1.4)
  is real and mis-measured — but the accurate monthly input is **MISALIGNED
  to the coupled-block representation** (rule 14's misalignment clause):
  armed alone it relocates error (statewide level up, gradient unchanged,
  UW-2023/Dec-25 over-priced, conduct rows added) instead of removing it.
  Cell `O → R` with re-open condition: **re-test as the companion of a
  locational mechanism that lets the west→east cutset bind — never alone.**

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
| 2 | **The winter downstate premium / zonal gradient — PROVEN LOCATIONAL (§2.2)**, and its lane routes are now all adjudicated: the fuel half REFUTED BY SOLVE (this session); the seam half UNIDENTIFIABLE from public data (the `SCH - PJ - NY` leg spans the cutset and neither P-32 nor PJM's tie file splits it — nyiso-125's rule-20 refusal, standing); the as-enforced interface limits REFUTE tightening (nyiso-122 BLOCKER-C); the model's own CE TTC matches the posted limit (accurate input, kept) | locational; **blocked on identification** | OPEN in owner court: unblocks on an authorized intake that splits the Capital_Hudson seam leg or resolves sub-zonal in-city formation (nyiso-122 BLOCKER-B class) — not on any lane lever now known |
| 3 | The ARM C′ successor, **re-specified in-session** (`FINDING-nyiso150-allegany-hr-identity-2026-08-22.md`): Allegany's hr 7.5 is the gas_cc "older" CLASS DEFAULT reached through an ORISPL registry split — eGRID carries the plant as 10619 with a stable measured 7.99–8.68 across seven vintages (pooled 8.42; identity proven by exact netgen equality all seven years). Successor = (1) the identity heat-rate repair (measured artifact at the existing `heat_rate` seam, default-off, NYISO-scoped) then (2) re-gate `cc_reserve_duty_split` on the repaired control; the graded-duty build returns only if the bar is still missed. The general CAMPD-less eGRID-HR channel was sized and REFUTED on its own population | lane lever, fully identified | OPEN — construction specified, own prereg |
| 4 | Flynn (56234) — RE-POINTED (§3): mild UNDER-starting in over-long runs, the recorded over-starting premise no longer reproduces; plus the Bethlehem start-count drift (42/14/29 vs 6–7) | lane lever, re-pointed | OPEN — small; own identification |
| 5 | Hydro RAMP10 machine-capability seams: `withholding.py::_ramp10_capability` reconciles measured caps only `if frac > 0.0` (hydro's class frac is 0.0) and `scripts/lib/ramp_capability/` has no NYISO module — both re-verified at HEAD this session | lane code seams, untested | OPEN — precise spec stands (nyiso-145 §5) |
| 6 | `online_rho` identification (unblocks the `nyiso_synchronised_reserve` / `nyiso_incity_commitment_obligation` `U` pair; the 1.0 literal fallback governs at HEAD — nyiso-143) | lane identification | OPEN |
| 7 | `RHO_CLIP` band | owner ruling | card delivered (nyiso-145), pending |
| 8 | NYISO hydro 10-min AS certification + hour-by-hour water limit | owner-funded intake | pending |
| 9 | Astoria attribution repair | lane hygiene (non-blocking, §3) | chartered |
| 10 | Q2 of the 2025-level card (annotate the keeper's C3a-2025 margin) | owner ruling | pending — note the annotation's subject improved: the −8.8 % is now an honest miss, not a cancellation |

## 5. GOVERNANCE

* Holdout freeze ACTIVE and untouched; every year solved, scored or read is
  2023/2024/2025. **No promotion occurred** (both arms rejected on their own
  gates), so no rule-22 D-5(b) re-key is owed: the keeper, the keeper shard,
  `calibration-complete.json` and `status/NYISO.js` are unchanged, and the
  keeper's determination was re-verified CALIBRATED at HEAD before anything
  ran (§0.b).
* Rule 15: every completed solve of this session is registered; rule 28(b)
  cells stamped in `docs/codebase-site/data/mechanism-matrix/NYISO.js` in
  this session.
* Rule 21: zero new free parameters introduced anywhere in this session.
* Rule 12: years sequential within each invocation; the two arm invocations
  ran concurrently (cap 2 for the plant-level LP).

## 6. THE FRONTIER VERDICT AT SESSION END

> **NOT-YET — by the owner's own definition ("we have tested everything we
> could have"), three testable lane objects remain untested**: the
> reserve-cohort graded duty (§2.1's named successor), the hydro RAMP10
> code seams, and the `online_rho` identification — plus the re-pointed
> Flynn/Bethlehem start-count residual. A frontier declaration cannot stand
> while those are live levers.

What changed in this session's favor, so the next declaration attempt reads
from a shorter and better-typed queue:

1. **The card's "last thing standing" is adjudicated.** The 2025
   offer-level/zonal-gradient object (owner card Q1, chartered by this
   session's directive) is now decomposed to completion: ~1/3 is the
   ledgered C3c summer face, measured (§1.3); the winter ~2/3 is PROVEN
   LOCATIONAL by solve (§2.2) with every lane route adjudicated — the
   fuel-side lever REFUTED-AS-ARMED, the seam split UNIDENTIFIABLE from
   public data (standing rule-20 refusal), tightening REFUTED by the
   as-enforced limits, the CE TTC accurate as carried. It is now an
   OWNER-COURT identification object (the BLOCKER-B intake class), not a
   lane lever. No solve can move it until new data exists.
2. **The DO-NOT-REDO ledger grew by two solve-tested rejections** with full
   gate records, and the standing `cc_reserve_duty_split` rejection narrowed
   to a single plant's duty story with the successor named.
3. **Four standing items closed or re-typed without solves** (§3): the D-4
   vintage guard shipped and live-verified; the taxonomy split executed;
   Astoria adjudicated non-blocking; Flynn re-measured and re-pointed.

**The path to frontier from here** (in queue order): (i) the reserve-cohort
graded duty A/B; (ii) the RAMP10 seams + an A/B on the reserve-supply side;
(iii) the `online_rho` identification (one identification unblocks the
`nyiso_synchronised_reserve` / `nyiso_incity_commitment_obligation` pair —
or, if no admissible measured source exists, their `G` adjudication); (iv)
the Flynn/Bethlehem start-conduct residual. All four are ordinary lane
sessions; none is blocked. When they are done, the remaining open set is
entirely owner-court (RHO_CLIP, the locational-identification intake, the
hydro certification intake, Q2 annotation) plus the ledgered C3c — which is
the shape a frontier declaration can honestly stand on, as nyiso-104's did.
