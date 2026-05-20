"""Per-ISO configuration parameters.

Defines the physical topology (zones and transfer links) for each supported
ISO using Pydantic models, plus a factory for retrieving them by name.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Tolerance for the load-share sum check; absorbs floating-point rounding.
_LOAD_SHARE_TOL = 1e-6


class Zone(BaseModel):
    """A load zone within an ISO."""

    name: str
    iso: str
    load_share: float = Field(ge=0.0, le=1.0)


class TransferLink(BaseModel):
    """A transmission interface connecting two zones.

    ``ttc_mw`` is the total transfer capability across the link.
    """

    from_zone: str
    to_zone: str
    ttc_mw: float = Field(gt=0.0)
    is_bidirectional: bool = True


class ISOConfig(BaseModel):
    """Physical topology and economic parameters for one ISO."""

    name: str
    zones: list[Zone]
    links: list[TransferLink]
    voll: float = Field(gt=0.0)

    @property
    def n_zones(self) -> int:
        """Number of zones in the ISO."""
        return len(self.zones)

    @property
    def zone_names(self) -> list[str]:
        """Names of all zones in the ISO."""
        return [zone.name for zone in self.zones]

    @property
    def n_links(self) -> int:
        """Number of transfer links in the ISO."""
        return len(self.links)

    def validate_topology(self) -> None:
        """Check topological consistency of the configuration.

        Raises:
            ValueError: if a link references an unknown zone, or if the
                zone load shares do not sum to 1.0.
        """
        valid_zones = set(self.zone_names)
        for link in self.links:
            if link.from_zone not in valid_zones:
                raise ValueError(
                    f"Link references unknown from_zone '{link.from_zone}'"
                )
            if link.to_zone not in valid_zones:
                raise ValueError(
                    f"Link references unknown to_zone '{link.to_zone}'"
                )

        total_share = sum(zone.load_share for zone in self.zones)
        if abs(total_share - 1.0) > _LOAD_SHARE_TOL:
            raise ValueError(
                f"Zone load shares sum to {total_share}, expected 1.0"
            )


def _ercot_config() -> ISOConfig:
    """Build the ERCOT topology configuration.

    The topology is defined by ERCOT's real congestion interfaces rather
    than by settlement pricing areas, so the West and Panhandle wind
    exporters sit behind explicit stability limits and can congest. Load
    shares are derived from ERCOT NP6-345-CD actual load by weather zone
    (19 sample days spanning 2023, at least one per month) by aggregating
    the 8 weather zones onto the 6 transmission zones; see
    scripts/derive_load_shares.py. Panhandle
    carries no modeled load: ERCOT has no Panhandle weather zone, and the
    small Lubbock load it would hold is reported inside the West weather
    zone and therefore currently lands in the West transmission zone.
    """
    # Weather zone -> transmission zone: West <- FAR_WEST + WEST;
    # North <- NORTH_C + EAST + NORTH; Houston <- COAST;
    # South_Central <- SOUTH_C; South <- SOUTHERN.
    zones = [
        Zone(name="West", iso="ERCOT", load_share=0.1494),
        Zone(name="Panhandle", iso="ERCOT", load_share=0.0),
        Zone(name="North", iso="ERCOT", load_share=0.3416),
        Zone(name="Houston", iso="ERCOT", load_share=0.2649),
        Zone(name="South_Central", iso="ERCOT", load_share=0.1642),
        Zone(name="South", iso="ERCOT", load_share=0.0799),
    ]
    # ERCOT zonal transfer capabilities, defined at the major congestion
    # interfaces. The West and Panhandle export limits are the mean observed
    # limits of the WESTEX and PNHNDL generic transmission constraints in
    # ERCOT NP6-86 SCED binding-constraint data (Oct 2023, 8,709 intervals;
    # see scripts/derive_ttc_limits.py). WESTEX averaged 8,895 MW, split
    # West->North + West->South_Central in the prior ~8:3 ratio; PNHNDL
    # averaged 2,673 MW. Both bind in 43-59% of intervals. Remaining TTCs
    # are estimates from the ERCOT 2022 Report on Existing and Potential
    # Electric System Constraints and Needs (top-10 congestion interfaces).
    # Sources: ERCOT NP6-86-CD SCED Shadow Prices and Binding Transmission
    # Constraints; ERCOT 2022 Constraints and Needs Report.
    links = [
        TransferLink(from_zone="West", to_zone="North", ttc_mw=6500.0),
        TransferLink(from_zone="West", to_zone="South_Central", ttc_mw=2400.0),
        TransferLink(from_zone="Panhandle", to_zone="North", ttc_mw=2700.0),
        TransferLink(from_zone="North", to_zone="Houston", ttc_mw=8000.0),
        TransferLink(from_zone="North", to_zone="South_Central", ttc_mw=5000.0),
        TransferLink(
            from_zone="South_Central", to_zone="South", ttc_mw=3000.0
        ),
        TransferLink(
            from_zone="South_Central", to_zone="Houston", ttc_mw=4000.0
        ),
        TransferLink(from_zone="South", to_zone="Houston", ttc_mw=2000.0),
    ]
    # ERCOT VOLL: $5,000/MWh — matches the day-ahead system-wide offer cap.
    # Post-RTC+B (Dec 5, 2025): DA SWCAP remains $5,000; RT SWCAP is $2,000.
    # PUCT also set an administrative VOLL of $35,000 for planning (Aug 2024).
    # This LP uses a single VOLL representing the DA energy-only cap.
    # Source: PUCT §25.505, ERCOT Nodal Protocols §4.4.11 (post-RTC+B).
    return ISOConfig(name="ERCOT", zones=zones, links=links, voll=5000.0)


def _caiso_config() -> ISOConfig:
    """Build the CAISO topology configuration.

    Three trading zones along CAISO's real north–south split — **NP15**
    (north of Path 15), **ZP26** (between Path 15 and Path 26), **SP15**
    (south of Path 26) — plus the ``WECC_import`` node for the rest of the
    WECC. These mirror CAISO's congestion-revenue-rights trading hubs and
    the Path 15 / Path 26 interties that bound the state's recurring
    north–south congestion.

    Load shares apportion CAISO TAC-area demand (PG&E / SCE / SDG&E) onto the
    three hubs: NP15 ≈ PG&E north of Path 15; ZP26 ≈ the PG&E central San
    Joaquin Valley between Path 15 and Path 26; SP15 ≈ SCE + SDG&E south of
    Path 26. Source: CAISO demand by TAC area (CAISO OASIS / Annual Report on
    Market Issues & Performance). Tier 3 (calibration) — verify against
    metered TAC-area load.
    """
    zones = [
        Zone(name="NP15", iso="CAISO", load_share=0.43),
        Zone(name="ZP26", iso="CAISO", load_share=0.07),
        Zone(name="SP15", iso="CAISO", load_share=0.50),
        # WECC_import is an import node, not a load zone, so it carries no load.
        Zone(name="WECC_import", iso="CAISO", load_share=0.0),
    ]
    # CAISO intertie TTCs seeded from the WECC Path Rating Catalog. Path 15
    # (Los Banos–Gates) is rated 5,400 MW N→S after the 2004 third-line
    # upgrade; Path 26 (Midway–Vincent) is rated 4,000 MW N→S. The WECC
    # import splits across the two major intertie groups: Path 66 / COI
    # (California–Oregon Intertie) ~4,800 MW into NP15 to the north, and
    # Path 46 / West of the River ~10,623 MW E→W into SP15 to the south
    # (the Palo Verde / WOR corridor). The two import links sum to ~15,400
    # MW, consistent with the 15,000 MW WECC import supply curve.
    # Source: WECC Path Rating Catalog (Path 15, Path 26, Path 46, Path 66).
    # Tier 3 (calibration) — verify against CAISO OASIS transfer capabilities
    # and binding-frequency from CAISO congestion/shadow-price data.
    links = [
        # Path 15: NP15 ↔ ZP26 (Los Banos–Gates).
        TransferLink(from_zone="NP15", to_zone="ZP26", ttc_mw=5400.0),
        # Path 26: ZP26 ↔ SP15 (Midway–Vincent) — the dominant N–S intertie,
        # completing the NP15 ↔ SP15 corridor through ZP26.
        TransferLink(from_zone="ZP26", to_zone="SP15", ttc_mw=4000.0),
        # Path 66 / COI: WECC import into NP15 (north).
        TransferLink(from_zone="WECC_import", to_zone="NP15", ttc_mw=4800.0),
        # Path 46 / West of the River: WECC import into SP15 (south).
        TransferLink(from_zone="WECC_import", to_zone="SP15", ttc_mw=10623.0),
    ]
    # CAISO VOLL: $2,000/MWh — represents the CAISO administrative price cap
    # for real-time energy. CAISO's bid cap is lower than ERCOT's because
    # CAISO has capacity-market-like mechanisms (RA program) that provide
    # revenue outside the energy market, so scarcity pricing carries less
    # of the reliability investment signal.
    # ERCOT's $5,000 DA SWCAP is higher because ERCOT is energy-only.
    # Source: CAISO Tariff §39.6.1; ERCOT Protocols §4.4.11.
    return ISOConfig(name="CAISO", zones=zones, links=links, voll=2000.0)


def _pjm_config() -> ISOConfig:
    """Build the PJM topology configuration."""
    # PJM load shares by state group — approximate, derived from PJM
    # 2024 State of the Market Report zonal load data.
    # West (IL+IN+OH+MI): ~37% of PJM peak
    # Central (PA+WV+KY): ~28%
    # East (NJ+DE+MD+DC): ~20%
    # South (VA+NC+TN): ~15%
    # Source: Monitoring Analytics, 2024 State of the Market Report,
    # Table 7-2: PJM Zonal Peak Loads.
    # Tier: 3 (calibration)
    # TODO: verify from PJM load data download
    zones = [
        Zone(name="PJM_West", iso="PJM", load_share=0.37),
        Zone(name="PJM_Central", iso="PJM", load_share=0.28),
        Zone(name="PJM_East", iso="PJM", load_share=0.20),
        Zone(name="PJM_South", iso="PJM", load_share=0.15),
    ]
    # Major transmission interfaces in PJM:
    # West→Central: AEP-DOM, AP South interfaces (~8-10 GW)
    # Central→East: Western/Central PA to NJ/DE/MD (~7-8 GW)
    # South→Central: Dominion to PJM Classic (~5 GW)
    # West→South: AEP to Dominion (~4 GW)
    # Source: PJM Regional Transmission Expansion Plan (RTEP) 2024.
    # TODO: verify TTCs from PJM OASIS — values below are placeholders
    # based on published flowgate ratings.
    links = [
        TransferLink(from_zone="PJM_West", to_zone="PJM_Central", ttc_mw=10000.0),
        TransferLink(from_zone="PJM_Central", to_zone="PJM_East", ttc_mw=8000.0),
        TransferLink(from_zone="PJM_South", to_zone="PJM_Central", ttc_mw=5000.0),
        TransferLink(from_zone="PJM_West", to_zone="PJM_South", ttc_mw=4000.0),
        TransferLink(from_zone="PJM_South", to_zone="PJM_East", ttc_mw=3000.0),
    ]
    # PJM cost-based energy offer cap is $2,000/MWh. PJM's Reliability
    # Pricing Model (RPM) capacity market provides revenue outside energy,
    # so the energy-only VOLL is lower than ERCOT's.
    # Source: PJM Manual 11 §2.3.1, FERC Order 831.
    return ISOConfig(name="PJM", zones=zones, links=links, voll=2000.0)


def _nyiso_config() -> ISOConfig:
    """Build the NYISO topology configuration."""
    zones = [
        Zone(name="NYISO_main", iso="NYISO", load_share=1.0),
    ]
    links: list[TransferLink] = []
    # NYISO bid cap is $2,000/MWh for energy. NYISO has an installed
    # capacity market (ICAP) that provides capacity revenue outside
    # the energy market, similar to PJM's RPM.
    # Source: NYISO Tariff §23.3.1.4, Market Administration and Control
    # Area Services Tariff (MST).
    return ISOConfig(name="NYISO", zones=zones, links=links, voll=2000.0)


def _neiso_config() -> ISOConfig:
    """Build the ISO New England topology configuration."""
    zones = [
        Zone(name="NEISO_main", iso="NEISO", load_share=1.0),
    ]
    links: list[TransferLink] = []
    # ISO-NE energy offer cap is $2,000/MWh. ISO-NE has a Forward
    # Capacity Market (FCM) providing capacity revenue.
    # Source: ISO-NE Tariff §III.1.10.1A.
    return ISOConfig(name="NEISO", zones=zones, links=links, voll=2000.0)


_ISO_BUILDERS = {
    "ERCOT": _ercot_config,
    "CAISO": _caiso_config,
    "PJM": _pjm_config,
    "NYISO": _nyiso_config,
    "NEISO": _neiso_config,
}


def get_iso_config(iso_name: str) -> ISOConfig:
    """Return the :class:`ISOConfig` for the named ISO.

    Args:
        iso_name: ISO identifier (case-insensitive), e.g. ``"ERCOT"``.

    Returns:
        The validated :class:`ISOConfig` for the requested ISO.

    Raises:
        ValueError: if ``iso_name`` is not a supported ISO.
    """
    builder = _ISO_BUILDERS.get(iso_name.upper())
    if builder is None:
        supported = ", ".join(sorted(_ISO_BUILDERS))
        raise ValueError(
            f"Unknown ISO '{iso_name}'. Supported ISOs: {supported}"
        )
    config = builder()
    config.validate_topology()
    return config
