"""miso-266 — restrict the blast radius to bins that actually CARRY outage rows.

``_miso266_denominator_blast_radius.py`` shows large ``denom / cap_LP`` ratios at
the CHP groups (medians ~3.3, maxima 7.8-10.0) and at the hydro bins. A ratio is
only load-bearing where the overlay has rows to route into that bin, so this
probe intersects the two: per plant group, the bins that carry at least one
routed extract row from the layers the MISO keeper ARMS, and the ratio
distribution over THOSE bins alone.

The layer scopes differ and the difference is the point:

* std >= 5-day / short / partial / lay-up route through
  ``_generic_unit_outage_target``, which EXCLUDES ``CT_PEAKER`` and ``CT_CHP``;
* ``unit_outage_maxgen_derate_factors`` is CLASS-AGNOSTIC by design, so it is
  the only layer that can reach a CT bin.

Reported per group and per layer: routed bins, their LP GW, and how many carry a
ratio below 0.98 (OVER-remove today) or above 1.02 (UNDER-remove today).
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
    _generic_unit_outage_target,
    _iso_plant_capacity,
    _load_unit_outage_events,
    unit_outage_csv_for_iso,
    unit_outage_maxgen_csv_for_iso,
    unit_layup_csv_for_iso,
)
from scripts.lib.bundle_fleet import bundle_gas_price, full_run_year_kwargs  # noqa: E402
from scripts.probes._miso266_repair_ceiling_ab import _leg_meta  # noqa: E402


def _std_targets(path: Path, short: bool) -> set[tuple[int, str]]:
    df = _load_unit_outage_events(path, "MISO")
    if df is None:
        return set()
    df = df[df["duration_days"] < UNIT_OUTAGE_MIN_DAYS] if short else df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    out = set()
    for r in df.itertuples(index=False):
        t = _generic_unit_outage_target(int(r.facility_id), r.unit_id, r.plant_group)
        if t is not None:
            out.add(t)
    return out


def _maxgen_targets(path: Path) -> set[tuple[int, str]]:
    if not path.exists():
        return set()
    df = pd.read_csv(path)
    out = set()
    for r in df.itertuples(index=False):
        g = "" if r.plant_group is None or (isinstance(r.plant_group, float) and np.isnan(r.plant_group)) else str(r.plant_group)
        if not g or g == "OTHER":
            continue
        out.add((int(r.facility_id), g))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--year", type=int, default=2020)
    args = ap.parse_args()

    bundle = REPO / args.bundle
    denom = _iso_plant_capacity(args.iso, False, False)
    from scripts.run_calibration import run_year

    meta = _leg_meta(bundle, args.year)
    state = run_year(
        args.year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, args.year),
        **full_run_year_kwargs(meta),
    )
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    codes = np.asarray(fa.plant_code)
    groups = np.asarray(fa.plant_group)
    lp: dict[tuple[int, str], float] = defaultdict(float)
    for i in range(len(pmax)):
        c, g = int(codes[i]), str(groups[i])
        if c > 0 and g:
            lp[(c, g)] += float(pmax[i])

    # The MISO keeper's armed layers, each with the extract it reads.
    std_csv = unit_outage_csv_for_iso(args.iso, True, False, False, False)
    layers = {
        "std >=5d": _std_targets(std_csv, short=False),
        "short <5d": _std_targets(std_csv.with_name(f"campd-unit-outages-short-{args.iso}.csv"), short=True),
        "lay-up": _std_targets(unit_layup_csv_for_iso(args.iso), short=False),
        "maxgen": _maxgen_targets(unit_outage_maxgen_csv_for_iso(args.iso, True)),
    }
    union: set[tuple[int, str]] = set().union(*layers.values())

    print(f"=== {args.iso} {args.year} — ratio distribution over bins that CARRY routed rows ===")
    for name, tgts in list(layers.items()) + [("ALL ARMED LAYERS", union)]:
        rows = defaultdict(list)
        for key in sorted(tgts):
            if key not in lp:
                continue  # routed, but the LP does not dispatch that bin
            d = denom.get(key)
            rows[key[1]].append((key[0], lp[key], d))
        print(f"\n-- {name} --")
        hdr = f"{'group':12} {'bins':>5} {'LP GW':>7} {'missing':>8} {'<0.98':>6} {'>1.02':>6} {'min':>6} {'p50':>6} {'max':>7}"
        print(hdr)
        print("-" * len(hdr))
        if not rows:
            print("  (no routed bins)")
            continue
        for g in sorted(rows):
            rs = rows[g]
            ratios = [d / mw for _c, mw, d in rs if d is not None and mw > 0]
            missing = sum(1 for _c, _mw, d in rs if d is None)
            if not ratios:
                ratios = [float("nan")]
            print(
                f"{g:12} {len(rs):5d} {sum(r[1] for r in rs) / 1000:7.2f} {missing:8d} "
                f"{sum(1 for r in ratios if r < 0.98):6d} {sum(1 for r in ratios if r > 1.02):6d} "
                f"{min(ratios):6.3f} {float(np.median(ratios)):6.3f} {max(ratios):7.3f}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
