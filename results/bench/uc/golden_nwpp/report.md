# ucmilp-golden-nwpp — NWPP off-gate replay (G-OFF), budget-stopped

- HEAD: `ec758d64c03f6407fe382f6a52814f3028b71890` (hard stop 1 ok)
- Keeper: `2026-10-03-nwpp-next-26-nevp` → `results/calibration/nwppnext26_span` (`unit_commitment_milp` = None in run_config; hard stop 4 ok, `grep -c` = 6)
- Gate: `unit_commitment_milp` OFF (not armed)

## Preflight / memory
- `before: memory ceiling 13.36 GiB, swap 0.0 GiB, 16.7 GiB free disk, 4 cpus`
- `swap: added 10 GiB at /swapfile-marketsim — ceiling 13.36 + swap 10.0 = 23.4 GiB total` (WARNING: 0.6 GiB below the 24 GiB target; non-blocking for NWPP)
- Memory, 2019: `resident=0.77 GB peak=3.65 GB` (after release)

## Data steps (hard stop 3)
- `hydrate_data.py --profile nwpp`: exit 0 (full clone, no-op)
- `regenerate_clean.py --solve-profile NWPP`: first attempt exit 1 (`ModuleNotFoundError: pandas` — container had no venv). Ran `uv sync` (CLAUDE.md's only install route; no repo file changed), then `uv run python scripts/regenerate_clean.py --solve-profile NWPP`: exit 0 (6 datatypes, including `uc-params` 7.7 s)

## Run
`eval "$(uv run python scripts/prepare_solve_container.py --emit-exports)"; MARKET_SIM_HIGHS_THREADS=1 MARKET_SIM_WARMSTART=1 MARKET_SIM_WARMSTART_XYEAR=0 uv run python scripts/capture_keeper_goldens.py --iso NWPP --stage-tag ucmilp-off --max-concurrency 1`
Started 2026-10-03 23:34 UTC; **stopped at the 90-min budget (01:03 UTC)** while 2020 was solving.

| year | P0 solve | P1 solve | status |
|---|---|---|---|
| 2019 | 1438.9 s (cold, 457,201 it) | 2848.2 s (warm, 215,494 it) | solved, sidecars written (wall ≈ 73 min) |
| 2020 | 926.1 s (cold, 410,121 it) | — | killed at budget |
| 2021–2025 | — | — | not started |

At this rate (1 thread), the full 7-year capture needs about 6–7 h in one container. It does not fit a 90-min budget; one shard per year would.

## golden-diff
Full line (the owed 7-year comparison did not complete):
`golden-diff: INCOMPLETE — budget reached; 1/7 years solved`

Partial result, 2019 only, on files present on both sides:
`golden-diff (2019 partial): PASS — 5 files compared (class_band_hourly, class_hourly, hydro_cascade, storage, unit_marginal _2019), 26 numeric columns compared, 0 failing columns, absent: system_2019 golden-side (written at bundle end, run stopped first), network_2019 + unit_hourly_2019 keeper-side (slim bundle); metrics.json absent golden-side (not compared); uc_* files: none on either side`

Inventory (2019, exact, atol = rtol = 0, np.array_equal after a stable sort on keys):
- class_band_hourly_2019: 385,440 rows; keys year,pass,klass,band,hour; numeric year,hour,mw,mw_oil
- class_hourly_2019: 148,920 rows; keys year,pass,klass,hour; numeric year,hour,mw
- hydro_cascade_2019: 43,800 rows; keys year,pass,plant_code,hour; numeric year,plant_code,hour,spill_kcfs,pond_kcfsh,water_value
- storage_2019: 17,520 rows; keys year,pass,tech,hour; numeric year,hour,charge_mw,discharge_mw,soc_mwh,energy_cap_mwh
- unit_marginal_2019: 5,983,080 rows; keys year,pass,unit_id,plant_code,zone,hour; numeric year,plant_code,hour,mw,cap_mw,mc,marginal
- Non-numeric columns (pass, klass, band, tech, unit_id, plant_group, fuel, zone) also compared with `Series.equals`: equal.

## Comparison tool
The repo engine (`scripts/regression_gate.py` → `scripts/regression_check.py`) compares `dispatch/`, `system.parquet`, `flows.parquet` and `storage.parquet` (`year_*.parquet` glob). It does not reach `hourly/`, and the slim keeper has none of those files. So I used a one-off script in the session scratchpad (not committed, not under scripts/). Command:
`uv run python <scratch>/golden_diff.py results/calibration/nwppnext26_span results/regression-goldens/ucmilp-off/NWPP 2019`
Self-check, keeper vs keeper: PASS, 42 files, 238 numeric columns.

```python
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
KEEP = Path(sys.argv[1]); GOLD = Path(sys.argv[2])
KEYS = ["year","pass","unit_id","plant_code","zone","klass","band","tech","hour"]
kf = {p.name for p in (KEEP/"hourly").glob("*.parquet")}
gf = {p.name for p in (GOLD/"hourly").glob("*.parquet")}
YR = sys.argv[3] if len(sys.argv) > 3 else ""
both = sorted(f for f in kf & gf if YR in f)
uc_files = sorted(f for f in kf | gf if f.startswith("uc_"))
fails, ncols = [], 0
for name in both:
    a = pd.read_parquet(KEEP/"hourly"/name); b = pd.read_parquet(GOLD/"hourly"/name)
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        fails.append(f"{name}: shape/cols"); continue
    keys = [k for k in KEYS if k in a.columns]
    a = a.sort_values(keys, kind="mergesort").reset_index(drop=True)
    b = b.sort_values(keys, kind="mergesort").reset_index(drop=True)
    for c in a.columns:
        if pd.api.types.is_numeric_dtype(a[c]) or pd.api.types.is_bool_dtype(a[c]):
            ncols += 1; x, y = a[c].to_numpy(), b[c].to_numpy()
            if a[c].dtype != b[c].dtype: fails.append(f"{name}:{c} dtype")
            if not np.array_equal(x, y, equal_nan=np.issubdtype(x.dtype, np.floating)):
                fails.append(f"{name}:{c} max|d|={np.nanmax(np.abs(x.astype(float)-y.astype(float)))}")
        elif not a[c].equals(b[c]): fails.append(f"{name}:{c} differs")
# metrics.json: json.load both sides and compare with == when the golden side exists
if uc_files: fails.append(f"uc_* present: {uc_files}")
```

## Retention
The partial golden bundle stays on disk, uncommitted, at `results/regression-goldens/ucmilp-off/NWPP/` (2019 dispatch/hourly/floors). It will not survive the container. No result was deleted.
