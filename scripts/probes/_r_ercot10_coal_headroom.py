"""R-ERCOT-10 phase 0: zero-LP per-plant PRB coal available-energy census.

Rebuilds the fusco keeper recipe's LP fleet with ``run_year(fleet_only=True)``
(reusing ``_r_ercot3_coal_census.build`` with the bundle swapped to
``r_ercot8_fusco_span``) and reports per coal plant: pmax, available energy
(sum pmax x availability), must-run floor energy (sum min_gen), per-tranche
available energy and mean mc, plus the coal fuel-price entries the loader set.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_r_ercot10_coal_headroom.py \
        --years 2019 2020 2023 --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts/probes"):
    sys.path.insert(0, str(p))

import _r_ercot3_coal_census as c3  # noqa: E402

c3.BUNDLE = REPO / "results/calibration/r_ercot8_fusco_span"


def census(st: dict) -> dict:
    """Per-plant, per-tranche available energy and mc for coal rows."""
    fa = st["fleet_arrays"]
    n = len(fa.pmax)
    grp = np.array([str(g) for g in fa.plant_group])
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    if av.ndim == 1:
        av = np.repeat(av[:, None], 8760, axis=1)
    mc = np.asarray(st["mc_base"], float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], 8760, axis=1)
    codes = c3._arr(fa, "plant_code", n)
    names = c3._arr(fa, "plant_name", n)
    tr = None
    for cand in ("tranche", "tranche_name", "bin_tranche", "tranche_label", "unit_name", "name"):
        tr = c3._arr(fa, cand, n)
        if tr is not None:
            break
    mg = c3._arr(fa, "min_gen", n)
    out: dict = {}
    gens = st.get("generators") or []
    uid = c3._arr(fa, "unit_ids", n)
    if uid is None:
        uid = c3._arr(fa, "unit_id", n)
    for i in np.where(np.char.find(grp.astype(str), "COAL") >= 0)[0]:
        gi = gens[i] if i < len(gens) else None
        pc = codes[i] if codes is not None else getattr(gi, "plant_code", None)
        un = str(uid[i]) if uid is not None else str(getattr(gi, "unit_id", i))
        key = f"{pc}|{grp[i]}"
        e = out.setdefault(key, {"pmax": 0.0, "avail_twh": 0.0, "mingen_twh": 0.0, "tranches": []})
        a_e = float((pmax[i] * av[i]).sum()) / 1e6
        m_e = 0.0 if mg is None else float(np.broadcast_to(np.asarray(mg[i], float), (8760,)).sum()) / 1e6
        e["pmax"] += float(pmax[i])
        e["avail_twh"] += a_e
        e["mingen_twh"] += m_e
        e["tranches"].append({"tr": un[-32:], "pmax": round(float(pmax[i]), 1),
                              "avail_twh": round(a_e, 3), "mingen_twh": round(m_e, 3),
                              "mc_mean": round(float(mc[i].mean()), 2)})
    return out


def main() -> None:
    """Run the census for the requested years."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {}
    for y in a.years:
        st, lines = c3.build(y)
        if y == a.years[0]:
            print("state keys", sorted(st.keys())[:60], flush=True)
            print("fa fields", sorted(vars(st["fleet_arrays"]).keys()) if hasattr(st["fleet_arrays"], "__dict__") else dir(st["fleet_arrays"]), flush=True)
        res[str(y)] = {"plants": census(st), "fuel": c3.summarize(st)["fuel_price_means"],
                       "coal_lines": sorted({ln.strip()[:300] for ln in lines if "coal" in ln.lower()})[:200]}
        print(y, "done", flush=True)
    Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
