"""Ownership reference data: parent-company lookup and M&A overlays.

This module holds *only data* — no logic. It is kept separate from
:mod:`market_sim.data.ownership` so it can be version-controlled and
hand-edited whenever a new deal closes or EIA publishes a new vintage.

Two tables live here:

* :data:`PARENT_COMPANY_LOOKUP` maps an EIA ``utility_id`` (the
  subsidiary-level operator/owner code) to its canonical ultimate parent
  company. EIA assigns ``utility_id`` at the *subsidiary* level, never the
  corporate parent, so this table is what performs the holding-company
  rollup (e.g. Duke Carolinas + Duke Progress + Duke Florida → Duke Energy).
* :data:`MNA_OVERLAYS` is a list of :class:`OwnershipChange` records, one
  per material 2023–2026 transaction, applied as a date-aware overlay on
  top of the static lookup.

.. warning::

   The EIA ``utility_id`` values below are *best-effort* and **must be
   verified against the actual EIA-860 Schedule 1 (Utility) workbook**
   before the map is relied on for reporting. EIA periodically renames
   subsidiaries after M&A and occasionally reissues IDs. Entries whose ID
   is not known carry a ``# TODO: verify utility_id from EIA-860`` comment
   naming the subsidiary so it can be filled in by hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Canonical parent-company name constants. Centralized so the lookup table
# and the overlay list cannot drift on spelling.
CONSTELLATION = "Constellation Energy"
VISTRA = "Vistra Corp"
TALEN = "Talen Energy"
NEXTERA = "NextEra Energy"
AES = "AES Corporation"
NRG = "NRG Energy"
DUKE = "Duke Energy"
SOUTHERN = "Southern Company"
DOMINION = "Dominion Energy"
BHE = "Berkshire Hathaway Energy"
AEP = "American Electric Power"
ENTERGY = "Entergy"
PSEG = "PSEG"
EXELON = "Exelon"
PGE = "PG&E"
EDISON = "Edison International"
XCEL = "Xcel Energy"
TVA = "TVA"
EVERGY = "Evergy"
AMEREN = "Ameren"
WEC = "WEC Energy Group"
CMS = "CMS Energy"
DTE = "DTE Energy"
PPL = "PPL Corporation"
AVANGRID = "Avangrid"
CLEARWAY = "Clearway Energy"
INVENERGY = "Invenergy"
LS_POWER = "LS Power"
CALPINE = "Calpine"
ENERGY_HARBOR = "Energy Harbor"

# Sentinel parent for generators whose owner cannot be resolved.
UNKNOWN_PARENT = "Other/Unknown"


# EIA ``utility_id`` (int) → canonical ``parent_company`` (str).
#
# Only the long-stable regulated-utility operator IDs are populated with
# numeric keys here. Competitive-generation subsidiaries (Constellation's
# former Exelon Generation entities, Vistra's Luminant/Dynegy, Calpine,
# Talen, the NextEra Energy Resources project LLCs, AES Clean Energy, NRG's
# merchant fleet, etc.) each appear under many short-lived project-level
# ``utility_id`` codes that are not reliably known without the EIA-860
# Schedule 1 workbook in hand; those are listed as TODO comments so the
# table is still complete in coverage and explicit about its gaps.
PARENT_COMPANY_LOOKUP: dict[int, str] = {
    # --- Southern Company -------------------------------------------------
    195: SOUTHERN,    # Alabama Power Co
    7140: SOUTHERN,   # Georgia Power Co
    12686: SOUTHERN,  # Mississippi Power Co
    # TODO: verify utility_id from EIA-860 — Southern Power Co (competitive)
    # --- NextEra Energy ---------------------------------------------------
    6452: NEXTERA,    # Florida Power & Light Co (FPL; absorbed Gulf Power 2021)
    # TODO: verify utility_id from EIA-860 — NextEra Energy Resources LLC subs
    # --- Duke Energy ------------------------------------------------------
    5416: DUKE,       # Duke Energy Carolinas LLC
    3046: DUKE,       # Duke Energy Progress LLC (ex-Carolina Power & Light)
    6455: DUKE,       # Duke Energy Florida LLC (ex-Florida Power Corp)
    15470: DUKE,      # Duke Energy Indiana LLC (ex-PSI Energy)
    # TODO: verify utility_id from EIA-860 — Duke Energy Ohio / Kentucky
    # --- Dominion Energy --------------------------------------------------
    19876: DOMINION,  # Virginia Electric & Power Co (VEPCO)
    17539: DOMINION,  # Dominion Energy South Carolina (ex-SCANA / SCE&G)
    # --- American Electric Power -----------------------------------------
    733: AEP,         # Appalachian Power Co (APCo)
    9324: AEP,        # Indiana Michigan Power Co (I&M)
    15474: AEP,       # Public Service Co of Oklahoma (PSO)
    17683: AEP,       # Southwestern Electric Power Co (SWEPCo)
    10434: AEP,       # Kentucky Power Co
    14015: AEP,       # Ohio Power Co (AEP Ohio generation lineage)
    # Note: AEP Texas is T&D-only in ERCOT and is intentionally NOT mapped
    # as a generation owner.
    # --- Entergy ----------------------------------------------------------
    814: ENTERGY,     # Entergy Arkansas LLC
    12465: ENTERGY,   # Entergy Louisiana LLC
    12685: ENTERGY,   # Entergy Mississippi LLC
    13478: ENTERGY,   # Entergy New Orleans LLC
    # TODO: verify utility_id from EIA-860 — Entergy Texas Inc (MISO South)
    # --- Berkshire Hathaway Energy ---------------------------------------
    14354: BHE,       # PacifiCorp (Pacific Power + Rocky Mountain Power)
    11208: BHE,       # MidAmerican Energy Co
    13407: BHE,       # Nevada Power Co (NV Energy)
    17166: BHE,       # Sierra Pacific Power Co (NV Energy)
    # TODO: verify utility_id from EIA-860 — BHE Renewables LLC subs
    # --- Xcel Energy ------------------------------------------------------
    15466: XCEL,      # Public Service Co of Colorado (PSCo)
    13781: XCEL,      # Northern States Power Co - Minnesota (NSP-MN)
    17698: XCEL,      # Southwestern Public Service Co (SPS)
    # TODO: verify utility_id from EIA-860 — Northern States Power Co - Wisconsin
    # --- TVA --------------------------------------------------------------
    18642: TVA,       # Tennessee Valley Authority
    # --- PSEG -------------------------------------------------------------
    15270: PSEG,      # Public Service Electric & Gas Co
    # TODO: verify utility_id from EIA-860 — PSEG Nuclear LLC
    # --- PG&E -------------------------------------------------------------
    14328: PGE,       # Pacific Gas & Electric Co
    # --- Edison International / SCE --------------------------------------
    17609: EDISON,    # Southern California Edison Co
    # --- Constellation Energy (post-2022 Exelon Generation spin-off) ------
    # TODO: verify utility_id from EIA-860 — Constellation Energy Generation LLC
    # TODO: verify utility_id from EIA-860 — Calpine LLC subs (post 2026-01-07)
    # --- Vistra Corp ------------------------------------------------------
    # TODO: verify utility_id from EIA-860 — Luminant Generation Co LLC
    # TODO: verify utility_id from EIA-860 — Dynegy / Vistra PJM-MISO subs
    # TODO: verify utility_id from EIA-860 — Energy Harbor subs (post 2024-03-01)
    # --- Talen Energy -----------------------------------------------------
    # TODO: verify utility_id from EIA-860 — Susquehanna Nuclear LLC (90% owner)
    # --- NRG Energy -------------------------------------------------------
    # TODO: verify utility_id from EIA-860 — NRG Texas Power LLC and merchant subs
    # --- Exelon (T&D only post-spinoff — retains no generation) ----------
    # TODO: verify utility_id from EIA-860 — Exelon T&D utilities (ComEd, PECO …)
    # --- Other large parents (regulated + competitive) -------------------
    # TODO: verify utility_id from EIA-860 — Evergy (KCP&L, Westar)
    # TODO: verify utility_id from EIA-860 — Ameren Missouri / Ameren Illinois
    # TODO: verify utility_id from EIA-860 — WEC Energy Group subs
    # TODO: verify utility_id from EIA-860 — CMS Energy / Consumers Energy
    # TODO: verify utility_id from EIA-860 — DTE Energy / DTE Electric Co
    # TODO: verify utility_id from EIA-860 — PPL Corporation utilities
    # TODO: verify utility_id from EIA-860 — Avangrid renewable subs
    # TODO: verify utility_id from EIA-860 — Clearway Energy yieldco subs
    # TODO: verify utility_id from EIA-860 — Invenergy project LLCs
}


@dataclass
class OwnershipChange:
    """A single M&A overlay applied on top of :data:`PARENT_COMPANY_LOOKUP`.

    Attributes:
        effective_date: Transaction effective date in ISO ``YYYY-MM-DD``
            format. The overlay applies only when an ``as_of_date`` is on or
            after this date *and* :attr:`status` is ``"closed"``.
        description: Human-readable transaction summary.
        plant_codes: EIA plant codes the change applies to. ``None`` means
            *all* plants of the affected utilities; an empty list ``[]``
            means *no* plants (a placeholder pending the real plant set).
        from_parent: Canonical parent the affected generators map to before
            the deal. Used as the match key when :attr:`source_utility_ids`
            is empty.
        to_parent: Canonical parent the affected generators map to after the
            deal closes.
        source_utility_ids: EIA ``utility_id`` values of the affected
            subsidiaries. When empty, the overlay matches on
            :attr:`from_parent` instead.
        status: ``"closed"``, ``"pending"`` or ``"announced"``. Only
            ``"closed"`` deals reassign parents; the others are flagged.
    """

    effective_date: str
    description: str
    plant_codes: list[int] | None
    from_parent: str
    to_parent: str
    source_utility_ids: list[int] = field(default_factory=list)
    status: str = "closed"


# Every material 2023–2026 transaction from the ownership research doc.
#
# ``source_utility_ids`` are left empty where the competitive-subsidiary
# EIA codes are not known; the overlay logic falls back to matching on
# ``from_parent`` in that case. ``plant_codes`` is likewise a TODO list
# where a deal covers a specific named plant set rather than a whole
# subsidiary — an empty list keeps the overlay a safe no-op until filled in.
MNA_OVERLAYS: list[OwnershipChange] = [
    OwnershipChange(
        effective_date="2024-03-01",
        description=(
            "Vistra acquires Energy Harbor — ~4,000 MW nuclear (Beaver "
            "Valley, Davis-Besse, Perry) plus retail. FERC-approved "
            "2024-02-16, closed 2024-03-01."
        ),
        plant_codes=None,
        from_parent=ENERGY_HARBOR,
        to_parent=VISTRA,
        source_utility_ids=[],  # TODO: verify utility_id from EIA-860 — Energy Harbor subs
        status="closed",
    ),
    OwnershipChange(
        effective_date="2025-04-10",
        description=(
            "NRG acquires 738 MW of flexible Texas gas peaking capacity "
            "from Rockland Capital for $560M."
        ),
        plant_codes=[],  # TODO: verify plant_codes from EIA-860 — Rockland TX gas plants
        from_parent="Rockland Capital",
        to_parent=NRG,
        source_utility_ids=[],
        status="closed",
    ),
    OwnershipChange(
        effective_date="2025-07-17",
        description=(
            "Talen announces acquisition of two H-class CCGTs (~2,500 MW) "
            "from Caithness Energy. Announced 2025-07-17; close pending."
        ),
        plant_codes=[],  # TODO: verify plant_codes from EIA-860 — Caithness H-class CCGTs
        from_parent="Caithness Energy",
        to_parent=TALEN,
        source_utility_ids=[],
        status="announced",
    ),
    OwnershipChange(
        effective_date="2025-10-22",
        description=(
            "Vistra acquires seven natural-gas plants (~2,600 MW) from "
            "Lotus Infrastructure Partners across PJM, ISO-NE, NYISO and "
            "CAISO. Closed 2025-10-22."
        ),
        plant_codes=[],  # TODO: verify plant_codes from EIA-860 — 7 Lotus gas plants
        from_parent="Lotus Infrastructure Partners",
        to_parent=VISTRA,
        source_utility_ids=[],
        status="closed",
    ),
    OwnershipChange(
        effective_date="2026-01-07",
        description=(
            "Constellation acquires Calpine — ~28 GW of gas and geothermal. "
            "FERC-approved 2025-07-24, closed 2026-01-07."
        ),
        plant_codes=None,
        from_parent=CALPINE,
        to_parent=CONSTELLATION,
        source_utility_ids=[],  # TODO: verify utility_id from EIA-860 — Calpine LLC subs
        status="closed",
    ),
    OwnershipChange(
        effective_date="2026-01-07",
        description=(
            "Constellation FERC/DOJ-mandated divestitures to LS Power — "
            "York 2, Hay Road, Edge Moor and the Jack Fusco Energy Center."
        ),
        plant_codes=[],  # TODO: verify plant_codes from EIA-860 — York 2, Hay Road, Edge Moor, Jack Fusco
        from_parent=CONSTELLATION,
        to_parent=LS_POWER,
        source_utility_ids=[],
        status="closed",
    ),
    OwnershipChange(
        effective_date="2026-03-31",
        description=(
            "NRG acquires an LS Power generation portfolio (~13 GW, "
            "largely Northeast/Texas gas). Announced 2025-05-12; expected "
            "to close Q1 2026 pending HSR, FERC and NYSPSC approvals."
        ),
        plant_codes=None,
        from_parent=LS_POWER,
        to_parent=NRG,
        source_utility_ids=[],
        status="pending",
    ),
]
