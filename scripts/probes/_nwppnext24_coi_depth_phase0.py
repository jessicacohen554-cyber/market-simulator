"""NWPP-NEXT-24 phase 0 (zero LP): is there a forward-admissible driver of the COI economic depth?

A. CAISO OASIS TRNS_USAGE DAM on MALIN500_ISL + CASCADE_ITC (NW->CA = CAISO "I"): OTC, unscheduled
   TR (ETC/TOR) capacity and DAM schedule against the measured CISO<->BPAT/PACW leg.
B. Schedule and meter by measured MALIN - NW spread bin.
C. Price-taker COI on keeper 2026-10-03-nwpp-next-23-coi's NW price, export cap net of unscheduled TR.
The DAM schedule is a market outcome: diagnostic only. FINDING-nwppnext24-coi-depth-phase0-2026-10-03.md.

Usage: PYTHONPATH=src python scripts/probes/_nwppnext24_coi_depth_phase0.py
"""


def section_a() -> None:
    """Section A (see module docstring)."""
    import sys, numpy as np, pandas as pd
    sys.path.insert(0,"scripts/data"); sys.path.insert(0,"scripts/probes")
    from _nwppnext20_seam_phase0 import _measured
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled
    for y in (2023,2024,2025):
        d=pd.read_parquet(f"data/raw/caiso-trns-usage/caiso_trns_usage_dam_{y}.parquet")
        utc=pd.DatetimeIndex(_eia_hourly_frame_filled("NWPP", y)["UTC time"])
        meas=_measured(y)["CAISO_COI"]
        def ser(ti, dr, col):
            s=d[(d.ti_id==ti)&(d.direction==dr)].set_index("interval_start_utc")[col]
            s.index=s.index.tz_convert("UTC").tz_localize(None) if s.index.tz is not None else s.index
            return s.reindex(utc.tz_localize(None) if utc.tz is not None else utc).to_numpy(float)
        out={}
        for ti in ("MALIN500_ISL","CASCADE_ITC","COTPISO_ITC","NOB_ITC"):
            out[ti]=dict(otcI=ser(ti,"I","OTC_MW"),otcE=ser(ti,"E","OTC_MW"),sch=ser(ti,"I","ENE_IMPORT_MW"),trI=ser(ti,"I","USEAGE_MW"),trE=ser(ti,"E","USEAGE_MW"),atcI=ser(ti,"I","ATC_MW"))
        ok=np.isfinite(out["MALIN500_ISL"]["sch"])
        mc=out["MALIN500_ISL"]; cc=out["CASCADE_ITC"]
        sch=mc["sch"]+np.nan_to_num(cc["sch"]); otc=mc["otcI"]+np.nan_to_num(cc["otcI"]); tr=mc["trI"]+np.nan_to_num(cc["trI"])
        print(f"\n{y}: hours {ok.sum()}  meas CISO-leg mean {np.nanmean(meas[ok]):.0f}  DAM sched Malin+Cascade {np.nanmean(sch[ok]):.0f}  r={np.corrcoef(meas[ok],sch[ok])[0,1]:.3f}")
        print(f"  OTC(I) mean {np.nanmean(otc[ok]):.0f}  unsched TR(I) mean {np.nanmean(tr[ok]):.0f} p10/50/90 {np.nanpercentile(tr[ok],[10,50,90]).round(0)}  OTC-TR {np.nanmean((otc-tr)[ok]):.0f}")
        for ti in ("COTPISO_ITC","NOB_ITC"):
            print(f"  {ti} sched {np.nanmean(out[ti]['sch'][ok]):.0f} OTC(I) {np.nanmean(out[ti]['otcI'][ok]):.0f} TR(I) {np.nanmean(out[ti]['trI'][ok]):.0f}")
        # saturation: sched vs OTC-TR
        hs=sch[ok]; head=(otc-tr)[ok]
        print("  sched quantiles p50/90/99/max", np.nanpercentile(hs,[50,90,99,100]).round(0), " share of hours sched >= 0.95*(OTC-TR):", np.mean(hs>=0.95*head).round(3), " sched>=0.95 OTC:", np.mean(hs>=0.95*otc[ok]).round(3))
        print("  meas quantiles p50/90/99/max", np.nanpercentile(meas[ok],[50,90,99,100]).round(0))


def section_b() -> None:
    """Section B (see module docstring)."""
    import sys, numpy as np, pandas as pd, warnings
    warnings.filterwarnings("ignore")
    sys.path.insert(0,"scripts/data"); sys.path.insert(0,"scripts/probes")
    from _nwppnext20_seam_phase0 import _measured
    from _nwppnext23_price_level_phase0 import _meas_anchor, _series, VAL
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled
    import logging; logging.disable(logging.WARNING)
    nw = pd.read_parquet(VAL / "actual_lmp_hourly_NWPP.parquet")
    bins=[-1e9,-10,-5,0,5,10,15,20,30,1e9]
    for y in (2023,2024,2025):
        d=pd.read_parquet(f"data/raw/caiso-trns-usage/caiso_trns_usage_dam_{y}.parquet")
        utc=pd.DatetimeIndex(_eia_hourly_frame_filled("NWPP", y)["UTC time"])
        idx=utc.tz_localize(None) if utc.tz is not None else utc
        def ser(ti,dr,col):
            s=d[(d.ti_id==ti)&(d.direction==dr)].set_index("interval_start_utc")[col]
            s.index=s.index.tz_convert("UTC").tz_localize(None)
            return s.reindex(idx).to_numpy(float)
        sch=ser("MALIN500_ISL","I","ENE_IMPORT_MW")+np.nan_to_num(ser("CASCADE_ITC","I","ENE_IMPORT_MW"))
        otc=ser("MALIN500_ISL","I","OTC_MW")
        meas=_measured(y)["CAISO_COI"]; m=_meas_anchor("CAISO_COI",y); n=_series(nw,y,"rt")
        ok=np.isfinite(sch)&np.isfinite(m)&np.isfinite(n)
        sp=pd.cut((m-n)[ok],bins)
        g=pd.DataFrame({"sch":sch[ok],"meas":meas[ok],"gap":(sch-meas)[ok],"otc":otc[ok]}).groupby(sp).mean().round(0)
        g["n"]=pd.Series(sch[ok]).groupby(sp).size()
        print(y); print(g.T.to_string())
        # hour of day (Pacific approx = UTC-8)
        hod=((idx.hour-8)%24)[ok]
        h=pd.DataFrame({"sch":sch[ok],"meas":meas[ok]}).groupby(hod).mean().round(0)
        print("hod sched:", h.sch.astype(int).tolist()); print("hod meas: ", h.meas.astype(int).tolist())


def section_c() -> None:
    """Section C (see module docstring)."""
    import sys, numpy as np, pandas as pd, warnings, logging
    warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
    sys.path.insert(0,"scripts/data"); sys.path.insert(0,"scripts/probes")
    import _nwppnext23_price_level_phase0 as P
    from pathlib import Path
    P.KEEPER=Path("results/calibration/nwppnext23_span/hourly")
    from _nwppnext20_seam_phase0 import SEAMS, _measured
    from market_sim.data.neighbor_price import seam_tranche_prices
    from market_sim.data.transfer_interface_limits import nwpp_seam_limits_hourly
    from market_sim.model.interchange.spec import CAISO_IMPORT_DELIVERY_BASIS
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled
    mult, add = CAISO_IMPORT_DELIVERY_BASIS["PNW_midC"]
    spec=SEAMS["CAISO_COI"]
    for y in (2023,2024,2025):
        _, zp = P._keeper(y)
        ex, im, _ = seam_tranche_prices(spec, y, 8760)
        bz = zp[list(spec.border_zones)].to_numpy(); lo, hi = bz.min(1), bz.max(1)
        step = spec.interface_limit_mw / ex.shape[0]
        imp_cap, exp_cap = nwpp_seam_limits_hourly(y, 8760)["CAISO_COI"]
        d=pd.read_parquet(f"data/raw/caiso-trns-usage/caiso_trns_usage_dam_{y}.parquet")
        utc=pd.DatetimeIndex(_eia_hourly_frame_filled("NWPP", y)["UTC time"]); idx=utc.tz_localize(None) if utc.tz is not None else utc
        def ser(ti,dr,col):
            s=d[(d.ti_id==ti)&(d.direction==dr)].set_index("interval_start_utc")[col]; s.index=s.index.tz_convert("UTC").tz_localize(None)
            return s.reindex(idx).to_numpy(float)
        trI=np.nan_to_num(ser("MALIN500_ISL","I","USEAGE_MW"))+np.nan_to_num(ser("CASCADE_ITC","I","USEAGE_MW"))
        trE=np.nan_to_num(ser("MALIN500_ISL","E","USEAGE_MW"))+np.nan_to_num(ser("CASCADE_ITC","E","USEAGE_MW"))
        e2 = (ex > (lo*(1+mult)+add)[None,:]).sum(0)*step
        i2 = ((im+spec.hurdle) < hi[None,:]).sum(0)*step
        base = np.minimum(e2,exp_cap)-np.minimum(i2,imp_cap)
        tr = np.minimum(e2,np.maximum(exp_cap-trI,0))-np.minimum(i2,np.maximum(imp_cap-trE,0))
        meas=_measured(y)["CAISO_COI"]
        print(f"{y} price-taker keeper(H2) {base.sum()/1e6:6.2f}  with OTC-unschedTR {tr.sum()/1e6:6.2f}  delta {(tr-base).sum()/1e6:+.2f}  measured {np.nansum(meas)/1e6:.2f}  expcap mean {exp_cap.mean():.0f}")


if __name__ == "__main__":
    section_a()
    section_b()
    section_c()
