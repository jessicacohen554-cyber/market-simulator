"""PJM-NEXT-14 card 1 (the LP's own answer): which keeper units price the low-end hours.

Reads a keeper REPLAY bundle's ``hourly/unit_hourly_<y>.parquet`` (per LP unit-hour:
``mw``, ``cap_mw``, the P1 offer ``mc`` the LP installed, and HiGHS ``red_cost``) and
``hourly/system_<y>.parquet`` (zonal P1 price and demand). No LP is run here.

A unit is MARGINAL in a zone-hour when it sits strictly inside its bounds
(``TOL_MW < mw < cap_mw - TOL_MW``) with a zero reduced cost (``|red_cost| <= TOL_RC``):
the LP optimality condition for a basic generation column. Several can qualify (ties,
ramp-coupled units); each zone-hour's marginal set is weighted equally within the
zone-hour, and zone-hours are weighted by zonal demand. A zone-hour with no interior
zero-reduced-cost thermal unit is priced by something else (storage, a transmission
limit with the price imported, renewables, slack) and is counted as ``no_thermal``.

LOW-END hours (actual PJM RT system price, ``actual_lmp_hourly_PJM.parquet``):
* ``delivered`` — below 6.5 x the model's PJM delivered-gas day (HH + PJM basis), the
  NEXT-12 definition (26-45 % of hours);
* ``production`` — below 6.5 x the IMM's monthly production-area spot (NEXT-13 card 2).

For every marginal unit the tranche kind (unit-id suffix), class, and — for gas CCs —
the plant's EIA-860 supply tier (``_pjmnext14_supply_point.classify``) are recorded, with
the offer ``mc`` and the offer's implied heat rate against delivered and production gas.
Writes ``results/calibration/_pjmnext14_lowend_lp_<y>.json``.

Run: ``python3 scripts/probes/_pjmnext14_lowend_lp.py <bundle_dir> <year>``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts/probes"))
from scripts.data.derive_pjm_offer_surface import _pjm_fuel_daily  # noqa: E402

import _pjmnext14_supply_point as SP  # noqa: E402

ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
SOM = REPO / "data/raw/som-competitive-conduct/som_competitive_conduct.csv"
LOW_HR = 6.5  # efficient-CC heat rate defining a low-end hour (NEXT-12/13)
TOL_MW = 0.5  # MW off a bound before a unit counts as interior
TOL_RC = 0.01  # $/MWh reduced-cost tolerance for a basic column
MONTH = pd.date_range("2001-01-01", periods=8760, freq="h").month.to_numpy() - 1


def _kind(uid: str) -> str:
    """Tranche kind from the unit-id suffix."""
    sfx = uid.rsplit("_", 1)[-1]
    if sfx.startswith("econ"):
        return "econ"
    if sfx.startswith("peak"):
        return "peak"
    return sfx if sfx in ("mustrun", "committed", "sync") else "other"


def _prod_gas(y: int) -> np.ndarray:
    """IMM monthly production-area spot broadcast to 8760."""
    d = pd.read_csv(SOM)
    d = d[
        (d.iso == "PJM")
        & (d.year == y)
        & (d.metric == "spot_price_digitized_usd_per_mmbtu")
        & (d.fleet_segment == "production_gas")
        & d.period.str.startswith("month_")
    ]
    m = d.assign(mo=d.period.str[-2:].astype(int)).set_index("mo")["value"]
    return m.reindex(range(1, 13)).to_numpy(float)[MONTH]


def main() -> None:
    """Classify the marginal set of every zone-hour and summarise by low-end definition."""
    bundle, y = Path(sys.argv[1]), int(sys.argv[2])
    cols = [
        "unit_id",
        "plant_code",
        "plant_group",
        "zone",
        "hour",
        "mw",
        "cap_mw",
        "mc",
        "red_cost",
        "pass",
    ]
    u = pd.read_parquet(bundle / f"hourly/unit_hourly_{y}.parquet", columns=cols)
    u = u[u["pass"].astype(str) == "P1"].drop(columns="pass")
    u = u[u.hour < 8760]
    marg = u[
        (u.mw > TOL_MW) & (u.mw < u.cap_mw - TOL_MW) & (u.red_cost.abs() <= TOL_RC)
    ]
    marg = marg.assign(
        uid=marg.unit_id.astype(str),
        zone=marg.zone.astype(str),
        cls=marg.plant_group.astype(str),
    )
    marg["kind"] = marg.uid.map(_kind)
    tiers = SP.plant_tiers()["tier"]
    marg["tier"] = (
        marg.plant_code.astype(str).map(tiers).where(marg.cls.str.startswith("CC_"), "")
    ).fillna("not_in_860")
    marg["n"] = marg.groupby(["zone", "hour"]).uid.transform("size")

    sysd = pd.read_parquet(bundle / f"hourly/system_{y}.parquet")
    sysd = sysd[(sysd["pass"].astype(str) == "P1") & (sysd.hour < 8760)]
    sysd = sysd.assign(zone=sysd.zone.astype(str))
    act = pd.read_parquet(ACTUAL)
    rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:8760]
    days = pd.date_range(f"{y}-01-01", periods=8760, freq="h").normalize()
    deliv = _pjm_fuel_daily().reindex(days).to_numpy(float)
    prod = _prod_gas(y)
    masks = {
        "all": np.ones(8760, bool),
        "low_delivered": rt < LOW_HR * deliv,
        "low_production": rt < LOW_HR * prod,
    }
    marg = marg.merge(sysd[["zone", "hour", "demand", "price"]], on=["zone", "hour"])
    marg["w"] = marg.demand / marg.n
    marg["hr_deliv"] = marg.mc / deliv[marg.hour.to_numpy()]
    marg["hr_prod"] = marg.mc / prod[marg.hour.to_numpy()]
    covered = marg[["zone", "hour"]].drop_duplicates().assign(cov=True)
    sysd = sysd.merge(covered, on=["zone", "hour"], how="left")
    sysd["cov"] = sysd["cov"].eq(True)

    out: dict = {"year": y, "n_zonehours": int(len(sysd))}
    for name, mh in masks.items():
        hs = np.where(mh)[0]
        s = sysd[sysd.hour.isin(hs)]
        mm = marg[marg.hour.isin(hs)]
        tot = float(s.demand.sum())
        if tot <= 0:
            out[name] = None
            continue

        def share(
            keys: list[str], top: int = 14, fr: pd.DataFrame | None = None
        ) -> dict:
            g = (mm if fr is None else fr).groupby(keys).w.sum().sort_values(
                ascending=False
            ) / tot
            return {
                ":".join(map(str, k)) if isinstance(k, tuple) else str(k): round(
                    float(v), 3
                )
                for k, v in g.head(top).items()
            }

        cc = mm[mm.cls.str.startswith("CC_")]
        out[name] = {
            "hour_share": round(float(mh.mean()), 3),
            "no_thermal_marginal_share": round(
                float(s.demand[~s["cov"]].sum() / tot), 3
            ),
            "by_class": share(["cls"]),
            "by_class_kind": share(["cls", "kind"]),
            "cc_by_tier": share(["tier"], fr=cc) if len(cc) else {},
            "median_model_price": round(float(np.median(s.price)), 2),
            "median_actual_rt": round(float(np.median(rt[mh])), 2),
            "median_marginal_mc": round(float(np.median(mm.mc)), 2)
            if len(mm)
            else None,
            "marginal_mc_implied_hr_delivered_p10_p50_p90": [
                round(float(np.percentile(mm.hr_deliv, q)), 2) for q in (10, 50, 90)
            ]
            if len(mm)
            else None,
            "cc_mc_implied_hr_production_by_tier_p50": {
                t: round(float(np.median(g.hr_prod)), 2) for t, g in cc.groupby("tier")
            },
            "share_marginal_mc_below_6p5_x_delivered": round(
                float(mm.w[mm.hr_deliv < LOW_HR].sum() / tot), 3
            )
            if len(mm)
            else None,
        }
    dest = REPO / f"results/calibration/_pjmnext14_lowend_lp_{y}.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
