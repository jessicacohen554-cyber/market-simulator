"""UC-BANDS-ERCOT phase 0 (zero LP): decompose the ERCOT 2019 C3a gap, keeper vs UC uc-1.4.

Inputs: the keeper bundle ``results/calibration/closeout_ercot_l1_span`` (on main) and the
uc-1.4 2019 bundle extracted from ``claude/ucmilp-fix5-ercot-2019`` @ ``f832aa52``
(``git archive f832aa52 results/calibration/ucmilp_fix5_ercot_2019 | tar -x -C <root>``),
plus ``data/raw/campd-unit-level/TX_2019.parquet`` (DATA PROFILE ercot).

Usage: python bands_zero_lp.py <root holding the extracted uc bundle> <out.json>
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

ROOT, OUT = sys.argv[1], sys.argv[2]
K = "results/calibration/closeout_ercot_l1_span/"
U = ROOT + "/results/calibration/ucmilp_fix5_ercot_2019/"
GAS = ["CC_REGULAR", "CC_CHP", "ST_GAS"]
R: dict = {}


def lw(b: str) -> pd.DataFrame:
    """Hourly load-weighted P1 price frame (the C3a basis)."""
    s = pd.read_parquet(b + "hourly/system_2019.parquet")
    s = s[s["pass"] == "P1"].assign(pd_=lambda d: d.price * d.demand)
    return s.groupby("hour")[["pd_", "demand"]].sum()


gk, gu = lw(K), lw(U)
D = gk.demand.sum()
h = pd.DataFrame({"pk": gk.pd_ / gk.demand, "pu": gu.pd_ / gu.demand, "c": (gu.pd_ - gk.pd_) / D})
R["lw_mean"] = {"keeper": gk.pd_.sum() / D, "uc": gu.pd_.sum() / gu.demand.sum(), "delta": h.c.sum()}

cols = ["unit_id", "plant_group", "hour", "mw", "cap_mw", "mc", "marginal"]
um = {}
for n, b in (("keeper", K), ("uc", U)):
    u = pd.read_parquet(b + "hourly/unit_marginal_2019.parquet", columns=cols)
    u["pg"] = u.plant_group.astype(str)
    u["tr"] = u.unit_id.astype(str).str.extract(r"_(committed|econc|peak|mustrun)")[0].fillna("other").values
    m = u[u.marginal == 1]
    top = m.sort_values("mc").groupby("hour").tail(1).set_index("hour")
    h[n[0] + "_mcls"], h[n[0] + "_mmc"] = top.pg, top.mc
    R.setdefault("marginal_hours", {})[n] = (
        {f"{a}/{b}": int(v) for (a, b), v in m.groupby(["pg", "tr"]).size().sort_values(ascending=False).head(12).items()}
    )
    R.setdefault("peak_tranche_twh", {})[n] = (u[u.tr == "peak"].groupby("pg").mw.sum() / 1e6).round(3).to_dict()
    R.setdefault("class_twh", {})[n] = (u.groupby("pg").mw.sum() / 1e6).round(2).to_dict()
    um[n] = u[u.pg.isin(GAS)][["unit_id", "pg", "hour", "cap_mw", "mc"]]
h = h.fillna({"k_mcls": "none", "u_mcls": "none"})

m = um["keeper"].merge(um["uc"][["unit_id", "hour", "cap_mw", "mc"]], on=["unit_id", "hour"], suffixes=("_k", "_u"))
m["off"] = (m.cap_mw_k - m.cap_mw_u).clip(lower=0)
m = m.merge(h[["pu"]], left_on="hour", right_index=True)
m["cheap_off"] = np.where(m.mc_u < m.pu - 0.01, m.off, 0.0)
h = h.join(m.groupby("hour")[["off", "cheap_off"]].sum())
R["offline_gw_mean_by_class"] = (m.groupby("pg").off.sum() / 8760 / 1e3).round(2).to_dict()

h["bucket"] = np.where(h.pu > 200, "A_scarcity_gt200",
                       np.where(h.cheap_off >= 500, "D_uc_offline_below_price_ge_0.5GW", "E_other"))
R["buckets"] = h.groupby("bucket").apply(
    lambda g: {"hours": len(g), "contrib_usd_mwh": g.c.sum(), "mean_dp": (g.pu - g.pk).mean(), "keeper_gt200": int((g.pk > 200).sum())}
).to_dict()
h["ch"] = np.where(h.pu > 200, "scarcity_gt200", np.where(h.u_mcls == h.k_mcls, "same_class_dearer_step", "class_switch"))
R["channels"] = h.groupby("ch").apply(lambda g: {"hours": len(g), "contrib_usd_mwh": g.c.sum()}).to_dict()
lo = h[h.pu <= 200]
bins = pd.cut(lo.cheap_off / 1e3, [-1, 0.5, 1, 2, 4, 100])
R["dp_by_offline_gw"] = {str(k): {"hours": len(g), "mean_dp": (g.pu - g.pk).mean(), "contrib": g.c.sum()}
                         for k, g in lo.groupby(bins, observed=True)}
cc = h[(h.k_mcls == "CC_REGULAR") & (h.u_mcls == "CC_REGULAR")]
R["cc_to_cc_marginal_mc"] = {"hours": len(cc), "keeper": float(cc.k_mmc.mean()), "uc": float(cc.u_mmc.mean())}

# UC online fraction vs CEMS (cap-weighted; on = opTime > 0 and grossLoad > 0)
L = json.load(open(U + "uc_solve_log_2019.json"))
c = pd.DataFrame(L["clusters"]); c = c[c.integer]
s = pd.read_parquet(U + "hourly/uc_schedule_2019.parquet"); s = s[s.cluster.isin(set(c.cluster))]
s["cap"] = c.set_index("cluster").loc[s.cluster, "pbar_mw"].values * s.n.values
s["oncap"] = s.cap * s.u / s.n
cm = pd.read_parquet("data/raw/campd-unit-level/TX_2019.parquet",
                     columns=["facilityId", "unitId", "date", "hour", "opTime", "grossLoad"])
cm["plant"] = pd.to_numeric(cm.facilityId, errors="coerce")
cm = cm[cm.plant.isin(set(c.plant_code))]
cm["hoy"] = ((cm.date - pd.Timestamp("2019-01-01")).dt.days * 24 + cm.hour).astype(int)
cm = cm.join(cm.groupby(["plant", "unitId"]).grossLoad.quantile(0.99).rename("ucap"), on=["plant", "unitId"])
cm["oncap"] = cm.ucap * ((cm.opTime.fillna(0) > 0) & (cm.grossLoad.fillna(0) > 0))
p = cm.groupby(["plant", "hoy"]).agg(oncap=("oncap", "sum"), cap=("ucap", "sum")).reset_index()
p["frac_cems"] = p.oncap / p.cap
for cls in ("cc", "st_gas"):
    sp = s[s.plant_code.isin(set(c[c.uc_class == cls].plant_code))]
    f = sp.groupby(["plant_code", "hour"]).agg(oncap=("oncap", "sum"), cap=("cap", "sum")).reset_index()
    f["frac_uc"] = f.oncap / f.cap
    f = f.merge(p.rename(columns={"plant": "plant_code", "hoy": "hour"})[["plant_code", "hour", "frac_cems"]],
                on=["plant_code", "hour"], how="left")
    cov = float(f.frac_cems.notna().mean()); f = f.dropna()
    wavg = lambda g, col: float((g[col] * g.cap).sum() / g.cap.sum())  # noqa: E731
    hod = f.assign(hod=f.hour % 24).groupby("hod")
    R.setdefault("online_frac_vs_cems", {})[cls] = {
        "cems_coverage": cov, "uc": wavg(f, "frac_uc"), "cems": wavg(f, "frac_cems"),
        "uc_by_hod": [round(wavg(g, "frac_uc"), 3) for _, g in hod],
        "cems_by_hod": [round(wavg(g, "frac_cems"), 3) for _, g in hod],
    }

up = pd.read_parquet(U + "hourly/uc_uplift_2019.parquet")
g = up.groupby("uc_class")[["energy_mwh", "energy_cost_usd", "noload_usd", "start_usd"]].sum()
R["noload"] = {k: {"noload_usd": v.noload_usd, "share_of_energy_cost": v.noload_usd / v.energy_cost_usd,
                   "usd_per_mwh": v.noload_usd / v.energy_mwh} for k, v in g.iterrows()}

json.dump(R, open(OUT, "w"), indent=1, default=float)
print(json.dumps(R, indent=1, default=float)[:6000])
