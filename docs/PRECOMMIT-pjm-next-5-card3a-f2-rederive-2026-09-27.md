# PRECOMMIT — PJM-NEXT-5 card 3(a): the F2 full outage-extract re-derive (2026-09-27)

Keeper `2026-09-26-pjm-next-4-midcurve2019` (bundle `results/calibration/pjmnext4_c1_span`, solved at `7394a279`).
Owner ruling 2026-09-27: **F2 full re-derive YES**, into a companion, never an in-place overwrite. Written and pushed
**before any solve**. One new flag, `unit_outage_full_rederive` (default off), and two new data files. No offer is
touched and no `offer_curve_by_group` multiplier moves.

## 1. What the re-derive found before it could be installed (zero LP)

The HEAD deriver (`derive_campd_unit_outages.py --iso PJM --years 2019..2025 --membership-vintage-union`,
COAL-SUB fix on main) reproduces the handoff's 2019 drift: window capacity-hours CC_REGULAR 74.3 → 91.7, ST_GAS
43.2 → 12.4, coal 198.6 → 187.3 TWh against the keeper's extract. Attributed by plant, it has three parts.

1. **A deriver defect, fixed here (rule 23, a deriver change).** The `ST_GAS_PEAKER_PLANTS` skip was
   **plant-wide**, but the registry is defined on a plant's **ST_GAS slice** (pjm-d4-2's qualifying test).
   - The plant-wide skip deleted Montour's pre-conversion coal windows (2019: 13.4 TWh) and the coal units at
     Yorktown and Chalk Point.
   - Fix: `_is_listed_peaker_steam(plant, group)` skips a unit only when its own resolved group is `ST_GAS`. It is
     applied per unit, and at the two plant-level fallbacks.
   - Every ERCOT and CAISO member is a gas-steam-only plant, so it is unaffected by construction. Test:
     `tests/curation/test_derive_campd_unit_outages_peaker_scope.py`.
   - After the fix, coal 2019 is 203.2 TWh.
2. **The listed gas-steam peakers lose their windows** (Martins Creek, Chalk Point, Edge Moor, Joliet 29, Yorktown
   steam, Montour's gas unit from 2024).
   - This is pjm-d4-2's own ruling ("NO outage overlay … they dispatch purely economically").
   - The committed extract predates it, and the loader does not re-filter.
   - Consistent, not new.
3. **The committed extract is year-inconsistent.**
   - Bergen, Hay Road, Brunot Island, Hunterstown and Ironwood carry 2023+ windows that the HEAD deriver reproduces
     **exactly** (Bergen 70/69/54 rows), and **no 2019–2022 windows**.
   - The re-derive applies one construction to every year (rule 14).

## 2. The arm (one field, zero DOF)

`unit_outage_full_rederive` (with the keeper's `unit_outage_membership_repair` and `unit_outage_unit_fuel_routing`)
selects two files.

- **Standard:** `data/raw/campd-unit-outages-rederive-unitfuel-PJM.csv`
  (sha256 `a77386d8facb25714edaa825b47e8f30f438b843b736d8633696f894e707ee6a`, 13,069 rows).
  - The HEAD re-derive supplies the rows starting in 2019–2025.
  - Rows starting outside the span are carried verbatim from `-memberrepair-`, because 2018 raw CAMPD is not in the
    repo.
  - Then `build_outage_unit_fuel_routing.build_companion` runs (237 rows re-tagged: Brunner Island, Montour, Chalk
    Point and five others).
- **Short-coal:** `data/raw/campd-unit-outages-short-rederive-PJM.csv`
  (sha256 `484fe8609b8785d52f984f07e30ab53d2f300dcab1055033ee8d088d10d4cb39`, 940 rows). It is the same construction
  with `--short-windows`.
- **Unchanged:** the short-gas extract. It was already re-derived in F2 (2019 +246).

Provenance sidecars: `*.meta.json` next to each file. It is a separate file and never an overwrite: every committed
extract is byte-unchanged (rule 23). Rule 19: the same overlay and the same accumulator read a different file of the
same family.

## 3. Zero-LP census (fleet-only rebuild, keeper recipe ± the flag)

`scripts/probes/pjm_next5_card3a_f2_census.py` → `results/calibration/_pjm_next5_card3a_f2_census.json`. Offers
(`mc_base`) are **byte-identical** in every year.

Δ available capacity-hours, TWh (arm − keeper):

| year | rows | CC_REGULAR | CC_CHP | COAL_BIT | ST_GAS | Δ min_gen |
|---|---|---|---|---|---|---|
| 2019 | 249 | −16.06 | −1.13 | +0.06 | +19.01 | −2.75 |
| 2020 | 184 | −19.11 | −0.74 | 0.00 | +20.88 | −2.11 |
| 2021 | 212 | −17.36 | −1.02 | −2.15 | +21.38 | −2.57 |
| 2022 | 173 | −13.21 | −1.34 | −0.05 | +23.61 | −1.86 |
| 2023 | 175 | −7.24 | −1.39 | −14.06 | +21.14 | −2.23 |
| 2024 | 175 | −4.45 | −0.76 | −1.30 | +22.17 | −0.94 |
| 2025 | 147 | −6.05 | −0.83 | −2.64 | +13.07 | −1.29 |

- **Largest movers.** CC loses Bergen, Hay Road, Brunot Island, Hunterstown, Ironwood and Gilbert. ST_GAS gains
  Martins Creek (+11.6 to +12.8), Chalk Point, Edge Moor and Joliet 29. Coal 2023 loses Clover (−6.7) and Rockport
  (−4.7), which are new measured windows.
- **Removed windows are dead periods by construction.** The event-based rule is broken by any hour above
  `ST_GAS_CF_PEAK`. So the energy effect is bounded by what the keeper dispatched in those windows, and it is far
  smaller than the capacity-hours.

## 4. Predictions (stated before the solve)

- **CC_REGULAR falls in every year, most in 2019–2022, by 0.5–4 TWh** (against interest):
  - 2019: −8.54 FAIL widens.
  - 2024 (training): −9.33 FAIL widens by 0–1.5 TWh.
- **ST_GAS:** small net change (±1 TWh). There is more availability on expensive peakers, but min_gen is lower.
- **COAL_BIT 2023 falls 0.5–3 TWh** (Clover/Rockport windows). Other years move by < 1 TWh.
- **C3a:** 0 to +1.5 pts in 2019–2022 (less cheap CC).
- **Determination:** no training-span criterion flips. PJM stays NOT-YET on C1 CC_REGULAR 2024.

Why this is solved although predicted neutral-to-worse: rule 14. It replaces a year-inconsistent extract with one
construction, and every committed deriver fix, on a measured input. The owner ruled it YES. Rule 1: the residual
does not select the input.

## 5. G-DRIFT (rule 29(b)): form 4 holds, no control solves

I classified `git diff 7394a279 HEAD` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`data/raw/_validation-source` and `data/raw/reference` (14 files). Every committed hunk is **INERT** for the PJM
backcast:

- **Other ISOs:**
  - SOCO 2019–2022 gas basis rows (`GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR["SOCO"]`);
  - NWPP Path 76 (`apply_nwpp_path76_link` returns the same object unless iso == NWPP and the flag is on);
  - NEISO winter fuel-security roster (flag off);
  - NYISO `_mg` selector in `fleet_to_bins` (guard armed only in NYISO; PJM `_mg` is False);
  - ERCOT per-unit event cap (ERCOT branch).
- **Default-off flags absent from the keeper recipe:** SPP-86 `unit_outage_coal_extract_basis_share`, and
  `forecast_parity_registry` (tooling).

This session's own changes are also INERT with the flag off: a new default-off field, and resolvers that fall
through byte-identically. The keeper's committed bundle is the control.

## 6. Execution (rules 32/34/36)

- **Shards:** one per year 2019–2025, pinned to the full SHA of the commit carrying this doc. Each runs
  `replay_keeper.py results/calibration/pjmnext4_c1_span --years <y> --out-dir results/calibration/pjmnext5_f2_<y>
  --set unit_outage_full_rederive=true`.
- **Hard stops:**
  - `git rev-parse HEAD` equals the pin.
  - The two companion sha256 values match §2.
  - The leg's `scenario_config` shows `unit_outage_full_rederive`, `unit_outage_membership_repair` and
    `unit_outage_unit_fuel_routing` all true.
- **Push:** the full bundle (including `dispatch/<y>_P1.parquet`) goes to `claude/pjmnext5-f2-<y>` via a
  `.gitignore` negation and a plain `git add`.
- **Parent:**
  - compose, rebuild the benchmark, and score against the keeper on the same benchmark;
  - attest: DOF ledger carried, zero entries added, `authorized_price_tuning.used = false`, config delta
    `unit_outage_full_rederive: False -> True`;
  - register `--no-prune`, update the matrix, and ask the promotion question.
