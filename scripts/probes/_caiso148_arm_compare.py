"""caiso-148 A/B comparison probe — control vs `nuclear_unit_availability` arm.

Scores the pre-registered checks in
``results/calibration/PREREG-caiso148-nuclear-availability-2026-07-31.md``
against the two solved bundles, with **no re-solve**: everything below reads the
committed per-run sidecars (``hourly/class_hourly_<year>.parquet``,
``hourly/system_<year>.parquet``) plus ``metrics.json`` and
``legitimacy_diagnostics.json``.

Checks, in the pre-registration's own numbering:

* **R3** — is the overlay inert? (nuclear class-hour deltas per year)
* **R4** — annual nuclear energy move > 0.5 % (the G3 gate in-solve)
* **S2** — does the arm's nuclear dispatch track EIA-930 metered better than the
  control's, on the days the extract covers?
* **§6** — the protective gates on the classes that ABSORB the displaced energy
  (CT_PEAKER / ST_GAS / COAL are C7-gated; CT_PEAKER is C8 peaker-capped).
  Nuclear is exempt from BOTH by explicit class list, so no nuclear D-1/D-2
  number is reported here as a gate.

Usage::

    python scripts/probes/_caiso148_arm_compare.py \
        --control results/calibration/caiso148_control_A \
        --arm     results/calibration/caiso148_nucavail_B
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
# The classes that absorb displaced nuclear energy and ARE gated (rule 20 /
# legitimacy_diagnostics D1_GATED_CLASSES + D2_PEAKER_CLASSES). Nuclear itself
# sits in D2_EXEMPT_CLASSES and is deliberately absent.
ABSORBING_GATED = ("CT_PEAKER", "ST_GAS", "COAL")


def class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class-hour dispatch for one bundle-year (the scored pass)."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return df[df["pass"] == "P1"]


def system_hourly(bundle: Path, year: int) -> pd.Series:
    """Hourly **demand-weighted** system price for one bundle-year (P1 pass).

    The sidecar is per (pass, zone, hour); the model's system lambda is the
    demand-weighted zonal price, so that is what is reconstructed here rather
    than a flat zone mean.
    """
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).sort_index()


def r3_r4_energy(control: Path, arm: Path) -> None:
    """R3 (inertness) and R4 (>0.5 % annual nuclear energy move)."""
    print("\n=== R3 / R4 — nuclear energy and inertness ===")
    for yr in YEARS:
        c = class_hourly(control, yr)
        a = class_hourly(arm, yr)
        cn = c[c.klass == "nuclear"].set_index("hour").mw.sort_index()
        an = a[a.klass == "nuclear"].set_index("hour").mw.sort_index()
        if cn.empty or an.empty:
            print(f"  {yr}: no nuclear rows — SKIP")
            continue
        d = (an - cn).dropna()
        dtwh = (an.sum() - cn.sum()) / 1e6
        pct = 100.0 * (an.sum() / cn.sum() - 1.0)
        nz = int((d.abs() > 1.0).sum())
        print(
            f"  {yr}: nuclear {cn.sum() / 1e6:7.4f} -> {an.sum() / 1e6:7.4f} TWh "
            f"(d={dtwh:+.4f} TWh, {pct:+.4f}%)  hours|d|>1MW={nz:5d}  "
            f"max|d|={d.abs().max():7.1f} MW"
        )
        verdict = "R4 FAIL" if abs(pct) > 0.5 else "R4 pass"
        inert = "R3 FAIL (inert)" if nz == 0 else "R3 pass (binding)"
        print(f"        {verdict} (gate |d| <= 0.5%)   {inert}")


def s2_metered(control: Path, arm: Path) -> None:
    """S2 — nuclear dispatch vs EIA-930 metered, control vs arm, covered days."""
    print("\n=== S2 — nuclear dispatch r_day vs EIA-930 CISO metered ===")
    print("    (covered days only; 2025 is expected short — 5 months keep the smear)")
    ext = pd.read_csv(REPO / "data/raw/nuclear-availability-CAISO.csv")
    ext["date"] = pd.to_datetime(ext["date"])
    g = pd.read_parquet(REPO / "data/raw/eia-930-hourly/CISO hourly.parquet")
    g["d"] = pd.to_datetime(g["Local date"]).dt.normalize()
    m930 = g.groupby("d")["NG: NUC"].mean()
    for yr in YEARS:
        cov = sorted(ext[ext.date.dt.year == yr].date.unique())
        if not cov:
            print(f"  {yr}: extract covers no day — SKIP")
            continue
        # Model clock is a fixed non-leap 8760; map covered real dates onto it.
        doy = {}
        for t in pd.to_datetime(cov):
            if t.month == 2 and t.day == 29:
                continue
            base = pd.Timestamp(2023, t.month, t.day).dayofyear - 1
            doy[t] = base
        out = {}
        for tag, b in (("control", control), ("arm", arm)):
            n = class_hourly(b, yr)
            n = n[n.klass == "nuclear"].set_index("hour").mw.sort_index()
            if n.empty:
                out[tag] = None
                continue
            arr = n.to_numpy(float)
            out[tag] = np.array(
                [arr[d * 24 : d * 24 + 24].mean() for d in doy.values()]
            )
        met = np.array([m930.get(t, np.nan) for t in doy])
        ok = np.isfinite(met)
        if out["control"] is None or out["arm"] is None:
            continue
        rc = np.corrcoef(out["control"][ok], met[ok])[0, 1]
        ra = np.corrcoef(out["arm"][ok], met[ok])[0, 1]
        mc = np.abs(out["control"][ok] - met[ok]).mean()
        ma = np.abs(out["arm"][ok] - met[ok]).mean()
        print(
            f"  {yr}: n={int(ok.sum()):3d}d  r_day {rc:.4f} -> {ra:.4f} "
            f"(lift {ra - rc:+.4f})   MAE {mc:6.1f} -> {ma:6.1f} MW"
        )


def absorbers(control: Path, arm: Path) -> None:
    """Where the displaced energy lands, by class."""
    print("\n=== Displacement: annual class energy delta (arm - control), GWh ===")
    for yr in YEARS:
        c = class_hourly(control, yr).groupby("klass").mw.sum() / 1e3
        a = class_hourly(arm, yr).groupby("klass").mw.sum() / 1e3
        d = (a - c).dropna().sort_values(key=np.abs, ascending=False)
        top = d[d.abs() > 0.5].head(9)
        print(f"  {yr}: " + "  ".join(f"{k} {v:+.1f}" for k, v in top.items()))
        mh = {}
        for k in set(c.index) | set(a.index):
            ch = class_hourly(control, yr)
            ah = class_hourly(arm, yr)
            cs = ch[ch.klass == k].set_index("hour").mw.sort_index()
            as_ = ah[ah.klass == k].set_index("hour").mw.sort_index()
            if cs.empty or as_.empty:
                continue
            mh[k] = float((as_ - cs).abs().max())
        worst = sorted(mh.items(), key=lambda kv: -kv[1])[:5]
        print(
            "        max |class-hour| delta: "
            + "  ".join(f"{k} {v:.0f} MW" for k, v in worst)
        )


def prices(control: Path, arm: Path) -> None:
    """System price movement — the C3a/C3c-relevant summary."""
    print("\n=== System price (P1) ===")
    for yr in YEARS:
        try:
            c = system_hourly(control, yr)
            a = system_hourly(arm, yr)
        except FileNotFoundError:
            print(f"  {yr}: no system sidecar — SKIP")
            continue
        cs, as_ = c.to_numpy(float), a.to_numpy(float)
        n = min(len(cs), len(as_))
        cs, as_ = cs[:n], as_[:n]
        print(
            f"  {yr}: mean {cs.mean():7.2f} -> {as_.mean():7.2f} "
            f"(d={as_.mean() - cs.mean():+.3f} $/MWh)   "
            f"p99 {np.percentile(cs, 99):7.2f} -> {np.percentile(as_, 99):7.2f}   "
            f"hours repriced |d|>0.01: {int((np.abs(as_ - cs) > 0.01).sum()):5d}"
        )


def criteria(control: Path, arm: Path) -> None:
    """Criterion-by-criterion verdict comparison (both arms UNATTESTED)."""
    print("\n=== Criterion verdicts (control vs arm, both unattested) ===")
    try:
        mc = json.load(open(control / "metrics.json"))
        ma = json.load(open(arm / "metrics.json"))
    except FileNotFoundError as e:
        print(f"  metrics.json missing ({e}) — SKIP")
        return
    print(f"  determination: {mc['determination']}  ->  {ma['determination']}")
    cc, ca = mc.get("criteria", {}), ma.get("criteria", {})
    for k in sorted(set(cc) | set(ca)):
        vc = cc.get(k, {})
        va = ca.get(k, {})
        vc = vc.get("verdict", vc) if isinstance(vc, dict) else vc
        va = va.get("verdict", va) if isinstance(va, dict) else va
        flag = "" if vc == va else "   <-- CHANGED"
        print(f"    {k:14s} {str(vc):10s} -> {str(va):10s}{flag}")


def gates(control: Path, arm: Path) -> None:
    """§6 protective gates on the ABSORBING classes only."""
    print(
        "\n=== Protective gates — ABSORBING classes (nuclear is exempt, not shown) ==="
    )
    side = {}
    for tag, b in (("control", control), ("arm", arm)):
        p = b / "legitimacy_diagnostics.json"
        if not p.exists():
            print(f"  {tag}: legitimacy_diagnostics.json ABSENT — C7/C8 would SKIP")
            continue
        d = json.load(open(p))
        side[tag] = d["diagnostics"]
        g = d.get("gates", {})
        if tag == "control":
            print(
                f"  gates: d1_min_profile_r={g.get('d1_min_profile_r')} "
                f"d1_min_cv_ratio={g.get('d1_min_cv_ratio')} "
                f"d2_peaker_max_share={g.get('d2_peaker_max_share')} "
                f"d2_merchant_max_share={g.get('d2_merchant_max_share')}"
            )
    if len(side) < 2:
        return

    print("  D-1 (C7 diurnal shape) — gated absorbing classes, control -> arm:")
    for k in ABSORBING_GATED:
        for yr in YEARS:
            rc = _row(side["control"]["D1"]["rows"], yr, k)
            ra = _row(side["arm"]["D1"]["rows"], yr, k)
            if not rc or not ra:
                continue
            chg = "" if rc["verdict"] == ra["verdict"] else "   <-- CHANGED"
            print(
                f"    {k:10s} {yr}  profile_r {rc['profile_r']:.3f} -> "
                f"{ra['profile_r']:.3f}   cv_ratio {rc['cv_ratio']:.3f} -> "
                f"{ra['cv_ratio']:.3f}   gated={rc['gated']}  "
                f"{rc['verdict']} -> {ra['verdict']}{chg}"
            )

    print("  D-2 (C8 forced share) — gated absorbing classes, control -> arm:")
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
                ra = next(
                    (r for r in ar if r["mechanism"] == rc["mechanism"]),
                    None,
                )
                if ra is None:
                    continue
                print(
                    f"    {k:10s} {yr}  {rc['mechanism']:26s} share "
                    f"{rc['share_of_class']:.4f} -> {ra['share_of_class']:.4f}"
                )
    for tag in ("control", "arm"):
        print(
            f"  {tag}: D1 passed={side[tag]['D1']['passed']}  "
            f"D2 passed={side[tag]['D2']['passed']}"
        )


def _row(rows: list, year: int, klass: str) -> dict | None:
    """First D-1 row for (year, class), or None."""
    return next(
        (r for r in rows if r.get("year") == year and r.get("class") == klass), None
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    a = ap.parse_args()
    print(f"CONTROL {a.control}\nARM     {a.arm}")
    r3_r4_energy(a.control, a.arm)
    s2_metered(a.control, a.arm)
    absorbers(a.control, a.arm)
    prices(a.control, a.arm)
    criteria(a.control, a.arm)
    gates(a.control, a.arm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
