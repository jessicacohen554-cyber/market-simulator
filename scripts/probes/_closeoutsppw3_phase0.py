"""Zero-LP phase 0 of lane closeout-SPP-w3 on the SPP keeper's committed bundle.

Keeper `2026-10-03-closeout-spp-nuc-keeper` (bundle `closeout_spp_nuc_span`). Reads only the committed
hourly sidecars (`system_<y>`, `class_hourly_<y>`, `unit_marginal_<y>`), the committed benchmark parts
(`frontend/data/backcast/bench/SPP/<y>.json.gz`), EIA-930 SWPP by fuel and the measured inputs the two
candidate mechanisms read. No LP.

Sections (all written to results/phase0/spp/_closeoutsppw3_phase0.json):
  A  oversupply-hour fleet vs EIA-930 and model wind vs the bench (context for the failing rows)
  B  `wind_ptc_vintage_offers` reach: every zone-hour the keeper clears at the flat wind floor
     (-ira_ptc_wind = -26.000) re-priced at the measured offer -PTC_statutory(y) x eligible_share[z, m]
     (policy.ira.wind_ptc_vintage_dispatch_offer's own array) -- exact while wind stays marginal there
  C  `hydro_dispatch_envelope` reach: model hydro above the measured month x hod p95 ceiling is moved,
     month by month, into the highest-priced hours with envelope room (the budget LP's water-value rule);
     thermal re-dispatch priced by a stack walk on the hour's own unit_marginal offers (approximation)
  D  B + C on the scorer's own basis (legacy equal-hour actual for 2019-22, load-weighted for 2023-25)
  E  the scorer basis: SPP 2019-22 are the only ISO-years in the repo scored on the LEGACY equal-hour
     basis; what derive_actual_lmp._lw_fields (the v2.4 retrofit, unchanged) yields for them
"""

from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
BUNDLE = REPO / "results/calibration/closeout_spp_nuc_span/hourly"
ZONES = ["SPP-North", "SPP-South"]
WIND_FLOOR = -26.0
OUT = REPO / "results/phase0/spp/_closeoutsppw3_phase0.json"


def model_frame(year: int) -> pd.DataFrame:
    """Zone-hour P1 price/demand with calendar month."""
    s = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"][["zone", "hour", "price", "demand"]].copy()
    s["zone"] = s["zone"].astype(str)
    s["month"] = (
        pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(s["hour"], unit="h")
    ).dt.month
    return s.reset_index(drop=True)


def bench(year: int) -> dict:
    """Committed benchmark avgLMP part."""
    p = REPO / f"frontend/data/backcast/bench/SPP/{year}.json.gz"
    return json.load(gzip.open(p))["bench"]


def scorer_actual(year: int) -> tuple[float, list[float], str]:
    """The actual the scorer gates on (its own basis ladder)."""
    a = bench(year)["avgLMP"]
    if a.get("rt_lw") is not None:
        return a["rt_lw"], a["rt_lw_mon"], "rt_lw"
    return a["rt"], a["rt_mon"], "rt (LEGACY equal-hour)"


def lw(df: pd.DataFrame, col: str) -> float:
    """Demand-weighted mean."""
    return float((df[col] * df["demand"]).sum() / df["demand"].sum())


def c3(df: pd.DataFrame, col: str, a: float, a_mon: list[float]) -> tuple[float, float]:
    """(C3a %, C3b NRMSE) of a model price column vs the scorer actual."""
    m = lw(df, col)
    mon = df.groupby("month").apply(lambda b: lw(b, col)).to_numpy()
    am = np.asarray(a_mon, dtype=float)
    return 100 * (m / a - 1), math.sqrt(float(((mon - am) ** 2).mean())) / float(
        am.mean()
    )


def section_a(year: int) -> dict:
    """Oversupply-hour fleet (model vs EIA-930) and wind energy vs the bench."""
    e = pd.read_parquet(REPO / "data/raw/SWPP_fueltype.parquet").pivot_table(
        index="period", columns="fueltype", values="value_mwh"
    )
    ch = pd.read_parquet(BUNDLE / f"class_hourly_{year}.parquet")
    ch = (
        ch[ch["pass"] == "P1"]
        .pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .fillna(0)
    )
    # model hour 0 = 07:00 UTC on EIA-930's period stamp (lag that maximises wind r, 0.992)
    idx = pd.date_range(f"{year}-01-01 07:00", periods=len(ch), freq="h", tz="UTC")
    act = e.reindex(idx)
    act.index = range(len(ch))
    s = model_frame(year)
    z = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    rt = z[z.year == year].set_index("hour")["rt"].reindex(range(len(ch)))
    gas_m = ch[[c for c in ch.columns if c[:2] in ("CC", "CT", "ST")]].sum(axis=1)
    coal_m = ch[[c for c in ch.columns if c.startswith("COAL")]].sum(axis=1)
    sysp = s.groupby("hour").apply(lambda b: lw(b, "price"))
    neg = rt <= 0
    b = bench(year)
    return {
        "rt_neg_hours": int(neg.sum()),
        "in_rt_neg_hours_MW": {
            "model_price": round(float(sysp[neg].mean()), 2),
            "wind_model": round(float(ch["wind"][neg].mean())),
            "wind_930": round(float(act["WND"][neg].mean())),
            "gas_model": round(float(gas_m[neg].mean())),
            "gas_930": round(float(act["NG"][neg].mean())),
            "coal_model": round(float(coal_m[neg].mean())),
            "coal_930": round(float(act["COL"][neg].mean())),
        },
        "wind_TWh_model": round(float(ch["wind"].sum()) / 1e6, 2),
        "wind_TWh_bench": b["classFull"].get("wind"),
        "hours_at_wind_floor_share": round(
            float(np.isclose(s["price"], WIND_FLOOR, atol=0.01).mean()), 4
        ),
    }


def ptc_delta(year: int, s: pd.DataFrame) -> tuple[np.ndarray, dict]:
    """Section B: exact re-price of the wind-floor zone-hours at the vintage-scoped offer."""
    from market_sim.config.constants import WIND_PTC_STATUTORY_USD_PER_MWH
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.renewables import wind_ptc_eligible_monthly_share

    share = wind_ptc_eligible_monthly_share("SPP", ZONES, year)
    ptc = WIND_PTC_STATUTORY_USD_PER_MWH.get(year, ScenarioConfig().ira_ptc_wind)
    zi = s["zone"].map({z: i for i, z in enumerate(ZONES)}).to_numpy()
    offer = -ptc * share[zi, s["month"].to_numpy() - 1]
    at = np.isclose(s["price"].to_numpy(), WIND_FLOOR, atol=0.01)
    d = np.where(at, offer - s["price"].to_numpy(), 0.0)
    return d, {
        "ptc_statutory": ptc,
        "eligible_share_mean": {
            z: round(float(share[i].mean()), 3) for i, z in enumerate(ZONES)
        },
        "zone_hours_at_floor": int(at.sum()),
        "mean_new_offer_at_floor": round(float(offer[at].mean()), 2)
        if at.any()
        else None,
    }


def hydro_delta(year: int, s: pd.DataFrame) -> tuple[np.ndarray, dict]:
    """Section C: stack-walk estimate of the measured hydro envelope (system price delta per hour)."""
    from market_sim.data.eia_loader import measured_hydro_hourly_envelope

    env = measured_hydro_hourly_envelope("SPP", year, 8760)
    um = pd.read_parquet(
        BUNDLE / f"unit_marginal_{year}.parquet",
        columns=["fuel", "hour", "mw", "cap_mw", "mc"],
    )
    fuel = um["fuel"].astype(str)
    hyd = (
        um[fuel == "hydro"]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(8760), fill_value=0)
        .to_numpy()
    )
    th = um[~fuel.isin(["hydro", "wind", "solar", "nuclear"])][
        ["hour", "mw", "cap_mw", "mc"]
    ].to_numpy()
    th = th[np.argsort(th[:, 0], kind="stable")]
    bnd = np.searchsorted(th[:, 0], np.arange(8761))
    sysp = s.groupby("hour").apply(lambda b: lw(b, "price")).to_numpy()
    month = (
        pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(8760), unit="h")
    ).month.to_numpy()
    exc = np.clip(hyd - env, 0, None)
    room = np.clip(env - hyd, 0, None)
    dh = -exc.copy()
    for m in range(1, 13):
        e_m = exc[month == m].sum()
        idx = np.where(month == m)[0]
        for t in idx[np.argsort(-sysp[idx])]:
            if e_m <= 0:
                break
            if exc[t] > 0:
                continue
            a = min(room[t], e_m)
            dh[t] += a
            e_m -= a
    newp = sysp.copy()
    for t in np.where(np.abs(dh) > 1)[0]:
        u = th[bnd[t] : bnd[t + 1]]
        need = -dh[t]
        if need > 0:
            c = u[(u[:, 2] - u[:, 1] > 0.5) & (u[:, 3] >= sysp[t] - 1e-6)]
            o = np.argsort(c[:, 3])
            k = np.searchsorted(np.cumsum((c[:, 2] - c[:, 1])[o]), need)
            if len(o):
                newp[t] = max(c[o][min(k, len(o) - 1), 3], sysp[t])
        else:
            c = u[(u[:, 1] > 0.5) & (u[:, 3] <= sysp[t] + 1e-6)]
            o = np.argsort(-c[:, 3])
            k = np.searchsorted(np.cumsum(c[o][:, 1]), -need)
            if len(o):
                newp[t] = min(c[o][min(k, len(o) - 1), 3], sysp[t])
    d_sys = newp - sysp
    return d_sys[s["hour"].to_numpy()], {
        "model_hydro_above_p95_TWh": round(float(exc.sum()) / 1e6, 2),
        "hours_capped": int((exc > 1).sum()),
        "mean_dP_capped_hours": round(float(d_sys[exc > 1].mean()), 2),
        "mean_dP_receiving_hours": round(float(d_sys[dh > 1].mean()), 2),
    }


def section_e(year: int, s: pd.DataFrame) -> dict | None:
    """Scorer basis: the v2.4 lw retrofit for a legacy-scored year (unchanged derive code)."""
    a = bench(year)["avgLMP"]
    if a.get("rt_lw") is not None:
        return None
    import derive_actual_lmp as dal

    f = dal._lw_fields("SPP", year)
    if not f:
        return None
    leg = c3(s, "price", a["rt"], a["rt_mon"])
    new = c3(s, "price", f["rt_lw"], f["rt_lw_mon"])
    return {
        "legacy_rt": a["rt"],
        "rt_lw": f["rt_lw"],
        "C3a_legacy_pct": round(leg[0], 1),
        "C3a_lw_pct": round(new[0], 1),
        "C3b_legacy": round(leg[1], 3),
        "C3b_lw": round(new[1], 3),
    }


def main() -> None:
    """Run sections A-E for 2019-2025."""
    rec: dict = {}
    for year in range(2019, 2026):
        s = model_frame(year)
        a, a_mon, basis = scorer_actual(year)
        d_ptc, b_info = ptc_delta(year, s)
        d_hyd, c_info = hydro_delta(year, s)
        s["p_ptc"] = s["price"] + d_ptc
        s["p_hyd"] = s["price"] + d_hyd
        s["p_both"] = s["price"] + d_ptc + d_hyd
        r = {
            "scorer_basis": basis,
            "A": section_a(year),
            "B": b_info,
            "C": c_info,
            "D": {},
        }
        for col in ("price", "p_ptc", "p_hyd", "p_both"):
            ca, cb = c3(s, col, a, a_mon)
            r["D"][col] = {"C3a_pct": round(ca, 2), "C3b": round(cb, 4)}
        r["E"] = section_e(year, s)
        rec[year] = r
        print(year, json.dumps({k: r[k] for k in ("B", "C", "D", "E")}), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
