# ucmilp-golden-nyiso — NYISO keeper replay, UC gate OFF (GATESPEC §4 G-OFF)

- **HEAD:** ec758d64c03f6407fe382f6a52814f3028b71890 (hard stop 1 OK)
- **Keeper:** 2026-10-02-w0-nyiso → `results/calibration/w0_nyiso_span` (basis_sha 306f2c00b6268b791fb77c392c8d69a756959e76, composed from 5 single-year legs)
- **Gate:** `grep -c unit_commitment_milp scenarios.py` = 6; keeper run_config `unit_commitment_milp` = None (hard stop 4 OK)

## Result

```
golden-diff: FAIL — 30 hourly files compared (5 yrs × class_band_hourly, class_hourly, reserve_family, storage, system, unit_marginal), 175 numeric columns; all 12 failing columns are 2021 only:
  class_band_hourly_2021.mw 70.34 · class_band_hourly_2021.mw_oil 0.132 · class_hourly_2021.mw 70.34 · reserve_family_2021.held_mw 142.13
  storage_2021.charge_mw 10.97 · storage_2021.discharge_mw 9.00 · storage_2021.soc_mwh 12.68
  system_2021.marginal_emission_rate 0.793 · system_2021.price 2.72 $/MWh (10,544 zone-hours differ)
  unit_marginal_2021.marginal 1 (655 rows) · unit_marginal_2021.mc 0.0772 · unit_marginal_2021.mw 690
  2022–2025: every file, every column bit-identical. No uc_* file on either side.
  absent: golden-only = network_<yr> ×5, unit_hourly_<yr> ×5 (keeper is slim); metrics.json absent on golden side (solve writes no metrics.json) → not compared.
```

Not retried, not re-solved (per brief: the engine lane fixes the leak, never the golden).

## Zero-LP leads for the engine lane (not root-caused)

- Solve-surface fingerprint differs: keeper legs `cb770a26d18f570f` vs golden `1bde698e1ca4ad89`. The only rows that differ in `solve_surface.moved`: `GAS_OFFER_MARGIN_ANCHOR_BY_ISO` None → 2e0bbf78a1ae14de, `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE` None → 118ab6ce71c39f16 (may be newly declared rather than value-moved; unverified).
- `unit_marginal_2021.mc` differs (max 0.077 $/MWh, 1,464 rows) → P1 offer prices for 2021 changed, i.e. an input/offer-path difference, not only an LP tie.
- Keeper legs ran on platform fc-v51, golden on fc-v64; same python/highspy/numpy/scipy/pandas/pyarrow versions. 2022–2025 identical makes a platform cause unlikely.
- Keeper basis 306f2c00 is not in this clone's history (`git merge-base` cannot resolve it), so the code diff could not be audited here.

## Preflight / memory

- `prepare_solve_container.py`: `before: memory ceiling 13.36 GiB, swap 0.0 GiB, 16.7 GiB free disk, 4 cpus`; `swap: added 10 GiB … ceiling 13.36 + swap 10.0 = 23.4 GiB total` (warning: below 24 GiB target; irrelevant for NYISO)
- `memory peak: cgroup_peak_rss_gib=7.40, cgroup_peak_rss_plus_swap_gib=7.40, process_vmhwm_gib=7.02, process_vmswap_now_gib=0.00`
- Fidelity oracle: `313 recorded flags replayed identically (0 HEAD-only meta keys); scenario_config 947 matched, 0 drifted`
- Setup note: container had no venv; ran `uv sync` (the repo's documented install route) before `regenerate_clean.py` (exit 0, 8 datatypes incl. uc-params). Hydrate exit 0 (full clone, no-op).

## Wall per year (one container, sequential, threads=1, cold)

| year | P0 solve | P1 solve | total |
|---|---|---|---|
| 2021 | 160.6 s | 145.4 s | 351.8 s |
| 2022 | 159.6 s | 143.0 s | 350.8 s |
| 2023 | 122.6 s | 125.5 s | 289.8 s |
| 2024 | 126.7 s | 119.5 s | 287.0 s |
| 2025 | 120.9 s | 116.9 s | 278.5 s |

Capture wall 23:34:20 → 00:01:50 UTC (27.5 min).

## Commands

```
eval "$(python3 scripts/prepare_solve_container.py --emit-exports)"
export MARKET_SIM_HIGHS_THREADS=1 MARKET_SIM_WARMSTART=1 MARKET_SIM_WARMSTART_XYEAR=0
python3 scripts/capture_keeper_goldens.py --iso NYISO --stage-tag ucmilp-off --max-concurrency 1
python3 compare_hourly.py results/calibration/w0_nyiso_span results/regression-goldens/ucmilp-off/NYISO
```

`scripts/regression_gate.py` compares only bundle-root dispatch/system/flows/storage parquets (absent from the slim keeper), so it does not reach hourly/. A one-off comparator was used instead (scratchpad, not committed). Text:

```python
"""One-off exact (atol=rtol=0) comparison of hourly/ parquets + metrics.json."""
import glob, json, os, sys
import numpy as np, pandas as pd

KEEP, GOLD = sys.argv[1], sys.argv[2]
KEYS = ["year", "pass", "unit_id", "zone", "klass", "band", "tech", "family",
        "reserve_class", "hour"]

def names(d):
    return {os.path.relpath(p, d) for p in glob.glob(os.path.join(d, "hourly", "*.parquet"))}

k, g = names(KEEP), names(GOLD)
both = sorted(k & g)
uc = sorted(n for n in k | g if os.path.basename(n).startswith("uc_"))
fails, ncols, nfiles = [], 0, 0
for n in both:
    a, b = pd.read_parquet(os.path.join(KEEP, n)), pd.read_parquet(os.path.join(GOLD, n))
    if set(a.columns) != set(b.columns):
        fails.append(f"{n}: columns differ keeper-only={set(a.columns)-set(b.columns)} golden-only={set(b.columns)-set(a.columns)}")
    if len(a) != len(b):
        fails.append(f"{n}: rows {len(a)} vs {len(b)}"); continue
    keys = [c for c in KEYS if c in a.columns and c in b.columns]
    a = a.sort_values(keys, kind="mergesort").reset_index(drop=True)
    b = b.sort_values(keys, kind="mergesort").reset_index(drop=True)
    nfiles += 1
    for c in sorted(set(a.columns) & set(b.columns)):
        x, y = a[c], b[c]
        if pd.api.types.is_numeric_dtype(x) and not isinstance(x.dtype, pd.CategoricalDtype):
            ncols += 1
            xv, yv = x.to_numpy(), y.to_numpy()
            if xv.dtype != yv.dtype:
                fails.append(f"{n}:{c} dtype {xv.dtype} vs {yv.dtype}")
            if not np.array_equal(xv, yv, equal_nan=True):
                d = np.nanmax(np.abs(xv.astype("f8") - yv.astype("f8")))
                fails.append(f"{n}:{c} max|d|={d:.6g} n_diff={int((xv != yv).sum())}")
        else:
            if not (x.astype(str).to_numpy() == y.astype(str).to_numpy()).all():
                fails.append(f"{n}:{c} (key/label) differs")
mp = [os.path.join(d, "metrics.json") for d in (KEEP, GOLD)]
print("metrics.json present (keeper, golden):", [os.path.exists(x) for x in mp])
ma = json.load(open(mp[0])) if os.path.exists(mp[0]) else None
mb = json.load(open(mp[1])) if os.path.exists(mp[1]) else None
if ma is not None and mb is not None and ma != mb:
    diff = sorted(set(ma) ^ set(mb)) + [x for x in ma if x in mb and ma[x] != mb[x]]
    fails.append(f"metrics.json differs at keys {diff[:30]}")
if uc:
    fails.append(f"uc_* files present: {uc}")
print("compared:", both)
print("keeper-only:", sorted(k - g)); print("golden-only:", sorted(g - k))
for f in fails: print("FAIL", f)
print(f"golden-diff: {'FAIL' if fails or not both else 'PASS'} — {nfiles} files, {ncols} numeric columns, "
      f"{len(fails)} failures, absent: keeper-only={len(k-g)} golden-only={len(g-k)}")
```

## Full comparator output

```
metrics.json present (keeper, golden): [True, False]
compared: ['hourly/class_band_hourly_2021.parquet', 'hourly/class_band_hourly_2022.parquet', 'hourly/class_band_hourly_2023.parquet', 'hourly/class_band_hourly_2024.parquet', 'hourly/class_band_hourly_2025.parquet', 'hourly/class_hourly_2021.parquet', 'hourly/class_hourly_2022.parquet', 'hourly/class_hourly_2023.parquet', 'hourly/class_hourly_2024.parquet', 'hourly/class_hourly_2025.parquet', 'hourly/reserve_family_2021.parquet', 'hourly/reserve_family_2022.parquet', 'hourly/reserve_family_2023.parquet', 'hourly/reserve_family_2024.parquet', 'hourly/reserve_family_2025.parquet', 'hourly/storage_2021.parquet', 'hourly/storage_2022.parquet', 'hourly/storage_2023.parquet', 'hourly/storage_2024.parquet', 'hourly/storage_2025.parquet', 'hourly/system_2021.parquet', 'hourly/system_2022.parquet', 'hourly/system_2023.parquet', 'hourly/system_2024.parquet', 'hourly/system_2025.parquet', 'hourly/unit_marginal_2021.parquet', 'hourly/unit_marginal_2022.parquet', 'hourly/unit_marginal_2023.parquet', 'hourly/unit_marginal_2024.parquet', 'hourly/unit_marginal_2025.parquet']
keeper-only: []
golden-only: ['hourly/network_2021.parquet', 'hourly/network_2022.parquet', 'hourly/network_2023.parquet', 'hourly/network_2024.parquet', 'hourly/network_2025.parquet', 'hourly/unit_hourly_2021.parquet', 'hourly/unit_hourly_2022.parquet', 'hourly/unit_hourly_2023.parquet', 'hourly/unit_hourly_2024.parquet', 'hourly/unit_hourly_2025.parquet']
FAIL hourly/class_band_hourly_2021.parquet:mw max|d|=70.3383 n_diff=12464
FAIL hourly/class_band_hourly_2021.parquet:mw_oil max|d|=0.132011 n_diff=32
FAIL hourly/class_hourly_2021.parquet:mw max|d|=70.3383 n_diff=12254
FAIL hourly/reserve_family_2021.parquet:held_mw max|d|=142.13 n_diff=131
FAIL hourly/storage_2021.parquet:charge_mw max|d|=10.9654 n_diff=253
FAIL hourly/storage_2021.parquet:discharge_mw max|d|=8.99754 n_diff=395
FAIL hourly/storage_2021.parquet:soc_mwh max|d|=12.6797 n_diff=4725
FAIL hourly/system_2021.parquet:marginal_emission_rate max|d|=0.792666 n_diff=721
FAIL hourly/system_2021.parquet:price max|d|=2.72046 n_diff=10544
FAIL hourly/unit_marginal_2021.parquet:marginal max|d|=1 n_diff=655
FAIL hourly/unit_marginal_2021.parquet:mc max|d|=0.0772133 n_diff=1464
FAIL hourly/unit_marginal_2021.parquet:mw max|d|=690 n_diff=9470
golden-diff: FAIL — 30 files, 175 numeric columns, 12 failures, absent: keeper-only=0 golden-only=10
```

The golden bundle (results/regression-goldens/ucmilp-off/NYISO, incl. dispatch/ and unit_hourly) is gitignored and stays in this container only; it will not outlive the container.

## 2021 mc-diff summary

Zero-LP, from `hourly/unit_marginal_2021.parquet` on both sides (inner join on unit_id, zone, plant_group, fuel, hour; join: 8707440 matched rows). Unit list: `diff_2021_units.csv`.

- Distinct units with mc differing in any hour: **1**; differing unit-hours: **1464**; max |Δmc| 0.0772 $/MWh; median |Δmc| 0.0772
- Rows where cap_mw differs: 0
- Hour range of differing rows: 2880–4343 (distinct hours 1464)

plant_group (units):
```
plant_group
CT_CHP    1
```
fuel (units):
```
fuel
gas_ct    1
```
zone (units):
```
zone
NYC    1
```
Month histogram of differing unit-hours (hour//730):
```
hour
3     40
4    730
5    694
```
Clustering: 1 run(s) of differing hours (gap > 24 h splits a run). Largest runs (start–end hour, n hours):
```
2880-4343  n=1464
```
Top 15 units by n_hours_mc_differs:
```
                   unit_id zone plant_group   fuel    cap_mw  n_hours_mc_differs  first_hour  last_hour  mc_keeper_first  mc_golden_first  mc_keeper_median  mc_golden_median  max_abs_mc_diff
CT_CHP_NYC_p2493_committed  NYC      CT_CHP gas_ct 88.364594                1464        2880       4343        34.012131        33.934921         34.262108         34.259491         0.077213
```
Date range: hours 2880–4343 (0-indexed, 2021 non-leap) = **2021-05-01 00:00 through 2021-06-30 23:00**, exactly the May and June calendar months, contiguous. (The hour//730 proxy splits this into bins 3–5.) A single unit's P1 offer `mc` moved over exactly two calendar months, which looks like a monthly-resolved input (e.g. a monthly fuel/offer-anchor or monthly heat-rate/CEMS value for plant 2493). That is an inference, not verified.
