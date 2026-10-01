"""SPP-58 leg — psi_2 as the DC PTDF / OTDF of each resolved constituent (PRECOMMIT §2.4–§2.6), on the
network build_network.py wrote. Reads no price, no shadow price, no binding hour, no model output.
Usage: ptdf.py <scratch> <out_dir> [xfmr_scale] [box:inner]"""
import sys, math, re, json, numpy as np, pandas as pd
from scipy.sparse import coo_matrix, csc_matrix
from scipy.sparse.linalg import splu
S, OUT = sys.argv[1], sys.argv[2]
XSCALE = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0          # transformer reactance sensitivity
INNER = (len(sys.argv) > 4 and sys.argv[4] == "inner")              # boundary sensitivity: lon [-105,-90], lat [31,47]
REPO = "/home/user/market-simulator"
N = pd.read_csv(f"{S}/hifld/nodes.csv"); B = pd.read_csv(f"{S}/hifld/branches.csv"); P = pd.read_csv(f"{S}/hifld/plants.csv")
main = json.load(open(f"{S}/hifld/network_meta.json"))["main_comp"]
B = B[B.in_spp].reset_index(drop=True)
if INNER:
    ok = (N.lon.between(-105, -90) & N.lat.between(31, 47)).values
    B = B[ok[B.a] & ok[B.b]].reset_index(drop=True)
B.loc[B.kind == "xfmr", "x_pu"] *= XSCALE
def hav(lat1, lon1, lat2, lon2):
    p = math.pi / 180; a = 0.5 - math.cos((lat2-lat1)*p)/2 + math.cos(lat1*p)*math.cos(lat2*p)*(1-math.cos((lon2-lon1)*p))/2
    return 12742.0 * math.asin(math.sqrt(a))
# ---------------- plants -> zones / pairs (PRECOMMIT §2.4) ----------------
ST = {"ND": "N", "SD": "N", "NE": "N", "MN": "N", "MT": "N", "IA": "N", "KS": "N", "MO": "N", "CO": "N", "OK": "S", "TX": "S", "NM": "S", "AR": "S", "LA": "S"}
sw = P[P.ba.eq("SWPP") & (P.node >= 0) & (P.comp == main)].copy(); sw["zone"] = sw.State.map(ST)
sps = sw.State.eq("NM") | (sw.State.eq("TX") & (((sw.Latitude >= 33.4) & (sw.Longitude <= -100.0)) | ((sw.Latitude >= 32.0) & (sw.Latitude < 33.4) & (sw.Longitude <= -101.9))))
sw["sub"] = np.where(sps, "SPS", sw.zone)
def inj(mask):
    v = np.zeros(len(N)); g = sw[mask].groupby("node").mw.sum(); v[g.index.values] = g.values / g.sum(); return v
PAIRS = {"P-NS": (inj(sw.zone.eq("N")), inj(sw.zone.eq("S"))),
         "P-NOK": (inj(sw.zone.eq("N")), inj(sw.State.eq("OK"))),
         "P-SS": (inj(sw["sub"].eq("S")), inj(sw["sub"].eq("SPS"))),
         "H-NEOK": (inj(sw.State.eq("NE")), inj(sw.State.eq("OK")))}
# sensitivity variants for P-NS (reported, never chosen): wind-only source / gas-only sink need fuel; EIA-860 generator fuel
G = pd.read_parquet(f"{REPO}/data/raw/eia-860/eia860_generator_operable.parquet"); G = G[G.Status.eq("OP")]
G["mw"] = pd.to_numeric(G["Nameplate Capacity (MW)"], errors="coerce")
fuel = G.groupby(["Plant Code", "Energy Source 1"]).mw.sum().reset_index()
wind_p = set(fuel[fuel["Energy Source 1"].eq("WND")]["Plant Code"]); gas_p = set(fuel[fuel["Energy Source 1"].eq("NG")]["Plant Code"])
PAIRS["P-NS-wind2gas"] = (inj(sw.zone.eq("N") & sw["Plant Code"].isin(wind_p)), inj(sw.zone.eq("S") & sw["Plant Code"].isin(gas_p)))
# ---------------- DC solve ----------------
def build_B(Bdf):
    a = Bdf.a.values; b = Bdf.b.values; y = 1.0 / Bdf.x_pu.values
    r = np.concatenate([a, b, a, b]); c = np.concatenate([a, b, b, a]); v = np.concatenate([y, y, -y, -y])
    return csc_matrix(coo_matrix((v, (r, c)), shape=(len(N), len(N))))
slack = int(sw.sort_values("mw", ascending=False).node.iloc[0])
def solve(Bdf, p):
    Bm = build_B(Bdf); keep = np.ones(len(N), bool); keep[slack] = False
    # restrict to the connected component of slack (nodes outside get theta 0 and no flow)
    from scipy.sparse.csgraph import connected_components
    nc, comp = connected_components(Bm, directed=False); keep &= (comp == comp[slack])
    idx = np.where(keep)[0]; lu = splu(Bm[idx][:, idx].tocsc()); th = np.zeros(len(N)); th[idx] = lu.solve(p[idx])
    return th, comp[slack], comp
def flows(Bdf, th):
    return (th[Bdf.a.values] - th[Bdf.b.values]) / Bdf.x_pu.values   # per MW of transfer, oriented a -> b
# ---------------- element map -> branch index ----------------
EM = pd.read_csv(f"{REPO}/docs/handoffs/spp58/element_map.csv")
def cluster_at(lat, lon):
    d = np.hypot((N.lat - lat) * 111, (N.lon - lon) * 88); i = int(d.idxmin()); return int(N.cluster[i]), float(d.min())
def find_branch(spec):
    """returns (branch index, orient) with orient=+1 if branch a->b is the monitored direction, else -1; None if absent"""
    spec = spec.strip(); frm = None
    if "@" in spec: spec, frm = spec.split("@"); frm = tuple(float(x) for x in frm.split(";"))
    if spec.startswith("L:"):
        hid = int(spec[2:]); m = B.index[(B.kind == "line") & (B.hifld_id == hid)]
        if not len(m): return None
        i = int(m[0]); return i, orient_line(i, frm)
    if spec.startswith("R:"):
        tag = spec[2:]; m = B.index[(B.hifld_id == -2) & B.sub1.str.upper().str.startswith(tag.replace("BEAVER1", "BEAVER COUNTY-HITCHLAND 345 CKT1").replace("BEAVER2", "BEAVER COUNTY-HITCHLAND 345 CKT2"))]
        if not len(m): return None
        i = int(m[0]); return i, orient_line(i, frm)
    if spec.startswith("X:"):
        hi_s, lo_s = spec[2:].split("/"); (la1, lo1, kv1) = parse_xy(hi_s); (la2, lo2, kv2) = parse_xy(lo_s)
        c1, d1 = cluster_at(la1, lo1); c2, d2 = cluster_at(la2, lo2)
        n1 = N.index[(N.cluster == c1) & (N.kv == kv1)]; n2 = N.index[(N.cluster == c2) & (N.kv == kv2)]
        if not len(n1) or not len(n2): return None
        n1, n2 = int(n1[0]), int(n2[0])
        m = B.index[((B.a == n1) & (B.b == n2)) | ((B.a == n2) & (B.b == n1))]
        if len(m): i = int(m[0]); return i, (1 if B.a[i] == n1 else -1)
        return ("manual", n1, n2, kv1)   # declared manual co-location: a transformer branch is added
    return None
def parse_xy(s):
    la, rest = s.split(";"); lo, kv = rest.split(":"); return float(la), float(lo), float(kv)
def orient_line(i, frm):
    if frm is None: return 1
    da = hav(frm[0], frm[1], N.lat[B.a[i]], N.lon[B.a[i]]); db = hav(frm[0], frm[1], N.lat[B.b[i]], N.lon[B.b[i]])
    return 1 if da <= db else -1
# add manual co-location transformers (Edwardsville, Viola) once
XF_MVA = {345: 500, 230: 300, 161: 150, 138: 150, 115: 100}
added = {}
for _, r in EM.iterrows():
    if isinstance(r.monitored_spec, str) and r.monitored_spec.startswith("X:"):
        res = find_branch(r.monitored_spec)
        if isinstance(res, tuple) and res and res[0] == "manual":
            _, n1, n2, kv1 = res
            if (n1, n2) not in added:
                B.loc[len(B)] = {"kind": "xfmr", "hifld_id": -3, "a": n1, "b": n2, "kv": kv1, "kv2": N.kv[n2], "len_km": 0.0, "x_pu": 0.10 * 100 / XF_MVA[int(kv1)] * XSCALE, "sub1": "manual co-location", "sub2": r.constraint, "c1": N.cluster[n1], "c2": N.cluster[n2], "owner": "", "in_spp": True}
                added[(n1, n2)] = len(B) - 1
def resolve(spec, frm=None):
    if frm is not None and "@" not in spec and not spec.startswith("X:"): spec = spec + "@" + frm
    res = find_branch(spec)
    if isinstance(res, tuple) and res and res[0] == "manual": _, n1, n2, kv1 = res; return added[(n1, n2)], 1
    return res
# ---------------- compute ----------------
base = {}; comp_slack = None
for k, (src, snk) in PAIRS.items():
    th, cs, comp = solve(B, src - snk); base[k] = flows(B, th); comp_slack = cs; compv = comp
# cut-set identities (K3)
node_zone = np.array([None] * len(N), dtype=object)
for r in sw.itertuples(): node_zone[r.node] = r.zone
nz = pd.Series(node_zone)
def crossing_sum(fl, labels_a, labels_b):
    # branches whose endpoint zones (by nearest SWPP plant zone, propagated by BFS) differ
    return None
# nearest-plant labelling for K3 by multi-source BFS over the SPP component
from collections import deque
adj = [[] for _ in range(len(N))]
for a, b in zip(B.a.values, B.b.values): adj[a].append(b); adj[b].append(a)
def bfs_label(seed_col):
    lab = np.array([None] * len(N), dtype=object); dist = np.full(len(N), 10 ** 9); dq = deque()
    for r in sw.itertuples():
        if dist[r.node] > 0: dist[r.node] = 0; lab[r.node] = getattr(r, seed_col); dq.append(r.node)
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if dist[v] > dist[u] + 1: dist[v] = dist[u] + 1; lab[v] = lab[u]; dq.append(v)
    return lab
labz = bfs_label("zone"); labs = bfs_label("sub")
k3 = {}
# identity: total flow INTO the sink-labelled region from every other label = 1 (P-NS: into S; P-SS: into SPS)
for k, la, sink in (("P-NS", labz, "S"), ("P-SS", labs, "SPS")):
    fl = base[k]; s = 0.0; nb = 0
    for i in range(len(B)):
        za, zb = la[B.a[i]], la[B.b[i]]
        if za != sink and zb == sink: s += fl[i]; nb += 1
        elif za == sink and zb != sink: s -= fl[i]; nb += 1
    k3[k] = (s, nb)
# the P-SS crossing branches (the interface the SPS bubble's boundary IS), with their shares
xs = []
for i in range(len(B)):
    za, zb = labs[B.a[i]], labs[B.b[i]]
    if (za != "SPS" and zb == "SPS") or (za == "SPS" and zb != "SPS"):
        sgn = 1 if zb == "SPS" else -1
        xs.append({"kind": B.kind[i], "hifld_id": int(B.hifld_id[i]), "kv": float(B.kv[i]), "sub1": B.sub1[i], "sub2": B.sub2[i], "from": f"({N.lat[B.a[i]]:.3f},{N.lon[B.a[i]]:.3f})", "to": f"({N.lat[B.b[i]]:.3f},{N.lon[B.b[i]]:.3f})", "share_into_SPS": float(base["P-SS"][i] * sgn)})
pd.DataFrame(xs).to_csv(f"{OUT}/pss_crossing_branches{'_x'+format(XSCALE,'g')+('_inner' if INNER else '')}.csv", index=False)
print("K3 cut-set sums:", {k: (round(v[0], 6), v[1]) for k, v in k3.items()})
# per constituent
rows = []
for _, r in EM.iterrows():
    if r["class"] == "U" or not isinstance(r.monitored_spec, str): rows.append({"constraint": r.constraint, "set": r.set, "class": r["class"], "resolved": False}); continue
    specs = r.monitored_spec[4:].split("|") if r.monitored_spec.startswith("SUM:") else [r.monitored_spec]
    frm = r.from_terminal if isinstance(r.from_terminal, str) and r.from_terminal.strip() else None
    mon = [resolve(s, frm) for s in specs]; mon = [m for m in mon if m is not None]
    if not mon: rows.append({"constraint": r.constraint, "set": r.set, "class": r["class"], "resolved": False, "note": "spec not found in network"}); continue
    cont = []
    if isinstance(r.contingency_spec, str) and r.contingency_spec.strip():
        for s in r.contingency_spec.split("|"):
            c = resolve(s)
            if c is not None: cont.append(c[0])
    out = {"constraint": r.constraint, "set": r.set, "class": r["class"], "resolved": True, "n_elements": len(mon), "n_cont_modelled": len(cont), "cont_declared": int(isinstance(r.contingency_spec, str) and bool(r.contingency_spec.strip()))}
    for k in PAIRS:
        ptdf = sum(base[k][i] * o for i, o in mon)
        out[f"ptdf_{k}"] = ptdf
        if cont:
            Bc = B.drop(index=cont).reset_index(drop=True)
            th, _, _ = solve(Bc, PAIRS[k][0] - PAIRS[k][1]); fc = flows(Bc, th)
            # map monitored indices into Bc
            pos = {old: new for new, old in enumerate([j for j in range(len(B)) if j not in set(cont)])}
            out[f"otdf_{k}"] = sum(fc[pos[i]] * o for i, o in mon if i in pos)
        else: out[f"otdf_{k}"] = np.nan
        out[f"psi2_{k}"] = out[f"otdf_{k}"] if cont else ptdf
    rows.append(out)
R = pd.DataFrame(rows)
tag = f"_x{XSCALE:g}" + ("_inner" if INNER else "")
R.to_csv(f"{OUT}/psi2_by_constituent{tag}.csv", index=False)
json.dump({"xfmr_scale": XSCALE, "inner_box": INNER, "k3": {k: {"sum": v[0], "n_crossing": v[1]} for k, v in k3.items()}, "slack_node": slack,
           "n_nodes_in_solve": int((compv == comp_slack).sum()), "n_branches": int(len(B)), "pairs_source_mw": {k: float(sw[m].mw.sum()) for k, m in (("P-NS N", sw.zone.eq("N")), ("P-NS S", sw.zone.eq("S")), ("P-SS S-rest", sw["sub"].eq("S")), ("P-SS SPS", sw["sub"].eq("SPS")), ("NE", sw.State.eq("NE")), ("OK", sw.State.eq("OK")))}},
          open(f"{OUT}/ptdf_meta{tag}.json", "w"), indent=1)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
print(R[R.resolved.fillna(False)][["constraint", "set", "class", "n_elements", "n_cont_modelled", "ptdf_P-NS", "otdf_P-NS", "psi2_P-NS", "psi2_H-NEOK", "psi2_P-NOK", "psi2_P-SS"]].round(4).to_string(index=False))
