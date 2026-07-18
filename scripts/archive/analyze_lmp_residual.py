"""Localize the model-vs-actual LMP residual with the hourly price overlay.

Compares a calibration bundle's hourly system price (the dispatch LP's
energy-balance duals, demand-weighted across zones — the dashboard's
average-LMP convention) against the actual hub-mean hourly LMP series
produced by ``scripts/data/derive_actual_lmp.py``
(``data/raw/_validation-source/actual_lmp_hourly_{ISO}.parquet``).

The point is diagnosis, not a score: before reaching for structural fixes
(reserves/ORDC, scarcity adders) the monthly residual must be localized.
A gap concentrated in the top duration-curve percentiles points at missing
scarcity pricing; a broad flat offset across mid-curve hours points at the
offer curves or fuel prices instead. Per focus month-window the report
breaks the residual down three ways:

  * duration curve — model vs actual percentiles, full year and focus window;
  * hour-of-day — is the gap an evening-ramp / afternoon-peak shape?
  * actual-price band — which actual price regimes carry the residual, with
    each band's share of the total $.h gap.

With ``--with-scarcity`` the model series becomes the ORDC-overlaid price
(energy LMP + scarcity adder) from the bundle's ``scarcity.parquet``
(scripts/data/derive_ordc_overlay.py); the energy-only series — which the
volume calibration gates are defined on — is what you get without the
flag.

Usage:
    python scripts/archive/analyze_lmp_residual.py RUN_DIR [RUN_DIR ...]
        [--months 7 8] [--years 2023 2024] [--out FILE.md]
        [--with-scarcity]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
# Validation source (actual_lmp_hourly_{ISO}.parquet) relocated from the old
# inputs/calibration tree to data/raw/_validation-source (paths.CALIBRATION_DIR).
CAL_DIR = REPO / "data" / "raw" / "_validation-source"

# Fixed non-leap dispatch calendar (matches market_sim.data.campd).
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = tuple(int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(13))
_MONTH_NAMES = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

# Duration-curve percentile levels reported in the overlay tables.
_PCT_LEVELS = (50, 75, 90, 95, 99)

# Actual-price band edges ($/MWh) for the residual localization table.
_BAND_EDGES = (-np.inf, 0, 25, 50, 75, 100, 200, np.inf)


def _month_of_hour(hours: np.ndarray) -> np.ndarray:
    """Map non-leap hour-of-year indices to 1-12 months."""
    return np.searchsorted(_MONTH_START_HOUR, hours, side="right").clip(1, 12)


def _model_system_price(bundle: Path) -> pd.DataFrame:
    """Demand-weighted hourly system price per year from ``system.parquet``.

    Uses the P1 pass when present (the dashboard's convention). Returns a
    frame with columns ``year``, ``hour``, ``price``.
    """
    sy = pd.read_parquet(bundle / "system.parquet")
    if "pass" in sy.columns and (sy["pass"] == "P1").any():
        sy = sy[sy["pass"] == "P1"]
    sy = sy.assign(pd_=sy["price"] * sy["demand"])
    g = sy.groupby(["year", "hour"], observed=True).agg(
        pd_=("pd_", "sum"), d=("demand", "sum"), p=("price", "mean")
    )
    price = np.where(g["d"] > 0, g["pd_"] / g["d"], g["p"])
    return g.assign(price=price).reset_index()[["year", "hour", "price"]]


def _actual_hourly(iso: str) -> pd.DataFrame:
    """Load the actual hub-mean hourly series for ``iso`` (must exist)."""
    p = CAL_DIR / f"actual_lmp_hourly_{iso}.parquet"
    if not p.exists():
        raise SystemExit(f"missing {p} — run scripts/data/derive_actual_lmp.py first")
    return pd.read_parquet(p)


def _pct_row(values: np.ndarray) -> list[float]:
    """Mean + percentile levels + max of a price series (NaNs ignored)."""
    return (
        [float(np.nanmean(values))]
        + [float(np.nanpercentile(values, p)) for p in _PCT_LEVELS]
        + [float(np.nanmax(values))]
    )


def _md_table(header: list[str], rows: list[list]) -> list[str]:
    """Render a small markdown table; floats to 2 decimals."""

    def cell(v):
        if v is None:
            return "—"
        if isinstance(v, float):
            return f"{v:,.2f}"
        return str(v)

    out = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    out += ["| " + " | ".join(cell(v) for v in r) + " |" for r in rows]
    return out


def _duration_section(model: np.ndarray, actual: np.ndarray, label: str) -> list[str]:
    """Duration-curve overlay table (model vs actual RT) for one window."""
    header = ["series", "mean"] + [f"p{p}" for p in _PCT_LEVELS] + ["max"]
    m, a = _pct_row(model), _pct_row(actual)
    rows = [
        ["model"] + m,
        ["actual RT"] + a,
        ["residual"] + [x - y for x, y in zip(m, a)],
    ]
    return [f"**Duration curve — {label}**", ""] + _md_table(header, rows)


def _hour_of_day_section(
    model: np.ndarray, actual: np.ndarray, hours: np.ndarray
) -> list[str]:
    """Mean residual by hour-of-day over the focus window."""
    hod = hours % 24
    rows = []
    for h in range(24):
        sel = hod == h
        ok = sel & np.isfinite(actual) & np.isfinite(model)
        if not ok.any():
            continue
        am, mm = float(actual[ok].mean()), float(model[ok].mean())
        rows.append([h, mm, am, mm - am])
    return ["**Residual by hour-of-day (focus window)**", ""] + _md_table(
        ["hour", "model", "actual RT", "residual"], rows
    )


def _band_section(model: np.ndarray, actual: np.ndarray) -> list[str]:
    """Residual by actual-price band, with each band's share of the $.h gap."""
    ok = np.isfinite(actual) & np.isfinite(model)
    model, actual = model[ok], actual[ok]
    total_gap = float((model - actual).sum())
    rows = []
    for lo, hi in zip(_BAND_EDGES[:-1], _BAND_EDGES[1:]):
        sel = (actual >= lo) & (actual < hi)
        if not sel.any():
            continue
        gap = float((model[sel] - actual[sel]).sum())
        share = gap / total_gap if total_gap else np.nan
        lab = (
            f"<{hi:g}"
            if not np.isfinite(lo)
            else f">={lo:g}"
            if not np.isfinite(hi)
            else f"{lo:g}-{hi:g}"
        )
        rows.append(
            [
                lab,
                int(sel.sum()),
                float(actual[sel].mean()),
                float(model[sel].mean()),
                float((model[sel] - actual[sel]).mean()),
                f"{share:+.0%}",
            ]
        )
    rows.append(
        [
            "total",
            len(actual),
            float(actual.mean()),
            float(model.mean()),
            float((model - actual).mean()),
            "100%",
        ]
    )
    return [
        "**Residual by actual-price band (focus window)** — `share` is "
        "the band's share of the total $·h gap",
        "",
    ] + _md_table(
        ["actual $/MWh", "hours", "actual RT", "model", "residual", "share"], rows
    )


def _threshold_section(model: np.ndarray, actual: np.ndarray) -> list[str]:
    """High-price hour counts, model vs actual (focus window)."""
    rows = [
        [f">${t}", int(np.nansum(actual > t)), int(np.nansum(model > t))]
        for t in (75, 100, 200, 500)
    ]
    return ["**High-price hours (focus window)**", ""] + _md_table(
        ["threshold", "actual RT", "model"], rows
    )


def _year_report(
    year: int, model_y: pd.DataFrame, act_y: pd.DataFrame, months: list[int]
) -> list[str]:
    """Full markdown section for one bundle-year."""
    T = len(act_y)
    model = np.full(T, np.nan)
    model[model_y["hour"].to_numpy()] = model_y["price"].to_numpy(float)
    rt = act_y["rt"].to_numpy(float)
    da = act_y["da"].to_numpy(float)
    hours = act_y["hour"].to_numpy()
    mon = _month_of_hour(hours)
    focus = np.isin(mon, months)
    win = "/".join(_MONTH_NAMES[m - 1] for m in months)

    lines = [f"### {year}", ""]
    ok = np.isfinite(model) & np.isfinite(rt)
    lines += [
        f"- annual mean: model **${np.nanmean(model[ok]):.2f}** vs actual "
        f"RT **${np.nanmean(rt[ok]):.2f}** / DA ${np.nanmean(da[ok]):.2f} "
        f"(residual vs RT **{np.nanmean(model[ok] - rt[ok]):+.2f}**)",
        f"- {win} mean: model **${np.nanmean(model[focus]):.2f}** vs actual "
        f"RT **${np.nanmean(rt[focus]):.2f}** (residual "
        f"**{np.nanmean((model - rt)[focus]):+.2f}**)",
        "",
    ]
    rows = []
    for m in range(1, 13):
        sel = (mon == m) & np.isfinite(model) & np.isfinite(rt)
        if not sel.any():
            continue
        mm, am = float(model[sel].mean()), float(rt[sel].mean())
        rows.append([_MONTH_NAMES[m - 1], mm, am, mm - am])
    lines += ["**Monthly mean LMP (model vs actual RT)**", ""] + _md_table(
        ["month", "model", "actual RT", "residual"], rows
    )
    lines += [""] + _duration_section(model, rt, f"{year} full year") + [""]
    lines += _duration_section(model[focus], rt[focus], f"{year} {win}") + [""]
    lines += _hour_of_day_section(model[focus], rt[focus], hours[focus]) + [""]
    lines += _band_section(model[focus], rt[focus]) + [""]
    lines += _threshold_section(model[focus], rt[focus]) + [""]
    return lines


def _apply_scarcity(model: pd.DataFrame, bundle: Path) -> pd.DataFrame:
    """Add the bundle's ORDC scarcity adder to the model price series."""
    p = bundle / "scarcity.parquet"
    if not p.exists():
        raise SystemExit(f"missing {p} — run scripts/data/derive_ordc_overlay.py first")
    sc = pd.read_parquet(p)[["year", "hour", "scarcity_adder"]]
    out = model.merge(sc, on=["year", "hour"], how="left")
    out["price"] = out["price"] + out["scarcity_adder"].fillna(0.0)
    return out[["year", "hour", "price"]]


def report(
    bundles: list[Path],
    months: list[int],
    years: list[int] | None,
    with_scarcity: bool = False,
) -> str:
    """Build the markdown residual report across ``bundles``."""
    title = "# Hourly LMP residual localization"
    if with_scarcity:
        title += " — ORDC scarcity overlay applied"
    lines = [title, ""]
    for bundle in bundles:
        meta = json.loads((bundle / "meta.json").read_text())
        iso = meta.get("iso", "ERCOT")
        actual = _actual_hourly(iso)
        model = _model_system_price(bundle)
        if with_scarcity:
            model = _apply_scarcity(model, bundle)
        got_years = sorted(set(model["year"]).intersection(actual["year"]))
        if years:
            got_years = [y for y in got_years if y in years]
        lines += [f"## {bundle.name} ({iso})", ""]
        for y in got_years:
            lines += _year_report(
                y,
                model[model["year"] == y],
                actual[actual["year"] == y].sort_values("hour"),
                months,
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "bundles",
        nargs="+",
        type=Path,
        help="calibration bundle directories (with system.parquet)",
    )
    ap.add_argument(
        "--months",
        nargs="+",
        type=int,
        default=[7, 8],
        help="focus window months, 1-12 (default Jul/Aug)",
    )
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write the markdown report here (default: stdout)",
    )
    ap.add_argument(
        "--with-scarcity",
        action="store_true",
        help="overlay the ORDC scarcity adder (scarcity.parquet)"
        " on the model price series",
    )
    args = ap.parse_args()
    md = report(args.bundles, args.months, args.years, args.with_scarcity)
    if args.out:
        args.out.write_text(md)
        print(f"wrote {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
