"""miso-265 — VALIDATE the ceiling formula against the keeper's own dispatch.

:mod:`scripts.probes._miso265_ceiling_vs_meter_hourly` claims that
``sum_g pmax[g] * availability[g, t]`` is the LP's hard hourly upper bound on a
plant. That claim carries the whole finding, so it is checked rather than
asserted, and the check is the strongest one available: **the keeper's own
solved dispatch must never exceed it.**

If the model's committed per-plant hourly MW is <= the reconstructed ceiling in
every hour of every plant, the formula is a valid upper bound on this LP and the
meter-above-ceiling hours are genuine infeasibilities. If the model's own
dispatch breaches it, the formula is wrong — ``pmax`` already carries a derate,
or availability is applied elsewhere — and the finding must be withdrawn.

The model series is the registered payload's per-plant ``m`` (``_b64``: uint8
percent of the bench's ``npl``), verified per plant against its own recorded
``m_ann`` before use, exactly as the meter series is.
"""

from __future__ import annotations

import argparse
import base64
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
from scripts.probes._miso265_coal_bit_2020_phase0 import load_payload  # noqa: E402

_DECODE_TOL = 0.005


def _decode(blob: str, cap: float, ann: float) -> np.ndarray | None:
    """Decode a ``_b64`` percent-of-``cap`` series to MW, verified against ``ann``."""
    if not blob or cap <= 0 or ann <= 0:
        return None
    mw = np.frombuffer(base64.b64decode(blob), dtype=np.uint8).astype(float) / 100.0 * cap
    return mw if abs(mw.sum() / 1e6 / ann - 1.0) <= _DECODE_TOL else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--run", default="2026-09-20-miso-264-anchor-vintage")
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument(
        "--tol-steps",
        type=float,
        default=1.0,
        help=(
            "Breach tolerance in DECODE QUANTIZATION STEPS. The payload series is "
            "uint8 percent-of-cap, so one step is cap/100 MW and the per-hour decode "
            "error is up to half a step; a 'breach' smaller than that is codec noise, "
            "not an LP fact."
        ),
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
    for i in np.nonzero(is_coal)[0]:
        ceiling[str(codes[i])] += pmax[i] * avail[i]

    bench = load_bench(args.iso, args.year)
    payload = load_payload(args.run)["years"][str(args.year)]["plants"]

    checked = breached = 0
    worst = []
    for key, rec in bench["plants"].items():
        if rec.get("group") not in COAL_CLASSES:
            continue
        base = key.split(":")[0]
        p = payload.get(key) or {}
        mod = _decode(p.get("m", ""), float(rec.get("npl") or 0), float(p.get("m_ann") or 0))
        if mod is None or base not in ceiling:
            continue
        c = ceiling[base]
        n = min(len(c), len(mod))
        exc = mod[:n] - c[:n]
        checked += 1
        tol = args.tol_steps * float(rec.get("npl") or 0) / 100.0
        nb = int((exc > tol).sum())
        if nb:
            breached += 1
        worst.append((float(exc.max()), nb, tol, key, rec.get("name", "?")))
    worst.sort(reverse=True)

    print(f"=== {args.iso} {args.year} — CEILING SELF-CHECK against the keeper's OWN dispatch ===")
    print(
        f"coal plants checked: {checked}   plants breaching by > {args.tol_steps:g} "
        f"decode step(s): {breached}"
    )
    print()
    print(f"{'worst MW over':>14} {'1 step MW':>10} {'hours':>7}  plant")
    print("-" * 64)
    for mx, nb, tol, key, name in worst[:10]:
        print(f"{mx:14.2f} {tol:10.2f} {nb:7d}  {key} {name[:28]}")
    print()
    if breached == 0:
        print("VERDICT: PASS — the model's own dispatch never exceeds pmax * availability.")
        print("  The formula is a valid hard upper bound on this LP, so a METER above it")
        print("  is an infeasible input pair, not a dispatch residual.")
    else:
        print("VERDICT: FAIL — the ceiling formula is NOT an upper bound on this LP.")
        print("  The meter-above-ceiling finding must be WITHDRAWN until the basis is fixed.")
    return 0 if breached == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
