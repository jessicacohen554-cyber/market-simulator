"""ERCOT-62b rule-16 throwaway: the committed-block INFLEXIBILITY probe.

The v1/v2 low-curve probes measured that repricing the gas committed (LSL)
block moves price LEVELS toward reality but cannot widen the daily SPREAD —
the committed tranche is the model's marginal segment at mild-day evenings
too, so both ends of the day fall together (and offline plants' cheap blocks
shuffle dispatch from coal). The measured structure reality has and the model
lacks is the block's INFLEXIBILITY: LSL energy is must-take while the unit is
on, so its cheap bid never sets the margin — the STATE does the work, not the
price.

This probe tests exactly that composition with ZERO new repo mechanisms, by
spoofing the existing physics-gated commitment bridge (the CAISO RA machinery:
min-down + startup-restart economics from the model's OWN P0 run pattern,
``pipeline.commitment.caiso_ra_p1_floor_fleet`` — ISO-neutral internals, only
the guards pin CAISO) onto the ERCOT gas CC fleet via a monkeypatch:

* keeper (ercot56-nucwin meta) base;
* + ``ercot_offer_surface_lowcurve`` (the measured LSL/lower-body markdown,
  P0-online-gated — v2);
* + the commitment bridge, ``min_load_frac`` = the MEASURED ERCOT committed-CC
  LSL/HSL capacity-weighted p50 = 0.574 (60-Day DAM disclosure, this
  session), startup-aware startup-bridge (the CAISO-adopted variant).

EXPLICITLY-LABELLED DIAGNOSTIC (rule 13/16): never registered, never a keeper
config — the real mechanism (an ERCOT gate + its own D-2/D-4 declarations)
is built only if this composition closes the spread/storage circle.

Usage::

    python scripts/probes/_ercot62b_bridge_probe.py [OUT_NAME] [--years 2023]
        [--no-lowcurve]
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_calibration as rc  # noqa: E402
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ercot61_stgas_drag_probe import build_kwargs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot56_nucwin"

# Measured ERCOT committed-CC LSL/HSL capacity-weighted p50 (this session,
# 60-Day DAM disclosure committed resources 2023-2025).
ERCOT_CC_MIN_LOAD_FRAC = 0.574

_orig_prep = rc.build_caiso_ra_p1_prep


def _spoofed_prep(config, iso, fleet, fleet_arrays, mc_base, **kw):
    """Route ERCOT through the ISO-neutral bridge internals (diagnostic only)."""
    if iso == "ERCOT" and getattr(config, "caiso_ra_mustoffer", False):
        import os

        import numpy as np

        from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER

        # startup-aware run screen: a ScenarioConfig-only field (no
        # solve_and_persist kwarg); ON unless ERCOT62B_NO_STARTUP_AWARE is set
        # (the screen may kill every anchor in the model's flat troughs).
        if not os.environ.get("ERCOT62B_NO_STARTUP_AWARE"):
            config = config.with_overrides(caiso_ra_bridge_startup_aware=True)
        inner = _orig_prep(config, "CAISO", fleet, fleet_arrays, mc_base, **kw)
        if inner is None:
            print("[62b] bridge prep is None (gate)", flush=True)
            return None

        def wrapped(r0):
            out = inner(r0)
            if out is None:
                print("[62b] bridge floored NOTHING", flush=True)
                return None
            n = int((out.min_gen_mechanism == MECH_RA_MUSTOFFER).sum())
            mw = float(np.where(out.min_gen_mechanism == MECH_RA_MUSTOFFER, out.min_gen, 0.0).sum())
            print(f"[62b] bridge floored unit-hours: {n}, TWh {mw/1e6:.2f}", flush=True)
            return out

        return wrapped
    return _orig_prep(config, iso, fleet, fleet_arrays, mc_base, **kw)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_name", nargs="?", default="ercot62b_bridge_2023")
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    ap.add_argument("--no-lowcurve", action="store_true")
    args = ap.parse_args()

    rc.build_caiso_ra_p1_prep = _spoofed_prep  # rule-16 diagnostic monkeypatch

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    kwargs["ercot_offer_surface_lowcurve"] = not args.no_lowcurve
    kwargs["caiso_ra_mustoffer"] = True
    kwargs["caiso_ra_min_load_frac"] = ERCOT_CC_MIN_LOAD_FRAC
    kwargs["caiso_ra_startup_bridge"] = True
    kwargs["note"] = (
        "ercot62b rule-16 throwaway (NEVER register): committed-block "
        "inflexibility probe — keeper base + measured LSL/lower-body markdown "
        f"(lowcurve={not args.no_lowcurve}) + the physics-gated commitment "
        "bridge spoofed onto ERCOT gas CC via monkeypatch (min_load_frac "
        "0.574 = measured committed-CC LSL/HSL p50). Tests whether state "
        "(must-run when on) + price (measured LSL bids) together widen the "
        "daily spread and move battery arbitrage (the ERCOT-58/60 circle) "
        "where price alone was probe-refuted."
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
