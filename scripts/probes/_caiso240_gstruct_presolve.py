"""caiso-240 G-STRUCT — the armed mechanism's fleet footprint, verified BEFORE the solve.

NO LP, NO SOLVE. Rebuilds the caiso-239 keeper's offer surface twice with
``run_year(fleet_only=True)`` — once as recorded, once with
``caiso_st_gas_peak_measured`` armed — and diffs every fleet row, so the gate's
claim ("exactly the three OTC steamers' ``_peak`` tranches move, at the exact
ratio 1.166 / 1.10, and nothing else") is measured rather than asserted.

Pre-registered in ``PRECOMMIT-caiso240-ADDENDUM-arm-2026-09-03.md`` §A7.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso240_gstruct_presolve.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import inspect
import io
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/caiso239_b1_stgas_committed_measured"
YEARS = (2023, 2024, 2025)
HOURS = 8760
OUT = REPO / "results/calibration/_caiso240_gstruct_presolve.json"

_spec = importlib.util.spec_from_file_location(
    "_caiso240_default_hr_mult_census",
    REPO / "scripts/probes/_caiso240_default_hr_mult_census.py",
)
CENSUS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CENSUS)


def rebuild(year: int, armed: bool) -> dict:
    """Rebuild the keeper fleet with the mechanism off / on."""
    from run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {k: v for k, v in meta.items() if k in params and k not in skip}
    if armed:
        kwargs["caiso_st_gas_peak_measured"] = True
    CENSUS._clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(
            year,
            meta["iso"],
            HOURS,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kwargs,
        )
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    return {
        "uid": np.array([str(u) for u in fa.unit_ids]),
        "hr": np.asarray(fa.heat_rate, dtype=float),
        "mc": mc,
        "pmax": np.asarray(fa.pmax, dtype=float),
        "plant_code": np.asarray(fa.plant_code, dtype=int),
    }


def main() -> None:
    result: dict = {
        "_provenance": {
            "session": "caiso-240",
            "gate": "G-STRUCT, pre-solve leg",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": "2026-09-02-caiso-239-b1-stgas",
            "flag": "caiso_st_gas_peak_measured",
            "expected_ratio": 1.166 / 1.10,
            "solves": 0,
        }
    }
    per_year: dict = {}
    for year in YEARS:
        off = rebuild(year, False)
        on = rebuild(year, True)
        assert np.array_equal(off["uid"], on["uid"]), "row set moved"
        ratio = np.divide(
            on["hr"], off["hr"], out=np.ones_like(off["hr"]), where=off["hr"] > 0
        )
        moved = np.flatnonzero(np.abs(ratio - 1.0) > 1e-12)
        rows = [
            {
                "uid": str(off["uid"][i]),
                "plant_code": int(off["plant_code"][i]),
                "pmax_mw": round(float(off["pmax"][i]), 2),
                "hr_off": round(float(off["hr"][i]), 6),
                "hr_on": round(float(on["hr"][i]), 6),
                "ratio": float(ratio[i]),
                "mc_mean_off": round(float(off["mc"][i].mean()), 4),
                "mc_mean_on": round(float(on["mc"][i].mean()), 4),
            }
            for i in moved
        ]
        exact = all(abs(r["ratio"] - 1.166 / 1.10) < 1e-12 for r in rows)
        bands = sorted({CENSUS.band_of(r["uid"]) for r in rows})
        plants = sorted({r["plant_code"] for r in rows})
        print(f"\n[{year}] fleet rows {off['uid'].size}  MOVED {len(rows)}")
        for r in rows:
            print(
                f"    {r['uid']:<34} p{r['plant_code']:<6} "
                f"{r['pmax_mw']:>8.1f} MW  hr {r['hr_off']:.4f} -> {r['hr_on']:.4f}"
                f"  ratio {r['ratio']:.12f}  mc {r['mc_mean_off']:.3f} -> "
                f"{r['mc_mean_on']:.3f}"
            )
        print(f"    bands {bands}  plants {plants}  ratio-exact {exact}")
        per_year[str(year)] = {
            "n_fleet_rows": int(off["uid"].size),
            "n_moved": len(rows),
            "bands_moved": bands,
            "plants_moved": plants,
            "ratio_exact": bool(exact),
            "rows": rows,
        }
    result["per_year"] = per_year
    result["G_STRUCT_presolve"] = {
        "PASS": all(
            v["n_moved"] == 3
            and v["bands_moved"] == ["peak"]
            and v["plants_moved"] == [315, 335, 350]
            and v["ratio_exact"]
            for v in per_year.values()
        )
    }
    OUT.write_text(json.dumps(result, indent=1, sort_keys=True))
    print(f"\nG-STRUCT pre-solve: {result['G_STRUCT_presolve']}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
