# ucmilp-golden: CAISO off-gate replay (GATESPEC §4 G-OFF)

- HEAD: `ec758d64c03f6407fe382f6a52814f3028b71890` (hard stop 1 OK)
- Keeper: `2026-10-02-closeout-caiso-w1-arm2` → `results/calibration/closeout_caiso_w1_a2_span` (`unit_commitment_milp` = None in run_config; scenarios.py carries the field, 6 hits)
- Golden: `results/regression-goldens/ucmilp-off/CAISO/` (gitignored, not pushed)

## Preflight / memory
- `before: memory ceiling 13.36 GiB, swap 0.0 GiB, 16.7 GiB free disk, 4 cpus`
- `swap: added 10 GiB at /swapfile-marketsim — ceiling 13.36 + swap 10.0 = 23.4 GiB total` (WARNING: < 24 GiB target; irrelevant for CAISO)
- hydrate `--profile caiso`: exit 0 (full clone → no-op); `uv sync` (venv absent) then `regenerate_clean --solve-profile CAISO`: exit 0, 9 datatypes incl. uc-params (13.8 s)
- Solver log: `memory peak: cgroup_peak_rss_gib=9.72, cgroup_peak_rss_plus_swap_gib=9.72, process_vmhwm_gib=8.84, process_vmswap_now_gib=0.00`
- Determinism pins: MARKET_SIM_HIGHS_THREADS=1, MARKET_SIM_WARMSTART=1, MARKET_SIM_WARMSTART_XYEAR=0, MALLOC_ARENA_MAX=2, OMP_NUM_THREADS=1
- Fidelity oracle: `fidelity OK: 313 recorded flags replayed identically (0 HEAD-only meta keys); scenario_config 947 matched, 0 drifted`

## Wall per year (one container, sequential; from dispatch/<year>_P1.parquet mtimes, start 23:34:56Z)
| year | done (UTC) | wall |
|---|---|---|
| 2019 | 23:50:42 | 15.8 min (incl. setup) |
| 2020 | 00:08:30 | 17.8 min |
| 2021 | 00:28:23 | 19.9 min |
| 2022 | 00:43:46 | 15.4 min |
| 2023 | 00:56:37 | 12.9 min |
| 2024 | 01:11:11 | 14.6 min |
| 2025 | 01:31:24 | 20.2 min |

Bundle written 01:31:50 (~117 min). The capture process was then killed at 01:34:56 by the harness's 2 h background-task cap
while in its post-bundle manifest step; `manifest.json` was not written. The bundle itself and the fidelity check completed before the kill.
A first launch attempt failed instantly (exit 127, `/usr/bin/time` not installed; no solve ran).

## Result
```
golden-diff: PASS — 35 hourly files compared, 119 numeric columns compared, no failing column, absent: keeper-only=none golden-only=['network_2019.parquet', 'network_2020.parquet', 'network_2021.parquet', 'network_2022.parquet', 'network_2023.parquet', 'network_2024.parquet', 'network_2025.parquet', 'unit_hourly_2019.parquet', 'unit_hourly_2020.parquet', 'unit_hourly_2021.parquet', 'unit_hourly_2022.parquet', 'unit_hourly_2023.parquet', 'unit_hourly_2024.parquet', 'unit_hourly_2025.parquet'] metrics.json=ABSENT(golden)
```

- No `uc_*` file on either side.
- `metrics.json`: **not compared** — absent from the golden. At this SHA `capture_keeper_goldens.py` writes no `metrics.json`; the keeper's is a scoring/verdict artifact (run_id, rubric determination) produced by the registration path (`calibration_verdict.py` / `dashboard_add_run.py`), which this shard is forbidden to run.
- Golden-only (keeper is slim): `network_<year>` ×7, `unit_hourly_<year>` ×7. Keeper-only: none. Keeper has no `reserve_family_<year>`.
- Only numeric non-key columns are value-compared; categorical non-key columns (`unit_marginal.plant_group`, `unit_marginal.fuel`) are not.

## Repo engine
`scripts/regression_gate.py` / `scripts/regression_check.py` compare `year_*.parquet` / `dispatch/`, `system.parquet`, `flows.parquet`, `storage.parquet` at bundle root — they do not reach `hourly/`, and the keeper is slim (no dispatch/ or root frames). So a one-off comparator was used (scratchpad, not committed), text below.

## Inventory (files, sort keys, numeric columns; atol = rtol = 0)
```
class_band_hourly_2019.parquet: rows=569400 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=['mw', 'mw_oil']
class_band_hourly_2020.parquet: rows=569400 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=['mw', 'mw_oil']
class_band_hourly_2021.parquet: rows=569400 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=['mw', 'mw_oil']
class_band_hourly_2022.parquet: rows=569400 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=['mw', 'mw_oil']
class_band_hourly_2023.parquet: rows=569400 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=['mw', 'mw_oil']
class_band_hourly_2024.parquet: rows=569400 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=['mw', 'mw_oil']
class_band_hourly_2025.parquet: rows=516840 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=['mw', 'mw_oil']
class_hourly_2019.parquet: rows=122640 keys=['year', 'pass', 'klass', 'hour'] numeric=['mw']
class_hourly_2020.parquet: rows=122640 keys=['year', 'pass', 'klass', 'hour'] numeric=['mw']
class_hourly_2021.parquet: rows=122640 keys=['year', 'pass', 'klass', 'hour'] numeric=['mw']
class_hourly_2022.parquet: rows=122640 keys=['year', 'pass', 'klass', 'hour'] numeric=['mw']
class_hourly_2023.parquet: rows=122640 keys=['year', 'pass', 'klass', 'hour'] numeric=['mw']
class_hourly_2024.parquet: rows=122640 keys=['year', 'pass', 'klass', 'hour'] numeric=['mw']
class_hourly_2025.parquet: rows=122640 keys=['year', 'pass', 'klass', 'hour'] numeric=['mw']
storage_2019.parquet: rows=17520 keys=['year', 'pass', 'tech', 'hour'] numeric=['charge_mw', 'discharge_mw', 'soc_mwh', 'energy_cap_mwh']
storage_2020.parquet: rows=17520 keys=['year', 'pass', 'tech', 'hour'] numeric=['charge_mw', 'discharge_mw', 'soc_mwh', 'energy_cap_mwh']
storage_2021.parquet: rows=17520 keys=['year', 'pass', 'tech', 'hour'] numeric=['charge_mw', 'discharge_mw', 'soc_mwh', 'energy_cap_mwh']
storage_2022.parquet: rows=17520 keys=['year', 'pass', 'tech', 'hour'] numeric=['charge_mw', 'discharge_mw', 'soc_mwh', 'energy_cap_mwh']
storage_2023.parquet: rows=17520 keys=['year', 'pass', 'tech', 'hour'] numeric=['charge_mw', 'discharge_mw', 'soc_mwh', 'energy_cap_mwh']
storage_2024.parquet: rows=17520 keys=['year', 'pass', 'tech', 'hour'] numeric=['charge_mw', 'discharge_mw', 'soc_mwh', 'energy_cap_mwh']
storage_2025.parquet: rows=17520 keys=['year', 'pass', 'tech', 'hour'] numeric=['charge_mw', 'discharge_mw', 'soc_mwh', 'energy_cap_mwh']
system_2019.parquet: rows=61320 keys=['year', 'pass', 'zone', 'hour'] numeric=['price', 'slack', 'dump', 'demand', 'reserve_price', 'marginal_emission_rate']
system_2020.parquet: rows=61320 keys=['year', 'pass', 'zone', 'hour'] numeric=['price', 'slack', 'dump', 'demand', 'reserve_price', 'marginal_emission_rate']
system_2021.parquet: rows=61320 keys=['year', 'pass', 'zone', 'hour'] numeric=['price', 'slack', 'dump', 'demand', 'reserve_price', 'marginal_emission_rate']
system_2022.parquet: rows=61320 keys=['year', 'pass', 'zone', 'hour'] numeric=['price', 'slack', 'dump', 'demand', 'reserve_price', 'marginal_emission_rate']
system_2023.parquet: rows=61320 keys=['year', 'pass', 'zone', 'hour'] numeric=['price', 'slack', 'dump', 'demand', 'reserve_price', 'marginal_emission_rate']
system_2024.parquet: rows=61320 keys=['year', 'pass', 'zone', 'hour'] numeric=['price', 'slack', 'dump', 'demand', 'reserve_price', 'marginal_emission_rate']
system_2025.parquet: rows=61320 keys=['year', 'pass', 'zone', 'hour'] numeric=['price', 'slack', 'dump', 'demand', 'reserve_price', 'marginal_emission_rate']
unit_marginal_2019.parquet: rows=15382560 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=['mw', 'cap_mw', 'mc', 'marginal']
unit_marginal_2020.parquet: rows=15619080 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=['mw', 'cap_mw', 'mc', 'marginal']
unit_marginal_2021.parquet: rows=15478920 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=['mw', 'cap_mw', 'mc', 'marginal']
unit_marginal_2022.parquet: rows=15794280 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=['mw', 'cap_mw', 'mc', 'marginal']
unit_marginal_2023.parquet: rows=15697920 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=['mw', 'cap_mw', 'mc', 'marginal']
unit_marginal_2024.parquet: rows=15689160 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=['mw', 'cap_mw', 'mc', 'marginal']
unit_marginal_2025.parquet: rows=15741720 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=['mw', 'cap_mw', 'mc', 'marginal']
```

## Command
```
python golden_diff.py results/calibration/closeout_caiso_w1_a2_span results/regression-goldens/ucmilp-off/CAISO
```

## Comparator script (golden_diff.py)
```python
"""One-off exact (atol=rtol=0) diff of hourly/*.parquet + metrics.json between two bundles."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

A = Path(sys.argv[1])  # keeper
B = Path(sys.argv[2])  # golden
KEYS = [
    "year",
    "pass",
    "unit_id",
    "plant_code",
    "zone",
    "klass",
    "band",
    "tech",
    "hour",
]


def is_num(s):
    return pd.api.types.is_numeric_dtype(s.dtype) and not isinstance(
        s.dtype, pd.CategoricalDtype
    )


fa = {p.name for p in (A / "hourly").glob("*.parquet")}
fb = {p.name for p in (B / "hourly").glob("*.parquet")}
both, only_a, only_b = sorted(fa & fb), sorted(fa - fb), sorted(fb - fa)
uc = sorted({str(p.relative_to(r)) for r in (A, B) for p in r.rglob("uc_*")})
fails, ncols, inventory = [], 0, []
for n in both:
    a, b = pd.read_parquet(A / "hourly" / n), pd.read_parquet(B / "hourly" / n)
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        fails.append(
            f"{n}: schema/rowcount {list(a.columns)}/{len(a)} vs {list(b.columns)}/{len(b)}"
        )
        continue
    keys = [k for k in KEYS if k in a.columns]
    for df in (a, b):
        for k in keys:
            if not is_num(df[k]):
                df[k] = df[k].astype(str)
    a = a.sort_values(keys, kind="mergesort").reset_index(drop=True)
    b = b.sort_values(keys, kind="mergesort").reset_index(drop=True)
    for k in keys:
        if not np.array_equal(a[k].to_numpy(), b[k].to_numpy()):
            fails.append(f"{n}:{k} key mismatch")
    num = [c for c in a.columns if c not in keys and is_num(a[c])]
    inventory.append(f"{n}: rows={len(a)} keys={keys} numeric={num}")
    for c in num:
        ncols += 1
        x, y = a[c].to_numpy(), b[c].to_numpy()
        if x.dtype != y.dtype:
            fails.append(f"{n}:{c} dtype {x.dtype} vs {y.dtype}")
        xf, yf = x.astype("float64"), y.astype("float64")
        if not np.array_equal(xf, yf, equal_nan=True):
            diff = ~((xf == yf) | (np.isnan(xf) & np.isnan(yf)))
            fails.append(
                f"{n}:{c} max|Δ|={np.nanmax(np.abs(xf - yf)):.6g} ({int(diff.sum())} cells)"
            )

ma = (
    json.loads((A / "metrics.json").read_text())
    if (A / "metrics.json").exists()
    else None
)
mb = (
    json.loads((B / "metrics.json").read_text())
    if (B / "metrics.json").exists()
    else None
)
metrics = (
    "ABSENT(keeper)"
    if ma is None
    else "ABSENT(golden)"
    if mb is None
    else ("equal" if ma == mb else "UNEQUAL")
)
if metrics == "UNEQUAL":
    fails.append(
        "metrics.json differs at keys "
        + str(sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k)))
    )
if uc:
    fails.append(f"uc_* files present: {uc}")

print("\n".join(inventory))
print("only keeper:", only_a, "| only golden:", only_b, "| metrics.json:", metrics)
for f in fails:
    print("FAIL", f)
print(
    f"golden-diff: {'PASS' if not fails else 'FAIL'} — {len(both)} hourly files compared, "
    f"{ncols} numeric columns compared, "
    f"{'no failing column' if not fails else '; '.join(fails)}, "
    f"absent: keeper-only={only_a or 'none'} golden-only={only_b or 'none'} metrics.json={metrics}"
)
```
