"""SPP-58 aggregation (PRECOMMIT §3–§4): T*_2 = L_f / psi_2 under SPP-53's rule (binding-hours-weighted
median, nearest 100), the like-for-like objects, the LOYO re-weighting spread, the band verdicts, the Potter
County width, the double-attribution re-examination, K3/K4. Reads the committed SPP-53 / SPP-57 / SPP-57b
tables verbatim (rule 23) and the psi_2 files ptdf.py wrote. Usage: aggregate_ttc_58.py <scratch>"""
import sys, json, math, numpy as np, pandas as pd
S = sys.argv[1]; R = "/home/user/market-simulator/docs/handoffs"
FLOOR = 0.005; BAND = 1.92
t53 = pd.read_csv(f"{R}/spp53/tstar_table.csv")                         # corridor: hours, psi (psi_1), t, identified, L_f, T_star
t57b = pd.read_csv(f"{R}/spp57b/tstar_ok_s_57b.csv")                    # sps_tie: hours, psi (psi_1 on p_S - p_OK), t, L_f, T_star
p_nok = pd.read_csv(f"{R}/spp57/psi_n_ok.csv"); p_oks = pd.read_csv(f"{R}/spp57/psi_ok_s.csv")
hy = pd.read_csv(f"{R}/spp58/binding_hours_by_year.csv").set_index("Constraint Name")
psi2 = {tag: pd.read_csv(f"{S}/out/psi2_by_constituent_{tag}.csv").set_index("constraint") for tag in ("x1", "x0.5", "x2", "x1_inner")}
def wmed(T, w, q=0.5):
    T = np.asarray(T, float); w = np.asarray(w, float); o = np.argsort(T); T, w = T[o], w[o]
    cw = np.cumsum(w) / w.sum(); return float(T[np.searchsorted(cw, q)])
def loyo(T, names, drop):
    w = np.array([hy.loc[n, "h_pooled"] - hy.loc[n, f"h{drop}"] for n in names], float)
    m = w > 0; return wmed(np.asarray(T)[m], w[m]) if m.sum() else np.nan
def band(t2, t1): return abs(math.log(t2 / t1)) <= math.log(BAND)
out = {}; log = []
def say(s): print(s); log.append(s)
# ---------------- per-constituent table ----------------
rows = []
for _, r in t53.iterrows():
    n = r["Constraint Name"]; p2 = psi2["x1"].loc[n] if n in psi2["x1"].index else None
    res = bool(p2 is not None and p2.get("resolved") == True)
    row = {"constraint": n, "set": "n_s_corridor", "element": r["Monitored Facility"], "class": (p2["class"] if p2 is not None else "U"), "resolved": res,
           "h_pooled": int(r.hours), "h2023": int(hy.loc[n, "h2023"]), "h2024": int(hy.loc[n, "h2024"]), "h2025": int(hy.loc[n, "h2025"]),
           "psi1": r.psi, "t1": r.t, "psi1_identified_NS": bool(r.identified), "psi1_SN": bool(r.psi < 0 and r.t <= -2),
           "psi1_drop2023": p_nok.set_index("Constraint Name").loc[n, "psi_drop2023"], "psi1_drop2024": p_nok.set_index("Constraint Name").loc[n, "psi_drop2024"], "psi1_drop2025": p_nok.set_index("Constraint Name").loc[n, "psi_drop2025"],
           "L_f": r.L_f, "L_source": r.L_source, "T1_NS": r.T_star, "T1_SN": (r.L_f / (-r.psi) if (r.psi < 0 and r.t <= -2 and pd.notna(r.L_f)) else np.nan)}
    if res:
        for k in ("P-NS", "H-NEOK", "P-NOK", "P-SS", "P-NS-wind2gas"): row[f"psi2_{k}"] = p2[f"psi2_{k}"]
        row["ptdf_P-NS"] = p2["ptdf_P-NS"]; row["otdf_P-NS"] = p2["otdf_P-NS"]; row["n_cont_modelled"] = p2["n_cont_modelled"]; row["cont_declared"] = p2["cont_declared"]
        for tag in ("x0.5", "x2", "x1_inner"): row[f"psi2_P-NS_{tag}"] = psi2[tag].loc[n, "psi2_P-NS"]
        v = p2["psi2_P-NS"]; row["psi2_identified_NS"] = bool(v >= FLOOR); row["psi2_SN"] = bool(v <= -FLOOR)
        row["T2_NS"] = r.L_f / v if v >= FLOOR else np.nan; row["T2_SN"] = r.L_f / (-v) if v <= -FLOOR else np.nan
        row["psi2_over_psi1"] = v / r.psi if r.psi else np.nan
        row["sign_agree"] = (np.sign(v) == np.sign(r.psi)) if abs(r.t) >= 2 else np.nan
    rows.append(row)
for _, r in t57b.iterrows():
    n = r["Constraint Name"]; p2 = psi2["x1"].loc[n]; v = p2["psi2_P-SS"]
    row = {"constraint": n, "set": "sps_tie", "element": r["Monitored Facility"], "class": p2["class"], "resolved": True,
           "h_pooled": int(r.hours), "h2023": int(hy.loc[n, "h2023"]), "h2024": int(hy.loc[n, "h2024"]), "h2025": int(hy.loc[n, "h2025"]),
           "psi1": r.psi, "t1": r.t, "psi1_identified_NS": bool(r.fwd), "psi1_SN": bool(r.rev),
           "psi1_drop2023": p_oks.set_index("Constraint Name").loc[n, "psi_drop2023"], "psi1_drop2024": p_oks.set_index("Constraint Name").loc[n, "psi_drop2024"], "psi1_drop2025": p_oks.set_index("Constraint Name").loc[n, "psi_drop2025"],
           "L_f": r.L_f, "L_source": r.L_source, "T1_NS": r.T_star, "T1_SN": np.nan,
           "psi2_P-NS": p2["psi2_P-NS"], "psi2_H-NEOK": p2["psi2_H-NEOK"], "psi2_P-NOK": p2["psi2_P-NOK"], "psi2_P-SS": v, "psi2_P-NS-wind2gas": p2["psi2_P-NS-wind2gas"],
           "ptdf_P-SS": p2["ptdf_P-SS"], "otdf_P-SS": p2["otdf_P-SS"], "n_cont_modelled": p2["n_cont_modelled"], "cont_declared": p2["cont_declared"],
           "psi2_identified_NS": bool(v >= FLOOR), "psi2_SN": bool(v <= -FLOOR), "T2_NS": r.L_f / v if v >= FLOOR else np.nan, "T2_SN": np.nan,
           "psi2_over_psi1": v / r.psi if r.psi else np.nan, "sign_agree": (np.sign(v) == np.sign(r.psi)) if abs(r.t) >= 2 else np.nan}
    for tag in ("x0.5", "x2", "x1_inner"): row[f"psi2_P-SS_{tag}"] = psi2[tag].loc[n, "psi2_P-SS"]
    rows.append(row)
T = pd.DataFrame(rows); T.to_csv(f"{R}/spp58/tstar_58.csv", index=False)
C = T[T.set.eq("n_s_corridor")]; SPS = T[T.set.eq("sps_tie")]
# ---------------- objects (PRECOMMIT §3) ----------------
def agg(df, Tcol, label, standing):
    d = df[df[Tcol].notna()]
    if len(d) < 1: say(f"{label}: no constituent"); return None
    m = wmed(d[Tcol], d.h_pooled); p25 = wmed(d[Tcol], d.h_pooled, 0.25); p75 = wmed(d[Tcol], d.h_pooled, 0.75)
    lo = {y: loyo(d[Tcol].values, d.constraint.values, y) for y in (2023, 2024, 2025)}
    verdict = ("INSIDE the band (confirms)" if band(m, standing) else "OUTSIDE the band (STOP; card)") if standing else "n/a"
    say(f"{label}: n={len(d)} hours={int(d.h_pooled.sum())} weighted median {m:,.0f} -> {round(m, -2):,.0f} MW | p25/p75 {p25:,.0f}/{p75:,.0f} ({p75/p25:.2f}x) | LOYO drop23/24/25 {lo[2023]:,.0f}/{lo[2024]:,.0f}/{lo[2025]:,.0f} | vs {standing}: ratio {m/standing if standing else float('nan'):.2f} -> {verdict}")
    say("   " + "; ".join(f"{r.constraint} {r[Tcol]:,.0f} ({int(r.h_pooled)} h)" for _, r in d.sort_values(Tcol).iterrows()))
    return {"n": int(len(d)), "hours": int(d.h_pooled.sum()), "wmedian": m, "rounded": round(m, -2), "p25": p25, "p75": p75, "loyo": lo, "standing": standing, "ratio": (m / standing if standing else None), "inside_band": (band(m, standing) if standing else None), "members": d[["constraint", Tcol, "h_pooled"]].values.tolist()}
say("== K3 / K4 ==")
meta = json.load(open(f"{S}/out/ptdf_meta_x1.json")); say(f"K3 cut-set identities: {meta['k3']}")
lines = C[C.resolved & ~C.element.str.startswith("XFMR") & C.sign_agree.notna()].copy(); lines["sign_agree"] = lines.sign_agree.astype(bool)
say("K4 sign agreement on resolved corridor LINES with |t1|>=2: %d/%d = %.0f%%  (%s)" % (int(lines.sign_agree.sum()), len(lines), 100*lines.sign_agree.mean(), ", ".join(r.constraint + (":agree" if r.sign_agree else ":DISAGREE") for _, r in lines.iterrows())))
xf = C[C.resolved & C.element.str.startswith("XFMR") & (C.t1.abs() >= 2)]
say(f"   transformers (|psi| only): {', '.join('%s psi1 %+.4f psi2 %+.4f' % (r.constraint, r.psi1, r['psi2_P-NS']) for _, r in xf.iterrows())}")
say("\n== N->S, the like-for-like object: S2 = psi1-identified N->S ∩ resolved ==")
S2 = C[C.psi1_identified_NS & C.resolved]; say(f"S2 = {len(S2)} of 12: {', '.join(S2.constraint)}; psi2-identified among them: {int(S2.psi2_identified_NS.sum())}")
out["NS_l4l_T1"] = agg(S2, "T1_NS", "T*1(S2) [SPP-53's rule on the subset]", None)
out["NS_l4l_T2"] = agg(S2, "T2_NS", "T*2(S2)", out["NS_l4l_T1"]["wmedian"]); out["NS_l4l_T2"]["standing_3400_ratio"] = out["NS_l4l_T2"]["wmedian"] / 3400; out["NS_l4l_T2"]["inside_band_vs_3400"] = band(out["NS_l4l_T2"]["wmedian"], 3400)
say(f"   T*2(S2) vs 3,400: ratio {out['NS_l4l_T2']['standing_3400_ratio']:.2f} -> {'INSIDE' if out['NS_l4l_T2']['inside_band_vs_3400'] else 'OUTSIDE'} the band")
say("\n== N->S, all-psi2 object: every corridor constituent with psi2 >= 0.005 under P-NS ==")
out["NS_all_T2"] = agg(C[C.resolved], "T2_NS", "T*2(all-psi2 N->S)", 3400)
say("\n== S->N ==")
S2s = C[C.psi1_SN & C.resolved]; say(f"S2(S->N) = {len(S2s)} of 8: {', '.join(S2s.constraint)}; psi2 reverse-loaded among them: {int(S2s.psi2_SN.sum())}")
out["SN_l4l_T1"] = agg(S2s, "T1_SN", "T*1(S2, S->N)", None)
out["SN_l4l_T2"] = agg(S2s, "T2_SN", "T*2(S2, S->N)", out["SN_l4l_T1"]["wmedian"]); out["SN_l4l_T2"]["standing_4206_ratio"] = out["SN_l4l_T2"]["wmedian"] / 4206; out["SN_l4l_T2"]["inside_band_vs_4206"] = band(out["SN_l4l_T2"]["wmedian"], 4206)
say(f"   T*2(S2,S->N) vs 4,206: ratio {out['SN_l4l_T2']['standing_4206_ratio']:.2f} -> {'INSIDE' if out['SN_l4l_T2']['inside_band_vs_4206'] else 'OUTSIDE'} the band")
out["SN_all_T2"] = agg(C[C.resolved], "T2_SN", "T*2(all-psi2 S->N)", 4206)
say("\n== sps_tie under P-SS (South-rest -> SPS) ==")
out["SPS_T2"] = agg(SPS, "T2_NS", "T*2(sps_tie, psi2-identified OK->SPS)", 10705)
out["SPS_T2_noSPSNM"] = agg(SPS[~SPS.constraint.eq("SPSNMTIES")], "T2_NS", "T*2(sps_tie) excluding SPSNMTIES (2/10 elements present, a lower-bound psi)", 10705)
a, b_ = psi2["x1"].loc["TEMP50_23126"], psi2["x1"].loc["TMP555_29231"]
ratio = a["psi2_P-SS"] / b_["psi2_P-SS"]; wv = "COLLAPSED" if ratio <= 1.5 else ("REAL" if (ratio <= 0.5) else "INDETERMINATE")
say(f"Potter County width: psi2(TEMP50, OTDF Border-Tuco out) {a['psi2_P-SS']:.4f} (PTDF {a['ptdf_P-SS']:.4f}) vs psi2(TMP555, PTDF) {b_['psi2_P-SS']:.4f}: ratio {ratio:.2f} -> {wv}; psi1 0.0473 vs 0.1321 (2.79x) | T*2 {505.9/a['psi2_P-SS']:,.0f} vs {508.7/b_['psi2_P-SS']:,.0f} MW; T*1 10,705 vs 3,850")
out["potter"] = {"psi2_TEMP50_otdf": a["psi2_P-SS"], "psi2_TEMP50_ptdf": a["ptdf_P-SS"], "psi2_TMP555": b_["psi2_P-SS"], "ratio": ratio, "verdict": wv}
say("\n== sensitivities (weighted medians of the same objects) ==")
sens = {}
for tag in ("x0.5", "x2", "x1_inner"):
    d = C[C.resolved].copy(); v = d[f"psi2_P-NS_{tag}"]; d["T2n"] = np.where(v >= FLOOR, d.L_f / v, np.nan); d["T2s"] = np.where(v <= -FLOOR, d.L_f / (-v), np.nan)
    s2 = d[d.psi1_identified_NS & d.T2n.notna()]; s2s = d[d.psi1_SN & d.T2s.notna()]
    sp = SPS.copy(); vs = sp[f"psi2_P-SS_{tag}"]; sp["T2"] = np.where(vs >= FLOOR, sp.L_f / vs, np.nan); spi = sp[sp.T2.notna()]
    sens[tag] = {"NS_l4l": wmed(s2.T2n, s2.h_pooled) if len(s2) else np.nan, "NS_all": wmed(d[d.T2n.notna()].T2n, d[d.T2n.notna()].h_pooled), "SN_l4l": wmed(s2s.T2s, s2s.h_pooled) if len(s2s) else np.nan, "SPS": wmed(spi.T2, spi.h_pooled) if len(spi) else np.nan,
                 "potter_ratio": psi2[tag].loc["TEMP50_23126", "psi2_P-SS"] / psi2[tag].loc["TMP555_29231", "psi2_P-SS"]}
    say(f"{tag}: NS like-for-like {sens[tag]['NS_l4l']:,.0f} | NS all-psi2 {sens[tag]['NS_all']:,.0f} | SN like-for-like {sens[tag]['SN_l4l']:,.0f} | sps_tie {sens[tag]['SPS']:,.0f} | Potter ratio {sens[tag]['potter_ratio']:.2f}")
d = C[C.resolved].copy(); v = d["psi2_P-NS-wind2gas"]; d["T2n"] = np.where(v >= FLOOR, d.L_f / v, np.nan); s2 = d[d.psi1_identified_NS & d.T2n.notna()]
sens["wind2gas"] = {"NS_l4l": wmed(s2.T2n, s2.h_pooled) if len(s2) else np.nan, "NS_all": wmed(d[d.T2n.notna()].T2n, d[d.T2n.notna()].h_pooled), "n_l4l": int(len(s2))}
say(f"wind-only source / gas-only sink: NS like-for-like {sens['wind2gas']['NS_l4l']:,.0f} (n={sens['wind2gas']['n_l4l']}) | NS all-psi2 {sens['wind2gas']['NS_all']:,.0f}")
out["sensitivities"] = sens
say("\n== H-NEOK (hub-pair proxy) vs psi1 on the resolved psi1-significant corridor constituents ==")
for _, r in C[C.resolved & (C.t1.abs() >= 2)].iterrows():
    say(f"   {r.constraint:14s} {r.element[:26]:26s} psi1 {r.psi1:+.4f}  psi2 P-NS {r['psi2_P-NS']:+.4f}  H-NEOK {r['psi2_H-NEOK']:+.4f}  P-NOK {r['psi2_P-NOK']:+.4f}  ratio psi2/psi1 {r.psi2_over_psi1:+.2f}")
say("\n== double attribution (oklahoma_internal, resolved) ==")
dd = []
for n in ("CIMXF2CIMXF3", "TMP573_26592", "CORNAPTERSUN"):
    p2 = psi2["x1"].loc[n]; a1 = p_nok.set_index("Constraint Name").loc[n]; b1 = p_oks.set_index("Constraint Name").loc[n]
    cls = "DOUBLE-ATTRIBUTED" if (abs(p2["psi2_P-NOK"]) >= FLOOR and abs(p2["psi2_P-SS"]) >= FLOOR) else ("LOCAL" if (abs(p2["psi2_P-NOK"]) < FLOOR and abs(p2["psi2_P-SS"]) < FLOOR) else "single-link")
    say(f"   {n}: psi1 (OK-N) {a1.psi:+.4f} t {a1.t:+.1f} | psi1 (S-OK) {b1.psi:+.4f} t {b1.t:+.1f} || psi2 P-NOK {p2['psi2_P-NOK']:+.4f} | psi2 P-SS {p2['psi2_P-SS']:+.4f} -> {cls}")
    dd.append({"constraint": n, "psi1_okn": a1.psi, "t1_okn": a1.t, "psi1_sok": b1.psi, "t1_sok": b1.t, "psi2_P-NOK": p2["psi2_P-NOK"], "psi2_P-SS": p2["psi2_P-SS"], "verdict": cls})
out["double_attribution"] = dd
json.dump(out, open(f"{R}/spp58/aggregates_58.json", "w"), indent=1, default=float)
open(f"{R}/spp58/aggregate_ttc_58.log", "w").write("\n".join(log) + "\n")
