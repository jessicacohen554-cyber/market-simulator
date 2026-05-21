"""Render the interactive HTML calibration report from persisted bundles.

Self-contained (no external JS/CSS). A top-level Charts/Tables page toggle over:
  * 24h x 365d commitment heatmaps — CAMPD actual vs model result, per plant
    or group aggregate, with a CF colour ramp;
  * average-hourly dispatch-profile line chart (CF% or MW) by period, with the
    must-run floor line and avg/bias/peak-hour stats;
  * annual-total bar chart (model vs CAMPD vs EIA-923);
  * monthly-variation line chart (model vs CAMPD vs EIA-923);
  * Tables page: per-plant hourly r/NRMSE vs CAMPD + the [3b]/[5] tables.

Hourly CF series (model from the dispatch parquet, CAMPD net from
campd.parquet) are embedded base64 uint8 (0-100). This is the documented
calibration report artifact — see docs/calibration-report.md.

Usage:
    python scripts/render_calibration_html.py [BUNDLE ...] [--out FILE]
    # default bundles: results/calibration/stgas_{2023,2024,2025}
"""
from __future__ import annotations

import argparse
import base64
import html
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rcf", str(REPO / "scripts" / "run_calibration_full.py"))
rcf = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(rcf)

from market_sim.data.fleet import COAL_MUSTRUN_BY_PLANT  # noqa: E402

GROUP_LABEL = {
    "COAL_LIGNITE": "Coal Lignite", "COAL_PRB": "Coal PRB",
    "CC_REGULAR": "CC Regular", "CC_CHP": "CC CHP", "CT_PEAKER": "CT Peaker",
    "ST_GAS": "Steam Gas",
}
HEAT_GROUPS = list(GROUP_LABEL)
_CUM = np.cumsum([0] + list(rcf._DAYS_IN_MONTH)) * 24  # month hour boundaries

# CHP behind-the-meter host self-supply removed from the grid LP and added back
# flat in the report. Matches ScenarioConfig.chp_btm_floor_pct used by the
# steam-following cogen model (the grid-delivered steam base is already in the
# dispatch parquet, so only the host floor is re-added here).
CHP_BTM_FLOOR_PCT = 40.0


def _b64(cf: np.ndarray) -> str:
    a = np.clip(np.nan_to_num(cf), 0, 100).round().astype(np.uint8)
    if a.shape[0] < 8760:
        a = np.concatenate([a, np.zeros(8760 - a.shape[0], np.uint8)])
    return base64.b64encode(a[:8760].tobytes()).decode()


def _monthly_gwh(mw: np.ndarray) -> list[float]:
    return [round(float(mw[_CUM[m]:_CUM[m + 1]].sum()) / 1e3, 2) for m in range(12)]


def _rfit(model: np.ndarray, obs: np.ndarray):
    """Pearson r / NRMSE of model vs obs (None when flat or undefined)."""
    m = np.nan_to_num(np.asarray(model, float))
    o = np.nan_to_num(np.asarray(obs, float))
    if m.std() == 0 or o.std() == 0:
        return None, None
    r = float(np.corrcoef(m, o)[0, 1])
    nr = float(np.sqrt(np.mean((m - o) ** 2)) / (o.mean() or 1))
    if not (np.isfinite(r) and np.isfinite(nr)):
        return None, None
    return round(r, 3), round(nr, 3)


def build_payload(bundles: dict[int, Path]):
    bins = pd.read_csv(REPO / "inputs" / "custom-bin-assignments.csv")
    npl = dict(zip(bins["Plant_Code"].astype(int), bins["Nameplate_MW"]))
    pname = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Name"]))
    pgroup = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Group"]))
    pmr = dict(zip(bins["Plant_Code"].astype(int), bins["Pct_Must_Run"]))

    def mrpct(code, group):
        if group == "COAL":
            return COAL_MUSTRUN_BY_PLANT.get(int(code), float(pmr.get(code, 0)))
        if "CHP" in str(group):
            return CHP_BTM_FLOOR_PCT  # host BTM removed from grid = report add-back
        return float(pmr.get(code, 0.0))

    series, group_plants = {}, {}
    for year, bdir in bundles.items():
        disp = pd.read_parquet(bdir / "dispatch" / f"{year}_P1.parquet")
        camp = pd.read_parquet(bdir / "campd.parquet"); camp = camp[camp["year"] == year]
        e923 = pd.read_parquet(bdir / "eia923.parquet"); e923 = e923[e923["year"] == year]
        mcols = [f"m{i:02d}" for i in range(1, 13)]
        dm = disp[disp["plant_code"] > 0]
        mwp = {int(c): g.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0).to_numpy()
               for c, g in dm.groupby("plant_code", observed=True)}
        cnp = {}
        for c, g in camp.groupby("plant_id", observed=True):
            a = np.nan_to_num(g.sort_values("hour")["net_mw"].to_numpy())
            cnp[int(c)] = np.concatenate([a, np.zeros(max(0, 8760 - a.shape[0]))])[:8760]
        supply = dm.groupby("plant_code", observed=True)["supply"].first().to_dict()
        eia_ann = e923.groupby("plant_id")["annual_mwh"].sum().to_dict()
        eia_pmon = {int(i): row.to_numpy() / 1e3
                    for i, row in e923.groupby("plant_id")[mcols].sum().iterrows()}

        agg = {g: {"m": np.zeros(8760), "g": np.zeros(8760), "c": np.zeros(8760),
                   "e": np.zeros(12), "npl": 0.0, "mr": 0.0, "ea": 0.0, "n": 0}
               for g in HEAT_GROUPS}
        for c in sorted(set(mwp) | set(cnp)):
            grp = pgroup.get(c)
            hg = ("COAL_LIGNITE" if supply.get(c) == "lignite"
                  else "COAL_PRB" if grp == "COAL" else grp)
            if hg not in HEAT_GROUPS:
                continue
            cap = float(npl.get(c, 0.0)) or 1.0
            mrp = mrpct(c, grp)
            grid = mwp.get(c, np.zeros(8760)); cn = cnp.get(c, np.zeros(8760))
            # Only plants that both contribute to the grid LP and report to
            # CAMPD are comparable here; drop no-CAMPD and full-BTM (host-steam
            # only, no grid contribution) plants from the report entirely.
            if float(grid.sum()) <= 0 or float(cn.sum()) <= 0:
                continue
            # CHP host-steam must-run is behind-the-meter: it's removed from the
            # LP grid dispatch, but CAMPD reports the full plant. For the hourly
            # *shape* views (heatmap, dispatch profile) and the hourly r/NRMSE
            # fit we add it back flat so CHP doesn't read as ~0 against CAMPD.
            # The annual/monthly totals stay grid-only (true model output), and
            # non-CHP must-run is already in the grid LP so nothing is added.
            btm = cap * mrp / 100.0 if "CHP" in (grp or "") else 0.0
            mt = grid + btm  # heatmap / dispatch profile / hourly fit only
            r, nr = _rfit(mt, cn)
            emon_p = eia_pmon.get(c, np.zeros(12))
            series[f"{year}|plant:{c}"] = {
                "name": str(pname.get(c, c)), "group": hg, "npl": round(cap),
                "mrpct": round(mrp, 1),
                "model": _b64(100 * mt / cap), "campd": _b64(100 * cn / cap),
                "m_ann": round(float(grid.sum()) / 1e6, 3), "c_ann": round(float(cn.sum()) / 1e6, 3),
                "e_ann": round(float(eia_ann.get(c, 0.0)) / 1e6, 3),
                "m_mon": _monthly_gwh(grid), "c_mon": _monthly_gwh(cn),
                "e_mon": [round(float(x), 2) for x in emon_p],
                "r": r, "nrmse": nr,
            }
            group_plants.setdefault(f"{year}|{hg}", []).append(
                {"code": int(c), "name": str(pname.get(c, c))})
            a = agg[hg]; a["m"] += mt; a["g"] += grid; a["c"] += cn; a["npl"] += cap
            a["mr"] += cap * mrp / 100.0; a["e"] += emon_p
            a["ea"] += float(eia_ann.get(c, 0.0)) / 1e6; a["n"] += 1
        for hg, a in agg.items():
            cap = a["npl"] or 1.0
            r, nr = _rfit(a["m"], a["c"])
            series[f"{year}|{hg}"] = {
                "name": f"{GROUP_LABEL[hg]} (aggregate)", "group": hg,
                "npl": round(cap), "mrpct": round(100 * a["mr"] / cap, 1), "n": a["n"],
                "model": _b64(100 * a["m"] / cap), "campd": _b64(100 * a["c"] / cap),
                "m_ann": round(float(a["g"].sum()) / 1e6, 3), "c_ann": round(float(a["c"].sum()) / 1e6, 3),
                "e_ann": round(float(a["ea"]), 3),
                "m_mon": _monthly_gwh(a["g"]), "c_mon": _monthly_gwh(a["c"]),
                "e_mon": [round(float(x), 2) for x in a["e"]],
                "r": r, "nrmse": nr,
            }
    return {"years": sorted(bundles), "groups": HEAT_GROUPS,
            "groupLabel": GROUP_LABEL, "series": series, "groupPlants": group_plants}


def _diffcls(d):
    a = abs(d); return "good" if a < 5 else "ok" if a < 15 else "bad"


def per_plant_fit_table(payload):
    """Per-plant hourly r/NRMSE from the same payload as the charts, so the
    figures match (CHP rows are BTM-aware, after parasitic correction)."""
    yrs = payload["years"]
    rows = {}
    for key, d in payload["series"].items():
        if "|plant:" not in key:
            continue
        year = int(key.split("|", 1)[0]); code = int(key.split("plant:")[1])
        rows.setdefault(code, {"name": d["name"], "grp": d["group"], "yr": {}})
        rows[code]["yr"][year] = (d["r"], d["nrmse"])
    head = ["plant", "group"] + [f"{y} r" for y in yrs] + [f"{y} NRMSE" for y in yrs]
    body = ""
    for code in sorted(rows, key=lambda c: (rows[c]["grp"], rows[c]["name"])):
        rec = rows[code]; cells = [rec["name"], rec["grp"]]
        cells += [f"{rec['yr'][y][0]:.3f}" if rec["yr"].get(y, (None,))[0] is not None
                  else "—" for y in yrs]
        cells += [f"{rec['yr'][y][1]:.3f}" if y in rec["yr"] and rec["yr"][y][1] is not None
                  else "—" for y in yrs]
        body += "<tr>" + "".join(
            f'<td class="{"lbl" if i < 2 else "num"}">{html.escape(str(c))}</td>'
            for i, c in enumerate(cells)) + "</tr>"
    th = "".join(f"<th>{html.escape(x)}</th>" for x in head)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def _thermal(disp, e923, btm):
    mh = rcf._class_hourly(disp); ann = rcf._e923_annual(e923)
    bt = dict(zip(btm["klass"], btm["btm_twh"]))
    rows = ""
    for c in ["CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP",
              "COAL_LIGNITE", "COAL_PRB"]:
        grid = mh.get(c, np.zeros(1)).sum() / 1e6; b = bt.get(c, 0.0)
        m = grid + b; e = ann.get(c, 0.0); d = 100 * (m - e) / e if e else float("nan")
        ds = f"{d:+.1f}%" if e else "—"
        rows += (f"<tr><td class=lbl>{c}</td><td class=num>{grid:.2f}</td>"
                 f"<td class=num>{b:.2f}</td><td class=num>{m:.2f}</td>"
                 f"<td class=num>{e:.2f}</td><td class='num {_diffcls(d) if e else ''}'>{ds}</td></tr>")
    return ("<table><thead><tr><th>class</th><th>grid</th><th>BTM</th><th>model</th>"
            f"<th>EIA-923</th><th>Δ%</th></tr></thead><tbody>{rows}</tbody></table>")


def _hourly(disp, e930):
    mh = rcf._class_hourly(disp)
    e = {s: e930[e930["series"] == s].sort_values("hour")["mw"].to_numpy()
         for s in e930["series"].unique()}
    T = e["coal"].shape[0]
    flat = sum(mh.get(c, np.zeros(T)).sum() for c in ("CC_CHP", "CT_CHP", "ST_CHP")) / T
    rows = ""
    for n, m, o in [("gas (non-CHP)", sum(mh.get(c, np.zeros(T)) for c in rcf._NONCHP_GAS), e["gas"] - flat),
                    ("coal", sum(mh.get(c, np.zeros(T)) for c in rcf._COAL_CLASSES), e["coal"]),
                    ("nuclear", mh.get("nuclear", np.zeros(T)), e.get("nuclear")),
                    ("solar", mh.get("solar", np.zeros(T)), e["solar"]),
                    ("wind", mh.get("wind", np.zeros(T)), e["wind"])]:
        if o is None:
            continue
        rows += (f"<tr><td class=lbl>{n}</td><td class=num>{rcf._pearson_r(m, o):.3f}</td>"
                 f"<td class=num>{rcf._nrmse(m, o):.3f}</td></tr>")
    return ("<table><thead><tr><th>fuel</th><th>Pearson r</th><th>NRMSE</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>")


def tabular_html(bundles, payload):
    out = ["<h3>Per-plant hourly fit vs CAMPD net (r / NRMSE, after parasitic correction)</h3>",
           per_plant_fit_table(payload)]
    for year, bdir in bundles.items():
        disp = pd.read_parquet(bdir / "dispatch" / f"{year}_P1.parquet")
        e923 = pd.read_parquet(bdir / "eia923.parquet"); e923 = e923[e923["year"] == year]
        e930 = pd.read_parquet(bdir / "eia930.parquet"); e930 = e930[e930["year"] == year]
        btm = pd.read_parquet(bdir / "btm.parquet")
        btm = btm[(btm["year"] == year) & (btm["pass"] == "P1")]
        out += [f"<h3>ERCOT {year} — thermal by class vs EIA-923 (TWh)</h3>",
                _thermal(disp, e923, btm),
                f"<h4>ERCOT {year} — hourly fit vs EIA-930</h4>", _hourly(disp, e930)]
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="*")
    ap.add_argument("--out", default=str(REPO / "results" / "calibration" / "calibration-report.html"))
    args = ap.parse_args()
    if args.bundles:
        bundles = {int(json.loads((Path(b) / "meta.json").read_text())["years"][0]): Path(b)
                   for b in args.bundles}
    else:
        bundles = {y: REPO / "results" / "calibration" / f"stgas_{y}" for y in (2023, 2024, 2025)}
    payload = build_payload(bundles)
    out = Path(args.out)
    out.write_text(TEMPLATE
                   .replace("__DATA__", json.dumps(payload))
                   .replace("__TABULAR__", tabular_html(bundles, payload))
                   .replace("__GEN__", datetime.now().strftime("%Y-%m-%d %H:%M")))
    print(f"wrote {out}  ({out.stat().st_size/1e6:.1f} MB, {len(payload['series'])} series)")


TEMPLATE = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>CAMPD vs Model — Dispatch Comparison</title><style>
:root{--bg:#f6f7f9;--card:#fff;--bd:#e3e7ec;--ink:#1a1f29;--mut:#6b7480;--blue:#2f9bd6;--orange:#ef7d2b;--green:#7aa884;}
*{box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);margin:0;padding:18px}
.wrap{max-width:1000px;margin:0 auto}h1{font-size:22px;margin:0 0 2px}.sub{color:var(--mut);font-size:13px;margin:0 0 14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px 18px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.row{display:flex;flex-wrap:wrap;gap:18px;align-items:center}
.lab{font-size:11px;letter-spacing:.06em;color:var(--mut);font-weight:600;text-transform:uppercase;margin-right:6px}
.seg{display:inline-flex;background:#eef1f4;border-radius:9px;padding:3px}
.seg button{border:0;background:transparent;padding:6px 13px;border-radius:7px;font-size:13px;cursor:pointer;color:var(--mut);font-weight:600}
.seg button.on{background:#fff;color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.12)}
select{font-size:14px;padding:7px 10px;border:1px solid var(--bd);border-radius:8px;background:#fff}
h2{font-size:18px;margin:2px 0}h3{font-size:15px;margin:18px 0 8px}h4{font-size:13px;margin:14px 0 6px;color:#3a4250}
.hsub{color:var(--mut);font-size:12px;margin:0 0 10px}
canvas.heat{width:100%;height:140px;image-rendering:pixelated;border:1px solid var(--bd);border-radius:6px;background:#eef3f7;display:block}
.ax{display:flex;justify-content:space-between;color:var(--mut);font-size:11px;margin:3px 2px 0}
.legend{display:flex;align-items:center;gap:14px;font-size:12px;color:var(--mut);margin:8px 0;flex-wrap:wrap}
.ramp{height:10px;width:150px;border-radius:3px;background:linear-gradient(90deg,#e8f3f7,#7fc4e6,#86c98f,#f2d65c,#ef8f3c,#c0392b)}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}
.stat{flex:1;min-width:115px;background:#f8fafc;border:1px solid var(--bd);border-radius:9px;padding:9px 12px}
.stat .k{font-size:11px;color:var(--mut);text-transform:uppercase}.stat .v{font-size:20px;font-weight:700;margin-top:2px}
table{border-collapse:collapse;width:100%;background:#fff;border:1px solid var(--bd);border-radius:8px;overflow:hidden;font-size:13px;margin:6px 0 14px}
th,td{padding:6px 10px;border-bottom:1px solid #eef1f4;text-align:left}th{background:#f0f3f6;font-size:11px;text-transform:uppercase;color:#46505f}
td.num{text-align:right;font-variant-numeric:tabular-nums}.good{color:#0f7d3d}.ok{color:#9a6700}.bad{color:#c01c28;font-weight:600}
.hide{display:none}.tabs{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0}
.tabs button{border:1px solid var(--bd);background:#fff;border-radius:7px;padding:5px 10px;font-size:12px;cursor:pointer;color:var(--mut)}
.tabs button.on{background:var(--blue);color:#fff;border-color:var(--blue)}
svg{width:100%;height:230px;display:block}
#tip{position:fixed;display:none;pointer-events:none;background:#1a1f29;color:#fff;font-size:12px;line-height:1.55;padding:7px 10px;border-radius:8px;box-shadow:0 4px 14px rgba(0,0,0,.28);z-index:99;max-width:240px;white-space:nowrap}
canvas.heat,svg{cursor:crosshair}
</style></head><body><div class=wrap>
<div id=tip></div>
<h1>CAMPD vs Model — Dispatch Comparison</h1>
<p class=sub>Hourly generation vs EPA CAMPD actuals · generated __GEN__</p>
<noscript><div class=card style="border-color:#c01c28;color:#c01c28">This report is interactive and needs JavaScript. Your viewer has it disabled (in-chat previews often sandbox scripts) — <b>download the file and open it in a web browser</b>.</div></noscript>
<div id=diag class=card style="border-color:#e0a800;color:#9a6700">Loading… if this message does not disappear, your viewer is blocking JavaScript or the file was truncated — download it and open in a web browser.</div>
<div class=card><div class=row><span class=lab>Page</span><span class=seg id=view>
  <button data-v=charts class=on>Charts</button><button data-v=tables>Tables</button></span></div></div>

<div id=charts-view>
<div class=card><div class=row>
  <div><span class=lab>Year</span><span class=seg id=yearSel></span></div>
  <div><span class=lab>Group</span><select id=groupSel></select></div>
  <div><span class=lab>Plant</span><select id=plantSel></select></div></div></div>
<div class=card><h2>Commitment heatmap</h2><p class=hsub id=heatSub></p>
  <div class=legend><span>0%</span><span class=ramp></span><span>100% CF</span></div>
  <h4>CAMPD actual</h4><canvas class=heat id=heatC width=365 height=24></canvas><div class=ax id=axC></div>
  <h4>Model result</h4><canvas class=heat id=heatM width=365 height=24></canvas><div class=ax id=axM></div></div>
<div class=card><h2>Dispatch comparison</h2><p class=hsub id=dispSub></p>
  <div class=row><span class=lab>Mode</span><span class=seg id=modeSel>
    <button data-m=cf class=on>CF %</button><button data-m=mw>MW</button></span></div>
  <div class=tabs id=periodSel></div>
  <div class=legend><span style="color:var(--blue)">— CAMPD actual</span>
    <span style="color:var(--orange)">— Model result</span><span style="color:#9aa">- - must-run floor</span></div>
  <svg id=profile viewBox="0 0 720 230"></svg><div class=stats id=profStats></div></div>
<div class=card><h2>Annual total — model vs CAMPD vs EIA-923 (TWh)</h2><svg id=annual viewBox="0 0 720 230"></svg></div>
<div class=card><h2>Monthly generation (GWh)</h2>
  <div class=legend><span style="color:var(--blue)">— CAMPD</span>
    <span style="color:var(--orange)">— Model</span><span style="color:var(--green)">— EIA-923</span></div>
  <svg id=monthly viewBox="0 0 720 230"></svg></div></div>

<div id=tables-view class=hide><div class=card>__TABULAR__</div></div>

<script>
const D=__DATA__;const MONTHS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const DIM=[31,28,31,30,31,30,31,31,30,31,30,31];
let st={year:D.years[0],group:D.groups[0],plant:"agg",mode:"cf",period:"annual"};
function dec(b){const s=atob(b),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return a;}
function cur(){return D.series[st.plant==="agg"?st.year+"|"+st.group:st.year+"|plant:"+st.plant];}
const tip=document.getElementById("tip");
function showTip(h,e){tip.innerHTML=h;tip.style.display="block";const p=14,w=tip.offsetWidth,ht=tip.offsetHeight;
 let x=e.clientX+p,y=e.clientY+p;if(x+w>innerWidth)x=e.clientX-w-p;if(y+ht>innerHeight)y=e.clientY-ht-p;
 tip.style.left=x+"px";tip.style.top=y+"px";}
function hideTip(){tip.style.display="none";}
function hoverX(svg,xs,rows){svg.onmousemove=e=>{const r=svg.getBoundingClientRect(),vx=(e.clientX-r.left)/r.width*720;
 let bi=0,bd=1e9;for(let i=0;i<xs.length;i++){const dd=Math.abs(xs[i]-vx);if(dd<bd){bd=dd;bi=i;}}showTip(rows[bi],e);};
 svg.onmouseleave=hideTip;}
function heatTip(cv,cf,which){cv.onmousemove=e=>{const r=cv.getBoundingClientRect();
 const day=Math.floor((e.clientX-r.left)/r.width*365),hod=Math.floor((e.clientY-r.top)/r.height*24);
 if(day<0||day>364||hod<0||hod>23){hideTip();return;}const dt=new Date(2023,0,1);dt.setDate(day+1);
 showTip(`<b>${which}</b><br>${MONTHS[dt.getMonth()]} ${dt.getDate()}, ${("0"+hod).slice(-2)}:00 &middot; CF ${cf[day*24+hod]}%`,e);};
 cv.onmouseleave=hideTip;}
function cfColor(v){if(v<=1)return[232,243,247];const t=Math.min(v,100)/100,
 S=[[0,232,243,247],[.04,127,196,230],[.30,134,201,143],[.55,242,214,92],[.78,239,143,60],[1,192,57,43]];
 for(let i=1;i<S.length;i++)if(t<=S[i][0]){const a=S[i-1],b=S[i],f=(t-a[0])/(b[0]-a[0]);
  return[a[1]+f*(b[1]-a[1]),a[2]+f*(b[2]-a[2]),a[3]+f*(b[3]-a[3])];}return[192,57,43];}
function drawHeat(cv,cf){const x=cv.getContext("2d"),im=x.createImageData(365,24);
 for(let h=0;h<8760;h++){const day=h/24|0,hod=h%24;if(day>364)break;const c=cfColor(cf[h]),i=(hod*365+day)*4;
  im.data[i]=c[0];im.data[i+1]=c[1];im.data[i+2]=c[2];im.data[i+3]=255;}x.putImageData(im,0,0);}
function axMonths(el){el.innerHTML=MONTHS.map(m=>`<span>${m}</span>`).join("");}
function profile(cf,p){const o=Array(24).fill(0),n=Array(24).fill(0);let lo=0,hi=8760;
 if(p!=="annual"){let s=0;for(let i=0;i<+p;i++)s+=DIM[i]*24;lo=s;hi=s+DIM[+p]*24;}
 for(let h=lo;h<hi;h++){o[h%24]+=cf[h];n[h%24]++;}return o.map((v,i)=>n[i]?v/n[i]:0);}
function line(svg,sets,ymax,xl,unit,labels,tunit){const W=720,H=230,L=48,R=12,T=12,B=34,pw=W-L-R,ph=H-T-B,n=sets[0].pts.length;tunit=tunit||unit;
 let s='<g font-size=11 fill="#9aa2ad">';
 for(let g=0;g<=4;g++){const y=T+ph*g/4;s+=`<line x1=${L} y1=${y} x2=${W-R} y2=${y} stroke="#eef1f4"/><text x=${L-6} y=${y+3} text-anchor=end>${(ymax*(1-g/4)).toFixed(0)}${unit}</text>`;}
 xl.forEach((lb,i)=>{if(lb){const x=L+(n>1?pw*i/(n-1):0);s+=`<text x=${x} y=${H-12} text-anchor=middle>${lb}</text>`;}});s+="</g>";
 for(const set of sets){const d=set.pts.map((v,i)=>{const x=L+(n>1?pw*i/(n-1):0),y=T+ph*(1-Math.min(v,ymax)/ymax);return`${i?"L":"M"}${x.toFixed(1)} ${y.toFixed(1)}`;}).join(" ");
  s+=`<path d="${d}" fill=none stroke="${set.color}" stroke-width=2 ${set.dash?'stroke-dasharray="5 4"':""}/>`;
  if(!set.dash)set.pts.forEach((v,i)=>{const x=L+(n>1?pw*i/(n-1):0),y=T+ph*(1-Math.min(v,ymax)/ymax);s+=`<circle cx=${x.toFixed(1)} cy=${y.toFixed(1)} r=2.4 fill=#fff stroke="${set.color}" stroke-width=1.5/>`;});}
 svg.innerHTML=s;
 const xs=[],rows=[];for(let i=0;i<n;i++){const x=L+(n>1?pw*i/(n-1):0);xs.push(x);
  let r=`<b>${(labels&&labels[i])||xl[i]||i}</b>`;
  for(const set of sets)if(!set.dash)r+=`<br><span style="color:${set.color}">●</span> ${set.name||""}: ${set.pts[i].toFixed(1)}${tunit}`;
  rows.push(r);}
 hoverX(svg,xs,rows);}
function bars(svg,bs,ymax,tunit){const W=720,H=230,L=48,R=12,T=12,B=42,pw=W-L-R,ph=H-T-B;
 let s='<g font-size=11 fill="#9aa2ad">';for(let g=0;g<=4;g++){const y=T+ph*g/4;s+=`<line x1=${L} y1=${y} x2=${W-R} y2=${y} stroke="#eef1f4"/><text x=${L-6} y=${y+3} text-anchor=end>${(ymax*(1-g/4)).toFixed(0)}</text>`;}s+="</g>";
 const bw=pw/bs.length*0.5;bs.forEach((b,i)=>{const cx=L+pw*(i+.5)/bs.length,h=ph*Math.min(b.v,ymax)/ymax,y=T+ph-h;
  s+=`<rect x=${cx-bw/2} y=${y} width=${bw} height=${h} rx=3 fill="${b.color}"/><text x=${cx} y=${H-22} text-anchor=middle font-size=12 fill=#46505f>${b.label}</text><text x=${cx} y=${y-5} text-anchor=middle font-size=12 fill=#46505f font-weight=600>${b.v.toFixed(1)}</text>`;});
 svg.innerHTML=s;
 hoverX(svg,bs.map((b,i)=>L+pw*(i+.5)/bs.length),bs.map(b=>`<b>${b.label}</b><br>${b.v.toFixed(2)}${tunit||""}`));}
function render(){const d=cur();if(!d)return;const mc=dec(d.model),cc=dec(d.campd),npl=d.npl;
 heatSub.textContent=`24h × 365d — ${d.name} — ${st.year} — ${npl.toLocaleString()} MW nameplate · ${Math.round(npl*d.mrpct/100).toLocaleString()} MW must-run (${d.mrpct}%)`;
 drawHeat(heatC,cc);drawHeat(heatM,mc);axMonths(axC);axMonths(axM);
 heatTip(heatC,cc,"CAMPD actual");heatTip(heatM,mc,"Model result");
 dispSub.textContent=`Average hourly profile — ${d.name} — ${st.period==="annual"?"annual":MONTHS[+st.period]}`;
 const pc=profile(cc,st.period),pm=profile(mc,st.period);const xl=Array(24).fill("");[0,6,12,18,23].forEach(h=>xl[h]=("0"+h).slice(-2)+":00");
 const hrs=Array.from({length:24},(_,h)=>("0"+h).slice(-2)+":00");
 let sets,ymax,unit,tunit;
 if(st.mode==="cf"){sets=[{pts:pc,color:"#2f9bd6",name:"CAMPD actual"},{pts:pm,color:"#ef7d2b",name:"Model result"},{pts:Array(24).fill(d.mrpct),color:"#aab",dash:1}];
  ymax=Math.max(50,Math.ceil(Math.max(...pc,...pm,d.mrpct)/10)*10+10);unit="%";tunit="%";}
 else{const a=pc.map(v=>v*npl/100),b=pm.map(v=>v*npl/100);sets=[{pts:a,color:"#2f9bd6",name:"CAMPD actual"},{pts:b,color:"#ef7d2b",name:"Model result"},{pts:Array(24).fill(npl*d.mrpct/100),color:"#aab",dash:1}];
  ymax=Math.ceil(Math.max(...a,...b,1)/100)*100+100;unit="";tunit=" MW";}
 line(profile_,sets,ymax,xl,unit,hrs,tunit);
 const aA=pc.reduce((a,b)=>a+b)/24,aM=pm.reduce((a,b)=>a+b)/24,pk=pc.indexOf(Math.max(...pc)),bias=aM-aA;
 profStats.innerHTML=`<div class=stat><div class=k>Avg actual</div><div class=v style=color:#2f9bd6>${aA.toFixed(1)}%</div></div>`
  +`<div class=stat><div class=k>Avg model</div><div class=v style=color:#ef7d2b>${aM.toFixed(1)}%</div></div>`
  +`<div class=stat><div class=k>Bias</div><div class=v class=${Math.abs(bias)<5?"good":"bad"} style=color:${Math.abs(bias)<5?"#0f7d3d":"#c01c28"}>${(bias>=0?"+":"")+bias.toFixed(1)} pp</div></div>`
  +`<div class=stat><div class=k>Actual peak hr</div><div class=v>${("0"+pk).slice(-2)}:00</div></div>`
  +(d.r!=null?`<div class=stat><div class=k>Hourly r / NRMSE</div><div class=v>${d.r} / ${d.nrmse}</div></div>`:"");
 bars(annual,[{label:"Model",v:d.m_ann,color:"#ef7d2b"},{label:"CAMPD",v:d.c_ann,color:"#2f9bd6"},{label:"EIA-923",v:d.e_ann,color:"#7aa884"}],Math.max(d.m_ann,d.c_ann,d.e_ann,.1)*1.25," TWh");
 const ms=[{pts:d.c_mon,color:"#2f9bd6",name:"CAMPD"},{pts:d.m_mon,color:"#ef7d2b",name:"Model"}];if(d.e_mon)ms.push({pts:d.e_mon,color:"#7aa884",name:"EIA-923"});
 line(monthly,ms,Math.max(...d.c_mon,...d.m_mon,...(d.e_mon||[0]),1)*1.15,MONTHS,"",MONTHS," GWh");}
const profile_=document.getElementById("profile");
function fillPlants(){const list=(D.groupPlants[st.year+"|"+st.group]||[]).slice().sort((a,b)=>a.name.localeCompare(b.name));
 plantSel.innerHTML=`<option value=agg>Aggregate (${list.length} plants)</option>`+list.map(p=>`<option value=${p.code}>${p.name}</option>`).join("");
 st.plant="agg";plantSel.value="agg";}
function build(){yearSel.innerHTML=D.years.map(y=>`<button data-y=${y} class=${y==st.year?"on":""}>${y}</button>`).join("");
 yearSel.onclick=e=>{if(e.target.dataset.y){st.year=+e.target.dataset.y;[...yearSel.children].forEach(b=>b.classList.toggle("on",+b.dataset.y===st.year));fillPlants();render();}};
 groupSel.innerHTML=D.groups.map(g=>`<option value=${g}>${D.groupLabel[g]}</option>`).join("");groupSel.value=st.group;
 groupSel.onchange=()=>{st.group=groupSel.value;fillPlants();render();};fillPlants();
 plantSel.onchange=()=>{st.plant=plantSel.value;render();};
 modeSel.onclick=e=>{if(e.target.dataset.m){st.mode=e.target.dataset.m;[...modeSel.children].forEach(b=>b.classList.toggle("on",b.dataset.m===st.mode));render();}};
 periodSel.innerHTML='<button data-p=annual class=on>Annual</button>'+MONTHS.map((m,i)=>`<button data-p=${i}>${m}</button>`).join("");
 periodSel.onclick=e=>{const p=e.target.dataset.p;if(p!==undefined){st.period=p;[...periodSel.children].forEach(b=>b.classList.toggle("on",b.dataset.p===st.period));render();}};
 view.onclick=e=>{const v=e.target.dataset.v;if(v){[...view.children].forEach(b=>b.classList.toggle("on",b.dataset.v===v));
  document.getElementById("charts-view").classList.toggle("hide",v!=="charts");document.getElementById("tables-view").classList.toggle("hide",v!=="tables");}};}
try{build();render();diag.style.display="none";}
catch(e){diag.style.color="#c01c28";diag.style.borderColor="#c01c28";
 diag.textContent="Render error: "+((e&&e.message)||e);}
</script></div></body></html>"""


if __name__ == "__main__":
    main()
