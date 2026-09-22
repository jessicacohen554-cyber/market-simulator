"""nwpp-46: evaluate the PRE-REGISTERED kill condition. ZERO LP.

WRITTEN AND COMMITTED BEFORE ANY LEG LANDED, deliberately: a kill condition
that is coded after the numbers are in hand is a kill condition that can be
written to fit them. Every threshold below is transcribed from
``docs/handoffs/PRECOMMIT-nwpp-46-2026-09-22.md`` §7 and nothing else.

THE CONDITION (PRECOMMIT §7, verbatim in substance):

  INERT limb -> verdict I.  If the solved HYDRO amplitude ratio does not fall
  by at least 0.03 in EVERY year -- i.e. if 2023 >= 1.11, 2024 >= 1.17, or
  2025 >= 1.35 -- the mechanism did not do what its own exactly-computed
  signature says it must, and the arm reads INERT whatever C4 does.

  OVERSHOOT limb -> verdict R.  Any one of:
    (a) the solved hydro amplitude ratio falls BELOW 0.90 in any year;
    (b) any C1 COAL row leaves its +/-8.00 TWh band;
    (c) NWPP hydro ANNUAL ENERGY moves by more than 5.0 TWh in any year
        (106.872 / 107.879 / 113.077 TWh in the keeper).

  A C4 ``r`` that fails to clear 0.70 is NOT a kill limb (PRECOMMIT §6d,
  rule 1 ``[R-STRUCT]``).

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwpp46_gates.py \
        --bundle results/calibration/nwpp46_hydroenv_span
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.bundle_io import require_bundle_input  # noqa: E402

#: PRECOMMIT §6a: the keeper's measured hydro amplitude ratio, per year.
KEEPER_HYDRO_RATIO: dict[int, float] = {2023: 1.14, 2024: 1.20, 2025: 1.38}
#: PRECOMMIT §7 INERT limb: the arm must land at or below these.
INERT_CEIL: dict[int, float] = {2023: 1.11, 2024: 1.17, 2025: 1.35}
#: PRECOMMIT §7 OVERSHOOT (a).
OVERSHOOT_FLOOR: float = 0.90
#: PRECOMMIT §7 OVERSHOOT (c): keeper hydro annual energy, TWh, and the budget.
KEEPER_HYDRO_TWH: dict[int, float] = {
    2023: 106.872, 2024: 107.879, 2025: 113.077,
}
HYDRO_TWH_BUDGET: float = 5.0
#: PRECOMMIT §6c: the predicted coal amplitude ratio band, reported not gated.
PREDICTED_COAL_RATIO: dict[int, tuple[float, float]] = {
    2023: (0.15, 0.18), 2024: (0.11, 0.14), 2025: (0.10, 0.16),
}
KEEPER_COAL_RATIO: dict[int, float] = {2023: 0.10, 2024: 0.05, 2025: 0.04}

HYDRO_CLASSES = ("hydro", "HYDRO")
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL")


def _diurnal(x: np.ndarray) -> np.ndarray:
    n = len(x) // 24 * 24
    return x[:n].reshape(-1, 24).mean(axis=0)


def _swing(x: np.ndarray) -> float:
    d = _diurnal(x)
    return float(d.max() - d.min())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    bundle = Path(args.bundle)
    e930 = pd.read_parquet(require_bundle_input(bundle, "eia930"))

    inert_hits: list[str] = []
    overshoot_hits: list[str] = []
    print(f"nwpp-46 PRE-REGISTERED GATES — {bundle}\n")
    print(f"  {'yr':<6}{'hydro TWh':>11}{'dTWh':>8}{'hyd ratio':>11}"
          f"{'keeper':>8}{'limit':>8}{'coal ratio':>12}{'predicted':>14}")
    for year in args.years:
        ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        a = e930[e930["year"] == year]

        def series(classes, name):
            m = (ch[ch["klass"].isin(classes)].groupby("hour")["mw"].sum()
                 .sort_index().to_numpy(float))
            act = a[a["series"] == name].sort_values("hour")["mw"].to_numpy(float)
            n = min(len(m), len(act))
            return m[:n], act[:n]

        hm, ha = series(HYDRO_CLASSES, "hydro")
        cm, ca = series(COAL_CLASSES, "coal")
        hr = _swing(hm) / _swing(ha)
        cr = _swing(cm) / _swing(ca)
        twh = hm.sum() / 1e6
        dtwh = twh - KEEPER_HYDRO_TWH[year]
        lo, hi = PREDICTED_COAL_RATIO[year]
        print(f"  {year:<6}{twh:>11.3f}{dtwh:>+8.3f}{hr:>11.3f}"
              f"{KEEPER_HYDRO_RATIO[year]:>8.2f}{INERT_CEIL[year]:>8.2f}"
              f"{cr:>12.3f}{f'{lo:.2f}-{hi:.2f}':>14}")
        if hr >= INERT_CEIL[year]:
            inert_hits.append(f"{year}: hydro ratio {hr:.3f} >= {INERT_CEIL[year]:.2f}")
        if hr < OVERSHOOT_FLOOR:
            overshoot_hits.append(f"{year}: hydro ratio {hr:.3f} < {OVERSHOOT_FLOOR}")
        if abs(dtwh) > HYDRO_TWH_BUDGET:
            overshoot_hits.append(
                f"{year}: hydro energy moved {dtwh:+.3f} TWh (> {HYDRO_TWH_BUDGET})")

    print("\n  OVERSHOOT (b): C1 COAL rows against the +/-8.00 TWh band — "
          "read from scripts/calibration_verdict.py on the registered run.")
    print("\n" + "=" * 72)
    if overshoot_hits:
        print("  VERDICT R (rejected) — OVERSHOOT limb fired:")
        for h in overshoot_hits:
            print(f"    - {h}")
        return 2
    if inert_hits:
        print("  VERDICT I (inert) — INERT limb fired:")
        for h in inert_hits:
            print(f"    - {h}")
        return 1
    print("  Neither limb fired on (a)/(c). The arm did what its signature predicted.")
    print("  Still to check: OVERSHOOT (b), the C1 COAL rows, on the scored run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
