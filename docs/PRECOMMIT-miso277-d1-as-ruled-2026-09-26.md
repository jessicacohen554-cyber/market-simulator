# PRECOMMIT — miso-277: D1 winter daily delivered gas, re-solved AS RULED (MISO-South on Henry Hub)

```
LANE    : miso-277 (owner ruling 2026-09-26 "Re-solve D1 as ruled (Recommended)")
KEEPER  : 2026-09-26-miso-275-cc-exempt (results/calibration/miso275_span, 2019-2025), legs solved at e5acf0fe
ARM     : keeper recipe + miso_winter_gas_daily_delivered = true (the miso-276 field), at a pin carrying the
          _miso_zone_hub_kind fix (South -> Henry Hub in 2019-2021)
CONTROL : none solved. G-DRIFT e5acf0fe..<pin> (§3); the keeper bundle IS the control (rule 29(b) form 4)
SHARDS  : 7 legs, one year each 2019-2025 (rules 34(c), 36), pinned to this document's commit SHA
DATA    : DATA PROFILE: miso — no intake
DOF     : +0
```

## 1. Why this solve exists

The miso-276 D1 arm (declined, matrix `winter_gas_daily_delivered` = R) was **mis-built for MISO-South**:
`miso_zonal_gas_hub.csv` has no South row before 2022, so the applier's `"chicago"` default priced South on the
$129.52 Chicago Uri print in 2019–2021. The owner's ruling was South = Henry Hub. FINDING-miso277 §3. The owner ruled
the corrected construction re-solved before the D1 verdict is taken as final.

## 2. The delta

Recipe: identical to miso-276 (one field). Code: `_miso_zone_hub_kind` takes a zone's hub from the nearest year the
table carries when the solve year has no row (hub = geography; basis value stays per-year). New log line
`MISO winter daily delivered hub map (<Y>): ... MISO-South=henry ...`. Legs 2022–2025 are expected to reproduce the
miso-276 legs' fuel arrays (South already had rows); they are re-solved because the registration needs every
year's `dispatch/<Y>_P1.parquet` and none is on `main` (rule 34(c)).

## 3. G-DRIFT — `e5acf0fe..<pin>`

miso-276 §3a audited every hunk up to its own arm commit (`ba2cc0b1`): all INERT. New since then on the backcast path:

| commit | class | reason |
|---|---|---|
| `736fbe9a` `admit_standby_units` | INERT | default `False`, absent from the keeper recipe; off path returns `{"OP"}` and the unchanged cache key (`_fleet_cache_dir_key` identical while off) |
| `3581f5a8` neiso-118 `scripts/lib/heat_rate_years.py` | INERT | derive-time helper (NEISO CT heat-rate re-derive); no solve-path import |
| miso-277 `_miso_zone_hub_kind` fallback + hub-map log | **LIVE, the delta** | reached only under `miso_winter_gas_daily_delivered` / `miso_gas_marginal_commodity_pricing`, both off in the keeper |
| miso-277 crosswalk intake `data/raw/reference/camd-eia-crosswalk/` | INERT | no loader reads it |

All non-delta hunks INERT → form 4 holds.

## 4. Zero-LP footprint (Feb 2021, keeper fleet, cap-weighted $/MMBtu)

| | storm Feb 13–16 | calm | South storm |
|---|---:|---:|---:|
| keeper | 29.7 | 11.9 | 32.5 |
| D1 as built (miso-276) | 102.3 | 5.5 | 111.5 |
| **D1 as ruled (this arm)** | **56.4** | 5.4 | **7.7** |

`results/calibration/_miso277_storm_print_conventions.json`.

## 5. Predictions (directions only)

1. 2021 storm-week price falls vs miso-276 (334.8); still above the keeper (123.6) because the Chicago-priced zones keep
   the $129.52 print.
2. The 4 h of MISO-South slack on Feb 15 2021 in miso-276 shrink or vanish (South gas now ~$8, not ~$111).
3. C3b 2021: better than miso-276's 0.416; direction vs the keeper's 0.290 not predicted.
4. 2022–2025: within solver noise of the miso-276 legs.

## 6. Decision rule (fixed now)

Structural gates as miso-276 §6 (S-1 recipe incl. `MISO-South=henry` marker and absent `MISO winter citygate daily (`;
S-2 winter-only fuel delta; S-3 slack reported; S-4 no `floors scaled`). C1–C8 reported per year at full magnitude,
vs the keeper and vs miso-276. Promotion is the owner's (rule 31); no criterion selects it (rule 1).

## 7. Arm command (per year Y, one shard each)

```
python scripts/replay_keeper.py results/calibration/miso275_span --years <Y> \
  --set miso_winter_gas_daily_delivered=true \
  --out-dir results/calibration/miso277_arm_<Y> \
  --note "miso-277 arm <Y>: D1 as ruled (South on Henry Hub; owner ruling 2026-09-26)"
```

Shard check: `scripts/probes/_miso277_shard_check.py --leg results/calibration/miso277_arm_<Y> --year <Y> --log <log>`.

## 8. Launch record

(appended after the pin)

Launched 2026-09-26 17:46 UTC, all pinned to `bd0329ed1e6ae134a124acf4c998a0102d5986d2`, tagged `miso-277` / `shard`,
auto-PR off. Each pushes `claude/miso277-arm-<Y>` from out-dir `miso277_arm_<Y>`.

| year | session |
|---|---|
| 2022 (first, slow leg) | `session_0173bFn15sPQdin5UuRWonHq` |
| 2021 | `session_01NQmft3uJCNjojgcW61mAzJ` |
| 2019 | `session_01ANRnWQSqCKDKpiypV5w4GG` |
| 2020 | `session_012prnDqoQAEKfTiBNBwac4n` |
| 2023 | `session_01Cdzx9cNeLsSnC7W3c4i8NF` |
| 2024 | `session_01XnvoRKoCoQP2DghvQ5yv2X` |
| 2025 | `session_01QtHdTTAvFcHC3GT9kuJo6L` |
