"""UC-DF-AUDIT task 4: zero-LP effect of the proposed SPP DA-basis repair (rule 14).

Current basis (commitment_demand.ba_forecast_error_mw): EIA-930 SWPP "Demand
forecast" - "Demand" on the model clock. Proposed: SPP's own MTLF, vintage
issued at or before 00:00 Central prevailing time of D-1 (the vintage EIA-930
carries whenever its DF is on SPP's basis), minus the same EIA "Demand". The
data-QA cut is the loader's (COMMITMENT_DF_DATA_ERROR_FRACTION). Also shown:
the DA-RUC-time vintage (at or before 13:00 CPT D-1, Protocols §4.3.2) as the
owner's alternative. Writes spp_proposal_effect.csv next to this file.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data import eia930
from market_sim.data.commitment_demand import qa_forecast_error
from market_sim.data.load_forecast_vintages import load_vintages

OUT = Path(__file__).parent
TZ = "America/Chicago"


def vintage_by_day_hour(v: pd.DataFrame, issue_hour: int) -> pd.Series:
    """Per hour, the latest vintage issued at or before ``issue_hour``:00 CPT of D-1."""
    start = v["interval_end_utc"] - pd.Timedelta(hours=1)
    day = start.dt.tz_convert(TZ).dt.normalize()
    cutoff = (day - pd.Timedelta(days=1) + pd.Timedelta(hours=issue_hour)).dt.tz_convert("UTC")
    # tz-aware normalize + offset is wall-clock; DST days shift by at most 1 h.
    ok = v["issue_time_utc"] <= cutoff
    return (
        v.loc[ok].sort_values(["interval_end_utc", "issue_time_utc"])
        .drop_duplicates("interval_end_utc", keep="last")
        .set_index("interval_end_utc")["forecast_mw"]
    )


def stats(name: str, year: int, fc: np.ndarray, act: np.ndarray) -> dict:
    """The uc_solve_log-style summary of a commitment increment."""
    err, valid = qa_forecast_error(fc, act)
    top = np.argsort(act)[::-1][:100]
    e = err[valid]
    return dict(year=year, basis=name, qa_dropped=int((~valid).sum()), mean_mw=e.mean(),
                frac_below_0=(e < 0).mean(), p5=np.quantile(e, 0.05), p95=np.quantile(e, 0.95),
                top100_median_mw=np.median(err[top]), mean_rel=(e / act[valid]).mean())


def main() -> None:
    """One row per (year, basis)."""
    rows = []
    for y in range(2019, 2026):
        f = eia930._eia_hourly_frame_filled("SWPP", y)
        end = pd.to_datetime(f["UTC time"]).dt.tz_localize("UTC").astype("datetime64[ns, UTC]")
        act = f["Demand"].to_numpy(dtype=float)
        v = load_vintages("SPP", (y - 1, y), area="SPP")
        v = v[v["lead_hours"] >= 1]
        rows.append(stats("EIA-930 DF (current)", y, f["Demand forecast"].to_numpy(dtype=float), act))
        for name, hh in (("MTLF D-1 00h (proposed)", 0), ("MTLF D-1 13h (DA-RUC alt.)", 13)):
            fc = vintage_by_day_hour(v, hh).reindex(end).to_numpy(dtype=float)
            rows.append(stats(name, y, fc, act))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "spp_proposal_effect.csv", index=False, float_format="%.4f")
    print(out.round(3).to_string())


if __name__ == "__main__":
    main()
