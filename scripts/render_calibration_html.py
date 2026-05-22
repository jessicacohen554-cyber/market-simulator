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

from market_sim.data.fleet import (  # noqa: E402
    COAL_MUSTRUN_BY_PLANT, chp_btm_pct,
)

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
                   "e": np.zeros(12), "npl": 0.0, "mr": 0.0, "ea": 0.0,
                   "btm": 0.0, "n": 0}
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
            # CHP host-steam self-supply is behind-the-meter: the model grid LP
            # produces only the cogen's *export*, while CAMPD reports the full
            # plant. For the hourly *shape* views (heatmap, dispatch profile)
            # and the hourly r/NRMSE fit we add the host back flat so the export
            # shape can be compared against the full plant at a matched level;
            # the host is inferred per-plant as (CAMPD mean - grid export mean),
            # since it is unmetered. Annual/monthly totals stay grid-only (the
            # true modeled export); non-CHP must-run is already in the grid LP.
            is_chp = "CHP" in (grp or "")
            btm = max(0.0, float(cn.mean() - grid.mean())) if is_chp else 0.0
            mr_mw = btm if is_chp else cap * mrp / 100.0
            mr_disp = 100.0 * btm / cap if is_chp else mrp
            mt = grid + btm  # heatmap / dispatch profile / hourly fit only
            r, nr = _rfit(mt, cn)
            e_ann_twh = float(eia_ann.get(c, 0.0)) / 1e6
            # Sector behind-the-meter share of net gen (TWh), so the KPI annual
            # total = grid + BTM reconciles to EIA-923 the same way the tables do.
            btm_ann = chp_btm_pct(c, grp) / 100.0 * e_ann_twh if is_chp else 0.0
            emon_p = eia_pmon.get(c, np.zeros(12))
            series[f"{year}|plant:{c}"] = {
                "name": str(pname.get(c, c)), "group": hg, "npl": round(cap),
                "btm_ann": round(btm_ann, 3),
                "mrpct": round(mr_disp, 1),
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
            a["mr"] += mr_mw; a["e"] += emon_p; a["btm"] += btm_ann
            a["ea"] += float(eia_ann.get(c, 0.0)) / 1e6; a["n"] += 1
        for hg, a in agg.items():
            cap = a["npl"] or 1.0
            r, nr = _rfit(a["m"], a["c"])
            series[f"{year}|{hg}"] = {
                "name": f"{GROUP_LABEL[hg]} (aggregate)", "group": hg,
                "btm_ann": round(float(a["btm"]), 3),
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


_GAS_CLASSES = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP")
_FOSSIL_CLASSES = (*_GAS_CLASSES, "COAL_LIGNITE", "COAL_PRB")


def _btm_by_class(e923):
    """BTM TWh per CHP class = EIA-923 sector share x net generation."""
    from market_sim.data.fleet import (
        CHP_SECTOR_CLASS_BY_PLANT as _SC, CHP_BTM_PCT_BY_SECTOR as _BP,
        CHP_ST_BTM_PCT as _STB,
    )
    out: dict[str, float] = {}
    for _, r in e923.iterrows():
        cls = r["klass"]
        if cls not in ("CC_CHP", "CT_CHP", "ST_CHP"):
            continue
        pct = _STB if cls == "ST_CHP" else _BP.get(
            _SC.get(int(r["plant_id"]), "merchant"), 40.0)
        out[cls] = out.get(cls, 0.0) + pct / 100.0 * float(r["annual_mwh"]) / 1e6
    return out


def _campd_class_hourly(campd, e923, T):
    """{class: (T,) MW} of CAMPD net summed by class (plant->class via e923)."""
    pcls = dict(zip(e923["plant_id"].astype(int), e923["klass"]))
    out: dict[str, np.ndarray] = {}
    for pid, g in campd.groupby("plant_id"):
        cls = pcls.get(int(pid))
        if cls is None:
            continue
        a = np.nan_to_num(g.sort_values("hour")["net_mw"].to_numpy(dtype=float))
        a = np.concatenate([a, np.zeros(max(0, T - a.shape[0]))])[:T]
        out[cls] = out.get(cls, np.zeros(T)) + a
    return out


def _fuel_table(disp, e923, e930, year):
    """[1] Annual TWh model vs benchmark by fuel, with a SUM row and the hourly
    r / NRMSE vs EIA-930. Benchmark is EIA-923 (930 for solar) — except 2025,
    where 923 is materially incomplete (wind, solar), so the whole table uses
    EIA-930 and the model is shown grid-only (930 is grid-delivered, no BTM)."""
    mh = rcf._class_hourly(disp)
    T = next(iter(mh.values())).shape[0] if mh else 8760
    ann = rcf._e923_annual(e923)
    btmc = _btm_by_class(e923)
    e = {s: e930[e930["series"] == s].sort_values("hour")["mw"].to_numpy()
         for s in e930["series"].unique()}
    flat = sum(mh.get(c, np.zeros(T)).sum() for c in ("CC_CHP", "CT_CHP", "ST_CHP")) / T
    # EIA-930 is the demand benchmark we scale to, and 923 is materially
    # incomplete (solar every year, wind in 2025), so compare every year to 930
    # (grid-delivered) with the model shown grid-only.
    use_930 = True

    def grid(classes):
        return sum((mh.get(c, np.zeros(T)) for c in classes), np.zeros(T))

    def gtwh(classes):
        return grid(classes).sum() / 1e6

    if use_930:
        rows_def = [
            ("gas", gtwh(_GAS_CLASSES), e["gas"].sum() / 1e6,
             grid(rcf._NONCHP_GAS), e["gas"] - flat),
            ("coal", gtwh(rcf._COAL_CLASSES), e["coal"].sum() / 1e6,
             grid(rcf._COAL_CLASSES), e["coal"]),
            ("nuclear", gtwh(("nuclear",)), e["nuclear"].sum() / 1e6,
             mh.get("nuclear", np.zeros(T)), e.get("nuclear")),
            ("wind", gtwh(("wind",)), e["wind"].sum() / 1e6,
             mh.get("wind", np.zeros(T)), e["wind"]),
            ("solar", gtwh(("solar",)), e["solar"].sum() / 1e6,
             mh.get("solar", np.zeros(T)), e["solar"]),
        ]
    else:
        rows_def = [
            ("gas", gtwh(_GAS_CLASSES) + sum(btmc.values()),
             sum(ann.get(c, 0.0) for c in _GAS_CLASSES),
             grid(rcf._NONCHP_GAS), e["gas"] - flat),
            ("coal", gtwh(rcf._COAL_CLASSES),
             sum(ann.get(c, 0.0) for c in rcf._COAL_CLASSES),
             grid(rcf._COAL_CLASSES), e["coal"]),
            ("nuclear", gtwh(("nuclear",)),
             ann.get("nuclear", e.get("nuclear", np.zeros(T)).sum() / 1e6),
             mh.get("nuclear", np.zeros(T)), e.get("nuclear")),
            ("wind", gtwh(("wind",)),
             ann.get("wind", e["wind"].sum() / 1e6),
             mh.get("wind", np.zeros(T)), e["wind"]),
            ("solar", gtwh(("solar",)),
             e["solar"].sum() / 1e6, mh.get("solar", np.zeros(T)), e["solar"]),
        ]
    body = ""
    sm = sb = 0.0
    for name, m, b, mo, ob in rows_def:
        sm += m
        sb += b
        d = 100 * (m - b) / b if b else float("nan")
        rr = nn = "—"
        if ob is not None:
            rr, nn = f"{rcf._pearson_r(mo, ob):.3f}", f"{rcf._nrmse(mo, ob):.3f}"
        ds = f"{d:+.1f}%" if b else "—"
        body += (f"<tr><td class=lbl>{name}</td><td class=num>{m:.1f}</td>"
                 f"<td class=num>{b:.1f}</td>"
                 f"<td class='num {_diffcls(d) if b else ''}'>{ds}</td>"
                 f"<td class=num>{rr}</td><td class=num>{nn}</td></tr>")
    dsum = 100 * (sm - sb) / sb if sb else 0.0
    body += (f"<tr class=sumrow><td class=lbl>ALL FUELS</td>"
             f"<td class=num>{sm:.1f}</td><td class=num>{sb:.1f}</td>"
             f"<td class='num {_diffcls(dsum)}'>{dsum:+.1f}%</td>"
             f"<td class=num></td><td class=num></td></tr>")
    bench_lbl = "EIA-930 TWh" if use_930 else "EIA-923 TWh"
    return ("<table><thead><tr><th>fuel</th><th>model TWh</th>"
            f"<th>{bench_lbl}</th><th>Δ</th><th>r vs 930</th><th>NRMSE</th>"
            f"</tr></thead><tbody>{body}</tbody></table>")


def _fossil_table(disp, e923, campd):
    """[2] Fossil classes: model GRID TWh vs (EIA-923 net − BTM), with hourly
    r / NRMSE vs CAMPD on absolute MW sums (not capacity factor)."""
    mh = rcf._class_hourly(disp)
    T = next(iter(mh.values())).shape[0] if mh else 8760
    ann = rcf._e923_annual(e923)
    btmc = _btm_by_class(e923)
    ch = _campd_class_hourly(campd, e923, T)
    body = ""
    # ST_CHP (3 tiny ~fully-behind-the-meter industrial steam cogens, 249 MW)
    # is irrelevant on the grid stack and its near-zero grid benchmark blows up
    # the percentage, so it is omitted from the fossil-class comparison.
    for c in (cls for cls in _FOSSIL_CLASSES if cls != "ST_CHP"):
        g = mh.get(c, np.zeros(T))
        gtwh = g.sum() / 1e6
        bench = ann.get(c, 0.0) - btmc.get(c, 0.0)
        # Guard the % against a near-zero grid-deliverable benchmark (e.g. a CHP
        # class that is ~fully behind-the-meter, or an EIA-923 reporting gap).
        ok = bench > 0.02
        d = 100 * (gtwh - bench) / bench if ok else float("nan")
        obs = ch.get(c)
        rr = nn = "—"
        if obs is not None and obs.sum() > 0:
            rr, nn = f"{rcf._pearson_r(g, obs):.3f}", f"{rcf._nrmse(g, obs):.3f}"
        ds = f"{d:+.1f}%" if ok else "—"
        body += (f"<tr><td class=lbl>{c}</td><td class=num>{gtwh:.2f}</td>"
                 f"<td class=num>{bench:.2f}</td>"
                 f"<td class='num {_diffcls(d) if ok else ''}'>{ds}</td>"
                 f"<td class=num>{rr}</td><td class=num>{nn}</td></tr>")
    return ("<table><thead><tr><th>fossil class</th><th>model grid TWh</th>"
            "<th>923 − BTM TWh</th><th>Δ</th><th>r vs CAMPD</th><th>NRMSE</th>"
            f"</tr></thead><tbody>{body}</tbody></table>")


def _plant_table(payload, year):
    """[3] One year: per-plant hourly r / NRMSE vs CAMPD and Δ vs EIA-923."""
    rows = {int(k.split("plant:")[1]): d for k, d in payload["series"].items()
            if "|plant:" in k and int(k.split("|", 1)[0]) == year}
    body = ""
    for code in sorted(rows, key=lambda c: (rows[c]["group"], rows[c]["name"])):
        d = rows[code]
        r = "—" if d.get("r") is None else f"{d['r']:.3f}"
        nr = "—" if d.get("nrmse") is None else f"{d['nrmse']:.3f}"
        m, e = d.get("m_ann"), d.get("e_ann")
        if e:
            dp = 100.0 * (m - e) / e
            dcell = f'<td class="num {_diffcls(dp)}">{dp:+.1f}</td>'
        else:
            dcell = "<td class=num>—</td>"
        body += (f"<tr><td class=lbl>{html.escape(d['name'])}</td>"
                 f"<td class=lbl>{d['group']}</td><td class=num>{r}</td>"
                 f"<td class=num>{nr}</td>{dcell}</tr>")
    return ("<table><thead><tr><th>plant</th><th>group</th><th>r vs CAMPD</th>"
            "<th>NRMSE</th><th>Δ923%</th></tr></thead>"
            f"<tbody>{body}</tbody></table>")



def tabular_html(bundles, payload):
    """Tables page: one year shown at a time (toggle), three tables each —
    fuel totals, fossil classes (grid vs 923-BTM), and plant-level."""
    years = sorted(bundles)
    btns = "".join(
        f'<button data-ty={y} class="{"on" if i == 0 else ""}">{y}</button>'
        for i, y in enumerate(years)
    )
    secs = ""
    for i, year in enumerate(years):
        bdir = bundles[year]
        disp = pd.read_parquet(bdir / "dispatch" / f"{year}_P1.parquet")
        e923 = pd.read_parquet(bdir / "eia923.parquet")
        e923 = e923[e923["year"] == year]
        e930 = pd.read_parquet(bdir / "eia930.parquet")
        e930 = e930[e930["year"] == year]
        campd = pd.read_parquet(bdir / "campd.parquet")
        campd = campd[campd["year"] == year]
        secs += (
            f'<div class="tyear{"" if i == 0 else " hide"}" data-ty={year}>'
            f"<h3>Fuel totals — model vs EIA-930 (the demand benchmark; 923 is "
            f"incomplete), hourly fit vs EIA-930</h3>"
            f'<div class=tablewrap>{_fuel_table(disp, e923, e930, year)}</div>'
            f"<h3>Fossil classes — model grid vs EIA-923 − BTM "
            f"(hourly r / NRMSE vs CAMPD, absolute MW)</h3>"
            f'<div class=tablewrap>{_fossil_table(disp, e923, campd)}</div>'
            f"<h3>Plant-level — hourly r / NRMSE vs CAMPD, Δ vs EIA-923</h3>"
            f'<div class=tablewrap>{_plant_table(payload, year)}</div></div>'
        )
    return f'<div class=tabs id=tyearSel>{btns}</div>{secs}'


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
:root{--bg:#f6f7f9;--card:#fff;--bd:#e3e7ec;--ink:#1a1f29;--mut:#6b7480;
  --model:#ef7d2b;--campd:#2f9bd6;--e923:#2e9e5b;--e930:#8b5cf6;--mr:#7b8794;}
*{box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);margin:0;padding:18px}
.wrap{max-width:1040px;margin:0 auto}h1{font-size:23px;margin:0 0 2px}.sub{color:var(--mut);font-size:14px;margin:0 0 14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px 18px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.row{display:flex;flex-wrap:wrap;gap:16px;align-items:center}
.lab{font-size:12px;letter-spacing:.06em;color:var(--mut);font-weight:600;text-transform:uppercase;margin-right:6px}
.seg{display:inline-flex;background:#eef1f4;border-radius:9px;padding:3px}
.seg button{border:0;background:transparent;padding:7px 14px;border-radius:7px;font-size:14px;cursor:pointer;color:var(--mut);font-weight:600}
.seg button.on{background:#fff;color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.12)}
select{font-size:15px;padding:8px 11px;border:1px solid var(--bd);border-radius:8px;background:#fff;max-width:100%}
h2{font-size:19px;margin:2px 0}h3{font-size:16px;margin:18px 0 8px}h4{font-size:14px;margin:14px 0 6px;color:#3a4250}
.hsub{color:var(--mut);font-size:13px;margin:0 0 10px}
canvas.heat{width:100%;height:200px;image-rendering:pixelated;border:1px solid var(--bd);border-radius:6px;background:#eef3f7;display:block}
.ax{display:flex;justify-content:space-between;color:var(--mut);font-size:12px;margin:3px 2px 0}
.legend{display:flex;align-items:center;gap:16px;font-size:13px;color:var(--mut);margin:10px 0;flex-wrap:wrap}
.legend b{font-weight:600}
.swatch{display:inline-block;width:22px;height:0;border-top-width:3px;border-top-style:solid;vertical-align:middle;margin-right:5px}
.ramp{height:11px;width:170px;border-radius:3px;background:linear-gradient(90deg,#e8f3f7,#7fc4e6,#86c98f,#f2d65c,#ef8f3c,#c0392b)}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}
.stat{flex:1;min-width:130px;background:#f8fafc;border:1px solid var(--bd);border-radius:9px;padding:10px 13px}
.stat .k{font-size:12px;color:var(--mut);text-transform:uppercase}.stat .v{font-size:22px;font-weight:700;margin-top:2px}
.tablewrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;margin:6px 0 14px;border:1px solid var(--bd);border-radius:8px}
table{border-collapse:collapse;width:100%;background:#fff;font-size:14px}
th,td{padding:8px 11px;border-bottom:1px solid #eef1f4;text-align:left;white-space:nowrap}th{background:#f0f3f6;font-size:12px;text-transform:uppercase;color:#46505f;position:sticky;top:0}
td.num{text-align:right;font-variant-numeric:tabular-nums}.good{color:#0f7d3d}.ok{color:#9a6700}.bad{color:#c01c28;font-weight:600}
tr.sumrow td{border-top:2px solid #cfd6dd;font-weight:700;background:#f8fafc}
.kpis{display:flex;flex-wrap:wrap;gap:10px}
.kpi{flex:1;min-width:140px;background:#f8fafc;border:1px solid var(--bd);border-radius:9px;padding:11px 14px}
.kpik{font-size:12px;color:var(--mut);text-transform:uppercase}.kpiv{font-size:23px;font-weight:700;margin-top:3px}
.hide{display:none}.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}
.tabs button{border:1px solid var(--bd);background:#fff;border-radius:7px;padding:6px 12px;font-size:13px;cursor:pointer;color:var(--mut)}
.tabs button.on{background:var(--campd);color:#fff;border-color:var(--campd)}
svg{width:100%;height:auto;display:block}
#tip{position:fixed;display:none;pointer-events:none;background:#1a1f29;color:#fff;font-size:13px;line-height:1.55;padding:8px 11px;border-radius:8px;box-shadow:0 4px 14px rgba(0,0,0,.28);z-index:99;max-width:260px;white-space:nowrap}
canvas.heat,svg{cursor:crosshair}
@media(max-width:640px){body{padding:10px}.card{padding:12px 12px}h1{font-size:20px}th,td{padding:7px 8px;font-size:13px}canvas.heat{height:150px}.stat{min-width:46%}}
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
<div class=card><div class=kpis id=kpi></div></div>
<div class=card><h2>Commitment heatmap</h2><p class=hsub id=heatSub></p>
  <div class=legend><span>0%</span><span class=ramp></span><span>100% CF</span></div>
  <h4>CAMPD actual</h4><canvas class=heat id=heatC width=365 height=24></canvas><div class=ax id=axC></div>
  <h4>Model result</h4><canvas class=heat id=heatM width=365 height=24></canvas><div class=ax id=axM></div></div>
<div class=card><h2>Dispatch comparison</h2><p class=hsub id=dispSub></p>
  <div class=row><span class=lab>Mode</span><span class=seg id=modeSel>
    <button data-m=cf class=on>CF %</button><button data-m=mw>MW</button></span></div>
  <div class=tabs id=periodSel></div>
  <div class=legend>
    <span><i class=swatch style="border-top-color:var(--campd)"></i><b>CAMPD actual</b></span>
    <span><i class=swatch style="border-top-color:var(--model);border-top-style:solid"></i><b>Model result</b></span>
    <span><i class=swatch style="border-top-color:var(--mr);border-top-style:dotted"></i><b>must-run floor</b></span></div>
  <svg id=profile viewBox="0 0 720 360"></svg><div class=stats id=profStats></div></div>
<div class=card><h2>Annual total (TWh)</h2>
  <div class=legend>
    <span><i class=swatch style="border-top-color:var(--model)"></i><b>Model</b></span>
    <span><i class=swatch style="border-top-color:var(--campd)"></i><b>CAMPD</b></span>
    <span><i class=swatch style="border-top-color:var(--e923)"></i><b>EIA-923</b></span></div>
  <svg id=annual viewBox="0 0 720 360"></svg></div>
<div class=card><h2>Monthly generation (GWh)</h2>
  <div class=legend>
    <span><i class=swatch style="border-top-color:var(--campd)"></i><b>CAMPD</b></span>
    <span><i class=swatch style="border-top-color:var(--model);border-top-style:solid"></i><b>Model</b></span>
    <span><i class=swatch style="border-top-color:var(--e923);border-top-style:dotted"></i><b>EIA-923</b></span></div>
  <svg id=monthly viewBox="0 0 720 360"></svg></div></div>

<div id=tables-view class=hide><div class=card>__TABULAR__</div></div>

<script>
const D=__DATA__;const MONTHS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const DIM=[31,28,31,30,31,30,31,31,30,31,30,31];
const C={model:"#ef7d2b",campd:"#2f9bd6",e923:"#2e9e5b",e930:"#8b5cf6",mr:"#7b8794"};
// Model series render solid (color distinguishes them from CAMPD); SVG
// stroke-dasharray did not render reliably across viewers.
const DASH={solid:"",dashed:"",dotted:'stroke-dasharray="2 4"'};
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
const NS="http://www.w3.org/2000/svg";
function mk(t,a,txt){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;return e;}
function clear(svg){while(svg.firstChild)svg.removeChild(svg.firstChild);}
function line(svg,sets,ymax,xl,unit,labels,tunit){const W=720,H=360,L=58,R=16,T=16,B=44,pw=W-L-R,ph=H-T-B,n=sets[0].pts.length;tunit=tunit||unit;
 clear(svg);const g=mk("g",{"font-size":14,fill:"#8a93a0"});
 for(let i=0;i<=4;i++){const y=T+ph*i/4;g.appendChild(mk("line",{x1:L,y1:y,x2:W-R,y2:y,stroke:"#eef1f4"}));g.appendChild(mk("text",{x:L-9,y:y+5,"text-anchor":"end"},(ymax*(1-i/4)).toFixed(0)+unit));}
 xl.forEach((lb,i)=>{if(lb)g.appendChild(mk("text",{x:L+(n>1?pw*i/(n-1):0),y:H-16,"text-anchor":"middle"},lb));});svg.appendChild(g);
 const X=i=>L+(n>1?pw*i/(n-1):0),Y=v=>T+ph*(1-Math.min(Number(v)||0,ymax)/ymax);
 for(const set of sets){const dd=set.pts.map((v,i)=>(i?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1)).join(" ");
  const at={d:dd,fill:"none",stroke:set.color,"stroke-width":set.floor?2:2.8};if(set.style==="dotted")at["stroke-dasharray"]="2 4";
  svg.appendChild(mk("path",at));
  if(!set.floor)set.pts.forEach((v,i)=>svg.appendChild(mk("circle",{cx:X(i).toFixed(1),cy:Y(v).toFixed(1),r:3.2,fill:"#fff",stroke:set.color,"stroke-width":2})));}
 const xs=[],rows=[];for(let i=0;i<n;i++){xs.push(X(i));let r=`<b>${(labels&&labels[i])||xl[i]||i}</b>`;
  for(const set of sets)if(!set.floor)r+=`<br><span style="color:${set.color}">●</span> ${set.name||""}: ${(Number(set.pts[i])||0).toFixed(1)}${tunit}`;rows.push(r);}
 hoverX(svg,xs,rows);}
function bars(svg,bs,ymax,tunit){const W=720,H=360,L=58,R=16,T=16,B=52,pw=W-L-R,ph=H-T-B;
 clear(svg);const g=mk("g",{"font-size":14,fill:"#8a93a0"});
 for(let i=0;i<=4;i++){const y=T+ph*i/4;g.appendChild(mk("line",{x1:L,y1:y,x2:W-R,y2:y,stroke:"#eef1f4"}));g.appendChild(mk("text",{x:L-9,y:y+5,"text-anchor":"end"},(ymax*(1-i/4)).toFixed(0)));}svg.appendChild(g);
 const bw=pw/bs.length*0.46;bs.forEach((b,i)=>{const cx=L+pw*(i+.5)/bs.length,h=ph*Math.min(b.v,ymax)/ymax,y=T+ph-h;
  svg.appendChild(mk("rect",{x:cx-bw/2,y:y,width:bw,height:h,rx:3,fill:b.color}));
  svg.appendChild(mk("text",{x:cx,y:H-28,"text-anchor":"middle","font-size":15,fill:"#46505f"},b.label));
  svg.appendChild(mk("text",{x:cx,y:y-8,"text-anchor":"middle","font-size":15,fill:"#46505f","font-weight":700},b.v.toFixed(1)));});
 hoverX(svg,bs.map((b,i)=>L+pw*(i+.5)/bs.length),bs.map(b=>`<b>${b.label}</b><br>${b.v.toFixed(2)}${tunit||""}`));}
function render(){const d=cur();if(!d)return;const mc=dec(d.model),cc=dec(d.campd),npl=d.npl;
 const mtot=(d.m_ann||0)+(d.btm_ann||0),e923=d.e_ann||0,dl=e923?100*(mtot-e923)/e923:null;
 const dcl=dl==null?"":Math.abs(dl)<5?"good":Math.abs(dl)<15?"ok":"bad";
 kpi.innerHTML=[["Model total (grid+BTM)",mtot.toFixed(1)+" TWh",""],["EIA-923 total",e923.toFixed(1)+" TWh",""],["Δ model vs 923",dl==null?"—":(dl>=0?"+":"")+dl.toFixed(1)+"%",dcl],["Hourly r vs CAMPD",d.r!=null?d.r:"—",""],["NRMSE",d.nrmse!=null?d.nrmse:"—",""]].map(k=>`<div class=kpi><div class=kpik>${k[0]}</div><div class="kpiv ${k[2]}">${k[1]}</div></div>`).join("");
 heatSub.textContent=`24h × 365d — ${d.name} — ${st.year} — model ${mtot.toFixed(1)} TWh vs EIA-923 ${e923.toFixed(1)} TWh · ${npl.toLocaleString()} MW nameplate`;
 drawHeat(heatC,cc);drawHeat(heatM,mc);axMonths(axC);axMonths(axM);
 heatTip(heatC,cc,"CAMPD actual");heatTip(heatM,mc,"Model result");
 dispSub.textContent=`Average hourly profile — ${d.name} — ${st.period==="annual"?"annual":MONTHS[+st.period]}`;
 const pc=profile(cc,st.period),pm=profile(mc,st.period);const xl=Array(24).fill("");[0,6,12,18,23].forEach(h=>xl[h]=("0"+h).slice(-2)+":00");
 const hrs=Array.from({length:24},(_,h)=>("0"+h).slice(-2)+":00");
 let sets,ymax,unit,tunit;
 if(st.mode==="cf"){sets=[{pts:pc,color:C.campd,name:"CAMPD actual"},{pts:pm,color:C.model,name:"Model result",style:"dashed"},{pts:Array(24).fill(d.mrpct),color:C.mr,style:"dotted",floor:1}];
  ymax=Math.max(50,Math.ceil(Math.max(...pc,...pm,d.mrpct)/10)*10+10);unit="%";tunit="%";}
 else{const a=pc.map(v=>v*npl/100),b=pm.map(v=>v*npl/100);sets=[{pts:a,color:C.campd,name:"CAMPD actual"},{pts:b,color:C.model,name:"Model result",style:"dashed"},{pts:Array(24).fill(npl*d.mrpct/100),color:C.mr,style:"dotted",floor:1}];
  ymax=Math.ceil(Math.max(...a,...b,1)/100)*100+100;unit="";tunit=" MW";}
 line(profile_,sets,ymax,xl,unit,hrs,tunit);
 const aA=pc.reduce((a,b)=>a+b)/24,aM=pm.reduce((a,b)=>a+b)/24,pk=pc.indexOf(Math.max(...pc)),bias=aM-aA;
 profStats.innerHTML=`<div class=stat><div class=k>Avg actual</div><div class=v style=color:${C.campd}>${aA.toFixed(1)}%</div></div>`
  +`<div class=stat><div class=k>Avg model</div><div class=v style=color:${C.model}>${aM.toFixed(1)}%</div></div>`
  +`<div class=stat><div class=k>Bias</div><div class=v class=${Math.abs(bias)<5?"good":"bad"} style=color:${Math.abs(bias)<5?"#0f7d3d":"#c01c28"}>${(bias>=0?"+":"")+bias.toFixed(1)} pp</div></div>`
  +`<div class=stat><div class=k>Actual peak hr</div><div class=v>${("0"+pk).slice(-2)}:00</div></div>`
  +(d.r!=null?`<div class=stat><div class=k>Hourly r / NRMSE</div><div class=v>${d.r} / ${d.nrmse}</div></div>`:"");
 bars(annual,[{label:"Model",v:d.m_ann,color:C.model},{label:"CAMPD",v:d.c_ann,color:C.campd},{label:"EIA-923",v:d.e_ann,color:C.e923}],Math.max(d.m_ann,d.c_ann,d.e_ann,.1)*1.25," TWh");
 const ms=[{pts:d.c_mon,color:C.campd,name:"CAMPD"},{pts:d.m_mon,color:C.model,name:"Model",style:"dashed"}];if(d.e_mon)ms.push({pts:d.e_mon,color:C.e923,name:"EIA-923",style:"dotted"});
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
  document.getElementById("charts-view").classList.toggle("hide",v!=="charts");document.getElementById("tables-view").classList.toggle("hide",v!=="tables");}};
 const ty=document.getElementById("tyearSel");
 if(ty)ty.onclick=e=>{const y=e.target.dataset.ty;if(y){[...ty.children].forEach(b=>b.classList.toggle("on",b.dataset.ty===y));
  document.querySelectorAll(".tyear").forEach(s=>s.classList.toggle("hide",s.dataset.ty!==y));}};}
try{build();render();diag.style.display="none";}
catch(e){diag.style.color="#c01c28";diag.style.borderColor="#c01c28";
 diag.textContent="Render error: "+((e&&e.message)||e);}
</script></div></body></html>"""


if __name__ == "__main__":
    main()
