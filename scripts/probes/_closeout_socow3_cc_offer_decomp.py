"""closeout-SOCO-w3 phase 0c, zero LP: decompose the CC-below-coal night ordering on the holdout control.

Desk direction (2026-10-04): check the measured inputs that set CC below coal at night — per-unit heat rates,
delivered gas, CC commitment physics — before any PRECOMMIT. Control: ``closeout_soco_w3_span``.

Per year (one ``fleet_only`` rebuild of the control, ``scripts/lib/bundle_fleet.reconstruct_bundle_fleet``):

1. **Offer build-up.** Each coal / CC_REGULAR tranche's ``mc_base`` = HR x fuel + VOM; the HR and fuel arrays the
   LP saw.
2. **Fuel vs EIA-923.** The model's monthly fuel price per plant against the plant's own EIA-923 Schedule-2
   delivered price (``load_monthly_fuel_costs``), capacity-weighted; plant-months whose ratio is outside
   [0.67, 1.5] are reported as print outliers and excluded from the robust gap.
3. **Parasitic coverage.** ``parasitic_load_factors.parquet`` carries no SOCO plant, so every SOCO measured HR
   artifact converts gross to net on the class default (coal 0.93, CC 0.975). The plant's own factor is computed
   in memory (``campd.compute_parasitic_factors``, the frozen deriver's construction, nothing written) and the
   offer change it implies is reported: d = HR x fuel x (default / measured - 1).
4. **Reach.** Idle non-must-run coal headroom (TWh) whose P1 offer sits within $x of the hour's LMP.

Writes ``docs/records/soco/closeout-soco-w3/phase0c_<year>.json``. Run: ``uv run python
scripts/probes/_closeout_socow3_cc_offer_decomp.py --year 2021``.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data import campd  # noqa: E402
from market_sim.data.eia923 import load_monthly_fuel_costs, load_monthly_generation  # noqa: E402
from scripts.lib import bundle_fleet as BF  # noqa: E402

BUNDLE = REPO / "results/calibration/closeout_soco_w3_span"
OUT_DIR = REPO / "docs/records/soco/closeout-soco-w3"
DEFAULT_PF = {"COAL": 0.93, "CC": 0.975}  # the class defaults the SOCO HR artifacts record (parasitic_factor col)
OUTLIER = (0.67, 1.5)
REACH_USD = (1, 2, 3, 4, 6)
_MONTH = np.repeat(np.arange(1, 13), np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24)


def _hourly(v, n: int) -> np.ndarray:
    """Return a (n, 8760) view of a per-unit or per-unit-hour array."""
    v = np.asarray(v, float)
    if v.ndim == 1:
        return np.repeat(v[:, None], 8760, 1)
    return v if v.shape == (n, 8760) else v.T


def fleet_frame(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Coal / CC tranche build-up and the per-(plant, month) model fuel price."""
    state, _ = BF.reconstruct_bundle_fleet(BUNDLE, year)
    fa = state["fleet_arrays"]
    n = len(fa.unit_ids)
    fuel = _hourly(state["fuel_prices"], n)
    mc = _hourly(state["mc_base"], n)
    night = np.arange(8760) % 24 < 5
    rows, mon = [], []
    for i in range(n):
        g = str(fa.plant_group[i])
        fam = "CC" if g == "CC_REGULAR" else "COAL" if g.startswith("COAL") else None
        if fam is None:
            continue
        r = dict(unit_id=str(fa.unit_ids[i]), plant_code=int(fa.plant_code[i]), family=fam, pmax=float(fa.pmax[i]),
                 hr=float(fa.heat_rate[i]), fuel_night=float(fuel[i, night].mean()),
                 mc_night=float(mc[i, night].mean()))
        rows.append(r)
        for m in range(1, 13):
            mon.append(dict(plant_code=r["plant_code"], family=fam, month=m, pmax=r["pmax"],
                            fuel=float(fuel[i, _MONTH == m].mean())))
    f = pd.DataFrame(rows)
    f["vom_implied"] = f.mc_night - f.hr * f.fuel_night
    m = pd.DataFrame(mon)
    m = (m.assign(w=m.fuel * m.pmax).groupby(["plant_code", "family", "month"])
         .agg(w=("w", "sum"), pmax=("pmax", "sum")).reset_index())
    m["model_fuel"] = m.w / m.pmax
    return f, m[["plant_code", "family", "month", "model_fuel"]]


def fuel_vs_f923(year: int, f: pd.DataFrame, m: pd.DataFrame) -> dict:
    """Capacity-weighted model fuel vs the plant's own EIA-923 delivered price, with outliers split out."""
    costs = load_monthly_fuel_costs()
    costs = costs[costs.year == year]
    out = {}
    for fam, fg in (("CC", "Natural Gas"), ("COAL", "Coal")):
        x = m[m.family == fam].merge(costs[costs.fuel_group == fg][["plant_id", "month", "price_per_mmbtu"]],
                                     left_on=["plant_code", "month"], right_on=["plant_id", "month"]).dropna()
        cap = f[(f.family == fam) & ~f.unit_id.str.contains("mustrun")].groupby("plant_code").pmax.sum()
        hr = float((f[f.family == fam].hr * f[f.family == fam].pmax).sum() / f[f.family == fam].pmax.sum())
        x["ratio"] = x.price_per_mmbtu / x.model_fuel
        bad = x[(x.ratio < OUTLIER[0]) | (x.ratio > OUTLIER[1])]
        ok = x.drop(bad.index)
        w = ok.plant_code.map(cap).fillna(0.0)
        gap = float(((ok.price_per_mmbtu - ok.model_fuel) * w).sum() / w.sum()) if w.sum() else float("nan")
        out[fam] = dict(robust_gap_usd_mmbtu=round(gap, 3), robust_gap_usd_mwh=round(gap * hr, 2),
                        plants=int(x.plant_code.nunique()),
                        outliers=bad[["plant_code", "month", "model_fuel", "price_per_mmbtu"]].round(2)
                        .to_dict("records"))
    return out


def parasitic_effect(year: int, f: pd.DataFrame) -> dict:
    """The plant's own net/gross (frozen construction, in memory) vs the class default, as $/MWh on the offer."""
    from scripts.data.derive_parasitic_load import _registry_plant_groups

    df = campd.load_campd_hourly(campd.states_for_iso("SOCO"), [year])
    gen = load_monthly_generation()
    par = campd.compute_parasitic_factors(campd.annual_plant_totals(df),
                                          campd.eia923_combustion_net(gen[gen.year == year]),
                                          plant_groups=_registry_plant_groups())
    pf = par[par.year == year].set_index("plant_id").parasitic_factor
    out = {}
    g = f[~f.unit_id.str.contains("mustrun")]
    for fam, dflt in DEFAULT_PF.items():
        s = g[g.family == fam].copy()
        s["pf"] = s.plant_code.map(pf).fillna(dflt)
        d = s.hr * s.fuel_night * (dflt / s.pf - 1.0)
        out[fam] = dict(measured_pf=round(float((s.pf * s.pmax).sum() / s.pmax.sum()), 4), default_pf=dflt,
                        offer_change_usd_mwh=round(float((d * s.pmax).sum() / s.pmax.sum()), 2))
    return out


def reach(year: int) -> dict:
    """Idle non-must-run coal headroom with offer within $x above the hour's LMP (TWh)."""
    u = pd.read_parquet(BUNDLE / f"hourly/unit_marginal_{year}.parquet",
                        columns=["unit_id", "plant_group", "hour", "mw", "cap_mw", "mc"])
    sysd = pd.read_parquet(BUNDLE / "system.parquet")
    lmp = sysd[sysd.year == year].groupby("hour")["price"].mean()
    c = u[u.plant_group.str.startswith("COAL") & ~u.unit_id.str.contains("mustrun")].copy()
    c["dx"] = c.mc - c.hour.map(lmp)
    head = (c.cap_mw - c.mw).clip(lower=0.0)
    cc = u[u.plant_group == "CC_REGULAR"]
    return dict(idle_coal_twh_within_usd={x: round(float(head[(c.dx > 0) & (c.dx <= x)].sum() / 1e6), 2)
                                          for x in REACH_USD},
                night_lmp=round(float(lmp[lmp.index % 24 < 5].mean()), 2),
                cc_night_offer_median=round(float(cc[cc.hour % 24 < 5].mc.median()), 2))


def main() -> None:
    """Run the four reads for one year and write the JSON."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--year", type=int, required=True)
    a = ap.parse_args()
    f, m = fleet_frame(a.year)
    vom = f.groupby("family").vom_implied.median().round(2).to_dict()
    res = dict(year=a.year, control=str(BUNDLE.relative_to(REPO)), vom_implied_median=vom,
               fuel_vs_f923=fuel_vs_f923(a.year, f, m), parasitic=parasitic_effect(a.year, f), reach=reach(a.year))
    path = OUT_DIR / f"phase0c_{a.year}.json"
    path.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "fuel_vs_f923"}, default=str))
    print({k: {kk: vv for kk, vv in v.items() if kk != "outliers"} for k, v in res["fuel_vs_f923"].items()})


if __name__ == "__main__":
    main()
