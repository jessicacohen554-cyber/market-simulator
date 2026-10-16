"""UC-DF-AUDIT task 2: EIA-930 SWPP day-ahead forecast vs SPP's own MTLF vintages (zero LP).

Reads the load-forecast-vintages SPP partitions (scripts/regenerate_clean.py
load-forecast-vintages) and the EIA-930 SWPP frame the commitment-demand loader
reads (eia930._eia_hourly_frame_filled). EIA "UTC time" is the hour END, the
same instant as SPP GMTIntervalEnd (checked in table A by the actuals).

Writes CSVs next to this file. Run from the repo root:
    .venv/bin/python docs/records/governance/uc-milp-2026-10/data/df_audit/spp_df_vs_mtlf.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import COMMITMENT_DF_DATA_ERROR_FRACTION
from market_sim.data import eia930
from market_sim.data.load_forecast_vintages import load_vintages, select_at_lead

OUT = Path(__file__).parent
YEARS = range(2019, 2026)
TZ = "America/Chicago"
#: First local operating days of the EIA-930 DF reporting regimes (table E).
REGIME_2 = "2023-09-02"
REGIME_3 = "2025-05-07"


def eia(year: int) -> pd.DataFrame:
    """EIA-930 SWPP model-year frame, keyed by UTC hour end."""
    f = eia930._eia_hourly_frame_filled("SWPP", year)
    return pd.DataFrame(
        {
            "end": pd.to_datetime(f["UTC time"]).dt.tz_localize("UTC").astype("datetime64[ns, UTC]"),
            "df": f["Demand forecast"].astype(float).to_numpy(),
            "eia_actual": f["Demand"].astype(float).to_numpy(),
        }
    )


def _one(rows: pd.DataFrame) -> pd.DataFrame:
    """One vintage per hour (a DST day can give a class two issue times; keep the later)."""
    return rows.sort_values("issue_time_utc").drop_duplicates("end", keep="last").set_index("end")


def main() -> None:
    """Tables A-E (FINDING §2)."""
    foot, which, sign, monthly, daily, vint, regimes = [], [], [], [], [], [], []
    for y in YEARS:
        e = eia(y)
        v = load_vintages("SPP", (y - 1, y), area="SPP")
        v = v[v["interval_end_utc"].isin(e["end"])]
        # A. footprint: SPP's settled actual (the last vintage reporting the
        # hour, lead -23 = 23 h after the hour ended) vs EIA-930 Demand, at
        # clock offsets -1/0/+1 h.
        act = (
            v[v["actual_mw"].notna() & (v["lead_hours"] <= -1)]
            .sort_values("issue_time_utc")
            .drop_duplicates("interval_end_utc", keep="last")
            .set_index("interval_end_utc")["actual_mw"]
        )
        for off in (-1, 0, 1):
            a = act.copy()
            a.index = a.index + pd.Timedelta(hours=off)
            j = e.set_index("end").join(a.rename("spp_actual"), how="inner").dropna()
            d = j["eia_actual"] - j["spp_actual"]
            qa = d.abs() <= COMMITMENT_DF_DATA_ERROR_FRACTION * j["spp_actual"]
            foot.append(
                dict(year=y, offset_h=off, n=len(j), mean_mw=d.mean(),
                     median_abs_mw=d.abs().median(), ratio=j.eia_actual.sum() / j.spp_actual.sum(),
                     exact_frac=(d.abs() < 0.5).mean(), corr=j.eia_actual.corr(j.spp_actual),
                     qa_dropped=int((~qa).sum()), corr_qa=j[qa].eia_actual.corr(j[qa].spp_actual))
            )
        # B. which vintage the DF tracks: vintage class = (days before the
        # local operating day, local issue hour).
        fw = v[v["lead_hours"] >= 1].copy()
        op_day = (fw["interval_end_utc"] - pd.Timedelta(hours=1)).dt.tz_convert(TZ).dt.normalize()
        iss = fw["issue_time_utc"].dt.tz_convert(TZ)
        fw["k_days"] = (op_day - iss.dt.normalize()).dt.days
        fw["issue_hour"] = iss.dt.hour
        j = fw.merge(e, left_on="interval_end_utc", right_on="end")
        j["d"] = j["df"] - j["forecast_mw"]
        j["ad"] = j["d"].abs()
        g = j[j["k_days"].between(0, 3)].groupby(["k_days", "issue_hour"])
        t = g.agg(n=("ad", "size"), median_abs_mw=("ad", "median"),
                  exact_frac=("ad", lambda s: (s < 0.5).mean())).reset_index()
        t.insert(0, "year", y)
        which.append(t)
        best = t[t.k_days >= 1].sort_values("median_abs_mw").iloc[0]  # full-day classes
        bk, bh = int(best.k_days), int(best.issue_hour)
        bj = _one(j[(j.k_days == bk) & (j.issue_hour == bh)])
        # C. sign of the error: DF vs EIA actual; best-matching MTLF vintage vs
        # EIA actual and vs SPP's own actual; DA-RUC-time vintage (D-1 13:00).
        ruc = _one(j[(j.k_days == 1) & (j.issue_hour == 13)])
        base = e.set_index("end").join(act.rename("spp_actual"))
        base["mtlf_best"] = bj["forecast_mw"]
        base["mtlf_d1_13"] = ruc["forecast_mw"]
        rows = {
            "DF - EIA actual": base.df - base.eia_actual,
            f"MTLF D-{bk} {bh:02d}h - EIA actual": base.mtlf_best - base.eia_actual,
            f"MTLF D-{bk} {bh:02d}h - SPP actual": base.mtlf_best - base.spp_actual,
            "MTLF D-1 13h - SPP actual": base.mtlf_d1_13 - base.spp_actual,
            f"DF - MTLF D-{bk} {bh:02d}h": base.df - base.mtlf_best,
        }
        for name, s in rows.items():
            s = s.dropna()
            sign.append(dict(year=y, series=name, n=len(s), mean_mw=s.mean(),
                             frac_below_0=(s < 0).mean(), p5=s.quantile(0.05), p95=s.quantile(0.95)))
        # F. SPP's own forecast error by vintage class (vs SPP and EIA actual),
        # the EIA DF beside it; QA as the commitment-demand loader applies it.
        classes = {
            "EIA-930 DF": base.df,
            "MTLF D-1 00h": _one(j[(j.k_days == 1) & (j.issue_hour == 0)])["forecast_mw"],
            "MTLF D-1 13h (DA-RUC)": base.mtlf_d1_13,
            "MTLF lead>=4h (ID-RUC)": select_at_lead(v, 4)["forecast_mw"],
            "MTLF lead>=1h": select_at_lead(v, 1)["forecast_mw"],
        }
        for name, fc in classes.items():
            for ref in ("eia_actual", "spp_actual"):
                jj = pd.concat([fc.rename("fc"), base[ref].rename("a")], axis=1, join="inner").dropna()
                err = jj.fc - jj.a
                ok = err.abs() <= COMMITMENT_DF_DATA_ERROR_FRACTION * jj.a
                err = err[ok]
                vint.append(dict(year=y, forecast=name, vs=ref, n=len(err), mean_mw=err.mean(),
                                 frac_below_0=(err < 0).mean(), mae_mw=err.abs().mean(),
                                 p5=err.quantile(0.05), p95=err.quantile(0.95)))
        # D. monthly: DF - EIA actual, best MTLF - SPP actual, DF - best MTLF.
        base["month"] = base.index.tz_convert(TZ).strftime("%Y-%m")
        m = base.groupby("month").apply(
            lambda b: pd.Series({
                "df_minus_eia": (b.df - b.eia_actual).mean(),
                "mtlf_best_minus_spp": (b.mtlf_best - b.spp_actual).mean(),
                "df_minus_mtlf_best_median_abs": (b.df - b.mtlf_best).abs().median(),
                "eia_minus_spp_actual": (b.eia_actual - b.spp_actual).mean(),
            }), include_groups=False)
        monthly.append(m.reset_index())
        # E. daily: which vintage class matches best each day (break dates).
        j["day"] = (j["end"] - pd.Timedelta(hours=1)).dt.tz_convert(TZ).dt.date
        dd = (j[j["k_days"].between(1, 2)].groupby(["day", "k_days", "issue_hour"])["ad"]
              .median().reset_index().sort_values(["day", "ad"]).drop_duplicates("day"))
        d00 = (j[(j.k_days == 1) & (j.issue_hour == 0)].groupby("day")["ad"]
               .agg(d1_00h_median_abs="median", d1_00h_exact=lambda a: (a < 0.5).mean()))
        daily.append(dd.set_index("day").join(d00).reset_index())
        # H. regimes (break dates from table E): share of days where the DF is
        # the D-1 00h vintage exactly, and the DF / MTLF ratio on the other days.
        q = j[(j.k_days == 1) & (j.issue_hour == 0)].sort_values("issue_time_utc").drop_duplicates("end", keep="last")
        q = q.assign(regime=np.select(
            [q["day"] < pd.Timestamp(REGIME_2).date(), q["day"] < pd.Timestamp(REGIME_3).date()],
            ["R1 (to 2023-09-01)", "R2 (2023-09-02 .. 2025-05-06)"], "R3 (from 2025-05-07)"))
        dmed = q.groupby("day")["d"].median()
        q["exact_day"] = q["day"].map(dmed.abs() < 0.5)
        for reg, r in q.groupby("regime"):
            off = r[~r["exact_day"]]
            regimes.append(dict(year=y, regime=reg, days=r["day"].nunique(),
                                exact_days=int(r.loc[r.exact_day, "day"].nunique()),
                                ratio_df_over_mtlf_other_days=(off["df"] / off["forecast_mw"]).median(),
                                mean_df_minus_mtlf_other_days=off["d"].mean()))
        print(y, f"best vintage D-{bk} {bh:02d}h", round(best.median_abs_mw, 1), round(best.exact_frac, 3))
    pd.DataFrame(foot).to_csv(OUT / "spp_A_footprint.csv", index=False, float_format="%.4f")
    pd.concat(which).to_csv(OUT / "spp_B_vintage_match.csv", index=False, float_format="%.4f")
    pd.DataFrame(sign).to_csv(OUT / "spp_C_error_sign.csv", index=False, float_format="%.4f")
    pd.concat(monthly).to_csv(OUT / "spp_D_monthly.csv", index=False, float_format="%.1f")
    pd.DataFrame(regimes).to_csv(OUT / "spp_H_regimes.csv", index=False, float_format="%.4f")
    pd.DataFrame(vint).to_csv(OUT / "spp_F_vintage_error.csv", index=False, float_format="%.4f")
    pd.concat(daily).to_csv(OUT / "spp_E_daily_best_vintage.csv", index=False, float_format="%.1f")


if __name__ == "__main__":
    main()
