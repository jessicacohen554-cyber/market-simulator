"""nyiso-180 — adjudicate the nyiso-179 §6.1 candidates on per-generator dispatch.

Reads ONLY committed-class bundle artifacts:

* ``hourly/unit_hourly_<year>.parquet`` — per LP unit-hour ``mw`` / ``cap_mw``
  and (nyiso-180) the solve's own ``mc`` and ``red_cost``;
* ``hourly/system_<year>.parquet`` — the per-zone hourly LP energy dual
  (``price``), which for NYISO is the raw dual (no overlay term is reachable
  outside ``iso == "ERCOT"``);
* ``hourly/reserve_family_<year>.parquet`` — per-family held reserve MW, for
  the reserve-headroom signature test.

No solve, no parameter, no band. Every gate and prediction is the one committed
in ``results/calibration/PREREG-nyiso180-per-generator-dispatch.md`` §2 before
the bundle existed.

The instrument is the generation column's stationarity identity

    red_cost[g,t] = mc[g,t] - price[zone(g),t] + sum_r a(r,g) * y_r

whose last term — everything charged by a NON-energy row — is measured here as

    omega[g,t] = red_cost[g,t] - (mc[g,t] - price[zone(g),t]).

Usage:
    python scripts/probes/nyiso180_unit_dispatch_adjudication.py \
        results/calibration/nyiso180_unitdispatch [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

# LP optimality tolerance band used to classify a column's basis status. HiGHS'
# default dual feasibility tolerance is 1e-7; $0.01/MWh is five orders above it
# and four below the smallest charge any conclusion here rests on, so the
# classification is insensitive to the exact value (reported both ways below).
BASIS_EPS = 0.01
# In-the-money margin for the population under study. The PREREG's §2.4 STOP
# test asks for a STRICT margin so a marginal (degenerate) column cannot be
# mistaken for an un-dispatched in-the-money one; nyiso-179's R1 already
# measured that capacity within $1/MWh of the clearing price is only 3-5% of
# ITM, so the two populations are reported side by side.
ITM_EPS_STRICT = 1.0

YEARS = (2023, 2024, 2025)


def _load_year(bundle: Path, year: int) -> pd.DataFrame | None:
    """Join the unit frame to its zonal price; return None if either is absent."""
    up = bundle / "hourly" / f"unit_hourly_{year}.parquet"
    sp = bundle / "hourly" / f"system_{year}.parquet"
    if not up.exists() or not sp.exists():
        return None
    unit = pd.read_parquet(up)
    if "mc" not in unit.columns or "red_cost" not in unit.columns:
        raise SystemExit(
            f"{up} carries no mc/red_cost columns — this bundle predates the "
            "nyiso-180 sidecar and cannot adjudicate anything"
        )
    sysd = pd.read_parquet(sp)
    # P1 is the scored pass and the only one this keeper runs; take it
    # explicitly rather than by position so a two-pass bundle cannot silently
    # mix P0 duals into a P1 comparison.
    if "pass" in unit.columns:
        unit = unit[unit["pass"].astype(str) == "P1"]
    if "pass" in sysd.columns:
        sysd = sysd[sysd["pass"].astype(str) == "P1"]
    px = sysd[["zone", "hour", "price"]].copy()
    px["zone"] = px["zone"].astype(str)
    unit["zone"] = unit["zone"].astype(str)
    out = unit.merge(px, on=["zone", "hour"], how="left", validate="many_to_one")
    if out["price"].isna().any():
        raise SystemExit(f"{year}: unit rows with no zonal price — join is broken")
    return out


def _class_mask(df: pd.DataFrame) -> pd.Series:
    """Rows belonging to the NYISO ``ST_GAS`` class under study.

    The frame carries ``fuel`` straight from ``context.fuel_types`` (never a
    re-derived classifier), so the class test is a fuel test. Both the raw
    fuel token and the unit-id class tag are accepted so a naming change in
    either cannot silently empty the population — a zero-row class is a hard
    error, never a quiet pass.
    """
    fuel = df["fuel"].astype(str).str.lower()
    uid = df["unit_id"].astype(str).str.upper()
    return fuel.eq("gas_st") | uid.str.contains("ST_GAS")


def _fmt(x) -> float | None:
    if x is None:
        return None
    v = float(x)
    return None if not np.isfinite(v) else round(v, 6)


def analyse_year(df: pd.DataFrame, year: int) -> dict:
    """All of §2's gates for one year, on the ST_GAS population."""
    cls = df[_class_mask(df)].copy()
    if cls.empty:
        raise SystemExit(f"{year}: ST_GAS population is empty — class test is wrong")

    mc = cls["mc"].to_numpy(dtype=float)
    price = cls["price"].to_numpy(dtype=float)
    rc = cls["red_cost"].to_numpy(dtype=float)
    mw = cls["mw"].to_numpy(dtype=float)
    cap = cls["cap_mw"].to_numpy(dtype=float)
    omega = rc - (mc - price)

    interior = np.abs(rc) <= BASIS_EPS
    at_lower = rc > BASIS_EPS
    at_upper = rc < -BASIS_EPS

    # --- P-a / P-b: is `price` the object `mc` is compared against? ---------
    # A column the LP itself calls marginal prices AT its zone's dual. Any
    # post-solve transform, or an injection-side delivery factor, displaces
    # this residual systematically.
    resid = (mc - price)[interior]
    p_b = {
        "interior_unit_hours": int(interior.sum()),
        "median_mc_minus_price": _fmt(np.median(resid)) if resid.size else None,
        "mean_mc_minus_price": _fmt(resid.mean()) if resid.size else None,
        "p95_abs": _fmt(np.percentile(np.abs(resid), 95)) if resid.size else None,
    }
    p_b["PASS"] = bool(
        resid.size
        and abs(p_b["median_mc_minus_price"]) <= 0.01
        and abs(p_b["mean_mc_minus_price"]) <= 0.05
    )

    # --- identity closure / §2.4 STOP --------------------------------------
    # Interior AND strictly in the money AND strictly inside its bounds with
    # omega ~ 0 would mean the identity does not close.
    strict_itm = mc < price - ITM_EPS_STRICT
    strictly_inside = (mw > 1e-6) & (mw < cap - 1e-6)
    stop_pop = strict_itm & strictly_inside & interior & (np.abs(omega) <= BASIS_EPS)
    stop = {
        "unit_hours": int(stop_pop.sum()),
        "share_of_class_unit_hours": _fmt(stop_pop.mean()),
        "mw_at_stake": _fmt(float((cap - mw)[stop_pop].sum())),
    }

    # --- the object: in the money at the model's OWN price, not dispatched --
    itm = mc <= price
    itm_cap = float(cap[itm].sum())
    itm_mw = float(mw[itm].sum())
    unrun = np.zeros_like(mw)
    unrun[itm] = np.maximum(cap[itm] - mw[itm], 0.0)
    unrun_tot = float(unrun.sum())
    obj = {
        "R_aggregate": _fmt(itm_mw / itm_cap) if itm_cap > 0 else None,
        "itm_cap_mwh": _fmt(itm_cap),
        "itm_dispatch_mwh": _fmt(itm_mw),
        "unrun_itm_mwh": _fmt(unrun_tot),
        "unrun_itm_twh": _fmt(unrun_tot / 1e6),
    }

    # --- P-c: capacity-basis mismatch --------------------------------------
    over = mw - cap
    p_c = {
        "max_mw_minus_cap": _fmt(float(over.max())),
        "unit_hours_mw_gt_cap": int((over > 1e-3).sum()),
        "unrun_share_at_upper_bound": _fmt(
            float(unrun[at_upper].sum()) / unrun_tot if unrun_tot > 0 else 0.0
        ),
    }
    p_c["PASS"] = bool(
        p_c["max_mw_minus_cap"] <= 1e-3
        and p_c["unit_hours_mw_gt_cap"] == 0
        and p_c["unrun_share_at_upper_bound"] < 0.10
    )

    # --- P-d: where the un-run MW actually sits ----------------------------
    p_d = {
        "unrun_share_at_lower_bound": _fmt(
            float(unrun[at_lower].sum()) / unrun_tot if unrun_tot > 0 else 0.0
        ),
        "unrun_share_interior": _fmt(
            float(unrun[interior].sum()) / unrun_tot if unrun_tot > 0 else 0.0
        ),
        "unrun_share_at_upper_bound": p_c["unrun_share_at_upper_bound"],
    }
    # The rent charged by non-energy rows, on the un-run in-the-money MW.
    wlo = unrun * at_lower
    p_d["omega_mwh_weighted_mean_at_lower"] = (
        _fmt(float((omega * wlo).sum() / wlo.sum())) if wlo.sum() > 0 else None
    )
    p_d["omega_p50_at_lower"] = (
        _fmt(float(np.median(omega[at_lower & itm])))
        if (at_lower & itm).any()
        else None
    )
    p_d["PASS_lower_bound_ge_70pct"] = bool(
        p_d["unrun_share_at_lower_bound"] is not None
        and p_d["unrun_share_at_lower_bound"] >= 0.70
    )

    # --- degeneracy control: how much of the "in the money" population is
    # actually AT the price (the LP is indifferent there, so it is not a
    # puzzle that it does not run). nyiso-179 R1 measured this at $1; repeated
    # here on the LP's own offer rather than a reconstruction of it.
    tie = itm & (mc > price - ITM_EPS_STRICT)
    degeneracy = {
        "unrun_share_within_1_dollar_of_price": _fmt(
            float(unrun[tie].sum()) / unrun_tot if unrun_tot > 0 else 0.0
        ),
        "R_aggregate_strict_1_dollar": _fmt(
            float(mw[strict_itm].sum()) / float(cap[strict_itm].sum())
            if float(cap[strict_itm].sum()) > 0
            else None
        ),
    }

    # --- ramp signature: is the column lower-bounded by its own t-1? -------
    # Per unit, the largest |delta mw| it ever achieves is its realised ramp
    # capability; hours sitting at that value are ramp-saturated. A pure
    # signature test with no parameter: the reference is the unit's OWN
    # measured maximum, not a configured rate.
    cls = cls.assign(_omega=omega, _unrun=unrun, _lower=at_lower, _itm=itm)
    cls = cls.sort_values(["unit_id", "hour"])
    d = cls.groupby("unit_id", observed=True)["mw"].diff().abs()
    umax = d.groupby(cls["unit_id"], observed=True).transform("max")
    ramp_sat = (umax > 1e-6) & (d >= 0.999 * umax)
    ramp = {
        "unrun_share_ramp_saturated": _fmt(
            float(cls.loc[ramp_sat.fillna(False) & cls["_lower"], "_unrun"].sum())
            / unrun_tot
            if unrun_tot > 0
            else 0.0
        )
    }

    return {
        "year": year,
        "class_unit_hours": int(len(cls)),
        "n_units": int(cls["unit_id"].nunique()),
        "object": obj,
        "P_b_price_is_the_dual": p_b,
        "P_c_capacity_basis": p_c,
        "P_d_where_the_unrun_MW_sits": p_d,
        "degeneracy_control": degeneracy,
        "ramp_signature": ramp,
        "STOP_2_4_identity_does_not_close": stop,
        "omega_all_rows": {
            "p50": _fmt(float(np.median(omega))),
            "p95": _fmt(float(np.percentile(omega, 95))),
            "share_nonzero": _fmt(float((np.abs(omega) > BASIS_EPS).mean())),
        },
    }


def reserve_overlay(bundle: Path, year: int, unrun_by_hour: pd.Series) -> dict:
    """Held reserve MW per hour vs the in-the-money un-run MW per hour.

    The shared-headroom row ``P[g,t] + R[g,t] <= cap[g,t]`` is the one armed
    mechanism that can cap an in-the-money column's ENERGY without any price
    signal, and nyiso-179's R2 could not see it: R2 tested a reserve family's
    balance-row DUAL, and reserve can be held at a zero dual. The committed
    ``reserve_family`` sidecar carries the held MW, so the occupancy test is
    available without a replay.
    """
    p = bundle / "hourly" / f"reserve_family_{year}.parquet"
    if not p.exists():
        return {"available": False}
    rf = pd.read_parquet(p)
    if "pass" in rf.columns:
        rf = rf[rf["pass"].astype(str) == "P1"]
    held_col = next((c for c in rf.columns if "held" in c.lower()), None)
    if held_col is None:
        return {"available": False, "reason": "no held-MW column"}
    held = rf.groupby("hour")[held_col].sum()
    j = pd.concat([held.rename("held"), unrun_by_hour.rename("unrun")], axis=1).dropna()
    if j.empty:
        return {"available": False, "reason": "no overlapping hours"}
    return {
        "available": True,
        "mean_held_mw": _fmt(float(j["held"].mean())),
        "mean_unrun_itm_mw": _fmt(float(j["unrun"].mean())),
        "held_over_unrun": _fmt(
            float(j["held"].mean() / j["unrun"].mean())
            if j["unrun"].mean() > 0
            else None
        ),
        "pearson_r": _fmt(float(j["held"].corr(j["unrun"]))),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    bundle = args.bundle if args.bundle.is_absolute() else REPO / args.bundle
    report: dict = {"bundle": str(bundle.relative_to(REPO)), "years": {}}
    for year in YEARS:
        df = _load_year(bundle, year)
        if df is None:
            report["years"][str(year)] = {"available": False}
            continue
        res = analyse_year(df, year)
        cls = df[_class_mask(df)]
        itm = cls["mc"].to_numpy(float) <= cls["price"].to_numpy(float)
        unrun_h = (
            cls.assign(
                _u=np.where(
                    itm,
                    np.maximum(
                        cls["cap_mw"].to_numpy(float) - cls["mw"].to_numpy(float), 0.0
                    ),
                    0.0,
                )
            )
            .groupby("hour")["_u"]
            .sum()
        )
        res["reserve_headroom_overlay"] = reserve_overlay(bundle, year, unrun_h)
        res["sidecar_bytes"] = (
            (bundle / "hourly" / f"unit_hourly_{year}.parquet").stat().st_size
        )
        report["years"][str(year)] = res

    out = args.out or (REPO / "results/calibration/_nyiso180_unit_dispatch.json")
    out.write_text(json.dumps(report, indent=2))
    json.dump(report, sys.stdout, indent=2)
    print(f"\n\nwrote {out}")


if __name__ == "__main__":
    main()
