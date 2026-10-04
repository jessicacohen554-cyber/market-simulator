# ucmilp-golden-spp — SPP off-gate replay (GATESPEC §4 G-OFF)

```
golden-diff: PASS — 35 files compared (hourly/{class_band_hourly,class_hourly,storage,system,unit_marginal}_2019..2025), 196 numeric columns compared, no failing column (all np.array_equal, atol=rtol=0), absent: keeper-only 0 / golden-only 14 (network_<y> ×7, unit_hourly_<y> ×7 — not in the slim keeper); metrics.json NOT COMPARED (capture writes no metrics.json; see §Caveats)
```

## Provenance
- HEAD: `ec758d64c03f6407fe382f6a52814f3028b71890` (hard stop 1 OK)
- Keeper: `2026-10-03-closeout-spp-nuc-keeper`, bundle `results/calibration/closeout_spp_nuc_span` (2019–2025); `unit_commitment_milp` in keeper run_config: `None` (hard stop 4 OK; `grep -c` in scenarios.py = 6). Golden run_config: `False`.
- No `uc_*` file on either side.

## Preflight / memory
- `before: memory ceiling 13.36 GiB, swap 0.0 GiB, 16.7 GiB free disk, 4 cpus`
- `swap: added 10 GiB at /swapfile-marketsim — ceiling 13.36 + swap 10.0 = 23.4 GiB total` (WARNING: below 24 GiB target; irrelevant for SPP)
- Env pins: MALLOC_ARENA_MAX=2, MARKET_SIM_HIGHS_THREADS=1, OMP_NUM_THREADS=1 (+ script pins WARMSTART=1, WARMSTART_XYEAR=0)
- Memory peak (both members): `cgroup_peak_rss_gib=6.90, rss_plus_swap=6.90, process_vmhwm_gib=6.04 (validation) / 5.28 (train), swap_now=0.00`

## Setup notes (no repo edits)
- Container had no Python deps: `regenerate_clean.py` first failed `ModuleNotFoundError: pandas`. Ran `uv sync` (the documented install route); all subsequent steps under `.venv`. Hydrate exit 0 (full clone, no-op); regenerate exit 0 (uc-params 36.8 s).
- Bare key `SPP` refused: "keepers/SPP.json declares a config_partition with no 'forward' role (roles: train-2023-2025, validation-2019-2022)". Per the shard prompt, captured both members in one invocation:
  `python3 scripts/capture_keeper_goldens.py --iso SPP__validation-2019-2022 SPP__train-2023-2025 --stage-tag ucmilp-off --max-concurrency 1` → exit 0.
- Fidelity oracle: validation 313 flags identical, scenario_config 948 matched / 0 drifted; train 313 flags identical, 946 matched / 2 drifted (`gas_price_override` 2.57→2.54, `weather_year` 2019→2023). Benign: the span-level keeper `run_config.json` records the first year (2019); keeper `run_config_2023.json` carries 2.54 / 2023, matching the golden.
- Non-fatal WARNING after each member: `resolved_inputs: split-remap probe failed — FileNotFoundError: campd_split_remap_companions is armed but campd-unit-outages-maxgen-splitremap-SPP.csv has not been derived`. Provenance probe only; caught, solve and outputs unaffected (diff is exact). Flag for the engine lane: the SPP recipe arms `campd_split_remap_companions` with no SPP companion file.

## Wall per year (phase-timing total)
| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| s | 171.2 | 169.3 | 161.6 | 149.5 | 152.1 | 153.1 | 151.9 |

## Inventory (rows, numeric cols compared; every file exact)
| file family | rows/yr | numeric cols |
|---|---|---|
| class_band_hourly | 359,160 | 4 |
| class_hourly | 140,160 | 3 |
| storage | 17,520 | 6 |
| system | 17,520 | 8 |
| unit_marginal | 11.13–11.39 M | 7 |

Per-year: 5 families × 7 years = 35 files; 28 numeric cols/yr × 7 = 196. Non-numeric columns (pass, klass, band, tech, zone, unit_id, plant_group, fuel) also compared as strings — all equal.

## Caveats
- **metrics.json not compared.** The keeper's `metrics.json` is the composed determination record (rubric v3.18, `determination`, `reasons`, …); `capture_keeper_goldens.py` writes no `metrics.json` into either golden member. Not re-scored here (scoring is outside a shard's scope). Since every hourly input it is scored from is bit-identical, a re-score would reproduce it, but that is inferred, not shown.
- `scripts/regression_gate.py` / `regression_check.py` compare `dispatch/*_P1`, `system/flows/storage.parquet` and `year_*.parquet` golden-vs-golden; neither reaches the keeper's `hourly/` layer, so the one-off script below was used (scratchpad, not committed).

## Comparison command
```
python3 golden_diff.py results/calibration/closeout_spp_nuc_span \
  results/regression-goldens/ucmilp-off/SPP__validation-2019-2022 \
  results/regression-goldens/ucmilp-off/SPP__train-2023-2025
```
```python
"""One-off exact diff: keeper hourly/*.parquet + metrics.json vs golden capture(s). atol=rtol=0."""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

KEEPER = Path(sys.argv[1])
GOLDENS = [Path(p) for p in sys.argv[2:]]
KEYS = ["year", "pass", "unit_id", "zone", "klass", "band", "tech", "hour"]

gold_files = {}
for g in GOLDENS:
    for f in sorted((g / "hourly").glob("*.parquet")):
        gold_files.setdefault(f.name, f)
keep_files = {f.name: f for f in sorted((KEEPER / "hourly").glob("*.parquet"))}

uc_files = sorted(n for n in set(gold_files) | set(keep_files) if n.startswith("uc_"))
both = sorted(set(gold_files) & set(keep_files))
only_keeper = sorted(set(keep_files) - set(gold_files))
only_golden = sorted(set(gold_files) - set(keep_files))

n_cols = 0
fails = []
inventory = []
for name in both:
    a = pd.read_parquet(keep_files[name])
    b = pd.read_parquet(gold_files[name])
    keys = [k for k in KEYS if k in a.columns and k in b.columns]
    a = a.sort_values(keys, kind="mergesort").reset_index(drop=True)
    b = b.sort_values(keys, kind="mergesort").reset_index(drop=True)
    cols_a, cols_b = set(a.columns), set(b.columns)
    if a.shape[0] != b.shape[0]:
        fails.append(f"{name}: rows {a.shape[0]} vs {b.shape[0]}")
        inventory.append((name, a.shape[0], 0, "ROWCOUNT"))
        continue
    if cols_a != cols_b:
        fails.append(
            f"{name}: columns keeper-only {sorted(cols_a - cols_b)} golden-only {sorted(cols_b - cols_a)}"
        )
    ncmp = 0
    for c in sorted(cols_a & cols_b):
        x, y = a[c].to_numpy(), b[c].to_numpy()
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
            ncmp += 1
            xf, yf = x.astype("float64"), y.astype("float64")
            if not np.array_equal(xf, yf, equal_nan=True):
                d = np.nanmax(np.abs(xf - yf))
                fails.append(
                    f"{name}:{c} max|Δ|={d:.6g} (dtype {a[c].dtype}/{b[c].dtype})"
                )
        else:
            if not (
                pd.Series(x).astype(str).values == pd.Series(y).astype(str).values
            ).all():
                fails.append(f"{name}:{c} (non-numeric mismatch)")
    n_cols += ncmp
    inventory.append((name, a.shape[0], ncmp, "ok"))

# metrics.json
metrics_note = []
km = KEEPER / "metrics.json"
for g in GOLDENS:
    gm = g / "metrics.json"
    if not gm.exists():
        metrics_note.append(f"{gm}: absent")
        continue
    if json.loads(km.read_text()) == json.loads(gm.read_text()):
        metrics_note.append(f"{gm}: EQUAL")
    else:
        a, b = json.loads(km.read_text()), json.loads(gm.read_text())
        diffk = (
            sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            if isinstance(a, dict) and isinstance(b, dict)
            else ["<non-dict>"]
        )
        metrics_note.append(f"{gm}: DIFFERS on keys {diffk[:30]}")

for row in inventory:
    print("INV", *row)
print("ONLY_KEEPER", only_keeper)
print("ONLY_GOLDEN", only_golden)
print("UC_FILES", uc_files)
print("METRICS", metrics_note)
status = "FAIL" if (fails or uc_files) else "PASS"
print(
    f"golden-diff: {status} — {len(both)} files compared, {n_cols} numeric columns compared, "
    f"{'; '.join(fails) if fails else 'no failing column'}, absent: keeper-only {len(only_keeper)} / golden-only {len(only_golden)}"
)
```
