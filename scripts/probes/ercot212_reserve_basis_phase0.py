"""ercot-212 Phase-0 (RESERVE-BASIS-1, card X item X-3): WHERE the ORDC pricing
region sits relative to the model's reserve representation.

READ-ONLY. No LP is built, no year is solved or scored, no ``ScenarioConfig``
field is read for arming. Executes the pre-registered measurement plan of
``docs/PRECOMMIT-ercot212-reserve-basis-phase0-2026-08-16.md`` (pushed before
this probe ran): A0 construction validation, A1 the held<->RTOLCAP crosswalk,
A2-A5 the term-by-term attribution of the ~zero 2024/2025 endogenous RTORPA
reading, A6 the 2023 contrast, and the V4/V5 out-of-LP viability statistics.

Sources (all committed; no intake):
  results/calibration/ercot204_rule26_delete/hourly/{reserve_family,system}_<y>.parquet
  results/calibration/ercot204_rule26_delete/run_config.json
  data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet          (NP6-905-CD)
  data/raw/ercot-AS/ercot_<year>_as_up_mw.parquet                   (NP3-911 LR credit)
  the measured storage AS-award series (results.scarcity.ercot_storage_as_reserve_mw)
  data/raw/_validation-source/ercot_ordc_lolp_params.csv            (NP6-576-ER, comparison only)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

import sys  # noqa: E402

sys.path.insert(0, str(REPO / "src"))

from market_sim.results.scarcity import (  # noqa: E402
    RTCB_GOLIVE_HOUR,
    ercot_ordc_demand_steps,
    ercot_storage_as_reserve_mw,
    floor_active_mask,
    load_lolp_params,
    ordc_adder,
)

KEEPER_BUNDLE = REPO / "results/calibration/ercot204_rule26_delete"
KEEPER_ID = "2026-08-15-ercot204-rule26-delete"
YEARS = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]: ERCOT holds no marker.
LOLP_TABLE = REPO / "data/raw/_validation-source/ercot_ordc_lolp_params.csv"
# ercot-198 settlement-closure guard: the single uncorrected archive print.
UNSETTLED_2025_HOUR = 4334
EPS = 1e-9


def _cfg() -> dict:
    return json.loads((KEEPER_BUNDLE / "run_config.json").read_text())


def _published(year: int) -> pd.DataFrame:
    df = pd.read_parquet(
        REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
    )
    return df.set_index("hour").reindex(range(8760)).reset_index()


def _reserve_family(year: int) -> pd.DataFrame:
    rf = pd.read_parquet(KEEPER_BUNDLE / f"hourly/reserve_family_{year}.parquet")
    return rf[rf["pass"] == "P1"]


def _system_ordc_adder(year: int) -> np.ndarray:
    """Demand-weighted per-hour sidecar ordc_adder (the scored series' component)."""
    d = pd.read_parquet(KEEPER_BUNDLE / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    g = d.groupby("hour").apply(
        lambda x: np.average(x["ordc_adder"], weights=x["demand"]),
        include_groups=False,
    )
    return g.reindex(range(8760)).to_numpy(dtype=float)


def _lr_credit(year: int) -> np.ndarray:
    path = REPO / "data/raw/ercot-AS" / f"ercot_{year}_as_up_mw.parquet"
    if not path.exists():
        return np.zeros(8760)
    s = pd.read_parquet(path)["rrsufr_mw"].to_numpy(dtype=float)
    if len(s) < 8760:
        s = np.concatenate([s, np.zeros(8760 - len(s))])
    return s[:8760]


def _steps(cfg_sc: dict, mu: float, sigma: float, shift: float):
    """The armed LP demand steps at the given (annual-scalar) parameters."""
    req_total, pens, wids = ercot_ordc_demand_steps(
        voll=float(cfg_sc["ordc_voll"]),
        mcl_mw=float(cfg_sc["ordc_mcl_mw"]),
        mu_mw=mu,
        sigma_mw=sigma,
        shift_sigma=shift,
        multistep_floor=bool(cfg_sc["ordc_multistep_floor"]),
    )
    grid = np.concatenate([[req_total], req_total - np.cumsum(wids)])
    return req_total, pens, grid


def _price_at_level(level: np.ndarray, pens: np.ndarray, grid: np.ndarray):
    """Marginal step penalty at absolute reserve level(s) on the LP curve.

    Bands are ordered outermost (highest-reserve, cheapest) first; band j
    spans (grid[j+1], grid[j]] and is priced at its lower edge. The marginal
    band at level L is the one containing L; L >= grid[0] prices 0.
    """
    lv = np.asarray(level, dtype=float)
    # grid descends; find j with grid[j+1] <= L < grid[j]
    idx = np.searchsorted(-grid, -lv, side="right") - 1
    idx = np.clip(idx, 0, len(pens) - 1)
    out = pens[idx]
    return np.where(lv >= grid[0], 0.0, out)


def _stats(a: np.ndarray) -> dict:
    a = a[np.isfinite(a)]
    if len(a) == 0:
        return {}
    return {
        "n": int(len(a)),
        "mean": float(np.mean(a)),
        "p05": float(np.percentile(a, 5)),
        "p50": float(np.percentile(a, 50)),
        "p95": float(np.percentile(a, 95)),
        "min": float(np.min(a)),
        "max": float(np.max(a)),
    }


def _incidence(adder: np.ndarray, lam: np.ndarray | None = None) -> dict:
    a = np.nan_to_num(np.asarray(adder, dtype=float), nan=0.0)
    top50 = float(np.mean(np.sort(a)[-50:])) if len(a) >= 50 else None
    return {
        "h_gt_1": int((a > 1.0).sum()),
        "h_gt_10": int((a > 10.0).sum()),
        "h_gt_100": int((a > 100.0).sum()),
        "max": float(a.max()) if len(a) else 0.0,
        "mean": float(a.mean()) if len(a) else 0.0,
        "top50_mean": top50,
    }


def measure_year(year: int, cfg: dict) -> dict:
    sc = cfg["scenario_config"]
    pub = _published(year)
    rf = _reserve_family(year)
    tot = (
        rf[rf["family"] == "ercot_ordc_total"]
        .groupby("hour")[["dual", "requirement_mw", "held_mw", "shortfall_mw"]]
        .sum()
        .reindex(range(8760))
    )
    prod_held = (
        rf[rf["family"] != "ercot_ordc_total"]
        .groupby(["family", "hour"])["held_mw"]
        .sum()
        .unstack(level=0)
        .reindex(range(8760))
    )
    nonspin = prod_held.get("NonSpin", pd.Series(0.0, index=range(8760))).to_numpy(
        dtype=float
    )
    sys_adder = _system_ordc_adder(year)

    hours = np.arange(8760)
    live = (
        (hours < RTCB_GOLIVE_HOUR)
        if year == 2025
        else np.ones(8760, dtype=bool)
    )
    rtorpa = np.nan_to_num(pub["rtorpa"].to_numpy(dtype=float), nan=0.0)
    rtolcap = pub["rtolcap"].to_numpy(dtype=float)
    rtoffcap = pub["rtoffcap"].to_numpy(dtype=float)
    lam = pub["system_lambda"].to_numpy(dtype=float)
    telemetry_ok = np.isfinite(rtolcap) & np.isfinite(rtoffcap) & np.isfinite(lam)

    held = tot["held_mw"].to_numpy(dtype=float)
    req = tot["requirement_mw"].to_numpy(dtype=float)
    short = tot["shortfall_mw"].to_numpy(dtype=float)
    dual = np.abs(tot["dual"].to_numpy(dtype=float))

    # The armed curve (flat fallback at the keeper's resolved scalars).
    mu_flat = float(sc["ordc_lolp_mu_mw"])
    sig_flat = float(sc["ordc_lolp_sigma_mw"])
    shift = float(sc["ordc_lolp_shift_sigma"])
    req_total, pens_flat, grid_flat = _steps(sc, mu_flat, sig_flat, shift)
    credits = req_total - req  # what the solve netted off the demand side
    level = held + credits  # the marginal band's absolute reserve edge

    # Credit series the solve read, for the A0b requirement identity.
    lr = _lr_credit(year)
    sas = ercot_storage_as_reserve_mw(year, 8760)
    req_rebuilt = np.maximum(req_total - lr - sas, float(sc["ordc_mcl_mw"]))

    # The NP6-576-ER table (comparison ONLY; shift 0 per ordc-overlay.md), both
    # per-hour and collapsed to the annual-mean scalars the LP builder would
    # actually use (spec.py mu_s = mean(mu)).
    mu_tab, sig_tab = load_lolp_params(LOLP_TABLE, 8760)
    _, pens_tab_mean, grid_tab_mean = _steps(
        sc, float(np.mean(mu_tab)), float(np.mean(sig_tab)), 0.0
    )

    fired = (rtorpa > EPS) & live
    fired_settled = fired.copy()
    if year == 2025:
        fired_settled[UNSETTLED_2025_HOUR] = False
    model_fired = np.nan_to_num(sys_adder, nan=0.0) > EPS
    short_pos = np.nan_to_num(short, nan=0.0) > 1e-6

    # ---- A0: construction validation --------------------------------------
    a0_hours = short_pos & np.isfinite(level)
    pred = _price_at_level(level[a0_hours], pens_flat, grid_flat)
    a0 = {
        "shortfall_hours": int(a0_hours.sum()),
        "dual_vs_step_price_mean_abs_diff": (
            float(np.mean(np.abs(pred - dual[a0_hours]))) if a0_hours.any() else None
        ),
        "dual_vs_step_price_max_abs_diff": (
            float(np.max(np.abs(pred - dual[a0_hours]))) if a0_hours.any() else None
        ),
        "requirement_identity_max_abs_diff_mw": float(
            np.nanmax(np.abs(req - req_rebuilt))
        ),
        "req_total_mw": float(req_total),
        "no_shortfall_hours_dual_gt_eps": int((dual[~short_pos] > EPS).sum()),
    }

    # ---- A1: the crosswalk ------------------------------------------------
    def _xw(mask: np.ndarray) -> dict:
        m = mask & telemetry_ok & np.isfinite(held)
        return {
            "held_mw": _stats(held[m]),
            "B_model_held_plus_credits": _stats((held + credits)[m]),
            "rtolcap": _stats(rtolcap[m]),
            "rtolcap_plus_rtoffcap": _stats((rtolcap + rtoffcap)[m]),
            "B_model_minus_rtolcap": _stats((held + credits - rtolcap)[m]),
            "B_model_minus_rtol_plus_rtoff": _stats(
                (held + credits - rtolcap - rtoffcap)[m]
            ),
        }

    a1 = {
        "all_live_hours": _xw(live),
        "published_fired_hours": _xw(fired),
        "corr_B_model_vs_rtolcap_live": float(
            np.corrcoef(
                (held + credits)[live & telemetry_ok], rtolcap[live & telemetry_ok]
            )[0, 1]
        ),
    }

    # ---- A2: held-quantity + requirement basis at the fired hours ---------
    at_top = np.abs(np.nan_to_num(short, nan=0.0)) <= 1e-6
    a2 = {
        "fired_hours": int(fired.sum()),
        "fired_hours_settled": int(fired_settled.sum()),
        "fired_at_curve_top_no_shortfall": int((fired & at_top).sum()),
        "fired_with_shortfall": int((fired & short_pos).sum()),
        "fired_model_fired_overlap": int((fired & model_fired).sum()),
        "model_fired_hours": int(model_fired.sum()),
        "credits_mw_fired": _stats(credits[fired]),
        "lr_credit_mw_fired": _stats(lr[fired]),
        "storage_as_credit_mw_fired": _stats(sas[fired]),
        "requirement_mw_fired": _stats(req[fired]),
        "held_mw_fired": _stats(held[fired]),
        "marginal_level_mw_fired": _stats(level[fired]),
    }

    # ---- A3: supply-cap basis in the shortfall hours ----------------------
    sh = short_pos & telemetry_ok
    cap_all = rtolcap + rtoffcap
    a3 = {
        "shortfall_hours": int(short_pos.sum()),
        "shortfall_and_published_fired": int((short_pos & fired).sum()),
        "held_at_cap_all_within_1mw": int(
            (sh & (np.abs(held - cap_all) <= 1.0)).sum()
        ),
        "held_at_rtolcap_within_1mw": int(
            (sh & (np.abs(held - rtolcap) <= 1.0)).sum()
        ),
        "held_minus_cap_all_mw": _stats((held - cap_all)[sh]),
        "marginal_level_minus_rtolcap_mw": _stats((level - rtolcap)[sh]),
        "marginal_level_mw": _stats(level[sh]),
        "dual_in_shortfall_hours": _stats(dual[sh]),
        "shortfall_depth_mw": _stats(short[sh]),
    }

    # ---- A4: demand-curve placement (curves x bases at the fired hours) ---
    floor_act = floor_active_mask(year, 8760)
    ok = fired & telemetry_ok

    def _pub_form(mu, sigma, shift_s):
        a = ordc_adder(
            cap_all[ok],
            lam[ok],
            voll=float(sc["ordc_voll"]),
            mcl_mw=float(sc["ordc_mcl_mw"]),
            mu_mw=np.asarray(mu)[ok] if np.ndim(mu) else mu,
            sigma_mw=np.asarray(sigma)[ok] if np.ndim(sigma) else sigma,
            shift_sigma=shift_s,
            multistep_floor=bool(sc["ordc_multistep_floor"]),
            floor_active=floor_act[ok],
            reserves_online_mw=rtolcap[ok],
        )
        full = np.zeros(8760)
        full[ok] = a
        return full

    a4 = {
        "published_rtorpa_fired": _incidence(rtorpa[fired]),
        "model_dual_fired": _incidence(dual[fired]),
        # LP single-level step pricing at the model's own marginal level:
        "flat_curve_at_model_level": _incidence(
            _price_at_level(level[fired], pens_flat, grid_flat)
        ),
        # LP pricing had the NP6 table been armed (annual-mean collapse, spec.py):
        "table_annualmean_curve_at_model_level": _incidence(
            _price_at_level(level[fired], pens_tab_mean, grid_tab_mean)
        ),
        # Published two-basis form on measured telemetry (the B0 construction):
        "flat_published_form_on_telemetry": _incidence(
            _pub_form(mu_flat, sig_flat, shift)[fired]
        ),
        "table_published_form_on_telemetry": _incidence(
            _pub_form(mu_tab, sig_tab, 0.0)[fired]
        ),
        # The same published two-basis form fed the MODEL's bases — full-hour
        # term at held+credits, half-hour term at the online (non-NonSpin)
        # held + credits: isolates basis-vs-curve.
        "flat_published_form_on_model_basis": _incidence(
            np.where(
                fired,
                ordc_adder(
                    np.nan_to_num(level, nan=1e9),
                    np.nan_to_num(lam, nan=0.0),
                    voll=float(sc["ordc_voll"]),
                    mcl_mw=float(sc["ordc_mcl_mw"]),
                    mu_mw=mu_flat,
                    sigma_mw=sig_flat,
                    shift_sigma=shift,
                    multistep_floor=bool(sc["ordc_multistep_floor"]),
                    floor_active=floor_act,
                    reserves_online_mw=np.nan_to_num(
                        held - nonspin + credits, nan=1e9
                    ),
                ),
                0.0,
            )[fired]
        ),
    }

    # ---- A5: floor date-gating -------------------------------------------
    pre_nov_2023 = hours < 7296  # 2023-11-01 00:00 on the non-leap clock
    a5 = {
        "floor_active_full_window": bool(floor_act[live].all()) if year > 2023 else False,
        "fired_hours_rtolcap_le_7000": int((fired & (rtolcap <= 7000)).sum()),
        "fired_hours_model_level_le_7000": int(
            (fired & np.nan_to_num(level <= 7000)).sum()
        ),
    }
    if year == 2023:
        a5["pre_nov_hours_model_level_le_7000"] = int(
            (pre_nov_2023 & np.nan_to_num(level <= 7000)).sum()
        )
        a5["pre_nov_hours_model_priced_dual_gt_1"] = int(
            (pre_nov_2023 & (dual > 1.0)).sum()
        )
        a5["pre_nov_hours_published_fired"] = int((fired & pre_nov_2023).sum())

    # ---- V4/V5: the candidate's out-of-LP implied series ------------------
    # C-A composite (basis consistency + published two-basis form), evaluated
    # from committed telemetry alone on the ARMED flat curve, marginal level
    # capped at the curve span (min(req_total, telemetry)); model headroom is
    # unobservable in the sidecars and could only RAISE incidence (caveat).
    cand = np.where(
        telemetry_ok & live,
        ordc_adder(
            np.minimum(np.nan_to_num(cap_all, nan=1e9), req_total),
            np.nan_to_num(lam, nan=0.0),
            voll=float(sc["ordc_voll"]),
            mcl_mw=float(sc["ordc_mcl_mw"]),
            mu_mw=mu_flat,
            sigma_mw=sig_flat,
            shift_sigma=shift,
            multistep_floor=bool(sc["ordc_multistep_floor"]),
            floor_active=floor_act,
            reserves_online_mw=np.minimum(np.nan_to_num(rtolcap, nan=1e9), req_total),
        ),
        0.0,
    )
    cand_settled = cand.copy()
    if year == 2025:
        cand_settled[UNSETTLED_2025_HOUR] = 0.0
    v = {
        "candidate_implied_all_live_hours": _incidence(cand[live]),
        "candidate_implied_settled": _incidence(cand_settled[live]),
        "published_rtorpa_settled_all_hours": _incidence(
            np.where(fired_settled, rtorpa, 0.0)[live]
        ),
    }

    return {
        "year": year,
        "A0_construction_validation": a0,
        "A1_crosswalk": a1,
        "A2_held_requirement_basis": a2,
        "A3_supply_cap_basis": a3,
        "A4_curve_placement": a4,
        "A5_floor_date_gating": a5,
        "V_candidate_out_of_lp": v,
    }


def main() -> None:
    cfg = _cfg()
    sc = cfg["scenario_config"]
    years = {y: measure_year(y, cfg) for y in YEARS}

    mu_tab, sig_tab = load_lolp_params(LOLP_TABLE, 8760)
    result = {
        "session": "ercot-212",
        "phase": "0 (RESERVE-BASIS-1) — READ ONLY, no LP, no year solved or scored",
        "precommit": "docs/PRECOMMIT-ercot212-reserve-basis-phase0-2026-08-16.md",
        "keeper": KEEPER_ID,
        "keeper_bundle": str(KEEPER_BUNDLE.relative_to(REPO)),
        "keeper_git_sha": cfg.get("git", {}).get("sha"),
        "armed_curve": {
            "ordc_voll": sc["ordc_voll"],
            "ordc_mcl_mw": sc["ordc_mcl_mw"],
            "ordc_lolp_mu_mw": sc["ordc_lolp_mu_mw"],
            "ordc_lolp_sigma_mw": sc["ordc_lolp_sigma_mw"],
            "ordc_lolp_shift_sigma": sc["ordc_lolp_shift_sigma"],
            "ordc_lolp_params_path": sc["ordc_lolp_params_path"],
            "ordc_multistep_floor": sc["ordc_multistep_floor"],
        },
        "np6_table_annual_means": {
            "mu_mw": float(np.mean(mu_tab)),
            "sigma_mw": float(np.mean(sig_tab)),
        },
        "years": years,
    }
    out = REPO / "results/calibration/ercot212_reserve_basis_phase0.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"wrote {out.relative_to(REPO)}")
    for y in YEARS:
        r = years[y]
        print(
            f"{y}: fired {r['A2_held_requirement_basis']['fired_hours']} h | "
            f"at curve top {r['A2_held_requirement_basis']['fired_at_curve_top_no_shortfall']} | "
            f"model dual >$1 {r['A4_curve_placement']['model_dual_fired']['h_gt_1']} | "
            f"candidate >$1 {r['V_candidate_out_of_lp']['candidate_implied_settled']['h_gt_1']}"
        )


if __name__ == "__main__":
    main()
