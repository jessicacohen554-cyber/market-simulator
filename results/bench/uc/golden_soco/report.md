# ucmilp-golden-soco — SOCO off-gate replay (GATESPEC §4 G-OFF)

- HEAD: `ec758d64c03f6407fe382f6a52814f3028b71890` (hard stop 1 OK)
- Keeper replayed: `2026-10-03-closeout-soco-3-coalpile` → `results/calibration/closeout_soco_3_span`
- Gate: `unit_commitment_milp` in keeper run_config = `None`; `grep -c` in scenarios.py = 6 (hard stop 4 OK)
- Model: Opus. DATA PROFILE: soco. One container, `--max-concurrency 1`.

## Preflight / environment
- `before: memory ceiling 13.36 GiB, swap 0.0 GiB, 16.7 GiB free disk, 4 cpus`
- `swap: added 10 GiB at /swapfile-marketsim — ceiling 13.36 + swap 10.0 = 23.4 GiB total` (warning: < 24 GiB target; irrelevant for SOCO)
- hydrate_data --profile soco: exit 0. regenerate_clean --solve-profile SOCO: exit 0 (5 datatypes incl. uc-params 23.9 s).
- Note: the container had no project venv (system python lacked pandas → first regenerate_clean exit 1). Ran `uv sync` (the documented install route; lockfile unchanged, `git status` clean) and re-ran both data steps under `.venv`. No repo file edited.
- Env pins: MARKET_SIM_HIGHS_THREADS=1, MARKET_SIM_WARMSTART=1, MARKET_SIM_WARMSTART_XYEAR=0, OMP_NUM_THREADS=1, MALLOC_ARENA_MAX=2
- Memory peak (script log): `cgroup_peak_rss_gib=4.81, cgroup_peak_rss_plus_swap_gib=4.81, process_vmhwm_gib=4.34, process_vmswap_now_gib=0.00`
- Fidelity oracle: `[SOCO] fidelity OK: 313 recorded flags replayed identically (0 HEAD-only meta keys); scenario_config 949 matched, 0 drifted`

## Wall per year (from dispatch/<year>_P1.parquet mtimes; start 23:35:17Z)
| year | wall |
|---|---|
| 2019 | 4m04s |
| 2020 | 4m03s |
| 2021 | 3m25s |
| 2022 | 3m50s |
| 2023 | 3m54s |
| 2024 | 3m33s |
| 2025 | 3m58s |
| total incl. manifest | 27m58s (exit 0 at 00:03:15Z) |

## Result
```
golden-diff: PASS — 42 hourly parquets (7 yrs × class_band_hourly, class_hourly, hydro_cascade, storage, system, unit_marginal), 238 numeric columns at atol=rtol=0 (np.array_equal after key sort), max |Δ| = none (0 failing columns), absent: keeper-only none; golden-only network_<yr> ×7 + unit_hourly_<yr> ×7 (slim keeper omits them by design); metrics.json ABSENT on golden side (not compared — see below); uc_* files: none on either side
```

**metrics.json not compared.** `capture_keeper_goldens.py` writes no metrics.json; the keeper's is the
determination output of `calibration_verdict.py --write-metrics`, which reads the *registry payload*,
attestation and benchmark parts — not the bundle parquets — so a golden-side copy requires registration
(forbidden for this shard). The engine lane decides whether the hourly identity suffices for G-OFF or a
registered-path comparison is still owed.

Repo engine not used: `regression_gate.py` / `regression_check.py` compare `dispatch/` + bundle-root
frames only and the slim keeper carries neither, so neither reaches `hourly/`. One-off script below
(scratchpad only, never committed under scripts/).

## Inventory (rows per file; sort keys; numeric/other column counts)
```
class_band_hourly_2019.parquet: rows=332880 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=4 other=3
class_band_hourly_2020.parquet: rows=332880 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=4 other=3
class_band_hourly_2021.parquet: rows=332880 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=4 other=3
class_band_hourly_2022.parquet: rows=332880 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=4 other=3
class_band_hourly_2023.parquet: rows=332880 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=4 other=3
class_band_hourly_2024.parquet: rows=332880 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=4 other=3
class_band_hourly_2025.parquet: rows=332880 keys=['year', 'pass', 'klass', 'band', 'hour'] numeric=4 other=3
class_hourly_2019.parquet: rows=131400 keys=['year', 'pass', 'klass', 'hour'] numeric=3 other=2
class_hourly_2020.parquet: rows=131400 keys=['year', 'pass', 'klass', 'hour'] numeric=3 other=2
class_hourly_2021.parquet: rows=131400 keys=['year', 'pass', 'klass', 'hour'] numeric=3 other=2
class_hourly_2022.parquet: rows=131400 keys=['year', 'pass', 'klass', 'hour'] numeric=3 other=2
class_hourly_2023.parquet: rows=131400 keys=['year', 'pass', 'klass', 'hour'] numeric=3 other=2
class_hourly_2024.parquet: rows=131400 keys=['year', 'pass', 'klass', 'hour'] numeric=3 other=2
class_hourly_2025.parquet: rows=131400 keys=['year', 'pass', 'klass', 'hour'] numeric=3 other=2
hydro_cascade_2019.parquet: rows=131400 keys=['year', 'pass', 'plant_code', 'hour'] numeric=6 other=1
hydro_cascade_2020.parquet: rows=140160 keys=['year', 'pass', 'plant_code', 'hour'] numeric=6 other=1
hydro_cascade_2021.parquet: rows=131400 keys=['year', 'pass', 'plant_code', 'hour'] numeric=6 other=1
hydro_cascade_2022.parquet: rows=131400 keys=['year', 'pass', 'plant_code', 'hour'] numeric=6 other=1
hydro_cascade_2023.parquet: rows=140160 keys=['year', 'pass', 'plant_code', 'hour'] numeric=6 other=1
hydro_cascade_2024.parquet: rows=131400 keys=['year', 'pass', 'plant_code', 'hour'] numeric=6 other=1
hydro_cascade_2025.parquet: rows=131400 keys=['year', 'pass', 'plant_code', 'hour'] numeric=6 other=1
storage_2019.parquet: rows=17520 keys=['year', 'pass', 'hour'] numeric=6 other=2
storage_2020.parquet: rows=17520 keys=['year', 'pass', 'hour'] numeric=6 other=2
storage_2021.parquet: rows=17520 keys=['year', 'pass', 'hour'] numeric=6 other=2
storage_2022.parquet: rows=17520 keys=['year', 'pass', 'hour'] numeric=6 other=2
storage_2023.parquet: rows=17520 keys=['year', 'pass', 'hour'] numeric=6 other=2
storage_2024.parquet: rows=17520 keys=['year', 'pass', 'hour'] numeric=6 other=2
storage_2025.parquet: rows=17520 keys=['year', 'pass', 'hour'] numeric=6 other=2
system_2019.parquet: rows=26280 keys=['year', 'pass', 'zone', 'hour'] numeric=8 other=2
system_2020.parquet: rows=26280 keys=['year', 'pass', 'zone', 'hour'] numeric=8 other=2
system_2021.parquet: rows=26280 keys=['year', 'pass', 'zone', 'hour'] numeric=8 other=2
system_2022.parquet: rows=26280 keys=['year', 'pass', 'zone', 'hour'] numeric=8 other=2
system_2023.parquet: rows=26280 keys=['year', 'pass', 'zone', 'hour'] numeric=8 other=2
system_2024.parquet: rows=26280 keys=['year', 'pass', 'zone', 'hour'] numeric=8 other=2
system_2025.parquet: rows=26280 keys=['year', 'pass', 'zone', 'hour'] numeric=8 other=2
unit_marginal_2019.parquet: rows=3723000 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=7 other=5
unit_marginal_2020.parquet: rows=3661680 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=7 other=5
unit_marginal_2021.parquet: rows=3740520 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=7 other=5
unit_marginal_2022.parquet: rows=3828120 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=7 other=5
unit_marginal_2023.parquet: rows=3644160 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=7 other=5
unit_marginal_2024.parquet: rows=3670440 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=7 other=5
unit_marginal_2025.parquet: rows=3565320 keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour'] numeric=7 other=5
```

## Comparison command
`python golden_diff.py results/calibration/closeout_soco_3_span results/regression-goldens/ucmilp-off/SOCO`

```python
"""One-off exact (atol=rtol=0) diff of hourly/*.parquet + metrics.json between keeper and golden."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

A = Path(sys.argv[1]); B = Path(sys.argv[2])
KEYS = ["year", "pass", "unit_id", "plant_code", "zone", "klass", "band", "hour", "timestamp"]
fa = {p.name for p in (A / "hourly").glob("*.parquet")}
fb = {p.name for p in (B / "hourly").glob("*.parquet")}
both = sorted(fa & fb)
fails, ncols, inv = [], 0, []
uc = sorted(n for n in fa | fb if n.startswith("uc_"))
for n in both:
    a = pd.read_parquet(A / "hourly" / n); b = pd.read_parquet(B / "hourly" / n)
    if set(a.columns) != set(b.columns):
        fails.append(f"{n}: column set differs a-b={set(a.columns)-set(b.columns)} b-a={set(b.columns)-set(a.columns)}")
    if len(a) != len(b):
        fails.append(f"{n}: rows {len(a)} vs {len(b)}"); continue
    keys = [k for k in KEYS if k in a.columns and k in b.columns]
    if keys:
        a = a.sort_values(keys, kind="mergesort").reset_index(drop=True)
        b = b.sort_values(keys, kind="mergesort").reset_index(drop=True)
    cols = [c for c in a.columns if c in b.columns]
    nnum = 0
    for c in cols:
        x, y = a[c].to_numpy(), b[c].to_numpy()
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
            nnum += 1
            if x.dtype != y.dtype:
                fails.append(f"{n}:{c} dtype {x.dtype} vs {y.dtype}")
            if not np.array_equal(x, y, equal_nan=x.dtype.kind == "f"):
                d = np.nanmax(np.abs(x.astype("float64") - y.astype("float64")))
                fails.append(f"{n}:{c} max|d|={d:.6g}")
        else:
            if not (a[c].astype(str).to_numpy() == b[c].astype(str).to_numpy()).all():
                fails.append(f"{n}:{c} non-numeric mismatch")
    ncols += nnum
    inv.append(f"{n}: rows={len(a)} keys={keys} numeric={nnum} other={len(cols)-nnum}")
mpa, mpb = A / "metrics.json", B / "metrics.json"
if not (mpa.exists() and mpb.exists()):
    mj = f"ABSENT (keeper={mpa.exists()}, golden={mpb.exists()})"
else:
    ma = json.loads(mpa.read_text()); mb = json.loads(mpb.read_text()); mj = ma == mb
if mj is False:
    def walk(x, y, p=""):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                if k not in x or k not in y: fails.append(f"metrics.json:{p}/{k} only one side")
                else: walk(x[k], y[k], f"{p}/{k}")
        elif x != y: fails.append(f"metrics.json:{p} {x!r} vs {y!r}")
    walk(ma, mb)
for f in uc: fails.append(f"uc file present: {f}")
print("\n".join(inv))
print("only-keeper:", sorted(fa - fb)); print("only-golden:", sorted(fb - fa))
print("metrics.json equal:", mj)
print("FAILS:", len(fails)); print("\n".join(fails[:200]))
print(f"golden-diff: {'PASS' if not fails else 'FAIL'} — {len(both)} hourly parquets + metrics.json, {ncols} numeric columns, "
      f"{len(fails)} failing items, absent: keeper-only={len(fa-fb)} golden-only={len(fb-fa)}")
```
