# FINDING — miso-279 phase 0: the ST_GAS no-row population is small, real, and outside the tranche window

```
LANE    : miso-279 (MISO lever queue §5.4; handoff candidate A, owner pick 2026-09-27)
KEEPER  : 2026-09-27-miso-278-fuelsplit (results/calibration/miso278_span, 2019-2025) — unchanged
LP      : none (zero-LP: CAMPD census + fleet-only rebuilds)
PROBES  : scripts/probes/_miso279_stgas_coverage_census.py  (CAMPD gas-steam energy vs artifact rows vs keeper)
          scripts/probes/_miso279_stcov_footprint.py       (floor footprint of the built gate)
```

## 1. Census: in-fleet gas-steam bins with no ST_GAS tranche row

CAMPD gross of gas-fired steam units (`primaryFuelInfo` gas, not coal; `unitType` not CC/CT) at plants whose
keeper fleet carries an ST_GAS bin but whose fuel-split artifact has **no ST_GAS row**, TWh:

| year | CEMS gas-steam, no-row bins | keeper model at those plants |
|---|---:|---:|
| 2019 | 2.89 | ~1.33 |
| 2020 | 2.19 | ~1.28 |
| 2021 | 0.37 | — |
| 2022 | 0.51 | — |
| 2023 | 0.41 | — |
| 2024 / 2025 | 0.12 / 0.07 | — |

2019 by plant (CEMS vs model): Baxter Wilson 2050 **1.59 vs 0.67**, Teche 1400 u3 **1.03 vs 0.54** (its CT u4 holds
the plant's only row, CT_PEAKER), Big Cajun 1 1464 0.09 vs 0.01, Rex Brown 2053 0.09 vs 0.09, Houma 1439 0.06 vs 0.005.

**Reading.** These units ran before the pooled 2023–2025 derive window (Baxter Wilson is absent from the 2021+ vintage fleets;
Teche 3's CEMS fell from 1.03 to 0.18 TWh over 2019–23), so the window never measured them. The ceiling of a coverage repair is **~1.5 TWh of the −8.20 TWh
2019 C1 ST_GAS gap** (~0.9 in 2020, ≤0.2 after). The rest is floored plants dispatched below actual on economics
(FINDING-miso276 §2) and VLR commitment the model does not represent (`scuc_load_pocket_commitment` = `·`).

## 2. The built lever: `campd_st_gas_span_coverage` (sub-gate of `campd_unit_fuel_split`)

`derive_thermal_tranches.py --st-gas-span-coverage` appends ST_GAS rows, derived over 2019–2025 with the SAME
unit-routed estimator as miso-278 (`_routed_family_rows`, factored out of `unit_fuel_split_rows`; the fuel-split
companions regenerate byte-identically after the refactor), for every ST_GAS bin the fuel-split companion lacks.
Each `-fuelsplit-stcov-` companion starts with the fuel-split companion's exact bytes. The soco-70 coal-coverage
construction applied to gas steam. Zero free parameters.

Rows appended (8): 1081 Riverside, 1400 Teche, 1439 Houma, 1464 Big Cajun 1, 2050 Baxter Wilson, 2070 Moselle,
2104 Meramec, 4078 Weston. Dan E Karn 1702 is a target and correctly gets **no** row (its gas boilers never reach
the online threshold; miso-278 dropped the coal-conduct row). Rex Brown 2053 is not a target (no ST_GAS vintage bin).

| plant | online_frac | p25 level MW | oom level MW |
|---|---:|---:|---:|
| Baxter Wilson 2050 | 0.461 | 275 | 269 |
| Teche 1400 | 0.327 | 95 | 95 |
| Big Cajun 1 1464 | 0.141 | 39 | 39 |
| Houma 1439 | 0.234 | 9 | 9 |
| Moselle 2070 | 0.098 | 20 | 20 |
| Meramec 2104 | 0.058 | 26 | 25 |

## 3. Footprint (fleet-only rebuild, keeper recipe vs + the single delta)

| year | ST_GAS floor keeper → arm (TWh) | Δ | plants moved |
|---|---|---:|---|
| 2019 | 9.999 → 10.839 | +0.839 | 2050 +0.52, 1400 +0.27, small others |
| 2020 | 10.396 → 11.191 | +0.795 | 2050 +0.48, 1400 +0.27 |
| 2021 | 9.344 → 9.656 | +0.312 | 1400 +0.27 |
| 2022 | 10.334 → 10.645 | +0.311 | 1400 +0.27 |
| 2023 | 9.552 → 9.836 | +0.285 | 1400 +0.27 |
| 2024 | 10.407 → 10.411 | +0.005 | 2070 |
| 2025 | 10.807 → 10.813 | +0.006 | 2070 |

Only ST_GAS floors move; ST_GAS pmax unchanged; no other group's floor changes. 2019–2020 gain 8 LP units (new rows
split the plants' ST_GAS bins into tranches).

**Stated limitation (rule 17).** The window is the pooled `online_frac`, as for every incumbent ST_GAS row
(`mustrun_online_frac_per_year` is `R`). Teche 3's pooled 0.327 floors ~0.27 TWh every year it is in the fleet,
including 2023 when its CEMS gross was 0.18 TWh — a D-4 unit-conduct exposure the scored diagnostics will show.
