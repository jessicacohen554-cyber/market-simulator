"""caiso-151 A/B comparison — control vs the `caiso_firm_import_selfsched_clip` arm.

Scores the pre-registered checks in
``results/calibration/PREREG-caiso151-firm-selfsched-clip-2026-07-31.md`` against
the two solved bundles with **no re-solve**: everything reads the committed
per-run sidecars (``hourly/class_hourly_<year>.parquet``,
``hourly/system_<year>.parquet``) plus ``metrics.json`` and
``legitimacy_diagnostics.json``. Adapted from
``_caiso148_arm_compare.py`` — same seams, different mechanism.

Checks, in the pre-registration's own numbering:

* **§4(b)** — is the clip inert? (import class-hour deltas per year; the
  mechanism is `I` rather than `K` if annual import energy moves < 0.5 %)
* **§3** — the E1-ADVERSE prediction, tested rather than asserted: overnight
  (h22–h05) λ is expected to RISE, and the removed import energy is expected to
  be concentrated there.
* **displacement** — which classes absorb the removed import.
* **§5.8 / §6** — the protective gates on the classes that ABSORB the change:
  **CC_REGULAR** and **CT_PEAKER** (C7-gated; CT_PEAKER additionally C8
  peaker-capped at 0.15), plus ST_GAS/COAL (C7-gated). Nuclear, CC_CHP, CT_CHP
  and ST_CHP are exempt from BOTH C7 and C8 by **explicit class list**, not by
  the 2 % materiality floor, so none of their D-1/D-2 numbers is reported here
  as a gate.
* **criterion verdicts**, both arms UNATTESTED (the control carries no
  attestation, so the comparison is criterion-by-criterion on raw metrics).

Usage::

    .venv/bin/python scripts/probes/_caiso151_arm_compare.py \
        --control results/calibration/caiso151_control_A \
        --arm     results/calibration/caiso151_clip_B
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)

#: Classes that absorb displaced import AND are gated (legitimacy_diagnostics
#: D1_GATED_CLASSES / D2_PEAKER_CLASSES). The CHP and nuclear classes sit in the
#: explicit exempt list and are deliberately absent — quoting an exempt class's
#: number as a passed gate is the error caiso-147 §G warns about.
ABSORBING_GATED = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL")

#: The window FINDING-caiso150 §C located the over-forcing in.
OVERNIGHT_HODS = (22, 23, 0, 1, 2, 3, 4, 5)


def class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class-hour dispatch for one bundle-year (the scored pass)."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return df[df["pass"] == "P1"]


def system_hourly(bundle: Path, year: int) -> pd.Series:
    """Hourly demand-weighted system price for one bundle-year (P1 pass)."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).sort_index()


def _series(bundle: Path, year: int, klass: str) -> pd.Series:
    d = class_hourly(bundle, year)
    return d[d.klass == klass].set_index("hour").mw.sort_index()


def inertness(control: Path, arm: Path) -> None:
    """§4(b) — did the clip actually remove forced import?"""
    print(
        "\n=== §4(b) — import energy and inertness (gate: |d| > 0.5 % to be live) ==="
    )
    for yr in YEARS:
        c = _series(control, yr, "import")
        a = _series(arm, yr, "import")
        if c.empty or a.empty:
            print(f"  {yr}: no import rows — SKIP")
            continue
        d = (a - c).dropna()
        pct = 100.0 * (a.sum() / c.sum() - 1.0)
        nz = int((d.abs() > 1.0).sum())
        print(
            f"  {yr}: import {c.sum() / 1e6:7.3f} -> {a.sum() / 1e6:7.3f} TWh "
            f"(d={(a.sum() - c.sum()) / 1e6:+.3f} TWh, {pct:+.3f} %)  "
            f"hours|d|>1MW={nz:5d}  max|d|={d.abs().max():7.1f} MW"
        )
        print(f"        {'INERT — verdict I' if abs(pct) <= 0.5 else 'binding — live'}")


def e1_adverse(control: Path, arm: Path) -> None:
    """§3 — the registered E1-adverse prediction, tested not asserted."""
    print("\n=== §3 — E1-ADVERSE prediction: overnight lambda RISES (h22-h05) ===")
    for yr in YEARS:
        try:
            c = system_hourly(control, yr).to_numpy(float)
            a = system_hourly(arm, yr).to_numpy(float)
        except FileNotFoundError:
            print(f"  {yr}: no system sidecar — SKIP")
            continue
        n = min(len(c), len(a))
        c, a = c[:n], a[:n]
        hod = np.arange(n) % 24
        night = np.isin(hod, OVERNIGHT_HODS)
        print(
            f"  {yr}: overnight mean {c[night].mean():7.2f} -> {a[night].mean():7.2f} "
            f"(d={a[night].mean() - c[night].mean():+.3f} $/MWh)   "
            f"all-hours {c.mean():7.2f} -> {a.mean():7.2f} "
            f"(d={a.mean() - c.mean():+.3f})"
        )
        cimp = _series(control, yr, "import").to_numpy(float)[:n]
        aimp = _series(arm, yr, "import").to_numpy(float)[:n]
        rem = cimp - aimp
        tot = rem.sum()
        if abs(tot) > 1e-6:
            print(
                f"        removed import energy {tot / 1e6:+.3f} TWh; "
                f"overnight share of it {100 * rem[night].sum() / tot:5.1f} % "
                f"(predicted: concentrated overnight)"
            )


def absorbers(control: Path, arm: Path) -> None:
    """Where the removed import energy lands, by class."""
    print("\n=== Displacement: annual class energy delta (arm - control), GWh ===")
    for yr in YEARS:
        c = class_hourly(control, yr).groupby("klass").mw.sum() / 1e3
        a = class_hourly(arm, yr).groupby("klass").mw.sum() / 1e3
        d = (a - c).dropna().sort_values(key=np.abs, ascending=False)
        top = d[d.abs() > 0.5].head(9)
        print(f"  {yr}: " + "  ".join(f"{k} {v:+.1f}" for k, v in top.items()))


def criteria(control: Path, arm: Path) -> None:
    """Criterion-by-criterion verdict comparison (both arms UNATTESTED)."""
    print("\n=== Criterion verdicts (control vs arm, both unattested) ===")
    try:
        mc = json.load(open(control / "metrics.json"))
        ma = json.load(open(arm / "metrics.json"))
    except FileNotFoundError as e:
        print(f"  metrics.json missing ({e}) — SKIP")
        return
    print(f"  determination: {mc.get('determination')}  ->  {ma.get('determination')}")
    cc, ca = mc.get("criteria", {}), ma.get("criteria", {})
    for k in sorted(set(cc) | set(ca)):
        vc, va = cc.get(k, {}), ca.get(k, {})
        vc = vc.get("verdict", vc) if isinstance(vc, dict) else vc
        va = va.get("verdict", va) if isinstance(va, dict) else va
        flag = "" if vc == va else "   <-- CHANGED"
        print(f"    {k:14s} {str(vc):10s} -> {str(va):10s}{flag}")


def _row(rows: list, year: int, klass: str) -> dict | None:
    return next(
        (r for r in rows if r.get("year") == year and r.get("class") == klass), None
    )


def gates(control: Path, arm: Path) -> None:
    """§5.8/§6 protective gates on the ABSORBING classes only."""
    print("\n=== Protective gates — ABSORBING classes (exempt classes NOT shown) ===")
    side = {}
    for tag, b in (("control", control), ("arm", arm)):
        p = b / "legitimacy_diagnostics.json"
        if not p.exists():
            print(f"  {tag}: legitimacy_diagnostics.json ABSENT — C7/C8 would SKIP")
            continue
        d = json.load(open(p))
        side[tag] = d["diagnostics"]
    if len(side) < 2:
        return

    print("  D-1 (C7 diurnal shape), control -> arm:")
    for k in ABSORBING_GATED:
        for yr in YEARS:
            rc = _row(side["control"]["D1"]["rows"], yr, k)
            ra = _row(side["arm"]["D1"]["rows"], yr, k)
            if not rc or not ra:
                continue
            chg = "" if rc["verdict"] == ra["verdict"] else "   <-- CHANGED"
            print(
                f"    {k:11s} {yr}  profile_r {rc['profile_r']:.3f} -> "
                f"{ra['profile_r']:.3f}   cv_ratio {rc['cv_ratio']:.3f} -> "
                f"{ra['cv_ratio']:.3f}   gated={rc['gated']}  "
                f"{rc['verdict']} -> {ra['verdict']}{chg}"
            )

    print("  D-2 (C8 forced share), control -> arm:")
    for k in ABSORBING_GATED:
        for yr in YEARS:
            cr = [
                r
                for r in side["control"]["D2"]["rows"]
                if r.get("class") == k and r.get("year") == yr
            ]
            ar = [
                r
                for r in side["arm"]["D2"]["rows"]
                if r.get("class") == k and r.get("year") == yr
            ]
            for rc in cr:
                ra = next((r for r in ar if r["mechanism"] == rc["mechanism"]), None)
                if ra is None:
                    continue
                print(
                    f"    {k:11s} {yr}  {rc['mechanism']:26s} share "
                    f"{rc['share_of_class']:.4f} -> {ra['share_of_class']:.4f}"
                )

    print("  D-4 (off-window binding) — firm_import is newly visible at caiso-151:")
    for tag in ("control", "arm"):
        rows = side[tag].get("D4", {}).get("rows", [])
        for r in rows:
            if "firm_import" in str(r.get("floor", "")):
                print(
                    f"    {tag:7s} {r.get('year')}  {r.get('floor')}  "
                    f"window {r.get('window')}  floored {r.get('floored_twh')} TWh  "
                    f"offwindow {r.get('offwindow_share')}  {r.get('verdict')}"
                )
    for tag in ("control", "arm"):
        print(
            f"  {tag}: D1 passed={side[tag]['D1']['passed']}  "
            f"D2 passed={side[tag]['D2']['passed']}"
        )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    a = ap.parse_args()
    print(f"CONTROL {a.control}\nARM     {a.arm}")
    inertness(a.control, a.arm)
    e1_adverse(a.control, a.arm)
    absorbers(a.control, a.arm)
    criteria(a.control, a.arm)
    gates(a.control, a.arm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
