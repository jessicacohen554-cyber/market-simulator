"""NWPP-NEXT-18 phase 0 (zero LP): does NWPP hydro have too much within-month freedom?

Reads keeper #20's per-year shard legs (``results/calibration/nwppnext16c_<Y>``,
extracted with ``git archive <sha> results/calibration/nwppnext16c_<Y>``; SHAs in
``docs/records/nwpp/HANDOFF-nwppnext18-2026-10-01.md``) plus committed raw data
(CROHMS hourly project power, EIA-930 NG:WAT envelope, WEIM hourly ELAP, CAISO
hourly LMP). Prints every table of
``docs/records/nwpp/FINDING-nwppnext18-hydro-within-month-phase0-2026-10-01.md``.

Usage: python scripts/probes/_nwppnext18_hydro_freedom_phase0.py LEG_ROOT
       (LEG_ROOT holds results/calibration/nwppnext16c_<Y>/ for 2022-2025)
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

YEARS = (2022, 2023, 2024, 2025)
# CROHMS station -> EIA plant id (data/raw/nwpp-hydro/nwpp_hydro_chain.csv).
STATIONS = {
    "GCL": 6163, "CHJ": 3921, "WEL": 3886, "RRH": 3883, "RIS": 6200, "WAN": 3888,
    "PRD": 3887, "MCN": 3084, "JDA": 3082, "TDA": 3895, "BON": 3075, "DWR": 840,
    "LWG": 6175, "LGS": 3926, "LMN": 3927, "IHR": 3925,
}
RAW = Path("data/raw")


def _leg(root: Path, year: int) -> Path:
    """Return the leg directory for one year."""
    return root / f"results/calibration/nwppnext16c_{year}"


def _hydro(root: Path, year: int) -> pd.DataFrame:
    """Return the leg's hydro unit-hours."""
    u = pd.read_parquet(
        _leg(root, year) / f"hourly/unit_hourly_{year}.parquet",
        columns=["plant_code", "fuel", "zone", "hour", "mw", "cap_mw"],
    )
    return u[u.fuel == "hydro"].copy()


def interior_census(root: Path, year: int) -> None:
    """Section 1: which hydro plants sit off their monthly bounds (price-setting)."""
    h = _hydro(root, year)
    h = h[h.zone != "NWPP-SNV"]
    h["m"] = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(h.hour, "h")).dt.month
    g = h.groupby(["plant_code", "m"]).mw
    lo, hi = g.transform("min"), g.transform("max")
    tol = 0.01 * h.cap_mw.clip(lower=1)
    h["interior"] = (h.mw > lo + tol) & (h.mw < hi - tol)
    chain = pd.read_csv(RAW / "nwpp-hydro/nwpp_hydro_chain.csv")
    h["chain"] = h.plant_code.isin(chain.plant_id)
    per = (
        h[h.interior]
        .groupby(["plant_code", "chain"])
        .agg(hours=("hour", "nunique"), cap=("cap_mw", "first"))
        .reset_index()
    )
    per["hour_mw"] = per.hours * per.cap
    share = per.groupby("chain").hour_mw.sum() / per.hour_mw.sum()
    print(f"\n## 1. Interior hydro hour-MW, north zones, {year}: chain share {share.get(True, 0):.3f}")
    top = per.sort_values("hour_mw", ascending=False).head(10)
    top = top.merge(chain[["plant_id", "plant_name"]], left_on="plant_code", right_on="plant_id")
    print(top[["plant_code", "plant_name", "cap", "hours"]].round(0).to_string(index=False))


def _crohms() -> pd.DataFrame:
    """Return CROHMS hourly project power (catalog clock: PST, no DST)."""
    c = pd.read_parquet(RAW / "nwpp-hydro/crohms/nwpp_crohms_hourly.parquet")
    c = c[c.series.str.startswith("Power.Total")].copy()
    c["ts"] = pd.to_datetime(c.ts)
    c["plant_code"] = c.station.map(STATIONS)
    return c


def daily_and_hourly_freedom(root: Path) -> None:
    """Sections 2-3: model vs CROHMS between-day and within-day variability."""
    c = _crohms()
    rows = []
    for y in YEARS:
        m = c[c.ts.dt.year == y].copy()
        m["hour"] = ((m.ts - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h")).astype(int)
        m = m[m.hour < 8760][["plant_code", "hour", "value"]].rename(columns={"value": "meas"})
        u = _hydro(root, y)
        u = u[u.plant_code.isin(STATIONS.values())].groupby(["plant_code", "hour"]).mw.sum().reset_index()
        j = m.merge(u, on=["plant_code", "hour"])
        j["day"] = j.hour // 24
        j["m"] = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(j.day, "D")).dt.month
        for name, sub in (("chain16", j), ("GCL", j[j.plant_code == 6163])):
            d = sub.groupby(["day", "m"])[["meas", "mw"]].sum().reset_index()
            sd_d = d.groupby("m")[["meas", "mw"]].std().mean()
            t = sub.groupby("hour")[["meas", "mw"]].sum()
            sd_h = t.groupby(t.index // 24)[["meas", "mw"]].std().mean()
            rows.append(
                dict(year=y, set=name,
                     between_day_meas_GWh=sd_d.meas / 1e3, between_day_model_GWh=sd_d.mw / 1e3,
                     between_ratio=sd_d.mw / sd_d.meas,
                     within_day_meas_MW=sd_h.meas, within_day_model_MW=sd_h.mw,
                     within_ratio=sd_h.mw / sd_h.meas)
            )
    print("\n## 2-3. Between-day (daily energy SD within month) and within-day (hourly SD) freedom")
    print(pd.DataFrame(rows).round(2).to_string(index=False))


def envelope_binding(root: Path) -> None:
    """Section 4: fleet envelope binding share and the price it lifts."""
    from market_sim.data.eia_loader import measured_hydro_hourly_envelope

    print("\n## 4. Fleet hydro envelope (hydro_dispatch_envelope) binding")
    for y in YEARS:
        env = measured_hydro_hourly_envelope("NWPP", y, 8760)
        tot = _hydro(root, y).groupby("hour").mw.sum().reindex(range(8760)).values
        s = pd.read_parquet(_leg(root, y) / "system.parquet")
        p = s[s.zone == "NWPP-NW"].set_index("hour").price.reindex(range(8760)).values
        b = tot >= env * 0.999
        top = p >= np.quantile(p, 0.9)
        lift = p[b].mean() - p[~b].mean()
        print(f"{y}: binding {b.mean():.1%} of hours, {b[top].mean():.1%} of top-decile price hours; "
              f"mean price binding minus free {lift:+.1f} $/MWh")
        if y == 2023:
            mth = (pd.Timestamp("2023-01-01") + pd.to_timedelta(np.arange(8760), "h")).month
            d = pd.DataFrame(dict(m=mth, p=p, b=b)).groupby(["m", "b"]).p.mean().unstack().round(1)
            print(d.rename(columns={False: "free", True: "binding"}).T.to_string())


def neighbour_comovement() -> None:
    """Section 5: measured NW WEIM prices vs CAISO, within-day and between-day."""
    c = pd.read_parquet(RAW / "_validation-source/actual_lmp_hourly_CAISO.parquet")
    w = pd.read_parquet(RAW / "nwpp-weim/weim_hourly_by_ba.parquet")
    print("\n## 5. Measured NW price co-movement with CAISO RT (r of daily-demeaned hours / of daily means)")
    for y in (2023, 2024, 2025):
        cc = c[c.year == y].set_index("hour").rt
        for ba in ("BPAT", "PACE", "IPCO"):
            b = w[(w.year == y) & (w.baa == ba)].set_index("hour").lmp
            j = pd.concat([b.rename("ba"), cc.rename("caiso")], axis=1, sort=True).dropna()
            j["day"] = j.index // 24
            dm = j.groupby("day")[["ba", "caiso"]].transform(lambda x: x - x.mean())
            dd = j.groupby("day")[["ba", "caiso"]].mean()
            print(f"{y} {ba}: within-day r {dm.ba.corr(dm.caiso):.2f}, between-day r {dd.ba.corr(dd.caiso):.2f}")


def main() -> None:
    """Run every section."""
    root = Path(sys.argv[1])
    for y in (2023, 2025):
        interior_census(root, y)
    daily_and_hourly_freedom(root)
    envelope_binding(root)
    neighbour_comovement()


if __name__ == "__main__":
    main()
