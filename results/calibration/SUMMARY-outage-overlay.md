# Historic coal/CC outage overlay — verification summary

Companion to the committed parquet bundles. Both runs are ERCOT 2023–2024,
P1 (no commitment), identical config **except** `outage_source`.

| run | `outage_source` | bundle (parquet) |
|---|---|---|
| historic | `historic` | [`results/calibration/_verify_historic/`](./_verify_historic/) |
| statistical | `statistical` | [`results/calibration/_verify_stat/`](./_verify_stat/) |

Each bundle holds `dispatch/<year>_P1.parquet` (per-generator-hour MW),
`system.parquet`, `eia923.parquet`, `eia930.parquet`, `btm.parquet` and
`meta.json`. Reprint the full [1]–[6] report with:

```
python3 scripts/run_calibration_full.py --report results/calibration/_verify_historic
```

## What the overlay does

When `outage_source == "historic"`, `generators_to_fleet_arrays` zeroes
availability for coal/CC plants (`Plant_Group` in COAL/CC_REGULAR/CC_CHP)
during their actual ERCOT outage windows longer than 10 days (start→stop
span > 240 h). 10 plants qualify across 2023–2025; 4 are active in 2023, more
in 2024. See `src/market_sim/data/outages.py`.

## Per-plant annual generation: statistical → historic vs EIA-923

`Δ overlay` is `historic − statistical` (the overlay's pure effect; both runs
otherwise identical). Outaged plants drop during their windows; non-outaged
plants in the same hours pick up a little of the freed demand (LP rebalancing).

### 2023  (annual GWh)

| plant | statistical | historic | Δ overlay | EIA-923 |
|---|--:|--:|--:|--:|
| Coleto Creek (PRB coal) | 1,665 | 1,389 | -276 | 2,660 |
| Limestone (PRB coal) | 5,028 | 4,681 | -347 | 6,059 |
| J K Spruce (PRB coal) | 4,669 | 4,688 | +19 | 5,078 |
| Frontera (CC) | 3,562 | 3,254 | -308 | 1,073 |
| Barney M Davis (CC) | 3,982 | 4,002 | +20 | 1,541 |
| Wise County (CC) | 5,836 | 5,853 | +17 | 3,353 |
| Wolf Hollow I (CC) | 5,271 | 5,299 | +28 | 3,093 |
| Green Power 2 (CHP, BTM) | 0 | 0 | +0 | 3,785 |

### 2024  (annual GWh)

| plant | statistical | historic | Δ overlay | EIA-923 |
|---|--:|--:|--:|--:|
| Coleto Creek (PRB coal) | 1,395 | 1,224 | -171 | 2,641 |
| Limestone (PRB coal) | 4,290 | 3,571 | -719 | 5,365 |
| J K Spruce (PRB coal) | 3,714 | 3,644 | -70 | 6,124 |
| Frontera (CC) | 3,649 | 3,661 | +12 | 2,266 |
| Barney M Davis (CC) | 1,338 | 1,187 | -151 | 1,561 |
| Wise County (CC) | 5,974 | 5,442 | -532 | 3,445 |
| Wolf Hollow I (CC) | 5,414 | 5,260 | -154 | 3,210 |
| Green Power 2 (CHP, BTM) | 0 | 0 | +0 | 3,879 |

## Reading the result

- The overlay is mechanically correct: it removes dispatch only during the
  real outage windows, and the freed demand is absorbed by other units.
- **Over-dispatched CC plants** (Frontera +200%, Wise/Wolf Hollow ~+70% over
  EIA-923) move **toward** actual — the intended direction.
- **Under-dispatched PRB coal plants** (Coleto, Limestone, J K Spruce already
  below EIA-923) move **further below** on the annual total: the model already
  under-runs coal because of the merit-order gap the must-run floor is meant to
  close, and zeroing the outage hours compounds it. The overlay fixes the
  *seasonal shape* (no output during the real outages) but not the *level*.

So the overlay should be paired with the coal must-run lever
(`coal_*_mustrun_override`), not used to set the coal level on its own. Set
`--outage-source statistical` to disable it for a comparison run.
