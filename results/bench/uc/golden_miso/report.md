# ucmilp-golden-miso — MISO off-gate replay at ec758d64 (GATESPEC §4 G-OFF)

**golden-diff: FAIL — partial: 6 of 7 years solved (2022 cut off at the 2 h background limit). 2019–2021 match exactly; 2023–2025 do not.**

| item | value |
|---|---|
| HEAD | `ec758d64c03f6407fe382f6a52814f3028b71890` (never moved) |
| keeper | 2026-10-03-closeout-miso-nuc-r → `results/calibration/closeout_miso_nuc_span` (`unit_commitment_milp` = None) |
| preflight before | `memory ceiling 13.36 GiB, swap 0.0 GiB, 16.7 GiB free disk, 4 cpus` |
| preflight swap | `added 10 GiB … ceiling 13.36 + swap 10.0 = 23.4 GiB total` (WARNING: below the 24 GiB target) |
| memory peak (train partition) | `cgroup_peak_rss_gib=13.36, cgroup_peak_rss_plus_swap_gib=16.50, process_vmhwm_gib=13.33` |
| determinism pins | MARKET_SIM_HIGHS_THREADS=1, MARKET_SIM_WARMSTART=1, MARKET_SIM_WARMSTART_XYEAR=0 (+ --emit-exports) |
| env setup | container had no venv: ran `uv sync` (the documented install route) before regenerate_clean; hydrate (full clone, no-op) exit 0; regenerate_clean --solve-profile MISO exit 0 (uc-params 40.6 s) |

## Capture

- `capture_keeper_goldens.py --iso MISO` **refused** (exit 2): `keepers/MISO.json declares a config_partition with no 'forward' role (roles present: ['train-2023-2025', 'validation-2020-2022'])`.
- Per the shard prompt, captured both members in ONE sequential run:
  `python3 scripts/capture_keeper_goldens.py --iso MISO__train-2023-2025 MISO__validation-2020-2022 --stage-tag ucmilp-off --max-concurrency 1`
- Train member fidelity: `fidelity OK: 313 recorded flags replayed identically (0 HEAD-only meta keys); scenario_config 946 matched, 3 drifted` (gas_offer_margin_anchor, gas_price_override, weather_year). The drift is against the keeper's top-level run_config.json, which carries the 2019 values; the keeper's run_config_2023.json matches the golden on all three (3.01868 / 2.54 / 2023), so it is benign.
- The process was killed by the harness's 7200 s background-task cap during 2022 (the validation member never wrote its bundle-root files, and no system_<year> sidecar for 2019–2021). Not restarted: about 65 min re-solve vs. about 25 min of budget left.

Wall per year (start 23:35:43Z; P1 parquet mtimes):

| year | finished | wall |
|---|---|---|
| 2023 | 23:46:53 | ~11.2 min (incl. fleet rebuild) |
| 2024 | 23:57:55 | ~11.0 min |
| 2025 | 00:11:39 | ~13.7 min |
| 2019 | 00:27:58 | ~16.3 min (incl. member-2 launch) |
| 2020 | 00:39:46 | ~11.8 min |
| 2021 | 00:57:02 | ~17.3 min |
| 2022 | — | killed at ~01:35:43 after ~38 min |

## Result

```
golden-diff: FAIL — 33 files compared, 165 numeric columns compared, class_band_hourly_2023.parquet:mw max|d|=847.358 n_diff=2300; class_band_hourly_2023.parquet:mw_oil max|d|=14.58 n_diff=1; class_band_hourly_2024.parquet:mw max|d|=797.49 n_diff=2463; class_band_hourly_2024.parquet:mw_oil max|d|=649.728 n_diff=7; class_band_hourly_2025.parquet:mw max|d|=2454.27 n_diff=3171; class_band_hourly_2025.parquet:mw_oil max|d|=1675 n_diff=15; class_hourly_2023.parquet:mw max|d|=864.264 n_diff=2173; class_hourly_2024.parquet:mw max|d|=797.49 n_diff=2187; class_hourly_2025.parquet:mw max|d|=2454.27 n_diff=2773; reserve_family_2023.parquet: shape/cols keeper (35040, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw'] vs golden (26280, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw']; reserve_family_2024.parquet: shape/cols keeper (35040, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw'] vs golden (26280, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw']; reserve_family_2025.parquet: shape/cols keeper (35040, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw'] vs golden (26280, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw']; storage_2023.parquet:charge_mw max|d|=505.651 n_diff=932; storage_2023.parquet:discharge_mw max|d|=663.238 n_diff=935; storage_2023.parquet:soc_mwh max|d|=1766.51 n_diff=3495; storage_2024.parquet:charge_mw max|d|=726.99 n_diff=1028; storage_2024.parquet:discharge_mw max|d|=458.984 n_diff=986; storage_2024.parquet:soc_mwh max|d|=848.356 n_diff=3871; storage_2025.parquet:charge_mw max|d|=1094.01 n_diff=1740; storage_2025.parquet:discharge_mw max|d|=800.325 n_diff=1088; storage_2025.parquet:soc_mwh max|d|=1461.9 n_diff=5329; system_2023.parquet:price max|d|=40.4257 n_diff=7044; system_2023.parquet:reserve_price max|d|=53.1994 n_diff=48; system_2023.parquet:marginal_emission_rate max|d|=1.10703 n_diff=5780; system_2024.parquet:price max|d|=305.44 n_diff=5587; system_2024.parquet:slack max|d|=3243.81 n_diff=10; system_2024.parquet:reserve_price max|d|=535.642 n_diff=136; system_2024.parquet:marginal_emission_rate max|d|=1.10495 n_diff=3194; system_2025.parquet:price max|d|=35.5564 n_diff=17643; system_2025.parquet:reserve_price max|d|=191.679 n_diff=200; system_2025.parquet:marginal_emission_rate max|d|=1.94612 n_diff=14753; unit_marginal_2023.parquet:mw max|d|=638.038 n_diff=3023; unit_marginal_2023.parquet:mc max|d|=41.6667 n_diff=102956; unit_marginal_2023.parquet:marginal max|d|=1 n_diff=1082; unit_marginal_2024.parquet:mw max|d|=869.261 n_diff=4100; unit_marginal_2024.parquet:mc max|d|=38.8889 n_diff=152056; unit_marginal_2024.parquet:marginal max|d|=1 n_diff=1195; unit_marginal_2025.parquet:mw max|d|=974.731 n_diff=7762; unit_marginal_2025.parquet:mc max|d|=42.3077 n_diff=237762; unit_marginal_2025.parquet:marginal max|d|=1 n_diff=1338, absent: keeper-only 9 ['class_band_hourly_2022.parquet', 'class_hourly_2022.parquet', 'reserve_family_2022.parquet', 'storage_2022.parquet', 'system_2019.parquet', 'system_2020.parquet', 'system_2021.parquet', 'system_2022.parquet', 'unit_marginal_2022.parquet'] / golden-only 12 ['network_2019.parquet', 'network_2020.parquet', 'network_2021.parquet', 'network_2023.parquet', 'network_2024.parquet', 'network_2025.parquet', 'unit_hourly_2019.parquet', 'unit_hourly_2020.parquet', 'unit_hourly_2021.parquet', 'unit_hourly_2023.parquet', 'unit_hourly_2024.parquet', 'unit_hourly_2025.parquet']
```

- **2019, 2020, 2021: every compared file is identical** (class_band_hourly, class_hourly, reserve_family, storage, unit_marginal; 0 diffs at atol = rtol = 0).
- **2023, 2024, 2025: FAIL in every file.** Worst max |Δ|: system price 40.4 / 305.4 / 35.6 $/MWh; unit_marginal mw 638 / 869 / 975 MW; class_hourly mw 864 / 797 / 2454 MW; system slack 3244 MW (2024).
- **Lead for the engine lane:** reserve_family_2023–2025 has 35040 rows in the keeper vs. 26280 in the golden. The golden is **missing the `miso_rbdc_regspin` family** (4 → 3 families). The train-member replay is not arming the RBDC reg/spin reserve family that the keeper carried in 2023–2025. That is either a recipe-reconstruction gap in the partition replay or a gate leak. It is not diagnosed here; per the prompt the engine lane fixes it, never the golden.
- uc_* files: **none on either side** (pass).
- metrics.json: **not compared.** The golden capture writes no metrics.json; the keeper's metrics.json is the calibration-scoring output (determination/criteria), not a solve artifact.

## File / column inventory

```
INVENTORY
class_band_hourly_2019.parquet  rows=648240  keys=['year', 'pass', 'klass', 'band', 'hour']  numeric_cols=4
class_band_hourly_2020.parquet  rows=648240  keys=['year', 'pass', 'klass', 'band', 'hour']  numeric_cols=4
class_band_hourly_2021.parquet  rows=648240  keys=['year', 'pass', 'klass', 'band', 'hour']  numeric_cols=4
class_band_hourly_2023.parquet  rows=648240  keys=['year', 'pass', 'klass', 'band', 'hour']  numeric_cols=4
class_band_hourly_2024.parquet  rows=648240  keys=['year', 'pass', 'klass', 'band', 'hour']  numeric_cols=4
class_band_hourly_2025.parquet  rows=648240  keys=['year', 'pass', 'klass', 'band', 'hour']  numeric_cols=4
class_hourly_2019.parquet  rows=148920  keys=['year', 'pass', 'klass', 'hour']  numeric_cols=3
class_hourly_2020.parquet  rows=148920  keys=['year', 'pass', 'klass', 'hour']  numeric_cols=3
class_hourly_2021.parquet  rows=148920  keys=['year', 'pass', 'klass', 'hour']  numeric_cols=3
class_hourly_2023.parquet  rows=148920  keys=['year', 'pass', 'klass', 'hour']  numeric_cols=3
class_hourly_2024.parquet  rows=148920  keys=['year', 'pass', 'klass', 'hour']  numeric_cols=3
class_hourly_2025.parquet  rows=148920  keys=['year', 'pass', 'klass', 'hour']  numeric_cols=3
reserve_family_2019.parquet  rows=26280  keys=['year', 'pass', 'family', 'reserve_class', 'zones', 'hour']  numeric_cols=7
reserve_family_2020.parquet  rows=26280  keys=['year', 'pass', 'family', 'reserve_class', 'zones', 'hour']  numeric_cols=7
reserve_family_2021.parquet  rows=26280  keys=['year', 'pass', 'family', 'reserve_class', 'zones', 'hour']  numeric_cols=7
storage_2019.parquet  rows=17520  keys=['year', 'pass', 'tech', 'hour']  numeric_cols=6
storage_2020.parquet  rows=17520  keys=['year', 'pass', 'tech', 'hour']  numeric_cols=6
storage_2021.parquet  rows=17520  keys=['year', 'pass', 'tech', 'hour']  numeric_cols=6
storage_2023.parquet  rows=17520  keys=['year', 'pass', 'tech', 'hour']  numeric_cols=6
storage_2024.parquet  rows=17520  keys=['year', 'pass', 'tech', 'hour']  numeric_cols=6
storage_2025.parquet  rows=17520  keys=['year', 'pass', 'tech', 'hour']  numeric_cols=6
system_2023.parquet  rows=70080  keys=['year', 'pass', 'zone', 'hour']  numeric_cols=8
system_2024.parquet  rows=70080  keys=['year', 'pass', 'zone', 'hour']  numeric_cols=8
system_2025.parquet  rows=70080  keys=['year', 'pass', 'zone', 'hour']  numeric_cols=8
unit_marginal_2019.parquet  rows=31054200  keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour']  numeric_cols=7
unit_marginal_2020.parquet  rows=30966600  keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour']  numeric_cols=7
unit_marginal_2021.parquet  rows=30677520  keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour']  numeric_cols=7
unit_marginal_2023.parquet  rows=30081840  keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour']  numeric_cols=7
unit_marginal_2024.parquet  rows=29845320  keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour']  numeric_cols=7
unit_marginal_2025.parquet  rows=29652600  keys=['year', 'pass', 'unit_id', 'plant_code', 'zone', 'hour']  numeric_cols=7
ONLY_KEEPER ['class_band_hourly_2022.parquet', 'class_hourly_2022.parquet', 'reserve_family_2022.parquet', 'storage_2022.parquet', 'system_2019.parquet', 'system_2020.parquet', 'system_2021.parquet', 'system_2022.parquet', 'unit_marginal_2022.parquet']
ONLY_GOLDEN ['network_2019.parquet', 'network_2020.parquet', 'network_2021.parquet', 'network_2023.parquet', 'network_2024.parquet', 'network_2025.parquet', 'unit_hourly_2019.parquet', 'unit_hourly_2020.parquet', 'unit_hourly_2021.parquet', 'unit_hourly_2023.parquet', 'unit_hourly_2024.parquet', 'unit_hourly_2025.parquet']
UC_FILES []
```

Failing columns (full list):

```
FAILS
class_band_hourly_2023.parquet:mw max|d|=847.358 n_diff=2300
class_band_hourly_2023.parquet:mw_oil max|d|=14.58 n_diff=1
class_band_hourly_2024.parquet:mw max|d|=797.49 n_diff=2463
class_band_hourly_2024.parquet:mw_oil max|d|=649.728 n_diff=7
class_band_hourly_2025.parquet:mw max|d|=2454.27 n_diff=3171
class_band_hourly_2025.parquet:mw_oil max|d|=1675 n_diff=15
class_hourly_2023.parquet:mw max|d|=864.264 n_diff=2173
class_hourly_2024.parquet:mw max|d|=797.49 n_diff=2187
class_hourly_2025.parquet:mw max|d|=2454.27 n_diff=2773
reserve_family_2023.parquet: shape/cols keeper (35040, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw'] vs golden (26280, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw']
reserve_family_2024.parquet: shape/cols keeper (35040, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw'] vs golden (26280, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw']
reserve_family_2025.parquet: shape/cols keeper (35040, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw'] vs golden (26280, 10) ['year', 'pass', 'family', 'reserve_class', 'zones', 'hour', 'dual', 'requirement_mw', 'held_mw', 'shortfall_mw']
storage_2023.parquet:charge_mw max|d|=505.651 n_diff=932
storage_2023.parquet:discharge_mw max|d|=663.238 n_diff=935
storage_2023.parquet:soc_mwh max|d|=1766.51 n_diff=3495
storage_2024.parquet:charge_mw max|d|=726.99 n_diff=1028
storage_2024.parquet:discharge_mw max|d|=458.984 n_diff=986
storage_2024.parquet:soc_mwh max|d|=848.356 n_diff=3871
storage_2025.parquet:charge_mw max|d|=1094.01 n_diff=1740
storage_2025.parquet:discharge_mw max|d|=800.325 n_diff=1088
storage_2025.parquet:soc_mwh max|d|=1461.9 n_diff=5329
system_2023.parquet:price max|d|=40.4257 n_diff=7044
system_2023.parquet:reserve_price max|d|=53.1994 n_diff=48
system_2023.parquet:marginal_emission_rate max|d|=1.10703 n_diff=5780
system_2024.parquet:price max|d|=305.44 n_diff=5587
system_2024.parquet:slack max|d|=3243.81 n_diff=10
system_2024.parquet:reserve_price max|d|=535.642 n_diff=136
system_2024.parquet:marginal_emission_rate max|d|=1.10495 n_diff=3194
system_2025.parquet:price max|d|=35.5564 n_diff=17643
system_2025.parquet:reserve_price max|d|=191.679 n_diff=200
system_2025.parquet:marginal_emission_rate max|d|=1.94612 n_diff=14753
unit_marginal_2023.parquet:mw max|d|=638.038 n_diff=3023
unit_marginal_2023.parquet:mc max|d|=41.6667 n_diff=102956
unit_marginal_2023.parquet:marginal max|d|=1 n_diff=1082
unit_marginal_2024.parquet:mw max|d|=869.261 n_diff=4100
unit_marginal_2024.parquet:mc max|d|=38.8889 n_diff=152056
unit_marginal_2024.parquet:marginal max|d|=1 n_diff=1195
unit_marginal_2025.parquet:mw max|d|=974.731 n_diff=7762
unit_marginal_2025.parquet:mc max|d|=42.3077 n_diff=237762
unit_marginal_2025.parquet:marginal max|d|=1 n_diff=1338
```

## Comparison

`scripts/regression_gate.py` / `regression_check.py` at this SHA compare dispatch/, system.parquet, flows.parquet, storage.parquet. They do not reach hourly/, and the keeper bundle is slim. So I used a one-off script, run from the session scratchpad (never under scripts/, not committed):

`python3 golden_diff.py results/calibration/closeout_miso_nuc_span results/regression-goldens/ucmilp-off/MISO__train-2023-2025 results/regression-goldens/ucmilp-off/MISO__validation-2020-2022`

```python
"""One-off exact (atol=rtol=0) comparison of hourly/ sidecars: keeper vs golden.

usage: golden_diff.py KEEPER_DIR GOLDEN_DIR [GOLDEN_DIR ...]
Golden dirs are searched in order for hourly/<name>; every parquet present in the
keeper's hourly/ and in some golden's hourly/ is compared column by column after
aligning both frames on the sort keys they carry. Never a float tolerance.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

KEY_ORDER = [
    "year",
    "pass",
    "family",
    "reserve_class",
    "zones",
    "tech",
    "unit_id",
    "plant_code",
    "zone",
    "klass",
    "band",
    "hour",
]


def align(df: pd.DataFrame) -> pd.DataFrame:
    keys = [k for k in KEY_ORDER if k in df.columns]
    out = df.copy()
    for c in out.columns:
        if isinstance(out[c].dtype, pd.CategoricalDtype):
            out[c] = out[c].astype(str)
    return out.sort_values(keys, kind="mergesort").reset_index(drop=True), keys


def main() -> int:
    keeper = Path(sys.argv[1])
    goldens = [Path(p) for p in sys.argv[2:]]
    kfiles = {p.name: p for p in sorted((keeper / "hourly").glob("*.parquet"))}
    gfiles = {}
    for g in goldens:
        for p in sorted((g / "hourly").glob("*.parquet")):
            gfiles.setdefault(p.name, p)
    both = sorted(set(kfiles) & set(gfiles))
    only_k = sorted(set(kfiles) - set(gfiles))
    only_g = sorted(set(gfiles) - set(kfiles))
    uc = [n for n in list(kfiles) + list(gfiles) if n.startswith("uc_")]
    n_num = 0
    fails = []
    inventory = []
    for name in both:
        a0, b0 = pd.read_parquet(kfiles[name]), pd.read_parquet(gfiles[name])
        keys = [k for k in KEY_ORDER if k in a0.columns]
        if a0.shape == b0.shape and list(a0.columns) == list(b0.columns) and all(
            np.array_equal(a0[k].astype(str).to_numpy() if isinstance(a0[k].dtype, pd.CategoricalDtype) else a0[k].to_numpy(),
                           b0[k].astype(str).to_numpy() if isinstance(b0[k].dtype, pd.CategoricalDtype) else b0[k].to_numpy())
            for k in keys):
            a, b = a0, b0  # already aligned row-for-row on every key column
            for c in keys:
                if isinstance(a[c].dtype, pd.CategoricalDtype):
                    a[c] = a[c].astype(str); b[c] = b[c].astype(str)
        else:
            a, keys = align(a0)
            b, _ = align(b0)
        del a0, b0
        if list(a.columns) != list(b.columns) or len(a) != len(b):
            fails.append(
                f"{name}: shape/cols keeper {a.shape} {list(a.columns)} vs golden {b.shape} {list(b.columns)}"
            )
            continue
        ncols = 0
        for c in a.columns:
            x, y = a[c].to_numpy(), b[c].to_numpy()
            if np.issubdtype(x.dtype, np.number):
                ncols += 1
                if not np.array_equal(x, y, equal_nan=True):
                    d = np.nanmax(np.abs(x.astype("float64") - y.astype("float64")))
                    nd = int(
                        (
                            ~(
                                (x == y)
                                | (
                                    np.isnan(x.astype(float))
                                    & np.isnan(y.astype(float))
                                )
                            )
                        ).sum()
                    )
                    fails.append(f"{name}:{c} max|d|={d:.6g} n_diff={nd}")
            elif not (x == y).all():
                fails.append(f"{name}:{c} (non-numeric key/label mismatch)")
        n_num += ncols
        inventory.append(f"{name}  rows={len(a)}  keys={keys}  numeric_cols={ncols}")
    print("INVENTORY")
    print("\n".join(inventory))
    print("ONLY_KEEPER", only_k)
    print("ONLY_GOLDEN", only_g)
    print("UC_FILES", uc)
    print("FAILS")
    print("\n".join(fails) or "(none)")
    status = "PASS" if not fails and not uc else "FAIL"
    print(
        f"golden-diff: {status} — {len(both)} files compared, {n_num} numeric columns compared, "
        f"{'; '.join(fails) if fails else 'no failing column'}, absent: keeper-only {len(only_k)} {only_k} / golden-only {len(only_g)} {only_g}"
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
```

Golden bundles stay under the gitignored results/regression-goldens/ucmilp-off/ in this container only (not pushed, per the shard rules) and do not survive it.
