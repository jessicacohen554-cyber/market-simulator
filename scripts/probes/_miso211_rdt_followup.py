"""miso-211 follow-up — two disclosed instrument corrections to the phase-0 record.

Written AFTER the first pass of ``_miso211_rdt_binding_state.py`` and recorded
under ``post_hoc`` in the same JSON (the miso-186 §7 pattern: corrections
committed with their own disclosure, no threshold moved).

1. **R-2b/R-2c South generation basis.** The first pass read the model's South
   generation from ``hourly/unit_hourly_<year>.parquet``, which carries only
   the thermal/hydro/nuclear UNITS — the LP's zonal wind/solar decision
   variables and the biomass/OTHER/oil bins are absent from it. That made the
   model's South solar read 0.0 GW against 1.95 GW measured and left the
   R-2c balance identity a 1–4 GW residual. Re-computed here from the
   zone-resolved ``dispatch/<year>_P1.parquet`` (every klass, incl.
   ``SOLAR_MISO-South`` / ``WIND_MISO-South``).
2. **R-3b RDT-attributable ceiling.** The first pass's separation ceiling uses
   the WHOLE measured Indiana−South-hubs separation; the RDT's own price is the
   PBC shadow, so the RDT-ATTRIBUTABLE part of that separation is bounded by
   |shadow| (unit shift factor across a corridor constraint). Reported here as
   ``lift = max(0, min(measured_sep, |shadow|) − model_spread)``, beside the
   whole-separation number. Neither replaces the other; both are reported.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso211_rdt_followup.py
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
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso211_rdt_binding_state as p  # noqa: E402  (re-points to the miso-210 keeper)

HOURS = p.HOURS
KLASS_FAMILY = {
    "COAL": "Coal",
    "CC_": "Gas",
    "CT_": "Gas",
    "ST_GAS": "Gas",
    "ST_CHP": "Gas",
    "nuclear": "Nuclear",
    "hydro": "Hydro",
    "wind": "Wind",
    "solar": "Solar",
}


def _fam(klass: str) -> str:
    k = str(klass)
    for key, fam in KLASS_FAMILY.items():
        if k.startswith(key) or k == key:
            return fam
    return "Other"  # biomass, OTHER, oil


def south_dispatch_by_family(year: int) -> tuple[dict[str, np.ndarray], np.ndarray]:
    d = pd.read_parquet(
        p.KEEPER / f"dispatch/{year}_P1.parquet",
        columns=["klass", "zone", "hour", "mw"],
    )
    d = d[d["zone"] == "MISO-South"]
    d = d.assign(fam=d["klass"].astype(str).map(_fam))
    by = (
        d.groupby(["fam", "hour"])["mw"]
        .sum()
        .unstack("fam")
        .reindex(range(HOURS))
        .fillna(0.0)
    )
    return {c: by[c].to_numpy(float) for c in by.columns}, by.sum(axis=1).to_numpy(
        float
    )


def main() -> None:
    rec = json.loads(p.OUT.read_text())
    mon = p.m207._hour_month()
    jj = np.where(np.isin(mon, (6, 7)))[0]
    hod = np.arange(HOURS) % 24
    post: dict = {
        "disclosure": (
            "Computed AFTER the first pass. (1) unit_hourly omits the LP's zonal wind/solar "
            "variables and the biomass/OTHER/oil bins, so the first-pass R-2b by-fuel table "
            "read model South solar as 0.0 and R-2c left a residual; re-computed from the "
            "zone-resolved dispatch parquet. (2) R-3b adds the RDT-attributable (shadow-"
            "bounded) ceiling beside the whole-separation one. No threshold changed."
        ),
        "years": {},
    }
    fams_all = ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other")
    for year in p.YEARS:
        price, lw, dem_s, slack_s = p.zone_prices(year)
        ind_act, south_act = p.actual_hubs(year)
        cor = p.corridor(year)
        pbc = p.pbc_hourly(year, "RDT_SO_MW")
        a = ind_act[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        other = np.array(sorted(set(jj) - set(shoulder) - set(tail)))
        day_other = other[np.isin(hod[other], range(10, 21))]
        pops = {"SHOULDER": shoulder, "TAIL": tail, "OTHER_DAYTIME": day_other}
        gaps = {k: p._m(lw, v) - p._m(ind_act, v) for k, v in pops.items()}

        fams_model, gen_model = south_dispatch_by_family(year)
        stor = p.south_storage_net(year)
        inflow = cor["n2s_flow"] - cor["s2n_flow"] + cor["ext_south_flow"]
        resid = dem_s - gen_model - stor - slack_s - inflow
        load_s = p.regional_series(year, "load", "South")
        gen_s = p.regional_series(year, "gen", "South")
        meas_ns = load_s - gen_s
        fam_meas = {
            f: p.regional_series(year, "gen", "South", fuel=f) for f in fams_all
        }
        spread = price["MISO-Indiana"].to_numpy() - price["MISO-South"].to_numpy()
        meas_sep = ind_act - south_act
        y: dict = {
            "r2c_identity_full_dispatch": {
                "max_abs_residual_mw": round(float(np.nanmax(np.abs(resid))), 3),
                "mean_abs_residual_mw": round(float(np.nanmean(np.abs(resid))), 3),
                "holds_under_1mw": bool(np.nanmax(np.abs(resid)) < 1.0),
            },
            "r2b_full_dispatch": {},
            "r3b_shadow_bounded": {},
        }
        for k, idx in pops.items():
            rb = idx[pbc["any"][idx]]
            y["r2b_full_dispatch"][k] = {
                "hours_real_s2n": int(rb.size),
                "measured_south_net_intake_gw": round(p._m(meas_ns, rb) / 1e3, 3),
                "model_south_net_inflow_gw": round(p._m(inflow, rb) / 1e3, 3),
                "gap_model_minus_measured_gw": round(
                    (p._m(inflow, rb) - p._m(meas_ns, rb)) / 1e3, 3
                ),
                "south_load_gw": {
                    "measured": round(p._m(load_s, rb) / 1e3, 3),
                    "model": round(p._m(dem_s, rb) / 1e3, 3),
                },
                "south_gen_total_gw": {
                    "measured": round(p._m(gen_s, rb) / 1e3, 3),
                    "model": round(p._m(gen_model, rb) / 1e3, 3),
                },
                "by_fuel_gw_model_minus_measured": {
                    f: round(
                        (
                            p._m(fams_model.get(f, np.zeros(HOURS)), rb)
                            - np.nan_to_num(p._m(fam_meas[f], rb))
                        )
                        / 1e3,
                        3,
                    )
                    for f in fams_all
                },
                "by_fuel_gw_model": {
                    f: round(p._m(fams_model.get(f, np.zeros(HOURS)), rb) / 1e3, 3)
                    for f in fams_all
                },
                "by_fuel_gw_measured": {
                    f: round(np.nan_to_num(p._m(fam_meas[f], rb)) / 1e3, 3)
                    for f in fams_all
                },
                "generation_term_share_of_gap": (
                    round(
                        (
                            (p._m(gen_s, rb) - p._m(gen_model, rb))
                            / (p._m(inflow, rb) - p._m(meas_ns, rb))
                        )
                        if (p._m(inflow, rb) - p._m(meas_ns, rb))
                        else float("nan"),
                        3,
                    )
                ),
            }
            rbm = pbc["any"][idx]
            bounded = np.minimum(
                np.nan_to_num(meas_sep[idx]), pbc["mean_abs_shadow"][idx]
            )
            lift_b = np.where(rbm, np.maximum(0.0, bounded - spread[idx]), 0.0)
            lift_w = np.where(
                rbm, np.maximum(0.0, np.nan_to_num(meas_sep[idx]) - spread[idx]), 0.0
            )
            gap = gaps[k]
            y["r3b_shadow_bounded"][k] = {
                "lift_shadow_bounded_usd_mean": round(float(lift_b.mean()), 3),
                "share_shadow_bounded": round(float(lift_b.mean()) / abs(gap), 4)
                if gap
                else None,
                "lift_whole_separation_usd_mean": round(float(lift_w.mean()), 3),
                "share_whole_separation": round(float(lift_w.mean()) / abs(gap), 4)
                if gap
                else None,
                "mean_abs_shadow_in_binding_hours": round(
                    p._m(pbc["mean_abs_shadow"], idx[rbm]), 3
                ),
                "reaches_25pct_shadow_bounded": bool(
                    gap and float(lift_b.mean()) / abs(gap) >= p.LICENSE
                ),
            }
        post["years"][year] = y
        print(year, "R-2c full", y["r2c_identity_full_dispatch"])
        print(
            year,
            "R-2b shoulder full",
            json.dumps(y["r2b_full_dispatch"]["SHOULDER"], default=str)[:900],
        )
        print(
            year,
            "R-3b shadow-bounded",
            json.dumps(y["r3b_shadow_bounded"], default=str)[:700],
        )
    rec["post_hoc"] = post
    p.OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(f"updated {p.OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
