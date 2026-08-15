"""ERCOT-204 Phase-0 gate: is the published-RTORPA overlay an ADMISSIBLE lever?

Read-only. No LP is built, no year is solved or scored, no ``ScenarioConfig``
field is added or read for arming. Answers the chartered ERCOT-204 question --
"complete the 2024 published-adder overlay by adding the missing published
RTORPA" -- against three tests that are decided BEFORE any residual is
consulted (rule 1 ``[R-STRUCT]``):

  G1  ARMED-STATE (the T-1 discipline). Read the keeper's RESOLVED
      ``run_config.json`` -- what the LP actually ran, rule 24 ``[R-REGISTRY]``
      -- not ``scenarios.py`` defaults. Is the model's RTORPA counterpart
      already armed?
  G2  RULE 19 ``[R-ONE-MECH]``. If an endogenous mechanism for the same
      phenomenon is armed, an overlay of the published series is a SECOND
      mechanism stacked on the first's unexplained residual.
  G3  RULE 13 ``[R-MEASURED]`` forward-analogue test. "Could this same
      quantity be produced for a forward year from forward drivers, and would
      it respond to changed conditions?" RTORPA is a deterministic FUNCTION of
      realized reserve levels through the published ORDC curve, so its forward
      analogue is the endogenous computation itself -- overlaying the measured
      series substitutes a measured OUTCOME for that computation.

Then measures the object the gate leaves standing: WHY the armed endogenous
mechanism reads ~zero in 2024/2025 but prices in 2023, by comparing the
model's own held ORDC-total reserve against the published ``rtolcap`` in the
hours the published RTORPA actually fired.

Sources, all already committed (no intake performed):
  data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet   (NP6-905-CD)
  results/calibration/<keeper>/hourly/{system,reserve_family}_<year>.parquet
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER_BUNDLE = REPO / "results/calibration/ercot202_plantphysics_B"
KEEPER_ID = "2026-08-14-ercot202-arm-plantphysics"
YEARS = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]: ERCOT holds no marker.

# The RTC+B go-live hour on the non-leap 8760 clock (2025-12-05 00:00 CST).
# Past it the pre-RTC+B adder regime does not exist; the published series ends
# there and carries no content by design.
RTCB_GOLIVE_HOUR = 338 * 24


def _published(year: int) -> pd.DataFrame:
    """Published NP6-905-CD hourly adders + reserve capacity for ``year``."""
    return pd.read_parquet(
        REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
    )


def _system_hourly(year: int) -> pd.DataFrame:
    """Keeper P1 system sidecar collapsed to one demand-weighted row per hour."""
    d = pd.read_parquet(KEEPER_BUNDLE / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    out = d.groupby("hour").apply(
        lambda x: pd.Series(
            {
                "ordc_adder": np.average(x["ordc_adder"], weights=x["demand"]),
                "rtordpa_overlay": np.average(
                    x["rtordpa_overlay"], weights=x["demand"]
                ),
                "price": np.average(x["price"], weights=x["demand"]),
                "demand": x["demand"].sum(),
            }
        ),
        include_groups=False,
    )
    return out.reset_index()


def _dw(series: pd.Series, weights: pd.Series) -> float:
    """Demand-weighted mean, the keeper's own weighting (bench convention)."""
    return float(np.average(series, weights=weights))


def measure_year(year: int) -> dict:
    """Measure the published-vs-committed adder split and the tightness gap."""
    pub = _published(year)
    sysh = _system_hourly(year)
    m = sysh.merge(pub, on="hour", how="inner")
    w = m["demand"]

    # The pre-RTC+B regime window. 2025's published series stops at go-live.
    live = m["hour"] < RTCB_GOLIVE_HOUR if year == 2025 else m["hour"] >= 0

    ordc_nonzero = m["ordc_adder"] > 1e-9
    rtorpa_fired = (m["rtorpa"] > 1e-9) & live

    # Model-held ORDC-total reserve vs published online reserve capacity, in
    # the hours the published RTORPA priced. This is the structural question
    # the gate leaves standing: is the mechanism broken, or is the model's
    # reserve simply never in the curve's pricing region?
    rf = pd.read_parquet(KEEPER_BUNDLE / f"hourly/reserve_family_{year}.parquet")
    rf = rf[(rf["pass"] == "P1") & (rf["family"] == "ercot_ordc_total")]
    rf = rf.groupby("hour")[["held_mw", "requirement_mw", "shortfall_mw"]].sum()
    m = m.merge(rf, on="hour", how="left")

    fired = m[rtorpa_fired]
    return {
        "year": year,
        "hours": int(len(m)),
        # --- the committed vs published split (ercot-198's object, re-measured
        #     on the CURRENT keeper rather than inherited from run192) ---
        "published_rtorpa_dw": _dw(m["rtorpa"].where(live, 0.0), w),
        "published_rtordpa_dw": _dw(m["rtordpa"].where(live, 0.0), w),
        "published_total_dw": _dw(
            (m["rtorpa"] + m["rtordpa"]).where(live, 0.0), w
        ),
        "committed_rtordpa_overlay_dw": _dw(m["rtordpa_overlay"], w),
        "committed_ordc_adder_dw": _dw(m["ordc_adder"], w),
        "committed_total_dw": _dw(m["rtordpa_overlay"] + m["ordc_adder"], w),
        # --- the armed overlay half is EXACT (ercot-198 verified; re-verified
        #     here on the current keeper) ---
        "rtordpa_overlay_max_abs_diff": float(
            (m["rtordpa_overlay"] - m["rtordpa"].where(live, 0.0)).abs().max()
        ),
        # --- the endogenous RTORPA counterpart's realized behaviour ---
        "ordc_adder_nonzero_hours": int(ordc_nonzero.sum()),
        "ordc_adder_max": float(m["ordc_adder"].max()),
        "published_rtorpa_nonzero_hours": int(rtorpa_fired.sum()),
        "published_rtorpa_max": float(m["rtorpa"].where(live, 0.0).max()),
        # --- the tightness comparison in the hours RTORPA priced ---
        "fired_hours_model_held_mw_mean": (
            float(fired["held_mw"].mean()) if len(fired) else None
        ),
        "fired_hours_published_rtolcap_mean": (
            float(fired["rtolcap"].mean()) if len(fired) else None
        ),
        "fired_hours_model_shortfall_mw_mean": (
            float(fired["shortfall_mw"].mean()) if len(fired) else None
        ),
        "fired_hours_model_shortfall_nonzero": (
            int((fired["shortfall_mw"] > 1e-6).sum()) if len(fired) else 0
        ),
        "overlap_hours_both_nonzero": int((ordc_nonzero & rtorpa_fired).sum()),
    }


def monthly_gap(year: int) -> dict:
    """Month-grain published-minus-committed gap, demand-weighted."""
    pub = _published(year)
    sysh = _system_hourly(year)
    m = sysh.merge(pub, on="hour", how="inner")
    live = m["hour"] < RTCB_GOLIVE_HOUR if year == 2025 else m["hour"] >= 0
    m["month"] = (
        pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(m["hour"], unit="h")
    ).dt.month
    m["pub_total"] = (m["rtorpa"] + m["rtordpa"]).where(live, 0.0)
    m["com_total"] = m["rtordpa_overlay"] + m["ordc_adder"]
    out = {}
    for mo, g in m.groupby("month"):
        out[int(mo)] = {
            "published": _dw(g["pub_total"], g["demand"]),
            "committed": _dw(g["com_total"], g["demand"]),
            "gap": _dw(g["pub_total"] - g["com_total"], g["demand"]),
        }
    return out


def main() -> None:
    cfg = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())
    sc = cfg["scenario_config"]
    flags = cfg["calibration_flags"]

    # G1 -- ARMED STATE, read from the RESOLVED config the LP actually ran.
    armed = {
        "ercot_ordc_total_reserve": sc.get("ercot_ordc_total_reserve"),
        "energy_reserve_coopt": sc.get("energy_reserve_coopt"),
        "ordc_multistep_floor": sc.get("ordc_multistep_floor"),
        "ercot_ordc_only_scarcity": sc.get("ercot_ordc_only_scarcity"),
        "ercot_thermal_as_endogenous": sc.get("ercot_thermal_as_endogenous"),
        "ercot_multiproduct_as_coopt": sc.get("ercot_multiproduct_as_coopt"),
        "ercot_rtordpa_overlay": flags.get("ercot_rtordpa_overlay"),
    }
    # The chartered delta would need a field/flag that does not exist. Record
    # its absence explicitly rather than inferring it.
    rtorpa_overlay_channel_exists = any(
        "rtorpa_overlay" in k for k in list(sc) + list(flags)
    )

    years = {y: measure_year(y) for y in YEARS}
    months = {y: monthly_gap(y) for y in YEARS}

    result = {
        "session": "ercot-204",
        "phase": "0 (admissibility gate) -- READ ONLY, no LP, no year solved or scored",
        "keeper": KEEPER_ID,
        "keeper_bundle": str(KEEPER_BUNDLE.relative_to(REPO)),
        "keeper_git_sha": cfg.get("git", {}).get("sha"),
        "G1_armed_state": armed,
        "G1_rtorpa_overlay_channel_exists": rtorpa_overlay_channel_exists,
        "G2_rule19_collision": (
            "ercot_ordc_total_reserve=True AND energy_reserve_coopt=True are ARMED "
            "on the keeper: the LP enforces the published ORDC total-reserve demand "
            "curve and its dual IS the model's RTORPA. A published-RTORPA overlay "
            "would be a SECOND mechanism for the same phenomenon, stacked on the "
            "first's unexplained residual -- rule 19 [R-ONE-MECH] verbatim."
        ),
        "G3_rule13_forward_analogue": (
            "RTORPA is not an independent market datum: it is a deterministic "
            "function of realized reserve levels through the published ORDC curve "
            "(adder = LOLP(R) x (VOLL - lambda), Nodal Protocols 6.5.7.3). Its "
            "forward analogue IS the endogenous computation the model already "
            "performs, so overlaying the measured series substitutes a measured "
            "OUTCOME for the mechanism under validation -- the forbidden half of "
            "rule 13 [R-MEASURED]. Contrast RTORDPA (armed as an overlay): it "
            "prices discretionary out-of-market RUC/ECRS DEPLOYMENTS, an operator "
            "action with no endogenous counterpart in the model. That asymmetry is "
            "why one is admissible as an overlay and the other is not."
        ),
        "years": years,
        "months": months,
        "CAVEAT_settlement_closure_guard": (
            "This probe reports the RAW NP6-905-CD archive. ercot-198 applied a "
            "settlement-closure guard that rejected ONE uncorrected archive print "
            "(2025 h4334, Jun-30 14:00: archive RTORPA $414.12/h against a settled "
            "hub RTSPP of $54.96 -- price-corrected, never settled). That single "
            "hour is the entire distance between this probe's 2025 published "
            "RTORPA (0.0787 dw) and ercot-198's guarded 0.015. The 2024 numbers "
            "are unaffected and reproduce ercot-198 exactly (0.2368 vs 0.237). "
            "Neither number changes the gate: the gate turns on admissibility, "
            "not on magnitude."
        ),
        "CAVEAT_tightness_basis": (
            "fired_hours_model_held_mw_mean (the ercot_ordc_total family's held MW "
            "in the keeper's reserve_family sidecar) and "
            "fired_hours_published_rtolcap_mean (NP6-905-CD RTOLCAP) are "
            "CONSTRUCTED DIFFERENTLY and are not an identity: the model family is "
            "the LP's online reserve balance row, RTOLCAP is ERCOT's telemetered "
            "on-line reserve capacity. The comparison is INDICATIVE of where each "
            "system's reserve sits, not a like-for-like reconciliation, and no "
            "lever is derived from it here. It is reported because it falsifies "
            "the simplest explanation of the mechanism's silence (see "
            "STRUCTURAL_FINDING)."
        ),
        "STRUCTURAL_FINDING": (
            "The armed endogenous mechanism is NOT broken. In 2023 it fires in 42 "
            "hours at up to $1,920/h and ALL 42 fall inside the 1,705 hours the "
            "published RTORPA priced (overlap 42/42), with the model's held ORDC "
            "reserve within 0.2 % of published RTOLCAP (8,122 vs 8,108 MW). In "
            "2024/2025 it reads ~zero across 560/253 published-fired hours -- and "
            "the simplest explanation, 'the model's system is comfortable in those "
            "hours', is FALSIFIED: the model holds materially LESS reserve than the "
            "real system did (2024 6,955 vs 8,854 MW; 2025 6,638 vs 9,654 MW) and "
            "still does not price, while its own ORDC-total row records non-zero "
            "shortfall in 40 (2024) and 4 (2025) of those hours. Where the ORDC "
            "pricing region sits relative to the model's reserve representation is "
            "therefore the open object -- a MECHANISM question about the "
            "co-optimized reserve dual, exactly as ercot-203b filed it. It is "
            "measured and handed to the owner here, NOT chartered: no lever is "
            "prepared, and the adjacent L-SCAR tightness identification is "
            "DO-NOT-REDO (V0 adjudication)."
        ),
    }

    out = REPO / "results/calibration/ercot204_rtorpa_admissibility.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"wrote {out.relative_to(REPO)}")
    for y in YEARS:
        r = years[y]
        print(
            f"{y}: published RTORPA dw {r['published_rtorpa_dw']:.4f} "
            f"({r['published_rtorpa_nonzero_hours']} h) | endogenous ordc_adder dw "
            f"{r['committed_ordc_adder_dw']:.4f} ({r['ordc_adder_nonzero_hours']} h) "
            f"| overlay exact to {r['rtordpa_overlay_max_abs_diff']:.2e}"
        )


if __name__ == "__main__":
    main()
