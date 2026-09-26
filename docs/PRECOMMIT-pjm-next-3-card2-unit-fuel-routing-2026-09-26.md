# PRECOMMIT — PJM-NEXT-3 card 2: route each steam outage window to its own unit's fuel slice (Montour, Brunner Island)

Session PJM-NEXT-3, 2026-09-26. Keeper `2026-09-25-pjm-next-2-joint` (bundle `results/calibration/pjmnext2_joint_span`,
2019–2025, solved at `d25a3ebb5`). Written and pushed **before any solve**. The arm is one gated field,
`unit_outage_unit_fuel_routing`, zero free parameters, on top of the unchanged keeper recipe.

## 1. The defect (zero LP)

The standard CAMPD deriver tags every window at a facility with **one class per year**. At a plant mid-conversion
whose steam generators burn different fuels in the same year, the fleet carries one LP slice per generator fuel
(keyed `(plant_code, class)`), but every unit's window lands on the one slice the facility tag names. The outage
accumulator divides the unit's MW by that slice's capacity, so that slice is zeroed through every window of
either unit, and the other slice runs fully available.

EIA-860 (the vintage the backcast fleet reads for the solved year, `eia860_vintage_tracks_solve_year`):

| plant | vintage | gen 1 | gen 2 | gen 3 | extract tag, both/all units |
|---|---|---|---|---|---|
| Montour 3149 | 2023 | BIT coal 752 MW | **NG steam** 752 MW | — | COAL |
| Montour 3149 | 2024 | **BIT coal** 752 MW | NG steam 752 MW | — | ST_GAS |
| Brunner Island 3140 | 2019 | **NG steam** 306 MW | **NG steam** 363 MW | RC coal 742 MW | COAL |

PJM-NEXT-2 measured the Montour consequence (PRECOMMIT card 2 §1): 2024 coal slice 4.53 TWh modelled vs 0.42 TWh
actual; 2023 gas slice 3.21 vs 0.28 TWh.

## 2. The arm

`unit_outage_unit_fuel_routing` (default False, `_CACHE_KEY_OPTIONAL_FIELDS`), meaningful only with
`unit_outage_membership_repair` (armed in the keeper). It selects
`data/raw/campd-unit-outages-memberrepair-unitfuel-PJM.csv`
(sha256 `ab6e163c55c72205ecc5c5a8a2a38faf1a1385a0915aaecaaa0d42ef4d4a5692`), built by
`scripts/data/build_outage_unit_fuel_routing.py` from the keeper's `-memberrepair-` extract: the **same 11,534 rows**,
text-identical except **66 `plant_group` re-tags** — a COAL/ST_GAS row moves to its own generator's class only where
that facility's steam generators split across coal and gas `Energy Source 1` in the row's own year's vintage.
Re-tags at HEAD: Montour 2023 unit 2 → ST_GAS (5 rows), Montour 2024 unit 1 → COAL (9 rows), Brunner Island
2018 units 2–3 and 2019 units 1–2 → ST_GAS (52 rows; 2018 is outside the span). No row added, dropped, moved or
resized. The rule is general (no per-plant list); these are the only plants it reaches in PJM.

Admissibility (rules 13/14/19): outage windows are an existing measured physical input; this corrects which slice a
measured unit outage derates. Same overlay, same accumulator — no new availability mechanism. Rule 23: the
committed extracts are untouched (a separate file).

## 3. Zero-LP census (fleet-only rebuild, keeper recipe ± the flag)

Availability capacity-hours, arm − keeper (TWh), `mc_base` byte-identical in every year:

| year | rows moved | plants | COAL_BIT | ST_GAS |
|---|---|---|---|---|
| 2019 | 12 | Brunner Island 3140 only | **+1.622** | **−4.108** |
| 2023 | 11 | Montour 3149 only | +0.384 | **−5.745** |
| 2024 | 11 | Montour 3149 only | **−4.502** | +1.400 |
| 2020, 2021, 2022, 2025 | 0 | — | 0 | 0 (inert by construction: no re-tagged row in these years) |

2023 is asymmetric because unit 1 (coal) was out 339 days, so freeing the coal slice of unit 2's windows returns
little, while the gas slice newly carries unit 2's 334 days. Fleet-only probe: `pjm_da_virtual_bids` off (demand-side,
inert for availability/offers), keeper recipe via `replay_keeper.run_year_kwargs`.

## 4. G-DRIFT (rule 29(b)) — form 4 holds, no control solves

`git diff d25a3ebb5 HEAD` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`data/raw/_validation-source`, `data/raw/reference`, classified hunk by hunk — all INERT for PJM:

- `coal_committed_nested_on_mustrun`, `wefor_residual_short_screened_coal`, `nyiso_ldc_generator_delivered_gas`,
  `nwpp_demand_plant_basis`: new fields, default False, absent from the keeper recipe;
- `apply_nyiso_ldc_generator_delivered_gas`: returns unless the flag is on AND `iso == "NYISO"`;
- `eia930/demand.py` / `envelopes.py`, `nwpp_plant_basis_energy.csv`: NWPP-only branch;
- `outages.short_screened_coal_shares` / `arrays.py` WEFOR relief: reached only under the default-off miso-273 flag;
- this session's own `unit_outage_unit_fuel_routing` plumbing: byte-inert off (a different file is read only when
  armed).

Extended to `origin/main` `2c71404c` (merged during this session): R-ERCOT-5 hour grain (the new branch fires only
for `iso == "ERCOT"`; PJM's `hour_grain` predicate is unchanged), NYISO `reliability_floor_layup_window_mask` and
R-CAISO-3 `caiso_*` interchange fields (default False, absent from the keeper), and `campd_bins._APPLIED_MEASURED_FLAGS`
admitting `eia923_identity` rows — **only `campd_cc_heat_rates_CAISO.csv` carries that flag** (commit `d5d0bcc4`
touches no PJM artifact), so PJM's measured heat rates read exactly as before. All INERT.

The keeper's committed bundle is the control.

## 5. Predictions (stated before the solve)

- **2024:** COAL_BIT falls (the Montour coal slice ran 4.53 TWh vs 0.42 actual): −2 to −4 TWh, the class error
  +0.3 TWh (joint) moves negative but stays inside its band. CC_REGULAR rises by part of the backfill (0 to +2 TWh);
  the −10.07 TWh C1 fail is **not** expected to close (Montour is Central_PA, not the Dominion/EMAAC/SWMAAC deficit).
- **2023:** ST_GAS falls (gas slice 3.21 vs 0.28 actual): −1.5 to −3 TWh.
- **2019:** against interest — COAL_BIT **rises** (+0.5 to +1.5 TWh, the +12.91 miss widens) and ST_GAS falls.
- 2020–2022, 2025: byte-identical to the keeper.
- C2/C3a/C3b/C3c: no direction predicted; no training-span criterion is expected to flip.

A regression on any criterion is reported at full magnitude and is not a reason to drop the arm (rule 1).

## 6. Execution (rules 32/34/36)

One shard per year 2019–2025, each
`replay_keeper.py results/calibration/pjmnext2_joint_span --years <y> --set unit_outage_unit_fuel_routing=true`,
pinned to the full SHA of the commit carrying this doc, full bundle (incl. `dispatch/<y>_P1.parquet`) pushed to
`claude/pjmnext3-c2-<y>` via a `.gitignore` negation and a plain `git add`. Hard stops: pinned SHA;
`scenario_config.unit_outage_unit_fuel_routing` and `unit_outage_membership_repair` both true;
`resolved_inputs.campd_unit_outages.path` ends `campd-unit-outages-memberrepair-unitfuel-PJM.csv` with sha256
`ab6e163c…`. The parent composes (copy of `_pjmnext2_compose_span.py`), scores against the keeper on the same
benchmark, attests (DOF ledger carried, zero entries added), registers `--no-prune`, and asks the promotion question.
