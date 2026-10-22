"""EIA-923 Page 1: monthly net generation for SWPP-BA wind (WND) and solar (SUN) plants, by state."""
import io, sys, zipfile
import pandas as pd
D, out = sys.argv[1], sys.argv[2]
M = ['January','February','March','April','May','June','July','August','September','October','November','December']
rows = []
for y in range(2019, 2026):
    with zipfile.ZipFile(f'{D}/f923_{y}.zip') as zf:
        n = next(n for n in zf.namelist() if 'Schedules_2_3_4_5' in n and n.endswith('.xlsx'))
        f = pd.read_excel(zf.open(n), sheet_name=0, header=5)
    f.columns = [' '.join(str(c).split()) for c in f.columns]
    ba = next(c for c in f.columns if c.lower().startswith('balancing authority code'))
    st = next(c for c in f.columns if c.lower().startswith('plant state'))
    pid = next(c for c in f.columns if c.lower().startswith('plant id'))
    fuel = next(c for c in f.columns if c.lower().startswith('reported fuel type'))
    ng = {m: next(c for c in f.columns if c.lower().startswith('netgen') and m.lower() in c.lower()) for m in M}
    f = f[(f[ba] == 'SWPP') & f[fuel].isin(['WND', 'SUN'])]
    for i, m in enumerate(M, 1):
        g = f.groupby([pid, st, fuel])[ng[m]].apply(lambda s: pd.to_numeric(s, errors='coerce').sum()).reset_index()
        g.columns = ['plant_id', 'state', 'fuel', 'net_mwh']; g['year'] = y; g['month'] = i
        rows.append(g)
    print(y, flush=True)
pd.concat(rows).to_csv(out, index=False, compression='gzip')
