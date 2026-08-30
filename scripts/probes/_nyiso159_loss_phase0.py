#!/usr/bin/env python3
"""nyiso-159 phase-0: measure the LOSS component of the NYISO zonal price
surface on the completed 2023-2025 RT component record — no solve.

Session nyiso-159, step 1b of the handoff. The nyiso-158 finding measured (on
the 8 then-committed months + 2022) that the real CH-UW spread decomposes on
NYISO's own posted LBMP components as ``dTotal = dLoss - dCong`` and that the
LOSS part alone is a permanent additive downstate premium the model's lossless
internal links omit in EVERY hour. This probe re-measures that object on the
COMPLETED 36-month 2023-2025 series (intaken this session via the frozen
``scripts/data/fetch_nyiso_zonal_lmp.py`` + ``scripts/data/curate_lmp.py``
route) and derives the identification the ``nyiso_zonal_loss_surface``
mechanism would consume:

1. **Contract checks** — coverage (36/36 zone-months), the posted identity
   ``LBMP = E + MCL - MCC`` (cross-zone uniformity of the recovered reference
   energy price E), and the to-the-cent spread identity.
2. **Model-zone monthly component table** — mean LBMP / MCL / MCC per model
   zone (simple mean of member A-K zones, the SAME aggregation the scoring
   actuals use: ``derive_actual_lmp.NYISO_ZONE_MAP`` + ``nyiso_zone_hourly``),
   and each downstate zone's spread vs Upstate_West split into loss / cong.
3. **The identification** — per-zone monthly delivery-factor deviations
   ``dev_z,m = sum(MCL_z)/sum(E)``, the SAME frozen estimator the
   MISO/PJM/CAISO loss surfaces use, computed from NYISO's OWN posted
   components only (rule 25 [R-ISO-SCOPE]; never the price residual).
4. **Rubric-face loss shares** — for each C3a/C3b failure face month
   (Jan/Feb/Jun/Jul-2025, the nyiso-158 two-face object) and for the annual
   gradient of all three years: the measured load-weighted downstate loss
   premium vs the face miss, i.e. how much of each face is the loss FLOOR
   (honest P3: losses are NOT predicted to close the object months, where
   congestion dominates).
5. **Named adverse cases** — the same LW loss premium for 2023 (C3a-2023
   sits +1.0 with the +10 band above) and the Upstate_West annual level
   (C3a-2025 upstate near-exact; the surface must not relocate error upstate).

Inputs (all committed/regenerable, no model output consumed as an answer):
  data/clean/lmp/NYISO/RTM/lmp_<year>.parquet   (curated posted components)
  results/calibration/nyiso157_pararm_B/hourly/system_<year>.parquet
      (keeper zonal duals + zonal demand -- demand used ONLY as LW weights,
       prices used ONLY as the model-side gradient context)
  frontend/data/backcast/bench/NYISO/<year>.json.gz  (scorer actual LW targets)

Output: ``results/calibration/_nyiso159_loss_phase0.json``.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data" / "clean" / "lmp" / "NYISO" / "RTM"
KEEPER = ROOT / "results" / "calibration" / "nyiso157_pararm_B"
BENCH = ROOT / "frontend" / "data" / "backcast" / "bench" / "NYISO"
OUT = ROOT / "results" / "calibration" / "_nyiso159_loss_phase0.json"

YEARS = (2023, 2024, 2025)

# The scoring crosswalk (derive_actual_lmp.NYISO_ZONE_MAP) and its simple-mean
# aggregation (nyiso_zone_hourly) — the model zone's actual price IS the simple
# mean of its members, so the loss identification must aggregate identically.
ZONE_MAP: dict[str, list[str]] = {
    "Upstate_West": ["WEST", "GENESE", "CENTRL", "NORTH", "MHK VL"],
    "Capital_Hudson": ["CAPITL"],
    "Lower_Hudson": ["HUD VL", "MILLWD", "DUNWOD"],
    "NYC": ["N.Y.C."],
    "Long_Island": ["LONGIL"],
}
INTERNAL = [m for ms in ZONE_MAP.values() for m in ms]
DOWNSTATE = ["Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
FACE_MONTHS_2025 = (1, 2, 6, 7)  # nyiso-158 §2: 98.4 % of C3b-2025 sq error


def _zone_hourly(year: int) -> dict[str, pd.DataFrame]:
    """Model-zone hourly component frames {lbmp, mcl, mcc, e} for ``year``.

    Wide frames indexed by UTC hour with one column per model zone (simple
    member mean), plus ``e`` — the recovered reference energy price
    ``E = LBMP - MCL + MCC`` (identical across zones up to publication
    rounding; the cross-zone spread is measured and reported, not assumed).
    """
    df = pd.read_parquet(CLEAN / f"lmp_{year}.parquet")
    df = df[df.zone.isin(INTERNAL)].copy()
    local = pd.to_datetime(df.interval_start_local)
    df["month"] = local.dt.month
    piv = {
        c: df.pivot_table(index="interval_start_utc", columns="zone", values=c)
        for c in ("lmp_usd_per_mwh", "loss_usd_per_mwh", "congestion_usd_per_mwh")
    }
    e_by_zone = (
        piv["lmp_usd_per_mwh"]
        - piv["loss_usd_per_mwh"]
        + piv["congestion_usd_per_mwh"]
    )
    month = (
        df.drop_duplicates("interval_start_utc")
        .set_index("interval_start_utc")["month"]
        .sort_index()
    )
    out: dict[str, pd.DataFrame] = {}
    for name, wide in (
        ("lbmp", piv["lmp_usd_per_mwh"]),
        ("mcl", piv["loss_usd_per_mwh"]),
        ("mcc", piv["congestion_usd_per_mwh"]),
    ):
        out[name] = pd.DataFrame(
            {z: wide[ms].mean(axis=1) for z, ms in ZONE_MAP.items()}
        )
    out["e"] = pd.DataFrame({"e": e_by_zone.mean(axis=1)})
    out["e_cross_zone_spread"] = pd.DataFrame(
        {"spread": e_by_zone.max(axis=1) - e_by_zone.min(axis=1)}
    )
    out["month"] = month
    return out


def _keeper_frames(year: int) -> pd.DataFrame:
    """Keeper P1 zonal duals + demand, wide by zone, hour-indexed."""
    df = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    price = df.pivot_table(index="hour", columns="zone", values="price")
    demand = df.pivot_table(index="hour", columns="zone", values="demand")
    return price, demand


def main() -> None:
    out: dict = {
        "session": "nyiso-159",
        "phase": "phase-0 loss-component identification (no solve)",
        "keeper": "2026-08-30-nyiso-157-par-attribution",
        "no_solve": True,
        "years": list(YEARS),
        "constructions": {
            "source": "data/clean/lmp/NYISO/RTM/lmp_<yr>.parquet — NYISO MIS "
            "P-24A 5-min RT zonal LBMP, hourly means, curated by the frozen "
            "scripts/data/curate_lmp.py contract; 36/36 months intaken "
            "nyiso-159 via scripts/data/fetch_nyiso_zonal_lmp.py",
            "aggregation": "model zone = SIMPLE MEAN of member A-K zones "
            "(derive_actual_lmp.NYISO_ZONE_MAP / nyiso_zone_hourly — the "
            "scoring actuals' own convention)",
            "identity": "NYISO posts LBMP = E + MCL - MCC (losses add, "
            "congestion subtracts); E recovered per zone-hour as "
            "LBMP - MCL + MCC and its cross-zone spread measured",
            "estimator": "dev_z,m = sum_h MCL_z,h / sum_h E_h — the frozen "
            "MISO/PJM/CAISO delivery-factor deviation estimator on NYISO's "
            "own posted components (rule 25: nothing crosses an ISO boundary)",
            "lw_weights": "keeper hourly zonal demand (the measured-load pin), "
            "used as weights only",
        },
        "contract_checks": {},
        "zone_month_components": {},
        "dev_surface": {},
        "spread_vs_uw_monthly": {},
        "annual_gradient": {},
        "face_months": {},
        "materiality": {},
        "adverse_cases": {},
    }

    lw_loss_premium_annual: dict[int, float] = {}
    lw_total_premium_annual: dict[int, float] = {}
    for year in YEARS:
        z = _zone_hourly(year)
        price_mod, demand = _keeper_frames(year)
        # Align keeper hours (0..8759 model clock) with the measured UTC index
        # by POSITION within the year: both are the year's hour sequence; the
        # measured index may carry 8,784 hours in a leap year (2024) — the
        # model clock drops Feb 29, so positional alignment uses the calendar
        # month series to stay month-faithful (monthly aggregates only; no
        # hour-level pairing is scored here).
        months = z["month"]
        lbmp, mcl, mcc, e = z["lbmp"], z["mcl"], z["mcc"], z["e"]["e"]

        # --- contract checks -------------------------------------------------
        n_hours = len(lbmp)
        ident_resid = {}
        for zn in DOWNSTATE:
            d_tot = lbmp[zn] - lbmp["Upstate_West"]
            d_loss = mcl[zn] - mcl["Upstate_West"]
            d_cong = mcc[zn] - mcc["Upstate_West"]
            ident_resid[zn] = float((d_tot - (d_loss - d_cong)).abs().max())
        out["contract_checks"][year] = {
            "hours": int(n_hours),
            "months_present": sorted(int(m) for m in months.unique()),
            "identity_max_abs_residual_usd": ident_resid,
            "e_cross_zone_spread_p99_usd": float(
                z["e_cross_zone_spread"]["spread"].quantile(0.99)
            ),
            "e_cross_zone_spread_max_usd": float(
                z["e_cross_zone_spread"]["spread"].max()
            ),
        }

        # --- per zone-month components + dev surface -------------------------
        comp_rows = {}
        dev_rows = {}
        spread_rows = {}
        month_index = months.reindex(lbmp.index)
        for m in range(1, 13):
            sel = month_index == m
            if not bool(sel.any()):
                continue
            e_sum = float(e[sel].sum())
            comp_rows[m] = {
                zn: {
                    "lbmp": round(float(lbmp.loc[sel, zn].mean()), 3),
                    "mcl": round(float(mcl.loc[sel, zn].mean()), 3),
                    "mcc": round(float(mcc.loc[sel, zn].mean()), 3),
                }
                for zn in ZONE_MAP
            }
            dev_rows[m] = {
                zn: round(float(mcl.loc[sel, zn].sum()) / e_sum, 6)
                for zn in ZONE_MAP
            }
            spread_rows[m] = {
                zn: {
                    "total": round(
                        float(
                            (lbmp.loc[sel, zn] - lbmp.loc[sel, "Upstate_West"]).mean()
                        ),
                        3,
                    ),
                    "loss": round(
                        float(
                            (mcl.loc[sel, zn] - mcl.loc[sel, "Upstate_West"]).mean()
                        ),
                        3,
                    ),
                    "cong": round(
                        float(
                            -(mcc.loc[sel, zn] - mcc.loc[sel, "Upstate_West"]).mean()
                        ),
                        3,
                    ),
                }
                for zn in DOWNSTATE
            }
        out["zone_month_components"][year] = comp_rows
        out["dev_surface"][year] = dev_rows
        out["spread_vs_uw_monthly"][year] = spread_rows

        # --- annual gradient: measured split vs model ------------------------
        grad = {}
        for zn in DOWNSTATE:
            grad[zn] = {
                "measured_total": round(
                    float((lbmp[zn] - lbmp["Upstate_West"]).mean()), 3
                ),
                "measured_loss": round(
                    float((mcl[zn] - mcl["Upstate_West"]).mean()), 3
                ),
                "measured_cong": round(
                    float(-(mcc[zn] - mcc["Upstate_West"]).mean()), 3
                ),
                "model_total": round(
                    float((price_mod[zn] - price_mod["Upstate_West"]).mean()), 3
                ),
            }
        out["annual_gradient"][year] = grad

        # --- LW premium split (weights: keeper zonal demand) ------------------
        # Positional month mapping for the model clock (8760, non-leap months).
        mh = np.repeat(
            np.arange(1, 13),
            np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24,
        )
        w = demand[list(ZONE_MAP)].to_numpy()
        w = w / w.sum(axis=1, keepdims=True)
        w_annual = w.mean(axis=0)
        zone_order = list(ZONE_MAP)
        w_ann = dict(zip(zone_order, (round(float(x), 4) for x in w_annual)))

        def lw_prem(series_wide: pd.DataFrame) -> float:
            """Annual mean of the static-annual-LW premium over Upstate_West."""
            prem = sum(
                w_annual[i] * (series_wide[zn] - series_wide["Upstate_West"])
                for i, zn in enumerate(zone_order)
            )
            return float(prem.mean())

        lw_loss = lw_prem(mcl)
        lw_tot = lw_prem(lbmp)
        lw_loss_premium_annual[year] = round(lw_loss, 3)
        lw_total_premium_annual[year] = round(lw_tot, 3)

        # per-face-month LW premium split (2025 faces; all months recorded)
        lw_by_month = {}
        for m in range(1, 13):
            sel = (month_index == m).to_numpy()
            if not sel.any():
                continue
            lw_by_month[m] = {
                "lw_loss_premium": round(
                    float(
                        sum(
                            w_annual[i]
                            * (mcl.loc[sel, zn] - mcl.loc[sel, "Upstate_West"])
                            for i, zn in enumerate(zone_order)
                        ).mean()
                    ),
                    3,
                ),
                "lw_total_premium": round(
                    float(
                        sum(
                            w_annual[i]
                            * (lbmp.loc[sel, zn] - lbmp.loc[sel, "Upstate_West"])
                            for i, zn in enumerate(zone_order)
                        ).mean()
                    ),
                    3,
                ),
            }
        out["face_months"][year] = {
            "lw_premium_by_month": lw_by_month,
            "annual_lw_weights": w_ann,
        }
        del mh  # month mapping only needed if hour-pairing were scored

    # --- scorer context + materiality ----------------------------------------
    bench_lw = {}
    for year in YEARS:
        b = json.load(gzip.open(BENCH / f"{year}.json.gz"))
        avg = b["bench"]["avgLMP"]
        bench_lw[year] = {
            "rt_lw_annual": round(float(avg["rt_lw"]), 2),
            "rt_lw_mon": [round(float(x), 2) for x in avg["rt_mon" if "rt_lw_mon" not in avg else "rt_lw_mon"]],
        }
    keeper_c3a = {"2023": "+1.0%", "2024": "-2.0%", "2025": "-12.0% (58.45 vs lw 66.43)"}
    out["materiality"] = {
        "bench_rt_lw": bench_lw,
        "keeper_c3a": keeper_c3a,
        "annual_lw_loss_premium_vs_uw_usd": lw_loss_premium_annual,
        "annual_lw_total_premium_vs_uw_usd": lw_total_premium_annual,
        "note": "the LW loss premium is the measured additive downstate LOSS "
        "floor the lossless model omits; as a share of the 2025 C3a gap "
        "(66.43 - 58.45 = 7.98 $/MWh) it bounds what the loss surface can "
        "close ex ante. It is a FLOOR component: congestion dominates the "
        "object months (nyiso-158 §1.5) and is NOT addressed here.",
    }
    out["adverse_cases"] = {
        "c3a_2023_up_side": {
            "keeper": "+1.0%",
            "band_headroom_pp": 9.0,
            "predicted_push_pp": round(
                100.0
                * lw_loss_premium_annual[2023]
                / float(bench_lw[2023]["rt_lw_annual"]),
                2,
            ),
            "note": "upper bound: assumes the full annual LW loss premium "
            "materializes as model LW price uplift",
        },
        "c3a_2025_upstate_relocation": {
            "gate": "arm Upstate_West annual mean dual within +/-0.75 $/MWh "
            "of control every year (W-K3d class: the surface must not "
            "relocate error upstate; UW is the persistent SENDER so its "
            "dual is set by its own balance — any move is second-order "
            "through dispatch reshuffle and must stay small)",
        },
    }

    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("contract_checks", "annual_gradient", "materiality", "adverse_cases")}, indent=1))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
