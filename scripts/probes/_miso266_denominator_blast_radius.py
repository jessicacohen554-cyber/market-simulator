"""miso-266 — the DISPATCHED-bin denominator's blast radius over EVERY model bin.

``scripts/probes/_miso266_denominator_vs_lp.py`` answers the question for one
plant group. ``ScenarioConfig.unit_outage_dispatched_bin_denominator`` is
fleet-wide, so the blast radius has to be stated for every group the outage
overlay can reach, not only the one the charter is about.

One fleet rebuild per year; the per-group split is free after it. Reported per
group: how many bins the LP dispatches, how many the reconstructed map is
MISSING entirely (those ride un-derated today), and the distribution of
``denom / cap_LP`` — below 1 OVER-removes, above 1 UNDER-removes.
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
    args = ap.parse_args()

    bundle = REPO / args.bundle
    denom = _iso_plant_capacity(args.iso, False, False)

    from scripts.run_calibration import run_year

    for year in args.years:
        meta = _leg_meta(bundle, year)
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
        lp: dict[tuple[int, str], float] = defaultdict(float)
        for i in range(len(pmax)):
            g = str(groups[i])
            c = int(codes[i])
            if c <= 0 or not g:
                continue
            lp[(c, g)] += float(pmax[i])

        by_group: dict[str, list] = defaultdict(list)
        for (code, g), mw in lp.items():
            by_group[g].append((code, mw, denom.get((code, g))))

        print(f"=== {args.iso} {year} — denominator blast radius, EVERY model bin ===")
        hdr = (
            f"{'group':14} {'bins':>5} {'LP GW':>8} {'missing':>8} {'miss GW':>8} "
            f"{'<0.98':>6} {'>1.02':>6} {'min':>6} {'p50':>6} {'max':>7}"
        )
        print(hdr)
        print("-" * len(hdr))
        for g in sorted(by_group):
            rows = by_group[g]
            ratios = [d / mw for _c, mw, d in rows if d is not None and mw > 0]
            missing = [(c, mw) for c, mw, d in rows if d is None]
            if not ratios:
                ratios = [float("nan")]
            print(
                f"{g:14} {len(rows):5d} {sum(r[1] for r in rows) / 1000:8.2f} "
                f"{len(missing):8d} {sum(m[1] for m in missing) / 1000:8.3f} "
                f"{sum(1 for r in ratios if r < 0.98):6d} "
                f"{sum(1 for r in ratios if r > 1.02):6d} "
                f"{min(ratios):6.3f} {float(np.median(ratios)):6.3f} {max(ratios):7.3f}"
            )
        print()
        print("  missing = bins the LP DISPATCHES that the reconstructed map lacks")
        print("            entirely; their measured outage rows are SKIPPED today.")
        print("  <0.98   = bins whose derate OVER-removes;  >1.02 = UNDER-removes.")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
