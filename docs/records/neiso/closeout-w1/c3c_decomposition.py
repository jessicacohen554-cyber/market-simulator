"""closeout-NEISO wave 1: zero-LP C3c tail decomposition from the committed ISO-NE SMD hub sheets (ISO NE CA, RT/DA LMP)."""
import pandas as pd
import json
out={}
for y in range(2019,2026):
    d=pd.read_excel(f'data/raw/lmp-data/NEISO/{y}_smd_hourly.xlsx',sheet_name='ISO NE CA')
    d['date']=pd.to_datetime(d.Date).dt.strftime('%Y-%m-%d')
    rt=d[d.RT_LMP>300]; both=rt[rt.DA_LMP>=300]
    # components: energy vs congestion/loss
    rec=dict(rt_h=len(rt), da_h=int((d.DA_LMP>300).sum()), rt_with_da_ge300=len(both), rt_only=len(rt)-len(both),
             rt_only_frac=round((len(rt)-len(both))/len(rt),3) if len(rt) else None,
             rt_by_month={k:int(v) for k,v in rt.date.str[5:7].value_counts().sort_index().items()},
             max_rt=round(float(rt.RT_LMP.max()),2) if len(rt) else None,
             median_da_on_rt_tail_hours=round(float(rt.DA_LMP.median()),2) if len(rt) else None,
             top_event_days={k:int(v) for k,v in rt.date.value_counts().head(6).items()},
             rt_energy_component_share=round(float((rt.RT_EC/rt.RT_LMP).median()),3) if len(rt) else None)
    out[y]=rec; print(y,rec)
json.dump(out,open('docs/records/neiso/closeout-w1/c3c_decomposition.json','w'),indent=1)
