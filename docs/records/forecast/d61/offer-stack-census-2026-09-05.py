"""capx D61 -- the offer-stack E&AS census: per screen year and class, units/firm MW at exactly zero E&AS (offer == bar/(a x 365)),
the implied E&AS distribution (EAS = bar - offer x 365 x a / 1000, $/kW-yr nameplate; censored at the bar when offer == 0) and the
per-unit margin that puts an offer AT the published price. Reads the committed arm-A ledgers only. Run from the repo root."""
import json, glob, numpy as np
BAR={"coal":45.0*1.3,"gas_cc":30.0,"gas_ct":21.0,"gas_st":35.0,"oil":25.0,"nuclear":130.0}
EFORD={"gas_cc":0.05,"gas_ct":0.06,"gas_st":0.07,"coal":0.08,"nuclear":0.03,"oil":0.10}
ELCC={"coal":0.83,"gas_cc":0.74,"gas_ct":0.60,"gas_st":0.73,"oil":0.91,"nuclear":0.95}
PUB={2022:50.00,2023:34.13,2024:28.92,2025:269.92}
b="results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a"
out={}
for y in (2022,2023,2024,2025):
    d=json.load(open(f"{b}/evolution_{y}.json")); cc=d["capacity_clearing"]; st=cc["offer_stack"]
    dev = y<=2024
    print(f"\n=== screen {y} -> DY {y}/{y+1}  clearing ${cc['price_usd_per_mw_day']:.2f}/MW-day  published ${PUB[y]:.2f}  cleared pos {cc['cleared_position']:.4f}")
    print(f"{'fuel':8s} {'n':>4s} {'firmMW':>8s} {'n_zero':>6s} {'MW_zero':>8s} {'n_off0':>6s} {'MW_off0':>8s} {'EAS p10':>8s} {'p50':>7s} {'p90':>7s} {'MWwt':>7s} {'n>pub':>5s} {'MW>pub':>8s} {'gap>pub p50':>11s}")
    out[y]={}
    for fuel,bar in BAR.items():
        rows=[(o,a) for uid,f,o,a,c in st if f==fuel]
        if not rows: continue
        afrac=(1-EFORD[fuel]) if dev else ELCC[fuel]
        o=np.array([r[0] for r in rows]); a=np.array([r[1] for r in rows])
        eas=bar - o*365*afrac/1000.0   # $/kW-yr nameplate; censored below at bar when offer==0
        zero=o>=0.999*bar*1000/(afrac*365)
        off0=o<=1e-9
        above=o>PUB[y]
        gap=(o-PUB[y])*365*afrac/1000.0  # $/kW-yr E&AS needed per unit to reach published
        w=a/a.sum()
        def wp(x,q): 
            i=np.argsort(x); cw=np.cumsum(w[i]); return float(x[i][np.searchsorted(cw,q)])
        print(f"{fuel:8s} {len(o):4d} {a.sum():8.0f} {zero.sum():6d} {a[zero].sum():8.0f} {off0.sum():6d} {a[off0].sum():8.0f} {wp(eas,.1):8.1f} {wp(eas,.5):7.1f} {wp(eas,.9):7.1f} {float((eas*w).sum()):7.1f} {above.sum():5d} {a[above].sum():8.0f} {np.median(gap[above]) if above.any() else 0:11.1f}")
        out[y][fuel]=dict(n=int(len(o)),firm=float(a.sum()),n_zero=int(zero.sum()),firm_zero=float(a[zero].sum()),n_off0=int(off0.sum()),firm_off0=float(a[off0].sum()),eas_p50=wp(eas,.5),eas_wmean=float((eas*w).sum()),n_above=int(above.sum()),firm_above=float(a[above].sum()),gap_med=float(np.median(gap[above])) if above.any() else 0.0, afrac=afrac, bar=bar, zero_offer=bar*1000/(afrac*365))
json.dump(out,open("docs/handoffs/d61/offer-stack-census-2026-09-05.json","w"),indent=1)
