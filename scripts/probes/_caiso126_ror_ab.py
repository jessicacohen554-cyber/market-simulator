"""caiso-126 A/B gate scorer: RoR-split family vs same-HEAD control.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-caiso126-ror-split-2026-07-27.md`` from the two
solved bundles (arm A = keeper recipe, arm B = + ``hydro_ror_split`` +
reconciled ``hydro_min_flow_floor``) plus raw EIA-930 — no solve, no gate not
in the prereg. Reuses the committed caiso-125 instrument's loaders so both
sessions measure identically.

Usage:
    PYTHONPATH=.:src:scripts/probes .venv/bin/python \
        scripts/probes/_caiso126_ror_ab.py \
        --control results/calibration/caiso126_control_A \
        --arm results/calibration/caiso126_rorsplit_B
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(p))

from _caiso125_overnight_attribution import (  # noqa: E402
    GAS_CLASSES,
    WINDOWS,
    ca_lambda,
    class_pivot,
    hydro_hourly,
    measured_hydro,
    month_index,
    system_frame,
)
from legitimacy_diagnostics import d1_shape_metrics  # noqa: E402

YEARS = (2023, 2024, 2025)
# Pre-registered thresholds (PREREG-caiso126 §4-§5).
P1_OVERNIGHT_MW = 150.0
K1_EVENING_MW = 300.0
P3_MIN_PROFILE_R = 0.8  # the rubric's d1_min_profile_r, C7's absolute gate
K4_CLIP_LOSS_FRAC = 0.01


def window_gap(series: np.ndarray, meas: np.ndarray, win: str) -> float:
    """Return mean (model - measured) MW over an hour-of-day window."""
    hod = np.arange(len(series)) % 24
    sel = np.isin(hod, list(WINDOWS[win]))
    return float(np.nanmean(series[sel] - meas[sel]))


def d4_offwindow(bundle: Path, mech: str) -> list[float]:
    """Return the D-4 off-window shares recorded for ``mech`` in the bundle."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    rows = payload.get("diagnostics", {}).get("D4", {}).get("rows", [])
    return [float(r.get("offwindow_share", 0.0)) for r in rows if r.get("floor") == mech]


def d2_share(bundle: Path, mech: str) -> list[dict]:
    """Return the D-2 rows for ``mech`` (forced energy attribution)."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    rows = payload.get("diagnostics", {}).get("D2", {}).get("rows", [])
    return [r for r in rows if r.get("mechanism") == mech]


def d1_pair_nan_safe(model_mw: np.ndarray, meas_mw: np.ndarray) -> tuple[float, float]:
    """Return (profile_r, cv_ratio) with d1_shape_metrics semantics, NaN-safe.

    The measured EIA-930 series carries missing hours; ``d1_shape_metrics``
    uses plain means, which propagate NaN through the profile. Same statistic,
    NaN-masked: hour-of-day means via nanmean, profile r over the 24 points,
    CVs over the off-peak points h0-14 (``D1_OFFPEAK_LAST_HOUR``).
    """
    from legitimacy_diagnostics import D1_OFFPEAK_LAST_HOUR

    t = model_mw.size
    prof_m = model_mw.reshape(-1, 24).mean(axis=0)
    prof_a = np.nanmean(meas_mw[:t].reshape(-1, 24), axis=0)
    r = float(np.corrcoef(prof_m, prof_a)[0, 1])
    off = np.arange(24) <= D1_OFFPEAK_LAST_HOUR

    def _cv(x: np.ndarray) -> float:
        m = float(x.mean())
        return float(x.std() / m) if m > 1e-9 else 0.0

    cva = _cv(prof_a[off])
    return r, (_cv(prof_m[off]) / cva if cva > 0 else float("nan"))


def main() -> None:
    """Score every pre-registered gate and print the verdict table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True)
    ap.add_argument("--arm", required=True)
    args = ap.parse_args()
    a_dir, b_dir = Path(args.control), Path(args.arm)

    fails: list[str] = []
    kills: list[str] = []

    print("=== caiso-126 pre-registered gate score (PREREG-caiso126 §4-§6) ===")
    for year in YEARS:
        ha, hb = hydro_hourly(a_dir, year), hydro_hourly(b_dir, year)
        meas = measured_hydro(year, len(ha))

        gaps = {
            w: (window_gap(ha, meas, w), window_gap(hb, meas, w))
            for w in ("overnight", "belly", "evening")
        }
        # P1 overnight
        ga, gb = gaps["overnight"]
        p1 = abs(gb) <= P1_OVERNIGHT_MW and abs(gb) < abs(ga)
        if not p1:
            fails.append(f"P1 {year}: overnight gap A {ga:+.0f} -> B {gb:+.0f}")
        # P2 belly
        ba, bb = gaps["belly"]
        p2 = abs(bb) < abs(ba)
        if not p2:
            fails.append(f"P2 {year}: belly gap A {ba:+.0f} -> B {bb:+.0f}")
        # K1 evening
        ea, eb = gaps["evening"]
        if abs(eb) > K1_EVENING_MW:
            kills.append(f"K1 {year}: evening gap B {eb:+.0f} (A {ea:+.0f})")

        # P3 — the D-1 pair as C7 scores it (NaN-safe over the measured gaps)
        r_a, ratio_a = d1_pair_nan_safe(ha, meas)
        r_b, ratio_b = d1_pair_nan_safe(hb, meas)
        p3 = r_b >= P3_MIN_PROFILE_R and abs(ratio_b - 1.0) <= abs(ratio_a - 1.0)
        if not p3:
            fails.append(
                f"P3 {year}: profile_r B {r_b:.3f} (gate >= {P3_MIN_PROFILE_R}), "
                f"|cv_ratio-1| A {abs(ratio_a - 1):.3f} -> B {abs(ratio_b - 1):.3f}"
            )

        # S1 direction: gas + lambda
        piv_a, piv_b = class_pivot(a_dir, year), class_pivot(b_dir, year)
        gas_a = float(
            piv_a[[c for c in GAS_CLASSES if c in piv_a.columns]].sum().sum() / 1e6
        )
        gas_b = float(
            piv_b[[c for c in GAS_CLASSES if c in piv_b.columns]].sum().sum() / 1e6
        )
        lam_a = float(np.mean(ca_lambda(system_frame(a_dir, year))))
        lam_b = float(np.mean(ca_lambda(system_frame(b_dir, year))))

        # S3: parks-at-zero
        lo10 = (int((ha < 10.0).sum()), int((hb < 10.0).sum()))
        lo100 = (int((ha < 100.0).sum()), int((hb < 100.0).sum()))

        print(f"\n{year}:")
        print(
            f"  gaps (A -> B, MW): overnight {ga:+.0f} -> {gb:+.0f} "
            f"[P1 {'PASS' if p1 else 'FAIL'}], belly {ba:+.0f} -> {bb:+.0f} "
            f"[P2 {'PASS' if p2 else 'FAIL'}], evening {ea:+.0f} -> {eb:+.0f} "
            f"[K1 {'ok' if abs(eb) <= K1_EVENING_MW else 'KILL'}]"
        )
        print(
            f"  D-1 pair: profile_r {r_a:.3f} -> {r_b:.3f}, cv_ratio "
            f"{ratio_a:.3f} -> {ratio_b:.3f} [P3 {'PASS' if p3 else 'FAIL'}]"
        )
        print(
            f"  S1: gas {gas_a:.2f} -> {gas_b:.2f} TWh ({gas_b - gas_a:+.3f}); "
            f"CA lambda {lam_a:.4f} -> {lam_b:.4f} ({100 * (lam_b / lam_a - 1):+.2f} %)"
        )
        print(f"  S3: h<10MW {lo10[0]} -> {lo10[1]}; h<100MW {lo100[0]} -> {lo100[1]}")

        # hydro annual energy conservation (the family must not change water)
        print(
            f"  hydro annual: A {ha.sum() / 1e6:.2f} TWh -> B {hb.sum() / 1e6:.2f} TWh"
        )

    # P4 / K3 from the committed diagnostics artifacts
    for mech in ("hydro_ror_flat", "hydro_min_flow"):
        rows = d2_share(b_dir, mech)
        offw = d4_offwindow(b_dir, mech)
        print(f"\nB-arm D-2 rows for {mech}: {rows if rows else 'ABSENT'}")
        print(f"B-arm D-4 off-window shares for {mech}: {offw if offw else 'ABSENT'}")
        if rows and any(float(r.get("share", 0.0)) < 0 for r in rows):
            fails.append(f"P4: negative D-2 share for {mech}")
        if any(v > 0.0 for v in offw):
            kills.append(f"K3: off-window share > 0 for {mech}")

    print("\n=== VERDICT (pre-registered) ===")
    print(f"PRIMARY failures: {fails if fails else 'none'}")
    print(f"KILLS: {kills if kills else 'none'}")
    verdict = "KILLED" if kills else ("REJECTED (primary)" if fails else "PASS")
    print(f"family verdict as armed: {verdict}")


if __name__ == "__main__":
    main()
