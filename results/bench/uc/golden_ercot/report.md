# ucmilp-golden-ercot — ERCOT keeper off-gate replay (GATESPEC §4 G-OFF)

**golden-diff: PASS — 14 hourly/ files (7 frame types × {2024, 2025}), 84 numeric columns, all bit-identical (atol = rtol = 0, np.array_equal, non-numeric key columns equal as strings, row counts and column order equal); no failing column; absent on one side: keeper-only = hourly/*_{2019..2023}.parquet (35, outside the bare key's designated years) + metrics.json (golden writes none — see §metrics); golden-only = network_{2024,2025}, unit_hourly_{2024,2025} (keeper is slim); uc_* files: none on either side.**

## Provenance
- HEAD: `ec758d64c03f6407fe382f6a52814f3028b71890` (hard stop 1 ✓)
- Keeper: `2026-10-02-closeout-l1-coal-fuel`, bundle `results/calibration/closeout_ercot_l1_span`; capture key `ERCOT` (bare = forward role, designated years [2024, 2025], R-AW). Partition members not captured separately (bare key did not refuse).
- `unit_commitment_milp`: `grep -c` in scenarios.py = 6; keeper run_config → `None`; golden run_config → `False` (hard stop 4 ✓).
- Determinism pins: MARKET_SIM_HIGHS_THREADS=1, MARKET_SIM_WARMSTART=1, MARKET_SIM_WARMSTART_XYEAR=0, MALLOC_ARENA_MAX=2, OMP_NUM_THREADS=1.

## Preflight / memory
```
INFO: before: memory ceiling 13.36 GiB (...), swap 0.0 GiB, 16.7 GiB free disk, 4 cpus
INFO: swap: added 10 GiB at /swapfile-marketsim — ceiling 13.36 + swap 10.0 = 23.4 GiB total
WARNING: ceiling+swap 23.4 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here.
INFO: year 2024 memory after release: resident=0.54 GB peak=12.27 GB
INFO: year 2025 memory after release: resident=0.61 GB peak=12.51 GB
INFO: memory peak: cgroup_peak_rss_gib=12.92, cgroup_peak_rss_plus_swap_gib=12.92, process_vmhwm_gib=12.51, process_vmswap_now_gib=0.00
```
Data steps: `hydrate_data.py --profile ercot` exit 0 (full clone, no-op); `regenerate_clean.py --solve-profile ERCOT` exit 0 under the project venv (system python3 lacked pandas → `uv sync`, the declared install route, then re-run; 5 datatypes incl. `uc-params` 19.4 s).

## Wall
| step | wall |
|---|---|
| capture total (2 years, sequential, 1 thread) | 34.6 min (23:35:35Z → 00:10:09Z) |
| 2024 P0 / P1 LP solve | 359.1 s / 343.9 s (objective 1526088186.2039 / 1761114222.6504) |
| 2025 P0 / P1 LP solve | 503.0 s / 433.9 s (objective 2745449035.3535 / 2942013394.5164) |

Fidelity oracle: `313 recorded flags replayed identically (0 HEAD-only meta keys); scenario_config 945 matched, 2 drifted` — drifted = `gas_price_override`, `weather_year`. Benign: the keeper's top-level run_config.json is its 2025 leg (3.52 / 2025), the golden's is its 2024 leg (2.19 / 2024); keeper `run_config_2024.json` = 2.19/2024 and `run_config_2025.json` = 3.52/2025 match the golden's per-year solves.

## metrics.json
Not comparable. The keeper's `metrics.json` is the rubric scoring output (`determination`, `criteria`, `caveats`, `grade_summary`, …), written at registration/scoring, not by the solve; `capture_keeper_goldens.py` at this SHA writes no `metrics.json`. Listed as absent golden-side, not as a data diff. If G-OFF requires it, scoring the golden is a parent-lane step (forbidden to this shard).

## Inventory (per year; both 2024 and 2025 compared)
| file | rows | numeric columns compared |
|---|---|---|
| adaptive_<year>.parquet | 8,760 | year, hour, s_model_day, p_hat_day, floor_usd |
| class_band_hourly_<year>.parquet | 849,720 | year, hour, mw, mw_oil |
| class_hourly_<year>.parquet | 131,400 | year, hour, mw |
| reserve_family_<year>.parquet | 52,560 | year, reserve_class, hour, dual, requirement_mw, held_mw, shortfall_mw |
| storage_<year>.parquet | 8,760 | year, hour, charge_mw, discharge_mw, soc_mwh, energy_cap_mwh |
| system_<year>.parquet | 61,320 | year, hour, price, slack, dump, demand, reserve_price, marginal_emission_rate, rtordpa_overlay, ordc_adder |
| unit_marginal_<year>.parquet | 21,129,120 | year, plant_code, hour, mw, cap_mw, mc, marginal |

Sort keys used (those present of): year, pass, unit_id, zone, zones, klass, band, family, reserve_class, tech, hour (stable mergesort, both sides).

## Comparison engine
`scripts/regression_gate.py` / `scripts/regression_check.py` compare only bundle-root `dispatch/<year>_P1.parquet`, `system.parquet`, `flows.parquet`, `storage.parquet`; the keeper is slim (none of those), so they cannot reach `hourly/`. One-off script below (shard scratchpad, not committed), run as:
```
uv run python golden_diff.py results/calibration/closeout_ercot_l1_span results/regression-goldens/ucmilp-off/ERCOT
```
Output:
```
files compared (14): adaptive_2024.parquet, adaptive_2025.parquet, class_band_hourly_2024.parquet, class_band_hourly_2025.parquet, class_hourly_2024.parquet, class_hourly_2025.parquet, reserve_family_2024.parquet, reserve_family_2025.parquet, storage_2024.parquet, storage_2025.parquet, system_2024.parquet, system_2025.parquet, unit_marginal_2024.parquet, unit_marginal_2025.parquet
numeric columns compared: 84
keeper-only files (35): adaptive_2019.parquet, adaptive_2020.parquet, adaptive_2021.parquet, adaptive_2022.parquet, adaptive_2023.parquet, class_band_hourly_2019.parquet, class_band_hourly_2020.parquet, class_band_hourly_2021.parquet, class_band_hourly_2022.parquet, class_band_hourly_2023.parquet, class_hourly_2019.parquet, class_hourly_2020.parquet, class_hourly_2021.parquet, class_hourly_2022.parquet, class_hourly_2023.parquet, reserve_family_2019.parquet, reserve_family_2020.parquet, reserve_family_2021.parquet, reserve_family_2022.parquet, reserve_family_2023.parquet, storage_2019.parquet, storage_2020.parquet, storage_2021.parquet, storage_2022.parquet, storage_2023.parquet, system_2019.parquet, system_2020.parquet, system_2021.parquet, system_2022.parquet, system_2023.parquet, unit_marginal_2019.parquet, unit_marginal_2020.parquet, unit_marginal_2021.parquet, unit_marginal_2022.parquet, unit_marginal_2023.parquet
golden-only files (4): network_2024.parquet, network_2025.parquet, unit_hourly_2024.parquet, unit_hourly_2025.parquet
FAIL metrics.json :: <missing> :: keeper=True golden=False
golden-diff: FAIL — 14 files, 84 numeric columns, 1 failing items, 35 keeper-only / 4 golden-only files
```
(The script's own last line says FAIL solely because it counts the absent golden-side metrics.json as a failing item; every data comparison passed.)

```python
"""One-off exact (atol=rtol=0) diff of hourly/ parquets + metrics.json: keeper vs golden.

Not committed; lives in the shard's scratchpad.
usage: python golden_diff.py <keeper_bundle> <golden_bundle>
"""

import glob
import json
import os
import sys

import numpy as np
import pandas as pd

KEYS = [
    "year",
    "pass",
    "unit_id",
    "zone",
    "zones",
    "klass",
    "band",
    "family",
    "reserve_class",
    "tech",
    "hour",
]

keeper, golden = sys.argv[1], sys.argv[2]
kf = {os.path.basename(p) for p in glob.glob(f"{keeper}/hourly/*.parquet")}
gf = {os.path.basename(p) for p in glob.glob(f"{golden}/hourly/*.parquet")}
both, only_k, only_g = sorted(kf & gf), sorted(kf - gf), sorted(gf - kf)
uc = [f for f in kf | gf if f.startswith("uc_")] + [
    os.path.relpath(p, d)
    for d in (keeper, golden)
    for p in glob.glob(f"{d}/**/uc_*", recursive=True)
]

n_files = n_num = 0
fails = []  # (file, column, detail)
for f in both:
    a = pd.read_parquet(f"{keeper}/hourly/{f}")
    b = pd.read_parquet(f"{golden}/hourly/{f}")
    n_files += 1
    if list(a.columns) != list(b.columns):
        fails.append(
            (f, "<columns>", f"keeper={list(a.columns)} golden={list(b.columns)}")
        )
        continue
    if len(a) != len(b):
        fails.append((f, "<rows>", f"keeper={len(a)} golden={len(b)}"))
        continue
    keys = [k for k in KEYS if k in a.columns]
    a = a.sort_values(keys, kind="mergesort").reset_index(drop=True)
    b = b.sort_values(keys, kind="mergesort").reset_index(drop=True)
    for c in a.columns:
        x, y = a[c], b[c]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            n_num += 1
            xv, yv = x.to_numpy(), y.to_numpy()
            if x.dtype != y.dtype:
                fails.append((f, c, f"dtype keeper={x.dtype} golden={y.dtype}"))
            if not np.array_equal(xv, yv, equal_nan=xv.dtype.kind == "f"):
                d = np.abs(xv.astype("float64") - yv.astype("float64"))
                fails.append(
                    (
                        f,
                        c,
                        f"max|Δ|={np.nanmax(d):.6g} n_diff={int(np.sum(~((d == 0) | (np.isnan(xv.astype(float)) & np.isnan(yv.astype(float))))))}",
                    )
                )
        else:
            if not np.array_equal(x.astype(str).to_numpy(), y.astype(str).to_numpy()):
                fails.append((f, c, "non-numeric values differ"))

mk, mg = f"{keeper}/metrics.json", f"{golden}/metrics.json"
if os.path.exists(mk) and os.path.exists(mg):
    jk, jg = json.load(open(mk)), json.load(open(mg))
    if jk != jg:
        fails.append(
            (
                "metrics.json",
                "<json>",
                f"unequal; top keys keeper-only={sorted(set(jk) - set(jg))} "
                f"golden-only={sorted(set(jg) - set(jk))} "
                f"shared-differing={sorted(k for k in set(jk) & set(jg) if jk[k] != jg[k])}",
            )
        )
else:
    fails.append(
        (
            "metrics.json",
            "<missing>",
            f"keeper={os.path.exists(mk)} golden={os.path.exists(mg)}",
        )
    )
if uc:
    fails.append(("uc_*", "<present>", ",".join(sorted(uc))))

print(f"files compared ({n_files}): {', '.join(both)}")
print(f"numeric columns compared: {n_num}")
print(f"keeper-only files ({len(only_k)}): {', '.join(only_k)}")
print(f"golden-only files ({len(only_g)}): {', '.join(only_g)}")
for f, c, d in fails:
    print(f"FAIL {f} :: {c} :: {d}")
print(
    f"golden-diff: {'FAIL' if fails else 'PASS'} — {n_files} files, {n_num} numeric columns, "
    f"{len(fails)} failing items, {len(only_k)} keeper-only / {len(only_g)} golden-only files"
)
```
