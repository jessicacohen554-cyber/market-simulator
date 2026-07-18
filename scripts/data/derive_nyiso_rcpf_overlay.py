"""Derive the NYISO RCPF scarcity-price overlay for a solved bundle.

Post-solve only: reads a persisted NYISO calibration bundle (dispatch +
system parquets), reconstructs the hourly fleet availability the LP solved
against (same config, same outage overlay — no LP is re-solved), computes
the hourly reserve headroom and applies NYISO's Reserve Constraint Penalty
Factor demand curve (market_sim.results.rcpf). Volumes, dispatch parquets
and emissions are untouched; the overlay is written as a separate
``scarcity.parquet`` series next to the energy-only LMP.

Mirrors scripts/data/derive_ordc_overlay.py (the ERCOT ORDC overlay), but for
NYISO's reserve-demand-curve market design: the adder is the stacked
penalty of the nested operating-reserve products, and reserves come from
dispatchable thermal + storage headroom (curtailed renewables do NOT count
in NYISO, unlike ERCOT telemetry).

Steps:
  1. ``availability_rcpf.parquet`` — hourly system dispatchable-thermal
     available MW, thermal dispatch MW (final pass) and storage power cap,
     cached in the bundle (rebuilt with ``--rebuild-availability``).
  2. ``scarcity.parquet`` (or ``scarcity_<tag>.parquet``) — per
     (year, hour): reserves_mw, scarcity_adder, lmp, lmp_scarcity, plus a
     per-product price column.
  3. A stdout report: adder incidence per year, the model price
     distribution (percentiles + tail counts) and hourly LMP MAE vs the
     actual NYCA RT series, with and without the adder.

Usage:
    python scripts/data/derive_nyiso_rcpf_overlay.py results/calibration/nyiso_cal_2023
        [--years 2023 2024 2025] [--tag scenarioX] [--rebuild-availability]
        [--diagnostic]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import FUEL_TYPE_NAMES  # noqa: E402
from market_sim.results.rcpf import (  # noqa: E402
    locational_zone_adders,
    rcpf_adder,
    rcpf_product_prices,
    resolve_rcpf_locational,
    resolve_rcpf_products,
)

# Validation source (actual_lmp_hourly / actual_as_reserve / actual_lmp.json)
# relocated from the old inputs/calibration tree to data/raw/_validation-source
# (paths.CALIBRATION_DIR). The stale path silently NaN-filled the measured
# columns, so the overlay's measured-vs-model validation printed "--".
CAL_DIR = REPO / "data" / "raw" / "_validation-source"

# Dispatchable fossil fuel types that carry NYISO operating reserve. Nuclear
# is baseload (no reserve; its headroom is ~0 anyway), coal is retired in NY,
# and renewables / hydro are excluded (renewables provide no operating
# reserve in NYISO; hydro headroom is energy-limited — its omission is a
# small conservative bias). Storage headroom is added separately.
NYISO_RESERVE_FUEL_TYPES: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "oil"}
)

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum([0] + [d * 24 for d in _DAYS_IN_MONTH])


def _month_of_hour(hours: np.ndarray) -> np.ndarray:
    """Map non-leap hour-of-year indices to months 1-12."""
    return np.searchsorted(_MONTH_START_HOUR, hours, side="right").clip(1, 12)


def _final_pass(passes: "list[str] | set[str]") -> str:
    """The reported pass: P2 (commitment) when present, else P1."""
    return "P2" if "P2" in set(passes) else "P1"


def _run_year_kwargs(meta: dict) -> dict:
    """Mirror solve_and_persist's run_year call from a bundle's meta.json.

    Availability is pass-independent (the outage overlay + derates are the
    same in P1 and P2), so the reconstruction runs commitment-off.
    """
    return dict(
        ttc_overrides={},
        commitment_enabled=False,
        commitment_screen_coal=meta.get("commitment_screen_coal", True),
        coal_lignite_mustrun=meta.get("coal_lignite_mustrun"),
        coal_prb_mustrun=meta.get("coal_prb_mustrun"),
        coal_prb_passthrough=meta.get("coal_prb_passthrough", 1.0),
        outage_source=meta.get("outage_source", "historic"),
        coal_prb_passthrough_sigmoid=meta.get("coal_prb_passthrough_sigmoid", False),
        coal_mustrun_per_plant=meta.get("coal_mustrun_per_plant", False),
        ct_mustrun_per_plant=meta.get("ct_mustrun_per_plant", False),
        ct_mustrun_floor_frac=meta.get("ct_mustrun_floor_frac", 1.0),
        coal_drop_pof=meta.get("coal_drop_pof", False),
        coal_prb_passthrough_tiered=meta.get("coal_prb_passthrough_tiered", False),
        prb_overrides=meta.get("coal_prb_sigmoid_overrides") or None,
        coal_bit_sigmoid=meta.get("coal_bit_passthrough_sigmoid", False),
        bit_overrides=meta.get("coal_bit_sigmoid_overrides") or None,
        storage_daily_cycling=meta.get("storage_daily_cycling", False),
        battery_dispatch_adder=meta.get("battery_dispatch_adder", 0.0),
        gas_offer_curve=meta.get("gas_offer_curve", False),
        gas_monthly_actuals=meta.get("gas_monthly_actuals", False),
        offer_curve_overrides=meta.get("offer_curve_overrides") or None,
        offer_curve_deltas=meta.get("offer_curve_deltas") or None,
        curve_smoothing=meta.get("curve_smoothing") or None,
        cc_derate_from_top=meta.get("cc_derate_from_top", False),
        priced_interchange=meta.get("priced_interchange", False),
        hydro_backfill_year=meta.get("hydro_backfill_year"),
        hydro_eia930_monthly=meta.get("hydro_eia930_monthly", False),
        fleet_only=True,
    )


def build_availability(
    bundle: Path, years: list[int], meta: dict, pass_label: str, force: bool = False
) -> pd.DataFrame:
    """Reconstruct (or load) hourly reserve-fleet availability for the bundle.

    Returns a frame with columns ``year``, ``hour``, ``thermal_avail_mw``
    (sum of pmax x availability over the NYISO reserve-providing fossil
    fleet), ``thermal_dispatch_mw`` (the same units' solved final-pass
    dispatch) and ``storage_power_cap_mw``. Cached as
    ``availability_rcpf.parquet``; the rebuild loads the fleet through the
    exact configuration recorded in meta.json (no LP solve).
    """
    out_path = bundle / "availability_rcpf.parquet"
    if out_path.exists() and not force:
        cached = pd.read_parquet(out_path)
        if set(cached["year"].unique()) >= set(years):
            return cached

    from run_calibration import run_year  # late import: heavy module

    frames = []
    for year in years:
        state = run_year(
            year,
            meta["iso"],
            meta["hours"],
            meta["gas_prices"][str(year)],
            **_run_year_kwargs(meta),
        )
        fa = state["fleet_arrays"]
        fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
        thermal = np.isin(fuel_names, sorted(NYISO_RESERVE_FUEL_TYPES))
        avail = (fa.pmax[thermal, None] * fa.availability[thermal]).sum(axis=0)
        thermal_units = set(np.asarray(fa.unit_ids, dtype=object)[thermal])

        disp = pd.read_parquet(bundle / "dispatch" / f"{year}_{pass_label}.parquet")
        disp_t = (
            disp[disp["unit_id"].astype(str).isin(thermal_units)]
            .groupby("hour")["mw"]
            .sum()
            .reindex(range(meta["hours"]), fill_value=0.0)
            .to_numpy()
        )

        cap = np.asarray(state["storage_power_cap"], dtype=float)
        cap_t = cap.sum(axis=0) if cap.ndim == 2 else np.full(meta["hours"], cap.sum())

        frames.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "hour": np.arange(meta["hours"], dtype=np.int32),
                    "thermal_avail_mw": avail.astype(np.float32),
                    "thermal_dispatch_mw": disp_t.astype(np.float32),
                    "storage_power_cap_mw": cap_t.astype(np.float32),
                }
            )
        )
        print(
            f"  {year}: reserve-fleet avail mean {avail.mean():,.0f} MW, "
            f"dispatch mean {disp_t.mean():,.0f} MW, headroom mean "
            f"{(avail - disp_t).mean():,.0f} MW, storage cap mean "
            f"{cap_t.mean():,.0f} MW"
        )
    df = pd.concat(frames, ignore_index=True)
    df.to_parquet(out_path, index=False)
    print(f"wrote {out_path}")
    return df


def _model_zone_names(meta: dict) -> list[str]:
    """The model topology's zone order (matches fleet ``zone_idx``).

    Rebuilds the NYISO config the solve used (the external import node joins
    the topology under ``--priced-interchange``), so ``zone_idx`` lines up
    with these names. The external node carries no load/reserve and is
    excluded from the locational reserve regions.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.transmission import extend_with_import_node

    cfg = get_iso_config(meta["iso"])
    if meta.get("priced_interchange"):
        cfg = extend_with_import_node(cfg)
    return list(cfg.zone_names)


def build_zonal_availability(
    bundle: Path, years: list[int], meta: dict, pass_label: str, force: bool = False
) -> pd.DataFrame:
    """Reconstruct (or load) per-model-zone hourly reserve-fleet availability.

    The locational analogue of :func:`build_availability`: a long frame with
    columns ``year``, ``hour``, ``zone``, ``thermal_avail_mw`` (the zone's
    reserve-providing fossil fleet pmax x availability), ``thermal_dispatch_mw``
    (those units' solved final-pass dispatch in the zone) and
    ``storage_power_cap_mw`` (the zone's storage discharge cap). Cached as
    ``availability_rcpf_zonal.parquet``. No LP solve (same config as meta.json).
    """
    out_path = bundle / "availability_rcpf_zonal.parquet"
    if out_path.exists() and not force:
        cached = pd.read_parquet(out_path)
        if set(cached["year"].unique()) >= set(years):
            return cached

    from run_calibration import run_year  # late import: heavy module

    zone_names = _model_zone_names(meta)
    frames = []
    for year in years:
        state = run_year(
            year,
            meta["iso"],
            meta["hours"],
            meta["gas_prices"][str(year)],
            **_run_year_kwargs(meta),
        )
        fa = state["fleet_arrays"]
        fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
        thermal = np.isin(fuel_names, sorted(NYISO_RESERVE_FUEL_TYPES))
        zidx = np.asarray(fa.zone_idx)

        disp = pd.read_parquet(bundle / "dispatch" / f"{year}_{pass_label}.parquet")
        disp_t = disp[disp["fuel"].astype(str).isin(NYISO_RESERVE_FUEL_TYPES)]
        disp_by_zone = (
            disp_t.groupby(["zone", "hour"])["mw"]
            .sum()
            .unstack(fill_value=0.0)
            .reindex(columns=range(meta["hours"]), fill_value=0.0)
        )

        # Per-zone storage discharge power cap (sum over the zone's ESRs).
        cap = np.asarray(state["storage_power_cap"], dtype=float)
        storage_units = state.get("storage_units") or []
        cap_by_zone: dict[str, np.ndarray] = {}
        for i, unit in enumerate(storage_units):
            z = getattr(unit, "zone", None)
            row = cap[i] if cap.ndim == 2 else np.full(meta["hours"], cap[i])
            cap_by_zone[z] = cap_by_zone.get(z, np.zeros(meta["hours"])) + row

        for zi, zone in enumerate(zone_names):
            sel = thermal & (zidx == zi)
            avail = (
                (fa.pmax[sel, None] * fa.availability[sel]).sum(axis=0)
                if sel.any()
                else np.zeros(meta["hours"])
            )
            disp_z = (
                disp_by_zone.loc[zone].to_numpy()
                if zone in disp_by_zone.index
                else np.zeros(meta["hours"])
            )
            frames.append(
                pd.DataFrame(
                    {
                        "year": np.int16(year),
                        "hour": np.arange(meta["hours"], dtype=np.int32),
                        "zone": zone,
                        "thermal_avail_mw": avail.astype(np.float32),
                        "thermal_dispatch_mw": disp_z.astype(np.float32),
                        "storage_power_cap_mw": cap_by_zone.get(
                            zone, np.zeros(meta["hours"])
                        ).astype(np.float32),
                    }
                )
            )
    df = pd.concat(frames, ignore_index=True)
    df.to_parquet(out_path, index=False)
    print(f"wrote {out_path}")
    return df


def _storage_headroom(
    bundle: Path,
    year: int,
    hours: int,
    pass_label: str,
    cap_t: np.ndarray,
    zone: "str | None" = None,
) -> np.ndarray:
    """Storage headroom: power cap - discharge + charge (ESR convention).

    System-wide when ``zone`` is None; otherwise restricted to one model zone.
    """
    p = bundle / "storage.parquet"
    if not p.exists():
        return cap_t
    st = pd.read_parquet(p)
    st = st[st["year"] == year]
    if "pass" in st.columns and (st["pass"] == pass_label).any():
        st = st[st["pass"] == pass_label]
    if zone is not None:
        st = st[st["zone"] == zone]
    g = (
        st.groupby("hour")[["charge_mw", "discharge_mw"]]
        .sum()
        .reindex(range(hours), fill_value=0.0)
    )
    return cap_t - g["discharge_mw"].to_numpy() + g["charge_mw"].to_numpy()


def _system_lambda(bundle: Path, year: int, hours: int, pass_label: str) -> np.ndarray:
    """Demand-weighted hourly system price — the NYCA-hub model price."""
    sy = pd.read_parquet(bundle / "system.parquet")
    sy = sy[sy["year"] == year]
    if "pass" in sy.columns and (sy["pass"] == pass_label).any():
        sy = sy[sy["pass"] == pass_label]
    g = (
        sy.assign(pd_=sy["price"] * sy["demand"])
        .groupby("hour")
        .agg(pd_=("pd_", "sum"), d=("demand", "sum"), p=("price", "mean"))
    )
    lam = np.where(g["d"] > 0, g["pd_"] / g["d"], g["p"])
    out = np.full(hours, np.nan)
    out[g.index.to_numpy()] = lam
    return out


def _zonal_lambda(
    bundle: Path, year: int, hours: int, pass_label: str
) -> dict[str, np.ndarray]:
    """Per-model-zone hourly energy price (the zonal LBMP the LP solved)."""
    sy = pd.read_parquet(bundle / "system.parquet")
    sy = sy[sy["year"] == year]
    if "pass" in sy.columns and (sy["pass"] == pass_label).any():
        sy = sy[sy["pass"] == pass_label]
    out: dict[str, np.ndarray] = {}
    for zone, g in sy.groupby("zone"):
        arr = np.full(hours, np.nan)
        arr[g["hour"].to_numpy()] = g["price"].to_numpy()
        out[str(zone)] = arr
    return out


def _demand_weights(bundle: Path, year: int, hours: int, pass_label: str) -> np.ndarray:
    """Hourly total demand, the weight series for demand-weighted MAE."""
    sy = pd.read_parquet(bundle / "system.parquet")
    sy = sy[sy["year"] == year]
    if "pass" in sy.columns and (sy["pass"] == pass_label).any():
        sy = sy[sy["pass"] == pass_label]
    g = sy.groupby("hour")["demand"].sum().reindex(range(hours))
    return g.to_numpy()


def _actual_rt(year: int, hours: int) -> np.ndarray:
    """Actual NYCA-hub hourly RT price for NYISO, NaN-padded."""
    p = CAL_DIR / "actual_lmp_hourly_NYISO.parquet"
    if not p.exists():
        return np.full(hours, np.nan)
    act = pd.read_parquet(p)
    act = act[act["year"] == year]
    out = np.full(hours, np.nan)
    out[act["hour"].to_numpy()] = act["rt"].to_numpy()
    return out


def _actual_as_reserve(year: int, hours: int) -> dict[str, np.ndarray]:
    """Measured RT reserve adder (NYCA + NYC) for a year, NaN-padded.

    From ``actual_as_reserve_NYISO.parquet`` (built by
    ``scripts/data/process_nyiso_as.py`` from the NYISO OASIS rtasp downloads):
    ``nyca_reserve_adder`` is the system-wide reserve price the overlay's
    system-wide adder should reproduce; ``nyc_reserve_adder`` is the full
    downstate cascade the (future) locational products target.
    """
    p = CAL_DIR / "actual_as_reserve_NYISO.parquet"
    out = {"nyca": np.full(hours, np.nan), "nyc": np.full(hours, np.nan)}
    if not p.exists():
        return out
    ref = pd.read_parquet(p)
    ref = ref[ref["year"] == year]
    h = ref["hour"].to_numpy()
    out["nyca"][h] = ref["nyca_reserve_adder"].to_numpy()
    out["nyc"][h] = ref["nyc_reserve_adder"].to_numpy()
    return out


# Representative NYISO settlement zone for each model zone's measured RT
# reserve price (the stacked spin_10 + nonsync_10 + op_30 cascade in
# NYISO_as_rt_<year>.csv). Each model zone validates against the NYISO zone
# whose cascade tier it carries (process_nyiso_as.py): A-E share the NYCA
# tier, F adds East, G-K add SENY, J adds NYC.
_MODEL_ZONE_TO_NYISO_AS = {
    "Upstate_West": "WEST",
    "Capital_Hudson": "CAPITL",
    "Lower_Hudson": "DUNWOD",
    "NYC": "N.Y.C.",
    "Long_Island": "LONGIL",
}


def _actual_zone_reserve(year: int, hours: int) -> dict[str, np.ndarray]:
    """Measured per-model-zone stacked RT reserve price, NaN-padded.

    Prefers the committed compact reference
    (``data/raw/_validation-source/actual_as_reserve_NYISO.parquet``, which carries one
    ``reserve_<model_zone>`` column per model zone, built by
    scripts/data/process_nyiso_as.py); falls back to the raw per-zone RT CSV. The
    value is the stacked reserve price (10-min spin + 10-min non-sync + 30-min
    operating) of the settlement zone whose cascade tier the model zone carries
    — the empirical target the modeled locational adder is validated against.
    Empty when neither source is available.
    """
    ref = CAL_DIR / "actual_as_reserve_NYISO.parquet"
    if ref.exists():
        rf = pd.read_parquet(ref)
        rf = rf[rf["year"] == year]
        cols = {z: f"reserve_{z}" for z in _MODEL_ZONE_TO_NYISO_AS}
        if rf.shape[0] and all(c in rf.columns for c in cols.values()):
            out: dict[str, np.ndarray] = {}
            for zone, col in cols.items():
                arr = np.full(hours, np.nan)
                arr[rf["hour"].to_numpy()] = rf[col].to_numpy()
                out[zone] = arr
            return out
    p = REPO / "data" / "raw" / "NYISO-AS" / f"NYISO_as_rt_{year}.csv"
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    df["stack"] = df[["spin_10", "nonsync_10", "op_30"]].sum(axis=1)
    ts = pd.to_datetime(df["Time Stamp"], errors="coerce")
    keep = ts.notna() & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    hoy = (
        _MONTH_START_HOUR[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    df = df.assign(hour=hoy)
    out: dict[str, np.ndarray] = {}
    for model_zone, ny_zone in _MODEL_ZONE_TO_NYISO_AS.items():
        s = (
            df[df["Name"] == ny_zone]
            .groupby("hour")["stack"]
            .max()
            .reindex(range(hours))
        )
        out[model_zone] = s.to_numpy(dtype=float)
    return out


def _mae(
    model: np.ndarray, actual: np.ndarray, weights: np.ndarray | None = None
) -> float:
    """Weighted mean absolute error, NaNs dropped."""
    ok = np.isfinite(model) & np.isfinite(actual)
    if weights is None:
        weights = np.ones_like(model)
    w = weights[ok]
    return float(np.sum(np.abs(model[ok] - actual[ok]) * w) / w.sum())


def _monthly_mae(model: np.ndarray, rt: np.ndarray, demand: np.ndarray) -> float:
    """Monthly demand-weighted LMP MAE (the calibration gate metric)."""
    mon = _month_of_hour(np.arange(len(model)))
    diffs, weights = [], []
    for m in range(1, 13):
        sel = (mon == m) & np.isfinite(rt) & np.isfinite(model)
        if not sel.any():
            continue
        mm = float(np.average(model[sel], weights=demand[sel]))
        diffs.append(abs(mm - float(np.nanmean(rt[sel]))))
        weights.append(float(demand[sel].sum()))
    return float(np.average(diffs, weights=weights)) if diffs else np.nan


_PCTS = [1, 5, 25, 50, 75, 95, 99]


def _dist(series: np.ndarray) -> dict:
    """min / percentiles / max of a finite series."""
    s = series[np.isfinite(series)]
    out = {"min": float(s.min()), "max": float(s.max())}
    for p in _PCTS:
        out[f"p{p}"] = float(np.percentile(s, p))
    return out


def _actual_dist(year: int) -> dict | None:
    """Actual RT percentile block from actual_lmp.json, if present."""
    p = CAL_DIR / "actual_lmp.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    blk = d.get("NYISO", d).get(str(year), {})
    return blk.get("rt_pct")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument(
        "--tag", default=None, help="write scarcity_<tag>.parquet (scenario runs)"
    )
    ap.add_argument(
        "--diagnostic",
        action="store_true",
        help="print headroom-vs-actual-tail localization only",
    )
    ap.add_argument(
        "--locational",
        action="store_true",
        help="per-zone locational reserve overlay (East/SENY/NYC) "
        "validated against the measured per-zone RT reserve",
    )
    ap.add_argument("--rebuild-availability", action="store_true")
    args = ap.parse_args()

    bundle = args.bundle.resolve()
    meta = json.loads((bundle / "meta.json").read_text())
    if meta["iso"] != "NYISO":
        raise SystemExit("NYISO RCPF scarcity overlay is NYISO-only")
    years = args.years or meta["years"]
    hours = meta["hours"]
    pass_label = _final_pass(meta.get("passes", ["P1"]))

    config = ScenarioConfig(iso="NYISO", mode="backcast", nyiso_rcpf_enabled=True)
    products = resolve_rcpf_products(config)
    print(f"bundle {bundle.name}: years {years}, reported pass {pass_label}")
    print("RCPF products (name, requirement_MW, critical_MW, max_$/MWh):")
    for prod in products:
        print(
            f"  {prod[0]}: req {prod[1]:,.0f}  crit {prod[2]:,.0f}  max ${prod[3]:,.0f}"
        )

    if args.locational:
        locational(
            bundle,
            years,
            meta,
            pass_label,
            config,
            args.tag,
            force=args.rebuild_availability,
        )
        return

    avail = build_availability(
        bundle, years, meta, pass_label, force=args.rebuild_availability
    )

    if args.diagnostic:
        diagnostic(avail, bundle, years, hours, pass_label)
        return

    frames = []
    for year in years:
        a = avail[avail["year"] == year]
        cap_t = a["storage_power_cap_mw"].to_numpy(float)
        reserves = (
            a["thermal_avail_mw"].to_numpy(float)
            - a["thermal_dispatch_mw"].to_numpy(float)
            + _storage_headroom(bundle, year, hours, pass_label, cap_t)
        )
        pp = rcpf_product_prices(reserves, config)
        adder = pp["adder"]
        lam = _system_lambda(bundle, year, hours, pass_label)

        frame = {
            "year": np.int16(year),
            "hour": np.arange(hours, dtype=np.int32),
            "reserves_mw": reserves.astype(np.float32),
            "scarcity_adder": adder.astype(np.float32),
            "lmp": lam.astype(np.float32),
            "lmp_scarcity": (lam + adder).astype(np.float32),
        }
        for prod in products:
            frame[f"price_{prod[0]}"] = pp[prod[0]].astype(np.float32)
        frames.append(pd.DataFrame(frame))

        # Report: incidence, distribution and the LMP gate metrics.
        rt = _actual_rt(year, hours)
        w = _demand_weights(bundle, year, hours, pass_label)
        mae0 = _monthly_mae(lam, rt, w)
        mae1 = _monthly_mae(lam + adder, rt, w)
        print(
            f"\n{year}: adder>$1 in {int((adder > 1).sum())} h, >$50 in "
            f"{int((adder > 50).sum())} h, >$200 in "
            f"{int((adder > 200).sum())} h, max ${adder.max():,.0f}; "
            f"mean ${adder.mean():.2f}"
        )
        print(
            f"  reserves (MW) p1/p5/p50 = "
            f"{np.percentile(reserves, [1, 5, 50]).round(0)}"
        )
        print(
            f"  monthly LMP MAE (gate) {mae0:.1f} -> {mae1:.1f} $/MWh; "
            f"hourly dw-MAE {_mae(lam, rt, w):.1f} -> "
            f"{_mae(lam + adder, rt, w):.1f}"
        )
        for thr in (100, 200, 500):
            print(
                f"  hours >${thr}: actual {int(np.nansum(rt > thr))}, "
                f"model {int(np.nansum(lam > thr))} -> "
                f"{int(np.nansum((lam + adder) > thr))}"
            )
        md0, md1 = _dist(lam), _dist(lam + adder)
        ad = _actual_dist(year)
        cols = ["min", "p50", "p95", "p99", "max"]
        print("  distribution ($/MWh)   " + "  ".join(f"{c:>7}" for c in cols))
        print("    model energy-only    " + "  ".join(f"{md0[c]:7.0f}" for c in cols))
        print("    model + RCPF         " + "  ".join(f"{md1[c]:7.0f}" for c in cols))
        if ad:
            print(
                "    actual RT            "
                + "  ".join(f"{ad.get(c, float('nan')):7.0f}" for c in cols)
            )

        # Validate the model adder against the MEASURED RT reserve price
        # (process_nyiso_as.py): the system-wide overlay targets the NYCA
        # (upstate) reserve adder; the downstate NYC cascade is the
        # locational products' (future) target. This is the model-vs-measured
        # check that keeps the curve honest rather than a magic number.
        meas = _actual_as_reserve(year, hours)
        if np.isfinite(meas["nyca"]).any():
            for label, key in (
                ("NYCA (system-wide)", "nyca"),
                ("NYC  (downstate)", "nyc"),
            ):
                m = meas[key]
                ok = np.isfinite(m)
                print(
                    f"  measured RT reserve adder {label}: >$0 in "
                    f"{int((m[ok] > 0).sum()):,} h, >$50 in "
                    f"{int((m[ok] > 50).sum()):,} h, max ${np.nanmax(m):,.0f}, "
                    f"mean ${np.nanmean(m):.2f}  (model adder mean "
                    f"${adder.mean():.2f})"
                )

    out = pd.concat(frames, ignore_index=True)
    name = f"scarcity_{args.tag}.parquet" if args.tag else "scarcity.parquet"
    out.to_parquet(bundle / name, index=False)
    print(f"\nwrote {bundle / name}")


def locational(
    bundle: Path,
    years: list[int],
    meta: dict,
    pass_label: str,
    config,
    tag: "str | None",
    force: bool = False,
) -> None:
    """Per-zone locational RCPF overlay: stack East/SENY/NYC reserve adders.

    Builds per-model-zone reserve headroom (build_zonal_availability), then
    for each zone the total scarcity adder = the system-wide NYCA adder (same
    for every zone) + the locational adder (sum of the demand-curve prices of
    every reserve region containing the zone, on that region's headroom;
    results.rcpf.locational_zone_adders). The adder is stacked onto the zone's
    energy LBMP and written to ``scarcity_locational[_<tag>].parquet`` (long,
    per year/hour/zone). Validates each zone's modeled adder against the
    measured per-zone RT reserve price (process_nyiso_as.py) — the empirical
    cascade the regions are meant to reproduce, not a fitted target.
    """
    zone_names = [z for z in _model_zone_names(meta) if z != "NYISO_external"]
    regions = resolve_rcpf_locational(config)
    print("\nlocational reserve regions (region: zones | products):")
    for name, reg in regions.items():
        members = [z for z in reg["zones"] if z in zone_names]
        prods = (
            ", ".join(
                f"{p[0]}(req {p[1]:,.0f}, max ${p[3]:,.0f})" for p in reg["products"]
            )
            or "(scaffolded, empty)"
        )
        print(f"  {name}: {'+'.join(members)} | {prods}")

    zavail = build_zonal_availability(bundle, years, meta, pass_label, force=force)

    frames = []
    for year in years:
        za = zavail[zavail["year"] == year]
        # Per-zone reserve headroom (thermal headroom + storage headroom).
        zone_reserves: dict[str, np.ndarray] = {}
        for zone in zone_names:
            z = za[za["zone"] == zone]
            cap_t = z["storage_power_cap_mw"].to_numpy(float)
            zone_reserves[zone] = (
                z["thermal_avail_mw"].to_numpy(float)
                - z["thermal_dispatch_mw"].to_numpy(float)
                + _storage_headroom(
                    bundle, year, meta["hours"], pass_label, cap_t, zone=zone
                )
            )
        # System-wide NYCA adder (same for every zone) + locational adders.
        system_reserves = sum(zone_reserves.values())
        nyca = rcpf_adder(system_reserves, config=config)
        loc = locational_zone_adders(zone_reserves, config=config)
        lam = _zonal_lambda(bundle, year, meta["hours"], pass_label)
        meas = _actual_zone_reserve(year, meta["hours"])

        print(
            f"\n=== {year} per-zone locational adder vs measured RT reserve "
            f"(NYISO zone) ==="
        )
        hdr = "  %-15s %-7s  %8s %8s %8s   %8s %8s %8s" % (
            "model zone",
            "NYISO",
            "mdl>$0h",
            "mdl_mean",
            "mdl_max",
            "meas>$0h",
            "meas_mean",
            "meas_max",
        )
        print(hdr)
        for zone in zone_names:
            adder = nyca + loc.get(zone, np.zeros(meta["hours"]))
            frames.append(
                pd.DataFrame(
                    {
                        "year": np.int16(year),
                        "hour": np.arange(meta["hours"], dtype=np.int32),
                        "zone": zone,
                        "reserves_mw": zone_reserves[zone].astype(np.float32),
                        "nyca_adder": nyca.astype(np.float32),
                        "locational_adder": loc.get(
                            zone, np.zeros(meta["hours"])
                        ).astype(np.float32),
                        "scarcity_adder": adder.astype(np.float32),
                        "lmp": lam.get(zone, np.full(meta["hours"], np.nan)).astype(
                            np.float32
                        ),
                        "lmp_scarcity": (
                            lam.get(zone, np.full(meta["hours"], np.nan)) + adder
                        ).astype(np.float32),
                    }
                )
            )
            m = meas.get(zone)
            ny = _MODEL_ZONE_TO_NYISO_AS.get(zone, "")
            if m is not None and np.isfinite(m).any():
                ok = np.isfinite(m)
                print(
                    "  %-15s %-7s  %8d %8.2f %8.0f   %8d %8.2f %8.0f"
                    % (
                        zone,
                        ny,
                        int((adder > 0).sum()),
                        float(adder.mean()),
                        float(adder.max()),
                        int((m[ok] > 0).sum()),
                        float(np.nanmean(m)),
                        float(np.nanmax(m)),
                    )
                )
            else:
                print(
                    "  %-15s %-7s  %8d %8.2f %8.0f   %8s %8s %8s"
                    % (
                        zone,
                        ny,
                        int((adder > 0).sum()),
                        float(adder.mean()),
                        float(adder.max()),
                        "-",
                        "-",
                        "-",
                    )
                )

    out = pd.concat(frames, ignore_index=True)
    name = (
        f"scarcity_locational_{tag}.parquet" if tag else "scarcity_locational.parquet"
    )
    out.to_parquet(bundle / name, index=False)
    print(f"\nwrote {bundle / name}")


def diagnostic(
    avail: pd.DataFrame, bundle: Path, years: list[int], hours: int, pass_label: str
) -> None:
    """Print actual-tail localization vs model headroom (pre-adder gate).

    If the model is NOT thin (low headroom) in the hours reality priced
    scarcity, the overlay would be papering over an availability/load-shape
    problem rather than pricing a real shortage — surface that before use.
    """
    for year in years:
        a = avail[avail["year"] == year]
        cap_t = a["storage_power_cap_mw"].to_numpy(float)
        headroom = (
            a["thermal_avail_mw"].to_numpy(float)
            - a["thermal_dispatch_mw"].to_numpy(float)
            + _storage_headroom(bundle, year, hours, pass_label, cap_t)
        )
        rt = _actual_rt(year, hours)
        ok = np.isfinite(rt)
        print(f"\n=== {year} model reserve headroom by actual-RT band ===")
        bands = [(-np.inf, 50), (50, 100), (100, 300), (300, np.inf)]
        labels = ["<$50", "$50-100", "$100-300", ">$300"]
        for (lo, hi), lab in zip(bands, labels):
            sel = ok & (rt >= lo) & (rt < hi)
            if not sel.any():
                continue
            hr = headroom[sel]
            print(
                f"  actual RT {lab:>9}: {int(sel.sum()):5d} h, headroom "
                f"p5/p25/p50 = {np.percentile(hr, [5, 25, 50]).round(0)} MW"
            )


if __name__ == "__main__":
    main()
