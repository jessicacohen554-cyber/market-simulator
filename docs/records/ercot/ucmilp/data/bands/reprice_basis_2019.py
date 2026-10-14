"""UC-BANDS-ERCOT rule-14 (b): fixed-dispatch 2019 re-price of a basis-consistent band normalization.

Offer bands are identified as ``m = P / (HR_norm × g_norm)``. ``HR_norm`` is the
class cap-weighted bin ``Plant_Avg_HR``; ``g_norm`` is Henry Hub − 0.50 over the
derivation window. The model offers ``m × HR_fleet × g_dispatch``. A consistent
band is therefore ``m' = m × (HR_norm / HR_fleet) × (g_norm / g_dispatch)``, and
the offer scales by that factor. This script applies the per-class factor to the
whole offer of each marginal gas body tranche (committed and econ; peak is
reported apart). It does so in both bundles, for the keeper bands and for the
phase-1a SCED bands, and then propagates the change to the load-weighted price.
The method and biases are those of ``reprice_2019.py``: no re-dispatch, and the
whole offer is scaled.

Usage: python reprice_basis_2019.py <root holding the extracted uc bundle> <factors.json> <out.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[6]
ROOT, FAC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
BUNDLES = {
    "keeper": REPO / "results/calibration/closeout_ercot_l1_span",
    "uc": Path(ROOT) / "results/calibration/ucmilp_fix5_ercot_2019",
}
fac = json.load(open(FAC))


def run(bdir: Path, factors: dict[str, float], peak: bool) -> dict:
    """Load-weighted Δ price from scaling marginal gas tranches by ``factors``."""
    u = pd.read_parquet(
        bdir / "hourly/unit_marginal_2019.parquet",
        columns=["unit_id", "plant_group", "zone", "hour", "mc", "marginal"],
    )
    m = u[u.marginal == 1].copy()
    m["pg"] = m.plant_group.astype(str)
    m["zone"] = m.zone.astype(str)
    sfx = m.unit_id.astype(str).str.extract(r"_p\d+_(\w+)$")[0].fillna("")
    body = sfx.str.startswith(("committed", "econ"))
    sel = body | (sfx.str.startswith("peak") if peak else False)
    f = m.pg.map(factors).fillna(1.0).to_numpy()
    m["dmc"] = np.where(sel, m.mc.to_numpy(float) * (f - 1.0), 0.0)
    s = pd.read_parquet(
        bdir / "hourly/system_2019.parquet",
        columns=["pass", "zone", "hour", "price", "demand"],
    )
    s = s[s["pass"] == "P1"].copy()
    s["zone"] = s.zone.astype(str)
    s = s.join(m.groupby(["hour", "zone"]).dmc.mean().rename("dz"), on=["hour", "zone"])
    s = s.join(m.groupby("hour").dmc.mean().rename("dh"), on="hour")
    dp = s.dz.fillna(s.dh).fillna(0.0)
    base = float((s.price * s.demand).sum() / s.demand.sum())
    new = float(((s.price + dp) * s.demand).sum() / s.demand.sum())
    return {
        "base": base,
        "repriced": new,
        "delta": new - base,
        "c3a_pct_base": 100 * (base / 46.55 - 1),
        "c3a_pct_repriced": 100 * (new / 46.55 - 1),
    }


out = {}
for nm, bd in BUNDLES.items():
    for case, factors in fac["cases"].items():
        out[f"{nm}/{case}"] = run(bd, factors, peak=False)
json.dump({"factors": fac, "readings": out}, open(OUT, "w"), indent=1)
for k, v in out.items():
    print(k, {kk: round(vv, 3) for kk, vv in v.items()})
