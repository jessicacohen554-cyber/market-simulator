#!/usr/bin/env python3
"""miso-285 phase 0 (ZERO LP): the MISO night price overshoot — quantity side.

For each span year, over night hours h0-5 (model clock) this compares the
designated keeper's committed P1 hourlies (``results/calibration/miso280_span``)
against measured MISO data:

* price: keeper MISO-Illinois vs ILLINOIS.HUB RT (hub clock lag chosen by
  max correlation over -2..+2 h, reported);
* supply by EIA-930 fuel series: keeper class dispatch re-bucketed to the
  930 series vs the benchmark's EIA-930 frame (``build_benchmark_frames``);
* the model's night band composition (must-run / committed / econ / peak);
* the reserve-family night duals.

Output: ``results/calibration/_miso285_night_supply_identity.json``.
Rule 13: nothing here feeds a solve.

Usage::

    uv run python scripts/probes/_miso285_night_supply_identity.py --bench-pkl X
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes._miso283_premium_localize import hub  # noqa: E402

KEEPER = REPO / "results/calibration/miso280_span"
YEARS = range(2019, 2026)
NIGHT = range(0, 6)
# keeper class -> EIA-930 fuel series (the benchmark's own series set)
SERIES = {
    "COAL_BIT": "coal",
    "COAL_LIGNITE": "coal",
    "COAL_PRB": "coal",
    "CC_CHP": "gas",
    "CC_REGULAR": "gas",
    "CT_CHP": "gas",
    "CT_PEAKER": "gas",
    "ST_CHP": "gas",
    "ST_GAS": "gas",
    "nuclear": "nuclear",
    "wind": "wind",
    "solar": "solar",
    "hydro": "hydro",
    "oil": "other",
    "biomass": "other",
    "OTHER": "other",
    "import": "interchange",
}


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--bench-pkl", required=True, help="pickled build_benchmark_frames dict"
    )
    args = ap.parse_args()
    e930 = pickle.load(open(args.bench_pkl, "rb"))["eia930"]
    out: dict = {}
    for y in YEARS:
        hod = np.arange(8760) % 24
        night = np.isin(hod, list(NIGHT))
        s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        pz = s.pivot(index="hour", columns="zone", values="price").sort_index()
        dz = s.pivot(index="hour", columns="zone", values="demand").sort_index()
        pil = pz["MISO-Illinois"].to_numpy()
        h = hub(y, "rt")["ILLINOIS.HUB"].to_numpy()
        lags = {}
        for lag in range(-2, 3):
            hv = np.roll(h, lag)
            ok = ~np.isnan(hv)
            lags[lag] = float(np.corrcoef(pil[ok], hv[ok])[0, 1])
        best = max(lags, key=lags.get)
        hb = np.roll(h, best)
        ok = night & ~np.isnan(hb)
        yo = {
            "hub_lag_h": best,
            "hub_lag_r": {k: round(v, 4) for k, v in lags.items()},
            "night_price": {
                "model_IL": round(float(pil[ok].mean()), 2),
                "hub_IL": round(float(hb[ok].mean()), 2),
                "diff": round(float((pil - hb)[ok].mean()), 2),
            },
        }
        # supply identity, whole footprint (internal zones), night
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"].copy()
        ch["series"] = ch.klass.astype(str).map(SERIES).fillna("other")
        m = ch.pivot_table(index="hour", columns="series", values="mw", aggfunc="sum")
        m = m.reindex(range(8760)).fillna(0.0)
        a = e930[e930.year == y].pivot(index="hour", columns="series", values="mw")
        a = a.reindex(range(8760))
        rows = {}
        for ser in [
            "coal",
            "gas",
            "nuclear",
            "wind",
            "solar",
            "hydro",
            "other",
            "interchange",
            "battery",
        ]:
            mv = m[ser].to_numpy() if ser in m else np.zeros(8760)
            av = a[ser].to_numpy() if ser in a else np.full(8760, np.nan)
            okk = night & ~np.isnan(av)
            rows[ser] = {
                "model": round(float(mv[okk].mean()), 0),
                "actual": round(float(av[okk].mean()), 0),
            }
        internal = [z for z in dz.columns if not z.startswith("MISO_external")]
        rows["demand_internal"] = {
            "model": round(float(dz[internal].to_numpy()[night].sum(1).mean()), 0)
        }
        yo["night_supply_mw"] = rows
        # band composition, night, by class
        cb = pd.read_parquet(KEEPER / f"hourly/class_band_hourly_{y}.parquet")
        cb = cb[(cb["pass"] == "P1") & np.isin(cb.hour % 24, list(NIGHT))]
        yo["night_band_mw"] = (
            cb.groupby(["klass", "band"], observed=True)
            .mw.sum()
            .div(night.sum())
            .round(0)
            .unstack(fill_value=0)
            .to_dict("index")
        )
        rf = pd.read_parquet(KEEPER / f"hourly/reserve_family_{y}.parquet")
        rf = rf[(rf["pass"] == "P1") & np.isin(rf.hour % 24, list(NIGHT))]
        yo["night_reserve"] = (
            rf.groupby(["family", "reserve_class"], observed=True)
            .agg(
                dual=("dual", "mean"),
                req=("requirement_mw", "mean"),
                held=("held_mw", "mean"),
                short=("shortfall_mw", "sum"),
            )
            .round(2)
            .reset_index()
            .to_dict("records")
        )
        yo["night_zone_price"] = {
            z: round(float(pz[z].to_numpy()[night].mean()), 2) for z in pz.columns
        }
        out[str(y)] = yo
        print(y, json.dumps(yo["night_price"]), "lag", best)
    (REPO / "results/calibration/_miso285_night_supply_identity.json").write_text(
        json.dumps(out, indent=1, default=str)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
