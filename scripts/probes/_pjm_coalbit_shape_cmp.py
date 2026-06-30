"""Compare per-plant bituminous CF shape: keeper vs marginal-bit.

Reads dispatch/<year>_P1.parquet + the campd shared input from each bundle,
builds per-plant hourly model MW (sum by plant_code) and CAMPD net MW, and
reports per-plant Pearson r (hourly shape), NRMSE, CF-band overlap / EMD
(timing-free operating-level histogram: a baseload-pinned plant sits in one
high band, a marginal plant spreads like CAMPD), and annual GWh.

Usage: python scripts/probes/_pjm_coalbit_shape_cmp.py <keeper_bundle> <marginal_bundle> <year>
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bundle_io import bundle_input_path  # noqa: E402
from market_sim.data.coal import coal_supply_class  # noqa: E402
from market_sim.results.calibration import check_cf_band_occupancy  # noqa: E402

keeper, marg, year = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
_T = 8760
KEY = {
    2828: "Cardinal",
    2876: "Kyger Crk",
    8102: "Gavin",
    3935: "Amos",
    3936: "Mountaineer",
    6264: "Conemaugh",
    3954: "Keystone",
}


def model_mw(bundle):
    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    dm = disp[(disp["plant_code"] > 0)]
    out = {}
    for code, g in dm.groupby("plant_code", observed=True):
        arr = (
            g.groupby("hour")["mw"]
            .sum()
            .reindex(range(_T), fill_value=0.0)
            .to_numpy(float)
        )
        out[int(code)] = arr
    return out


def campd_mw(bundle):
    cp = bundle_input_path(bundle, "campd")
    campd = pd.read_parquet(cp)
    campd = campd[campd["year"] == year]
    out = {}
    for code, g in campd.groupby("plant_id", observed=True):
        a = np.nan_to_num(g.sort_values("hour")["net_mw"].to_numpy(float))
        out[int(code)] = np.concatenate([a, np.zeros(max(0, _T - a.shape[0]))])[:_T]
    return out


def pear(m, o):
    if m.std() < 1e-9 or o.std() < 1e-9:
        return float("nan")
    return float(np.corrcoef(m, o)[0, 1])


def nrmse(m, o):
    d = o.max() - o.min()
    return float(np.sqrt(np.mean((m - o) ** 2)) / d) if d > 1e-9 else float("nan")


mk, mm = model_mw(keeper), model_mw(marg)
cn = campd_mw(keeper)  # same shared campd benchmark for both

codes = [
    c
    for c in cn
    if coal_supply_class(c) == "bituminous" and c in mk and c in mm and cn[c].sum() > 0
]
codes = sorted(codes, key=lambda c: -cn[c].sum())

print(
    f"\n=== PJM bituminous per-plant CF shape {year}: keeper(floor0.76,mustrun) "
    f"vs marginal(floor1.0,dispatchable) ==="
)
print(
    f"{'plant':>11} {'r_keep':>6}{'r_mar':>6} {'emd_k':>6}{'emd_m':>6} "
    f"{'ovl_k':>6}{'ovl_m':>6} {'GWh_k':>7}{'GWh_m':>7}{'GWh_C':>7}"
)
W = {"r": [0.0, 0.0], "emd": [0.0, 0.0], "ovl": [0.0, 0.0]}
nw = 0.0
tk = tm = tc = 0.0
for c in codes:
    o = cn[c]
    mk_, mm_ = mk[c], mm[c]
    rk, rm = pear(mk_, o), pear(mm_, o)
    try:
        ok = check_cf_band_occupancy(mk_, o)
        om = check_cf_band_occupancy(mm_, o)
        emk, emm = ok["cf_emd"], om["cf_emd"]
        ovk, ovm = ok["band_overlap"], om["band_overlap"]
    except Exception:
        emk = emm = ovk = ovm = float("nan")
    gk, gm, gc = mk_.sum() / 1e3, mm_.sum() / 1e3, o.sum() / 1e3
    nm = KEY.get(c, str(c))
    print(
        f"{nm:>11} {rk:6.3f}{rm:6.3f} {emk:6.3f}{emm:6.3f} {ovk:6.3f}{ovm:6.3f} "
        f"{gk:7.0f}{gm:7.0f}{gc:7.0f}"
    )
    w = gc
    for key, a, b in [("r", rk, rm), ("emd", emk, emm), ("ovl", ovk, ovm)]:
        if np.isfinite(a) and np.isfinite(b):
            W[key][0] += a * w
            W[key][1] += b * w
    nw += w
    tk += gk
    tm += gm
    tc += gc
print("-" * 86)
print(f"CAMPD-GWh-weighted fleet (n={len(codes)}):")
for key, lbl, better in [
    ("r", "pearson_r", "higher"),
    ("emd", "cf_emd", "lower"),
    ("ovl", "band_overlap", "higher"),
]:
    a, b = W[key][0] / nw, W[key][1] / nw
    print(
        f"  {lbl:14} keeper={a:.4f}  marginal={b:.4f}  delta={b - a:+.4f}  ({better} better)"
    )
print(
    f"  annual TWh     keeper={tk / 1e3:.1f}  marginal={tm / 1e3:.1f}  campd={tc / 1e3:.1f}"
)
