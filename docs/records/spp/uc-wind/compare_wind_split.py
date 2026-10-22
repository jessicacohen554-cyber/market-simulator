"""UC-SPP-WIND: model (keeper data layer) vs measured zonal wind/solar, zero LP.

Measured North/South without a plant->reserve-zone map:
  RZ1 (NPPD/OPPD/LES) + RZ5 (WAUE) are wholly SPP-North; RZ3 (SPS) is wholly SPP-South
  (SL_to_Pnode_to_Zone_with_Area.csv NODE_AREA x RESZONE). RZ2 + RZ4 straddle the seam.
  f_m = South fraction of the mixed RZ2+RZ4 in month m
      = (EIA-923 South share_m x SPP RZ total_m - RZ3_m) / (RZ2+RZ4)_m      [both measured]
  S_central(t) = RZ3(t) + f_m x (RZ2+RZ4)(t);  S_lo = RZ3;  S_hi = RZ3 + RZ2 + RZ4.

Usage (repo root): compare_wind_split.py docs/records/spp/uc-wind/ 2019 ... 2025
"""
import sys, numpy as np, pandas as pd
R='docs/records/spp/uc-wind/'
SC='docs/records/spp/ucmilp/data/spp_south_scarcity_2026_10_18/'
OUT=sys.argv[1]; years=[int(a) for a in sys.argv[2:]]
NST={'ND','SD','NE','MN','MT','IA','KS','MO','CO'}
f923=pd.read_csv(R+'f923_swpp_vre_monthly.csv.gz'); f923['z']=np.where(f923.state.isin(NST),'N','S')
mod=pd.read_csv(R+'model_zone_vre_hourly.csv.gz')
RZ=pd.read_csv(R+'rz_actual_hourly_2019_2025.csv.gz',parse_dates=['t_utc_end'])
sl=pd.read_csv(SC+'slack_hour_attribution.csv')[['year','hour','slack','implied_NS_lo','implied_NS_hi']]
ann=[]; mon=[]; hrs=[]; hrs_all=[]
for y in years:
    m=mod[mod.year==y].reset_index(drop=True)
    r=RZ.copy(); r['t']=r.t_utc_end.dt.tz_localize('UTC').dt.tz_convert('America/Chicago')-pd.Timedelta(hours=1)
    r=r.drop_duplicates(['t','ReserveZone'])
    r=r[(r.t>=pd.Timestamp(f'{y}-01-01',tz='America/Chicago'))&(r.t<pd.Timestamp(f'{y+1}-01-01',tz='America/Chicago'))]
    rng=pd.date_range(pd.Timestamp(f'{y}-01-01',tz='America/Chicago'),pd.Timestamp(f'{y+1}-01-01',tz='America/Chicago'),freq='h',inclusive='left')
    rng=rng[~((rng.month==2)&(rng.day==29))]; assert len(rng)==8760  # model clock: local year, Feb 29 dropped (eia930/frames.py)
    mo=rng.month.values
    for tech,col,fu in [('wind','WindActualMW','WND'),('solar','SolarActualMW','SUN')]:
        meas=r.pivot(index='t',columns='ReserveZone',values=col).reindex(rng); meas.columns=[int(c) for c in meas.columns]
        ok=r.pivot(index='t',columns='ReserveZone',values='WindActualMW').reindex(rng).notna().all(axis=1).values  # file-present hours; solar blank at night = 0
        meas=meas.fillna(0.0) if tech=='solar' else meas
        tot=meas[[1,2,3,4,5]].sum(axis=1).values; Np=(meas[1]+meas[5]).values; Sp=meas[3].values; M=(meas[2]+meas[4]).values
        e=f923[(f923.year==y)&(f923.fuel==fu)].groupby(['month','z']).net_mwh.sum().unstack(fill_value=0)
        sh923=(e['S']/e.sum(axis=1)).reindex(range(1,13))
        fm={}
        for k in range(1,13):
            sel=ok&(mo==k)
            T,S3,MM=tot[sel].sum(),Sp[sel].sum(),M[sel].sum()
            fm[k]=float(np.clip((sh923[k]*T-S3)/MM,0,1)) if MM>0 else 0.0
            WN=m[f'{tech}_SPP-North'].values; WS=m[f'{tech}_SPP-South'].values
            mon.append(dict(year=y,tech=tech,month=k,f_mixed=fm[k],eia923_S_share=sh923[k],
                meas_S_share=(S3+fm[k]*MM)/T if T>0 else np.nan, model_S_share=WS[sel].sum()/(WN[sel].sum()+WS[sel].sum()),
                meas_TWh=T/1e6, model_TWh=(WN[sel].sum()+WS[sel].sum())/1e6))
        f_h=np.nan_to_num(np.array([fm[k] for k in mo]))
        Sc=Sp+f_h*M; Slo=Sp; Shi=Sp+M
        WN=m[f'{tech}_SPP-North'].values; WS=m[f'{tech}_SPP-South'].values
        ann.append(dict(year=y,tech=tech,hours=int(ok.sum()),meas_TWh=tot[ok].sum()/1e6,model_TWh=(WN+WS)[ok].sum()/1e6,
            eia923_S_share=(e['S'].sum()/e.values.sum()),meas_S_share_c=Sc[ok].sum()/tot[ok].sum(),
            meas_S_share_lo=Slo[ok].sum()/tot[ok].sum(),meas_S_share_hi=Shi[ok].sum()/tot[ok].sum(),
            model_S_share=WS[ok].sum()/(WN+WS)[ok].sum(),
            r_S=np.corrcoef(Sc[ok],WS[ok])[0,1], r_N=np.corrcoef((tot-Sc)[ok],WN[ok])[0,1], r_tot=np.corrcoef(tot[ok],(WN+WS)[ok])[0,1],
            r_pureN_vs_modelN=np.corrcoef(Np[ok],WN[ok])[0,1], r_pureS_vs_modelS=np.corrcoef(Sp[ok],WS[ok])[0,1]))
        hrs_all.append(pd.DataFrame(dict(year=y,hour=np.arange(8760),tech=tech,ok=ok,meas_tot=tot,model_tot=WN+WS,meas_N_pure=Np,meas_S_pure=Sp,meas_mixed=M,f_mixed=f_h,meas_S_c=Sc,model_S=WS,model_N=WN)))
H=pd.concat(hrs_all)
w=H[H.tech=='wind'].set_index(['year','hour']); so=H[H.tech=='solar'].set_index(['year','hour'])
sl=sl[sl.year.isin(years)].set_index(['year','hour'])
J=sl.join(w[['meas_tot','model_tot','meas_N_pure','meas_S_pure','meas_mixed','f_mixed','meas_S_c','model_S']])
J=J.join(so[['meas_S_c','model_S']].rename(columns={'meas_S_c':'sol_meas_S_c','model_S':'sol_model_S'}))
J['dS_wind_c']=J.meas_S_c-J.model_S; J['dS_wind_hi']=J.meas_S_pure+J.meas_mixed-J.model_S
J['dS_sol']=J.sol_meas_S_c-J.sol_model_S
J['implied_NS_lo_meas']=J.implied_NS_lo-J.dS_wind_c-J.dS_sol; J['implied_NS_hi_meas']=J.implied_NS_hi-J.dS_wind_c-J.dS_sol
J['implied_NS_lo_extreme']=J.implied_NS_lo-J.dS_wind_hi-J.dS_sol
J['f_needed']=((J.model_S+(J.implied_NS_lo-3400)-J.dS_sol)-J.meas_S_pure)/J.meas_mixed
# Direct slack test: South is short at the link limit, so extra South VRE offsets unserved 1:1.
J['closes_slack_central']=(J.dS_wind_c+J.dS_sol)>=J.slack
J['f_needed_slack']=(J.model_S+J.slack-J.dS_sol-J.meas_S_pure)/J.meas_mixed
# Pure-zone test (no apportioning): RZ3 (wholly South) vs RZ1+RZ5 (wholly North), each relative to its
# own annual mean, against the model's South/North ratio relative to its own annual means.
w=H[(H.tech=='wind')&H.ok].copy(); g=w.groupby('year')
w['ratio_model']=(w.model_S/g.model_S.transform('mean'))/(w.model_N/g.model_N.transform('mean'))
w['ratio_pure_meas']=(w.meas_S_pure/g.meas_S_pure.transform('mean'))/(w.meas_N_pure/g.meas_N_pure.transform('mean'))
w['model_S_share']=w.model_S/w.model_tot; w['meas_S_share_c']=w.meas_S_c/w.meas_tot
bot=w[w.model_S_share<g.model_S_share.transform(lambda x:x.quantile(.1))]
bot.groupby('year')[['model_S_share','meas_S_share_c','ratio_model','ratio_pure_meas']].median().join(bot.groupby('year').size().rename('hours')).to_csv(OUT+'low_south_decile_test.csv')
w['dS']=w.meas_S_c-w.model_S; w['summer_aft']=(w.hour//24).between(151,272)&(w.hour%24).between(13,18)
def _st(d):
    return pd.Series({'mean':d.dS.mean(),'p5':d.dS.quantile(.05),'p50':d.dS.median(),'p95':d.dS.quantile(.95),'MAE':d.dS.abs().mean(),
        'r':np.corrcoef(d.meas_S_c,d.model_S)[0,1],'model_Ssh':d.model_S.sum()/d.model_tot.sum(),'meas_Ssh':d.meas_S_c.sum()/d.meas_tot.sum()})
pd.concat({'all':w.groupby('year').apply(_st),'summer_13_18':w[w.summer_aft].groupby('year').apply(_st)},axis=1).round(2).to_csv(OUT+'split_error_by_year.csv')
J=J.join(w.set_index(['year','hour'])[['ratio_model','ratio_pure_meas']])
pd.DataFrame(ann).to_csv(OUT+'annual_by_year.csv',index=False); pd.DataFrame(mon).to_csv(OUT+'monthly_by_year.csv',index=False)
J.reset_index().to_csv(OUT+'slack_hours_wind_split.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
print(pd.DataFrame(ann).round(3).to_string())
print(J.reset_index()[['year','hour','slack','meas_tot','model_tot','meas_N_pure','meas_S_pure','meas_mixed','f_mixed','meas_S_c','model_S','dS_wind_c','dS_sol','implied_NS_lo','implied_NS_lo_meas','implied_NS_hi_meas','implied_NS_lo_extreme','f_needed','closes_slack_central','f_needed_slack']].round(2).to_string())
