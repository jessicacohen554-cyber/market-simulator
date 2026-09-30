"""SPP CT_PEAKER forced outage from SPP's own LOLE-study EFOR (SPP-104).

Armed by ``ScenarioConfig.spp_ct_lole_efor`` (default off). The keeper's CT_PEAKER
rows otherwise carry the national NERC-GADS statistical stack
(``THERMAL_AVAILABILITY["CT_PEAKER"]``, WEFOR scaled by ``wefor_multiplier`` and
redistributed by ``SUMMER_WEFOR_SHARE``). This module supplies the replacement
forced-outage rate: each plant's capacity-weighted mean of its CT units' SPP
natural-gas EFOR for their size bin (``constants.SPP_LOLE_GAS_EFOR_BY_SIZE``),
one summer and one winter value. It REPLACES the WEFOR term; it never stacks on it
(rule 19 [R-ONE-MECH]). Zero free parameters (rule 21 [R-DOF]).
docs/handoffs/DESIGN-spp-104-ct-outage-2026-09-29.md.
"""

from __future__ import annotations

from market_sim.config.constants import SPP_LOLE_GAS_EFOR_BY_SIZE


def efor_for_unit_mw(mw: float) -> tuple[float, float]:
    """Return ``(summer, winter)`` SPP natural-gas EFOR for one unit of ``mw`` MW.

    Raises:
        ValueError: ``mw`` is non-positive or above the table's last edge (SPP
            publishes no natural-gas EFOR above 600 MW, and none is invented).
    """
    if not mw > 0.0:
        raise ValueError(f"unit size must be positive, got {mw!r}")
    for edge, summer, winter in SPP_LOLE_GAS_EFOR_BY_SIZE:
        if mw <= edge:
            return summer, winter
    raise ValueError(f"no SPP natural-gas EFOR published for a {mw:.1f} MW unit")


def plant_efor(unit_mw: dict[str, float]) -> tuple[float, float]:
    """Capacity-weighted ``(summer, winter)`` EFOR over one plant's CT units."""
    total = sum(unit_mw.values())
    if total <= 0.0:
        raise ValueError("plant CT roster carries no capacity")
    s = sum(mw * efor_for_unit_mw(mw)[0] for mw in unit_mw.values())
    w = sum(mw * efor_for_unit_mw(mw)[1] for mw in unit_mw.values())
    return s / total, w / total


def spp_ct_plant_efor(
    iso: str,
    year: int,
    cc_steam_part_reclass: bool = False,
    mid_vintage_exit_carry: bool = False,
) -> dict[int, tuple[float, float]]:
    """Return ``{plant_code: (summer_efor, winter_efor)}`` for every SPP CT_PEAKER plant.

    Unit sizes are the per-generator MW of the SAME fleet load the outage layer's
    per-unit roster reads (``outages._iso_plant_unit_capacity``), at the active
    EIA-860 vintage, so the roster and the LP rows cannot disagree about which
    units a plant carries.

    Raises:
        ValueError: ``iso`` is not SPP — the table is SPP's own (rule 25
            [R-ISO-SCOPE]).
    """
    if iso != "SPP":
        raise ValueError(
            f"spp_ct_lole_efor is SPP's own LOLE table and cannot arm for {iso!r} "
            "(rule 25 [R-ISO-SCOPE])"
        )
    from market_sim.data.outages import _iso_plant_unit_capacity

    roster = (
        _iso_plant_unit_capacity(iso, cc_steam_part_reclass, int(year), True)
        if mid_vintage_exit_carry
        else _iso_plant_unit_capacity(iso, cc_steam_part_reclass)
    )
    return {
        int(code): plant_efor(units)
        for (code, group), units in roster.items()
        if group == "CT_PEAKER" and units
    }
