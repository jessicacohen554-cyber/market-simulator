"""Calibration backcast: solve, persist, and report off persisted parquet.

Each run solves the dispatch for the requested years (and the P2 commitment
pass when ``--commitment`` is set), writes the full hourly per-plant results
to a timestamped parquet bundle, and then computes the comparison report from
that bundle. Nothing is lost: the bundle is the source of truth and can be
re-queried for any ad-hoc analysis, and re-running never overwrites a prior
run (each lands in its own timestamped directory).

A run bundle lives in ``results/calibration/<timestamp>/`` and holds:

  * ``dispatch/<year>_<pass>.parquet`` — every generator's hourly MW (8760h)
    with plant_code / class / fuel / supply / zone metadata, plus wind and
    solar as per-zone pseudo-units. Coal carries its supply class
    (COAL_LIGNITE / COAL_PRB) so mine-mouth and PRB can be separated.
  * ``system.parquet`` — per-zone hourly price, load slack and demand target,
    for every year and pass.
  * ``eia930.parquet`` — EIA-930 hourly benchmark series (gas, coal, wind,
    solar, nuclear, net generation).
  * ``eia923.parquet`` — EIA-923 net generation per (plant, class), annual and
    by month.
  * ``btm.parquet`` — behind-the-meter CHP must-run by class (off-grid).
  * ``meta.json`` — run metadata (timestamp, years, passes, flags, prices).

The report ([1]-[6] tables) is then computed entirely from the bundle, so the
same numbers can be reproduced from an old run with ``--report <dir>``.

Usage:
    python scripts/run_calibration_full.py --year 2023 2024
    python scripts/run_calibration_full.py --year 2023 --commitment --no-coal-p2
    python scripts/run_calibration_full.py --report results/calibration/<ts>
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
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
from market_sim.data.fleet import COAL_PLANT_SUPPLY  # noqa: E402
from scripts.run_calibration import (  # noqa: E402
    _calibration_config,
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
# Gas Plant_Group classes, in print order.
_GAS_CLASSES: tuple[str, ...] = (
    "CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP",
)
# Coal classes split by fuel supply (mine-mouth lignite vs PRB by rail).
_COAL_CLASSES: tuple[str, ...] = ("COAL_LIGNITE", "COAL_PRB")
# CHP classes — reported in their own dedicated table and excluded from every
# other comparison.
_CHP_CLASSES: tuple[str, ...] = ("CC_CHP", "CT_CHP", "ST_CHP")
_NONCHP_GAS: tuple[str, ...] = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
# All thermal classes the [3b] / [4] tables iterate over.
_THERMAL_CLASSES: tuple[str, ...] = (*_GAS_CLASSES, *_COAL_CLASSES)

# Representative plants for the plant-level report. The user picks these
# because they span every operational class the per-plant binning resolves
# (efficient CC, legacy CC, gas steam, CHP, coal, peakers).
_PLANT_PANEL: tuple[tuple[int, str], ...] = (
    (60122, "Colorado Bend II"),
    (59812, "Wolf Hollow II"),
    (3491,  "Handley"),
    (55464, "Deer Park Energy Center"),
    (55327, "Baytown Energy Center"),
    (55545, "Hidalgo Energy Center"),
    (298,   "Limestone (coal)"),
    (3470,  "W A Parish (coal units 5-8)"),
    (3504,  "Stryker Creek (gas steam)"),
    (3492,  "Morgan Creek (CT peaker)"),
    (63688, "Topaz Generating (CT peaker)"),
)


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def _coal_supply_class(plant_code: int, fuel_code: str = "") -> str:
    """Return ``COAL_LIGNITE`` or ``COAL_PRB`` for a coal plant.

    Uses the authoritative model mapping (:data:`COAL_PLANT_SUPPLY`) so the
    model and the EIA-923 benchmark split coal the same way. For a plant not
    in the map, fall back to the EIA-923 fuel code (``LIG`` = lignite).
    """
    supply = COAL_PLANT_SUPPLY.get(int(plant_code))
    if supply == "lignite":
        return "COAL_LIGNITE"
    if supply == "prb":
        return "COAL_PRB"
    return "COAL_LIGNITE" if str(fuel_code).upper() == "LIG" else "COAL_PRB"


def _model_class_for_unit(unit_id: str, fuel: str, eff_bin: str) -> str:
    """Return the model class for one generator unit id.

    CAMPD generator ids carry their Plant_Group through ``efficiency_bin``
    (e.g. ``CC_REGULAR_Houston_p60122_econ``). Non-CAMPD generators fall back
    to a class derived from the fuel type. Coal is returned as the bare
    ``COAL`` here; the caller splits it into the supply class.
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


def _classify_f923(fuel: str, pm: str, chp: bool, plant_id: int) -> str:
    """Bucket one EIA-923 Page-1 row into a model class.

    Mirrors :func:`market_sim.data.fleet` classification. Coal is split into
    its supply class; gas is split by prime mover and CHP flag; wind, solar
    and nuclear are returned as their own classes; everything else is OTHER.
    """
    fuel = str(fuel).strip().upper()
    pm = str(pm).strip().upper()
    if fuel in _COAL_FUELS:
        return _coal_supply_class(plant_id, fuel)
    if fuel == "NG":
        if pm in {"CA", "CS", "CT", "CC"}:
            return "CC_CHP" if chp else "CC_REGULAR"
        if pm in {"GT", "IC"}:
            return "CT_CHP" if chp else "CT_PEAKER"
        if pm == "ST":
            return "ST_CHP" if chp else "ST_GAS"
        return "OTHER"
    if fuel == "WND" or pm == "WT":
        return "wind"
    if fuel == "SUN" or pm in {"PV", "CP"}:
        return "solar"
    if fuel == "NUC":
        return "nuclear"
    return "OTHER"


def _plant_codes_from_unit_ids(unit_ids: list[str]) -> np.ndarray:
    """Return ``(n_gen,)`` plant codes parsed from ``..._p{code}_<suffix>``."""
    out = np.zeros(len(unit_ids), dtype=int)
    for i, uid in enumerate(unit_ids):
        for token in uid.split("_"):
            if token.startswith("p") and token[1:].isdigit():
                out[i] = int(token[1:])
                break
    return out


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


def _hourly_to_monthly(hourly_mw: np.ndarray) -> np.ndarray:
    """Return ``(12,) MWh`` for a length-8760 hourly MW array."""
    months = _hour_to_month(hourly_mw.shape[0])
    return np.array(
        [hourly_mw[months == m].sum() for m in range(1, 13)], dtype=float
    )


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


def _print_table(rows: list[tuple]) -> None:
    """Print a column-aligned text table from a header + rows tuple list."""
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


# ---------------------------------------------------------------------------
# Persistence — build the parquet bundle from a solved dispatch
# ---------------------------------------------------------------------------

def _dispatch_frame(
    year: int, pass_label: str, result, context, zone_names: list[str],
) -> pd.DataFrame:
    """Return the long per-generator-hour dispatch frame for one year-pass.

    One row per (generator, hour) carrying the dispatched MW and the
    generator's class / fuel / supply / zone, plus wind and solar as per-zone
    pseudo-units so the frame reconciles to total grid generation.
    """
    disp = np.asarray(result.dispatch, dtype=np.float32)
    n_gen, T = disp.shape
    unit_ids = list(context.unit_ids)
    fuels = list(context.fuel_types)
    bins = list(context.efficiency_bins)
    zones = list(context.zones)
    plant_codes = _plant_codes_from_unit_ids(unit_ids)

    klass = []
    supply = []
    for g in range(n_gen):
        k = _model_class_for_unit(unit_ids[g], fuels[g], bins[g])
        if k == "COAL":
            k = _coal_supply_class(int(plant_codes[g]))
            supply.append("lignite" if k == "COAL_LIGNITE" else "prb")
        else:
            supply.append("")
        klass.append(k)

    rep = lambda a: np.repeat(np.asarray(a, dtype=object), T)  # noqa: E731
    hours = np.tile(np.arange(T, dtype=np.int32), n_gen)
    frames = [pd.DataFrame({
        "unit_id": rep(unit_ids),
        "plant_code": np.repeat(plant_codes.astype(np.int32), T),
        "klass": rep(klass),
        "fuel": rep(fuels),
        "supply": rep(supply),
        "zone": rep(zones),
        "hour": hours,
        "mw": disp.reshape(-1),
    })]

    for name, arr in (
        ("wind", result.wind_dispatched), ("solar", result.solar_dispatched),
    ):
        a = np.asarray(arr, dtype=np.float32)
        for z in range(a.shape[0]):
            zone = zone_names[z]
            frames.append(pd.DataFrame({
                "unit_id": f"{name.upper()}_{zone}",
                "plant_code": np.int32(0),
                "klass": name, "fuel": name, "supply": "",
                "zone": zone, "hour": np.arange(T, dtype=np.int32), "mw": a[z],
            }))

    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "pass", pass_label)
    df.insert(0, "year", np.int16(year))
    for col in ("pass", "unit_id", "klass", "fuel", "supply", "zone"):
        df[col] = df[col].astype("category")
    df["mw"] = df["mw"].astype(np.float32)
    return df


def _system_frame(
    year: int, pass_label: str, result, demand: np.ndarray,
    zone_names: list[str],
) -> pd.DataFrame:
    """Return the per-zone hourly price / slack / demand frame."""
    prices = np.asarray(result.prices, dtype=float)
    slack = np.asarray(result.slack, dtype=float)
    n_zones, T = prices.shape
    rows = []
    for z in range(n_zones):
        rows.append(pd.DataFrame({
            "year": np.int16(year), "pass": pass_label, "zone": zone_names[z],
            "hour": np.arange(T, dtype=np.int32),
            "price": prices[z], "slack": slack[z], "demand": demand[z, :T],
        }))
    return pd.concat(rows, ignore_index=True)


def _eia930_frame(year: int, iso: str, iso_config) -> pd.DataFrame | None:
    """Return the EIA-930 hourly benchmark series for a year, long format."""
    fossil = load_ercot_fossil_gen(year)
    renew = load_ercot_renewable_gen(year)
    if fossil is None or renew is None:
        return None
    nuclear = load_ercot_nuclear_gen(year)
    # net generation = Demand + Interchange = load_demand with no gross-up.
    net_gen = load_demand(iso, year, iso_config, td_loss_factor=0.0).sum(axis=0)
    series = {
        "gas": fossil["gas"], "coal": fossil["coal"],
        "wind": renew["wind"], "solar": renew["solar"], "net_gen": net_gen,
    }
    if nuclear is not None:
        series["nuclear"] = nuclear
    out = []
    for name, arr in series.items():
        a = np.asarray(arr, dtype=float)
        out.append(pd.DataFrame({
            "year": np.int16(year), "series": name,
            "hour": np.arange(a.shape[0], dtype=np.int32), "mw": a,
        }))
    return pd.concat(out, ignore_index=True)


def _eia923_frame(year: int, generation: pd.DataFrame) -> pd.DataFrame:
    """Return EIA-923 net generation per (plant, class), annual and monthly."""
    df = generation[generation["year"] == year].copy()
    df["klass"] = [
        _classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
        for f, pm, c, pid in zip(
            df["fuel_type"], df["prime_mover"], df["chp"], df["plant_id"]
        )
    ]
    cols = monthly_netgen_columns()
    agg = {"netgen_annual_mwh": "sum", **{c: "sum" for c in cols}}
    grouped = df.groupby(["plant_id", "klass"], as_index=False).agg(agg)
    grouped.insert(0, "year", np.int16(year))
    rename = {c: f"m{i + 1:02d}" for i, c in enumerate(cols)}
    rename["netgen_annual_mwh"] = "annual_mwh"
    return grouped.rename(columns=rename)


def _btm_frame(
    year: int, pass_label: str, result, context, generation: pd.DataFrame,
) -> pd.DataFrame:
    """Return behind-the-meter CHP must-run by class for one year-pass."""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import load_campd_bins
    from market_sim.results.emissions import compute_must_run_emissions

    dispatch = np.asarray(result.dispatch)
    plant_codes = _plant_codes_from_unit_ids(list(context.unit_ids))
    grid_by_plant: dict[int, float] = {}
    for g in range(dispatch.shape[0]):
        pc = int(plant_codes[g])
        if pc > 0:
            grid_by_plant[pc] = grid_by_plant.get(pc, 0.0) + float(
                dispatch[g].sum()
            )
    f923 = generation[generation["year"] == year]
    total_by_plant = (
        f923.groupby("plant_id")["netgen_annual_mwh"].sum().to_dict()
    )
    bins = load_campd_bins(ScenarioConfig().campd_bins_path)
    mr = compute_must_run_emissions(
        bins, year, total_gen_by_plant=total_by_plant,
        grid_gen_by_plant=grid_by_plant,
    )
    if mr.empty:
        return pd.DataFrame(columns=["year", "pass", "klass", "btm_twh"])
    by_class = mr.groupby("Plant_Group")["mr_gen_mwh"].sum() / _MWH_PER_TWH
    return pd.DataFrame({
        "year": np.int16(year), "pass": pass_label,
        "klass": by_class.index, "btm_twh": by_class.to_numpy(),
    })


def _git_sha() -> str:
    """Return the current git short SHA, or '' if unavailable."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def solve_and_persist(
    years: list[int], iso: str, hours: int, reference: dict,
    commitment: bool, screen_coal: bool, run_dir: Path,
) -> Path:
    """Solve every year/pass, write the parquet bundle, return the run dir."""
    iso_config = get_iso_config(iso)
    zone_names = iso_config.zone_names
    (run_dir / "dispatch").mkdir(parents=True, exist_ok=True)

    generation = load_monthly_generation()
    system_frames, eia930_frames, eia923_frames, btm_frames = [], [], [], []
    gas_prices: dict[int, float] = {}
    passes_seen: set[str] = set()

    for year in years:
        gas_price = _henry_hub_actual(reference, year)
        gas_prices[year] = gas_price
        cfg = _calibration_config(year, iso, hours, gas_price)
        demand = load_demand(
            iso, year, iso_config, td_loss_factor=cfg.td_loss_factor
        )
        logger.info(
            "solving %s %d (hours=%d, Henry Hub=$%.2f/MMBtu, commitment=%s)",
            iso, year, hours, gas_price, commitment,
        )
        result, context, result_p1 = run_year(
            year, iso, hours, gas_price, ttc_overrides={},
            commitment_enabled=commitment, commitment_screen_coal=screen_coal,
        )
        labelled = [("P2" if result_p1 is not None else "P1", result)]
        if result_p1 is not None:
            labelled.insert(0, ("P1", result_p1))

        for label, res in labelled:
            passes_seen.add(label)
            _dispatch_frame(year, label, res, context, zone_names).to_parquet(
                run_dir / "dispatch" / f"{year}_{label}.parquet", index=False
            )
            system_frames.append(
                _system_frame(year, label, res, demand, zone_names)
            )
            btm_frames.append(
                _btm_frame(year, label, res, context, generation)
            )

        e930 = _eia930_frame(year, iso, iso_config)
        if e930 is not None:
            eia930_frames.append(e930)
        eia923_frames.append(_eia923_frame(year, generation))

    pd.concat(system_frames, ignore_index=True).to_parquet(
        run_dir / "system.parquet", index=False
    )
    if eia930_frames:
        pd.concat(eia930_frames, ignore_index=True).to_parquet(
            run_dir / "eia930.parquet", index=False
        )
    pd.concat(eia923_frames, ignore_index=True).to_parquet(
        run_dir / "eia923.parquet", index=False
    )
    pd.concat(btm_frames, ignore_index=True).to_parquet(
        run_dir / "btm.parquet", index=False
    )
    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "iso": iso, "years": years, "hours": hours,
        "passes": sorted(passes_seen), "commitment": commitment,
        "commitment_screen_coal": screen_coal, "gas_prices": gas_prices,
        "td_loss_factor": _calibration_config(
            years[0], iso, hours, gas_prices[years[0]]
        ).td_loss_factor,
        "git_sha": _git_sha(),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    logger.info("wrote calibration bundle to %s", run_dir)
    return run_dir


# ---------------------------------------------------------------------------
# Report — computed entirely from the persisted bundle
# ---------------------------------------------------------------------------

def _class_hourly(dispatch: pd.DataFrame) -> dict[str, np.ndarray]:
    """Return ``{class: (T,) MW}`` from a year-pass dispatch frame."""
    piv = (
        dispatch.groupby(["klass", "hour"], observed=True)["mw"].sum()
        .unstack("klass", fill_value=0.0).sort_index()
    )
    return {cls: piv[cls].to_numpy(dtype=float) for cls in piv.columns}


def _e923_annual(e923: pd.DataFrame) -> dict[str, float]:
    """Return ``{class: TWh}`` of EIA-923 annual net generation."""
    s = e923.groupby("klass")["annual_mwh"].sum() / _MWH_PER_TWH
    return {k: float(v) for k, v in s.items()}


def _e923_monthly(e923: pd.DataFrame) -> dict[str, np.ndarray]:
    """Return ``{class: (12,) MWh}`` of EIA-923 monthly net generation."""
    cols = [f"m{i:02d}" for i in range(1, 13)]
    g = e923.groupby("klass")[cols].sum()
    return {k: g.loc[k].to_numpy(dtype=float) for k in g.index}


def _print_chp(year, model_twh, btm, e923_annual) -> float:
    """[1] The one table where CHP appears. Returns CHP grid-delivered TWh."""
    print(f"\n  [1] CHP — {year}  (model grid LP + behind-meter must-run "
          "vs EIA-923 total)")
    rows = [("class", "grid LP", "BTM-MR", "model tot", "EIA-923", "diff %")]
    tg = tb = te = 0.0
    for cls in _CHP_CLASSES:
        grid = model_twh.get(cls, 0.0)
        b = btm.get(cls, 0.0)
        m = grid + b
        e = e923_annual.get(cls, 0.0)
        diff = 100.0 * (m - e) / e if e else float("nan")
        rows.append((cls, f"{grid:7.2f}", f"{b:6.2f}", f"{m:8.2f}",
                     f"{e:7.2f}", f"{diff:+6.1f}" if e else "    —"))
        tg += grid
        tb += b
        te += e
    tm = tg + tb
    rows.append(("TOTAL", f"{tg:7.2f}", f"{tb:6.2f}", f"{tm:8.2f}",
                 f"{te:7.2f}", f"{100.0 * (tm - te) / te:+6.1f}" if te else "—"))
    _print_table(rows)
    print("    (BTM-MR = behind-the-meter must-run, off-grid. CHP is excluded "
          "from every table below.)")
    return tg


def _print_reconciliation(
    year, net_gen, model_target, model_grid, unserved, btm_total,
) -> None:
    """[2] Grid generation reconciliation — model grid vs EIA-930 net gen."""
    gap = model_grid - net_gen
    print(f"\n  [2] Grid generation reconciliation — {year}")
    rows = [
        ("EIA-930 net generation (Demand + Interchange)", f"{net_gen:7.2f} TWh"),
        ("Model demand target", f"{model_target:7.2f} TWh"),
        ("Model grid generation (LP)", f"{model_grid:7.2f} TWh"),
        ("Gap (model grid − EIA-930 net gen)", f"{gap:+7.2f} TWh"),
        ("Unserved energy / load slack (should be 0)", f"{unserved:7.4f} TWh"),
        ("Behind-meter CHP must-run (off-grid; table [1] only)",
         f"{btm_total:7.2f} TWh"),
    ]
    width = max(len(r[0]) for r in rows)
    for label, val in rows:
        print(f"    {label.ljust(width)}  {val}")


def _print_nonchp_grid(year, model_hourly, e930, chp_grid_twh) -> None:
    """[3] Non-CHP grid generation vs EIA-930 (CHP excluded both sides)."""
    coal_m = sum(
        model_hourly.get(c, np.zeros(1)).sum() for c in _COAL_CLASSES
    ) / _MWH_PER_TWH
    gas_m = sum(
        model_hourly.get(c, np.zeros(1)).sum() for c in _NONCHP_GAS
    ) / _MWH_PER_TWH
    nuc_m = model_hourly.get("nuclear", np.zeros(1)).sum() / _MWH_PER_TWH
    wind_m = model_hourly.get("wind", np.zeros(1)).sum() / _MWH_PER_TWH
    solar_m = model_hourly.get("solar", np.zeros(1)).sum() / _MWH_PER_TWH

    series = [
        ("gas (non-CHP)", gas_m, e930["gas"].sum() / _MWH_PER_TWH - chp_grid_twh),
        ("coal", coal_m, e930["coal"].sum() / _MWH_PER_TWH),
        ("nuclear", nuc_m, e930.get("nuclear", np.zeros(1)).sum() / _MWH_PER_TWH),
        ("wind", wind_m, e930["wind"].sum() / _MWH_PER_TWH),
        ("solar", solar_m, e930["solar"].sum() / _MWH_PER_TWH),
    ]
    model_total = sum(m for _, m, _ in series)
    eia_total = sum(b for _, _, b in series)
    print(f"\n  [3] Non-CHP grid generation — {year}  (model LP vs EIA-930, "
          "CHP excluded)")
    rows = [("fuel", "model TWh", "model %", "EIA-930 TWh", "EIA-930 %", "Δpp")]
    for fuel, m, b in series:
        mp = 100.0 * m / model_total if model_total else 0.0
        bp = 100.0 * b / eia_total if eia_total else 0.0
        rows.append((fuel, f"{m:8.2f}", f"{mp:6.1f}", f"{b:8.2f}",
                     f"{bp:6.1f}", f"{mp - bp:+6.1f}"))
    rows.append(("TOTAL", f"{model_total:8.2f}", " 100.0",
                 f"{eia_total:8.2f}", " 100.0", "      "))
    _print_table(rows)
    print(f"    (EIA-930 non-CHP gas = EIA-930 all-gas − {chp_grid_twh:.1f} TWh "
          "model CHP grid-delivered.)")


def _print_thermal_annual(year, model_twh, btm, e923_annual) -> None:
    """[3b] Every thermal class (coal split) — model + BTM vs EIA-923."""
    print(f"\n  [3b] Thermal by class — {year}  (model grid LP + behind-meter "
          "must-run vs EIA-923 total; coal split lignite/PRB)")
    rows = [("class", "grid LP", "BTM-MR", "model tot", "EIA-923", "diff %")]
    tg = tb = tm = te = 0.0
    for cls in _THERMAL_CLASSES:
        grid = model_twh.get(cls, 0.0)
        b = btm.get(cls, 0.0)
        m = grid + b
        e = e923_annual.get(cls, 0.0)
        diff = 100.0 * (m - e) / e if e else float("nan")
        rows.append((cls, f"{grid:7.2f}", f"{b:6.2f}", f"{m:8.2f}",
                     f"{e:7.2f}", f"{diff:+6.1f}" if e else "    —"))
        tg += grid
        tb += b
        tm += m
        te += e
    rows.append(("TOTAL", f"{tg:7.2f}", f"{tb:6.2f}", f"{tm:8.2f}",
                 f"{te:7.2f}", f"{100.0 * (tm - te) / te:+6.1f}" if te else "—"))
    _print_table(rows)


def _print_monthly(year, model_hourly, e923_monthly, e930_solar_monthly,
                   btm, e923_annual) -> None:
    """[4] Monthly +/- % bias vs EIA-923 (coal split; solar vs EIA-930)."""
    print(f"\n  [4] Monthly bias — {year}   (% of EIA-923 per month; coal split; "
          "CHP incl. behind-meter)")
    rows = [("class",) + _MONTH_NAMES]

    def _row(label, model_monthly, bench_monthly):
        cells = []
        for m in range(12):
            b = bench_monthly[m]
            cells.append(
                f"{100.0 * (model_monthly[m] - b) / b:+5.1f}" if b > 0 else "    ·"
            )
        rows.append((label,) + tuple(cells))

    for cls in _THERMAL_CLASSES:
        grid_monthly = _hourly_to_monthly(model_hourly.get(cls, np.zeros(_HOURS_PER_YEAR)))
        bench = e923_monthly.get(cls, np.zeros(12))
        btm_annual = btm.get(cls, 0.0) * _MWH_PER_TWH
        if btm_annual > 0 and bench.sum() > 0:
            model_monthly = grid_monthly + btm_annual * (bench / bench.sum())
        else:
            model_monthly = grid_monthly
        _row(cls, model_monthly, bench)
    _row("wind", _hourly_to_monthly(model_hourly.get("wind", np.zeros(_HOURS_PER_YEAR))),
         e923_monthly.get("wind", np.zeros(12)))
    _row("solar (930)",
         _hourly_to_monthly(model_hourly.get("solar", np.zeros(_HOURS_PER_YEAR))),
         e930_solar_monthly)
    _row("nuclear",
         _hourly_to_monthly(model_hourly.get("nuclear", np.zeros(_HOURS_PER_YEAR))),
         e923_monthly.get("nuclear", np.zeros(12)))
    _print_table(rows)


def _print_hourly_fit(year, model_hourly, e930, chp_grid_twh) -> None:
    """[5] Hourly Pearson r and NRMSE vs EIA-930 — non-CHP gas, coal combined."""
    print(f"\n  [5] Hourly dispatch fit — {year} (model vs EIA-930, non-CHP gas)")
    rows = [("fuel", "Pearson r", " NRMSE", "model TWh", "EIA-930 TWh")]
    T = e930["gas"].shape[0]
    gas_m = sum(model_hourly.get(c, np.zeros(T)) for c in _NONCHP_GAS)
    coal_m = sum(model_hourly.get(c, np.zeros(T)) for c in _COAL_CLASSES)
    flat_chp = chp_grid_twh * _MWH_PER_TWH / T
    pairs = [
        ("gas (non-CHP)", gas_m, e930["gas"] - flat_chp),
        ("coal", coal_m, e930["coal"]),
        ("nuclear", model_hourly.get("nuclear", np.zeros(T)), e930.get("nuclear")),
        ("solar", model_hourly.get("solar", np.zeros(T)), e930["solar"]),
        ("wind", model_hourly.get("wind", np.zeros(T)), e930["wind"]),
    ]
    for fuel, m, o in pairs:
        if o is None:
            continue
        rows.append((fuel, f"{_pearson_r(m, o):.3f}", f"{_nrmse(m, o):.3f}",
                     f"{m.sum() / _MWH_PER_TWH:8.2f}",
                     f"{o.sum() / _MWH_PER_TWH:8.2f}"))
    _print_table(rows)


def _print_plant_level(year, dispatch, e923) -> None:
    """[6] Per-plant model vs EIA-923 annual generation for the panel."""
    model_by_plant = (
        dispatch.groupby("plant_code", observed=True)["mw"].sum().to_dict()
    )
    class_by_plant = (
        dispatch[dispatch["plant_code"] > 0]
        .groupby("plant_code", observed=True)["klass"].first().to_dict()
    )
    f923_by_plant = e923.groupby("plant_id")["annual_mwh"].sum().to_dict()
    print(f"\n  [6] Plant-level annual generation — {year} (EIA-923)")
    rows = [("plant", "EIA code", "model GWh", "EIA-923 GWh", "diff %", "class")]
    for code, label in _PLANT_PANEL:
        model_gwh = model_by_plant.get(code, 0.0) / 1e3
        eia_gwh = f923_by_plant.get(code, 0.0) / 1e3
        diff = 100.0 * (model_gwh - eia_gwh) / eia_gwh if eia_gwh else float("nan")
        rows.append((label, str(code), f"{model_gwh:9.0f}", f"{eia_gwh:9.0f}",
                     f"{diff:+6.1f}" if eia_gwh else "    —",
                     str(class_by_plant.get(code, "—"))))
    _print_table(rows)


def report_run(run_dir: Path) -> None:
    """Print the full calibration report from a persisted bundle."""
    meta = json.loads((run_dir / "meta.json").read_text())
    iso = meta["iso"]
    system = pd.read_parquet(run_dir / "system.parquet")
    e930_all = (
        pd.read_parquet(run_dir / "eia930.parquet")
        if (run_dir / "eia930.parquet").exists() else None
    )
    e923_all = pd.read_parquet(run_dir / "eia923.parquet")
    btm_all = pd.read_parquet(run_dir / "btm.parquet")

    print(f"\n{'=' * 80}")
    print(f"  CALIBRATION REPORT  ({iso}; run {meta['timestamp']}; "
          f"git {meta.get('git_sha', '?')})")
    print(f"  bundle: {run_dir}")
    print(f"{'=' * 80}")

    for year in meta["years"]:
        e923 = e923_all[e923_all["year"] == year]
        e923_annual = _e923_annual(e923)
        e923_monthly = _e923_monthly(e923)
        e930 = None
        e930_solar_monthly = np.zeros(12)
        if e930_all is not None:
            ey = e930_all[e930_all["year"] == year]
            e930 = {
                s: ey[ey["series"] == s].sort_values("hour")["mw"].to_numpy()
                for s in ey["series"].unique()
            }
            e930_solar_monthly = _hourly_to_monthly(e930["solar"])

        print(f"\n{'=' * 80}\n  ERCOT {year} BACKCAST\n{'=' * 80}")
        for pass_label in meta["passes"]:
            disp_path = run_dir / "dispatch" / f"{year}_{pass_label}.parquet"
            if not disp_path.exists():
                continue
            if len(meta["passes"]) > 1:
                tag = "P1 (pre-commitment)" if pass_label == "P1" else "P2 (committed)"
                print(f"\n  ----- {tag} -----")
            dispatch = pd.read_parquet(disp_path)
            sysd = system[(system["year"] == year) & (system["pass"] == pass_label)]
            btm = dict(zip(
                btm_all[(btm_all["year"] == year) & (btm_all["pass"] == pass_label)]["klass"],
                btm_all[(btm_all["year"] == year) & (btm_all["pass"] == pass_label)]["btm_twh"],
            ))
            model_hourly = _class_hourly(dispatch)
            model_twh = {k: v.sum() / _MWH_PER_TWH for k, v in model_hourly.items()}

            chp_grid_twh = _print_chp(year, model_twh, btm, e923_annual)

            model_grid = dispatch["mw"].sum() / _MWH_PER_TWH
            net_gen = (
                e930["net_gen"].sum() / _MWH_PER_TWH if e930 is not None
                else float("nan")
            )
            model_target = sysd["demand"].sum() / _MWH_PER_TWH
            unserved = sysd["slack"].sum() / _MWH_PER_TWH
            _print_reconciliation(
                year, net_gen, model_target, model_grid, unserved, sum(btm.values()),
            )
            if e930 is not None:
                _print_nonchp_grid(year, model_hourly, e930, chp_grid_twh)
            _print_thermal_annual(year, model_twh, btm, e923_annual)
            _print_monthly(year, model_hourly, e923_monthly, e930_solar_monthly,
                           btm, e923_annual)
            if e930 is not None:
                _print_hourly_fit(year, model_hourly, e930, chp_grid_twh)
            _print_plant_level(year, dispatch, e923)


def main() -> None:
    """Solve + persist a timestamped bundle and report it, or report an old one."""
    parser = argparse.ArgumentParser(
        description="ERCOT calibration backcast: solve, persist, report."
    )
    parser.add_argument("--year", nargs="+", type=int, default=[2023, 2024])
    parser.add_argument("--iso", default="ERCOT")
    parser.add_argument("--hours", type=int, default=_HOURS_PER_YEAR)
    parser.add_argument(
        "--commitment", action="store_true",
        help="Run the P2 unit-commitment pass after P1; both are persisted.",
    )
    parser.add_argument(
        "--no-coal-p2", action="store_true",
        help="Pin coal to its P1 dispatch in P2 (coal gains no new P2 gen).",
    )
    parser.add_argument(
        "--report", metavar="DIR", default=None,
        help="Skip solving; print the report from an existing bundle directory.",
    )
    parser.add_argument(
        "--out-dir", default=None,
        help="Bundle root (default results/calibration/<timestamp>).",
    )
    args = parser.parse_args()

    if args.report:
        report_run(Path(args.report))
        return

    iso = args.iso.upper()
    reference = _load_reference()
    if args.out_dir:
        run_dir = Path(args.out_dir)
    else:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = REPO / "results" / "calibration" / ts
    run_dir = solve_and_persist(
        args.year, iso, args.hours, reference,
        commitment=args.commitment, screen_coal=not args.no_coal_p2,
        run_dir=run_dir,
    )
    report_run(run_dir)


if __name__ == "__main__":
    main()
