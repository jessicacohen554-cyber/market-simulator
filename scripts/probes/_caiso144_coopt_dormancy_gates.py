"""caiso-144 — dormancy gates for the COMPLETED in-LP reserve co-opt (queue #1).

Design-first, kill-before-solve (the caiso-129/140/142/143 discipline). Reads
ONLY committed bytes — the caiso-139 keeper bundle's hourly sidecars
(``unit_hourly_<y>.parquet`` / ``system_<y>.parquet``), the committed actual
RT hourly LMPs (``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet``)
and the raw CAISO OASIS AS_REQ CSVs — plus the model's own reserve-design
constants imported from source. **No LP is built and no solver runs.**

Context. CAISO lever-queue item 1 (docs/mechanism-testing-matrix.md §5.2) owes
"energy_reserve_coopt + completing caiso_reserve_coopt (add storage/hydro/
RegUp-Down to the pergen builder first)" before any further scarcity-overlay
work (rule 19 — pick one owner for scarcity). The queue text is STALE against
source: ``_caiso_design`` already carries the storage RS columns (ASSOC SOC
gate, ``CAISO_AS_SUSTAIN_DURATION_H``) and the hydro pergen membership
(``_caiso_reserve_eligible`` + ``CAISO_HYDRO_RAMP10_FRAC`` backfill) — its
docstring records "issue #1492 design constraints 2/3, completed". The single
remaining gap is Regulation (walled: no forward-derivable requirement series;
RegDown is a downward product outside the upward-headroom row). So the owed
test is decidable on the CURRENT keeper's committed bytes: measure, hour by
hour, whether the completed design's requirement can ever go short at the
keeper's solved dispatch.

Gates:

* §A — the completed requirement, reproduced exactly from the design's own
  formula: ``max(MSSC, CAISO_CONTINGENCY_FRAC × load)`` with the
  availability-aware plant-aggregated MSSC (``largest_single_contingency_mw``
  semantics on the sidecar's ``cap_mw``), plus a measured Regulation-Up
  sensitivity tier (OASIS AS_REQ ``RU_REQ_MIN_MW``, AS_CAISO, DAM — the
  must-procure floor, taken at its ANNUAL MAX as a flat conservative adder).
* §B — the completed pergen supply at the keeper's solved dispatch: per-pool
  (zone, fuel) ``min(Σ ramp10·avail, Σ (cap − P))`` over the design's own
  eligibility (RESERVE_FUEL_TYPES + hydro, ramp10 > 0), in two tiers —
  T1 thermal-only (the caiso-59 basis) and T2 +hydro (the completed builder).
  Storage RS is EXCLUDED entirely (it only adds supply), so every slack number
  is a LOWER bound on the completed design's slack.
* §C — the C3c cross-check: the same slack measured IN the actual RT>$200
  hours specifically (the 47/35/8 hours C3c fails against). If the pool is
  slack by GW in exactly reality's scarcity hours, no in-LP reserve
  co-optimization at any completion level can price them.
* §D — the forecast-path LOLP overlay UPPER BOUND in those same hours: the
  ``caiso_scarcity_overlay`` arithmetic (reserve_headroom → ordc_adder,
  VOLL 2000 / MCL 1400 / σ 2500) reproduced from the committed sidecars.
  ``r_online`` matches the real measure's composition (thermal online
  headroom + storage headroom) except that (a) the storage power cap is
  LOWER-bounded by each tech's annual max observed discharge (the committed
  sidecar carries no cap column — a real cap is ≥ any realised discharge, and
  the COD ramp only lowers it earlier in the year), and (b) curtailed-VRE
  headroom is EXCLUDED (it is in the real ``r_online``; in the evening tail
  hours it is ~0 by construction). Both directions UNDER-state ``r_online``,
  so the adder is an OVER-estimate. If even the over-estimated settlement
  (λ + adder) clears $200 in ~none of the actual tail hours, the caiso-137b
  charter question ("should CAISO have a scarcity overlay in the scored
  backcast lane?") is answered by measurement: wiring it could not close C3c
  either.

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso144_coopt_dormancy_gates.py
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.model.reserves.spec import (  # noqa: E402
    CAISO_CONTINGENCY_FRAC,
    CAISO_HYDRO_RAMP10_FRAC,
    QUICK_START_FUEL_TYPES,
    RESERVE_FUEL_TYPES,
)
from market_sim.data.fleet.withholding import (  # noqa: E402
    RAMP10_FRAC_BY_FUEL,
    RAMP10_FRAC_BY_GROUP,
)
from market_sim.results.scarcity import (  # noqa: E402
    CAISO_SCARCITY_MCL_MW,
    CAISO_SCARCITY_SIGMA_MW,
    CAISO_SCARCITY_SHIFT_SIGMA,
    CAISO_SCARCITY_VOLL,
    ordc_adder,
)

BUNDLE = REPO / "results/calibration/caiso139_dumpguard_B/hourly"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
AS_REQ_DIR = REPO / "data/raw/CAISO-AS"
TAIL_THRESHOLD = 200.0  # frontend/data/backcast/tail/actual_tail.json CAISO
YEARS = (2023, 2024, 2025)
CA_ZONES = ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")  # load-carrying


def _ramp10_frac(group: str, fuel: str) -> float:
    """The design's per-unit ramp10 fraction: group table, fuel fallback,
    hydro backfilled at CAISO_HYDRO_RAMP10_FRAC (spec.caiso_pergen_structure)."""
    frac = RAMP10_FRAC_BY_GROUP.get(group or "")
    if frac is None:
        frac = RAMP10_FRAC_BY_FUEL.get(fuel, 0.0)
    if fuel == "hydro" and frac <= 0.0:
        frac = CAISO_HYDRO_RAMP10_FRAC
    return float(frac)


def _measured_ru_req_max(year: int) -> float:
    """Annual MAX of the DAM AS_CAISO Regulation-Up must-procure floor
    (RU_REQ_MIN_MW) — the conservative flat Regulation sensitivity adder."""
    vals = []
    for f in sorted(glob.glob(str(AS_REQ_DIR / f"asreq_ALL_{year}*.csv"))):
        d = pd.read_csv(
            f, usecols=["MARKET_RUN_ID", "ANC_TYPE", "ANC_REGION", "XML_DATA_ITEM", "MW"]
        )
        m = d[
            (d.MARKET_RUN_ID == "DAM")
            & (d.ANC_TYPE == "RU")
            & (d.ANC_REGION == "AS_CAISO")
            & (d.XML_DATA_ITEM == "RU_REQ_MIN_MW")
        ]
        if len(m):
            vals.append(float(m.MW.max()))
    return max(vals) if vals else float("nan")


def main() -> None:
    out: dict = {}
    actual = pd.read_parquet(ACTUAL_LMP)
    for year in YEARS:
        u = pd.read_parquet(BUNDLE / f"unit_hourly_{year}.parquet")
        s = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
        u = u[u["pass"] == "P1"].copy()
        s = s[s["pass"] == "P1"].copy()
        T = int(s.hour.max()) + 1

        # ---- system load + prices ------------------------------------------
        load = (
            s[s.zone.isin(CA_ZONES)].groupby("hour")["demand"].sum().reindex(range(T)).to_numpy()
        )
        piv_price = s.pivot_table(index="hour", columns="zone", values="price")
        piv_dem = s.pivot_table(index="hour", columns="zone", values="demand")
        ca = [z for z in CA_ZONES if z in piv_price.columns]
        lam_dw = (piv_price[ca] * piv_dem[ca]).sum(axis=1).to_numpy() / piv_dem[
            ca
        ].sum(axis=1).to_numpy()
        lam_max = piv_price[ca].max(axis=1).to_numpy()

        # ---- per-unit static attributes ------------------------------------
        att = (
            u.groupby("unit_id")
            .agg(
                fuel=("fuel", "first"),
                group=("plant_group", "first"),
                zone=("zone", "first"),
                plant=("plant_code", "first"),
                pmax=("cap_mw", "max"),
            )
            .reset_index()
        )
        att["frac"] = [
            _ramp10_frac(g, f) for g, f in zip(att.group, att.fuel)
        ]
        thermal_eligible = att.fuel.isin(sorted(RESERVE_FUEL_TYPES))
        att["elig_t1"] = thermal_eligible & (att.frac > 0)  # caiso-59 basis
        att["elig_t2"] = (thermal_eligible | (att.fuel == "hydro")) & (
            att.frac > 0
        )  # completed builder

        # ---- §A requirement ------------------------------------------------
        # MSSC: availability-aware plant-aggregated (spec semantics — pmax ×
        # max availability summed per plant over eligible units; rows with no
        # plant code count individually).
        el = att[att.fuel.isin(sorted(RESERVE_FUEL_TYPES)) | (att.fuel == "hydro")]
        pc = el.plant.astype(str).str.strip()
        agg = el.assign(_pc=pc).groupby("_pc")["pmax"].sum()
        solo = el[pc == ""]["pmax"]
        mssc = float(max(agg.max() if len(agg) else 0.0, solo.max() if len(solo) else 0.0))
        contingency = np.maximum(mssc, CAISO_CONTINGENCY_FRAC * load)
        ru_max = _measured_ru_req_max(year)

        # ---- §B completed pergen supply at the solved dispatch -------------
        u = u.merge(att[["unit_id", "frac", "elig_t1", "elig_t2"]], on="unit_id")
        u["headroom"] = np.maximum(u.cap_mw - u.mw, 0.0)
        u["ramp_avail"] = u.frac * u.cap_mw  # frac × pmax × availability(t)

        def pool_supply(mask_col: str) -> np.ndarray:
            e = u[u[mask_col]]
            g = e.groupby(["zone", "fuel", "hour"], observed=True).agg(
                ramp=("ramp_avail", "sum"), head=("headroom", "sum")
            )
            pool_r = np.minimum(g["ramp"], g["head"])
            return pool_r.groupby(level="hour").sum().reindex(range(T)).fillna(0.0).to_numpy()

        s_t1 = pool_supply("elig_t1")
        s_t2 = pool_supply("elig_t2")

        def slack_stats(supply: np.ndarray, req: np.ndarray) -> dict:
            slack = supply - req
            return {
                "min_slack_mw": round(float(slack.min()), 1),
                "p01_slack_mw": round(float(np.quantile(slack, 0.01)), 1),
                "mean_slack_mw": round(float(slack.mean()), 1),
                "hours_short": int((slack < 0).sum()),
            }

        # ---- §C actual RT tail hours ---------------------------------------
        a = actual[actual.year == year].set_index("hour")
        tail_hours = a.index[a.rt > TAIL_THRESHOLD].to_numpy()
        tail_hours = tail_hours[tail_hours < T]
        slack_t2 = s_t2 - contingency
        tail_slack = slack_t2[tail_hours] if len(tail_hours) else np.array([])
        # Fixed non-leap clock: month/hod histograms of the actual tail hours.
        month_edges = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
        tail_month = np.searchsorted(month_edges, tail_hours, side="right")
        tail_hod = tail_hours % 24

        # ---- §D LOLP overlay upper bound ----------------------------------
        # reserve_headroom reproduced: thermal online headroom + storage
        # headroom (power cap lower-bounded by annual max observed discharge
        # per tech — sidecars carry no cap column), curtailed-VRE excluded.
        # Both under-state r_online → the adder is an over-estimate. Online
        # status at the plant level (>1 MW summed dispatch),
        # spec._online_plant_mask.
        th = u[u.fuel.isin(sorted(RESERVE_FUEL_TYPES))].copy()
        pcs = th.plant_code.astype(str).str.strip()
        th["_plant"] = np.where(pcs == "", "u:" + th.unit_id.astype(str), pcs)
        pl_on = (
            th.groupby(["_plant", "hour"], observed=True)["mw"].sum() > 1.0
        ).rename("online")
        th = th.merge(pl_on, left_on=["_plant", "hour"], right_index=True)
        th_on = th[th.online]
        r_online = (
            th_on.groupby("hour")["headroom"].sum().reindex(range(T)).fillna(0.0).to_numpy()
        )
        quick = th[th.fuel.isin(sorted(QUICK_START_FUEL_TYPES)) & ~th.online]
        r_offline = (
            quick.groupby("hour")["headroom"].sum().reindex(range(T)).fillna(0.0).to_numpy()
        )
        # Storage headroom, cap lower-bounded by annual max observed discharge
        # per tech (real: power_cap − discharge + charge, results/scarcity.py
        # reserve_headroom).
        st = pd.read_parquet(BUNDLE / f"storage_{year}.parquet")
        st = st[st["pass"] == "P1"]
        cap_lb = st.groupby("tech", observed=True)["discharge_mw"].max()
        st = st.merge(cap_lb.rename("cap_lb"), left_on="tech", right_index=True)
        st["headroom"] = st.cap_lb - st.discharge_mw + st.charge_mw
        storage_head = (
            st.groupby("hour")["headroom"].sum().reindex(range(T)).fillna(0.0).to_numpy()
        )
        r_online = r_online + storage_head
        adder = ordc_adder(
            r_online + r_offline,
            lam_dw,
            voll=CAISO_SCARCITY_VOLL,
            mcl_mw=CAISO_SCARCITY_MCL_MW,
            mu_mw=0.0,
            sigma_mw=CAISO_SCARCITY_SIGMA_MW,
            shift_sigma=CAISO_SCARCITY_SHIFT_SIGMA,
            multistep_floor=False,
            reserves_online_mw=r_online,
        )
        settle_dw = lam_dw + adder
        settle_max = lam_max + adder  # adder on the max-zonal dual: upper bound

        out[year] = {
            "A_requirement": {
                "mssc_mw": round(mssc, 1),
                "load_mean_mw": round(float(load.mean()), 0),
                "contingency_min/mean/max_mw": [
                    round(float(f(contingency)), 0) for f in (np.min, np.mean, np.max)
                ],
                "measured_ru_req_annual_max_mw": round(ru_max, 1),
            },
            "B_slack": {
                "T1_thermal_only": slack_stats(s_t1, contingency),
                "T2_completed_+hydro": slack_stats(s_t2, contingency),
                "T2_+RegUp_flat_max": slack_stats(s_t2, contingency + ru_max),
            },
            "C_actual_tail_hours": {
                "n_hours_rt_gt200": int(len(tail_hours)),
                "min_T2_slack_in_those_hours_mw": (
                    round(float(tail_slack.min()), 1) if len(tail_slack) else None
                ),
                "mean_T2_slack_in_those_hours_mw": (
                    round(float(tail_slack.mean()), 1) if len(tail_slack) else None
                ),
                "by_month": {
                    int(m): int(c)
                    for m, c in zip(*np.unique(tail_month, return_counts=True))
                },
                "by_hod": {
                    int(h): int(c)
                    for h, c in zip(*np.unique(tail_hod, return_counts=True))
                },
            },
            "D_overlay_upper_bound": {
                "adder_max_all_hours": round(float(adder.max()), 3),
                "adder_dwmean": round(float(adder.mean()), 4),
                "hours_settle_dw_gt200": int((settle_dw > TAIL_THRESHOLD).sum()),
                "hours_settle_maxzonal_gt200": int((settle_max > TAIL_THRESHOLD).sum()),
                "energy_only_hours_maxzonal_gt200": int(
                    (lam_max > TAIL_THRESHOLD).sum()
                ),
                "adder_max_in_actual_tail_hours": (
                    round(float(adder[tail_hours].max()), 3) if len(tail_hours) else None
                ),
                "settle_maxzonal_max_in_actual_tail_hours": (
                    round(float(settle_max[tail_hours].max()), 2)
                    if len(tail_hours)
                    else None
                ),
                "min_r_online_mw": round(float(r_online.min()), 1),
                "min_r_online_in_tail_hours_mw": (
                    round(float(r_online[tail_hours].min()), 1)
                    if len(tail_hours)
                    else None
                ),
                # Timing overlap: hours the over-stated overlay settles >$200
                # vs the hours reality's RT tail actually occurred.
                "overlap_fired_and_actual_tail": int(
                    np.isin(np.flatnonzero(settle_max > TAIL_THRESHOLD), tail_hours).sum()
                ),
                "fired_by_month": {
                    int(m): int(c)
                    for m, c in zip(
                        *np.unique(
                            np.searchsorted(
                                month_edges,
                                np.flatnonzero(settle_dw > TAIL_THRESHOLD),
                                side="right",
                            ),
                            return_counts=True,
                        )
                    )
                },
            },
        }

    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
