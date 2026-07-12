"""ERCOT-62 rule-16 throwaway: the ercot56-nucwin keeper reconstructed from its
meta.json + the G-22 conditional-offer-distribution LOW leg
(``ercot_offer_surface_lowcurve``) as the SINGLE delta, solved for one year.

The lane (ERCOT-58 §4 -> ERCOT-60 §7 -> ERCOT-61 §5): the model's daily price
spread is missing from the BOTTOM — the measured 2023 market spent ~1,500 h
below $15 where the model floors at its all-hours-p50 gas bands (~$19-23) —
and that flat spread is what starves battery arbitrage at binding hours (the
storage/price-formation circle). The low leg restores the measured lower-tail
offer distribution (committed LSL block + lower-body econ segments, committed
resources only) per net-load bin, P1-only, ratio clamped <= 1.

NEVER registered (CLAUDE.md rule 16 — single-year diagnostic probe). Analysis:
``scripts/probes/_ercot62_lowcurve_analyze.py``.

Usage::

    python scripts/probes/_ercot62_lowcurve_probe.py [OUT_NAME] [--years 2023]
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

from _ercot61_stgas_drag_probe import build_kwargs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot56_nucwin"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_name", nargs="?", default="ercot62_lowcurve_2023")
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    kwargs["ercot_offer_surface_lowcurve"] = True
    kwargs["note"] = (
        "ercot62 rule-16 throwaway (NEVER register): ercot56_nucwin keeper "
        "config reconstructed from meta.json + ercot_offer_surface_lowcurve "
        "(the G-22 conditional-offer-distribution LOW leg, measured trough-side "
        "quantile ladders, P1-only markdown) as the single delta — the "
        "storage/price-formation circle probe (ERCOT-58 §4 / ERCOT-60 §7)."
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
    print(f"DONE -> {out}")


if __name__ == "__main__":
    main()
