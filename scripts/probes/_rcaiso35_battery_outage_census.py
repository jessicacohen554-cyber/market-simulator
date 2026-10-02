"""R-CAISO-35 probe: battery-outage census and the rule-19 test vs the shape anchor.

Zero LP, report-only (handoff R-CAISO-35, link 17; tests pre-registered in
``docs/records/caiso/r-caiso-35/PRECOMMIT-r-caiso-35-battery-outage-census-2026-10-02.md``).
Re-run in R-CAISO-36 (link 18) after the crosswalk review and the selector fix
in ``build_caiso_resource_crosswalk.is_battery_resource``; the census
population follows that selector, and coverage is also split by
``match_method``.

Per hour of 2023-25 on the EIA-930 CISO row clock the envelope was derived on
(``scripts/derive_caiso_storage_shape.py``: first 8760 rows of each year),
battery MW offline in the CNOG episodes (per resource, overlapping curtailments
summed and capped at the resource Pmax) is divided by the EIA-860 monthly
battery fleet MW, giving ``o(t)`` and ``a(t) = 1 - o(t)``.

- T1 (primary): share of hours where the p95 envelope ``e_d[hod]`` exceeds
  ``a(t)`` (the envelope grants MW the outages removed), d in {chg, dis}.
  Sensitivities: RTM storage bidding fleet denominator; crosswalk-accepted
  population only.
- T2: share of hours where measured ``|NG: OTH|`` / fleet exceeds ``a(t)``.
- T3: within-quarter Spearman of daily mean ``o`` vs daily max measured
  discharge / fleet (descriptive).

Usage::

    python3 scripts/probes/_rcaiso35_battery_outage_census.py \
        --out docs/records/caiso/r-caiso-35/battery_outage_census.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from build_caiso_resource_crosswalk import is_battery_resource  # noqa: E402
from derive_caiso_storage_shape import (  # noqa: E402
    DAYS_IN_MONTH,
    EIA930,
    monthly_battery_fleet_mw,
)

YEARS = (2023, 2024, 2025)
WINDOWS = REPO / "data/raw/caiso-dam-outages/caiso-dam-outage-windows.parquet"
ENVELOPE = REPO / "data/raw/reference/caiso-storage-shape-envelope.csv"
XWALK = REPO / "data/raw/reference/caiso-storage-resource-eia-crosswalk.csv"
UNIVERSE = REPO / "data/raw/caiso-rtm-eoh-soc"
TZ = "America/Los_Angeles"
#: PRECOMMIT §4 bands on max over (year, direction) of B.
CARRIED_MAX, MARGINAL_MAX = 0.01, 0.05


def eia930_rows(year: int) -> pd.DataFrame:
    """The derive's 8760 rows of ``year``: hour-beginning UTC, local date, OTH."""
    d = pd.read_parquet(EIA930, columns=["UTC time", "Local date", "Hour", "NG: OTH"])
    d["Local date"] = pd.to_datetime(d["Local date"])
    d = d[d["Local date"].dt.year == year].sort_values(["Local date", "Hour"])
    d = d.iloc[:8760].reset_index(drop=True)
    d["hb_utc"] = pd.to_datetime(d["UTC time"]) - pd.Timedelta(hours=1)
    d["oth"] = np.nan_to_num(d["NG: OTH"].to_numpy(dtype=float))
    if len(d) < 8760:  # the derive zero-pads a short year; extend the clock alike
        n = 8760 - len(d)
        last = d.iloc[-1]
        pad = pd.DataFrame(
            {
                "hb_utc": last["hb_utc"] + pd.to_timedelta(np.arange(1, n + 1), "h"),
                "Local date": last["Local date"],
                "oth": 0.0,
            }
        )
        d = pd.concat([d, pad], ignore_index=True)
    return d


def offline_mw(win: pd.DataFrame, grid_utc: pd.DatetimeIndex) -> np.ndarray:
    """Hourly battery MW offline on ``grid_utc`` (hour-beginning, UTC)."""
    total = np.zeros(len(grid_utc))
    for _, g in win.groupby("resource_id"):
        cur = np.zeros(len(grid_utc))
        pmax = float(g["resource_pmax_mw"].max())
        for st, en, mw in zip(g["start_utc"], g["end_utc"], g["curtailment_mw"]):
            a, b = grid_utc.searchsorted(st), grid_utc.searchsorted(en)
            cur[a:b] += float(mw)
        total += np.minimum(cur, pmax)
    return total


def localize(ts: pd.Series) -> pd.Series:
    """Pacific prevailing naive stamps -> UTC (DST gaps shifted forward)."""
    return (
        pd.to_datetime(ts)
        .dt.tz_localize(TZ, ambiguous="NaT", nonexistent="shift_forward")
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
    )


def rtm_fleet(year: int, local_dates: pd.Series) -> np.ndarray:
    """Daily RTM storage bidding fleet MW (Σ en_max_mw, s1) mapped to rows."""
    u = pd.read_parquet(UNIVERSE / f"caiso_rtm_storage_universe_{year}.parquet")
    f = u[u["is_storage_s1"]].groupby("trade_date")["en_max_mw"].sum()
    f.index = pd.to_datetime(f.index)
    return local_dates.map(f).ffill().bfill().to_numpy(dtype=float)


def t1(e: np.ndarray, a: np.ndarray, fleet: np.ndarray) -> dict:
    """Share of hours (and MW-h) where the envelope exceeds the available share."""
    over = e > a
    return {
        "bind_share": round(float(over.mean()), 5),
        "bind_hours": int(over.sum()),
        "excess_mwh_share_of_envelope": round(
            float((np.clip(e - a, 0, None) * fleet).sum() / (e * fleet).sum()), 5
        ),
    }


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    win = pd.read_parquet(WINDOWS)
    win = win[
        [
            is_battery_resource(i, n)
            for i, n in zip(win["resource_id"], win["resource_name"])
        ]
    ].copy()
    win["start_utc"], win["end_utc"] = localize(win["start"]), localize(win["end"])
    win = win.dropna(subset=["start_utc", "end_utc"])
    xw = pd.read_csv(XWALK)
    accepted = set(xw.loc[xw["accepted"] == 1, "resource_id"])
    # R-CAISO-36: the name-token-only population (the pre-registered method)
    # beside the reviewed additions, so the coverage lift stays attributable.
    by_method = {
        m: set(g.loc[g["accepted"] == 1, "resource_id"])
        for m, g in xw.groupby("match_method")
    }
    env = pd.read_csv(ENVELOPE)
    month_of_row = np.repeat(np.arange(12), np.array(DAYS_IN_MONTH) * 24)[:8760]
    hod = np.arange(8760) % 24

    result: dict = {
        "population": {
            "census_resources": int(win["resource_id"].nunique()),
            "crosswalk_rows": int(len(xw)),
            "crosswalk_accepted": int(len(accepted)),
            "crosswalk_accepted_plants": int(
                xw.loc[xw["accepted"] == 1, "plant_code"].nunique()
            ),
            "crosswalk_accepted_by_method": {m: len(v) for m, v in by_method.items()},
        },
        "years": {},
    }
    for year in YEARS:
        rows = eia930_rows(year)
        grid = pd.DatetimeIndex(rows["hb_utc"])
        off_all = offline_mw(win, grid)
        off_acc = offline_mw(win[win["resource_id"].isin(accepted)], grid)
        f860 = monthly_battery_fleet_mw(year)[month_of_row]
        frtm = rtm_fleet(year, rows["Local date"])
        ey = env[env["year"] == year].sort_values("hod")
        e = {
            "chg": ey["chg_frac_p95"].to_numpy()[hod],
            "dis": ey["dis_frac_p95"].to_numpy()[hod],
        }
        a860 = 1 - off_all / f860
        artm = 1 - off_all / frtm
        aacc = 1 - off_acc / f860
        yr: dict = {
            "fleet_860_mw_mean": round(float(f860.mean())),
            "fleet_rtm_mw_mean": round(float(frtm.mean())),
            "offline_mw_mean": round(float(off_all.mean())),
            "offline_mw_p99": round(float(np.quantile(off_all, 0.99))),
            "o_860_mean": round(float((1 - a860).mean()), 4),
            "o_860_p99": round(float(np.quantile(1 - a860, 0.99)), 4),
            "o_860_max": round(float((1 - a860).max()), 4),
            "o_rtm_mean": round(float((1 - artm).mean()), 4),
            "coverage_accepted_offline_mwh_share": round(
                float(off_acc.sum() / off_all.sum()), 4
            ),
            "coverage_by_method_offline_mwh_share": {
                m: round(
                    float(offline_mw(win[win["resource_id"].isin(v)], grid).sum())
                    / float(off_all.sum()),
                    4,
                )
                for m, v in by_method.items()
            },
            "envelope_max": {d: round(float(v.max()), 4) for d, v in e.items()},
            "min_headroom_a_minus_e": {
                d: round(float((a860 - v).min()), 4) for d, v in e.items()
            },
            "T1_primary": {d: t1(v, a860, f860) for d, v in e.items()},
            "T1_sens_rtm_denominator": {d: t1(v, artm, frtm) for d, v in e.items()},
            "T1_sens_crosswalk_only": {d: t1(v, aacc, f860) for d, v in e.items()},
        }
        meas = {
            "chg": np.clip(-rows["oth"].to_numpy(), 0, None) / f860,
            "dis": np.clip(rows["oth"].to_numpy(), 0, None) / f860,
        }
        yr["T2_measured_over_available_share"] = {
            d: round(float((v > a860).mean()), 5) for d, v in meas.items()
        }
        day = (
            pd.DataFrame(
                {
                    "date": rows["Local date"].to_numpy(),
                    "o": 1 - a860,
                    "dis": meas["dis"],
                }
            )
            .groupby("date")
            .agg(o=("o", "mean"), dis=("dis", "max"))
        )
        day["q"] = pd.to_datetime(day.index).quarter
        rhos = {}
        for q, g in day.groupby("q"):
            rhos[f"Q{q}"] = round(float(g["o"].corr(g["dis"], method="spearman")), 3)
        yr["T3_spearman_daily_o_vs_peak_dis"] = rhos
        result["years"][str(year)] = yr

    def worst(key: str) -> float:
        return max(
            result["years"][str(y)][key][d]["bind_share"]
            for y in YEARS
            for d in ("chg", "dis")
        )

    def band(x: float) -> str:
        if x <= CARRIED_MAX:
            return "CARRIED"
        return "MARGINAL" if x <= MARGINAL_MAX else "NOT CARRIED"

    prim = worst("T1_primary")
    sens = {k: worst(k) for k in ("T1_sens_rtm_denominator", "T1_sens_crosswalk_only")}
    order = ["CARRIED", "MARGINAL", "NOT CARRIED"]
    reading = max([band(prim)] + [band(v) for v in sens.values()], key=order.index)
    t2_max = max(
        v
        for y in YEARS
        for v in result["years"][str(y)]["T2_measured_over_available_share"].values()
    )
    result["adjudication"] = {
        "T1_primary_max_bind_share": prim,
        "T1_primary_band": band(prim),
        "T1_sensitivity_max_bind_share": sens,
        "reading": reading,
        "T2_max_share": t2_max,
        "T2_caveat": t2_max > 0.01,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
