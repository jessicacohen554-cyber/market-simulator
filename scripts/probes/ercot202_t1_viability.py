#!/usr/bin/env python3
"""ERCOT-202 — read-only viability test of DECISION-CARD-ercot196 card T option (T-1),
plus its chartered companion (T-3b), the published-adder overlay-completeness audit.

NOTHING IS SOLVED, SCORED OR REGISTERED HERE. The probe reads committed
artifacts only (the keeper bundle's ``meta.json`` / ``run_config.json``, the
committed measured Henry Hub monthly series, and the committed ERCOT ORDC /
price-adder parquets) and evaluates two questions:

**Part A — is (T-1) viable?** Card T recommends arming ``gas_hh_monthly_shape``
as an input-correctness A/B against the run192 keeper recipe, on the premise
(card §2(c) / §4(T-1)(b)) that the field is "built, unarmed" so "the measured
month-to-month commodity shape never enters" ERCOT. The probe tests that
premise against the keeper's own committed config and against the code path
(``data/fuel/trajectories.py::gas_seasonal_shape``), and then compares the
recipes the chartered CONTROL and ARM would actually resolve to, through the
same ``scripts/replay_keeper.build_kwargs`` seam the A/B would use.

**Part B — (T-3b): is the committed published-adder overlay complete?** ERCOT's
measured RT price adders arrive in one committed artifact per year
(``data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet``, from ERCOT MIS
report NP6-905-CD "Historical Real-Time Price Adders by SCED Interval" — see
``scripts/data/fetch_ercot_ordc_reserves.py``). The probe measures how much
published adder content each column carries and which of them any ``src/`` code
path actually consumes.

Rule 13 ``[R-MEASURED]``: every measured series here is read for ATTRIBUTION and
AUDIT only — none is fed back into a model input. Rule 22: no year outside the
2023-2025 training span is read, solved or scored.

Usage:
    python scripts/probes/ercot202_t1_viability.py \
        [--bundle results/calibration/ercot192_arm_B] \
        [--json-out results/calibration/ercot202_t1_viability.json]
"""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# The training span (rule 22 [R-HOLDOUT]); ERCOT holds no complete/final marker,
# so these are the only years this probe may read.
YEARS: tuple[int, ...] = (2023, 2024, 2025)

# Non-leap 8760-hour model clock (config.constants._DAYS_IN_MONTH ordering).
DAYS_IN_MONTH: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_NAMES: tuple[str, ...] = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

# The three published RT price-adder columns curated by
# scripts/data/fetch_ercot_ordc_reserves.py from NP6-905-CD.
ADDER_COLUMNS: tuple[str, ...] = ("rtorpa", "rtoffpa", "rtordpa")


def _month_edges() -> np.ndarray:
    """Return the 13 hour-boundaries of the non-leap 8760-hour month grid."""
    return np.cumsum([0] + [d * 24 for d in DAYS_IN_MONTH])


def part_a_flag_state(bundle: Path) -> dict:
    """Return what the keeper's committed artifacts say about the T-1 field.

    Reads both records that rule 24 ``[R-REGISTRY]`` makes authoritative: the
    ``meta.json`` solve-kwarg snapshot and the RESOLVED ``scenario_config``
    block of ``run_config.json`` (what the LP actually ran with).
    """
    meta = json.loads((bundle / "meta.json").read_text())
    run_config = json.loads((bundle / "run_config.json").read_text())
    scenario = run_config["scenario_config"]
    return {
        "bundle": str(bundle),
        "run_id": json.loads((bundle / "metrics.json").read_text())["run_id"],
        "meta_timestamp": meta.get("timestamp"),
        "meta_gas_hh_monthly_shape": meta.get("gas_hh_monthly_shape"),
        "resolved_gas_hh_monthly_shape": scenario.get("gas_hh_monthly_shape"),
        "resolved_gas_seasonality": scenario.get("gas_seasonality"),
        "resolved_gas_daily_shape": scenario.get("gas_daily_shape"),
        "resolved_gas_monthly_actuals": scenario.get("gas_monthly_actuals"),
        "resolved_mode": scenario.get("mode"),
    }


def part_a_shape_effect(gas_levels: dict[int, float]) -> dict:
    """Return armed-vs-unarmed monthly gas shape factors, per training year.

    Calls the production code path (``fuel.trajectories.gas_seasonal_shape``)
    twice per year — once with ``gas_hh_monthly_shape`` set and once without —
    and records the resulting month-start factors, the hour-weighted mean of the
    armed factors (the level-preservation check: it must be exactly 1.0, which is
    what makes the mechanism carry ZERO fitted scalars, rules 20/23), and the
    per-month $/MMBtu difference at the keeper's own annual gas level.

    ``gas_levels`` maps year -> the keeper's ``gas_price_override`` for that year
    (its measured annual Henry Hub pin), so the reported wedge is on the keeper's
    own basis rather than an invented level.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel.hubs import _henry_hub_monthly
    from market_sim.data.fuel.trajectories import gas_seasonal_shape

    hh = _henry_hub_monthly(None)
    edges = _month_edges()
    month_hours = np.array(DAYS_IN_MONTH, dtype=float) * 24.0
    out: dict = {
        "henry_hub_rows_loaded": len(hh),
        "henry_hub_source": "data/raw/gas-prices/henry_hub_monthly.csv",
        "years": {},
    }
    for year in YEARS:
        level = gas_levels[year]
        measured_months = [hh.get((year, m)) for m in range(1, 13)]
        common = dict(
            iso="ERCOT", mode="backcast", gas_seasonality=True,
            gas_price_override=level,
        )
        armed = gas_seasonal_shape(
            ScenarioConfig(gas_hh_monthly_shape=True, **common), year, 8760
        )
        unarmed = gas_seasonal_shape(
            ScenarioConfig(gas_hh_monthly_shape=False, **common), year, 8760
        )
        armed_m = np.array([armed[edges[i]] for i in range(12)])
        unarmed_m = np.array([unarmed[edges[i]] for i in range(12)])
        out["years"][str(year)] = {
            "keeper_annual_gas_level_usd_mmbtu": level,
            "measured_hh_months_present": sum(v is not None for v in measured_months),
            "armed_month_factors": [round(float(v), 6) for v in armed_m],
            "unarmed_month_factors": [round(float(v), 6) for v in unarmed_m],
            "armed_hour_weighted_mean_factor": float(
                (armed_m * month_hours).sum() / month_hours.sum()
            ),
            "armed_equals_unarmed": bool(np.allclose(armed, unarmed)),
            "wedge_usd_mmbtu_by_month": [
                round(float(level * (armed_m[i] - unarmed_m[i])), 4) for i in range(12)
            ],
        }
    return out


def part_a_recipe_delta(bundle: Path) -> dict:
    """Return the recipe difference between the chartered CONTROL and ARM.

    The chartered A/B is CONTROL = the run192 keeper recipe replayed verbatim,
    ARM = the same recipe plus ``--set gas_hh_monthly_shape=true``. Both are
    reconstructed through the exact seam ``scripts/replay_keeper`` uses, so the
    comparison is the one the solves would actually see — not a paraphrase.
    """
    sys.argv = [sys.argv[0]]  # replay_keeper parses argv at import-time use only
    from market_sim.config.scenarios import ScenarioConfig
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf

    meta = json.loads((bundle / "meta.json").read_text())
    control = rk.build_kwargs(meta)

    key = "gas_hh_monthly_shape"
    arm = dict(control)
    arm["prb_overrides"] = dict(control.get("prb_overrides") or {})
    cfg_fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    solve_params = set(inspect.signature(rcf.solve_and_persist).parameters)
    # Mirror replay_keeper's --set routing exactly (both channels).
    if key in solve_params:
        arm[key] = True
    if key in cfg_fields:
        arm["prb_overrides"][key] = True

    differing = sorted(
        k for k in set(control) | set(arm) if control.get(k) != arm.get(k)
    )
    return {
        "control_effective": control.get(key),
        "arm_effective": arm.get(key),
        "effective_values_equal": control.get(key) == arm.get(key),
        "kwargs_keys_differing": differing,
        "prb_overrides_delta": {
            key: [
                (control.get("prb_overrides") or {}).get(key),
                arm["prb_overrides"].get(key),
            ]
        },
    }


def part_b_adder_audit(raw_ercot: Path) -> dict:
    """Return the published-adder content per column vs what any src/ path reads.

    Applies the SAME regime gate the committed overlay applies
    (``results/scarcity.py::ercot_rtordpa_overlay_series``): pre-RTC+B only, so
    2025 hours at/after the go-live hour are zeroed. Reports annual and monthly
    means per column so an incomplete overlay is visible at the grain card T
    §2(c)/§2(d) reasons on.
    """
    import pandas as pd

    from market_sim.results.scarcity import RTCB_GOLIVE_HOUR

    edges = _month_edges()
    consumed = _columns_consumed_by_src()
    out: dict = {
        "source_report": "ERCOT MIS NP6-905-CD (Historical Real-Time Price "
                         "Adders by SCED Interval)",
        "regime_gate": f"2025 hours >= {RTCB_GOLIVE_HOUR} zeroed (RTC+B go-live)",
        "columns_read_by_src": consumed,
        "years": {},
    }
    for year in YEARS:
        path = raw_ercot / f"ercot_{year}_ordc_reserves_hourly.parquet"
        if not path.exists():
            out["years"][str(year)] = {"error": f"missing artifact {path}"}
            continue
        frame = pd.read_parquet(path).set_index("hour").reindex(range(8760))
        series = {
            c: np.nan_to_num(frame[c].to_numpy(dtype=float)) for c in ADDER_COLUMNS
        }
        if year == 2025:
            for c in series:
                series[c][RTCB_GOLIVE_HOUR:] = 0.0
        year_out: dict = {}
        for c in ADDER_COLUMNS:
            v = series[c]
            year_out[c] = {
                "annual_mean_usd_mwh": round(float(v.mean()), 4),
                "hours_nonzero": int((v > 0).sum()),
                "max_usd_mwh": round(float(v.max()), 2),
                "monthly_mean_usd_mwh": [
                    round(float(v[edges[i]:edges[i + 1]].mean()), 4) for i in range(12)
                ],
                "consumed_by_src": c in consumed,
            }
        applied = series["rtordpa"].mean()
        unapplied = series["rtoffpa"].mean()
        year_out["summary"] = {
            "applied_overlay_mean_usd_mwh": round(float(applied), 4),
            "unapplied_rtoffpa_mean_usd_mwh": round(float(unapplied), 4),
            "rtoffpa_uplift_pct_of_applied": (
                round(float(unapplied / applied * 100.0), 1) if applied > 0 else None
            ),
            "total_published_adder_mean_usd_mwh": round(
                float(sum(series[c].mean() for c in ADDER_COLUMNS)), 4
            ),
        }
        out["years"][str(year)] = year_out
    return out


def _columns_consumed_by_src() -> list[str]:
    """Return which adder columns any ``src/`` code path actually reads.

    Measured, not asserted: greps ``src/`` for each column name and keeps only
    matches that are real code reads rather than prose in a comment/docstring.
    """
    consumed: list[str] = []
    for col in ADDER_COLUMNS:
        proc = subprocess.run(
            ["grep", "-rn", "--include=*.py", col, str(REPO / "src")],
            capture_output=True, text=True,
        )
        code_hits = [
            ln for ln in proc.stdout.splitlines()
            if ln.split(":", 2)[-1].lstrip()[:1] not in ("#", "")
            and '"' + col + '"' in ln or "'" + col + "'" in ln
        ]
        if code_hits:
            consumed.append(col)
    return consumed


def main(argv: list[str] | None = None) -> int:
    """Run both parts of the probe and emit the JSON report."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/ercot192_arm_B")
    ap.add_argument("--json-out", default="results/calibration/ercot202_t1_viability.json")
    ap.add_argument("--raw-ercot", default="data/raw/ercot")
    args = ap.parse_args(argv)

    bundle = (REPO / args.bundle) if not Path(args.bundle).is_absolute() else Path(args.bundle)
    raw = (REPO / args.raw_ercot) if not Path(args.raw_ercot).is_absolute() else Path(args.raw_ercot)

    flag_state = part_a_flag_state(bundle)
    meta = json.loads((bundle / "meta.json").read_text())
    gas_levels = {int(y): float(v) for y, v in meta["gas_prices"].items()}

    report = {
        "probe": "ercot202_t1_viability",
        "card": "DECISION-CARD-ercot196-shape-2024-2025-2026-08-13.md card T",
        "keeper_flag_state": flag_state,
        "shape_effect": part_a_shape_effect(gas_levels),
        "recipe_delta": part_a_recipe_delta(bundle),
        "t3b_adder_audit": part_b_adder_audit(raw),
    }
    report["verdict"] = {
        "t1_viable": not report["recipe_delta"]["effective_values_equal"],
        "reason": (
            "CONTROL and ARM resolve to the same effective "
            "gas_hh_monthly_shape value — the mechanism T-1 proposes to arm is "
            "already armed in the keeper, so the chartered A/B has zero delta"
            if report["recipe_delta"]["effective_values_equal"]
            else "CONTROL and ARM differ; the A/B is a real single-delta test"
        ),
    }

    out_path = (REPO / args.json_out) if not Path(args.json_out).is_absolute() else Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"ercot202 viability probe -> {out_path}")
    print(f"  keeper resolved gas_hh_monthly_shape = "
          f"{flag_state['resolved_gas_hh_monthly_shape']}")
    print(f"  T-1 viable: {report['verdict']['t1_viable']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
