"""Zero-LP greedy for the SOCO 2019-2022 NUCLEAR_MONTHLY_CF_BY_YEAR coverage repair."""

import json
import re
import base64
import gzip
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
import calibration_verdict as cv

OUT = "docs/records/soco/r-soco/closeout-soco-2/"
FALL = (
    np.array([0.99, 0.89, 0.83, 0.89, 0.91, 0.94, 0.93, 0.98, 0.84, 0.89, 0.92, 0.98])
    * 0.97
)
NEW = {
    2019: [1.00, 0.83, 0.73, 0.87, 0.95, 0.99, 0.96, 0.99, 0.93, 0.87, 1.00, 1.00],
    2020: [1.00, 0.86, 0.76, 0.95, 1.00, 0.94, 1.00, 0.89, 0.92, 0.90, 0.87, 1.00],
    2021: [1.00, 0.90, 0.91, 0.87, 1.00, 0.96, 0.95, 0.97, 0.88, 0.96, 1.00, 0.99],
    2022: [1.00, 0.89, 0.83, 0.86, 0.94, 1.00, 1.00, 0.99, 0.93, 0.83, 0.86, 0.89],
}
t = open("frontend/data/backcast/runs/2026-10-02-w0-soco-fix2.js").read()
P = json.loads(
    gzip.decompress(base64.b64decode(re.search(r'="([A-Za-z0-9+/=]+)"', t).group(1)))
)
EXCL = {"nuclear", "hydro", "solar", "wind", "biomass", "OTHER"}
summary = []
for y in range(2019, 2026):
    yp = json.loads(json.dumps(P["years"][str(y)]))
    yb = json.load(gzip.open(f"frontend/data/backcast/bench/SOCO/{y}.json.gz"))["bench"]
    base_c1 = {
        r["key"]: r for r in cv.score_fuelmix(y, P["years"][str(y)], yb, iso="SOCO")
    }
    base_c3 = cv.score_price_mean(y, P["years"][str(y)], yb, "SOCO")
    dcls = {}
    dprice_lw = 0.0
    if y in NEW:
        u = pd.read_parquet(
            f"results/calibration/w0_soco_span/hourly/unit_marginal_{y}.parquet"
        )
        s = pd.read_parquet(
            f"results/calibration/w0_soco_span/hourly/system_{y}.parquet"
        )
        s = s[s["pass"] == "P1"]
        dem = s.groupby("hour").demand.sum().values
        lw_price = s.assign(pd_=s.price * s.demand).groupby("hour").pd_.sum().values
        base_lw = lw_price.sum() / dem.sum()
        hrs = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
        mo = hrs.month.values - 1
        nuc = u[u.fuel.astype(str) == "nuclear"]
        cap = nuc.pivot_table(
            index="hour", columns="unit_id", values="cap_mw", observed=True
        ).values
        pmax = cap / FALL[mo][:, None]
        dN = (pmax * np.array(NEW[y])[mo][:, None] - cap).sum(
            1
        )  # MW per hour (+ = more nuclear)
        zp = s.pivot_table(index="hour", columns="zone", values="price", observed=True)
        th = u[
            (u.fuel.astype(str).isin(["gas_cc", "gas_ct", "gas_st", "coal", "oil"]))
            & ~u.unit_id.astype(str).str.endswith("mustrun")
        ].copy()
        th["zprice"] = zp.values[
            th.hour.values, zp.columns.get_indexer(th.zone.astype(str))
        ]
        H = th.hour.values
        MW = th.mw.values.astype(float)
        CAP = th.cap_mw.values.astype(float)
        MC = th.mc.values.astype(float)
        GRP = np.where(
            th.fuel.astype(str).values == "oil",
            "oil",
            th.plant_group.astype(str).values,
        )
        ZP = th.zprice.values.astype(float)
        order = np.lexsort((-MC, H))
        H, MW, CAP, MC, GRP, ZP = (
            H[order],
            MW[order],
            CAP[order],
            MC[order],
            GRP[order],
            ZP[order],
        )
        bounds = np.searchsorted(H, np.arange(8761))
        newMW = MW.copy()
        dprice = np.zeros(8760)
        TOL = 0.05
        for h in range(8760):
            a, b = bounds[h], bounds[h + 1]
            d = dN[h]
            mw = newMW[a:b]
            mc = MC[a:b]
            cp = CAP[a:b]
            zpr = ZP[a:b]
            inm = mc <= zpr + TOL
            _st = [i for i in range(b - a) if inm[i] and mw[i] > 1e-3]
            p0 = mc[_st].max() if _st else 0
            if d > 0:
                rem = d
                last = None
                for i in range(b - a):
                    if rem <= 0:
                        break
                    if mw[i] > 1e-3 and inm[i]:
                        take = min(mw[i], rem)
                        mw[i] -= take
                        rem -= take
                        last = i
                # new setter: highest-mc in-merit unit still above 0 output
                still = [i for i in range(b - a) if inm[i] and mw[i] > 1e-3]
                setter = mc[still].max() if still else 0
                dprice[h] = min(0.0, setter - p0) if last is not None else 0.0
            elif d < 0:
                rem = -d
                top = None
                for i in range(b - a - 1, -1, -1):
                    if rem <= 0:
                        break
                    hr = cp[i] - mw[i]
                    if hr > 1e-3:
                        add = min(hr, rem)
                        mw[i] += add
                        rem -= add
                        top = mc[i]
                dprice[h] = max(0.0, top - p0) if top is not None else 0.0
        pass
        dmw = newMW - MW
        dcls = pd.Series(dmw).groupby(GRP).sum().div(1e6).to_dict()
        dcls["nuclear"] = dN.sum() / 1e6
        new_lw = ((lw_price / dem + dprice) * dem).sum() / dem.sum()
        dprice_lw = new_lw - base_lw
        for k, v in dcls.items():
            yp["gmModel"][k] = yp["gmModel"].get(k, 0) + v
    new_c1 = {r["key"]: r for r in cv.score_fuelmix(y, yp, yb, iso="SOCO")}
    m3 = base_c3["model"]
    a3 = base_c3["actual"]
    pct_base = 100 * (m3 - a3) / a3
    pct_new = 100 * (m3 + dprice_lw - a3) / a3
    flips = [
        (k, base_c1[k]["status"], new_c1[k]["status"])
        for k in new_c1
        if base_c1[k]["status"] != new_c1[k]["status"]
    ]
    summary.append(
        dict(
            year=y,
            dNuc=round(dcls.get("nuclear", 0), 3),
            dCC=round(dcls.get("CC_REGULAR", 0), 3),
            dBIT=round(dcls.get("COAL_BIT", 0), 3),
            dPRB=round(dcls.get("COAL_PRB", 0), 3),
            dCT=round(dcls.get("CT_PEAKER", 0), 3),
            dSTG=round(dcls.get("ST_GAS", 0), 3),
            cc_pp_base=base_c1["CC_REGULAR"]["share_pp"],
            cc_pp_new=new_c1["CC_REGULAR"]["share_pp"],
            cc_status=new_c1["CC_REGULAR"]["status"],
            bit_pp_base=base_c1["COAL_BIT"]["share_pp"],
            bit_pp_new=new_c1["COAL_BIT"]["share_pp"],
            prb_pp_new=new_c1["COAL_PRB"]["share_pp"],
            c3a_base=round(pct_base, 2),
            c3a_new=round(pct_new, 2),
            dLW=round(dprice_lw, 3),
            flips=flips,
        )
    )
pd.set_option("display.width", 300)
S = pd.DataFrame(summary)
S.to_csv(OUT + "greedy_nuc.csv", index=False)
print(S.to_string())
