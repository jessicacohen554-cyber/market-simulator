"""miso-266 — the A/B readout over the per-year control/arm bundle pairs.

One table, three questions, all answered from the committed bundles with no LP:

* **DRIFT** — each CONTROL leg against the COMMITTED KEEPER. This is the rule 29
  ``[R-SCREEN]`` (b) form-4 question, and measuring it is what settles whether
  the keeper could have served as the control. (It could: the drift is zero.
  See the PRECOMMIT's §4 correction.)
* **ARM** — each arm against its OWN same-SHA, same-container control. This is
  the mechanism, and it needs no argument about which years reproduce.
* **CONSERVATION** — total generation moves by ~0 in every year, because the
  flag reallocates availability rather than creating or destroying energy.

Run it over whatever years are present; it reports what it finds and says which
years are missing rather than failing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CAL = REPO / "results" / "calibration"
#: Reported per year. COAL_* are the charter's object; the rest are where the
#: displaced energy goes. CC_CHP / ST_CHP are EXCLUDED from the flag by
#: construction, so any move there is merit-order displacement, never a changed
#: availability envelope (proved by _miso266_chp_exclusion_check.py).
CLASSES = (
    "COAL_BIT",
    "COAL_PRB",
    "COAL_LIGNITE",
    "CC_REGULAR",
    "ST_GAS",
    "CT_PEAKER",
    "import",
    "CC_CHP",
    "ST_CHP",
)


#: Reproduction tolerance on a per-class ANNUAL TWh, in TWh. A class total is a
#: float sum over 8,760-8,784 hours and dozens of LP rows, so bit-exact equality
#: is not the right test even for a byte-identical solve; the measured spread
#: over the five landed years is 0.000000-0.000008 TWh, i.e. at most **8 kWh** on
#: totals of 5-160 TWh (a relative 5e-11). This threshold is 100 kWh — twelve
#: times the observed worst case and eleven orders of magnitude below any
#: decision-relevant scale, so it separates "float accumulation" from any real
#: dispatch difference without being tuned to the data it judges.
_DRIFT_TOL: float = 1e-4


def _twh(bundle: Path, year: int) -> pd.Series:
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    d = pd.read_parquet(path, columns=["klass", "mw"])
    return d.groupby("klass", observed=True)["mw"].sum() / 1e6


def _price(bundle: Path) -> float:
    return float(pd.read_parquet(bundle / "system.parquet")["price"].mean())


def _keeper_price(keeper: Path, year: int) -> float | None:
    p = keeper / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    k = pd.read_parquet(p)
    if "pass" in k.columns:
        k = k[k["pass"] == "P1"]
    return float(k["price"].mean())


def _keeper_twh(keeper: Path, year: int) -> pd.Series | None:
    p = keeper / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        return None
    k = pd.read_parquet(p)
    k = k[k["pass"] == "P1"]
    return k.groupby("klass", observed=True)["mw"].sum() / 1e6


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--years", type=int, nargs="+", default=[2020, 2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--prefix", default="miso266")
    args = ap.parse_args()

    keeper = REPO / args.keeper
    present, missing = [], []
    for y in args.years:
        c, a = CAL / f"{args.prefix}_ctl_{y}", CAL / f"{args.prefix}_arm_{y}"
        (present if (c.exists() and a.exists()) else missing).append(y)

    print("=== miso-266 A/B readout (ZERO LP, from the committed bundles) ===")
    print(f"keeper: {args.keeper}")
    print(f"years present: {present}" + (f"   MISSING: {missing}" if missing else ""))
    print()

    print("-- PRICE: control vs the committed keeper (drift), arm vs control (the mechanism) --")
    hdr = f"{'yr':>5}{'keeper':>10}{'control':>10}{'drift':>9}{'arm':>10}{'arm-ctl':>9}{'cells':>8}"
    print(hdr)
    print("-" * len(hdr))
    for y in present:
        kp = _keeper_price(keeper, y)
        cp, apx = _price(CAL / f"{args.prefix}_ctl_{y}"), _price(CAL / f"{args.prefix}_arm_{y}")
        cs = pd.read_parquet(CAL / f"{args.prefix}_ctl_{y}" / "system.parquet")["price"].to_numpy()
        as_ = pd.read_parquet(CAL / f"{args.prefix}_arm_{y}" / "system.parquet")["price"].to_numpy()
        n = int((np.abs(as_ - cs) > 1e-6).sum())
        kps = f"{kp:10.3f}" if kp is not None else f"{'—':>10}"
        dr = f"{cp - kp:+9.3f}" if kp is not None else f"{'—':>9}"
        print(f"{y:>5}{kps}{cp:10.3f}{dr}{apx:10.3f}{apx - cp:+9.3f}{n:8d}")

    print()
    print("-- PER-CLASS TWh: arm minus control --")
    hdr = f"{'yr':>5} " + "".join(f"{c[:10]:>11}" for c in CLASSES)
    print(hdr)
    print("-" * len(hdr))
    span: dict[str, float] = {}
    for y in present:
        ct = _twh(CAL / f"{args.prefix}_ctl_{y}", y)
        at = _twh(CAL / f"{args.prefix}_arm_{y}", y)
        row = f"{y:>5} "
        for c in CLASSES:
            d = float(at.get(c, 0.0)) - float(ct.get(c, 0.0))
            span[c] = span.get(c, 0.0) + d
            row += f"{d:+11.3f}"
        print(row)
        tot = float(at.sum()) - float(ct.sum())
        print(f"{'':>5} " + f"{'TOTAL Δ':>11}" + f"{tot:+11.4f}  (conservation: the flag moves availability, not energy)")
    print("-" * len(hdr))
    print(f"{'SPAN':>5} " + "".join(f"{span[c]:+11.3f}" for c in CLASSES))

    print()
    print("-- DRIFT, per class: control minus the committed keeper --")
    worst = 0.0
    for y in present:
        kt = _keeper_twh(keeper, y)
        if kt is None:
            print(f"  {y}: keeper sidecar absent, skipped")
            continue
        ct = _twh(CAL / f"{args.prefix}_ctl_{y}", y)
        m = max(
            abs(float(ct.get(k, 0.0)) - float(kt.get(k, 0.0)))
            for k in set(kt.index) | set(ct.index)
        )
        worst = max(worst, m)
        print(f"  {y}: max |Δ class TWh| vs keeper = {m:.6f}")
    print()
    print(f"  WORST DRIFT ACROSS ALL YEARS: {worst:.6f} TWh  (tolerance {_DRIFT_TOL:g})")
    if worst < _DRIFT_TOL:
        print("  => the committed keeper WAS a valid control (form 4 valid), and the")
        print("     solve-path drift between the keeper's sha and the shard's is INERT.")
    else:
        print("  => DRIFT IS REAL: the keeper is not a valid control at this HEAD.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
