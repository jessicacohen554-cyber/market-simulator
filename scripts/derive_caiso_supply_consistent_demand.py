"""Derive the supply-consistent CAISO backcast demand series (no LP solve).

Owner-signed caiso-80 Option A
(``results/calibration/FINDING-caiso80-demand-basis-wedge-2026-07-13.md`` §6):
the CISO EIA-930 ``Demand`` cell carries the same fabricated solar-shaped
block as the corrupt ``NG: NG`` cell by the ``Demand = NetGen + TI`` identity
(onset 2024-05), plus a ~6 TWh/yr flat CHP host-accounting wedge and the
chronic 930 identity gap — +10.4/+11.6/+18.5 TWh/yr (2023/24/25) that the
transmission-level grid fleet the model represents did not serve. This script
rebuilds the demand input on the honest CEMS-anchored basis the run is scored
against:

    demand(t) = [930 NetGen(t) − NG_cell(t)
                 + CEMS bench-gas grid(t)          (committed bench hourly)
                 + gas_cogen_grid / 8760           (committed anchor, flat)
                 + geo/biomass fold-in / 8760      (render's own fold-in)]
                − TI(t)

Every term is a measured input (rule 14): the 930 cells from the committed
``CISO hourly`` extract, the CEMS gas hourly and the cogen/fold-in anchors
from the committed CEMS-anchored bench parts (the owner-signed bench-rework
basis, ``scripts/regen_caiso_bench_cems.py``). The series regenerates for any
year from source data and re-derives only when the sources update (rule 23).
It is built on the generation frame's clock (the same rows the renewables
ride), so the Demand cell's +1 h clock convention (caiso-75) never enters.

Writes ``data/raw/reference/caiso-supply-consistent-demand/
caiso_supply_consistent_demand_<year>.csv`` (8760 rows: hour, demand_mw +
audit columns) plus a ``provenance.json`` sidecar with the annual totals and
anchors. Guard rails fail LOUDLY if the decoded CEMS hourly drifts from the
committed ``gas_cems_grid`` anchor or the derived annual total moves outside
the FINDING §6 pre-registered window.

Usage:
    python scripts/derive_caiso_supply_consistent_demand.py
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO / "src", _REPO, _REPO / "scripts"):
    sys.path.insert(0, str(_p))

from market_sim.config.paths import (  # noqa: E402
    CAISO_SUPPLY_CONSISTENT_DEMAND_DIR,
)
from market_sim.data.eia_loader import _eia_hourly_frame_filled  # noqa: E402

import scripts.legitimacy_diagnostics as L  # noqa: E402


def _load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, str(_REPO / rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
# FINDING §6 pre-registered annual levels (TWh) ±1.5 TWh tolerance: a derive
# outside these windows means an input drifted — refuse to write.
_ANNUAL_GUARD = {2023: (206.2, 209.2), 2024: (210.9, 213.9), 2025: (203.8, 206.8)}
# Committed-anchor reproduction tolerance (TWh) for the decoded CEMS hourly.
_ANCHOR_TOL = 0.1


def _year_frame(year: int) -> pd.DataFrame:
    """The CISO 930 hourly rows as local hour-of-year (non-leap 8760).

    Uses the loader's own gap-bridging frame
    (:func:`market_sim.data.eia_loader._eia_hourly_frame_filled`) so the
    artifact rides the exact clock the solve's demand/renewables ride;
    isolated missing hours come back as NaN rows and are interpolated below,
    the same treatment ``_load_caiso_hourly_demand`` applies to the raw cell.
    """
    frame = _eia_hourly_frame_filled("CISO", year)
    if frame is None:
        raise SystemExit(f"CISO {year}: no usable 8760-hour 930 frame")
    return frame


def main() -> int:
    rch = _load_module("rch", "scripts/render_calibration_html.py")
    gas_groups = set(rch._GAS_GROUPS)
    out_dir = CAISO_SUPPLY_CONSISTENT_DEMAND_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    provenance: dict[str, dict] = {}

    for year in YEARS:
        part = json.loads(
            gzip.decompress(
                (
                    _REPO / "frontend/data/backcast/bench" / ISO / f"{year}.json.gz"
                ).read_bytes()
            )
        )
        bench = part["bench"]
        e930 = bench["e930"]
        if "gas_cems_grid" not in e930:
            raise SystemExit(
                f"{ISO} {year}: bench part carries no CEMS anchor — run "
                "scripts/regen_caiso_bench_cems.py first."
            )

        # CEMS bench-gas hourly, grid-delivered: decoded committed per-plant
        # series (c_ann-rescaled), gas groups only, flat per-plant BTM share.
        plants = L.load_bench(_REPO, ISO, year)
        cems_grid = np.zeros(HOURS)
        for pid, meta in bench["plants"].items():
            if meta.get("nodata") or meta["group"] not in gas_groups:
                continue
            hourly = plants.get(pid)
            if hourly is None:
                continue
            c_ann = float(meta.get("c_ann") or 0.0)
            btm = float(meta.get("btm") or 0.0)
            share = (1.0 - btm / c_ann) if c_ann > 0 else 1.0
            cems_grid += hourly["mw"] * share
        anchor = float(e930["gas_cems_grid"])
        if abs(cems_grid.sum() / 1e6 - anchor) > _ANCHOR_TOL:
            raise SystemExit(
                f"GUARD FAIL {ISO} {year}: decoded CEMS gas grid "
                f"{cems_grid.sum() / 1e6:.3f} TWh vs committed anchor "
                f"{anchor:.3f} — bench/plant decode mismatch."
            )

        cogen_flat = float(e930["gas_cogen_grid"]) * 1e6 / HOURS
        foldin_twh = rch._gas_foldin_deflation(bench["classFull"], e930, ISO)
        foldin_flat = foldin_twh * 1e6 / HOURS

        frame = _year_frame(year)
        netgen = frame["Net generation"].interpolate().bfill().ffill().to_numpy(float)
        ng_cell = frame["NG: NG"].interpolate().bfill().ffill().to_numpy(float)
        ti = frame["Total interchange"].interpolate().bfill().ffill().to_numpy(float)

        demand = netgen - ng_cell + cems_grid + cogen_flat + foldin_flat - ti
        total = demand.sum() / 1e6
        lo, hi = _ANNUAL_GUARD[year]
        if not (lo <= total <= hi):
            raise SystemExit(
                f"GUARD FAIL {ISO} {year}: derived demand {total:.2f} TWh "
                f"outside pre-registered [{lo}, {hi}] (FINDING §6)."
            )
        if demand.min() <= 0:
            raise SystemExit(
                f"GUARD FAIL {ISO} {year}: non-positive demand hour "
                f"(min {demand.min():.1f} MW)."
            )

        out = pd.DataFrame(
            {
                "hour": np.arange(HOURS),
                "demand_mw": demand.round(3),
                "netgen_mw": netgen.round(3),
                "ng_cell_mw": ng_cell.round(3),
                "cems_gas_grid_mw": cems_grid.round(3),
                "ti_mw": ti.round(3),
            }
        )
        path = out_dir / f"caiso_supply_consistent_demand_{year}.csv"
        out.to_csv(path, index=False)
        provenance[str(year)] = {
            "annual_twh": round(total, 3),
            "eia930_demand_cell_twh": round(float(frame["Demand"].sum()) / 1e6, 3),
            "gas_cems_grid_twh": round(anchor, 3),
            "gas_cogen_grid_twh": round(float(e930["gas_cogen_grid"]), 3),
            "geo_biomass_foldin_twh": round(foldin_twh, 3),
            "flat_adders_mw": round(cogen_flat + foldin_flat, 1),
        }
        print(
            f"{ISO} {year}: demand {total:.2f} TWh "
            f"(930 Demand cell {provenance[str(year)]['eia930_demand_cell_twh']:.2f}; "
            f"cems {anchor:.2f} + cogen {e930['gas_cogen_grid']:.2f} "
            f"+ foldin {foldin_twh:.2f}) -> {path.name}"
        )

    (out_dir / "provenance.json").write_text(
        json.dumps(
            {
                "finding": "FINDING-caiso80-demand-basis-wedge-2026-07-13.md",
                "construction": (
                    "demand(t) = 930 NetGen(t) - NG_cell(t) + CEMS bench-gas "
                    "grid(t) + gas_cogen_grid/8760 + geo_biomass_foldin/8760 "
                    "- TI(t)"
                ),
                "years": provenance,
            },
            indent=1,
        )
        + "\n"
    )
    print("derive_caiso_supply_consistent_demand: done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
