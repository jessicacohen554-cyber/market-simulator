"""miso-147 Q3 + Q4 drivers — January 2025 opened, May reversal drivers (PREREG §4.5).

Five candidate measurements for the January-2025 tail (16 hours), each reported
for ALL 12 months and both signs (TRAP 8), plus the S0 (May) driver block and
the month-resolved AV_CC - A_CC series that tests whether the CC availability
deficit is summer-concentrated (the miso-141 connection). Candidates are NAMED,
never armed.

Writes ``results/calibration/_miso147_january.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _miso147_strata import (  # noqa: E402
    FAMILY_TO_KLASSES,
    HOURS,
    KEEPER,
    REPO,
    TAIL_USD,
    YEARS,
    bucket_series,
    campd_family_hourly,
    campd_units,
    c3a_weight,
    day_of_hoy,
    e930_demand,
    fam_of_klass,
    fleet_pack,
    hygiene,
    month_of_hour,
    outage_daily,
    parasitic_map,
    sidecar_pivot,
    strata,
    wmean,
)

OUT = REPO / "results" / "calibration" / "_miso147_january.json"
GAS_KLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")


def monthly(series: np.ndarray, w: np.ndarray, valid: np.ndarray) -> list[float]:
    mo = month_of_hour(np.arange(HOURS))
    return [round(wmean(series, w, valid & (mo == m)), 1) for m in range(1, 13)]


def candidate_tables(year: int) -> dict:
    """The x12-month candidate diagnostics for one year (TRAP 8)."""
    s = strata(year)
    rt, valid = s["rt"], s["valid"]
    w = c3a_weight(year)
    mo = month_of_hour(np.arange(HOURS))
    fp = fleet_pack(year)
    fam_map = fam_of_klass()
    kl = fp["klass"]
    thermal = np.array([k in fam_map for k in kl])
    cap_full = fp["pmax"][:, None] * np.ones((1, HOURS))
    avail_cap = fp["pmax"][:, None] * fp["availability"]
    # model implied thermal outage take, (8760,)
    model_out = (cap_full[thermal] - avail_cap[thermal]).sum(axis=0)
    # AV per family
    av = {
        fam: avail_cap[np.array([fam_map.get(k) == fam for k in kl])].sum(axis=0)
        for fam in FAMILY_TO_KLASSES
    }
    units, _meta = campd_units(year)
    fam_net = campd_family_hourly(units, "net", parasitic_map())
    # real outage CSV daily -> hourly step series
    outg = outage_daily(year)
    forced_d = (outg["MISO_Forced"] + outg["MISO_Unplanned"]).to_numpy(float)
    derated_d = outg["MISO_Derated"].to_numpy(float)
    planned_d = outg["MISO_Planned"].to_numpy(float)
    dd = np.clip(day_of_hoy(np.arange(HOURS)), 0, len(forced_d) - 1)
    forced_h, derated_h, planned_h = forced_d[dd], derated_d[dd], planned_d[dd]
    piv = sidecar_pivot(year)

    tab = {
        "AV_CC_minus_A_CC": monthly(av["CC"] - fam_net["CC"], w, valid),
        "M_CC_minus_A_CC": monthly(
            bucket_series(piv, FAMILY_TO_KLASSES["CC"]) - fam_net["CC"], w, valid
        ),
        "model_implied_thermal_outage": monthly(model_out, w, np.ones(HOURS, bool)),
        "real_forced_plus_unplanned": monthly(forced_h, w, np.ones(HOURS, bool)),
        "real_derated": monthly(derated_h, w, np.ones(HOURS, bool)),
        "real_planned": monthly(planned_h, w, np.ones(HOURS, bool)),
        "outage_gap_model_minus_real_forced": monthly(
            model_out - forced_h, w, np.ones(HOURS, bool)
        ),
        "demand_control_sidecar_minus_930": monthly(
            w - e930_demand(year), np.ones(HOURS), np.ones(HOURS, bool)
        ),
        "note": (
            "columns Jan..Dec; C3a-weighted month means; model_implied_thermal_outage = "
            "sum pmax*(1-availability) over fossil rows; real_* from the MISO outage CSV "
            "(system grain, ALL fuel incl. non-fossil — an upper bound, never class-attributed)"
        ),
    }
    del units
    return tab, s, fam_net, av, model_out, (forced_h, derated_h, planned_h)


def january_2025(s, fam_net, av, model_out, real_out, year: int = 2025) -> dict:
    """The January-2025 tail block: operating states + the five candidates."""
    rt, valid = s["rt"], s["valid"]
    mo = month_of_hour(np.arange(HOURS))
    w = c3a_weight(year)
    jan = valid & (mo == 1)
    tail = jan & (rt > TAIL_USD)
    ntail = jan & (rt <= TAIL_USD)
    forced_h, derated_h, planned_h = real_out
    piv = sidecar_pivot(year)
    fp = fleet_pack(year)
    fam_map = fam_of_klass()
    kl = fp["klass"]

    units, _ = campd_units(year)
    out: dict = {"n_tail_hours": int(tail.sum())}
    # 1. operating states per family, tail vs non-tail
    states = {}
    for fam in FAMILY_TO_KLASSES:
        g = units[(units["family"] == fam) & (units["gross"] > 0)]
        on_mw = np.zeros(HOURS)
        np.add.at(on_mw, g["hoy"].to_numpy(int), g["gross"].to_numpy(float))
        n_on_tail = int(g.loc[np.isin(g["hoy"].to_numpy(int), np.nonzero(tail)[0]), "unit"].nunique())
        states[fam] = {
            "campd_ON_gross_tail": round(wmean(on_mw, w, tail), 1),
            "campd_ON_gross_jan_nontail": round(wmean(on_mw, w, ntail), 1),
            "campd_units_on_tail": n_on_tail,
            "model_M_tail": round(wmean(bucket_series(piv, FAMILY_TO_KLASSES[fam]), w, tail), 1),
            "model_AV_tail": round(wmean(av[fam], w, tail), 1),
            "campd_A_net_tail": round(wmean(fam_net[fam], w, tail), 1),
        }
    out["operating_states"] = states
    # 2. forced outage vs model availability, tail days
    out["outage_vs_availability_tail"] = {
        "real_forced_plus_unplanned": round(wmean(forced_h, w, tail), 1),
        "real_derated": round(wmean(derated_h, w, tail), 1),
        "model_implied_thermal_outage": round(wmean(model_out, w, tail), 1),
        "gap_model_minus_real_forced": round(wmean(model_out - forced_h, w, tail), 1),
    }
    # 3. gas marginal-cost distribution in tail hours (citygate overlay ARMED, §2(f))
    gas_rows = np.isin(kl, GAS_KLASSES)
    mc_gas = fp["mc_base"][gas_rows][:, np.nonzero(tail)[0]].astype(float)
    cap_gas = (fp["pmax"][:, None] * fp["availability"])[gas_rows][:, np.nonzero(tail)[0]]
    m = cap_gas > 0
    out["gas_mc_in_tail_hours"] = {
        "p10_p50_p90": [round(float(np.percentile(mc_gas[m], q)), 2) for q in (10, 50, 90)],
        "capacity_weighted_mean": round(float((mc_gas * cap_gas).sum() / cap_gas.sum()), 2),
        "annual_gas_mc_p50_all_hours": round(float(np.percentile(
            fp["mc_base"][gas_rows][(fp["pmax"][:, None] * fp["availability"])[gas_rows] > 0], 50)), 2),
        "note": "keeper mc_base (P0 objective) — winter citygate + dual-fuel overlays ARMED",
    }
    # 4. dual-fuel proxy: oil-capable gas units ON in tail hours (CAMPD fuel strings)
    fuel = _jan_fuel_states(year, tail)
    out["dual_fuel_proxy"] = fuel
    # 5. winter reserve binding in tail hours
    rf = pd.read_parquet(KEEPER / "hourly" / f"reserve_family_{year}.parquet")
    if "pass" in rf:
        rf = rf[rf["pass"].astype(str).str.upper() == "P1"]
    tail_h = set(np.nonzero(tail)[0].tolist())
    rft = rf[rf["hour"].isin(tail_h)]
    out["winter_reserve_tail"] = {
        fam: {
            "dual_mean": round(float(g["dual"].mean()), 3),
            "dual_max": round(float(g["dual"].max()), 3),
            "shortfall_mw_max": round(float(g["shortfall_mw"].max()), 1),
            "held_mw_mean": round(float(g["held_mw"].mean()), 1),
        }
        for fam, g in rft.groupby("family")
    }
    del units
    return out


def _jan_fuel_states(year: int, tail: np.ndarray) -> dict:
    """CAMPD oil-capable vs gas-only unit ON states in the tail hours (proxy)."""
    from market_sim.data import campd as campd_mod
    from market_sim.data.zone_assignment import build_zone_lookup

    zones = build_zone_lookup("MISO")
    tail_hours = set(np.nonzero(tail)[0].tolist())
    rows = {"oil_capable_gas": {"on": 0.0, "units": set()},
            "gas_only": {"on": 0.0, "units": set()},
            "oil_primary": {"on": 0.0, "units": set()}}
    for st in campd_mod.states_for_iso("MISO"):
        df = pd.read_parquet(
            REPO / "data" / "raw" / "campd-unit-level" / f"{st}_{year}.parquet",
            columns=["facilityId", "unitId", "date", "hour", "grossLoad", "primaryFuelInfo"],
        )
        df = df[pd.to_datetime(df["date"]).dt.month == 1]
        if df.empty:
            continue
        fac = pd.to_numeric(df["facilityId"], errors="coerce").fillna(-1).astype(int)
        df = df[fac.isin(zones)]
        if df.empty:
            continue
        dt = pd.to_datetime(df["date"])
        hoy = campd_mod._hour_index_8760(dt.dt.month.to_numpy(), dt.dt.day.to_numpy(), df["hour"].to_numpy())
        df = df.assign(hoy=hoy)
        df = df[df["hoy"].isin(tail_hours) & (df["grossLoad"].fillna(0) > 0)]
        if df.empty:
            continue
        f = df["primaryFuelInfo"].astype(str).str.lower()
        oilcap = f.str.contains("oil") & f.str.contains("gas")
        oilpri = f.str.startswith(("diesel", "residual", "distillate")) | (
            f.str.contains("oil") & ~f.str.contains("gas")
        )
        gasonly = f.str.contains("gas") & ~f.str.contains("oil")
        key = df["facilityId"].astype(str) + ":" + df["unitId"].astype(str)
        for name, mask in (("oil_capable_gas", oilcap), ("oil_primary", oilpri), ("gas_only", gasonly)):
            rows[name]["on"] += float(df.loc[mask, "grossLoad"].sum())
            rows[name]["units"].update(key[mask].unique())
    n_tail = max(1, len(tail_hours))
    return {
        k: {"mean_on_gross_mw": round(v["on"] / n_tail, 1), "n_units_on": len(v["units"])}
        for k, v in rows.items()
    } | {"note": "proxy — CAMPD has no hourly fuel-switch field (PREREG §4.5.4)"}


def run() -> dict:
    hygiene()
    res: dict = {"session": "miso-147", "monthly_tables": {}, "january_2025": None, "S0_drivers": None}
    keep = {}
    for year in YEARS:
        tab, s, fam_net, av, model_out, real_out = candidate_tables(year)
        res["monthly_tables"][str(year)] = tab
        if year == 2025:
            keep = dict(s=s, fam_net=fam_net, av=av, model_out=model_out, real_out=real_out)
    res["january_2025"] = january_2025(keep["s"], keep["fam_net"], keep["av"],
                                       keep["model_out"], keep["real_out"])
    # S0 driver block: May availability take, model vs real (both signs, x12 already above)
    t25 = res["monthly_tables"]["2025"]
    res["S0_drivers"] = {
        "may_model_implied_thermal_outage": t25["model_implied_thermal_outage"][4],
        "may_real_forced_plus_unplanned": t25["real_forced_plus_unplanned"][4],
        "may_real_planned": t25["real_planned"][4],
        "may_real_derated": t25["real_derated"][4],
        "may_AV_CC_minus_A_CC": t25["AV_CC_minus_A_CC"][4],
        "note": "May = column 5 of the x12 tables; the spring-maintenance comparison",
    }
    # P-5 adjudication (reported, not gating)
    j = res["january_2025"]["outage_vs_availability_tail"]
    res["P5_reported"] = {
        "real_forced_exceeds_model_by": round(j["real_forced_plus_unplanned"] - j["model_implied_thermal_outage"], 1),
        "bar_2000mw": bool(j["real_forced_plus_unplanned"] - j["model_implied_thermal_outage"] >= 2000.0),
        "caveat": "real side is ALL-fuel system grain (upper bound); model side fossil-only",
    }
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    print("Jan-2025 tail:", r["january_2025"]["n_tail_hours"], "h")
    print("outage vs availability (tail):", r["january_2025"]["outage_vs_availability_tail"])
    print("P-5:", r["P5_reported"])
    print("S0 drivers:", r["S0_drivers"])
    print(f"-> {OUT}")
