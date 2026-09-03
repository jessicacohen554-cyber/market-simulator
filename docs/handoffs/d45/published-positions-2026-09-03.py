"""capx D45 instrument, published side: where PJM and NYISO REALLY sat, from the
published record only (zero solves, zero model quantities).

PJM  — per delivery year: BRA offered UCAP (Table 6 / Table 5 of the BRA
       reports, in-session fetch, sha256 in the finding), cleared UCAP + RTO
       clearing price (committed auction-price/pjm/pjm.csv), the auction's own
       demand denominator (committed demand-curve/pjm/pjm.csv:
       reliability_requirement_frr_adj + ee_addback, pre-CIFP; frr_adj alone
       from 2025/26 where EE left the market), the BRA report's basis-free
       Total Reserve Margin vs target IRM, and HEAD's vintage curve evaluated at
       each published position (self-check: must reproduce the real clearing).
NYISO — per capability year: NYSRC IRM (study + adopted, Gold Book Table V-3),
       NYSRC peak forecast (IRM study report bodies), the NYCA ICAP->UCAP
       translation factor (committed demand-curve/nyiso/nyiso.csv), the
       Potomac SOM "UCAP Margin (Summer), % of Requirement" (the market's own
       cleared position), the NYCA spot price (committed auction-price), and
       HEAD's vintage curve at the published position.
Every number is either read from a committed CSV or transcribed from the
fetched primary document named in the finding. Nothing here is a model output.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from market_sim.config.capacity_market import (evaluate_demand_curve, resolve_demand_curve_vintage,
    FORECAST_POOL_REQUIREMENT_BY_ISO, PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO, PLANNING_RESERVE_MARGIN_BY_ISO)
REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data/raw/capacity-market"

def price(iso, year, pos):
    v = resolve_demand_curve_vintage(iso, year)
    return evaluate_demand_curve(v.demand_curve, pos) * v.net_cone_curve_per_kw_yr, v.delivery_year

# ---- PJM ------------------------------------------------------------------
# BRA report Table 6 (UCAP offered: generation + DR + EE) per delivery year; 2025/26 and
# 2026/27 totals from the 2026/27 BRA report narrative ("declined 500.5 MW UCAP from
# 135,692.3 MW in the 2025/2026 BRA to 135,191.8"). Total Reserve Margin and target IRM
# from each report's Table 1/2 summary.
BRA = {  # DY: (offered_gen, offered_dr, offered_ee, total_rm_pct, target_irm_pct)
    "2021/2022": (171663.2, 11886.8, 2954.8, 21.5, 15.8),
    "2022/2023": (152128.6, 10513.0, 5056.8, 19.9, 14.5),
    "2023/2024": (141026.7, 10116.7, 5471.1, 20.3, 14.8),
    "2024/2025": (138799.3, 10146.4, 8417.0, 20.4, 14.7),
    "2025/2026": (135692.3, None, None, 18.5, 17.8),
    "2026/2027": (135191.8, None, None, 18.9, 19.1),
}
ap = pd.read_csv(RAW / "auction-price/pjm/pjm.csv")
dc = pd.read_csv(RAW / "demand-curve/pjm/pjm.csv")
rows = []
for dy, (og, odr, oee, rm, irm) in BRA.items():
    r = ap[(ap.delivery_year == dy) & (ap.area == "RTO")].iloc[0]
    cleared, px_day = float(r.cleared_mw), float(r.clearing_price)
    d = dc[dc.delivery_year == dy]
    frr = d[d.metric == "reliability_requirement_frr_adj"].y_value
    ee = d[d.metric == "ee_addback"].y_value
    # The auction's own demand denominator = the FRR-adjusted RTO Reliability Requirement
    # plus the published EE addback wherever PJM publishes one (2021/22-2025/26; the
    # 2025/26 workbook still carries 1,459.8 MW and HEAD's vintage normalizes by
    # 133,563.6 + 1,459.8 = 135,023.4). 2026/27 publishes no FRR-adjusted requirement in
    # the committed rows (its curve is normalized in pct terms); its quantity positions are
    # left None and only the basis-free Total-Reserve-Margin position is reported for it.
    ee = float(ee.iloc[0]) if len(ee) else 0.0
    req = (float(frr.iloc[0]) + ee) if len(frr) else None
    offered = og + (odr or 0.0) + (oee or 0.0)
    yr = int(dy[:4])
    px_cleared, vint = price("PJM", yr, cleared / req) if req else (None, resolve_demand_curve_vintage("PJM", yr).delivery_year)
    px_offered = price("PJM", yr, offered / req)[0] if req else None
    rows.append(dict(delivery_year=dy, vintage=vint, requirement_ucap_mw=req, offered_ucap_mw=offered,
        cleared_ucap_mw=cleared, pos_offered=(offered / req) if req else None, pos_cleared=(cleared / req) if req else None,
        pos_total_rm=(1 + rm / 100) / (1 + irm / 100), total_rm_pct=rm, target_irm_pct=irm,
        real_price_kw_yr=px_day * 365 / 1000, head_curve_at_cleared=px_cleared,
        head_curve_at_offered=px_offered,
        zero_cross=resolve_demand_curve_vintage("PJM", yr).demand_curve[-1].reserve_ratio))
pjm = pd.DataFrame(rows)
# HEAD's own requirement factor (share of gross peak) per calendar year 2021-2025
f_dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
head_req = {}
for y in (2021, 2023, 2024, 2025):
    dy = f"{y}/{y+1}"
    fpr = FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"].get(dy)
    fac = (1 - f_dr) * (fpr if fpr else (1 + PLANNING_RESERVE_MARGIN_BY_ISO["PJM"]) * PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["PJM"])
    head_req[y] = dict(delivery_year=dy, path="published FPR" if fpr else "composite (1+IRM)x0.7699", factor_of_gross_peak=fac,
                       published_fpr_ucap=float(dc[(dc.delivery_year == dy) & (dc.metric == "forecast_pool_requirement")].y_value.iloc[0]))

# ---- NYISO ----------------------------------------------------------------
# NYSRC 2026-2027 IRM Study Technical Report Appendices (Dec 2025), Appendix D §D.1.1
# Table D.2 "New York Control Area ICAP to UCAP Translation" (p.68): per capability year
# the ICAP-market forecast peak, the ADOPTED IRM, the Derate (translation) Factor, the
# ICAP and UCAP requirements. IRM-study values (the pre-adoption number the committed
# nyiso.csv carries for 2023-24 = 19.9 and 2024-25 = 23.1) from the NYSRC study bodies.
# SOM margin = Potomac SOM "UCAP Margin (Summer), Margin (% of Requirement)", NYCA column,
# 2021-2025 SOM reports (Table 12 / 14 / 9 / 11 / 9).
NYISO = {  # CY: (IRM study %, IRM adopted %, ICAP-market peak MW, derate, ICAP req, UCAP req, SOM margin %)
    2021: (20.7, 20.7, 32333.0, 0.0877, 39026.0, 35604.0, 4.9),
    2022: (19.6, 19.6, 31767.0, 0.0978, 37993.0, 34277.0, 8.3),
    2023: (19.9, 20.0, 32049.0, 0.1014, 38459.0, 34559.0, 4.3),
    2024: (23.1, 22.0, 31542.0, 0.1321, 38481.0, 33397.0, 5.8),
    2025: (24.4, 24.4, 31469.0, 0.1300, 39148.0, 34059.0, 5.8),
}
nd = pd.read_csv(RAW / "demand-curve/nyiso/nyiso.csv")
na = pd.read_csv(RAW / "auction-price/nyiso/nyiso.csv")
tf = {int(r.delivery_year[:4]): float(r.y_value) for _, r in nd[nd.metric == "icap_ucap_translation_factor"].iterrows()}
nrows = []
for cy, (irm_s, irm_a, peak, t, icap_req, ucap_req, margin) in NYISO.items():
    lbl = f"{cy}/{str(cy+1)[2:]}"
    spot = float(na[(na.delivery_year == lbl) & (na.area == "NYCA")].clearing_price.iloc[0])
    assert tf.get(cy) is None or abs(tf[cy] - t) < 1e-9, (cy, tf.get(cy), t)  # committed CSV rows agree
    assert abs(peak * (1 + irm_a / 100) - icap_req) < 1.0, (cy, peak * (1 + irm_a / 100), icap_req)
    assert abs(icap_req * (1 - t) - ucap_req) < 1.0, (cy, icap_req * (1 - t), ucap_req)
    pos = 1 + margin / 100
    px, vint = price("NYISO", cy, pos)
    nrows.append(dict(capability_year=lbl, vintage=vint, irm_study_pct=irm_s, irm_adopted_pct=irm_a, nysrc_peak_mw=peak,
        translation_factor=t, icap_requirement_mw=icap_req, ucap_requirement_mw=ucap_req,
        ucap_supplied_mw=(ucap_req * pos) if ucap_req else None, pos_published=pos,
        spot_kw_month=spot, spot_kw_yr=spot * 12, head_curve_at_published_pos=px,
        zero_cross=resolve_demand_curve_vintage("NYISO", cy).demand_curve[-1].reserve_ratio if resolve_demand_curve_vintage("NYISO", cy).demand_curve else None))
ny = pd.DataFrame(nrows)
head_ny = dict(irm=PLANNING_RESERVE_MARGIN_BY_ISO["NYISO"], ratio=PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"],
               factor_of_gross_peak=(1 + PLANNING_RESERVE_MARGIN_BY_ISO["NYISO"]) * PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"],
               dr_fraction=ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO.get("NYISO", 0.0))
if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.float_format", lambda x: f"{x:,.4f}")
    print("== PJM published positions (RPM, UCAP) =="); print(pjm.to_string(index=False))
    print("\n== HEAD PJM requirement factor (x gross peak) =="); print(json.dumps(head_req, indent=1))
    print("\n== NYISO published positions (NYCA, UCAP) =="); print(ny.to_string(index=False))
    print("\n== HEAD NYISO requirement factor ==", json.dumps(head_ny))
    out = dict(pjm=pjm.to_dict("records"), pjm_head_requirement=head_req, nyiso=ny.to_dict("records"), nyiso_head_requirement=head_ny)
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1, default=float))
