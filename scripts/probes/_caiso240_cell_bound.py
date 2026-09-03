"""caiso-240 C-4 — the first-order ADVERSE C3a bound of moving a live
``_DEFAULT_HR_MULT_BY_GROUP`` cell to its measured counterpart, caiso-230 §H
form, on the CAISO keeper.

NO LP, NO SOLVE. The marginal-rung attribution and the §H bounding form are
imported UNCHANGED from ``_caiso230_abovefloor_decomposition.py`` and re-pointed
at the **caiso-239 keeper**, as caiso-230 §9 and caiso-231's DO-NOT-REDO
require. The responsive-row set per cell is re-measured by the caiso-240 census
harness (``_caiso240_default_hr_mult_census.rebuild`` /``attribute``), so the
bound is computed over exactly the rows the cell is MEASURED to price.

Pre-registered in ``PRECOMMIT-caiso240-default-hr-mult-census-2026-09-03.md``
§3.6, with §0.7(2)'s reading fixed in advance: a bound of zero is reported as
"zero to within the estimator's attribution tolerance", never as an exact zero.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso240_cell_bound.py \
        --moves ST_GAS:econ=1.255 ST_GAS:peak=1.166
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso239_b1_stgas_committed_measured"
OUT = REPO / "results/calibration/_caiso240_cell_bound.json"
CACHE = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "95982375-9434-5792-9a87-27d31c2e6e20/scratchpad/caiso240"
)


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M230 = _load("_caiso230_abovefloor_decomposition", "scripts/probes/_caiso230_abovefloor_decomposition.py")
M230.BUNDLE = BUNDLE
M230.CACHE = CACHE
M230.M202.BUNDLE = BUNDLE
M230.M202.CACHE = CACHE

CENSUS = _load("_caiso240_default_hr_mult_census", "scripts/probes/_caiso240_default_hr_mult_census.py")


def responsive_rows(year: int, cell: tuple[str, str]) -> tuple[dict, list[int]]:
    """Rebuild the keeper fleet and return (base arrays, rows the cell prices)."""
    f = CENSUS.FACTORS[cell]
    base = CENSUS.rebuild(BUNDLE, year, None)
    arm = CENSUS.rebuild(BUNDLE, year, {cell: f})
    hits = CENSUS.attribute(base, arm, {cell: f})
    return base, hits.get(f"{cell[0]}:{cell[1]}", [])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--moves", nargs="+", required=True,
        help="GROUP:BAND=target, e.g. ST_GAS:econ=1.255 (target is the measured "
             "counterpart; the armed literal is read from the live dict)",
    )
    ap.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    from market_sim.data.fleet import campd_bins as cb

    moves = []
    for m in a.moves:
        lhs, tgt = m.split("=")
        g, b = lhs.split(":")
        moves.append(((g, b), float(cb._DEFAULT_HR_MULT_BY_GROUP[g][b]), float(tgt)))

    CACHE.mkdir(parents=True, exist_ok=True)
    result: dict = {
        "_provenance": {
            "session": "caiso-240",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": "2026-09-02-caiso-239-b1-stgas",
            "form": "caiso-230 §H, re-pointed at the caiso-239 keeper",
            "tolerance_usd_mwh": M230.TOL,
            "solves": 0,
            "moves": [
                {"cell": f"{c[0]}:{c[1]}", "armed": armed, "target": tgt}
                for c, armed, tgt in moves
            ],
        }
    }
    per_year: dict = {}
    for year in a.years:
        M230.FRAMES[year] = M230.frame(year)
        M230.HIT[(year, "annual")] = M230._attribute(M230.FRAMES[year], np.arange(HOURS))
        f = M230.FRAMES[year]
        hit = M230.HIT[(year, "annual")]
        wann = f["w"].sum()
        rows: dict = {}
        for cell, armed, tgt in moves:
            base, idx = responsive_rows(year, cell)
            resp_uids = {str(base["uid"][i]) for i in idx}
            n_zh, wp = 0, 0.0
            for (h, zi), (_lab, _loc, gi) in hit.items():
                if gi < 0:
                    continue
                if str(f["uuid"][gi]) not in resp_uids:
                    continue
                n_zh += 1
                wp += float(f["dz"][h, zi] / wann) * float(f["pz"][h, zi])
            rel = abs(tgt - armed) / armed if armed else float("nan")
            bound = wp * rel
            key = f"{cell[0]}:{cell[1]}"
            rows[key] = {
                "armed": armed,
                "target": tgt,
                "relative_move": round(rel, 6),
                "n_responsive_tranches": len(idx),
                "n_marginal_zone_hours": n_zh,
                "w_weighted_price": round(wp, 6),
                "first_order_bound_usd_mwh": round(bound, 6),
                "direction": "ADVERSE (offer up)" if tgt > armed else "favourable (offer down)",
            }
            print(f"[{year}] {key:<16} armed {armed:.4f} -> {tgt:.4f} "
                  f"({100*rel:+.1f}%)  responsive tranches {len(idx):>4}  "
                  f"marginal zone-hours {n_zh:>6}  bound {bound:+.4f} $/MWh")
        per_year[str(year)] = {
            "model_lw_price": round(float((f["pz"] * f["dz"]).sum() / f["dz"].sum()), 4),
            "cells": rows,
        }
    result["per_year"] = per_year
    Path(a.out).write_text(json.dumps(result, indent=1, sort_keys=True))
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
