"""ERCOT-162 storage RT offer-surface A/B scorer (read-only, pre-registered).

The storage-specific gates the standard ``_ercot89_span_check.py`` analyzer
does not cover, pre-declared in
``docs/PRECOMMIT-ercot162-storage-rt-offer-surface-2026-08-04.md`` §4. Given the
control (Run A) and arm (Run B) bundles it reports, all on the SAME load-weighted
P1 price convention as the standard analyzer (Σ_zone price×demand / Σ_zone demand
per hour, pass P1) and the committed actual RT parquet:

* **The 100-hour gap set** (``_ercot161_wall_phase0.json``, the FINDING top-100:
  keeper model mean $441.27, target λ $1,470.16): control vs arm load-weighted
  mean/median, and the lift toward λ — the owner-priority residual.
* **Matched-hour C3c** on the 2023 Phase-0 144 actual >$300 hours: the
  missed/hit split re-derived on the CONTROL's own prices, and the arm's model
  mean at each.
* **New-tail-outside-actual KILL**: 2023 model >$300 hours NEW under the arm
  (arm >$300 & control ≤$300) that lie OUTSIDE the actual >$300 set — must be 0.
* **2025 EIA-930 NG:BAT volume guard** (ERCOT-154 ground-(c) recurrence test):
  control vs arm 2025 battery discharge GWh vs the measured 5,444.8 GWh; the arm
  must not fall below the control by more than 5% of the measured volume.

Read-only: consumes the two bundles' ``hourly/{system,storage}_<year>.parquet``
sidecars, the committed actual RT parquet, and the committed gap-hour set;
solves nothing, registers nothing.

Usage::

    python scripts/probes/_ercot162_storage_ab.py \
        --base results/calibration/ercot162_control_A \
        --probe results/calibration/ercot162_stormarm_B \
        [--out results/calibration/_ercot162_storage_ab.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUAL_LMP = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
GAP_SET = REPO / "results" / "calibration" / "_ercot161_wall_phase0.json"
DEFAULT_OUT = REPO / "results" / "calibration" / "_ercot162_storage_ab.json"

#: EIA-930 measured ERCOT NG:BAT annual battery discharge, 2025 (ERCOT-154 §3,
#: the only full-series year). The control model was 4,483.3 GWh (−17.7%).
EIA930_NGBAT_2025_GWH = 5444.8
#: The 2025 volume guard kills only if the arm falls below the control by more
#: than this fraction of the measured volume (PRECOMMIT §4).
VOLUME_GUARD_FRAC = 0.05

YEARS = (2023, 2024, 2025)


def _lw_price(bundle: Path, year: int) -> pd.Series:
    """Hourly demand-weighted system P1 price for ``year`` (the analyzer convention)."""
    path = bundle / "hourly" / f"system_{year}.parquet"
    if not path.exists():
        path = bundle / f"system_{year}.parquet"
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).sort_index()


def _discharge_gwh(bundle: Path, year: int) -> float:
    """Total P1 battery (li_ion) discharge in GWh for ``year``."""
    path = bundle / "hourly" / f"storage_{year}.parquet"
    if not path.exists():
        return float("nan")
    df = pd.read_parquet(path)
    df = df[(df["pass"] == "P1") & (df["tech"] != "pumped_storage")]
    return float(df["discharge_mw"].sum() / 1e3)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True, help="control (Run A) bundle")
    ap.add_argument("--probe", type=Path, required=True, help="arm (Run B) bundle")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    actual = pd.read_parquet(ACTUAL_LMP)
    gap = json.loads(GAP_SET.read_text())["hour_set"]
    gap_hours = np.asarray(sorted(int(h) for h in gap["hours"]), dtype=int)
    target_lambda = float(gap["lambda_mean"])

    out: dict = {
        "_provenance": {
            "scorer": "scripts/probes/_ercot162_storage_ab.py",
            "base": str(args.base),
            "probe": str(args.probe),
            "gap_set": "results/calibration/_ercot161_wall_phase0.json (top-100)",
            "target_lambda_mean": target_lambda,
            "keeper_model_mean_ref": gap["model_mean"],
        },
        "gap_hour_set": {},
        "matched_hour_c3c_2023": {},
        "new_tail_outside_actual_2023": {},
        "volume_guard_2025": {},
    }

    # --- The 100-hour gap set (2023): load-weighted control vs arm vs λ.
    base_lw = _lw_price(args.base, 2023)
    probe_lw = _lw_price(args.probe, 2023)
    b_gap = base_lw.reindex(gap_hours)
    p_gap = probe_lw.reindex(gap_hours)
    out["gap_hour_set"] = {
        "n_hours": int(gap_hours.size),
        "control_mean": round(float(b_gap.mean()), 2),
        "arm_mean": round(float(p_gap.mean()), 2),
        "control_median": round(float(b_gap.median()), 2),
        "arm_median": round(float(p_gap.median()), 2),
        "target_lambda_mean": round(target_lambda, 2),
        "lift_toward_lambda": round(float(p_gap.mean() - b_gap.mean()), 2),
        "closes_gap_pct": round(
            100.0
            * float(p_gap.mean() - b_gap.mean())
            / max(target_lambda - float(b_gap.mean()), 1e-9),
            1,
        ),
    }

    # --- Matched-hour C3c on the 2023 Phase-0 144 actual >$300 hours, missed/hit
    #     split re-derived on the CONTROL's own prices.
    a2023 = actual[actual["year"] == 2023].set_index("hour")["rt"]
    tail_hours = np.asarray(sorted(a2023[a2023 > 300.0].index), dtype=int)
    b_tail = base_lw.reindex(tail_hours)
    missed = tail_hours[b_tail.to_numpy() < 300.0]  # control missed (< $300)
    hit = tail_hours[b_tail.to_numpy() >= 300.0]
    out["matched_hour_c3c_2023"] = {
        "n_actual_gt300": int(tail_hours.size),
        "control_missed": int(missed.size),
        "control_hit": int(hit.size),
        "control_missed_mean": round(float(base_lw.reindex(missed).mean()), 2),
        "arm_missed_mean": round(float(probe_lw.reindex(missed).mean()), 2),
        "control_hit_mean": round(float(base_lw.reindex(hit).mean()), 2),
        "arm_hit_mean": round(float(probe_lw.reindex(hit).mean()), 2),
        "missed_flipped_by_arm": int(
            (probe_lw.reindex(missed).to_numpy() >= 300.0).sum()
        ),
    }

    # --- New-tail-outside-actual KILL (2023): arm >$300 & control ≤$300 hours
    #     that lie OUTSIDE the actual >$300 set.
    actual_tail = set(int(h) for h in tail_hours)
    b_all = base_lw
    p_all = probe_lw
    new_tail = [
        int(h)
        for h in b_all.index
        if p_all.get(h, 0.0) > 300.0 and b_all.get(h, 0.0) <= 300.0
    ]
    new_outside = [h for h in new_tail if h not in actual_tail]
    out["new_tail_outside_actual_2023"] = {
        "n_new_tail_hours": len(new_tail),
        "n_new_outside_actual": len(new_outside),
        "kill": len(new_outside) > 0,
        "sample_outside_hours": sorted(new_outside)[:20],
    }

    # --- 2025 EIA-930 NG:BAT volume guard.
    b_vol = _discharge_gwh(args.base, 2025)
    p_vol = _discharge_gwh(args.probe, 2025)
    drop = b_vol - p_vol
    out["volume_guard_2025"] = {
        "control_discharge_gwh": round(b_vol, 1),
        "arm_discharge_gwh": round(p_vol, 1),
        "measured_ng_bat_gwh": EIA930_NGBAT_2025_GWH,
        "control_vs_measured_pct": round(
            100.0 * (b_vol - EIA930_NGBAT_2025_GWH) / EIA930_NGBAT_2025_GWH, 1
        ),
        "arm_vs_measured_pct": round(
            100.0 * (p_vol - EIA930_NGBAT_2025_GWH) / EIA930_NGBAT_2025_GWH, 1
        ),
        "arm_drop_vs_control_gwh": round(drop, 1),
        "guard_threshold_gwh": round(VOLUME_GUARD_FRAC * EIA930_NGBAT_2025_GWH, 1),
        "kill": bool(drop > VOLUME_GUARD_FRAC * EIA930_NGBAT_2025_GWH),
    }

    args.out.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
