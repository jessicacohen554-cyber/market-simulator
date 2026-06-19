"""Before/after comparison for the reliability-deployment overlay.

Given a baseline and a treatment bundle (same year), prints:
  * zonal net-export and model-thermal-by-zone, before -> after (TWh)
  * per-class model TWh + miss vs (EIA-923 - BTM), before -> after, with the
    universal gate verdict (|model-actual| <= 0.33% / 0.5% of ISO annual gen).

ISO annual generation (TWh) for the 0.33%/0.5% gate denominators.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from lib.session_score import class_table  # noqa: E402
from lib.reldeploy_zonal_report import THERMAL  # noqa: E402

ISO_GEN = {2023: 446.0, 2024: 463.0, 2025: 488.0}
ZONES = ["North", "South_Central", "West", "Northeast", "Houston", "South"]
CLS_MAP = {"COAL": ["COAL_PRB", "COAL_LIGNITE"]}  # dispatch COAL -> 923 classes


def zonal(bundle: Path, year: int):
    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    sysd = pd.read_parquet(bundle / "system.parquet")
    sysd = sysd[(sysd["year"] == year) & (sysd["pass"] == "P1")]
    gen = disp.groupby("zone", observed=True)["mw"].sum() / 1e6
    dem = sysd.groupby("zone", observed=True)["demand"].sum() / 1e6
    th = (disp[disp["klass"].isin(THERMAL)]
          .groupby("zone", observed=True)["mw"].sum() / 1e6)
    cc = (disp[disp["klass"] == "CC_REGULAR"]
          .groupby("zone", observed=True)["mw"].sum() / 1e6)
    return (gen - dem), th, cc


def main() -> None:
    base = Path(sys.argv[1])
    treat = Path(sys.argv[2])
    year = int(sys.argv[3]) if len(sys.argv) > 3 else 2025

    nb, tb, cb = zonal(base, year)
    nt, tt, ct = zonal(treat, year)
    print(f"\n=== zonal before -> after (year {year}) ===")
    print(f"{'zone':>14} | {'net-export':>20} | {'model thermal':>20} | "
          f"{'CC_REGULAR':>20}")
    print(f"{'':>14} | {'base':>9} {'rd':>9} | {'base':>9} {'rd':>9} | "
          f"{'base':>9} {'rd':>9}")
    for z in ZONES:
        print(f"{z:>14} | {nb.get(z, 0):>9.1f} {nt.get(z, 0):>9.1f} | "
              f"{tb.get(z, 0):>9.1f} {tt.get(z, 0):>9.1f} | "
              f"{cb.get(z, 0):>9.1f} {ct.get(z, 0):>9.1f}")

    # Class gate.
    croot = (REPO / "results" / "calibration").resolve()
    cbt = class_table(str(base.resolve().relative_to(croot)))
    ctt = class_table(str(treat.resolve().relative_to(croot)))
    cbt = cbt[cbt["year"] == year].set_index("class")
    ctt = ctt[ctt["year"] == year].set_index("class")
    g033 = 0.0033 * ISO_GEN[year]
    g050 = 0.005 * ISO_GEN[year]
    print(f"\n=== class gate (year {year}; 0.33%={g033:.2f} 0.5%={g050:.2f} "
          f"TWh) ===")
    print(f"{'class':>13} {'bench':>7} {'base_d':>8} {'rd_d':>8} "
          f"{'g033':>6} {'g050':>6}")
    for cls in cbt.index:
        bench = cbt.loc[cls, "bench"]
        bd = cbt.loc[cls, "model"] - bench
        rd = ctt.loc[cls, "model"] - bench
        excl = cls == "CT_CHP"
        v033 = "excl" if excl else ("PASS" if abs(rd) <= g033 else "FAIL")
        v050 = "excl" if excl else ("PASS" if abs(rd) <= g050 else "FAIL")
        print(f"{cls:>13} {bench:>7.1f} {bd:>8.2f} {rd:>8.2f} "
              f"{v033:>6} {v050:>6}")


if __name__ == "__main__":
    main()
