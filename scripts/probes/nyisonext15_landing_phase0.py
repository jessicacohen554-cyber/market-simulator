"""NYISO-NEXT-15 phase 0 (ZERO LP): why the Total-East link binds in the wrong hours.

Reads the NEXT-14 keeper legs' committed P1 network + system sidecars (fetched
from the leg shard commits into ``--legs``; provenance SHAs in
``docs/records/nyiso/RESULT-nyiso-next14-total-east-cutset-2026-09-30.md`` §3) and the
``nyiso-interface-flows`` clean partition (MIS P-32). Writes
``results/phase0/nyiso/_nyisonext15_phase0.json``.

Blocks, per year 2021-2025:

* ``market_ce_binding``: measured TOTAL EAST / CENTRAL EAST flow, CE limit, and
  the model's link flow, in the market's CE-binding hours (CE >= 95 % of its
  posted limit) vs the rest; the CE/TE regression slope.
* ``landing``: each pooled border link's model mean flow and cap vs its measured
  attributed P-32 net (the allocation defect).
* ``band_feasibility``: minimum monthly headroom of the per-landing targets
  against the link's own hourly caps, for (a) EIA-930 total split by P-32 shares
  and (b) each link's own P-32 schedule (the armed construction).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from market_sim.data.eia_loader import nyiso_net_interchange  # noqa: E402
from market_sim.data.fleet import _hour_to_month_index  # noqa: E402
from market_sim.data.nyiso_par_attribution import attributed_zone_net  # noqa: E402
from scripts.lib.clean_io import read_clean  # noqa: E402

OUT = REPO / "results" / "phase0" / "nyiso" / "_nyisonext15_phase0.json"
LINK = "Upstate_West>Capital_Hudson"
ZONES = ["Capital_Hudson", "Long_Island", "NYC", "Upstate_West"]
NE_ROW = "SCH - NE - NY"


def year_block(y: int, legs: Path) -> dict:
    """All phase-0 numbers for one year."""
    f = read_clean("nyiso-interface-flows", iso="NYISO", year=y, validate=False)
    f["lh"] = pd.to_datetime(f.interval_start_local).dt.floor("h")
    p = f.groupby(["lh", "interface"]).flow_mw.mean().unstack()
    lim = f.groupby(["lh", "interface"]).positive_limit_mw.mean().unstack()
    n = pd.read_parquet(legs / f"network_{y}.parquet")
    n = n[n["pass"] == "P1"]
    idx = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
    flow = n.pivot_table(index="hour", columns="name", values="mw")
    flow.index = idx
    up = n.pivot_table(index="hour", columns="name", values="limit_up")
    up.index = idx
    dn = n.pivot_table(index="hour", columns="name", values="limit_dn")
    dn.index = idx

    d = pd.DataFrame(
        {
            "te": p["TOTAL EAST"],
            "ce": p["CENTRAL EAST - VC"],
            "ce_limit": lim["CENTRAL EAST - VC"],
        }
    ).reindex(idx)
    d["model_link"] = flow[LINK]
    d["model_link_limit"] = up[LINK]
    d = d.dropna()
    b = d.ce >= 0.95 * d.ce_limit
    slope, icpt = np.polyfit(d.te, d.ce, 1)
    ce_block = {
        "share_h": round(float(b.mean()), 3),
        "binding": {k: round(float(v), 0) for k, v in d[b].mean().items()},
        "other": {k: round(float(v), 0) for k, v in d[~b].mean().items()},
        "ce_on_te_slope": round(float(slope), 3),
        "ce_on_te_intercept": round(float(icpt), 0),
        "corr_ce_te": round(float(d.ce.corr(d.te)), 2),
        "corr_te_model_link": round(float(d.te.corr(d.model_link)), 2),
    }

    an = attributed_zone_net(f[f.interface != NE_ROW], y)
    an = an[~((an.local_hour.dt.month == 2) & (an.local_hour.dt.day == 29))]
    meas = an.groupby("zone").flow_mw.mean()
    landing = {}
    for z in ZONES:
        col = f"NYISO_external>{z}"
        landing[z] = {
            "model_mw": round(float(flow[col].mean()), 0),
            "cap_mw": round(float(up[col].mean()), 0),
            "measured_mw": round(float(meas[z]), 0),
            "h_at_cap": round(float((flow[col] >= up[col] - 1).mean()), 3),
        }

    mi = _hour_to_month_index(8760)
    pz = an.groupby([an.local_hour.dt.month, "zone"]).flow_mw.sum().unstack()[ZONES]
    ne = f[f.interface == NE_ROW].groupby("lh").flow_mw.mean()
    ne = ne[~((ne.index.month == 2) & (ne.index.day == 29))]
    eia = -np.asarray(nyiso_net_interchange(y), float)[:8760]
    total = np.bincount(mi, weights=eia) - ne.groupby(ne.index.month).sum().values
    share_tgt = pz.div(pz.sum(axis=1), axis=0).mul(total, axis=0)
    feas = {}
    for name, tgt in (("eia930_split", share_tgt), ("p32_per_link", pz)):
        rows = {}
        for z in ZONES:
            col = f"NYISO_external>{z}"
            cap_up = np.bincount(mi, weights=up[col].to_numpy())
            cap_dn = np.bincount(mi, weights=dn[col].to_numpy())
            t = tgt[z].to_numpy()
            rows[z] = {
                "min_upper_headroom_gwh": round(float(np.min(cap_up - 1.02 * t)) / 1e3, 1),
                "min_lower_headroom_gwh": round(float(np.min(0.98 * t - cap_dn)) / 1e3, 1),
            }
        feas[name] = rows
    return {
        "market_ce_binding": ce_block,
        "landing": landing,
        "pooled_twh": {
            "eia930_band_target": round(float(total.sum()) / 1e6, 2),
            "p32_sum": round(float(pz.sum().sum()) / 1e6, 2),
        },
        "band_feasibility": feas,
    }


def main() -> None:
    """Compute every year and write the JSON record."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--legs", type=Path, required=True)
    a = ap.parse_args()
    out = {str(y): year_block(y, a.legs) for y in range(2021, 2026)}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    for y, blk in out.items():
        print(y, blk["pooled_twh"], {z: v["model_mw"] - v["measured_mw"] for z, v in blk["landing"].items()})


if __name__ == "__main__":
    main()
