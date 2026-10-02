"""NYISO-NEXT-34 phase 0 (ZERO LP): measured oil burn on the keeper's off-cap days.

Open item 3 is the 2023 winter under-pricing left after the print-level repair. The
miss is February 2023 alone. It sits on Feb 3-4, when CAMPD shows the NYISO gas fleet
burning 43-49 % oil by heat input while the keeper's trade-dated Z6 series prices those
days at the $3.52 weekend print. The parity cap ``min(gas, oil)`` can only LOWER a unit's
fuel cost, so it cannot represent a unit that burns oil while gas is cheaper.

This probe reads, with no LP:

1. **Population.** Fleet-wide plant-day oil share from the CAMPD artifact
   (``derive_measured_oil_burn_days.py --iso NYISO``, zero parameters). A high-oil day is
   a day the fleet's oil share of gas-unit heat input is >= 0.10. The error is the keeper
   P1 system load-weighted daily price minus RT and DA (committed sidecars).
2. **Cap state.** For the same days, whether the keeper's parity cap binds anywhere
   (fleet-only rebuild of the keeper recipe; a capable tranche whose gas exceeds oil).
3. **Bracket.** A second fleet-only rebuild with ``dual_fuel_measured_oil_burn`` on.
   Per zone-hour, ``dmc`` = the change in ``mc_base`` of the zone's gas tranches.
   * ``lo``: price + pmax-weighted mean ``dmc`` over every gas tranche in the zone (the
     expected shift if the marginal unit is a capacity-drawn gas tranche);
   * ``mo``: the same shift, reported by month (where the arm moves the year).
   Annual C3a (system load-weighted vs RT) and monthly NRMSE are recomputed on each.

Every number is a diagnostic. Nothing here feeds a solve (rule 13). The LP decides.

Usage: uv run python scripts/probes/nyisonext34_oilburn_offcap.py --out <json>
"""

from __future__ import annotations

import argparse
import importlib
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
YEARS = (2021, 2022, 2023, 2024, 2025)
HIGH_OIL = 0.10  # population cut only; not a model parameter


def _bundle(year: int) -> Path:
    """Keeper bundle carrying ``year``."""
    name = "nyisonext26p_2021" if year == 2021 else "nyisonext26p_span"
    return REPO / "results/calibration" / name


def fleet_state(year: int, overrides: dict) -> dict:
    """Fleet-only rebuild of the keeper recipe with ``overrides`` in prb_overrides."""
    os.environ["NYISO_KEEPER_BUNDLE"] = str(_bundle(year))
    import scripts.probes.nyiso242_tail_reachability as t

    t = importlib.reload(t)
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((t.BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(t.BUNDLE, year))
    prb = dict(kw.get("prb_overrides") or {})
    prb.update(overrides)
    kw["prb_overrides"] = prb
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def fleet_oil_share(path: Path) -> pd.Series:
    """Fleet-wide daily oil share of gas-unit heat input (CAMPD artifact)."""
    d = pd.read_csv(path, parse_dates=["date"])
    d["oil"] = d.oil_heat_share * d.heat_input_mmbtu
    g = d.groupby("date")[["oil", "heat_input_mmbtu"]].sum()
    return g.oil / g.heat_input_mmbtu


def system_frame(year: int) -> pd.DataFrame:
    """Keeper P1 zonal price joined to measured RT / DA on the 8760 clock."""
    s = pd.read_parquet(_bundle(year) / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"][["zone", "hour", "price", "demand"]]
    a = pd.read_parquet(ZONAL)
    a = a[a.year == year][["zone", "hour", "rt", "da"]]
    m = s.merge(a, on=["zone", "hour"])
    m["rt"] = m.rt.fillna(m.da)
    return m


def c3a(m: pd.DataFrame, col: str) -> float:
    """System load-weighted mean price error vs RT, percent."""
    return 100.0 * (np.average(m[col], weights=m.demand) / np.average(m.rt, weights=m.demand) - 1)  # fmt: skip


def nrmse(m: pd.DataFrame, col: str, year: int) -> float:
    """Monthly load-weighted price NRMSE vs RT (the C3b construction)."""
    mon = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(m.hour, "h")).dt.month
    g = m.assign(mon=mon.values).groupby("mon")
    mod = g.apply(lambda x: np.average(x[col], weights=x.demand))
    act = g.apply(lambda x: np.average(x.rt, weights=x.demand))
    return float(np.sqrt(((mod - act) ** 2).mean()) / act.mean())


def daily(m: pd.DataFrame, year: int, cols: list[str]) -> pd.DataFrame:
    """System load-weighted daily means."""
    day = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(m.hour // 24, "D")
    g = m.assign(date=day.values).groupby("date")
    return pd.DataFrame({c: g.apply(lambda x, c=c: np.average(x[c], weights=x.demand)) for c in cols})  # fmt: skip


def year_bracket(year: int, share: pd.Series) -> dict:
    """Cap state and price bracket for one year."""
    from market_sim.data.fuel.dual_fuel import _GAS_FUEL_IDX, dual_fuel_oil_price_series
    from market_sim.data.fleet import dual_fuel_plant_groups

    base = fleet_state(year, {})
    arm = fleet_state(year, {"dual_fuel_measured_oil_burn": True})
    fa = base["fleet_arrays"]
    zones = list(base["iso_config"].zone_names)
    is_gas = np.isin(fa.fuel_type_idx, _GAS_FUEL_IDX)
    zidx = np.asarray(fa.zone_idx)
    pmax = np.asarray(fa.pmax, float)
    dmc = np.asarray(arm["mc_base"], float)[:, :8760] - np.asarray(base["mc_base"], float)[:, :8760]  # fmt: skip

    # keeper cap state: capable gas tranche with pre-cap gas > oil, any hour of the day
    pre = fleet_state(year, {"dual_fuel_switching": False})
    gas_pre = np.asarray(pre["fuel_prices"], float)[:, :8760]
    oil = dual_fuel_oil_price_series(base["config"], year)[:8760]
    capable = dual_fuel_plant_groups()
    cap_sel = [
        g
        for g in np.nonzero(is_gas)[0]
        if (int(fa.plant_code[g]), str(fa.plant_group[g])) in capable
    ]
    cap_day = (gas_pre[cap_sel] > oil).reshape(len(cap_sel), 365, 24).any((0, 2))

    m = system_frame(year)
    lo = np.zeros(len(m))
    for zi, z in enumerate(zones):
        sel = np.nonzero(is_gas & (zidx == zi))[0]
        rows = (m.zone == z).to_numpy()
        if not len(sel) or not rows.any():
            continue
        hrs = m.hour.to_numpy()[rows]
        d = dmc[sel][:, hrs]
        lo[rows] = (d * pmax[sel, None]).sum(0) / pmax[sel].sum()
    m["lo"] = m.price + lo
    mon = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(m.hour, "h")).dt.month
    m["mon"] = mon.to_numpy()

    dd = daily(m, year, ["price", "lo", "rt", "da"])
    dd["share"] = share.reindex(dd.index).to_numpy()
    dd["cap_binds"] = cap_day[: len(dd)]
    hot = dd[dd.share >= HIGH_OIL]

    def err(df, col, ref):
        return round(float((df[col] - df[ref]).sum()), 1)

    out = {
        "year": year,
        "c3a_vs_rt_pct": {c: round(c3a(m, c), 2) for c in ("price", "lo")},
        "c3b_monthly_nrmse": {
            c: round(nrmse(m, c, year), 3) for c in ("price", "lo")
        },  # fmt: skip
        "arm_cells_written_share": round(float((dmc[is_gas] != 0).mean()), 4),
        "high_oil_days": int(len(hot)),
        "high_oil_days_cap_binds": int(hot.cap_binds.sum()),
    }
    for sub, df in (
        ("off_cap", hot[~hot.cap_binds]),
        ("cap_binds", hot[hot.cap_binds]),
    ):
        out[f"high_oil_{sub}"] = {
            "n": int(len(df)),
            "sum_err_vs_rt": {c: err(df, c, "rt") for c in ("price", "lo")},
            "sum_err_vs_da": {c: err(df, c, "da") for c in ("price", "lo")},
            "sum_abs_err_vs_rt": {
                c: round(float((df[c] - df.rt).abs().sum()), 1) for c in ("price", "lo")
            },
        }
    out["days"] = [
        {
            "date": str(i.date()),
            **{
                k: round(float(v), 2)
                if not isinstance(v, (bool, np.bool_))
                else bool(v)
                for k, v in r.items()
            },
        }  # fmt: skip
        for i, r in hot.iterrows()
    ]
    out["monthly_pct_vs_rt"] = {
        int(k): {c: round(c3a(g, c), 2) for c in ("price", "lo")}
        for k, g in m.groupby("mon")
    }
    if year == 2023:
        feb = m[
            (pd.Timestamp("2023-01-01") + pd.to_timedelta(m.hour, "h")).dt.month == 2
        ]
        out["feb_2023_pct_vs_rt"] = {c: round(c3a(feb, c), 2) for c in ("price", "lo")}  # fmt: skip
    return out


def main() -> None:
    """Run the bracket for every keeper year and write the JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    args = ap.parse_args()
    from market_sim.config.paths import measured_oil_burn_days_path

    share = fleet_oil_share(measured_oil_burn_days_path("NYISO"))
    res = [year_bracket(y, share) for y in args.years]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1))
    for r in res:
        print(json.dumps({k: v for k, v in r.items() if k != "days"}))


if __name__ == "__main__":
    main()
