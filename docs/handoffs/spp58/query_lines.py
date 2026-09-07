"""SPP-58 helper — list HIFLD line branches by name pair / voltage / box, for the element join."""
import sys, pandas as pd, numpy as np
S = sys.argv[1]
N = pd.read_csv(f"{S}/hifld/nodes.csv"); B = pd.read_csv(f"{S}/hifld/branches.csv"); L = B[B.kind == "line"].copy()
L["la1"] = N.lat.values[L.a]; L["lo1"] = N.lon.values[L.a]; L["la2"] = N.lat.values[L.b]; L["lo2"] = N.lon.values[L.b]
def names(kw1, kw2=None, kv=None):
    s1 = L.sub1.fillna("").str.upper(); s2 = L.sub2.fillna("").str.upper()
    m = (s1.str.contains(kw1) | s2.str.contains(kw1))
    if kw2: m &= (s1.str.contains(kw2) | s2.str.contains(kw2))
    if kv: m &= (L.kv == kv)
    return L[m]
def box(la0, la1, lo0, lo1, kv=None):
    m = ((L.la1.between(la0, la1) & L.lo1.between(lo0, lo1)) | (L.la2.between(la0, la1) & L.lo2.between(lo0, lo1)))
    if kv: m &= (L.kv == kv)
    return L[m]
def show(df, tag):
    print(f"--- {tag}: {len(df)}")
    for r in df.itertuples():
        print(f"  id{r.hifld_id} kv{int(r.kv)} n{r.a}-n{r.b} c{r.c1}-c{r.c2} ({r.la1:.3f},{r.lo1:.3f})->({r.la2:.3f},{r.lo2:.3f}) {r.len_km:.1f}km {r.sub1}|{r.sub2} [{r.owner}]")
def levels(c):
    return sorted(N[N.cluster == c].kv.tolist())
if __name__ == "__main__":
    for q in sys.argv[2:]:
        parts = q.split(";")
        if parts[0] == "n": show(names(parts[1].upper(), parts[2].upper() if len(parts) > 2 and parts[2] else None, float(parts[3]) if len(parts) > 3 and parts[3] else None), q)
        elif parts[0] == "b": show(box(*[float(x) for x in parts[1:5]], float(parts[5]) if len(parts) > 5 and parts[5] else None), q)
        elif parts[0] == "p":
            la, lo = float(parts[1]), float(parts[2]); d = np.hypot((N.lat - la) * 111, (N.lon - lo) * 88)
            for c in sorted(set(N.cluster[d <= 1.5])): print(q, "cluster", c, levels(c), N[N.cluster == c][["lat", "lon", "subs"]].iloc[0].tolist())
