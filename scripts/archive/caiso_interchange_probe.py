"""CAISO interchange shape diagnostic — model diurnal vs EIA-930 measured.

Compares model net interchange (sum of import tranches + export sinks from
the dispatch parquet) against measured EIA-930 ``Total interchange`` for each
year, reporting:

* Diurnal (hour-of-day) mean MW profiles — model vs actual
* Annual TWh totals
* Duration RMSE (MW)
* Diurnal Pearson correlation
* Peak-to-trough amplitude (MW)
* Import-hours fraction (% of hours model/actual is net-importing)
* Per-corridor breakdown (WECC_PNW / WECC_DSW) when per-hub data is available

Usage::

    .venv/bin/python scripts/archive/caiso_interchange_probe.py BUNDLE_DIR \\
        [--year 2023 2024 2025] [--pass P1] [--compare BUNDLE2 ...]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr


def _load_eia930_interchange(year: int) -> np.ndarray | None:
    """Load EIA-930 actual net import (MW) for CAISO, 8760 hours.

    EIA sign: positive = export, negative = import.
    Returns NEGATIVE of that → positive = net import into CAISO.
    """
    path = Path("data/raw/eia-930-hourly/CISO hourly.parquet")
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    lt = pd.to_datetime(df["Local time"])
    mask = lt.dt.year == year
    if year % 4 == 0:
        mask = mask & ~((lt.dt.month == 2) & (lt.dt.day == 29))
    sub = df.loc[mask].copy()
    if len(sub) < 8760:
        return None
    sub = sub.head(8760)
    ti = pd.to_numeric(sub["Total interchange"], errors="coerce")
    net_import = -ti.interpolate().bfill().ffill().to_numpy(dtype=float)
    return net_import


def _load_model_interchange(
    bundle: Path, year: int, pass_label: str
) -> np.ndarray | None:
    """Load model net interchange from dispatch parquet.

    Import tranches (fuel='import', mw>0) and export sinks (fuel='import', mw<0)
    are summed per hour. The total is net import (positive = importing).
    """
    path = bundle / "dispatch" / f"{year}_{pass_label}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    imp = df[df["fuel"] == "import"]
    if imp.empty:
        return None
    net = imp.groupby("hour")["mw"].sum().sort_index().to_numpy(dtype=float)
    if len(net) < 8760:
        return None
    return net[:8760]


def _load_model_corridor_interchange(
    bundle: Path, year: int, pass_label: str
) -> dict[str, np.ndarray]:
    """Load per-corridor model interchange."""
    path = bundle / "dispatch" / f"{year}_{pass_label}.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    imp = df[df["fuel"] == "import"]
    if imp.empty:
        return {}
    out = {}
    for zone in imp["zone"].unique():
        z = str(zone)
        if z.startswith("WECC"):
            corridor = imp[imp["zone"] == zone]
            net = (
                corridor.groupby("hour")["mw"].sum().sort_index().to_numpy(dtype=float)
            )
            if len(net) >= 8760:
                out[z] = net[:8760]
    return out


def _diurnal_mean(arr: np.ndarray) -> np.ndarray:
    """Return mean by hour-of-day (24 values)."""
    return arr.reshape(-1, 24).mean(axis=0) if len(arr) == 8760 else np.full(24, np.nan)


def _metrics(model: np.ndarray, actual: np.ndarray) -> dict:
    """Compute interchange shape metrics."""
    twh_model = model.sum() / 1e6
    twh_actual = actual.sum() / 1e6

    rmse = np.sqrt(np.mean((model - actual) ** 2))

    d_model = _diurnal_mean(model)
    d_actual = _diurnal_mean(actual)
    corr, _ = pearsonr(d_model, d_actual)

    pk_tr_model = d_model.max() - d_model.min()
    pk_tr_actual = d_actual.max() - d_actual.min()

    import_hrs_model = (model > 0).sum() / len(model) * 100
    import_hrs_actual = (actual > 0).sum() / len(actual) * 100

    return {
        "twh_model": twh_model,
        "twh_actual": twh_actual,
        "twh_err": twh_model - twh_actual,
        "dur_rmse_mw": rmse,
        "diurnal_corr": corr,
        "pk_tr_model": pk_tr_model,
        "pk_tr_actual": pk_tr_actual,
        "import_hrs_model": import_hrs_model,
        "import_hrs_actual": import_hrs_actual,
    }


def _print_metrics_table(all_metrics: dict[int, dict], label: str = ""):
    """Print a formatted metrics table."""
    if label:
        print(f"\n{'=' * 80}")
        print(f"  {label}")
        print(f"{'=' * 80}")
    print(
        f"{'Year':>4}  {'Act TWh':>8}  {'Mdl TWh':>8}  {'Err TWh':>8}  "
        f"{'Dur RMSE':>8}  {'Diurn r':>7}  "
        f"{'Mdl pk→tr':>9}  {'Act pk→tr':>9}  "
        f"{'Imp hrs mdl':>11}  {'Imp hrs act':>11}"
    )
    print("-" * 110)
    for yr in sorted(all_metrics):
        m = all_metrics[yr]
        print(
            f"{yr:>4}  {m['twh_actual']:>8.2f}  {m['twh_model']:>8.2f}  "
            f"{m['twh_err']:>+8.2f}  {m['dur_rmse_mw']:>7.0f} MW  "
            f"{m['diurnal_corr']:>+7.2f}  "
            f"{m['pk_tr_model']:>8.0f} MW  {m['pk_tr_actual']:>8.0f} MW  "
            f"{m['import_hrs_model']:>10.1f}%  {m['import_hrs_actual']:>10.1f}%"
        )


def _print_diurnal_profile(year: int, model: np.ndarray, actual: np.ndarray):
    """Print hour-of-day diurnal profile."""
    d_model = _diurnal_mean(model)
    d_actual = _diurnal_mean(actual)
    print(f"\n  Diurnal profile {year} (mean MW, positive = net import)")
    print(f"  {'Hour':>4}  {'Model':>8}  {'Actual':>8}  {'Delta':>8}")
    print(f"  {'-' * 36}")
    for h in range(24):
        print(
            f"  {h:>4}  {d_model[h]:>8.0f}  {d_actual[h]:>8.0f}  "
            f"{d_model[h] - d_actual[h]:>+8.0f}"
        )


def _print_corridor_breakdown(corridors: dict[str, np.ndarray], year: int):
    """Print per-corridor interchange stats."""
    if not corridors:
        return
    print(f"\n  Per-corridor breakdown {year}:")
    print(
        f"  {'Corridor':>12}  {'TWh':>7}  {'Mean MW':>8}  {'Pk MW':>8}  {'Tr MW':>8}  {'Pk→Tr':>7}  {'Imp hrs':>7}"
    )
    print(f"  {'-' * 66}")
    for zone in sorted(corridors):
        arr = corridors[zone]
        twh = arr.sum() / 1e6
        mean = arr.mean()
        diurn = _diurnal_mean(arr)
        pk = diurn.max()
        tr = diurn.min()
        imp_pct = (arr > 0).sum() / len(arr) * 100
        print(
            f"  {zone:>12}  {twh:>+7.2f}  {mean:>+8.0f}  {pk:>+8.0f}  "
            f"{tr:>+8.0f}  {pk - tr:>6.0f}  {imp_pct:>6.1f}%"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Calibration bundle directory")
    parser.add_argument("--year", type=int, nargs="+", default=[2023, 2024, 2025])
    parser.add_argument(
        "--pass", dest="pass_label", default="P1", help="Pass label (P1 or P2)"
    )
    parser.add_argument(
        "--compare", type=Path, nargs="+", help="Additional bundles to compare"
    )
    parser.add_argument(
        "--diurnal", action="store_true", help="Print full diurnal profiles"
    )
    args = parser.parse_args()

    bundles = [(args.bundle, args.bundle.name)]
    if args.compare:
        for b in args.compare:
            bundles.append((b, b.name))

    for bundle, label in bundles:
        all_metrics = {}
        for yr in args.year:
            actual = _load_eia930_interchange(yr)
            model = _load_model_interchange(bundle, yr, args.pass_label)
            if actual is None:
                print(f"  SKIP {yr}: no EIA-930 data", file=sys.stderr)
                continue
            if model is None:
                print(f"  SKIP {yr}: no dispatch parquet at {bundle}", file=sys.stderr)
                continue
            all_metrics[yr] = _metrics(model, actual)

            if args.diurnal:
                _print_diurnal_profile(yr, model, actual)

            corridors = _load_model_corridor_interchange(bundle, yr, args.pass_label)
            if corridors:
                _print_corridor_breakdown(corridors, yr)

        if all_metrics:
            _print_metrics_table(all_metrics, label=label)

    return 0


if __name__ == "__main__":
    sys.exit(main())
