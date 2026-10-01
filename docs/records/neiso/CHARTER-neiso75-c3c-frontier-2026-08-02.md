# neiso-75 — the NEISO C3c frontier charter

**Date:** 2026-08-02 · **Scope:** NEISO, charter session (matrix §5.6 frontier
discipline: "charter required before any lever") · **NO LP SOLVED, no keeper
change, no bundle, no dashboard registration** (the neiso-71/73/74 disposition).
**Keeper:** `2026-07-31-neiso-72-hy-window` (bundle
`results/calibration/neiso72_hy_window_B`), untouched.
**Probe:** `scripts/probes/_neiso75_c3c_decomposition.py` (read-only; imports the
xiso-1 loaders so the construction is identical).
**Record:** `results/calibration/PROBE-neiso75-c3c-decomposition-2026-08-02.txt`.

Charter tasks, per the queue brief: (a) decompose the C3c miss into the
systemic-amplitude share vs any NEISO-local scarcity/winter share, no-LP;
(b) enumerate candidate levers with rule-17 shape, matrix cells, and
standing-order blocks; (c) pre-register kill rules for the ONE recommended
lever, or conclude frontier-blocked and route to the owner.

---

## 0. Verdict

**The C3c miss is two different defects wearing one criterion, and they split
by year.**

* **2025's FAIL is majority the SYSTEMIC diurnal-amplitude defect** (xiso-1):
  restoring the year's measured daily-cycle gain to the keeper's own price
  carries 10 of the 20 missed hours over $300 and produces a full-year model
  tail of 25 h — inside the [10, 40] gate band — with **every crossing on the
  five real event days**. The amplitude lane (§5.6 item 1) is the right and
  sufficient first lever for 2025.
* **2023's FAIL is NEISO-local winter formation and is MEASURED-UNREACHABLE at
  the DA-formation ceiling.** 9 of its 10 winter tail hours are RT-only: the
  real market's own day-ahead — clearing the full real offer book, every
  conduct premium included — priced ≥ $300 in only **5** hours of 2023 against
  a gate floor of **8**. No DA-type formation mechanism, however faithful, can
  close the 2023 gate; the residual channel is RT-only formation, which the
  rubric itself classes out of representation for a realized-weather hourly
  LP. **2023 is frontier-blocked → routed to the owner (§5).**
* **2024 needs nothing**: its gate already passes on the small-count rule
  (|0−8| ≤ 10), and its miss is 7/8 pure RT transients (all DA < $185).

**One lever is recommended and pre-registered (§4): the §5.6 item-1 DA-book
diurnal-formation identification** — supply-conduct limb first (the corpus is
already on disk), demand-depth limb second — behind kill rules K1–K5.
**This charter authorizes Phase-0 (measurement, no LP) only; any solve arm
requires its own pre-registration on Phase-0's surviving numbers.** The
standing order (xiso-1) is untouched: no storage-side lever is chartered, and
the rubric diurnal-amplitude criterion remains the owner's open call (§6),
surfaced here with new sizing evidence, not decided.

---

## 1. The gate and the miss (facts on record)

C3c (rubric v2.7): model settlement-price hours > $300/MWh (NEISO threshold,
`TAIL_THRESHOLD`) gated against the committed **RT hourly** actual count —
band [0.5×, 2×] for actual ≥ 10, |model − actual| ≤ 10 below that
(`scripts/calibration_verdict.py::score_price_tail`). DA is the report-only
diagnostic basis.

| year | actual RT | actual DA | model | gate needs | verdict |
|---|---|---|---|---|---|
| 2023 | 15 | 5 | 0 | ≥ 8 (band [8, 30]) | FAIL (ledgered) |
| 2024 | 8 | 5 | 0 | \|m−8\| ≤ 10 | PASS (small-count) |
| 2025 | 20 | 12 | 0 | ≥ 10 (band [10, 40]) | FAIL (ledgered) |

Keeper model maxima $249 / $218 / $281; the co-opt reserve dual is $0.00 in
all 26,280 train hours (attestation). The RT hour-set anatomy (attestation,
2026-07-16 re-check) stands, with one correction found here **against
interest**: the attestation's **2024 event-day names are one calendar day
early** (Jun-17 → Jun-18, "Jul-7 Sun" → Jul-8 Mon, Jul-31 → Aug-1, Dec-2 →
Dec-3) — verified against the raw ISO-NE SMD workbook
(`data/raw/lmp-data/NEISO/2024_smd_hourly.xlsx`: RT max $2,112.77 on
**2024-08-01** HE19). A leap-year dating slip in the ledger prose only; counts,
hours, scoring, and the committed parquets (label-keyed, Feb-29 dropped) are
unaffected. To be corrected whenever the attestation text is next regenerated;
not edited in place by this session.

---

## 2. The decomposition (charter task a)

Method (probe §docstring): split model and actual into DAILY LEVEL (24-h mean)
+ WITHIN-DAY DEVIATION, and form three counterfactual model prices —
**CF-A** "gain restored" (the model's own deviation scaled by the year's
measured/model hour-of-day range ratio: the *systemic-defect* counterfactual),
**CF-B** "shape graft" (the actual's own deviation on the model's daily level:
the *upper bound of every within-day mechanism*), **CF-C** "level graft" (the
actual's daily level with the model's own deviation: an *event-day level*
mechanism alone). Amplitude gains G = 3.66 / 4.35 / 2.92 (RT basis); the
loader check reproduces the xiso-1 NEISO row exactly (level +3.9/+5.0/+2.8 %,
amplitude 27.1/23.6/29.9 % of DA; hod ranges model $7.03/$6.82/$13.30 vs DA
$25.96/$28.96/$44.47).

**Hour-matched closability of the 43 missed RT tail hours:**

| year | n | CF-A (systemic) | CF-B (within-day UB) | CF-C (level) | JOINT-ONLY | DA-visible |
|---|---|---|---|---|---|---|
| 2023 | 15 | 3 | 5 | 0 | 10 | 1 |
| 2024 | 8 | 0 | 7 | 0 | 1 | 0 |
| 2025 | 20 | **10** | 16 | 5 | 3 | 6 |
| all | 43 | **13** | 28 | 5 | 14 | 7 |

**Full-8760 counterfactual tail counts vs the gate:**

| year | keeper | CF-A | CF-B | CF-C | CF-A placement |
|---|---|---|---|---|---|
| 2023 | 0 FAIL | 14 "PASS" | 12 PASS | 0 FAIL | **mis-timed**: 0/14 on Feb-4 (the event); prints Feb-3 ×4 + Sep-5..7 ×10 |
| 2024 | 0 PASS | 1 PASS | 7 PASS | 0 PASS | 1 crossing, on a DA-tail day |
| 2025 | 0 FAIL | **25 PASS** | 18 PASS | 7 FAIL | **well-placed**: all 25 on the five real event days; 10/25 exactly on tail hours |

Reading, share by share:

1. **Systemic-amplitude share = 13/43 hour-matched, ALL summer, 10 of them
   2025.** Restoring the measured daily-cycle gain closes zero winter hours in
   any year: the winter hours' required within-day gain is far beyond the
   systemic defect (median needed gain 6.8× in 2023, 20.8× in 2025, 32.8× in
   2024, vs systemic G 2.9–4.4; three 2023 hours have non-positive model
   deviation — no gain closes them). In gate terms the systemic share **is**
   the 2025 FAIL: CF-A prints 25 h inside [10, 40] on the right days. In 2023
   CF-A's nominal 14-count "pass" is a mis-timed tail (the caiso-144 hazard):
   it never prints the Feb-4 arctic-blast block and over-prints Sep 5–7.
2. **RT-transient share (CF-B \ CF-A ≈ 15/43).** The entire 2024 summer set
   (needed gains 20–33×; DA < $185 in all 8 hours; day levels: model $39–92 vs
   RT day means inflated by the spikes themselves), Jul-5-2023 ($1,162 RT vs
   $129 DA), the Nov-23-2025 shoulder pair ($529/$865 RT vs $117/$91 DA).
   This is the DA–RT forecast-risk wedge the rubric classes out of
   representation; only 7 of 43 tail hours were DA-visible at all.
3. **Winter-local share (18/43; 0 closable by CF-A).** Two distinct anatomies:
   * **2023 (Feb-4 ×9, Feb-26 ×1): joint level + within-day.** Feb-4 day
     levels: model $195, DA $227, RT $275 — a −$32 model-vs-DA level shortfall
     (in representation: cold-day fuel/offer formation) UNDER a +$48 DA-vs-RT
     wedge (out of representation). Feb-26 evening: model day $46 vs DA $114
     vs RT $201. Even CF-B (perfect within-day shape) closes only 3 of the 10;
     CF-C (perfect day level) closes 0.
   * **2025 (Jan-17/20/22, Feb-10, Dec-10 ×7): within-day only.** The model's
     winter day LEVELS are essentially right (Jan-17 model $206 vs RT $196;
     Jan-20 $196 vs $163) — the misses are RT morning/evening spikes (CF-B
     closes 5/7). Nothing here is the daily-cycle defect (CF-A 0/7).
4. **The DA-formation ceiling, measured.** The real DA — the full real book —
   cleared ≥ $300 in **5 / 5 / 12** hours. Against gates of ≥8 / ≤18 / ≥10:
   **2023 is unreachable by any DA-type formation** (5 < 8), 2024 needs
   nothing, 2025 passes at the ceiling with 2 h of margin — and the model is
   already close on 2025's DA-visible block (model $259–281 vs the $300 line
   on Jun-24; DA itself $316–475 there). A model printing *more* winter-2023
   tail than the real DA did would be pricing RT-only formation (adjudicated
   out of representation) or fitting the residual (rule 13).

**Answer to (a): the systemic-amplitude share of the C3c miss is 13/43 hours
(30 %), concentrated in and gate-decisive for 2025; the NEISO-local share is
the 18-hour winter block (joint level+shape in 2023, RT-transient in 2025) plus
the 15-hour RT-wedge, and the 2023 gate specifically is closed by NO
representable formation — its measured DA ceiling (5 h) sits below the gate
floor (8 h).**

---

## 3. Candidate levers (charter task b)

Frontier discipline (§5.6): every named admissible mechanism in the
winter/summer scarcity family is on record; anything below needs its own new
charter with a new measured identification. The neiso-58 §3 scope clause named
the admissible identification classes: **dual-fuel/oil-parity offer formation,
import offers, DA load/virtual bids** — i.e. §5.6 items 1 and 2.

| # | lever | matrix cell (NEISO) | rule-17 shape (driver / window / forward story) | status for C3c |
|---|---|---|---|---|
| L1 | **DA-book diurnal formation** (§5.6 item 1: supply-conduct limb + DA-depth limb) | `da_virtual_bids` **U → O this session** (chartered); `diurnal_price_amplitude` U | driver: the submitted DA book (`hbdayaheadenergyoffer` corpus, on disk, 1,058/1,096 days, event days verified; demand side behind K3 existence). window: all-hours offer formation (not a floor — no rule-17 window owed; identification/DOF rules bind instead). forward story: conduct conditioned on forward-reproducible drivers (hour-of-day, net-load, month), the ERCOT G-22 / cleared-share-ladder admissibility class | **RECOMMENDED (§4).** Targets the systemic share = the 2025 gate; also the unblocking condition for the xiso-1 standing order |
| L2 | **Import-side scarcity** (§5.6 item 2: HQ/NB tie behavior in tight hours) | `import_hub_pricing` K (fixed HQ tranches); `priced_interchange` U (priced node untested at NEISO) | driver: measured tie schedules vs temperature (EIA-930 interchange, in repo); window: cold-event hours; forward story: temperature-conditioned import response | NOT chartered. Ceiling bounded by §2.4: it is DA-type formation, and the 2023 winter block it would target is 9/10 RT-only — it cannot close any gate the recommended lever doesn't. Stays an owner option (§5) for winter *fidelity* (level share), not for C3c |
| L3 | **Declared-window emergency tiers** (OP-4 / M/LCC-2 + RCPF ladder, the MISO `maxgen` analogue) | `maxgen_emergency_tier_pricing` U | driver: ISO-NE's declared-window registry (NOT in repo — data-first); window: declared hours; forward story: fires from model-simulated tightness (miso-70 pattern) | NOT chartered. Two blockers: no declared-window registry on disk, and rule 19 — the in-LP RCPF co-opt (`energy_reserve_coopt` K) already owns reserve-scarcity pricing at NEISO; a tier overlay must replace/reconcile, not stack. Owner option (§5) |
| L4 | **Dynamic reserve requirements, Limb A promotion** (neiso-57) | `dynamic_reserve_requirements` R | measured as-enforced hourly requirements (built, un-promoted; LOYO-gated owner decision on record) | Not a gate-closer: engages exactly 1 of the 2025 tail hours (Jun-24 18:00 → $397). Its promotion remains the owner's standing decision; nothing new here. DO-NOT-REDO the test itself (cell R) |
| L5 | **Storage-side PS levers** (adder / RTE / duration / AS value) | `pumped_storage_cycling_depth` G | — | **BLOCKED by the xiso-1 standing order** (DO-NOT-REDO until the diurnal-amplitude defect closes; neiso-74 premise inversion stands) |
| L6 | **Re-arm `neiso_offer_surface_conditional`** (Limb B) | `measured_offer_surface` I | — | NOT chartered; DO-NOT-REDO stands. The I adjudication (neiso-58: dormant — the real tail forms while the model holds GW of cheaper non-fast-start headroom) is untouched by this charter; §4's supply limb is a NEW identification (within-day movement of the body band), not a re-conditioning of the tail-rung artifact. The caiso-154 fuel-tail exposure on its q0.7/q0.9 rungs is inherited as kill K4 |
| L7 | **Winter fuel-security family** (coldsnap derate, fuel inventory, mustrun, oil budget) | `winter_fuelsec_posture` K (dormant), `gas_coldsnap_derate` K | — | Exhausted on record (2026-07-11 frontier designation; attestation: dormant on 2023–25, unchanged vs the zero-forcing twin). §2 confirms the winter share they targeted is majority out-of-representation anyway |
| L8 | **Any offer adder / multiplier / hinge sized to the tail or the amplitude gap** | — | — | **FORBIDDEN** (rules 1/5/13/21/24; xiso-1 §7 states it for the amplitude gap explicitly) |

---

## 4. The recommended lever, pre-registered (charter task c)

**L1 — the §5.6 item-1 DA-book diurnal-formation identification.** Theory of
change, stated before any measurement: the keeper's offer stack is
**within-day static by construction** (daily fuel shape, static tranche
markups, run-constant P1 startup amortization), while xiso-1's attribution has
`CC_REGULAR` absorbing 2,045 MW of the 4,117 MW diurnal demand swing with
peakers already online at the trough — the same offer band marginal at h02 and
h17. If the *measured* submitted book moves within the day (the marginal band
offering systematically dearer at the peak than overnight), that movement is a
measured, forward-conditionable conduct object the model lacks, and it is the
missing amplitude. If the book does NOT move, the supply-conduct limb is
empty — and that kill is itself decisive evidence (the amplitude then lives in
demand-side depth, imports, or non-book physics), which is exactly what a
charter-gated identification is for.

**Phase-0 (authorized by this charter): measurement only, zero LP.** Corpus:
the on-disk `hbdayaheadenergyoffer` daily CSVs (README-documented gaps;
regenerate via the committed fetcher, train years only). Statistic, frozen
now: per (asset, day), the capacity-weighted mean submitted incremental-segment
price over peak hours (h16–19 EST) minus over trough hours (h01–04 EST);
aggregated capacity-weighted over the **non-fast-start band** (the complement
of neiso-58's physics selection, Claim30 < 0.9 × EcoMax), per year; conditioned
only on hour-of-day × net-load bin × month.

Kill rules (all pre-registered; any one fires → that limb is dead and the cell
re-stamps accordingly):

* **K1 — movement floor.** The supply limb dies if the fleet-level within-day
  movement is **< $5/MWh in 2023 and 2024, < $8/MWh in 2025** (≈ 25 % of each
  year's measured hod-range gap: $18.93 / $22.14 / $31.17). Below a quarter of
  the gap, supply conduct cannot be the dominant carrier of the defect.
* **K2 — conditioning admissibility.** Conditioning is hour-of-day × net-load ×
  month (temperature allowed as a forward-reproducible driver) and **never the
  clearing price or the residual**. If movement ≥ K1's bar is obtainable only
  under price-conditioning, the limb dies (rule 13 circularity).
* **K3 — demand-limb existence + λ0-attractor.** The demand-depth limb runs
  only behind: (i) ISO-NE must publish a SUBMITTED priced DA demand/virtual
  book (price axis + MW, hourly, 2023–25) — cleared-only MW kills it (the
  nyiso-94 blocker); (ii) the miso-105 attractor test — if the book's crossing
  price reproduces the DA clearing price to ≤ $2 AND the book's stiffness
  against the model stack's elasticity implies ≥ 30 % of hourly price
  displacement supplied by the bid curve, the limb dies (rules 1/13: the
  model's price would become the measured book's price).
* **K4 — fuel-granularity robustness (the caiso-154 filed exposure).** Every
  conduct statistic is recomputed excluding the 34 Algonquin fuel-tail days
  (the Feb-2023 arctic week + the Dec-2025 weekly-anchor ffill plateau). A
  component moving > 15 % relative is treated as fuel-series granularity, not
  conduct: re-derive on a daily-grain fuel basis or drop the component.
* **K5 — event-day coverage.** The statistic must be computable on the five
  2025 event days (Jun-23/24/25, Jul-28/29 — README-verified present). If any
  is absent from the corpus at derive time, the C3c-placement half of the lane
  shrinks to amplitude-only and the prereg must say so.

**Phase-1 (a solve arm): NOT authorized by this charter.** If Phase-0
survives, the arm needs its own pre-registration, which MUST carry these gates
verbatim (formulas frozen here; the numeric bar for G1 is fixed from Phase-0's
measured movement before any solve):

* **G1 amplitude:** hod-range model÷DA improves from 27.1 / 23.6 / 29.9 % by
  at least half of Phase-0's measured supply-conduct share of the gap, all
  three years.
* **G2 C3c-2025 count AND placement:** model settlement tail ∈ [10, 40] h with
  ≥ half of all model > $300 hours landing on days carrying actual RT tail
  hours (the caiso-144 anti-mis-timed-tail gate).
* **G3 neutrality:** C3a and C3b stay PASS in all three years; C1 free-band
  counts do not degrade (12/12 stays 12/12).
* **G4 level:** annual level error vs DA stays within ±8 % (currently
  +3.9 / +5.0 / +2.8 % — xiso-1 (b): the level passes by cancellation today,
  so the level effect of any amplitude fix is pre-registered, not discovered).
* **G5 hard kills:** C3b flipping FAIL in any year kills the arm outright;
  2023 must not degrade on any scored criterion.
* **Discipline:** LOYO within 2023–25 before any promotion (rule 22); no
  storage-side co-lever in the arm (standing order); PS throughput is
  *reported* against interest but never graded (neiso-74's 45 %-of-optimum
  caveat); no grading on the amplitude ratio alone (xiso-1 §7).

Expected honest outcome, stated in advance: L1 at its best closes **2025 and
the amplitude defect**. It does not close 2023 (§2.4), and 2024 needs nothing.
A successor that finds L1 delivering 2025 + amplitude should treat that as
full success, re-stamp `da_virtual_bids` and `diurnal_price_amplitude`
accordingly, and leave 2023 to the owner's §5 decision — not stack a winter
mechanism on the same arm.

---

## 5. Frontier-blocked residue → the owner

**C3c-2023 cannot be closed by any admissible lever this charter can name.**
The measured chain: 10 of 15 hours are winter; 9 of those 10 cleared the real
DA below $300; the full real book's DA ceiling is 5 h against a gate floor of
8; the residual channel is RT-only formation, adjudicated out of
representation for the realized-weather hourly LP (rubric v2.7's own DA/RT
framing, the 2024-exception precedent). Three owner options, none exercised
here:

1. **Accept and hold.** Keep C3c-2023 as the ledgered MODEL-MISS caveat it
   already is (the nyiso-104b pattern: an exhausted queue on a diagnosed
   structural limit, with the 2023 ceiling now measured). Zero cost; the
   charter's evidence upgrades the ledger text from "dormant mechanisms" to
   "measured DA ceiling below the gate floor".
2. **Winter fidelity lane (not a C3c lane).** Authorize the
   oil-parity/dual-fuel offer-formation identification (the third neiso-58
   class) on the same DA-book corpus — target: the −$32 Feb-4 model-vs-DA day
   level and the winter C3a/C3b/C5b fidelity share, explicitly NOT the 2023
   C3c gate (unreachable). Own charter + prereg required; K2/K4 apply
   verbatim.
3. **Representation change.** Only an RT-formation representation (sub-hourly
   scarcity, forecast-error pricing) could reach the 36/43 RT-only hours; that
   is a methodology-spec change (owner-level, cross-ISO), not an NEISO lever,
   and nothing in this charter recommends it.

---

## 6. Owner calls surfaced (not decided)

1. **The rubric diurnal-amplitude criterion** (filed by neiso-74, re-filed by
   xiso-1, re-surfaced here as instructed). New sizing from §2: C3c is a
   *proxy* for the amplitude defect in exactly one of six ISO-years-with-FAIL
   (NEISO-2025); everywhere else the defect is invisible to every load-bearing
   criterion. If the owner adds the xiso-1 statistic as a criterion, L1's
   success becomes directly scored and C3c stops carrying a burden it measures
   only obliquely. This charter takes no position and changed no scorer.
2. **The L1 execution green-light.** §5.6 item 1 is owner-gated; this charter
   discharges the "charter required" precondition (it is the chartered charter
   session) and authorizes Phase-0 measurement only. If the owner prefers to
   veto even Phase-0, the cell re-stamps O → U with this charter as the
   standing prereg.
3. **§5 residue disposition** (options 1–3 above).
4. Standing, unchanged: Limb-A promotion (L4, LOYO-gated owner decision);
   §5.6 item 5 (STEP 3 seam disposition).

---

## 7. Governance

No LP solved; no config changed; no bundle written; no dashboard registration
(rule 15 binds bundles; there is none). Years 2023–2025 only; the holdout
spend freeze is ACTIVE; NEISO's locked test is SPENT and untouched; nothing
outside the training window was read (rule 22). The probe reads committed
keeper sidecars + committed actuals and feeds nothing back into any solve
(rule 13 not engaged — the xiso-1/neiso-74 disposition). Rule 25: every number
here is NEISO's own; the cross-ISO xiso-1 context transfers no verdict.

Matrix duties (rule 28) discharged this session: `da_virtual_bids` NEISO
U → O (chartered, this document + kill rules); `diurnal_price_amplitude` and
`measured_offer_surface` NEISO notes updated (charter boundary; the I stamp
and the caiso-154 exposure stand); NEISO header re-check stamp; §5.6 item 1
stamped CHARTERED with the frontier-decomposition summary and the §5 routing.
Log: `docs/calibration-log/neiso.md` neiso-75 entry.

**DO-NOT-REDO:** do not re-measure this decomposition — re-run
`scripts/probes/_neiso75_c3c_decomposition.py` (it reads the live keeper store
at zero LP cost). Do not re-open L5/L6/L7/L8 on this charter's authority; only
K-survival re-opens anything, and only L1.
