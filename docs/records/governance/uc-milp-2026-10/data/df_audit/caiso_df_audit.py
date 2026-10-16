"""UC-DF-AUDIT task 3: EIA-930 CISO DF vs demand, against CAISO's own OASIS series (zero LP).

Inputs:
  * data/raw/eia-930-hourly/CISO hourly.parquet (the frame the demand and
    commitment-demand loaders read); "UTC time" is the hour end. NG: OTH is
    CAISO's battery net output (negative = charging), see table G.
  * CAISO OASIS SLD_FCST, TAC_AREA_NAME "CA ISO-TAC", market_run_id DAM
    (SYS_FCST_DA_MW) and ACTUAL (SYS_FCST_ACT_MW), fetched in 28-day UTC
    windows; argv[1] is the directory of the OASIS zips. Re-fetch:
    https://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&market_run_id=<DAM|ACTUAL>
      &startdatetime=<YYYYMMDD>T08:00-0000&enddatetime=<YYYYMMDD>T08:00-0000&version=1&resultformat=6
    The hourly CA ISO-TAC extract is written to caiso_oasis_ca_iso_tac.csv.gz
    so the tables reproduce without the fetch.

Writes caiso_G_*.csv next to this file.
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent
TAC = "CA ISO-TAC"


def oasis(zdir: Path) -> pd.DataFrame:
    """Hourly CA ISO-TAC DAM forecast and actual, indexed by UTC hour end."""
    frames = []
    for p in sorted(Path(zdir).glob("*.zip")):
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if n.endswith(".csv"):
                    d = pd.read_csv(io.BytesIO(z.read(n)))
                    frames.append(d[d["TAC_AREA_NAME"] == TAC])
    d = pd.concat(frames, ignore_index=True)
    d["end"] = pd.to_datetime(d["INTERVALENDTIME_GMT"], utc=True)
    d = d.drop_duplicates(["end", "XML_DATA_ITEM"], keep="last")
    w = d.pivot(index="end", columns="XML_DATA_ITEM", values="MW")
    return w.rename(columns={"SYS_FCST_DA_MW": "oasis_dam", "SYS_FCST_ACT_MW": "oasis_actual"})


def eia() -> pd.DataFrame:
    """EIA-930 CISO DF, Demand and battery charging, indexed by UTC hour end."""
    r = pd.read_parquet(Path("data/raw/eia-930-hourly/CISO hourly.parquet"))
    out = pd.DataFrame(
        {
            "eia_df": r["Demand forecast"].astype(float).to_numpy(),
            "eia_demand": r["Demand"].astype(float).to_numpy(),
            "charge": (-r["NG: OTH"].astype(float)).clip(lower=0).fillna(0.0).to_numpy(),
            "local_date": r["Local date"].to_numpy(),
            "he": r["Hour"].to_numpy(),
        },
        index=pd.to_datetime(r["UTC time"]).dt.tz_localize("UTC"),
    )
    return out


def err_stats(e: pd.Series, day: pd.Series) -> dict:
    """Mean, tails and the count of days with an hour below -1 GW."""
    e = e.dropna()
    return dict(n=len(e), mean_mw=e.mean(), p5=e.quantile(0.05), p50=e.median(), p95=e.quantile(0.95),
                days_hour_below_m1gw=int((e.groupby(day.reindex(e.index)).min() < -1000).sum()))


def main(zdir: str | None) -> None:
    """Tables G1 (basis), G2 (error under each basis), G3 (charging regression)."""
    e = eia()
    if zdir:
        o = oasis(Path(zdir))
        o.to_csv(OUT / "caiso_oasis_ca_iso_tac.csv.gz", float_format="%.2f")
    else:
        o = pd.read_csv(OUT / "caiso_oasis_ca_iso_tac.csv.gz", index_col=0, parse_dates=[0])
    j = e.join(o, how="inner")
    j["year"] = pd.DatetimeIndex(j["local_date"]).year
    basis, errs, reg = [], [], []
    for y, q in j.groupby("year"):
        if y < 2019 or y > 2025:
            continue
        # G1. Is EIA DF CAISO's DAM forecast? Is EIA Demand CAISO's actual,
        # or CAISO's actual plus battery charging?
        for a, b in (("eia_df", "oasis_dam"), ("eia_demand", "oasis_actual")):
            d = (q[a] - q[b]).dropna()
            basis.append(dict(year=y, pair=f"{a} - {b}", n=len(d), mean_mw=d.mean(),
                              median_abs_mw=d.abs().median(), exact_frac=(d.abs() < 1).mean()))
        d = (q["eia_demand"] - q["charge"] - q["oasis_actual"]).dropna()
        basis.append(dict(year=y, pair="eia_demand - charge - oasis_actual", n=len(d), mean_mw=d.mean(),
                          median_abs_mw=d.abs().median(), exact_frac=(d.abs() < 1).mean()))
        day = q["local_date"]
        for name, s in {
            "EIA DF - EIA Demand (model DA basis today)": q.eia_df - q.eia_demand,
            "EIA DF - (EIA Demand - charging)": q.eia_df - (q.eia_demand - q.charge),
            "OASIS DAM - OASIS actual (CAISO's own)": q.oasis_dam - q.oasis_actual,
        }.items():
            errs.append(dict(year=y, series=name, **err_stats(s, day)))
        # G3. err = a + b*charge + c*discharge (discharge omitted: see FINDING).
        z = q.dropna(subset=["eia_df", "eia_demand", "oasis_actual"])
        X = np.c_[np.ones(len(z)), z["charge"]]
        for name, tgt in (("EIA Demand - OASIS actual", z.eia_demand - z.oasis_actual),
                          ("EIA DF - EIA Demand", z.eia_df - z.eia_demand)):
            c = np.linalg.lstsq(X, tgt, rcond=None)[0]
            reg.append(dict(year=y, target=name, intercept_mw=c[0], charge_coef=c[1],
                            charge_mean_mw=z["charge"].mean(), charge_max_mw=z["charge"].max()))
    for nm, rows in (("G1_basis", basis), ("G2_error", errs), ("G3_charging_regression", reg)):
        df = pd.DataFrame(rows)
        df.to_csv(OUT / f"caiso_{nm}.csv", index=False, float_format="%.4f")
        print(df.round(3).to_string())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
