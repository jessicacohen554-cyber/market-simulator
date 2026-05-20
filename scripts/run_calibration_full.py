"""Comprehensive calibration backcast diagnostic.

Runs the dispatch model for one or more calibration years and reports:

  * Annual generation by fossil class — model vs EIA-923 (Page 1) totals,
    with the model classes broken out: CC_CHP, CC_REGULAR, CT_CHP,
    CT_PEAKER, ST_GAS+ST_CHP, COAL. Solar uses EIA-930 because EIA-923's
    monthly file lags and under-reports recent utility solar additions.
    Wind and nuclear use EIA-923.
  * Monthly +/- % by fuel class against the same benchmark mix.
  * Hourly Pearson r and NRMSE against EIA-930 for gas, coal, solar,
    wind and nuclear — the same chronological clock the dispatch fits.
  * Plant-level annual generation for a curated set of representative
    plants (Colorado Bend II, Wolf Hollow II, Handley, Deer Park,
    Baytown, Hidalgo, plus a coal plant and several large CT peakers),
    model vs EIA-923 Page 1.

Usage:
    python scripts/run_calibration_full.py --year 2023 2024
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data.eia923 import (  # noqa: E402
    load_monthly_generation,
    monthly_netgen_columns,
)
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
logger = logging.getLogger("calibration_full")

_MWH_PER_TWH: float = 1.0e6
_HOURS_PER_YEAR: int = 8760
_DAYS_IN_MONTH: tuple[int, ...] = (
    31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
)
_MONTH_NAMES: tuple[str, ...] = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

# Fuel codes that EIA-923 reports for coal-class units.
_COAL_FUELS: frozenset[str] = frozenset(
    {"SUB", "BIT", "LIG", "ANT", "RC", "WC", "SC"}
)
# Plant_Group classes the report breaks gas into, in print order.
_GAS_CLASSES: tuple[str, ...] = (
    "CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP",
)

# Representative plants for the plant-level report. The user picks these
# because they span every operational class the per-plant binning now
# resolves (efficient CC, legacy CC, gas steam, CHP, coal, peakers).
_PLANT_PANEL: tuple[tuple[int, str], ...] = (
    (60122, "Colorado Bend II"),
    (59812, "Wolf Hollow II"),
    (3491,  "Handley"),
    (55464, "Deer Park Energy Center"),
    (55327, "Baytown Energy Center"),
    (55545, "Hidalgo Energy Center"),
    (298,   "Limestone (coal)"),
    (3470,  "W A Parish (coal units 5-8)"),
    (3504,  "Stryker Creek (CT peaker)"),
    (3492,  "Morgan Creek (CT peaker)"),
    (63688, "Topaz Generating (CT peaker)"),
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


def _classify_f923_row(row: pd.Series) -> str:
    """Bucket one F923 Page-1 row into a model fossil class or 'OTHER'.

    Classification logic mirrors :mod:`market_sim.data.fleet`:

      * Coal-class fuels → COAL.
      * Natural gas + CC prime mover (CA, CS, CT, CC) → CC_CHP or CC_REGULAR.
      * Natural gas + GT prime mover → CT_CHP or CT_PEAKER.
      * Natural gas + ST prime mover → ST_CHP or ST_GAS.
      * Anything else → OTHER (BTM, biomass, hydro, wind, solar, oil, …).
    """
    fuel = str(row["fuel_type"]).strip().upper()
    pm = str(row["prime_mover"]).strip().upper()
    chp = str(row["chp"]).strip().upper().startswith("Y")
    if fuel in _COAL_FUELS:
        return "COAL"
    if fuel != "NG":
        return "OTHER"
    if pm in {"CA", "CS", "CT", "CC"}:
        return "CC_CHP" if chp else "CC_REGULAR"
    if pm in {"GT", "IC"}:
        return "CT_CHP" if chp else "CT_PEAKER"
    if pm == "ST":
        return "ST_CHP" if chp else "ST_GAS"
    return "OTHER"


def _f923_annual_by_class(generation: pd.DataFrame, year: int) -> dict[str, float]:
    """Return ``{class: TWh}`` of EIA-923 annual net generation for a year."""
    year_df = generation[generation["year"] == year].copy()
    year_df["class"] = year_df.apply(_classify_f923_row, axis=1)
    twh = (
        year_df.groupby("class")["netgen_annual_mwh"].sum() / _MWH_PER_TWH
    )
    out: dict[str, float] = {}
    for cls in (*_GAS_CLASSES, "COAL"):
        out[cls] = float(twh.get(cls, 0.0))
    out["wind"] = float(twh.get("OTHER", 0.0))  # filled below
    return out


def _f923_annual_renewable_and_nuclear(
    generation: pd.DataFrame, year: int,
) -> dict[str, float]:
    """Return EIA-923 annual wind, solar and nuclear (TWh)."""
    df = generation[generation["year"] == year]
    fuel = df["fuel_type"].astype(str).str.upper()
    pm = df["prime_mover"].astype(str).str.upper()

    def _twh(mask: np.ndarray) -> float:
        return float(df.loc[mask, "netgen_annual_mwh"].sum()) / _MWH_PER_TWH

    return {
        "wind": _twh((fuel == "WND") | (pm == "WT")),
        "solar": _twh((fuel == "SUN") | (pm == "PV") | (pm == "CP")),
        "nuclear": _twh(fuel == "NUC"),
    }


def _f923_monthly_by_class(
    generation: pd.DataFrame, year: int,
) -> dict[str, np.ndarray]:
    """Return ``{class: (12,) MWh}`` for the year from EIA-923 Page 1."""
    year_df = generation[generation["year"] == year].copy()
    year_df["class"] = year_df.apply(_classify_f923_row, axis=1)
    cols = monthly_netgen_columns()
    out: dict[str, np.ndarray] = {}
    for cls in (*_GAS_CLASSES, "COAL"):
        sub = year_df[year_df["class"] == cls]
        if sub.empty:
            out[cls] = np.zeros(12)
        else:
            out[cls] = sub[cols].sum().to_numpy(dtype=float)
    return out


def _f923_monthly_renewable(
    generation: pd.DataFrame, year: int,
) -> dict[str, np.ndarray]:
    """Return ``{fuel: (12,) MWh}`` for wind/solar/nuclear from EIA-923."""
    df = generation[generation["year"] == year]
    fuel = df["fuel_type"].astype(str).str.upper()
    pm = df["prime_mover"].astype(str).str.upper()
    cols = monthly_netgen_columns()

    def _monthly(mask) -> np.ndarray:
        sub = df.loc[mask, cols]
        return sub.sum().to_numpy(dtype=float) if not sub.empty else np.zeros(12)

    return {
        "wind": _monthly((fuel == "WND") | (pm == "WT")),
        "solar": _monthly((fuel == "SUN") | (pm.isin(["PV", "CP"]))),
        "nuclear": _monthly(fuel == "NUC"),
    }


def _model_class_for_unit(unit_id: str, fuel: str, eff_bin: str) -> str:
    """Return the model class for one generator unit id.

    Generator unit ids built by :func:`bins_to_fleet` look like
    ``CC_REGULAR_Houston_p60122_econ`` — the prefix is the Plant_Group
    (carried through ``efficiency_bin`` in the FleetContext for CAMPD
    generators). Non-CAMPD generators (nuclear, hydro, imports) fall
    back to a class derived from their fuel type.
    """
    if eff_bin in {*_GAS_CLASSES, "COAL"}:
        return eff_bin
    if fuel == "nuclear":
        return "nuclear"
    if fuel in {"wind", "offshore_wind"}:
        return "wind"
    if fuel == "solar":
        return "solar"
    return "OTHER"


def _model_class_arrays(
    context, dispatch: np.ndarray,
) -> dict[str, np.ndarray]:
    """Return ``{class: (T,) MW}`` hourly modeled generation by class."""
    n_gen, T = dispatch.shape
    out: dict[str, np.ndarray] = {}
    for cls in (*_GAS_CLASSES, "COAL", "nuclear"):
        out[cls] = np.zeros(T)
    for g in range(n_gen):
        cls = _model_class_for_unit(
            context.unit_ids[g],
            context.fuel_types[g],
            context.efficiency_bins[g],
        )
        if cls in out:
            out[cls] += dispatch[g]
    return out


def _hourly_to_monthly(hourly_mw: np.ndarray) -> np.ndarray:
    """Return ``(12,) MWh`` for a length-8760 hourly MW array."""
    months = _hour_to_month(hourly_mw.shape[0])
    out = np.zeros(12)
    for m in range(1, 13):
        out[m - 1] = hourly_mw[months == m].sum()
    return out


def _print_table(rows: list[tuple]) -> None:
    """Print a column-aligned text table from a header + rows tuple list."""
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


def _pearson_r(model: np.ndarray, observed: np.ndarray) -> float:
    """Return the Pearson correlation of two equal-length series."""
    m = model - model.mean()
    o = observed - observed.mean()
    denom = float(np.sqrt((m * m).sum() * (o * o).sum()))
    return float((m * o).sum() / denom) if denom > 0.0 else float("nan")


def _nrmse(model: np.ndarray, observed: np.ndarray) -> float:
    """Return RMSE divided by mean observed."""
    rmse = float(np.sqrt(((model - observed) ** 2).mean()))
    denom = float(observed.mean())
    return rmse / denom if denom > 0.0 else float("nan")


def _print_grid_vs_930(
    year: int,
    model_class_hourly: dict[str, np.ndarray],
    model_hourly: dict[str, np.ndarray],
    fossil: dict[str, np.ndarray],
    renewables: dict[str, np.ndarray],
) -> None:
    """Print grid-delivered dispatch vs EIA-930 (the clean grid-vs-grid check).

    EIA-930 is grid-delivered, so the LP's grid dispatch is the right
    thing to compare here. Behind-the-meter CHP is invisible to EIA-930
    and is reported separately in the total-vs-EIA-923 table.
    """
    print(f"\n  Grid-delivered dispatch — {year} (model LP vs EIA-930 grid)")
    gas_grid = float(sum(model_class_hourly[c] for c in _GAS_CLASSES).sum()) / _MWH_PER_TWH
    coal_grid = float(model_class_hourly["COAL"].sum()) / _MWH_PER_TWH
    rows: list[tuple] = [("fuel", "model TWh", "EIA-930 TWh", "diff %")]
    pairs = [
        ("gas (all)", gas_grid, fossil["gas"].sum() / _MWH_PER_TWH),
        ("coal", coal_grid, fossil["coal"].sum() / _MWH_PER_TWH),
        ("wind", float(model_hourly["wind"].sum()) / _MWH_PER_TWH,
         renewables["wind"].sum() / _MWH_PER_TWH),
        ("solar", float(model_hourly["solar"].sum()) / _MWH_PER_TWH,
         renewables["solar"].sum() / _MWH_PER_TWH),
    ]
    for fuel, m, b in pairs:
        diff = 100.0 * (m - b) / b if b else float("nan")
        rows.append((fuel, f"{m:7.2f}", f"{b:7.2f}", f"{diff:+6.1f}"))
    _print_table(rows)


def _print_annual_breakdown(
    year: int,
    model_hourly: dict[str, np.ndarray],
    model_total_class_twh: dict[str, float],
    btm_by_class_twh: dict[str, float],
    f923_class_twh: dict[str, float],
    f923_re_nuc_twh: dict[str, float],
    eia930_solar_twh: float,
) -> None:
    """Print the annual class table: grid LP + behind-meter must-run vs EIA-923.

    For CHP classes the model total is the LP grid dispatch plus the
    behind-the-meter must-run (sized from EIA-923 by the resized
    :func:`compute_must_run_emissions`), so total reconciles to the
    measured EIA-923 figure and the BTM amount is visible for the
    downstream fleet-emissions step. Non-CHP classes carry no BTM, so
    their model total is the LP grid dispatch. Solar uses EIA-930.
    """
    print(f"\n  Total generation by class — {year}   "
          "(grid LP + behind-meter must-run vs EIA-923; solar vs EIA-930)")
    rows: list[tuple] = [
        ("class", "grid LP", "BTM-MR", "model tot", "EIA TWh", "diff %"),
    ]
    total_m = total_b = total_btm = 0.0
    for cls in (*_GAS_CLASSES, "COAL"):
        grid = model_total_class_twh.get(cls, 0.0)
        btm = btm_by_class_twh.get(cls, 0.0)
        m = grid + btm
        b = f923_class_twh.get(cls, 0.0)
        diff = 100.0 * (m - b) / b if b else float("nan")
        rows.append((
            cls, f"{grid:7.2f}", f"{btm:6.2f}", f"{m:8.2f}", f"{b:7.2f}",
            f"{diff:+6.1f}" if not np.isnan(diff) else "    —",
        ))
        total_m += m
        total_b += b
        total_btm += btm
    # Renewables and nuclear (no behind-meter component).
    wind_m = float(model_hourly["wind"].sum()) / _MWH_PER_TWH
    wind_b = f923_re_nuc_twh["wind"]
    rows.append((
        "wind", f"{wind_m:7.2f}", "  0.00", f"{wind_m:8.2f}", f"{wind_b:7.2f}",
        f"{100.0 * (wind_m - wind_b) / wind_b:+6.1f}" if wind_b else "    —",
    ))
    solar_m = float(model_hourly["solar"].sum()) / _MWH_PER_TWH
    rows.append((
        "solar (930)", f"{solar_m:7.2f}", "  0.00", f"{solar_m:8.2f}",
        f"{eia930_solar_twh:7.2f}",
        f"{100.0 * (solar_m - eia930_solar_twh) / eia930_solar_twh:+6.1f}"
        if eia930_solar_twh else "    —",
    ))
    nuc_m = model_total_class_twh.get("nuclear", 0.0)
    nuc_b = f923_re_nuc_twh["nuclear"]
    rows.append((
        "nuclear", f"{nuc_m:7.2f}", "  0.00", f"{nuc_m:8.2f}", f"{nuc_b:7.2f}",
        f"{100.0 * (nuc_m - nuc_b) / nuc_b:+6.1f}" if nuc_b else "    —",
    ))
    grand_m = total_m + wind_m + solar_m + nuc_m
    grand_b = total_b + wind_b + eia930_solar_twh + nuc_b
    rows.append((
        "TOTAL", "", f"{total_btm:6.2f}", f"{grand_m:8.2f}", f"{grand_b:7.2f}",
        f"{100.0 * (grand_m - grand_b) / grand_b:+6.1f}",
    ))
    _print_table(rows)
    print(f"    (behind-the-meter CHP must-run total: {total_btm:.2f} TWh — "
          "carried for the fleet-emissions post-process)")


def _print_monthly_breakdown(
    year: int,
    model_class_hourly: dict[str, np.ndarray],
    model_hourly: dict[str, np.ndarray],
    f923_monthly_class: dict[str, np.ndarray],
    f923_monthly_re: dict[str, np.ndarray],
    eia930_solar_monthly: np.ndarray,
) -> None:
    """Print the monthly +/- % table by class.

    Bias = (model − benchmark) / benchmark * 100.  Each fuel uses
    EIA-923 except solar (EIA-930).
    """
    print(f"\n  Monthly bias — {year}   (% of benchmark per month)")
    header = ("class",) + _MONTH_NAMES
    rows: list[tuple] = [header]

    def _row(label: str, model_monthly: np.ndarray, bench_monthly: np.ndarray):
        cells = []
        for m in range(12):
            b = bench_monthly[m]
            if b > 0:
                cells.append(f"{100.0 * (model_monthly[m] - b) / b:+5.1f}")
            else:
                cells.append("    ·")
        rows.append((label,) + tuple(cells))

    for cls in (*_GAS_CLASSES, "COAL"):
        _row(
            cls,
            _hourly_to_monthly(model_class_hourly[cls]),
            f923_monthly_class[cls],
        )
    _row(
        "wind",
        _hourly_to_monthly(model_hourly["wind"]),
        f923_monthly_re["wind"],
    )
    _row(
        "solar (930)",
        _hourly_to_monthly(model_hourly["solar"]),
        eia930_solar_monthly,
    )
    _row(
        "nuclear",
        _hourly_to_monthly(model_class_hourly["nuclear"]),
        f923_monthly_re["nuclear"],
    )
    _print_table(rows)


def _print_hourly_fit(
    year: int,
    model_class_hourly: dict[str, np.ndarray],
    model_hourly: dict[str, np.ndarray],
    fossil: dict[str, np.ndarray],
    renewables: dict[str, np.ndarray],
) -> None:
    """Print hourly Pearson r and NRMSE vs EIA-930."""
    print(f"\n  Hourly dispatch fit — {year} (model vs EIA-930)")
    rows: list[tuple] = [("fuel", "Pearson r", " NRMSE", "model TWh", "EIA-930 TWh")]
    # Aggregate gas across all model gas classes.
    gas_m = sum(model_class_hourly[c] for c in _GAS_CLASSES)
    coal_m = model_class_hourly["COAL"]
    nuc_m = model_class_hourly["nuclear"]
    wind_m = model_hourly["wind"]
    solar_m = model_hourly["solar"]
    nuc_obs = np.full(_HOURS_PER_YEAR, fossil.get("nuclear_mean", np.nan))
    pairs = [
        ("gas", gas_m, fossil["gas"]),
        ("coal", coal_m, fossil["coal"]),
        ("solar", solar_m, renewables["solar"]),
        ("wind", wind_m, renewables["wind"]),
    ]
    # If EIA-930 has a nuclear series, include it. The ERCO file has NG: NUC.
    if "nuclear" in fossil and fossil["nuclear"] is not None:
        pairs.append(("nuclear", nuc_m, fossil["nuclear"]))
    for fuel, m, o in pairs:
        rows.append((
            fuel,
            f"{_pearson_r(m, o):.3f}",
            f"{_nrmse(m, o):.3f}",
            f"{m.sum() / _MWH_PER_TWH:8.2f}",
            f"{o.sum() / _MWH_PER_TWH:8.2f}",
        ))
    _print_table(rows)


def _print_plant_level(
    year: int,
    dispatch: np.ndarray,
    context,
    plant_codes: np.ndarray,
    generation: pd.DataFrame,
) -> None:
    """Print the per-plant model vs EIA-923 annual + January-rep table."""
    f923 = generation[generation["year"] == year]
    f923_by_plant = (
        f923.groupby("plant_id")["netgen_annual_mwh"].sum().to_dict()
    )

    # Sum model dispatch by plant code.
    model_by_plant: dict[int, float] = {}
    n_gen = dispatch.shape[0]
    for g in range(n_gen):
        pc = int(plant_codes[g])
        if pc <= 0:
            continue
        model_by_plant[pc] = (
            model_by_plant.get(pc, 0.0) + float(dispatch[g].sum())
        )

    print(f"\n  Plant-level annual generation — {year} (EIA-923)")
    rows: list[tuple] = [
        ("plant", "EIA code", "model GWh", "EIA-923 GWh", "diff %", "class"),
    ]
    for code, label in _PLANT_PANEL:
        model_gwh = model_by_plant.get(code, 0.0) / 1e3
        eia_gwh = f923_by_plant.get(code, 0.0) / 1e3
        diff = (
            100.0 * (model_gwh - eia_gwh) / eia_gwh if eia_gwh else float("nan")
        )
        # Class from the first matching generator's efficiency bin.
        class_label = "—"
        for g in range(n_gen):
            if int(plant_codes[g]) == code:
                class_label = context.efficiency_bins[g]
                break
        rows.append((
            label,
            str(code),
            f"{model_gwh:9.0f}",
            f"{eia_gwh:9.0f}",
            f"{diff:+6.1f}" if not np.isnan(diff) else "    —",
            class_label,
        ))
    _print_table(rows)


def _run_and_report(
    year: int, iso: str, hours: int, gas_price: float,
    generation_f923: pd.DataFrame,
) -> None:
    """Run one calibration year and print every comparison block."""
    result, context = run_year(
        year, iso, hours, gas_price, ttc_overrides={}
    )

    print(f"\n{'=' * 80}")
    print(f"  ERCOT {year} BACKCAST   (status: {result.status})")
    print(f"{'=' * 80}")

    fossil = load_ercot_fossil_gen(year)
    renewables = load_ercot_renewable_gen(year)
    if fossil is None or renewables is None:
        logger.error("EIA-930 ERCO hourly data missing for %d", year)
        return

    # Pull plant_codes from the unit ids — they encode ``..._p{code}_<suffix>``.
    plant_codes = _plant_codes_from_unit_ids(context.unit_ids)

    # Hourly model series, by class and by renewable/nuclear bucket.
    dispatch = np.asarray(result.dispatch)
    model_class_hourly = _model_class_arrays(context, dispatch)
    model_hourly = {
        "wind": np.asarray(result.wind_dispatched).sum(axis=0),
        "solar": np.asarray(result.solar_dispatched).sum(axis=0),
    }

    # Annual EIA-923 by class and renewables.
    f923_class_twh = _f923_annual_by_class(generation_f923, year)
    f923_re_nuc_twh = _f923_annual_renewable_and_nuclear(generation_f923, year)

    # Model TWh by class, for the annual table.
    model_total_class_twh = {
        cls: float(model_class_hourly[cls].sum()) / _MWH_PER_TWH
        for cls in (*_GAS_CLASSES, "COAL", "nuclear")
    }

    # EIA-930 solar for the year (annual + monthly).
    eia930_solar_twh = float(renewables["solar"].sum()) / _MWH_PER_TWH
    eia930_solar_monthly = _hourly_to_monthly(renewables["solar"])

    # Behind-the-meter CHP must-run, sized from EIA-923 net generation minus
    # the LP's grid-delivered dispatch per plant. This is what the resized
    # compute_must_run_emissions produces; we aggregate it by class so the
    # CHP totals reconcile to EIA-923 and the BTM is visible for the
    # downstream fleet-emissions step.
    btm_by_class_twh = _btm_must_run_by_class(
        year, dispatch, plant_codes, context, generation_f923,
    )

    _print_grid_vs_930(
        year, model_class_hourly, model_hourly, fossil, renewables,
    )
    _print_annual_breakdown(
        year, model_hourly, model_total_class_twh, btm_by_class_twh,
        f923_class_twh, f923_re_nuc_twh, eia930_solar_twh,
    )

    f923_monthly_class = _f923_monthly_by_class(generation_f923, year)
    f923_monthly_re = _f923_monthly_renewable(generation_f923, year)
    _print_monthly_breakdown(
        year, model_class_hourly, model_hourly,
        f923_monthly_class, f923_monthly_re, eia930_solar_monthly,
    )

    _print_hourly_fit(year, model_class_hourly, model_hourly, fossil, renewables)
    _print_plant_level(
        year, dispatch, context, plant_codes, generation_f923,
    )


def _btm_must_run_by_class(
    year: int,
    dispatch: np.ndarray,
    plant_codes: np.ndarray,
    context,
    generation_f923: pd.DataFrame,
) -> dict[str, float]:
    """Return ``{CHP class: behind-meter must-run TWh}`` via the resized helper.

    Builds the per-plant grid-delivered dispatch (LP) and the per-plant
    EIA-923 total net generation, hands both to
    :func:`compute_must_run_emissions`, and aggregates the resulting
    behind-the-meter generation by plant group.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import load_campd_bins
    from market_sim.results.emissions import compute_must_run_emissions

    # Per-plant grid dispatch from the LP (sum tranches by plant code).
    grid_by_plant: dict[int, float] = {}
    for g in range(dispatch.shape[0]):
        pc = int(plant_codes[g])
        if pc > 0:
            grid_by_plant[pc] = grid_by_plant.get(pc, 0.0) + float(dispatch[g].sum())

    # Per-plant EIA-923 total net generation.
    f923 = generation_f923[generation_f923["year"] == year]
    total_by_plant = f923.groupby("plant_id")["netgen_annual_mwh"].sum().to_dict()

    bins = load_campd_bins(ScenarioConfig().campd_bins_path)
    mr = compute_must_run_emissions(
        bins, year,
        total_gen_by_plant=total_by_plant,
        grid_gen_by_plant=grid_by_plant,
    )
    if mr.empty:
        return {}
    by_class = mr.groupby("Plant_Group")["mr_gen_mwh"].sum() / _MWH_PER_TWH
    return {cls: float(v) for cls, v in by_class.items()}


def _plant_codes_from_unit_ids(unit_ids: list[str]) -> np.ndarray:
    """Return ``(n_gen,)`` plant codes parsed from ``..._p{code}_<suffix>``."""
    out = np.zeros(len(unit_ids), dtype=int)
    for i, uid in enumerate(unit_ids):
        # Match ``_p<digits>_`` token; CAMPD bin ids are e.g.
        # ``CC_REGULAR_Houston_p60122_econ``.
        parts = uid.split("_")
        for token in parts:
            if token.startswith("p") and token[1:].isdigit():
                out[i] = int(token[1:])
                break
    return out


def main() -> None:
    """Run every requested year and print the full diagnostic."""
    parser = argparse.ArgumentParser(
        description="Comprehensive ERCOT calibration backcast diagnostic."
    )
    parser.add_argument(
        "--year", nargs="+", type=int, default=[2023, 2024],
        help="Calibration years to run (default 2023 2024).",
    )
    parser.add_argument("--iso", default="ERCOT")
    parser.add_argument("--hours", type=int, default=_HOURS_PER_YEAR)
    args = parser.parse_args()

    reference = _load_reference()
    generation = load_monthly_generation()
    for year in args.year:
        gas_price = _henry_hub_actual(reference, year)
        logger.info(
            "running %s %d (hours=%d, Henry Hub=$%.2f/MMBtu)",
            args.iso, year, args.hours, gas_price,
        )
        _run_and_report(year, args.iso, args.hours, gas_price, generation)


if __name__ == "__main__":
    main()
