"""caiso-241 G-STRUCT — the armed mechanism's fleet footprint, verified BEFORE the solve.

NO LP, NO SOLVE. Rebuilds the caiso-240 keeper's offer surface twice with
``run_year(fleet_only=True)`` — once as recorded, once with
``caiso_ct_peaker_committed_measured`` armed — and diffs every fleet row, so the
gate's claim is MEASURED rather than asserted:

  * exactly the CAISO ``CT_PEAKER`` ``_committed`` tranches move,
  * at the exact heat-rate ratio ``0.991 / 1.350 = 0.734074074074``,
  * with ``offer_markup_hr`` driven to exactly ``0.0`` on those rows
    (``gas_offer_net_revenue_margin``'s ``max(0, mult - phys)`` clipping, which
    is the rule-19 [R-ONE-MECH] half of the repair: the offer-curve start-cost
    limb retires and P1's identified amortized startup markup is left as the
    sole commitment mechanism on the tranche),
  * and nothing else moves, in any band, class or ISO.

This is ALSO the registered substitute for the dispatch-level control this arm
cannot have: it is expected live in all three years, so the caiso-240
dispatch-identity form of G-CTRL has no inert year to bind on and the caiso-231
"no control arms" directive leaves no other check (precommit §0.6(2)). It proves
the FOOTPRINT; it cannot prove the absence of HEAD drift.

Pre-registered in ``PRECOMMIT-caiso241-ct-peaker-committed-2026-09-03.md`` §5.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso241_gstruct_presolve.py
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

BUNDLE = REPO / "results/calibration/caiso240_b1_stgas_peak_measured"
KEEPER_RUN_ID = "2026-09-03-caiso-240-b1-stgas"
FLAG = "caiso_ct_peaker_committed_measured"
FITTED = 1.350
MEASURED = 0.991
EXPECTED_RATIO = MEASURED / FITTED
YEARS = (2023, 2024, 2025)
HOURS = 8760
OUT = REPO / "results/calibration/_caiso241_gstruct_presolve.json"

_spec = importlib.util.spec_from_file_location(
    "_caiso240_default_hr_mult_census",
    REPO / "scripts/probes/_caiso240_default_hr_mult_census.py",
)
CENSUS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CENSUS)


def rebuild(year: int, armed: bool) -> dict:
    """Rebuild the keeper fleet with the mechanism off / on (no LP)."""
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
        kwargs[FLAG] = True
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
    gens = st.get("fleet") or []
    markup = np.array(
        [float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in gens], dtype=float
    )
    group = np.array([str(getattr(g, "plant_group", "")) for g in gens])
    if markup.size != np.asarray(fa.heat_rate).size:  # defensive: grain mismatch
        markup = np.full(np.asarray(fa.heat_rate).size, np.nan)
        group = np.full(np.asarray(fa.heat_rate).size, "")
    return {
        "uid": np.array([str(u) for u in fa.unit_ids]),
        "hr": np.asarray(fa.heat_rate, dtype=float),
        "mc": mc,
        "pmax": np.asarray(fa.pmax, dtype=float),
        "plant_code": np.asarray(fa.plant_code, dtype=int),
        "markup": markup,
        "group": group,
    }


def main() -> None:
    result: dict = {
        "_provenance": {
            "session": "caiso-241",
            "gate": "G-STRUCT, pre-solve leg (and the registered substitute for "
            "a dispatch-level control this arm cannot have — precommit §0.6(2))",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": KEEPER_RUN_ID,
            "flag": FLAG,
            "fitted": FITTED,
            "measured": MEASURED,
            "measured_source": "data/raw/reference/caiso_campd_marginal_hr_summary.csv"
            " → CT_PEAKER.avg_committed_p50 (n=75, IQR [0.969, 1.085])",
            "expected_ratio": EXPECTED_RATIO,
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
        moved_hr = set(np.flatnonzero(np.abs(ratio - 1.0) > 1e-12).tolist())
        moved_mk = set(
            np.flatnonzero(
                np.abs(np.nan_to_num(on["markup"]) - np.nan_to_num(off["markup"]))
                > 1e-12
            ).tolist()
        )
        moved = sorted(moved_hr | moved_mk)
        rows = [
            {
                "uid": str(off["uid"][i]),
                "group": str(off["group"][i]),
                "band": CENSUS.band_of(str(off["uid"][i])),
                "plant_code": int(off["plant_code"][i]),
                "pmax_mw": round(float(off["pmax"][i]), 2),
                "hr_off": round(float(off["hr"][i]), 6),
                "hr_on": round(float(on["hr"][i]), 6),
                "ratio": float(ratio[i]),
                "markup_hr_off": round(float(off["markup"][i]), 6),
                "markup_hr_on": round(float(on["markup"][i]), 6),
                "mc_mean_off": round(float(off["mc"][i].mean()), 4),
                "mc_mean_on": round(float(on["mc"][i].mean()), 4),
            }
            for i in moved
        ]
        ratio_exact = all(abs(r["ratio"] - EXPECTED_RATIO) < 1e-12 for r in rows)
        markup_zeroed = all(abs(r["markup_hr_on"]) < 1e-12 for r in rows)
        bands = sorted({r["band"] for r in rows})
        groups = sorted({r["group"] for r in rows})
        plants = sorted({r["plant_code"] for r in rows})
        cap = round(sum(r["pmax_mw"] for r in rows), 2)
        # Materiality context: the class's total grid capacity and the moved share.
        ct_mask = off["group"] == "CT_PEAKER"
        ct_cap = float(off["pmax"][ct_mask].sum()) if ct_mask.any() else float("nan")
        print(f"\n[{year}] fleet rows {off['uid'].size}  MOVED {len(rows)}")
        for r in rows[:6]:
            print(
                f"    {r['uid']:<36} {r['group']:<10} {r['pmax_mw']:>8.1f} MW "
                f" hr {r['hr_off']:.4f}->{r['hr_on']:.4f}  ratio {r['ratio']:.12f}"
                f"  mkup {r['markup_hr_off']:.4f}->{r['markup_hr_on']:.4f}"
                f"  mc {r['mc_mean_off']:.2f}->{r['mc_mean_on']:.2f}"
            )
        if len(rows) > 6:
            print(f"    ... {len(rows) - 6} more")
        print(
            f"    groups {groups}  bands {bands}  n_plants {len(plants)}"
            f"  moved_cap {cap:.1f} MW of CT_PEAKER {ct_cap:.1f} MW"
            f"  ({100.0 * cap / ct_cap:.1f} %)"
            f"  ratio-exact {ratio_exact}  markup-zeroed {markup_zeroed}"
        )
        per_year[str(year)] = {
            "n_fleet_rows": int(off["uid"].size),
            "n_moved": len(rows),
            "groups_moved": groups,
            "bands_moved": bands,
            "n_plants_moved": len(plants),
            "plants_moved": plants,
            "moved_capacity_mw": cap,
            "ct_peaker_capacity_mw": round(ct_cap, 2),
            "moved_share_of_class_pct": round(100.0 * cap / ct_cap, 4),
            "ratio_exact": bool(ratio_exact),
            "markup_zeroed": bool(markup_zeroed),
            "rows": rows,
        }
    result["per_year"] = per_year
    result["G_STRUCT_presolve"] = {
        "PASS": all(
            v["n_moved"] > 0
            and v["groups_moved"] == ["CT_PEAKER"]
            and v["bands_moved"] == ["mc"]  # census band_of(): committed → "mc"
            and v["ratio_exact"]
            and v["markup_zeroed"]
            for v in per_year.values()
        ),
        "falsifier": "any row moves at another ratio, in another band/group/ISO, "
        "or keeps a non-zero offer_markup_hr after arming",
    }
    OUT.write_text(json.dumps(result, indent=1, sort_keys=True))
    print(f"\nG-STRUCT pre-solve: {result['G_STRUCT_presolve']['PASS']}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
