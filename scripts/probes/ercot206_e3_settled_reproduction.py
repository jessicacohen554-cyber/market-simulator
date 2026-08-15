"""ercot-206 Phase B0: the FFR-8A §1.1(b) ORDC reproduction test on the SETTLED basis.

Read-only probe over COMMITTED measured artifacts — no LP, no solve, no model
output read, no year scored. Pre-registered in
``docs/PRECOMMIT-ercot206-e3-reopen-b0-2026-08-15.md`` §3–§4 (pushed before this
probe ran).

Construction: identical to FFR-8A ``leg_ab``
(``scripts/probes/ffr8a_scarcity_decomposition.py``) — the implemented
``results.scarcity.ordc_adder`` evaluated on the measured NP6-905-CD
RTOLCAP/RTOFFCAP series at both in-repo parameter sets (flat fallback mu=0,
sigma=1400; committed NP6-576-ER seasonal table) — with ONE change: the measured
RTORPA side is **settlement-closed** first by the ercot-198 guard (archive
RTORPA+RTORDPA > settled hub RTSPP + $50 => the archive print never settled and
is zeroed; every flagged hour is reported). 2025 is restricted to the
pre-RTC+B-go-live 8,112 ORDC-regime hours, as in FFR-8A.

Verdict years {2024, 2025}; the §4 REPRODUCES rule is applied mechanically and
the branch (validate one set / both / NEITHER) is emitted by the probe, not
judged afterwards. 2023 is reported as a context block at full magnitude
(``floor_active_mask(2023)`` honoured) with ZERO verdict weight, pre-declared.

Usage::

    python scripts/probes/ercot206_e3_settled_reproduction.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    floor_active_mask,
    load_lolp_params,
    ordc_adder,
)

CURATED = REPO / "data" / "raw" / "ercot" / "ercot_{year}_ordc_reserves_hourly.parquet"
ACTUAL_HOURLY = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
LOLP_TABLE = REPO / "data" / "raw" / "_validation-source" / "ercot_ordc_lolp_params.csv"
OUT = REPO / "results" / "calibration" / "ercot206_e3_settled_reproduction.json"

VERDICT_YEARS = (2024, 2025)
CONTEXT_YEARS = (2023,)
HOURS = 8760
RTCB_GOLIVE_HOUR = 338 * 24  # 2025-12-05 00:00, non-leap clock (scarcity module)
CORRECTION_MARGIN = 50.0  # ercot-198 settlement-closure guard ($/MWh)


def _dense(series: pd.Series, hours: int = HOURS) -> np.ndarray:
    return series.reindex(range(hours)).to_numpy(dtype=float)


def _stats(x: np.ndarray) -> dict:
    return {
        "mean": round(float(x.mean()), 4),
        "max": round(float(x.max()), 2),
        "h_gt_1": int((x > 1).sum()),
        "h_gt_10": int((x > 10).sum()),
        "h_gt_100": int((x > 100).sum()),
        "top50_mean": round(float(np.sort(x)[-50:].mean()), 3),
    }


def _reproduces(model: dict, meas: dict) -> dict:
    """The §4 rule, mechanically: (a) top-50 magnitude, (b) $1/$10 counts, (c) $100."""

    def _ratio_ok(m: float, a: float) -> bool:
        return a > 0 and 0.5 <= (m / a) <= 2.0

    if meas["top50_mean"] < 0.50:
        leg_a = abs(model["top50_mean"] - meas["top50_mean"]) <= 1.00
    else:
        leg_a = _ratio_ok(model["top50_mean"], meas["top50_mean"])
    legs_b = {}
    for t in (1, 10):
        m, a = model[f"h_gt_{t}"], meas[f"h_gt_{t}"]
        legs_b[f"h_gt_{t}"] = (m <= 2) if a == 0 else (_ratio_ok(m, a) or abs(m - a) <= 2)
    m, a = model["h_gt_100"], meas["h_gt_100"]
    leg_c = abs(m - a) <= 2 or _ratio_ok(m, a)
    return {
        "a_top50": bool(leg_a),
        "b_counts": {k: bool(v) for k, v in legs_b.items()},
        "c_deep_tail": bool(leg_c),
        "reproduces": bool(leg_a and all(legs_b.values()) and leg_c),
    }


def run_year(year: int, config: ScenarioConfig, actual: pd.DataFrame) -> dict:
    cur = pd.read_parquet(
        Path(str(CURATED).format(year=year))
    ).set_index("hour")
    n = RTCB_GOLIVE_HOUR if year == 2025 else HOURS
    pub_rtorpa = np.nan_to_num(_dense(cur["rtorpa"], n), nan=np.nan)
    pub_rtordpa = np.nan_to_num(_dense(cur["rtordpa"], n), nan=0.0)
    lam = _dense(cur["system_lambda"], n)
    rtolcap = _dense(cur["rtolcap"], n)
    rtoffcap = _dense(cur["rtoffcap"], n)

    # Settlement-closure guard (ercot-198): archive prints that never settled.
    rt = _dense(actual[actual["year"] == year].set_index("hour")["rt"], n)
    adder_total = np.nan_to_num(pub_rtorpa, nan=0.0) + pub_rtordpa
    flagged = np.where(adder_total > rt + CORRECTION_MARGIN)[0]
    flag_rows = [
        {
            "hour": int(h),
            "archive_rtorpa": round(float(pub_rtorpa[h]), 2),
            "archive_rtordpa": round(float(pub_rtordpa[h]), 2),
            "settled_hub_rtspp": round(float(rt[h]), 2),
            "system_lambda": round(float(lam[h]), 2),
        }
        for h in flagged
    ]
    settled_rtorpa = pub_rtorpa.copy()
    settled_rtorpa[flagged] = 0.0

    ok = (
        np.isfinite(lam)
        & np.isfinite(rtolcap)
        & np.isfinite(rtoffcap)
        & np.isfinite(settled_rtorpa)
    )
    hour_of_year = np.arange(n)[ok]
    lam_v, rol_v, rof_v = lam[ok], rtolcap[ok], rtoffcap[ok]
    meas_v = settled_rtorpa[ok]
    r_full = rol_v + rof_v

    if year == 2023:
        floor_act = floor_active_mask(2023, n)[hour_of_year]
    else:
        floor_act = True

    out: dict = {
        "n_hours": int(ok.sum()),
        "n_flagged_unsettled": len(flag_rows),
        "flagged_hours": flag_rows,
        "measured_settled": _stats(meas_v),
    }
    for label, table in (("fallback", False), ("np6_576_er", True)):
        if table:
            mu, sigma = load_lolp_params(LOLP_TABLE, HOURS)
            mu, sigma = mu[hour_of_year], sigma[hour_of_year]
        else:
            mu, sigma = config.ordc_lolp_mu_mw, config.ordc_lolp_sigma_mw
        model = ordc_adder(
            r_full,
            lam_v,
            voll=config.ordc_voll,
            mcl_mw=config.ordc_mcl_mw,
            mu_mw=mu,
            sigma_mw=sigma,
            shift_sigma=config.ordc_lolp_shift_sigma,
            multistep_floor=config.ordc_multistep_floor,
            floor_active=floor_act,
            reserves_online_mw=rol_v,
        )
        blk = {"curve": _stats(model)}
        if year in VERDICT_YEARS:
            blk["rule"] = _reproduces(blk["curve"], out["measured_settled"])
        out[label] = blk
    return out


def main() -> None:
    config = ScenarioConfig(iso="ERCOT")  # shipped defaults = the keeper's ORDC params
    actual = pd.read_parquet(ACTUAL_HOURLY)
    result: dict = {
        "probe": "ercot206_e3_settled_reproduction",
        "precommit": "docs/PRECOMMIT-ercot206-e3-reopen-b0-2026-08-15.md",
        "guard": f"archive RTORPA+RTORDPA > settled hub RTSPP + ${CORRECTION_MARGIN:.0f}",
        "construction": "FFR-8A leg_ab (ordc_adder on measured RTOLCAP/RTOFFCAP)",
        "verdict_years": list(VERDICT_YEARS),
        "context_years_zero_verdict_weight": list(CONTEXT_YEARS),
        "years": {},
    }
    for year in (*CONTEXT_YEARS, *VERDICT_YEARS):
        result["years"][str(year)] = run_year(year, config, actual)

    both = {}
    for label in ("fallback", "np6_576_er"):
        both[label] = all(
            result["years"][str(y)][label]["rule"]["reproduces"] for y in VERDICT_YEARS
        )
    winners = [k for k, v in both.items() if v]
    if len(winners) == 1:
        branch = f"VALIDATED:{winners[0]}"
    elif len(winners) == 2:
        branch = "VALIDATED:np6_576_er (pre-registered legitimacy tiebreak)"
    else:
        branch = "NEITHER — E3 stays escalated; lane STOPS at B0"
    result["reproduces_both"] = both
    result["branch"] = branch

    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: result[k] for k in ("reproduces_both", "branch")}, indent=1))
    for y in ("2023", "2024", "2025"):
        b = result["years"][y]
        print(f"\n{y}: n={b['n_hours']} flagged={b['n_flagged_unsettled']}")
        print("  measured(settled):", b["measured_settled"])
        for label in ("fallback", "np6_576_er"):
            print(f"  {label}:", b[label]["curve"], b[label].get("rule", {}).get("reproduces"))


if __name__ == "__main__":
    main()
