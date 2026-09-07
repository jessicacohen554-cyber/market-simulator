"""SPP-57 PRECOMMIT §3.2 aggregation for BOTH links: T*_f = L_f / psi_f over the identified
constituents of each link's membership set; the binding-hours-weighted median in the link's
data-named direction; the reverse reading; R1-R4. The corridor constituents of the N<->OK link
keep SPP-53's committed L_f (spp53/tstar_table.csv); every other constituent's L_f comes from the
new Oklahoma sidecar's limit-at-bind table (limits_2026_oklahoma_by_constraint.csv), else the
registry rating by the SPP-53 join order."""

import re
import sys

import numpy as np
import pandas as pd

S = sys.argv[1]
REPO = "/home/user/market-simulator"
psi_nok = pd.read_csv(f"{S}/bc/psi_n_ok.csv")
psi_oks = pd.read_csv(f"{S}/bc/psi_ok_s.csv")
lim53 = pd.read_csv(f"{REPO}/docs/handoffs/spp53/tstar_table.csv")
lim = pd.read_csv(f"{S}/bc/limits_2026_oklahoma_by_constraint.csv")
fg = pd.read_csv(f"{REPO}/data/raw/spp-binding-constraints/Flowgates.csv", dtype=str)
tfg = pd.read_csv(f"{REPO}/data/raw/spp-binding-constraints/Temp_Flowgate.csv", dtype=str)


def key(s):
    s = str(s).upper()
    s = re.sub(r"^(XFMR|XF|LN)\s+", "", s)
    s = re.sub(r"\s+\d+(/\d+)?\s*KV$", "", s)
    a = [re.sub(r"\d+$", "", x.strip()) for x in s.split(" - ")]
    if len(a) == 1:
        return a[0]
    if len(a) == 2 and a[0] == a[1]:
        return a[0]
    return " - ".join(sorted(a)) if len(a) == 2 else s


lim["k"] = lim["Monitored Facility"].map(key)
lim_by_name = lim.groupby("Constraint Name").agg(n_bind=("n_bind", "sum"), rtel_med=("rtel_med", "median"),
                                                  rtel_p10=("rtel_p10", "min"), rtel_p90=("rtel_p90", "max"),
                                                  src_med=("src_med", "median"))
lim_by_elem = lim.groupby("k").agg(n_bind=("n_bind", "sum"), rtel_med=("rtel_med", "median"),
                                   rtel_p10=("rtel_p10", "min"), rtel_p90=("rtel_p90", "max"),
                                   src_med=("src_med", "median"), names=("Constraint Name", lambda s: "|".join(s)))
# registry ratings (column names verified on the landed CSVs: Flowgates.csv has
# "Flowgate", "ElementType", "Element" and the eight seasonal Normal/Emergency
# columns; Temp_Flowgate.csv has "Flowgate", "ElementType", "Element", "NormLimit")
tfg_norm = tfg.assign(v=pd.to_numeric(tfg["NormLimit"], errors="coerce"))
tfg_norm = tfg_norm[tfg_norm["ElementType"].astype(str).str.strip().eq("Monitored")]
tfg_by_name = tfg_norm.groupby("Flowgate")["v"].median()
seas = ["Spring Normal", "Summer Normal", "Fall Normal", "Winter Normal"]
fg_norm = fg.assign(v=fg[seas].apply(pd.to_numeric, errors="coerce").mean(axis=1))
mon_fg = fg_norm[fg_norm["ElementType"].astype(str).str.strip().eq("Monitored")]
fg_by_name = mon_fg.groupby("Flowgate")["v"].mean()


def registry_L(name):
    if name in tfg_by_name.index and pd.notna(tfg_by_name[name]):
        return float(tfg_by_name[name]), "registry Temp_Flowgate NormLimit"
    if name in fg_by_name.index and pd.notna(fg_by_name[name]):
        return float(fg_by_name[name]), "registry Flowgates seasonal Normal mean"
    return np.nan, "none"


def L_for(row, corridor_first):
    n = row["Constraint Name"]
    if corridor_first:
        m = lim53[lim53["Constraint Name"].eq(n)]
        if len(m) and pd.notna(m.iloc[0]["L_f"]):
            r = m.iloc[0]
            return float(r["L_f"]), "SPP-53 committed (" + str(r["L_source"]) + ")", int(r["n_bind_2026"]), r["rtel_p10"], r["rtel_p90"], r["src_med"]
    if n in lim_by_name.index and lim_by_name.loc[n, "n_bind"] >= 100:
        x = lim_by_name.loc[n]
        return float(x.rtel_med), "2026 archive (same Constraint Name)", int(x.n_bind), x.rtel_p10, x.rtel_p90, x.src_med
    k = key(row["Monitored Facility"])
    if k in lim_by_elem.index and lim_by_elem.loc[k, "n_bind"] >= 100:
        x = lim_by_elem.loc[k]
        return float(x.rtel_med), "2026 archive (same Monitored Facility: " + x.names + ")", int(x.n_bind), x.rtel_p10, x.rtel_p90, x.src_med
    L, src = registry_L(n)
    return L, src, 0, np.nan, np.nan, np.nan


def wq(I, q):
    I = I.sort_values("T_star")
    w = I.hours.values
    cw = np.cumsum(w) / w.sum()
    return float(I.T_star.values[np.searchsorted(cw, q)])


pd.set_option("display.width", 320)
out_tables = {}
for link, psi, members, corridor_first in (
    ("N<->OK (+ = N->OK)", psi_nok,
     lambda r: r.group in ("n_s_corridor", "oklahoma_internal"), True),
    ("OK<->S (+ = OK->S)", psi_oks,
     lambda r: r.group in ("oklahoma_internal", "sps_tie") or r.why == "other areas: CSWS", False),
):
    c = psi[psi.apply(members, axis=1) & (psi.hours >= 263)].copy()
    c["fwd"] = (c.psi > 0) & (c.t >= 2.0) & (c.psi <= 1.0)
    c["rev"] = (c.psi < 0) & (c.t <= -2.0) & (c.psi >= -1.0)
    rows = []
    for _, r in c.iterrows():
        L, src, nb, p10, p90, srcm = L_for(r, corridor_first and r.group == "n_s_corridor")
        T = L / abs(r.psi) if (r.fwd or r.rev) and pd.notna(L) else np.nan
        rows.append({"Constraint Name": r["Constraint Name"], "Monitored Facility": r["Monitored Facility"],
                     "group": r.group, "hours": int(r.hours), "psi": r.psi, "t": r.t, "fwd": bool(r.fwd),
                     "rev": bool(r.rev), "L_f": L, "L_source": src, "n_bind_2026": nb,
                     "rtel_p10": p10, "rtel_p90": p90, "src_med": srcm, "T_star": T})
    O = pd.DataFrame(rows).sort_values("hours", ascending=False)
    tag = "n_ok" if "N<->OK" in link else "ok_s"
    O.to_csv(f"{S}/bc/tstar_{tag}.csv", index=False)
    out_tables[tag] = O
    print(f"\n================ {link}: {len(O)} members >= 263 h; fwd-identified {int(O.fwd.sum())} "
          f"({int(O[O.fwd].hours.sum())} h), rev-identified {int(O.rev.sum())} ({int(O[O.rev].hours.sum())} h), "
          f"neither {int((~O.fwd & ~O.rev).sum())} ({int(O[~O.fwd & ~O.rev].hours.sum())} h)")
    print(O[O.fwd | O.rev].drop(columns=["rtel_p10", "rtel_p90"]).to_string(index=False, max_colwidth=34))
    F = O[O.fwd & O.T_star.notna()]
    R = O[O.rev & O.T_star.notna()]
    hf, hr = int(F.hours.sum()), int(R.hours.sum())
    named = "forward" if hf >= hr else "reverse"
    for lab, I in (("forward", F), ("reverse", R)):
        if len(I) == 0:
            print(f"  {lab}: no identified constituent with an L_f")
            continue
        med, p25, p75 = wq(I, 0.5), wq(I, 0.25), wq(I, 0.75)
        print(f"  {lab}: n={len(I)} hours={int(I.hours.sum())} weighted median T* = {med:,.0f} -> {round(med, -2):,.0f} MW"
              f" | p25 {p25:,.0f} p75 {p75:,.0f} ratio {p75 / max(p25, 1e-9):.2f} | unweighted median {I.T_star.median():,.0f}"
              f" min {I.T_star.min():,.0f} max {I.T_star.max():,.0f}")
        for g, x in I.groupby("group"):
            print(f"     by group {g}: n={len(x)} hours={int(x.hours.sum())} weighted median {wq(x, 0.5):,.0f}")
        # LOYO psi
        for yr in (2023, 2024, 2025):
            col = f"psi_drop{yr}"
            ps = psi.set_index("Constraint Name")[col]
            J = I.assign(T_loyo=I.L_f / ps.reindex(I["Constraint Name"]).abs().values)
            J = J[np.isfinite(J.T_loyo) & (J.T_loyo > 0)]
            print(f"     LOYO drop {yr}: weighted median T* = {wq(J.assign(T_star=J.T_loyo), 0.5):,.0f}")
    print(f"  NAMED DIRECTION = {named} (forward {hf} h vs reverse {hr} h)")
    # R2/R3 bounds are evaluated in the FINDING with the measured w_OK.
