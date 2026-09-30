# PRECOMMIT — NYISO-NEXT-16: re-test `nyiso_iroquois_winter_spread` under the cutset link — 2026-09-30

- **Session:** NYISO-NEXT-16, the orchestrator. This container runs no LP (rule 32 (a)).
- **Phase 0:** `docs/FINDING-nyiso-next16-c3b-2022-phase0-2026-09-30.md`.
- **Owner decision card (this session):** "Re-test, 5 yrs".
- **Queue:** item 1 (C3b 2022). Phase 0 splits it into winter under-pricing (48 % of the squared error) and Upstate_West shoulder over-pricing (41 %). It rejects the CENTRAL EAST distribution-factor cap ex ante (no solve).
- **Rule 28 (re-test of an R cell):**
  - nyiso-150 refused the cell because the mainland priced as one coupled block, with the internal cutset never binding.
  - NEXT-14 removed that premise: the link now binds 8.9–27.2 % of P1 hours.
  - The rule-14 defect is measured in FINDING §3: Upstate_West gas carries the New England winter shape.
- **Control (form 4):**
  - Keeper `2026-09-30-nyisonext15-landing-band-span` (bundle `results/calibration/nyisonext15_span`, 2022–2025).
  - Stamped `2026-09-30-nyisonext15-landing-band-2021` (bundle `results/calibration/nyisonext15_2021`).
- **Arm:** the keeper recipe plus `nyiso_iroquois_winter_spread: true`. Nothing else moves. No code change.

## 1. The mechanism (zero free parameters; existing code)

- **Reference hub (`basis/nyiso.py::nyiso_reconciled_reference_monthly`).** The Iroquois Z2 reference carries the measured SOM annual Iroquois–Transco spread, in the months the measured Algonquin basis puts it. Each month is capped at the measured Algonquin Citygate level, and the shaved excess is water-filled into the other months. The annual spread is preserved exactly.
- **Zone ratios (`nyiso_zonal_gas_ratios_monthly`).** Each zone prices at the reference times its own measured monthly hub ratio:
  - NYC at Transco monthly;
  - Capital_Hudson, Lower_Hudson and Long_Island at the reference;
  - Upstate_West at its SOM Tenn Z4 annual on the Henry Hub within-year shape.
- **Rule 19.** It replaces the flat additive offsets on the same seam and never stacks.
- **Rule 13.** Backcast-only: a forward year has no basis rows.

## 2. G-DRIFT (keeper `git_sha` 4c98e6dd → pin)

- `19e9437e` SPP-104 `spp_ct_lole_efor` (`arrays.py`, `ct_lole_efor.py`, constants, scenarios, `solve_surface_declared`): default off, not in the recipe. **INERT.**
- `b8eade78` R-CAISO-16 (`eia930/demand.py`, `eia930/frames.py`): CAISO's EIA-930 clock. Another ISO's branch. **INERT.**
- `f2547c8b` / `98ead1f3` are the NEXT-15 promotion itself (registry, docs, the forecast-parity row). **INERT.**
- This session adds only `scripts/probes/nyisonext16_phase0.py` and docs. **INERT.**

Form 4 is valid; the keeper's committed bundles are the control.

## 3. Legs (rule 36)

Five year-isolated shards at the pinned `main` SHA:

- 2022–2025: `python3 scripts/replay_keeper.py results/calibration/nyisonext15_span --years <y> --out-dir results/calibration/nyisonext16_<y> --set nyiso_iroquois_winter_spread=true`
- 2021: the same from `results/calibration/nyisonext15_2021`.

## 4. Gates (fixed before any solve)

- **G-1 leg acceptance.** `git rev-parse HEAD` equals the pin. The leg's `scenario_config` equals the keeper's except (i) `nyiso_iroquois_winter_spread: true` and (ii) keys absent from the keeper's config that sit at their dataclass default. The solve log carries `NYISO zonal gas basis (<y>, monthly reconciled)`, so the construction is live rather than fallen through.
- **G-2 the construction is exact.** Recomputed at zero LP from the pinned code: each zone's annual mean delivered-gas input equals its measured SOM annual within $0.005/MMBtu, every year. The LP moves: DJF mean |ΔLMP| vs the keeper is > $1/MWh in at least one zone, every year.
- **G-3 the cutset link stays live.** The `Upstate_West>Capital_Hudson` link sits at its forward bound in ≥ 1 % and ≤ 50 % of P1 hours, every year.
- **G-4 no re-collapse upstate.** Upstate_West P1 hours at ≤ $0 are ≤ 100 in every year (measured 0; keeper 0).
- **G-5.** C6 PASS and C8 PASS, every year.
- **G-6 no infeasibility pressure.** P1 load-slack energy does not exceed the keeper's by more than 1 GWh in any year.
- **G-7 conduct (the nyiso-150 kill).** No D-4 failure row keyed (year, check, floor, plant) appears in the arm's `legitimacy_diagnostics.json` that is absent from the keeper's, in any year.

## 5. Promotion rule (fixed before any solve)

**Promote iff G-1 to G-7 hold in all five years.** This is a structural promotion (rule 1).

The following are **reported, not gating**, in either direction:

- C1, C3a, C3b, C3c and price MAE;
- zonal prices and the zone-month errors;
- the link's binding share, lift and spread;
- the downstate − Upstate_West winter spread against measured;
- nyiso-150's W-K3 target measures.

If any gate fails, the run is registered (rule 15) and not promoted, and the owner is asked.

## 6. Prediction (recorded, not a gate)

- Upstate_West winter prices fall: its Jan 2022 gas moves 9.67 → 3.71 $/MMBtu. Its spring and autumn prices rise slightly (gas +$1.0–1.3).
- Eastern winter prices rise where gas, not oil, is marginal. The oil cap (about $25 in Dec 2022) bounds most of the downstate fleet, so much of the Dec 2022 gap should remain.
- The Upstate_West shoulder overshoot is **not** addressed: it is the CENTRAL EAST object (FINDING §2).
