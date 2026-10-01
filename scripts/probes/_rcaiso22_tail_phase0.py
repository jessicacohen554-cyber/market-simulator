"""R-CAISO-22 phase 0 (ZERO LP): the C3c RT price tail on keeper 2026-09-30-caiso-r20-overnight.

For every measured RT tail hour (3-hub mean of TH_NP15 / TH_ZP26 / TH_SP15 RTM > $200, on the
model's fixed-PST hour-of-year clock, reusing `_rcaiso21_evening_phase0.measured`):

* the model's max-zone P1 price, and the NP15 - SP15 split (model and measured);
* the model-minus-EIA-930 supply delta for CISO demand, gas and net imports, and the model's
  storage net discharge (EIA-930 storage is not published on one schema across 2022-2025);
* the same deltas in a CONTROL set (same month x hod, non-tail days), so the event-specific
  part of each delta is separable from the year's standing offset;
* each tail hour classified as GAS-EVENT (measured implied HR on the model's own daily CA
  composite citygate print >= 10.5 and the day's print >= 1.5x the year median),
  NORTH-CONGESTION (measured NP15 - SP15 > $100), or TRANSIENT (the rest).

Inputs: the keeper's committed hourly sidecars (results/calibration/rcaiso20_A_span/hourly/),
data/raw/lmp-data/CAISO RTM, data/raw/eia-930 BALANCE, data/raw/gas-prices/caiso_citygate_daily.csv.
Writes results/calibration/_rcaiso22/tail_phase0.json (gitignored scratch).

Part B (``--stack``): rebuild the keeper's 2024 offer surface with no LP
(``scripts.lib.bundle_fleet.reconstruct_bundle_fleet``, the caiso-272 route) and read the CA gas
supply stack (in-state CC/CT/ST/oil, per-hour ``mc_base`` x ``pmax x availability``) at the
model's dispatched gas MW, and at +1 / +2.3 / +4 GW, in the Jan 13-16 event hours. It bounds what
removing the event-specific import excess (+2.3 GW, part A) could do to the price.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso22_tail_phase0.py [--stack]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import _rcaiso21_evening_phase0 as r21  # noqa: E402

BUNDLE = Path("results/calibration/rcaiso20_A_span/hourly")
OUT = Path("results/calibration/_rcaiso22/tail_phase0.json")
GAS = Path("data/raw/gas-prices/caiso_citygate_daily.csv")
THR = 200.0  # calibration_verdict.TAIL_THRESHOLD["CAISO"]
GAS_CLASSES = ["CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS"]


def eia930(y: int) -> pd.DataFrame:
    """CISO demand, gas and net import (MW) on the model's fixed-PST hour-of-year index."""
    parts = []
    for half in ("Jan_Jun", "Jul_Dec"):
        p = Path(f"data/raw/eia-930/EIA930_BALANCE_{y}_{half}.parquet")
        if p.exists():
            d = pd.read_parquet(p)
            parts.append(d[d["Balancing Authority"] == "CISO"])
    d = pd.concat(parts)
    t = pd.to_datetime(d["UTC Time at End of Hour"]) - pd.Timedelta(hours=1)
    h = ((t - pd.Timestamp(f"{y}-01-01 08:00")) / pd.Timedelta(hours=1)).astype(int)
    out = pd.DataFrame(
        {
            "dem": d["Demand (MW) (Adjusted)"].to_numpy(),
            "gas": d["Net Generation (MW) from Natural Gas (Adjusted)"].to_numpy(),
            "imp": -d["Total Interchange (MW) (Adjusted)"].to_numpy(),
        },
        index=h.to_numpy(),
    )
    out = out[~out.index.duplicated()]
    return out.reindex(np.arange(8760))


def model(y: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Model P1 zonal prices and system supply (demand, gas, import, storage net) per hour."""
    s = pd.read_parquet(BUNDLE / f"system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    price = s.pivot(index="hour", columns="zone", values="price").iloc[:8760]
    c = pd.read_parquet(BUNDLE / f"class_hourly_{y}.parquet")
    c = c[c["pass"] == "P1"].pivot(index="hour", columns="klass", values="mw")
    st = pd.read_parquet(BUNDLE / f"storage_{y}.parquet")
    st = st[st["pass"] == "P1"]
    stor = (st.discharge_mw - st.charge_mw).groupby(st.hour).sum()
    sup = pd.DataFrame(
        {
            "dem": s.groupby("hour").demand.sum(),
            "gas": c[[k for k in GAS_CLASSES if k in c]].sum(axis=1),
            "imp": c["import"],
            "stor": stor,
        }
    ).iloc[:8760]
    return price, sup


def gas_by_hour(y: int) -> np.ndarray:
    """CA composite citygate print applied to each hour (flow date = next print date's eve)."""
    g = pd.read_csv(GAS, parse_dates=["date"]).set_index("date").ca_composite_usd_mmbtu
    # trade date D prices flow D+1 .. next trade date (weekend/holiday package)
    flow = g.copy()
    flow.index = flow.index + pd.Timedelta(days=1)
    days = pd.date_range(f"{y}-01-01", f"{y}-12-31", freq="D")
    daily = flow.reindex(flow.index.union(days)).ffill().reindex(days).to_numpy()
    return np.repeat(daily, 24)[:8760]


def main() -> None:
    """Classify each measured RT tail hour and tabulate the model-vs-measured supply deltas."""
    res = {}
    for y in (2022, 2023, 2024, 2025):
        m = r21.measured(y, "rtm")
        hub = np.nanmean(np.vstack([m["NP15"], m["ZP26"], m["SP15_rest"]]), axis=0)
        price, sup = model(y)
        meas = eia930(y)
        gas = gas_by_hour(y)
        pmax = price.max(axis=1).to_numpy()
        ts = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), "h")
        mo, hod, day = ts.month.to_numpy(), ts.hour.to_numpy(), ts.dayofyear.to_numpy()
        tail = np.where(hub > THR)[0]
        med = np.nanmedian(gas)
        ihr = hub / gas
        spread = m["NP15"] - m["SP15_rest"]
        cls = np.where(
            spread[tail] > 100,
            "north_congestion",
            np.where(
                (ihr[tail] >= 10.5) & (gas[tail] >= 1.5 * med), "gas_event", "transient"
            ),
        )
        tail_days = set(day[tail])
        delta = (
            sup[["dem", "gas", "imp"]].to_numpy()
            - meas[["dem", "gas", "imp"]].to_numpy()
        )
        yr = {
            "n_tail": int(len(tail)),
            "model_hours_gt200": int((pmax > THR).sum()),
            "model_max": round(float(pmax.max()), 1),
            "gas_median": round(float(med), 2),
            "classes": {},
        }
        for k in ("gas_event", "north_congestion", "transient"):
            idx = tail[cls == k]
            if not len(idx):
                continue
            ctrl = np.array(
                [
                    h
                    for h in range(8760)
                    if day[h] not in tail_days
                    and (mo[h], hod[h]) in set(zip(mo[idx], hod[idx]))
                ]
            )
            dt = np.nanmean(delta[idx], axis=0)
            dc = np.nanmean(delta[ctrl], axis=0)
            yr["classes"][k] = {
                "hours": int(len(idx)),
                "dates": sorted({str(ts[h].date()) for h in idx}),
                "meas_mean": round(float(np.nanmean(hub[idx])), 1),
                "model_mean": round(float(np.mean(pmax[idx])), 1),
                "model_hours_gt200": int((pmax[idx] > THR).sum()),
                "gas_print_mean": round(float(np.mean(gas[idx])), 2),
                "implied_hr_meas": round(float(np.nanmean(ihr[idx])), 2),
                "implied_hr_model": round(float(np.mean(pmax[idx] / gas[idx])), 2),
                "np_sp_meas": round(float(np.nanmean(spread[idx])), 1),
                "np_sp_model": round(
                    float(
                        np.mean(
                            price["NP15"].to_numpy()[idx]
                            - price["SP15_rest"].to_numpy()[idx]
                        )
                    ),
                    1,
                ),
                "delta_tail_gw": dict(
                    zip(("dem", "gas", "imp"), np.round(dt / 1e3, 2).tolist())
                ),
                "delta_ctrl_gw": dict(
                    zip(("dem", "gas", "imp"), np.round(dc / 1e3, 2).tolist())
                ),
                "model_stor_gw_tail": round(
                    float(sup.stor.to_numpy()[idx].mean() / 1e3), 2
                ),
                "model_stor_gw_ctrl": round(
                    float(sup.stor.to_numpy()[ctrl].mean() / 1e3), 2
                ),
            }
        res[y] = yr
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    for y, yr in res.items():
        print(y, {k: v for k, v in yr.items() if k != "classes"})
        for k, v in yr["classes"].items():
            print(
                "  ", k, json.dumps({kk: vv for kk, vv in v.items() if kk != "dates"})
            )
            print("      dates", v["dates"][:12], "..." if len(v["dates"]) > 12 else "")


def stack_bound() -> None:
    """Part B: the CA gas offer stack at, and above, the model's dispatch in the Jan-2024 event."""
    repo = Path(__file__).resolve().parents[2]
    for q in (repo, repo / "src"):
        if str(q) not in sys.path:
            sys.path.insert(0, str(q))
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    bundle = BUNDLE.parent
    state, _ = reconstruct_bundle_fleet(
        bundle, 2024, required_flags=(), required_sequences=()
    )
    fa, fleet = state["fleet_arrays"], state["fleet"]
    mc = np.asarray(state["mc_base"], float)
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    klass = np.array(
        [
            str(getattr(g, "plant_group", "") or getattr(g, "fuel_type", ""))
            for g in fleet
        ]
    )
    zone = np.array([str(getattr(g, "zone", "")) for g in fleet])
    gmask = np.isin(klass, GAS_CLASSES + ["oil"]) & ~np.char.startswith(
        zone.astype(str), "WECC"
    )
    price, _ = model(2024)
    cb = pd.read_parquet(BUNDLE / "class_band_hourly_2024.parquet")
    cb = cb[(cb["pass"] == "P1") & cb.klass.isin(GAS_CLASSES)]
    disp = cb.groupby("hour").mw.sum()
    rows = []
    for d, hs in (
        (12, range(16, 24)),
        (14, range(16, 24)),
        (15, [*range(8), *range(16, 22)]),
    ):
        for hh in hs:
            h = d * 24 + hh
            o = np.argsort(mc[gmask, h])
            cm, ms = np.cumsum(cap[gmask, h][o]), mc[gmask, h][o]

            def at(q: float) -> float:
                return round(float(ms[min(np.searchsorted(cm, q), len(ms) - 1)]), 1)

            x = float(disp.loc[h])
            rows.append(
                {
                    "hour": f"01-{d + 1:02d} {hh:02d}",
                    "lambda": round(float(price.loc[h].max()), 1),
                    "gas_gw": round(x / 1e3, 2),
                    "stack": at(x),
                    "plus1": at(x + 1000),
                    "plus2_3": at(x + 2300),
                    "plus4": at(x + 4000),
                }
            )
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.with_name("stack_bound_2024.json").write_text(
        df.to_json(orient="records", indent=1)
    )
    print(df.to_string())


if __name__ == "__main__":
    if "--stack" in sys.argv:
        stack_bound()
    else:
        main()
