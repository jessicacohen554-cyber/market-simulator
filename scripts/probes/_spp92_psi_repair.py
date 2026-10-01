"""SPP-92 (zero LP): SPP-53's ψ / T* construction re-run with the bubble-average spread and the GMT clock.

Pre-declared in docs/records/spp/spp92/PREDECLARE-psi-repair.md (committed before this ran). Spec is SPP-53's
(docs/records/spp/spp53/{parse_2325,psi_regression,aggregate_ttc}.py); L_f from SPP-53's committed tables.
Needs the bubble hourly files from scripts/probes/_spp92_bubble_spread.py.
"""
import glob, re, zipfile, importlib.util, sys
import numpy as np, pandas as pd

ROOT = "/home/user/market-simulator"; R = f"{ROOT}/data/raw/spp-binding-constraints"; D53 = f"{ROOT}/docs/records/spp/spp53"
spec = importlib.util.spec_from_file_location("g", f"{ROOT}/scripts/probes/_spp92_seam_probe.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def hoy_from(t):
    doy = t.dt.dayofyear.values.copy(); leap = t.dt.is_leap_year.values
    feb29 = leap & (t.dt.month.values == 2) & (t.dt.day.values == 29)
    doy = np.where(leap & (doy > 59), doy - 1, doy)
    return np.where(feb29, -1, (doy - 1) * 24 + t.dt.hour.values), t.dt.year.values

def parse(clock):
    files = [f"{R}/RTBM-BC-YEARLY-2023.csv.zip", f"{R}/RTBM-BC-YEARLY-2024.csv.zip"] + sorted(glob.glob(f"{R}/RTBM-BC-MONTHLY-2025*.csv.zip"))
    frames, meta = [], []
    for f in files:
        z = zipfile.ZipFile(f); df = pd.read_csv(z.open(z.namelist()[0]), usecols=["Interval","GMTIntervalEnd","Constraint Name","State","Shadow Price","Monitored Facility","Contingent Facility"], dtype={"Shadow Price": float})
        if clock == "local":
            t = pd.to_datetime(df["Interval"], format="mixed") - pd.Timedelta(minutes=1)
        else:
            t = pd.to_datetime(df["GMTIntervalEnd"], format="mixed") - pd.Timedelta(minutes=1) - pd.Timedelta(hours=6)
        df["hoy"], df["year"] = hoy_from(t)
        niv = df.drop_duplicates(["year","hoy","GMTIntervalEnd"]).groupby(["year","hoy"]).size().rename("n_iv")
        b = df[df.State.eq("BINDING") & (df.hoy >= 0) & df.year.between(2023, 2025)].copy(); b["asp"] = b["Shadow Price"].abs()
        hs = b.groupby(["year","hoy","Constraint Name"])["asp"].sum().reset_index().join(niv, on=["year","hoy"]); hs["mean_asp"] = hs.asp / hs.n_iv
        frames.append(hs[["year","hoy","Constraint Name","mean_asp"]])
        meta.append(b.groupby("Constraint Name").agg(hours=("hoy", lambda s: s.nunique()), mon=("Monitored Facility", lambda s: s.mode().iat[0]), con=("Contingent Facility", lambda s: s.mode().iat[0])).reset_index())
    H = pd.concat(frames)
    M = pd.concat(meta).groupby("Constraint Name").agg(hours=("hours","sum"), mon=("mon", lambda s: s.mode().iat[0]), con=("con", lambda s: s.mode().iat[0])).reset_index()
    M["Monitored Facility"] = M.mon; M["Contingent Facility"] = M.con
    M["group"] = [g.group(a, b, g.tokens(c)) for a, b, c in M[["Constraint Name","Monitored Facility","Contingent Facility"]].itertuples(index=False)]
    return H, M

def spread(kind):
    out = []
    for y in (2023, 2024, 2025):
        d = pd.read_parquet(f"{ROOT}/results/calibration/_spp92_seam_hourly_bubble_{y}.parquet")
        s = (d.hS - d.hN) if kind == "hub" else (d.bS - d.bN)
        out.append(pd.DataFrame({"year": y, "hoy": d.index, "spread": s.values}))
    return pd.concat(out).set_index(["year","hoy"])["spread"]

def psi(H, M, y):
    keep = M[M.hours >= 263]["Constraint Name"].tolist()
    W = H[H["Constraint Name"].isin(keep)].pivot_table(index=["year","hoy"], columns="Constraint Name", values="mean_asp", aggfunc="sum", fill_value=0.0)
    D = W.join(y.rename("spread"), how="right").dropna(subset=["spread"]).fillna(0.0)
    cols = list(W.columns); X = np.column_stack([np.ones(len(D)), D[cols].values]); yv = D["spread"].values
    n, k = X.shape; Xi = np.linalg.pinv(X.T @ X); beta = Xi @ X.T @ yv; e = yv - X @ beta
    cov = Xi @ ((X * e[:, None] ** 2).T @ X) @ Xi * (n / (n - k)); t = beta / np.sqrt(np.diag(cov))
    res = pd.DataFrame({"Constraint Name": ["_intercept"] + cols, "psi": beta, "t": t}).merge(M, on="Constraint Name", how="left")
    res["identified"] = (res.psi > 0) & (res.t >= 2.0) & (res.psi <= 1.0)
    return res, 1 - e.var() / yv.var(), n

def key(s):
    s = str(s).upper(); s = re.sub(r"^(XFMR|XF|LN)\s+", "", s); s = re.sub(r"\s+\d+(/\d+)?\s*KV$", "", s)
    a = [re.sub(r"\d+$", "", x.strip()) for x in s.split(" - ")]
    if len(a) == 1: return a[0]
    if len(a) == 2 and a[0] == a[1]: return a[0]
    return " - ".join(sorted(a)) if len(a) == 2 else s

def tstar(res):
    """SPP-53 aggregate_ttc.py L_f lookup verbatim (archive by name >=100 binds, else by element, else registry)."""
    lim = pd.read_csv(f"{D53}/limits_2026_by_constraint.csv"); xc = pd.read_csv(f"{D53}/registry_xcheck.csv")
    lim["k"] = lim["Monitored Facility"].map(key)
    by_name = lim.set_index("Constraint Name")
    by_elem = lim.groupby("k").agg(n_bind=("n_bind","sum"), rtel_med=("rtel_med","median"))
    c = res[res.group.eq("n_s_corridor")].copy(); c["k"] = c["Monitored Facility"].map(key); rows = []
    for _, r in c.iterrows():
        n = r["Constraint Name"]; L = np.nan
        if n in by_name.index and by_name.loc[n, "n_bind"] >= 100: L = by_name.loc[n, "rtel_med"]
        elif r.k in by_elem.index and by_elem.loc[r.k, "n_bind"] >= 100: L = by_elem.loc[r.k, "rtel_med"]
        else:
            y = xc[xc["Constraint Name"].eq(n)]
            if len(y):
                y = y.iloc[0]
                if pd.notna(y.temp_norm): L = y.temp_norm
                elif pd.notna(y.perm_normal_mean): L = y.perm_normal_mean
                elif isinstance(y.elem_temp_norm_range, str) and y.elem_temp_norm_range != "None": L = float(re.findall(r"\((\d+\.?\d*)", y.elem_temp_norm_range)[0])
                elif isinstance(y.elem_perm_normal_range, str) and y.elem_perm_normal_range != "None": L = float(re.findall(r"\((\d+\.?\d*)", y.elem_perm_normal_range)[0])
        rows.append({"name": n, "mon": r["Monitored Facility"], "hours": r.hours, "psi": r.psi, "t": r.t, "identified": r.identified, "L": L,
                     "T": L / r.psi if (r.identified and pd.notna(L)) else np.nan})
    O = pd.DataFrame(rows); I = O[O.identified & O["T"].notna()].sort_values("T")
    if len(I) < 3: return O, None, len(I)
    cw = np.cumsum(I.hours.values) / I.hours.sum()
    q = lambda p: float(I["T"].values[np.searchsorted(cw, p)])
    return O, (q(.25), q(.5), q(.75)), len(I)

if __name__ == "__main__":
    out = {}
    for clock in ("local", "gmt"):
        H, M = parse(clock)
        for kind in ("hub", "bubble"):
            res, r2, n = psi(H, M, spread(kind)); O, qs, nid = tstar(res)
            cor = res[res.group.eq("n_s_corridor") & (res.hours >= 263)]
            out[f"{clock}/{kind}"] = {"n": n, "R2": round(r2, 3), "corridor_constituents": len(cor), "identified_NtoS": int(cor.identified.sum()),
                "StoN_loaded": int(((cor.psi < 0) & (cor.t <= -2)).sum()), "identified_with_L": nid,
                "T_p25_p50_p75": [round(x) for x in qs] if qs else None, "TTC_rounded": round(qs[1], -2) if qs else None}
            O.sort_values("hours", ascending=False).to_csv(f"{ROOT}/docs/records/spp/spp92/tstar_{clock}_{kind}.csv", index=False)
            print(clock, kind, out[f"{clock}/{kind}"], flush=True)
    import json; json.dump(out, open(f"{ROOT}/docs/records/spp/spp92/psi_repair.json", "w"), indent=1)
