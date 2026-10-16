"""UC-DF-AUDIT §2.1: shape of the EIA-930 SWPP DF uplift over the MTLF D-1 00h vintage (zero LP).

For R1 years (2019, 2021, 2022) and R3 (2025 Jun-Sep): exact-match share at
clock offsets -3..+3 h, the within-day std and hour-of-day profile of DF - MTLF
on non-exact days, and corr(DF - actual, MTLF - actual). Prints only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.data import eia930
from market_sim.data.load_forecast_vintages import load_vintages

TZ = "America/Chicago"
H = pd.Timedelta(hours=1)


def d1_00h(year: int) -> pd.Series:
    """MTLF vintage issued 00:00 CPT D-1, per UTC hour end."""
    v = load_vintages("SPP", (year - 1, year), area="SPP")
    v = v[v.lead_hours >= 1]
    op = (v.interval_end_utc - H).dt.tz_convert(TZ).dt.normalize()
    iss = v.issue_time_utc.dt.tz_convert(TZ)
    v = v[((op - iss.dt.normalize()).dt.days == 1) & (iss.dt.hour == 0)]
    return (v.sort_values("issue_time_utc").drop_duplicates("interval_end_utc", keep="last")
            .set_index("interval_end_utc")["forecast_mw"])


def main() -> None:
    """Print the per-year diagnostics."""
    for y, months in ((2019, None), (2021, None), (2022, None), (2025, (6, 7, 8, 9))):
        f = eia930._eia_hourly_frame_filled("SWPP", y)
        e = pd.DataFrame({"df": f["Demand forecast"].astype(float).values, "act": f["Demand"].astype(float).values},
                         index=pd.to_datetime(f["UTC time"]).dt.tz_localize("UTC").astype("datetime64[ns, UTC]"))
        m = d1_00h(y)
        keep = (lambda idx: idx.tz_convert(TZ).month.isin(months)) if months else (lambda idx: np.ones(len(idx), bool))
        for off in range(-3, 4):
            s = m.copy()
            s.index = s.index + off * H
            j = e.join(s.rename("m"), how="inner").dropna()
            j = j[keep(j.index)]
            d = j.df - j.m
            print(y, f"offset {off:+d} h: median |DF-MTLF| {d.abs().median():.0f} MW, exact {(d.abs() < 0.5).mean():.3f}")
        j = e.join(m.rename("m"), how="inner").dropna()
        j = j[keep(j.index)]
        j["d"] = j.df - j.m
        loc = (j.index - H).tz_convert(TZ)
        p = j.assign(day=loc.date, hod=loc.hour).pivot_table(index="day", columns="hod", values="d")
        p = p[p.median(axis=1).abs() > 100]
        print(y, f"non-exact days {len(p)}; within-day std median {p.std(axis=1).median():.0f} MW; "
              f"corr(DF-act, MTLF-act) {np.corrcoef(j.df - j.act, j.m - j.act)[0, 1]:.2f}")
        print(y, "hour-of-day median DF-MTLF (MW):", p.median().round(0).astype(int).tolist())


if __name__ == "__main__":
    main()
