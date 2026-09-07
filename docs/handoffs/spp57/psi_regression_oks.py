"""SPP-57 leg 2 for the OK<->S link: psi_f from (p_S - p_OK) regressed on every constraint's
hourly mean |shadow price| (>= 263 pooled binding hours, all four groups, + intercept), OLS + HC1,
leave-one-year-out — PRECOMMIT-spp-53 §2.1's specification with the PRECOMMIT-spp-57 §3.2
dependent. Also re-runs the N<->OK regression (p_OK - p_N) on the same sample to confirm it
reproduces spp53/psi_all.csv (the reused leg)."""

import sys

import numpy as np
import pandas as pd

S = sys.argv[1]
H = pd.read_parquet(f"{S}/bc/hourly_asp_2325.parquet")
M = pd.read_parquet(f"{S}/bc/constraints_2325.parquet")
keep = M[M.hours >= 263]["Constraint Name"].tolist()
W = H[H["Constraint Name"].isin(keep)].pivot_table(
    index=["year", "hoy"], columns="Constraint Name", values="mean_asp", aggfunc="sum", fill_value=0.0
)
L = pd.read_parquet("/home/user/market-simulator/data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet")
P = L.pivot_table(index=["year", "hour"], columns="zone", values="rt")
P.index.names = ["year", "hoy"]
A = pd.read_parquet("/home/user/market-simulator/data/raw/_validation-source/actual_lmp_hourly_area_SPP.parquet")
A = A.set_index(["year", "hour"])
A.index.names = ["year", "hoy"]
dep = {
    "n_ok": (P["SPPSOUTH_HUB"] - P["SPPNORTH_HUB"]).rename("spread"),
    "ok_s": (A["p_s"] - P["SPPSOUTH_HUB"]).rename("spread"),
}


def ols_hc1(X, y):
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    e = y - X @ beta
    meat = (X * e[:, None] ** 2).T @ X
    cov = XtX_inv @ meat @ XtX_inv * (n / (n - k))
    se = np.sqrt(np.diag(cov))
    return beta, se, beta / se, 1 - e.var() / y.var(), n, k


pd.set_option("display.width", 260)
for link, y in dep.items():
    D = W.join(y, how="right").dropna(subset=["spread"]).fillna(0.0)
    cols = list(W.columns)
    X = np.column_stack([np.ones(len(D)), D[cols].values])
    yv = D["spread"].values
    beta, se, t, r2, n, k = ols_hc1(X, yv)
    res = pd.DataFrame({"Constraint Name": ["_intercept"] + cols, "psi": beta, "se": se, "t": t}).merge(
        M, on="Constraint Name", how="left"
    )
    res["identified"] = (res.psi > 0) & (res.t >= 2.0) & (res.psi <= 1.0)
    res["reverse"] = (res.psi < 0) & (res.t <= -2.0) & (res.psi >= -1.0)
    for yr in (2023, 2024, 2025):
        m = D.index.get_level_values("year") != yr
        bl = np.linalg.pinv(X[m].T @ X[m]) @ X[m].T @ yv[m]
        res[f"psi_drop{yr}"] = np.concatenate([[bl[0]], bl[1:]])
    res.to_csv(f"{S}/bc/psi_{link}.csv", index=False)
    print(f"\n===== {link}: n={n} k={k} R2={r2:.3f} intercept={beta[0]:.3f} (t={t[0]:.1f}); "
          f"mean dependent {yv.mean():+.3f}")
    for g in ("n_s_corridor", "oklahoma_internal", "sps_tie", "other"):
        x = res[res.group.eq(g)]
        print(f"  {g}: n={len(x)} identified(psi>0,t>=2)={int(x.identified.sum())} "
              f"reverse(psi<0,t<=-2)={int(x.reverse.sum())} hours id={int(x[x.identified].hours.sum())} "
              f"hours rev={int(x[x.reverse].hours.sum())}")
    show = res[res.group.isin(["oklahoma_internal", "sps_tie"]) | res.why.eq("other areas: CSWS")]
    show = show.sort_values("hours", ascending=False)
    print(show[["Constraint Name", "Monitored Facility", "group", "why", "hours", "psi", "t",
                "identified", "reverse"]].head(45).to_string(index=False, max_colwidth=40))
# reuse check: does n_ok reproduce spp53/psi_all.csv?
old = pd.read_csv("/home/user/market-simulator/docs/handoffs/spp53/psi_all.csv")
new = pd.read_csv(f"{S}/bc/psi_n_ok.csv")
j = old.merge(new, on="Constraint Name", suffixes=("_53", "_57"))
print("\nN<->OK reuse check vs spp53/psi_all.csv: rows", len(j), "max |psi diff|",
      float((j.psi_53 - j.psi_57).abs().max()), "max |t diff|", float((j.t_53 - j.t_57).abs().max()))
