"""miso-265 — the hour-grain form: hours where the LP's own coal ceiling is BELOW the meter.

The annual form (:mod:`scripts.probes._miso265_coal_availability_ceiling`) shows
that seven MISO COAL_BIT plants carry an annual ``pmax * availability`` ceiling
below their own measured 2020 output. That is already an internal contradiction
between two measured inputs, but the annual form can in principle be produced by
a timing mismatch (the ceiling in the right hours, the meter in others).

This script removes that escape. For each plant it compares, **hour by hour**,
the LP's own upper bound against the CAMPD metered output the benchmark carries::

    ceiling[t] = sum_{g in plant} pmax[g] * availability[g, t]      (MW)
    meter[t]   = the bench's committed CAMPD series for that plant  (MW)

and reports the hours where ``meter[t] > ceiling[t]`` and the energy in them.
An hour in that set is one the solved dispatch could not have reproduced at any
price, under any offer curve, with any commitment rule — so it is not a
calibration residual, it is an infeasible input pair.

BASIS DISCIPLINE. The bench's plant series is ``_b64(100 * mw / cap)`` — a uint8
percent-of-``cap`` series, where ``cap`` is the same per-plant capacity the bench
records as ``npl``. The decode is therefore ``cf/100 * npl`` MW, and this script
VERIFIES it per plant against the independently recorded ``c_ann`` before using
it, skipping any plant whose reconstruction does not reproduce its own annual to
0.5 %. Clipped series (a split-plant row whose ``cap`` is a rounded 1 MW) fail
that check and are skipped rather than silently read, which is the crossed-basis
error the MISO log records at the ``apply_other_fossil_scoring`` correction.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402
from scripts.probes._miso265_coal_availability_ceiling import (  # noqa: E402
    COAL_CLASSES,
    _assert_partition_leg,
    load_bench,
)

#: Reconstruction tolerance: |rebuilt annual / recorded annual - 1|.
_DECODE_TOL = 0.005


def decode_plant_mw(rec: dict, key: str) -> np.ndarray | None:
    """Return the bench plant's CAMPD hourly MW, or ``None`` if unverifiable."""
    blob, cap = rec.get("campd"), float(rec.get("npl") or 0.0)
    ann = float(rec.get("c_ann") or 0.0)
    if not blob or cap <= 0 or ann <= 0:
        return None
    cf = np.frombuffer(base64.b64decode(blob), dtype=np.uint8).astype(float)
    mw = cf / 100.0 * cap
    if abs(mw.sum() / 1e6 / ann - 1.0) > _DECODE_TOL:
        return None
    return mw


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument(
        "--tol-steps",
        type=float,
        default=1.0,
        help="Breach tolerance in uint8 decode quantization steps (one step = cap/100 MW).",
    )
    args = ap.parse_args()

    bundle = REPO / args.bundle
    meta = json.loads((bundle / "meta.json").read_text())
    _assert_partition_leg(meta, args.year)
    state, _ = reconstruct_bundle_fleet(bundle, args.year, verbose=False)
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    codes = np.asarray(fa.plant_code)

    from market_sim.data.fleet import FUEL_TYPE_MAP

    is_coal = np.asarray(fa.fuel_type_idx) == FUEL_TYPE_MAP["coal"]
    # Per-plant hourly LP ceiling, summed over that plant's coal rows.
    ceiling: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(avail.shape[1]))
    for i in np.nonzero(is_coal)[0]:
        ceiling[str(codes[i])] += pmax[i] * avail[i]

    bench = load_bench(args.iso, args.year)
    rows, skipped = [], []
    for key, rec in bench["plants"].items():
        if rec.get("group") not in COAL_CLASSES:
            continue
        base = key.split(":")[0]
        if base not in ceiling:
            continue
        meter = decode_plant_mw(rec, key)
        if meter is None:
            skipped.append((key, rec.get("name", "?")))
            continue
        c = ceiling[base]
        n = min(len(c), len(meter))
        c, meter = c[:n], meter[:n]
        # The meter series is uint8 percent-of-cap, so its per-hour decode error is
        # up to half a step (cap/200 MW). A breach smaller than a full step is codec
        # noise: the SELF-CHECK companion measures the keeper's OWN dispatch against
        # the same ceiling and finds apparent breaches of exactly this size, which is
        # what sets the threshold — it is a measured codec property, not a chosen
        # tolerance, and it is applied in the direction that SHRINKS the finding.
        tol = args.tol_steps * float(rec.get("npl") or 0.0) / 100.0
        over = meter > c + tol
        rows.append(
            {
                "key": key,
                "name": rec.get("name", "?"),
                "group": rec.get("group"),
                "hours": int(over.sum()),
                "twh": float((meter[over] - c[over]).sum()) / 1e6,
                "meter_twh": float(meter.sum()) / 1e6,
                "ceil_twh": float(c.sum()) / 1e6,
                "worst_mw": float((meter - c).max()),
                "step_mw": tol,
            }
        )
    rows.sort(key=lambda r: -r["twh"])

    print(f"=== {args.iso} {args.year} — HOURS WHERE THE METER EXCEEDS THE LP'S OWN CEILING ===")
    print(f"bundle: {args.bundle}  |  {len(rows)} coal plants verified, {len(skipped)} skipped (unverifiable decode)")
    print()
    hdr = (
        f"{'key':>13} {'plant':26} {'class':13} {'over_h':>7} {'over_TWh':>9} "
        f"{'meter':>8} {'ceiling':>8} {'worstMW':>8}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows[: args.top]:
        print(
            f"{r['key']:>13} {r['name'][:26]:26} {r['group']:13} {r['hours']:7d} "
            f"{r['twh']:9.3f} {r['meter_twh']:8.3f} {r['ceil_twh']:8.3f} {r['worst_mw']:8.0f}"
        )
    tot = sum(r["twh"] for r in rows)
    nz = [r for r in rows if r["twh"] > 1e-6]
    print()
    print(
        f"TOTAL infeasible energy (meter above the LP's own ceiling): {tot:.3f} TWh "
        f"across {len(nz)} plants and {sum(r['hours'] for r in rows):,} plant-hours"
    )
    by_class: dict[str, float] = defaultdict(float)
    for r in rows:
        by_class[r["group"]] += r["twh"]
    for k, v in sorted(by_class.items(), key=lambda x: -x[1]):
        print(f"   {k:14} {v:7.3f} TWh")
    if skipped:
        print()
        print(f"skipped (decode not verifiable — clipped/rounded cap): {len(skipped)}")
        for key, name in skipped[:10]:
            print(f"   {key:>13} {name[:34]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
