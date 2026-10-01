# CAISO Evening CC Commitment Posture — Mechanism Design (2026-07-11)

> **DEAD — DO NOT BUILD (2026-07-11, caiso-77 session,
> `results/calibration/FINDING-caiso77-c1-cluster-firm-selfschedule-2026-07-11.md`
> §1).** The motivating measurement was an artifact:
> `scripts/archive/caiso_belly_commitment_probe.py`'s actual side counted the whole
> CAMPD **CA state** extract (16.6–18.5 TWh/yr of non-CAISO CC — LADWP
> Haynes/Scattergood/Valley, SMUD Cosumnes, TID Walnut, IID El Centro, …), so
> the "+1.9/+1.2/+0.3 GW evening CC gap" this design was written against never
> existed. Same-fleet (probe corrected 2026-07-11), the model CC is
> **over**-committed in both the belly and the evening in every year
> (evening actual−model −0.6/−1.3/−1.4 GW). A floor that ADDS evening CC
> energy pushes the wrong direction in all three years. The §0 re-measures
> recorded below (and in FINDING-caiso76 §1) carry the same contamination.

**Design only — no build, no solve.** The mechanism-design deliverable for the
evening gas-CC commitment gap measured by
`docs/handoffs/caiso-belly-commitment-probe-2026-07.md` (model CC under-runs
the CAMPD evening ramp h18-21 by **+1.9 / +1.2 / +0.3 GW** in 2023/24/25 on the
caiso-65 keeper; the belly is within ~1 GW). Written against rule 17 (window +
driver + forward story before any floor exists) and rule 19 (enumerate and
replace what already floors the class — never stack).

## 0. Ordering constraint — re-measure after caiso-74/75 land

The probe's Δ was measured on the caiso-65 keeper, **before** the hydro
envelope (caiso-72), the shaped firm import base (caiso-73), the measured
battery AS reservation (caiso-74, measured inert) and the 2023 demand-clock
realignment (caiso-75). Each of those moves evening supply or evening load.
The 2023 demand fix in particular moves ~1.4 GW of 2023 ramp-hour load one
hour earlier. **Gate: re-run
`scripts/archive/caiso_belly_commitment_probe.py --run-id <caiso-75 main>` and
re-measure the evening Δ before building.** If the residual evening CC gap
falls under ~0.5 GW in 2024/25, this mechanism is not worth its complexity
(the 2023 gap alone may be the demand clock, not commitment posture).

## 1. The phenomenon and its real-market driver

Reality commits more CC (and CT) into the evening net-load ramp than an
exact-fit energy LP clears, because CAISO's market design commits capacity
against *forecast* need with *unit-commitment inertia*:

- **RUC (Residual Unit Commitment)**: after the IFM, CAISO procures capacity
  up to the CAISO forecast of demand for every hour — RUC commits/positions
  units the energy market alone would leave off, explicitly for the evening
  peak and ramp (Tariff §31.5; BPM Market Operations §6.6).
- **RA must-offer + minimum online commitments**: RA resources must offer;
  local/system commitments (incl. exceptional dispatch and minimum online
  constraints for the largest contingencies) keep synchronized capacity
  through the ramp.
- **UC inertia physics**: a CC committed for the evening peak is online from
  late afternoon (start lead) through its min-run — the posture spans the
  ramp shoulder hours, not just the peak hour.

The forward-native driver of all three is the **daily evening net-load ramp /
peak** (demand − VRE): it exists in every forecast year from the model's own
inputs and responds to changed conditions (more solar → deeper duck → larger
ramp commitment; more storage → flatter net peak → less). This satisfies
rule 17(a) and (c) by construction.

## 2. Window (rule 17(b), D-4 declaration up front)

Binding window: **the evening net-load ramp block of each day** — from the
net-load trough hour + 2 to the net-load peak hour + 2 (empirically h16-22
PT in summer, h17-21 winter; derived per-day from the model's own net-load
series, never a fixed clock window). The driver evidence (CAMPD CC online GW
by hod) shows the posture is a *daily-peak* phenomenon: off-window (overnight,
belly) the mechanism must be inert — a floor binding in the belly would
re-create exactly the unconditional RA-bridge behaviour this design replaces.
`D4_WINDOWS` entry: `caiso_evening_cc_commitment → per-day net-load-ramp
block` with the trough/peak derivation cited.

## 3. Mechanism shape

A **day-resolved CC commitment floor** (min_gen on committed CC tranches, the
existing commitment-scaffolding channel):

1. For each day d, compute the model's own net-load evening peak
   `NLP(d) = max_{t∈evening(d)} (demand − wind − solar)(t)` — model inputs
   only, so it regenerates forward (rule 13).
2. Committed evening CC posture `C(d) = f(NLP(d))`, where `f` is a
   **measured-behaviour mapping** derived once from CAMPD: regress (or bin)
   observed CAISO CC online-GW in the evening block on the observed net-load
   evening peak, per season, 2023-2025 pooled. `f` is a *derive-script
   parameter set* in the rule-24 class (min-stable loads, committed shares):
   frozen against residuals, re-derived only when the CAMPD source updates.
   It is fit to measured COMMITMENT (which units were online), never to the
   price/volume residual (rule 13's line).
3. Apply `C(d)` as a min_gen floor across the day's evening window on the
   RA-fleet CC tranches (pro-rata by available committed-tranche capacity,
   respecting outages), with UC-inertia shoulders: the floor ramps in over
   the 2 h before the block (start lead) and holds through min-run after the
   peak (both from the existing per-class physics parameters, not new
   numbers).

**Zero new free parameters beyond the measured mapping `f`** (whose
identification source is CAMPD online-hours, listed in the DOF ledger with
that provenance).

## 4. Rule-19 reconciliation — what already floors evening CC

Enumerated current CC-floor mechanisms (D-2 attribution):

| mechanism | window today | disposition under this design |
|---|---|---|
| `caiso_ra_mustoffer` P1 bridge (min_gen from P0 run pattern, `caiso_ra_min_load_frac=0.26`) | all committed hours (belly + evening, unconditional) | **REPLACED in the evening block** by the day-resolved posture; the belly keeps the bridge (the probe shows the belly wants *more* committed CC, not less — G-61(b) evidence). Long-term: one unified posture for both, but never both floors on the same hours. |
| `caiso_ra_bridge_startup_aware` (UC-physics gate on which units bridge) | filter on the above | kept — it is the physics gate, not a floor. |
| `ct_netload_drag` | OFF since caiso-69 | stays off; this design must not resurrect it via the CC side door — the CT evening story belongs to the imports/commitment ledger, not to this floor. |

The build therefore modifies the bridge's hour mask, it does not add a second
floor: **in the evening block, the binding floor is
max(bridge floor, C(d) allocation) collapsed into ONE min_gen array** with
D-2 attribution split by contributor, so C8's budget sees a single mechanism.

## 5. Acceptance gates (pre-registered for the eventual probe)

- Evening CC online GW moves toward CAMPD (+Δ target from the §0 re-measure).
- C7 CC/CT diurnal profile_r holds or improves (the caiso-73 C7 PASS must not
  regress — protective).
- C8: CC_REGULAR forced share stays within budget, or clears the grounded
  pass-path (D-4 window + D-1 shape) — the design's window declaration exists
  precisely so D-4 can score it.
- C3a body: evening λ moves toward the measured $13-33 body band
  (the seam-tz FINDING §4.3 target), C3b duration shape improves.
- Zero-forcing ablation twin: the floor is commitment scaffolding and is
  ablated OFF (unlike the capability caps) — the twin quantifies its energy.

## 6. Explicitly out of scope (QUEUED)

- **Bay-Area local topology for the missing 2024/25 C3c tail**: NorCal local
  pockets (Greater Bay LCR ≈ 7.3 GW) don't exist in the split topology; the
  measured LCT boundary data and the scoping pattern are in
  `docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md`. That
  is a topology change (separate session), not a commitment mechanism, and
  it owns the 2024/25 local-tail miss (0/0 h > $200 modeled vs 35/8 actual).
- CT-side evening posture: revisit only after the re-measured displacement
  ledger on the caiso-75 line says what CT gap remains.
