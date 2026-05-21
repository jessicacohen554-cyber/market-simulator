"""Generate a styled HTML calibration report from persisted bundles.

Reads the dispatch + benchmark parquets and renders the [3]/[3b]/[4]/[5]/[6]
tables as HTML, reusing run_calibration_full's computation helpers so the
numbers match `--report`. Output: results/calibration/calibration-report.html.
"""
import sys
sys.path.insert(0, "."); sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
import html
import importlib.util
from datetime import datetime

import numpy as np
import pandas as pd

_spec = importlib.util.spec_from_file_location(
    "rcf", "scripts/run_calibration_full.py")
rcf = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(rcf)

BUNDLES = {2023: "stgas_2023", 2024: "stgas_2024", 2025: "stgas_2025"}
ROOT = "results/calibration"
GAS = {2023: 2.54, 2024: 2.19, 2025: 3.52}

THERMAL = ["CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP",
           "COAL_LIGNITE", "COAL_PRB"]


def cls_diff(d):
    """CSS class by absolute diff %."""
    a = abs(d)
    return "good" if a < 5 else "ok" if a < 15 else "bad"


def pct(x):
    return f"{x:+.1f}%" if x == x else "—"


def load(year):
    b = f"{ROOT}/{BUNDLES[year]}"
    disp = pd.read_parquet(f"{b}/dispatch/{year}_P1.parquet")
    e923 = pd.read_parquet(f"{b}/eia923.parquet")
    e923 = e923[e923["year"] == year]
    e930 = pd.read_parquet(f"{b}/eia930.parquet")
    e930 = e930[e930["year"] == year]
    btm = pd.read_parquet(f"{b}/btm.parquet")
    btm = btm[(btm["year"] == year) & (btm["pass"] == "P1")]
    return disp, e923, e930, btm


def fmt_table(headers, rows, right_from=1):
    h = "".join(f"<th>{html.escape(str(x))}</th>" for x in headers)
    body = []
    for r in rows:
        cells = []
        for i, c in enumerate(r):
            cls = ""
            val = c
            if isinstance(c, tuple):  # (text, css_class)
                val, cls = c
            align = "num" if i >= right_from else "lbl"
            cells.append(f'<td class="{align} {cls}">{html.escape(str(val))}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<table><thead><tr>{h}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table>')


def section_thermal(year, disp, e923, btm):
    mh = rcf._class_hourly(disp)
    mtwh = {k: v.sum() / rcf._MWH_PER_TWH for k, v in mh.items()}
    ann = rcf._e923_annual(e923)
    bt = dict(zip(btm["klass"], btm["btm_twh"]))
    rows = []
    tg = tb = tm = te = 0.0
    for c in THERMAL:
        grid = mtwh.get(c, 0.0); b = bt.get(c, 0.0); m = grid + b
        e = ann.get(c, 0.0); d = 100 * (m - e) / e if e else float("nan")
        rows.append([c, f"{grid:.2f}", f"{b:.2f}", f"{m:.2f}", f"{e:.2f}",
                     (pct(d), cls_diff(d) if e else "")])
        tg += grid; tb += b; tm += m; te += e
    td = 100 * (tm - te) / te
    rows.append([("TOTAL", "tot"), (f"{tg:.2f}", "tot"), (f"{tb:.2f}", "tot"),
                 (f"{tm:.2f}", "tot"), (f"{te:.2f}", "tot"),
                 (pct(td), "tot " + cls_diff(td))])
    return fmt_table(
        ["class", "grid LP", "BTM-MR", "model", "EIA-923", "Δ%"], rows)


def section_hourly(year, disp, e930, btm):
    mh = rcf._class_hourly(disp)
    e = {s: e930[e930["series"] == s].sort_values("hour")["mw"].to_numpy()
         for s in e930["series"].unique()}
    T = e["coal"].shape[0]
    chp_grid = sum(mh.get(c, np.zeros(T)).sum()
                   for c in ("CC_CHP", "CT_CHP", "ST_CHP")) / rcf._MWH_PER_TWH
    flat = chp_grid * rcf._MWH_PER_TWH / T
    gas_m = sum(mh.get(c, np.zeros(T)) for c in rcf._NONCHP_GAS)
    coal_m = sum(mh.get(c, np.zeros(T)) for c in rcf._COAL_CLASSES)
    pairs = [("gas (non-CHP)", gas_m, e["gas"] - flat),
             ("coal", coal_m, e["coal"]),
             ("nuclear", mh.get("nuclear", np.zeros(T)), e.get("nuclear")),
             ("solar", mh.get("solar", np.zeros(T)), e["solar"]),
             ("wind", mh.get("wind", np.zeros(T)), e["wind"])]
    rows = []
    for name, m, o in pairs:
        if o is None:
            continue
        r = rcf._pearson_r(m, o)
        rows.append([name, f"{r:.3f}", f"{rcf._nrmse(m, o):.3f}",
                     f"{m.sum() / rcf._MWH_PER_TWH:.2f}",
                     f"{o.sum() / rcf._MWH_PER_TWH:.2f}"])
    return fmt_table(
        ["fuel", "Pearson r", "NRMSE", "model TWh", "EIA-930 TWh"], rows)


def section_plant(year, disp, e923):
    mbp = disp.groupby("plant_code", observed=True)["mw"].sum().to_dict()
    cbp = (disp[disp["plant_code"] > 0]
           .groupby("plant_code", observed=True)["klass"].first().to_dict())
    fbp = e923.groupby("plant_id")["annual_mwh"].sum().to_dict()
    rows = []
    for code, label in rcf._PLANT_PANEL:
        mg = mbp.get(code, 0.0) / 1e3; eg = fbp.get(code, 0.0) / 1e3
        d = 100 * (mg - eg) / eg if eg else float("nan")
        rows.append([label, str(code), f"{mg:,.0f}", f"{eg:,.0f}",
                     (pct(d), cls_diff(d) if eg else ""),
                     str(cbp.get(code, "—"))])
    return fmt_table(
        ["plant", "EIA code", "model GWh", "EIA-923 GWh", "Δ%", "class"], rows)


def section_monthly(year, disp, e923):
    mh = rcf._class_hourly(disp)
    emon = rcf._e923_monthly(e923)
    rows = []
    for c in rcf._COAL_CLASSES + ("CC_REGULAR", "ST_GAS", "CT_PEAKER"):
        gm = rcf._hourly_to_monthly(mh.get(c, np.zeros(rcf._HOURS_PER_YEAR)))
        bm = emon.get(c, np.zeros(12))
        cells = [c]
        for i in range(12):
            if bm[i] > 0:
                d = 100 * (gm[i] - bm[i]) / bm[i]
                cells.append((f"{d:+.0f}", cls_diff(d)))
            else:
                cells.append("·")
        rows.append(cells)
    return fmt_table(["class"] + list(rcf._MONTH_NAMES), rows)


def summary_table():
    rows = []
    for year in BUNDLES:
        disp, e923, e930, btm = load(year)
        mh = rcf._class_hourly(disp)
        ann = rcf._e923_annual(e923)
        def dl(model_cls, eia_cls):
            m = sum(mh.get(c, np.zeros(1)).sum() for c in model_cls) / rcf._MWH_PER_TWH
            e = sum(ann.get(c, 0.0) for c in eia_cls)
            return 100 * (m - e) / e if e else float("nan")
        coal = dl(rcf._COAL_CLASSES, rcf._COAL_CLASSES)
        prb = dl(["COAL_PRB"], ["COAL_PRB"]); lig = dl(["COAL_LIGNITE"], ["COAL_LIGNITE"])
        gas = dl(rcf._NONCHP_GAS, rcf._NONCHP_GAS)
        e = {s: e930[e930["series"] == s].sort_values("hour")["mw"].to_numpy()
             for s in e930["series"].unique()}
        T = e["coal"].shape[0]
        coal_m = sum(mh.get(c, np.zeros(T)) for c in rcf._COAL_CLASSES)
        cr = rcf._pearson_r(coal_m, e["coal"])
        rows.append([str(year), f"${GAS[year]:.2f}",
                     (pct(coal), cls_diff(coal)), (pct(prb), cls_diff(prb)),
                     (pct(lig), cls_diff(lig)), (pct(gas), cls_diff(gas)),
                     f"{cr:.3f}"])
    return fmt_table(
        ["year", "gas $/MMBtu", "coal Δ%", "PRB Δ%", "lignite Δ%",
         "gas Δ%", "coal r"], rows)


CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
 background:#f6f7f9;color:#1a1f29;margin:0;padding:32px;line-height:1.5;}
.wrap{max-width:1040px;margin:0 auto;}
h1{font-size:26px;margin:0 0 4px;}h2{font-size:20px;margin:34px 0 6px;border-bottom:2px solid #e3e7ec;padding-bottom:6px;}
h3{font-size:15px;margin:20px 0 8px;color:#3a4250;font-weight:600;}
.sub{color:#6b7480;font-size:14px;margin:0 0 8px;}
.cfg{background:#fff;border:1px solid #e3e7ec;border-radius:10px;padding:14px 18px;font-size:13px;color:#3a4250;margin:14px 0 8px;}
.cfg code{background:#eef1f4;padding:1px 6px;border-radius:4px;}
table{border-collapse:collapse;width:100%;background:#fff;border:1px solid #e3e7ec;
 border-radius:10px;overflow:hidden;font-size:13px;margin:6px 0 18px;box-shadow:0 1px 2px rgba(0,0,0,.03);}
th,td{padding:7px 11px;text-align:left;border-bottom:1px solid #eef1f4;}
th{background:#f0f3f6;font-weight:600;color:#46505f;font-size:12px;text-transform:uppercase;letter-spacing:.03em;}
td.num{text-align:right;font-variant-numeric:tabular-nums;}
tr:last-child td{border-bottom:none;}
.tot{font-weight:700;background:#f8fafc;}
.good{color:#0f7d3d;}.ok{color:#9a6700;}.bad{color:#c01c28;font-weight:600;}
.year{background:#fff;border:1px solid #e3e7ec;border-radius:12px;padding:20px 24px;margin:18px 0;}
.legend{font-size:12px;color:#6b7480;margin:4px 0 16px;}
.legend b{padding:1px 7px;border-radius:4px;}
footer{color:#9aa2ad;font-size:12px;margin-top:30px;text-align:center;}
"""


def build():
    parts = [f"<!doctype html><html><head><meta charset='utf-8'>"
             f"<title>ERCOT calibration report</title><style>{CSS}</style></head><body><div class='wrap'>"]
    parts.append("<h1>ERCOT coal/gas calibration report</h1>")
    parts.append(f"<p class='sub'>Generated {datetime.now():%Y-%m-%d %H:%M} · "
                 "weather years 2023–2025 · single-year economic dispatch (P1)</p>")
    parts.append(
        "<div class='cfg'><b>Locked config (tier pass 2):</b> historic outages "
        "(CAMPD-derived, &gt;10-day) · per-plant CAMPD coal must-run · "
        "plant-specific monthly coal price · gas-keyed PRB passthrough sigmoid, "
        "tiered (baseload <code>0.82/1.50</code>, follower <code>0.71</code>) · "
        "coal POF dropped · ST_GAS May–Sep 10% reliability floor + seasonal "
        "startup spread · benchmark = EIA-923 with CAMPD backfill for "
        "under-reported 2025 plants.</div>")
    parts.append(
        "<p class='legend'>Δ% = (model − benchmark)/benchmark.&nbsp; "
        "<b class='good'>green</b> |Δ|&lt;5%&nbsp; "
        "<b class='ok'>amber</b> 5–15%&nbsp; <b class='bad'>red</b> &gt;15%</p>")

    parts.append("<h2>Summary — annual level &amp; coal hourly fit</h2>")
    parts.append(summary_table())

    for year in BUNDLES:
        disp, e923, e930, btm = load(year)
        parts.append(f"<div class='year'><h2 style='border:none;margin-top:0'>ERCOT {year} "
                     f"<span class='sub'>(Henry Hub ${GAS[year]:.2f}/MMBtu)</span></h2>")
        parts.append("<h3>Thermal generation by class — model (grid + behind-meter) vs EIA-923 (TWh)</h3>")
        parts.append(section_thermal(year, disp, e923, btm))
        parts.append("<h3>Hourly dispatch fit vs EIA-930</h3>")
        parts.append(section_hourly(year, disp, e930, btm))
        parts.append("<h3>Coal monthly bias — % of EIA-923 per month</h3>")
        parts.append(section_monthly(year, disp, e923))
        parts.append("<h3>Representative plants — annual generation vs EIA-923 (GWh)</h3>")
        parts.append(section_plant(year, disp, e923))
        parts.append("</div>")

    parts.append("<footer>market-simulator · ERCOT calibration · "
                 "tables computed from persisted dispatch + CAMPD-backfilled benchmark parquets</footer>")
    parts.append("</div></body></html>")
    out = f"{ROOT}/calibration-report.html"
    with open(out, "w") as fh:
        fh.write("".join(parts))
    print("wrote", out)


build()
