"""Crosswalk each ISO's capacity *areas* onto the model's *zones*.

The ``capacity-deliverability`` clean datatype is keyed by each market's native
capacity area — a PJM LDA, MISO LRZ, NYISO locality, ISO-NE capacity zone, or
CAISO local area / intertie branch group. The dispatch LP is built on the model
zones declared in :mod:`market_sim.config.iso_configs`, whose granularity does
**not** match: PJM's 8 zones already track LDA clusters, but MISO collapses 10
LRZs onto 3 regions, NYISO's localities nest, and CAISO's local capacity areas
are sub-zonal transmission pockets that the 3-hub (Path 15 / Path 26) topology
cannot fully resolve.

This module makes every one of those mappings explicit, per ISO, via a small
registry of resolver callables (:data:`_RESOLVERS`) — never an ``if iso ==``
ladder in the consumer. Each area resolves to an :class:`AreaMapping` carrying
the target model zone(s), a ``kind`` describing the granularity relationship,
and whether the area *contributes* to its zone's rollup. The contribution flag
is what prevents double-counting: a nested sub-area (PJM ATSI-Cleveland ⊂ ATSI)
or a super-area spanning several zones (PJM MAAC ⊇ EMAAC+SWMAAC+…, NYISO G-J,
ISO-NE SENE, MISO "North"/"South" subregions) is mapped for documentation but
excluded from the per-zone sum.

Any area with no clean single-zone (or aggregable) home is returned as
``kind="unmapped"`` with an empty ``zones`` tuple and logged by
:func:`aggregate_by_zone` — the crosswalk never invents a mapping.

``kind`` vocabulary
-------------------
* ``leaf``      — one area ↔ one zone, 1:1; contributes.
* ``component`` — one of several sibling areas summed into one zone; contributes.
* ``seam``      — an intertie/branch group summed into an import node; contributes.
* ``nested``    — a proper subset of another mapped area; single zone but does
  NOT contribute (its parent already does).
* ``aggregate`` — a super-area spanning ≥1 zones that other areas already cover;
  does NOT contribute.
* ``system``    — an RTO/statewide row (PRMR/IRM/ICR); no internal zone.
* ``unmapped``  — no clean model-zone home; logged, never counted.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)

# The model calls ISO New England "NEISO"; capacity areas are filed under the
# "ISONE" label used by the clean partition and by the resolver table below.
_CLEAN_ISO_ALIAS: dict[str, str] = {"NEISO": "ISONE"}

# kinds whose value is summed into their (single) target zone.
_CONTRIBUTING_KINDS: frozenset[str] = frozenset({"leaf", "component", "seam"})


@dataclass(frozen=True)
class AreaMapping:
    """How one capacity area maps onto the model topology.

    Attributes:
        area: The ISO's native area label (verbatim from the clean frame).
        zones: Model zone name(s) the area covers. Empty for ``system`` /
            ``unmapped`` areas.
        kind: Granularity relationship — one of the vocabulary in the module
            docstring.
        note: Human-readable justification for the mapping (geography, nesting,
            or why it is unmapped), surfaced in docs and review.
    """

    area: str
    zones: tuple[str, ...]
    kind: str
    note: str = ""

    @property
    def contributes(self) -> bool:
        """Whether this area's value is summed into its zone's rollup.

        True only for single-zone contributing kinds; a contributing mapping
        must name exactly one zone (siblings sum; supersets never contribute).
        """
        return self.kind in _CONTRIBUTING_KINDS and len(self.zones) == 1


# ---------------------------------------------------------------------------
# PJM — 8 model zones already track LDA clusters (iso_configs `_pjm_config`).
# MAAC is the super-LDA (MAAC ⊇ EMAAC + SWMAAC + central-PA); EMAAC and SWMAAC
# are themselves parents of their component LDAs (PSEG/JCPL/DPL-SOUTH/PS-NORTH ⊂
# EMAAC; BGE/PEPCO ⊂ SWMAAC), so only the LDA that matches a whole zone
# contributes and the nested sub-LDAs are excluded. PJM_West_APS (AP/DUQ) has no
# published LDA row and is therefore left with no requirement source.
# ---------------------------------------------------------------------------
_PJM: dict[str, AreaMapping] = {
    "COMED": AreaMapping("COMED", ("PJM_ComEd",), "leaf", "ComEd ≙ PJM_ComEd"),
    "DAY": AreaMapping(
        "DAY",
        ("PJM_AEP_Ohio",),
        "component",
        "Dayton LDA, one of the AEP-Ohio-zone sub-LDAs (partial: AEP/OVEC not filed separately)",
    ),
    "DEOK": AreaMapping(
        "DEOK",
        ("PJM_AEP_Ohio",),
        "component",
        "Duke-OH/KY LDA within the AEP_Ohio zone (summed with DAY)",
    ),
    "ATSI": AreaMapping("ATSI", ("PJM_ATSI",), "leaf", "ATSI ≙ PJM_ATSI"),
    "ATSI-Cleveland": AreaMapping(
        "ATSI-Cleveland",
        ("PJM_ATSI",),
        "nested",
        "Cleveland sub-LDA ⊂ ATSI — excluded so ATSI is not double-counted",
    ),
    "PL": AreaMapping("PL", ("PJM_Central_PA",), "leaf", "PPL (PL) ≙ PJM_Central_PA"),
    "DOM": AreaMapping("DOM", ("PJM_Dominion",), "leaf", "Dominion ≙ PJM_Dominion"),
    "EMAAC": AreaMapping("EMAAC", ("PJM_EMAAC",), "leaf", "EMAAC ≙ PJM_EMAAC"),
    "PSEG": AreaMapping(
        "PSEG", ("PJM_EMAAC",), "nested", "PSEG sub-LDA ⊂ EMAAC — excluded"
    ),
    "PS-NORTH": AreaMapping(
        "PS-NORTH", ("PJM_EMAAC",), "nested", "PSEG-North sub-LDA ⊂ EMAAC — excluded"
    ),
    "JCPL": AreaMapping(
        "JCPL", ("PJM_EMAAC",), "nested", "JCPL sub-LDA ⊂ EMAAC — excluded"
    ),
    "DPL-SOUTH": AreaMapping(
        "DPL-SOUTH", ("PJM_EMAAC",), "nested", "DPL-South sub-LDA ⊂ EMAAC — excluded"
    ),
    "SWMAAC": AreaMapping("SWMAAC", ("PJM_SWMAAC",), "leaf", "SWMAAC ≙ PJM_SWMAAC"),
    "BGE": AreaMapping(
        "BGE", ("PJM_SWMAAC",), "nested", "BGE sub-LDA ⊂ SWMAAC — excluded"
    ),
    "PEPCO": AreaMapping(
        "PEPCO", ("PJM_SWMAAC",), "nested", "PEPCO sub-LDA ⊂ SWMAAC — excluded"
    ),
    "MAAC": AreaMapping(
        "MAAC",
        ("PJM_EMAAC", "PJM_SWMAAC", "PJM_Central_PA"),
        "aggregate",
        "MAAC super-LDA ⊇ EMAAC + SWMAAC + central PA — excluded (children counted)",
    ),
}


# ---------------------------------------------------------------------------
# MISO — 10 LRZs → 6 model zones (iso_configs `_miso_config`, the whole-sub-BA
# LRZ-union partition of the zonal refinement): West = LRZ 1, Plains = LRZ
# 3+5, Illinois = LRZ 4, Indiana = LRZ 6, East = LRZ 2+7, South = LRZ 8+9+10.
# Each LRZ is a `component` summed into its zone (strictly finer than the old
# {1,3,5}/{2,4,6,7}/{8,9,10} split and exactly aligned to the LOLE/PRA data).
# MISO's own subregional "North" (LRZ 1-7 Midwest) and "South" (LRZ 8-10) PRMR
# rows are supersets of the LRZ rows, so they are excluded to avoid
# double-counting; "RTO" is the system row.
# ---------------------------------------------------------------------------
_MISO_LRZ_TO_ZONE: dict[str, str] = {
    "LRZ 1": "MISO-West",
    "LRZ 3": "MISO-Plains",
    "LRZ 5": "MISO-Plains",
    "LRZ 4": "MISO-Illinois",
    "LRZ 6": "MISO-Indiana",
    "LRZ 2": "MISO-East",
    "LRZ 7": "MISO-East",
    "LRZ 8": "MISO-South",
    "LRZ 9": "MISO-South",
    "LRZ 10": "MISO-South",
}
_MISO: dict[str, AreaMapping] = {
    lrz: AreaMapping(
        lrz,
        (zone,),
        "component",
        f"{lrz} summed into {zone} (iso_configs LRZ→region split)",
    )
    for lrz, zone in _MISO_LRZ_TO_ZONE.items()
}
_MISO.update(
    {
        # MISO "North" subregion = LRZ 1-7 = the five Midwest model zones.
        "North": AreaMapping(
            "North",
            (
                "MISO-West",
                "MISO-Plains",
                "MISO-Illinois",
                "MISO-Indiana",
                "MISO-East",
            ),
            "aggregate",
            "MISO Midwest subregion (LRZ 1-7) — superset of the LRZ rows, excluded",
        ),
        # MISO "South" subregion = LRZ 8-10 = MISO-South; superset of those LRZs.
        "South": AreaMapping(
            "South",
            ("MISO-South",),
            "aggregate",
            "MISO South subregion (LRZ 8-10) — superset of LRZ 8/9/10, excluded",
        ),
        "RTO": AreaMapping("RTO", (), "system", "MISO system PRMR/PRM row"),
    }
)


# ---------------------------------------------------------------------------
# NYISO — localities vs 5 model zones (iso_configs `_nyiso_config`). NYC (J) and
# Long Island (K) map 1:1; G-J (zones G,H,I,J) is a nested super-locality that
# spans Capital/Hudson (G) + Lower-Hudson (H,I) + NYC (J), so it is excluded.
# NYCA is the statewide IRM.
# ---------------------------------------------------------------------------
_NYISO: dict[str, AreaMapping] = {
    "NYC": AreaMapping("NYC", ("NYC",), "leaf", "Load Zone J ≙ NYC"),
    "Long Island": AreaMapping(
        "Long Island", ("Long_Island",), "leaf", "Load Zone K ≙ Long_Island"
    ),
    "G-J": AreaMapping(
        "G-J",
        ("Capital_Hudson", "Lower_Hudson", "NYC"),
        "aggregate",
        "G-J locality (zones G,H,I,J) spans Capital/Hudson + Lower-Hudson + NYC — excluded",
    ),
    "NYCA": AreaMapping("NYCA", (), "system", "NYCA statewide IRM row"),
}


# ---------------------------------------------------------------------------
# ISO-NE — capacity zones vs 4-5 model zones (iso_configs `_neiso_config`). Only
# NNE (ME/NH/VT) maps cleanly onto North; Maine is nested inside NNE. SENE
# (Southeast New England) spans the three southern load pockets (Central +
# Boston + Connecticut) and is excluded. RestOfSystem is the system ICR.
# ---------------------------------------------------------------------------
_ISONE: dict[str, AreaMapping] = {
    "NNE": AreaMapping(
        "NNE", ("North",), "leaf", "Northern New England (ME+NH+VT) ≙ North"
    ),
    "Maine": AreaMapping(
        "Maine", ("North",), "nested", "Maine ⊂ NNE — excluded (NNE counted)"
    ),
    "SENE": AreaMapping(
        "SENE",
        ("Central", "Boston", "Connecticut"),
        "aggregate",
        "Southeast New England spans Central + Boston + Connecticut — excluded",
    ),
    "RestOfSystem": AreaMapping("RestOfSystem", (), "system", "ISO-NE system ICR row"),
}


# ---------------------------------------------------------------------------
# CAISO — requirement rows are internal local-capacity-area LCRs; import_limit
# rows are branch-group Maximum Import Capability (a SEAM import limit into the
# WECC boundary, NOT an internal transfer). The 3-hub (NP15/ZP26/SP15 across
# Path 15 / Path 26) topology cannot resolve most local areas, so only the ones
# with an unambiguous north/south geography are mapped; boundary-straddling
# pockets are left unmapped. Branch groups all route to the WECC_import node.
# ---------------------------------------------------------------------------
# LCR local areas → the Path-15/26 hub they sit in, by geography. Unresolvable
# pockets (straddling Path 15 or Path 26) are omitted here and fall through to
# `unmapped` rather than being guessed.
_CAISO_LCR_TO_ZONE: dict[str, tuple[str, str]] = {
    "Humboldt": ("NP15", "far-northern coast, north of Path 15"),
    "North Coast/North Bay": ("NP15", "north of Path 15 (PG&E north)"),
    "Greater Bay": ("NP15", "SF Bay Area, north of Path 15"),
    "Sierra": ("NP15", "Sacramento/Sierra, north of Path 15"),
    "Greater Fresno": (
        "ZP26",
        "central San Joaquin, between Path 15 and Path 26 ≙ ZP26",
    ),
    # SP15 split (2026-07-09 foundation): Big Creek/Ventura has no membership
    # rows of its own (docs/handoffs/caiso-sp15-split-implementation-scope
    # -2026-07-09.md "FOUNDATION DECISIONS") and is the SCE LA-basin pocket
    # per the LCT geography, so it folds into LA_BASIN rather than SP15_rest.
    "Big Creek/Ventura": ("LA_BASIN", "SCE LA-basin pocket, south of Path 26"),
    "LA Basin": ("LA_BASIN", "Los Angeles basin LCR pocket, south of Path 26"),
    "San Diego/Imperial Valley": (
        "SDGE",
        "SDG&E/Imperial LCR pocket, south of Path 26, Path-44 import-limited",
    ),
}
# LCR pockets the 3-hub model cannot resolve — documented as unmapped, not guessed.
_CAISO_LCR_UNMAPPED: dict[str, str] = {
    "Stockton": "northern San Joaquin straddling the Path 15 boundary — unresolved",
    "Kern": "Kern County straddling the Path 26 (ZP26/SP15) boundary — unresolved",
}


def _caiso_resolve(area: str, area_type: str | None) -> AreaMapping:
    """Resolve one CAISO area, dispatching on its ``area_type``.

    ``branch_group`` → the WECC_import seam node (MIC is a seam import limit);
    ``local_area`` → the Path-15/26 hub by geography (or unmapped where the hub
    model cannot resolve the pocket); ``rto`` → the system PRM row.
    """
    if area == "CAISO" or area_type == "rto":
        return AreaMapping(area, (), "system", "CAISO system PRM row")
    if area_type == "branch_group":
        return AreaMapping(
            area,
            ("WECC_import",),
            "seam",
            "branch-group MIC — seam import limit into the WECC_import node",
        )
    # local_area (LCR) rows.
    if area in _CAISO_LCR_TO_ZONE:
        zone, why = _CAISO_LCR_TO_ZONE[area]
        return AreaMapping(area, (zone,), "leaf", f"LCR local area: {why}")
    if area in _CAISO_LCR_UNMAPPED:
        return AreaMapping(area, (), "unmapped", _CAISO_LCR_UNMAPPED[area])
    return AreaMapping(
        area, (), "unmapped", "CAISO local area with no clean Path-15/26 hub home"
    )


def _dict_resolver(
    table: dict[str, AreaMapping],
) -> Callable[[str, str | None], AreaMapping]:
    """Build a resolver that looks an area up in an explicit table.

    Unknown areas resolve to ``kind="unmapped"`` so a new area label in the
    source data surfaces in the logs instead of silently vanishing.
    """

    def resolve(area: str, area_type: str | None) -> AreaMapping:
        mapping = table.get(area)
        if mapping is not None:
            return mapping
        return AreaMapping(area, (), "unmapped", "no crosswalk entry")

    return resolve


# Per-ISO resolver registry — the consumer dispatches through this, never a
# per-ISO branch. Keyed by the clean-partition ISO label (ISONE, not NEISO).
_RESOLVERS: dict[str, Callable[[str, str | None], AreaMapping]] = {
    "PJM": _dict_resolver(_PJM),
    "MISO": _dict_resolver(_MISO),
    "NYISO": _dict_resolver(_NYISO),
    "ISONE": _dict_resolver(_ISONE),
    "CAISO": _caiso_resolve,
}


def _clean_iso(iso: str) -> str:
    """Return the resolver-registry ISO label for a model ISO name."""
    up = iso.upper()
    return _CLEAN_ISO_ALIAS.get(up, up)


def map_area(iso: str, area: str, area_type: str | None = None) -> AreaMapping:
    """Return the :class:`AreaMapping` for one capacity area of ``iso``.

    Args:
        iso: Model ISO name (``NEISO`` is accepted for ISO New England).
        area: The area label exactly as it appears in the clean frame.
        area_type: The clean frame's ``area_type`` for the row (needed to
            distinguish CAISO branch groups from local areas); optional for the
            table-driven ISOs.

    Returns:
        The mapping; ``kind="unmapped"`` (empty ``zones``) when the ISO is
        unknown or the area has no clean model-zone home.
    """
    resolver = _RESOLVERS.get(_clean_iso(iso))
    if resolver is None:
        return AreaMapping(area, (), "unmapped", f"no resolver for ISO {iso}")
    return resolver(area, area_type)


def aggregate_by_zone(
    iso: str,
    area_values: dict[str, float],
    area_types: dict[str, str] | None = None,
) -> tuple[dict[str, float], list[AreaMapping]]:
    """Aggregate area-keyed values onto model zones, honouring nesting.

    Sums each *contributing* area's value into its single target zone (leaf /
    component / seam kinds); nested subsets, multi-zone super-areas, system
    rows and unmapped areas are excluded from the sum to avoid double-counting.

    Args:
        iso: Model ISO name.
        area_values: ``{area: MW}`` as returned by the reader in
            :mod:`market_sim.data.capacity_deliverability`.
        area_types: Optional ``{area: area_type}`` needed to route CAISO
            branch groups vs local areas correctly; other ISOs ignore it.

    Returns:
        Tuple ``(by_zone, skipped)`` where ``by_zone`` is ``{zone: MW}`` summed
        over contributing areas and ``skipped`` is the list of non-contributing
        :class:`AreaMapping`\\ s (aggregate/nested/system/unmapped) for logging.
    """
    area_types = area_types or {}
    by_zone: dict[str, float] = {}
    skipped: list[AreaMapping] = []
    for area, value in area_values.items():
        mapping = map_area(iso, area, area_types.get(area))
        if mapping.contributes:
            zone = mapping.zones[0]
            by_zone[zone] = by_zone.get(zone, 0.0) + float(value)
        else:
            skipped.append(mapping)
    if skipped:
        unmapped = [m.area for m in skipped if m.kind == "unmapped"]
        if unmapped:
            logger.info(
                "capacity-deliverability %s: %d area(s) unmapped, excluded from "
                "zone rollup: %s",
                iso,
                len(unmapped),
                ", ".join(sorted(unmapped)),
            )
    return by_zone, skipped
