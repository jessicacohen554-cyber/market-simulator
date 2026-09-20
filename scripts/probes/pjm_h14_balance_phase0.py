"""pjm-h14 phase 0b — is PJM's 2020-2022 fossil over-run a MIX defect or a LEVEL defect?

Zero LP. Uses the committed keeper hourlies for the model side and the committed
benchmark's ``classFull`` (EIA-923/CEMS annual, the SAME series C1 scores against)
for the measured side, so no decode quantisation enters any level claim.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "frontend/data/backcast/bench/PJM"
BUNDLES = {y: ROOT / ("results/calibration/pjm_h13_meritalloc_touchpoint"
                      if y <= 2022 else "results/calibration/pjm_h13_meritalloc_span")
           for y in range(2020, 2026)}
YEARS = sorted(BUNDLES)


def model_classes(year: int) -> pd.Series:
    df = pd.read_parquet(BUNDLES[year] / f"hourly/class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return df.groupby("klass")["mw"].sum() / 1e6


def main() -> None:
    print("### A. C1 class table — model vs the SCORED measured series (classFull), TWh\n")
    frames = {}
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        meas = pd.Series(bench["classFull"])
        mod = model_classes(y)
        keys = sorted(set(meas.index) | set(mod.index))
        frames[y] = pd.DataFrame(
            {"meas": meas.reindex(keys).fillna(0.0), "model": mod.reindex(keys).fillna(0.0)}
        ).assign(delta=lambda d: d["model"] - d["meas"])["delta"]
    d = pd.DataFrame(frames)
    d = d.loc[d.abs().max(axis=1).sort_values(ascending=False).index]
    print(d.to_string(float_format=lambda v: f"{v:8.3f}"))

    print("\n### B. TOTAL model generation vs TOTAL measured (classFull sum), TWh\n")
    rows = []
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        meas = pd.Series(bench["classFull"])
        mod = model_classes(y)
        s = pd.read_parquet(BUNDLES[y] / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        internal = s[s["zone"] != "PJM_external"]
        ext = s[s["zone"] == "PJM_external"]
        rows.append(dict(
            year=y,
            meas_total=float(meas.sum()),
            model_total=float(mod.sum()),
            delta=float(mod.sum() - meas.sum()),
            e930_total=float(sum(bench["e930"][k] for k in
                                 ("gas", "coal", "nuclear", "wind", "solar", "other", "oil"))),
            model_load_TWh=float(internal["demand"].sum() / 1e6),
            ext_node_load_TWh=float(ext["demand"].sum() / 1e6) if len(ext) else np.nan,
            slack_GWh=float(internal["slack"].sum() / 1e3),
            dump_GWh=float(internal["dump"].sum() / 1e3),
        ))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:10.3f}"))

    print("\n### C. The implied residual: model_gen - model_load  (= net export + losses), TWh\n")
    print("    against the measured net interchange the bench records, if present.\n")
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        mod = model_classes(y)
        s = pd.read_parquet(BUNDLES[y] / f"hourly/system_{y}.parquet")
        s = s[(s["pass"] == "P1") & (s["zone"] != "PJM_external")]
        load = s["demand"].sum() / 1e6
        print(f"  {y}: model gen {mod.sum():8.2f}  model internal load {load:8.2f}  "
              f"implied net export {mod.sum()-load:8.2f}   measured total gen {sum(bench['classFull'].values()):8.2f}")

    print("\n### D. NON-fossil model vs measured (where the balance could be absorbed), TWh\n")
    nf = ["nuclear", "wind", "solar", "hydro", "biomass", "storage", "OTHER"]
    rows = []
    for y in YEARS:
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        meas = pd.Series(bench["classFull"])
        mod = model_classes(y)
        for k in nf:
            if k in meas.index or k in mod.index:
                rows.append(dict(year=y, klass=k, meas=float(meas.get(k, 0.0)),
                                 model=float(mod.get(k, 0.0)),
                                 delta=float(mod.get(k, 0.0) - meas.get(k, 0.0))))
    t = pd.DataFrame(rows)
    print(t.pivot(index="klass", columns="year", values="delta").to_string(float_format=lambda v: f"{v:8.3f}"))


if __name__ == "__main__":
    main()
