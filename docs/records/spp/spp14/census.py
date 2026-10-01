import zipfile, pandas as pd, hashlib, glob
S="/tmp/claude-0/-home-user-market-simulator/1865f405-6252-5de2-847a-c8d1ca7ab210/scratchpad"
for y in (2023,2024):
    z=zipfile.ZipFile(f"{S}/bc/RTBM-BC-{y}.zip"); m=f"{y}/RTBM-BC-YEARLY-{y}.csv.zip"
    data=z.read(m); open(f"{S}/bc/land/RTBM-BC-YEARLY-{y}.csv.zip","wb").write(data)
    print(y,"yearly extracted",len(data),hashlib.sha256(data).hexdigest(),flush=True)
def read_year(y):
    if y in (2023,2024):
        z=zipfile.ZipFile(f"{S}/bc/land/RTBM-BC-YEARLY-{y}.csv.zip"); n=[x for x in z.namelist() if x.endswith(".csv")][0]
        frames=[pd.read_csv(z.open(n), dtype=str)]
    else:
        frames=[]
        for f in sorted(glob.glob(f"{S}/bc/RTBM-BC-MONTHLY-2025*.csv.zip")):
            z=zipfile.ZipFile(f); n=[x for x in z.namelist() if x.endswith(".csv")][0]; frames.append(pd.read_csv(z.open(n), dtype=str))
    df=pd.concat(frames, ignore_index=True); df.columns=[c.strip() for c in df.columns]; return df
out=[]
for y in (2023,2024,2025):
    df=read_year(y); print(y,"rows",len(df),"cols",list(df.columns),flush=True)
    df["Shadow Price"]=pd.to_numeric(df["Shadow Price"],errors="coerce")
    for c in ("Interconnect","Real Time Effective Limit","Source Limit","Initial Effective Limit","TLR Level"):
        if c not in df.columns: df[c]=pd.NA
    print(y,"State",df["State"].value_counts().to_dict(),"| Interconnect",df["Interconnect"].value_counts(dropna=False).to_dict(),"| Type",df["Constraint Type"].value_counts().to_dict(),flush=True)
    print(y,"GMTIntervalEnd min/max",df["GMTIntervalEnd"].min(),df["GMTIntervalEnd"].max(),"| distinct intervals",df["GMTIntervalEnd"].nunique(),flush=True)
    b=df[(df["State"]=="BINDING")&((df["Interconnect"]=="E")|(df["Interconnect"].isna()))].copy()
    b["gmt"]=pd.to_datetime(b["GMTIntervalEnd"],format="%m/%d/%Y %H:%M:%S",errors="coerce")
    b["hour"]=b["gmt"].dt.floor("h")
    print(y,"binding E rows",len(b),"| distinct hours",b["hour"].nunique(),"| distinct constraints",b["Constraint Name"].nunique(),"| gmt NaT",b["gmt"].isna().sum(),flush=True)
    g=b.groupby(["Constraint Name","Constraint Type","Monitored Facility","Contingent Facility"]).agg(intervals=("hour","size"),hours=("hour","nunique"),mean_sp=("Shadow Price","mean"),max_sp=("Shadow Price","max"),eff_lim_p50=("Real Time Effective Limit",lambda s: pd.to_numeric(s,errors="coerce").median())).reset_index()
    g["year"]=y; out.append(g.sort_values("hours",ascending=False))
    b[["hour","gmt","Constraint Name","Monitored Facility","Contingent Facility","Shadow Price","Real Time Effective Limit","Source Limit","Initial Effective Limit"]].to_parquet(f"{S}/bc/binding_E_{y}.parquet",index=False)
cen=pd.concat(out,ignore_index=True); cen.to_csv(f"{S}/bc/census.csv",index=False); print("census written",len(cen),flush=True)
