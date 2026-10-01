# ERCOT commitment-thinness lane — design + build note (`ercot_commitment_posture`)

**Date:** 2026-07-18. **Lane:** ERCOT COMMITMENT-THINNESS (the last structural lever for the
2023 scarcity gap after the DAM-offer-surface and availability lanes were exhausted). **Role:**
Opus/Fable (rule 27 — writes `dispatch.py`, `scenarios.py`, `run_*.py`). **Status:** BUILT,
probe-tested — see the calibration-log entry / dashboard A/B for the verdict.

## Why this lane (established this session, all throwaway probes, ercot80 keeper unchanged)

The 2023 >$200 tail is **offer-driven**, not reserve-scarcity-driven (146/181 tail hours had
measured ORDC adder <$50; on the 124 missed hours model energy λ $58 vs actual system λ $527).
The DAM-offer-basis lane is exhausted on the corrected (post-ERCOT-70-phantom-fix) fleet:

- **Flat CT offer surface** rebuilds the tail (132/181) but **over-withholds** → 72 false
  positives. Refuted.
- **Midcurve belt** (`ercot_offer_surface_midcurve_conditional`) engages but the LP **substitutes
  around it** into cheaper unfloored CC → no lift. Refuted.

Both poles fail for the SAME reason: **the LP has cheap unfloored CC to route into.** The
hypothesis for this lane: the model's perfect P1 commitment keeps too much cheap CC online, so it
serves load with cheap CC where reality ran expensive CT peakers (ERCOT-70 measured: real CT
2.2–2.8 GW vs model 1.0–1.8 GW). Add the commitment friction P1 lacks → thin the effective online
cheap CC → force the CT peakers on → price climbs, and the offer surface stops being routed-around
(no cheap alternative to substitute into). Commitment-thinness **composes** with the offer surface.

## Architecture finding (resolved with owner, 2026-07-18)

The pooled-linear commitment-posture lever live for MISO/CAISO/PJM (`*_commitment_posture`,
design note `docs/multi-iso/miso-scarcity-posture-design-2026-07.md` §A) is **hard-coupled to a
per-generator (pergen) reserve pool structure**: the posture `U[p,t]` columns re-anchor the
pergen reserve pools (`ΣP + R ≤ U`, `R ≤ ρ·U`), and `dispatch.build_constraints` hard-errors if
`reserve_posture_pools` is supplied without `reserve_pergen_gen_idx` (dispatch.py "posture pools:
pergen-only").

**ERCOT has no pergen substrate.** Every ERCOT keeper (incl. ercot80) runs
`ercot_multiproduct_as_coopt` — a *fleet-wide* eligible-mask ORDC co-opt
(`eligible.reshape(1,-1)`), not (zone×class) pergen pools. So "port the flag verbatim" is not
achievable: there is nothing for the U-columns to attach to.

Two options were weighed:

- **(A) Give ERCOT a pergen reserve first**, then attach the posture verbatim. REJECTED: reprices
  ERCOT reserve from fleet-wide ORDC → per-gen opportunity cost — a *second* entangled mechanism
  change that makes the posture A/B uninterpretable and conflicts with rule 19.
- **(B) Standalone energy-only posture** (CHOSEN, owner-approved): the ERCOT hypothesis is
  energy-side (thin online cheap CC → force CT peakers on), which needs only the U + energy
  headroom + min-load + startup rows — **not** the reserve coupling. ERCOT keeps its fleet-wide
  multi-product ORDC reserve untouched. Clean single mechanism (rule 19).

## Mechanism (`ercot_commitment_posture`, GATED default-off, ERCOT-only)

Standalone posture columns/rows in `dispatch.py`, decoupled from any reserve spec. Per
(zone × gas-class) pool `p` over the **merchant gas fleet**, a continuous online-capacity variable
`U[p,t] ∈ [0, Σ pmax·availability]` with:

1. **Energy headroom** `Σ_{members} P[g,t] − U[p,t] ≤ 0` — a pool cannot dispatch more than the
   capacity it keeps online.
2. **Min-load coupling** `Σ_{members} P[g,t] − mlf_p·U[p,t] ≥ 0` — being online costs min-load
   energy at the committed band; binds only capacity the LP itself keeps online (NOT a floor —
   forces no exogenous energy; window deliberately none, design note §A).
3. **Startup charge** `SU[p,t] ≥ U[p,t] − U[p,t−1]` (cyclic), cost `startup_$/MW × SU` — re-timing
   CC energy now pays a real start instead of the P1 zero-commitment-cost relief. Makes committing
   CC for a short peak expensive → the LP prefers fast-start CT for peaks → CC thins.

The reserve ramp gate `R ≤ ρ·U` (design note §A point 4) is **omitted** — that is the pergen-only
reserve-coupling half; ERCOT's ORDC scarcity is already fleet-wide. Min-run/min-down smoothing on
U stays **deferred** (as in MISO/CAISO/PJM — the startup charge carries the cycling economics).

**Eligibility (rule 18, physics-gated — never class tuples):** candidate members = reserve-eligible
`gas_cc` + `gas_ct` thermal units. The capacity-weighted fast-start gate (min-down ≤ 2 h AND
startup < $30/MW) **exempts `gas_ct`** (min-down 1 h — a fast-start CT is never economically
bridged), so only `gas_cc` pools carry U columns. `coal` and `gas_st` are excluded from the
candidate set by **rule 19** (their committed state is already owned by other D-2 mechanisms — coal
take-or-pay/must-run, `gas_st` netload drag — documented in the reserve_config helper).

**Parameters — all measured/published, zero fitted (rules 5/13/23):**
- `startup_$/MW`, `min_down_h` per member: NREL/SR-5500-55433 class tables
  (`COMMITMENT_PARAMS_BY_FUEL`), capacity-weighted per pool — identical to `_posture_pool_params`.
- `mlf` per pool: the **measured** committed-CC LSL/HSL capacity-weighted p50 from the 60-Day DAM
  disclosure (ERCOT-62 derive, `derive_ercot_commitment_loading_state.py` corpus; CC 0.574 — the
  same frozen value the `ercot_gas_commitment_bridge` uses), exposed as
  `ercot_commitment_posture_min_load_frac` (frozen rule 23, NOT swept to move the residual).

**Rule-19 non-overlap:** the default-off `ercot_gas_commitment_bridge` is a min-gen floor that
*thickens* CC (holds it on across idle gaps); the posture is a friction that lets the LP commit
*less* CC. Opposite directions, different phenomena. The composed test runs posture + the peak/
midcurve offer surface with the bridge OFF, so no two mechanisms price the same rows.

## Guards carried into the verdict

- **§6.1 promotion gate:** judge on 2024/2025 (current-design years). A 2023-only win that hurts
  2024/2025 = fitting the retired pre-reform-ECRS transient = REJECT.
- **C8 forced-energy budget (rule 19):** the min-load coupling adds min-gen-like floors — watch
  D-2/D-4 attribution and the peaker <15% / class <30% forced-share caps.
- **LOYO within 2023–2025 (rule 22)** before any promotion; keeper spans all three years (rule 16).
- **mlf is measured, frozen** — never swept.

## Risk

The lever may fail: the energy-only posture (no reserve pressure pinning U up) can leave the
min-load coupling slack (U tracks ΣP), so the dominant effect is the startup re-timing charge. If
that doesn't shift CC→CT the right way, or hits the forced-share budget, register the full-span A/B
either way (rule 15) and recommend ERCOT is at representation limit — accept 2023, weight 2024/2025
(frontier declaration is owner-only, FLAG-NEVER-ACT).
