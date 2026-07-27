"""Compare nyiso-87 arms on the metrics the charter names (shape + seam + price).

The scoring companion to ``scripts/calibration_verdict.py`` /
``scripts/legitimacy_diagnostics.py`` for the nyiso-87 commitment-drag lane. The
verdict script scores the rubric criteria; this reads the same committed bundle
sidecars and reports the things the rubric does NOT gate but the owner directive
is about:

* **Class diurnal shape** — hour-of-day mean MW per class, model vs the CEMS
  actual, with the D-1 statistics (``profile_r``, ``cv_ratio``). The directive's
  claim is that the model under-runs gas through the belly/peak; this is where
  that shows.
* **Interchange hour-of-day profile and within-month r** — the nyiso-86 §3
  method: the monthly pin is fine, the within-month allocation is inverted. If
  the bridge works, belly imports fall and the pinned monthly quota relocates
  peak-ward.
* **Internal diurnal price swing** — load-weighted hour-of-day max-minus-min,
  the nyiso-86 §3 measurement ($7.4/$8.2/$16.5 model vs $22.5/$25.1/$43.3 real).

Everything is read from committed artifacts: the arms' ``hourly/`` sidecars
(``class_hourly_<year>.parquet`` + ``system_<year>.parquet``, written by every
solve), the EIA-930 NYIS frame, and ``actual_lmp_hourly_NYISO.parquet``. No LP
is run and no measured series enters any model input — this is scoring-side
only (rule 14).

CLOCK: the committed hourly parquet is on the model's non-leap 8760
local-standard clock, which DROPS local-standard Feb 29 in a leap year. Row ->
UTC mapping therefore steps over that day (the ``nyiso85_tail_anatomy``
``_utc_of_hour`` construction, reproduced here).

Usage::

    python scripts/probes/nyiso87_arm_compare.py \
        --arms results/calibration/nyiso87_control results/calibration/nyiso87_a_floorsoff \
        --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# Row index at which the model's non-leap 8760 clock steps over local-standard
# Feb 29: 31 (Jan) + 28 (Feb) days of hours.
_LEAP_SKIP_INDEX: int = (31 + 28) * 24


def _is_leap(year: int) -> bool:
    """Return True when *year* is a Gregorian leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _utc_index(year: int, n_hours: int) -> pd.DatetimeIndex:
    """Return the UTC timestamps of chronological rows ``0..n_hours-1``.

    Row 0 is local-standard midnight Jan 1 = 05:00Z for NYISO (EST = UTC-5); in
    a leap year rows at/after :data:`_LEAP_SKIP_INDEX` step over the dropped
    local-standard Feb 29 (``nyiso85_tail_anatomy._utc_of_hour``).
    """
    k = np.arange(n_hours, dtype=int)
    if _is_leap(year):
        k = np.where(k >= _LEAP_SKIP_INDEX, k + 24, k)
    base = dt.datetime(year, 1, 1, 5, 0)
    return pd.DatetimeIndex([base + dt.timedelta(hours=int(h)) for h in k])


def _local_standard_hod(n_hours: int) -> np.ndarray:
    """Hour-of-day on the model's own local-standard clock (row % 24)."""
    return np.arange(n_hours, dtype=int) % 24


def load_class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """Return the arm's ``(hour x class)`` P1 dispatch MW matrix."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return df.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")


def load_system_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """Return the arm's per-zone P1 price/demand frame."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def load_weighted_price(sys_df: pd.DataFrame) -> pd.Series:
    """Return the load-weighted system price per hour."""
    g = sys_df.copy()
    g["wp"] = g["price"] * g["demand"]
    agg = g.groupby("hour").agg(wp=("wp", "sum"), d=("demand", "sum"))
    return agg["wp"] / agg["d"].replace(0.0, np.nan)


def diurnal_swing(price: pd.Series) -> float:
    """Return hour-of-day max-minus-min of the load-weighted price."""
    hod = price.groupby(price.index % 24).mean()
    return float(hod.max() - hod.min())


def model_net_imports(class_hourly: pd.DataFrame, sys_df: pd.DataFrame) -> pd.Series:
    """Return the model's hourly net imports (MW) as demand minus own generation.

    The class sidecar carries every dispatched class including the priced
    interchange pseudo-units; deriving net imports as ``demand - internal
    generation`` avoids depending on which label the import node carries in a
    given vintage, and matches the balance the LP actually solved (storage
    round-trip losses are the only residual, ~0.1% of load).
    """
    demand = sys_df.groupby("hour")["demand"].sum()
    internal = [c for c in class_hourly.columns if not _is_seam_class(c)]
    gen = class_hourly[internal].sum(axis=1)
    return (demand - gen).reindex(demand.index)


def _is_seam_class(name: str) -> bool:
    """True for the priced-interchange pseudo-unit classes."""
    n = str(name).lower()
    return "import" in n or "export" in n or n in ("interchange", "seam")


def actual_net_imports(year: int, n_hours: int) -> pd.Series | None:
    """Return measured EIA-930 NYIS net imports (MW) on the model's clock.

    Net imports = -(Total interchange), the nyiso-86 §3 convention. The 930
    hourly frame is ALREADY on the model's non-leap 8760 local-standard clock
    (``_eia_hourly_frame_filled``: "Row k is local hour k of the year, the same
    clock as the strict frame", leap Feb 29 dropped), so no realignment is
    needed — which is also why the :func:`_utc_index` helper is reserved for
    the month labelling, where a calendar date is genuinely required.

    Returns ``None`` when the frame is unavailable for the year.
    """
    try:
        from market_sim.data.eia930.frames import _eia_hourly_frame_filled

        frame = _eia_hourly_frame_filled("NYIS", year)
    except Exception:
        return None
    if frame is None or frame.empty or "Total interchange" not in frame.columns:
        return None
    ti = pd.to_numeric(frame["Total interchange"], errors="coerce").to_numpy(float)
    return pd.Series(-ti[:n_hours], index=np.arange(min(n_hours, ti.size)))


def hod_table(series: pd.Series, n_hours: int) -> pd.Series:
    """Return the hour-of-day mean of a row-indexed hourly series."""
    hod = _local_standard_hod(n_hours)
    return pd.Series(series.to_numpy(dtype=float)).groupby(hod).mean()


def within_month_r(model: pd.Series, actual: pd.Series, year: int) -> float:
    """Return the MEAN within-month hourly Pearson r (nyiso-86 §3).

    The annual r on a monthly-pinned series is dominated by month-level
    variation the reconciliation band supplies by construction; conditioning on
    month removes that and measures the within-month allocation, which is what
    the seam economics actually decide.
    """
    n = len(model)
    idx = _utc_index(year, n)
    month = pd.Series(idx.month, index=np.arange(n))
    rows = []
    for m, sel in month.groupby(month):
        a = model.reindex(sel.index).to_numpy(dtype=float)
        b = actual.reindex(sel.index).to_numpy(dtype=float)
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() > 24 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0:
            rows.append(float(np.corrcoef(a[ok], b[ok])[0, 1]))
    return float(np.mean(rows)) if rows else float("nan")


def compare(arms: list[Path], years: list[int], classes: list[str]) -> None:
    """Print the arm comparison tables."""
    for year in years:
        print(f"\n{'=' * 78}\n{year}\n{'=' * 78}")
        loaded = {}
        for arm in arms:
            try:
                ch = load_class_hourly(arm, year)
                sd = load_system_hourly(arm, year)
            except FileNotFoundError:
                print(f"  (skip {arm.name}: no {year} sidecar)")
                continue
            loaded[arm.name] = (ch, sd)
        if not loaded:
            continue
        n_hours = max(len(ch) for ch, _ in loaded.values())

        print("\n-- class annual TWh")
        rows = {}
        for name, (ch, _) in loaded.items():
            rows[name] = {c: ch[c].sum() / 1e6 for c in ch.columns if c in classes}
        print(pd.DataFrame(rows).round(3).to_string())

        print("\n-- load-weighted price: annual mean $/MWh, diurnal swing $/MWh")
        for name, (_, sd) in loaded.items():
            p = load_weighted_price(sd)
            print(f"  {name:34s} mean {p.mean():7.2f}   swing {diurnal_swing(p):6.2f}")

        print("\n-- net imports: annual TWh, hour-of-day mean MW, within-month r")
        act = actual_net_imports(year, n_hours)
        for name, (ch, sd) in loaded.items():
            ni = model_net_imports(ch, sd)
            hod = hod_table(ni, len(ni))
            wm = within_month_r(ni, act, year) if act is not None else float("nan")
            print(
                f"  {name:34s} {ni.sum() / 1e6:6.2f} TWh  "
                f"hod01-03 {hod.loc[1:3].mean():7.0f}  hod16-18 "
                f"{hod.loc[16:18].mean():7.0f}  within-month r {wm:+.3f}"
            )
        if act is not None:
            hod = hod_table(act, n_hours)
            print(
                f"  {'ACTUAL (EIA-930 NYIS)':34s} "
                f"{np.nansum(act.to_numpy()) / 1e6:6.2f} TWh  "
                f"hod01-03 {hod.loc[1:3].mean():7.0f}  hod16-18 "
                f"{hod.loc[16:18].mean():7.0f}"
            )

        print("\n-- gas-class hour-of-day mean MW (model)")
        for klass in classes:
            present = {n: ch for n, (ch, _) in loaded.items() if klass in ch.columns}
            if not present:
                continue
            print(f"  {klass}")
            for name, ch in present.items():
                hod = hod_table(ch[klass], len(ch))
                cells = " ".join(f"{hod.loc[h]:6.0f}" for h in (0, 4, 8, 12, 16, 18, 20))
                print(f"    {name:32s} h00/04/08/12/16/18/20: {cells}")


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arms", nargs="+", required=True, help="bundle directories")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--classes",
        nargs="+",
        default=["CC_REGULAR", "ST_GAS", "CT_PEAKER", "CC_CHP", "CT_CHP", "ST_CHP"],
    )
    args = ap.parse_args()
    compare([Path(a) for a in args.arms], args.years, args.classes)


if __name__ == "__main__":
    main()
