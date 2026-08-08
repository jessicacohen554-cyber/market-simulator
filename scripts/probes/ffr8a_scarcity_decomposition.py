"""FFR-8A Phase-1 Part A: measured-data diagnosis of the lookahead's missing scarcity.

Read-only probe over COMMITTED measured artifacts (no solve, no model output, no
2022/pre-2023 read). Three legs, pre-registered in
``docs/handoffs/ffr-8a-scarcity-restoration-2026-08-08.md`` §1.1–§1.2:

* **(a) the reserve QUANTITY benchmark** — the measured RTOLCAP/RTOFFCAP
  distribution (NP6-905-CD) the published ORDC actually prices, and the curve's
  knee levels (reserves at adder = $10/$100/$1000) under both in-repo parameter
  sets, so the arm's pro-forma headroom (Part B, from the control-arm dump) can
  be placed against both.
* **(b) the curve REPRODUCTION test** — the implemented ``ordc_adder`` evaluated
  on the MEASURED reserve series against the MEASURED ``rtorpa`` series, at the
  flat fallback params (mu=0, sigma=1400 — the arm's as-run tail) and at the
  committed NP6-576-ER table. A transcription validation of a published formula
  against the formula's own published output — nothing is fitted. Includes the
  measured decomposition of the year's h>$100 price hours into lambda-driven vs
  adder-driven (the ceiling any adder-side repair can reach).
* **(d) the AS-quantity scope check** — the model's forward AS-requirement model
  (NP3-160-CD methodology) vs the measured ASPLANNP433 plan for 2024/2025, per
  product; scopes repair element E2 without any new intake. Requires the clean
  demand/VRE store (run after ``regenerate_clean``); skipped cleanly if absent.

Usage::

    uv run python scripts/probes/ffr8a_scarcity_decomposition.py \
        --out docs/handoffs/ffr-8a/part-a-measured-2026-08-08.json [--skip-d]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    load_lolp_params,
    ordc_adder,
)

YEARS = (2024, 2025)
LOLP_TABLE = RAW_DATA_DIR / "_validation-source" / "ercot_ordc_lolp_params.csv"
# 2025-12-05 00:00 RTC+B go-live on the non-leap clock (scarcity.RTCB_GOLIVE_HOUR).
RTCB_GOLIVE_HOUR = 338 * 24


def _quantiles(x: np.ndarray) -> dict:
    """Duration-curve summary of a measured MW/price series (NaN-safe)."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return {}
    qs = {f"p{q}": float(np.percentile(x, q)) for q in (1, 5, 10, 25, 50, 75, 90, 95, 99)}
    return {"n": int(x.size), "mean": float(x.mean()), "min": float(x.min()), "max": float(x.max()), **qs}


def _params(config: ScenarioConfig, hours: int, table: bool):
    """(mu, sigma) at the flat fallback or the committed NP6-576-ER table."""
    if table:
        return load_lolp_params(LOLP_TABLE, hours)
    return config.ordc_lolp_mu_mw, config.ordc_lolp_sigma_mw


def _knee_table(config: ScenarioConfig, table: bool, lam: float = 30.0) -> dict:
    """Reserve level at which the curve's adder reaches $10/$100/$1000.

    Single-tier view (online == full == R) at a representative lambda; the curve
    is monotone in R so bisection is exact. Seasonal-table params are evaluated
    at each season's own (mu, sigma) — reported per season.
    """
    if table:
        mu_h, sig_h = load_lolp_params(LOLP_TABLE, 8760)
        # One representative hour per season (the committed table is TOD-flat).
        season_hours = {"winter": 0, "spring": 24 * 90, "summer": 24 * 182, "fall": 24 * 274}
        cases = {s: (float(np.asarray(mu_h)[h]), float(np.asarray(sig_h)[h])) for s, h in season_hours.items()}
    else:
        cases = {"flat": (float(config.ordc_lolp_mu_mw), float(config.ordc_lolp_sigma_mw))}
    out = {}
    for name, (mu, sigma) in cases.items():
        row = {"mu_mw": mu, "sigma_mw": sigma}
        for target in (10.0, 100.0, 1000.0):
            lo, hi = 0.0, 30000.0
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                a = ordc_adder(
                    np.array([mid]),
                    np.array([lam]),
                    voll=config.ordc_voll,
                    mcl_mw=config.ordc_mcl_mw,
                    mu_mw=mu,
                    sigma_mw=sigma,
                    shift_sigma=config.ordc_lolp_shift_sigma,
                    multistep_floor=config.ordc_multistep_floor,
                    floor_active=True,
                    reserves_online_mw=np.array([mid]),
                )
                if float(a[0]) >= target:
                    lo = mid
                else:
                    hi = mid
            row[f"r_at_${int(target)}_mw"] = round(0.5 * (lo + hi), 1)
        out[name] = row
    return out


def leg_ab(config: ScenarioConfig) -> dict:
    """Legs (a) and (b): measured reserve benchmark + curve reproduction."""
    import pandas as pd

    out: dict = {"lolp_table_path": str(LOLP_TABLE.relative_to(REPO))}
    out["knee"] = {
        "fallback": _knee_table(config, table=False),
        "np6_576_er": _knee_table(config, table=True),
    }
    for year in YEARS:
        path = RAW_DATA_DIR / "ercot" / f"ercot_{year}_ordc_reserves_hourly.parquet"
        df = pd.read_parquet(path)
        # 2025: the ORDC regime ends at the RTC+B go-live; the tail is NaN by
        # construction — restrict every read to the ORDC-regime hours.
        if year == 2025:
            df = df.iloc[:RTCB_GOLIVE_HOUR]
        lam = df["system_lambda"].to_numpy(dtype=float)
        rtolcap = df["rtolcap"].to_numpy(dtype=float)
        rtoffcap = df["rtoffcap"].to_numpy(dtype=float)
        rtorpa = df["rtorpa"].to_numpy(dtype=float)
        rtordpa = df["rtordpa"].to_numpy(dtype=float)
        hour_of_year = df["hour"].to_numpy(dtype=int)
        ok = np.isfinite(lam) & np.isfinite(rtolcap) & np.isfinite(rtoffcap) & np.isfinite(rtorpa)
        lam, rtolcap, rtoffcap, rtorpa = lam[ok], rtolcap[ok], rtoffcap[ok], rtorpa[ok]
        rtordpa = np.nan_to_num(rtordpa[ok], nan=0.0)
        hour_of_year = hour_of_year[ok]
        r_full = rtolcap + rtoffcap
        year_out: dict = {
            "n_hours": int(ok.sum()),
            "rtolcap": _quantiles(rtolcap),
            "rtolcap_plus_rtoffcap": _quantiles(r_full),
            "system_lambda": _quantiles(lam),
            "rtorpa": _quantiles(rtorpa),
            "rtordpa_mean": float(rtordpa.mean()),
            "rtordpa_max": float(rtordpa.max()),
        }
        # (b) reproduction: implemented curve on measured reserves vs measured RTORPA.
        for label, table in (("fallback", False), ("np6_576_er", True)):
            mu, sigma = _params(config, 8760, table)
            if isinstance(mu, np.ndarray):
                mu, sigma = mu[hour_of_year], sigma[hour_of_year]
            model = ordc_adder(
                r_full,
                lam,
                voll=config.ordc_voll,
                mcl_mw=config.ordc_mcl_mw,
                mu_mw=mu,
                sigma_mw=sigma,
                shift_sigma=config.ordc_lolp_shift_sigma,
                multistep_floor=config.ordc_multistep_floor,
                floor_active=True,
                reserves_online_mw=rtolcap,
            )
            year_out[f"curve_{label}"] = {
                "mean": float(model.mean()),
                "max": float(model.max()),
                "h_gt_1": int((model > 1).sum()),
                "h_gt_10": int((model > 10).sum()),
                "h_gt_100": int((model > 100).sum()),
                "measured_rtorpa_mean": float(rtorpa.mean()),
                "measured_rtorpa_max": float(rtorpa.max()),
                "measured_h_gt_1": int((rtorpa > 1).sum()),
                "measured_h_gt_10": int((rtorpa > 10).sum()),
                "measured_h_gt_100": int((rtorpa > 100).sum()),
                # Mean model-vs-measured adder on the 50 tightest measured-reserve
                # hours: where the curve is supposed to live.
                "tightest50_model_mean": float(np.sort(model)[-50:].mean()),
                "tightest50_measured_mean": float(np.sort(rtorpa)[-50:].mean()),
            }
        # The measured h>$100 decomposition: what any adder-side repair can reach.
        rtspp = lam + rtorpa + rtordpa  # system-price analogue (basis-free)
        year_out["scarcity_hour_decomposition"] = {
            "h_rtspp_gt_100": int((rtspp > 100).sum()),
            "h_lambda_gt_100": int((lam > 100).sum()),
            "h_adders_gt_100": int(((rtorpa + rtordpa) > 100).sum()),
            "h_lambda_gt_100_and_adders_le_10": int(((lam > 100) & ((rtorpa + rtordpa) <= 10)).sum()),
            "h_rtspp_gt_1000": int((rtspp > 1000).sum()),
            "h_lambda_gt_1000": int((lam > 1000).sum()),
            "rtolcap_p50_in_rtspp_gt_100_hours": (
                float(np.median(rtolcap[rtspp > 100])) if (rtspp > 100).any() else None
            ),
            "rtolcap_plus_off_p50_in_rtspp_gt_100_hours": (
                float(np.median(r_full[rtspp > 100])) if (rtspp > 100).any() else None
            ),
        }
        out[str(year)] = year_out
    return out


def _system_series_from_clean_generation(year: int) -> dict[str, np.ndarray] | None:
    """Hourly system wind/solar/total-gen MW from the clean generation store.

    Measured EIA-930-derived generation on the model's local non-leap 8760
    clock (Feb-29 dropped). Total generation stands in for served load in the
    driver construction — a scope-check-grade proxy (interchange < 1 % of
    ERCOT load). Returns ``None`` when the year's clean parquet is absent.
    """
    import pandas as pd

    path = REPO / "data" / "clean" / "generation" / "ERCOT" / f"generation_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["interval_start_local", "fuel", "generation_mw"])
    ts = pd.to_datetime(df["interval_start_local"])
    df = df[(ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))]
    ts = pd.to_datetime(df["interval_start_local"])
    hour = (ts.dt.dayofyear - 1) * 24 + ts.dt.hour
    # Leap years: local dayofyear past Feb-29 is one ahead on the non-leap clock.
    if int(year) % 4 == 0:
        after = (ts.dt.month > 2).to_numpy()
        hour = hour.to_numpy() - np.where(after, 24, 0)
    else:
        hour = hour.to_numpy()
    df = df.assign(hour=hour)
    piv = df.pivot_table(index="hour", columns="fuel", values="generation_mw", aggfunc="sum")
    piv = piv.reindex(range(8760)).interpolate(limit_direction="both")
    fuels = {str(c).lower(): c for c in piv.columns}
    wind = piv[fuels["wind"]].to_numpy(dtype=float) if "wind" in fuels else np.zeros(8760)
    solar = piv[fuels["solar"]].to_numpy(dtype=float) if "solar" in fuels else np.zeros(8760)
    total = piv.sum(axis=1).to_numpy(dtype=float)
    return {"wind": wind, "solar": solar, "load": total}


def leg_d(config: ScenarioConfig) -> dict:
    """Leg (d): forward AS-requirement model vs the measured ASPLANNP433 plan.

    Scope check for repair element E2 (no intake): both sides are already in
    the repo. Drivers from the clean generation store's measured system
    load/wind/solar; returns per-year {"skipped": reason} when unavailable.
    """
    from market_sim.results.scarcity import (
        ercot_as_forward_drivers,
        ercot_as_forward_requirement_mw,
        ercot_as_plan_requirement_mw,
    )

    out: dict = {}
    cfg = config.with_overrides(ercot_as_forward_requirement=True)
    for year in YEARS:
        series = _system_series_from_clean_generation(year)
        if series is None:
            out[str(year)] = {"skipped": "clean generation store not built for year"}
            continue
        hours = 8760
        drivers = ercot_as_forward_drivers(series["load"], series["wind"], series["solar"])
        year_out = {}
        for product in ("REGUP", "RRS", "ECRS", "NSPIN"):
            fwd = ercot_as_forward_requirement_mw(cfg, product, hours, drivers)
            meas = ercot_as_plan_requirement_mw(year, hours, product)
            year_out[product] = {
                "forward_mean": None if fwd is None else float(np.mean(fwd)),
                "forward_p95": None if fwd is None else float(np.percentile(fwd, 95)),
                "measured_mean": float(np.mean(meas)) if np.any(meas) else None,
                "measured_p95": float(np.percentile(meas, 95)) if np.any(meas) else None,
            }
        out[str(year)] = year_out
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-d", action="store_true", help="skip the clean-data-dependent AS leg")
    args = ap.parse_args()

    config = ScenarioConfig(iso="ERCOT", mode="forecast")
    result = {
        "probe": "ffr8a_scarcity_decomposition part A",
        "ordc_params_as_shipped": {
            "voll": config.ordc_voll,
            "mcl_mw": config.ordc_mcl_mw,
            "mu_mw_fallback": config.ordc_lolp_mu_mw,
            "sigma_mw_fallback": config.ordc_lolp_sigma_mw,
            "shift_sigma": config.ordc_lolp_shift_sigma,
            "multistep_floor": config.ordc_multistep_floor,
            "as_plan_netting_mw": config.ordc_as_plan_mw,
            "lolp_params_path_in_arm": None,
        },
        "legs_ab": leg_ab(config),
    }
    if not args.skip_d:
        result["leg_d"] = leg_d(config)
    out_path = REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
