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
basis, ``scripts/data/regen_caiso_bench_cems.py``). The series regenerates for any
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
    python scripts/data/derive_caiso_supply_consistent_demand.py --years 2019 2020 2021

``--years`` is REQUIRED (R-CAISO-4, 2026-09-26): the script used to rewrite
every listed year on each run, which at HEAD would silently move the committed
2022 artifact (219.538 -> 219.275 TWh, code/data drift since it was written).
Only the named years are derived and written; ``provenance.json`` is MERGED,
so the other years' entries survive untouched.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (_REPO / "src", _REPO, _REPO / "scripts"):
    sys.path.insert(0, str(_p))

from market_sim.config.paths import (  # noqa: E402
    CAISO_SUPPLY_CONSISTENT_DEMAND_DIR,
)
from market_sim.data.eia_loader import _eia_hourly_frame_filled  # noqa: E402

import scripts.legitimacy_diagnostics as L  # noqa: E402

ISO = "CAISO"
# 2022 ADDED 2026-09-07 (caiso-262, the rule-22 validation touchpoint): the
# keeper runs ``caiso_supply_consistent_demand=True`` and the loader RAISES
# rather than falling back, so without the 2022 artifact the touchpoint cannot
# solve at all. Same producer, same construction, same sources — only the year
# is new. NOTE this script takes NO arguments and REWRITES every year listed
# here on any invocation; the 2023-2025 outputs are asserted sha256-identical
# after the run (PRECOMMIT-caiso262 A-7).
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
HOURS = 8760
# FINDING §6 pre-registered annual levels (TWh) ±1.5 TWh tolerance: a derive
# outside these windows means an input drifted — refuse to write.
#
# 2022's window is NOT a FINDING §6 level — none exists for a year never
# derived, and a window fitted to this derive's own output would guard nothing.
# It is **G-DEMAND-2022** (PRECOMMIT-caiso262 §5.2), a WEDGE band fixed from
# the COMMITTED 2023-2025 artifacts BEFORE the 2022 derive ran, where
#     wedge(y) = [930 CISO NetGen - TI](y) - derived demand(y)
# measured +5.416 / +10.780 / +17.675 TWh for 2023/24/25. The admissible 2022
# wedge is [-1.5, max(wedge) + 1.5] = [-1.500, +19.175] TWh, and the 2022 930
# identity total is 218.809 TWh, giving the window below. The band is
# one-sided-generous by design: it is computable ex ante, is not fitted to
# 2022, and catches the failure it must (a corrupt NG cell, a missing CEMS
# block, a clock slip), while not pretending to pin a level nobody has
# measured. DIRECTION REPORTED, NOT GATED: the NG-cell corruption onset is
# ~2024-05 (caiso-80 FINDING §6) and the wedge grows monotonically with it, so
# 2022 is EXPECTED to sit near or below 2023's +5.4 rather than near 2025's
# +17.7; if it does not, that is a finding to report, never a reason to move
# the band.
_ANNUAL_GUARD = {
    2023: (206.2, 209.2),
    2024: (210.9, 213.9),
    2025: (203.8, 206.8),
}
# G-DEMAND ON THE MEASURED 930 BASIS (R-CAISO-4, owner ruling 2026-09-26,
# option (a) of docs/handoffs/i-caiso/INTAKE-i-caiso-2019-2021-2026-09-24.md
# section 1). Replaces G-DEMAND-2022 for every year with no FINDING section-6
# level (2019-2022). The old band measured
#     wedge = [930 NetGen - TI] - derived = NG_cell - CEMS - cogen - foldin,
# i.e. it assumed the CISO `NG: NG` cell FOLDS geothermal + biomass. CAISO's own
# Outlook fuel mix refutes that: the 930 NG cell equals Outlook natural_gas
# alone (65.15 vs 64.95 / 73.69 vs 73.82 / 79.23 vs 79.20 TWh, 2019/20/21), and
# geo/bio appear in no 930 cell, so the fold-in is a term 930 NetGen genuinely
# LACKS and must not sit inside the drift check. The measured-basis wedge is the
# gas-vs-gas residual
#     W_gas = NG_cell - CEMS bench-gas grid - gas_cogen_grid,
# and the band is the IDENTICAL G-DEMAND construction applied to it, fixed from
# the COMMITTED 2023-2025 artifacts only (wedge + foldin from provenance.json:
# 5.416+13.786 / 10.780+13.589 / 17.675+10.499 = 19.202 / 24.369 / 28.174 TWh):
# [-1.5, max + 1.5] = [-1.500, +29.674]. No new parameter; no value chosen
# after seeing a 2019-2021 result (the 2019-21 wedges were already on record
# in the intake doc, so this is stated rather than hidden). Measured W_gas:
# 6.21 / 9.04 / 10.66 / 12.93 / 19.22 / 24.36 / 28.17 TWh (2019..2025), its
# hourly correlation with 930 solar rising 0.04 -> 0.81: the growing
# solar-shaped NG-cell artifact the derive removes by construction.
_WGAS_GUARD = (-1.500, 29.674)
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, required=True, choices=YEARS)
    args = ap.parse_args(argv)

    # Package import, not a ``spec_from_file_location`` file-load (refactor
    # plan §6-E): the old form executed the renderer a second time under the
    # synthetic name "rch" — a private copy that could drift from the
    # canonical ``scripts.render_calibration_html``. Kept lazy: the renderer
    # imports run_calibration_full at module level.
    from scripts import render_calibration_html as rch

    gas_groups = set(rch._GAS_GROUPS)
    out_dir = CAISO_SUPPLY_CONSISTENT_DEMAND_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    prov_path = out_dir / "provenance.json"
    prior = json.loads(prov_path.read_text()) if prov_path.exists() else {}
    provenance: dict[str, dict] = dict(prior.get("years", {}))

    for year in args.years:
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
                "scripts/data/regen_caiso_bench_cems.py first."
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
        wgas = float(ng_cell.sum() / 1e6 - anchor - float(e930["gas_cogen_grid"]))
        if year in _ANNUAL_GUARD:
            lo, hi = _ANNUAL_GUARD[year]
            if not (lo <= total <= hi):
                raise SystemExit(
                    f"GUARD FAIL {ISO} {year}: derived demand {total:.2f} TWh "
                    f"outside pre-registered [{lo}, {hi}] (FINDING §6)."
                )
        else:
            lo, hi = _WGAS_GUARD
            if not (lo <= wgas <= hi):
                raise SystemExit(
                    f"GUARD FAIL {ISO} {year}: measured-basis gas wedge "
                    f"{wgas:.2f} TWh outside [{lo}, {hi}] (G-DEMAND, 930 basis)."
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
            "gas_wedge_930_basis_twh": round(wgas, 3),
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
                "years": {k: provenance[k] for k in sorted(provenance)},
            },
            indent=1,
        )
        + "\n"
    )
    print("derive_caiso_supply_consistent_demand: done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
