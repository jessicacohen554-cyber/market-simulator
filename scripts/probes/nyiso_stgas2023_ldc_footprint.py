"""NYISO-STGAS-2023 G-FOOTPRINT census (zero LP): what nyiso_ldc_generator_delivered_gas moves.

Fleet-only rebuild of the keeper recipe (``replay_keeper.run_year_kwargs`` ->
``run_calibration.run_year(fleet_only=True)``) per year, flag off and on. Reports every
generator row whose assembled fuel price or ``mc_base`` differs (plant, class, MW, mean
$/MMBtu and $/MWh deltas) and asserts nothing else in the fleet arrays moves.
Writes ``results/calibration/_nyiso_stgas2023_ldc_footprint.json``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLES = {2021: "results/calibration/rnyiso_2021"}
DEFAULT_BUNDLE = "results/calibration/rnyiso_span"
FIELD = "nyiso_ldc_generator_delivered_gas"


def _build(year: int, arm: bool):
    """Fleet-only rebuild at the keeper recipe, flag set to ``arm``."""
    from scripts.replay_keeper import run_year_kwargs
    from scripts.run_calibration import run_year
    from scripts import run_calibration_full as rcf

    meta = json.loads(
        (REPO / BUNDLES.get(year, DEFAULT_BUNDLE) / "meta.json").read_text()
    )
    kw = run_year_kwargs(meta)
    prb = dict(kw.get("prb_overrides") or {})
    prb[FIELD] = arm
    kw["prb_overrides"] = prb
    gp = rcf._henry_hub_actual(rcf._load_reference(), year)
    return run_year(year, meta["iso"], 8760, gp, {}, fleet_only=True, **kw)


def census(year: int) -> dict:
    """Diff the off/on builds for one year."""
    off, on = _build(year, False), _build(year, True)
    fa0, fa1 = off["fleet_arrays"], on["fleet_arrays"]
    for attr in (
        "pmax",
        "pmin",
        "heat_rate",
        "availability",
        "vom",
        "zone_idx",
        "plant_code",
    ):
        a, b = np.asarray(getattr(fa0, attr)), np.asarray(getattr(fa1, attr))
        assert a.shape == b.shape and np.array_equal(a, b), (
            f"{year}: fleet {attr} moved"
        )
    f0, f1 = np.asarray(off["fuel_prices"]), np.asarray(on["fuel_prices"])
    m0, m1 = np.asarray(off["mc_base"]), np.asarray(on["mc_base"])
    changed = np.nonzero(
        (np.abs(f1 - f0) > 1e-12).any(axis=1) | (np.abs(m1 - m0) > 1e-12).any(axis=1)
    )[0]
    pg = np.asarray(fa0.plant_group).astype(str)
    rows = []
    by_class = defaultdict(float)
    for i in changed:
        rows.append(
            {
                "unit_id": fa0.unit_ids[i],
                "plant_code": int(fa0.plant_code[i]),
                "class": pg[i],
                "pmax_mw": round(float(fa0.pmax[i]), 1),
                "d_fuel_usd_mmbtu": round(float((f1[i] - f0[i]).mean()), 4),
                "d_mc_usd_mwh": round(float((m1[i] - m0[i]).mean()), 3),
            }
        )
        by_class[pg[i]] += float(fa0.pmax[i])
    return {
        "n_rows_changed": int(changed.size),
        "plants": sorted({r["plant_code"] for r in rows}),
        "mw_by_class": {k: round(v, 1) for k, v in sorted(by_class.items())},
        "rows": rows,
    }


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025]
    )
    ap.add_argument(
        "--out",
        default=str(REPO / "results/calibration/_nyiso_stgas2023_ldc_footprint.json"),
    )
    a = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)
    p = Path(a.out)
    res = json.loads(p.read_text()) if p.exists() else {}
    for y in a.years:
        res[str(y)] = census(y)
        p.write_text(json.dumps(res, indent=1))
        r = res[str(y)]
        print(
            y,
            "rows",
            r["n_rows_changed"],
            "plants",
            r["plants"],
            "MW",
            r["mw_by_class"],
            flush=True,
        )


if __name__ == "__main__":
    main()
