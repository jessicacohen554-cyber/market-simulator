"""pjm-h14 phase 0c — WHICH PLANTS carry PJM's COAL_BIT over-run? Zero LP.

Model side: the designated keeper pair's committed run payloads
``frontend/data/backcast/runs/<id>.js`` (per-plant ``m_ann`` TWh + the hourly
``m`` CF series the Run Explorer renders).
Measured side: the committed benchmark ``frontend/data/backcast/bench/PJM/<y>.json.gz``
(per-plant ``c_ann`` CAMPD TWh and ``e_ann`` EIA-923 TWh).

``c_ann``/``e_ann``/``m_ann`` are stored annual totals, NOT decoded byte series, so
every level number here is exact to the payload's own rounding.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUNS = {
    "touchpoint": ROOT / "frontend/data/backcast/runs/2026-09-20-pjm-h13-meritalloc-touchpoint.js",
    "span": ROOT / "frontend/data/backcast/runs/2026-09-20-pjm-h13-meritalloc-span.js",
}
BENCH = ROOT / "frontend/data/backcast/bench/PJM"


def load_run(path: Path) -> dict:
    t = path.read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', t)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def dec(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8).astype(float)


def main() -> None:
    payloads = {}
    for tag, p in RUNS.items():
        d = load_run(p)
        for y, rec in d["years"].items():
            payloads[int(y)] = rec
    years = sorted(payloads)

    print("### 1. PER-PLANT COAL_BIT ledger — model vs CAMPD, TWh (top 20 by |Δ| in 2020)\n")
    tables = {}
    for y in years:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
        mp = payloads[y]["plants"]
        rows = []
        for key, brec in bench.items():
            if brec.get("group") != "COAL_BIT":
                continue
            mrec = mp.get(key, {})
            rows.append(dict(
                key=key, name=brec.get("name", "?")[:22], zone=brec.get("zone", "?").replace("PJM_", ""),
                npl=brec.get("npl", 0),
                campd=float(brec.get("c_ann") or 0.0),
                e923=float(brec.get("e_ann") or 0.0),
                model=float(mrec.get("m_ann") or 0.0),
                r=mrec.get("r"),
                nodata=bool(brec.get("nodata")),
            ))
        t = pd.DataFrame(rows)
        t["delta"] = t["model"] - t["campd"]
        t["meas_cf"] = t["campd"] * 1e6 / (t["npl"] * 8760).replace(0, np.nan)
        t["mod_cf"] = t["model"] * 1e6 / (t["npl"] * 8760).replace(0, np.nan)
        tables[y] = t.set_index("key")

    base = tables[2020].sort_values("delta", ascending=False)
    show = base.head(20)[["name", "zone", "npl", "campd", "model", "delta", "meas_cf", "mod_cf", "r"]]
    print(show.to_string(float_format=lambda v: f"{v:8.3f}"))
    print(f"\n  2020 totals: CAMPD {base['campd'].sum():.2f}  model {base['model'].sum():.2f}  "
          f"Δ {base['delta'].sum():.2f} TWh over {len(base)} plants")

    print("\n### 2. How CONCENTRATED is the miss? (2020 / 2021, cumulative Δ share)\n")
    for y in (2020, 2021, 2025):
        t = tables[y].sort_values("delta", ascending=False)
        pos = t[t["delta"] > 0]
        tot = t["delta"].sum()
        print(f"  {y}: Δ total {tot:7.2f} TWh over {len(t)} plants; "
              f"{len(pos)} over-run (+{pos['delta'].sum():.2f}), {len(t)-len(pos)} under-run "
              f"({t[t['delta']<=0]['delta'].sum():.2f}). "
              f"top-5 = {t.head(5)['delta'].sum()/tot*100:5.1f}%  top-10 = {t.head(10)['delta'].sum()/tot*100:5.1f}%")

    print("\n### 3. THE LAY-UP SIGNATURE — plants whose CAMPD CF is near zero but the model runs\n")
    print("    (measured CF < 0.10 in the year; these are economically laid-up / mothballed units)\n")
    for y in years:
        t = tables[y]
        lay = t[(t["meas_cf"] < 0.10) & (~t["nodata"]) & (t["npl"] > 50)]
        print(f"  {y}: {len(lay):3d} plants, {lay['npl'].sum():7.0f} MW  "
              f"measured {lay['campd'].sum():6.2f} TWh  model {lay['model'].sum():6.2f} TWh  "
              f"Δ {lay['delta'].sum():+6.2f} TWh")

    print("\n### 4. Same, but for MID-CF plants (0.10-0.45) — the cyclers\n")
    for y in years:
        t = tables[y]
        mid = t[(t["meas_cf"] >= 0.10) & (t["meas_cf"] < 0.45) & (~t["nodata"]) & (t["npl"] > 50)]
        hi = t[(t["meas_cf"] >= 0.45) & (~t["nodata"]) & (t["npl"] > 50)]
        print(f"  {y}: cyclers {len(mid):3d} plants {mid['npl'].sum():7.0f} MW Δ {mid['delta'].sum():+6.2f} | "
              f"baseload {len(hi):3d} plants {hi['npl'].sum():7.0f} MW Δ {hi['delta'].sum():+6.2f}")

    print("\n### 5. The single largest contributors across all six years (Δ TWh)\n")
    allk = sorted({k for y in years for k in tables[y].index})
    grid = pd.DataFrame(
        {y: tables[y]["delta"].reindex(allk) for y in years}, index=allk
    )
    names = {}
    for y in years:
        for k, r in tables[y].iterrows():
            names.setdefault(k, f"{r['name']} ({r['zone']}, {r['npl']:.0f}MW)")
    grid.insert(0, "plant", [names.get(k, k) for k in allk])
    grid = grid.loc[grid[years].abs().sum(axis=1).sort_values(ascending=False).index]
    print(grid.head(22).to_string(float_format=lambda v: f"{v:7.2f}"))

    print("\n### 6. HOURLY SHAPE of the top over-runners (2020): does the model ever turn them off?\n")
    bench20 = json.load(gzip.open(BENCH / "2020.json.gz"))["bench"]["plants"]
    for k in base.head(6).index:
        brec, mrec = bench20[k], payloads[2020]["plants"].get(k, {})
        if "m" not in mrec:
            continue
        mcf, ccf = dec(mrec["m"]), dec(brec["campd"])
        print(f"  {base.loc[k,'name']:<22} npl {base.loc[k,'npl']:>5.0f}  "
              f"measured: off-hours(CF<2%) {int((ccf < 2).sum()):5d}  median CF {np.median(ccf):5.1f}  | "
              f"model: off-hours {int((mcf < 2).sum()):5d}  median CF {np.median(mcf):5.1f}   r={mrec.get('r')}")


if __name__ == "__main__":
    main()
