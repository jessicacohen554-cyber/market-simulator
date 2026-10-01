"""NYISO-NEXT-25 phase 0 (ZERO LP): monthly trade/calendar compression of the NYISO daily gas construction.

``_nyiso_hub_daily_gas_prices`` scales the month's hub level by day factors renormalised to a
CALENDAR-day mean of 1.0, while the level is a TRADE-day mean of the Transco Z6 NY prints. Every
ordinary day of a month is therefore scaled by ``c = trade_mean / calendar_mean`` (trade-date
interpolation: ``c_trade``; ``nyiso_gas_flow_date`` staircase: ``c_flow``). This census reports
``c`` per month 2021-2025 from the committed print series beside the keeper's NYC monthly
model - DA gap (committed sidecars). Diagnostic only (rule 13).

Usage: uv run python scripts/probes/nyisonext25_compression_census.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.nyisonext25_offcap_winter_gap import ZONAL, _bundle, _hourly_price  # noqa: E402

DIM = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def census(years: list[int]) -> pd.DataFrame:
    """Per-month compression factors and the keeper NYC gap."""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel import hubs

    a = pd.read_parquet(ZONAL)
    rows = []
    for y in years:
        cfg = ScenarioConfig(iso="NYISO", mode="backcast", nyiso_gas_flow_date=True)
        flow = hubs.nyiso_transco_z6_flow_daily(cfg, y)
        dated = hubs._transco_z6_daily_dated(hubs.TRANSCO_Z6_NY_DAILY_PATH).get(y, {})
        p = _hourly_price(_bundle(y) / "hourly" / f"system_{y}.parquet", y, "NYC")
        d = (
            a[(a.year == y) & (a.zone == "NYC")]
            .sort_values("hour")
            .da.to_numpy()[:8760]
        )
        gap = (p - d).reshape(365, 24).mean(1)
        for m in range(12):
            dd = dated.get(m + 1, {})
            if not dd:
                continue
            days = np.array(sorted(dd), float)
            vals = np.array([dd[int(x)] for x in days])
            interp = np.interp(np.arange(DIM[m]), days - 1, vals)
            d0 = sum(DIM[:m])
            seg = flow[d0 : d0 + DIM[m]]
            rows.append(
                {
                    "year": y,
                    "month": m + 1,
                    "trade_mean": round(float(vals.mean()), 3),
                    "calendar_mean_trade_dated": round(float(interp.mean()), 3),
                    "calendar_mean_flow_dated": round(float(seg.mean()), 3),
                    "c_trade": round(float(vals.mean() / interp.mean()), 3),
                    "c_flow": round(float(vals.mean() / seg.mean()), 3),
                    "keeper_nyc_gap": round(float(gap[d0 : d0 + DIM[m]].mean()), 2),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    """Write the census JSON with winter correlations."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025])  # fmt: skip
    a = ap.parse_args()
    r = census(a.years)
    w = r[r.month.isin([1, 2, 12])]
    out = {
        "rows": r.to_dict("records"),
        "winter_corr_c_trade_vs_gap": round(
            float(np.corrcoef(w.c_trade, w.keeper_nyc_gap)[0, 1]), 3
        ),  # fmt: skip
        "winter_corr_c_flow_vs_gap": round(
            float(np.corrcoef(w.c_flow, w.keeper_nyc_gap)[0, 1]), 3
        ),  # fmt: skip
        "all_corr_c_trade_vs_gap": round(
            float(np.corrcoef(r.c_trade, r.keeper_nyc_gap)[0, 1]), 3
        ),  # fmt: skip
    }
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(w.to_string(index=False))
    print({k: v for k, v in out.items() if k != "rows"})


if __name__ == "__main__":
    main()
