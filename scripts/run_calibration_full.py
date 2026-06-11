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
import gzip
import json
import logging
import pickle
import subprocess
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.plant_taxonomy import (  # noqa: E402
    classes_for_fuel930, classify_plant, coal_code_to_class, fossil_classes,
)
from market_sim.data import campd  # noqa: E402
from market_sim.data.eia923 import (  # noqa: E402
    load_monthly_generation,
    monthly_netgen_columns,
)
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_eia_hourly_benchmark,
    pjm_net_interchange,
    load_ercot_battery_gen,
    load_ercot_fossil_gen,
    load_ercot_nuclear_gen,
    load_ercot_renewable_gen,
)
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402
from market_sim.model.transmission import extend_with_import_node  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    _COAL_SUPPLY_TO_CURVE,
    coal_supply_class,
)
from market_sim.results.calibration import check_cf_band_occupancy  # noqa: E402
from scripts.run_calibration import (  # noqa: E402
    _calibration_config,
    _commitment_pass,
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
# All class groupings derive from the canonical taxonomy
# (market_sim.config.plant_taxonomy) — no hardcoded class lists.
_GAS_CLASSES: tuple[str, ...] = classes_for_fuel930("gas")
_COAL_CLASSES: tuple[str, ...] = classes_for_fuel930("coal")
# CHP classes — reported in their own dedicated table and excluded from every
# other comparison.
_CHP_CLASSES: tuple[str, ...] = tuple(
    c for c in _GAS_CLASSES if c.endswith("_CHP"))
_NONCHP_GAS: tuple[str, ...] = tuple(
    c for c in _GAS_CLASSES if not c.endswith("_CHP"))
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

# CF-band width for the per-plant operating-level histogram ([7b] panel and
# plant_cf_bands.parquet): 0.10 -> ten 10%-of-capacity bands. Coarse enough
# to be robust to CAMPD net-vs-gross noise, fine enough to separate a CC's
# committed floor / part-load / duct-fired modes.
_CF_BAND_WIDTH: float = 0.10


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def _coal_supply_class(plant_code: int, fuel_code: str = "") -> str:
    """Return the coal supply class (``COAL_BIT`` / ``COAL_WC`` /
    ``COAL_LIGNITE`` / ``COAL_PRB``) for a coal plant.

    Uses the authoritative model mapping (:func:`coal_supply_class`, which
    merges the curated ERCOT lignite/PRB map with the EIA-923-derived per-ISO
    ranks) so the model and the EIA-923 benchmark split coal the same way. For
    a plant not in either map, fall back to the EIA-923 receipt fuel code
    (``LIG``/``SUB``/``WC``/``BIT``); unknown -> generic ``COAL``.
    """
    key = _COAL_SUPPLY_TO_CURVE.get(coal_supply_class(int(plant_code)))
    return key or coal_code_to_class(fuel_code) or "COAL"


def _model_class_for_unit(unit_id: str, fuel: str, eff_bin: str) -> str:
    """Return the model class for one generator unit id.

    CAMPD generator ids carry their Plant_Group through ``efficiency_bin``
    (e.g. ``CC_REGULAR_Houston_p60122_econ``). Non-CAMPD generators fall back
    to a class derived from the fuel type. Coal is returned as the bare
    ``COAL`` here; the caller splits it into the supply class.
    """
    if eff_bin in {*_GAS_CLASSES, "COAL"}:
        return eff_bin
    # Non-CAMPD fleets (every non-ERCOT ISO, e.g. PJM's per-plant EIA-860
    # fleet) carry no Plant_Group in ``eff_bin``, so derive the class from the
    # model fuel type — giving each plant its proper class (one plant per bin)
    # instead of collapsing the thermal fleet into OTHER. ERCOT is unaffected:
    # its CAMPD units return at the ``eff_bin`` branch above.
    if fuel == "coal":
        return "COAL"
    if fuel == "import":
        return "import"
    if fuel in {"gas_cc", "gas_cc_ccs"}:
        return "CC_REGULAR"
    if fuel == "gas_ct":
        return "CT_PEAKER"
    if fuel == "gas_st":
        return "ST_GAS"
    if fuel == "nuclear":
        return "nuclear"
    if fuel == "hydro":
        return "hydro"
    if fuel in {"wind", "offshore_wind"}:
        return "wind"
    if fuel == "solar":
        return "solar"
    if fuel == "oil":
        return "oil"
    if fuel == "biomass":
        return "biomass"
    return "OTHER"


def _classify_f923(
    fuel: str, pm: str, chp: bool, plant_id: int
) -> str:
    """Bucket one EIA-923 Page-1 row into a model class.

    Thin wrapper over the canonical
    :func:`market_sim.config.plant_taxonomy.classify_plant` — the single source
    of truth the model fleet uses too, so the benchmark and the model bucket a
    plant identically by construction. Coal is split into its supply class
    (ERCOT lignite/PRB; EIA-923-derived bituminous / sub-bituminous / waste
    elsewhere) via :func:`_coal_supply_class`.
    """
    return classify_plant(
        fuel, pm, chp, plant_id, coal_class_resolver=_coal_supply_class
    )


def _plant_codes_from_unit_ids(
    unit_ids: list[str], numeric_head: bool = False
) -> np.ndarray:
    """Return ``(n_gen,)`` plant codes parsed from the unit id.

    ERCOT CAMPD ids carry the code as a ``..._p{code}_<suffix>`` token. The
    EIA-860 per-plant fleet (every non-ERCOT ISO, e.g. PJM) instead names units
    ``{plant_code}_{generator_id}`` (e.g. ``54_GT1``); with ``numeric_head`` the
    leading all-digit token is used when no ``p{code}`` token is present.
    ``numeric_head`` is off for ERCOT, so its dispatch frame is unchanged (ERCOT
    nuclear shares the ``{code}_{gen}`` shape but is not matched by plant code).
    """
    out = np.zeros(len(unit_ids), dtype=int)
    for i, uid in enumerate(unit_ids):
        for token in uid.split("_"):
            if token.startswith("p") and token[1:].isdigit():
                out[i] = int(token[1:])
                break
        else:
            head = uid.split("_", 1)[0]
            if numeric_head and head.isdigit():
                out[i] = int(head)
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
    iso: str = "ERCOT",
    must_run: dict[str, np.ndarray] | None = None,
) -> pd.DataFrame:
    """Return the long per-generator-hour dispatch frame for one year-pass.

    One row per (generator, hour) carrying the dispatched MW and the
    generator's class / fuel / supply / zone, plus wind and solar (and any
    injected must-run residual classes) as per-zone pseudo-units so the frame
    reconciles to total grid generation.
    """
    disp = np.asarray(result.dispatch, dtype=np.float32)
    n_gen, T = disp.shape
    unit_ids = list(context.unit_ids)
    fuels = list(context.fuel_types)
    bins = list(context.efficiency_bins)
    zones = list(context.zones)
    pgroups = list(getattr(context, "plant_groups", []) or [])
    is_ercot = iso == "ERCOT"
    plant_codes = _plant_codes_from_unit_ids(
        unit_ids, numeric_head=not is_ercot
    )

    klass = []
    supply = []
    for g in range(n_gen):
        # Non-ERCOT fleets carry the real plant group (CC_CHP, CT_CHP, ST_GAS,
        # ... distinct from the merchant variants), so class by it rather than
        # collapsing by fuel. ERCOT keeps the efficiency-bin path. Nuclear /
        # wind / solar carry no group and fall back to the fuel classifier.
        if not is_ercot and g < len(pgroups) and pgroups[g]:
            k = pgroups[g]
        else:
            k = _model_class_for_unit(unit_ids[g], fuels[g], bins[g])
        if k == "COAL":
            # Split coal into its supply class — ERCOT mine-mouth lignite /
            # PRB-by-rail, and the EIA-923-derived bituminous / sub-bituminous /
            # waste ranks for other ISOs (a single COAL only for unclassified
            # plants). The raw supply string rides along in ``supply``.
            k = _coal_supply_class(int(plant_codes[g]))
            supply.append(coal_supply_class(int(plant_codes[g])))
        else:
            supply.append("")
        klass.append(k)

    # Zonal LMP (the dispatch LP's energy-balance dual) carried per
    # generator-hour, so unit revenue (mw x lmp) and commitment economics are
    # queryable straight from this frame. zone_idx maps each generator to its
    # zone's price row.
    prices = np.asarray(result.prices, dtype=np.float32)
    zone_to_idx = {z: i for i, z in enumerate(zone_names)}
    gen_zidx = np.array([zone_to_idx[z] for z in zones], dtype=int)

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
        "lmp": prices[gen_zidx, :].reshape(-1),
    })]

    pseudo = [
        ("wind", result.wind_dispatched), ("solar", result.solar_dispatched),
    ]
    # Injected must-run residual classes (biomass / hydro / OTHER), re-added per
    # zone so total model generation reconciles to load (they were netted out of
    # the LP's demand). Carry klass == fuel == the class key.
    for klass, arr in (must_run or {}).items():
        pseudo.append((klass, arr))
    for name, arr in pseudo:
        a = np.asarray(arr, dtype=np.float32)[:, :T]
        for z in range(a.shape[0]):
            zone = zone_names[z]
            frames.append(pd.DataFrame({
                "unit_id": f"{name.upper()}_{zone}",
                "plant_code": np.int32(0),
                "klass": name, "fuel": name, "supply": "",
                "zone": zone, "hour": np.arange(T, dtype=np.int32), "mw": a[z],
                "lmp": prices[z],
            }))

    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "pass", pass_label)
    df.insert(0, "year", np.int16(year))
    for col in ("pass", "unit_id", "klass", "fuel", "supply", "zone"):
        df[col] = df[col].astype("category")
    df["mw"] = df["mw"].astype(np.float32)
    df["lmp"] = df["lmp"].astype(np.float32)
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


def _storage_frame(
    year: int, pass_label: str, result, storage_units,
) -> pd.DataFrame | None:
    """Return the long per-storage-unit hourly charge/discharge frame.

    One row per (storage unit, hour) carrying the unit's charge and
    discharge MW plus its tech (li_ion / pumped_storage) and zone, so the
    bundle exposes storage throughput the way ``dispatch/`` exposes
    generator output. Returns ``None`` when the fleet is empty.
    """
    if not storage_units or result.storage_discharge is None:
        return None
    chg = np.asarray(result.storage_charge, dtype=np.float32)
    dis = np.asarray(result.storage_discharge, dtype=np.float32)
    n_storage, T = dis.shape
    hours = np.tile(np.arange(T, dtype=np.int32), n_storage)
    rep = lambda vals: np.repeat(np.asarray(vals, dtype=object), T)  # noqa: E731
    df = pd.DataFrame({
        "unit_id": rep([u.unit_id for u in storage_units]),
        "tech": rep([u.tech_name for u in storage_units]),
        "zone": rep([u.zone for u in storage_units]),
        "hour": hours,
        "charge_mw": chg.reshape(-1),
        "discharge_mw": dis.reshape(-1),
    })
    df.insert(0, "pass", pass_label)
    df.insert(0, "year", np.int16(year))
    for col in ("pass", "unit_id", "tech", "zone"):
        df[col] = df[col].astype("category")
    return df


def _eia930_frame(year: int, iso: str, iso_config) -> pd.DataFrame | None:
    """Return the EIA-930 hourly benchmark series for a year, long format.

    ERCOT keeps its dedicated full-year fossil/nuclear/renewable loaders (so
    its bundle is unchanged). Every other ISO is served by the generic per-BA
    benchmark loader, which also carries the BA's net generation and net
    interchange and tolerates a BA-year a few hours short of 8760.

    The ERCOT battery series (``battery_discharge`` / ``battery_charge``)
    keep NaN over hours the BA had not yet begun reporting them (the series
    start mid-2024), so a partial year still benchmarks its reported window.
    """
    if iso != "ERCOT":
        return _eia930_frame_generic(year, iso)

    fossil = load_ercot_fossil_gen(year)
    renew = load_ercot_renewable_gen(year)
    if fossil is None or renew is None:
        return None
    nuclear = load_ercot_nuclear_gen(year)
    battery = load_ercot_battery_gen(year)
    # net generation = Demand + Interchange = load_demand with no gross-up.
    net_gen = load_demand(iso, year, iso_config, td_loss_factor=0.0).sum(axis=0)
    series = {
        "gas": fossil["gas"], "coal": fossil["coal"],
        "wind": renew["wind"], "solar": renew["solar"], "net_gen": net_gen,
    }
    if nuclear is not None:
        series["nuclear"] = nuclear
    if battery is not None:
        series.update(battery)
    out = []
    for name, arr in series.items():
        a = np.asarray(arr, dtype=float)
        out.append(pd.DataFrame({
            "year": np.int16(year), "series": name,
            "hour": np.arange(a.shape[0], dtype=np.int32), "mw": a,
        }))
    return pd.concat(out, ignore_index=True)


def _eia930_frame_generic(year: int, iso: str) -> pd.DataFrame | None:
    """Return the EIA-930 hourly benchmark for a non-ERCOT ISO, long format.

    Carries each delivered per-fuel series plus the BA's net generation and
    net interchange, read straight from the per-BA ``<BA> hourly`` extract.
    """
    bench = load_eia_hourly_benchmark(iso, year)
    if bench is None:
        return None
    out = []
    for name, arr in bench.items():
        a = np.asarray(arr, dtype=float)
        out.append(pd.DataFrame({
            "year": np.int16(year), "series": name,
            "hour": np.arange(a.shape[0], dtype=np.int32), "mw": a,
        }))
    return pd.concat(out, ignore_index=True)


def _parasitic_factor_map() -> dict[int, float]:
    """Return ``{plant_id: net/gross factor}`` from the derived artifact.

    Empty when the artifact is missing — the per-plant hourly fit then
    falls back to scaling CAMPD gross by 1.0 (treating gross as net), which
    only shifts the level, not the timing the correlation cares about.
    """
    path = REPO / "inputs" / "processed" / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}
    return campd.pooled_factor_map(pd.read_parquet(path))


def _fleet_group_by_code(iso: str, iso_config) -> dict[int, str]:
    """Return ``{plant_code: plant_group}`` from the EIA-860 per-plant fleet.

    The non-ERCOT analogue of the ERCOT CAMPD bin sheet's plant->group map,
    used to bucket the CAMPD/EIA-923 benchmark backfill. Built from the fleet's
    ``plant_group`` (COAL / CC_REGULAR / CT_PEAKER / ST_GAS / their CHP
    variants), so it matches the dispatch frame's classes.
    """
    from market_sim.data.fleet import load_fleet_from_csv

    out: dict[int, str] = {}
    for g in load_fleet_from_csv(iso, iso_config):
        code = int(g.plant_code)
        if code > 0 and g.plant_group:
            out[code] = g.plant_group
    return out


def _campd_hourly_frame(
    year: int, iso: str, factors: dict[int, float], hours: int,
) -> pd.DataFrame | None:
    """Return the per-plant 8760-hour CAMPD **net** generation frame.

    One row per ``(plant_id, hour)`` carrying net MW (CAMPD gross scaled by
    the plant's parasitic factor). ``None`` when no CAMPD extract covers the
    ISO's states for the year.
    """
    states = campd.states_for_iso(iso)
    if not states:
        return None
    df = campd.load_campd_hourly(states, [year])
    if df.empty:
        return None
    net = campd.plant_hourly_net(df, factors, year, hours=hours)
    if not net:
        return None
    frames = [
        pd.DataFrame({
            "year": np.int16(year),
            "plant_id": np.int32(plant_id),
            "hour": np.arange(series.shape[0], dtype=np.int32),
            "net_mw": series.astype(np.float32),
        })
        for plant_id, series in net.items()
    ]
    return pd.concat(frames, ignore_index=True)


@lru_cache(maxsize=8)
def _iso_plant_ids(iso: str) -> frozenset[int]:
    """ORIS codes physically located in ``iso`` (eGRID/EIA-860 BA geography).

    EIA-923's ``generation`` table is national; without restricting to the
    ISO the per-class benchmark totals leak in every other US plant (e.g. PRB
    coal shows the ~639 TWh national figure instead of ERCOT's ~47 TWh).
    """
    return frozenset(build_zone_lookup(iso))


def _eia923_frame(
    year: int, generation: pd.DataFrame, iso: str = "ERCOT",
) -> pd.DataFrame:
    """Return EIA-923 net generation per (plant, class), annual and monthly.

    Restricted to plants in ``iso`` so the per-class totals are the ISO's
    actual generation, not the national EIA-923 sum.
    """
    df = generation[generation["year"] == year].copy()
    iso_plants = _iso_plant_ids(iso)
    if iso_plants:
        df = df[df["plant_id"].isin(iso_plants)].copy()
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


# Residual / non-fossil classes injected into the dispatch as must-run
# resources: they serve load exogenously (biomass/landfill, refinery process
# gas, purchased steam, ...) rather than clearing the LP merit order. Oil is
# NOT here — it is a price-responsive peaker dispatched in the LP. Hydro is
# NOT here either: conventional hydro is an LP unit with a monthly energy
# budget (run_calibration._hydro_fleet) and pumped storage is a storage
# resource (load_eia860_pumped_storage), so injecting it would double-count.
_INJECTED_MUSTRUN_CLASSES: tuple[str, ...] = ("biomass", "OTHER")


def _hour_months(year: int, hours: int) -> np.ndarray:
    """``(hours,)`` array of 1-based calendar month for each hour-of-year."""
    idx = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    return idx.month.to_numpy()


@lru_cache(maxsize=1)
def _pumped_storage_plant_ids() -> frozenset[int]:
    """EIA plant ids with pumped-storage (prime mover ``PS``) generators.

    Used to hold PS plants out of the injected OTHER must-run profile —
    ``classify_plant`` buckets PS into OTHER, but PS is dispatched as an LP
    storage resource (``load_eia860_pumped_storage``), so leaving its EIA-923
    net generation in the injection would double-count it.
    """
    from market_sim.data.fleet import EIA_860_DIR, EIA_860_PARQUET_NAME

    path = EIA_860_DIR / EIA_860_PARQUET_NAME
    if not path.exists():
        return frozenset()
    df = pd.read_parquet(path, columns=["plant_id", "prime_mover"])
    ps = df[df["prime_mover"].astype(str).str.upper() == "PS"]
    return frozenset(int(p) for p in ps["plant_id"].unique())


def _must_run_profiles(
    year: int, generation: pd.DataFrame, iso: str, demand: np.ndarray,
    skip_classes: frozenset[str] = frozenset(),
) -> dict[str, np.ndarray]:
    """Per-zone hourly must-run MW for each injected residual class.

    Each class's EIA-923 annual generation is shaped by its monthly profile
    (flat within a month, negatives clamped then rescaled to preserve the net
    annual energy) and split across zones by their share of annual demand.
    ``skip_classes`` drops classes the LP fleet already represents as units
    (e.g. biomass for the per-plant non-ERCOT fleets), so nothing is served
    twice. Pumped-storage plants are held out of OTHER — they dispatch as LP
    storage. Returns ``{klass: (n_zones, hours) MW}`` for the classes with
    positive net generation in ``iso`` and ``year``.
    """
    n_zones, hours = demand.shape
    e923 = _eia923_frame(year, generation, iso=iso)
    months = _hour_months(year, hours)
    hours_per_month = np.array(
        [(months == m).sum() for m in range(1, 13)], dtype=float)
    zone_tot = demand.sum(axis=1)
    grand = zone_tot.sum()
    zone_share = (zone_tot / grand) if grand > 0 \
        else np.full(n_zones, 1.0 / n_zones)
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    out: dict[str, np.ndarray] = {}
    for klass in _INJECTED_MUSTRUN_CLASSES:
        if klass in skip_classes:
            continue
        rows = e923[e923["klass"] == klass]
        if klass == "OTHER":
            rows = rows[~rows["plant_id"].isin(_pumped_storage_plant_ids())]
        annual = float(rows["annual_mwh"].sum())
        if annual <= 0:
            continue
        monthly = np.clip(rows[mcols].sum().to_numpy(dtype=float), 0.0, None)
        if monthly.sum() <= 0:
            monthly = hours_per_month.copy()  # no monthly detail -> flat
        with np.errstate(divide="ignore", invalid="ignore"):
            mw_by_month = np.where(
                hours_per_month > 0, monthly / hours_per_month, 0.0)
        prof = mw_by_month[months - 1]
        psum = float(prof.sum())
        if psum <= 0:
            continue
        prof = prof * (annual / psum)  # preserve net annual energy
        out[klass] = zone_share[:, None] * prof[None, :]
    return out


# EIA-923 lags for recent years (2025): plants that ran can report ~0 net gen.
# Below this annual threshold, if CAMPD net is above it, the plant is treated
# as under-reported and the benchmark is backfilled with CAMPD net.
_CAMPD_BACKFILL_MIN_MWH: float = 50_000.0  # 50 GWh
# Non-CHP grid groups eligible for CAMPD backfill (CHP kept on EIA-923 — the
# host-steam split is absent from CAMPD net).
_BACKFILL_GROUPS: frozenset[str] = frozenset(
    {"COAL", "CC_REGULAR", "ST_GAS", "CT_PEAKER"}
)


def _backfill_eia923_with_campd(
    e923: pd.DataFrame, campd_year: pd.DataFrame | None,
    group_by_code: dict[int, str], year: int,
) -> pd.DataFrame:
    """Backfill EIA-923 with CAMPD net for model plants it under-reports.

    For each non-CHP grid plant (coal / CC_REGULAR / ST_GAS / CT_PEAKER) whose
    EIA-923 annual is below :data:`_CAMPD_BACKFILL_MIN_MWH` while CAMPD net is
    above it, set the benchmark annual + monthly to CAMPD net (gross x
    parasitic factor), keyed to the plant's class. Plants EIA-923 already
    reports (e.g. V H Braunig, R W Miller) are untouched.
    """
    if campd_year is None or campd_year.empty:
        return e923
    e923 = e923.copy()
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    month1 = _hour_to_month(int(campd_year["hour"].max()) + 1)  # 1-based
    add, n_repl = [], 0
    for pid, sub in campd_year.groupby("plant_id"):
        group = group_by_code.get(int(pid))
        if group not in _BACKFILL_GROUPS:
            continue
        net = sub.sort_values("hour")["net_mw"].to_numpy(dtype=float)
        if net.sum() < _CAMPD_BACKFILL_MIN_MWH:
            continue
        if group == "COAL":
            klass = _coal_supply_class(int(pid))
        else:
            klass = group
        cur = e923[(e923["plant_id"] == int(pid)) & (e923["klass"] == klass)]
        if float(cur["annual_mwh"].sum()) >= _CAMPD_BACKFILL_MIN_MWH:
            continue  # EIA-923 reports it adequately
        monthly = {
            mcols[m]: float(net[month1[:len(net)] == m + 1].sum())
            for m in range(12)
        }
        if len(cur):
            i = cur.index[0]
            e923.at[i, "annual_mwh"] = float(net.sum())
            for k, v in monthly.items():
                e923.at[i, k] = v
            n_repl += 1
        else:
            add.append({
                "year": np.int16(year), "plant_id": int(pid), "klass": klass,
                "annual_mwh": float(net.sum()), **monthly,
            })
    if add or n_repl:
        logger.info(
            "EIA-923 %d: CAMPD-backfilled %d under-reported plants "
            "(%d replaced, %d added)", year, n_repl + len(add), n_repl, len(add),
        )
    if add:
        e923 = pd.concat([e923, pd.DataFrame(add)], ignore_index=True)
    return e923


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
    # The EIA-923 bins carry the 923-dominant class for the year, so the bin's
    # class is what the plant actually burned (no curated drift).
    bins = load_campd_bins(ScenarioConfig().campd_bins_path, year=year)
    # Key BTM off the plant's PER-CLASS EIA-923 net generation — the 923 total
    # of the bin's own class, not whole-plant netgen. A plant that splits across
    # classes (e.g. a merchant CC block plus a CHP train) then can't lend one
    # class's output to another, so a class total can't exceed its real EIA-923.
    f923 = generation[generation["year"] == year].copy()
    f923["klass"] = [
        _classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
        for f, pm, c, pid in zip(
            f923["fuel_type"], f923["prime_mover"], f923["chp"], f923["plant_id"]
        )
    ]
    class_total = f923.groupby(["plant_id", "klass"])["netgen_annual_mwh"].sum()
    total_by_plant = {
        int(code): float(class_total.get((int(code), str(grp)), 0.0))
        for code, grp in zip(bins["Plant_Code"], bins["Plant_Group"])
    }
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


def _highspy_version() -> str:
    """Return the installed highspy version, or '' if unavailable."""
    try:
        from importlib.metadata import version
        return version("highspy")
    except Exception:
        return ""


def _git_sha() -> str:
    """Return the current git short SHA, or '' if unavailable."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def _git(*args: str) -> str:
    """Run a git command in REPO and return stripped stdout (or '')."""
    try:
        return subprocess.check_output(
            ["git", *args], cwd=REPO, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


# Paths excluded from the manifest's git state: a run's own outputs (and other
# bundles) are not "model changes" and would just be noise.
_GIT_STATE_EXCLUDE = (":(exclude)results", ":(exclude)outputs")


def _git_state() -> dict:
    """Capture git provenance so a bundle records exactly which code ran.

    Returns the short SHA, branch, a ``dirty`` flag, the list of changed model
    files, and a diffstat. ``results/`` and ``outputs/`` are excluded so the
    state reflects model/source edits, not the run's own artifacts. When dirty
    the run included uncommitted model changes; the caller snapshots the diff.
    """
    porcelain = _git("status", "--porcelain", "--", *_GIT_STATE_EXCLUDE)
    changed = [ln[3:] for ln in porcelain.splitlines()] if porcelain else []
    return {
        "sha": _git("rev-parse", "--short", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(porcelain),
        "changed_files": changed,
        "diffstat": _git("diff", "--stat", "HEAD", "--", *_GIT_STATE_EXCLUDE),
    }


def _parse_offer_curve_json(raw: str | None, flag: str = "--offer-curve-json") -> dict | None:
    """Parse an offer-curve JSON argument, failing fast on bad input.

    Accepts an inline JSON object, a path to a ``.json`` file, or ``None``.
    Returns the parsed ``{class: {band: number}}`` mapping, or ``None`` when
    nothing was given. Used for both the absolute ``--offer-curve-json`` and
    the relative ``--offer-curve-delta-json`` (same shape: class -> band ->
    number). Raises ``SystemExit`` with a clear, ``flag``-tagged message on
    malformed JSON or the wrong shape so a CI run fails loudly rather than
    silently solving against the wrong curve.
    """
    if raw is None or not str(raw).strip():
        return None
    text = raw
    candidate = Path(raw)
    if not raw.lstrip().startswith("{") and candidate.exists():
        text = candidate.read_text()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"{flag}: invalid JSON ({exc}). Expected an object "
            'like {"CT_PEAKER":{"committed":1.40,"econ_low":1.27}}.')
    if not isinstance(parsed, dict):
        raise SystemExit(
            f"{flag}: top level must be a JSON object keyed by "
            f"fleet class, got {type(parsed).__name__}.")
    valid_classes = set(fossil_classes())
    for cls, bands in parsed.items():
        # Fail loudly on a class key the offer-curve router will never read
        # (e.g. COAL_SUB after the SUB -> COAL_PRB taxonomy rename): a dead
        # knob silently tunes nothing, which is worse than an error.
        if cls not in valid_classes:
            raise SystemExit(
                f"{flag}: unknown fleet class {cls!r} — the offer-curve "
                f"router only reads {sorted(valid_classes)}. (Sub-bituminous "
                "coal is COAL_PRB; COAL_SUB no longer exists.)")
        if not isinstance(bands, dict):
            raise SystemExit(
                f"{flag}: value for {cls!r} must be an object of "
                f"band->number, got {type(bands).__name__}.")
        for band, val in bands.items():
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise SystemExit(
                    f"{flag}: {cls}.{band} must be a number, got "
                    f"{val!r}.")
    return parsed


def write_run_config(run_dir: Path, cfg, meta: dict, note: str = "") -> None:
    """Write ``run_config.json`` (and ``model_changes.diff`` if dirty).

    A discrete, self-contained record of what was run: the full resolved
    ``ScenarioConfig`` (every knob), the calibration flags, git provenance,
    and any free-text note describing pre-run model changes. The companion
    ``model_changes.diff`` snapshots uncommitted edits so the exact code is
    reproducible from the bundle alone.
    """
    import dataclasses

    git = _git_state()
    payload = {
        "timestamp": meta.get("timestamp"),
        "git": git,
        "model_changes_note": note,
        "calibration_flags": {
            k: meta.get(k) for k in (
                "iso", "years", "hours", "passes", "commitment",
                "commitment_screen_coal", "gas_prices", "outage_source",
                "coal_lignite_mustrun", "coal_prb_mustrun",
                "coal_prb_passthrough", "coal_prb_passthrough_sigmoid",
                "coal_mustrun_per_plant", "coal_drop_pof",
                "coal_prb_passthrough_tiered", "coal_plant_monthly_pricing",
                "td_loss_factor", "offer_curve_overrides",
                "offer_curve_deltas", "priced_interchange", "git_sha",
            )
        },
        "scenario_config": dataclasses.asdict(cfg),
    }
    (run_dir / "run_config.json").write_text(
        json.dumps(payload, indent=2, default=str)
    )
    if git["dirty"]:
        diff = _git("diff", "HEAD", "--", *_GIT_STATE_EXCLUDE)
        if diff:
            (run_dir / "model_changes.diff").write_text(diff)


def solve_and_persist(
    years: list[int], iso: str, hours: int, reference: dict,
    commitment: bool, screen_coal: bool, run_dir: Path,
    coal_lignite_mustrun: float | None = None,
    coal_prb_mustrun: float | None = None,
    coal_prb_passthrough: float = 1.0,
    persist_p2_state: bool = False,
    outage_source: str = "historic",
    coal_prb_passthrough_sigmoid: bool = False,
    coal_mustrun_per_plant: bool = False,
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    prb_overrides: dict | None = None,
    plant_tranche_config: str | None = None,
    storage_daily_cycling: bool = False,
    battery_dispatch_adder: float = 0.0,
    gas_offer_curve: bool = False,
    gas_monthly_actuals: bool = False,
    offer_curve_overrides: dict | None = None,
    offer_curve_deltas: dict | None = None,
    curve_smoothing: dict | None = None,
    cc_derate_from_top: bool = False,
    priced_interchange: bool = False,
    note: str = "",
) -> Path:
    """Solve every year/pass, write the parquet bundle, return the run dir."""
    iso_config = get_iso_config(iso)
    if priced_interchange:
        # Interchange served by the priced import/export node (external zone
        # + import tranches + export sinks) instead of the measured schedule;
        # the bundle's zone set and demand frames follow the extended
        # topology so they match run_year's solve.
        iso_config = extend_with_import_node(iso_config)
    zone_names = iso_config.zone_names
    (run_dir / "dispatch").mkdir(parents=True, exist_ok=True)

    # Per-plant CAMPD net + EIA-923 benchmarks are built for any ISO whose
    # CAMPD CEMS state extracts are present (ERCOT = TX; PJM = PA/NJ/MD/DE/IL/IN
    # ...). The class map keying the CAMPD/EIA-923 backfill comes from the
    # curated ERCOT bin sheet for ERCOT and from the per-plant EIA-860 fleet's
    # plant_group for every other ISO. BTM CHP (host-steam split) stays
    # ERCOT-only. ISOs with no CAMPD coverage keep the energy-only bundle
    # (dispatch + system prices + EIA-930). ERCOT is unchanged.
    is_ercot = iso == "ERCOT"
    has_campd = bool(campd.states_for_iso(iso))
    generation = load_monthly_generation()
    parasitic_factors = _parasitic_factor_map()
    if is_ercot:
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import load_campd_bins
        _bins = load_campd_bins(ScenarioConfig().campd_bins_path)
        group_by_code = dict(
            zip(_bins["Plant_Code"].astype(int), _bins["Plant_Group"])
        )
    else:
        group_by_code = _fleet_group_by_code(iso, iso_config)
    system_frames, eia930_frames, eia923_frames, btm_frames = [], [], [], []
    campd_frames: list[pd.DataFrame] = []
    storage_frames: list[pd.DataFrame] = []
    gas_prices: dict[int, float] = {}
    passes_seen: set[str] = set()

    for year in years:
        gas_price = _henry_hub_actual(reference, year)
        gas_prices[year] = gas_price
        cfg = _calibration_config(year, iso, hours, gas_price)
        demand = load_demand(
            iso, year, iso_config, td_loss_factor=cfg.td_loss_factor,
            include_interchange=not priced_interchange,
        )
        # Must-run residual classes (biomass / other-gas / ...) are netted out
        # of demand for the LP and re-added as pseudo-units in the dispatch
        # frame, so they displace marginal gas and appear as their own classes
        # instead of an invisible OTHER gap. Applies to every ISO; classes the
        # LP fleet already carries as units are skipped — the ERCOT CAMPD-bin
        # fleet deliberately drops biomass units in favor of this injection
        # (run_calibration.run_year), while the per-plant fleet of every other
        # ISO keeps biomass as raw LP units. Hydro is an LP resource for all
        # ISOs (budget hydro + pumped storage), never injected.
        must_run = _must_run_profiles(
            year, generation, iso, demand,
            skip_classes=frozenset() if is_ercot else frozenset({"biomass"}),
        )
        must_run_total = (
            np.sum(list(must_run.values()), axis=0) if must_run else None
        )
        logger.info(
            "solving %s %d (hours=%d, Henry Hub=$%.2f/MMBtu, commitment=%s)",
            iso, year, hours, gas_price, commitment,
        )
        result, context, result_p1, p2_state = run_year(
            year, iso, hours, gas_price, ttc_overrides={},
            commitment_enabled=commitment, commitment_screen_coal=screen_coal,
            coal_lignite_mustrun=coal_lignite_mustrun,
            coal_prb_mustrun=coal_prb_mustrun,
            coal_prb_passthrough=coal_prb_passthrough,
            outage_source=outage_source,
            coal_prb_passthrough_sigmoid=coal_prb_passthrough_sigmoid,
            coal_mustrun_per_plant=coal_mustrun_per_plant,
            coal_drop_pof=coal_drop_pof,
            coal_prb_passthrough_tiered=coal_prb_passthrough_tiered,
            prb_overrides=prb_overrides,
            plant_tranche_config=plant_tranche_config,
            storage_daily_cycling=storage_daily_cycling,
            battery_dispatch_adder=battery_dispatch_adder,
            gas_offer_curve=gas_offer_curve,
            gas_monthly_actuals=gas_monthly_actuals,
            offer_curve_overrides=offer_curve_overrides,
            offer_curve_deltas=offer_curve_deltas,
            curve_smoothing=curve_smoothing,
            cc_derate_from_top=cc_derate_from_top,
            must_run_mw=must_run_total,
            priced_interchange=priced_interchange,
        )
        if persist_p2_state:
            _save_p2_state(run_dir, year, p2_state)
        labelled = [("P2" if result_p1 is not None else "P1", result)]
        if result_p1 is not None:
            labelled.insert(0, ("P1", result_p1))

        for label, res in labelled:
            passes_seen.add(label)
            _dispatch_frame(
                year, label, res, context, zone_names, iso=iso,
                must_run=must_run,
            ).to_parquet(
                run_dir / "dispatch" / f"{year}_{label}.parquet", index=False
            )
            system_frames.append(
                _system_frame(year, label, res, demand, zone_names)
            )
            storage_frame = _storage_frame(
                year, label, res, p2_state["storage_units"]
            )
            if storage_frame is not None:
                storage_frames.append(storage_frame)
            if is_ercot:
                btm_frames.append(
                    _btm_frame(year, label, res, context, generation)
                )

        e930 = _eia930_frame(year, iso, iso_config)
        if e930 is not None:
            eia930_frames.append(e930)
        if has_campd:
            campd_year = _campd_hourly_frame(
                year, iso, parasitic_factors, hours
            )
            eia923_frames.append(
                _backfill_eia923_with_campd(
                    _eia923_frame(year, generation, iso), campd_year,
                    group_by_code, year,
                )
            )
            if campd_year is not None:
                campd_frames.append(campd_year)

    pd.concat(system_frames, ignore_index=True).to_parquet(
        run_dir / "system.parquet", index=False
    )
    if eia930_frames:
        pd.concat(eia930_frames, ignore_index=True).to_parquet(
            run_dir / "eia930.parquet", index=False
        )
    if eia923_frames:
        pd.concat(eia923_frames, ignore_index=True).to_parquet(
            run_dir / "eia923.parquet", index=False
        )
    if btm_frames:
        pd.concat(btm_frames, ignore_index=True).to_parquet(
            run_dir / "btm.parquet", index=False
        )
    if campd_frames:
        pd.concat(campd_frames, ignore_index=True).to_parquet(
            run_dir / "campd.parquet", index=False
        )
    if storage_frames:
        pd.concat(storage_frames, ignore_index=True).to_parquet(
            run_dir / "storage.parquet", index=False
        )
    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "iso": iso, "years": years, "hours": hours,
        "passes": sorted(passes_seen), "commitment": commitment,
        "commitment_screen_coal": screen_coal, "gas_prices": gas_prices,
        "coal_lignite_mustrun": coal_lignite_mustrun,
        "coal_prb_mustrun": coal_prb_mustrun,
        "coal_prb_passthrough": coal_prb_passthrough,
        "outage_source": outage_source,
        "coal_prb_passthrough_sigmoid": coal_prb_passthrough_sigmoid,
        "coal_mustrun_per_plant": coal_mustrun_per_plant,
        "coal_drop_pof": coal_drop_pof,
        "coal_prb_passthrough_tiered": coal_prb_passthrough_tiered,
        "coal_plant_monthly_pricing": _calibration_config(
            years[0], iso, hours, gas_prices[years[0]]
        ).coal_plant_monthly_pricing,
        "td_loss_factor": _calibration_config(
            years[0], iso, hours, gas_prices[years[0]]
        ).td_loss_factor,
        "storage_daily_cycling": storage_daily_cycling,
        "battery_dispatch_adder": battery_dispatch_adder,
        "gas_offer_curve": gas_offer_curve,
        "gas_monthly_actuals": gas_monthly_actuals,
        "offer_curve_overrides": offer_curve_overrides or {},
        "offer_curve_deltas": offer_curve_deltas or {},
        "curve_smoothing": curve_smoothing or {},
        "cc_derate_from_top": cc_derate_from_top,
        "priced_interchange": priced_interchange,
        "git_sha": _git_sha(),
        # Solver provenance: near-tied offer-curve plateaus (e.g. cheap-gas
        # years putting PRB committed bids on top of gas committed bids)
        # admit alternate optimal vertices, and different HiGHS releases
        # pick different ones — class TWh can move several TWh at an
        # identical objective. Record the version so a non-reproducing
        # bundle can be traced to a solver upgrade.
        "highspy_version": _highspy_version(),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    # Rebuild the recorded config WITH the same overrides + deltas applied, so
    # run_config.json's scenario_config.offer_curve_by_group is the exact
    # merged curve the LP solved against (not the bare defaults).
    recorded_cfg = _calibration_config(
        years[0], iso, hours, gas_prices[years[0]],
        offer_curve_overrides=offer_curve_overrides,
        offer_curve_deltas=offer_curve_deltas,
    )
    if plant_tranche_config:
        recorded_cfg = recorded_cfg.with_overrides(
            plant_tranche_config_path=plant_tranche_config)
    if storage_daily_cycling:
        recorded_cfg = recorded_cfg.with_overrides(storage_daily_cycling=True)
    if battery_dispatch_adder:
        recorded_cfg = recorded_cfg.with_overrides(
            battery_dispatch_adder=battery_dispatch_adder)
    if gas_offer_curve:
        recorded_cfg = recorded_cfg.with_overrides(gas_offer_curve=True)
    if gas_monthly_actuals:
        recorded_cfg = recorded_cfg.with_overrides(gas_monthly_actuals=True)
    if curve_smoothing:
        recorded_cfg = recorded_cfg.with_overrides(
            **{k: v for k, v in curve_smoothing.items() if v is not None})
    if cc_derate_from_top:
        recorded_cfg = recorded_cfg.with_overrides(
            cc_outage_derate_from_top=True)
    write_run_config(run_dir, recorded_cfg, meta, note)
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


# Non-fossil / residual classes surfaced in their own table: the dispatchable
# oil peaker plus the must-run injected classes (biomass, hydro, OTHER).
_NONFOSSIL_REPORT_CLASSES: tuple[str, ...] = ("oil", "biomass", "hydro", "OTHER")


def _print_nonfossil_annual(year, model_twh, e923_annual) -> None:
    """[3c] Oil / biomass / hydro / residual OTHER — model vs EIA-923."""
    print(f"\n  [3c] Non-fossil & residual by class — {year}  (oil = LP peaker; "
          "biomass / hydro / OTHER = must-run injected; vs EIA-923 total)")
    rows = [("class", "model", "EIA-923", "diff %")]
    tm = te = 0.0
    for cls in _NONFOSSIL_REPORT_CLASSES:
        m = model_twh.get(cls, 0.0)
        e = e923_annual.get(cls, 0.0)
        diff = 100.0 * (m - e) / e if e else float("nan")
        rows.append((cls, f"{m:7.2f}", f"{e:7.2f}",
                     f"{diff:+6.1f}" if e else "    —"))
        tm += m
        te += e
    rows.append(("TOTAL", f"{tm:7.2f}", f"{te:7.2f}",
                 f"{100.0 * (tm - te) / te:+6.1f}" if te else "—"))
    _print_table(rows)


def _print_storage(year, storage_df, e930) -> None:
    """[3d] Storage throughput — model charge/discharge vs EIA-930 battery.

    The EIA-930 battery benchmark (BAT discharge / UES charge) is NaN over
    hours the BA had not begun reporting it (ERCOT: mid-2024 onward), so the
    model is compared over the benchmark's reported window only and the
    window's coverage is printed alongside.
    """
    if storage_df is None or storage_df.empty:
        return
    by_tech = storage_df.groupby("tech", observed=True)[
        ["discharge_mw", "charge_mw"]
    ].sum() / _MWH_PER_TWH
    print(f"\n  [3d] Storage throughput — {year}  (model LP vs EIA-930 "
          "battery series where reported)")
    rows = [("tech", "dis TWh", "chg TWh")]
    for tech, r in by_tech.iterrows():
        rows.append((tech, f"{r['discharge_mw']:7.2f}", f"{r['charge_mw']:7.2f}"))
    _print_table(rows)

    bench_dis = (e930 or {}).get("battery_discharge")
    if bench_dis is None:
        print("    EIA-930 battery series: not reported this year")
        return
    bench_chg = e930.get("battery_charge")
    reported = ~np.isnan(bench_dis)
    coverage = 100.0 * reported.sum() / len(bench_dis)
    # Model battery (non-PS) discharge summed over the benchmark's window.
    batt = storage_df[storage_df["tech"] != "pumped_storage"]
    hourly = batt.groupby("hour", observed=True)[
        ["discharge_mw", "charge_mw"]
    ].sum().reindex(np.arange(len(bench_dis)), fill_value=0.0)
    m_dis = hourly["discharge_mw"].to_numpy()[reported].sum() / _MWH_PER_TWH
    m_chg = hourly["charge_mw"].to_numpy()[reported].sum() / _MWH_PER_TWH
    a_dis = np.nansum(bench_dis) / _MWH_PER_TWH
    a_chg = (np.nansum(bench_chg) / _MWH_PER_TWH
             if bench_chg is not None else float("nan"))
    rows = [("battery (930 window)", "model", "EIA-930", "diff %"),
            ("discharge TWh", f"{m_dis:7.2f}", f"{a_dis:7.2f}",
             f"{100.0 * (m_dis - a_dis) / a_dis:+6.1f}" if a_dis else "—"),
            ("charge TWh", f"{m_chg:7.2f}", f"{a_chg:7.2f}",
             f"{100.0 * (m_chg - a_chg) / a_chg:+6.1f}" if a_chg else "—")]
    _print_table(rows)
    print(f"    benchmark coverage: {coverage:.0f}% of hours reported")


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
    # The model series follow the solved horizon, which on a partial-hours run
    # (``--hours`` below 8760) is shorter than the always-full-year EIA-930
    # observed series. Compare over the overlapping leading window so such a run
    # still reports a fit instead of crashing on a shape mismatch; for a full
    # year model and observed lengths match and the slices are no-ops.
    obs_T = e930["gas"].shape[0]
    model_T = next((v.shape[0] for v in model_hourly.values()
                    if hasattr(v, "shape")), obs_T)
    T = min(model_T, obs_T)
    gas_m = sum(model_hourly.get(c, np.zeros(T))[:T] for c in _NONCHP_GAS)
    coal_m = sum(model_hourly.get(c, np.zeros(T))[:T] for c in _COAL_CLASSES)
    flat_chp = chp_grid_twh * _MWH_PER_TWH / T
    nuclear_o = e930.get("nuclear")
    pairs = [
        ("gas (non-CHP)", gas_m, e930["gas"][:T] - flat_chp),
        ("coal", coal_m, e930["coal"][:T]),
        ("nuclear", model_hourly.get("nuclear", np.zeros(T))[:T],
         None if nuclear_o is None else nuclear_o[:T]),
        ("solar", model_hourly.get("solar", np.zeros(T))[:T], e930["solar"][:T]),
        ("wind", model_hourly.get("wind", np.zeros(T))[:T], e930["wind"][:T]),
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


def _plant_hourly_fit(
    year: int, dispatch: pd.DataFrame, campd_year: pd.DataFrame, hours: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return per-plant hourly model-vs-CAMPD fit for every resolved plant.

    The model dispatch is summed by ``plant_code`` to an hourly MW series and
    compared against the plant's CAMPD **net** generation. Plants the model
    aggregates into multi-plant bins (``plant_code == 0``) and plants without
    CAMPD coverage are absent.

    Returns two frames: ``fit`` — one row per plant with Pearson r, NRMSE,
    annual model / CAMPD GWh and the CF-band occupancy summary
    (``cf_band_overlap`` / ``cf_emd``, see
    :func:`market_sim.results.calibration.check_cf_band_occupancy`), sorted
    worst-fit first — and ``bands`` — one row per plant per CF band with the
    model and CAMPD hours spent in that band (the timing-free operating-level
    histogram).
    """
    model = dispatch[dispatch["plant_code"] > 0]
    piv = (
        model.groupby(["plant_code", "hour"], observed=True)["mw"].sum()
        .unstack("plant_code", fill_value=0.0).sort_index()
    )
    obs = {
        int(pid): g.sort_values("hour")["net_mw"].to_numpy(dtype=float)
        for pid, g in campd_year.groupby("plant_id", observed=True)
    }
    rows = []
    band_rows: list[dict] = []
    for plant_code in piv.columns:
        observed = obs.get(int(plant_code))
        if observed is None:
            continue
        m = piv[plant_code].to_numpy(dtype=float)
        T = min(m.shape[0], observed.shape[0], hours)
        m, o = m[:T], observed[:T]
        try:
            occ = check_cf_band_occupancy(m, o, band_width=_CF_BAND_WIDTH)
        except ValueError:  # both series identically zero
            occ = None
        rows.append({
            "year": np.int16(year),
            "plant_code": int(plant_code),
            "pearson_r": round(_pearson_r(m, o), 4),
            "nrmse": round(_nrmse(m, o), 4),
            "model_gwh": round(float(m.sum()) / 1e3, 1),
            "campd_gwh": round(float(o.sum()) / 1e3, 1),
            "campd_op_hours": int((o > 0).sum()),
            "cf_band_overlap": occ["band_overlap"] if occ else float("nan"),
            "cf_emd": occ["cf_emd"] if occ else float("nan"),
            "cap_mw": occ["capacity_mw"] if occ else float("nan"),
        })
        if occ:
            for band in occ["bands"]:
                band_rows.append({
                    "year": np.int16(year),
                    "plant_code": int(plant_code),
                    "cf_lo": band["lo"],
                    "cf_hi": band["hi"],
                    "model_hours": np.int32(band["model_hours"]),
                    "campd_hours": np.int32(band["actual_hours"]),
                })
    fit = pd.DataFrame(rows)
    fit = fit.sort_values("pearson_r").reset_index(drop=True) if len(fit) else fit
    return fit, pd.DataFrame(band_rows)


def _print_plant_hourly_fit(year: int, fit: pd.DataFrame) -> None:
    """[7] Per-plant hourly dispatch fit vs CAMPD net — representative panel."""
    by_code = fit.set_index("plant_code") if len(fit) else fit
    print(f"\n  [7] Per-plant hourly dispatch fit — {year} "
          "(model vs CAMPD net; representative panel)")
    rows = [("plant", "EIA code", "Pearson r", " NRMSE", "model GWh",
             "CAMPD GWh", "op hrs", "band ovlp", "CF EMD")]
    for code, label in _PLANT_PANEL:
        if len(by_code) and code in by_code.index:
            r = by_code.loc[code]
            rows.append((label, str(code), f"{r['pearson_r']:.3f}",
                         f"{r['nrmse']:.3f}", f"{r['model_gwh']:9.0f}",
                         f"{r['campd_gwh']:9.0f}", str(int(r['campd_op_hours'])),
                         f"{r['cf_band_overlap']:.3f}", f"{r['cf_emd']:.3f}"))
        else:
            rows.append((label, str(code), "    —", "    —", "    —",
                         "    —", "  —", "    —", "    —"))
    _print_table(rows)
    if len(fit):
        print(f"    (full per-plant fit for all {len(fit)} resolved plants "
              "written to plant_hourly_fit.parquet)")


def _print_plant_cf_bands(year: int, bands: pd.DataFrame) -> None:
    """[7b] Hours per CF band, model vs CAMPD — representative panel.

    The timing-free companion to [7]: for each panel plant, how many hours
    the model and the real plant spent in each capacity-factor band. A plant
    can be hourly-correlated and hit its annual GWh while still parking at
    the wrong operating levels (committed floor too low, ramp top in place
    of duct firing); this is the table that shows it.
    """
    if not len(bands):
        return
    print(f"\n  [7b] Hours per {_CF_BAND_WIDTH:.0%} CF band — {year} "
          "(model / CAMPD net; representative panel)")
    grouped = bands.groupby("plant_code", observed=True)
    edges = sorted(bands["cf_lo"].unique())
    header = ("plant", "", *(f"{lo:.0%}-{lo + _CF_BAND_WIDTH:.0%}"
                             for lo in edges))
    rows = [header]
    for code, label in _PLANT_PANEL:
        if code not in grouped.groups:
            continue
        g = grouped.get_group(code).sort_values("cf_lo")
        rows.append((label, "model",
                     *(str(int(h)) for h in g["model_hours"])))
        rows.append(("", "CAMPD",
                     *(str(int(h)) for h in g["campd_hours"])))
    _print_table(rows)


def _save_p2_state(run_dir: Path, year: int, p2_state: dict) -> None:
    """Pickle the cached P1 inputs so P2 can be re-run as a post-process."""
    d = run_dir / "p2_state"
    d.mkdir(parents=True, exist_ok=True)
    with gzip.open(d / f"{year}.pkl.gz", "wb") as fh:
        pickle.dump(p2_state, fh, protocol=pickle.HIGHEST_PROTOCOL)


def run_p2_layer(bundle: Path, screen_coal: bool) -> None:
    """Run the P2 commitment pass from a bundle's cached P1 state, then report.

    Loads each year's pickled P1 inputs from ``<bundle>/p2_state/``, runs the
    single P2 LP solve (no P0/P1 re-solve), writes the P2 dispatch / system /
    btm into the bundle, marks P2 in ``meta.json`` and prints the full report.
    The bundle must have been produced with ``--persist-p2-state``.
    """
    meta = json.loads((bundle / "meta.json").read_text())
    iso_config = get_iso_config(meta["iso"])
    zone_names = iso_config.zone_names
    generation = load_monthly_generation()
    states = sorted((bundle / "p2_state").glob("*.pkl.gz"))
    if not states:
        logger.error(
            "no p2_state pickles in %s — re-run the bundle with "
            "--persist-p2-state first", bundle / "p2_state",
        )
        return

    system_p2, btm_p2, storage_p2 = [], [], []
    for sp in states:
        with gzip.open(sp, "rb") as fh:
            state = pickle.load(fh)
        year = int(state["year"])
        cfg = state["config"].with_overrides(
            commitment_enabled=True, commitment_screen_coal=screen_coal,
        )
        logger.info("P2 post-process %d (screen_coal=%s)", year, screen_coal)
        result = _commitment_pass(state, cfg)
        ctx = state["context"]
        must_run = _must_run_profiles(
            year, generation, meta["iso"], state["demand"],
            skip_classes=(frozenset() if meta["iso"] == "ERCOT"
                          else frozenset({"biomass"})),
        )
        _dispatch_frame(
            year, "P2", result, ctx, zone_names, iso=meta["iso"],
            must_run=must_run,
        ).to_parquet(
            bundle / "dispatch" / f"{year}_P2.parquet", index=False
        )
        system_p2.append(
            _system_frame(year, "P2", result, state["demand"], zone_names)
        )
        btm_p2.append(_btm_frame(year, "P2", result, ctx, generation))
        # Older p2_state pickles predate the storage frame; skip them.
        storage_frame = _storage_frame(
            year, "P2", result, state.get("storage_units")
        )
        if storage_frame is not None:
            storage_p2.append(storage_frame)

    for name, frames in (
        ("system", system_p2), ("btm", btm_p2), ("storage", storage_p2),
    ):
        if not frames:
            continue
        path = bundle / f"{name}.parquet"
        new = pd.concat(frames, ignore_index=True)
        if path.exists():
            old = pd.read_parquet(path)
            old = old[old["pass"] != "P2"]  # replace any prior P2
            new = pd.concat([old, new], ignore_index=True)
        new.to_parquet(path, index=False)

    meta["passes"] = sorted(set(meta.get("passes", [])) | {"P2"})
    meta["p2_screen_coal"] = screen_coal
    (bundle / "meta.json").write_text(json.dumps(meta, indent=2))
    report_run(bundle)


# Model fuel labels that aggregate into the EIA-930 / EIA-923 "gas" series.
_MODEL_GAS_FUELS: frozenset[str] = frozenset({"gas_cc", "gas_ct", "gas_st"})
# Canonical fuel order for the generic fuel-mix table.
_GENERIC_FUEL_ORDER: tuple[str, ...] = (
    "coal", "gas", "nuclear", "wind", "solar", "hydro", "oil", "biomass",
    "other",
)


def _canon_fuel(fuel: str) -> str:
    """Collapse a model fuel label to its benchmark fuel (gas_* -> gas)."""
    return "gas" if fuel in _MODEL_GAS_FUELS else fuel


def _aggregate_twh(by_fuel: dict[str, float]) -> dict[str, float]:
    """Sum a per-fuel TWh mapping into canonical benchmark fuels."""
    out: dict[str, float] = {}
    for fuel, twh in by_fuel.items():
        out[_canon_fuel(fuel)] = out.get(_canon_fuel(fuel), 0.0) + twh
    return out


# Local hours-of-day of the evening net-load peak window, used to summarize
# the battery discharge shape (CAISO's duck-curve discharge concentrates in
# HE18-23, i.e. hours 17-22 0-based). Both the model and the EIA-930 series
# index hour 0 at local midnight Jan 1, so ``hour % 24`` is the local hour.
_EVENING_HOURS: tuple[int, int] = (17, 22)


def _evening_share_pct(discharge: np.ndarray) -> float:
    """Share (%) of total discharge falling in the evening-peak window."""
    total = float(discharge.sum())
    if total <= 0.0:
        return float("nan")
    hod = np.arange(discharge.shape[0]) % 24  # hour of local day
    lo, hi = _EVENING_HOURS
    return 100.0 * float(discharge[(hod >= lo) & (hod <= hi)].sum()) / total


def _print_storage_cycling(
    year: int, storage: pd.DataFrame, e930: dict | None,
) -> None:
    """[2b] Battery throughput + evening-discharge shape vs EIA-930.

    The model side is the bundle's storage frame (battery vs pumped-storage
    techs split out). The benchmark side is the EIA-930 ``battery`` /
    ``pumped_storage`` net series, present only when the BA extract carries
    the storage fuel codes (the current CISO extract folds batteries into
    ``OTH``); absent benchmarks print as ``—`` so the model throughput is
    still on the record.
    """
    batt = storage[storage["tech"] != "pumped_storage"]
    if batt.empty:
        return
    hourly = (
        batt.groupby("hour")[["charge_mw", "discharge_mw"]]
        .sum().sort_index()
    )
    dis = hourly["discharge_mw"].to_numpy(dtype=float)
    chg = hourly["charge_mw"].to_numpy(dtype=float)
    obs = e930.get("battery") if e930 is not None else None

    lo, hi = _EVENING_HOURS
    print(f"\n  [2b] Battery cycling — {year} (model EIA-860 fleet vs "
          "EIA-930 BAT)")
    rows: list[tuple] = [("metric", "model", "EIA-930")]
    if obs is not None:
        T = min(dis.shape[0], obs.shape[0])
        dis, chg, obs = dis[:T], chg[:T], obs[:T]
        # EIA-930 BAT is a net series: + = discharging, - = charging.
        o_dis = np.clip(obs, 0.0, None)
        o_chg = np.clip(-obs, 0.0, None)
        rows.append(("discharge TWh", f"{dis.sum() / _MWH_PER_TWH:.2f}",
                     f"{o_dis.sum() / _MWH_PER_TWH:.2f}"))
        rows.append(("charge TWh", f"{chg.sum() / _MWH_PER_TWH:.2f}",
                     f"{o_chg.sum() / _MWH_PER_TWH:.2f}"))
        rows.append((f"evening (h{lo}-{hi}) discharge share %",
                     f"{_evening_share_pct(dis):.1f}",
                     f"{_evening_share_pct(o_dis):.1f}"))
        rows.append(("hourly net Pearson r",
                     f"{_pearson_r(dis - chg, obs):.3f}", ""))
    else:
        rows.append(("discharge TWh",
                     f"{dis.sum() / _MWH_PER_TWH:.2f}", "—"))
        rows.append(("charge TWh", f"{chg.sum() / _MWH_PER_TWH:.2f}", "—"))
        rows.append((f"evening (h{lo}-{hi}) discharge share %",
                     f"{_evening_share_pct(dis):.1f}", "—"))
    _print_table(rows)
    if obs is None:
        print("    (no EIA-930 battery series in this BA extract — model "
              "throughput reported alone)")

    ps = storage[storage["tech"] == "pumped_storage"]
    if not ps.empty:
        ps_dis = float(ps["discharge_mw"].sum()) / _MWH_PER_TWH
        ps_obs = e930.get("pumped_storage") if e930 is not None else None
        bench = (
            f"{np.clip(ps_obs, 0.0, None).sum() / _MWH_PER_TWH:.2f}"
            if ps_obs is not None else "—"
        )
        print(f"    pumped-storage discharge: model {ps_dis:.2f} TWh; "
              f"EIA-930 {bench}")


def _print_curtailment_vs_reported(
    year: int, iso: str, dispatch: pd.DataFrame
) -> None:
    """[1b] Modeled vs reported wind/solar curtailment (HSL-backed ISO-years).

    The headline re-curtailment metric of playbook §8.3: the dispatch was fed
    the *uncurtailed* potential (delivered + reported curtailment, the HSL
    analogue — see ``market_sim.data.renewables``), so its endogenous
    curtailment ``potential - dispatched`` is directly comparable to the
    curtailment the ISO actually reported (``hsl - gen`` in the same
    parquet). Annual TWh per fuel plus the monthly GWh shape. Skipped
    silently for ISO-years with no HSL dataset (those backcasts consume the
    delivered profile and have nothing to re-curtail).
    """
    from market_sim.data.renewables import load_hsl_hourly

    hsl = load_hsl_hourly(iso, year)
    if hsl is None:
        return

    modeled = {}
    for fuel in ("wind", "solar"):
        rows = dispatch[dispatch["fuel"] == fuel]
        if rows.empty:
            return
        modeled[fuel] = (
            rows.groupby("hour", observed=True)["mw"].sum()
            .sort_index().to_numpy(dtype=float)
        )

    T = min(_HOURS_PER_YEAR, *(len(v) for v in modeled.values()))
    print(f"\n  [1b] Renewable curtailment — {year} "
          "(model re-curtailment vs ISO-reported; potential = delivered + "
          "reported curtailment)")
    if T < _HOURS_PER_YEAR:
        print(f"    NOTE: {T}-hour run — reported series truncated to match.")
    rows_out: list[tuple] = [(
        "fuel", "potential TWh", "model TWh", "model curt", "model %",
        "reported curt", "reported %",
    )]
    monthly: dict[str, dict[str, np.ndarray]] = {}
    for fuel in ("wind", "solar"):
        # The potential the LP saw is the CF-floored HSL (negative EIA-930
        # night-time values clamp to zero in the profile), so floor here too;
        # otherwise modeled curtailment picks up phantom night-time slack.
        potential = np.maximum(
            hsl[f"{fuel}_hsl_mw"].to_numpy(dtype=float)[:T], 0.0
        )
        delivered = np.minimum(
            np.maximum(hsl[f"{fuel}_gen_mw"].to_numpy(dtype=float)[:T], 0.0),
            potential,
        )
        model_curt = np.maximum(potential - modeled[fuel][:T], 0.0)
        reported_curt = potential - delivered
        monthly[fuel] = {"model": model_curt, "reported": reported_curt}
        pot_twh = potential.sum() / _MWH_PER_TWH
        rows_out.append((
            fuel,
            f"{pot_twh:.2f}",
            f"{modeled[fuel][:T].sum() / _MWH_PER_TWH:.2f}",
            f"{model_curt.sum() / _MWH_PER_TWH:.3f}",
            f"{100.0 * model_curt.sum() / potential.sum():.2f}",
            f"{reported_curt.sum() / _MWH_PER_TWH:.3f}",
            f"{100.0 * reported_curt.sum() / potential.sum():.2f}",
        ))
    _print_table(rows_out)

    month_idx = _hour_to_month(T)
    month_rows: list[tuple] = [(
        "month", "wind mdl", "wind rep", "solar mdl", "solar rep",
    )]
    for m in range(1, 13):
        sel = month_idx == m
        if not sel.any():
            break
        month_rows.append((
            _MONTH_NAMES[m - 1],
            *(f"{monthly[fuel][kind][sel].sum() / 1e3:.1f}"
              for fuel in ("wind", "solar") for kind in ("model", "reported")),
        ))
    print("\n    Monthly curtailment (GWh):")
    _print_table(month_rows)


def _report_generic(
    run_dir: Path, iso: str, meta: dict, system: pd.DataFrame,
    e930_all: pd.DataFrame | None,
) -> None:
    """Print the generic energy-only calibration report for a non-ERCOT ISO.

    Compares modeled annual generation by fuel against the EIA-930 hourly
    delivered mix and the EIA-923 reference benchmark, summarizes the zonal
    and system price level and duration, and contrasts the (zero) modeled net
    interchange against the EIA-930 actual. This is the Stage G comparison the
    energy-only PJM backcast supports today; the ERCOT-specific plant-level,
    CHP and CAMPD diagnostics are skipped.
    """
    reference = _load_reference()
    storage_path = run_dir / "storage.parquet"
    storage_all = (
        pd.read_parquet(storage_path) if storage_path.exists() else None
    )
    for year in meta["years"]:
        ref_year = reference.get("isos", {}).get(iso, {}).get(str(year), {})
        ref_gen = _aggregate_twh(ref_year.get("generation_twh", {}))
        # Renewables are judged against EIA-930 grid-delivered generation (the
        # 930 column), not EIA-923 — the same basis the ERCOT report uses
        # (_print_nonchp_grid compares solar/wind to e930). EIA-923's solar/wind
        # totals fold in behind-the-meter / distributed output that never
        # reaches the wholesale grid (PJM 2024: 20.6 TWh 923 solar vs ~16 on the
        # grid), so the 923 cell is blanked for solar/wind in the print loop
        # below. The value is kept in ref_gen here so the 923 system total (and
        # thus the thermal 923% shares) still reflect the full reported mix.

        e930 = None
        if e930_all is not None:
            ey = e930_all[e930_all["year"] == year]
            e930 = {
                s: ey[ey["series"] == s].sort_values("hour")["mw"].to_numpy()
                for s in ey["series"].unique()
            }

        pass_label = meta["passes"][-1]
        disp_path = run_dir / "dispatch" / f"{year}_{pass_label}.parquet"
        if not disp_path.exists():
            continue
        dispatch = pd.read_parquet(disp_path)
        sysd = system[
            (system["year"] == year) & (system["pass"] == pass_label)
        ]

        print(f"\n{'=' * 80}\n  {iso} {year} BACKCAST  (energy-only)\n{'=' * 80}")

        # --- [1] Generation by fuel: model vs EIA-930 vs EIA-923 reference ---
        model = _aggregate_twh(
            (dispatch.groupby("fuel")["mw"].sum() / _MWH_PER_TWH).to_dict()
        )
        # The priced import/export node's net position is interchange, not
        # generation — it reports in [2], and excluding it keeps the model
        # total (gross internal generation) comparable to the EIA-930 total.
        model.pop("import", None)
        e930_twh = {
            f: float(e930[f].sum()) / _MWH_PER_TWH
            for f in _GENERIC_FUEL_ORDER
            if e930 is not None and f in e930
        } if e930 is not None else {}
        model_total = sum(model.values())
        e930_total = sum(e930_twh.values()) if e930_twh else None
        ref_total = sum(ref_gen.values()) if ref_gen else None

        def _twh(v: float | None) -> str:
            return "      —" if v is None else f"{v:7.2f}"

        def _pct(v: float | None, total: float | None) -> str:
            return "    —" if not v or not total else f"{100 * v / total:5.1f}"

        print("\n  [1] Generation by fuel (TWh; share of own total)")
        print(f"    {'fuel':<9} {'model':>7} {'mdl%':>5} "
              f"{'EIA-930':>7} {'930%':>5} {'EIA-923':>7} {'923%':>5}")
        for fuel in _GENERIC_FUEL_ORDER:
            m, g, r = model.get(fuel), e930_twh.get(fuel), ref_gen.get(fuel)
            # Solar/wind compared vs EIA-930 only (see note above); blank the
            # BTM-inflated 923 cell while leaving it in the total.
            if fuel in ("solar", "wind"):
                r = None
            if m is None and g is None and r is None:
                continue
            print(f"    {fuel:<9} {_twh(m)} {_pct(m, model_total)} "
                  f"{_twh(g)} {_pct(g, e930_total)} "
                  f"{_twh(r)} {_pct(r, ref_total)}")
        print(f"    {'TOTAL':<9} {_twh(model_total)} {'100.0':>5} "
              f"{_twh(e930_total)} {'100.0' if e930_total else '    —':>5} "
              f"{_twh(ref_total)} {'100.0' if ref_total else '    —':>5}")

        # --- [1b] Curtailment: model re-curtailment vs ISO-reported ---
        _print_curtailment_vs_reported(year, iso, dispatch)

        # --- [2] Net interchange: model vs EIA-930 ---
        if e930 is not None and "interchange" in e930:
            ix = e930["interchange"]
            ix_twh = float(ix.sum()) / _MWH_PER_TWH
            print("\n  [2] Net interchange (EIA sign: + = net export)")
            print(f"    actual (EIA-930): {ix_twh:+.2f} TWh "
                  f"({ix.mean():+.0f} MW avg)")
            # Three interchange representations, in order of preference:
            # the priced import/export node when its units are in the
            # dispatch (net export = -(import tranches + export sinks));
            # PJM's measured tie-line schedule added to demand; else the
            # energy-only zero.
            node = dispatch[dispatch["fuel"] == "import"]
            if len(node):
                model_ix = -(
                    node.groupby("hour", observed=True)["mw"].sum()
                    .sort_index().to_numpy(dtype=float)
                )
                how = "priced import/export node"
            else:
                model_ix = pjm_net_interchange(year) if iso == "PJM" else None
                how = "served as a scheduled interchange added to demand"
            if model_ix is not None:
                m_twh = float(model_ix.sum()) / _MWH_PER_TWH
                print(f"    model            : {m_twh:+.2f} TWh "
                      f"({model_ix.mean():+.0f} MW avg; {how})")
                n = min(model_ix.shape[0], ix.shape[0])
                dur_m = np.sort(model_ix[:n])
                dur_a = np.sort(np.asarray(ix, dtype=float)[:n])
                rmse = float(np.sqrt(((dur_m - dur_a) ** 2).mean()))
                pcts = [1, 10, 50, 90, 99]
                qm = np.percentile(model_ix[:n], pcts)
                qa = np.percentile(np.asarray(ix, dtype=float)[:n], pcts)
                print(f"    duration curve   : RMSE {rmse:.0f} MW; "
                      "p01/p10/p50/p90/p99 model "
                      + "/".join(f"{v:+.0f}" for v in qm)
                      + " vs actual "
                      + "/".join(f"{v:+.0f}" for v in qa))
                print(f"    import hours     : model "
                      f"{100.0 * float((model_ix[:n] < 0).mean()):.1f}% vs "
                      f"actual "
                      f"{100.0 * float((np.asarray(ix)[:n] < 0).mean()):.1f}%")
            else:
                print("    model            :    0.00 TWh "
                      "(energy-only; no external interchange node)")

        # --- [2b] Battery cycling: throughput + evening-discharge shape ---
        if storage_all is not None:
            s = storage_all[
                (storage_all["year"] == year)
                & (storage_all["pass"] == pass_label)
            ]
            if not s.empty:
                _print_storage_cycling(year, s, e930)

        # --- [3] Price level + duration ---
        zones = sorted(sysd["zone"].unique())
        print("\n  [3] Zonal price level ($/MWh)")
        print(f"    {'zone':<14} {'avg':>8} {'neg-hrs':>8}")
        for zone in zones:
            zp = sysd[sysd["zone"] == zone]["price"].to_numpy()
            print(f"    {zone:<14} {zp.mean():8.2f} {int((zp < 0).sum()):>8}")
        sysprice = (
            sysd.groupby("hour")["price"].mean().sort_index().to_numpy()
        )
        pct = np.percentile(sysprice, [100, 90, 50, 10, 0])
        print("\n  [3] System price duration ($/MWh)")
        print(f"    avg {sysprice.mean():8.2f}   max {pct[0]:8.2f}   "
              f"p90 {pct[1]:7.2f}   p50 {pct[2]:7.2f}   "
              f"p10 {pct[3]:7.2f}   min {pct[4]:8.2f}")
        print(f"    negative-price hours: {int((sysprice < 0).sum())}")


def report_run(run_dir: Path) -> None:
    """Print the full calibration report from a persisted bundle.

    ERCOT prints the full plant-level / CHP / CAMPD diagnostic. Other ISOs
    (PJM energy-only) print the generic fuel-mix / price / interchange report,
    which is all their bundle carries (see :func:`solve_and_persist`).
    """
    meta = json.loads((run_dir / "meta.json").read_text())
    iso = meta["iso"]
    system = pd.read_parquet(run_dir / "system.parquet")
    e930_all = (
        pd.read_parquet(run_dir / "eia930.parquet")
        if (run_dir / "eia930.parquet").exists() else None
    )

    print(f"\n{'=' * 80}")
    print(f"  CALIBRATION REPORT  ({iso}; run {meta['timestamp']}; "
          f"git {meta.get('git_sha', '?')})")
    print(f"  bundle: {run_dir}")
    print(f"{'=' * 80}")

    if iso != "ERCOT":
        _report_generic(run_dir, iso, meta, system, e930_all)
        return

    e923_all = pd.read_parquet(run_dir / "eia923.parquet")
    btm_all = pd.read_parquet(run_dir / "btm.parquet")
    campd_all = (
        pd.read_parquet(run_dir / "campd.parquet")
        if (run_dir / "campd.parquet").exists() else None
    )
    storage_all = (
        pd.read_parquet(run_dir / "storage.parquet")
        if (run_dir / "storage.parquet").exists() else None
    )
    plant_fit_frames: list[pd.DataFrame] = []
    plant_band_frames: list[pd.DataFrame] = []

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

        print(f"\n{'=' * 80}\n  {iso} {year} BACKCAST\n{'=' * 80}")
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
            _print_nonfossil_annual(year, model_twh, e923_annual)
            if storage_all is not None:
                _print_storage(
                    year,
                    storage_all[(storage_all["year"] == year)
                                & (storage_all["pass"] == pass_label)],
                    e930,
                )
            _print_monthly(year, model_hourly, e923_monthly, e930_solar_monthly,
                           btm, e923_annual)
            if e930 is not None:
                _print_hourly_fit(year, model_hourly, e930, chp_grid_twh)
            _print_plant_level(year, dispatch, e923)
            if campd_all is not None:
                campd_year = campd_all[campd_all["year"] == year]
                if not campd_year.empty:
                    hours = int(dispatch["hour"].max()) + 1
                    fit, cf_bands = _plant_hourly_fit(
                        year, dispatch, campd_year, hours
                    )
                    _print_plant_hourly_fit(year, fit)
                    _print_plant_cf_bands(year, cf_bands)
                    if len(fit):
                        fit = fit.copy()
                        fit["pass"] = pass_label
                        plant_fit_frames.append(fit)
                    if len(cf_bands):
                        cf_bands = cf_bands.copy()
                        cf_bands["pass"] = pass_label
                        plant_band_frames.append(cf_bands)

    if plant_fit_frames:
        pd.concat(plant_fit_frames, ignore_index=True).to_parquet(
            run_dir / "plant_hourly_fit.parquet", index=False
        )
    if plant_band_frames:
        pd.concat(plant_band_frames, ignore_index=True).to_parquet(
            run_dir / "plant_cf_bands.parquet", index=False
        )


def rebuild_benchmark(bundle: Path) -> None:
    """Rebuild a bundle's benchmark parquets off its meta, then re-report.

    The benchmark frames — EIA-923 (with CAMPD backfill), EIA-930 and CAMPD
    net — are pure functions of ``(year, iso)`` and the reference data;
    they do not depend on the model dispatch. So refreshing them after a
    benchmark-logic change (e.g. the CAMPD backfill) is a post-processing
    step over the persisted dispatch parquets — no LP re-solve needed.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import load_campd_bins

    meta = json.loads((bundle / "meta.json").read_text())
    iso = meta["iso"]
    is_ercot = iso == "ERCOT"
    years = meta["years"]
    hours = int(meta.get("hours", _HOURS_PER_YEAR))
    iso_config = get_iso_config(iso)
    generation = load_monthly_generation()
    parasitic_factors = _parasitic_factor_map()
    # Plant -> group map for the CAMPD backfill: ERCOT's curated bin sheet,
    # the per-plant EIA-860 fleet for every other ISO — the same sources the
    # solve path uses, so a rebuilt benchmark groups plants identically.
    if is_ercot:
        bins = load_campd_bins(ScenarioConfig().campd_bins_path)
        group_by_code = dict(
            zip(bins["Plant_Code"].astype(int), bins["Plant_Group"])
        )
    else:
        group_by_code = _fleet_group_by_code(iso, iso_config)

    e923f, e930f, campdf = [], [], []
    for year in years:
        campd_year = _campd_hourly_frame(year, iso, parasitic_factors, hours)
        e923f.append(
            _backfill_eia923_with_campd(
                _eia923_frame(year, generation, iso), campd_year,
                group_by_code, year,
            )
        )
        e930 = _eia930_frame(year, iso, iso_config)
        if e930 is not None:
            e930f.append(e930)
        if campd_year is not None:
            campdf.append(campd_year)

    pd.concat(e923f, ignore_index=True).to_parquet(
        bundle / "eia923.parquet", index=False
    )
    if e930f:
        pd.concat(e930f, ignore_index=True).to_parquet(
            bundle / "eia930.parquet", index=False
        )
    if campdf:
        pd.concat(campdf, ignore_index=True).to_parquet(
            bundle / "campd.parquet", index=False
        )
    logger.info("rebuilt benchmark parquets in %s (no re-solve)", bundle)
    report_run(bundle)


def main() -> None:
    """Solve + persist a timestamped bundle and report it, or report an old one."""
    parser = argparse.ArgumentParser(
        description="Calibration backcast (ERCOT full; other ISOs energy-only): "
                    "solve, persist, report."
    )
    parser.add_argument("--year", nargs="+", type=int, default=[2023, 2024])
    parser.add_argument(
        "--iso", default="ERCOT",
        help="ISO to backcast. ERCOT runs the full plant-level diagnostic; "
             "other ISOs (e.g. PJM) run energy-only (generic fuel-mix / price "
             "/ interchange report; ERCOT-only steps skipped).",
    )
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
        "--coal-lignite-mustrun", type=float, default=None,
        help="Override mine-mouth lignite coal must-run %% (sweep knob).",
    )
    parser.add_argument(
        "--coal-prb-mustrun", type=float, default=None,
        help="Override PRB coal must-run %% (sweep knob).",
    )
    parser.add_argument(
        "--coal-prb-passthrough", type=float, default=1.0,
        help="PRB above-must-run fuel passthrough (1.0 = off).",
    )
    parser.add_argument(
        "--outage-source", choices=["historic", "statistical"],
        default="historic",
        help="Coal/CC availability: 'historic' overlays actual >10-day ERCOT "
             "outages (default backcast); 'statistical' uses WEFOR/POF only.",
    )
    # Locked calibration config ("tier pass 2"): per-plant CAMPD coal must-run,
    # gas-keyed PRB passthrough sigmoid (tiered baseload/follower), POF dropped
    # on coal. All on by default; use the --no-* form to disable.
    parser.add_argument(
        "--prb-passthrough-sigmoid", action=argparse.BooleanOptionalAction,
        default=True,
        help="Gas-key the PRB passthrough: a logistic of the monthly gas "
             "price replaces the flat --coal-prb-passthrough (deep discount "
             "when gas is cheap, none/markup when dear).",
    )
    parser.add_argument(
        "--coal-mustrun-per-plant", action=argparse.BooleanOptionalAction,
        default=True,
        help="Use per-plant CAMPD-derived coal must-run floors "
             "(fleet.COAL_MUSTRUN_BY_PLANT) instead of uniform lignite/PRB "
             "must-run overrides.",
    )
    parser.add_argument(
        "--coal-drop-pof", action=argparse.BooleanOptionalAction, default=True,
        help="Drop the statistical planned-outage (POF) derate on coal "
             "(planned maintenance comes from the historic outage overlay); "
             "keep WEFOR in non-summer months and the derate all year.",
    )
    parser.add_argument(
        "--prb-sigmoid-tiered", action=argparse.BooleanOptionalAction,
        default=True,
        help="Use a separate follower-tier PRB passthrough sigmoid for "
             "low-must-run load-follower plants (coal_prb_follower_*).",
    )
    parser.add_argument(
        "--report", metavar="DIR", default=None,
        help="Skip solving; print the report from an existing bundle directory.",
    )
    parser.add_argument(
        "--rebuild-benchmark", metavar="DIR", default=None,
        help="Rebuild a bundle's benchmark parquets (EIA-923 w/ CAMPD "
             "backfill, EIA-930, CAMPD) off its meta and re-report — no "
             "dispatch re-solve.",
    )
    parser.add_argument(
        "--persist-p2-state", action="store_true",
        help="Pickle each year's P1 inputs (large) so P2 can be re-run via "
             "--run-p2 without re-solving P0/P1.",
    )
    parser.add_argument(
        "--run-p2", metavar="DIR", default=None,
        help="Run the P2 commitment pass from a bundle's cached P1 state "
             "(one LP solve, no re-solve). Honours --no-coal-p2.",
    )
    parser.add_argument(
        "--out-dir", default=None,
        help="Bundle root (default results/calibration/<timestamp>).",
    )
    parser.add_argument(
        "--note", default="",
        help="Free-text note describing pre-run model changes; recorded in "
             "the bundle's run_config.json alongside the full config and git "
             "provenance.",
    )
    # PRB passthrough sigmoid floor/ceiling tune (baseload + follower tiers).
    # None leaves the ScenarioConfig default in place.
    parser.add_argument("--prb-floor", type=float, default=None,
                        help="Baseload PRB sigmoid cheap-gas floor.")
    parser.add_argument("--prb-ceil", type=float, default=None,
                        help="Baseload PRB sigmoid dear-gas ceiling.")
    parser.add_argument("--prb-follower-floor", type=float, default=None,
                        help="Follower-tier PRB sigmoid floor.")
    parser.add_argument("--prb-follower-ceil", type=float, default=None,
                        help="Follower-tier PRB sigmoid ceiling.")
    parser.add_argument(
        "--storage-daily-cycling", action="store_true",
        help="Cap storage to within-day arbitrage: each unit's SOC must "
             "return to its day-start level every 24h (bounds the single-LP "
             "perfect-foresight advantage). Off = annual-cyclic (default).",
    )
    parser.add_argument(
        "--battery-adder", type=float, default=0.0,
        help="Grid-battery throughput/cycling cost in $/MWh discharged "
             "(ScenarioConfig.battery_dispatch_adder): degradation + "
             "ancillary-service opportunity cost the energy-only LP "
             "otherwise ignores, taming BESS over-cycling. 0 = off "
             "(default; pumped storage keeps its own adder).",
    )
    parser.add_argument(
        "--gas-offer-curve", action="store_true",
        help="Give the non-ERCOT per-plant gas fleet a stepped offer curve "
             "(committed/economic/peaking heat-rate bands) via "
             "split_gas_tranches, instead of a single flat block. Off by "
             "default.",
    )
    parser.add_argument(
        "--gas-monthly-actuals", action="store_true",
        help="Price gas at the ISO's measured EIA-923 monthly volume-weighted "
             "delivered cost (one hub-level price per month) instead of the "
             "annual Henry Hub + basis x generic seasonality shape, so real "
             "winter gas events reach the merit order. Off by default.",
    )
    parser.add_argument("--plant-tranche-config", default=None,
                        help="Per-plant tranche-config CSV (one row per plant "
                             "with its tranche shares + per-band HR mults). "
                             "Each listed plant's offer comes from the sheet, "
                             "bypassing offer_curve_by_group. Generate/edit "
                             "with scripts/export_tranche_config.py.")
    parser.add_argument(
        "--offer-curve-json", default=None, metavar="JSON",
        help="Per-class/per-band heat-rate multiplier overrides as a JSON "
             "object, deep-merged onto the calibrated offer_curve_by_group "
             "defaults. Each top-level key is a fleet class (CC_REGULAR, "
             "CC_CHP, CT_PEAKER, ST_GAS, ST_CHP, COAL_LIGNITE, COAL_PRB); the "
             "nested object overrides only the named bands (committed, "
             "econ_low, econ_high, peak, econ_low_share, pct_peaking). "
             'E.g. \'{"CT_PEAKER":{"committed":1.40,"econ_low":1.27},'
             '"COAL_PRB":{"committed":0.95}}\'. May also be a path to a '
             ".json file. The merged curve is recorded in run_config.json.")
    parser.add_argument(
        "--cc-derate-from-top", action="store_true",
        help="Reallocate CC_REGULAR outage derates top-of-stack: a partial "
             "outage truncates the duct-fire/high-econ end of the plant's "
             "offer curve instead of scaling every tranche (incl. the cheap "
             "committed floor) pro-rata. Plant hourly available MW unchanged.")
    parser.add_argument(
        "--curve-n", type=int, default=None,
        help="Override offer_curve_smoothing_n (default 6): the number of "
             "equal-capacity slices the econ ramp is rendered into. Sweep "
             "knob for testing finer offer-curve granularity (e.g. 12).")
    parser.add_argument(
        "--curve-mid", type=float, default=None,
        help="Override offer_curve_smoothing_mid: fraction of the econ "
             "ramp's lo->pk rise reached at its capacity midpoint "
             "(piecewise-linear shape anchor; <0.5 = cheap middle, steep "
             "top). Unset keeps the t**exp power shape.")
    parser.add_argument(
        "--curve-exp", type=float, default=None,
        help="Override offer_curve_smoothing_exp (default 1.0 = linear "
             "ramp): exponent of the econ-ramp heat-rate rise. >1 convex "
             "(cheap-bottomed), <1 concave (cheap mid/top).")
    parser.add_argument(
        "--priced-interchange", action="store_true",
        help="Serve interchange through the priced import/export node "
             "(import tranches + export sinks in the ISO's external zone, "
             "the forward-scenario mechanism) instead of the measured "
             "schedule added to demand. Used to validate the node's tranche "
             "calibration against the EIA-930 net-interchange duration "
             "curve.")
    parser.add_argument(
        "--offer-curve-delta-json", default=None, metavar="JSON",
        help="Like --offer-curve-json but each value is ADDED to the current "
             "band rather than replacing it, so a re-tune need not restate the "
             "prior absolute. Same shape (class -> band -> number); the number "
             'is a signed delta. E.g. \'{"CT_PEAKER":{"committed":0.05},'
             '"COAL_PRB":{"committed":-0.05}}\' nudges committed +0.05 / -0.05. '
             "Applied on top of --offer-curve-json when both are given. The "
             "resolved absolute curve is recorded in run_config.json.")
    args = parser.parse_args()

    offer_curve_overrides = _parse_offer_curve_json(args.offer_curve_json)
    offer_curve_deltas = _parse_offer_curve_json(
        args.offer_curve_delta_json, flag="--offer-curve-delta-json")

    if args.report:
        report_run(Path(args.report))
        return

    if args.rebuild_benchmark:
        rebuild_benchmark(Path(args.rebuild_benchmark))
        return

    if args.run_p2:
        run_p2_layer(Path(args.run_p2), screen_coal=not args.no_coal_p2)
        return

    iso = args.iso.upper()
    if iso != "ERCOT":
        has_campd = bool(campd.states_for_iso(iso))
        logger.info(
            "%s backcast: NP6 HSL and coal must-run tuning are ERCOT-only and "
            "skipped; per-plant CAMPD + EIA-923 benchmark %s; the report "
            "compares fuel mix, prices and net interchange.",
            iso,
            "built for the covered states" if has_campd
            else "skipped (no CAMPD coverage)",
        )
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
        coal_lignite_mustrun=args.coal_lignite_mustrun,
        coal_prb_mustrun=args.coal_prb_mustrun,
        coal_prb_passthrough=args.coal_prb_passthrough,
        persist_p2_state=args.persist_p2_state,
        outage_source=args.outage_source,
        coal_prb_passthrough_sigmoid=args.prb_passthrough_sigmoid,
        coal_mustrun_per_plant=args.coal_mustrun_per_plant,
        coal_drop_pof=args.coal_drop_pof,
        coal_prb_passthrough_tiered=args.prb_sigmoid_tiered,
        prb_overrides={
            "coal_prb_passthrough_floor": args.prb_floor,
            "coal_prb_passthrough_ceil": args.prb_ceil,
            "coal_prb_follower_floor": args.prb_follower_floor,
            "coal_prb_follower_ceil": args.prb_follower_ceil,
        },
        plant_tranche_config=args.plant_tranche_config,
        storage_daily_cycling=args.storage_daily_cycling,
        battery_dispatch_adder=args.battery_adder,
        gas_offer_curve=args.gas_offer_curve,
        gas_monthly_actuals=args.gas_monthly_actuals,
        offer_curve_overrides=offer_curve_overrides,
        offer_curve_deltas=offer_curve_deltas,
        curve_smoothing={
            "offer_curve_smoothing_n": args.curve_n,
            "offer_curve_smoothing_exp": args.curve_exp,
            "offer_curve_smoothing_mid": args.curve_mid,
        },
        cc_derate_from_top=args.cc_derate_from_top,
        priced_interchange=args.priced_interchange,
        note=args.note,
    )
    report_run(run_dir)


if __name__ == "__main__":
    main()
