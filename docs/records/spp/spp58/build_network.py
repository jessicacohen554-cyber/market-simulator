"""SPP-58 step 0 — the reduced DC network from the pulled HIFLD pages (PRECOMMIT §2.2 rules,
applied as written): voltage assignment, endpoint snapping into substation clusters, one node per
(cluster, kV), transformer chains, DC-line removal, back-to-back station cuts, component selection,
plant snapping (EIA-860). Writes nodes.csv / branches.csv / plants.csv to OUT. No PTDF here."""
import json, glob, sys, math, numpy as np, pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
IN, OUT = sys.argv[1], sys.argv[2]
REPO = "/home/user/market-simulator"
# ---- §2.2 declared constants ----
SNAP_M = 300.0                       # endpoint cluster radius
VCLASS = {"UNDER 100": 69.0, "100-161": 138.0, "220-287": 230.0, "345": 345.0, "500": 500.0, "735 AND ABOVE": 765.0}
X_OHM_PER_MI = [(60, 0.80), (100, 0.78), (130, 0.75), (150, 0.73), (200, 0.70), (300, 0.58), (450, 0.53), (700, 0.50)]  # by kV floor
XFMR_MVA = [(60, 50), (100, 100), (130, 150), (200, 300), (300, 500), (450, 1000), (700, 1500)]                    # by high-side kV floor
XFMR_PU_ON_RATING = 0.10; SBASE = 100.0
B2B = {  # back-to-back / asynchronous tie stations to CUT (2 km): SPP-ERCOT and East-West
 "Oklaunion": (34.077, -99.186), "Welsh": (33.054, -94.846), "Eddy County": (32.34, -104.14), "Blackwater": (34.41, -103.27),
 "Lamar": (38.12, -102.56), "Stegall": (41.88, -103.60), "Sidney/Virginia Smith": (41.15, -103.02), "Rapid City": (44.10, -103.20),
 "Miles City": (46.40, -105.85), "Artesia": (32.84, -104.40), "Roswell Tie": (33.35, -104.45), "Fort Thompson": (44.05, -99.45)}
def kv_bucket(table, kv):
    v = table[0][1]
    for lo, val in table:
        if kv >= lo: v = val
    return v
def hav(lat1, lon1, lat2, lon2):
    p = math.pi / 180; a = 0.5 - math.cos((lat2-lat1)*p)/2 + math.cos(lat1*p)*math.cos(lat2*p)*(1-math.cos((lon2-lon1)*p))/2
    return 12742.0 * math.asin(math.sqrt(a))
rows = []
for f in sorted(glob.glob(f"{IN}/page_*.json")):
    for ft in json.load(open(f))["features"]:
        a = ft["attributes"]; paths = ft["geometry"]["paths"]
        pts = [p for path in paths for p in path]
        L = sum(hav(pts[i][1], pts[i][0], pts[i+1][1], pts[i+1][0]) for i in range(len(pts)-1))
        rows.append({**a, "lon1": pts[0][0], "lat1": pts[0][1], "lon2": pts[-1][0], "lat2": pts[-1][1], "len_km": L, "n_paths": len(paths)})
D = pd.DataFrame(rows); print("features", len(D))
D["TYPE"] = D.TYPE.fillna("NOT AVAILABLE"); D["STATUS"] = D.STATUS.fillna("NOT AVAILABLE")
print(D.TYPE.value_counts().to_dict()); print(D.STATUS.value_counts().to_dict())
D["kv"] = np.where(D.VOLTAGE > 0, D.VOLTAGE, D.VOLT_CLASS.map(VCLASS))
print("voltage: numeric", int((D.VOLTAGE > 0).sum()), "class-only", int(((D.VOLTAGE <= 0) & D.kv.notna()).sum()), "unknown", int(D.kv.isna().sum()))
keep = D.kv.notna() & (D.kv >= 60) & ~D.TYPE.str.contains("DC", na=False) & ~D.STATUS.str.contains("UNDER|PROPOS|DECOM", na=False)
print("dropped: kv unknown/<60", int((~(D.kv.notna() & (D.kv >= 60))).sum()), "DC", int(D.TYPE.str.contains("DC", na=False).sum()), "status", int(D.STATUS.str.contains("UNDER|PROPOS|DECOM", na=False).sum()))
D = D[keep].reset_index(drop=True); print("kept", len(D)); print(D.kv.value_counts().sort_index().to_dict())

# ---- §2.3 interconnection labelling (line level), applied BEFORE node building so no ERCOT / Western
# line can share a node with an Eastern one. OWNER decides where the owner is a known ERCOT or
# Western utility; otherwise a declared geography. Verified afterwards by EIA-860 BA codes.
ERCOT_OWNERS = ("ONCOR", "CENTERPOINT", "BANDERA", "BLUEBONNET", "AEP TEXAS", "TEXAS-NEW MEXICO", "PEDERNALES", "GUADALUPE",
    "CITY OF LUBBOCK", "MID-SOUTH", "CITY OF BRYAN", "FARMERS ELECTRIC COOP, INC - (TX)", "TAYLOR ELECTRIC", "BIG COUNTRY",
    "CONCHO VALLEY", "COLEMAN COUNTY", "CENTRAL TEXAS ELEC", "TRI-COUNTY ELECTRIC COOP, INC", "SOUTHWEST TEXAS", "FREDERICKSBURG",
    "CHEROKEE COUNTY", "SHARYLAND", "SAN ANTONIO", "BELLVILLE", "WOOD COUNTY", "KARNES", "NAVASOTA", "SAN BERNARD", "HEMPSTEAD",
    "COMANCHE COUNTY", "COOKE COUNTY", "HOUSTON COUNTY", "NAVARRO", "LOWER COLORADO", "FORT BELKNAP", "CITY OF MASON", "CITY OF BRADY",
    "FAYETTE", "TXU", "SAM HOUSTON", "CITY OF LIVINGSTON", "SOUTH PLAINS ELECTRIC")
WEST_OWNERS = ("PUBLIC SERVICE COMPANY OF NEW MEXICO", "EL PASO ELECTRIC", "TRI-STATE", "TRI STATE", "PUBLIC SERVICE CO OF COLORADO",
    "XCEL ENERGY - COLORADO", "BLACK HILLS", "WAPA", "WESTERN AREA POWER", "JEMEZ", "MORA-SAN MIGUEL", "CENTRAL NEW MEXICO", "OTERO COUNTY",
    "KIT CARSON", "SOCORRO", "NORTHWESTERN ENERGY", "PLATTE RIVER", "COLORADO SPRINGS", "HIGH WEST", "BASIN ELECTRIC", "TRI-STATE G & T")
def ix_label(owner, mlat, mlon):
    o = (owner or "").upper()
    if any(k in o for k in ERCOT_OWNERS): return "ERCOT"
    if any(k in o for k in WEST_OWNERS) and not (mlon > -102.0 and mlat > 41.0): return "WEST"
    # geography for the rest
    if mlat < 37.0 and mlon < -105.0: return "WEST"
    if 37.0 <= mlat < 41.0 and mlon < -102.05: return "WEST"
    if 41.0 <= mlat < 46.0 and mlon < -103.0: return "WEST"
    if mlat >= 46.0 and mlon < -105.5: return "WEST"
    in_tx = (mlat < 36.5) and (mlon > -106.7) and (mlon < -93.5) and not (mlat > 36.5) and not (mlat >= 33.65 and mlon > -103.05 and mlon < -100.0 and False)
    if in_tx and mlat < 36.5 and not (mlat >= 33.62 and mlon > -103.06) and mlon > -103.06:
        # Texas below the Oklahoma line; Eastern pockets: SPS (Panhandle / South Plains), NE Texas (SWEPCO), SE Texas (Entergy)
        if (mlat >= 33.4 and mlon <= -100.0) or (32.0 <= mlat < 33.4 and mlon <= -101.9): return "EAST"
        if mlat >= 31.9 and mlon >= -95.0: return "EAST"
        if 29.9 <= mlat < 31.9 and mlon >= -95.65 and (mlon >= -95.0 or mlat >= 30.25): return "EAST"
        if mlat >= 33.62: return "EAST"   # Oklahoma / NM north of the TX line handled above; guard
        return "ERCOT"
    return "EAST"
D["mlat"] = (D.lat1 + D.lat2) / 2; D["mlon"] = (D.lon1 + D.lon2) / 2
D["ix"] = [ix_label(o, la, lo) for o, la, lo in zip(D.OWNER, D.mlat, D.mlon)]
print("line labels:", D.ix.value_counts().to_dict())
# East-West asynchronous ties (WECC side is WEST of the station): cut the west-side line at the station.
# The SPP-ERCOT back-to-back ties (Oklaunion, Welsh) are NOT in this list: their ERCOT side is removed by
# the owner / geography label, and a direction rule would wrongly remove SPP's own Oklaunion-Tuco 345 kV.
TIE = {"EDDY AC-DC-AC TIE": (32.814, -104.241), "BLACKWATER TIE": (34.301, -103.174), "LAMAR HVDC TIE": (38.207, -102.529),
       "STEGALL": (41.82, -103.943), "VIRGINIA SMITH": (41.164, -102.988), "RAPID CITY DC TIE": (44.01, -103.165), "MILES CITY": (46.41, -105.79)}
def tie_west(r):
    for la, lo in TIE.values():
        for (a1, o1, a2, o2) in ((r.lat1, r.lon1, r.lat2, r.lon2), (r.lat2, r.lon2, r.lat1, r.lon1)):
            if hav(la, lo, a1, o1) <= 1.5 and o2 < lo - 0.2: return True
    return False
D["tie_west"] = [tie_west(r) for r in D.itertuples()]
print("tie west-side lines cut:", int(D.tie_west.sum()))
# ERCOT's Panhandle CREZ 345/138 kV network carries SPS / coop owner strings in HIFLD and joins SPS through a
# drawn Spinning Spur I - II line; it is asynchronous with SPP, so every line touching a CREZ station inside the
# Panhandle box is dropped (declared station list; box lat 33.4-36.5, lon -103.0 to -100.0).
CREZ = ("TULE CANYON", "OGALLALA", "WINDMILL", "ALIBATES", "GRAY", "TESLA", "CROSS", "WHITE RIVER", "RAILHEAD", "AJ SWOPE", "JACK RAMEY",
        "DAVID SWINFORD", "COTTONWOOD", "SPINNING SPUR II", "SPINNING SPUR III", "LONGHORN WIND", "BRISCOE WIND", "MIAMI WIND", "SALT FORK WIND",
        "DERMOTT", "EDITH CLARKE", "SILVERTON", "PANHANDLE", "HEREFORD WIND", "GRANDVIEW", "ROUTE 66", "PALO DURO", "TESLA")
def crez(r):
    if not (33.4 <= r.mlat <= 36.5 and -103.0 <= r.mlon <= -100.0): return False
    for sname in (r.SUB_1, r.SUB_2):
        u = str(sname).upper()
        if any(u == k or u.startswith(k + " ") or u.startswith(k + "|") or (k in u and k not in ("CROSS", "GRAY", "PANHANDLE")) for k in CREZ): return True
        if u in ("CROSS", "GRAY"): return True
    return False
D["crez"] = [crez(r) for r in D.itertuples()]
print("CREZ lines dropped:", int(D.crez.sum()))
D = D[~D.crez]
D = D[(D.ix == "EAST") & ~D.tie_west].reset_index(drop=True); print("kept EAST", len(D))

# ---- endpoint clustering (grid hash + union-find within SNAP_M) ----
E = pd.concat([D[["lon1", "lat1"]].rename(columns={"lon1": "lon", "lat1": "lat"}), D[["lon2", "lat2"]].rename(columns={"lon2": "lon", "lat2": "lat"})]).reset_index(drop=True)
E["sub"] = list(D.SUB_1) + list(D.SUB_2); E["kv"] = list(D.kv) + list(D.kv)
cell = 0.004  # ~400 m
E["cx"] = np.floor(E.lon / cell).astype(int); E["cy"] = np.floor(E.lat / cell).astype(int)
parent = np.arange(len(E))
def find(i):
    while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
    return i
grid = {}
for i, (cx, cy) in enumerate(zip(E.cx, E.cy)): grid.setdefault((cx, cy), []).append(i)
lat = E.lat.values; lon = E.lon.values
for i in range(len(E)):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for j in grid.get((E.cx.iat[i]+dx, E.cy.iat[i]+dy), []):
                if j > i and hav(lat[i], lon[i], lat[j], lon[j]) * 1000 <= SNAP_M:
                    ri, rj = find(i), find(j)
                    if ri != rj: parent[ri] = rj
E["cl"] = [find(i) for i in range(len(E))]
cl = E.groupby("cl").agg(lat=("lat", "mean"), lon=("lon", "mean"), n=("lat", "size"),
                          subs=("sub", lambda s: "|".join(sorted(set(str(x) for x in s if isinstance(x, str) and x not in ("NOT AVAILABLE", "UNKNOWN") and not x.startswith("UNKNOWN")))))).reset_index()
print("endpoint clusters", len(cl))
E = E.merge(cl[["cl"]].assign(cid=np.arange(len(cl))), on="cl")
n = len(D); D["c1"] = E.cid.values[:n]; D["c2"] = E.cid.values[n:]
# ---- nodes = (cluster, kv); transformer chains between consecutive levels present ----
node_key = {}; nodes = []
def node(c, kv):
    k = (int(c), float(kv))
    if k not in node_key: node_key[k] = len(nodes); nodes.append(k)
    return node_key[k]
br = []
for r in D.itertuples():
    a, b = node(r.c1, r.kv), node(r.c2, r.kv)
    if a == b: continue
    x = kv_bucket(X_OHM_PER_MI, r.kv) * r.len_km / 1.609344 / (r.kv ** 2 / SBASE)
    x = max(x, 1e-4)
    br.append({"kind": "line", "hifld_id": int(r.OBJECTID_1), "a": a, "b": b, "kv": r.kv, "kv2": r.kv, "len_km": r.len_km, "x_pu": x,
               "sub1": r.SUB_1, "sub2": r.SUB_2, "c1": int(r.c1), "c2": int(r.c2), "owner": r.OWNER})
# Registry-completed branches: SPS 345 kV ties named in SPP's own Flowgates.csv whose BOTH terminals exist in
# HIFLD but whose line feature is absent from this HIFLD edition. Added with the same reactance rule (length =
# great-circle between the terminal clusters x 1.15 routing factor). Declared list; each is reported in the FINDING.
REG_ADD = [("BORDER-TUCO 345 (SPPSPSTIES / TEMP50 contingency)", (35.201, -99.930), (33.869, -101.843), 345.0),
           ("BEAVER COUNTY-HITCHLAND 345 ckt1 (SPPSPSTIES)", (36.525, -100.950), (36.496, -101.392), 345.0),
           ("BEAVER COUNTY-HITCHLAND 345 ckt2 (SPPSPSTIES)", (36.525, -100.950), (36.496, -101.392), 345.0)]
def nearest_cluster(la, lo, kv):
    d = np.array([hav(la, lo, x, y) for x, y in zip(cl.lat, cl.lon)]); i = int(np.argmin(d)); return i, float(d[i])
for tag, (la1, lo1), (la2, lo2), kv in REG_ADD:
    c1, d1 = nearest_cluster(la1, lo1, kv); c2, d2 = nearest_cluster(la2, lo2, kv)
    if d1 > 1.0 or d2 > 1.0: print("REG_ADD terminal not found:", tag, d1, d2); continue
    Lkm = hav(la1, lo1, la2, lo2) * 1.15
    x = kv_bucket(X_OHM_PER_MI, kv) * Lkm / 1.609344 / (kv ** 2 / SBASE)
    br.append({"kind": "line", "hifld_id": -2, "a": node(c1, kv), "b": node(c2, kv), "kv": kv, "kv2": kv, "len_km": Lkm, "x_pu": x,
               "sub1": tag, "sub2": "REGISTRY", "c1": c1, "c2": c2, "owner": "Flowgates.csv"}); print("REG_ADD:", tag, f"{Lkm:.0f} km")
lv = {}
for (c, kv) in nodes: lv.setdefault(c, set()).add(kv)
nx_ = 0
for c, kvs in lv.items():
    ks = sorted(kvs)
    for lo, hi in zip(ks[:-1], ks[1:]):
        rating = kv_bucket(XFMR_MVA, hi)
        br.append({"kind": "xfmr", "hifld_id": -1, "a": node(c, hi), "b": node(c, lo), "kv": hi, "kv2": lo, "len_km": 0.0,
                   "x_pu": XFMR_PU_ON_RATING * SBASE / rating, "sub1": "", "sub2": "", "c1": c, "c2": c, "owner": ""}); nx_ += 1
B = pd.DataFrame(br); N = pd.DataFrame(nodes, columns=["cluster", "kv"]).merge(cl[["lat", "lon", "n", "subs"]].reset_index(drop=True).rename_axis("cluster").reset_index(), on="cluster")
print("nodes", len(N), "line branches", int((B.kind == "line").sum()), "transformer branches", nx_)
# Manual transformer cuts (declared): two ERCOT plant sites in the NE-Texas ERCOT/SWEPCO interleave whose ERCOT
# 345 kV lines carry SWEPCO / Upshur owner strings in HIFLD and end within the snap radius of a SWEPCO 138 kV
# bus, so the transformer chain would join the interconnections (min-cut = that transformer, FINDING §2).
MANUAL_XFMR_CUT = {"Martin Lake": (32.257, -94.575), "Tenaska Gateway": (32.018, -94.621)}
keepb = np.ones(len(B), bool)
for nm, (la, lo) in MANUAL_XFMR_CUT.items():
    m = (B.kind == "xfmr") & np.array([hav(la, lo, N.lat[a], N.lon[a]) <= 1.0 for a in B.a])
    print(f"  manual xfmr cut {nm}: {int(m.sum())} branch(es)"); keepb &= ~m.values
B = B[keepb].reset_index(drop=True)
N["cut"] = False
Bk = B[~(N.cut.values[B.a] | N.cut.values[B.b])]
# ---- components ----
A = coo_matrix((np.ones(len(Bk)), (Bk.a.values, Bk.b.values)), shape=(len(N), len(N)))
ncomp, comp = connected_components(A, directed=False); N["comp"] = comp
# ---- plants (EIA-860 operable, snapped) ----
P = pd.read_parquet(f"{REPO}/data/raw/eia-860/eia860_plant.parquet"); G = pd.read_parquet(f"{REPO}/data/raw/eia-860/eia860_generator_operable.parquet")
G = G[G.Status.eq("OP")]; G["Nameplate Capacity (MW)"] = pd.to_numeric(G["Nameplate Capacity (MW)"], errors="coerce"); cap = G.groupby("Plant Code")["Nameplate Capacity (MW)"].sum().rename("mw")
P = P.merge(cap, left_on="Plant Code", right_index=True, how="inner")
P["Latitude"] = pd.to_numeric(P.Latitude, errors="coerce"); P["Longitude"] = pd.to_numeric(P.Longitude, errors="coerce")
P = P[P.Latitude.between(29, 49.5) & P.Longitude.between(-108, -88)].copy()
P["ba"] = P["Balancing Authority Code"]; P["gkv"] = pd.to_numeric(P["Grid Voltage (kV)"], errors="coerce")
# nearest cluster within 15 km; prefer a node at the plant's grid voltage
clat = N.lat.values; clon = N.lon.values
def snap(r):
    d = np.array([hav(r.Latitude, r.Longitude, la, lo) for la, lo in zip(clat, clon)])
    d[N.cut.values] = 1e9
    if np.nanmin(d) > 15: return -1, np.nan
    cand = np.where(d <= 15)[0]
    if pd.notna(r.gkv):
        same = cand[np.abs(N.kv.values[cand] - r.gkv) <= 5]
        if len(same): i = same[np.argmin(d[same])]; return int(i), float(d[i])
    i = cand[np.argmin(d[cand])]; return int(i), float(d[i])
sn = [snap(r) for r in P.itertuples()]; P["node"] = [s[0] for s in sn]; P["snap_km"] = [s[1] for s in sn]
P["comp"] = np.where(P.node >= 0, N.comp.values[P.node.clip(lower=0)], -1)
sw = P[P.ba.eq("SWPP")]; main = sw[sw.node >= 0].groupby("comp").mw.sum().idxmax()
print("SPP component", main, "| SWPP nameplate in it", round(sw[sw.comp == main].mw.sum()), "of", round(sw.mw.sum()), "(unsnapped", round(sw[sw.node < 0].mw.sum()), ")")
for ba in ("ERCO", "SWPP", "MISO", "AECI", "WACM", "PNM", "EPE", "PSCO", "TVA", "SOCO"):
    x = P[P.ba.eq(ba)]; print(f"  {ba}: nameplate {x.mw.sum():,.0f} MW; in SPP component {x[x.comp==main].mw.sum():,.0f}; unsnapped {x[x.node<0].mw.sum():,.0f}")
print("nodes in SPP component", int((N.comp == main).sum()), "branches", int(((N.comp.values[Bk.a] == main)).sum()))
N.to_csv(f"{OUT}/nodes.csv", index=False); Bk.assign(in_spp=(N.comp.values[Bk.a] == main)).to_csv(f"{OUT}/branches.csv", index=False)
P[["Plant Code", "Plant Name", "State", "ba", "Latitude", "Longitude", "gkv", "mw", "node", "snap_km", "comp"]].to_csv(f"{OUT}/plants.csv", index=False)
json.dump({"main_comp": int(main)}, open(f"{OUT}/network_meta.json", "w"))
