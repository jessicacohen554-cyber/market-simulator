# RESULT nyiso-146b/c — the duty-scoped LSL state floor is the NEW KEEPER; the CC over-cycling object is CLOSED

Session nyiso-146 (single session, continuing from the min-run rejection
`RESULT-nyiso146-perplant-min-run-ab-2026-08-19.md`). Pre-registrations
committed before every solve: `PREREG-nyiso146b-online-hours-and-reserve-duty-
2026-08-19.md` (arms B and C, incl. the disclosed arm-C plumbing amendment)
and `PREREG-nyiso146c-state-floor-duty-scoping-2026-08-19.md` (arm B2). All
years 2023/2024/2025, one bundle per arm, arms sequential; holdout freeze
ACTIVE and untouched. Gates record: `_nyiso146bc_gates.json`. FIVE runs
registered this session (rule 15): the control, the rejected min-run arm, and
the three arms below.

## 1. THE PROMOTION

**NEW KEEPER: `2026-08-19-nyiso-146c-state-scoped`** (bundle
`results/calibration/nyiso146c_state_arm`), determination **CALIBRATED**
(C1/C2/C3a/C3b/C4/C6/C8 PASS; C3c the lone ledgered caveat, **bit-identical
2/0/5 h** to the superseded keeper). Two fields over
`2026-08-18-nyiso-144-layup-exclusion`, single-delta at each registered link:

* `nyiso_gas_bridge_online_hours` — the ercot141 `floor_online_hours`
  detector leg on the NYISO bridge, **gas_cc-scoped**: a synchronized CC's
  LSL block is must-take in EVERY P0-online hour (the gap legs model the
  restart DECISION; this models the committed STATE they interpolate
  between). Zero new scalars — the level is the bridge's measured CC
  min-load fraction (0.523), capped at the base tranche.
* `nyiso_gas_bridge_state_floor_min_run` — the floor holds ONLY plants whose
  own measured plant-basis run-length p25 clears the **6.6× population gap**
  (`constants.NYISO_STATE_FLOOR_MIN_RUN_HOURS = 100 h` over the frozen
  nyiso-146 artifact `campd_perplant_min_run_NYISO.csv`): effective
  membership **{2539 Bethlehem, 56234 Caithness, 56196 Poletti}** (p25
  130-646 h) against the 7-20 h cyclers.

**What it buys — the nyiso-145 frontier-blocking object 1, closed:**

| plant | control P1 starts | keeper P1 starts | metered | median run ctl → arm |
|---|---|---|---|---|
| 2539 Bethlehem | 327 / 526 / 262 | **41 / 10 / 15** | 6 / 7 / 7 | 12/7/14 h → **68/144/319 h** |
| 56234 Caithness | 102 / 8 / 14 | **3 / 2 / 4** | 4 / 6 / 8 | 22/178/144 h → 3,000/3,132/1,980 h |

Zero new D-4/D-1 findings; the full no-degrade cohort (Athens, Cricket,
Saranac, Flynn, Valley, Bethpage, Poletti, Barrett, 2500) inside its
pre-registered bars; CC bridge forced share rises modestly (4.4→5.3 / 2.4→3.5
/ 1.8→2.2 %) and the K6′ escalation clears both legs. Delivery on-prediction
(gas_cc leg 17.06/19.00/17.67 TWh unscoped-basis check; scoped totals
5.0-5.7 TWh inside the [4,8] band). The `complete` marker is re-keyed with
both determinations re-verified (rule 22 D-5(b) — the superseded keeper
re-scores CALIBRATED, the stop does not fire); keeper auditor PASS 0/0.

## 2. THE CHAIN THAT GOT THERE — three pre-registered arms, two rejections doing real work

1. **Arm B, `2026-08-19-nyiso-146b-online-hours` — REJECTED-AS-ARMED, and it
   is the arm that MEASURED the keeper's scoping.** Unscoped, the state floor
   repairs the near-baseload cohort exactly (the table above) and
   **over-glues the intermediate-duty cyclers**: Athens-2025 69→9 starts
   against 63 metered, Cricket-2024 26→1 against 20, one new D-4 conviction
   (Saranac 2024, a 0.43-on-share cycler held on metered-zero hours). Fails
   pre-registered B-K3(b) (2 of 20 plant-years) and B-K4 (the new
   conviction). The repaired and the broken cohorts are exactly the two
   sides of the phase-0 run-length gap — which is the B2 membership.
2. **Arm B2, the keeper** (§1) — B + the duty scope; passes every gate.
3. **Arm C, `2026-08-19-nyiso-146b-reserve-duty` — REJECTED** on C-K2 +
   C-K5. The reserve-duty split (measured 7-plant capacity-only cohort →
   class peak band, 2.25× as the recipe resolves it) repairs three of the
   four object plants at ≥88 % in the gated years (Sterling −88/−90 %,
   Massena −89/−90 %, Batavia −93/−94 %) and moves Bethlehem's underrun the
   right way (3,224→3,484 GWh vs 3,639 metered, 2024) — but **Allegany**
   (hr 7.5, the cohort's most efficient) falls only −64/−50 % against the
   ≥80 % bar, and **C3a-2023 goes +9.0 % → +11.3 %**: the ~1.4 TWh of
   phantom cheap upstate energy was price-relevant, and 2023 held 1 pp of
   band headroom. Zero new D-4/D-1. Its first solve was INERT (registered
   as `2026-08-19-nyiso-146b-reserve-inert`): the frame-side seam was
   clobbered by the recipe's `pct_peaking`/`cc_duct_peaking` overrides —
   fixed (the override now applies LAST in `bins_to_fleet`), disclosed in
   the prereg before the valid solve.

## 3. WHAT THIS LEAVES ON THE QUEUE

1. **The merit-order inversion (defect B) is now a JOINT object with the
   2023 upstate price level.** The reserve-duty mechanism works for the
   Seneca fleet and its membership/plumbing are built, tested and frozen;
   what rejects it is (a) Allegany's efficient heat rate needing a duty
   story stronger than the class peak band, and (b) the fact that removing
   phantom cheap supply FIRMS 2023 upstate prices past a band that was
   already +9.0 % at the control. Re-arming it requires either the 2023
   overpricing root cause to move first, or an owner ruling that the
   +11.3 % reading with the phantom capacity REMOVED is the more truthful
   2023 (rule 14's discovered-bug reading — the control's +9.0 % is partly
   BOUGHT by ~1.4 TWh of energy from plants that were not running).
2. Flynn's start-count excess (over-starting at correct run length) —
   untouched by design in every arm; still open, now the largest remaining
   per-plant conduct object.
3. The out-of-lane items (RHO_CLIP card, Iroquois taxonomy, D-4 vintage
   guard charter, Astoria campus attribution) are unchanged.

## 4. REPRODUCTION

```
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso146b_armB_recipe  --out-dir results/calibration/nyiso146b_online_arm
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso146c_armB2_recipe --out-dir results/calibration/nyiso146c_state_arm
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso146b_armC_recipe  --out-dir results/calibration/nyiso146b_reserve_arm
python scripts/calibration_verdict.py --run-id 2026-08-19-nyiso-146c-state-scoped
```
