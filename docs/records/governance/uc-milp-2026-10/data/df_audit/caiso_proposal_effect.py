"""UC-DF-AUDIT task 4: zero-LP effect of the proposed CAISO DA-basis repair (rule 14).

Current (commitment_demand.ba_forecast_error_mw): EIA-930 CISO "Demand
forecast" - "Demand". CAISO's day-ahead load forecast (= OASIS SYS_FCST_DA_MW
CA ISO-TAC, table G1) excludes storage charging; its integrated actual load,
and the EIA "Demand" cell, include it (G3: coefficient -0.91 to -1.14 per MW of
charging). Proposed: DF - (Demand - charging), charging = max(-NG: OTH, 0) on
the same filled frame. QA as the loader applies it. Writes
caiso_proposal_effect.csv next to this file.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data import eia930
from market_sim.data.commitment_demand import qa_forecast_error

OUT = Path(__file__).parent


def stats(name: str, year: int, fc: np.ndarray, act: np.ndarray, ref: np.ndarray) -> dict:
    """uc_solve_log-style summary; top-100 hours ranked on ``ref`` (the metered Demand)."""
    err, valid = qa_forecast_error(fc, act)
    e = err[valid]
    top = np.argsort(ref)[::-1][:100]
    day_min = pd.Series(np.where(valid, err, np.nan)).groupby(np.arange(err.size) // 24).min()
    return dict(year=year, basis=name, qa_dropped=int((~valid).sum()), mean_mw=e.mean(),
                frac_below_0=(e < 0).mean(), p5=np.quantile(e, 0.05), p95=np.quantile(e, 0.95),
                top100_median_mw=np.median(err[top]), days_hour_below_m1gw=int((day_min < -1000).sum()))


def main() -> None:
    """One row per (year, basis)."""
    rows = []
    for y in range(2019, 2026):
        f = eia930._eia_hourly_frame_filled("CISO", y)
        df = f["Demand forecast"].to_numpy(dtype=float)
        dem = f["Demand"].to_numpy(dtype=float)
        chg = np.clip(-f["NG: OTH"].to_numpy(dtype=float), 0.0, None)
        chg = np.nan_to_num(chg, nan=0.0)
        rows.append(stats("EIA DF - Demand (current)", y, df, dem, dem))
        rows.append(stats("EIA DF - (Demand - charging) (proposed)", y, df, dem - chg, dem))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "caiso_proposal_effect.csv", index=False, float_format="%.4f")
    print(out.round(1).to_string())


if __name__ == "__main__":
    main()
