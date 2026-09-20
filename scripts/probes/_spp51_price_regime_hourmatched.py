"""Hour-matched: what does the model do in the market's OWN negative-price hours?"""
import sys; sys.path.insert(0,'src')
import numpy as np, pandas as pd
BUN = {y:'results/calibration/spp42_span_a' for y in (2023,2024,2025)}
BUN.update({y:'results/calibration/spp49_benchmembership_span' for y in (2019,2020,2021,2022)})
act = pd.read_parquet('data/raw/_validation-source/actual_lmp_hourly_SPP.parquet')
rows=[]
for y in sorted(BUN):
    s=pd.read_parquet(f'{BUN[y]}/hourly/system_{y}.parquet'); s=s[s['pass']=='P1']
    mp=((s['price']*s['demand']).groupby(s['hour']).sum()/s.groupby('hour')['demand'].sum()).to_numpy()
    ch=pd.read_parquet(f'{BUN[y]}/hourly/class_hourly_{y}.parquet'); ch=ch[ch['pass']=='P1']
    coal=ch[ch.klass.isin(['COAL_PRB','COAL_LIGNITE'])].groupby('hour')['mw'].sum().reindex(range(8760),fill_value=0.).to_numpy()
    a=act[act['year']==y]; rt=a['rt'].to_numpy()
    ok=~np.isnan(rt)
    neg = ok & (rt<0)                      # the market's own negative hours
    pos = ok & (rt>=0)
    rows.append(dict(year=y, act_neg_h=int(neg.sum()),
        model_price_in_actneg=mp[neg].mean(), model_price_in_actpos=mp[pos].mean(),
        model_neg_share_of_actneg=float((mp[neg]<0).mean()),
        coal_in_actneg_GW=coal[neg].mean()/1e3, coal_in_actpos_GW=coal[pos].mean()/1e3,
        coal_ratio=coal[neg].mean()/coal[pos].mean()))
r=pd.DataFrame(rows); pd.set_option('display.width',220)
print("=== HOUR-MATCHED: the model inside the MARKET's own negative-price hours ===")
print(r.to_string(index=False,float_format=lambda v:f'{v:9.3f}'))
