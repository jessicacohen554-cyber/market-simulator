"""ercot-220 Phase-0 (READ-ONLY): the stage-1 capability-object candidate space,
measured against the armed 2023-vs-2024/25 split.

The ercot-219 handback (FINDING-ercot219 §6): stages 2-3 of the
artificial-shortage mechanism are built, seam-proven and default-off, and are
inert without a stage-1 capability object; the aggregate ONLINE basis
(`rtolhsl`/`T_tel`) is REJECTED (dimensional category error) and DO-NOT-REDO.
This probe measures, from COMMITTED ARTIFACTS ONLY (no LP, no solve, no
year re-scored), what each remaining candidate basis would feed stage 2:

  L1  Incidence audit of the expectation layer on the ercot-219 T_tel basis
      (the committed `exhaustion_<year>.parquet` audit trail of the REJECTED
      arm — read, never re-run) against the actual RT tail calendar:
      precision/recall of exhaustion hours vs actual >$200 / >$1000 hours,
      per year and per published-instrument window.
  L2  Split decomposition: how much of the 2023-vs-24/25 exhaustion split is
      carried by the SEQUESTRATION input (the armed *_withheld families,
      measured ASPLANNP433) vs by the telemetry's embedded commitment
      posture + load + fleet. Counterfactuals: seq -> 0, and 2023/2024 with
      the 2025 sequestration profile substituted, LOLP recomputed through
      the registered machinery (results.scarcity.lolp) at the run's own
      registered constants (read from the committed run_config.json).
  L3  The ENDOGENOUS (model-own-state) basis degeneracy, bounded from the
      KEEPER's committed class_hourly/system sidecars:
      (a) count-no-offline-capability: in an LP, dispatch = load by the
          energy-balance identity, so H = -seq in every hour -> LOLP = 1
          wherever seq > 0 (count reported) -> exhaustion everywhere, no
          split;
      (b) count-physics-fast-start (rule 18): merchant-thermal and
          CT_PEAKER headroom LOWER bounds (year-max class dispatch minus
          hourly dispatch) at the 2023 exhaustion-calendar hours -> compare
          to the LOLP thresholds H(LOLP=0.5), H(P_exhaust*VOLL=$1000).
  L4  The fleet-scope (cogen/PUN) wedge insufficiency: the ercot-163 §4 /
      ercot-170 wedge (~2.7-3.6 GW) against the same headroom bounds and
      thresholds.

Output: results/calibration/ercot220_stage1_basis_phase0.json

Read-only discipline: no ScenarioConfig field, no constant, no derive, no
matrix verdict; prices are read only as the evaluation calendar (actual RT),
never as an input to anything. Rule 22: years 2023-2025 only. Rule 25:
ERCOT only. Clock: the model's fixed non-leap 8760 hour-beginning CST index
throughout (ercot-216 §6); the actuals parquet is already on that index.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.results.scarcity import lolp, within_day_forward_max  # noqa: E402

YEARS = (2023, 2024, 2025)
ARM = REPO / "results/calibration/ercot219_optionb_B"  # committed audit trail
KEEPER = REPO / "results/calibration/ercot215_decontam_B"  # the keeper bundle
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
OUT = REPO / "results/calibration/ercot220_stage1_basis_phase0.json"

MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_CUM = np.cumsum((0,) + MONTH_DAYS)

# Published-instrument windows on the fixed non-leap clock (rule 8; the
# ercot-217 constructions): ECRS go-live OD 2023-06-10 -> hour 160*24; the
# 2024-08-01 release reform -> hour 212*24 (spec.py ERCOT_ECRS_RELEASE_
# REFORM_HOUR); RTC+B go-live 2025-12-05 -> hour 338*24 (scarcity.py
# RTCB_GOLIVE_HOUR).
ECRS_GOLIVE_HOUR = 160 * 24
ECRS_REFORM_HOUR = 212 * 24
RTCB_HOUR = 338 * 24

MERCHANT_THERMAL = [
    "CC_CHP",
    "CC_REGULAR",
    "COAL_LIGNITE",
    "COAL_PRB",
    "CT_CHP",
    "CT_PEAKER",
    "OTHER",
    "ST_CHP",
    "ST_GAS",
    "oil",
]
# rule 18 [R-PHYSICS] fast-start: min-down <= 2 h, startup < $30/MW — the CT
# fleet (and oil peakers); the slow classes are never intra-hour startable.
FAST_START = ["CT_PEAKER", "oil"]


def month_of_hour(hours: np.ndarray) -> np.ndarray:
    """1..12 for fixed non-leap hour-of-year indices."""
    return np.searchsorted(_MONTH_CUM, hours // 24, side="right")


def load_exhaustion(year: int) -> pd.DataFrame:
    df = pd.read_parquet(ARM / "hourly" / f"exhaustion_{year}.parquet")
    return df.sort_values("hour").reset_index(drop=True)


def load_actual(year: int) -> np.ndarray:
    lmp = pd.read_parquet(ACTUAL)
    return (
        lmp[lmp["year"] == year].sort_values("hour")["rt"].to_numpy(float)[:8760]
    )


def lolp_constants() -> dict:
    """The registered constants the ercot-219 run itself solved with."""
    rc = json.loads((ARM / "run_config.json").read_text())
    sc = rc.get("scenario_config", rc)
    return {
        "mu_mw": float(sc["ordc_lolp_mu_mw"]),
        "sigma_mw": float(sc["ordc_lolp_sigma_mw"]),
        "mcl_mw": float(sc["ordc_mcl_mw"]),
        "shift_sigma": float(sc["ordc_lolp_shift_sigma"]),
        "voll": float(sc["ordc_voll"]),
    }


def h_threshold(p: float, c: dict) -> float:
    """H at which LOLP == p under the registered curve (analytic inverse)."""
    from scipy.special import ndtri

    return c["mcl_mw"] + c["mu_mw"] + c["sigma_mw"] * (
        c["shift_sigma"] + float(ndtri(1.0 - p))
    )


def window_counts(hours_mask: np.ndarray, year: int) -> dict:
    """Split a boolean hour mask by the published-instrument windows."""
    idx = np.arange(8760)
    if year == 2023:
        wins = {
            "pre_ecrs_golive": idx < ECRS_GOLIVE_HOUR,
            "ecrs_sequestration": idx >= ECRS_GOLIVE_HOUR,
        }
    elif year == 2024:
        wins = {
            "ecrs_sequestration": idx < ECRS_REFORM_HOUR,
            "post_release_reform": idx >= ECRS_REFORM_HOUR,
        }
    else:
        wins = {
            "post_release_reform": idx < RTCB_HOUR,
            "rtcb": idx >= RTCB_HOUR,
        }
    return {k: int((hours_mask & m).sum()) for k, m in wins.items()}


def l1_incidence(c: dict) -> dict:
    """T_tel-basis expectation layer vs the actual tail calendar."""
    out = {}
    for y in YEARS:
        df = load_exhaustion(y)
        act = load_actual(y)
        exh = df["lolp"].to_numpy(float) >= 0.5
        offer_1k = df["p_exhaust"].to_numpy(float) * c["voll"] >= 1000.0
        act_ok = ~np.isnan(act)
        tail200 = act_ok & (act > 200.0)
        tail1k = act_ok & (act > 1000.0)
        inter200 = exh & tail200
        out[str(y)] = {
            "exhaustion_hours_lolp_ge_0p5": int(exh.sum()),
            "offer_active_hours_ge_1000": int(offer_1k.sum()),
            "actual_tail_hours_gt200": int(tail200.sum()),
            "actual_tail_hours_gt1000": int(tail1k.sum()),
            "exh_and_tail200": int(inter200.sum()),
            "exh_and_tail1000": int((exh & tail1k).sum()),
            "precision_exh_vs_tail200": round(
                float(inter200.sum() / exh.sum()), 4
            )
            if exh.sum()
            else None,
            "recall_exh_vs_tail200": round(
                float(inter200.sum() / tail200.sum()), 4
            )
            if tail200.sum()
            else None,
            "offer1k_and_tail200": int((offer_1k & tail200).sum()),
            "precision_offer1k_vs_tail200": round(
                float((offer_1k & tail200).sum() / offer_1k.sum()), 4
            )
            if offer_1k.sum()
            else None,
            "exhaustion_by_window": window_counts(exh, y),
            "tail200_by_window": window_counts(tail200, y),
            "exhaustion_monthly": {
                str(m): int((exh & (month_of_hour(np.arange(8760)) == m)).sum())
                for m in range(1, 13)
            },
            "tail200_monthly": {
                str(m): int(
                    (tail200 & (month_of_hour(np.arange(8760)) == m)).sum()
                )
                for m in range(1, 13)
            },
        }
    return out


def recount(h: np.ndarray, c: dict) -> dict:
    """Exhaustion counts for a counterfactual margin series."""
    lp = lolp(h, c["mu_mw"], c["sigma_mw"], c["mcl_mw"], c["shift_sigma"])
    pex = within_day_forward_max(lp)
    return {
        "h_p5_mw": round(float(np.percentile(h, 5)), 1),
        "exhaustion_hours_lolp_ge_0p5": int((lp >= 0.5).sum()),
        "offer_active_hours_ge_1000": int((pex * c["voll"] >= 1000.0).sum()),
    }


def l2_split_decomposition(c: dict) -> dict:
    """Carried-sequestration vs commitment-posture share of the split."""
    seq25 = load_exhaustion(2025)["as_sequestered_mw"].to_numpy(float)
    out = {}
    for y in YEARS:
        df = load_exhaustion(y)
        h = df["h_margin_mw"].to_numpy(float)
        seq = df["as_sequestered_mw"].to_numpy(float)
        base = recount(h, c)
        noseq = recount(h + seq, c)
        seq_as_2025 = recount(h + seq - seq25, c) if y != 2025 else None
        out[str(y)] = {
            "h_mean_mw": round(float(h.mean()), 1),
            "seq_mean_mw": round(float(seq.mean()), 1),
            "h_plus_seq_mean_mw": round(float((h + seq).mean()), 1),
            "as_carried": base,
            "seq_zeroed": noseq,
            "seq_replaced_by_2025_profile": seq_as_2025,
        }
    return out


def l3_endogenous_degeneracy(c: dict) -> dict:
    """The model-own-state basis, bounded from the KEEPER's sidecars."""
    thr_05 = h_threshold(0.5, c)
    thr_1k = h_threshold(1000.0 / c["voll"], c)
    out = {
        "h_at_lolp_0p5_mw": round(thr_05, 1),
        "h_at_offer_1000_mw": round(thr_1k, 1),
        "years": {},
    }
    for y in YEARS:
        seq = load_exhaustion(y)["as_sequestered_mw"].to_numpy(float)
        exh23 = load_exhaustion(y)["lolp"].to_numpy(float) >= 0.5
        ch = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        piv = (
            ch.pivot_table(
                index="hour", columns="klass", values="mw", aggfunc="sum",
                observed=True,
            )
            .reindex(range(8760))
            .fillna(0.0)
        )
        # LOWER bound on class available capability: its own year-max dispatch.
        # True availability >= max dispatch, so headroom bounds are LOWER
        # bounds on the model's real headroom (conservative for the claim).
        mt = [k for k in MERCHANT_THERMAL if k in piv.columns]
        fs = [k for k in FAST_START if k in piv.columns]
        head_mt = (piv[mt].max(axis=0) - piv[mt]).clip(lower=0.0).sum(axis=1)
        head_fs = (piv[fs].max(axis=0) - piv[fs]).clip(lower=0.0).sum(axis=1)
        hb_mt = head_mt.to_numpy(float)
        hb_fs = head_fs.to_numpy(float)
        sel = exh23 if exh23.sum() else np.ones(8760, bool)
        out["years"][str(y)] = {
            # (a) count-no-offline: H = -seq by the LP energy-balance identity
            "count_none_hours_seq_gt0_lolp_eq_1": int((seq > 0).sum()),
            # (b) physics-fast-start-inclusive H >= fast-start headroom - seq
            "faststart_headroom_bound_minus_seq_p5_mw": round(
                float(np.percentile(hb_fs - seq, 5)), 1
            ),
            "merchant_thermal_headroom_bound_p5_at_exh_hours_mw": round(
                float(np.percentile(hb_mt[sel], 5)), 1
            ),
            "merchant_thermal_headroom_bound_p50_at_exh_hours_mw": round(
                float(np.percentile(hb_mt[sel], 50)), 1
            ),
            "faststart_headroom_bound_p5_at_exh_hours_mw": round(
                float(np.percentile(hb_fs[sel], 5)), 1
            ),
            "n_eval_hours": int(sel.sum()),
        }
    return out


def l5_ideal_availability_ceiling(c: dict) -> dict:
    """What reality's OWN available responsive margin (PRC) implies.

    PRC (published NP6-905, quantity column only — ``system_lambda``/adder
    columns NOT read) is the real grid's physical responsive capability: the
    honest ceiling for ANY admissible availability-side stage-1 basis,
    because a licensed basis cannot credibly produce margins thinner than
    the margins reality itself telemetered. Applies the registered LOLP
    curve and the stage-3 offer form ``P x VOLL`` to it, same-hour, and
    scores the implied offer against the actual tail calendar. 2025 is cut
    at the RTC+B go-live hour (the series' own NaN tail).
    """
    out = {}
    for y in YEARS:
        prc = (
            pd.read_parquet(
                REPO / "data/raw/ercot" / f"ercot_{y}_ordc_reserves_hourly.parquet",
                columns=["hour", "prc"],
            )
            .sort_values("hour")["prc"]
            .to_numpy(float)[:8760]
        )
        act = load_actual(y)
        ok = ~np.isnan(prc) & ~np.isnan(act)
        lp = lolp(
            prc[ok], c["mu_mw"], c["sigma_mw"], c["mcl_mw"], c["shift_sigma"]
        )
        offer = lp * c["voll"]
        # The stage-2 window convention applied to the same series: NaN
        # hours (the 2025 RTC+B tail) carried as 0 before the forward max.
        lp_full = np.zeros(8760)
        lp_full[np.where(ok)[0]] = lp
        pex_offer = within_day_forward_max(lp_full)[ok] * c["voll"]
        tail = act[ok] > 200.0
        out[str(y)] = {
            "hours_evaluated": int(ok.sum()),
            "prc_p10_at_tail_mw": round(float(np.percentile(prc[ok][tail], 10)), 0)
            if tail.sum()
            else None,
            "prc_p50_at_tail_mw": round(float(np.percentile(prc[ok][tail], 50)), 0)
            if tail.sum()
            else None,
            "implied_offer_p50_at_tail": round(
                float(np.percentile(offer[tail], 50)), 1
            )
            if tail.sum()
            else None,
            "implied_offer_p90_at_tail": round(
                float(np.percentile(offer[tail], 90)), 1
            )
            if tail.sum()
            else None,
            "implied_offer_max_at_tail": round(float(offer[tail].max()), 1)
            if tail.sum()
            else None,
            "windowed_offer_p50_at_tail": round(
                float(np.percentile(pex_offer[tail], 50)), 1
            )
            if tail.sum()
            else None,
            "windowed_offer_p90_at_tail": round(
                float(np.percentile(pex_offer[tail], 90)), 1
            )
            if tail.sum()
            else None,
            "windowed_hours_offer_ge_1000": int((pex_offer >= 1000.0).sum()),
            "windowed_hours_offer_ge_2500": int((pex_offer >= 2500.0).sum()),
            "hours_offer_ge_1000": int((offer >= 1000.0).sum()),
            "hours_offer_ge_2500": int((offer >= 2500.0).sum()),
            "hours_prc_below_mcl": int((prc[ok] < c["mcl_mw"]).sum()),
            "actual_tail_hours_gt200": int(tail.sum()),
        }
    return out


def main() -> None:
    c = lolp_constants()
    result = {
        "probe": "ercot220_stage1_basis_phase0",
        "date": "2026-08-18",
        "read_only": True,
        "sources": {
            "exhaustion_audit_trail": str(ARM.relative_to(REPO)),
            "keeper_bundle": str(KEEPER.relative_to(REPO)),
            "actual_rt": str(ACTUAL.relative_to(REPO)),
            "note": (
                "The ercot-219 arm's committed exhaustion parquets are READ "
                "as the T_tel-basis audit trail; nothing is re-run. The "
                "keeper's class_hourly bounds the endogenous basis. Actual "
                "RT enters ONLY as the evaluation calendar (never an input)."
            ),
        },
        "registered_constants": c,
        "L1_ttel_basis_incidence": l1_incidence(c),
        "L2_split_decomposition": l2_split_decomposition(c),
        "L3_endogenous_degeneracy": l3_endogenous_degeneracy(c),
        "L5_ideal_availability_ceiling": l5_ideal_availability_ceiling(c),
        "L4_fleet_scope_wedge": {
            "wedge_gw_cited": "2.7-3.6 (ercot-163 §4; ercot-170/191 term A)",
            "note": (
                "Compare L3's merchant-thermal headroom LOWER bounds at the "
                "exhaustion-calendar hours minus 3.6 GW against "
                "h_at_lolp_0p5_mw — computed in the finding from these "
                "numbers."
            ),
        },
    }
    OUT.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
