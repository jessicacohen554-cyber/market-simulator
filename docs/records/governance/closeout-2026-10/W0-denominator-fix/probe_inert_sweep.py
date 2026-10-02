"""Zero-LP before/after: hash every fleet array the outage overlay feeds, per ISO-year, W0 posture."""

import hashlib
import json
import sys
from pathlib import Path
import numpy as np

root = Path(sys.argv[1])
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src"))
import market_sim  # noqa: E402

assert str(root) in market_sim.__file__, market_sim.__file__
from scripts.build_fleet_census import rebuild_fleet  # noqa: E402

REPO = Path("/home/user/market-simulator")
bundle, years = sys.argv[2], [int(y) for y in sys.argv[3].split(",")]
out = {}
for y in years:
    res = rebuild_fleet(
        REPO / "results/calibration" / bundle,
        y,
        "w0",
        json.loads(sys.argv[5]) if len(sys.argv) > 5 else None,
    )
    fa, fleet = res["fleet_arrays"], res["fleet"]
    h = {}
    for name in ("availability", "pmax", "pmin", "min_gen", "mc_base"):
        v = getattr(fa, name, None)
        if v is not None:
            h[name] = hashlib.sha256(
                np.ascontiguousarray(np.asarray(v, float)).tobytes()
            ).hexdigest()[:16]
    rec = dict(hashes=h, n_units=len(fleet))
    try:
        from market_sim.data.outages import lp_bin_capacity_index

        ros = lp_bin_capacity_index(fleet, np.asarray(fa.pmax, float), exit_year=y)
        rec["monthly_bins"] = [[k[0], k[1], list(v)] for k, v in ros if len(k) == 3]
    except TypeError:
        rec["monthly_bins"] = None
    rec["in_year_exit_rows"] = sorted(
        {g.unit_id.rsplit("_", 1)[0] for g in fleet if f"_r{y}" in str(g.unit_id)}
    )
    out[y] = rec
    print(bundle, y, json.dumps(rec)[:400], flush=True)
Path(sys.argv[4]).write_text(json.dumps(out, indent=1))
