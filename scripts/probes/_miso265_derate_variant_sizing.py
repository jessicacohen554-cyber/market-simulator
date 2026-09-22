"""miso-265 — size the candidate repairs for the full-derate zeroing, at ZERO LP.

:mod:`scripts.probes._miso265_hard_zero_hours` establishes that MISO's coal
plants are driven to ``availability == 0`` in hours their own meter says they
ran, and :func:`market_sim.data.outages.unit_outage_derate_factors` is measured
to be the whole driver (its factor alone is 0.0000 for 8,112 h at R M Schahfer).

The accumulator's own docstring names two GATED repairs for exactly this
pathology — a numerator/denominator mismatch that, in its words, can *"sum to
1.23 of the modeled OP half and clip it to 0.0"*:

* ``unit_outage_fleet_status_scope`` — drop non-``OP`` rows before accumulating,
  so a retired/dark unit's capacity is not charged against a denominator that
  already excludes it;
* ``unit_outage_extract_basis_share`` (nyiso-196) — take the removed fraction on
  the extract's OWN capacity basis, so numerator and denominator come from one
  construction.

Neither is reachable from ``run_year``, so neither can be A/B'd through a
bundle reconstruction. They ARE reachable here: the factors are rebuilt directly
for each variant and scored on the SAME fleet and the SAME committed meter, which
is all the sizing needs and costs no LP.

Reported per variant: the plant-hours the factor drives to a hard zero, and how
many of those the meter contradicts. A repair that works shrinks the second
column toward zero.
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

from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402
from scripts.probes._miso265_ceiling_vs_meter_hourly import decode_plant_mw  # noqa: E402
from scripts.probes._miso265_coal_availability_ceiling import (  # noqa: E402
    COAL_CLASSES,
    _assert_partition_leg,
    load_bench,
)

#: The keeper's own outage-overlay posture, read from its per-year
#: ``run_config_<year>.json`` and held fixed in every variant so each row is a
#: SINGLE delta off the incumbent.
#:
#: CORRECTION (miso-266): this dict omitted ``fleet_status_scope=True``, which
#: the MISO keeper's ``run_config_2020.json`` carries, so miso-265's "incumbent"
#: row was one flag off the keeper's real posture. It changes no number here —
#: that session's own ``+fleet_status_scope`` row is byte-identical to its
#: incumbent, which is exactly the measurement saying the flag is inert on this
#: object — but the base is the keeper's, so it is corrected rather than left.
BASE_KWARGS = dict(
    st_capacity_basis=True,
    mixed_gas_routing=True,
    per_unit_clip=True,
    fleet_status_scope=True,
)

#: Variants keyed on a callable when they need the LP fleet itself. A plain dict
#: is passed straight through as kwargs; a callable receives the LP bin roster
#: (:func:`market_sim.data.outages.lp_bin_capacity_index`) and returns kwargs.
VARIANTS: dict[str, dict | object] = {
    "incumbent (keeper)": {},
    "-fleet_status_scope": {"fleet_status_scope": False},
    "+extract_basis_share": {"extract_basis_share": True},
    "+merit_order_guard": {"per_unit_crosswalk": True, "merit_order_guard": True},
    # miso-266: the DISPATCHED-bin denominator. The candidate this probe exists
    # to size, chosen on the extract's/LP's own construction (the denominator
    # must be the capacity the multiplier is applied to), never on the residual.
    "+dispatched_bin_denom": lambda roster: {"lp_bin_capacity": roster},
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--iso", default="MISO")
    args = ap.parse_args()

    bundle = REPO / args.bundle
    _assert_partition_leg(json.loads((bundle / "meta.json").read_text()), args.year)
    state, _ = reconstruct_bundle_fleet(bundle, args.year, verbose=False)
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    codes = np.asarray(fa.plant_code)
    groups = np.asarray(fa.plant_group)

    from market_sim.data.fleet import FUEL_TYPE_MAP

    is_coal = np.asarray(fa.fuel_type_idx) == FUEL_TYPE_MAP["coal"]
    # The LP's OWN per-bin capacity, off the very generators/pmax the overlay is
    # applied to — the miso-266 candidate's denominator.
    from market_sim.data.outages import lp_bin_capacity_index

    roster = lp_bin_capacity_index(state["fleet"], pmax)
    # The overlay is keyed (plant_code, plant_group); collect each coal plant's
    # key and its LP capacity once, so every variant is scored on one fleet.
    plant_keys: dict[str, tuple[int, str]] = {}
    plant_cap: dict[str, float] = defaultdict(float)
    for i in np.nonzero(is_coal)[0]:
        code = str(codes[i])
        plant_keys[code] = (int(codes[i]), str(groups[i]))
        plant_cap[code] += pmax[i]

    bench = load_bench(args.iso, args.year)
    meters: dict[str, np.ndarray] = {}
    for key, rec in bench["plants"].items():
        if rec.get("group") not in COAL_CLASSES:
            continue
        base = key.split(":")[0]
        if base not in plant_keys:
            continue
        m = decode_plant_mw(rec, key)
        if m is not None:
            meters[base] = m

    print(f"=== {args.iso} {args.year} — derate-variant sizing on the hard-zero contradiction (ZERO LP) ===")
    print(f"fleet: {args.bundle}   coal plants with a verified meter: {len(meters)}")
    print()
    hdr = f"{'variant':24} {'avail==0 h':>11} {'contradicted h':>15} {'metered TWh':>12} {'plants':>7}"
    print(hdr)
    print("-" * len(hdr))
    for name, spec in VARIANTS.items():
        extra = spec(roster) if callable(spec) else spec
        try:
            fac = unit_outage_derate_factors(
                args.year, iso=args.iso, **{**BASE_KWARGS, **extra}
            )
        except Exception as exc:  # pragma: no cover - a variant may be unbuildable
            print(f"{name:24} ERROR: {exc}")
            continue
        zero_h = contra_h = 0
        twh = 0.0
        plants = 0
        for base, meter in meters.items():
            f = fac.get(plant_keys[base])
            if f is None:
                continue
            f = np.asarray(f, dtype=float)
            n = min(len(f), len(meter))
            z = f[:n] <= 1e-9
            zero_h += int(z.sum())
            bad = z & (meter[:n] > 0.0)
            if bad.any():
                plants += 1
            contra_h += int(bad.sum())
            twh += float(meter[:n][bad].sum()) / 1e6
        print(f"{name:24} {zero_h:11,d} {contra_h:15,d} {twh:12.3f} {plants:7d}")
    print()
    print("  avail==0 h      = plant-hours the outage overlay alone drives to FULL derate")
    print("  contradicted h  = those hours in which the plant's own committed meter is above zero")
    print("  A repair that addresses the zeroing SHRINKS the contradicted column.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
