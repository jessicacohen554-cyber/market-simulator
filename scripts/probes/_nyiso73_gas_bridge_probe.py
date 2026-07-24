"""NYISO-73 rule-16 throwaway: route the ISO-neutral gas commitment bridge onto NYISO.

The two 2026-07-23 NYISO findings concluded that the dominant open miss — the
2023 C3a OFF-PEAK trough (+53-59%, model floors overnight LBMP at ~$29-31 where
the real market troughs to ~$19.6) — has one structurally-honest forward lever:
a below-SRMC overnight commitment mechanism (committed thermal held online at
min-load through the trough rather than cycling off), which they framed as an
UNBUILT cross-ISO price-formation methodology change.

That mechanism EXISTS. ERCOT-63 built ``ercot_gas_commitment_bridge`` (diagnosis
docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md §7): the CAISO RA
must-offer bridge internals (``model.commitment.caiso_ra_mustoffer_min_gen`` —
min-down + startup-restart economics detected from the model's OWN P0 run
pattern, physics-gated per rule 18, forward-native) scoped to the merchant
gas-CC fleet, with ``min_load_frac`` = the MEASURED committed-CC LSL/HSL
capacity-weighted p50. The detector body ``_ercot_gas_bridge_floor`` is
ISO-neutral; only the two wrapper gates pin ERCOT. On ERCOT the STATE bridge
closed the trough LEVEL (C3a +3.9% -> +0.3%) and DEEPENED the trough while
improving evening battery discharge.

This probe tests whether that same STATE mechanism helps NYISO's C3a off-peak
trough, with ZERO new repo mechanisms, by routing the ISO-neutral bridge onto
the NYISO gas-CC fleet via a monkeypatch of
``scripts.run_calibration.build_ercot_gas_bridge_p1_preps``.

Structural priors (both directions, resolved by the floored-volume + price A/B):
  * FOR: NYISO's off-peak marginal IS CC_REGULAR (gas_cc) — the exact class the
    bridge lands on; NYISO's EVENING marginal is a different tranche
    (CT_PEAKER/hydro), so the ERCOT spread-compression failure mode (the
    committed tranche playing both LSL and evening-marginal roles) is
    structurally weaker here.
  * AGAINST: NYISO CCs are baseload-duty (median CF 79-86%; class daily min/max
    ratio p50 0.81), so few units cycle FULLY OFF overnight -> the bridge's
    idle-gap detector may floor little; and the off-peak marginal stays a
    high-$20s CC regardless of added must-take volume, so the trough may not
    reach reality's $19.6.

min_load_frac = 0.574 is the ERCOT-MEASURED committed-CC LSL/HSL p50, used here
as a physical CC min-stable proxy for the APPLICABILITY test only (the floored
VOLUME the detector finds is ~independent of the exact fraction — it depends on
the P0 idle-gap pattern, not the floor level). A real NYISO keeper would require
a NYISO-measured min-stable derive (NYISO DAM disclosure is masked; the analogue
is a NYISO-CAMPD CC sustained-min/max p50). EXPLICITLY-LABELLED DIAGNOSTIC (rules
13/16): never registered, never a keeper config. The real mechanism (a NYISO
gate + its own D-2/D-4 declarations + a NYISO-measured min_load_frac) is built
only if this probe closes the trough without wrecking C1/C7/spread.

Usage::

    python scripts/probes/_nyiso73_gas_bridge_probe.py [OUT_NAME] [--years 2023]
        [--min-load-frac 0.574]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

# Byte-faithful replay pin (mirror replay_keeper): cross-year warm-start OFF.
os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"

import numpy as np  # noqa: E402

import scripts.run_calibration as rc  # noqa: E402  (patch the PACKAGE module)
import run_calibration_full as rcf  # noqa: E402
from replay_keeper import build_kwargs  # noqa: E402

from market_sim.data.floor_mechanisms import MECH_GAS_COMMITMENT_BRIDGE  # noqa: E402
from market_sim.pipeline.commitment import (  # noqa: E402
    _bridge_floored_fleet,
    _ercot_gas_bridge_floor,
)

ROOT = REPO / "results" / "calibration"
KEEPER = ROOT / "nyiso72_netrev_margin"

_orig_preps = rc.build_ercot_gas_bridge_p1_preps


def _make_nyiso_preps(min_load_frac: float):
    """Return a drop-in for build_ercot_gas_bridge_p1_preps that fires on NYISO."""

    def _nyiso_preps(config, iso, fleet, fleet_arrays, mc_base, floorscoped_markdown_fn=None):
        if iso != "NYISO":
            return _orig_preps(
                config, iso, fleet, fleet_arrays, mc_base, floorscoped_markdown_fn
            )
        # Route the ISO-neutral detector onto NYISO gas-CC. Same construction as
        # the ERCOT gate: economic (>=min-down) startup-restart bridging on the
        # model's own P0 duals, bounded to one DA operating day.
        cfg = config.with_overrides(
            ercot_gas_bridge_min_load_frac=float(min_load_frac),
            ercot_gas_bridge_startup=True,
            ercot_gas_bridge_da_horizon=True,
        )
        memo: dict = {"key": None, "floor": None}

        def _floor_for(r0):
            key = id(r0)
            if memo["key"] != key:
                memo["key"] = key
                memo["floor"] = _ercot_gas_bridge_floor(
                    cfg, fleet, fleet_arrays, r0.dispatch, r0.prices, mc_base
                )
            return memo["floor"]

        def _fleet_prep(r0):
            floor = _floor_for(r0)
            if floor is None:
                print("[nyiso73-bridge] bridge floored NOTHING (no idle gaps on gas_cc)", flush=True)
                return None
            n = int((floor > 0.0).sum())
            twh = float(floor.sum()) / 1e6
            print(f"[nyiso73-bridge] floored unit-hours {n}, floor volume {twh:.3f} TWh", flush=True)
            return _bridge_floored_fleet(fleet_arrays, floor, MECH_GAS_COMMITMENT_BRIDGE)

        return _fleet_prep, None

    return _nyiso_preps


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_name", nargs="?", default="nyiso73_gas_bridge_2023")
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    ap.add_argument("--min-load-frac", type=float, default=0.574)
    args = ap.parse_args()

    rc.build_ercot_gas_bridge_p1_preps = _make_nyiso_preps(args.min_load_frac)

    meta = json.loads((KEEPER / "meta.json").read_text())
    out = ROOT / args.out_name
    out.mkdir(parents=True, exist_ok=True)

    # Mirror replay_keeper: everything rides kwargs (commitment/screen_coal come
    # from build_kwargs), including years/iso/hours/reference/run_dir.
    kwargs = build_kwargs(meta)
    kwargs["years"] = [int(y) for y in args.years]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = out
    kwargs["note"] = (
        "nyiso73 rule-16 throwaway (NEVER register): ISO-neutral gas commitment "
        "bridge (ERCOT-63 internals) routed onto NYISO gas-CC via monkeypatch, "
        f"min_load_frac {args.min_load_frac} (ERCOT-measured LSL/HSL p50, "
        "physical proxy). Tests whether the committed-STATE mechanism closes the "
        "2023 C3a off-peak trough on NYISO's baseload CC fleet."
    )

    rcf.solve_and_persist(**kwargs)
    print(f"DONE -> {out}")


if __name__ == "__main__":
    main()
