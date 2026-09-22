"""miso-266 — prove the CHP exclusion end to end, in the production path, ZERO LP.

``outages._DISPATCHED_DENOM_EXCLUDED_GROUPS`` keeps CC_CHP / CT_CHP / ST_CHP on
their incumbent nameplate denominator, because at those bins ``cap_LP`` is the
grid-facing residual after the behind-the-meter host steam is held out and the
flag's identity does not apply. The unit tests assert that on a synthetic frame;
this asserts it on the REAL fleet, through the real
``generators_to_fleet_arrays`` overlay path.

The claim under test is exact and falsifiable: with the flag armed, every
EXCLUDED bin's hourly availability row is **byte-identical** to the unarmed
run's, and at least one non-excluded bin's is not (otherwise the flag would be
inert and the test vacuous).
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.outages import (  # noqa: E402
    _DISPATCHED_DENOM_EXCLUDED_GROUPS,
)
from scripts.lib.bundle_fleet import bundle_gas_price, full_run_year_kwargs  # noqa: E402
from scripts.probes._miso266_repair_ceiling_ab import _leg_meta  # noqa: E402


def _avail_by_bin(bundle: Path, year: int, armed: bool) -> dict[tuple[int, str], np.ndarray]:
    """Capacity-weighted mean availability per ``(plant_code, plant_group)`` bin."""
    from scripts.run_calibration import run_year

    meta = _leg_meta(bundle, year)
    kwargs = full_run_year_kwargs(meta)
    kwargs["unit_outage_dispatched_bin_denominator"] = armed
    state = run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kwargs
    )
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    codes = np.asarray(fa.plant_code)
    groups = np.asarray(fa.plant_group)
    num: dict[tuple[int, str], np.ndarray] = defaultdict(
        lambda: np.zeros(avail.shape[1])
    )
    den: dict[tuple[int, str], float] = defaultdict(float)
    for i in range(len(pmax)):
        c, g = int(codes[i]), str(groups[i])
        if c <= 0 or not g or pmax[i] <= 0:
            continue
        num[(c, g)] += pmax[i] * avail[i]
        den[(c, g)] += pmax[i]
    return {k: num[k] / den[k] for k in num}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--year", type=int, default=2020)
    args = ap.parse_args()

    bundle = REPO / args.bundle
    off = _avail_by_bin(bundle, args.year, False)
    on = _avail_by_bin(bundle, args.year, True)

    moved: dict[str, list] = defaultdict(list)
    same: dict[str, int] = defaultdict(int)
    for key in sorted(set(off) | set(on)):
        a, b = off.get(key), on.get(key)
        if a is None or b is None:
            moved[key[1]].append((key[0], float("nan")))
            continue
        d = float(np.abs(b - a).max())
        if d > 0.0:
            moved[key[1]].append((key[0], d))
        else:
            same[key[1]] += 1

    print(f"=== MISO {args.year} — CHP exclusion, on the REAL fleet (ZERO LP) ===")
    print(f"excluded groups: {sorted(_DISPATCHED_DENOM_EXCLUDED_GROUPS)}")
    print()
    hdr = f"{'group':12} {'bins':>5} {'identical':>10} {'MOVED':>7} {'max |d avail|':>14}  verdict"
    print(hdr)
    print("-" * len(hdr))
    bad = False
    any_moved = False
    for g in sorted(set(same) | set(moved)):
        mv = moved.get(g, [])
        n = same.get(g, 0) + len(mv)
        mx = max((d for _c, d in mv), default=0.0)
        excluded = g in _DISPATCHED_DENOM_EXCLUDED_GROUPS
        if excluded:
            ok = not mv
            verdict = "EXCLUDED, identical" if ok else "EXCLUDED but MOVED — FAIL"
            bad |= bool(mv)
        else:
            verdict = "in scope"
            any_moved |= bool(mv)
        print(f"{g:12} {n:5d} {same.get(g, 0):10d} {len(mv):7d} {mx:14.6f}  {verdict}")
    print()
    if bad:
        print("VERDICT: FAIL — an excluded CHP bin's availability moved.")
        return 1
    if not any_moved:
        print("VERDICT: VACUOUS — no in-scope bin moved either; the test proves nothing.")
        return 1
    print("VERDICT: PASS — every excluded CHP bin is byte-identical, and in-scope")
    print("  bins do move, so the exclusion is real and the check is not vacuous.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
