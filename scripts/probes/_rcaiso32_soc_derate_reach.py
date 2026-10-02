"""R-CAISO-32 probe: reach of a quarterly SOC-range derate on the CAISO keeper.

Zero LP, report-only (handoff R-CAISO-32, link 14). Two parts, one JSON.

Part A -- SOC-range derate bound on the keeper's committed storage sidecar
(``results/calibration/<bundle>/hourly/storage_<year>.parquet``, P1,
``li_ion`` pool). For each day the pool's max SOC is compared with a
ceiling lowered by the DMM quarterly "share of charge range on outage"
(the Max-SOC leg) and a floor raised by the Min-SOC leg. Energy above the
ceiling or below the floor is counted as lost that day -- an upper bound,
because a re-solved LP would redistribute part of it within the day. The
lost energy is spread over HE17-21 as an MW equivalent and priced on the
R-CAISO-24 Part B gas-stack slope (lift per MW of h18 battery delta), which
is itself an over-statement (only gas responds). Years without a DMM series
(2022, 2025) borrow the 2024 quarters and are labelled so.

Part B -- the MW leg already in hand: battery resources in the committed
CNOG outage windows (``data/raw/caiso-dam-outages``), per-resource offline MW
capped at the resource Pmax, as a share of the RTM storage bidding fleet
(``data/raw/caiso-rtm-eoh-soc`` storage universe, daily sum of ``en_max_mw``).
Battery rows are selected by resource-id suffix (``_BT/_BX/_ES/_BE`` + digit)
or a storage/battery/BESS name, solar-only names excluded; the crosswalk the
runtime consumer reads carries no battery rows, so none of this reaches a
solve today.

Usage::

    python3 scripts/probes/_rcaiso32_soc_derate_reach.py \
        --dmm docs/records/caiso/r-caiso-32/dmm_soc_outage_digitized.json \
        --bundle results/calibration/rcaiso20_A_span \
        --out docs/records/caiso/r-caiso-32/soc_derate_reach.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

QUARTERS = ("Q1", "Q2", "Q3", "Q4")
#: R-CAISO-24 PRECOMMIT §0 Part B: price lift ($/MWh at SP15_rest RT h18) per
#: MW of h18 battery net-discharge delta, 2023/2024/2025. 2022 borrows 2023.
H18_SLOPE_PER_MW = {2022: 0.5 / 149, 2023: 0.5 / 149, 2024: 0.2 / 131, 2025: 1.5 / 766}
#: HE17-21: the evening window the lost energy is spread over (R-CAISO-24 §2).
EVENING_HOURS = 5.0
STORAGE_ID = re.compile(r"_(?:BT|BX|ES|BE)\d")
STORAGE_NAME = re.compile(r"storage|batter|bess", re.I)
SOLAR_ONLY = re.compile(r"solar(?!.*bess)", re.I)


def part_a(dmm: dict, bundle: Path, years: tuple[int, ...]) -> dict:
    """Daily SOC-ceiling/floor bind census and the price-reach bound per year."""
    series_years = sorted(int(y) for y in dmm)
    proxy = str(max(series_years))
    out = {}
    for year in years:
        key = str(year) if str(year) in dmm else proxy
        q = dmm[key]["quarters"]
        max_share = np.array(
            [q[k]["share_of_charge_range_pct"] / 100 for k in QUARTERS]
        )
        min_share = np.array(
            [
                q[k]["min_soc_outage_mwh"] / q[k]["implied_charge_range_mwh"]
                for k in QUARTERS
            ]
        )
        d = pd.read_parquet(bundle / "hourly" / f"storage_{year}.parquet")
        b = d[(d["pass"] == "P1") & (d["tech"] == "li_ion")].copy()
        b["day"] = b["hour"] // 24
        g = b.groupby("day")
        cap = g["energy_cap_mwh"].max().to_numpy()
        dmax = g["soc_mwh"].max().to_numpy()
        dmin = g["soc_mwh"].min().to_numpy()
        days = pd.date_range(f"{year}-01-01", periods=len(cap), freq="D")
        qi = days.quarter.to_numpy() - 1
        ceiling = (1.0 - max_share[qi]) * cap
        floor = min_share[qi] * cap
        lost = np.maximum(0.0, dmax - ceiling) + np.maximum(0.0, floor - dmin)
        bind = lost > 0
        mw_eq = lost / EVENING_HOURS
        lift = mw_eq * H18_SLOPE_PER_MW[year]
        util = dmax / cap
        out[str(year)] = {
            "dmm_series": "own" if key == str(year) else f"{key} quarters as proxy",
            "energy_cap_mwh": round(float(cap.max())),
            "daily_max_soc_over_cap_p50": round(float(np.median(util)), 3),
            "daily_max_soc_over_cap_p95": round(float(np.quantile(util, 0.95)), 3),
            "days_max_soc_ge_95pct": int((util >= 0.95).sum()),
            "days_min_soc_le_1pct": int((dmin / cap <= 0.01).sum()),
            "bind_days": int(bind.sum()),
            "lost_energy_gwh": round(float(lost.sum() / 1e3), 1),
            "lost_energy_pct_of_annual_discharge": round(
                float(100 * lost.sum() / b["discharge_mw"].sum()), 2
            ),
            "mw_equivalent_bind_day_mean": round(
                float(mw_eq[bind].mean()) if bind.any() else 0
            ),
            "mw_equivalent_max": round(float(mw_eq.max())),
            "h18_slope_usd_per_mwh_per_mw": round(H18_SLOPE_PER_MW[year], 5),
            "lift_bind_day_mean_usd_per_mwh": round(
                float(lift[bind].mean()) if bind.any() else 0, 2
            ),
            "lift_max_day_usd_per_mwh": round(float(lift.max()), 2),
            "lift_annual_mean_usd_per_mwh": round(float(lift.mean()), 3),
        }
    return out


def part_b(windows: Path, universe_dir: Path, years: tuple[int, ...]) -> dict:
    """Quarterly battery MW on CNOG outage/derate as a share of the RTM storage fleet."""
    df = pd.read_parquet(windows)
    is_batt = (
        df["resource_id"].str.contains(STORAGE_ID)
        | df["resource_name"].str.contains(STORAGE_NAME)
    ) & ~df["resource_name"].str.contains(SOLAR_ONLY)
    s = df[is_batt]
    idx = pd.date_range(f"{years[0]}-01-01", f"{years[-1]}-12-31 23:00", freq="h")
    offline = np.zeros(len(idx))
    for _, g in s.groupby("resource_id"):
        cur = np.zeros(len(idx))
        pmax = float(g["resource_pmax_mw"].max())
        for st, en, mw in zip(g["start"], g["end"], g["curtailment_mw"]):
            a, b = idx.searchsorted(st), idx.searchsorted(en)
            cur[a:b] += float(mw)
        offline += np.minimum(cur, pmax)
    off = pd.Series(offline, index=idx).resample("QS").mean()
    fleet = []
    for y in years:
        u = pd.read_parquet(universe_dir / f"caiso_rtm_storage_universe_{y}.parquet")
        fleet.append(u[u["is_storage_s1"]].groupby("trade_date")["en_max_mw"].sum())
    fleet = pd.concat(fleet)
    fleet.index = pd.to_datetime(fleet.index)
    fleet = fleet.resample("QS").mean()
    rows = {}
    for t in off.index:
        rows[f"{t.year}Q{t.quarter}"] = {
            "offline_mw_mean": round(float(off[t])),
            "rtm_storage_fleet_mw_mean": round(float(fleet.get(t, np.nan))),
            "share_pct": round(float(100 * off[t] / fleet.get(t, np.nan)), 1),
        }
    by_year = {
        str(y): round(
            float(
                np.mean(
                    [v["share_pct"] for k, v in rows.items() if k.startswith(str(y))]
                )
            ),
            1,
        )
        for y in years
    }
    return {
        "battery_resources": int(s["resource_id"].nunique()),
        "nature_of_work_rows": s["nature_of_work"].value_counts().head(6).to_dict(),
        "quarters": rows,
        "annual_mean_share_pct": by_year,
    }


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dmm", type=Path, required=True)
    ap.add_argument(
        "--bundle", type=Path, default=Path("results/calibration/rcaiso20_A_span")
    )
    ap.add_argument(
        "--windows",
        type=Path,
        default=Path("data/raw/caiso-dam-outages/caiso-dam-outage-windows.parquet"),
    )
    ap.add_argument("--universe", type=Path, default=Path("data/raw/caiso-rtm-eoh-soc"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    dmm = json.loads(args.dmm.read_text())
    result = {
        "part_a_soc_range_derate_bound": part_a(
            dmm, args.bundle, (2022, 2023, 2024, 2025)
        ),
        "part_b_cnog_battery_mw_outage": part_b(
            args.windows, args.universe, (2023, 2024, 2025)
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=1)[:4000])


if __name__ == "__main__":
    main()
