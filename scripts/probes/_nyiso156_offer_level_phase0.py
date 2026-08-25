#!/usr/bin/env python3
"""nyiso-156 phase 0 — the 2025 offer-level object re-measured on the hydro-repair keeper (no LP).

Implements the six declared measurements of
``PRECOMMIT-nyiso156-offer-level-phase0-2026-08-25.md`` §2 on committed
artifacts only: the two registered nyiso-155 bundles (a same-HEAD pair, so
arm−control is exactly the hydro repair) and the committed actuals.

M1  lw monthly face table (model vs ``rt_lw_mon``), control/arm, + arm−control
    delta by month — locates the ~$1.79 unmasking in the calendar.
M2  equal-hour vs load-weighted gap split — level miss vs high-load-hour miss.
M3  model−actual hub error by system-demand decile, per year and arm.
M4  nyiso-150 continuity: eqh zone errors, zonal gradient, winter zone-month
    tables, on control and arm.
M5  monthly hydro energy control vs arm (where the repair's TWh land).
M6  2025 event-window lw accounting (Jun 22–26, Jul 1/25/28–30, Jan/Feb/Dec).

Constructions (declared in the record):
- model hub hour h = Σ_z price(z,h)·demand(z,h) / Σ_z demand(z,h) over the
  five internal zones — the hourly analogue of the scorer's C3a model number
  (Σ p_z·d_z / Σ d_z), so the annual demand-weighted mean of this series must
  reproduce the recorded 61.04 / 59.24 (anchor check, tol $0.15).
- actual hub hour h = the committed ``actual_lmp_hourly_NYISO.parquet`` ``rt``
  (11-zone simple mean); its demand-weighted annual mean must reproduce
  ``rt_lw`` (66.43 for 2025).
- the eqh model hub uses the A–K constituent multiplicities (5,2,2,1,1)/11
  across model zones — the exact analogue of the actual hub's 11-zone simple
  mean (`iso_configs._nyiso_config`).

Report-class: exit 0 always — this reports, it does not gate.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CTRL = REPO / "results/calibration/nyiso155_hydro_control"
ARM = REPO / "results/calibration/nyiso155_hydro_repair"
REF = REPO / "data/raw/_validation-source/actual_lmp.json"
ACT_H = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
OUT = REPO / "results/calibration/_nyiso156_offer_level_phase0.json"

ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
# A–K constituent counts per model zone (iso_configs._nyiso_config: A–E, F–G,
# H–I, J, K) — the eqh hub analogue of the actual 11-zone simple mean.
HUB_W = np.array([5.0, 2.0, 2.0, 1.0, 1.0]) / 11.0
YEARS = (2023, 2024, 2025)
WINTER_MONTHS = (1, 2, 12)
SUMMER_MONTHS = (6, 7)
# 2025 event windows (nyiso-150 §1.3, extended to the lw basis here).
EVENT_DAYS_2025 = {
    "jun22_26_heat": [(6, d) for d in range(22, 27)],
    "jul_event_days": [(7, 1), (7, 25), (7, 28), (7, 29), (7, 30)],
}
# Recorded anchors (FINDING-nyiso-hydro-truncation-repair §4.4).
ANCHOR_LW = {"control": {2023: 33.96, 2024: 37.13, 2025: 61.04},
             "arm": {2023: 34.45, 2024: 37.46, 2025: 59.24}}
ANCHOR_TOL = 0.15


def _load_year(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """P1 price and demand as (hour × zone) frames for the internal zones."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["zone"].isin(ZONES))]
    price = df.pivot(index="hour", columns="zone", values="price")[ZONES]
    demand = df.pivot(index="hour", columns="zone", values="demand")[ZONES]
    return price, demand


def _cal(year: int) -> pd.DatetimeIndex:
    return pd.date_range(f"{year}-01-01", periods=8760, freq="h")


def _hub_series(price: pd.DataFrame, demand: pd.DataFrame) -> pd.Series:
    """Demand-weighted model hub per hour (the C3a-consistent construction)."""
    return (price * demand).sum(axis=1) / demand.sum(axis=1)


def _r2(x: float) -> float:
    return round(float(x), 2)


def main() -> None:
    ref = json.loads(REF.read_text())["NYISO"]
    act_h = pd.read_parquet(ACT_H)
    out: dict = {
        "session": "nyiso-156",
        "phase": 0,
        "precommit": "PRECOMMIT-nyiso156-offer-level-phase0-2026-08-25.md",
        "bundles": {"control": str(CTRL.name), "arm": str(ARM.name)},
        "zones": ZONES,
    }

    anchors: dict = {}
    m1: dict = {}
    m2: dict = {}
    m3: dict = {}
    m4: dict = {}
    m5: dict = {}
    m6: dict = {}

    for year in YEARS:
        cal = _cal(year)
        months = cal.month.values
        rt_hub = (
            act_h[act_h["year"] == year].set_index("hour")["rt"].reindex(range(8760))
        )
        yref = ref[str(year)]
        data = {}
        for name, bundle in (("control", CTRL), ("arm", ARM)):
            price, demand = _load_year(bundle, year)
            sysd = demand.sum(axis=1)
            hub = _hub_series(price, demand)
            data[name] = {"price": price, "demand": demand, "sysd": sysd, "hub": hub}

        # ── anchors: model lw vs recorded; actual lw vs committed rt_lw ──────
        sysd = data["control"]["sysd"]
        act_lw = float((rt_hub * sysd).sum() / sysd.sum())
        anchors[year] = {
            "actual_rt_lw_recomputed": _r2(act_lw),
            "actual_rt_lw_committed": yref["rt_lw"],
            "actual_anchor_ok": bool(abs(act_lw - yref["rt_lw"]) <= ANCHOR_TOL),
        }
        for name in ("control", "arm"):
            mod_lw = float(
                (data[name]["hub"] * data[name]["sysd"]).sum()
                / data[name]["sysd"].sum()
            )
            anchors[year][f"model_lw_{name}"] = _r2(mod_lw)
            anchors[year][f"model_lw_{name}_recorded"] = ANCHOR_LW[name][year]
            anchors[year][f"model_anchor_{name}_ok"] = bool(
                abs(mod_lw - ANCHOR_LW[name][year]) <= ANCHOR_TOL
            )

        # ── M1: lw monthly face table + arm−control delta ────────────────────
        tab: dict = {}
        for m in range(1, 13):
            sel = months == m
            row: dict = {"actual_rt_lw": yref["rt_lw_mon"][m - 1]}
            for name in ("control", "arm"):
                h, d = data[name]["hub"].values[sel], data[name]["sysd"].values[sel]
                row[name] = _r2((h * d).sum() / d.sum())
            row["arm_minus_control"] = _r2(row["arm"] - row["control"])
            row["arm_err"] = _r2(row["arm"] - row["actual_rt_lw"])
            tab[m] = row
        # each month's demand-share-weighted contribution to the annual lw
        # delta and to the annual lw gap (Σ over months = annual numbers).
        dshare = {
            m: float(sysd.values[months == m].sum() / sysd.values.sum())
            for m in range(1, 13)
        }
        m1[year] = {
            "months": tab,
            "demand_share": {m: round(dshare[m], 4) for m in dshare},
            "delta_contrib": {
                m: round(tab[m]["arm_minus_control"] * dshare[m], 3) for m in tab
            },
            "gap_contrib_arm": {
                m: round(tab[m]["arm_err"] * dshare[m], 3) for m in tab
            },
        }

        # ── M2: eqh vs lw split ─────────────────────────────────────────────
        eqh_act = yref["rt"]
        m2[year] = {"actual_eqh": eqh_act, "actual_lw": yref["rt_lw"]}
        for name in ("control", "arm"):
            eqh_hub = float((data[name]["price"].values * HUB_W).sum(axis=1).mean())
            eqh_5z = float(data[name]["price"].values.mean())
            lw = anchors[year][f"model_lw_{name}"]
            m2[year][name] = {
                "model_eqh_hub": _r2(eqh_hub),
                "model_eqh_5zone_mean": _r2(eqh_5z),
                "model_lw": lw,
                "eqh_gap": _r2(eqh_hub - eqh_act),
                "lw_gap": _r2(lw - yref["rt_lw"]),
                "covariance_term": _r2((lw - yref["rt_lw"]) - (eqh_hub - eqh_act)),
            }

        # ── M3: error by system-demand decile ───────────────────────────────
        dec = pd.qcut(sysd, 10, labels=False)
        m3[year] = {}
        for name in ("control", "arm"):
            err = data[name]["hub"] - rt_hub.values
            prof = [
                _r2(err[dec == i].mean()) for i in range(10)
            ]
            # demand-weighted contribution of each decile to the annual lw gap
            contrib = [
                round(
                    float((err[dec == i] * sysd[dec == i]).sum() / sysd.sum()), 3
                )
                for i in range(10)
            ]
            m3[year][name] = {
                "mean_err_by_decile": prof,
                "lw_gap_contrib_by_decile": contrib,
            }

        # ── M4: nyiso-150 continuity (eqh zone errors, gradient, winter) ─────
        act_z = yref["zones"]
        m4[year] = {}
        for name in ("control", "arm"):
            price = data[name]["price"]
            ann = price.mean(axis=0)
            m4[year][name] = {
                "zones": {
                    z: {
                        "model_eqh": _r2(ann[z]),
                        "actual_rt": act_z[z]["rt"],
                        "err_pct": round(
                            100 * (float(ann[z]) - act_z[z]["rt"]) / act_z[z]["rt"], 1
                        ),
                    }
                    for z in ZONES
                },
                "gradient_model": _r2(ann.max() - ann.min()),
                "gradient_actual": _r2(
                    max(act_z[z]["rt"] for z in ZONES)
                    - min(act_z[z]["rt"] for z in ZONES)
                ),
            }
        wtab: dict = {}
        for m in WINTER_MONTHS:
            sel = months == m
            row = {}
            for z in ZONES:
                row[z] = {
                    "control": _r2(data["control"]["price"][z].values[sel].mean()),
                    "arm": _r2(data["arm"]["price"][z].values[sel].mean()),
                    "actual": act_z[z]["rt_mon"][m - 1],
                }
            wtab[m] = row
        m4[year]["winter_zone_months"] = wtab

        # ── M5: monthly hydro energy, control vs arm ────────────────────────
        hyd = {}
        for name, bundle in (("control", CTRL), ("arm", ARM)):
            cl = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
            cl = cl[(cl["pass"] == "P1") & (cl["klass"] == "hydro")]
            hw = cl.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0.0)
            hyd[name] = np.array(
                [hw.values[months == m].sum() / 1e6 for m in range(1, 13)]
            )
        m5[year] = {
            "control_twh": [round(float(x), 4) for x in hyd["control"]],
            "arm_twh": [round(float(x), 4) for x in hyd["arm"]],
            "delta_twh": [round(float(x), 4) for x in hyd["arm"] - hyd["control"]],
            "annual_delta_twh": round(float((hyd["arm"] - hyd["control"]).sum()), 4),
        }

        # ── M6: event-window lw accounting (2025 only) ──────────────────────
        if year == 2025:
            windows: dict[str, np.ndarray] = {
                f"month_{m:02d}": months == m for m in WINTER_MONTHS + SUMMER_MONTHS
            }
            md = list(zip(cal.month.values, cal.day.values))
            for wname, days in EVENT_DAYS_2025.items():
                windows[wname] = np.array([t in days for t in md])
            for wname, sel in windows.items():
                row = {"hours": int(sel.sum())}
                for name in ("control", "arm"):
                    err = data[name]["hub"].values[sel] - rt_hub.values[sel]
                    d = sysd.values[sel]
                    row[name] = {
                        "model_lw": _r2(
                            (data[name]["hub"].values[sel] * d).sum() / d.sum()
                        ),
                        "actual_lw": _r2((rt_hub.values[sel] * d).sum() / d.sum()),
                        # window contribution to the ANNUAL lw gap, $/MWh
                        "annual_lw_gap_contrib": round(
                            float((err * d).sum() / sysd.values.sum()), 3
                        ),
                    }
                m6[wname] = row

    out["anchors"] = anchors
    out["m1_lw_monthly"] = m1
    out["m2_eqh_vs_lw"] = m2
    out["m3_demand_decile"] = m3
    out["m4_zonal_continuity"] = m4
    out["m5_hydro_monthly"] = m5
    out["m6_event_windows_2025"] = m6

    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    for year in YEARS:
        a = anchors[year]
        print(
            f"{year}: anchors ok={a['actual_anchor_ok']}/{a['model_anchor_control_ok']}"
            f"/{a['model_anchor_arm_ok']} "
            f"(act {a['actual_rt_lw_recomputed']} vs {a['actual_rt_lw_committed']}; "
            f"ctl {a['model_lw_control']} vs {a['model_lw_control_recorded']}; "
            f"arm {a['model_lw_arm']} vs {a['model_lw_arm_recorded']})"
        )
        g = m2[year]
        print(
            f"  eqh gap ctl {g['control']['eqh_gap']:+.2f} arm {g['arm']['eqh_gap']:+.2f} | "
            f"lw gap ctl {g['control']['lw_gap']:+.2f} arm {g['arm']['lw_gap']:+.2f} | "
            f"cov arm {g['arm']['covariance_term']:+.2f}"
        )


if __name__ == "__main__":
    main()
