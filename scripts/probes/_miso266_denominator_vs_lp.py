"""miso-266 — is the derate DENOMINATOR the capacity the LP applies it to?

:func:`market_sim.data.outages._iso_plant_capacity`'s own docstring states the
invariant this probe tests:

    "this denominator has to be THE SAME capacity the derate multiplier is
    applied to in the LP ... reading the denominator off an un-armed fleet
    while the LP holds an armed one would remove the wrong absolute MW"

It states it about a FLAG (``cc_steam_part_reclass``). The same invariant binds
in the VINTAGE / RETIREMENT dimension, and nothing checks it: the denominator is
built once from ``active_eia860_dir()`` + ``load_retired_within_window`` with no
knowledge of the solve year's own fleet, while the LP's ``pmax`` for that year is
built by the year's own fleet path (``vintage_capacity_ramp``, the retired-within
-window injection, the tranche split).

This probe puts the two side by side, per coal bin, per year, off the KEEPER's
own reconstructed fleet -- zero LP. ``ratio = cap_denominator / cap_LP``. A bin
where the ratio is below 1 removes MORE MW than went out; at ``ratio < 1 / (share
of the plant actually flagged)`` it zeroes a plant that is only partly out.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.outages import _iso_plant_capacity  # noqa: E402
from scripts.lib.bundle_fleet import bundle_gas_price, full_run_year_kwargs  # noqa: E402
from scripts.probes._miso266_repair_ceiling_ab import _leg_meta  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--years", type=int, nargs="+", default=[2020])
    ap.add_argument("--group", default="COAL")
    args = ap.parse_args()

    bundle = REPO / args.bundle
    denom = _iso_plant_capacity(args.iso, False, False)

    for year in args.years:
        # Each year's OWN partition leg (RESULT-miso263 §3), so 2023-2025
        # measure the fleet the keeper actually solved.
        meta = _leg_meta(bundle, year)
        from scripts.run_calibration import run_year

        state = run_year(
            year,
            meta["iso"],
            int(meta["hours"]),
            bundle_gas_price(meta, year),
            **full_run_year_kwargs(meta),
        )
        fa = state["fleet_arrays"]
        pmax = np.asarray(fa.pmax, dtype=float)
        codes = np.asarray(fa.plant_code)
        groups = np.asarray(fa.plant_group)
        lp_cap: dict[tuple[int, str], float] = defaultdict(float)
        for i in range(len(pmax)):
            g = str(groups[i])
            if g != args.group:
                continue
            lp_cap[(int(codes[i]), g)] += float(pmax[i])

        rows = []
        for k, lp in sorted(lp_cap.items()):
            d = denom.get(k)
            if d is None or lp <= 0:
                rows.append((k[0], lp, float("nan"), float("nan")))
                continue
            rows.append((k[0], lp, d, d / lp))
        rows.sort(key=lambda r: (r[3] if r[3] == r[3] else 9e9))

        mism = [r for r in rows if r[3] == r[3] and abs(r[3] - 1.0) > 0.02]
        print(f"=== {args.iso} {year} — derate DENOMINATOR vs the LP's OWN {args.group} bin capacity ===")
        print(f"{args.group} bins in the LP fleet: {len(rows)}   |ratio-1| > 2 %: {len(mism)}")
        print()
        hdr = f"{'plant':>6} {'LP MW':>9} {'denom MW':>9} {'denom/LP':>9}"
        print(hdr)
        print("-" * len(hdr))
        for code, lp, d, r in rows[:16]:
            print(f"{code:6d} {lp:9.1f} {d:9.1f} {r:9.3f}")
        print("   ...")
        for code, lp, d, r in rows[-4:]:
            print(f"{code:6d} {lp:9.1f} {d:9.1f} {r:9.3f}")
        tot_lp = sum(r[1] for r in rows if r[3] == r[3])
        tot_d = sum(r[2] for r in rows if r[3] == r[3])
        print()
        print(f"  fleet totals: LP {tot_lp:,.1f} MW   denominator {tot_d:,.1f} MW   ratio {tot_d / tot_lp:.4f}")
        print(f"  bins where the denominator is BELOW the LP by >2 %: "
              f"{sum(1 for r in rows if r[3] == r[3] and r[3] < 0.98)}")
        print(f"  bins where it is ABOVE by >2 %                    : "
              f"{sum(1 for r in rows if r[3] == r[3] and r[3] > 1.02)}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
