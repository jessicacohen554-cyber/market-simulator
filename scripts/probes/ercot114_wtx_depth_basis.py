"""ERCOT-114 Task B: re-derive the West-Texas curtailment DEPTH on the correct spatial basis.

ERCOT-113 refuted the per-zone wind SHAPE on the tilt and localized the cause: the
depth coefficient ``ercot_wtx_curtail_depth_wind`` was derived while wind was
spread flat across the zones, so putting wind where it physically is over-curtails
(``FINDING-ercot113-wind-zone-shape-2026-07-26.md`` section 5). This probe measures
that coupling exactly, and it finds the defect is sharper — and different — from
the "flat profile was silently compensating" reading.

**The actual defect is a units mismatch between derivation and application.**

``scripts/data/derive_ercot_wtx_curtailment_share.py::_depth`` computes

    depth = sum_t (HSL_ISO - GEN_ISO) / sum_t (HSL_ISO * share)

— numerator and denominator both **ISO-total**, read off the ISO-wide
``ercot-hsl`` parquet. But ``data.curtailment_share.wtx_curtail_multipliers``
applies ``1 - depth * share`` to the **West/Panhandle rows only**, so the
curtailment the LP actually sees is

    curt_applied = depth * sum_t (share * HSL_corridor)
                 = depth * sum_t (share * f(t) * HSL_ISO)

where ``f(t)`` is the corridor's share of ISO wind potential. The derivation
therefore under-delivers its own measured anchor by a factor of ``f`` under ANY
allocation — and ``f`` is exactly what the per-zone SHAPE changes. That makes the
two parameters one mechanism, which is why the charter requires them adjudicated
jointly.

This probe is **no-LP**. It builds the real zonal wind/solar arrays through the
production loader under both allocations (gate off = flat, gate on = per-zone
MERRA-2 SHAPE), measures ``f(t)`` for each, and re-derives the depth on the
corridor basis so ``curt_applied`` hits the measured curtailment quantity the
derive script was always centred on.

Usage:
    python scripts/probes/ercot114_wtx_depth_basis.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.curtailment_share import (  # noqa: E402
    WEST_CORRIDOR_ZONES,
    _share_lookup,
    load_share_table,
)
from market_sim.data.renewables import load_renewable_profiles  # noqa: E402

YEARS = (2023, 2024, 2025)


def _reported(year: int) -> dict[str, np.ndarray]:
    """Measured ISO wind/solar HSL potential and delivered generation (MW).

    The same ``ercot-hsl`` artifact and column convention the derive script's
    ``_reported_curtailment`` uses, so the anchor quantity is identical.
    """
    hsl = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")
    return {
        "wind_hsl": hsl["wind_hsl_mw"].to_numpy(dtype=float),
        "wind_gen": hsl["wind_gen_mw"].to_numpy(dtype=float),
        "solar_hsl": hsl["solar_hsl_mw"].to_numpy(dtype=float),
        "solar_gen": hsl["solar_gen_mw"].to_numpy(dtype=float),
    }


def _net_load(year: int, rep: dict[str, np.ndarray]) -> np.ndarray:
    """Measured system net load (demand - wind potential - solar potential).

    Same potential-based convention as the derive script, so the congestion
    share lands in the same (decile, hour-of-day, season) cells.
    """
    dem = pd.read_parquet(
        paths.RAW_DIR / "eia-930-hourly" / "ERCO hourly.parquet",
        columns=["Local date", "Hour", "Demand"],
    )
    dem["ld"] = pd.to_datetime(dem["Local date"])
    dem = dem[
        (dem["ld"].dt.year == year)
        & ~((dem["ld"].dt.month == 2) & (dem["ld"].dt.day == 29))
    ].sort_values(["ld", "Hour"])
    demand = dem["Demand"].to_numpy()[:8760]
    if len(demand) < 8760:
        demand = np.pad(
            demand, (0, 8760 - len(demand)), constant_values=float(np.nanmean(demand))
        )
    return demand - rep["wind_hsl"] - rep["solar_hsl"]


def _corridor_fraction(year: int, zone_shape: bool) -> dict[str, np.ndarray] | None:
    """Corridor share ``f(t)`` of ISO wind/solar potential, per hour.

    Runs the production renewable loader with ``ercot_wind_zone_shape`` set to
    ``zone_shape`` and reduces the per-zone ``cf x cap`` potential to the
    West/Panhandle fraction of the ISO total. Returns ``None`` if the loader
    cannot produce the year.
    """
    iso_config = get_iso_config("ERCOT")
    config = ScenarioConfig()
    config.mode = "backcast"
    config.ercot_wind_zone_shape = zone_shape
    try:
        wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
            "ERCOT", year, iso_config, config
        )
    except Exception as exc:  # pragma: no cover - diagnostic probe
        print(f"    loader failed for {year} (zone_shape={zone_shape}): {exc}")
        return None

    # iso_config.zones holds Zone objects; the LP consumer is handed zone NAMES.
    zones = [z.name for z in iso_config.zones]
    corridor = [i for i, z in enumerate(zones) if z in WEST_CORRIDOR_ZONES]
    if not corridor:
        raise RuntimeError(f"no West/Panhandle zone in {zones}")
    out = {}
    for tech, cf, cap in (("wind", wind_cf, wind_cap), ("solar", solar_cf, solar_cap)):
        pot = cf * np.asarray(cap, dtype=float)[:, None]  # (n_zones, T) MW
        tot = pot.sum(axis=0)
        cor = pot[corridor].sum(axis=0)
        out[tech] = np.divide(cor, tot, out=np.zeros_like(tot), where=tot > 0)
        out[f"{tech}_pot"] = tot
        out[f"{tech}_cor"] = cor
    return out


def _model_wind_twh(bundle: Path, year: int) -> float | None:
    """Model P1 wind dispatch (TWh) from a bundle's class sidecar, or ``None``."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    wind = df[df["klass"].astype(str).str.upper().str.contains("WIND")]
    if wind.empty:
        return None
    return float(wind["mw"].sum()) / 1e6


def total_curtailment_check(baseline: Path, shape_arm: Path) -> pd.DataFrame | None:
    """Total MODEL wind curtailment vs measured — the calibration target check.

    This is what decides which re-derivation is correct. The WTX driver is not
    the model's only source of curtailment: wind is an LP decision variable with
    MC ~ 0, so the dispatch curtails endogenously whenever the energy balance or
    a transmission limit cannot absorb it. Centring the *driver alone* on the
    full measured curtailment quantity would therefore double-count against that
    endogenous curtailment.

    Model curtailment is ``measured potential - model dispatch``, where the
    potential is the measured HSL series the backcast CF profile is built from.
    """
    rows = []
    for year in YEARS:
        rep = _reported(year)
        pot = float(rep["wind_hsl"].sum()) / 1e6
        measured_curt = float(np.clip(rep["wind_hsl"] - rep["wind_gen"], 0.0, None).sum()) / 1e6
        row = {"year": year, "potential_twh": pot, "measured_curt_twh": measured_curt}
        for label, bundle in (("baseline", baseline), ("shape", shape_arm)):
            twh = _model_wind_twh(bundle, year)
            if twh is None:
                continue
            row[f"{label}_wind_twh"] = twh
            row[f"{label}_curt_twh"] = pot - twh
            row[f"{label}_curt_err"] = (pot - twh) - measured_curt
        rows.append(row)
    return pd.DataFrame(rows).set_index("year") if rows else None


def main() -> None:
    """Report the corridor fraction and the corrected depth under both allocations."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--depth-wind",
        type=float,
        default=ScenarioConfig().ercot_wtx_curtail_depth_wind,
    )
    ap.add_argument(
        "--depth-solar",
        type=float,
        default=ScenarioConfig().ercot_wtx_curtail_depth_solar,
    )
    ap.add_argument(
        "--baseline",
        type=Path,
        default=REPO / "results/calibration/ercot_netrev_margin",
        help="baseline bundle for the W1b curtailment-quantity check",
    )
    ap.add_argument(
        "--arm",
        type=Path,
        default=REPO / "results/calibration/ercot113_wind_zone_shape",
        help="treatment bundle for the W1b curtailment-quantity check",
    )
    args = ap.parse_args()

    table = load_share_table(paths.RAW_DIR / "reference")
    if table is None:
        print("no congestion-share table — run the derive script first")
        return

    print("=" * 88)
    print("ERCOT-114 Task B: West-Texas curtailment DEPTH spatial basis")
    print("=" * 88)
    print(
        f"in-repo depth: wind={args.depth_wind:.4f} solar={args.depth_solar:.4f}  "
        "(derived ISO-total, applied corridor-only)"
    )

    # Accumulators for the pooled re-derivation, mirroring _depth's pooling.
    acc: dict[tuple[str, bool], dict[str, float]] = {}
    rows = []
    for year in YEARS:
        rep = _reported(year)
        share = _share_lookup(table, _net_load(year, rep))
        for zone_shape in (False, True):
            frac = _corridor_fraction(year, zone_shape)
            if frac is None:
                continue
            for tech in ("wind", "solar"):
                hsl, gen = rep[f"{tech}_hsl"], rep[f"{tech}_gen"]
                measured = float(np.clip(hsl - gen, 0.0, None).sum())
                # ISO-total denominator: what the derive script divides by.
                den_iso = float((hsl * share).sum())
                # Corridor denominator: what the LP actually multiplies depth by.
                # f(t) comes from the model's own allocation; the HSL level stays
                # the measured ISO potential so the anchor is unchanged.
                den_cor = float((hsl * share * frac[tech]).sum())
                key = (tech, zone_shape)
                a = acc.setdefault(key, {"m": 0.0, "iso": 0.0, "cor": 0.0})
                a["m"] += measured
                a["iso"] += den_iso
                a["cor"] += den_cor
                rows.append(
                    {
                        "year": year,
                        "tech": tech,
                        "alloc": "per-zone" if zone_shape else "flat",
                        "f_mean": float(np.average(frac[tech], weights=hsl))
                        if hsl.sum() > 0
                        else np.nan,
                        "measured_curt_gwh": measured / 1e3,
                        "applied_curt_gwh": (
                            args.depth_wind if tech == "wind" else args.depth_solar
                        )
                        * den_cor
                        / 1e3,
                    }
                )

    df = pd.DataFrame(rows)
    df["delivered_frac"] = df["applied_curt_gwh"] / df["measured_curt_gwh"]
    print()
    print("Per-year: corridor share of potential, and how much of the measured")
    print("curtailment the in-repo depth actually delivers:")
    print(
        df.pivot(index=["tech", "year"], columns="alloc",
                 values=["f_mean", "applied_curt_gwh", "delivered_frac"])
        .round(4)
        .to_string()
    )
    print()
    print(f"(measured curtailment GWh: "
          f"{df.groupby(['tech', 'year'])['measured_curt_gwh'].first().round(1).to_dict()})")

    print()
    print("=" * 88)
    print("RE-DERIVED depth on the CORRIDOR basis (pooled 2023-2025, as _depth pools)")
    print("=" * 88)
    out = []
    for (tech, zone_shape), a in sorted(acc.items()):
        out.append(
            {
                "tech": tech,
                "alloc": "per-zone" if zone_shape else "flat",
                "depth_iso_basis": a["m"] / a["iso"] if a["iso"] else np.nan,
                "depth_corridor_basis": a["m"] / a["cor"] if a["cor"] else np.nan,
                "corridor_share": a["cor"] / a["iso"] if a["iso"] else np.nan,
            }
        )
    res = pd.DataFrame(out)
    print(res.round(4).to_string(index=False))
    print()
    print("depth_iso_basis reproduces the in-repo value (it is the same formula);")
    print("depth_corridor_basis is the value that makes the APPLIED curtailment")
    print("equal the measured quantity the derive script is centred on.")

    print()
    print("=" * 88)
    print("CALIBRATION TARGET: is the driver the model's only curtailment?")
    print("=" * 88)
    chk = total_curtailment_check(args.baseline, args.arm)
    if chk is None:
        print("  bundles unavailable")
    else:
        print(f"  baseline={args.baseline.name}  arm={args.arm.name}")
        print(chk.round(3).to_string())
        if "shape_curt_twh" in chk and "baseline_curt_twh" in chk:
            # W1b as pre-committed: the arm's total curtailment must stay within
            # +/-0.5 TWh of the BASELINE's, which is what says the depth
            # re-derivation isolated the shape from the level.
            delta = chk["shape_curt_twh"] - chk["baseline_curt_twh"]
            print()
            print("  W1b curtailment-quantity preservation (|arm - baseline| <= 0.5 TWh):")
            for year, d in delta.items():
                print(f"    {year}: {d:+.3f} TWh  {'PASS' if abs(d) <= 0.5 else 'FAIL'}")

    print()
    print("=" * 88)
    print("QUANTITY-PRESERVING re-derivation (the spatial-basis correction)")
    print("=" * 88)
    print(
        "Holding the mechanism's calibrated curtailment QUANTITY fixed and changing\n"
        "only the spatial basis it is applied on:\n"
        "    depth_per_zone = depth_flat * corridor_share_flat / corridor_share_per_zone"
    )
    for tech, in_repo in (("wind", args.depth_wind), ("solar", args.depth_solar)):
        flat = acc.get((tech, False))
        zone = acc.get((tech, True))
        if not flat or not zone or not zone["cor"]:
            continue
        ratio = (flat["cor"] / flat["iso"]) / (zone["cor"] / zone["iso"])
        print(
            f"  {tech:6s}: {in_repo:.4f} x {ratio:.4f} = {in_repo * ratio:.4f}"
            + ("   (unchanged — the gate redistributes wind only)"
               if abs(ratio - 1.0) < 1e-9 else "")
        )


if __name__ == "__main__":
    main()
