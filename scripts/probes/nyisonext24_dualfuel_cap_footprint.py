"""NYISO-NEXT-24 phase 0 (ZERO LP): dual-fuel parity-cap footprint on the FLOW-DATED gas series vs measured CAMPD oil burn and the DA-implied marginal fuel.

Fleet-only rebuild of the keeper recipe (``nyiso242_tail_reachability.fleet_state``) with
``nyiso_gas_flow_date=True`` (the NEXT-23 arm) and ``dual_fuel_switching=False`` so
``fuel_prices`` is the final delivered gas BEFORE the min(gas, oil) cap. The cap-binding
cells are capable gas generator-hours with gas > oil (the same test as
``dual_fuel.dual_fuel_switch_mask``). Each binding generator-day is joined to the plant-day
measured oil heat share from ``derive_measured_oil_burn_days.py --iso NYISO`` (absent = 0).

The DA-implied fuel on a day is ``(NYC daily DA - VOM) / HR`` of the MW-weighted capped
NYC units — a diagnostic of which fuel the clearing price is consistent with, never a
target (rule 13).

Usage: uv run python scripts/probes/nyisonext24_dualfuel_cap_footprint.py --oil-burn <csv> --out <json>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet"


def year_state(year: int) -> dict:
    """Fleet-only rebuild with the flow-date arm on and the parity cap off."""
    os.environ["NYISO_KEEPER_BUNDLE"] = str(
        REPO / "results/calibration" / ("nyisonext21_2021" if year == 2021 else "nyisonext21_span")
    )
    import importlib

    import scripts.probes.nyiso242_tail_reachability as t

    t = importlib.reload(t)
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((t.BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(t.BUNDLE, year))
    prb = dict(kw.get("prb_overrides") or {})
    prb.update({"nyiso_gas_flow_date": True, "dual_fuel_switching": False})
    kw["prb_overrides"] = prb
    return run_year(year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)


def footprint(year: int, burn: pd.DataFrame) -> dict:
    """Cap-binding generator-day census for one year."""
    from market_sim.data.fleet import dual_fuel_plant_groups
    from market_sim.data.fuel.dual_fuel import _GAS_FUEL_IDX, dual_fuel_oil_price_series

    st = year_state(year)
    fa, cfg = st["fleet_arrays"], st["config"]
    assert cfg.nyiso_gas_flow_date and not cfg.dual_fuel_switching
    zones = list(st["iso_config"].zone_names)
    gas = np.asarray(st["fuel_prices"], float)[:, :8760]
    oil = dual_fuel_oil_price_series(cfg, year)[:8760]
    capable = dual_fuel_plant_groups()
    is_gas = np.isin(fa.fuel_type_idx, _GAS_FUEL_IDX)
    sel = [
        g for g in np.nonzero(is_gas)[0]
        if (int(fa.plant_code[g]), str(fa.plant_group[g])) in capable
    ]
    gas_d = gas[sel].reshape(len(sel), 365, 24).mean(2)
    oil_d = oil.reshape(365, 24).mean(1)
    bind_d = (gas[sel] > oil).reshape(len(sel), 365, 24).any(2)
    by = burn[burn.year == year]
    dates = pd.to_datetime(by.date)
    doy = dates.dt.dayofyear.to_numpy() - 1
    if pd.Timestamp(year=year, month=12, day=31).dayofyear == 366:
        doy = np.where(dates.dt.month.to_numpy() > 2, doy - 1, doy)
    fmap = {}
    for code, d, f in zip(by.plant_code.astype(int), doy, by.oil_heat_share):
        fmap[(code, int(d))] = float(f)
    rows = []
    for i, g in enumerate(sel):
        for d in np.nonzero(bind_d[i])[0]:
            rows.append(
                {
                    "g": int(g),
                    "plant": int(fa.plant_code[g]),
                    "klass": str(fa.plant_group[g]),
                    "zone": zones[int(fa.zone_idx[g])],
                    "mw": float(fa.pmax[g]),
                    "hr": float(fa.heat_rate[g]),
                    "vom": float(np.asarray(fa.vom)[g]) if getattr(fa, "vom", None) is not None else 0.0,
                    "day": int(d),
                    "gas": float(gas_d[i, d]),
                    "oil": float(oil_d[d]),
                    "f": fmap.get((int(fa.plant_code[g]), int(d)), 0.0),
                }
            )
    r = pd.DataFrame(rows)
    out = {"year": year, "capable_tranches": len(sel), "capable_mw": float(fa.pmax[sel].sum())}
    if r.empty:
        out["binding_gen_days"] = 0
        return out
    out["binding_gen_days"] = int(len(r))
    out["binding_days"] = int(r.day.nunique())
    out["by_zone"] = {
        z: {
            "gen_days": int(len(g)),
            "mw_days": round(float(g.mw.sum()), 0),
            "mw_wtd_oil_share": round(float(np.average(g.f, weights=g.mw)), 3),
            "share_mw_below_1pct": round(float(g.mw[g.f < 0.01].sum() / g.mw.sum()), 3),
            "share_mw_above_50pct": round(float(g.mw[g.f >= 0.5].sum() / g.mw.sum()), 3),
            "relief_wtd_oil_share": round(float(np.average(g.f, weights=g.mw * (g.gas - g.oil))), 3),
        }
        for z, g in r.groupby("zone")
    }
    r["relief"] = r.mw * (r.gas - r.oil)
    near = (r.gas - r.oil) < 1.0
    out["all"] = {
        "mw_wtd_oil_share": round(float(np.average(r.f, weights=r.mw)), 3),
        "relief_wtd_oil_share": round(float(np.average(r.f, weights=r.relief)), 3),
        "share_mw_days_near_parity_lt_1usd": round(float(r.mw[near].sum() / r.mw.sum()), 3),
        "share_mw_below_1pct_when_relief_ge_5usd": round(
            float(r.mw[(r.f < 0.01) & ~((r.gas - r.oil) < 5.0)].sum() / max(r.mw[~((r.gas - r.oil) < 5.0)].sum(), 1e-9)), 3
        ),
        "share_mw_below_1pct": round(float(r.mw[r.f < 0.01].sum() / r.mw.sum()), 3),
    }
    # DA-implied fuel on NYC binding days (diagnostic only)
    a = pd.read_parquet(ZONAL)
    a = a[(a.year == year) & (a.zone == "NYC")].sort_values("hour")
    da = a.da.to_numpy()[:8760].reshape(365, 24).mean(1)
    nyc = r[r.zone == "NYC"]
    days = []
    for d, g in nyc.groupby("day"):
        w = g.mw
        hr = float(np.average(g.hr, weights=w))
        vom = float(np.average(g.vom, weights=w))
        days.append(
            {
                "date": str((pd.Timestamp(year=year, month=1, day=1) + pd.Timedelta(days=int(d))).date()),
                "nyc_da": round(float(da[d]), 1),
                "hr": round(hr, 2),
                "implied_fuel": round((float(da[d]) - vom) / hr, 2),
                "gas": round(float(np.average(g.gas, weights=w)), 2),
                "oil": round(float(g.oil.iloc[0]), 2),
                "meas_f": round(float(np.average(g.f, weights=w)), 3),
                "meas_mix_price": round(float(np.average(g.f * g.oil + (1 - g.f) * g.gas, weights=w)), 2),
            }
        )
    dd = pd.DataFrame(days)
    if not dd.empty:
        out["nyc_days"] = int(len(dd))
        out["nyc_median"] = {
            k: round(float(dd[k].median()), 2)
            for k in ("nyc_da", "implied_fuel", "gas", "oil", "meas_mix_price", "meas_f")
        }
        # which price is closer to the DA-implied fuel, day by day
        cap = np.minimum(dd.gas, dd.oil)
        out["nyc_closest"] = {
            "cap_min_gas_oil": int(((cap - dd.implied_fuel).abs() <= (dd.meas_mix_price - dd.implied_fuel).abs()).sum()),
            "measured_mix": int(((cap - dd.implied_fuel).abs() > (dd.meas_mix_price - dd.implied_fuel).abs()).sum()),
        }
        out["nyc_mae"] = {
            "cap": round(float((cap - dd.implied_fuel).abs().mean()), 2),
            "measured_mix": round(float((dd.meas_mix_price - dd.implied_fuel).abs().mean()), 2),
            "gas_uncapped": round(float((dd.gas - dd.implied_fuel).abs().mean()), 2),
        }
        out["nyc_top10"] = dd.sort_values("gas", ascending=False).head(10).to_dict("records")
        out["nyc_days_table"] = dd.to_dict("records")
    return out


def main() -> None:
    """Run the census for 2021-2025 and write JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--oil-burn", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025])
    a = ap.parse_args()
    burn = pd.read_csv(a.oil_burn)
    res = [footprint(y, burn) for y in a.years]
    Path(a.out).write_text(json.dumps(res, indent=1))
    for r in res:
        print(json.dumps({k: v for k, v in r.items() if k != "nyc_top10"}))


if __name__ == "__main__":
    main()
