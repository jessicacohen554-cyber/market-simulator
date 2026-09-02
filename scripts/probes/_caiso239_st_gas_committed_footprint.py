"""caiso-239 §Q — the LIVE footprint of ``offer_curve_by_group["ST_GAS"]["committed"]``
and the first-order ADVERSE C3a bound of moving it, on the caiso-231 keeper.

NO LP, NO SOLVE. Every input is committed: the ``2026-09-01-caiso-231-b1-ungrounded``
keeper's ``hourly/`` sidecars, the committed actual-LMP reference, and the
caiso-105/121/131 ``run_year(fleet_only=True)`` offer reconstruction (assembles
the fleet + availability + P0 objective, builds no matrix, calls no solver). The
marginal-rung attribution and the §H bounding form are imported UNCHANGED from
``_caiso230_abovefloor_decomposition.py`` and re-pointed at the NEW keeper, as
caiso-231's DO-NOT-REDO requires ("never re-derive the caiso-230 §A-§H
decomposition without re-running it on the NEW keeper").

WHAT THIS MEASURES.

  §Q1  WHICH LP tranches the class-wide ``ST_GAS:committed`` band actually
       prices, established by REBUILDING the fleet at three candidate values
       (0.81 armed / 1.00 Lever-A / 1.683 measured ``avg_committed_p50``) and
       diffing ``mc_base`` row-by-row. A tranche whose mc is byte-identical
       across all three is NOT priced by the band.
  §Q2  the responsive tranches' MATERIALITY: available capacity-hours and the
       keeper's own class dispatch.
  §Q3  the first-order bound on C3a of each candidate move, in the caiso-230
       §H form -- ``|dlambda| <= SUM omega * p_z * |dmult/mult|`` over the
       zone-hours where a responsive tranche is the marginal rung, annualised
       on the SCORER's own zone-hour load-weighted basis.
  §Q4  the measurement-quality read on ``avg_committed_p50`` itself: the
       per-class dispersion of the CAMPD artifact the value is drawn from.

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso239_st_gas_committed_footprint.py
"""

from __future__ import annotations

import contextlib
import csv
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

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso231_b1_ungrounded"
HR_SUMMARY = REPO / "data/raw/reference/caiso_campd_marginal_hr_summary.csv"
OUT = REPO / "results/calibration/_caiso239_st_gas_committed_footprint.json"
CACHE = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "45b1fef2-79f9-5ac1-8796-09fb43e66750/scratchpad/caiso239"
)

#: The armed value on the keeper and the two candidate replacements the
#: caiso-238 object-2 charter puts against each other.
ARMED = 0.81
CANDIDATES = {"leverA_1.00": 1.00, "measured_1.683": 1.683}

_spec = importlib.util.spec_from_file_location(
    "_caiso230_abovefloor_decomposition",
    REPO / "scripts/probes/_caiso230_abovefloor_decomposition.py",
)
M230 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M230)
M230.BUNDLE = BUNDLE
M230.CACHE = CACHE
M230.M202.BUNDLE = BUNDLE
M230.M202.CACHE = CACHE

RESULT: dict = {}


def rebuild(year: int, committed: float | None) -> dict:
    """Rebuild the keeper's offer surface with one band value substituted."""
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
    if committed is not None:
        kwargs["offer_curve_overrides"] = {"ST_GAS": {"committed": committed}}
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(year, meta["iso"], HOURS, float(meta["gas_prices"][str(year)]),
                      {}, fleet_only=True, **kwargs)
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    avail = np.asarray(fa.availability, dtype=float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    return {
        "uid": np.array([str(u) for u in fa.unit_ids]),
        "group": np.array([str(g) for g in np.asarray(fa.plant_group)]),
        "mc": mc,
        "pmax": np.asarray(fa.pmax, dtype=float),
        "avail": avail,
        "hr": np.asarray(fa.heat_rate, dtype=float),
    }


def section_q1_q2() -> dict:
    """Which tranches the band prices, and how material they are."""
    print("\n" + "=" * 78)
    print("§Q1/§Q2 — the band's LIVE footprint, per year")
    print("=" * 78)
    out: dict = {}
    for year in YEARS:
        base = rebuild(year, None)
        arms = {k: rebuild(year, v) for k, v in CANDIDATES.items()}
        sel = np.where(base["group"] == "ST_GAS")[0]
        rows = []
        for i in sel:
            deltas = {
                k: float(np.abs(a["mc"][i] - base["mc"][i]).max()) for k, a in arms.items()
            }
            responsive = max(deltas.values()) > 1e-9
            cap_mwh = float((base["pmax"][i] * base["avail"][i]).sum())
            rows.append(
                {
                    "uid": str(base["uid"][i]),
                    "pmax_mw": round(float(base["pmax"][i]), 2),
                    "tranche_hr": round(float(base["hr"][i]), 3),
                    "avail_mean": round(float(base["avail"][i].mean()), 4),
                    "available_capacity_gwh": round(cap_mwh / 1000.0, 1),
                    "mc_mean_armed": round(float(base["mc"][i].mean()), 2),
                    "mc_mean": {
                        k: round(float(a["mc"][i].mean()), 2) for k, a in arms.items()
                    },
                    "max_abs_mc_delta": {k: round(v, 4) for k, v in deltas.items()},
                    "responsive_to_band": responsive,
                }
            )
        resp = [r for r in rows if r["responsive_to_band"]]
        inert = [r for r in rows if not r["responsive_to_band"]]
        print(f"\n[{year}] ST_GAS LP tranches: {len(rows)}  "
              f"RESPONSIVE to the class band: {len(resp)}  INERT: {len(inert)}")
        print(f"    {'tranche':<38}{'pmax':>9}{'avail':>8}{'GWh-avail':>11}"
              f"{'mc(0.81)':>10}{'mc(1.00)':>10}{'mc(1.683)':>11}")
        for r in sorted(rows, key=lambda r: (not r["responsive_to_band"], r["uid"])):
            flag = "*" if r["responsive_to_band"] else " "
            print(f"  {flag} {r['uid']:<38}{r['pmax_mw']:>9.1f}{r['avail_mean']:>8.3f}"
                  f"{r['available_capacity_gwh']:>11.1f}{r['mc_mean_armed']:>10.2f}"
                  f"{r['mc_mean']['leverA_1.00']:>10.2f}"
                  f"{r['mc_mean']['measured_1.683']:>11.2f}")
        out[str(year)] = {
            "n_tranches": len(rows),
            "n_responsive": len(resp),
            "responsive_available_gwh": round(
                sum(r["available_capacity_gwh"] for r in resp), 1
            ),
            "inert_available_gwh": round(
                sum(r["available_capacity_gwh"] for r in inert), 1
            ),
            "tranches": rows,
        }
    return out


def section_q3() -> dict:
    """First-order C3a bound of each candidate, caiso-230 §H form."""
    print("\n" + "=" * 78)
    print("§Q3 — first-order ADVERSE C3a bound, caiso-230 §H form, on THIS keeper")
    print("=" * 78)
    out: dict = {}
    for year in YEARS:
        f = M230.FRAMES[year]
        hit = M230.HIT[(year, "annual")]
        wann = f["w"].sum()
        base = rebuild(year, None)
        # the responsive tranche ids, from §Q1
        arms = {k: rebuild(year, v) for k, v in CANDIDATES.items()}
        resp_uids = {
            str(base["uid"][i])
            for i in range(len(base["uid"]))
            if base["group"][i] == "ST_GAS"
            and max(float(np.abs(a["mc"][i] - base["mc"][i]).max()) for a in arms.values())
            > 1e-9
        }
        cells: dict[str, dict] = {}
        for (h, zi), (_lab, _loc, gi) in hit.items():
            if gi < 0:
                continue
            uid = str(f["uuid"][gi])
            if str(f["ugroup"][gi]) != "ST_GAS":
                continue
            band = uid.split("_")[-1]
            band = ("committed" if band.startswith("committed")
                    else "peak" if band.startswith("peak")
                    else "econ" if band.startswith("econ") else band)
            key = f"{uid}:{band}"
            w = float(f["dz"][h, zi] / wann)
            c = cells.setdefault(
                key,
                {"n": 0, "w_p": 0.0, "responsive": uid in resp_uids},
            )
            c["n"] += 1
            c["w_p"] += w * float(f["pz"][h, zi])
        bounds = {}
        for k, v in CANDIDATES.items():
            r = (v - ARMED) / ARMED
            bounds[k] = round(
                sum(c["w_p"] * r for c in cells.values() if c["responsive"]), 4
            )
        print(f"\n[{year}] ST_GAS marginal zone-hours by tranche "
              f"(scorer basis, {int(sum(c['n'] for c in cells.values()))} zone-hours)")
        for k, c in sorted(cells.items(), key=lambda kv: -kv[1]["n"]):
            print(f"    {'RESPONSIVE' if c['responsive'] else '   inert  '} "
                  f"{k:<44}{c['n']:>7} zone-h  w*p={c['w_p']:>8.4f}")
        for k, v in CANDIDATES.items():
            print(f"    first-order bound, {k:<16} move {100*(v-ARMED)/ARMED:+7.1f}%"
                  f"  ->  {bounds[k]:+.4f} $/MWh (annual load-weighted)")
        out[str(year)] = {
            "cells": {
                k: {"n_zone_hours": c["n"], "w_weighted_price": round(c["w_p"], 5),
                    "responsive": c["responsive"]}
                for k, c in cells.items()
            },
            "first_order_bound_usd_mwh": bounds,
            "model_lw_price": round(float((f["pz"] * f["dz"]).sum() / f["dz"].sum()), 4),
        }
    return out


def section_q4() -> dict:
    """The dispersion of the CAMPD artifact the measured candidate is drawn from."""
    print("\n" + "=" * 78)
    print("§Q4 — measurement quality of avg_committed_p50, per class")
    print("=" * 78)
    rows = list(csv.DictReader(HR_SUMMARY.open()))
    out = {}
    print(f"    {'class':<12}{'n_units':>8}{'p25':>8}{'p50':>8}{'p75':>8}{'p75/p25':>9}")
    for r in rows:
        p25, p50, p75 = (float(r[f"avg_committed_p{q}"]) for q in (25, 50, 75))
        ratio = p75 / p25 if p25 else float("nan")
        print(f"    {r['class']:<12}{int(r['n_units']):>8}{p25:>8.3f}{p50:>8.3f}"
              f"{p75:>8.3f}{ratio:>9.2f}")
        out[r["class"]] = {
            "n_units": int(r["n_units"]),
            "base_hr": float(r["base_hr"]),
            "avg_committed_p25": p25,
            "avg_committed_p50": p50,
            "avg_committed_p75": p75,
            "iqr_ratio_p75_over_p25": round(ratio, 3),
            "marg_committed_p50": float(r["marg_committed_p50"]),
        }
    return out


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for year in YEARS:
        M230.FRAMES[year] = M230.frame(year)
        M230.HIT[(year, "annual")] = M230._attribute(
            M230.FRAMES[year], np.arange(HOURS)
        )
    RESULT["Q1_Q2_footprint"] = section_q1_q2()
    RESULT["Q3_first_order_bound"] = section_q3()
    RESULT["Q4_measurement_quality"] = section_q4()
    RESULT["_provenance"] = {
        "bundle": str(BUNDLE.relative_to(REPO)),
        "keeper_run_id": "2026-09-01-caiso-231-b1-ungrounded",
        "armed_value": ARMED,
        "candidates": CANDIDATES,
        "years": list(YEARS),
        "solves": 0,
    }
    OUT.write_text(json.dumps(RESULT, indent=1, sort_keys=True))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
