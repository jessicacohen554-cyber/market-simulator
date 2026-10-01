"""PJM-NEXT-13 zero-LP arm delta: keeper vs ``pjm_replacement_cost_fuel`` offers.

Reads the paired ``fleet_only`` dumps (``_pjmnext13_fleet_dump.py`` without and with
``--arm``) and reports, per year:

* per class, the capacity-weighted change in fuel price and in the P1 bid
  (``mc_base`` + the mid-curve floor markup, the bid the LP sees before startup
  amortization);
* a STATIC marginal-unit re-pricing of the keeper's own zonal P1 prices. In each
  zone-hour the unit whose keeper bid lies within ``MATCH_TOL`` of the zone price is
  taken as marginal and the price moves by that unit's bid change. An unmatched
  zone-hour takes the mean move of the matched hours in its zone-month. No
  re-dispatch: a first-order prediction for the PRECOMMIT, not a result.

Writes ``results/phase0/pjm/_pjmnext13_arm_delta.json``. Run with the dump dir as argv[1].
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"
OUT = REPO / "results/phase0/pjm/_pjmnext13_arm_delta.json"
ZONES = (
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
)
CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS", "COAL_BIT", "COAL_PRB")
MATCH_TOL = 0.25  # $/MWh — the keeper bid-vs-price match (79 % of 2023 zone-hours)
MONTH = pd.date_range("2001-01-01", periods=8760, freq="h").month.to_numpy() - 1


def bid(d: dict) -> np.ndarray:
    """The P1 bid before startup amortization."""
    return d["mc_base"] + d.get("midcurve_markup", 0.0)


def main() -> None:
    """Per-year class deltas and the static price move."""
    d_dir = Path(sys.argv[1])
    out = {}
    for y in range(2019, 2026):
        k = dict(np.load(d_dir / f"pjmnext13_fleet_{y}.npz", allow_pickle=True))
        a = dict(np.load(d_dir / f"pjmnext13_fleet_{y}_arm.npz", allow_pickle=True))
        assert (k["unit_ids"] == a["unit_ids"]).all()
        g, pm = k["plant_group"], k["pmax"]
        bk, ba = bid(k), bid(a)
        cls = {}
        for c in CLASSES:
            s = g == c
            if not s.any():
                continue
            w = pm[s]
            cls[c] = {
                "dfuel": round(float(np.average((a["fuel_prices"][s] - k["fuel_prices"][s]).mean(1), weights=w)), 3),
                "dbid": round(float(np.average((ba[s] - bk[s]).mean(1), weights=w)), 2),
            }  # fmt: skip
        sysd = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        P = sysd.pivot_table(index="hour", columns="zone", values="price").sort_index()[list(ZONES)].to_numpy()[:8760]  # fmt: skip
        W = sysd.pivot_table(index="hour", columns="zone", values="demand").sort_index()[list(ZONES)].to_numpy()[:8760]  # fmt: skip
        zi, av = k["zone"].astype(int), k["availability"]
        # Leg attribution: the same static re-pricing with only the GAS rows' bid
        # change (coal rows held at the keeper bid).
        gas_only = np.isin(
            g, ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
        )
        ba_gas = np.where(gas_only[:, None], ba, bk)
        res = {}
        for leg, arm_bid in (("joint", ba), ("gas_only", ba_gas)):
            res[leg] = _static(P, W, bk, arm_bid, zi, av)
        out[str(y)] = {
            "class": cls,
            "keeper_lw_price": res["joint"][0],
            "static_arm_lw_price": res["joint"][1],
            "static_dprice": round(res["joint"][1] - res["joint"][0], 2),
            "static_dprice_gas_only": round(res["gas_only"][1] - res["gas_only"][0], 2),
        }
        print(y, json.dumps(out[str(y)]), flush=True)
    OUT.write_text(json.dumps(out, indent=1))


def _static(P, W, bk, ba, zi, av) -> tuple[float, float]:
    """Keeper and statically re-priced load-weighted mean price (see module doc)."""
    if True:
        dP = np.full(P.shape, np.nan)
        for z in range(len(ZONES)):
            r = np.where(zi == z)[0]
            gap = np.abs(bk[r] - P[:, z][None, :])
            gap = np.where(av[r] > 0, gap, np.inf)
            j = gap.argmin(0)
            ok = gap[j, np.arange(P.shape[0])] < MATCH_TOL
            dP[ok, z] = (ba[r] - bk[r])[j[ok], np.arange(P.shape[0])[ok]]
            for m in range(12):
                hm = (MONTH == m) & ~ok
                fill = (
                    np.nanmean(dP[(MONTH == m) & ok, z])
                    if ((MONTH == m) & ok).any()
                    else 0.0
                )
                dP[hm, z] = fill
        lw_k = float((P * W).sum() / W.sum())
        lw_a = float(((P + dP) * W).sum() / W.sum())
    return round(lw_k, 2), round(lw_a, 2)


if __name__ == "__main__":
    main()
