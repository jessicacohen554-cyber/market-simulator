"""SPP-93 (zero LP): the W↔E link rating, PRECOMMIT-spp-93 §2. SPP-53's construction (A), FCITC.

Reuses SPP-92's ``_spp92_psi_repair.py`` mechanics:
- GMT clock, 2023-25;
- regressors = the mean |shadow| of every constraint with >= 263 binding hours;
- OLS with HC1.

What changes, as declared in PRECOMMIT §2:
- the spread is the ACTUAL East-bubble - West-bubble price (``_spp93_we_spread.py`` hourly output);
- the constituent set is ``n_s_corridor`` ∪ ``sps_tie``;
- L_f is looked up in SPP-53's order over SPP-53's + SPP-57's limit tables and SPP-53's registry xcheck.

Identified = psi > 0, t >= 2, psi <= 1; T* = L / psi; TTC = binding-hours-weighted median, nearest 100 MW.
R1: < 3 identified with L. R4: p75/p25 > 10. R2/R3 are graded against the census bounds.

Usage: ``python scripts/probes/_spp93_psi_we.py <dir with we_hourly_<y>.parquet> <out dir>``
"""
import importlib.util
import json
import re
import sys

import numpy as np
import pandas as pd

ROOT = "/home/user/market-simulator"
D53 = f"{ROOT}/docs/handoffs/spp53"
D57 = f"{ROOT}/docs/handoffs/spp57"
_spec = importlib.util.spec_from_file_location("r92", f"{ROOT}/scripts/probes/_spp92_psi_repair.py")
r92 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r92)
SET = ("n_s_corridor", "sps_tie")


def spread(d):
    """Hourly actual East - West bubble spread, 2023-25."""
    out = []
    for y in (2023, 2024, 2025):
        b = pd.read_parquet(f"{d}/we_hourly_{y}.parquet")
        out.append(pd.DataFrame({"year": y, "hoy": b.hour.values, "spread": (b.E - b.W).values}))
    return pd.concat(out).set_index(["year", "hoy"])["spread"]


def tstar(res):
    """T* over the declared set; L_f in SPP-53's order over the SPP-53 ∪ SPP-57 limit tables."""
    lim = pd.concat([pd.read_csv(f"{D53}/limits_2026_by_constraint.csv"),
                     pd.read_csv(f"{D57}/limits_2026_oklahoma_by_constraint.csv")], ignore_index=True)
    lim = lim.sort_values("n_bind", ascending=False).drop_duplicates("Constraint Name")
    xc = pd.read_csv(f"{D53}/registry_xcheck.csv")
    lim["k"] = lim["Monitored Facility"].map(r92.key)
    by_name = lim.set_index("Constraint Name")
    by_elem = lim.groupby("k").agg(n_bind=("n_bind", "sum"), rtel_med=("rtel_med", "median"))
    c = res[res.group.isin(SET)].copy()
    c["k"] = c["Monitored Facility"].map(r92.key)
    rows = []
    for _, r in c.iterrows():
        n = r["Constraint Name"]
        L, src = np.nan, ""
        if n in by_name.index and by_name.loc[n, "n_bind"] >= 100:
            L, src = by_name.loc[n, "rtel_med"], "archive_name"
        elif r.k in by_elem.index and by_elem.loc[r.k, "n_bind"] >= 100:
            L, src = by_elem.loc[r.k, "rtel_med"], "archive_elem"
        else:
            y = xc[xc["Constraint Name"].eq(n)]
            if len(y):
                y = y.iloc[0]
                if pd.notna(y.temp_norm):
                    L, src = y.temp_norm, "registry"
                elif pd.notna(y.perm_normal_mean):
                    L, src = y.perm_normal_mean, "registry"
                elif isinstance(y.elem_temp_norm_range, str) and y.elem_temp_norm_range != "None":
                    L, src = float(re.findall(r"\((\d+\.?\d*)", y.elem_temp_norm_range)[0]), "registry"
                elif isinstance(y.elem_perm_normal_range, str) and y.elem_perm_normal_range != "None":
                    L, src = float(re.findall(r"\((\d+\.?\d*)", y.elem_perm_normal_range)[0]), "registry"
        rows.append({"name": n, "group": r.group, "mon": r["Monitored Facility"], "hours": r.hours, "psi": r.psi,
                     "t": r.t, "identified": r.identified, "L": L, "L_src": src,
                     "T": L / r.psi if (r.identified and pd.notna(L)) else np.nan})
    O = pd.DataFrame(rows)
    identified_total = int(O.identified.sum())
    I = O[O.identified & O["T"].notna()].sort_values("T")
    if len(I) < 3:
        return O, None, len(I), identified_total
    cw = np.cumsum(I.hours.values) / I.hours.sum()

    def q(p):
        return float(I["T"].values[np.searchsorted(cw, p)])

    return O, (q(.25), q(.5), q(.75)), len(I), identified_total


def main():
    """Fit ψ on the E-W spread, aggregate T*, write the table and a JSON verdict."""
    src, out = sys.argv[1], sys.argv[2]
    H, M = r92.parse("gmt")
    res, r2, n = r92.psi(H, M, spread(src))
    O, qs, nid, nident = tstar(res)
    cand = res[res.group.isin(SET) & (res.hours >= 263)]
    v = {"n_hours": n, "R2": round(r2, 3), "constituents": int(len(cand)),
         "identified_WtoE": nident, "EtoW_loaded": int(((cand.psi < 0) & (cand.t <= -2)).sum()),
         "identified_with_L": nid, "T_p25_p50_p75": [round(x) for x in qs] if qs else None,
         "TTC": round(qs[1], -2) if qs else None,
         "R1_pass": nid >= 3, "R4_pass": bool(qs and qs[2] / qs[0] <= 10)}
    O.sort_values("hours", ascending=False).to_csv(f"{out}/tstar_we.csv", index=False)
    json.dump(v, open(f"{out}/psi_we.json", "w"), indent=1)
    print(v)
    print(O[O.identified].sort_values("hours", ascending=False).to_string())


if __name__ == "__main__":
    main()
