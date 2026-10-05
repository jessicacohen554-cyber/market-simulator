import pandas as pd, numpy as np
d=pd.read_parquet('data/raw/eia-930-interchange/PJM interchange hourly.parquet')
s=d.groupby('local_time').mw.sum(min_count=7); s=s.groupby(level=0).first()
s.index=s.index+pd.Timedelta(hours=1)  # -> UTC hour-ending
frames=[]
for yr in (2019,2020):
    t=pd.read_csv(f'data/raw/iso-specific-transmission/PJM_{yr}_import_export_act_sch_interchange.csv',usecols=['datetime_ending_utc','actual_flow'])
    t['utc']=pd.to_datetime(t.datetime_ending_utc,format='%m/%d/%Y %I:%M:%S %p')
    frames.append(-t.groupby('utc').actual_flow.sum())
ref=pd.concat(frames); ref=ref.groupby(level=0).first()
j=pd.concat([s.rename('eia'),ref.rename('tie')],axis=1,join='inner').dropna()
j=j[j.index<'2020-04-01']
m=j.groupby(j.index.to_period('M')).apply(lambda g: pd.Series({'r':g.eia.corr(g.tie),'eia':g.eia.mean(),'tie':g.tie.mean()}))
print(m.round(2).to_string())
# find flip point
j['agree']=np.sign(j.eia)==np.sign(j.tie)
x=j.loc['2019-12-01':'2020-01-15','agree'].astype(int)
print(x.rolling(24).mean().dropna().iloc[::12].to_string())
x=j.loc['2019-10-25':'2019-11-08']
r=x.eia.rolling(12).corr(x.tie)
print(r.iloc[::6].round(2).to_string())
