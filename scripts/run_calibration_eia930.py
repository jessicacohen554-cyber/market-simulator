"""Calibration backcast diagnostic against EIA-930 hourly metered output.

Runs the dispatch model for one or more calibration years and prints a
side-by-side comparison against the EIA-930 ``ERCO hourly`` series:

  * Annual generation by fuel — model vs EIA-930 totals and percent diff.
  * Hourly dispatch fit (Pearson r and NRMSE) for coal and gas, the two
    fuels that move with merit order.
  * Monthly bias (model − EIA-930) as a percentage of EIA-930 generation,
    by fuel class. Useful for finding seasonal calibration drift.
  * Worst month × hour-of-day cells for coal and gas — the average
    residual (MW) per (month, hour-of-day) pair, so under-/over-dispatch
    by time of day jumps out. Highlights the worst 10 cells by absolute
    bias.

EIA-930 is preferred over EIA-923 because the monthly file lags by ~12
months and under-reports recent utility solar additions. The dispatch
fits the EIA-930 hourly profile by construction, so EIA-930 is the
right benchmark for tracking calibration accuracy of merit-order
dispatch.

Usage:
    python scripts/run_calibration_eia930.py --year 2023 2024
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data.eia_loader import (  # noqa: E402
    load_ercot_fossil_gen,
    load_ercot_renewable_gen,
)
from scripts.run_calibration import (  # noqa: E402
    _henry_hub_actual,
    _load_reference,
    run_year,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("calibration_eia930")

_MWH_PER_TWH: float = 1.0e6
_HOURS_PER_YEAR: int = 8760
_DAYS_IN_MONTH: tuple[int, ...] = (
    31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
)


def _hour_to_month(hours: int) -> np.ndarray:
    """Return ``(hours,)`` mapping each hour to a 1-based month."""
    month = np.empty(hours, dtype=int)
    h = 0
    for m, days in enumerate(_DAYS_IN_MONTH, start=1):
        end = min(h + days * 24, hours)
        month[h:end] = m
        h = end
        if h >= hours:
            break
    return month


def _hour_of_day(hours: int) -> np.ndarray:
    """Return ``(hours,)`` mapping each hour to 0-23 hour-of-day."""
    return np.arange(hours) % 24


def _sum_by_fuel(dispatch: np.ndarray, fuels: list[str]) -> dict[str, np.ndarray]:
    """Return ``{fuel: (T,)}`` hourly dispatch summed across generators."""
    out: dict[str, np.ndarray] = {}
    for g, fuel in enumerate(fuels):
        out.setdefault(fuel, np.zeros(dispatch.shape[1])).__iadd__(0)
        out[fuel] += dispatch[g, :]
    return out


def _pearson_r(model: np.ndarray, observed: np.ndarray) -> float:
    """Return the Pearson correlation of two equal-length series."""
    m = model - model.mean()
    o = observed - observed.mean()
    denom = float(np.sqrt((m * m).sum() * (o * o).sum()))
    return float((m * o).sum() / denom) if denom > 0.0 else float("nan")


def _nrmse(model: np.ndarray, observed: np.ndarray) -> float:
    """Return RMSE divided by mean observed — unitless dispersion metric."""
    rmse = float(np.sqrt(((model - observed) ** 2).mean()))
    denom = float(observed.mean())
    return rmse / denom if denom > 0.0 else float("nan")


def _build_model_hourly(
    result, fuels: list[str],
) -> dict[str, np.ndarray]:
    """Return modeled hourly generation (MW) by aggregated fuel class.

    Combines per-generator gas tranches into one ``"gas"`` series matching
    EIA-930's NG: NG aggregate (CC, CT and steam together).
    """
    gas_set = {"gas_cc", "gas_ct", "gas_st"}
    n_gen, T = result.dispatch.shape
    model: dict[str, np.ndarray] = {
        "gas": np.zeros(T),
        "coal": np.zeros(T),
        "nuclear": np.zeros(T),
    }
    for g in range(n_gen):
        fuel = fuels[g]
        if fuel in gas_set:
            model["gas"] += result.dispatch[g]
        elif fuel == "coal":
            model["coal"] += result.dispatch[g]
        elif fuel == "nuclear":
            model["nuclear"] += result.dispatch[g]
    # wind_dispatched / solar_dispatched are (n_zones, T); sum across zones.
    model["wind"] = np.asarray(result.wind_dispatched).sum(axis=0)
    model["solar"] = np.asarray(result.solar_dispatched).sum(axis=0)
    return model


def _print_annual_table(
    year: int, model_hourly: dict[str, np.ndarray],
    eia930: dict[str, np.ndarray],
) -> None:
    """Print model vs EIA-930 annual generation totals by fuel."""
    print(f"\n  Annual generation by fuel — {year} (vs EIA-930)")
    rows = [("fuel", "model TWh", "EIA-930 TWh", "diff %")]
    total_m = total_o = 0.0
    for fuel in ("coal", "gas", "wind", "solar"):
        m_twh = float(model_hourly[fuel].sum()) / _MWH_PER_TWH
        o_twh = float(eia930[fuel].sum()) / _MWH_PER_TWH if fuel in eia930 else 0.0
        total_m += m_twh
        total_o += o_twh
        diff = 100.0 * (m_twh - o_twh) / o_twh if o_twh else float("nan")
        rows.append((
            fuel, f"{m_twh:7.2f}", f"{o_twh:7.2f}", f"{diff:+6.1f}",
        ))
    nuclear_twh = float(model_hourly["nuclear"].sum()) / _MWH_PER_TWH
    rows.append((
        "nuclear (model only)", f"{nuclear_twh:7.2f}", "    —", "    —",
    ))
    rows.append((
        "TOTAL (excl nuclear)", f"{total_m:7.2f}", f"{total_o:7.2f}",
        f"{100.0 * (total_m - total_o) / total_o:+6.1f}",
    ))
    _print_table(rows)


def _print_table(rows: list[tuple]) -> None:
    """Print a column-aligned table from a header + rows tuple list."""
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


def _print_dispatch_fit(
    year: int,
    model_hourly: dict[str, np.ndarray],
    eia930: dict[str, np.ndarray],
) -> None:
    """Print hourly Pearson r and NRMSE for coal and gas."""
    print(f"\n  Hourly dispatch fit — {year} (model vs EIA-930)")
    rows = [("fuel", "Pearson r", " NRMSE", "model TWh", "EIA TWh")]
    for fuel in ("coal", "gas"):
        m = model_hourly[fuel]
        o = eia930[fuel]
        rows.append((
            fuel,
            f"{_pearson_r(m, o):.3f}",
            f"{_nrmse(m, o):.3f}",
            f"{m.sum() / _MWH_PER_TWH:7.2f}",
            f"{o.sum() / _MWH_PER_TWH:7.2f}",
        ))
    _print_table(rows)


def _print_monthly_bias(
    year: int,
    model_hourly: dict[str, np.ndarray],
    eia930: dict[str, np.ndarray],
) -> None:
    """Print monthly bias (model − EIA-930) as a percentage of EIA-930 gen."""
    print(f"\n  Monthly bias — {year}   (% of EIA-930 generation per month)")
    months = _hour_to_month(_HOURS_PER_YEAR)
    header = ("fuel",) + tuple(
        ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
    )
    rows: list[tuple] = [header]
    for fuel in ("coal", "gas", "wind", "solar"):
        m = model_hourly[fuel]
        o = eia930[fuel]
        cells: list[str] = []
        for mo in range(1, 13):
            mask = months == mo
            m_sum = float(m[mask].sum())
            o_sum = float(o[mask].sum())
            if o_sum > 0:
                cells.append(f"{100.0 * (m_sum - o_sum) / o_sum:+5.1f}")
            else:
                cells.append("   ·")
        rows.append((fuel,) + tuple(cells))
    _print_table(rows)


def _worst_cells(
    fuel: str,
    model: np.ndarray, observed: np.ndarray, top_n: int = 12,
) -> list[tuple[int, int, float, float, float]]:
    """Return the top-``top_n`` (month, hour-of-day) cells by |bias| in MW."""
    months = _hour_to_month(_HOURS_PER_YEAR)
    hods = _hour_of_day(_HOURS_PER_YEAR)
    grid_model = np.zeros((12, 24))
    grid_obs = np.zeros((12, 24))
    grid_count = np.zeros((12, 24), dtype=int)
    for t in range(_HOURS_PER_YEAR):
        m = months[t] - 1
        h = hods[t]
        grid_model[m, h] += model[t]
        grid_obs[m, h] += observed[t]
        grid_count[m, h] += 1
    avg_model = grid_model / grid_count
    avg_obs = grid_obs / grid_count
    bias = avg_model - avg_obs
    # Rank by absolute bias in MW.
    flat = sorted(
        ((abs(bias[m, h]), m + 1, h, bias[m, h], avg_model[m, h], avg_obs[m, h])
         for m in range(12) for h in range(24)),
        reverse=True,
    )
    return [(mo, hod, b, mw_m, mw_o) for _, mo, hod, b, mw_m, mw_o in flat[:top_n]]


def _print_worst_cells(year: int, fuel: str, cells) -> None:
    """Print the worst (month, hour) bias cells for one fuel."""
    print(
        f"\n  Worst {fuel.upper()} month × hour-of-day cells — {year}"
    )
    rows: list[tuple] = [
        ("month", "hour", "bias MW", "model MW", "EIA-930 MW", "bias %"),
    ]
    month_name = (
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    )
    for mo, hod, bias, mw_m, mw_o in cells:
        pct = 100.0 * bias / mw_o if mw_o > 0 else float("nan")
        rows.append((
            month_name[mo - 1],
            f"{hod:02d}",
            f"{bias:+8.0f}",
            f"{mw_m:8.0f}",
            f"{mw_o:8.0f}",
            f"{pct:+6.1f}",
        ))
    _print_table(rows)


def _print_monthly_hour_heatmap(
    year: int, fuel: str,
    model: np.ndarray, observed: np.ndarray,
) -> None:
    """Print a 12×24 heatmap of bias % (model − EIA-930) / EIA-930 per cell."""
    print(
        f"\n  {fuel.upper()} bias heatmap — {year}   "
        "(% of EIA-930 per (month, hour))"
    )
    months = _hour_to_month(_HOURS_PER_YEAR)
    hods = _hour_of_day(_HOURS_PER_YEAR)
    g_m = np.zeros((12, 24))
    g_o = np.zeros((12, 24))
    cnt = np.zeros((12, 24), dtype=int)
    for t in range(_HOURS_PER_YEAR):
        i = months[t] - 1
        j = hods[t]
        g_m[i, j] += model[t]
        g_o[i, j] += observed[t]
        cnt[i, j] += 1
    avg_m = g_m / cnt
    avg_o = g_o / cnt
    with np.errstate(divide="ignore", invalid="ignore"):
        bias_pct = np.where(avg_o > 0, 100.0 * (avg_m - avg_o) / avg_o, np.nan)
    month_name = (
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    )
    header = ("month",) + tuple(f"h{h:02d}" for h in range(24))
    rows: list[tuple] = [header]
    for i in range(12):
        cells = []
        for j in range(24):
            v = bias_pct[i, j]
            cells.append("   ·" if np.isnan(v) else f"{v:+4.0f}")
        rows.append((month_name[i],) + tuple(cells))
    _print_table(rows)


def _run_and_report(
    year: int, iso: str, hours: int, gas_price: float,
) -> None:
    """Run one calibration year and print the EIA-930 comparison report."""
    result, context, _, _ = run_year(
        year, iso, hours, gas_price, ttc_overrides={}
    )

    print(f"\n{'=' * 72}")
    print(f"  ERCOT {year} BACKCAST   (status: {result.status})")
    print(f"{'=' * 72}")

    fossil = load_ercot_fossil_gen(year)
    renewables = load_ercot_renewable_gen(year)
    if fossil is None or renewables is None:
        logger.error("EIA-930 ERCO hourly data missing for %d", year)
        return

    # Nuclear is steady but we still report it for completeness.
    eia930: dict[str, np.ndarray] = {
        "coal": fossil["coal"], "gas": fossil["gas"],
        "wind": renewables["wind"], "solar": renewables["solar"],
        "nuclear": np.zeros(_HOURS_PER_YEAR),
    }
    model_hourly = _build_model_hourly(result, list(context.fuel_types))

    _print_annual_table(year, model_hourly, eia930)
    _print_dispatch_fit(year, model_hourly, eia930)
    _print_monthly_bias(year, model_hourly, eia930)
    for fuel in ("coal", "gas"):
        cells = _worst_cells(fuel, model_hourly[fuel], eia930[fuel])
        _print_worst_cells(year, fuel, cells)
    for fuel in ("coal", "gas"):
        _print_monthly_hour_heatmap(
            year, fuel, model_hourly[fuel], eia930[fuel]
        )


def main() -> None:
    """Run every calibration year requested and print the comparison."""
    parser = argparse.ArgumentParser(
        description="Calibration backcast diagnostic vs EIA-930."
    )
    parser.add_argument(
        "--year", nargs="+", type=int, default=[2023, 2024],
        help="Calibration years to run (default 2023 2024).",
    )
    parser.add_argument("--iso", default="ERCOT")
    parser.add_argument("--hours", type=int, default=_HOURS_PER_YEAR)
    args = parser.parse_args()

    reference = _load_reference()
    for year in args.year:
        gas_price = _henry_hub_actual(reference, year)
        logger.info(
            "running %s %d (hours=%d, Henry Hub=$%.2f/MMBtu)",
            args.iso, year, args.hours, gas_price,
        )
        _run_and_report(year, args.iso, args.hours, gas_price)


if __name__ == "__main__":
    main()
