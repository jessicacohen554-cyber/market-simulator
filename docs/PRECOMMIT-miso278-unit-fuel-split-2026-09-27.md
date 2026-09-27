# PRECOMMIT — miso-278: thermal-tranche family re-derived with each CAMPD unit routed on its own fuel

```
LANE    : miso-278 (owner charter 2026-09-26, docs/handoffs/CHARTER-miso-stgas-unit-fuel-attribution-2026-09-26.md;
          rule 28(a) off-queue lever, owner-chartered)
KEEPER  : 2026-09-26-miso-277-d1-as (results/calibration/miso277_span, 2019-2025), legs solved at bd0329ed
ARM     : keeper recipe + campd_unit_fuel_split = true (new field, default False)
CONTROL : none solved. G-DRIFT bd0329ed..<pin> (§3); the keeper bundle IS the control (rule 29(b) form 4)
SHARDS  : 7 legs, one year each 2019-2025 (rules 34(c), 36), pinned to this document's commit SHA
DATA    : DATA PROFILE: miso — no intake; four derived companions committed with this document
DOF     : +0 (CAMPD primaryFuelInfo + EIA-860 vintage fleets; no parameter)
```

## 1. The object (rule 23 trigger = the attribution defect, never the C1 residual)

`derive_thermal_tranches.py` attributes a plant's **facility-summed** CAMPD net to its largest-nameplate group. Where
coal and gas boilers share a facility, one bin carries both fuels' conduct (FINDING-miso277 §2). The nyiso-175b
per-unit crosswalk cannot separate them: it routes by prime-mover family, and both are boilers.

## 2. The delta

- **Derive** (`--unit-fuel-split`, `unit_fuel_split_rows`): a plant is mixed-fuel when, in any of 2023–2025, its
  positive-gross CAMPD units include a coal unit and a non-coal unit, or their fuel disagrees with every filed row.
  Each unit routes on its own `primaryFuelInfo`: coal → coal bin; gas → its family's gas bin (`corrected_unit_class`);
  pet-coke / oil / wood → no bin. Group membership and denominators come from each year's EIA-860 vintage fleet;
  the derate is the keeper's own `-unitroute-` basis. The per-row estimator is the frozen one, factored out
  (`_tranche_stats_row`) — **main-path output byte-identical before/after the refactor** (MISO 2023–2025,
  239 rows). Gas-plus-oil plants are out of scope (liquid-fuel defect class).
- **Mixed-fuel set** (16 codes, 9 of them MISO fleet plants with rows): 976, 1001, 1702, 4078, 6034, 6055, 6085,
  6137, 6190. **9 incumbent rows → 14.** Every other line of all four artifacts byte-identical (pinned by
  `tests/unit/data/test_campd_unit_fuel_split.py`).
- **Gate** `campd_unit_fuel_split` (default False, `_CACHE_KEY_OPTIONAL_FIELDS`): one selector
  (`campd_bins.campd_fuel_split_selector`) threaded to every tranche reader whose rows can differ (overrides,
  peaking, online_frac, p25 level, the three intermediate splits, coal sync frac, the three level/window companions,
  the reserve-posture mlf, the coverage guard); CHP readers are invariant by construction (CHP lines kept verbatim).
  `resolved_inputs` records the companions only when armed.
- **Armed fleet build reproduces the probe's swapped-artifact build on all 3,002 LP units, 0 mismatches (2019).**

Key rows (incumbent → fuel split):

| plant | row | incumbent | fuel split |
|---|---|---|---|
| Brame 6190 | COAL | committed 70 / mustrun 60 / online 0.942 | 41.7 / 0 / 0.777 |
| Brame 6190 | ST_GAS | — (no row) | committed 17.6, online 0.672, oom level 75 MW |
| Big Cajun 2 6055 | ST_GAS | — (no row) | committed 20.4, online 0.350, oom level 117 MW |
| Dan E Karn 1702 | ST_GAS | online 0.099, level 158 MW (coal conduct) | row dropped (gas boilers dark) |
| A B Brown 6137 | CT_PEAKER | median CF 40.6 (coal inside) | 18.2 |
| Marion 976 | CT_PEAKER → + COAL | CT median 66.9 (coal inside) | COAL row added; CT online 0.118 |

## 3. G-DRIFT — `bd0329ed..<pin>`

Tree diff over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`, `scripts/replay_keeper.py`,
`data/raw/_validation-source`, `data/raw/reference`; no MISO data file changed.

| hunk | class | reason |
|---|---|---|
| `neiso_winter_fuelsec_conduct_roster` + winter_fuel_inventory refactor + constant | INERT | reached only under `neiso_winter_fuel_mustrun` (False in keeper) |
| `nwpp_path76_alturas_link` (iso_configs, ttc, runner, run_calibration) | INERT | returns the same object unless ISO == NWPP and flag armed |
| `ercot_dam_availability_event_cap_per_unit` (arrays, outages active-units) | INERT | ERCOT-only flag, absent from keeper |
| `unit_outage_coal_extract_basis_share` (outages, floors, arrays, run_calibration) | INERT | default False, absent from keeper; off ⇒ `extract_basis_groups` = the CC groups as before |
| NYISO-NEXT-3 `_mg` in `fleet_to_bins` | INERT | `_mg` forced False without `campd_per_unit_attribution` (False in keeper) |
| SOCO `GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR` 2019–2022 | INERT | SOCO-keyed |
| `solve_surface_declared` new constant | INERT | NEISO winter-fuel constant only |
| `forecast_parity_registry` | INERT | declaration table, no solve import |
| `data/raw/reference/pjm_offer_midcurve_*` | INERT | PJM-only |
| **miso-278 gate + companions** | **LIVE, the delta** | reached only under `campd_unit_fuel_split` |
| miso-278 derive refactor (`_tranche_stats_row`) | INERT | derive-time only; byte-identical output measured |

**Held OUT of the pin:** the charter's Riverside remap (55641 CT-03/CT-04 → EIA 64020). It is not solve-inert:
`run_calibration_full._campd_hourly_frame` (benchmark / BTM-backfill activity gate) and
`scripts/lib/bench_multiclass.py` read raw CAMPD through `CAMPD_UNIT_PLANT_REMAP`. It lands as a separate commit
after this arm is scored, and is LIVE in the next MISO lane's G-DRIFT.

All non-delta hunks INERT → form 4 holds.

## 4. Zero-LP footprint (fleet-only rebuild, keeper recipe; `scripts/probes/_miso278_fuelsplit_footprint.py`)

| year | ST_GAS floor keeper (TWh) | arm | Δ | ST_GAS floored plants added / removed |
|---|---:|---:|---:|---|
| 2019 | 9.659 | 9.999 | +0.340 | +6055, +6190 / none |
| 2020 | 10.066 | 10.396 | +0.331 | same |
| 2021 | 9.150 | 9.344 | +0.194 | same |
| 2022 | 10.099 | 10.334 | +0.235 | same |
| 2023 | 9.172 | 9.552 | +0.380 | same |
| 2024 | 10.170 | 10.407 | +0.237 | same |
| 2025 | 10.566 | 10.807 | +0.242 | same |

Coal and CT floor totals unchanged in every year. 83–103 LP units change tranche split (coal/CT at the nine plants).
ST_GAS pmax unchanged (12,456 MW in 2019): no machine moves class; only the rows describing them change.

## 5. Predictions (directions and bounds only)

1. ST_GAS energy rises by roughly the floor delta (≤ ~0.5 TWh/yr). **C1 ST_GAS 2019 (−8.56 TWh) stays FAIL**: this
   repair reaches ~4 % of the gap. The charter's stated risk holds — most of the gap is units the model does not
   commit (VLR, `scuc_load_pocket_commitment` = `·`) or no-row plants outside the 2023–2025 window (Baxter Wilson).
2. Coal energy at Brame falls (mustrun 60 → 0 on the coal-only series); small COAL_PRB/COAL_BIT moves elsewhere.
3. C3a/C3b: direction not predicted; expected within a few tenths of a percent.

## 6. Decision rule (fixed now)

Structural gates: S-1 recipe = keeper + exactly `campd_unit_fuel_split` (shard check HARD 1); S-2 the leg read the
four pinned `-fuelsplit-` companions (HARD 1b); S-3 inputs/vintage/classifier/log as miso-277. C1–C8 reported per
year at full magnitude vs the keeper. Promotion is the owner's (rule 31); no criterion selects it (rule 1). The
structural case for promotion is rule 14 (an accurate attribution replacing a proxy), independent of the residual.

## 7. Arm command (per year Y, one shard each)

```
python scripts/replay_keeper.py results/calibration/miso277_span --years <Y> \
  --set campd_unit_fuel_split=true \
  --out-dir results/calibration/miso278_arm_<Y> \
  --note "miso-278 arm <Y>: thermal-tranche family re-derived per unit fuel (owner charter 2026-09-26)"
```

Shard check: `scripts/probes/_miso278_shard_check.py --leg results/calibration/miso278_arm_<Y> --year <Y> --log <log>`.
Compose: `scripts/probes/_miso278_compose_span.py`.

## 8. Launch record

(appended after the pin)
