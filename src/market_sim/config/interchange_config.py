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
#
# PRICE-LADDER PROVENANCE (gap register G-26, issue #1350 / audit C-6): the
# volumes above are measured (DMM RA capacity × MIC split, cited above); the
# $/MWh values are still static-fitted-pending-measured — Tier-3 proxies, not
# a Q-Q derivation of measured flow x hub LMP like MISO_SEAM_LADDER_BY_YEAR /
# the NEISO ladders below. Labelled per rule 24/rule 11 honesty; values
# unchanged.
IMPORT_TRANCHES: dict[str, list[tuple[str, float, float]]] = {
    "CAISO": [
        ("PNW_hydro_base", 1566.0, 28.0),
        ("PNW_midC", 1800.0, 36.0),
        ("DSW_solar_PV", 1805.0, 48.0),
        ("DSW_CCGT", 1800.0, 68.0),
        ("DSW_CT", 2200.0, 110.0),
        ("WECC_scarcity", 3000.0, 180.0),
    ],
    # PJM STATIC tranches (STATIC-FITTED-PENDING-MEASURED, gap register G-26,
    # issue #1350 / audit C-6): these two scarcity-rung tranches are bare
    # literals with no cited primary source and no by-year entry. They serve
    # ONLY the static-node path (reference_price_interface off) — the priced
    # reference seam now has its own measured Q-Q derivation,
    # PJM_SEAM_LADDER_BY_YEAR below (scripts/derive_pjm_seam_ladders.py,
    # 2026-07-10, closing C-6 for PJM's priced path the way
    # MISO_SEAM_LADDER_BY_YEAR / the NEISO ladders closed theirs). Labelled
    # per rule 24/rule 11 honesty; values unchanged.
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
    # NEISO seams (audit C-6 closure, 2026-07-06): measured-data ladders from
    # scripts/derive_neiso_import_tranches.py — per-seam Q-Q duration coupling
    # of the measured ISO-NE DA hub LMP (SMD workbooks) with the measured
    # EIA-930 per-seam flows (ISNE↔HQT/NBSO/NYIS,
    # data/raw/eia-930-interchange/"ISNE interchange hourly.parquet"),
    # anchored on the NYISO proxy-bus DA LBMPs (NYISO_HQ = HQ's measured
    # opportunity cost; NYISO_NPX = the NY-side NY–NE interface price;
    # data/raw/_validation-source/nyiso_proxy_lmp_hourly_NEISO.parquet).
    # Capacities: measured p98 per-seam import depth (Highgate carved at its
    # published ~225 MW converter rating); scarcity rung = p99.9 total-import
    # depth beyond the per-seam rungs. Identification: measured (rule 23 —
    # re-derive only when the source data extends), replacing the
    # residual-fitted rungs the DOF ledger flagged. This static entry is the
    # POOLED 2023-2025 derivation — the multi-year revealed seam supply curve
    # carried forward (HQ water value, NY–NE arbitrage parity, NB surplus);
    # backcast years use IMPORT_TRANCHES_BY_YEAR/EXPORT_TRANCHES_BY_YEAR.
    "NEISO": [
        ("Highgate", 225.0, 26.53),
        ("HQ_PhaseII", 1830.0, 41.10),
        ("NB_north", 630.0, 59.15),
        ("NYISO_CT_base", 870.0, 34.79),
        ("NYISO_CT_peak", 870.0, 73.04),
        ("import_scarcity", 95.0, 286.12),
    ],
}

IMPORT_TRANCHES_BY_YEAR: dict[str, dict[int, list[tuple[str, float, float]]]] = {
    # CAISO: only the two firm-block capacities vary by year (DMM RA import
    # capacity × MIC corridor share — full derivation in the IMPORT_TRANCHES
    # comment above). Spot tranches and all prices are identical to the static
    # ladder. 2025 firm total carries the 2024 DMM measurement (open data gap
    # until the DMM 2025 annual report publishes).
    #
    # PRICE-LADDER PROVENANCE (gap register G-26, issue #1350 / audit C-6):
    # the $/MWh values are STATIC-FITTED-PENDING-MEASURED and identical across
    # all three years — Tier-3 contract-cost proxies, not a measured Q-Q
    # derivation like MISO_SEAM_LADDER_BY_YEAR or the NEISO ladders below.
    # Labelled per rule 24/rule 11 honesty; values unchanged.
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
    # NEISO: year-grounded measured ladders (derivation + sources in the
    # static IMPORT_TRANCHES["NEISO"] comment; scripts/
    # derive_neiso_import_tranches.py). Year texture is real market history:
    # HQ deliveries collapse 10.6 → 2.8 TWh across 2023-2025 as HQ's measured
    # opportunity cost (NYISO_HQ proxy) rises $24.6 → $56.0/MWh, so the
    # HQ_PhaseII rung carries a growing energy-limitation (water-value)
    # premium over the anchor (+$0.1 / +$11.1 / +$51.9); the NYISO_CT rungs
    # bracket the measured NPX parity each year. 2024 has no scarcity rung —
    # the measured p99.9 total import sits within the per-seam p98 rungs.
    "NEISO": {
        2023: [
            ("Highgate", 225.0, 17.00),
            ("HQ_PhaseII", 1595.0, 24.70),
            ("NB_north", 625.0, 35.28),
            ("NYISO_CT_base", 790.0, 31.17),
            ("NYISO_CT_peak", 790.0, 53.81),
            ("import_scarcity", 115.0, 265.42),
        ],
        2024: [
            ("Highgate", 225.0, 22.04),
            ("HQ_PhaseII", 1840.0, 44.22),
            ("NB_north", 605.0, 73.34),
            ("NYISO_CT_base", 870.0, 30.90),
            ("NYISO_CT_peak", 870.0, 51.76),
        ],
        2025: [
            ("Highgate", 225.0, 56.35),
            ("HQ_PhaseII", 1935.0, 107.89),
            ("NB_north", 655.0, 129.96),
            ("NYISO_CT_base", 880.0, 44.48),
            ("NYISO_CT_peak", 880.0, 112.57),
            ("import_scarcity", 105.0, 299.86),
        ],
    },
}

# CAISO and PJM export sinks below are STATIC-FITTED-PENDING-MEASURED (gap
# register G-26, issue #1350 / audit C-6) — bare literals with no cited
# primary source and no by-year entry, unlike the NEISO export ladder in
# EXPORT_TRANCHES_BY_YEAR, which is a measured derivation (same Q-Q method as
# its import-side counterpart). Labelled per rule 24/rule 11 honesty; values
# unchanged.
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
    # NEISO: measured per-seam export sinks (same derivation + sources as
    # IMPORT_TRANCHES["NEISO"]; pooled 2023-2025). Sink prices carry the
    # no-wash clamp (every sink < cheapest import rung − $0.01): the pooled
    # HQ_import node cannot host simultaneous counterflow (wheel-through), so
    # a sink priced above an import rung would be a same-node wash-trade
    # money pump — a documented rule-14 reconciliation of the measured
    # thresholds to the single-node representation.
    "NEISO": [
        ("export_NYISO", 1030.0, 22.30),
        ("export_NB", 380.0, 21.84),
        ("export_HQ", 835.0, 19.86),
    ],
}

# Year-grounded export-sink ladders — the export-side mirror of
# IMPORT_TRANCHES_BY_YEAR, resolved identically (an unmapped ISO/year falls
# back to the static EXPORT_TRANCHES entry). Added 2026-07-06 with the NEISO
# measured seam ladders: the export side has the same real year texture as
# the import side (NEISO's 2025 export_HQ sink is 940 MW where 2023 had no
# measurable HQ export depth at all).
EXPORT_TRANCHES_BY_YEAR: dict[str, dict[int, list[tuple[str, float, float]]]] = {
    # NEISO: derivation + sources in the IMPORT_TRANCHES["NEISO"] comment
    # (scripts/derive_neiso_import_tranches.py). 2023 has no export_HQ sink
    # (no measurable export depth on the HQT seam); sinks clamped by the
    # no-wash ordering where the measured threshold crossed the year's
    # cheapest import rung (2023 export sinks at $16.99 = Highgate $17.00 −
    # $0.01; 2024 export_NB at $22.03 = Highgate $22.04 − $0.01).
    "NEISO": {
        2023: [
            ("export_NYISO", 950.0, 16.99),
            ("export_NB", 180.0, 16.99),
        ],
        2024: [
            ("export_NYISO", 1110.0, 21.37),
            ("export_NB", 455.0, 22.03),
            ("export_HQ", 590.0, 18.06),
        ],
        2025: [
            ("export_NYISO", 1040.0, 27.12),
            ("export_NB", 365.0, 26.02),
            ("export_HQ", 940.0, 28.33),
        ],
    },
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

# Percentile of the measured total CISO corridor net import, per (month ×
# hour-of-day) bucket, defining the SHAPE of the firm/contracted import base
# when ScenarioConfig.caiso_firm_import_shape is on (caiso-73). The MEDIAN is
# the revealed typical-day schedule of the contracted/self-scheduled base —
# robust to scarcity spikes (which belong to the spot tranches) and to outage
# dips. The shape is normalized to unit mean before use
# (eia_loader.measured_firm_import_shape), so this percentile choice sets only
# the profile, never the level — the level stays the published DMM RA-import ×
# MIC-split sizing of IMPORT_TRANCHES_BY_YEAR. Identification: measured
# (rule 23 — re-derives only when the EIA-930 extract extends). Source:
# EIA-930 BA-to-BA interchange, CISO extract.
CAISO_FIRM_IMPORT_SHAPE_PERCENTILE: float = 50.0

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
            # Palo Verde/WOR import terminates on SP15_rest after the 2026-07-09
            # SP15 local-area split (re-pointed off the removed SP15 zone).
            border_zones=("SP15_rest",),
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

# PJM tie line (DataMiner act_sch_interchange ``tie_line``) → priced seam.
# The PJM counterpart of MISO_SEAM_DIBA, at tie level because PJM's canonical
# measured boundary is its own settlement-grade tie-line file
# (data/raw/iso-specific-transmission/PJM_{year}_import_export_act_sch_
# interchange.csv — the file behind eia_loader.pjm_net_interchange and the
# pjm_seam_flow_limit envelopes), not the EIA-930 BA-to-BA product (whose PJM
# submission disagrees with both this meter and the counterparty meters on
# the MISO seam; scripts/derive_pjm_seam_ladders.py BOUNDARY NOTE). Each tie
# maps to the neighbor BA it physically interconnects: the NJ–NY merchant
# HVDC ties (Neptune / Hudson / Linden) pool into the NYISO seam; Duke
# Progress East/West pool with Duke Carolinas; every MISO-member tie —
# including the MECS Michigan interface and the OVEC / LAGN dynamic
# schedules — pools into the MISO seam.
PJM_SEAM_TIE: dict[str, tuple[str, ...]] = {
    "MISO": (
        "ALTE",
        "ALTW",
        "AMIL",
        "CIN",
        "CWLP",
        "IPL",
        "LAGN",
        "MDU",
        "MEC",
        "MECS",
        "NIPS",
        "OVEC",
        "SIGE",
        "WEC",
    ),
    "NYISO": ("NYIS", "NEPT", "HUDS", "LIND"),
    "Carolinas": ("DUK", "CPLE", "CPLW"),
    "TVA": ("TVA",),
    "LGEE": ("LGEE",),
}

# PJM's MISO-facing western border heat rates (for border_anchor re-anchor).
MISO_PJM_BORDER_HR_BY_YEAR: dict[int, float] = {
    2023: 10.99,
    2024: 12.90,
    2025: 11.40,
}

# MISO per-seam measured band-price ladders (audit C-6 closure for MISO;
# gap register G-23 residual "2025 import starvation"): the revealed seam
# supply curve, derived by scripts/derive_miso_seam_ladders.py from two
# measured sources — the EIA-930 MISO BA-to-BA seam flows (pooled onto the
# three priced seams by MISO_SEAM_DIBA) Q-Q duration-coupled with the
# measured MISO Day-Ahead hub LMP (external transactions schedule in the DA
# market). Band k of a seam's import side is priced at the DA quantile whose
# exceedance duration equals the measured duration of the seam flowing
# deeper than the band's midpoint (export side mirrored), on the existing
# SEAM_FLOW_TRANCHES (8) equal-band grid of each seam's interface limit —
# capacities and the measured (month x hour-of-day) deliverability envelopes
# are untouched; ONLY the price ladder is measured.
#
# Why (rule #1 — right market structure): the measured PJM+IESO seam flow is
# a firm/scheduled base (imports in 97.5-99.5% of ALL hours, p10 0.9-1.7 GW,
# hourly flow uncorrelated with the RT spread r=+0.06, 2025 annual RT spread
# $0.00 while 28 TWh flowed) — firm PTP service, grandfathered agreements
# and JOA firm flow entitlements, not spot-spread arbitrage. A hurdle-gated
# gas x HR x load-shape seam structurally deletes that flow in a zero-spread
# year (the miso-45 2025 gross imports 3.4 TWh vs actual net 19.0). The
# ladder encodes the revealed willingness-to-flow as a rising supply curve
# the LP still clears ECONOMICALLY hour by hour against its own internal
# price — nothing is forced (contrast the rejected miso_firm_import_floor
# min_gen pin): at price extremes even the base band backs off, and flows
# respond to changed model conditions.
#
# Identification (rule 23): measured-behaviour, frozen formula, zero fitted
# parameters — re-derives ONLY when the source data extends (a new EIA-930 /
# settlement year). Forward story (rules 12/13): the pooled 2023-2025 ladder
# printed by the derive script is the multi-year revealed seam structure
# (persistent firm-transfer base + arbitrage increment) that regenerates as
# the measured record extends; forecast years keep the gas-elastic
# reference-price formula (the same two-track design as hr_by_year).
#
# Boundary reconciliations (rule 14, documented in the derive script):
# IESO's Ontario tie pools into the PJM seam per MISO_SEAM_DIBA (one eastern
# seam; its surplus-baseload economics land in the cheap base bands); the
# coupling anchor is the MISO hub-mean DA (in-repo canonical), with the PJM
# western-border DA (pjm_border_lmp_hourly_MISO.parquet: $28.86/$28.56/
# $41.45) reported as the interpretability anchor; same-seam no-wash
# ordering (every export band below the seam's cheapest import band) holds
# naturally in all years — cross-seam counterflow (import PJM while
# exporting South) is real wheel-through the multi-link external node
# carries, bounded by the measured per-seam envelopes.
#
# Applied by transmission.inject_miso_seam_ladder_prices under
# ScenarioConfig.miso_seam_measured_ladder (default off, backcast years
# below only); displaces miso_pjm_border_anchor / miso_pjm_lmp_import_pricing
# on the rows it prices (alternatives, never stacked).
MISO_SEAM_LADDER_BY_YEAR: dict[int, dict[str, dict[str, tuple[float, ...]]]] = {
    2023: {
        "PJM": {
            "import": (13.40, 16.25, 19.79, 24.09, 27.86, 32.78, 37.99, 46.55),
            "export": (12.34, 11.72, 11.72, 11.72, 11.72, 11.72, 11.72, 11.72),
        },
        "SPP": {
            "import": (33.03, 44.43, 64.03, 111.92, 177.08, 204.68, 204.68, 204.68),
            "export": (25.00, 20.03, 16.25, 13.59, 12.38, 11.72, 11.72, 11.72),
        },
        "South": {
            "import": (50.99, 63.58, 85.76, 112.47, 204.68, 204.68, 204.68, 204.68),
            "export": (43.04, 36.49, 31.69, 27.69, 24.74, 22.09, 19.70, 17.34),
        },
    },
    2024: {
        "PJM": {
            "import": (14.01, 17.18, 20.92, 24.58, 29.38, 37.03, 50.15, 73.78),
            "export": (11.32, 9.48, 8.43, 8.43, 8.43, 8.43, 8.43, 8.43),
        },
        "SPP": {
            "import": (31.20, 49.28, 116.01, 239.27, 284.59, 284.59, 284.59, 284.59),
            "export": (23.13, 18.85, 16.19, 14.75, 13.39, 12.63, 12.20, 11.73),
        },
        "South": {
            "import": (57.86, 82.81, 163.02, 241.36, 260.66, 284.59, 284.59, 284.59),
            "export": (46.72, 38.67, 32.32, 27.61, 23.77, 20.81, 18.47, 16.00),
        },
    },
    2025: {
        "PJM": {
            "import": (21.82, 25.85, 31.31, 37.36, 46.47, 59.25, 82.59, 121.91),
            "export": (18.36, 16.40, 16.40, 16.40, 16.40, 16.40, 16.40, 16.40),
        },
        "SPP": {
            "import": (40.09, 64.24, 112.65, 198.83, 247.99, 296.90, 310.00, 406.47),
            "export": (28.65, 23.85, 21.43, 19.60, 17.91, 17.34, 16.40, 16.40),
        },
        "South": {
            "import": (68.46, 87.90, 121.12, 155.42, 258.05, 327.25, 433.12, 433.12),
            "export": (53.00, 44.14, 37.04, 32.38, 29.43, 26.61, 24.29, 22.35),
        },
    },
}


# PJM per-seam measured band-price ladders (the MISO/NEISO audit-C-6 pattern
# applied to PJM; pjm-95 C1 root-cause lead "2023 interchange duration miss"):
# the revealed seam supply curve, derived by scripts/derive_pjm_seam_ladders.py
# from two measured sources — PJM's settlement-grade tie-line interchange
# (data/raw/iso-specific-transmission/PJM_{year}_import_export_act_sch_
# interchange.csv, pooled onto the five priced seams by PJM_SEAM_TIE) Q-Q
# duration-coupled with the measured PJM Day-Ahead system LMP
# (actual_lmp_hourly_PJM.parquet; external transactions schedule in the DA
# market). Band k of a seam's import side is priced at the DA quantile whose
# exceedance duration equals the measured duration of the seam flowing deeper
# than the band's midpoint (export side mirrored), on the existing
# SEAM_FLOW_TRANCHES (8) equal-band grid of each seam's interface limit —
# capacities and the measured per-border (month x hour-of-day) deliverability
# envelopes (pjm_seam_flow_limit) are untouched; ONLY the price ladder is
# measured.
#
# Why (rule #1 — right market structure): the measured PJM interchange is
# direction-STRUCTURAL, not spread-driven — PJM exports to MISO/NYISO in
# ~97-100% of ALL hours (2023 import hours 0.4%/0.1%) while importing from
# the south (Carolinas/TVA/LGEE, 77-97% of hours): firm PTP service,
# long-term schedules and JOA entitlements revealed only statistically. The
# hurdle-gated gas x HR x load-shape seam clears on the hourly spot spread
# and structurally inverts that record (pjm-95 2023: imports in 46% of hours
# vs measured ~2%, diurnal corr -0.50 — phantom imports that displace
# CC_REGULAR dispatch, the C1 FAIL). The ladder encodes the revealed
# willingness-to-flow as a rising supply curve the LP still clears
# ECONOMICALLY hour by hour against its own internal price — nothing is
# forced: at price extremes even the base band backs off, and flows respond
# to changed model conditions. Import rungs at the sample extreme (e.g.
# $308.05 = the 2023 DA max) are bands deeper than the measured record's
# deepest flow — effectively never-clearing scarcity rungs, kept so the
# capability exists at the measured price of using it.
#
# Identification (rule 23): measured-behaviour, frozen formula, zero fitted
# parameters — re-derives ONLY when the source data extends (a new tie-line /
# settlement year). Forward story (rules 12/13): the pooled 2023-2025 ladder
# printed by the derive script is the multi-year revealed seam structure
# (persistent firm-transfer base + arbitrage increment) that regenerates as
# the measured record extends; forecast years keep the gas-elastic
# reference-price formula (the same two-track design as hr_by_year).
#
# Boundary reconciliations (rule 14, documented in the derive script):
# the tie-line meter is the chosen boundary (PJM's EIA-930 submission
# disagrees with it AND with the counterparty meters on the MISO seam —
# 56.6 vs 35.3 vs MISO's own 33.5 TWh in 2023; the tie file is the boundary
# the model already uses in pjm_net_interchange and the seam envelopes);
# offline P9 reproduces every seam's measured volume within ±0.06 TWh and
# the import-hour shares (MISO 0-1% vs 0-2% measured). Same-seam no-wash
# ordering holds naturally in all years (no clamp fired); cross-seam
# counterflow (import TVA while exporting MISO) is real wheel-through the
# multi-link external node carries, bounded by the measured envelopes.
#
# Applied by transmission.inject_pjm_seam_ladder_prices under
# ScenarioConfig.pjm_seam_measured_ladder (default off, backcast years below
# only); displaces the firm scheduled-export floor
# (inject_reference_price_firm_export) on the years it covers — the firm
# base the floor pinned is exactly the deep-duration structure the ladder
# prices (alternatives, never stacked; rule 19).
PJM_SEAM_LADDER_BY_YEAR: dict[int, dict[str, dict[str, tuple[float, ...]]]] = {
    2023: {
        "MISO": {
            "import": (140.34, 308.05, 308.05, 308.05, 308.05, 308.05, 308.05, 308.05),
            "export": (72.78, 52.34, 39.12, 31.75, 26.75, 22.22, 18.38, 14.67),
        },
        "NYISO": {
            "import": (308.05, 308.05, 308.05, 308.05, 308.05, 308.05, 308.05, 308.05),
            "export": (86.28, 48.61, 36.0, 31.11, 27.2, 22.58, 18.08, 13.0),
        },
        "Carolinas": {
            "import": (20.51, 24.1, 28.52, 34.07, 41.91, 57.03, 78.04, 260.2),
            "export": (17.62, 15.32, 13.65, 12.06, 10.39, 9.88, 7.68, 7.68),
        },
        "TVA": {
            "import": (15.49, 18.43, 22.09, 26.85, 32.19, 38.54, 49.07, 69.66),
            "export": (13.54, 12.17, 10.95, 10.29, 9.08, 7.68, 7.68, 7.68),
        },
        "LGEE": {
            "import": (21.52, 25.79, 30.44, 36.2, 43.2, 51.02, 61.99, 72.81),
            "export": (17.96, 15.18, 13.58, 11.8, 9.88, 7.68, 7.68, 7.68),
        },
    },
    2024: {
        "MISO": {
            "import": (129.46, 179.14, 276.93, 276.93, 276.93, 276.93, 276.93, 276.93),
            "export": (62.02, 41.54, 31.09, 24.99, 20.26, 16.13, 12.72, 10.47),
        },
        "NYISO": {
            "import": (276.93, 276.93, 276.93, 276.93, 276.93, 276.93, 276.93, 276.93),
            "export": (159.98, 95.88, 52.89, 37.29, 28.63, 21.6, 15.5, 9.73),
        },
        "Carolinas": {
            "import": (17.7, 20.81, 24.67, 30.1, 39.13, 55.25, 94.3, 148.67),
            "export": (15.55, 13.75, 12.5, 11.41, 10.5, 9.59, 8.99, 8.56),
        },
        "TVA": {
            "import": (14.75, 17.31, 20.98, 25.91, 33.2, 43.39, 65.02, 126.63),
            "export": (12.68, 11.45, 10.6, 9.57, 8.65, 7.77, 7.75, 7.75),
        },
        "LGEE": {
            "import": (19.08, 23.53, 28.98, 36.39, 46.87, 59.61, 76.77, 111.23),
            "export": (15.75, 12.67, 10.63, 9.22, 8.65, 7.75, 7.75, 7.75),
        },
    },
    2025: {
        "MISO": {
            "import": (166.87, 384.6, 502.65, 502.65, 502.65, 502.65, 502.65, 502.65),
            "export": (84.96, 55.77, 40.86, 32.7, 27.02, 22.09, 17.85, 14.46),
        },
        "NYISO": {
            "import": (502.65, 502.65, 502.65, 502.65, 502.65, 502.65, 502.65, 502.65),
            "export": (381.93, 178.51, 92.15, 62.13, 44.27, 33.17, 26.61, 19.64),
        },
        "Carolinas": {
            "import": (29.92, 33.71, 38.15, 43.53, 49.96, 58.26, 71.37, 102.29),
            "export": (25.95, 22.74, 20.18, 18.02, 16.13, 15.08, 13.65, 13.0),
        },
        "TVA": {
            "import": (23.84, 28.08, 32.96, 39.08, 46.77, 58.18, 80.86, 126.23),
            "export": (21.09, 18.25, 16.14, 15.08, 13.76, 13.26, 11.65, 11.62),
        },
        "LGEE": {
            "import": (28.93, 34.09, 40.64, 49.81, 63.91, 86.47, 129.98, 259.9),
            "export": (24.18, 20.22, 17.04, 15.08, 13.65, 11.97, 11.88, 11.88),
        },
    },
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
        use_reference_price: Whether the seam is served by the reference-price
            node (``build_reference_price_node``) — the generic non-CAISO seam
            or CAISO's dedicated ``caiso_reference_price_seam``.
        use_corridors: Whether the CAISO per-hub corridor TOPOLOGY is active
            (the ``WECC_import`` node splits into ``WECC_PNW``/``WECC_DSW`` and
            the corridor ATC/flow envelopes may bind). True for both the
            per-hub intertie and the CAISO reference-price seam, matching the
            backcast's ``caiso_corridors`` resolution.
        caiso_mode: Which CAISO seam builder is active — ``"reference_seam"``
            (forward reference-price corridors), ``"per_hub"`` (two signed
            corridors priced at their own hubs), ``"bidir"`` (single signed
            tie), or ``None`` (static tranche ladder / non-CAISO). Resolved
            with the same mutual-exclusion ladder the backcast orchestrator
            has always used: reference seam supersedes per-hub supersedes
            bidir.
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
    caiso_mode: str | None = None
    # MISO only: host the South seam's reference-price bands in their own
    # external zone (constants.MISO_SOUTH_EXTERNAL_ZONE) so they ride the
    # split topology of transmission.split_miso_south_external_node instead
    # of the shared MISO_external bus (which fabricates a free
    # South→external→Midwest wheel around the RDT). Resolved from
    # ScenarioConfig.miso_south_seam_split.
    miso_south_split: bool = False


def get_interchange_spec(config, iso: str, year: int | None = None) -> InterchangeSpec:
    """Build the ``InterchangeSpec`` for ``iso`` from ``config`` flags.

    Returns a spec that encodes which interchange model is active (static
    tranche ladder, reference-price seam, CAISO per-hub / bidirectional
    intertie) based on the scenario config flags.  The caller passes this to
    ``build_interchange_fleet`` to get the ``Generator`` list and to
    ``apply_interchange_topology`` to get the matching topology.

    The CAISO builder choice replicates the backcast orchestrator's
    long-standing mutual-exclusion ladder exactly (all gates are existing
    ``ScenarioConfig`` fields, every one default-off):

    1. ``caiso_reference_price_seam`` — forward reference-price corridors
       (``build_reference_price_node``), per-hub corridor topology.
    2. else ``caiso_per_hub_intertie`` — two signed corridors priced at their
       own hubs (``build_caiso_per_hub_intertie``), per-hub corridor topology.
    3. else ``caiso_bidir_intertie`` — single signed tie
       (``build_caiso_bidir_intertie``), pooled ``WECC_import`` node.
    4. else — static import tranches + export sinks on the pooled node.

    The generic ``reference_price_interface`` path never applies to CAISO
    (CAISO's seam is the dedicated mode-1 above; the generic single-node path
    would land its per-corridor tranches with no corridor zones to host them).

    Args:
        config: Scenario config carrying the interchange gates.
        iso: ISO identifier.
        year: Solve year grounding the year-varying inputs
            (``IMPORT_TRANCHES_BY_YEAR`` ladder, measured Manitoba firm-import
            capacity in backcast mode). ``None`` falls back to
            ``config.weather_year`` — identical in a backcast, where the
            weather year is pinned to the solve year.
    """
    import_zone = IMPORT_ZONE.get(iso, "")
    if not import_zone:
        return InterchangeSpec(iso=iso, import_zone="")

    eford = IMPORT_EFORD.get(iso, 0.0)

    caiso_ref_seam = iso == "CAISO" and getattr(
        config, "caiso_reference_price_seam", False
    )
    caiso_per_hub = (
        (not caiso_ref_seam)
        and iso == "CAISO"
        and getattr(config, "caiso_per_hub_intertie", False)
    )
    caiso_bidir = (
        (not caiso_ref_seam)
        and (not caiso_per_hub)
        and iso == "CAISO"
        and getattr(config, "caiso_bidir_intertie", False)
    )
    caiso_mode = (
        "reference_seam"
        if caiso_ref_seam
        else "per_hub"
        if caiso_per_hub
        else "bidir"
        if caiso_bidir
        else None
    )
    use_ref = caiso_ref_seam or (
        getattr(config, "reference_price_interface", False)
        and iso in INTERFACE_NEIGHBORS
        and iso != "CAISO"
    )
    use_corridors = caiso_per_hub or caiso_ref_seam

    if year is None:
        year = getattr(config, "weather_year", None)
    tranches = IMPORT_TRANCHES.get(iso, [])
    exports = EXPORT_TRANCHES.get(iso, [])
    if year is not None:
        tranches = IMPORT_TRANCHES_BY_YEAR.get(iso, {}).get(year, tranches)
        exports = EXPORT_TRANCHES_BY_YEAR.get(iso, {}).get(year, exports)

    neighbors = INTERFACE_NEIGHBORS.get(iso, []) if use_ref else []

    corridors: list[Corridor] = []
    if use_corridors:
        from market_sim.model.transmission import (
            wecc_border_carbon_adder,
        )

        border = wecc_border_carbon_adder(getattr(config, "carbon_price", 0.0))
        # Informational corridor inventory (zones + per-hub tranche split).
        # The per-hub GENERATORS are built by the canonical
        # transmission.build_caiso_per_hub_intertie, which uses the static
        # IMPORT_TRANCHES ladder (per-tranche capacities are contract
        # structure, not year-shaped) — so the corridor entries here carry the
        # same static split.
        for hub, zone in CAISO_PER_HUB_IMPORT_ZONES.items():
            hub_tranches = [
                (name, cap, mc)
                for name, cap, mc in IMPORT_TRANCHES.get(iso, [])
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
            year,
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
        import_tranches=tranches
        if not (use_ref or use_corridors or caiso_bidir)
        else [],
        export_tranches=exports
        if not (use_ref or use_corridors or caiso_bidir)
        else [],
        neighbors=neighbors,
        corridors=corridors,
        firm_imports=firm_imports,
        monthly_reconciliation=recon,
        eford=eford,
        use_reference_price=use_ref,
        use_corridors=use_corridors,
        caiso_mode=caiso_mode,
        miso_south_split=(
            iso == "MISO"
            and use_ref
            and getattr(config, "miso_south_seam_split", False)
        ),
    )


def build_interchange_fleet(
    spec: InterchangeSpec,
    border_carbon_per_mwh: float = 0.0,
) -> list[Generator]:
    """Build ``Generator`` objects from an ``InterchangeSpec``.

    Delegates to the canonical builders in
    :mod:`market_sim.model.transmission` — the same functions the backcast
    orchestrator has always used inline — selected by the spec's mode flags,
    so both orchestrators produce identical ``Generator`` lists by
    construction:

    * ``use_reference_price`` → :func:`~market_sim.model.transmission.build_reference_price_node`
      (generic non-CAISO seam and CAISO's ``caiso_reference_price_seam``).
    * ``caiso_mode == "per_hub"`` → :func:`~market_sim.model.transmission.build_caiso_per_hub_intertie`.
    * ``caiso_mode == "bidir"`` → :func:`~market_sim.model.transmission.build_caiso_bidir_intertie`.
    * otherwise → the static import-tranche + export-sink ladder (identical to
      ``build_import_generators`` + ``build_export_sinks`` on the spec's
      year-grounded tranches).

    Firm import blocks (``spec.firm_imports``) are appended last, matching the
    backcast construction order and byte-identical to
    :func:`~market_sim.model.transmission.build_miso_firm_imports`.
    """
    if not spec.import_zone:
        return []

    gens: list[Generator] = []

    if spec.use_reference_price:
        from market_sim.model.transmission import build_reference_price_node

        overrides = None
        if spec.miso_south_split:
            from market_sim.config.constants import MISO_SOUTH_EXTERNAL_ZONE

            # The South seam's bands ride the split topology
            # (transmission.split_miso_south_external_node) so they clear in
            # the zone actually linked to MISO-South.
            overrides = {"South": MISO_SOUTH_EXTERNAL_ZONE}
        gens.extend(build_reference_price_node(spec.iso, zone_overrides=overrides))
    elif spec.caiso_mode == "per_hub":
        from market_sim.model.transmission import build_caiso_per_hub_intertie

        gens.extend(build_caiso_per_hub_intertie(border_carbon_per_mwh))
    elif spec.caiso_mode == "bidir":
        from market_sim.model.transmission import build_caiso_bidir_intertie

        gens.extend(build_caiso_bidir_intertie(border_carbon_per_mwh))
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


def apply_interchange_topology(
    iso_config,
    spec: InterchangeSpec,
    config,
    *,
    year: int,
    extend_node: bool = True,
):
    """Apply the spec's interchange topology to ``iso_config``.

    The single topology sequence both orchestrators run, in the order the
    backcast has always used:

    1. ``extend_node`` — append the ISO's external import/export zone + border
       links (:func:`~market_sim.model.transmission.extend_with_import_node`;
       a no-op where the zone is baked in, e.g. CAISO/NEISO).
    2. ``config.capacity_deliverability_limits`` (Part A) — replace the
       calibrated simultaneous-import scalar with the ISO's published per-area
       SEAM import limit (CAISO branch-group MIC → ``WECC_import``), resolved
       for ``year``'s delivery year. No-op when the flag is off (default), the
       ISO publishes no seam ``import_limit``, or the clean data is absent.
    3. ``spec.use_corridors`` — split CAISO's single ``WECC_import`` node into
       the two per-hub corridors and re-home the import links + the
       simultaneous-import interface limit onto them
       (:func:`~market_sim.model.transmission.split_caiso_import_node_per_hub`).
       Applied after step 2 so the seam limit's structural identification
       (every link originates at the import node) matches, and the split then
       re-homes the replaced cap onto the corridor links.
    4. ``config.caiso_asymmetric_path_ratings`` — cap the internal Path 15 /
       Path 26 links at their WECC-accepted directional ratings
       (:func:`~market_sim.model.transmission.apply_caiso_asymmetric_path_limits`).
       Internal links only; applied last so the import-node identification in
       step 2 is untouched. No-op when the flag is off (default).

    Args:
        iso_config: ISO topology (possibly already carrying the import node).
        spec: The ISO's resolved :class:`InterchangeSpec`.
        config: Scenario config (reads ``capacity_deliverability_limits``).
        year: Solve year resolving the deliverability delivery year.
        extend_node: Whether to append the external node. Callers keep their
            existing gate (the forecast runner extends only when the priced
            node has generators; the backcast extends whenever priced
            interchange is on).

    Returns:
        The updated ``iso_config``.
    """
    import logging

    from market_sim.model.transmission import (
        apply_deliverability_seam_limit,
        extend_with_import_node,
        split_caiso_import_node_per_hub,
    )

    logger = logging.getLogger(__name__)
    iso = spec.iso
    if extend_node:
        iso_config = extend_with_import_node(iso_config)
    if getattr(config, "capacity_deliverability_limits", False):
        from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
        from market_sim.data import capacity_deliverability as capdel

        _dy = capdel.resolve_delivery_year(iso, year)
        _season = capdel.resolve_season(iso)
        _imp_area = capdel.import_limit_by_area(iso, _dy, _season)
        _imp_types = capdel.area_types_by_area(iso, _dy, _season, "import_limit")
        _imp_by_zone, _ = aggregate_by_zone(iso, _imp_area, _imp_types)
        _import_zone = IMPORT_ZONE.get(iso)
        _seam_mw = _imp_by_zone.get(_import_zone) if _import_zone else None
        if _seam_mw:
            iso_config = apply_deliverability_seam_limit(iso_config, iso, _seam_mw)
            logger.info(
                "%s %d: capacity_deliverability_limits — seam import cap "
                "set to %.0f MW (summed per-area import_limit, delivery "
                "year %s)",
                iso,
                year,
                _seam_mw,
                _dy,
            )
    if spec.use_corridors:
        iso_config = split_caiso_import_node_per_hub(iso_config)
    # 4. ``config.caiso_asymmetric_path_ratings`` — cap the internal Path 15 /
    #    Path 26 links at their WECC-accepted directional ratings (the baked-in
    #    symmetric TTC is only one direction's rating). Internal links only, so
    #    it composes with the import-node steps above in any order; last keeps
    #    the import-node structural identification in step 2 untouched. No-op
    #    when the flag is off (default) or the ISO carries neither link.
    from market_sim.model.transmission import apply_caiso_asymmetric_path_limits

    iso_config = apply_caiso_asymmetric_path_limits(iso_config, config)
    # 5. ``spec.miso_south_split`` — re-home the MISO-South border link (and
    #    the South seam's SIL member) onto its own external zone, severing the
    #    free South→external→Midwest wheel around the RDT. Needs the import
    #    node from step 1, so it only fires when the node was extended.
    if spec.miso_south_split and iso == "MISO" and extend_node:
        from market_sim.model.transmission import split_miso_south_external_node

        iso_config = split_miso_south_external_node(iso_config)
        logger.info(
            "MISO %d: miso_south_seam_split — South seam re-homed onto its "
            "own external zone (RDT wheel-through bypass severed)",
            year,
        )
    # 6. ``config.miso_rdt_tcdc`` — replace the static JOA-limit RDT pair with
    #    the published 92% default derate + two-step TCDC priced tiers
    #    (transmission.apply_miso_rdt_tcdc). Internal links only, so it
    #    composes with every step above; last keeps the import-node
    #    identification untouched. ``config.miso_rpe_pricing`` rides the same
    #    transform: the RPE constraint's published $200/MWh demand value is
    #    added to both violation tiers (2023-2025 additive pricing, 2024 SOM
    #    §II.E/§III.B) — it has no meaning without the TCDC tiers, so arming
    #    it alone fails loud rather than silently doing nothing.
    rpe_pricing = getattr(config, "miso_rpe_pricing", False)
    if rpe_pricing and iso == "MISO" and not getattr(config, "miso_rdt_tcdc", False):
        raise ValueError(
            "miso_rpe_pricing requires miso_rdt_tcdc: the RPE demand value "
            "prices the RDT violation tiers, which only exist under the "
            "TCDC representation (transmission.apply_miso_rdt_tcdc)"
        )
    if getattr(config, "miso_rdt_tcdc", False) and iso == "MISO":
        from market_sim.model.transmission import apply_miso_rdt_tcdc

        iso_config = apply_miso_rdt_tcdc(iso_config, rpe_pricing=rpe_pricing)
        logger.info(
            "MISO %d: miso_rdt_tcdc — RDT pair replaced with 92%% default "
            "derate + $40/$500 TCDC tiers (2024 SOM §III.B)%s",
            year,
            (
                " + RPE $200 additive on violation tiers "
                "(miso_rpe_pricing, 2024 SOM §II.E/§III.B)"
                if rpe_pricing
                else ""
            ),
        )
    return iso_config
