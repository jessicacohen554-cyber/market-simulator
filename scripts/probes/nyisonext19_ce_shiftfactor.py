"""NYISO-NEXT-19 phase 0 (ZERO LP): is CENTRAL EAST one shadow price with stable zone shift factors?

Reads only committed raw data:

* NYISO RT 5-minute zonal LBMP with its loss and congestion components
  (``data/raw/lmp-data/NYISO/*realtime_zone_csv.zip``: all of 2022, plus
  2023-06, 2023-12, 2024-02..06, 2024-09, 2025-08);
* the hourly CENTRAL EAST flow and posted limit
  (``data/raw/NYISO/interface-flows``).

Congestion is taken relative to MHK VL (zone E, the CE sending end), so a
zone's value is the CE-side congestion step from E to that zone. In intervals
where F (CAPITL) sits more than $5 above E on congestion, each zone's ratio
to F estimates its CE shift factor relative to F's. A rank-1 congestion matrix
(one binding element) shows up as a dominant first singular value.

Blocks: ``ratio`` (per-zone ratio quantiles, all active intervals), ``svd``
(variance share of the first three components), ``by_year`` (median ratios),
``loading_2022`` (F-E congestion by measured CE loading band, hourly) and
``monthly_2022`` (median NYC/F and HUD VL/F ratio by month).

Usage::

    python3 scripts/probes/nyisonext19_ce_shiftfactor.py \
        --out results/phase0/nyiso/_nyisonext19_ce_shiftfactor.json
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RT_DIR = REPO / "data/raw/lmp-data/NYISO"
FLOW_DIR = REPO / "data/raw/NYISO/interface-flows"
ZONES = ["WEST", "GENESE", "CENTRL", "NORTH", "MHK VL", "CAPITL",
         "HUD VL", "MILLWD", "DUNWOD", "N.Y.C.", "LONGIL"]
ACTIVE_USD = 5.0  # F-E congestion step that marks a CE-active interval, $/MWh (probe screen)
CONG = "Marginal Cost Congestion ($/MWHr)"


def load_rt_congestion() -> pd.DataFrame:
    """RT 5-min congestion component, interval x zone, relative to MHK VL (zone E)."""
    frames = []
    for f in sorted(RT_DIR.glob("*realtime_zone_csv.zip")):
        z = zipfile.ZipFile(f)
        frames += [pd.read_csv(z.open(n), usecols=["Time Stamp", "Name", CONG])
                   for n in z.namelist()]
    d = pd.concat(frames)
    d["t"] = pd.to_datetime(d["Time Stamp"])
    c = d.pivot_table(index="t", columns="Name", values=CONG)[ZONES]
    return c.sub(c["MHK VL"], axis=0)


def ce_hourly(year: int) -> pd.DataFrame:
    """Hourly CENTRAL EAST flow and posted positive limit, local hour-beginning."""
    f = pd.read_csv(FLOW_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz")
    f = f[f.interface == "CENTRAL EAST - VC"].copy()
    f["t"] = pd.to_datetime(f.interval_start_local)
    f = f.set_index("t")
    return f[~f.index.duplicated()][["flow_mw", "positive_limit_mw"]]


def main(argv: list[str] | None = None) -> int:
    """Run the probe and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path,
                    default=REPO / "results/phase0/nyiso/_nyisonext19_ce_shiftfactor.json")
    a = ap.parse_args(argv)

    rel = load_rt_congestion()
    act = rel["CAPITL"] < -ACTIVE_USD  # congestion sign: negative raises LBMP
    ratio = rel[act].div(rel["CAPITL"][act], axis=0)
    q = ratio.quantile([0.1, 0.25, 0.5, 0.75, 0.9]).T.round(3)

    cols = [z for z in ZONES if z != "MHK VL"]
    _, s, vt = np.linalg.svd(rel.loc[act, cols].to_numpy(), full_matrices=False)
    pc1 = vt[0] / vt[0][cols.index("CAPITL")]

    by_year = {}
    for y in sorted(set(rel.index.year)):
        m = act & (rel.index.year == y)
        by_year[int(y)] = {"active_intervals": int(m.sum()),
                           "median_ratio": ratio[m[act]].median().round(3).to_dict()}

    # 2022 (the one full RT year): F-E congestion by measured CE loading band.
    r22 = rel[rel.index.year == 2022].copy()
    r22.index = (r22.index - pd.Timedelta(minutes=5)).floor("h")  # interval-ending -> hour-beginning
    j = r22.groupby(level=0).mean().join(ce_hourly(2022), how="inner")
    j["load"] = j.flow_mw / j.positive_limit_mw
    j["fe"] = -j["CAPITL"]
    loading = {}
    for lo, hi in [(0, 0.7), (0.7, 0.85), (0.85, 0.95), (0.95, 9)]:
        m = (j.load >= lo) & (j.load < hi)
        loading[f"{lo}-{hi}"] = {"hours": int(m.sum()),
                                 "mean_FE_congestion": round(float(j.fe[m].mean()), 2),
                                 "share_FE_gt5": round(float((j.fe[m] > ACTIVE_USD).mean()), 3)}
    ja = j[j.fe > ACTIVE_USD]
    monthly = {z: (ja[z] / ja["CAPITL"]).groupby(ja.index.month).median().round(3).to_dict()
               for z in ("N.Y.C.", "HUD VL")}

    rec = {
        "active_rule": f"F-E congestion > ${ACTIVE_USD}/MWh, RT 5-min",
        "intervals": int(len(rel)), "active_intervals": int(act.sum()),
        "ratio_quantiles": q.to_dict(orient="index"),
        "svd_variance_share": (s**2 / np.sum(s**2))[:3].round(4).tolist(),
        "pc1_loadings_F1": dict(zip(cols, pc1.round(3).tolist())),
        "by_year": by_year, "loading_2022": loading, "monthly_2022": monthly,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rec, indent=1, default=float))
    print(json.dumps({k: rec[k] for k in ("active_intervals", "svd_variance_share",
                                          "pc1_loadings_F1", "loading_2022")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
