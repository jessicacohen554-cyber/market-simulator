# FINDING nyiso-152 phase-0 — the "reserve-provision dispatch" re-type is OVERTURNED by measurement; Allegany's mid-load hours are 100 % commitment-bridge floor hours; the hydro RAMP10 seams are PROVABLY LP-INERT for NYISO and are adjudicated off the queue

Session nyiso-152, 2026-08-22. Owner charter (nyiso-151 sitting): before any
RAMP10-seams arm is designed, phase-0 must (a) measure which reserve family
binds in Allegany's mid-load hours, (b) establish whether the hydro
deliverability envelope or a nyca/east 10-min family drives the demand, and
(c) settle whether the hydro RAMP10 seams as recorded are even the right
repair. Probe: `scripts/probes/_nyiso152_phase0.py` → record
`results/calibration/_nyiso152_phase0.json`, measured entirely on the
COMMITTED `nyiso151_armHC` (≡ registered `2026-08-22-nyiso-150-reserve-rearm`
bit-exactly) and `nyiso151_control` (≡ keeper
`2026-08-22-nyiso-151-identity-hr` bit-exactly) bundles — no solve, no holdout
spend (2023–2025 only).

## 1. The three phase-0 answers

**(a) Which reserve family binds in Allegany's mid-load hours? NONE.** Every
family reachable from Upstate_West — `nyca_10min_total`, `nyca_10min_spin`,
`nyca_30min_total` (and `east_10min_total`, whose zone set excludes
Upstate_West anyway) — has a balance-row dual of exactly zero in **all 8,760
hours of 2023 AND 2024** (armHC). The only families that bind at all are the
downstate pockets Allegany cannot supply: `nyc_10min_total` 18/9 h,
`nyc_30min_total` 8/4 h, `seny_30min_total` 2/0 h — and none of those hours
intersects a single Allegany floor hour.

**(b) Hydro deliverability envelope vs a 10-min family driving demand?
NEITHER EXISTS.** The keeper's reserve design is the non-gated `else` branch
of `spec._nyiso_design` (obligation / synchronised / spin-online all off):
`eligible = vstack([full_elig, quick_elig])`, `online_gated = None`. With
`nyiso_hydro_reserve_eligible` armed (it is, in the keeper), hydro is unioned
into BOTH classes and its headroom enters the shared-headroom row at **full
`cap × availability` — there is no ramp10 term, no supply cap, no
deliverability envelope anywhere in the NYISO reserve LP**. Measured:
Upstate_West class-1 (10-min) eligible capacity averages 5.5–5.6 GW and its
headroom **never drops below ~1.5 GW in any hour of any year** (min 1,521 /
1,466 / 1,253 MW in 2023/24/25; ≥ 1,503 MW in every Allegany floor hour) —
upstate 10-minute supply is never scarce, which is why the NYCA families
never bind.

**(c) Are the RAMP10 seams as recorded the right repair? NO — the recorded
repair is provably LP-inert for NYISO.** The recorded seams
(`withholding.py::_ramp10_capability` reconciling measured caps only when
`frac > 0.0`, hydro absent from `RAMP10_FRAC_BY_FUEL`, no NYISO module under
`scripts/lib/ramp_capability/`) feed the ramp10-limited reserve paths — ERCOT
supply caps, PJM/MISO/CAISO pergen deliverable-ramp pools. **The NYISO design
consumes none of them**: `_nyiso_design` returns only
`(families, eligible, storage_eligible, online_gated, online_rho)` — no
`supply_cap`, no pergen columns — and the keeper additionally has
`measured_ramp_capability=False`. Repairing the seams changes no coefficient
of the NYISO keeper LP. The premise recorded in nyiso-151 §3 ("the model's
10-minute reserve supply is missing its real cheapest provider — NY hydro …
because `_ramp10_capability` … zeroed") is **wrong for the keeper
configuration**: hydro's 10-minute eligibility does not route through ramp10
at all — it is already armed, at full headroom, via
`nyiso_hydro_reserve_eligible`.

## 2. The nyiso-151 §3 re-type is overturned — structurally and empirically

The §3 claim was: Allegany's offer-insensitive residual is "reserve-provision
dispatch — the co-opt values its quick-start headroom, and its energy is a
by-product." Three independent refutations:

1. **Structural (design):** in the non-gated design the shared-headroom row is
   `Σ P + R[c,z] ≤ Σ cap` — **idle capacity backs reserve; online output only
   consumes headroom**. Reserve demand can never hold a unit on; the LP would
   always rather leave an eligible unit off (more headroom, no energy cost).
2. **Structural (eligibility):** `QUICK_START_FUEL_TYPES = {gas_ct, oil}` —
   a gas CC is not class-1 eligible at all. Allegany cannot supply one MW of
   10-minute reserve in the model. ("~30+ MW of 10-minute headroom" in §3 was
   never a thing the LP could see.)
3. **Empirical:** `floors/<year>_P1.npz` shows Allegany's mid-load hours ARE
   the bridge floor: **every one of its 1,804 (2023) / 2,797 (2024) floored
   hours carries mechanism code 20 = `MECH_NYISO_GAS_COMMITMENT_BRIDGE`, at
   min_gen 30.28–33.81 MW (= the measured CC 0.523 min-load × 64.7 MW ×
   availability), and dispatch rides the floor exactly (|mw − min_gen| ≤ 0.05
   MW) in 100 % of them**. All reserve-family duals are zero in every one of
   those hours. What §3 read as reserve posture is commitment-bridge
   scaffolding.

The bit-identity §3 tried to explain is explained by the floor: floor-forced
energy is offer-insensitive by construction, and the above-floor remainder
(1,720 h / 90.4 GWh in 2023, 2,252 h / 111.8 GWh in 2024) clears deep in
merit during spike hours where a ±$3.4/MWh peak-band shift crosses no vertex.

## 3. The re-typed object: a membership-channel coverage gap on the bridge

Allegany's armHC decomposition (2023/2024; 2025 it does not run at all in
either bundle — 0 h, 0 GWh):

| piece | 2023 | 2024 | driver |
|---|---|---|---|
| floor-riding (mech 20) | 1,804 h / 57.8 GWh | 2,797 h / 91.4 GWh | bridge gap-glue + 21 h class min-run extension of spike runs |
| above-floor economic | 1,720 h / 90.4 GWh | 2,252 h / 111.8 GWh | peak-band offer clears in spike hours |
| **total** | **3,524 h / 148.2 GWh** | **5,049 h / 203.2 GWh** | vs measured ≈ 10–16 GWh/yr (e923 pooled CF 0.0173) |

The floor piece is a **rule 17 [R-FLOOR-WINDOW] violation on its face**: the
bridge holds a plant at min-load 1,800–2,800 h/yr whose own measured record
(`reserve_duty_cc_NYISO.csv`, e923 pooled CF **0.0173** ≈ 152 equivalent
full-load hours) says it essentially never runs. The mechanism is the same
one nyiso-144 already corrected for the laid-up fleet — a plant that is not
in the day-ahead commitment population must not be bridged — and the reason
Allegany escaped that correction is a **coverage gap, not a verdict**: the
lay-up criterion (`campd_bridge_layup_exclusions_NYISO.csv`) requires a CAMPD
gross-load series, and Allegany is CEMS-invisible (its duty basis is
`e923_pooled_cf`; it appears in NEITHER `campd_bridge_layup_exclusions_NYISO`
NOR `campd_perplant_min_run_NYISO`). Six of the seven measured reserve-duty
plants (Carthage, Syracuse, Sterling, Rensselaer, Massena, Batavia) are
ALREADY bridge-excluded through the lay-up channel; **Allegany is the sole
duty-cohort plant the bridge can still floor, purely because the only
membership channel is CAMPD-based.**

The repair this evidence specifies (pre-registered separately,
`PREREG-nyiso152-bridge-reserve-duty-exclusion-2026-08-22.md`): extend the
bridge's membership correction to the measured reserve-duty cohort —
`nyiso_gas_bridge_reserve_duty_exclusions`, a gated default-off field
consuming the FROZEN `reserve_duty_cc_NYISO.csv` through the detector's own
population gate (`min_load_frac_by_gen` zeroing), exactly the
`nyiso_gas_bridge_plant_exclusions` / miso-113 convention. Net new membership
at HEAD: exactly one plant, 7784. Composed with `cc_reserve_duty_split` (the
offer half of the same duty-role phenomenon) it completes the duty-role
mechanism: the split owns the cohort's offer shape, the exclusion its
commitment population — one phenomenon, one reconciled mechanism pair
(rule 19 [R-ONE-MECH]).

## 4. Queue adjudications carried by this finding

* **"Hydro RAMP10 seams" (the nyiso-150 assessment §4 item 5 / nyiso-151 §3
  chain): ADJUDICATED OFF THE QUEUE — provably inert for NYISO** (§1c). No
  solve is spent on a mechanism with no coefficient in the target ISO's LP
  (the ercot-lane "provably inert" adjudication class). The
  `_ramp10_capability` `frac > 0.0` seam remains a real cross-ISO code note
  for the lanes whose designs DO consume ramp10 (ERCOT/PJM/MISO/CAISO);
  logged for those lanes in `docs/calibration-log/governance.md` — rule 25
  keeps the verdict per-ISO, and hydro RAMP10_FRAC entries are theirs to
  derive.
* **The AS-certification admissibility question the RAMP10 item carried**
  (whether EIA-860 Sch. 3.1 10-minute flags / NYISO reserve certification may
  gate hydro's reserve supply) **DISSOLVES for NYISO**: there is no ramp10
  gate for a certification input to feed, and hydro's eligibility union is
  already armed and keeper-adjudicated. Nothing is left for the owner to
  rule on in this ISO; withdrawn from the owner-court list.
* **The winter downstate premium / locational identification intake items are
  untouched** (owner-court, nyiso-150 assessment §5) — this finding neither
  spends nor advances them.

## 5. Reproduction

```
python3 scripts/probes/_nyiso152_phase0.py
# reads results/calibration/nyiso151_{armHC,control}/{floors,hourly}/ only
```

Structural citations at HEAD: `src/market_sim/model/reserves/spec.py`
(`_nyiso_design` else-branch, `QUICK_START_FUEL_TYPES`,
`nyiso_hydro_reserve_eligible` union), `model/lp/reserve_rows.py`
(`_build_reserve_rows` shared-headroom form),
`src/market_sim/data/floor_mechanisms.py` (`MECH_NYISO_GAS_COMMITMENT_BRIDGE
= 20`), `pipeline/commitment.py::_nyiso_gas_bridge_floor` (population gate,
lay-up exclusion precedent), `data/raw/_processed-legacy/`
(`reserve_duty_cc_NYISO.csv`, `campd_bridge_layup_exclusions_NYISO.csv`).
