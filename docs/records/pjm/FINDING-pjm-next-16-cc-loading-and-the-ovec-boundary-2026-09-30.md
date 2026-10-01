# FINDING — PJM-NEXT-16: the CC loading error is too FLAT, and the 2019/2020 LP fleet is missing OVEC (zero LP)

**Keeper** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`), unchanged by this finding.

**Probes** (zero LP):
- `scripts/probes/_pjmnext16_cc_loading.py` → `results/calibration/_pjmnext16_cc_loading.json`: CC loading term by hour class and zone, plus the hourly system ledger.
- `scripts/probes/_pjmnext16_fleet_boundary.py` → `results/calibration/_pjmnext16_fleet_boundary.json`: the energy identity and the LP-fleet vs C1-benchmark boundary.
- `scripts/probes/_pjmnext16_fleet_delta.py`: a `fleet_only` rebuild delta against the keeper, with `--set` routed as `replay_keeper` routes it.

## Card 1 — what pushes CC loading up in 2019/2020/2022/2023

**Method.** For every bench CC_REGULAR plant-hour the model−actual gap is split exactly into three parts:
- `LOAD`: both on, model − actual;
- `ON`: model on, actual off;
- `OFF`: actual on only.

Model is the payload `m`; actual is CAMPD rescaled to EIA-923. Hour classes are the actual PJM demand decile and day (HE 08–23) vs night.

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| C1 CC status | FAIL | FAIL | pass | FAIL | FAIL | pass | pass |
| LOAD, night | **+5.6** | **+6.0** | +1.4 | **+4.3** | **+4.3** | +0.1 | −1.7 |
| LOAD, day | +2.4 | +3.0 | **−2.9** | +3.0 | +0.2 | **−3.8** | **−6.1** |
| LOAD, lowest demand decile | +2.5 | +2.2 | +0.7 | +1.7 | +2.6 | +0.3 | +0.8 |
| ON (extra on-hours) | +8.5 | +10.2 | +10.1 | +10.4 | +9.8 | +7.8 | +6.8 |
| export gap (model − EIA-930) | −12.4 | −13.5 | −13.3 | −9.5 | −11.9 | −11.5 | +5.0* |

\* 2025 EIA-930 total interchange is defective (NEXT-6); the tie meter gives −9.9.

**1. The loading error is a shape error: too flat.**
- Model CCs are over-loaded at night and in low-load hours in every fail year.
- They are under-loaded at daytime peaks in the pass years.
- Online capacity matches CAMPD within ~1 GW in every decile. Loading-when-on at low load is 0.69–0.72 (model) vs 0.65–0.68 (actual) in the fail years.
- The **year signal is the night term**; day and night move together.

**2. Exports are not the driver.** Under-export is −9.5 to −13.5 TWh in every year, pass and fail alike. Two-thirds of it falls in daytime hours.

**3. Zone.** No single zone carries it. The largest LOAD contributors (TWh):

| zone | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| EMAAC | +8.6 | +3.8 | +2.9 | +2.3 | +6.3 | −1.1 | −5.7 |
| Central_PA | +5.8 | +6.0 | +2.3 | +5.4 | +4.3 | +3.8 | +1.4 |
| Dominion | −5.9 | −4.3 | −5.2 | −2.1 | −9.2 | −3.7 | −1.6 |

**4. Coal vs CC econ bid** (cap-weighted P1 bid, $/MWh, `fleet_only` rebuild):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| COAL_BIT econ | 25.0 | 23.0 | 32.8 | 61.7 | 35.6 | 35.9 | 38.9 |
| CC_REGULAR econ | 23.8 | 20.5 | 35.6 | 58.9 | 26.2 | 26.9 | 40.1 |

- In 2019, 2020 and 2022 the two ladders are within $3, so the split of any system over-run between coal and CC is knife-edge.
- The hour-level LOAD term anti-correlates with Δcoal in every year (r = −0.12 to −0.38).

## Card 1b — the system over-run, and a fleet-boundary defect it exposed

**The energy identity closes exactly on the current keeper.** Model generation − `classFull` = model export shortfall + model losses + `U_a`, where `U_a` = EIA-930 demand + tie export − `classFull`.

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| model gen − classFull | +12.8 | +8.3 | +9.1 | +16.2 | +6.7 | −0.1 | +7.4 |
| export shortfall | −12.6 | −13.6 | −13.2 | −9.6 | −11.9 | −11.8 | −9.9 |
| model losses | +3.7 | +3.5 | +4.0 | +4.2 | +3.6 | +4.3 | +5.0 |
| **U_a** | **21.8** | **19.2** | 18.2 | **21.8** | 15.1 | 7.5 | 12.3 |

**The fossil plants the C1 benchmark counts but the LP fleet does not dispatch** (EIA-923 net generation; benchmark membership = `_iso_plant_ids(..., vintage_union=True)`, the keeper's own setting):

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| total | **15.04** | **12.84** | 3.88 | **6.28** | 3.73 | 3.95 | 4.56 |
| of which OVEC (Clifty Creek 983 + Kyger Creek 2876) | **11.24** | **9.03** | 0 | 0 | 0 | 0 | 0 |
| of which Morgantown 1573 + Waukegan 883 | 0 | 0 | 0 | 2.48 | 0 | 0 | 0 |
| `classFull` COAL_BIT − Σ per-plant bench | +10.8 | +8.8 | −1.2 | +2.2 | +0.2 | +0.3 | +2.0 |

The flat ~3.7–4.6 TWh/yr is small industrial and cogeneration units (Bay Shore, Mon Valley Works, …) and does not vary by year.

**OVEC is a fleet-boundary defect.**
- EIA-860 vintages 2018–2020 code both plants BA `OVEC`; vintages 2021+ code them `PJM`.
- `BA_CODE_TO_ISO` has no `OVEC`, so `process_eia860.py` dropped them from the 2019/2020 generator tables.
- The benchmark's eGRID zone lookup still carries them, and the C1 actual counts their 11.24 / 9.03 TWh.
- So in 2019/2020 the model's other units must serve OVEC's energy.
- OVEC is inside PJM's balancing authority in every hour of the corpus:
  - PJM's EIA-930 interchange file has no `OVEC` leg from 2019-01-01;
  - EIA-930 BALANCE carries no `OVEC` BA in 2019–2021;
  - PJM's tie meter lists no OVEC tie in any year.
- pjm-h10 §1.1 had already noted OVEC inside the *benchmark* footprint; nobody had checked the LP fleet.

**Morgantown/Waukegan (2022)** are partial-plant exits, handled by the gated `partial_plant_exit_carry` (miso-190, PJM cell U).
- Under that flag the admitted plants' real missing generation is small: model − actual on those plants is −2.2 / −0.7 / −0.2 / −1.6 / 0 / 0 / +1.0 TWh.
- But it adds 1–10 TWh/yr of available capacity.
- Not chartered this session.

**A second seam defect found while building the fix.**
- The outage apportionment's capacity maps (`outages.py` `_iso_plant_capacity_cached` / `_iso_plant_unit_capacity_cached`) load the fleet **without a year**, so they admit no `ISO_BA_JOINS` BA.
- A joining BA's plants would therefore dispatch with none of their CAMPD outage windows: OVEC 2019 would run at 0.96 availability instead of its measured 0.2–0.96 monthly profile.
- Fixed alongside (`_joining_ba_generators`).
- Scope:
  - The fix sits only in the `mid_vintage_exit_carry` branch, which SOCO's keeper does not arm, and it selects nothing where no vintage plant carries a joining code.
  - Measured on the rebuilt fleet: 2021 and 2023 are identical to the keeper (float32 storage noise ≤ 6e-5).
  - In 2019, 262 non-OVEC units move. They are downstream fleet-level constructions responding to OVEC's membership, and their mechanisms are **not traced here**:
    - 98 AEP-Ohio coal units (mc);
    - three oil units (+$16–18/MWh mc);
    - hydro unit availability profiles.
  - They are part of arm A as built, and they are reported, not hidden.

**Static zero-LP prediction for admitting OVEC** (the keeper's own cross-hour displacement shares: CC 0.35, coal 0.38–0.41, CT 0.18; supply slope ≈ $0.2/MWh per GW):
- CC 2019 falls ~4 TWh and passes.
- COAL_BIT 2019 rises to ~+18, and 2020 to ~+10.
- C3a moves about −1 pt.

**What that reveals.** The model's own coal plants over-run their own actuals by +21 / +13 / +17 TWh in 2019 / 2020 / 2021 alike. The 2020 COAL_BIT "pass" was the missing 9 TWh of OVEC.

## Verdict

| object | status | next |
|---|---|---|
| CC loading term | **OPEN, located.** A shape error (night/low-load over-loading), with the year signal in the night term. The coal/CC ladders are within $3 in 2019/2020/2022. | Solved as arm B (owner ruling): a P0-pattern min-load bridge replacing `cc_mustrun_per_plant`. |
| OVEC 2019/2020 | **Defect, fix built** (`ISO_BA_JOINS["PJM"] = {"OVEC": (2019, 1)}`, vintages rescoped, outage seam fixed). | Arm A (owner ruling "Build + solve"). |
| COAL_BIT over-run 2019–2021, 2025 | **OPEN.** It is flat across 2019–2021 once OVEC is counted. | After arm A, the coal ladder vs replacement cost (NEXT-13 addendum) and the night coal/CC ordering. |
| Partial-plant exits (2022) | **OPEN, small** (≤ 2.5 TWh of real generation). | `partial_plant_exit_carry` screen, not chartered. |
| Flat ~4 TWh/yr of small industrial/CHP units outside the fleet | **OPEN, not year-discriminating.** | Fleet-coverage lane. |

Nothing here is called a model-class limit.
