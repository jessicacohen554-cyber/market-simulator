"""miso-265 — the sharpest form: hours the model says a coal plant is 100 % OUT and the meter says it ran.

The hour-grain ceiling probe measures ``meter > pmax * availability``. This one
isolates the unambiguous subset of that set, the one that needs no theory at all
about merit order, offers or commitment:

    availability[plant, t] == 0   AND   meter[plant, t] > 0

In such an hour the model asserts the plant is **entirely unavailable** while the
plant's own metered record says it was generating. There is no reading of the LP
under which that hour is reproducible, and no offer curve or price that changes
it.

WHY THIS SET EXISTS. ``unit_outage_derate_factors`` derates a plant by
``unit_capacity_mw / plant_capacity_mw`` per outage window and sums CONCURRENT
units, "clipped at full derate". So a plant whose units carry overlapping
detected windows summing past 1.0 is zeroed outright — and the detector's windows
are sustained-low-output windows, which for a cycling unit include the hours it
was merely idle. The clip converts several partial, individually plausible unit
derates into a whole-plant outage the meter contradicts.

The companion :mod:`scripts.probes._miso265_ceiling_vs_meter_hourly` carries the
full (and larger) contradiction; this script reports the part of it that cannot
be argued about.
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

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402
from scripts.probes._miso265_ceiling_vs_meter_hourly import decode_plant_mw  # noqa: E402
from scripts.probes._miso265_coal_availability_ceiling import (  # noqa: E402
    COAL_CLASSES,
    _assert_partition_leg,
    load_bench,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument(
        "--zero-tol",
        type=float,
        default=1e-9,
        help="availability at or below this counts as a hard zero",
    )
    args = ap.parse_args()

    bundle = REPO / args.bundle
    _assert_partition_leg(json.loads((bundle / "meta.json").read_text()), args.year)
    state, _ = reconstruct_bundle_fleet(bundle, args.year, verbose=False)
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    codes = np.asarray(fa.plant_code)

    from market_sim.data.fleet import FUEL_TYPE_MAP

    is_coal = np.asarray(fa.fuel_type_idx) == FUEL_TYPE_MAP["coal"]
    ceiling: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(avail.shape[1]))
    cap: dict[str, float] = defaultdict(float)
    for i in np.nonzero(is_coal)[0]:
        ceiling[str(codes[i])] += pmax[i] * avail[i]
        cap[str(codes[i])] += pmax[i]

    bench = load_bench(args.iso, args.year)
    rows = []
    for key, rec in bench["plants"].items():
        if rec.get("group") not in COAL_CLASSES:
            continue
        base = key.split(":")[0]
        if base not in ceiling:
            continue
        meter = decode_plant_mw(rec, key)
        if meter is None:
            continue
        c = ceiling[base]
        n = min(len(c), len(meter))
        c, meter = c[:n], meter[:n]
        # A hard zero on the PLANT's ceiling: every one of its coal rows is out.
        # The meter threshold is one decode step, so a single quantization tick
        # above zero is never counted as generation.
        step = float(rec.get("npl") or 0.0) / 100.0
        hard = (c <= args.zero_tol) & (meter > step)
        rows.append(
            {
                "key": key,
                "name": rec.get("name", "?"),
                "group": rec.get("group"),
                "zero_h": int((c <= args.zero_tol).sum()),
                "hours": int(hard.sum()),
                "twh": float(meter[hard].sum()) / 1e6,
                "peak_mw": float(meter[hard].max()) if hard.any() else 0.0,
                "lp_mw": cap[base],
            }
        )
    rows.sort(key=lambda r: -r["twh"])

    print(f"=== {args.iso} {args.year} — HOURS THE MODEL CALLS THE PLANT 100% OUT AND THE METER DISAGREES ===")
    print(f"bundle: {args.bundle}")
    print()
    hdr = (
        f"{'key':>13} {'plant':26} {'class':13} {'LP MW':>8} {'avail=0 h':>10} "
        f"{'contra h':>9} {'TWh':>8} {'peak MW':>8}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows[: args.top]:
        if r["hours"] == 0:
            continue
        print(
            f"{r['key']:>13} {r['name'][:26]:26} {r['group']:13} {r['lp_mw']:8.0f} "
            f"{r['zero_h']:10d} {r['hours']:9d} {r['twh']:8.3f} {r['peak_mw']:8.0f}"
        )
    nz = [r for r in rows if r["hours"] > 0]
    print()
    print(
        f"TOTAL: {sum(r['twh'] for r in rows):.3f} TWh metered in "
        f"{sum(r['hours'] for r in rows):,} plant-hours the model calls FULLY UNAVAILABLE, "
        f"across {len(nz)} plants"
    )
    tot_zero = sum(r["zero_h"] for r in rows)
    print(
        f"  plant-hours at availability == 0 in total: {tot_zero:,} "
        f"({100.0 * sum(r['hours'] for r in rows) / max(tot_zero, 1):.1f}% of them contradicted by the meter)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
