"""Format census_<tag>_<ISO>_<year>.json into the PRECOMMIT / FINDING tables (markdown)."""
import glob, json, sys
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parent
tag = sys.argv[1] if len(sys.argv) > 1 else "pre"
rows, cls, plants = [], [], []
for f in sorted(glob.glob(str(OUT / f"census_{tag}_*_*.json"))):
    d = json.load(open(f)); s = d["summary"]
    rows.append({k: v for k, v in s.items() if k != "seam2_plants"} | {"lw_price_ratio": d["pred"].get("_lw_price_ratio")})
    for p in s["seam2_plants"]:
        plants.append(dict(iso=s["iso"], year=s["year"], **{k: (v if k != "vintage" else f"{v[0]}-{v[1]}") for k, v in p.items()}))
    pred = {k: v for k, v in d["pred"].items() if isinstance(v, dict)}
    for c in d["by_class"]:
        p = pred.get(c["klass"], {})
        cls.append(c | dict(pred_keeper_twh=p.get("keeper_twh"), pred_d_twh=p.get("d_twh")))
    for k, p in pred.items():
        if k not in {c["klass"] for c in d["by_class"]}:
            cls.append(dict(iso=s["iso"], year=s["year"], klass=k, pred_keeper_twh=p.get("keeper_twh"), pred_d_twh=p.get("d_twh")))
S = pd.DataFrame(rows).fillna(0)
print("## Seam 1 — plant-month census (own-reported Natural Gas months of the ISO's gas plants)\n")
print("| ISO | year | armed | gas plants / MW | own-reporting plants | plant-months | in band | low | negative | high | US-ref months | no-band (ref<=0) | flagged plants | rows / MW touched (share) |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in S.itertuples():
    print(f"| {r.iso} | {r.year} | {'yes' if r.seam1_armed else 'NO' } | {r.gas_plants} / {r.gas_mw:,.0f} | {r.own_reporting_plants} | {r.plant_months} | {int(r.pm_in_band)} | {int(getattr(r,'pm_low',0))} | {int(getattr(r,'pm_negative',0))} | {int(getattr(r,'pm_high',0))} | {r.ref_us_fallback_months} | {int(getattr(r,'pm_unscreened_nonpos_ref',0))} | {r.flagged_plants} | {r.seam1_rows} / {r.seam1_mw:,.0f} ({100*r.seam1_mw_share:.1f} %) |")
print("\n## Seam 2 — simple-cycle-only plants below the floor\n")
print("| ISO | year | simple-cycle-only plants | below 9.0 | of which < 6.0 | 8.0–9.0 | rows / MW clamped (share of gas MW) |")
print("|---|---|---|---|---|---|---|")
for r in S.itertuples():
    print(f"| {r.iso} | {r.year} | {r.ct_only_plants} | {r.ct_only_below_floor} | {r.ct_only_below_6} | {r.ct_only_between_8_and_floor} | {r.seam2_rows} / {r.seam2_mw:,.0f} ({100*r.seam2_mw_share:.2f} %) |")
P = pd.DataFrame(plants)
if len(P):
    P = P[P.year == P.groupby("iso").year.transform("max")].drop(columns=["year"])
    print("\n### Seam 2 plants (latest keeper year), clamp 9.0\n")
    print("| ISO | plant | eGRID rate | nameplate MW | fleet MW at plant | fleet MW below floor | vintage |")
    print("|---|---|---|---|---|---|---|")
    for r in P.sort_values(["iso", "heat_rate"]).itertuples():
        print(f"| {r.iso} | {r.plant_code} | {r.heat_rate:.2f} | {r.nameplate:,.1f} | {r.fleet_mw:,.1f} | {getattr(r,'fleet_mw_below_floor',float('nan')):,.1f} | {r.vintage} |")
C = pd.DataFrame(cls)
print("\n## Predicted marginal-cost delta and re-clearing response (zero LP)\n")
print("| ISO | year | class | rows / MW | rows / MW touched | Δmc cap-wtd (class) $/MWh | Δmc on touched rows | keeper TWh | predicted ΔTWh |")
print("|---|---|---|---|---|---|---|---|---|")
for r in C.itertuples():
    if pd.isna(getattr(r, "rows", None)) or getattr(r, "rows", None) is None:
        print(f"| {r.iso} | {r.year} | {r.klass} | — | — | — | — | {r.pred_keeper_twh:.2f} | {r.pred_d_twh:+.2f} |" if pd.notna(r.pred_d_twh) else "")
        continue
    kt = f"{r.pred_keeper_twh:.2f}" if pd.notna(r.pred_keeper_twh) else "—"; dt = f"{r.pred_d_twh:+.2f}" if pd.notna(r.pred_d_twh) else "—"
    print(f"| {r.iso} | {r.year} | {r.klass} | {int(r.rows)} / {r.mw:,.0f} | {int(r.rows_touched)} / {r.mw_touched:,.0f} | {r.d_mc_capwtd:+.2f} | {r.d_mc_touched_capwtd:+.2f} | {kt} | {dt} |")
print("\n| ISO | year | load-weighted marginal-price ratio (predictor) |\n|---|---|---|")
for r in S.itertuples():
    print(f"| {r.iso} | {r.year} | {r.lw_price_ratio:.4f} |")
