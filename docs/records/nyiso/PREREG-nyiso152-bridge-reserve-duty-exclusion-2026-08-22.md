# PREREG nyiso-152 — bridge reserve-duty membership exclusion (`nyiso_gas_bridge_reserve_duty_exclusions`), composed with the duty split

Session nyiso-152, 2026-08-22. Committed and pushed BEFORE any arm solves.
Evidence base:
`FINDING-nyiso152-phase0-reserve-posture-overturned-2026-08-22.md` (phase-0,
same session) — the owner-chartered RAMP10 phase-0 whose measurement re-typed
the queue item: the recorded RAMP10 seams are provably LP-inert for NYISO, and
Allegany's (7784) offer-insensitive residual is 100 % commitment-bridge floor
(mech 20) plus peak-band spike-hour economics. Holdout freeze ACTIVE: every
year solved, scored or read is 2023–2025 (rule 22); all three years in one
invocation per arm (rule 16).

## 1. Object

The `nyiso_gas_commitment_bridge` floors Allegany — measured e923 pooled CF
0.0173, the sole `reserve_duty_cc_NYISO.csv` cohort plant with no CAMPD
series — at min-load for 1,804 h (2023) / 2,797 h (2024) under the armed duty
split, manufacturing 57.8 / 91.4 GWh of energy at a plant whose own meter
says it essentially never runs: a rule 17 [R-FLOOR-WINDOW] violation. Six of
the seven duty-cohort plants are already bridge-excluded through the CAMPD
lay-up channel (`nyiso_gas_bridge_plant_exclusions`, nyiso-144); Allegany
escapes only because that channel requires a CAMPD gross-load series
(coverage gap, not verdict).

## 2. Mechanism (one new gated field)

`nyiso_gas_bridge_reserve_duty_exclusions: bool = False` — when armed, the
plant codes of the measured reserve-duty CC cohort
(`data.reserve_duty.load_reserve_duty_cc`, the FROZEN nyiso-149 artifact
`reserve_duty_cc_NYISO.csv`, rule 23) are added to the bridge's excluded
membership set and scoped out through the detector's own population gate
(`min_load_frac_by_gen` zeroing) — byte-for-byte the
`nyiso_gas_bridge_plant_exclusions` / miso-113 convention: no new detector
parameter, no class tuple (rule 18 [R-PHYSICS] keeps eligibility on physics;
this is MEMBERSHIP, on a measured duty-role signal). Zero new scalars
(rule 21 [R-DOF]: the entry is a plant-code set, n_scalars 0). Identification
(rules 13/23): duty membership = pooled online-share/CF ≤ 0.1 against the
population gap (the split's own artifact, derived blind to the bridge's floor
pattern — agreement with the D-4/rule-17 evidence is evidence, not fitting).
Net new membership at HEAD: exactly {7784} (the other six are lay-up
excluded). Rule 19 [R-ONE-MECH]: composed with `cc_reserve_duty_split` this
COMPLETES the duty-role mechanism — the split owns the cohort's offer shape,
the exclusion its commitment population; the pair is one phenomenon's one
reconciled mechanism, not a stack (the exclusion REMOVES a floor).

## 3. Arms (2 solves; the committed armHC is the mid-rung)

* **CONTROL** `nyiso152_control` — the keeper recipe
  (`2026-08-22-nyiso-151-identity-hr`), replayed at this session's HEAD.
  `--replay-bundle results/calibration/nyiso152_control_recipe` (byte-copy of
  `nyiso151_armH_recipe`).
* **ARM SE** `nyiso152_armSE` — keeper recipe + `cc_reserve_duty_split` +
  `nyiso_gas_bridge_reserve_duty_exclusions`
  (`nyiso152_armSE_recipe` = `nyiso151_armHC_recipe` + the new flag).
* **Mid-rung (no solve):** the committed `nyiso151_armHC` (≡ registered
  `2026-08-22-nyiso-150-reserve-rearm`) differs from SE by EXACTLY the new
  flag, so SE−armHC isolates the exclusion and SE−control the composed pair.

Solves run per rule 12: control and SE may run concurrently (2 per-plant
invocations max), years sequential within each.

## 4. Gates (all pre-registered; measured by `scripts/probes/_nyiso152_ab_gates.py`)

* **IDENT** — control replay vs the committed `nyiso151_control`:
  max |Δprice| = 0 over every zone-hour of all three years (proves the
  post-151 HEAD — RHO_CLIP floor deletion, docs/registry commits —
  NYISO-keeper-inert). A nonzero IDENT stops the session: re-diagnose before
  any arm is read.
* **K1 exactness** — `run_config.json` scenario diff: SE vs control =
  {`cc_reserve_duty_split`, `nyiso_gas_bridge_reserve_duty_exclusions`}; SE
  vs committed armHC = {`nyiso_gas_bridge_reserve_duty_exclusions`}. Anything
  else = kill.
* **K2 liveness** — the exclusion log line fires every SE year and names
  7784 in the composed excluded set; Allegany's bridge-floored unit-hours
  (floors npz, mech 20) = **0** in every SE year.
* **K3 target (mechanism-scoped)** — the floor piece is removed and nothing
  else moves at Allegany beyond LP re-equilibration:
  (i) SE Allegany floored energy = 0 (2023/2024/2025);
  (ii) SE Allegany total annual energy within **±50 %** of the phase-0
  control-side capture prediction = armHC's above-floor piece: **90.4 GWh
  (2023), 111.8 GWh (2024), 0 (2025)** (the nyiso-144 K2-prediction
  convention: predicted BEFORE the solve from the committed bundle's own
  decomposition);
  (iii) Sterling 50744 / Massena 54592 / Batavia 54593 reproduce their
  armC/armHC collapses (each ≥80 % fall vs control in 2023 and 2024) — the
  split's own effect must survive the composition.
  **REPORTED, NOT GATED:** the nyiso-150/151 ≥80 %-total-fall bar for
  Allegany (predicted 82.0 % / 78.3 % for 2023/2024). That bar belonged to
  the split-as-offer-lever arms and its two rejections STAND as records;
  phase-0 re-typed the residual into a floor piece (this arm's claim) plus a
  peak-band economic piece that the CLOSED offer lane owns (two levers proven
  bit-insensitive, nyiso-151 §1–2). Gating this arm on energy it never
  claimed would judge a membership mechanism by an offer-lane residual
  (rule 1 [R-STRUCT] — a real correction stays in even if a headline number
  it never targeted stays imperfect).
* **K4 legitimacy** — zero NEW D-4 FAILs vs control anywhere in the fleet;
  no material class's forced share rises (K6′); the D-2
  `nyiso_gas_commitment_bridge` attribution does not grow.
* **K5 criteria** — no CRITERIA PASS→FAIL vs control in any year; the
  determination of SE is not worse than the keeper's (CALIBRATED, lone
  ledgered C3c). C3c magnitude reported at whatever it lands.

## 5. Decision tree (pre-committed)

* **IDENT/K1/K2 fail** → stop / fix harness, no adjudication.
* **K3(i,ii,iii) + K4 + K5 all pass** → SE REGISTERS (rule 15, all three
  years, one bundle) and — per the nyiso-146c convention — is **promoted to
  keeper in-session iff** its determination is not worse than the current
  keeper's AND legitimacy strictly improves (the rule-17 floor at a
  meter-dark plant is gone; no new convictions anywhere). Promotion carries
  the full workflow: shard swap, D-5(b) re-key with determination
  re-verification, status/audit, matrix re-stamp. The
  `cc_reserve_duty_split` NYISO cell moves R → K′ (kept-in-composition) with
  both prior rejections preserved verbatim; the new field's cell stamps K.
* **K3 fails on (i) or (ii)** (floor not removed / Allegany lands outside the
  band) → REJECTED-AS-ARMED, both records committed (`_nyiso152_ab_gates.json`
  + this prereg), matrix cell R for the new field, split cell stays R,
  Allegany object returns to the queue re-typed with whatever the failure
  reveals.
* **K3(iii) fails** (composition breaks the split's own collapses) →
  REJECTED-AS-ARMED; the exclusion is adjudicated incompatible with the
  split; both cells stay/return R.
* **K4/K5 fail** → REJECTED-AS-ARMED on legitimacy/criteria regression.

Registration disposition of the control replay: expected bit-identical to
`nyiso151_control` ≡ the keeper — NOT separately registered (the nyiso-149
non-double-registration convention); the IDENT proof is its record.

## 6. DO-NOT-REDO reconciliation (rule 28 duty a)

`cc_reserve_duty_split` NYISO cell is **R** (nyiso-150 armC, nyiso-151 armHC —
both on the Allegany ≥80 % bar). This session re-arms it ONLY in composition,
on NEW EVIDENCE: phase-0's measurement that 39–45 % of the bar's residual was
bridge-floor energy no offer mechanism could ever remove (the very rejections
cited). The two R records stand unrewritten. The RAMP10-seams queue item is
adjudicated off-queue (provably inert for NYISO) by the phase-0 finding — no
solve is spent on it, per the ercot-lane provably-inert class.

## 7. Rule-28(c) matrix duty

The new field registers on the `gas_commitment_bridge` base row's `def` — the
row's own "per-leg sub-scalars registered HERE, not as rows (rule 28(c)
escape hatch)" convention that already carries the other nine
`nyiso_gas_bridge_*` legs — in the SAME push as the code, before any solve.
The adjudication outcome lands on the NYISO shard's `gas_commitment_bridge`
cell record (and the `cc_reserve_duty_split` cell for the composition).

## 8. Reproduction

```
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso152_control_recipe --out-dir results/calibration/nyiso152_control
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso152_armSE_recipe  --out-dir results/calibration/nyiso152_armSE
python3 scripts/probes/_nyiso152_ab_gates.py
```
