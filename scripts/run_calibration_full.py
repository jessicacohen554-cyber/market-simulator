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

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia923 import (  # noqa: E402
    load_monthly_generation,
    monthly_netgen_columns,
)
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_ercot_fossil_gen,
    load_ercot_nuclear_gen,
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
# CHP classes — reported in their own dedicated table and excluded from
# every other comparison. The remaining (non-CHP) gas classes are the
# only gas that the grid / hourly comparisons against EIA-930 use.
_CHP_CLASSES: tuple[str, ...] = ("CC_CHP", "CT_CHP", "ST_CHP")
_NONCHP_GAS: tuple[str, ...] = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")

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


def _print_reconciliation(
    year: int, iso: str,
    model_grid_twh: float,
    eia930_total_twh: float,
    btm_total_twh: float,
) -> None:
    """Print the supply/demand reconciliation that explains the total gap.

    The model dispatches to a demand target = EIA-930 metered load grossed
    up by the T&D loss factor. That gross-up was calibrated to eGRID net
    generation, which *includes* behind-the-meter CHP — so the model's
    grid generation runs above EIA-930's by-fuel net generation by roughly
    (T&D losses + behind-the-meter CHP host load). This block makes that
    structural gap explicit so the per-fuel table below is read as
    merit-order misalignment, not a demand error.
    """
    iso_config = get_iso_config(iso)
    raw_load = load_demand(iso, year, iso_config, td_loss_factor=0.0).sum() / _MWH_PER_TWH
    model_demand = load_demand(iso, year, iso_config, td_loss_factor=0.058).sum() / _MWH_PER_TWH
    gap = model_grid_twh - eia930_total_twh
    print(f"\n  [2] Generation reconciliation — {year}")
    rows = [
        ("EIA-930 metered load", f"{raw_load:7.2f} TWh"),
        ("Model demand target (load x1.058 T&D)", f"{model_demand:7.2f} TWh"),
        ("Model grid generation (LP)", f"{model_grid_twh:7.2f} TWh"),
        ("EIA-930 net generation (all fuels)", f"{eia930_total_twh:7.2f} TWh"),
        ("Gap (model grid - EIA-930)", f"{gap:+7.2f} TWh"),
        ("  = T&D losses + behind-meter CHP host load in the gross-up", ""),
        ("Behind-meter CHP must-run (off-LP, for emissions)",
         f"{btm_total_twh:7.2f} TWh"),
    ]
    width = max(len(r[0]) for r in rows)
    for label, val in rows:
        print(f"    {label.ljust(width)}  {val}")


def _print_chp_table(
    year: int,
    model_total_class_twh: dict[str, float],
    btm_by_class_twh: dict[str, float],
    f923_class_twh: dict[str, float],
) -> float:
    """[1] The ONE table where CHP appears. Returns total CHP grid-delivered.

    Each CHP class shows the LP grid-delivered dispatch, the
    behind-the-meter must-run (off-LP, sized from EIA-923 by the resized
    :func:`compute_must_run_emissions`), the model total (grid + BTM) and
    the measured EIA-923 total. CHP is excluded from every other table so
    the grid comparisons stay apples-to-apples against EIA-930.
    """
    print(f"\n  [1] CHP — {year}  (model grid LP + behind-meter must-run vs EIA-923 total)")
    rows: list[tuple] = [
        ("class", "grid LP", "BTM-MR", "model tot", "EIA-923", "diff %"),
    ]
    tot_grid = tot_btm = tot_b = 0.0
    for cls in _CHP_CLASSES:
        grid = model_total_class_twh.get(cls, 0.0)
        btm = btm_by_class_twh.get(cls, 0.0)
        m = grid + btm
        b = f923_class_twh.get(cls, 0.0)
        diff = 100.0 * (m - b) / b if b else float("nan")
        rows.append((
            cls, f"{grid:7.2f}", f"{btm:6.2f}", f"{m:8.2f}", f"{b:7.2f}",
            f"{diff:+6.1f}" if not np.isnan(diff) else "    —",
        ))
        tot_grid += grid
        tot_btm += btm
        tot_b += b
    tot_m = tot_grid + tot_btm
    rows.append((
        "TOTAL", f"{tot_grid:7.2f}", f"{tot_btm:6.2f}", f"{tot_m:8.2f}",
        f"{tot_b:7.2f}", f"{100.0 * (tot_m - tot_b) / tot_b:+6.1f}" if tot_b else "    —",
    ))
    _print_table(rows)
    print("    (BTM-MR = behind-the-meter must-run, off-LP — carried for the "
          "fleet-emissions post-process. CHP is excluded from every table below.)")
    return tot_grid


def _print_nonchp_grid(
    year: int,
    model_class_hourly: dict[str, np.ndarray],
    model_hourly: dict[str, np.ndarray],
    fossil: dict[str, np.ndarray],
    renewables: dict[str, np.ndarray],
    nuclear_930: np.ndarray | None,
    chp_grid_twh: float,
) -> None:
    """[3] Non-CHP grid generation vs EIA-930 — CHP excluded from BOTH sides.

    Model gas here is non-CHP only (CC_REGULAR + CT_PEAKER + ST_GAS). To
    keep the benchmark non-CHP too, the CHP grid-delivered estimate
    (``chp_grid_twh``, the model's grid-facing CHP) is subtracted from
    EIA-930's all-gas series — EIA-930 does not separately report CHP.
    The share-Δpp column is the merit-order misalignment, free of the
    T&D loss gross-up that still inflates the absolute TWh on both gas
    and the total.
    """
    gas_m = float(sum(model_class_hourly[c] for c in _NONCHP_GAS).sum()) / _MWH_PER_TWH
    coal_m = float(model_class_hourly["COAL"].sum()) / _MWH_PER_TWH
    nuc_m = float(model_class_hourly["nuclear"].sum()) / _MWH_PER_TWH
    wind_m = float(model_hourly["wind"].sum()) / _MWH_PER_TWH
    solar_m = float(model_hourly["solar"].sum()) / _MWH_PER_TWH

    nuc_930 = float(nuclear_930.sum()) / _MWH_PER_TWH if nuclear_930 is not None else 0.0
    gas_930_nonchp = fossil["gas"].sum() / _MWH_PER_TWH - chp_grid_twh
    series = [
        ("gas (non-CHP)", gas_m, gas_930_nonchp),
        ("coal", coal_m, fossil["coal"].sum() / _MWH_PER_TWH),
        ("nuclear", nuc_m, nuc_930),
        ("wind", wind_m, renewables["wind"].sum() / _MWH_PER_TWH),
        ("solar", solar_m, renewables["solar"].sum() / _MWH_PER_TWH),
    ]
    model_total = sum(m for _, m, _ in series)
    eia_total = sum(b for _, _, b in series)

    print(f"\n  [3] Non-CHP grid generation — {year}  (model LP vs EIA-930, CHP excluded)")
    rows: list[tuple] = [
        ("fuel", "model TWh", "model %", "EIA-930 TWh", "EIA-930 %", "Δpp"),
    ]
    for fuel, m, b in series:
        m_pct = 100.0 * m / model_total if model_total else 0.0
        b_pct = 100.0 * b / eia_total if eia_total else 0.0
        rows.append((
            fuel, f"{m:8.2f}", f"{m_pct:6.1f}", f"{b:8.2f}",
            f"{b_pct:6.1f}", f"{m_pct - b_pct:+6.1f}",
        ))
    rows.append((
        "TOTAL", f"{model_total:8.2f}", " 100.0", f"{eia_total:8.2f}",
        " 100.0", "      ",
    ))
    _print_table(rows)
    print(f"    (EIA-930 non-CHP gas = EIA-930 all-gas − {chp_grid_twh:.1f} TWh CHP "
          "grid-delivered estimate. Δpp = model share − EIA-930 share, the")
    print("     merit-order misalignment free of the T&D-loss gross-up in the totals.)")


def _print_gas_class_annual(
    year: int,
    model_total_class_twh: dict[str, float],
    btm_by_class_twh: dict[str, float],
    f923_class_twh: dict[str, float],
) -> None:
    """[3b] Every thermal class — annual model (grid LP + behind-meter) vs EIA-923.

    The complete thermal picture in one table: CC_CHP, CC_REGULAR,
    CT_CHP, CT_PEAKER, ST_GAS, ST_CHP and COAL. CHP classes carry
    behind-the-meter must-run (off-LP); the rest are grid LP only.
    EIA-923 is the total-generation benchmark for every class.
    """
    print(f"\n  [3b] Thermal by class — {year}  (model grid LP + behind-meter must-run vs EIA-923 total)")
    rows: list[tuple] = [
        ("class", "grid LP", "BTM-MR", "model tot", "EIA-923", "diff %"),
    ]
    tg = tbtm = tm = tb = 0.0
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
        tg += grid
        tbtm += btm
        tm += m
        tb += b
    rows.append((
        "TOTAL", f"{tg:7.2f}", f"{tbtm:6.2f}", f"{tm:8.2f}", f"{tb:7.2f}",
        f"{100.0 * (tm - tb) / tb:+6.1f}" if tb else "    —",
    ))
    _print_table(rows)


def _print_monthly_breakdown(
    year: int,
    model_class_hourly: dict[str, np.ndarray],
    model_hourly: dict[str, np.ndarray],
    f923_monthly_class: dict[str, np.ndarray],
    f923_monthly_re: dict[str, np.ndarray],
    eia930_solar_monthly: np.ndarray,
    btm_by_class_twh: dict[str, float],
    f923_class_twh: dict[str, float],
) -> None:
    """[4] Monthly +/- % bias vs EIA-923 (all gas classes; solar vs EIA-930).

    Bias = (model − benchmark) / benchmark * 100. For CHP classes the
    model is grid LP + behind-meter must-run, with the annual BTM
    distributed across months in proportion to the class's EIA-923
    monthly net generation (steam load roughly tracks output). Non-CHP
    classes are LP grid only.
    """
    print(f"\n  [4] Monthly bias — {year}   (% of EIA-923 per month; CHP incl. behind-meter)")
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
        grid_monthly = _hourly_to_monthly(model_class_hourly[cls])
        bench = f923_monthly_class[cls]
        # Distribute the class's annual behind-meter must-run across months
        # in proportion to its EIA-923 monthly shape (CHP classes only).
        btm_annual = btm_by_class_twh.get(cls, 0.0) * _MWH_PER_TWH
        if btm_annual > 0 and bench.sum() > 0:
            model_monthly = grid_monthly + btm_annual * (bench / bench.sum())
        else:
            model_monthly = grid_monthly
        _row(cls, model_monthly, bench)
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
    nuclear_930: np.ndarray | None,
    chp_grid_twh: float,
) -> None:
    """[5] Hourly Pearson r and NRMSE vs EIA-930 — non-CHP gas.

    Gas is non-CHP only (CC_REGULAR + CT_PEAKER + ST_GAS). The EIA-930
    benchmark subtracts a flat CHP grid-delivered baseload
    (``chp_grid_twh`` spread evenly over the year — CHP steam load is
    near-constant), so both sides are non-CHP and the shape correlation
    is not diluted by the CHP baseload.
    """
    print(f"\n  [5] Hourly dispatch fit — {year} (model vs EIA-930, non-CHP gas)")
    rows: list[tuple] = [("fuel", "Pearson r", " NRMSE", "model TWh", "EIA-930 TWh")]
    gas_m = sum(model_class_hourly[c] for c in _NONCHP_GAS)
    coal_m = model_class_hourly["COAL"]
    nuc_m = model_class_hourly["nuclear"]
    wind_m = model_hourly["wind"]
    solar_m = model_hourly["solar"]
    # EIA-930 non-CHP gas = all-gas minus a flat CHP grid-delivered baseload.
    flat_chp = chp_grid_twh * _MWH_PER_TWH / _HOURS_PER_YEAR
    gas_930_nonchp = fossil["gas"] - flat_chp
    pairs = [
        ("gas (non-CHP)", gas_m, gas_930_nonchp),
        ("coal", coal_m, fossil["coal"]),
        ("nuclear", nuc_m, nuclear_930),
        ("solar", solar_m, renewables["solar"]),
        ("wind", wind_m, renewables["wind"]),
    ]
    for fuel, m, o in pairs:
        if o is None:
            continue
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

    print(f"\n  [6] Plant-level annual generation — {year} (EIA-923)")
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

    # Annual EIA-923 net generation by class (for the CHP table).
    f923_class_twh = _f923_annual_by_class(generation_f923, year)

    # Model grid-delivered (LP) TWh by class.
    model_total_class_twh = {
        cls: float(model_class_hourly[cls].sum()) / _MWH_PER_TWH
        for cls in (*_GAS_CLASSES, "COAL", "nuclear")
    }

    # EIA-930 solar monthly (for the non-CHP monthly table; solar uses 930).
    eia930_solar_monthly = _hourly_to_monthly(renewables["solar"])

    # Behind-the-meter CHP must-run, sized from EIA-923 net generation minus
    # the LP's grid-delivered dispatch per plant. This is what the resized
    # compute_must_run_emissions produces; we aggregate it by class so the
    # CHP totals reconcile to EIA-923 and the BTM is visible for the
    # downstream fleet-emissions step.
    btm_by_class_twh = _btm_must_run_by_class(
        year, dispatch, plant_codes, context, generation_f923,
    )

    nuclear_930 = load_ercot_nuclear_gen(year)

    # [1] CHP — the one table where CHP appears; returns CHP grid-delivered.
    chp_grid_twh = _print_chp_table(
        year, model_total_class_twh, btm_by_class_twh, f923_class_twh,
    )

    # [2] Reconciliation — why the model total runs over EIA-930.
    model_grid_twh = (
        float(dispatch.sum())
        + float(model_hourly["wind"].sum())
        + float(model_hourly["solar"].sum())
    ) / _MWH_PER_TWH
    eia930_total_twh = (
        fossil["gas"].sum() + fossil["coal"].sum()
        + renewables["wind"].sum() + renewables["solar"].sum()
        + (nuclear_930.sum() if nuclear_930 is not None else 0.0)
    ) / _MWH_PER_TWH
    btm_total_twh = sum(btm_by_class_twh.values())
    _print_reconciliation(
        year, iso, model_grid_twh, eia930_total_twh, btm_total_twh,
    )

    # [3] Non-CHP grid generation vs EIA-930.
    _print_nonchp_grid(
        year, model_class_hourly, model_hourly, fossil, renewables,
        nuclear_930, chp_grid_twh,
    )

    # [3b] Every gas class — annual model (grid + behind-meter) vs EIA-923.
    _print_gas_class_annual(
        year, model_total_class_twh, btm_by_class_twh, f923_class_twh,
    )

    # [4] Monthly bias (all gas classes; CHP incl. behind-meter).
    f923_monthly_class = _f923_monthly_by_class(generation_f923, year)
    f923_monthly_re = _f923_monthly_renewable(generation_f923, year)
    _print_monthly_breakdown(
        year, model_class_hourly, model_hourly,
        f923_monthly_class, f923_monthly_re, eia930_solar_monthly,
        btm_by_class_twh, f923_class_twh,
    )

    # [5] Hourly fit (non-CHP gas).
    _print_hourly_fit(
        year, model_class_hourly, model_hourly, fossil, renewables,
        nuclear_930, chp_grid_twh,
    )

    # [6] Plant-level (EIA-923).
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
