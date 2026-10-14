"""UC-1-FIX-5 phase 0 (zero LP): the UC cost basis of integer clusters vs CEMS fuel truth.

For every integer cluster of a uc-1.x bundle whose no-load came from the
``uc-params`` regression, compare per unit and per hour:

* ``model``  — what the UC objective charges today: the cheapest-fill energy of
  the members' P1 offers (``unit_marginal.mc``; integer rows carry ``mc_base``,
  their start markup is zeroed) plus the explicit no-load
  (``uc_schedule.noload_usd_per_unit_h``);
* ``energy`` — the same without the explicit no-load (option A);
* ``fix``    — uc-1.5: the explicit no-load kept, every member's energy moved
  to the incremental basis by removing the no-load heat the average-basis
  offer carries per MWh at full output, ``nl / pbar`` (option B as built);
* ``truth``  — the CAMPD regression the no-load comes from, completed with its
  slope: ``(a + b P) * p_eff + vom * P`` (``a`` = plant intercept / n, ``b`` =
  the units' peak-weighted OLS slope, pooled 2023-2025, same fit screen as
  ``scripts/lib/uc_params._noload_fit``; ``p_eff`` = the cluster's own $/MMBtu,
  no-load $/h / no-load MMBtu/h, so fuel and carbon are the model's).

Evaluated per unit at Pmin (``mlf * pbar * a``) and at P_hi, the top of the
non-peak curve (``pbar * a`` less the ``_peak*`` tranches: ERCOT's 2019-23
peak bands sit at x151 and would swamp a full-output average).
Usage: python cost_basis_zero_lp.py <bundle_dir> <year> <out.json>
(CAMPD extracts under data/raw/campd-unit-level; run from the repo root).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.fleet.eia860 import get_vom
from market_sim.model.uc.params import FAMILY_BY_GROUP
from scripts.lib.uc_params import (
    NOLOAD_MIN_POINTS,
    NOLOAD_MIN_RANGE_FRAC,
    POOLED_VINTAGES,
    REGISTRY,
    _CROSSWALK_CSV,
    _CROSSWALK_PUDL,
    _load_state_year,
    camd_to_eia_plant,
    load_crosswalk,
)

B, YEAR, OUT = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
RAW = Path("data/raw")
log = json.load(open(B / f"uc_solve_log_{YEAR}.json"))
iso = log["engine"]["iso"]
cl = pd.json_normalize(log["clusters"])
cl = cl[cl.integer & (cl["src.noload"] == "uc-params")].set_index("cluster")


def unit_fits() -> pd.DataFrame:
    """Per CEMS unit (plant_code, family): intercept, slope, peak — pooled vintages."""
    import scripts.lib.uc_params as up

    up.load_registry()
    frames = []
    for st in REGISTRY[iso].campd_states:
        for y in POOLED_VINTAGES:
            p = RAW / "campd-unit-level" / f"{st}_{y}.parquet"
            if p.is_file():
                frames.append(_load_state_year(p))
    d = pd.concat(frames, ignore_index=True)
    cw = load_crosswalk(RAW / _CROSSWALK_CSV, RAW / _CROSSWALK_PUDL)
    d["plant_code"] = camd_to_eia_plant(d.facilityId.to_numpy(), d.unitId.to_numpy(), cw)
    d = d[d.plant_code.isin(set(cl.plant_code))]
    rows = []
    for (pc, fam, uid), u in d.groupby(["plant_code", "uc_class", "unitId"]):
        x, y, op = u.grossLoad.to_numpy(), u.heatInput.to_numpy(), u.opTime.to_numpy()
        peak = float(x.max()) if x.size else 0.0
        m = (op >= 1.0) & (x > 0) & (y > 0)
        if peak <= 0 or m.sum() < NOLOAD_MIN_POINTS or np.ptp(x[m]) < NOLOAD_MIN_RANGE_FRAC * peak:
            continue
        b, a = np.polyfit(x[m], y[m], 1)
        rows.append(dict(plant_code=int(pc), uc_class=fam, a=max(a, 0.0), b=b, peak=peak,
                         avg_hr=float(y[m].sum() / x[m].sum())))
    return pd.DataFrame(rows)


fits = unit_fits()
plant = fits.groupby(["plant_code", "uc_class"]).apply(
    lambda g: pd.Series({"b": np.average(g.b, weights=g.peak),
                         "avg_hr": np.average(g.avg_hr, weights=g.peak)})
)
um = pd.read_parquet(B / "hourly" / f"unit_marginal_{YEAR}.parquet",
                     columns=["pass", "unit_id", "plant_code", "plant_group", "fuel", "hour", "cap_mw", "mc"])
um = um[um["pass"] == "P1"]
um["fam"] = um.plant_group.astype(str).map(FAMILY_BY_GROUP)
sch = pd.read_parquet(B / "hourly" / f"uc_schedule_{YEAR}.parquet")
out = []
for c, r in cl.iterrows():
    key = (int(r.plant_code), r.uc_class)
    if key not in plant.index:
        continue
    m = um[(um.plant_code == r.plant_code) & (um.fam == r.uc_class)]
    if m.empty:
        continue
    n = int(r.n)
    m = m.assign(cap=m.cap_mw / n).sort_values(["hour", "mc"])
    m["cum"] = m.groupby("hour").cap.cumsum()
    pmax = m.groupby("hour").cap.sum()
    pmin = r.mlf * pmax
    nonpeak = ~m.unit_id.astype(str).str.contains("_peak")
    phi = m[nonpeak].groupby("hour").cap.sum().reindex(pmax.index).fillna(0.0)

    def fill(level: pd.Series) -> pd.Series:
        lv = m.hour.map(level)
        take = (m.cap - (m.cum - lv).clip(lower=0)).clip(lower=0, upper=m.cap)
        return (take * m.mc).groupby(m.hour).sum()

    e_min, e_max = fill(pmin), fill(phi)
    s = sch[sch.cluster == c].set_index("hour").noload_usd_per_unit_h
    ok = (pmax > 1.0) & (s.reindex(pmax.index) > 0)
    a, b = r.noload_mmbtu_h, plant.loc[key, "b"]
    vom = get_vom(str(m.fuel.iloc[0]))
    ok &= phi > 1.0
    nl = s.reindex(pmax.index)[ok]
    p_eff = nl / r.noload_mmbtu_h
    pm, px = pmin[ok], phi[ok]
    rec = dict(cluster=int(c), plant_code=int(r.plant_code), uc_class=r.uc_class,
               cap_mw=float(r.pbar_mw * n), mlf=float(r.mlf),
               nl_mmbtu_per_mwh_at_pmax=float(a / r.pbar_mw),
               slope_over_avg=float(b / plant.loc[key, "avg_hr"]))
    for tag, P, E in (("pmin", pm, e_min[ok]), ("phi", px, e_max[ok])):
        truth = (a + b * P) * p_eff + vom * P
        rec[f"truth_{tag}"] = float((truth / P).mean())
        rec[f"model_{tag}"] = float(((E + nl) / P).mean())
        rec[f"energy_{tag}"] = float((E / P).mean())
        rec[f"fix_{tag}"] = float(((E - nl / r.pbar_mw * P + nl) / P).mean())
    out.append(rec)
d = pd.DataFrame(out)


def wavg(g: pd.DataFrame, col: str) -> float:
    ok = g[col].notna()
    return float(np.average(g.loc[ok, col], weights=g.loc[ok, "cap_mw"])) if ok.any() else None


summary = {}
for fam, g in d.groupby("uc_class"):
    summary[fam] = {"clusters": len(g), "cap_gw": float(g.cap_mw.sum() / 1e3),
                    **{k: (None if wavg(g, k) is None else round(wavg(g, k), 3)) for k in d.columns
                       if k.startswith(("truth", "model", "energy", "fix", "nl_", "mlf", "slope"))}}
json.dump({"iso": iso, "year": YEAR, "engine": log["engine"]["version"],
           "summary": summary, "clusters": out}, open(OUT, "w"), indent=1, default=float)
print(json.dumps(summary, indent=1))
