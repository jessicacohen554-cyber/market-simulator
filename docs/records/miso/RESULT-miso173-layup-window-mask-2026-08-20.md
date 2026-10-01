# RESULT miso-173 — the measured lay-up window mask: ALL KILLS SILENT, **PROMOTED TO KEEPER**, and the MISO bundle's D-4 conduct failures go to ZERO

**Session miso-173, 2026-08-20.** Executes
`PREREG-miso173-layup-window-mask-2026-08-20.md`, committed — with its
pre-solve engine-build predictions frozen in
`_miso173_layup_mask_instrument.json` — before any solve. Control
`miso173_control`, arm `miso173_layupmask`, both `--year 2023 2024 2025`
sequential in one invocation (rules 12/16), solved consecutively on the 15 GB
container (FINDING-miso169 recipe: pins + 8 GB swapfile +
`MARKET_SIM_HIGHS_THREADS=4`).

**Outcome: EVERY PRE-REGISTERED KILL IS SILENT and the pre-registered target
(M-4b) cleared. Promoted to keeper `2026-08-20-miso-173-layup-mask` on the
arm's own candidate rule — no owner override needed.** Determination
**UNCHANGED at NOT-YET on C3a-2025 (−11.8 %) ALONE**, C3c the single ledgered
caveat: this promotion buys structural legitimacy — the floors no longer
contradict the model's own measured lay-up record — not a determination
change.

## 1. The object, decided and defended (the charter's three candidates)

The 1402 seasonal/part-year lay-up defect is the **commitment-window
object**. The decisive fact, found in this session: the missing windows
already exist in the repo, produced by the model's own outage pipeline. The
merit-order guard (`scripts/lib/outage_detect.py`, frozen) partitions every
detected ≥ 5-day full stop into MECHANICAL OUTAGE (enters the availability
envelope) or ECONOMIC LAY-UP (`campd-unit-outages-layup-MISO.csv`), the
latter kept out of the envelope on the express charter that *"an economically
idle unit is AVAILABLE; the LP declines it on its own economics."* The engine
then contradicted its own adjudication: the must-run floor **forced** 1402 on
for 2,542 hours of 2023, 71.1 % of them inside windows the pipeline had
classified as not-operating (unit 3 in lay-up Jan 1 – Mar 9 at out-of-merit
share 1.0; both units Oct 4 / Nov 4 – Dec 31; meter online share 0.000–0.058
in those months).

* **NOT a seasonal availability correction** — the windows are the guard's
  ECONOMIC class; feeding them back as unavailability would re-arm the
  23–46 % CC phantom-outage bias the guard exists to remove, fail rule 13
  ("didn't run" → "couldn't run"), and reach into reserves/cushion/retirement
  economics where no symptom exists. The admissible unit-grain physical
  instrument for MISO also does not exist (miso-157/160: MOM is fleet-grain,
  CAMPD inadmissible for outage measurement).
* **NOT a per-year census tier** — 1402 is a cycler (it ran Apr–Sep 2023);
  exclusion deletes a floor that is right in kind and wrong in
  hour-eligibility. The "1402 never enters the census" line has now held
  **five** times.
* **IT IS the floor's hour-eligibility** — membership
  (`mustrun_plant_exclusions`), window size (`online_frac`), level (p25) and
  hour-eligibility (this mask) are four orthogonal properties of the ONE
  floor (rule 19); the mask refines the last using the same measured-conduct
  family that identifies the other three.

## 2. The mechanism

`ScenarioConfig.mustrun_layup_window_mask` (default off, backcast-only
double-gated, **zero new free parameters** — ledger 33 entries / 2 residual,
unchanged). Floor clip basis per hour:
`pmax × max(0, availability − layup_share)`, the share from the new loader
`outages.unit_layup_removed_fractions` — the SAME accumulator, unit→plant
routing and model-fleet capacity denominator as the unit-outage overlay, so
outage and lay-up shares are additive by construction. **Availability is not
touched.** A masked window-hour loses its floor exactly as a measured-outage
hour already does under the existing clip; no hour is added or moved.

## 3. The gates, as scored (`_miso173_layup_mask_ab.json`)

| gate | verdict | measurement |
|---|---|---|
| **M-0** control inertness | **PASS** | 12/12 scored sidecars, all years, `max\|diff\| = 0.0` vs the committed keeper — the mask (and the repaired cache-key registrations) are provably byte-inert when off |
| **M-1** volume exactness | **PASS** | every live plant-year's floors-npz ST_GAS volume within `max(0.005 TWh, 3 %)` of the frozen pre-solve ENGINE build, control and arm alike |
| **M-2** volume liveness | **PASS** | every engine-predicted mover DOWN, every engine-flat plant flat; mechanism-total floor volume Δ **−0.944 / −0.564 / −0.762 TWh**, in band all years |
| **M-3** at-floor movement | **sign PASS all years; 2024 magnitude reported out-of-band** | D-2 `st_gas_mustrun_per_plant` forced energy 5.5632 / 5.6112 / 7.1480 → **4.6839 / 5.0515 / 6.3594 TWh** (Δ −0.8793 / −0.5597 / −0.7886 vs bands [−0.9504,−0.3168] / [−0.5417,−0.1806] / [−0.8485,−0.2828]); 2024 lands 0.018 TWh past its band — at-floor-rate drift, the pre-registered NON-KILL interpretation (miso-172 §4's instrument class), reported against interest |
| **M-4a** conduct | **PASS — 2 → 0, ZERO new** | **both** remaining 2023 conduct failures CLEARED |
| **M-4b** the target | **CLEARED** | 1402-2023 FAIL → pass, exactly as predicted pre-solve (0.4 % window-grain zero-share vs the 50 % rider — where miso-172 arm-1, attacking the window's SIZE, missed by 2.2 pp) |
| **M-5** C8 | **PASS, no regression** | all years PASS; 2025 ST_GAS grounded above budget at 32.2 % forced, profile_r 0.981, all binding mechanisms clear D-4 |
| **M-6** record flips | **PASS** | 67 records, **ZERO** PASS → non-PASS flips |
| **M-7** ST_GAS shape | **PASS** | profile_r 0.945 / 0.959 / 0.981 (within 0.002 of control); cv_ratio 1.719 / 1.249 / 1.531 |

## 4. What moved, and the side effect worth naming

**The first MISO bundle with ZERO D-4 conduct failures.** The target row
(1402-2023, `st_gas_mustrun_per_plant`) cleared as predicted. The second
clearance is a **side effect, not a target**: the plant-990
`reliability_floor` row — the regenerated-diagnostics conviction on
**0.0000 TWh across ONE binding hour** that miso-171/172 raised to the owner
as the sharpest instance of the missing materiality floor inside C8's
provenance leg — cleared because the mask removed that single binding hour.
**The underlying rubric question REMAINS OPEN** (re-raised in this session's
close); this bundle simply no longer instantiates it.

Every one of the seven live floored plants moved TOWARD its own meter in
every year it carries windows (window-grain metered zero-share: 1402
0.633→0.004 / 0.356→0.096 / 0.273→0.049; 3459 0.109→0.008 / 0.200→0.017 /
0.168→0.050; none perverse).

## 5. Reported against interest

* **C3a-2025 is unchanged and still FAILS (−11.8 %).** Nothing here is
  claimed against the miso-163 owner ruling or the miso-171 decomposition —
  the masked energy is winter; the miss is summer.
* **M-3's 2024 magnitude missed its ±50 % band by 0.018 TWh** (more at-floor
  removal than the fixed-rate prediction) with M-1/M-2 clean — the same
  instrument limitation that killed miso-172 arm-1's K-2, here pre-registered
  as a non-kill and reported rather than absorbed silently.
* **The committed-vs-regenerated diagnostics exposure is unchanged in kind**
  and disclosed, not created here; every gate compares regen-control to
  regen-arm through the same path at the same HEAD.

## 6. The miso-172 arm-1 re-run (charter item 3): NOT taken, with reasons

The per-year window vintage (`mustrun_online_frac_per_year`, cell `R`) stays
rejected-as-armed. The mask **subsumes the 2023 half of its case** — 1402's
conduct row, the defect that motivated it, is now clear — and its 2024/25
half (window UNDER-sizing) would RAISE forced share against C8's budget while
buying no gate. Its K-2 rejection is annotated as instrument-limited (the
banding, not the mechanism); a future session re-arming it must write a
reconciliation charter against this keeper's mask (rule 19: both mechanisms
move the same floor's window properties) and band on the floor-energy basis.

## 7. Governance and housekeeping

* Rule 22: 2023–2025 only; MISO holds neither `complete` nor `final`; the
  spend freeze is untouched; no marker re-key owed. LOO is vacuous for the
  same argued reason as miso-172 arm 2 (zero free parameters; uniform
  every-plant-toward-its-meter movement across all years).
* Rule 28: base row + cell line in every ISO shard landed in the
  implementation commit; MISO's cell stamped `K` with this evidence; no other
  ISO's verdict touched (rule 25 — other shards enter `U`).
* **Cache-key registration repair** (found here, fixed in the implementation
  commit): miso-172's two fields were never registered drop-at-default
  (nyiso-119 discipline), silently moving the pinned global default key and
  failing nine pin tests at HEAD; both are registered at their merge-time
  defaults, the pin `603c2498bf71d21d` is restored, and M-0 re-proves
  solve-path inertness of all three fields at this HEAD.
* **The miso-172 keeper-audit debt is discharged**: `audit_keepers.py --iso
  MISO` PASS, zero drift, zero repairs (run before this session's promotion;
  re-run against the new keeper at promotion).
* Runs registered: `2026-08-20-miso-173-control`,
  `2026-08-20-miso-173-layup-mask` (retention pruned
  `2026-08-09-miso-148-basis-aware`, the top-15 sweep working as designed).
