"""caiso-130 A/B gate scorer: `hydro_budget_nameplate_aware` vs same-HEAD control.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-caiso130-hydro-budget-nameplate-aware-2026-07-27.md``
from the two solved bundles (arm A = keeper recipe, arm B = + the single flag)
plus raw EIA-930 and the committed actual-LMP validation source — no solve, and
no gate that is not in the prereg. Reuses the committed caiso-125/126
instruments' loaders so every session measures the same windows on the same
series.

Usage:
    PYTHONPATH=.:src:scripts/probes .venv/bin/python \
        scripts/probes/_caiso130_nameplate_ab.py \
        --control results/calibration/caiso130_control_A \
        --arm results/calibration/caiso130_nameplate_B
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

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
    system_frame,
)

YEARS = (2023, 2024, 2025)
LMP = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"

# Pre-registered thresholds (PREREG-caiso130 §3-§5). Frozen with the prereg.
EVENING_CEILING_MW = {2023: 64.8, 2024: 172.5, 2025: 13.2}  # §3, no-feedback
P1_MIN_FRAC_OF_CEILING = 0.25  # §4 P1 size limb
P2_PREDICTED_MW = {2023: 14.8, 2024: 38.9, 2025: 3.0}  # §4 P2, full delivery
P2_MIN_FRAC = 0.60
P3_MAX_D2_SHARE_MOVE_PP = 2.0
K1_C3A_MAX_WORSEN_PP = 0.25
K2_OVERNIGHT_MAX_WORSEN_MW = 50.0
K3_BELLY_ABS_MW = 150.0


def window_gap(series: np.ndarray, meas: np.ndarray, win: str) -> float:
    """Return mean (model - measured) MW over an hour-of-day window."""
    hod = np.arange(len(series)) % 24
    sel = np.isin(hod, list(WINDOWS[win]))
    return float(np.nanmean(series[sel] - meas[sel]))


def actual_mean_lmp(year: int) -> float:
    """Return the measured CAISO RT hourly mean LMP for ``year`` ($/MWh)."""
    frame = pd.read_parquet(LMP)
    frame = frame[frame.year == year].sort_values("hour")
    return float(np.nanmean(frame["rt"].to_numpy(dtype=float)[: 365 * 24]))


def d4_offwindow(bundle: Path, mech: str) -> list[float]:
    """Return the D-4 off-window shares recorded for ``mech`` in the bundle."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text())
    rows = payload.get("diagnostics", {}).get("D4", {}).get("rows", [])
    return [float(r.get("offwindow_share", 0.0)) for r in rows if r.get("floor") == mech]


def d2_shares(bundle: Path, mech: str) -> dict[int, float]:
    """Return ``{year: forced share}`` for ``mech`` from the bundle diagnostics."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text())
    rows = payload.get("diagnostics", {}).get("D2", {}).get("rows", [])
    out: dict[int, float] = {}
    for r in rows:
        if r.get("mechanism") == mech and r.get("year") is not None:
            out[int(r["year"])] = float(r.get("share", 0.0))
    return out


def rubric_status(bundle: Path) -> dict[str, str]:
    """Return ``{criterion: status}`` from the bundle's scored metrics."""
    path = bundle / "metrics.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text())
    return {k: v.get("status", "") for k, v in payload.get("criteria", {}).items()}


def main() -> None:
    """Score every pre-registered gate and print the verdict table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True)
    ap.add_argument("--arm", required=True)
    args = ap.parse_args()
    a_dir, b_dir = Path(args.control), Path(args.arm)

    fails: list[str] = []
    kills: list[str] = []
    report: dict = {"years": {}}

    print("=== caiso-130 pre-registered gate score (PREREG-caiso130 §4-§6) ===")
    for year in YEARS:
        ha, hb = hydro_hourly(a_dir, year), hydro_hourly(b_dir, year)
        meas = measured_hydro(year, len(ha))
        gaps = {
            w: (window_gap(ha, meas, w), window_gap(hb, meas, w))
            for w in ("overnight", "belly", "evening")
        }

        # --- P1 PRIMARY: evening moves toward zero, by >= 25 % of the ceiling
        ea, eb = gaps["evening"]
        move = eb - ea  # positive == less negative == toward zero
        ceiling = EVENING_CEILING_MW[year]
        need = P1_MIN_FRAC_OF_CEILING * ceiling
        p1 = move > 0.0 and move >= need
        if not p1:
            fails.append(
                f"P1 {year}: evening {ea:+.1f} -> {eb:+.1f} (move {move:+.1f} MW, "
                f"need >= {need:+.1f})"
            )

        # --- P2: annual hydro energy deficit narrows
        ann_a, ann_b = float(np.nanmean(ha)), float(np.nanmean(hb))
        rise = ann_b - ann_a
        need2 = P2_MIN_FRAC * P2_PREDICTED_MW[year]
        p2 = rise >= need2
        if not p2:
            fails.append(
                f"P2 {year}: annual hydro {ann_a:.1f} -> {ann_b:.1f} MW "
                f"(rise {rise:+.1f}, need >= {need2:+.1f})"
            )

        # --- K1: the C3a guard
        act = actual_mean_lmp(year)
        lam_a = float(np.mean(ca_lambda(system_frame(a_dir, year))))
        lam_b = float(np.mean(ca_lambda(system_frame(b_dir, year))))
        err_a, err_b = abs(lam_a / act - 1.0) * 100.0, abs(lam_b / act - 1.0) * 100.0
        if err_b - err_a > K1_C3A_MAX_WORSEN_PP:
            kills.append(
                f"K1 {year}: C3a |err| {err_a:.2f} % -> {err_b:.2f} % "
                f"(+{err_b - err_a:.2f} pp > {K1_C3A_MAX_WORSEN_PP})"
            )

        # --- K2: overnight may not worsen by more than +50 MW
        oa, ob = gaps["overnight"]
        if abs(ob) - abs(oa) > K2_OVERNIGHT_MAX_WORSEN_MW:
            kills.append(
                f"K2 {year}: overnight |gap| {abs(oa):.0f} -> {abs(ob):.0f} MW"
            )

        # --- K3: belly stays inside +/-150 MW
        ba, bb = gaps["belly"]
        if abs(bb) > K3_BELLY_ABS_MW:
            kills.append(f"K3 {year}: belly gap B {bb:+.0f} MW (A {ba:+.0f})")

        piv_a, piv_b = class_pivot(a_dir, year), class_pivot(b_dir, year)
        gas_a = float(
            piv_a[[c for c in GAS_CLASSES if c in piv_a.columns]].sum().sum() / 1e6
        )
        gas_b = float(
            piv_b[[c for c in GAS_CLASSES if c in piv_b.columns]].sum().sum() / 1e6
        )

        print(f"\n{year}:")
        print(
            f"  evening gap {ea:+7.1f} -> {eb:+7.1f} MW (move {move:+6.1f}, "
            f"ceiling {ceiling:+5.1f}, feedback ratio "
            f"{move / ceiling if ceiling else float('nan'):+.2f}x) "
            f"[P1 {'PASS' if p1 else 'FAIL'}]"
        )
        print(
            f"  annual hydro {ann_a:7.1f} -> {ann_b:7.1f} MW (rise {rise:+5.1f}, "
            f"predicted {P2_PREDICTED_MW[year]:+5.1f}) [P2 {'PASS' if p2 else 'FAIL'}]"
        )
        print(
            f"  overnight {oa:+7.1f} -> {ob:+7.1f} [K2 "
            f"{'ok' if abs(ob) - abs(oa) <= K2_OVERNIGHT_MAX_WORSEN_MW else 'KILL'}]; "
            f"belly {ba:+7.1f} -> {bb:+7.1f} [K3 "
            f"{'ok' if abs(bb) <= K3_BELLY_ABS_MW else 'KILL'}]"
        )
        print(
            f"  CA lambda {lam_a:.3f} -> {lam_b:.3f} vs actual {act:.3f}; "
            f"C3a |err| {err_a:+.2f} % -> {err_b:+.2f} % [K1 "
            f"{'ok' if err_b - err_a <= K1_C3A_MAX_WORSEN_PP else 'KILL'}]"
        )
        print(f"  gas {gas_a:.3f} -> {gas_b:.3f} TWh ({gas_b - gas_a:+.3f})")
        print(f"  hydro annual energy: {ha.sum() / 1e6:.3f} -> {hb.sum() / 1e6:.3f} TWh")

        report["years"][year] = {
            "evening_a": ea,
            "evening_b": eb,
            "evening_move": move,
            "evening_ceiling": ceiling,
            "P1": bool(p1),
            "annual_hydro_a": ann_a,
            "annual_hydro_b": ann_b,
            "annual_rise": rise,
            "P2": bool(p2),
            "overnight_a": oa,
            "overnight_b": ob,
            "belly_a": ba,
            "belly_b": bb,
            "lambda_a": lam_a,
            "lambda_b": lam_b,
            "actual_lmp": act,
            "c3a_err_a_pct": err_a,
            "c3a_err_b_pct": err_b,
            "gas_a_twh": gas_a,
            "gas_b_twh": gas_b,
        }

    # --- P3: mechanism accounting (D-2 shares, D-4 off-window)
    print("\n--- P3 mechanism accounting ---")
    for mech in ("hydro_ror_flat", "hydro_min_flow"):
        sa, sb = d2_shares(a_dir, mech), d2_shares(b_dir, mech)
        offw = d4_offwindow(b_dir, mech)
        print(f"  {mech}: D-2 share A {sa} -> B {sb}; D-4 off-window B {offw}")
        for year in sorted(set(sa) & set(sb)):
            move_pp = abs(sb[year] - sa[year]) * 100.0
            if move_pp > P3_MAX_D2_SHARE_MOVE_PP:
                fails.append(f"P3 {year}: {mech} D-2 share moved {move_pp:.2f} pp")
        if any(v > 0.0 for v in offw):
            fails.append(f"P3: D-4 off-window share > 0 for {mech}")
    report["d4_offwindow"] = {
        m: d4_offwindow(b_dir, m) for m in ("hydro_ror_flat", "hydro_min_flow")
    }

    # --- K4: rubric non-regression
    ra, rb = rubric_status(a_dir), rubric_status(b_dir)
    print(f"\n--- K4 rubric ---\n  A {ra}\n  B {rb}")
    for crit, status in ra.items():
        if status == "PASS" and rb.get(crit) == "FAIL":
            kills.append(f"K4: {crit} PASS -> FAIL")
    report["rubric_a"], report["rubric_b"] = ra, rb

    # --- K5: no silent structural change (plant count / budget total)
    print("\n--- K5 structural ---")
    for year in YEARS:
        pa = pd.read_parquet(a_dir / "hourly" / f"class_hourly_{year}.parquet")
        pb = pd.read_parquet(b_dir / "hourly" / f"class_hourly_{year}.parquet")
        ka = set(pa["klass"].unique())
        kb = set(pb["klass"].unique())
        if ka != kb:
            kills.append(f"K5 {year}: class set changed {ka ^ kb}")
        print(f"  {year}: class sets {'identical' if ka == kb else 'DIFFER'}")

    print("\n=== VERDICT (pre-registered) ===")
    print(f"PRIMARY/SECONDARY failures: {fails if fails else 'none'}")
    print(f"KILLS: {kills if kills else 'none'}")
    verdict = "KILLED" if kills else ("REJECTED (primary)" if fails else "PASS")
    print(f"delta verdict as armed: {verdict}")
    report["fails"], report["kills"], report["verdict"] = fails, kills, verdict

    out = REPO / "results" / "probes" / "caiso130_ab_score.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, default=float) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
