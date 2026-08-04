"""caiso-172 A/B scorer — the MEASURED Path-15 split of PG&E TAC load.

Reads the two arms' COMMITTED sidecars only (``hourly/system_<year>.parquet``
+ ``metrics.json``); no LP, no replay. Reports exactly what
``PRECHECK-caiso172-path15-load-split-2026-08-04.md`` §9 pre-registered:

* the zonal **served energy** shift (the quantity observable — the caiso-162
  lesson: a `run_config.json` recording a change is not evidence the LP saw it,
  so the delta is confirmed on a QUANTITY before any price is read);
* the **NP15−ZP26 price basis**, both arms, against the measured
  +5.947 / +8.576 / +5.727 $/MWh (congestion share 80.2 / 87.2 / 81.7 %) and the
  incumbent keeper's +0.236 / +0.127 / +0.109 — **reported, not gated** (§6:
  steering a load-split input by a price residual is the outcome pin rule 13
  forbids);
* the scored headline metrics both arms carry.

Usage::

    uv run python scripts/probes/_caiso172_ab_compare.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CONTROL = REPO / "results/calibration/caiso172_control_pge_estimate"
ARM = REPO / "results/calibration/caiso172_measured_path15_split"
KEEPER = REPO / "results/calibration/caiso166_measured_loss_zones"
YEARS = (2023, 2024, 2025)

#: Measured CAISO NP15−ZP26 annual-mean basis ($/MWh) and its congestion share,
#: from ASSESSMENT-caiso171 §4 KNOWN-OPEN 1 (itself caiso-163 S3 / caiso-164).
MEASURED_BASIS = {2023: 5.947, 2024: 8.576, 2025: 5.727}
MEASURED_CONG_SHARE = {2023: 0.802, 2024: 0.872, 2025: 0.817}
#: The incumbent keeper's modelled basis, same source.
KEEPER_BASIS = {2023: 0.236, 2024: 0.127, 2025: 0.109}


def _system(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def zonal_energy(df: pd.DataFrame) -> pd.Series:
    """Annual served energy (TWh) per zone."""
    return df.groupby("zone")["demand"].sum() / 1e6


def basis(df: pd.DataFrame, a: str = "NP15", b: str = "ZP26") -> float:
    """Annual-mean price basis a − b ($/MWh), load-agnostic simple mean."""
    p = df.pivot_table(index="hour", columns="zone", values="price", aggfunc="mean")
    return float((p[a] - p[b]).mean())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", default=str(CONTROL))
    ap.add_argument("--arm", default=str(ARM))
    args = ap.parse_args()
    ctrl, arm = Path(args.control), Path(args.arm)

    print("=" * 78)
    print("caiso-172 A/B — MEASURED Path-15 split of PG&E TAC load")
    print(f"  control (0.86/0.14 estimate)   {ctrl.name}")
    print(f"  arm     (0.883951/0.116049)    {arm.name}")
    print("=" * 78)

    print("\n### 1. QUANTITY observable — zonal served energy (TWh), NP15/ZP26")
    print(f"{'year':<6}{'zone':<10}{'control':>10}{'arm':>10}{'delta':>10}{'delta %':>10}")
    for y in YEARS:
        c, a = _system(ctrl, y), _system(arm, y)
        if c is None or a is None:
            print(f"{y:<6}(missing sidecar: control={c is not None} arm={a is not None})")
            continue
        ce, ae = zonal_energy(c), zonal_energy(a)
        for z in ("NP15", "ZP26"):
            if z not in ce.index or z not in ae.index:
                continue
            d = ae[z] - ce[z]
            pct = 100 * d / ce[z] if ce[z] else float("nan")
            print(f"{y:<6}{z:<10}{ce[z]:>10.3f}{ae[z]:>10.3f}{d:>+10.3f}{pct:>+9.2f}%")
        tot_c = ce.sum()
        tot_a = ae.sum()
        print(f"{'':<6}{'ISO total':<10}{tot_c:>10.3f}{tot_a:>10.3f}{tot_a - tot_c:>+10.3f}"
              f"{100 * (tot_a - tot_c) / tot_c:>+9.4f}%")

    print("\n### 1b. FLOW observable — the Path-15 link (NP15->ZP26), P1")
    print(f"{'year':<6}{'arm':<9}{'mean MW':>10}{'p50':>9}{'p95':>9}"
          f"{'TWh N->S':>10}{'h at bound':>12}")
    for y in YEARS:
        for label, b in (("control", ctrl), ("arm", arm)):
            f = b / "flows.parquet"
            if not f.exists():
                continue
            d = pd.read_parquet(f)
            d = d[(d["year"] == y) & (d["pass"] == "P1")
                  & (d["from_zone"] == "NP15") & (d["to_zone"] == "ZP26")]
            if d.empty:
                continue
            mw = d["mw"]
            bound = int((mw.abs() >= 0.999 * mw.abs().max()).sum())
            print(f"{y if label == 'control' else '':<6}{label:<9}{mw.mean():>10.1f}"
                  f"{mw.median():>9.1f}{mw.quantile(0.95):>9.1f}"
                  f"{mw.clip(lower=0).sum() / 1e6:>10.3f}{bound:>12}")

    print("\n### 2. NP15−ZP26 price basis ($/MWh) — REPORTED, NOT GATED (prereg §6)")
    print(f"{'year':<6}{'measured':>10}{'cong.sh':>9}{'keeper':>9}{'control':>9}"
          f"{'arm':>9}{'arm/meas':>10}")
    for y in YEARS:
        c, a = _system(ctrl, y), _system(arm, y)
        if c is None or a is None:
            continue
        bc, ba = basis(c), basis(a)
        m = MEASURED_BASIS[y]
        print(f"{y:<6}{m:>+10.3f}{100 * MEASURED_CONG_SHARE[y]:>8.1f}%"
              f"{KEEPER_BASIS[y]:>+9.3f}{bc:>+9.3f}{ba:>+9.3f}{100 * ba / m:>9.1f}%")

    print("\n### 3. Scored headline metrics")
    for label, b in (("keeper", KEEPER), ("control", ctrl), ("arm", arm)):
        f = b / "metrics.json"
        if not f.exists():
            print(f"  {label:<8} (no metrics.json)")
            continue
        m = json.loads(f.read_text())
        det = m.get("determination", "?")
        reasons = "; ".join(m.get("reasons", []))
        print(f"  {label:<8} {det}  [{reasons}]")
        gs = m.get("grade_summary", {})
        cav = m.get("caveats", {})
        print(f"           grade {gs} ledgered={cav.get('ledgered', [])}")
        fails = [k for k, v in m.get("criteria", {}).items() if v.get("status") == "FAIL"]
        print(f"           FAIL criteria: {fails or 'none'}")

    print("\n### 4. Load-weighted mean LMP by year ($/MWh) — the C3a object")
    print(f"{'label':<10}" + "".join(f"{y:>12}" for y in YEARS))
    for label, b in (("keeper", KEEPER), ("control", ctrl), ("arm", arm)):
        cells = []
        for y in YEARS:
            df = _system(b, y)
            if df is None:
                cells.append(f"{'—':>12}")
                continue
            w = df["demand"].to_numpy()
            p = df["price"].to_numpy()
            cells.append(f"{(p * w).sum() / w.sum():>12.3f}")
        print(f"{label:<10}" + "".join(cells))
    return 0


if __name__ == "__main__":
    sys.exit(main())
