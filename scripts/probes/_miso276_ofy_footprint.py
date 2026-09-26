#!/usr/bin/env python3
"""miso-276 phase 0 (zero LP): footprint of ``mustrun_online_frac_per_year`` on the keeper, 2019-2025.

The per-year window artifact (``thermal_tranches_online_frac_by_year_MISO.csv``)
covers only 2023-2025, the pooled artifact's own derive window, so on the
keeper's held-out years 2019-2022 the flag would fall back to the pooled value
for every plant. This probe points the loader at an EXTENDED artifact (the
committed rows plus 2019-2022 rows from the same deriver,
``scripts/data/derive_thermal_tranche_online_frac_by_year.py``) and rebuilds the
keeper fleet (``run_year(fleet_only=True)``) with the flag off (keeper) and on.

It reports per year the must-run floor energy (``min_gen`` summed over the
year, clipped by the engine to ``pmax x availability``) for ST_GAS and
CC_REGULAR, and the per-plant ST_GAS floor move.

Usage::

    uv run python scripts/probes/_miso276_ofy_footprint.py --artifact <extended csv> \
        --years 2019 2020 2021 2022 2023 --out results/calibration/_miso276_ofy_footprint.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import _miso271_cc_decomp as dec  # noqa: E402

dec.KEEPER = REPO / "results/calibration/miso275_span"
GROUPS = ("ST_GAS", "CC_REGULAR")


def floors(year: int, hh: float, on: bool) -> pd.DataFrame:
    """Per-unit annual floor MWh for the keeper fleet with the flag ``on``/off."""
    from scripts.run_calibration import run_year  # type: ignore

    flips = {"mustrun_online_frac_per_year": True} if on else {}
    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, flips))
    fa = st["fleet_arrays"]
    mg = fa.min_gen if fa.min_gen is not None else np.repeat(
        np.asarray(fa.pmin, float)[:, None], 8760, axis=1)
    return pd.DataFrame({
        "unit": list(fa.unit_ids),
        "group": list(fa.plant_group),
        "plant_code": np.asarray(fa.plant_code).astype(int),
        "floor_mwh": np.asarray(mg, float).sum(axis=1),
    })


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2019, 2020, 2021, 2022, 2023])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    import market_sim.data.fleet as fleet_pkg
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    art = pd.read_csv(args.artifact)
    by_year = {
        (int(r.plant_code), str(r.plant_group), int(r.year)): float(r.online_frac)
        for r in art.itertuples()
    }
    # Point the loader at the extended artifact (probe-local; no file on disk moves).
    fleet_pkg.thermal_tranche_online_frac_by_year = lambda iso: by_year  # type: ignore[assignment]
    ref = _load_reference()
    res: dict = {}
    for y in args.years:
        hh = _henry_hub_actual(ref, y)
        a, b = floors(y, hh, False), floors(y, hh, True)
        assert (a.unit.to_numpy() == b.unit.to_numpy()).all()
        rec: dict = {}
        for g in GROUPS:
            k = a.group == g
            rec[g] = {
                "floor_twh_off": round(float(a.floor_mwh[k].sum()) / 1e6, 4),
                "floor_twh_on": round(float(b.floor_mwh[k].sum()) / 1e6, 4),
            }
        k = a.group == "ST_GAS"
        d = (b.floor_mwh[k] - a.floor_mwh[k]).groupby(a.plant_code[k]).sum() / 1e6
        rec["ST_GAS_plant_delta_twh"] = {int(p): round(float(v), 4)
                                         for p, v in d[d.abs() > 1e-4].sort_values().items()}
        other = ~a.group.isin(GROUPS)
        rec["other_groups_floor_delta_twh"] = round(
            float((b.floor_mwh[other] - a.floor_mwh[other]).sum()) / 1e6, 4)
        res[str(y)] = rec
        print(y, json.dumps(rec), flush=True)
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
