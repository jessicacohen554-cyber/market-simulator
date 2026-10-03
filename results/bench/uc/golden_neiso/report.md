# ucmilp-golden NEISO — off-gate replay of keeper 2026-10-02-w0-neiso

- HEAD: `ec758d64c03f6407fe382f6a52814f3028b71890` (hard stop 1 pass)
- Preflight: `before: memory ceiling 13.36 GiB, swap 0.0 GiB, 16.7 GiB free disk, 4 cpus`; `swap: added 10 GiB — ceiling 13.36 + swap 10.0 = 23.4 GiB total` (below-24-GiB warning is MISO/PJM-scoped; NEISO peak far under)
- Data: `uv sync` (no .venv in fresh container), `hydrate_data.py --profile neiso` exit 0 (full clone, no-op), `regenerate_clean.py --solve-profile NEISO` exit 0 (8 datatypes incl. uc-params 9.0 s)
- Gate: `unit_commitment_milp` occurs 6× in scenarios.py; keeper run_config value = None (not armed)
- Env: MALLOC_ARENA_MAX=2, MARKET_SIM_HIGHS_THREADS=1, OMP_NUM_THREADS=1; WARMSTART=1 / WARMSTART_XYEAR=0 pinned by capture_keeper_goldens.py
- Command: `python3 scripts/capture_keeper_goldens.py --iso NEISO --stage-tag ucmilp-off --max-concurrency 1` → exit 0, start 23:33:32, end 23:51:38 UTC (18.1 min)
- Fidelity oracle: `fidelity OK: 313 recorded flags replayed identically (0 HEAD-only meta keys); scenario_config 947 matched, 0 drifted`
- Memory peak: cgroup_peak_rss_gib=5.70, rss+swap 5.70, process_vmhwm 5.21 GiB, swap 0.00

## Wall per year (phase timing total)
| year | total s | P0 s | P1 s | peak GB |
|---|---|---|---|---|
| 2019 | 139.2 | 76.5 | 23.8 | 4.50 |
| 2020 | 139.4 | 77.4 | 25.7 | 5.00 |
| 2021 | 145.5 | 74.6 | 32.1 | 5.16 |
| 2022 | 135.7 | 70.0 | 30.1 | 5.16 |
| 2023 | 170.9 | 90.1 | 34.4 | 5.16 |
| 2024 | 125.8 | 69.4 | 22.3 | 5.21 |
| 2025 | 115.4 | 65.0 | 21.2 | 5.21 |

## Result
```
golden-diff: PASS — 42 hourly/ files compared (6 families × 7 years), 154 numeric columns compared, 0 failing columns (max |Δ| = 0 everywhere), absent on golden side: none; absent on keeper side: 14 (network_<yr> ×7, unit_hourly_<yr> ×7 — slim keeper by design); uc_* files: 0 on either side; metrics.json NOT COMPARED (golden capture writes no metrics.json — it is a scoring output, not a solve output)
```

## Inventory (keeper ∩ golden, all years 2019–2025)
| family | sort keys | numeric columns (exact) | non-numeric (string-equal) |
|---|---|---|---|
| class_band_hourly | year, pass, klass, band, hour | mw, mw_oil | — |
| class_hourly | year, pass, klass, hour | mw | — |
| reserve_family | year, pass, family, reserve_class, zones, hour | dual, requirement_mw, held_mw, shortfall_mw | — |
| storage | year, pass, tech, hour | charge_mw, discharge_mw, soc_mwh, energy_cap_mwh | — |
| system | year, pass, zone, hour | price, slack, dump, demand, reserve_price, marginal_emission_rate | — |
| unit_marginal | year, pass, unit_id, zone, hour | plant_code, mw, cap_mw, mc, marginal | plant_group, fuel |

Row counts and column sets identical per file; dtypes identical (checked per column).

## Comparison method
`scripts/regression_gate.py` / `regression_check.py` cover dispatch/system/flows/storage bundle-root parquets only (absent from the slim keeper), not `hourly/`, so a one-off script in the session scratchpad was used (not under scripts/, not committed):

```
python3 golden_diff.py results/calibration/w0_neiso_span results/regression-goldens/ucmilp-off/NEISO
```
```python
"""One-off exact (atol=rtol=0) diff of hourly/ sidecars + metrics.json: keeper vs golden."""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

KEEP = Path(sys.argv[1])
GOLD = Path(sys.argv[2])
KEYS = [
    "year",
    "pass",
    "unit_id",
    "zone",
    "klass",
    "band",
    "family",
    "reserve_class",
    "zones",
    "tech",
    "hour",
]


def norm(d, keys):
    d = d.copy()
    for k in keys:
        d[k] = (
            d[k].astype(str)
            if str(d[k].dtype) in ("category", "object", "str", "string")
            else d[k]
        )
    return d.sort_values(keys, kind="mergesort").reset_index(drop=True)


kp = {p.name for p in (KEEP / "hourly").glob("*.parquet")}
gp = {p.name for p in (GOLD / "hourly").glob("*.parquet")}
both = sorted(kp & gp)
fails, ncols, inv = [], 0, []
uc = sorted(n for n in kp | gp if n.startswith("uc_"))
for n in both:
    a = pd.read_parquet(KEEP / "hourly" / n)
    b = pd.read_parquet(GOLD / "hourly" / n)
    keys = [k for k in KEYS if k in a.columns]
    if set(a.columns) != set(b.columns) or len(a) != len(b):
        fails.append(
            f"{n}: schema/rows differ ({sorted(set(a.columns) ^ set(b.columns))}, {len(a)} vs {len(b)})"
        )
        continue
    a, b = norm(a, keys), norm(b, keys)
    for k in keys:
        if not (a[k].astype(str).values == b[k].astype(str).values).all():
            fails.append(f"{n}:{k} key mismatch")
    nums = [
        c for c in a.columns if c not in keys and pd.api.types.is_numeric_dtype(a[c].dtype)
    ]
    others = [c for c in a.columns if c not in keys and c not in nums]
    for c in others:
        if not (a[c].astype(str).values == b[c].astype(str).values).all():
            fails.append(f"{n}:{c} (non-numeric) differs")
    for c in nums:
        ncols += 1
        x, y = a[c].to_numpy(), b[c].to_numpy()
        if x.dtype != y.dtype:
            fails.append(f"{n}:{c} dtype {x.dtype} vs {y.dtype}")
        if not np.array_equal(x, y, equal_nan=True):
            d = np.nanmax(np.abs(x.astype("float64") - y.astype("float64")))
            fails.append(f"{n}:{c} max|d|={d:.6g}")
    inv.append(f"{n}: rows={len(a)} keys={keys} numeric={nums} other={others}")
MK = KEEP / "metrics.json"
MG = GOLD / "metrics.json"
if not MG.exists():
    mjson = "golden absent"
else:
    mk = json.loads(MK.read_text())
    mg = json.loads(MG.read_text())
    mjson = mk == mg
if mjson is False:
    diff = sorted(k for k in set(mk) | set(mg) if mk.get(k) != mg.get(k))
    fails.append(f"metrics.json differs at top-level keys {diff[:20]}")
print("\n".join(inv))
print("absent in golden:", sorted(kp - gp))
print("absent in keeper:", sorted(gp - kp))
print("uc_ files:", uc)
if uc:
    fails.append(f"uc_* files present: {uc}")
print("FAILS:", *fails, sep="\n  ")
print(
    f"golden-diff: {'PASS' if not fails else 'FAIL'} — {len(both)} files compared, {ncols} numeric columns compared, "
    f"{len(fails)} failing item(s), absent golden={len(kp - gp)} absent keeper={len(gp - kp)}, metrics.json equal={mjson}"
)
```
