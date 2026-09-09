"""SPP-51c phase 0 diagnostic: is net-load-on-delivered CENSORED by curtailment?

The PRECOMMIT's indicator NL(t) = load - delivered_wind - delivered_solar is fully
metered. This asks the question that decides whether that is a strength or the
instrument's identification defect: in a curtailment hour the system is HELD at its
turn-down floor BY the curtailment, so NL is clipped there and cannot carry the DEPTH
of the spill. Measured, not asserted. Zero LP, no outcome is used to select anything --
the measured-negative-hour set is used only to LABEL, never to fit.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data import renewables as R
from market_sim.data.eia930.demand import load_demand

ISO, YEARS = "SPP", (2023, 2024, 2025)
lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source" / f"actual_lmp_hourly_{ISO}.parquet")
iso_cfg = get_iso_config(ISO)
out = {}

for year in YEARS:
    gen = R.load_eia_hourly_renewable_gen(ISO, year)
    wind = np.asarray(gen["wind"], float)
    solar = np.asarray(gen.get("solar", np.zeros(HOURS_PER_YEAR)), float)
    load = load_demand(ISO, year, iso_cfg).sum(axis=0)
    nl = load - wind - solar
    sub = lmp[lmp["year"] == year] if "year" in lmp.columns else lmp
    rt = sub.sort_values("hour")["rt"].to_numpy(float)[:HOURS_PER_YEAR]
    neg = np.isfinite(rt) & (rt < 0.0)
    n = int(neg.sum())

    order = np.argsort(nl)                       # ascending net load
    low_n = np.zeros(HOURS_PER_YEAR, bool); low_n[order[:n]] = True
    # same test on the availability axis, for the like-for-like comparison
    order_w = np.argsort(-wind)
    high_w = np.zeros(HOURS_PER_YEAR, bool); high_w[order_w[:n]] = True

    out[year] = {
        "load_mean_GW": float(load.mean()) / 1e3,
        "wind_mean_GW": float(wind.mean()) / 1e3,
        "solar_mean_GW": float(solar.mean()) / 1e3,
        "nl_mean_GW": float(nl.mean()) / 1e3,
        # CENSORING TEST: is NL tightly clustered (clipped at a floor) in the
        # measured-negative hours relative to the rest of the year?
        "nl_neg_mean_GW": float(nl[neg].mean()) / 1e3,
        "nl_neg_sd_GW": float(nl[neg].std()) / 1e3,
        "nl_pos_mean_GW": float(nl[~neg].mean()) / 1e3,
        "nl_pos_sd_GW": float(nl[~neg].std()) / 1e3,
        "nl_neg_p05_GW": float(np.percentile(nl[neg], 5)) / 1e3,
        "nl_neg_p95_GW": float(np.percentile(nl[neg], 95)) / 1e3,
        "nl_cv_neg": float(nl[neg].std() / nl[neg].mean()),
        "nl_cv_all": float(nl.std() / nl.mean()),
        # RANKING POWER: of the n lowest-net-load hours, how many are measured-negative?
        "recall_lowest_NL": float((low_n & neg).sum() / n),
        "recall_highest_wind": float((high_w & neg).sum() / n),
        "n_neg": n,
        # how much of the year sits BELOW the mean NL of the negative hours
        "hours_below_neg_mean_NL": int((nl < nl[neg].mean()).sum()),
    }

print(json.dumps(out, indent=1))
Path("results/calibration/_spp51c_censoring.json").write_text(json.dumps(out, indent=1))
