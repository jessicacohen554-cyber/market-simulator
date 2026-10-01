# FINDING — miso-144: the 19.3 GW "in-merit idle block" is ~97 % an INSTRUMENT UNIVERSE ARTIFACT, and the attribution CLOSES — the model's summer-afternoon price IS the merit-order clear of its own thermal stack (corrected copperplate median |Δ| $0.58, r 0.99, bias +$0.06 at `hi`). There is no in-model dispatch defect for the lane to fix. Queue item 5 is DISCHARGED; the C3a frontier moves to the ACTUAL side of the curve.

**Session:** miso-144, 2026-08-08. **Lane:** §5.4 queue **item 5 (NEW)** — the
in-merit idle block, miso-143's named successor. **Posture: NO LP SOLVED.** No
`ScenarioConfig` field, no parameter, no mechanism armed, no run registered,
**no cell verdict minted** (no mechanism tested for arming — BRANCH-INSTRUMENT
resolved the charter's object to an instrument correction, so G-B mechanism
naming never fired and G-C was never reached). Keeper **UNCHANGED** at
`2026-08-05-miso-132b-cc-committed` (bundle `results/calibration/miso132_ccmin_B`).

**PREREG** `results/calibration/PREREG-miso144-inmerit-idle-attribution-2026-08-08.md`,
pushed at **`017f6bee`** (blob **`5599ba80`**, verified against the remote)
**BEFORE any adjudicating statistic**, with 13 falsifiable predictions, four
pre-committed branches with priors, two construction-error stops, seven
kill-gate bars fixed in advance, and 11 traps each with a counter-measurement.
§10 of the PREREG disclosed in full every committed artifact read before
registration.

**Owner directive honoured:** target is the 2024/2025 mean-LMP level miss; the
"without disturbing the rest" constraint was enforced by pre-registered kill
gates that were never exercised (nothing armed). No C7 lane, no C7 ledger.

---

## 0. §0 re-verified from committed artifacts

`calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`, no
re-solve, all three years in one invocation (rule 16; rule 22 — MISO holds no
marker, 2023–2025 only): **`NOT-YET`**, rubric v3.1, **sole FAIL C3a
`price_mean`** (2025 −14.1 % MODEL MISS), sole ledgered caveat **C3c 1 of 1**,
C1/C2/C4/C6/C8 PASS with C1 skipped for all eight classes and C2 for both
families in 2025 (preliminary EIA-923 vintage), C8 ST_GAS **grounded above
budget** (31.9 / 33.1 / 45.1 % forced, all binding mechanisms clear D-4).
Identical to the charter §0. The bundle `metrics.json` stale `price_mean:
CAVEAT` noted and ignored (scorer authoritative; not re-discovered).

---

## 1. G-A0 — the replication is exact, six for six

`scripts/probes/_miso144_attribution.py` reproduces miso-143's
`footing_failure_diagnostic` construction byte-for-byte at HEAD (same harness,
same anchor, same mixed weighting):

| year | `lo` committed → replicated | `hi` committed → replicated |
|---|---|---|
| 2023 | 21,951.2 → 21,951.2 (Δ −0.01) | 20,966.2 → 20,966.2 (Δ +0.02) |
| 2024 | 20,001.0 → 20,001.0 (Δ +0.03) | 19,031.5 → 19,031.5 (Δ −0.02) |
| 2025 | 19,330.1 → 19,330.1 (Δ −0.02) | 18,210.2 → 18,210.2 (Δ −0.00) |

**P1 PASS** (bar ≤ 5 MW; measured ≤ 0.03 MW). The object is stable at HEAD;
what follows decomposes it, not a drifted cousin of it.

*(One instrument note, TRAP 7's spirit: miso-143's excess subtracts an
UNWEIGHTED thermal mean from a LOAD-WEIGHTED capability mean — an 807 MW
crossing in 2025. The ledger below restates A0 on ONE weight: 18,523.0 MW.
Both are reported; the replication used miso-143's own construction.)*

## 2. G-A1/G-A2/G-A3 — the ledger closes, and the block is the instrument

2025 JJA h12–17, load-weighted on C3a's own weight, MW. (2024 / 2023 in
parentheses where they matter; full three-year, two-window table in
`_miso144_attribution.json`.)

| term | `lo` | `hi` | what it is |
|---|---:|---:|---|
| **A0** (one weight) | **18,523.0** | 17,403.1 | the block, restated |
| **T_universe** | **18,764.6** | 18,764.6 | capability of NON-THERMAL fleet classes counted in `below` while their dispatch is EXCLUDED from `thermal` — **nuclear 10,664.8 + hydro 2,371.7 + import 4,272.0 + biomass 1,456.1** |
| **T_injected** | −1,135.7 | −1,135.7 | OTHER + biomass 12-value injections counted as served with no fleet capability behind them |
| **thermal_gap** (identity CC-1, dev < 0.001) | **894.1** | **−225.8** | what is left of the block on the same-universe thermal ledger |
| idle_sys_LB / oom_sys_LB (CC-2 exact) | 2,046.2 / 1,152.2 | 1,028.1 / 1,253.9 | cheapest-first class-grain bounds |
| floor-based OOM (unit-grain, `min_gen` × offer>anchor) | 1,266.8 | 1,346.7 | **ST_GAS per-plant must-run 965.6 + reliability-floor limbs 201.7–270.5 + CHP steam 99.5–110.6** (mechanism ids 16/4/2) — all three D-4-cleared families |
| T_zonal | 393.9 | 355.9 | in-merit at the demand-weighted mean anchor but not at the unit's own zonal price |
| T_tie (δ=$0.10) | 75.9 | 61.1 | the partially-loaded marginal rung |
| T_offerbasis (strict lo→hi) | — | 965.4 | P0-basis offers below price whose P1 offer is not |
| **strict in-merit idle** (own-zone price, δ=$0.10) | 1,576.5 | **611.1** | CT_PEAKER 411.3 + CC_REGULAR 122.2 + CHP 77.3 + ST_GAS 0.3 |
| **T_reserve** (rbdc held, partition asserted ≤ 1 MW) | 2,543.0 | 2,543.0 | the LP's physical co-optimized reserve holding |
| **T_resid** (strict − reserve) | **−966.5** | **−1,931.9** | **NEGATIVE — over-explained. The stop (\|resid\| > 3.0 GW) does NOT fire.** |

**Reading it off:**

1. **T_universe alone is 97–101 % of the block** (2025: 18,765 vs A0 18,523;
   2024: 106 %; 2023: 104 %). The committed miso-143 instrument summed
   `pmax × availability` over **every** fleet row with offer ≤ anchor —
   nuclear, hydro, import and biomass included — and subtracted dispatch over
   **`THERMAL_COLS` only**, which contains none of those classes
   (`_miso143_ladder.py` L325 vs L185; `_miso143_stack.py` L78). Nuclear alone
   — 10.7 GW in-merit, fully dispatched, dispatch excluded — is over half of
   the "block". **P2 CONFIRMED** (band [13.5, 19.5], point 16.5); **P13
   year-generality CONFIRMED** (the term is 97–106 % in all three years, as an
   explanation of a three-year block must be).
2. **The same-universe thermal gap is 0.9 GW at `lo` and −0.2 GW at `hi`** —
   at the honest offer basis the thermal fleet dispatches slightly MORE than
   its strictly-in-merit capability, because the floors force ~1.3 GW of
   out-of-merit ST_GAS/CHP in (the known, C8-grounded, D-4-cleared families;
   the displacement direction the charter's identity anticipated, at 1/15th of
   the block's size).
3. **Strict in-merit idle collapses to 0.61 GW** once measured at each unit's
   own zonal price at the `hi` offer basis — and sits entirely inside the
   **2.54 GW** the LP physically holds as reserve (miso-56/71's measured
   requirements). Complementary slackness has nothing left to explain:
   **T_resid ≤ 0 in every year, window and bracket.** The pre-registered stop
   never fires.
4. The reserve subtraction over-subtracts by construction (held includes
   non-thermal/storage backing — PREREG note), which is why the residual is
   negative rather than zero: the ledger errs on the side of leaving mass
   UN-explained, and even so nothing is left.

## 3. The corrected copperplate — the price side of the same artifact (SUPPLEMENTARY, post-hoc, labelled)

miso-143's pre-registered footing gate cleared the ALL-CLASS stack against the
THERMAL_COLS requirement and failed its own bar (median |Δ| 9.998 vs 4.00; bias
−10.9), firing BRANCH-INSTRUMENT-FAIL. That is the **same universe crossing**:
~16–18 GW of nuclear/hydro/import capability in the stack that the requirement
never asks to serve puts the marginal unit far too low. Re-clearing the
**thermal-fleet stack against the fleet-thermal need** (injections netted;
`_miso144_footing_corrected.py`, marked post-hoc — not among the pre-registered
predictions, two-sided by construction):

| 2025 JJA h12–17 | bias (keeper − clear) | median \|Δ\| | r |
|---|---:|---:|---:|
| miso-143 committed (all-class stack) | −10.86 / −10.60 | 9.998 / 9.661 | 0.853 / 0.859 |
| **corrected, `lo`** | **+1.00** | **0.995** | **0.992** |
| **corrected, `hi`** | **+0.06** | **0.581** | **0.992** |

All six year-windows land at median |Δ| $0.38–1.00 (worst mean bias +2.7,
2024 JJA `lo`). **The keeper's P1 price IS the merit-order clear of its own
thermal stack at its own offers, to a dollar.** The `v2` variant (need +
reserve held) overshoots negative (−1.4 to −4.7) — the reserve holding sits on
above-margin capability, which is also why the reserve balance duals are ~0 in
all but 5 hours of 2025 and why the adopted reserve mechanisms (miso-39/56/71)
do not lift ordinary summer prices.

## 4. What survives of miso-143, and what is corrected

**SURVIVES (above-anchor instruments, untouched by the below-anchor universe):**
the merit-order gain bracket (+$2.297/+$5.474 — replacement supply above the
anchor), the within-hour ladder slope ($1.496/MWh per GW) and its correction of
miso-142's empirical curve, the 16.14 GW ladder walk to the actual price, the
at-anchor marginal-tranche composition, and all four G-B mechanism
eliminations (B-1…B-4). **miso-142's verdict** (no quantity lever of admissible
size closes C3a) survives and is REINFORCED: the model's dispatch is
merit-order optimal, so there is no mis-dispatch to harvest either.

**CORRECTED:** (i) the footing-gate failure was the instrument's, not the
model's — the pre-registered response (re-anchor, gaps only) remains valid, and
every gaps-only number above the anchor stands; (ii) **the "19.3 GW in-merit
idle block" dissolves as a model object** — "the model's dispatch is NOT
merit-order at the margin: cheap capability is held out and dearer capability
is held in" is REFUTED by this attribution (the held-out part is nuclear
counted against a thermal-only denominator; the held-in part is 1.3 GW of
D-4-cleared floors); (iii) miso-143's "idle by class" percentages (CT_PEAKER
64.5 % etc.) were TOTAL idle fractions (`class_idle_frac` = 1 − dispatch /
capability over ALL capability), not the block's composition — the true strict
in-merit idle of CT_PEAKER is **411 MW (2.3 % of its capability)**, inside
reserve holding; (iv) the congestion refutation (r = −0.113) stands trivially —
the under-price it correlated against spread was the artifact, so its
non-correlation is expected; nothing there needs re-running (TRAP 2 honoured).

**Method note (the lane's fourth instrument correction in four sessions):**
miso-142 corrected miso-137's window framing, miso-143 corrected miso-142's
empirical slope, miso-140b corrected the comparator vintage, and this session
corrects miso-143's universe. Every one was caught by reproducing the prior
session's committed numbers before extending them — the discipline exists
because it keeps firing.

## 5. Predictions scored, against interest

| # | prediction (2025 JJA h12–17) | outcome |
|---|---|---|
| P1 | replication ≤ 5 MW × 6 | ✅ ≤ 0.03 MW |
| P2 | T_universe ∈ [13.5, 19.5] GW, point 16.5 | ✅ **18.76** (above point by 2.3) |
| P3 | T_injected ∈ [0.7, 1.4], point 1.0 | ✅ **1.136** |
| P4 | thermal_gap ∈ [0.8, 6.8], point 3.8 | ⚠️ **0.894 at `lo` — at the band's floor; −0.226 at `hi` — OUTSIDE the band entirely (sign flip the band failed to anticipate)** |
| P5 | OOM_LB ∈ [0.8, 4.5], point 2.0 | ✅ 1.15/1.25 (2023 `lo` 0.51 — below band; point over-estimated) |
| P6 | CC-2 identity | ✅ dev < 0.001 MW |
| P7 | T_zonal ∈ [0.2, 2.5], point 0.9 | ✅ 0.39 (below point) |
| P8 | T_tie(0.10) ∈ [0.1, 3.0], point 0.6 | ❌ **0.076 — BELOW the band.** The feared CT tranche cluster at the price did not materialise |
| P9 | T_offerbasis ∈ [0.5, 1.8], point 1.1 | ✅ 0.965 |
| P10 | T_reserve ∈ [2.2, 3.2], point 2.65; partition ≤ 1 MW | ✅ 2.543; partition holds |
| P11 | T_resid ∈ [−1.0, +1.5]; STOP \|resid\| > 3.0 | ⚠️ `lo` −0.97 in band; **`hi` −1.93 outside the band** (inside the stop — over-subtraction direction pre-disclosed, magnitude under-called) |
| P12 | ramp term 0 (structural) | ✅ `ramp_limits=None`, `min_gen` lower bounds only |
| P13 | year-generality ±25 % | ✅ 97/106/104 % |
| — | branch priors | **BRANCH-INSTRUMENT (65 % prior) fires on its pre-registered condition** (instrument terms ≥ 60 % of A0; stop silent) |

**Recorded against interest:** P4's `hi` sign flip and P11's `hi` magnitude
were outside their bands (both in the direction that makes the block SMALLER
than predicted — the artifact was even more total than the charter-motivated
prior allowed); P8 missed low; P5's point was high. The three band misses all
push the same way: even this session's prior UNDER-estimated how completely
the block dissolves.

## 6. What this licenses, and where the C3a frontier now stands

**Nothing is armed.** No mechanism was tested (BRANCH-INSTRUMENT is an
instrument verdict, not a mechanism verdict), so no cell verdict is minted
(rule 28(b)) and no run is registered (rule 15 — no LP).

**Queue item 5 is DISCHARGED with the object DISSOLVED.** Its reopen condition:
a measurement showing material in-merit idle capability *on a same-universe,
own-zone-price, P1-offer-basis ledger* that reserve holding and D-4-cleared
floors cannot absorb. No such mass exists at HEAD (largest strict residual
anywhere: −0.9 GW, i.e. over-explained).

**The C3a frontier, stated for the owner — every model-side family is now
closed by measurement:** quantity (miso-142, on reach), merit-order re-ranking
(miso-143, all four mechanisms eliminated), and dispatch/price-formation
optimality (this session: the price is the merit-order clear of the stack to
$0.58 median). What remains is the object miso-142 measured and nobody has
owned since: **the model's stack itself never reaches the actual price** (max
$51.97 anywhere in 2025 JJA h12–17 vs actual load-weighted $74.68; real curve
$2.15/MWh per GW vs model $0.64). With dispatch exonerated, the deficit lives
in **offer LEVELS above SRMC in ordinary summer-afternoon hours** — market
conduct / adders the model's SRMC-anchored offers do not carry — or in real
capability loss the fleet's measured availability does not reproduce (the
ambient-derate family is already refused at 30–39× too small, miso-139, and no
quantity lever reaches, so conduct is the live direction).

**This is NOT the C3c scarcity-tail list re-opened** (charter demanded the
difference be shown): the C3c ledger covers the >$200 spike tail (88 hours in
2025) priced by MISO's administrative ORDC/RCPF machinery over sub-hourly
uncertainty; the object here is the **−40 % miss across 403 ordinary July
window hours at an actual price of ~$75** — below every scarcity step, in
hours with zero model shortfall and reserve duals of zero. The exhausted list
(reserve deliverability, ramp caps, subregional reserves, measured
requirements) was tried against the tail and is adopted; none of it is an
ordinary-hour offer-level mechanism. A successor needs a **NEW measured
identification of summer-afternoon offer conduct** — and one candidate source
exists that this program has never intaken: **MISO publishes its actual RT/DA
offer curves at a ~90-day lag** (Market Data → historical offer sets), a
measured, forward-regenerable, rule-13-admissible input that would identify
offer-vs-SRMC conduct directly rather than by residual. Chartering that intake
is an **owner decision** (rules 19/24 — new mechanism, new data source), not
this session's to take.

## 7. Kill gates

Not exercised — no arm was proposed and no solve was spent. The bars stand
recorded (C3b-2025 0.191 vs ≤ 0.200; C3a 2023/2024 PASS; C1/C2 gated years;
C4; C8 with ST_GAS 45.1 % grounded; C3c 1/1 SPENT; fail-set ⊆ {C3a}) for
whichever successor next reaches a G-C.

## 8. Rule duties, and the traps

- **Rule 15** — no LP solved, no run to register (miso-131…143 precedent).
- **Rule 28(b)** — no cell verdict minted; the **§5.4 queue stamp is written
  this session** and item 5 is written into the queue as discharged.
  No `ScenarioConfig` field (28(c) silent); no other ISO touched (28(d)).
- **Rule 22** — 2023/2024/2025 only; MISO holds no marker.
- **Rules 13/14/19/21/23/24/25** — every number a committed artifact or the
  orchestrator's own reconstruction; nothing sized to a residual; no derive
  script re-run; no tuning channel; no cross-ISO transfer.
- **Probe hygiene (miso-140b §6)** — both probes insert the REPO ROOT and
  assert `load_zonal_shares(...)` non-None via the reused `_miso143_stack`
  `hygiene()`.
- **DO-NOT-REDO** — congestion not re-run (T_zonal is the instrument's
  price-basis term, stated as such); quantity family untouched as a lever; no
  seam re-open (import's 4.27 GW universe line cites the armed
  `miso_seam_envelope_merit_cap` as its owner); no `*_lw` re-derivation; the
  trough window untouched; `miso_cc_coal_rebalance` and
  `cc_nameplate_summer_derate` untouched.
- **Traps:** TRAP 9's counter fired as designed (family partition asserted ≤
  1 MW — summing families would have tripled the reserve term); TRAP 10's
  12-value assertions held; TRAP 7's counter surfaced miso-143's own 807 MW
  weight crossing; TRAPs 1–6, 8, 11 honoured as pre-registered.
- **Concurrent-session check** — at open and close: one open PR (CAISO #3736),
  no other MISO branch beyond miso-143's merged leftover.

## 9. The generalisable lesson

**AN IDENTITY IS ONLY AS GOOD AS ITS UNIVERSE.** A subtraction is a claim that
its two sides count the same population. miso-143's block subtracted
thermal-classes-served from all-classes-offered, and 97 % of the result was
the population difference — nuclear, hydro, imports and injections — wearing
the costume of a dispatch defect. The check that caught it cost one afternoon:
list the classes on each side of the minus sign before believing the
difference. The corollary for this lane: **before attributing a residual to a
mechanism, close its accounting identity first** — the charter's G-A-before-G-B
ordering is what kept twelve floor limbs from being prosecuted for an
instrument's crime.

---

**Artifacts** (all committed): PREREG (`017f6bee`, blob `5599ba80`) ·
`_miso144_attribution.json` · `_miso144_footing_corrected.json` · probes
`scripts/probes/_miso144_attribution.py`,
`scripts/probes/_miso144_footing_corrected.py` · this finding · the §5.4 queue
stamp and `docs/calibration-log/miso.md` entry.
