"""ercot-217 Phase-0 (read-only): the 2023 regime lane's three measurements.

Dispatched by the owner (ERCOT-217, 2026-08-17) to adjudicate whether a
2023-vs-2024/25 market-DESIGN regime split of the ERCOT keeper is buildable.
Three read-only measurements, no LP, no solve, no year scored:

(P0-B) The -33.2 -> -40.1 C3a-2023 move decomposed across the five committed
       lineage bundles (ercot-204 -> ercot-213 ctl/arm -> ercot-215 ctl/arm)
       into settlement-price components: energy dual (lambda), measured
       RTORDPA overlay, and written ORDC adder — demand-weighted annual
       means on the standing ``_ercot173_ab`` convention (hub actual).

(P0-C) The residual step test at the published design dates: ECRS go-live
       (2023-06-10 = fleet hour 3840, market notice M-D050523-01), the ECRS
       release reform (2024-08-01 = hour 5088), RTC+B go-live (2025-12-05 =
       hour 8112) — pre/post windows, 14-day straddles, monthly bias and
       tail-catch tables, with the same calendar splits applied to 2024 and
       2025 as placebo. All splits on the model's fixed non-leap 8760 clock
       (ercot-216 s.6 clock discipline: no naive leap-year date_range).

(P0-A support) The measured regime quantities the model already carries:
       ASPLANNP433 per-product monthly means for 2023/2024/2025 and the
       first ECRS delivery date in the measured input; the armed regime
       flags read from every lineage bundle's run_config.json.

Conventions: demand-weighted P1 system price (``_ercot89_span_check``), the
committed actual RT parquet, tail = actual > $200 (rubric ERCOT threshold).
Read-only: consumes committed sidecars + committed raw inputs; solves nothing.

Usage::

    python scripts/probes/ercot217_regime_phase0.py \
        [--out results/calibration/ercot217_regime_phase0.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUAL_LMP = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
DEFAULT_OUT = REPO / "results" / "calibration" / "ercot217_regime_phase0.json"
YEARS = (2023, 2024, 2025)

# The five lineage bundles (P0-B). ercot-213-ctl replays the ercot-204 recipe
# at the ercot-213 tree; ercot-215-ctl replays the ercot-213 arm (12/12
# sha256-identical, FINDING-ercot215 s.2).
BUNDLES = {
    "ercot204": "ercot204_rule26_delete",
    "ercot213_ctl": "ercot213_control_A",
    "ercot213_arm": "ercot213_anchor_B",
    "ercot215_ctl": "ercot215_control_A",
    "ercot215_arm": "ercot215_decontam_B",
}

# Published design dates on the model's fixed non-leap 8760 clock (rule 8).
# Sources: spec.py ERCOT_ECRS_* citation blocks; ERCOT market notice
# M-D050523-01 (go-live OD 2023-06-10); the 2024-08-01 operating-procedure
# release reform (NPRR1224 process implemented without the $750 floor after
# the PUCT rejected the floor 2024-07-25 — IMM 2024 SOM, rec 2023-3); RTC+B
# go-live 2025-12-05 (IMM 2025 SOM: "before RTC went live on December 5,
# 2025"). Non-leap clock: Jan-May=151 d -> Jun 10 00:00 = 160*24; Jan-Jul=
# 212 d -> Aug 1 00:00 = 212*24; Jan-Nov+4 d = 338 d -> Dec 5 00:00 = 338*24.
ECRS_GOLIVE_HOUR = 160 * 24  # 3840
ECRS_REFORM_HOUR = 212 * 24  # 5088
RTCB_GOLIVE_HOUR = 338 * 24  # 8112
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_EDGES = np.cumsum((0,) + MONTH_DAYS) * 24

TAIL = 200.0  # rubric s.5 ERCOT actual-RT tail threshold ($/MWh)


def lw_component(bundle: Path, year: int, col: str) -> np.ndarray:
    """Hourly demand-weighted P1 system series for ``col``."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    num = (df[col] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).reindex(range(8760)).to_numpy(float)


def actual_rt(year: int) -> np.ndarray:
    a = pd.read_parquet(ACTUAL_LMP)
    a = a[a["year"] == year]
    return a.set_index("hour")["rt"].reindex(range(8760)).to_numpy(float)


def window_stats(m: np.ndarray, a: np.ndarray, sel: np.ndarray) -> dict:
    ok = np.isfinite(m) & np.isfinite(a) & sel
    if not ok.any():
        return {"n": 0}
    mm, am = float(m[ok].mean()), float(a[ok].mean())
    return {
        "n": int(ok.sum()),
        "model_mean": round(mm, 2),
        "actual_mean": round(am, 2),
        "bias_pct": round((mm - am) / am * 100.0, 1),
        "actual_tail_h": int((a[ok] > TAIL).sum()),
        "model_tail_h": int((m[ok] > TAIL).sum()),
        "caught_h": int(((a[ok] > TAIL) & (m[ok] > TAIL)).sum()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    payload: dict = {"probe": "ercot217_regime_phase0", "years": YEARS}

    # ---- P0-B: component decomposition across the lineage -----------------
    p0b: dict = {}
    for key, name in BUNDLES.items():
        bundle = REPO / "results" / "calibration" / name
        rows = {}
        for yr in YEARS:
            a = actual_rt(yr)
            price = lw_component(bundle, yr, "price")
            ovl = lw_component(bundle, yr, "rtordpa_overlay")
            add = lw_component(bundle, yr, "ordc_adder")
            lam = price - ovl - add
            ok = np.isfinite(price) & np.isfinite(a)
            rows[yr] = {
                "price_mean": round(float(np.nanmean(price)), 2),
                "lambda_mean": round(float(np.nanmean(lam)), 2),
                "overlay_mean": round(float(np.nanmean(ovl)), 2),
                "adder_mean": round(float(np.nanmean(add)), 2),
                "actual_mean": round(float(np.nanmean(a)), 2),
                "c3a_probe_pct": round(
                    (float(np.nanmean(price)) - float(np.nanmean(a)))
                    / float(np.nanmean(a)) * 100.0, 1),
                "model_tail_h": int((price[ok] > TAIL).sum()),
                "adder_h_gt100": int((add > 100.0).sum()),
            }
        p0b[key] = {"bundle": name, "by_year": rows}
    payload["p0b_component_decomposition"] = p0b

    # ---- P0-C: design-date step test on the keeper ------------------------
    keeper = REPO / "results" / "calibration" / BUNDLES["ercot215_arm"]
    p0c: dict = {}
    hours = np.arange(8760)
    for yr in YEARS:
        a = actual_rt(yr)
        m = lw_component(keeper, yr, "price")
        entry: dict = {
            "pre_ecrs_golive": window_stats(m, a, hours < ECRS_GOLIVE_HOUR),
            "post_ecrs_golive": window_stats(m, a, hours >= ECRS_GOLIVE_HOUR),
            "straddle_14d_before": window_stats(
                m, a, (hours >= ECRS_GOLIVE_HOUR - 14 * 24) & (hours < ECRS_GOLIVE_HOUR)),
            "straddle_14d_after": window_stats(
                m, a, (hours >= ECRS_GOLIVE_HOUR) & (hours < ECRS_GOLIVE_HOUR + 14 * 24)),
            "straddle_14d_next": window_stats(
                m, a, (hours >= ECRS_GOLIVE_HOUR + 14 * 24)
                & (hours < ECRS_GOLIVE_HOUR + 28 * 24)),
            "pre_ecrs_reform": window_stats(m, a, hours < ECRS_REFORM_HOUR),
            "post_ecrs_reform": window_stats(m, a, hours >= ECRS_REFORM_HOUR),
            "pre_rtcb": window_stats(m, a, hours < RTCB_GOLIVE_HOUR),
            "post_rtcb": window_stats(m, a, hours >= RTCB_GOLIVE_HOUR),
            "monthly": {},
        }
        for mo in range(12):
            sel = (hours >= MONTH_EDGES[mo]) & (hours < MONTH_EDGES[mo + 1])
            entry["monthly"][mo + 1] = window_stats(m, a, sel)
        p0c[yr] = entry
    payload["p0c_design_date_step_test"] = p0c

    # ---- P0-A support: measured regime quantities + armed flags -----------
    asplan: dict = {}
    for yr in YEARS:
        f = REPO / "data" / "raw" / "ercot" / f"ASPLANNP433_{yr}.parquet"
        df = pd.read_parquet(f)
        df["d"] = pd.to_datetime(df["DeliveryDate"], format="%m/%d/%Y")
        df = df[df["d"].dt.year == yr]
        piv = df.pivot_table(index=df["d"].dt.month, columns="AncillaryType",
                             values="Quantity", aggfunc="mean")
        asplan[yr] = {
            str(prod): {int(mo): round(float(v), 0)
                        for mo, v in piv[prod].dropna().items()}
            for prod in piv.columns
        }
        if yr == 2023:
            ecrs = df[df["AncillaryType"] == "ECRS"]
            asplan["first_ecrs_delivery_date"] = str(ecrs["d"].min().date())
    payload["p0a_asplan_monthly_mw"] = asplan

    flags: dict = {}
    for key, name in BUNDLES.items():
        rc = json.loads(
            (REPO / "results" / "calibration" / name / "run_config.json").read_text())
        sc = rc.get("scenario_config", {})
        flags[key] = {
            k: sc.get(k)
            for k in (
                "ercot_ecrs_conservative_deployment",
                "ercot_nonreleasable_as_withholding",
                "ercot_multiproduct_as_coopt",
                "ercot_ordc_total_reserve",
                "ercot_reserve_supply_cap_net_credits",
                "ordc_voll", "ordc_mcl_mw", "ercot_market_design",
            )
        }
    payload["p0a_armed_regime_flags"] = flags

    args.out.write_text(json.dumps(payload, indent=1, default=str) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
