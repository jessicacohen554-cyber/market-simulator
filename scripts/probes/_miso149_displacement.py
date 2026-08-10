"""miso-149 G-3 — does Object A exist as a DISPLACEMENT object, or dissolve into item 9? **NO LP.**

Adjudicates PREREG ``results/calibration/PREREG-miso149-overlay-contradiction-2026-08-10.md``
§3 G-3 (pushed at ``318c0542`` before this script was written).

miso-147 measured ``E - M ~= 2,131 MW`` of model CC that is available AND in-merit
**at the REAL price** and still not dispatched, and the §5.4 queue carries that as
"the all-months CC commitment/displacement residual".  But at the model's OWN
price an LP optimum leaves no capability undispatched except through a nameable
blocker, so that number cannot by itself establish a commitment object.  This
probe splits it, on the keeper's own committed sidecars, into a telescoping sum
that closes exactly::

    E_actual(mc_base <= actual RT)                     <- miso-147's E
      - E_model_sys(mc_base <= model system price)     = leg PRICE-LEVEL   \\
      - E_model_bid_sys(bid <= model system price)     = leg MARKUP         > leg 1 (item 9)
      - E_model_bid_zone(bid <= own ZONAL price)       = leg CONGESTION    -> leg 2
      - M(class sidecar dispatch)                      = leg RESIDUAL      -> legs 3+4

with leg 3 (reserve-held) bounded from the ``reserve_family`` sidecar -- the only
artifact in which a locational family's binding is observable.

**Pre-committed rule (PREREG §3 G-3):** leg 1 >= 60 % of ``E - M`` means Object A
DISSOLVES INTO ITEM 9; legs 2+3 >= 40 % means a genuine blocker exists and is
named.  The test is registered AGAINST INTEREST -- it can retire this session's
own priority-1 object.

**Bound direction, declared:** ``markup_ceiling`` is a LOWER bound on the P1
markup, so ``E_model_bid_*`` is an UPPER bound and leg 1 is a **LOWER** bound.
A leg-1 verdict of "dissolves" is therefore conservative.

Writes ``results/calibration/_miso149_displacement.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _i, _p in enumerate((REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes")):
    sys.path.insert(_i, str(_p))

from _miso147_strata import (  # noqa: E402
    FAMILY_TO_KLASSES,
    HOURS,
    YEARS,
    c3a_weight,
    fam_of_klass,
    strata,
    wmean,
)
import _miso143_stack as stack  # noqa: E402
from _miso143_stack import hygiene, month_of_hour  # noqa: E402
from _miso137_c3a_gap_decomposition import actual_hourly  # noqa: E402
from _miso149_overlay import KEEPER149, fleet149  # noqa: E402

OUT = REPO / "results" / "calibration" / "_miso149_displacement.json"
DISSOLVE_BAR = 0.60  # PREREG §3 G-3
BLOCKER_BAR = 0.40


def zone_price(year: int) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """{zone: (8760,) P1 LMP} and the load-weighted system series, keeper sidecar."""
    df = pd.read_parquet(KEEPER149 / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    zp = {
        str(z): g.sort_values("hour")["price"].to_numpy(float)
        for z, g in df.groupby("zone", sort=False)
    }
    num = df.groupby("hour").apply(
        lambda g: float((g["price"] * g["demand"]).sum()), include_groups=False
    )
    den = df.groupby("hour")["demand"].sum()
    sysp = (num / den).reindex(range(HOURS)).to_numpy(float)
    return zp, sysp


def class_dispatch(year: int, klasses: tuple[str, ...]) -> np.ndarray:
    """P1 dispatch (8760,) MW summed over the named sidecar klasses."""
    df = pd.read_parquet(KEEPER149 / "hourly" / f"class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"].isin(klasses))]
    return (
        df.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )


def reserve_held(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(held MW, max family dual) per hour, all families -- an UPPER bound on leg 3."""
    df = pd.read_parquet(KEEPER149 / "hourly" / f"reserve_family_{year}.parquet")
    df = df[df["pass"] == "P1"]
    held = df.groupby("hour")["held_mw"].sum().reindex(range(HOURS)).fillna(0.0)
    dual = df.groupby("hour")["dual"].max().reindex(range(HOURS)).fillna(0.0)
    return held.to_numpy(float), dual.to_numpy(float)


def run() -> dict:
    hygiene()
    stack.KEEPER = KEEPER149  # PREREG §2 — new measurements read the CURRENT keeper
    res: dict = {
        "session": "miso-149",
        "prereg": "results/calibration/PREREG-miso149-overlay-contradiction-2026-08-10.md",
        "prereg_commit": "318c0542",
        "keeper_bundle": str(KEEPER149.relative_to(REPO)),
        "gate": "G-3 -- does the all-months CC residual dissolve into item 9?",
        "bound_note": (
            "markup_ceiling is a LOWER bound on the P1 markup, so E_bid is an UPPER "
            "bound and leg 1 is a LOWER bound: a 'dissolves' verdict is conservative."
        ),
        "years": {},
    }
    fmap = fam_of_klass()
    for year in YEARS:
        pack = fleet149(year)
        st = strata(year)
        w = c3a_weight(year)
        rt, _ = actual_hourly(year)
        zp, sysp = zone_price(year)
        held, rdual = reserve_held(year)

        cap = pack["pmax"][:, None] * pack["availability"].astype(np.float64)
        mc = pack["mc_base"].astype(np.float64)
        bid = mc + pack["markup"][:, None]
        zprice = np.vstack(
            [zp.get(str(z), np.full(HOURS, np.nan)) for z in pack["zone"]]
        )

        yr: dict = {"families": {}}
        for fam in ("CC", "ST_GAS", "ST_COAL"):
            rows = np.array([fmap.get(str(k)) == fam for k in pack["klass"]])
            if not rows.any():
                continue
            c = cap[rows]
            e_actual = np.where(mc[rows] <= rt[None, :], c, 0.0).sum(axis=0)
            e_sys = np.where(mc[rows] <= sysp[None, :], c, 0.0).sum(axis=0)
            e_bid_sys = np.where(bid[rows] <= sysp[None, :], c, 0.0).sum(axis=0)
            e_bid_zone = np.where(bid[rows] <= zprice[rows], c, 0.0).sum(axis=0)
            m = class_dispatch(year, FAMILY_TO_KLASSES[fam])

            frow: dict = {"strata": {}}
            for sname, mask in st["masks"].items():
                E = wmean(np.nan_to_num(e_actual), w, mask)
                Es = wmean(np.nan_to_num(e_sys), w, mask)
                Eb = wmean(np.nan_to_num(e_bid_sys), w, mask)
                Ez = wmean(np.nan_to_num(e_bid_zone), w, mask)
                M = wmean(m, w, mask)
                U = E - M
                legs = {
                    "price_level": E - Es,
                    "markup": Es - Eb,
                    "congestion": Eb - Ez,
                    "residual_incl_reserve": Ez - M,
                }
                frow["strata"][sname] = {
                    "E_actual": round(E, 1),
                    "E_model_sys": round(Es, 1),
                    "E_model_bid_sys": round(Eb, 1),
                    "E_model_bid_zone": round(Ez, 1),
                    "M_dispatch": round(M, 1),
                    "U_E_minus_M": round(U, 1),
                    "legs_mw": {k: round(v, 1) for k, v in legs.items()},
                    "legs_share_of_U": (
                        {k: round(v / U, 3) for k, v in legs.items()}
                        if abs(U) > 1e-6 else None
                    ),
                    "leg1_price_and_markup_share": (
                        round((legs["price_level"] + legs["markup"]) / U, 3)
                        if abs(U) > 1e-6 else None
                    ),
                    "reserve_held_all_families_mw_upper_bound": round(
                        wmean(held, w, mask), 1
                    ),
                    "reserve_max_family_dual": round(wmean(rdual, w, mask), 4),
                }
            mon = month_of_hour(np.arange(HOURS))
            frow["monthly_U_mw"] = [
                round(float((e_actual - m)[mon == mm].mean()), 1) for mm in range(1, 13)
            ]
            frow["monthly_leg1_mw"] = [
                round(float((e_actual - e_bid_sys)[mon == mm].mean()), 1)
                for mm in range(1, 13)
            ]
            yr["families"][fam] = frow
        res["years"][str(year)] = yr
        del pack, cap, mc, bid, zprice

    s1 = res["years"]["2025"]["families"]["CC"]["strata"]["S1"]
    leg1 = s1["leg1_price_and_markup_share"]
    blocker = (
        round(
            (s1["legs_mw"]["congestion"] + s1["legs_mw"]["residual_incl_reserve"])
            / s1["U_E_minus_M"],
            3,
        )
        if abs(s1["U_E_minus_M"]) > 1e-6 else None
    )
    res["G3_verdict"] = {
        "S1_2025_U_mw": s1["U_E_minus_M"],
        "leg1_share_lower_bound": leg1,
        "legs2plus_share": blocker,
        "branch": (
            "DISSOLVES-INTO-ITEM-9" if leg1 is not None and leg1 >= DISSOLVE_BAR
            else "BLOCKER-NAMED" if blocker is not None and blocker >= BLOCKER_BAR
            else "INCONCLUSIVE"
        ),
        "bars": {"dissolve": DISSOLVE_BAR, "blocker": BLOCKER_BAR},
    }
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    v = r["G3_verdict"]
    print("G-3", v["branch"], json.dumps(v))
    print("S1 2025 CC legs:", json.dumps(
        r["years"]["2025"]["families"]["CC"]["strata"]["S1"], indent=1))
    print("->", OUT)
