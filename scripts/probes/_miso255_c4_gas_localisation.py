"""miso-255 phase 0, item 4: WHERE IN TIME does MISO's C4 gas fit break down?

C4 is failing on MISO's held-out years in a way it does not in PJM
(2021 gas r = 0.864, NRMSE = 0.392 against 0.959-0.967 / 0.146-0.179 in the
training span). An hourly-correlation failure localises in TIME, which an
annual C1 miss cannot — so this is a handle ``pjm-h1`` did not have.

Rebuilds C4's own gas/coal series exactly as ``render_calibration_html`` does
at registration (``nyiso218_screen_gates._fuel_rows``): the model side is the
P1 hourly sum of the classes ``classes_for_fuel930`` rolls up to each EIA-930
fuel, from the bundle's committed ``hourly/class_hourly_<year>.parquet``; the
actual side is ``load_eia_hourly_benchmark``. **Zero LP.**

Decomposes the residual by calendar month and by decile of the actual system
load, and reports the correlation restricted to each slice.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.config.plant_taxonomy import classes_for_fuel930  # noqa: E402
from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402

T = 8760
BUNDLES = {
    2020: "miso251_tp2020",
    2021: "miso251_tp2021",
    2022: "miso251_screen2022",
    2023: "miso_fuelvintage_A",
    2024: "miso_fuelvintage_A",
    2025: "miso_fuelvintage_A",
}
YEARS = tuple(sorted(BUNDLES))


def series(year: int, fuel: str) -> tuple[np.ndarray, np.ndarray]:
    """``(model, actual)`` hourly MW for one EIA-930 fuel, C4's own construction."""
    ch = pd.read_parquet(
        REPO
        / "results/calibration"
        / BUNDLES[year]
        / "hourly"
        / f"class_hourly_{year}.parquet"
    )
    ch = ch[ch["pass"] == "P1"]
    piv = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    piv = piv.reindex(range(T)).fillna(0.0)
    model = np.zeros(T)
    for c in classes_for_fuel930(fuel):
        if c in piv.columns:
            model = model + piv[c].to_numpy(dtype=float)
    bench = load_eia_hourly_benchmark("MISO", year)
    actual = np.asarray(bench[fuel], dtype=float)[:T]
    return model, actual


def load_series(year: int) -> np.ndarray:
    """Actual hourly system load (EIA-930 demand) for the load-percentile cut."""
    bench = load_eia_hourly_benchmark("MISO", year)
    for key in ("demand", "load", "d"):
        if key in bench:
            return np.asarray(bench[key], dtype=float)[:T]
    # fall back to the sum of every generation series the benchmark carries
    tot = np.zeros(T)
    for k, v in bench.items():
        a = np.asarray(v, dtype=float)
        if a.size >= T and k not in ("demand", "load", "interchange", "d"):
            tot = tot + a[:T]
    return tot


def _fit(m: np.ndarray, a: np.ndarray) -> tuple[float, float]:
    if m.size < 3 or m.std() == 0.0 or a.std() == 0.0 or a.mean() == 0.0:
        return float("nan"), float("nan")
    return (
        float(np.corrcoef(m, a)[0, 1]),
        float(np.sqrt(((m - a) ** 2).mean()) / a.mean()),
    )


def _month_index() -> np.ndarray:
    days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    return np.repeat(np.arange(12), [d * 24 for d in days])[:T]


def main() -> None:
    mo = _month_index()
    for fuel in ("gas", "coal"):
        print("=" * 108)
        print(f"C4 {fuel.upper()} — whole year, then by MONTH")
        print("=" * 108)
        print(
            f"{'yr':>6s}{'r':>8s}{'nrmse':>8s}{'model':>9s}{'bench':>9s}"
            + "".join(f"{m:>7d}" for m in range(1, 13))
            + "   (per-month residual model-bench, TWh)"
        )
        for y in YEARS:
            m, a = series(y, fuel)
            r, nr = _fit(m, a)
            d = m - a
            per = [float(d[mo == k].sum()) / 1e6 for k in range(12)]
            print(
                f"{y:>6d}{r:>8.3f}{nr:>8.3f}{m.sum() / 1e6:>9.1f}{a.sum() / 1e6:>9.1f}"
                + "".join(f"{v:>7.1f}" for v in per)
            )
        print()
        print(f"{'yr':>6s}  per-month Pearson r")
        for y in YEARS:
            m, a = series(y, fuel)
            rs = [_fit(m[mo == k], a[mo == k])[0] for k in range(12)]
            print(f"{y:>6d}" + "".join(f"{v:>7.2f}" for v in rs))
        print()
        print(f"{'yr':>6s}  per-month NRMSE")
        for y in YEARS:
            m, a = series(y, fuel)
            rs = [_fit(m[mo == k], a[mo == k])[1] for k in range(12)]
            print(f"{y:>6d}" + "".join(f"{v:>7.2f}" for v in rs))
        print()

    print("=" * 108)
    print("C4 GAS by DECILE of the actual system load (D1 = lowest-load hours)")
    print("=" * 108)
    for y in YEARS:
        m, a = series(y, "gas")
        ld = load_series(y)
        q = np.quantile(ld, np.linspace(0, 1, 11))
        q[0] -= 1.0
        dec = np.clip(np.searchsorted(q, ld, side="left") - 1, 0, 9)
        print(
            f"\n--- {y} (whole-year r {_fit(m, a)[0]:.3f}, nrmse {_fit(m, a)[1]:.3f}) ---"
        )
        print(
            f"{'decile':>8s}{'hours':>7s}{'model GW':>10s}{'bench GW':>10s}"
            f"{'delta GW':>10s}{'delta TWh':>11s}{'r':>8s}{'nrmse':>8s}"
        )
        for k in range(10):
            sel = dec == k
            r, nr = _fit(m[sel], a[sel])
            print(
                f"{'D' + str(k + 1):>8s}{int(sel.sum()):>7d}"
                f"{m[sel].mean() / 1e3:>10.2f}{a[sel].mean() / 1e3:>10.2f}"
                f"{(m[sel] - a[sel]).mean() / 1e3:>10.2f}"
                f"{float((m[sel] - a[sel]).sum()) / 1e6:>11.2f}{r:>8.3f}{nr:>8.3f}"
            )


if __name__ == "__main__":
    main()
