#!/usr/bin/env python3
"""miso-269 phase 0: is the keeper's February-2021 gas LEVEL the C3b 2021 object?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Nothing is solved. The keeper's 2021 fleet
and assembled fuel-price array are rebuilt with ``run_year(..., fleet_only=True)``
— the same assembly the LP is handed, every gas overlay applied — and compared
day by day against the traded Chicago Citygate and Henry Hub daily prints
(``data/raw/gas-prices/miso_citygate_daily.csv``, flow-date placed exactly as the
production overlay places them).

THE HYPOTHESIS (FINDING-miso268 §1, untested there): MISO's February-2021
EIA-923 delivered gas price is a MONTHLY average that folds Winter Storm Uri's
purchases into every February day; ``miso_winter_citygate_daily`` reshapes
within the month but preserves the mean, so non-storm days inherit part of the
spike.

WHAT IT REPORTS, per day of Feb and Oct-Nov 2021 (and the monthly means for
every month): the capacity-weighted mean gas fuel price over the model's gas
rows, split Chicago-hub zones vs the rest, beside the Chicago and Henry Hub
daily prints. It also reports the keeper's P1 load-weighted price and the
actual RT price per day, so the reader can see whether the gas-price gap and the
price gap co-move. Nothing is tuned, nothing is selected.

Usage::

    uv run python scripts/probes/_miso269_feb2021_gas_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.fuel.basis.miso import (  # noqa: E402
    _GAS_FUEL_IDX,
    _miso_chicago_hub_zones,
    miso_chicago_daily_shape_factors,
)
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402

KEEPER = REPO / "results/calibration/miso268_yard_span"
OUT = REPO / "results/calibration/_miso269_feb2021_gas_phase0.json"
YEAR = 2021


def rebuild(year: int) -> dict:
    """The keeper's fleet_only state for ``year`` (no LP)."""
    meta = json.loads((KEEPER / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(KEEPER, year))
    cfg = json.loads((KEEPER / f"run_config_{year}.json").read_text())
    sc = cfg.get("scenario_config", cfg)
    gas = sc.get("gas_price_override", meta.get("gas_price"))
    return run_year(year, "MISO", 8760, gas, {}, fleet_only=True, **kw)


def main() -> int:
    """Run the probe and write the JSON record."""
    st = rebuild(YEAR)
    fa, fp, cfg = st["fleet_arrays"], st["fuel_prices"], st["config"]
    from market_sim.config.iso_configs import get_iso_config

    zones = list(get_iso_config("MISO").zone_names)
    chi = _miso_chicago_hub_zones(YEAR, None)
    gas = np.nonzero(np.isin(fa.fuel_type_idx, _GAS_FUEL_IDX))[0]
    cap = np.asarray(fa.pmax, dtype=float)[gas]
    zchi = np.array([zones[z] in chi for z in fa.zone_idx[gas]])
    day = np.arange(8760) // 24
    dates = pd.Timestamp(f"{YEAR}-01-01") + pd.to_timedelta(np.arange(365), "D")

    def daily_mean(rows_mask: np.ndarray) -> np.ndarray:
        w = cap[rows_mask]
        hourly = (fp[gas[rows_mask], :] * w[:, None]).sum(0) / w.sum()
        return np.bincount(day, weights=hourly)[:365] / 24.0

    g_chi, g_rest, g_all = daily_mean(zchi), daily_mean(~zchi), daily_mean(np.ones_like(zchi))

    # Traded daily prints, flow-date placed as production places them.
    shape = miso_chicago_daily_shape_factors(YEAR, 8760, None)
    cg = pd.read_csv(REPO / "data/raw/gas-prices/miso_citygate_daily.csv", parse_dates=["date"])
    cg = cg[cg.date.dt.year == YEAR].set_index("date")
    # forward-fill trade-date prints onto calendar flow days (weekend package)
    cal = cg.reindex(pd.date_range(f"{YEAR}-01-01", f"{YEAR}-12-31")).ffill()

    # Keeper P1 load-weighted price and actual RT (load-weighted over zones).
    sysd = pd.read_parquet(KEEPER / f"hourly/system_{YEAR}.parquet")
    sysd = sysd[sysd["pass"] == "P1"] if "pass" in sysd else sysd
    lw = sysd.assign(pd_=sysd.price * sysd.demand).groupby("hour")[["pd_", "demand"]].sum()
    model_px = (lw.pd_ / lw.demand).to_numpy()
    model_d = np.bincount(day, weights=model_px)[:365] / 24.0

    rows = []
    for i, d in enumerate(dates):
        if d.month not in (1, 2, 3, 10, 11, 12):
            continue
        rows.append({
            "date": d.strftime("%Y-%m-%d"),
            "model_gas_chicago_zones": round(float(g_chi[i]), 3),
            "model_gas_other_zones": round(float(g_rest[i]), 3),
            "model_gas_all": round(float(g_all[i]), 3),
            "chicago_citygate_print": round(float(cal.chicago_citygate_usd_mmbtu.iloc[i]), 3),
            "henry_hub_print": round(float(cal.henry_hub_usd_mmbtu.iloc[i]), 3),
            "chicago_shape_factor": round(float(shape[i * 24]), 4),
            "model_price_lw": round(float(model_d[i]), 2),
        })
    monthly = []
    m_idx = dates.month.to_numpy()
    for m in range(1, 13):
        k = m_idx == m
        monthly.append({
            "month": m,
            "model_gas_chicago_zones": round(float(g_chi[k].mean()), 3),
            "model_gas_other_zones": round(float(g_rest[k].mean()), 3),
            "chicago_print_mean_calendar": round(float(cal.chicago_citygate_usd_mmbtu.to_numpy()[k].mean()), 3),
            "henry_hub_mean_calendar": round(float(cal.henry_hub_usd_mmbtu.to_numpy()[k].mean()), 3),
            "model_price_lw": round(float(model_d[k].mean()), 2),
        })
    rec = {
        "year": YEAR, "keeper": KEEPER.name, "n_gas_rows": int(gas.size),
        "chicago_zones": sorted(chi), "gas_cap_mw_chicago": round(float(cap[zchi].sum())),
        "gas_cap_mw_other": round(float(cap[~zchi].sum())),
        "monthly": monthly, "daily": rows,
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(pd.DataFrame(monthly).to_string(index=False))
    print(pd.DataFrame([r for r in rows if r["date"][5:7] == "02"]).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
