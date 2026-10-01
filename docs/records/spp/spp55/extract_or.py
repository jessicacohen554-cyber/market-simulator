"""Extract the SPP-BAA row (cleared Spin/Supp) from every 5-min RTBM-OR file in the annual zips."""
import zipfile, io, sys
import pandas as pd
S='/tmp/claude-0/-home-user-market-simulator/1ff2487a-af08-5367-b9d9-cba4cd0fc66c/scratchpad/or'
for y in (2023,2024):
    rows=[]
    with zipfile.ZipFile(f'{S}/{y}.zip') as z:
        names=[n for n in z.namelist() if n.endswith('.csv')]
        for n in names:
            b=z.read(n)
            hdr=None
            for line in b.decode('utf-8','ignore').splitlines():
                if line.startswith('Interval'): hdr=line.split(','); continue
                if ',SPP,' in line:
                    rows.append((hdr, line.split(','))); break
    recs=[]
    for hdr,vals in rows:
        d=dict(zip([h.strip() for h in hdr],vals)); recs.append(d)
    df=pd.DataFrame(recs)
    for c in df.columns:
        if c.endswith('_Clr'): df[c]=pd.to_numeric(df[c],errors='coerce')
    df.to_parquet(f'{S}/or_spp_{y}.parquet')
    print(y,len(df),df.columns.tolist(), df[['Spin_Clr','Supp_Clr']].describe().round(0).to_string())
