"""neiso-99 probe: decompose the movement into its basis and routing arms.

Reads COMMITTED bundle sidecars only — no LP, no solve. Reports, per year:

* **P1 bit-identity** of arm A against the incumbent keeper's own persisted P1
  (prediction P1 of ``PREREG-neiso99-p2basis-routing-2026-08-17.md``: dropping
  the archived P2 pass cannot move P1, because P2 runs after it);
* the **basis** arm — the incumbent's scored P2 numbers against its own P1;
* the **routing** arm — arm B against arm A, both on the P1 basis;
* the **joint** movement, arm B against the incumbent as scored.

Every price statistic is computed under the pinned
``render_calibration_html._tail_hours`` convention (max across zones, NaN →
−inf) so the arms and the dashboard are one measurement rather than two.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

YEARS = (2023, 2024, 2025)
KEEPER = ROOT / "results" / "calibration" / "neiso97_dstrepair_A"
ARM_A = ROOT / "results" / "calibration" / "neiso99_basis_A"
ARM_B = ROOT / "results" / "calibration" / "neiso99_joint_B"
TAIL_THRESHOLD = 300.0  # NEISO C3c threshold, $/MWh


def system_frame(bundle: Path, year: int, pass_label: str | None) -> pd.DataFrame:
    """Return one pass's ``hourly/system_<year>.parquet`` rows for a bundle."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    if pass_label is not None and "pass" in df.columns:
        df = df[df["pass"] == pass_label]
    return df


def passes(bundle: Path, year: int) -> list[str]:
    """Return the pass labels a bundle's system sidecar persists."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return sorted(df["pass"].unique().tolist()) if "pass" in df.columns else []


def price_stats(df: pd.DataFrame) -> dict:
    """Return mean / max / tail-hour statistics under the pinned tail convention."""
    wide = df.pivot_table(index="hour", columns="zone", values="price", aggfunc="first")
    across = wide.to_numpy(dtype=float)
    mx = np.nanmax(np.where(np.isnan(across), -np.inf, across), axis=1)
    return {
        "mean_lambda": round(float(np.nanmean(across)), 4),
        "max_across_zones": round(float(mx.max()), 4),
        "hours_gt_threshold": int((mx > TAIL_THRESHOLD).sum()),
    }


def class_energy(bundle: Path, year: int, pass_label: str | None) -> dict[str, float]:
    """Return per-class annual energy (TWh) from ``class_hourly_<year>.parquet``."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    if pass_label is not None and "pass" in df.columns:
        df = df[df["pass"] == pass_label]
    g = df.groupby("klass")["mw"].sum() / 1e6
    return {str(k): round(float(v), 4) for k, v in g.items()}


def bit_identical(a: Path, b: Path, year: int, pa: str, pb: str) -> dict:
    """Compare two bundles' hourly sidecars cell-by-cell for one year/pass pair."""
    out: dict[str, object] = {}
    for name in ("system", "class_hourly", "reserve_family"):
        fa, fb = (
            a / "hourly" / f"{name}_{year}.parquet",
            b / "hourly" / f"{name}_{year}.parquet",
        )
        if not fa.exists() or not fb.exists():
            out[name] = "absent"
            continue
        da, db = pd.read_parquet(fa), pd.read_parquet(fb)
        if "pass" in da.columns:
            da = da[da["pass"] == pa].drop(columns=["pass"])
        if "pass" in db.columns:
            db = db[db["pass"] == pb].drop(columns=["pass"])
        da = da.reset_index(drop=True)
        db = db.reset_index(drop=True)
        if da.shape != db.shape or list(da.columns) != list(db.columns):
            out[name] = f"shape/cols differ {da.shape} vs {db.shape}"
            continue
        num = da.select_dtypes("number").columns
        diff = da[num].to_numpy(float) - db[num].to_numpy(float)
        nd = int((diff != 0).sum())
        out[name] = {
            "differing_cells": nd,
            "max_abs_delta": round(float(np.abs(diff).max()), 10) if diff.size else 0.0,
            "rows": int(len(da)),
        }
    return out


def main() -> None:
    """Measure the basis arm, the routing arm and the joint movement."""
    result: dict[str, dict] = {"years": {}, "passes": {}}
    for b, nm in ((KEEPER, "keeper"), (ARM_A, "armA"), (ARM_B, "armB")):
        result["passes"][nm] = {str(y): passes(b, y) for y in YEARS}
    print("persisted passes:", json.dumps(result["passes"]))

    for y in YEARS:
        kp = result["passes"]["keeper"][str(y)]
        scored = "P2" if "P2" in kp else "P1"
        a_pass = result["passes"]["armA"][str(y)][0]
        b_pass = result["passes"]["armB"][str(y)][0]

        row: dict[str, object] = {
            "keeper_scored_pass": scored,
            "armA_pass": a_pass,
            "armB_pass": b_pass,
            "P1_bit_identity_armA_vs_keeperP1": bit_identical(
                ARM_A, KEEPER, y, a_pass, "P1"
            ),
            "prices": {
                "keeper_scored": price_stats(system_frame(KEEPER, y, scored)),
                "keeper_P1": price_stats(system_frame(KEEPER, y, "P1")),
                "armA": price_stats(system_frame(ARM_A, y, a_pass)),
                "armB": price_stats(system_frame(ARM_B, y, b_pass)),
            },
            "class_twh": {
                "keeper_scored": class_energy(KEEPER, y, scored),
                "armA": class_energy(ARM_A, y, a_pass),
                "armB": class_energy(ARM_B, y, b_pass),
            },
        }
        p = row["prices"]
        row["deltas"] = {
            "basis_armA_minus_keeperScored": {
                k: round(p["armA"][k] - p["keeper_scored"][k], 4) for k in p["armA"]
            },
            "routing_armB_minus_armA": {
                k: round(p["armB"][k] - p["armA"][k], 4) for k in p["armA"]
            },
            "joint_armB_minus_keeperScored": {
                k: round(p["armB"][k] - p["keeper_scored"][k], 4) for k in p["armA"]
            },
        }
        result["years"][str(y)] = row

        print(f"\n=== {y}  (keeper scored on {scored})")
        print(
            f"  P1 bit-identity armA vs keeper P1: "
            f"{json.dumps(row['P1_bit_identity_armA_vs_keeperP1'])}"
        )
        for nm in ("keeper_scored", "keeper_P1", "armA", "armB"):
            s = p[nm]
            print(
                f"  {nm:14s} mean {s['mean_lambda']:9.4f} | max "
                f"{s['max_across_zones']:9.4f} | h>${TAIL_THRESHOLD:.0f} "
                f"{s['hours_gt_threshold']}"
            )
        for nm, dd in row["deltas"].items():
            print(f"  d {nm:34s} {dd}")
        ce = row["class_twh"]
        moved = {
            k: (round(ce["armB"].get(k, 0.0) - ce["armA"].get(k, 0.0), 4))
            for k in set(ce["armA"]) | set(ce["armB"])
        }
        moved = {k: v for k, v in sorted(moved.items(), key=lambda x: -abs(x[1])) if v}
        print(f"  routing class-TWh delta (armB-armA): {moved}")

    out = ROOT / "results" / "calibration" / "_neiso99_arm_decomposition.json"
    out.write_text(json.dumps(result, indent=1, sort_keys=True, default=str))
    print("\nwrote", out)


if __name__ == "__main__":
    main()
