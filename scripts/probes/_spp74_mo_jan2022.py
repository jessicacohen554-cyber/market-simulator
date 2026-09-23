"""SPP-74 — size the N3045MO3 Jan-2022 reference defect at zero LP.

The committed EIA state table prints MO Jan 2022 at 152.45 $/Mcf (23.8x the US series; MO's
next 11 months 4.31-7.27). The SPP-49 plausibility screen trusts that reference, so every MO
gas row's Jan 2022 fuel is 147.15 $/MMBtu in the rung's LP. Diagnostic counterfactual only:
re-price those rows at the US series reference (6.41 $/Mcf), re-clear the SPP-70 merit order at
the LP's own served thermal, and re-score C3a/C3b 2022 with the per-hour price delta. The served
quantity is held fixed, so this is a first-order (price-side) estimate, not a re-dispatch.

Usage: ``uv run python scripts/probes/_spp74_mo_jan2022.py --out <json>``
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.probes._spp70_meritorder_counterfactual import THERMAL_PREFIXES  # noqa: E402
from scripts.probes._spp72_demand_tightness import (  # noqa: E402
    CST_OFFSET_H,
    model_clock_index,
)
from scripts.probes._spp74_body_decomposition import (  # noqa: E402
    MCF_TO_MMBTU,
    RUNG,
    model_price_demand,
    rows,
)

Y = 2022
BAD, US_REF = (
    152.45 / MCF_TO_MMBTU,
    6.41 / MCF_TO_MMBTU,
)  # N3045MO3 / N3045US3, Jan 2022


def main() -> int:
    """Size the defect; one JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    bundle = REPO / "results/calibration" / RUNG
    st, _ = reconstruct_bundle_fleet(bundle, Y, verbose=False)
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], float)
    fuel = np.asarray(st["fuel_prices"], float)
    vom = np.asarray(fa.vom, float)
    pmax = np.asarray(fa.pmax, float)
    avail = np.asarray(fa.availability, float)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], mc.shape)
    g = np.asarray(fa.plant_group).astype(str)
    th = np.array([x.startswith(THERMAL_PREFIXES) for x in g])
    clock = model_clock_index(Y).tz_convert(None) - pd.Timedelta(hours=CST_OFFSET_H)
    month = clock.month.to_numpy() - 1
    jan = month == 0
    # the exact reference value, plus every row the nearby pool blended it into
    hit = (fuel > 3.0 * US_REF) & jan[None, :] & th[:, None]
    exact = np.isclose(fuel, BAD, rtol=1e-6)
    rows_hit = hit.any(axis=1)
    mc_fix = mc.copy()
    scale = np.where(hit, US_REF / np.where(hit, fuel, 1.0), 1.0)
    mc_fix = vom[:, None] + (mc - vom[:, None]) * scale
    cap = pmax[:, None] * avail
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{Y}.parquet")
    ch = ch[
        (ch["pass"] == "P1") & ch["klass"].astype(str).str.startswith(THERMAL_PREFIXES)
    ]
    served = (
        ch.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0.0).to_numpy()
    )

    def clear(m, t):
        o = np.argsort(m[th, t], kind="stable")
        c = np.cumsum(cap[th, t][o])
        i = min(int(np.searchsorted(c, served[t])), len(o) - 1)
        return m[th, t][o[i]]

    hrs = np.flatnonzero(jan)
    base = np.array([clear(mc, t) for t in hrs])
    fix = np.array([clear(mc_fix, t) for t in hrs])
    p, d = model_price_demand(Y)
    q = p.copy()
    q[hrs] = p[hrs] + (fix - base)
    with gzip.open(REPO / f"frontend/data/backcast/bench/SPP/{Y}.json.gz") as f:
        b = json.load(f)["bench"]["avgLMP"]
    a0, b0 = rows(p, d, month, b)
    a1, b1 = rows(q, d, month, b)
    jan_dw0 = float(np.sum(p[jan] * d[jan]) / d[jan].sum())
    jan_dw1 = float(np.sum(q[jan] * d[jan]) / d[jan].sum())
    out = {
        "rows_exact": int(exact.any(axis=1).sum()),
        "mw_exact": float(pmax[exact.any(axis=1)].sum()),
        "rows_hit": int(rows_hit.sum()),
        "jan_fuel_hit_range": [float(fuel[hit].min()), float(fuel[hit].max())],
        "mw_hit": float(pmax[rows_hit].sum()),
        "hours_hit": int(hit.any(axis=0).sum()),
        "exact_only_jan": bool(not exact[:, ~jan].any()),
        "classes_hit": pd.Series(g[rows_hit]).value_counts().to_dict(),
        "plants_hit": sorted({int(x) for x in np.asarray(fa.plant_code)[rows_hit]}),
        "jan_recon_mean_base": float(base.mean()),
        "jan_recon_mean_fix": float(fix.mean()),
        "jan_delta_mean": float((fix - base).mean()),
        "jan_hours_moved": int((np.abs(fix - base) > 0.01).sum()),
        "jan_model_dw": [jan_dw0, jan_dw1],
        "jan_rt_bench": b["rt_mon"][0],
        "C3a_2022": [a0, a1],
        "C3b_2022": [b0, b1],
    }
    args.out.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
