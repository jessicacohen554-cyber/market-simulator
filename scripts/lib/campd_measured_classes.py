"""Assign a CAMPD unit to a MODEL plant class, on the primary-record basis.

Why this exists. Every calibration probe that compares a model class against
"the measured class" has to decide which CAMPD units make up that class. The
obvious construction — read CAMPD's own ``unitType`` string and map
``"Combined cycle" -> CC_*``, ``"Combustion turbine" -> CT_*``,
``"...boiler"/"...fired" -> ST_*``, crossed with the EIA-860 CHP flag — is what
nyiso-169b / 170 / 171 / 172 / 173 all used. It is wrong at mixed facilities,
because **CAMPD's ``unitType`` is a CEMS monitoring-configuration descriptor,
not an EIA prime-mover code**, and the two disagree.

The measured case that forced this (nyiso-174, ``docs/FINDING-nyiso174-east-
river-class-crosswalk-2026-09-02.md``): Con Edison **East River (2493)**, a
Manhattan steam/electric cogen. CAMPD tags its two 180 MW machines
``"Combined cycle"``, so the ``unitType`` construction sweeps the whole plant
into ``CC_CHP`` — 2.13 / 2.26 / 2.19 TWh a year. The primary record says
otherwise, three independent ways: EIA-860 codes the plant ``GT`` x2 + ``ST``
x2 with **no combined-cycle prime mover (CA/CT/CS) anywhere**; EIA-923 files its
net generation under **two** prime movers, ``GT`` and ``ST``; and CAMPD's own
meters refute CAMPD's own label — those units burn at a measured **10.5-10.9
MMBtu/MWh** and export **zero** steam. The model, which builds its fleet from
EIA-860 through :func:`market_sim.config.plant_taxonomy.classify_plant`,
carries the plant correctly as ``CT_CHP`` 306.0 MW + ``ST_CHP`` 309.5 MW — the
EIA-860 summer split to the megawatt. So does the committed ``classFull``
benchmark, which runs through the same classifier. **The defect was only ever
in the probe-side measured series, never in the model or in anything scored.**

What this module does. It keeps a unit's prime-mover FAMILY (turbine-fired vs
boiler-fired) and lets the unit's own plant's model roster pick the class inside
that family, so a CAMPD unit can never land on a bin its plant does not have.
It is a strict CROSSWALK repair, not a reclassification: at every plant whose
``unitType`` class is one the model carries — which is every NYISO plant but
six, and 99.1 % of measured NY energy — it is a no-op and reproduces the old
construction exactly.

Scope. Nothing here reaches the LP. This is measurement-side only: it decides
which CAMPD rows a probe sums, never what the model dispatches. Rule 13
``[R-MEASURED]`` is satisfied by construction — the inputs are EIA-860 prime
movers and CAMPD unit types, both reproducible for a forward year, and no
statistic is tuned to any residual.
"""

from __future__ import annotations

import re

__all__ = ["campd_unittype_class", "corrected_unit_class", "PRIME_MOVER_FAMILY"]


#: Candidate model classes for a unit's prime-mover FAMILY, in preference order.
#: A turbine-fired unit may be any of the four CC/CT classes (a CEMS stack can
#: monitor a whole combined-cycle block or a bare turbine); a boiler-fired unit
#: is steam and can only ever be one of the two ST classes. The CHP/merchant
#: preference within a family follows the unit's own ``unitType`` verdict, so a
#: plant carrying both variants keeps the one the shared construction chose.
PRIME_MOVER_FAMILY: dict[str, tuple[str, ...]] = {
    "CC_CHP": ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER"),
    "CC_REGULAR": ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP"),
    "CT_CHP": ("CT_CHP", "CT_PEAKER", "CC_CHP", "CC_REGULAR"),
    "CT_PEAKER": ("CT_PEAKER", "CT_CHP", "CC_REGULAR", "CC_CHP"),
    "ST_CHP": ("ST_CHP", "ST_GAS"),
    "ST_GAS": ("ST_GAS", "ST_CHP"),
}


def campd_unittype_class(unit_type: object, is_chp: bool) -> str | None:
    """The class CAMPD's own ``unitType`` string implies, or ``None``.

    This is the SHARED construction nyiso-169b/170/171/172/173 use, reproduced
    verbatim so callers can measure both bases side by side. It is the input to
    :func:`corrected_unit_class`, not a substitute for it.

    Args:
        unit_type: CAMPD ``unitType`` (e.g. ``"Combined cycle"``,
            ``"Dry bottom wall-fired boiler"``).
        is_chp: Whether the unit's plant carries the EIA-860 CHP flag.

    Returns:
        One of the six gas classes, or ``None`` for a unit type outside them
        (coal-only boiler vocabularies still resolve to a steam class, so the
        caller filters those on fuel as it always did).
    """
    s = "" if unit_type is None else str(unit_type)
    if "Combined cycle" in s:
        return "CC_CHP" if is_chp else "CC_REGULAR"
    if "Combustion turbine" in s:
        return "CT_CHP" if is_chp else "CT_PEAKER"
    if re.search("fired|boiler", s, re.I):
        return "ST_CHP" if is_chp else "ST_GAS"
    return None


def corrected_unit_class(
    unittype_class: str | None, plant_model_groups: dict[str, float] | set[str] | None
) -> str | None:
    """Re-seat one CAMPD unit on a class its own plant's model fleet carries.

    The unit keeps its prime-mover family; only the class inside that family
    can change, and only to one the plant actually has. Three cases:

    * the ``unitType`` class IS one of the plant's model groups — returned
      unchanged (the no-op that makes this a strict crosswalk repair);
    * it is not, but the plant carries another class in the same family — the
      first such class in :data:`PRIME_MOVER_FAMILY` preference order wins
      (East River: a turbine-fired unit at a ``{CT_CHP, ST_CHP}`` plant is
      ``CT_CHP``, and its boilers stay ``ST_CHP``);
    * the plant is absent from the model fleet, or carries nothing in the
      unit's family — the ``unitType`` class stands. The correction never
      invents a bin and never moves a machine across the turbine/boiler line,
      so a genuine population gap stays visible as one instead of being
      silently absorbed into a neighbouring class.

    Args:
        unittype_class: The class from :func:`campd_unittype_class`.
        plant_model_groups: The plant's model ``plant_group`` keys — a
            ``{group: MW}`` map or a bare set. Build it from
            ``market_sim.data.fleet.load_fleet_from_csv`` so it is the same
            EIA-860 classification the benchmark and the LP use.

    Returns:
        The corrected model class, or ``None`` when ``unittype_class`` is.
    """
    if not unittype_class:
        return None
    groups = set(plant_model_groups or ())
    if not groups or unittype_class in groups:
        return unittype_class
    for candidate in PRIME_MOVER_FAMILY.get(unittype_class, ()):
        if candidate in groups:
            return candidate
    return unittype_class
