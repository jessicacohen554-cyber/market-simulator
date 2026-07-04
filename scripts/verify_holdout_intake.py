#!/usr/bin/env python3
"""Dry-run check that the 2022 / H1-2026 holdout intake resolves end-to-end.

For ERCOT and PJM, loads each holdout year's driver, fleet, bench and overlay
inputs through the SAME loaders a backcast would use, and prints shapes and
non-zero counts — WITHOUT constructing or solving any LP. This proves the
2022 / 2026 intake (EIA-930 fuel-mix + demand, CAMPD unit-level, unit-outage
overlay, delivered gas) is loader-resolvable; it does NOT score anything
(holdout scoring is a separate, explicitly-authorized one-shot step —
CLAUDE.md rule 22).

Run:
    python scripts/verify_holdout_intake.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data import fuel as fuel_mod  # noqa: E402
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_eia_hourly_benchmark,
)
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402

CAMPD_DIR = REPO / "data" / "raw" / "campd-unit-level"
ISO_STATES = {
    "ERCOT": ("TX",),
    "PJM": (
        "IL",
        "IN",
        "MI",
        "OH",
        "PA",
        "WV",
        "VA",
        "MD",
        "DC",
        "DE",
        "NJ",
        "NC",
        "TN",
        "KY",
    ),
}
YEARS = (2022, 2026)


def _check_demand(iso: str, year: int) -> str:
    """Zonal demand via the model's own loader (full-year contract)."""
    try:
        d = load_demand(iso, year, get_iso_config(iso))
    except (AssertionError, ValueError, KeyError, IndexError) as exc:
        return f"NOT LOADABLE ({type(exc).__name__}: {exc})"
    return f"shape {d.shape}, nonzero {int((d > 0).sum()):,}, total {d.sum() / 1e6:.1f} TWh"


def _check_bench(iso: str, year: int) -> str:
    """EIA-930 fuel-mix bench via the calibration bench loader."""
    bench = load_eia_hourly_benchmark(iso, year)
    if bench is None:
        return "NOT LOADABLE (no rows)"
    fuels = sorted(bench)
    total = sum(np.nansum(v) for v in bench.values()) / 1e6
    # The bench loader pads a short year to 8760 with monthly means, so a
    # partial year LOOKS complete — report the raw published hours honestly.
    ba = {"ERCOT": "ERCO", "PJM": "PJM"}[iso]
    raw = pd.read_parquet(
        REPO / "data" / "raw" / "eia-930-hourly" / f"{ba} hourly.parquet",
        columns=["Local date"],
    )
    ld = raw.loc[raw["Local date"].dt.year == year, "Local date"]
    span = f"{ld.min().date()}..{ld.max().date()}" if len(ld) else "none"
    pad = "" if len(ld) >= 8760 else " — PARTIAL, loader pads to 8760"
    return (
        f"{len(fuels)} fuels x {len(bench[fuels[0]])} h, "
        f"raw published hours {len(ld):,} ({span}){pad}, sum {total:.1f} TWh"
    )


def _check_fleet(iso: str, year: int) -> str:
    """Thermal fleet via load_fleet_from_csv (per-year CHP refinement)."""
    gens = load_fleet_from_csv(iso, get_iso_config(iso), year=year)
    cap = sum(g.pmax_mw for g in gens)
    return f"{len(gens)} units, {cap / 1e3:.1f} GW"


def _check_campd(iso: str, year: int) -> str:
    """CAMPD unit-level parquet coverage (metadata only, no full read)."""
    rows, missing = 0, []
    for st in ISO_STATES[iso]:
        p = CAMPD_DIR / f"{st}_{year}.parquet"
        if p.exists():
            rows += pq.read_metadata(p).num_rows
        else:
            missing.append(st)
    out = f"{rows:,} unit-hour rows"
    if missing:
        out += f", MISSING states: {','.join(missing)}"
    return out


def _check_outages(iso: str, year: int) -> str:
    """Derived unit-outage overlay via the model's own reader."""
    hours = 8760
    fac = unit_outage_derate_factors(year, hours, iso=iso)
    if not fac:
        return "EMPTY (no windows for year)"
    derated = sum(int((v < 1.0).sum()) for v in fac.values())
    return f"{len(fac)} plant-groups, {derated:,} derated plant-hours"


def _check_gas(iso: str, year: int) -> str:
    """Delivered-gas overlays the keeper configs enable for this ISO."""
    if iso == "ERCOT":
        basis = fuel_mod.ercot_electric_power_gas_basis(year)
        zonal = fuel_mod._zonal_gas_basis_by_zone(
            fuel_mod.ERCOT_ZONAL_GAS_HUB_PATH, year
        )
        return (
            f"N3045TX3 basis {basis:+.3f}" if basis is not None else "N3045TX3 MISSING"
        ) + (
            f", zonal hub {len(zonal)} zones"
            if zonal
            else ", zonal hub MISSING (F923 Sch5/Waha follow-up)"
        )
    zonal = fuel_mod.pjm_zonal_gas_basis_by_zone(year)
    return f"zonal hub {len(zonal)} zones" if zonal else "zonal hub MISSING"


def main() -> None:
    """Print the per-ISO / per-year intake resolution table."""
    checks = (
        ("demand", _check_demand),
        ("fuel-mix bench", _check_bench),
        ("fleet", _check_fleet),
        ("campd unit-level", _check_campd),
        ("unit-outage overlay", _check_outages),
        ("delivered gas", _check_gas),
    )
    for iso in ("ERCOT", "PJM"):
        for year in YEARS:
            print(f"== {iso} {year}")
            for name, fn in checks:
                try:
                    print(f"  {name:20s} {fn(iso, year)}")
                except Exception as exc:  # surface, never mask
                    print(f"  {name:20s} ERROR {type(exc).__name__}: {exc}")
    print("\nNOTE: no LP was constructed or solved; this is a loader dry-run only.")


if __name__ == "__main__":
    main()
