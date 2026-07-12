"""ERCOT-62 low-curve runner: the ercot56-nucwin keeper reconstructed from its
meta.json + ONE delta, ``ercot_offer_surface_lowcurve``.

The G-22 conditional-offer-distribution LOW leg
(docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md §3-4): the measured
lower-tail offer quantile ladders (committed Min-Gen-Cost LSL block +
lower-body econ segments, 60-Day DAM disclosure, committed resources only)
posted onto the gas committed/econ rungs as a P1-only markdown per net-load
bin, ratio clamped <= 1 — the trough-price-formation mirror of the ADOPTED
``ercot_offer_surface_conditional`` top leg (same corpus, same bins, same
P1-only seam). Zero new fitted parameters (rules 13/20/21); the only new
config is the ON/OFF gate + the frozen-JSON path.

A rule-16 2023-only probe pair (never registered) validated the mechanism
before this full-span run — see the ERCOT-62 calibration-log entry.

Usage::

    python scripts/probes/_ercot62_ab.py OUT_NAME \
        [--years 2023 2024 2025] [--ablation --ablation-of NAME]
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ercot61_stgas_drag_probe import build_kwargs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot56_nucwin"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_name", help="bundle name under results/calibration/")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--ablation-of", default=None, help="bundle name of the main run")
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    # The ONE delta vs the promoted keeper: the conditional-offer-distribution
    # LOW leg (measured trough-side quantile ladders, P1-only markdown).
    kwargs["ercot_offer_surface_lowcurve"] = True

    kwargs["zero_forcing_ablation"] = args.ablation
    kwargs["ablation_of"] = args.ablation_of if args.ablation else None
    kwargs["note"] = (
        "ercot62 lowcurve: ercot56_nucwin keeper config reconstructed from "
        "meta.json + ercot_offer_surface_lowcurve=True (the G-22 conditional-"
        "offer-distribution LOW leg, docs/DIAGNOSIS-ercot-trough-price-"
        "formation-2026-07.md): the measured committed-fleet lower-tail offer "
        "quantile ladders (LSL Min-Gen-Cost block + lower-body econ segments, "
        "60-Day DAM disclosure, committed resources only) as a P1-only markdown "
        "on the gas committed/econ rungs per net-load bin, ratio clamped <= 1 — "
        "the mirror of the adopted top-of-curve surface. Restores the measured "
        "sub-$15 trough epochs the all-hours-p50 band collapse deleted; the "
        "daily spread widens from below and battery arbitrage responds "
        "endogenously (the ERCOT-58 §4 / ERCOT-60 §7 storage/price-formation "
        "circle). Zero new fitted parameters."
    )

    out = ROOT / args.out_name
    out.mkdir(parents=True, exist_ok=True)
    solve_and_persist(
        args.years,
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        run_dir=out,
        **kwargs,
    )
    print(f"DONE ablation={args.ablation} -> {out}")


if __name__ == "__main__":
    main()
