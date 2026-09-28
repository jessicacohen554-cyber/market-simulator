#!/usr/bin/env python3
"""miso-279 phase 0 (ZERO LP): floor footprint of ``campd_st_gas_span_coverage``.

Fleet-only rebuilds (``run_year(fleet_only=True)``) of the designated MISO
keeper's recipe (``results/calibration/miso278_span``) per year, twice: ``K``
the keeper as registered, ``A`` the same recipe with the single delta
``campd_st_gas_span_coverage=True`` (reads the four ``-fuelsplit-stcov-``
companions). Records ST_GAS pmax, floor TWh by plant, and the floor TWh of
every group, so any floor that appears or disappears is visible.

Usage::

    uv run python scripts/probes/_miso279_stcov_footprint.py --years 2019 --out-dir X
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402

KEEPER = REPO / "results/calibration/miso278_span"
DELTA = {"campd_st_gas_span_coverage": True}


def unit_floors(year: int, hh: float, flips: dict) -> pd.DataFrame:
    """One row per LP unit: plant, class, pmax, floor TWh."""
    from scripts.run_calibration import run_year

    st = run_year(
        year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, flips)
    )
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    mg = (
        np.asarray(fa.min_gen, dtype=float)
        if fa.min_gen is not None
        else np.zeros((len(pmax), 8760))
    )
    return pd.DataFrame(
        {
            "unit_id": list(fa.unit_ids),
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "group": list(fa.plant_group),
            "pmax": pmax,
            "floor_twh": np.clip(mg, 0.0, None).sum(axis=1) / 1e6,
        }
    )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2019])
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ref = _load_reference()
    summary: dict = {}
    for y in args.years:
        hh = _henry_hub_actual(ref, y)
        k = unit_floors(y, hh, {})
        a = unit_floors(y, hh, DELTA)
        k.to_parquet(out / f"{y}_K.parquet", index=False)
        a.to_parquet(out / f"{y}_A.parquet", index=False)
        by_plant = (
            a.groupby(["plant_code", "group"]).floor_twh.sum()
            - k.groupby(["plant_code", "group"]).floor_twh.sum()
        )
        moved = by_plant[by_plant.abs() > 1e-6]
        summary[str(y)] = {
            "n_units": [len(k), len(a)],
            "st_gas_pmax_mw": [
                round(float(d[d.group == "ST_GAS"].pmax.sum()), 1) for d in (k, a)
            ],
            "st_gas_floor_twh": [
                round(float(d[d.group == "ST_GAS"].floor_twh.sum()), 4) for d in (k, a)
            ],
            "floor_twh_by_group_delta": {
                str(g): round(
                    float(
                        a[a.group == g].floor_twh.sum()
                        - k[k.group == g].floor_twh.sum()
                    ),
                    4,
                )
                for g in sorted(set(k.group) | set(a.group))
                if abs(
                    a[a.group == g].floor_twh.sum() - k[k.group == g].floor_twh.sum()
                )
                > 1e-6
            },
            "moved_plant_group_twh": {
                f"{p}:{g}": round(float(v), 4) for (p, g), v in moved.items()
            },
        }
        print(json.dumps({y: summary[str(y)]}), flush=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
