"""SPP-97 phase 0 (zero LP): SPP's OWN CC incremental heat rate by offer band, from CEMS.

The keeper offers every CC_REGULAR tranche (committed / econ_low / econ_high / peak) at the
plant's measured AVERAGE heat rate x 0.93, so each plant is one flat price step and the class
dispatches 0-or-100 %. This probe measures, per SPP CC plant (the ``flag=='ok'`` rows of
``campd_cc_heat_rates_SPP.csv``, whose boundary guard confirms the steam turbine is metered),
the incremental heat rate dHeatInput/dLoad over each band of the plant's own tranche split
(``thermal_tranches_SPP.csv``: committed_pct, peaking_pct; econ split at econ_low_share 0.5),
and reports it as a ratio to the plant's average heat rate over the same hours.

Method: plant-hour sums of CEMS heatInput and grossLoad over the plant's CC units, hours with
every reporting unit at opTime >= 0.99 dropped only if load is zero; load normalised by the plant's
p99 hourly load; heat input binned on 2 %-of-max load bins (median per bin, >= 20 h), then a
monotone piecewise-linear interpolation gives HI at each band edge. Incremental HR of a band =
(HI(hi) - HI(lo)) / (L(hi) - L(lo)). Committed band = average HR at its top edge (no-load +
min-load, what a committed block actually costs per MWh). Years 2019-2025 pooled, the same window
the applied CC heat rates use.

Usage: uv run python scripts/probes/_spp97_cc_incremental_hr.py
Writes docs/records/spp/spp97/cc_incremental_hr.json
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs/records/spp/spp97"
LEG = REPO / "data/raw/_processed-legacy"
YEARS = range(2019, 2026)
BIN = 0.02
MIN_BIN_HOURS = 20
ECON_LOW_SHARE = 0.5  # offer_curve_by_group CC_REGULAR econ_low_share in the keeper


def plant_curve(h: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Return (load fraction bin centres, median heat input MMBtu/h) for one plant."""
    h = h[h.load > 0]
    lmax = h.load.quantile(0.99)
    f = (h.load / lmax).clip(upper=1.0)
    b = (f / BIN).round() * BIN
    g = h.assign(b=b).groupby("b").agg(hi=("hi", "median"), n=("hi", "size"), ld=("load", "median"))
    g = g[g.n >= MIN_BIN_HOURS]
    # enforce monotone HI in load (CEMS noise at sparse bins)
    return g.ld.values / lmax, np.maximum.accumulate(g.hi.values), lmax


def main() -> None:
    """Measure band incremental HR ratios for every applied SPP CC plant."""
    OUT.mkdir(parents=True, exist_ok=True)
    hr = pd.read_csv(LEG / "campd_cc_heat_rates_SPP.csv")
    hr = hr[(hr.flag == "ok") & (hr.year == 0)]
    tr = pd.read_csv(LEG / "thermal_tranches_SPP.csv")
    tr = tr[tr.plant_group == "CC_REGULAR"].set_index("plant_code")
    units = pd.read_csv(LEG / "campd_cc_heat_rates_SPP_units.csv")
    codes = {str(int(x)) for x in set(hr.plant_code) & set(tr.index)}
    frames = []
    for f in sorted((REPO / "data/raw/campd-unit-level").glob("*_20*.parquet")):
        y = int(f.stem.split("_")[1])
        if y not in YEARS:
            continue
        d = pd.read_parquet(f, columns=["facilityId", "unitId", "date", "hour", "grossLoad", "heatInput", "unitType"])
        d = d[d.facilityId.isin(codes) & d.unitType.str.lower().str.startswith("combined cycle", na=False)]
        if len(d):
            frames.append(d)
    c = pd.concat(frames)
    c = c.merge(units[["plant_code", "unit_id"]].astype(str), left_on=[c.facilityId.astype(str), c.unitId.astype(str)],
                right_on=["plant_code", "unit_id"], how="inner")
    c["facilityId"] = c.facilityId.astype(int)
    h = c.groupby(["facilityId", "date", "hour"]).agg(load=("grossLoad", "sum"), hi=("heatInput", "sum")).reset_index()
    rows = []
    for pc, g in h.groupby("facilityId"):
        x, y, lmax = plant_curve(g)
        if len(x) < 10:
            continue
        t = tr.loc[pc]
        com = t.committed_pct / 100.0
        pk = t.peaking_pct / 100.0
        edges = [max(com, x.min()), None, 1.0 - pk, 1.0]
        edges[1] = edges[0] + ECON_LOW_SHARE * (edges[2] - edges[0])
        hi_at = np.interp(edges, x, y)
        avg_hr = g.hi.sum() / g.load.sum()
        inc = [(hi_at[i + 1] - hi_at[i]) / ((edges[i + 1] - edges[i]) * lmax) for i in range(3)]
        rows.append(
            {
                "plant_code": int(pc),
                "name": t["name"],
                "cap_p99_mw": round(float(lmax), 1),
                "avg_hr": round(float(avg_hr), 3),
                "committed_edge": round(edges[0], 3),
                "peak_edge": round(edges[2], 3),
                "committed_avg_hr": round(float(hi_at[0] / (edges[0] * lmax)), 3),
                "inc_econ_low": round(float(inc[0]), 3),
                "inc_econ_high": round(float(inc[1]), 3),
                "inc_peak": round(float(inc[2]), 3),
                "ratio_committed": round(float(hi_at[0] / (edges[0] * lmax) / avg_hr), 3),
                "ratio_econ_low": round(float(inc[0] / avg_hr), 3),
                "ratio_econ_high": round(float(inc[1] / avg_hr), 3),
                "ratio_peak": round(float(inc[2] / avg_hr), 3),
                "hours": int(len(g)),
            }
        )
    df = pd.DataFrame(rows)
    w = df.cap_p99_mw
    summ = {
        k: {"cap_weighted": round(float((df[k] * w).sum() / w.sum()), 3), "median": round(float(df[k].median()), 3),
            "p25": round(float(df[k].quantile(0.25)), 3), "p75": round(float(df[k].quantile(0.75)), 3)}
        for k in ("ratio_committed", "ratio_econ_low", "ratio_econ_high", "ratio_peak")
    }
    print(df.to_string())
    print(json.dumps(summ, indent=1))
    (OUT / "cc_incremental_hr.json").write_text(json.dumps({"plants": rows, "summary": summ, "n_plants": len(rows)}, indent=1))


if __name__ == "__main__":
    main()
