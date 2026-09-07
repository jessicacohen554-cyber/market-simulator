"""Phase-0 offer-array delta (ZERO LP) — PJM PRICE-TAIL lane, gate G-OA.

Builds the PJM base fleet twice under the REGISTERED T1-H hindcast recipe
(``results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm/run_config.json``),
changing exactly one field:

  * control : ``offer_curve_by_group = {}``                    (what the lane ships)
  * arm     : ``offer_curve_by_group = base_offer_curve_by_group("PJM")``

and reports, for each, the thermal offer stack's top and the implied
market-heat-rate ceiling it can support at the hindcast's flat delivered gas
(3.91 Henry Hub + 0.67 PJM basis = 4.58 $/MMBtu).

Read-only: no solve, no config written to disk, no registration. See
``docs/handoffs/PRECOMMIT-pjm-price-tail-2026-09-07.md`` §5 for the
pre-registered STOP gate this feeds.
"""

from __future__ import annotations

import json
import sys

import logging

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet.assembly import build_base_fleet, load_or_synthesize_bins
from market_sim.pipeline.offer_curve_base import base_offer_curve_by_group

CONTROL = (
    "results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm/run_config.json"
)
GAS = 3.91 + 0.67  # hindcast_realized[2021] + GAS_BASIS_DIFFERENTIAL["PJM"]
YEAR = 2021


def _config(offer_curve: dict) -> ScenarioConfig:
    """Rebuild the control's recorded ScenarioConfig with one field replaced."""
    rec = json.load(open(CONTROL))["scenario_config"]
    fields = set(ScenarioConfig.__dataclass_fields__)
    kwargs = {k: v for k, v in rec.items() if k in fields}
    dropped = sorted(set(rec) - fields)
    if dropped:
        print(f"  [warn] recorded fields absent from HEAD dataclass: {dropped}")
    kwargs["offer_curve_by_group"] = offer_curve
    return ScenarioConfig(**kwargs)


def _stack(config: ScenarioConfig) -> list:
    iso_cfg = get_iso_config("PJM")
    zones = list(iso_cfg.zone_names)
    bins = load_or_synthesize_bins(config, "PJM", iso_cfg, [])
    print(f"  bins: {'synthesized ' + str(len(bins)) + ' rows' if bins is not None else 'None (legacy path)'}")
    return build_base_fleet(bins, "PJM", iso_cfg, zones, config, [], [], YEAR)


def _report(label: str, fleet: list) -> dict:
    thermal = [
        g
        for g in fleet
        if getattr(g, "fuel_type", None)
        in {"gas_cc", "gas_ct", "gas_st", "coal", "oil"}
        and float(getattr(g, "pmax_mw", 0.0)) > 0
    ]
    hr = np.array([float(g.heat_rate) for g in thermal])
    cap = np.array([float(g.pmax_mw) for g in thermal])
    vom = np.array([float(getattr(g, "vom", 0.0)) for g in thermal])
    offer = hr * GAS + vom
    order = np.argsort(offer)
    cum = np.cumsum(cap[order])
    print(f"\n=== {label} ===")
    print(f"  thermal LP units: {len(thermal)}   capacity {cap.sum():,.1f} MW")
    print(f"  offer $/MWh @ {GAS:.2f} $/MMBtu:")
    for q in (0.5, 0.9, 0.99, 1.0):
        print(f"     p{int(q*100):<4} {np.quantile(offer, q):8.3f}")
    print(f"  MAX OFFER  = {offer.max():8.3f} $/MWh")
    print(f"  implied market-heat-rate CEILING = max_offer / gas = {offer.max()/GAS:7.3f} MMBtu/MWh")
    print(f"  top-of-stack heat rate (MW-wtd top 1%): {hr[order][cum > 0.99*cap.sum()].min():.3f}")
    return {"max_offer": float(offer.max()), "ceiling": float(offer.max() / GAS),
            "n": len(thermal), "cap": float(cap.sum())}


def main() -> int:
    logging.disable(logging.CRITICAL)
    print("PHASE-0 OFFER-ARRAY DELTA (zero LP) — PJM, year %d, gas %.2f $/MMBtu" % (YEAR, GAS))
    out = {}
    print("\n[control] offer_curve_by_group = {}")
    out["control"] = _report("CONTROL  (shipped T1-H recipe)", _stack(_config({})))
    print("\n[arm] offer_curve_by_group = base_offer_curve_by_group('PJM')")
    base = base_offer_curve_by_group("PJM")
    print(f"  base curve groups: {sorted(base)}")
    out["arm"] = _report("ARM  (shared per-ISO base curve)", _stack(_config(base)))

    # Pre-registered STOP gate G-OA (PRECOMMIT §5): the most expensive unit in
    # the 103-unit failing set has heat rate (58.24 - 4.0)/4.58 = 11.84.
    thresh = 11.84
    print("\n=== GATE G-OA ===")
    print(f"  STOP threshold: implied market-heat-rate ceiling must exceed {thresh} MMBtu/MWh")
    for k in ("control", "arm"):
        v = out[k]["ceiling"]
        print(f"  {k:<8} ceiling {v:7.3f}  -> {'CLEARS' if v > thresh else 'BELOW THRESHOLD'}")
    json.dump(out, open("docs/handoffs/pjmtail/phase0-offer-array-delta.json", "w"), indent=1)
    print("\nwrote docs/handoffs/pjmtail/phase0-offer-array-delta.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
