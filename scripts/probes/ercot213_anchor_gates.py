"""ercot-213 published-anchor scorer (read-only, no LP): G-CAP + the adder census.

Two things the inherited ercot-172/173 gate scorer cannot see, both
pre-registered in ``docs/PRECOMMIT-ercot213-published-anchor-2026-08-16.md``:

* **G-CAP** (the added gate, §3) — no written ``ordc_adder(t)`` may exceed
  ``VOLL - lambda(t)``, the published protocol cap ``lambda + adders <= VOLL``.
  The ercot-212 arm wrote a maximum of ``2 x VOLL``; this is the check that
  the repair repaired. ``lambda`` is recovered from the committed sidecar
  exactly as ``_system_frame`` formed it: the persisted ``price`` is
  ``LP dual + rtordpa_overlay + dam_as_overlay + ordc_adder``, so subtracting
  the persisted overlay columns returns the raw per-zone LP energy dual, and
  the demand-weighted mean over zones is the system lambda the anchor used.
* **The adder census** (§2's landing zone) — hours with ``ordc_adder`` nonzero
  / ``> $1`` / ``> $100``, and the maximum written adder, per year and per
  member. The dispatch's expected landing zone is 2023 ~20-37 h > $100 (17
  published settled) and 2024 ~45-48 h > $1 (78 published settled).

Also reports the OBDRR048-floor exposure the precommit names as a limitation:
the share of adder-writing hours whose model reserve level is low enough for
the floor steps to be in play at all.

Read-only: consumes the two bundles' ``hourly/`` sidecars; solves nothing.

Usage::

    python scripts/probes/ercot213_anchor_gates.py \
        --base results/calibration/ercot213_control_A \
        --arm  results/calibration/ercot213_anchor_B \
        [--voll 5000] [--out results/calibration/ercot213_anchor_gates.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
YEARS = (2023, 2024, 2025)
# Published settled RTORPA incidence, ercot-212 Phase-0 §1 (live hours).
PUBLISHED = {2023: {"gt1": 294, "gt100": 17}, 2024: {"gt1": 78, "gt100": 4},
             2025: {"gt1": 14, "gt100": 0}}
# OBDRR048 floor steps (reserves MW -> $/MWh), spec.ORDC_FLOOR_STEPS.
FLOOR_TOP_MW = 7000.0


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[(df["year"] == year) & (df["pass"] == "P1")]


def _series(df: pd.DataFrame, col: str) -> np.ndarray:
    """Per-hour series of a system-wide (zone-broadcast) column."""
    if col not in df.columns:
        return np.zeros(8760, dtype=float)
    return (
        df.groupby("hour")[col].first().reindex(range(8760)).to_numpy(float)
    )


def _lambda(df: pd.DataFrame) -> np.ndarray:
    """Demand-weighted raw LP energy dual — the anchor's lambda, recovered."""
    overlay = np.zeros(len(df), dtype=float)
    for col in ("rtordpa_overlay", "dam_as_overlay", "ordc_adder"):
        if col in df.columns:
            overlay = overlay + df[col].to_numpy(float)
    lam_z = df["price"].to_numpy(float) - overlay
    dem = df["demand"].to_numpy(float)
    hour = df["hour"].to_numpy()
    num = pd.Series(lam_z * dem).groupby(hour).sum()
    den = pd.Series(dem).groupby(hour).sum()
    return (num / den).reindex(range(8760)).to_numpy(float)


def _held_total(bundle: Path, year: int) -> np.ndarray | None:
    """Total-family held reserve MW, if the reserve_family sidecar is present."""
    path = bundle / "hourly" / f"reserve_family_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[(df["pass"] == "P1") & (df["family"] == "ercot_ordc_total")]
    if df.empty or "held_mw" not in df.columns:
        return None
    return (
        df.groupby("hour")["held_mw"].sum().reindex(range(8760)).to_numpy(float)
    )


def score_member(bundle: Path, year: int, voll: float) -> dict:
    df = _system(bundle, year)
    adder = _series(df, "ordc_adder")
    lam = _lambda(df)
    head = np.maximum(voll - lam, 0.0)
    violation = adder - head
    worst = int(np.argmax(violation))
    held = _held_total(bundle, year)
    out = {
        "adder_nonzero_h": int((adder > 0.0).sum()),
        "adder_gt1_h": int((adder > 1.0).sum()),
        "adder_gt100_h": int((adder > 100.0).sum()),
        "adder_max": round(float(adder.max()), 4),
        "adder_sum_dw": round(float(adder.mean()), 4),
        "lambda_at_adder_max": round(float(lam[int(np.argmax(adder))]), 3),
        "gcap_max_violation": round(float(violation.max()), 6),
        "gcap_violation_hours": int((violation > 1e-6).sum()),
        "gcap_worst_hour": worst,
        "published_gt1": PUBLISHED[year]["gt1"],
        "published_gt100": PUBLISHED[year]["gt100"],
    }
    if held is not None:
        writing = adder > 0.0
        out["floor_region_h_of_writing"] = int(
            (writing & (held <= FLOOR_TOP_MW)).sum()
        )
        out["held_total_p50_when_writing"] = (
            round(float(np.median(held[writing])), 1) if writing.any() else None
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--voll", type=float, default=5000.0)
    ap.add_argument(
        "--out",
        type=Path,
        default=REPO / "results" / "calibration" / "ercot213_anchor_gates.json",
    )
    args = ap.parse_args()

    res: dict = {
        "_provenance": {
            "scorer": "scripts/probes/ercot213_anchor_gates.py",
            "base": str(args.base),
            "arm": str(args.arm),
            "voll": args.voll,
            "gates": "PRECOMMIT-ercot213-published-anchor-2026-08-16.md §3 G-CAP",
        },
        "years": {},
    }
    gcap_pass = True
    for year in YEARS:
        base = score_member(args.base, year, args.voll)
        arm = score_member(args.arm, year, args.voll)
        gcap_pass = gcap_pass and arm["gcap_violation_hours"] == 0
        res["years"][str(year)] = {"base": base, "arm": arm}
    res["gates"] = {
        "G-CAP": {
            "pass": bool(gcap_pass),
            "rule": "no written ordc_adder(t) may exceed VOLL - lambda(t)",
        }
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res["years"], indent=1))
    print(f"G-CAP pass={gcap_pass} -> {args.out}")


if __name__ == "__main__":
    main()
