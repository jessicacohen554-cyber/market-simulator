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
    """Build the ERCOT topology configuration."""
    zones = [
        Zone(name="North", iso="ERCOT", load_share=0.38),
        Zone(name="South", iso="ERCOT", load_share=0.20),
        Zone(name="West", iso="ERCOT", load_share=0.08),
        Zone(name="Houston", iso="ERCOT", load_share=0.34),
    ]
    # TODO: verify TTCs from ERCOT CDR — values below are placeholders.
    links = [
        TransferLink(from_zone="North", to_zone="South", ttc_mw=5000.0),
        TransferLink(from_zone="North", to_zone="West", ttc_mw=3000.0),
        TransferLink(from_zone="North", to_zone="Houston", ttc_mw=8000.0),
        TransferLink(from_zone="South", to_zone="Houston", ttc_mw=4000.0),
        TransferLink(from_zone="South", to_zone="West", ttc_mw=2000.0),
        TransferLink(from_zone="West", to_zone="Houston", ttc_mw=2500.0),
    ]
    return ISOConfig(name="ERCOT", zones=zones, links=links, voll=5000.0)


def _caiso_config() -> ISOConfig:
    """Build the CAISO topology configuration."""
    zones = [
        Zone(name="CAISO_main", iso="CAISO", load_share=1.0),
        # WECC_import is an import node, not a load zone, so it carries no load.
        Zone(name="WECC_import", iso="CAISO", load_share=0.0),
    ]
    links = [
        TransferLink(
            from_zone="WECC_import", to_zone="CAISO_main", ttc_mw=15000.0
        ),
    ]
    return ISOConfig(name="CAISO", zones=zones, links=links, voll=2000.0)


_ISO_BUILDERS = {
    "ERCOT": _ercot_config,
    "CAISO": _caiso_config,
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
