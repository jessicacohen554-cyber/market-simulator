"""nwpp-49: evaluate the PRE-REGISTERED kill condition for ``hydro_pondage_bound``. ZERO LP.

WRITTEN AND COMMITTED BEFORE ANY LEG EXISTS, and before the owner has ruled
on whether any leg will be solved: a kill condition coded after the numbers
are in hand can be written to fit them. Every threshold below is transcribed
from ``docs/handoffs/FINDING-nwpp-49-pondage-design-2026-09-23.md`` §5 and
nothing else. The arm it scores is design (a2) of that FINDING: the pondage
bound on every hydro plant OUTSIDE the registered regulated chains
(``nwpp_hydro_chain.csv``), the cascade unchanged on its five plants.

METRIC. The hydro INTRA-DAY standard deviation (hourly MW minus its own daily
mean), model over EIA-930 measured, per year -- the NWPP-48 §4 metric, whose
keeper values this script reproduces (2,154 / 2,216 / 2,236 MW model against
2,004 / 1,918 / 1,913 measured).

THE CONDITION:

  INERT limb -> verdict I.  The intra-day ratio falls by less than 0.010 in
  EVERY year (arm >= 1.065 / 1.145 / 1.159).

  OVERSHOOT limb -> verdict R.  Any one of:
    (a) the intra-day ratio falls below 0.95 in any year (the bound removing
        swing the measured fleet has);
    (b) NWPP hydro ANNUAL energy moves by more than 1.0 TWh in any year (the
        rule-19 invariant says the rows move WHEN, never HOW MUCH; keeper
        106.872 / 107.879 / 113.077 TWh);
    (c) any C1 COAL row leaves its +/-8.00 TWh band (read from
        ``scripts/calibration_verdict.py`` on the registered run).

  A C4 ``r`` that fails to clear 0.70 is NOT a kill limb, and a C4 ``r`` that
  moves is not a promotion argument either (rule 1 ``[R-STRUCT]``). The coal
  bracket below is REPORTED against its prediction, never gated.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwpp49_gates.py --bundle <composed bundle>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.bundle_io import require_bundle_input  # noqa: E402

#: FINDING §5: keeper (nwpp47_gridwind_span) intra-day hydro sd ratio, model/measured.
KEEPER_RATIO: dict[int, float] = {2023: 1.075, 2024: 1.155, 2025: 1.169}
#: FINDING §5: static-clip prediction for design (a2) -- the pro-rata proxy's
#: value, which is an UPPER bound on the effect (the proxy gives every small
#: plant the fleet's full swing), so the arm is predicted in [clip, keeper].
PREDICTED_RATIO: dict[int, float] = {2023: 1.044, 2024: 1.120, 2025: 1.129}
#: INERT limb: the arm must land strictly below these.
INERT_CEIL: dict[int, float] = {2023: 1.065, 2024: 1.145, 2025: 1.159}
#: OVERSHOOT (a).
OVERSHOOT_FLOOR: float = 0.95
#: OVERSHOOT (b): keeper hydro annual energy, TWh, and the budget.
KEEPER_HYDRO_TWH: dict[int, float] = {2023: 106.872, 2024: 107.879, 2025: 113.077}
HYDRO_TWH_BUDGET: float = 1.0
#: FINDING §5, reported not gated: coal r and r_intra brackets
#: (lo = coal absorbs none of the removed hydro swing, hi = coal absorbs all).
PREDICTED_COAL_R: dict[int, tuple[float, float]] = {
    2023: (0.659, 0.670), 2024: (0.617, 0.647), 2025: (0.638, 0.674),
}
PREDICTED_COAL_R_INTRA: dict[int, tuple[float, float]] = {
    2023: (0.374, 0.464), 2024: (0.396, 0.589), 2025: (0.365, 0.527),
}

HYDRO_CLASSES = ("hydro", "HYDRO")
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL")


def _intra(x: np.ndarray) -> np.ndarray:
    """Within-day deviation of an hourly vector from its own daily mean."""
    x = x[: len(x) // 24 * 24].reshape(-1, 24)
    return (x - x.mean(1, keepdims=True)).ravel()


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r."""
    return float(np.corrcoef(a, b)[0, 1])


def main() -> int:
    """Score the bundle against the pre-registered limbs; exit 0 / 1 (I) / 2 (R)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    bundle = Path(args.bundle)
    e930 = pd.read_parquet(require_bundle_input(bundle, "eia930"))

    inert_hits: list[str] = []
    overshoot_hits: list[str] = []
    print(f"nwpp-49 PRE-REGISTERED GATES — {bundle}\n")
    print(f"  {'yr':<6}{'hydro TWh':>11}{'dTWh':>8}{'ratio':>8}{'keeper':>8}"
          f"{'pred':>7}{'ceil':>7}{'coal r':>8}{'pred':>13}{'r_intra':>9}{'pred':>13}")
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
        ratio = _intra(hm).std() / _intra(ha).std()
        twh = hm.sum() / 1e6
        dtwh = twh - KEEPER_HYDRO_TWH[year]
        cr, cri = _r(cm, ca), _r(_intra(cm), _intra(ca))
        lo, hi = PREDICTED_COAL_R[year]
        ilo, ihi = PREDICTED_COAL_R_INTRA[year]
        print(f"  {year:<6}{twh:>11.3f}{dtwh:>+8.3f}{ratio:>8.3f}{KEEPER_RATIO[year]:>8.3f}"
              f"{PREDICTED_RATIO[year]:>7.3f}{INERT_CEIL[year]:>7.3f}{cr:>8.3f}"
              f"{f'{lo:.3f}-{hi:.3f}':>13}{cri:>9.3f}{f'{ilo:.3f}-{ihi:.3f}':>13}")
        if ratio >= INERT_CEIL[year]:
            inert_hits.append(f"{year}: ratio {ratio:.3f} >= {INERT_CEIL[year]:.3f}")
        if ratio < OVERSHOOT_FLOOR:
            overshoot_hits.append(f"{year}: ratio {ratio:.3f} < {OVERSHOOT_FLOOR}")
        if abs(dtwh) > HYDRO_TWH_BUDGET:
            overshoot_hits.append(
                f"{year}: hydro energy moved {dtwh:+.3f} TWh (> {HYDRO_TWH_BUDGET})")

    print("\n  OVERSHOOT (c): C1 COAL rows against +/-8.00 TWh — read from "
          "scripts/calibration_verdict.py on the registered run.")
    print("\n" + "=" * 72)
    if overshoot_hits:
        print("  VERDICT R (rejected) — OVERSHOOT limb fired:")
        for h in overshoot_hits:
            print(f"    - {h}")
        return 2
    if len(inert_hits) == len(args.years):
        print("  VERDICT I (inert) — INERT limb fired in every year:")
        for h in inert_hits:
            print(f"    - {h}")
        return 1
    print("  Neither limb fired on (a)/(b)/INERT. Still to check: OVERSHOOT (c).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
