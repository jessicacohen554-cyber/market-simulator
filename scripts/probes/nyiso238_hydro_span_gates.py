"""nyiso-238 (ZERO LP): score nyiso-236's G1-G5 on the four-year
``hydro_budget_period_by_instrument`` arm bundle against the keeper.

Every gate is the one written in
``docs/PRECOMMIT-nyiso236-hydro-budget-period-screen-2026-09-16.md`` and re-stated
verbatim in ``docs/PRECOMMIT-nyiso238-hydro-budget-span-2026-09-16.md`` section 3:

* **G1 FEASIBILITY** - LP optimal; slack / dump as the keeper.
* **G2 IDENTITY** (KILL) - annual hydro within 0.1 %, every month within 0.5 %.
* **G3 DIRECTION & MAGNITUDE** - the cross-day footprint FALLS from the keeper's
  into 1.0-6.0 % and never reaches 0.00 (measured by
  ``scripts/probes/nyiso220_phase0_period_overlap.py``, run separately per bundle).
* **G4** - reported in BOTH forms: ``as-written`` (every non-hydro class within
  2 %) and ``material`` (2 % on classes >= 2 % of ISO load, plus conservation).
* **G5 NO NON-TARGET FLIP** - no non-hydro load-bearing criterion flips PASS ->
  FAIL. C3a / C3b are computed directly from the committed hourly sidecars
  because scoring a screen bundle through ``calibration_verdict.py`` needs a
  registry sidecar (rule 29 forbids registering one).

Usage::

    python3 scripts/probes/nyiso238_hydro_span_gates.py \\
        --keeper results/calibration/nyiso235_gasrepair_span \\
        --arm results/calibration/nyiso238_hydroperiod_span
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
YEARS = (2022, 2023, 2024, 2025)
G2_ANNUAL_TOL = 0.1   # %
G2_MONTH_TOL = 0.5    # %
G4_TOL = 2.0          # %
MATERIAL_FRAC = 0.02  # class >= 2 % of ISO load


def _classes(bundle: Path, year: int) -> pd.DataFrame:
    """Return the P1 class-hour frame for ``year``."""
    c = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    return c[c["pass"] == "P1"]


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """Return the P1 zonal system frame for ``year``."""
    s = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    return s[s["pass"] == "P1"]


def _hydro_monthly(bundle: Path, year: int) -> tuple[float, np.ndarray]:
    """Return (annual TWh, 12 monthly TWh) of every HYDRO class."""
    c = _classes(bundle, year)
    h = c[c.klass.str.contains("HYDRO", case=False, na=False)]
    by_hour = h.groupby("hour").mw.sum().sort_index()
    n = len(by_hour)
    month = pd.date_range(f"{year}-01-01", periods=n, freq="h").month
    mo = np.asarray([by_hour.to_numpy()[month == m].sum() / 1e6 for m in range(1, 13)])
    return float(by_hour.sum() / 1e6), mo


def _class_annual(bundle: Path, year: int) -> dict[str, float]:
    """Return {class: annual TWh} for ``year``."""
    c = _classes(bundle, year)
    return {k: float(v / 1e6) for k, v in c.groupby("klass").mw.sum().items()}


def _lw_price(bundle: Path, year: int) -> tuple[float, float]:
    """Return (load-weighted ISO price, total load TWh) from the zonal sidecar."""
    s = _system(bundle, year)
    s = s[s.zone != "NYISO_external"]
    w = s.demand.to_numpy()
    p = s.price.to_numpy()
    return float(np.average(p, weights=w)), float(w.sum() / 1e6)


def _slack_dump(bundle: Path, year: int) -> tuple[float, float, int, int]:
    """Return (slack MWh, dump MWh, slack hours, dump hours)."""
    s = _system(bundle, year)
    sl, du = s.slack.to_numpy(), s.dump.to_numpy()
    return float(sl.sum()), float(du.sum()), int((sl > 0).sum()), int((du > 0).sum())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", default="results/calibration/nyiso235_gasrepair_span")
    ap.add_argument("--arm", default="results/calibration/nyiso238_hydroperiod_span")
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    a = ap.parse_args()
    keep, arm = ROOT / a.keeper, ROOT / a.arm

    print(f"KEEPER {a.keeper}\nARM    {a.arm}\n")
    print("=" * 108)
    print("  G1 FEASIBILITY + G2 IDENTITY (KILL: annual <= 0.1 %, worst month <= 0.5 %)")
    print("=" * 108)
    print(f"  {'yr':>4s} {'keeper TWh':>11s} {'arm TWh':>10s} {'ann %':>9s} {'worst mo %':>11s} "
          f"{'G2':>6s} | {'slack MWh':>10s} {'dump MWh':>9s} {'G1':>5s}")
    g2 = {}
    for y in a.years:
        ka, km = _hydro_monthly(keep, y)
        aa, am = _hydro_monthly(arm, y)
        ann = 100.0 * (aa - ka) / ka
        with np.errstate(divide="ignore", invalid="ignore"):
            mo = np.where(km > 0, 100.0 * (am - km) / km, 0.0)
        worst = float(mo[np.argmax(np.abs(mo))])
        sl, du, slh, duh = _slack_dump(arm, y)
        ksl, kdu, _, _ = _slack_dump(keep, y)
        ok1 = (abs(sl - ksl) < 1e-6) and (abs(du - kdu) < 1e-6)
        ok2 = abs(ann) <= G2_ANNUAL_TOL and abs(worst) <= G2_MONTH_TOL
        g2[y] = (ann, worst, ok2)
        print(f"  {y:4d} {ka:11.4f} {aa:10.4f} {ann:+9.4f} {worst:+11.3f} "
              f"{'PASS' if ok2 else 'FAIL':>6s} | {sl:10.4f} {du:9.4f} {'PASS' if ok1 else 'FAIL':>5s}")
        if not ok2:
            lost = [(m + 1, (am[m] - km[m]) * 1e3) for m in range(12) if abs(mo[m]) > G2_MONTH_TOL]
            det = " · ".join(f"m{m:02d} {d:+.1f} GWh" for m, d in lost)
            print(f"       losing months: {det}   TOTAL {1e3*(aa-ka):+.1f} GWh")

    print()
    print("=" * 108)
    print("  G4 - BOTH FORMS (as-written: every non-hydro class within 2 %; "
          "material: classes >= 2 % of ISO load)")
    print("=" * 108)
    for y in a.years:
        kc, ac = _class_annual(keep, y), _class_annual(arm, y)
        _, load = _lw_price(keep, y)
        floor = MATERIAL_FRAC * load
        worst_w = worst_m = None
        for k in sorted(set(kc) | set(ac)):
            if "HYDRO" in k.upper():
                continue
            kv, av = kc.get(k, 0.0), ac.get(k, 0.0)
            if kv <= 0:
                continue
            pct = 100.0 * (av - kv) / kv
            if worst_w is None or abs(pct) > abs(worst_w[1]):
                worst_w = (k, pct, av - kv)
            if max(kv, av) >= floor and (worst_m is None or abs(pct) > abs(worst_m[1])):
                worst_m = (k, pct, av - kv)
        dh = sum(v for k, v in ac.items() if "HYDRO" in k.upper()) - \
             sum(v for k, v in kc.items() if "HYDRO" in k.upper())
        dn = sum(v for k, v in ac.items() if "HYDRO" not in k.upper()) - \
             sum(v for k, v in kc.items() if "HYDRO" not in k.upper())
        okw = worst_w is not None and abs(worst_w[1]) <= G4_TOL
        okm = worst_m is not None and abs(worst_m[1]) <= G4_TOL
        print(f"  {y}  as-written worst {worst_w[0]:<12s} {worst_w[1]:+7.2f} % "
              f"({worst_w[2]:+.4f} TWh) -> {'PASS' if okw else 'FAIL'}")
        print(f"        material  worst {worst_m[0]:<12s} {worst_m[1]:+7.2f} % "
              f"({worst_m[2]:+.4f} TWh) -> {'PASS' if okm else 'FAIL'}   "
              f"[materiality floor {floor:.3f} TWh]")
        print(f"        conservation: hydro {dh:+.4f} TWh vs non-hydro {dn:+.4f} TWh")

    print()
    print("=" * 108)
    print("  G5 NO NON-TARGET FLIP - C3a (ISO load-weighted price) and the gas family, "
          "computed from sidecars")
    print("=" * 108)
    print(f"  {'yr':>4s} {'keeper LW $':>12s} {'arm LW $':>10s} {'delta':>8s} | "
          f"{'keeper gas TWh':>15s} {'arm gas TWh':>12s} {'delta %':>9s}")
    for y in a.years:
        kp, _ = _lw_price(keep, y)
        apz, _ = _lw_price(arm, y)
        kc, ac = _class_annual(keep, y), _class_annual(arm, y)
        gk = sum(v for k, v in kc.items() if any(t in k.upper() for t in ("CC_", "CT_", "ST_GAS")))
        ga = sum(v for k, v in ac.items() if any(t in k.upper() for t in ("CC_", "CT_", "ST_GAS")))
        print(f"  {y:4d} {kp:12.4f} {apz:10.4f} {apz-kp:+8.4f} | {gk:15.4f} {ga:12.4f} "
              f"{100*(ga-gk)/gk:+9.3f}")

    print()
    print("=" * 108)
    print("  THE UPSIDE - hourly SHAPE against the EIA-930 meter (the reason the fix is wanted).")
    print("  A hydro budget that banks across days at zero cost displaces fossil in the WRONG hours,")
    print("  so a correct hydro shape should show up as a better GAS-fleet hourly fit.")
    print("=" * 108)
    m930 = ROOT / "data/raw/eia-930-hourly/NYIS hourly.parquet"
    if not m930.exists():
        print("  EIA-930 NYIS extract absent - skipped.")
    else:
        h = pd.read_parquet(m930)
        h["ts"] = pd.to_datetime(h["Local time"])
        h = h.groupby("ts", as_index=False).mean(numeric_only=True).sort_values("ts")
        h["yr"] = h.ts.dt.year
        print(f"  {'yr':>4s} {'series':>7s} | {'keeper r':>9s} {'arm r':>8s} {'delta':>8s} | "
              f"{'keeper NRMSE':>13s} {'arm NRMSE':>10s} {'delta':>8s}")
        for y in a.years:
            meas = h[h.yr == y].reset_index(drop=True)
            for label, col, match in (("hydro", "NG: WAT", ("HYDRO",)),
                                      ("gas", "NG: NG", ("CC_", "CT_", "ST_GAS"))):
                if col not in meas.columns:
                    continue
                row = []
                for b in (keep, arm):
                    c = _classes(b, y)
                    sel = c[c.klass.str.upper().str.startswith(match)] if label == "gas" else \
                          c[c.klass.str.contains("HYDRO", case=False, na=False)]
                    mv = sel.groupby("hour").mw.sum().sort_index().to_numpy()
                    n = min(len(mv), len(meas))
                    av = pd.to_numeric(meas[col], errors="coerce").to_numpy()[:n]
                    mv = mv[:n]
                    ok = np.isfinite(av) & np.isfinite(mv)
                    r = float(np.corrcoef(mv[ok], av[ok])[0, 1])
                    nrmse = float(np.sqrt(np.mean((mv[ok] - av[ok]) ** 2)) / np.mean(av[ok]))
                    row.append((r, nrmse))
                (kr, kn), (ar_, an) = row
                print(f"  {y:4d} {label:>7s} | {kr:9.4f} {ar_:8.4f} {ar_-kr:+8.4f} | "
                      f"{kn:13.4f} {an:10.4f} {an-kn:+8.4f}")

    print()
    print("=" * 108)
    print("  VERDICT")
    print("=" * 108)
    for y in a.years:
        ann, worst, ok = g2[y]
        print(f"  {y}: G2 {'PASS' if ok else 'FAIL'}  annual {ann:+.4f} %  worst month {worst:+.3f} %")


if __name__ == "__main__":
    main()
