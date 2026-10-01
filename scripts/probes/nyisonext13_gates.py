"""NYISO-NEXT-13 G-2 (a)(b)(c) and reported diagnostics (ZERO LP), per arm leg.

``docs/records/nyiso/PRECOMMIT-nyiso-next13-ne-ac-recon-detach-2026-09-29.md`` sec. 5:

G-2 (a): the NE AC node's P1 net flow is within one band step of the flow its own
     bands imply at its own LMP in >= 95 % of hours (keeper 33.5-63.2 %).
G-2 (b): the pooled node's monthly net import lies inside the detached band
     (EIA-930 net import - measured NE AC schedule, +-NYISO_IMPORT_RECON_BAND_FRAC)
     in every month.
G-2 (c): the node exports in >= 1 h and imports in >= 1 h.
Reported: node / pooled TWh vs measured, hours at the posted bounds, load-weighted
P1 price delta vs the keeper by zone. Record: ``results/phase0/nyiso/_nyisonext13_gates.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO / "src", REPO, REPO / "scripts" / "data", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(p))

import derive_nyiso_ne_ac_ladder as dne  # noqa: E402
from nyisonext11_ne_ac_node_phase0 import implied_flow  # noqa: E402

from market_sim.data.eia_loader import nyiso_net_interchange  # noqa: E402
from market_sim.data.fleet import _hour_to_month_index  # noqa: E402
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES  # noqa: E402
from market_sim.model.interchange.nyiso import (  # noqa: E402
    load_nyiso_ne_ac_measured_flow,
    load_nyiso_ne_ac_neighbour_price,
)
from market_sim.model.interchange.spec import (  # noqa: E402
    NYISO_IMPORT_RECON_BAND_FRAC,
    NYISO_NE_AC_LADDER_BY_YEAR,
)

CAL = REPO / "results" / "calibration"
H = 8760
G2A_SHARE = 0.95
KEEP = {2021: "nyisonext12_2021", **{y: "nyisonext12_span" for y in range(2022, 2026)}}
NODE = "NYISO_NE_AC_"


def _lw(s: pd.DataFrame) -> dict:
    s = s[s["pass"] == "P1"]
    out = {}
    for z, g in s.groupby(s.zone.astype(str)):
        if g.demand.sum() > 0:
            out[z] = float((g.price * g.demand).sum() / g.demand.sum())
    out["system"] = float((s.price * s.demand).sum() / s.demand.sum())
    return out


def year(y: int, leg: str) -> dict:
    """Gate values for one leg."""
    d = pd.read_parquet(
        CAL / leg / "dispatch" / f"{y}_P1.parquet",
        columns=["unit_id", "hour", "mw", "lmp", "fuel"],
    )
    d["unit_id"] = d["unit_id"].astype(str)
    imp = d[d.fuel.astype(str) == "import"]
    is_node = imp.unit_id.str.startswith(NODE)
    node = imp[is_node]
    q = node.groupby("hour").mw.sum().reindex(range(H), fill_value=0.0).to_numpy()
    lmp = node.groupby("hour").lmp.first().reindex(range(H)).to_numpy()
    pooled = (
        imp[~is_node].groupby("hour").mw.sum().reindex(range(H), fill_value=0.0)
    ).to_numpy()

    lad = NYISO_NE_AC_LADDER_BY_YEAR[y]
    si, se = (
        lad["import_mw"] / SEAM_FLOW_TRANCHES,
        lad["export_mw"] / SEAM_FLOW_TRANCHES,
    )
    dd = dne.derive_year(y)
    ci = np.nan_to_num(dd["limit_import"], nan=lad["import_mw"])
    ce = np.nan_to_num(dd["limit_export"], nan=lad["export_mw"])
    ros = load_nyiso_ne_ac_neighbour_price(y, H)
    qi = implied_flow(lmp - ros, lad["import"], lad["export"], si, se, ci, ce)
    share = float((np.abs(q - qi) <= max(si, se) + 1.0).mean())

    mi = _hour_to_month_index(H)
    ne_meas = load_nyiso_ne_ac_measured_flow(y, H)
    tgt = -np.asarray(nyiso_net_interchange(y), float)[:H] - ne_meas
    tm = np.bincount(mi, weights=tgt)
    half = NYISO_IMPORT_RECON_BAND_FRAC * np.abs(tm)
    pm = np.bincount(mi, weights=pooled)
    tol = 1.0  # MWh, LP feasibility tolerance
    inside = (pm >= tm - half - tol) & (pm <= tm + half + tol)

    exp_h = int(
        (
            node[node.unit_id.str.contains("_exp#")].groupby("hour").mw.sum() < -1e-6
        ).sum()
    )
    imp_h = int(
        (node[node.unit_id.str.contains("_imp#")].groupby("hour").mw.sum() > 1e-6).sum()
    )

    lw_a = _lw(pd.read_parquet(CAL / leg / "hourly" / f"system_{y}.parquet"))
    lw_k = _lw(pd.read_parquet(CAL / KEEP[y] / "hourly" / f"system_{y}.parquet"))
    return {
        "G2a_share_within_one_band": round(share, 4),
        "G2a_pass": share >= G2A_SHARE,
        "G2b_months_inside": int(inside.sum()),
        "G2b_pass": bool(inside.all()),
        "G2b_pooled_minus_target_gwh": np.round((pm - tm) / 1e3, 1).tolist(),
        "G2c_hours_export_import": [exp_h, imp_h],
        "G2c_pass": exp_h >= 1 and imp_h >= 1,
        "node_twh": round(float(q.sum()) / 1e6, 3),
        "node_measured_twh": round(float(ne_meas.sum()) / 1e6, 3),
        "node_implied_at_own_lmp_twh": round(float(qi.sum()) / 1e6, 3),
        "pooled_twh": round(float(pooled.sum()) / 1e6, 3),
        "pooled_target_twh": round(float(tgt.sum()) / 1e6, 3),
        "hours_at_posted_import": int((q >= ci - 1).sum()),
        "hours_at_posted_export": int((-q >= ce - 1).sum()),
        "lw_price_delta_vs_keeper": {
            z: round(lw_a[z] - lw_k[z], 2) for z in lw_a if z in lw_k
        },
    }


if __name__ == "__main__":
    ys = [int(x) for x in sys.argv[1:]] or [2021, 2022, 2023, 2024, 2025]
    res = {str(y): year(y, f"nyisonext13_{y}") for y in ys}
    p = CAL.parent / "phase0" / "nyiso" / "_nyisonext13_gates.json"
    old = json.loads(p.read_text()) if p.exists() else {}
    old.update(res)
    p.write_text(json.dumps(old, indent=1) + "\n")
    print(json.dumps(res, indent=1))
