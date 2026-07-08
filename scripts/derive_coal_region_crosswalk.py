#!/usr/bin/env python3
"""Derive the region -> ISO coal-plant crosswalk for the new coal-basin-price
datatype (see ``fetch_eia_coal_prices.py`` / ``curate_coal_basin_price.py``).

Every coal plant across the six ISOs already carries a resolved supply-chain
tag (:func:`market_sim.data.coal.coal_supply_class`: ``prb`` / ``subbituminous``
/ ``bituminous`` / ``lignite`` / ``waste``) — the tag the coal-vs-gas
passthrough sigmoids key off (issue #1347). This script maps each tagged plant
onto the EIA Annual Coal Report PRODUCING region/state its coal is sourced
from, so a future re-derivation of the sigmoids can pull the region's own
f.o.b.-mine price series instead of reusing another ISO's byte-copied
``gas_mid``/``gas_slope`` constants (the rule-24 wart this collection session
exists to unblock).

Resolution logic (documented, no fitting — every rule is a physical/contract
fact, not a residual-fit):

1. ``prb`` / ``subbituminous`` -> region ``PRB`` (Powder River Basin, WY/MT),
   REGARDLESS of the plant's own state. Both tags mean "PRB-by-rail delivered"
   per ``coal.py``'s own docstrings (:data:`market_sim.data.coal.COAL_PLANT_SUPPLY`
   comments, and ``fuel.py``'s PJM-subbituminous comment) — the coal is mined
   in Wyoming/Montana and railed to the plant, so the PRODUCING region is PRB
   no matter where the plant sits.
2. ``lignite`` -> the plant's OWN state (mine-mouth: lignite is burned at or
   near the mine, never railed cross-country — Texas and North Dakota lignite
   never leaves those states' EIA price-by-rank rows).
3. ``bituminous`` -> the plant's own state if EIA publishes a dedicated
   ``stateRegionId`` for it (``STATE_TO_EIA_REGION`` below); otherwise falls
   back to the state's U.S. Census Bureau division aggregate that EIA groups
   under (documented per-state in the table) — every fallback aggregate
   carries its own BIT-rank price-by-rank rows (verified for all years used).
4. ``waste`` -> no EIA region (culm/gob reclamation fuel is not commodity-
   traded; ``fuel.py`` already prices it with ``floor=1.0`` for exactly this
   reason — there is no cheap-gas discount to key off a nonexistent market).
5. Unresolved supply tag (e.g. CAISO's Argus Cogen, a 50 MW industrial cogen
   whose coal.py-derived tag is empty at HEAD) -> falls back to the docstring-
   documented rank (``coal_chp_overrides``' own comment: "predominantly
   bituminous") with LOW confidence and no state/basin match (California is
   not a coal-producing state and has no EIA aggregate); left for a human
   sourcing decision, not guessed into a specific basin.

Two ISOs have plants with no dedicated or aggregate EIA producing-region
(NEISO's sole coal plant, in New Hampshire — no coal-producing New England
census division exists) — these get a documented LOW-confidence proxy
(Appalachia Total, the historical rail-delivery source for Northeast utility
bituminous) rather than a fabricated precise match. NYISO has ZERO coal
plants at HEAD (verified via ``load_fleet_from_csv``) — explicitly excluded,
mirroring the ``capacity-deliverability`` datatype's ERCOT-exclusion
convention (:mod:`docs.adding_new_data_types`).

Output: data/raw/reference/coal_region_crosswalk.csv
  columns: iso, plant_code, plant_name, state, coal_supply_class, region_id,
           region_name, confidence, note

Usage:
    python scripts/derive_coal_region_crosswalk.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.coal import coal_supply_class  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

OUT_PATH = REPO / "data" / "raw" / "reference" / "coal_region_crosswalk.csv"

# EIA coal/market-sales-price + coal/price-by-rank "stateRegionId" values that
# are dedicated to a single state (vs. a multi-state Census-division
# aggregate). Source: EIA Open Data API v2, coal/market-sales-price facet
# discovery (fetch_eia_coal_prices.py). West Virginia and Kentucky carry a
# further Northern/Southern and East/West split EIA also publishes
# (WVN/WVS, KYE/KYW) but this crosswalk uses the whole-state code — the
# finer split needs county-level plant siting this session did not do.
STATE_HAS_DEDICATED_REGION: frozenset[str] = frozenset(
    {
        "AL",
        "CO",
        "IL",
        "IN",
        "KY",
        "LA",
        "MD",
        "MO",
        "MS",
        "MT",
        "ND",
        "NM",
        "OH",
        "PA",
        "TX",
        "UT",
        "VA",
        "WV",
        "WY",
    }
)

# States EIA does not publish a dedicated coal-price row for -> their U.S.
# Census Bureau division aggregate (the EIA region grouping the state's coal
# consumption/production rolls into). Source: EIA Annual Coal Report region
# definitions (Census divisions); verified each aggregate carries its own
# rank-level price-by-rank rows in the fetched data.
STATE_TO_CENSUS_AGGREGATE: dict[str, str] = {
    "IA": "WNC",  # West North Central
    "MN": "WNC",
    "SD": "WNC",
    "MI": "ENC",  # East North Central
    "WI": "ENC",
    "AR": "WSC",  # West South Central
    "TN": "ESC",  # East South Central
    # No coal-producing New England / Pacific aggregate exists in the EIA
    # region set; these two are LOW-confidence physical-plausibility proxies
    # (documented per-row below), not a Census-division lookup.
    "NH": "APP",  # Appalachia Total: historical NE utility bituminous source
    "CA": "WST",  # West Total: no CA production; broadest western proxy
}

_LOW_CONFIDENCE_STATES = frozenset({"NH", "CA"})


def _region_for(supply: str, state: str) -> tuple[str, str]:
    """Return ``(region_id, confidence)`` for one plant's supply tag/state."""
    if supply in ("prb", "subbituminous"):
        return "PRB", "high"
    if supply == "lignite":
        # Mine-mouth: always the plant's own state.
        return state, "high" if state in STATE_HAS_DEDICATED_REGION else "low"
    if supply == "bituminous":
        if state in STATE_HAS_DEDICATED_REGION:
            return state, "high"
        agg = STATE_TO_CENSUS_AGGREGATE.get(state)
        if agg:
            conf = "low" if state in _LOW_CONFIDENCE_STATES else "medium"
            return agg, conf
        return "", "none"
    if supply == "waste":
        return "", "none"
    return "", "none"


_NOTE = {
    "PRB": "PRB-by-rail (coal.py/fuel.py docstring), producing region fixed regardless of plant state",
    "lignite": "mine-mouth: producing region = plant's own state",
    "bituminous_dedicated": "plant's own state has a dedicated EIA producing-region code",
    "bituminous_census": "no dedicated state code; EIA Census-division aggregate",
    "bituminous_low": "no coal-producing region for this state; low-confidence physical-plausibility proxy",
    "waste": "culm/gob reclamation fuel; not commodity-traded, no EIA region",
    "unresolved": "coal.py supply tag unresolved at HEAD; rank per coal.py docstring only, no region match",
}


def build_crosswalk() -> list[dict]:
    """Return one row per (ISO, coal plant) with its resolved EIA region."""
    rows: list[dict] = []
    for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"):
        cfg = get_iso_config(iso)
        fleet = load_fleet_from_csv(iso, cfg)
        plants: dict[int, dict] = {}
        for g in fleet:
            if g.fuel_type != "coal" or int(g.plant_code) <= 0:
                continue
            code = int(g.plant_code)
            plants.setdefault(code, {"name": g.name, "state": g.state, "pmax": 0.0})
            plants[code]["pmax"] += g.pmax_mw
        for code, info in sorted(plants.items()):
            supply = coal_supply_class(code)
            state = info["state"]
            if not supply:
                rows.append(
                    {
                        "iso": iso,
                        "plant_code": code,
                        "plant_name": info["name"],
                        "state": state,
                        "coal_supply_class": "",
                        "region_id": "",
                        "region_name": "",
                        "confidence": "none",
                        "note": _NOTE["unresolved"],
                    }
                )
                continue
            region_id, confidence = _region_for(supply, state)
            if supply in ("prb", "subbituminous"):
                note = _NOTE["PRB"]
            elif supply == "lignite":
                note = _NOTE["lignite"]
            elif supply == "bituminous":
                if state in STATE_HAS_DEDICATED_REGION:
                    note = _NOTE["bituminous_dedicated"]
                elif confidence == "low":
                    note = _NOTE["bituminous_low"]
                elif region_id:
                    note = _NOTE["bituminous_census"]
                else:
                    note = _NOTE["unresolved"]
            elif supply == "waste":
                note = _NOTE["waste"]
            else:
                note = _NOTE["unresolved"]
            rows.append(
                {
                    "iso": iso,
                    "plant_code": code,
                    "plant_name": info["name"],
                    "state": state,
                    "coal_supply_class": supply,
                    "region_id": region_id,
                    "region_name": region_id,
                    "confidence": confidence,
                    "note": note,
                }
            )
    return rows


def main() -> None:
    rows = build_crosswalk()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "iso",
                "plant_code",
                "plant_name",
                "state",
                "coal_supply_class",
                "region_id",
                "region_name",
                "confidence",
                "note",
            ],
        )
        w.writeheader()
        w.writerows(rows)
    by_iso: dict[str, int] = {}
    for r in rows:
        by_iso[r["iso"]] = by_iso.get(r["iso"], 0) + 1
    print(f"wrote {len(rows)} rows -> {OUT_PATH}")
    print("plants per ISO:", by_iso)


if __name__ == "__main__":
    main()
