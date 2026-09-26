"""neiso-119 phase 0 (d), zero LP: decompose the price-setting CC_REGULAR offer.

fleet_only rebuild of a year on the keeper recipe; for every CC_REGULAR tranche
reports heat_rate, delivered fuel, vom and mc_base, and splits mc_base into
phys burn (phys band x base HR x fuel), the anchored margin term
(offer_markup_hr x anchor) and the remainder. Writes phase0_cc_offer_<Y>.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
BUNDLE = REPO / "results/calibration/neiso118_span"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2019)
    y = ap.parse_args().year
    os.chdir(REPO)
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = rk.run_year_kwargs(meta)
    kw.update(rk.derived_run_year_inputs(BUNDLE, y))
    st = run_year(
        y,
        "NEISO",
        8760,
        henry_hub_actual(rcf._load_reference(), y),
        {},
        fleet_only=True,
        **kw,
    )
    set_eia860_vintage(None)
    fa, gens = st["fleet_arrays"], st["fleet"]
    cfg = st["config"]
    anchor = float(cfg.gas_offer_margin_anchor)
    grp = np.asarray(fa.plant_group).astype(str)
    mc = np.asarray(st["mc_base"], float)
    fp = np.asarray(st["fuel_prices"], float)
    hr = np.asarray(fa.heat_rate, float)
    vom = np.asarray(fa.vom, float)
    mk = np.array([float(getattr(g, "offer_markup_hr", 0.0)) for g in gens])
    band = np.array([str(getattr(g, "tranche", getattr(g, "band", ""))) for g in gens])
    mon = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), "h")).month
    rows = []
    for klass in ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS"):
        m = grp == klass
        for k in range(1, 13):
            cols = mon == k
            f = fp[m][:, cols].mean(1)
            c = mc[m][:, cols].mean(1)
            w = np.asarray(fa.pmax, float)[m]
            margin = mk[m] * anchor
            rows.append(
                {
                    "class": klass,
                    "month": k,
                    "fuel": round(float((f * w).sum() / w.sum()), 3),
                    "mc": round(float((c * w).sum() / w.sum()), 2),
                    "hr": round(float((hr[m] * w).sum() / w.sum()), 3),
                    "markup_hr": round(float((mk[m] * w).sum() / w.sum()), 3),
                    "anchored_margin_$": round(float((margin * w).sum() / w.sum()), 2),
                    "margin_if_scaled_$": round(
                        float((mk[m] * f * w).sum() / w.sum()), 2
                    ),
                    "vom": round(float((vom[m] * w).sum() / w.sum()), 2),
                    "p10_mc": round(float(np.percentile(c, 10)), 2),
                }
            )
    bands = sorted(set(band[grp == "CC_REGULAR"]))
    out = {"year": y, "anchor": anchor, "bands": bands, "rows": rows}
    Path(__file__).with_name(f"phase0_cc_offer_{y}.json").write_text(
        json.dumps(out, indent=1)
    )
    print(
        "anchor",
        anchor,
        "bands",
        bands,
        "gen attrs",
        [a for a in dir(gens[0]) if not a.startswith("_")][:60],
    )
    for r in rows:
        if r["class"] == "CC_REGULAR":
            print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
