"""UC-SPP-CORRIDOR: per-year N->S link from SPP's own in-window effective limits.

Re-runs the SPP-53 construction (FINDING-spp-53 §0, PRECOMMIT-spp-53 §2) with
one input changed: L_f, the constituent's limit-at-bind, is taken from the
year's OWN RTBM effective limits (clean `flowgate-limits-at-bind`, SPP portal
`effective-limits`, 2022-04-14 on) instead of the 2026 archive / registry.
psi_f, the identified constituents and the aggregation (binding-hours-weighted
median of T*_f = L_f / psi_f) are SPP-53's, unchanged and not re-fit.

Usage: python docs/records/spp/uc-corridor/corridor_limits.py <out_dir>
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from scripts.lib import clean_io  # noqa: E402

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
YEARS = [int(y) for y in (sys.argv[2:] or ["2022", "2023", "2024", "2025"])]
T53 = pd.read_csv(REPO / "docs/records/spp/spp53/tstar_table.csv")
IDENT = T53[T53.identified].copy()


def key(s):
    """SPP-53's monitored-facility element key (aggregate_ttc.py, verbatim)."""
    s = str(s).upper(); s = re.sub(r"^(XFMR|XF|LN)\s+", "", s); s = re.sub(r"\s+\d+(/\d+)?\s*KV$", "", s)
    a = [re.sub(r"\d+$", "", x.strip()) for x in s.split(" - ")]
    if len(a) == 1: return a[0]
    if len(a) == 2 and a[0] == a[1]: return a[0]
    return " - ".join(sorted(a)) if len(a) == 2 else s


IDENT["k"] = IDENT["Monitored Facility"].map(key)
frames = []
for y in YEARS:
    d = clean_io.read_clean("flowgate-limits-at-bind", iso="SPP", year=y, market="rt")
    d["year"] = y; frames.append(d)
D = pd.concat(frames, ignore_index=True)
D["k"] = D.monitored_facility.map(key)
D["season"] = D.hour_start_utc.dt.month.map(lambda m: "summer" if 6 <= m <= 9 else ("winter" if m in (12, 1, 2) else "shoulder"))
D["derated"] = D.effective_limit_mw < D.source_limit_mw - 1e-9

rows = []
for _, c in IDENT.iterrows():
    for y in YEARS:
        x = D[(D.year == y) & (D.constraint_name == c["Constraint Name"])]; match = "same Constraint Name"
        if len(x) < 1:
            x = D[(D.year == y) & (D.k == c.k)]; match = "same Monitored Facility"
        h = len(x)
        rows.append({
            "constraint": c["Constraint Name"], "monitored": c["Monitored Facility"], "psi": c.psi,
            "hours_pooled_2325": int(c.hours), "L_spp53": c.L_f, "L_spp53_source": c.L_source, "year": y,
            "match": match if h else "did not bind", "bind_hours": h,
            "L_eff_med": float(x.effective_limit_mw.median()) if h else np.nan,
            "L_eff_p10": float(x.effective_limit_mw.quantile(.1)) if h else np.nan,
            "L_eff_p90": float(x.effective_limit_mw.quantile(.9)) if h else np.nan,
            "L_src_med": float(x.source_limit_mw.median()) if h else np.nan,
            "derate_share": float(x.derated.mean()) if h else np.nan,
        })
C = pd.DataFrame(rows)
C["T_star_y"] = C.L_eff_med / C.psi
C["T_star_spp53"] = C.L_spp53 / C.psi
C.to_csv(OUT / "constituent_limits_by_year.csv", index=False)


def wmed(v, w):
    """Weighted median (SPP-53's searchsorted convention)."""
    o = np.argsort(v); v, w = np.asarray(v)[o], np.asarray(w, float)[o]
    cw = np.cumsum(w) / w.sum()
    return float(v[np.searchsorted(cw, 0.5)]), float(v[np.searchsorted(cw, 0.25)]), float(v[np.searchsorted(cw, 0.75)])


agg = []
for y in YEARS:
    x = C[(C.year == y) & C.T_star_y.notna()]
    if x.empty: continue
    m, p25, p75 = wmed(x.T_star_y, x.bind_hours)                 # (A) own limits, own-year hours
    mb, _, _ = wmed(x.T_star_y, x.hours_pooled_2325)            # (B) own limits, SPP-53 hours
    # (C) SPP-53 limits where the constituent did not bind this year (fill), own-year limits otherwise
    z = C[C.year == y].copy(); z["T"] = z.T_star_y.fillna(z.T_star_spp53)
    mc, _, _ = wmed(z["T"], z.hours_pooled_2325)
    agg.append({"year": y, "n_constituents_bound": len(x), "bind_hours_sum": int(x.bind_hours.sum()),
                "TTC_own_limits_own_hours": m, "p25": p25, "p75": p75,
                "TTC_own_limits_spp53_hours": mb, "TTC_mixed_fill_spp53": mc,
                "franklin_hours_share": float(x[x.monitored.str.contains("FRANKLN5")].bind_hours.sum() / x.bind_hours.sum())})
A = pd.DataFrame(agg); A.to_csv(OUT / "ttc_by_year.csv", index=False)

# season split over the pooled in-window years (own limits, own hours)
S = []
for s in ("winter", "shoulder", "summer"):
    for y in YEARS:
        rr = []
        for _, c in IDENT.iterrows():
            x = D[(D.year == y) & (D.season == s) & (D.constraint_name == c["Constraint Name"])]
            if x.empty:  # same match rule as the annual table: name first, then element
                x = D[(D.year == y) & (D.season == s) & (D.k == c.k)]
            if len(x): rr.append((float(x.effective_limit_mw.median()) / c.psi, len(x)))
        if rr:
            m, p25, p75 = wmed([r[0] for r in rr], [r[1] for r in rr])
            S.append({"year": y, "season": s, "n": len(rr), "hours": sum(r[1] for r in rr), "TTC": m, "p25": p25, "p75": p75})
pd.DataFrame(S).to_csv(OUT / "ttc_by_year_season.csv", index=False)

pd.set_option("display.width", 250)
print(C[["constraint", "monitored", "psi", "year", "match", "bind_hours", "L_spp53", "L_eff_med", "L_eff_p10", "L_eff_p90", "L_src_med", "derate_share", "T_star_spp53", "T_star_y"]].round(3).to_string(index=False))
print(A.round(1).to_string(index=False))
print(pd.DataFrame(S).round(0).to_string(index=False))
