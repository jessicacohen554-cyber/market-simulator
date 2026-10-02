"""Zero-LP Scherer 6257 availability under the soco96 recipe at W0 posture."""

import sys
import json
from pathlib import Path
import numpy as np

sys.path.insert(0, ".")
from scripts.build_fleet_census import rebuild_fleet  # noqa: E402
from market_sim.data.fleet.models import _hour_to_month_index  # noqa: E402

year = int(sys.argv[1])
ov = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
res = rebuild_fleet(Path("results/calibration/soco96_span"), year, "w0", ov)
fa, fleet = res["fleet_arrays"], res["fleet"]
pmax = np.asarray(fa.pmax, float)
av = np.asarray(fa.availability, float)
mi = _hour_to_month_index(av.shape[1])
idx = [i for i, g in enumerate(fleet) if int(g.plant_code) == 6257]
surv = [i for i in idx if "_r2" not in fleet[i].unit_id]
coh = [i for i in idx if "_r2" in fleet[i].unit_id]


def wmean(rows, m):
    w = pmax[rows]
    return float((w[:, None] * av[rows][:, m]).sum() / w.sum() / m.sum())


r = dict(
    overrides=ov,
    survivors_mw=float(pmax[surv].sum()),
    cohort_mw=float(pmax[coh].sum()),
    surv_avail_jan=wmean(surv, mi == 0),
    surv_avail_febdec=wmean(surv, mi > 0),
    surv_avail_year=wmean(surv, mi >= 0),
    cohort_avail_jan=wmean(coh, mi == 0) if coh else None,
    scherer_avail_twh=float((pmax[idx, None] * av[idx]).sum() / 1e6),
)
print("RESULT " + json.dumps(r))
