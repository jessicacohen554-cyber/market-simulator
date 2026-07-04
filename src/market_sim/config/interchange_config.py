"""Interchange model configuration — unified spec for all ISOs.

Replaces the parallel CAISO per-hub corridor model and the generic
reference-price seam with a single ``InterchangeSpec`` per ISO, each
containing corridors, reference-price neighbors, firm imports, and
optional monthly reconciliation.  The spec drives a single
``build_interchange_fleet`` function that produces identical
``Generator`` objects regardless of which code path produced them before.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


from market_sim.data.fleet import Generator

# Local copies of constants whose canonical definitions live in constants.py.
# Duplicated here (not imported) to break the circular import:
# interchange_config → constants → interchange_config.
CARB_UNSPECIFIED_IMPORT_EF: float = 0.428  # CARB MRR §95111(b)
_GAS_BASIS_NYISO: float = 0.55  # EIA-923 delivered-gas basis

# ---------------------------------------------------------------------------
# Data constants — moved from constants.py (unchanged values)
# ---------------------------------------------------------------------------

# Per-ISO external zone hosting import/export pseudo-generators.
IMPORT_ZONE: dict[str, str] = {
    "CAISO": "WECC_import",
    "PJM": "PJM_external",
    "NYISO": "NYISO_external",
    "NEISO": "HQ_import",
    "MISO": "MISO_external",
}

# Per-ISO forced-outage derate on import tranches.
IMPORT_EFORD: dict[str, float] = {
    "CAISO": 0.02,
    "PJM": 0.0,
    "NYISO": 0.0,
    "NEISO": 0.0,
    "MISO": 0.0,
}

# Per-tranche CO2 emission factor (tCO2/MWh) for the CARB border-carbon
# adjustment on imports.
IMPORT_TRANCHE_EF: dict[str, dict[str, float]] = {
    "CAISO": {
        "PNW_hydro_base": 0.0,
        "PNW_midC": 0.0,
        "DSW_solar_PV": 0.0,
        "DSW_CCGT": 0.37,
        "DSW_CT": 0.55,
        "WECC_scarcity": CARB_UNSPECIFIED_IMPORT_EF,
    },
}

# Per-tranche physical delivered-cost basis over the measured WECC
# neighbor-hub price, for CAISO priced imports.
CAISO_IMPORT_DELIVERY_BASIS: dict[str, tuple[float, float]] = {
    "PNW_hydro_base": (0.04, 2.0),
    "PNW_midC": (0.05, 5.0),
    "DSW_solar_PV": (0.03, 4.0),
    "DSW_CCGT": (0.03, 4.0),
    "DSW_CT": (0.03, 4.0),
    "WECC_scarcity": (0.03, 6.0),
}

# IMPORT_TRANCHES / EXPORT_TRANCHES entries: (name, capacity MW, $/MWh).
#
# CAISO firm-block volumes (LEVER B, 2026-07-04, FINDING-caiso-evening-merit):
# the two firm/contracted tranches (PNW_hydro_base, DSW_solar_PV — see
# transmission.CAISO_FIRM_IMPORT_TRANCHES) proxy CAISO's resource-adequacy
# import contracts: capacity-backed, must-offer supply that is self-scheduled
# or bid at/below $0/MWh during the availability assessment hours (CPUC
# D.20-06-028), i.e. price-taking firm blocks at the CAISO BAA boundary.
# Their volumes are grounded on two published primary sources:
#   1. TOTAL = DMM Annual Report on Market Issues & Performance, average
#      system RA capacity table, "Imports" row (excl. "Imports-MSS", which are
#      internal metered subsystems, not boundary imports):
#        2023: 2,323 MW (2023 report, Jul 2024, RA chapter capacity table)
#        2024: 3,371 MW (2024 report, Aug 2025, Table 15.6)
#        2025: not yet published (annual report due ~Aug 2026) → carry the
#              latest measured year (2024, 3,371 MW). OPEN DATA GAP: replace
#              when the DMM 2025 annual report lands; the 2025 quarterlies
#              publish only mixed YoY bid-volume changes (+256/-6/-28/-37%)
#              off unpublished monthly bases, insufficient for an annual MW.
#   2. SPLIT PNW vs DSW = published Maximum Import Capability (MIC) per
#      branch group (data/raw/capacity-deliverability/caiso/caiso.csv, CAISO
#      "Maximum RA Import Capability for year YYYY" docs). RA imports require
#      MIC on the source intertie, so the corridor split follows the MIC share
#      north vs south of Path 15 (north = Malin 500, COTP, NOB [PDCI — PNW
#      source, CISO–BPAT interchange], Cascade, Summit, Round Mountain 230,
#      Cottonwood 230, Northwest 230, Marble, and the BANC/TIDC-area ties
#      [Tracy 230/500, Tracy-TEA, Westley-*, Standiford, Oakdale, New Melones,
#      Rancho Seco/Lake], matching CAISO_CORRIDOR_DIBA geography):
#        2023: north 7,411 / 16,055 = 46.2% → PNW 1,072, DSW 1,251
#        2024: north 7,603 / 16,452 = 46.2% → PNW 1,558, DSW 1,813
#        2025: north 7,500 / 16,148 = 46.4% → PNW 1,566, DSW 1,805
#      ("Merchant", 387–516 MW, is unmappable from the MIC doc alone and is
#      kept south; moving it north would shift the split by ~3%.)
# Boundary caveats (rule #14): CEC Total System Electric Generation NW/SW
# imports are all-California (LADWP/IID/BANC included) and CARB's specified
# split is the jurisdictional-importer boundary — both rejected as misaligned.
# EIA-930 net corridor flows cannot size a gross firm block (their low
# percentiles are negative: midday solar exports net against firm imports).
# Prices are unchanged Tier-3 contract-cost proxies (see
# CAISO_FIRM_IMPORT_TRANCHES). The static entry below carries the latest
# grounded (2025) volumes as the forward story — RA import contracting is a
# persistent market structure; backcast years use IMPORT_TRANCHES_BY_YEAR.
IMPORT_TRANCHES: dict[str, list[tuple[str, float, float]]] = {
    "CAISO": [
        ("PNW_hydro_base", 1566.0, 28.0),
        ("PNW_midC", 1800.0, 36.0),
        ("DSW_solar_PV", 1805.0, 48.0),
        ("DSW_CCGT", 1800.0, 68.0),
        ("DSW_CT", 2200.0, 110.0),
        ("WECC_scarcity", 3000.0, 180.0),
    ],
    "PJM": [
        ("import_scarcity_1", 1000.0, 46.0),
        ("import_scarcity_2", 3000.0, 60.0),
    ],
    "NYISO": [
        ("HQ_hydro", 900.0, 14.0),
        ("IESO_Ontario", 1200.0, 24.0),
        ("PJM_west", 1100.0, 34.0),
        ("ISONE_tie", 800.0, 44.0),
        ("import_scarcity", 1900.0, 75.0),
    ],
    "NEISO": [
        ("HQ_PhaseII", 1000.0, 18.0),
        ("Highgate", 300.0, 22.0),
        ("NB_north", 800.0, 30.0),
        ("NYISO_CT", 1100.0, 36.0),
        ("import_scarcity", 1200.0, 68.0),
    ],
}

IMPORT_TRANCHES_BY_YEAR: dict[str, dict[int, list[tuple[str, float, float]]]] = {
    # CAISO: only the two firm-block capacities vary by year (DMM RA import
    # capacity × MIC corridor share — full derivation in the IMPORT_TRANCHES
    # comment above). Spot tranches and all prices are identical to the static
    # ladder. 2025 firm total carries the 2024 DMM measurement (open data gap
    # until the DMM 2025 annual report publishes).
    "CAISO": {
        2023: [
            ("PNW_hydro_base", 1072.0, 28.0),
            ("PNW_midC", 1800.0, 36.0),
            ("DSW_solar_PV", 1251.0, 48.0),
            ("DSW_CCGT", 1800.0, 68.0),
            ("DSW_CT", 2200.0, 110.0),
            ("WECC_scarcity", 3000.0, 180.0),
        ],
        2024: [
            ("PNW_hydro_base", 1558.0, 28.0),
            ("PNW_midC", 1800.0, 36.0),
            ("DSW_solar_PV", 1813.0, 48.0),
            ("DSW_CCGT", 1800.0, 68.0),
            ("DSW_CT", 2200.0, 110.0),
            ("WECC_scarcity", 3000.0, 180.0),
        ],
        2025: [
            ("PNW_hydro_base", 1566.0, 28.0),
            ("PNW_midC", 1800.0, 36.0),
            ("DSW_solar_PV", 1805.0, 48.0),
            ("DSW_CCGT", 1800.0, 68.0),
            ("DSW_CT", 2200.0, 110.0),
            ("WECC_scarcity", 3000.0, 180.0),
        ],
    },
    "NYISO": {
        2023: [
            ("HQ_hydro", 900.0, 13.0),
            ("IESO_Ontario", 1200.0, 22.5),
            ("PJM_west", 1100.0, 34.2),
            ("ISONE_tie", 800.0, 39.9),
            ("import_scarcity", 1900.0, 68.4),
        ],
        2024: [
            ("HQ_hydro", 900.0, 13.5),
            ("IESO_Ontario", 1200.0, 23.6),
            ("PJM_west", 1100.0, 35.4),
            ("ISONE_tie", 800.0, 44.9),
            ("import_scarcity", 1900.0, 79.7),
        ],
        2025: [
            ("HQ_hydro", 900.0, 20.2),
            ("IESO_Ontario", 1200.0, 37.0),
            ("PJM_west", 1100.0, 49.4),
            ("ISONE_tie", 800.0, 82.6),
            ("import_scarcity", 1900.0, 135.2),
        ],
    },
}

EXPORT_TRANCHES: dict[str, list[tuple[str, float, float]]] = {
    "CAISO": [
        ("export_solar", 2500.0, 8.0),
        ("export_curtail", 4000.0, 0.0),
    ],
    "PJM": [
        ("export_firm", 700.0, 36.0),
        ("export_peak", 1700.0, 30.0),
        ("export_mid", 1700.0, 24.0),
        ("export_shoulder", 1800.0, 19.0),
        ("export_offpeak", 1800.0, 18.0),
        ("export_trough", 2100.0, 16.0),
    ],
    "NYISO": [
        ("export_surplus", 600.0, 10.0),
    ],
    "NEISO": [
        ("export_firm", 700.0, 16.0),
        ("export_trough", 1100.0, 8.0),
    ],
}

# Per-hub external zones and the corridor link each terminates on.
CAISO_PER_HUB_IMPORT_ZONES: dict[str, str] = {
    "MALIN": "WECC_PNW",
    "PALOVRDE": "WECC_DSW",
}

# CAISO import tranche → the WECC neighbor hub.
CAISO_IMPORT_TRANCHE_HUB: dict[str, str] = {
    "PNW_hydro_base": "MALIN",
    "PNW_midC": "MALIN",
    "DSW_solar_PV": "PALOVRDE",
    "DSW_CCGT": "PALOVRDE",
    "DSW_CT": "PALOVRDE",
    "WECC_scarcity": "PALOVRDE",
}

# CISO DIBA → corridor, split geographically at Path-15.
CAISO_CORRIDOR_DIBA: dict[str, str] = {
    "BPAT": "WECC_PNW",
    "PACW": "WECC_PNW",
    "BANC": "WECC_PNW",
    "TIDC": "WECC_PNW",
    "AZPS": "WECC_DSW",
    "SRP": "WECC_DSW",
    "WALC": "WECC_DSW",
    "NEVP": "WECC_DSW",
    "IID": "WECC_DSW",
    "LDWP": "WECC_DSW",
    "CEN": "WECC_DSW",
}

CAISO_CORRIDOR_FLOW_PERCENTILE: float = 95.0

# Strength of the midday solar deliverability derate.
CAISO_CORRIDOR_ATC_SOLAR_K: float = 1.5

# Per-hub external zone → ISO topology links.
IMPORT_NODE_LINKS: dict[str, list[tuple[str, float]]] = {
    "PJM": [
        ("PJM_ComEd", 7500.0),
        ("PJM_AEP_Ohio", 4900.0),
        ("PJM_ATSI", 5800.0),
        ("PJM_Dominion", 6300.0),
        ("PJM_EMAAC", 5700.0),
    ],
    "NYISO": [
        ("Upstate_West", 3000.0),
        ("NYC", 1000.0),
        ("Long_Island", 1200.0),
    ],
    # MISO border links re-pointed at the six-zone refinement: the 7,300 MW
    # eastern (PJM/IESO) seam envelope splits across its three physical border
    # zones — Illinois (ComEd-facing, the heaviest tie set), Indiana
    # (AEP-facing) and East (Michigan↔Ontario, ~2 GW interconnection) — a
    # reconciled split of the same measured 7,300 MW total (rule #12: the
    # seam envelope is measured at BA level, not per model zone; the split
    # follows the physical tie distribution and the per-seam band caps still
    # bound the seam total). West carries the SPP/Manitoba 4,000 MW seam;
    # South keeps its 3,000 MW southern (SOCO/TVA/AECI) seam unchanged.
    "MISO": [
        ("MISO-Illinois", 3300.0),
        ("MISO-Indiana", 2000.0),
        ("MISO-East", 2000.0),
        ("MISO-West", 4000.0),
        ("MISO-South", 3000.0),
    ],
}

# ISOs whose backcasts serve interchange through the priced import/export
# node by default (no --priced-interchange flag required).
PRICED_INTERCHANGE_DEFAULT_ISOS: frozenset[str] = frozenset({"CAISO"})


def resolve_priced_interchange(flag: bool | None, iso: str) -> bool:
    """Resolve the ``--priced-interchange`` tri-state flag for ``iso``."""
    if flag is not None:
        return flag
    return iso in PRICED_INTERCHANGE_DEFAULT_ISOS


# ISOs whose backcasts enable the reference-price interface by default.
REFERENCE_PRICE_DEFAULT_ISOS: frozenset[str] = frozenset({"MISO"})


# NeighborInterface and INTERFACE_NEIGHBORS — moved from constants.py.
@dataclass
class NeighborInterface:
    """One external seam to a neighboring balancing authority.

    Every field is a forecast input (a forward gas/load driver) or a
    physically-pinned structural constant — none is tuned to a
    net-interchange target.
    """

    name: str
    ba_code: str
    gas_basis: float
    marginal_heat_rate: float
    hurdle: float
    interface_limit_mw: float
    border_zones: tuple[str, ...]
    proxy_ba: str | None = None
    load_shape_exponent: float = 1.0
    load_shape_kind: str = "gross"
    import_emission_factor: float | None = None
    hr_by_year: dict[int, float] | None = field(default=None, compare=False)
    firm_export_floor_by_year: dict[int, float] | None = field(
        default=None, compare=False
    )
    firm_import_floor_by_year: dict[int, float] | None = field(
        default=None, compare=False
    )


INTERFACE_NEIGHBORS: dict[str, list[NeighborInterface]] = {
    "PJM": [
        NeighborInterface(
            name="MISO",
            ba_code="MISO",
            gas_basis=0.0,
            marginal_heat_rate=12.9,
            hurdle=1.0,
            interface_limit_mw=7300.0,
            border_zones=("PJM_ComEd", "PJM_AEP_Ohio", "PJM_ATSI"),
            load_shape_exponent=1.60,
            hr_by_year={2023: 12.38, 2024: 13.92, 2025: 12.03},
            firm_export_floor_by_year={2023: 1250.0, 2024: 100.0, 2025: 0.0},
        ),
        NeighborInterface(
            name="NYISO",
            ba_code="NYIS",
            gas_basis=_GAS_BASIS_NYISO,
            marginal_heat_rate=10.4,
            hurdle=1.0,
            interface_limit_mw=3900.0,
            border_zones=("PJM_EMAAC",),
            load_shape_exponent=1.63,
            hr_by_year={2023: 8.65, 2024: 10.85, 2025: 11.59},
            firm_export_floor_by_year={2023: 900.0, 2024: 1400.0, 2025: 1650.0},
        ),
        NeighborInterface(
            name="Carolinas",
            ba_code="DUK",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=1.0,
            interface_limit_mw=2400.0,
            border_zones=("PJM_Dominion",),
            load_shape_exponent=1.60,
        ),
        NeighborInterface(
            name="TVA",
            ba_code="TVA",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=1.0,
            interface_limit_mw=1600.0,
            border_zones=("PJM_AEP_Ohio", "PJM_Dominion"),
            load_shape_exponent=1.60,
        ),
        NeighborInterface(
            name="LGEE",
            ba_code="LGEE",
            proxy_ba="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=11.6,
            hurdle=1.0,
            interface_limit_mw=1100.0,
            border_zones=("PJM_West_APS", "PJM_AEP_Ohio"),
            load_shape_exponent=1.60,
        ),
    ],
    "MISO": [
        NeighborInterface(
            name="PJM",
            ba_code="PJM",
            gas_basis=0.0,
            marginal_heat_rate=12.3,
            hurdle=2.0,
            interface_limit_mw=7300.0,
            border_zones=("MISO-Illinois", "MISO-Indiana", "MISO-East"),
            load_shape_exponent=1.0,
            hr_by_year={2023: 11.2, 2024: 13.49, 2025: 12.18},
            firm_import_floor_by_year={2023: 2615.0, 2024: 1710.0, 2025: 1135.0},
        ),
        NeighborInterface(
            name="SPP",
            ba_code="SWPP",
            gas_basis=0.0,
            marginal_heat_rate=10.0,
            hurdle=2.0,
            interface_limit_mw=4000.0,
            border_zones=("MISO-West",),
            load_shape_exponent=1.0,
            hr_by_year={2023: 9.24, 2024: 10.65, 2025: 7.7},
        ),
        NeighborInterface(
            name="South",
            ba_code="SOCO",
            gas_basis=0.0,
            marginal_heat_rate=12.0,
            hurdle=2.0,
            interface_limit_mw=3000.0,
            border_zones=("MISO-South",),
            load_shape_exponent=1.0,
        ),
    ],
    "CAISO": [
        NeighborInterface(
            name="WECC_DSW",
            ba_code="SRP",
            proxy_ba="CISO",
            gas_basis=0.30,
            marginal_heat_rate=12.97,
            hurdle=4.0,
            interface_limit_mw=10623.0,
            border_zones=("SP15",),
            load_shape_kind="net",
            load_shape_exponent=1.0,
            import_emission_factor=0.37,
            hr_by_year={2023: 17.01, 2024: 13.39, 2025: 8.50},
        ),
        NeighborInterface(
            name="WECC_PNW",
            ba_code="BPAT",
            proxy_ba="CISO",
            gas_basis=-0.30,
            marginal_heat_rate=18.50,
            hurdle=3.0,
            interface_limit_mw=4800.0,
            border_zones=("NP15",),
            load_shape_kind="gross",
            load_shape_exponent=1.0,
            import_emission_factor=0.0,
            hr_by_year={2023: 22.50, 2024: 21.20, 2025: 11.80},
        ),
    ],
}

# MISO per-seam measured BA-to-BA deliverability envelope.
MISO_SEAM_DIBA: dict[str, tuple[str, ...]] = {
    "PJM": ("PJM", "IESO"),
    "SPP": ("SWPP", "SPA"),
    "South": ("SOCO", "TVA", "AECI", "LGEE", "SIKE"),
}

# PJM's MISO-facing western border heat rates (for border_anchor re-anchor).
MISO_PJM_BORDER_HR_BY_YEAR: dict[int, float] = {
    2023: 10.99,
    2024: 12.90,
    2025: 11.40,
}


@dataclass(frozen=True)
class CaisoHubNeighbor:
    """One CAISO WECC import corridor priced as a forward reference-price seam."""

    zone: str
    hub: str
    gas_basis: float
    marginal_heat_rate: float
    load_shape_kind: str
    load_shape_exponent: float
    atc_base_fraction: float
    atc_solar_floor: float


CAISO_PER_HUB_NEIGHBORS: dict[str, CaisoHubNeighbor] = {
    "WECC_PNW": CaisoHubNeighbor(
        zone="WECC_PNW",
        hub="MALIN",
        gas_basis=-0.30,
        marginal_heat_rate=16.0,
        load_shape_kind="gross",
        load_shape_exponent=1.0,
        atc_base_fraction=0.43,
        atc_solar_floor=0.30,
    ),
    "WECC_DSW": CaisoHubNeighbor(
        zone="WECC_DSW",
        hub="PALOVRDE",
        gas_basis=0.30,
        marginal_heat_rate=13.0,
        load_shape_kind="net",
        load_shape_exponent=1.0,
        atc_base_fraction=0.56,
        atc_solar_floor=0.30,
    ),
}


# --- NYISO-specific interchange constants ---

NYISO_FIRM_IMPORT_FLOOR_FRAC: dict[str, float] = {
    "HQ_hydro": 1.0,
    "IESO_Ontario": 0.0,
}

NYISO_IMPORT_RECON_BAND_FRAC: float = 0.02


# --- MISO Manitoba firm-hydro import constants ---

MISO_MANITOBA_FIRM_IMPORT_MW: float = 1400.0
MISO_MANITOBA_FIRM_IMPORT_OFFER: float = 8.0
MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC: float = 1.0
# The Manitoba↔US HVDC / 500 kV ties land in Minnesota (LRZ 1) = MISO-West.
MISO_MANITOBA_FIRM_IMPORT_ZONE: str = "MISO-West"
MISO_MANITOBA_FIRM_IMPORT_NAME: str = "Manitoba_firmhydro"

MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR: dict[int, float] = {
    2023: 726.0,
    2024: 531.0,
    2025: 224.0,
}

MISO_FIRM_IMPORT_DEFAULT_ISOS: frozenset[str] = frozenset({"MISO"})


def resolve_miso_manitoba_firm_import_mw(year: int | None, mode: str) -> float:
    """Return the Manitoba firm-import block capacity (MW) for ``year``/``mode``."""
    if mode == "backcast" and year in MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR:
        return MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR[year]
    return MISO_MANITOBA_FIRM_IMPORT_MW


def resolve_miso_firm_imports(flag: bool | None, iso: str) -> bool:
    """Resolve the ``--miso-firm-imports`` tri-state flag for ``iso``."""
    if flag is not None:
        return flag
    return iso in MISO_FIRM_IMPORT_DEFAULT_ISOS


# ---------------------------------------------------------------------------
# Simultaneous Import/Export Limits (SIL/SEC) — per ISO
# ---------------------------------------------------------------------------
# These cap the total simultaneous flow across ALL external border links of an
# ISO's import/export zone, ensuring aggregate import (or export, when
# bidirectional) does not exceed the receiving (or sending) network's
# simultaneous transfer capability — which is materially less than the sum of
# individual path ratings because the paths share upstream/downstream network
# capacity.  The per-link TTC still binds each individual path; this constraint
# binds only when several paths would load simultaneously past the aggregate
# rating.
#
# Stored as (name, cap_mw, bidirectional) per ISO.  The link references are
# built dynamically from IMPORT_NODE_LINKS by
# :func:`~market_sim.model.transmission.extend_with_import_node`, so they
# always match the border links actually present in the topology.
#
# CAISO's equivalent (``WECC_import_simultaneous``, 7,500 MW) is baked directly
# into ``_caiso_config`` in iso_configs.py.  NEISO's (``HQ_import_simultaneous``,
# 3,850 MW) is baked into ``_neiso_config`` because HQ_import is a baked-in zone.
# ERCOT has no external import zone (DC ties ~1.2 GW embedded in demand).
EXTERNAL_SIMULTANEOUS_LIMITS: dict[str, tuple[str, float, bool]] = {
    # PJM Simultaneous Import Limit.  PJM publishes CETL (Capacity Emergency
    # Transfer Limit) per LDA via the RTEP process and conducts simultaneous-
    # feasibility studies for the RPM Base Residual Auction.  The system-wide
    # aggregate simultaneous import capability is ~10,500 MW — well below the
    # sum of individual seam limits (MISO 7.3 + NYISO 3.9 + Carolinas 2.4 +
    # TVA 1.6 + LGEE 1.1 = 16.3 GW) and far below the border-link TTC sum
    # (30.2 GW), because the western interfaces (AP-South, Bedington-BlackOak)
    # share downstream 500 kV capacity.
    # Source: PJM RTEP Annual Report (CETL tables); PJM Manual 14B §3.3
    # (simultaneous feasibility); RPM Base Residual Auction parameters.
    "PJM": ("PJM_simultaneous_import", 10500.0, True),
    # MISO Capacity Import Limit (CIL).  MISO publishes CIL/CEL with the annual
    # Planning Resource Auction (PRA) via the LOLE study.  The system-wide CIL
    # is ~8,700 MW — below the sum of individual seam limits (PJM 7.3 + SPP 4.0
    # + South 3.0 = 14.3 GW), because the contract-path RDT bottleneck between
    # MISO Midwest and MISO South limits how much of each seam can flow
    # simultaneously.
    # Source: MISO PRA clearing results; MISO LOLE Study Report; MTEP.
    "MISO": ("MISO_simultaneous_import", 8700.0, True),
    # NYISO Simultaneous Import Limit.  NYISO publishes external interface
    # transfer limits via the Gold Book (Load & Capacity Data Report) and the
    # IRM/LCR (Installed Reserve Margin / Locational Capacity Requirement) study.
    # The total simultaneous import capability is ~4,350 MW — below the sum of
    # border-link TTCs (Upstate_West 3.0 + NYC 1.0 + Long_Island 1.2 = 5.2 GW),
    # because the downstate import interfaces (Dunwoodie-South 3.9 GW into NYC,
    # cable-limited 1.65 GW into LI) share upstream transmission.
    # Source: NYISO Gold Book; IRM/LCR studies; NYISO Reliability Needs
    # Assessment; NYISO Comprehensive Reliability Plan.
    "NYISO": ("NYISO_simultaneous_import", 4350.0, True),
}

# Backwards-compatible aliases for the original CAISO-only WECC names.
WECC_IMPORT_TRANCHES: list[tuple[str, float, float]] = IMPORT_TRANCHES["CAISO"]
WECC_EXPORT_CAP_MW: float = EXPORT_TRANCHES["CAISO"][0][1]
WECC_IMPORT_EFORD: float = IMPORT_EFORD["CAISO"]


# ---------------------------------------------------------------------------
# InterchangeSpec dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Corridor:
    """One physical WECC corridor (CAISO per-hub import path).

    Attributes:
        name: Corridor identifier (e.g. ``"WECC_PNW"``).
        zone: External zone hosting the corridor generators.
        import_tranches: ``(name, capacity_mw, marginal_cost)`` ladder.
        export_cap_mw_fn: Returns the export-direction MW bound.
        ttc_mw: Physical line rating (MW).
        carbon_adder: Border carbon per MWh on unspecified imports.
        gas_coupling_fn: Optional callback to shift gas-set import tranches.
        solar_derate_fn: Optional callback returning hourly ATC derate.
    """

    name: str
    zone: str
    import_tranches: list[tuple[str, float, float]]
    export_cap_mw_fn: Callable[[], float] | None = None
    ttc_mw: float = float("inf")
    carbon_adder: float = 0.0
    gas_coupling_fn: Callable | None = None
    solar_derate_fn: Callable | None = None


@dataclass
class FirmImport:
    """A must-flow firm import block (e.g. Manitoba hydro into MISO-West).

    Attributes:
        name: Block name.
        zone: Zone the block lands in.
        capacity_mw: Maximum import MW.
        offer: $/MWh offer price.
        floor_frac: Fraction of capacity forced as must-flow.
    """

    name: str
    zone: str
    capacity_mw: float
    offer: float
    floor_frac: float = 1.0


@dataclass
class ReconciliationBand:
    """Monthly net-interchange reconciliation envelope (NYISO).

    Attributes:
        band_frac: Monthly band half-width as a fraction of net import.
        iso: ISO this applies to.
    """

    band_frac: float
    iso: str = "NYISO"


@dataclass
class InterchangeSpec:
    """Unified interchange specification for one ISO.

    Configures all external seams: static import/export tranches (the
    ``build_import_generators`` / ``build_export_sinks`` path), reference-
    price neighbors, CAISO corridors, firm imports, and monthly reconciliation.

    Attributes:
        iso: ISO identifier.
        import_zone: External zone name.
        import_tranches: Static import supply ladder.
        export_tranches: Static export sink ladder.
        neighbors: Reference-price seam neighbors.
        corridors: CAISO per-hub corridors (empty for non-CAISO).
        firm_imports: Must-flow firm import blocks.
        monthly_reconciliation: Optional monthly band constraint.
        eford: Forced-outage derate on import tranches.
        use_reference_price: Whether to use the reference-price seam.
        use_corridors: Whether to use CAISO corridor model.
    """

    iso: str
    import_zone: str
    import_tranches: list[tuple[str, float, float]] = field(default_factory=list)
    export_tranches: list[tuple[str, float, float]] = field(default_factory=list)
    neighbors: list[NeighborInterface] = field(default_factory=list)
    corridors: list[Corridor] = field(default_factory=list)
    firm_imports: list[FirmImport] = field(default_factory=list)
    monthly_reconciliation: ReconciliationBand | None = None
    eford: float = 0.0
    use_reference_price: bool = False
    use_corridors: bool = False


def get_interchange_spec(config, iso: str) -> InterchangeSpec:
    """Build the ``InterchangeSpec`` for ``iso`` from ``config`` flags.

    Returns a spec that encodes which interchange model is active (static
    tranche ladder, reference-price seam, or CAISO corridor model) based on
    the scenario config flags.  The caller passes this to
    ``build_interchange_fleet`` to get the ``Generator`` list.
    """
    import_zone = IMPORT_ZONE.get(iso, "")
    if not import_zone:
        return InterchangeSpec(iso=iso, import_zone="")

    eford = IMPORT_EFORD.get(iso, 0.0)
    use_ref = (
        getattr(config, "reference_price_interface", False)
        and iso in INTERFACE_NEIGHBORS
    )
    use_corridors = iso == "CAISO" and getattr(config, "caiso_per_hub_intertie", False)

    year = getattr(config, "weather_year", None)
    tranches = IMPORT_TRANCHES.get(iso, [])
    if year is not None:
        tranches = IMPORT_TRANCHES_BY_YEAR.get(iso, {}).get(year, tranches)
    exports = EXPORT_TRANCHES.get(iso, [])

    neighbors = INTERFACE_NEIGHBORS.get(iso, []) if use_ref else []

    corridors: list[Corridor] = []
    if use_corridors:
        from market_sim.model.transmission import (
            wecc_border_carbon_adder,
        )

        border = wecc_border_carbon_adder(getattr(config, "carbon_price", 0.0))
        for hub, zone in CAISO_PER_HUB_IMPORT_ZONES.items():
            hub_tranches = [
                (name, cap, mc)
                for name, cap, mc in tranches
                if CAISO_IMPORT_TRANCHE_HUB.get(name) == hub
            ]
            corridors.append(
                Corridor(
                    name=zone,
                    zone=zone,
                    import_tranches=hub_tranches,
                    carbon_adder=border,
                )
            )

    firm_imports: list[FirmImport] = []
    if getattr(config, "miso_firm_imports", False) and iso == "MISO":
        pmax = resolve_miso_manitoba_firm_import_mw(
            getattr(config, "weather_year", None),
            getattr(config, "mode", "forecast"),
        )
        firm_imports.append(
            FirmImport(
                name=MISO_MANITOBA_FIRM_IMPORT_NAME,
                zone=MISO_MANITOBA_FIRM_IMPORT_ZONE,
                capacity_mw=pmax,
                offer=MISO_MANITOBA_FIRM_IMPORT_OFFER,
                floor_frac=MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC,
            )
        )

    recon = None
    if getattr(config, "nyiso_import_reconciliation", False) and iso == "NYISO":
        recon = ReconciliationBand(
            band_frac=NYISO_IMPORT_RECON_BAND_FRAC,
            iso="NYISO",
        )

    return InterchangeSpec(
        iso=iso,
        import_zone=import_zone,
        import_tranches=tranches if not use_ref else [],
        export_tranches=exports if not use_ref else [],
        neighbors=neighbors,
        corridors=corridors,
        firm_imports=firm_imports,
        monthly_reconciliation=recon,
        eford=eford,
        use_reference_price=use_ref,
        use_corridors=use_corridors,
    )


def build_interchange_fleet(
    spec: InterchangeSpec,
    border_carbon_per_mwh: float = 0.0,
) -> list[Generator]:
    """Build ``Generator`` objects from an ``InterchangeSpec``.

    Produces identical generators to the old ``build_import_generators`` +
    ``build_export_sinks`` / ``build_reference_price_node`` /
    ``build_caiso_per_hub_intertie`` paths, driven by the spec's flags.
    """
    if not spec.import_zone:
        return []

    gens: list[Generator] = []

    if spec.use_reference_price and not spec.use_corridors:
        gens.extend(_build_reference_price_gens(spec))
    elif spec.use_corridors:
        gens.extend(_build_corridor_gens(spec, border_carbon_per_mwh))
    else:
        gens.extend(_build_static_tranche_gens(spec, border_carbon_per_mwh))

    for fi in spec.firm_imports:
        gens.append(
            Generator(
                unit_id=f"{fi.zone}_{fi.name}",
                name=fi.name,
                zone=fi.zone,
                fuel_type="import",
                pmax_mw=fi.capacity_mw,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=fi.offer,
                eford=0.0,
            )
        )

    return gens


def _build_static_tranche_gens(
    spec: InterchangeSpec,
    border_carbon_per_mwh: float,
) -> list[Generator]:
    """Build the static import tranche + export sink generators."""
    zone = spec.import_zone
    ef_map = IMPORT_TRANCHE_EF.get(spec.iso, {})
    gens: list[Generator] = []
    for name, capacity, marginal_cost in spec.import_tranches:
        ef = ef_map.get(name, CARB_UNSPECIFIED_IMPORT_EF)
        tranche_carbon = border_carbon_per_mwh * (ef / CARB_UNSPECIFIED_IMPORT_EF)
        gens.append(
            Generator(
                unit_id=f"{zone}_{name}",
                name=name,
                zone=zone,
                fuel_type="import",
                pmax_mw=capacity,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=marginal_cost + tranche_carbon,
                eford=spec.eford,
            )
        )
    for name, capacity, price in spec.export_tranches:
        gens.append(
            Generator(
                unit_id=f"{zone}_{name}",
                name=name,
                zone=zone,
                fuel_type="import",
                pmax_mw=0.0,
                pmin_mw=-capacity,
                heat_rate=0.0,
                vom=price,
                eford=0.0,
            )
        )
    return gens


def _build_reference_price_gens(spec: InterchangeSpec) -> list[Generator]:
    """Build the reference-price seam import/export pseudo-generators."""
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.transmission import _REF_EXPORT_MARK, _REF_IMPORT_MARK

    gens: list[Generator] = []
    for neighbor in spec.neighbors:
        zone = neighbor.name if spec.iso == "CAISO" else spec.import_zone
        step = neighbor.interface_limit_mw / SEAM_FLOW_TRANCHES
        for k in range(1, SEAM_FLOW_TRANCHES + 1):
            gens.append(
                Generator(
                    unit_id=f"{zone}{_REF_IMPORT_MARK}{neighbor.name}#{k}",
                    name=f"ref_import_{neighbor.name}_t{k}",
                    zone=zone,
                    fuel_type="import",
                    pmax_mw=step,
                    pmin_mw=0.0,
                    heat_rate=0.0,
                    vom=0.0,
                    eford=0.0,
                )
            )
            gens.append(
                Generator(
                    unit_id=f"{zone}{_REF_EXPORT_MARK}{neighbor.name}#{k}",
                    name=f"ref_export_{neighbor.name}_t{k}",
                    zone=zone,
                    fuel_type="import",
                    pmax_mw=0.0,
                    pmin_mw=-step,
                    heat_rate=0.0,
                    vom=0.0,
                    eford=0.0,
                )
            )
    return gens


def _build_corridor_gens(
    spec: InterchangeSpec,
    border_carbon_per_mwh: float,
) -> list[Generator]:
    """Build CAISO's per-hub corridor generators."""
    from market_sim.model.transmission import _caiso_corridor_export_cap_mw

    ef_map = IMPORT_TRANCHE_EF.get(spec.iso, {})
    eford = spec.eford
    _CAISO_PER_HUB_EXPORT_PREFIX = "export"
    gens: list[Generator] = []
    for corridor in spec.corridors:
        for name, capacity, marginal_cost in corridor.import_tranches:
            ef = ef_map.get(name, CARB_UNSPECIFIED_IMPORT_EF)
            tranche_carbon = border_carbon_per_mwh * (ef / CARB_UNSPECIFIED_IMPORT_EF)
            gens.append(
                Generator(
                    unit_id=f"{corridor.zone}_{name}",
                    name=name,
                    zone=corridor.zone,
                    fuel_type="import",
                    pmax_mw=capacity,
                    pmin_mw=0.0,
                    heat_rate=0.0,
                    vom=marginal_cost + tranche_carbon,
                    eford=eford,
                )
            )
        hub = next(
            (h for h, z in CAISO_PER_HUB_IMPORT_ZONES.items() if z == corridor.zone),
            corridor.name,
        )
        gens.append(
            Generator(
                unit_id=f"{corridor.zone}_{_CAISO_PER_HUB_EXPORT_PREFIX}_{hub}",
                name=f"{_CAISO_PER_HUB_EXPORT_PREFIX}_{hub}",
                zone=corridor.zone,
                fuel_type="import",
                pmax_mw=0.0,
                pmin_mw=-_caiso_corridor_export_cap_mw(corridor.zone),
                heat_rate=0.0,
                vom=0.0,
                eford=0.0,
            )
        )
    return gens
