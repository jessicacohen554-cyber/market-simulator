"""miso-149 G-1/G-2 CLEAN SCOPE — the trap-2/trap-3 completion of the contradiction census. **NO LP.**

PREREG ``results/calibration/PREREG-miso149-overlay-contradiction-2026-08-10.md``
(``318c0542``) §5 traps 2 and 3 pre-committed the counter-measurements this probe
executes.  ``_miso149_overlay.py`` ran the census exactly as pre-registered and
returned ``Kcc = 3,674 MW`` (2025), which fires branch B-1 -- but the per-plant
detail shows the quantity is dominated by two things the census was never meant to
measure, both already adjudicated:

* **the industrial-CHP / BTM boundary** (miso-148 §3, DO-NOT-REDO: it is NOT
  missing capacity).  The model deliberately carries only a cogen's GRID-delivered
  share while CAMPD meters the unit's TOTAL gross, so ``A > C`` at Plaquemine
  Cogen / Taft / R S Cogen / Pine Bluff / Carville / Midland Cogeneration is the
  boundary working as designed, not a defect;
* **family-crosswalk and plant-code splits within a MATCHED plant** -- Ninemile
  Point (model 649.5 CC + 1,465.4 ST_GAS vs CAMPD's own CC/ST_GAS split) and
  Perryville both carry MORE total model capacity than their CAMPD total p99 while
  still showing a CC-family contradiction; Riverside Energy Center's capacity is
  split across plant codes 55641 and 64020 (eGRID's own PLHTIAN co-location
  warning names the pair) while CAMPD books it all under 55641.

Both are removed by ONE construction change: compare at **PLANT TOTAL across all
four fossil families**, and restrict to plants whose model total capacity is not
itself below the plant's own demonstrated total rating.  What survives is a clean
availability statement -- the model's TOTAL capability at a plant sits below that
plant's TOTAL measured output -- with no rating, population, split or boundary
question inside it.

Writes ``results/calibration/_miso149_clean_scope.json``.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for _i, _p in enumerate((REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes")):
    sys.path.insert(_i, str(_p))
os.environ.setdefault("MISO149_CACHE", str(Path("/tmp") / "_miso149_cache"))

import _miso143_stack as stack  # noqa: E402
from _miso143_stack import hygiene, month_of_hour  # noqa: E402
from _miso147_strata import (  # noqa: E402
    FAMILY_TO_KLASSES,
    HOURS,
    YEARS,
    campd_units,
    fam_of_klass,
    parasitic_map,
    strata,
)
from _miso149_overlay import (  # noqa: E402
    KEEPER149,
    OA_DROPPED_PLANTS,
    fleet149,
    layer_matrix,
    overlay_layers,
)

OUT = REPO / "results" / "calibration" / "_miso149_clean_scope.json"
CHP_KLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")
FOSSIL_FAMS = ("CC", "CT", "ST_GAS", "ST_COAL")


def run() -> dict:
    hygiene()
    stack.KEEPER = KEEPER149
    fmap = fam_of_klass()
    res: dict = {
        "session": "miso-149",
        "prereg": "results/calibration/PREREG-miso149-overlay-contradiction-2026-08-10.md",
        "prereg_commit": "318c0542",
        "gate": "G-1/G-2 CLEAN SCOPE (PREREG §5 traps 2+3 counter-measurements)",
        "construction": (
            "PLANT TOTAL over all four fossil families on BOTH sides, so a "
            "family-crosswalk split inside a matched plant cancels; CHP-bearing "
            "plants reported separately (the adjudicated BTM boundary); and the "
            "rating question separated from the availability question by "
            "conditioning on model total pmax >= plant CAMPD total p99."
        ),
        "years": {},
    }
    for year in YEARS:
        pack = fleet149(year)
        lay = layer_matrix(pack, overlay_layers(year))
        avail = pack["availability"].astype(np.float64)
        prod = (lay["ufac"] * lay["sfac"] * lay["mgfac"]).astype(np.float64)
        pmax = pack["pmax"]
        st = strata(year)
        mon = month_of_hour(np.arange(HOURS))

        units, _meta = campd_units(year)
        fac = parasitic_map()
        fossil = units[units["family"].isin(FOSSIL_FAMS)]

        # --- CAMPD plant TOTAL net series -----------------------------------
        obs: dict[int, np.ndarray] = {}
        for pid, g in fossil.groupby("plant_id", sort=False):
            a = np.zeros(HOURS)
            np.add.at(a, g["hoy"].to_numpy(int), g["gross"].to_numpy(float))
            obs[int(pid)] = a * float(fac.get(int(pid), 1.0))

        # --- model plant TOTAL capability (all fossil klasses) ---------------
        is_fossil = np.array([fmap.get(str(k)) in FOSSIL_FAMS for k in pack["klass"]])
        plants = np.unique(pack["plant"][is_fossil])
        rows: dict[int, dict] = {}
        for pid in plants:
            sel = is_fossil & (pack["plant"] == pid)
            rows[int(pid)] = {
                "sel": sel,
                "pmax": float(pmax[sel].sum()),
                "has_chp": bool(any(str(k) in CHP_KLASSES for k in pack["klass"][sel])),
            }

        both = sorted(set(rows) & set(obs))
        variants = {
            "keeper": lambda s: pmax[s][:, None] * avail[s],
            "no_ufac": lambda s: pmax[s][:, None] * (avail[s] / np.maximum(lay["ufac"][s], 1e-12)),
            "no_mgfac": lambda s: pmax[s][:, None] * (avail[s] / np.maximum(lay["mgfac"][s], 1e-12)),
            "no_overlay": lambda s: pmax[s][:, None] * (avail[s] / np.maximum(prod[s], 1e-12)),
            "at_rating": None,  # capability = model pmax, no availability at all
        }
        buckets = {
            "ALL": lambda r, pid: True,
            "NO_CHP": lambda r, pid: not r["has_chp"],
            "ADEQUATELY_RATED": lambda r, pid: r["pmax"] >= r["p99"],
            "NO_CHP_AND_ADEQUATELY_RATED": lambda r, pid: (not r["has_chp"]) and r["pmax"] >= r["p99"],
            "NO_CHP_ADEQ_EXCL_OA": lambda r, pid: (
                (not r["has_chp"]) and r["pmax"] >= r["p99"] and pid not in OA_DROPPED_PLANTS
            ),
        }
        for pid in both:
            rows[pid]["p99"] = float(np.quantile(obs[pid], 0.99))

        yr: dict = {"n_plants_both": len(both), "variants": {}, "buckets": {}}
        series_by_variant: dict[str, dict[str, np.ndarray]] = {}
        for vname, make in variants.items():
            acc = {b: np.zeros(HOURS) for b in buckets}
            for pid in both:
                r = rows[pid]
                s = r["sel"]
                cap = (
                    np.repeat(r["pmax"], HOURS)
                    if vname == "at_rating"
                    else make(s).sum(axis=0)
                )
                d = np.maximum(0.0, obs[pid] - cap)
                if not d.any():
                    continue
                for b, keep in buckets.items():
                    if keep(r, pid):
                        acc[b] += d
            series_by_variant[vname] = acc
            yr["variants"][vname] = {
                b: round(float(v.mean()), 1) for b, v in acc.items()
            }

        base = series_by_variant["keeper"]
        for b in buckets:
            n = sum(1 for pid in both if buckets[b](rows[pid], pid))
            mw = sum(rows[pid]["pmax"] for pid in both if buckets[b](rows[pid], pid))
            yr["buckets"][b] = {
                "n_plants": n,
                "model_pmax_mw": round(mw, 1),
                "contradiction_mean_mw": round(float(base[b].mean()), 1),
                "contradiction_S1_mw": round(float(base[b][st["masks"]["S1"]].mean()), 1),
                "monthly_mw": [
                    round(float(base[b][mon == m].mean()), 1) for m in range(1, 13)
                ],
                "may_mw": round(float(base[b][mon == 5].mean()), 1),
            }

        # --- the RATING question, stated separately from availability --------
        under = [
            {
                "plant": pid,
                "model_pmax": round(rows[pid]["pmax"], 1),
                "campd_p99": round(rows[pid]["p99"], 1),
                "ratio": round(rows[pid]["pmax"] / max(rows[pid]["p99"], 1e-9), 3),
                "has_chp": rows[pid]["has_chp"],
                "gap_mw": round(rows[pid]["p99"] - rows[pid]["pmax"], 1),
            }
            for pid in both
            if rows[pid]["pmax"] < rows[pid]["p99"]
        ]
        under.sort(key=lambda r: -r["gap_mw"])
        yr["rating_question"] = {
            "n_plants_under_rated": len(under),
            "total_gap_mw": round(sum(u["gap_mw"] for u in under), 1),
            "gap_mw_chp_plants": round(
                sum(u["gap_mw"] for u in under if u["has_chp"]), 1
            ),
            "gap_mw_non_chp_plants": round(
                sum(u["gap_mw"] for u in under if not u["has_chp"]), 1
            ),
            "top": under[:15],
        }
        res["years"][str(year)] = yr
        del pack, lay, avail, prod, obs, series_by_variant

    # --- verdict ----------------------------------------------------------- #
    y = res["years"]["2025"]
    clean = y["buckets"]["NO_CHP_ADEQ_EXCL_OA"]["contradiction_mean_mw"]
    allm = y["buckets"]["ALL"]["contradiction_mean_mw"]
    v = y["variants"]
    owned = (
        round((clean - v["no_overlay"]["NO_CHP_ADEQ_EXCL_OA"]) / clean, 3)
        if clean > 0 else None
    )
    res["CLEAN_VERDICT"] = {
        "Kcc_as_preregistered_2025_mw": allm,
        "clean_scope_2025_mw": clean,
        "clean_share_of_preregistered": round(clean / allm, 3) if allm else None,
        "share_of_clean_removable_by_dropping_ALL_overlays": owned,
        "bar_mw": 500.0,
        "branch_on_clean_scope": (
            "B-1 overlay_over_removal" if clean >= 500.0 else "B-2 immaterial"
        ),
        "note": (
            "The pre-registered census is reported at full magnitude and is NOT "
            "withdrawn; this is its trap-2/trap-3 counter-measurement, which the "
            "PREREG required before B-1 could be quoted."
        ),
    }
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    print(json.dumps(r["CLEAN_VERDICT"], indent=1))
    for y in ("2023", "2024", "2025"):
        Y = r["years"][y]
        print(f"--- {y} buckets ---")
        for b, v in Y["buckets"].items():
            print(f"  {b:32s} n={v['n_plants']:3d} pmax={v['model_pmax_mw']:9.1f} "
                  f"contra={v['contradiction_mean_mw']:8.1f} S1={v['contradiction_S1_mw']:8.1f} may={v['may_mw']:8.1f}")
        print("  variants:", json.dumps(Y["variants"]))
        print("  rating:", {k: Y["rating_question"][k] for k in
                            ("n_plants_under_rated", "total_gap_mw", "gap_mw_chp_plants", "gap_mw_non_chp_plants")})
    print("->", OUT)
