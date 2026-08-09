"""miso-147 Q2 — the available / mispriced / absent trichotomy (PREREG §4.3).

Per fossil family x stratum x year: model capability AV_F (pmax x availability),
in-merit-at-the-REAL-price capability E_F (mc_base <= actual RT), dispatch M_F
(sidecar, NET) vs CAMPD states — ON gross, committed headroom HR_F, recallable
OFF_cyc_F (+-24 h), dark OFF_dark_F (whole month) — with the outage-CSV system
bound alongside (aggregate grain, never class-attributed).

Positive delta (model runs what reality didn't): legs (i)/(iii)/MIXED per the
pre-registered arithmetic. Negative delta (reality ran what the model didn't,
the composition probe's headline): availability-deficit iff AV_F < A_F, else
priced-out (E_F vs A_F — an offer object). Adjudicates PREREG P-2. Writes
``results/calibration/_miso147_headroom.json``.
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
    REPO,
    YEARS,
    bucket_series,
    campd_family_hourly,
    campd_units,
    c3a_weight,
    day_of_hoy,
    fam_of_klass,
    family_parasitic_factor,
    fleet_pack,
    floor_for,
    hygiene,
    outage_daily,
    parasitic_map,
    sidecar_pivot,
    strata,
    wmean,
)
from _miso137_c3a_gap_decomposition import actual_hourly  # noqa: E402

OUT = REPO / "results" / "calibration" / "_miso147_headroom.json"
RECALL_H = 24  # OFF_cyc: OFF in-hour but ON within +-24 h (PREREG §4.3)


def model_family_arrays(year: int) -> dict[str, dict[str, np.ndarray]]:
    """AV_F and E_F per family, (8760,) MW, from the cached fleet pack (no LP)."""
    fp = fleet_pack(year)
    rt, _ = actual_hourly(year)
    fam_map = fam_of_klass()
    kl = fp["klass"]
    cap = fp["pmax"][:, None] * fp["availability"]  # (n_gen, T)
    mc = fp["mc_base"]
    out: dict[str, dict[str, np.ndarray]] = {}
    for fam in FAMILY_TO_KLASSES:
        rows = np.array([fam_map.get(k) == fam for k in kl])
        c = cap[rows]
        inmerit = np.where(mc[rows] <= rt[None, :], c, 0.0)
        out[fam] = {"AV": c.sum(axis=0), "E": np.nan_to_num(inmerit).sum(axis=0),
                    "n_units": int(rows.sum())}
    return out


def campd_state_arrays(units: pd.DataFrame) -> dict[str, dict[str, np.ndarray]]:
    """ON / HR / OFF_cyc / OFF_dark per family, (8760,) MW GROSS (state readings)."""
    out: dict[str, dict[str, np.ndarray]] = {}
    mo_of_h = (day_of_hoy(np.arange(HOURS)) // 31)  # unused placeholder guard
    for fam in FAMILY_TO_KLASSES:
        g = units[units["family"] == fam]
        cap_u = g.groupby("unit")["gross"].quantile(0.99)
        cap95 = g.groupby("unit")["gross"].quantile(0.95)
        on = np.zeros(HOURS)
        hr = np.zeros(HOURS)
        hr95 = np.zeros(HOURS)
        off_cyc = np.zeros(HOURS)
        off_dark = np.zeros(HOURS)
        # per-unit dense series
        for unit, gu in g.groupby("unit", sort=False):
            v = np.zeros(HOURS)
            v[gu["hoy"].to_numpy(int)] = gu["gross"].to_numpy(float)
            cu, cu95 = float(cap_u[unit]), float(cap95[unit])
            is_on = v > 0
            on += np.where(is_on, v, 0.0)
            hr += np.where(is_on, np.maximum(0.0, cu - v), 0.0)
            hr95 += np.where(is_on, np.maximum(0.0, cu95 - v), 0.0)
            # recallable: OFF now, ON within +-RECALL_H
            k = 2 * RECALL_H + 1
            near_on = np.convolve(is_on.astype(float), np.ones(k), mode="same") > 0
            off_cyc += np.where(~is_on & near_on, cu, 0.0)
            # dark: OFF the entire calendar month
            mo = _month_of(np.arange(HOURS))
            on_months = set(np.unique(mo[is_on]).tolist())
            dark_m = ~np.isin(mo, sorted(on_months))
            off_dark += np.where(dark_m, cu, 0.0)
        out[fam] = {"ON": on, "HR": hr, "HR95": hr95, "OFF_cyc": off_cyc, "OFF_dark": off_dark}
    return out


def _month_of(hoy: np.ndarray) -> np.ndarray:
    from _miso143_stack import month_of_hour

    return month_of_hour(hoy)


def run() -> dict:
    hygiene()
    factors = parasitic_map()
    res: dict = {"session": "miso-147", "years": {}}
    for year in YEARS:
        s = strata(year)
        rt = s["rt"]
        piv = sidecar_pivot(year)
        w = c3a_weight(year)
        units, meta = campd_units(year)
        fam_net = campd_family_hourly(units, "net", factors)
        fam_pf = family_parasitic_factor(units, factors)
        states = campd_state_arrays(units)
        marr = model_family_arrays(year)
        outg = outage_daily(year)
        forced = (outg["MISO_Forced"] + outg["MISO_Unplanned"]).to_numpy(float)
        derated = outg["MISO_Derated"].to_numpy(float)
        planned = outg["MISO_Planned"].to_numpy(float)
        yblock: dict = {"campd_meta": meta}
        for sname, mask in s["masks"].items():
            days = np.unique(day_of_hoy(np.nonzero(mask)[0]))
            days = days[days < len(forced)]
            rows = {}
            for fam in FAMILY_TO_KLASSES:
                M = wmean(bucket_series(piv, FAMILY_TO_KLASSES[fam]), w, mask)
                A = wmean(fam_net[fam], w, mask)
                d = M - A
                fl = floor_for(A)
                pf = fam_pf[fam]
                AV = wmean(marr[fam]["AV"], w, mask)
                E = wmean(marr[fam]["E"], w, mask)
                ON = wmean(states[fam]["ON"], w, mask)
                HR = wmean(states[fam]["HR"], w, mask)
                HR95 = wmean(states[fam]["HR95"], w, mask)
                OFFc = wmean(states[fam]["OFF_cyc"], w, mask)
                OFFd = wmean(states[fam]["OFF_dark"], w, mask)
                row = {
                    "model_dispatch_M": round(M, 1),
                    "campd_net_A": round(A, 1),
                    "delta": round(d, 1),
                    "floor": round(fl, 1),
                    "material": bool(abs(d) >= fl),
                    "model_capability_AV": round(AV, 1),
                    "model_inmerit_at_actual_E": round(E, 1),
                    "model_units": marr[fam]["n_units"],
                    "campd_ON_gross": round(ON, 1),
                    "campd_HR_gross": round(HR, 1),
                    "campd_HR95_gross": round(HR95, 1),
                    "campd_OFFcyc_gross": round(OFFc, 1),
                    "campd_OFFdark_gross": round(OFFd, 1),
                    "family_pf": round(pf, 4),
                }
                if abs(d) >= fl:
                    if d > 0:
                        lim_i = (HR + OFFc) * pf
                        lim_iii = (HR + OFFc + OFFd) * pf
                        leg = (
                            "i_available_undispatched" if d <= lim_i
                            else ("iii_absent" if d > lim_iii else "MIXED")
                        )
                        row["legs"] = {
                            "verdict": leg,
                            "share_coverable_by_HR_OFFcyc": round(min(1.0, lim_i / d), 4),
                            "share_needing_OFFdark": round(max(0.0, (d - lim_i) / d), 4),
                        }
                    else:
                        # negative delta: reality ran what the model didn't
                        avail_deficit = AV < A
                        row["legs"] = {
                            "verdict": (
                                "availability_deficit" if avail_deficit else "priced_out"
                            ),
                            "AV_minus_A": round(AV - A, 1),
                            "E_minus_A": round(E - A, 1),
                            "E_share_of_A": round(E / A, 4) if A else None,
                            "undispatched_inmerit_capability": round(max(0.0, E - M), 1),
                        }
                rows[fam] = row
            yblock[sname] = {
                "rows": rows,
                "n_hours": int(mask.sum()),
                "outage_bound_mw_on_stratum_days": {
                    "forced_plus_unplanned_mean": round(float(forced[days].mean()), 1),
                    "derated_mean": round(float(derated[days].mean()), 1),
                    "planned_mean": round(float(planned[days].mean()), 1),
                    "grain": "MISO system daily; aggregate only, never class-attributed",
                },
                "basis_note": (
                    "M/A/delta NET; AV/E model-side NET-equivalent capability; "
                    "ON/HR/OFF_* CAMPD GROSS state readings, pf-scaled only inside leg tests"
                ),
            }
        res["years"][str(year)] = yblock
        del units
    # P-2 adjudication on the largest-|delta| material family in S1-2025
    s1 = res["years"]["2025"]["S1"]["rows"]
    mat = {f: r for f, r in s1.items() if r["material"]}
    largest = max(mat, key=lambda f: abs(mat[f]["delta"])) if mat else None
    p2: dict = {"largest_gap_family_S1_2025": largest}
    if largest:
        r = mat[largest]
        p2["delta"] = r["delta"]
        p2["legs"] = r.get("legs")
        if r["delta"] > 0:
            sh = r["legs"]["share_coverable_by_HR_OFFcyc"]
            p2["verdict"] = (
                "leg_i_dispatch_commitment" if sh >= 0.6
                else ("leg_iii_availability" if r["legs"]["share_needing_OFFdark"] >= 0.6 else "INDETERMINATE")
            )
        else:
            p2["verdict"] = r["legs"]["verdict"]
            p2["note"] = (
                "negative-delta branch (PREREG §4.3): the prior's positive direction "
                "did not obtain; adjudicated by the pre-registered negative-delta rule"
            )
    res["P2"] = p2
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    print("P-2:", json.dumps(r["P2"], indent=1))
    print(f"-> {OUT}")
