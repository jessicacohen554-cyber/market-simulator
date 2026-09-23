"""nwpp-47: evaluate the PRE-REGISTERED prediction and kill condition. ZERO LP.

WRITTEN AND COMMITTED BEFORE ANY LEG LANDED: a kill condition coded after the
numbers are in hand can be written to fit them. Every threshold below is
transcribed from ``docs/handoffs/PRECOMMIT-nwpp-47-2026-09-22.md`` §4-§5.

The arm (``nwpp_grid_carried_wind_served``) changes ONE input: it adds GRID's
pool-carried wind back onto the served schedule, raising the LP's energy
requirement by exactly +2.074 / +2.171 / +2.002 TWh (computed zero-LP from
``load_demand``). Everything below is a difference against the keeper's own
committed bundle (rule 29(b) form 4; G-DRIFT all-INERT, PRECOMMIT §3).

KILL LIMBS (either fires -> the run is NOT evidence and is not registered as
a candidate; the limb that fired is reported):

  PLUMBING / INERT.  P1 demand delta != the zero-LP delta within 0.010 TWh in
  any year, OR total P1 generation moves by less than 1.5 TWh in any year —
  the input did not reach the LP.

  OVERSHOOT.  Total P1 generation moves by more than 2.6 TWh in any year, OR
  any class whose energy is pinned to a measured budget / profile (hydro,
  wind, solar, nuclear, biomass, OTHER) moves by more than 0.10 TWh, OR any
  single class moves by more than 2.5 TWh — something other than the
  requirement moved.

REPORTED, NEVER A KILL LIMB (rule 1 [R-STRUCT]):
  * the predicted split: CC_REGULAR absorbs 0.5-1.0 of the added energy in
    every year; coal classes together absorb <= 0.3;
  * C1 CC_REGULAR 2023, predicted [-7.60, -6.57] TWh vs actual. Whether it
    clears the +/-8.00 band is a consequence, not a criterion.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwpp47_gates.py \
        --arm results/calibration/<composed arm bundle>
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

KEEPER_BUNDLE = Path("results/calibration/nwpp46_hydroenv_span")
BENCH = Path("frontend/data/backcast/bench/NWPP")
YEARS = (2023, 2024, 2025)

#: PRECOMMIT §2: the zero-LP demand delta the arm adds, TWh.
DEMAND_DELTA: dict[int, float] = {2023: 2.074, 2024: 2.171, 2025: 2.002}
DEMAND_TOL = 0.010
GEN_MIN, GEN_MAX = 1.5, 2.6
PINNED_CLASSES = ("hydro", "wind", "solar", "nuclear", "biomass", "OTHER")
PINNED_TOL = 0.10
CLASS_MAX = 2.5
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE")
CC_SHARE = (0.5, 1.0)
COAL_SHARE_MAX = 0.3
CC_2023_BAND = (-7.60, -6.57)


def _year(bundle: Path, year: int) -> tuple[pd.Series, float]:
    cls = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    return cls.groupby("klass")["mw"].sum() / 1e6, float(sysf["demand"].sum()) / 1e6


def main() -> int:
    """Print the gate table and return 1 when a kill limb fires."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--keeper", default=str(KEEPER_BUNDLE))
    args = ap.parse_args()
    arm, keep = Path(args.arm), Path(args.keeper)
    fired: list[str] = []
    for year in YEARS:
        k_cls, k_dem = _year(keep, year)
        a_cls, a_dem = _year(arm, year)
        d = a_cls.sub(k_cls, fill_value=0.0)
        d_dem, d_gen = a_dem - k_dem, float(d.sum())
        bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["classFull"]
        cc = float(a_cls.get("CC_REGULAR", 0.0)) - float(bench["CC_REGULAR"])
        cc_share = float(d.get("CC_REGULAR", 0.0)) / d_gen if d_gen else float("nan")
        coal_share = sum(float(d.get(c, 0.0)) for c in COAL_CLASSES) / d_gen if d_gen else float("nan")
        print(f"\n{year}: d_demand {d_dem:+.3f} (pre-reg {DEMAND_DELTA[year]:+.3f})  "
              f"d_gen {d_gen:+.3f}  CC share {cc_share:.2f}  coal share {coal_share:.2f}  "
              f"C1 CC_REGULAR {cc:+.3f} vs actual")
        for klass, v in d[d.abs() > 0.0005].sort_values().items():
            print(f"    {klass:<14}{v:+.3f}")
        if abs(d_dem - DEMAND_DELTA[year]) > DEMAND_TOL or d_gen < GEN_MIN:
            fired.append(f"PLUMBING/INERT {year}")
        if d_gen > GEN_MAX:
            fired.append(f"OVERSHOOT {year}: d_gen {d_gen:+.3f}")
        for klass in PINNED_CLASSES:
            if abs(float(d.get(klass, 0.0))) > PINNED_TOL:
                fired.append(f"OVERSHOOT {year}: pinned {klass} {float(d[klass]):+.3f}")
        big = d[d.abs() > CLASS_MAX]
        for klass, v in big.items():
            fired.append(f"OVERSHOOT {year}: {klass} {v:+.3f}")
        lo, hi = CC_SHARE
        print(f"    [reported] CC share in [{lo}, {hi}]: {lo <= cc_share <= hi};"
              f" coal share <= {COAL_SHARE_MAX}: {coal_share <= COAL_SHARE_MAX}")
        if year == 2023:
            print(f"    [reported] C1 CC_REGULAR 2023 in {CC_2023_BAND}: "
                  f"{CC_2023_BAND[0] <= cc <= CC_2023_BAND[1]}")
    print("\nKILL:", "; ".join(fired) if fired else "none fired")
    return 1 if fired else 0


if __name__ == "__main__":
    raise SystemExit(main())
