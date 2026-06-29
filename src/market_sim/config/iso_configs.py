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


class InterfaceLimit(BaseModel):
    """An aggregate transfer cap shared across a *group* of links.

    A real interface's *simultaneous* transfer limit is smaller than the sum
    of its component paths' individual ratings: CAISO's published WECC Maximum
    Import Capability is ~8.3 GW, well below Path 66 (COI, 4,800 MW) + Path 46
    (West-of-River, 10,623 MW) ≈ 15.4 GW. ``cap_mw`` bounds the *signed* sum of
    the named links' flows -- the total simultaneous transfer across the
    interface -- while each component link keeps its own per-link TTC. With
    ``bidirectional`` the reverse direction is floored at ``-cap_mw`` too.

    ``links`` lists ``(from_zone, to_zone)`` pairs that must each match an
    existing :class:`TransferLink` (validated in
    :meth:`ISOConfig.validate_topology`); the flows are summed with the links'
    own from→to sign, so links must share an orientation for the sum to read as
    a net interface flow.
    """

    name: str
    links: list[tuple[str, str]]
    cap_mw: float = Field(gt=0.0)
    bidirectional: bool = True


class ISOConfig(BaseModel):
    """Physical topology and economic parameters for one ISO."""

    name: str
    zones: list[Zone]
    links: list[TransferLink]
    voll: float = Field(gt=0.0)
    interface_limits: list[InterfaceLimit] = Field(default_factory=list)
    default_scenario_overrides: dict[str, object] = Field(default_factory=dict)

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
                raise ValueError(f"Link references unknown to_zone '{link.to_zone}'")

        # Aggregate interface limits must reference existing links.
        link_pairs = {(link.from_zone, link.to_zone) for link in self.links}
        for limit in self.interface_limits:
            for pair in limit.links:
                if tuple(pair) not in link_pairs:
                    raise ValueError(
                        f"Interface limit '{limit.name}' references unknown link "
                        f"{tuple(pair)}"
                    )

        total_share = sum(zone.load_share for zone in self.zones)
        if abs(total_share - 1.0) > _LOAD_SHARE_TOL:
            raise ValueError(f"Zone load shares sum to {total_share}, expected 1.0")


def _ercot_config() -> ISOConfig:
    """Build the ERCOT topology configuration.

    The topology is defined by ERCOT's real congestion interfaces rather
    than by settlement pricing areas, so the West and Panhandle wind
    exporters sit behind explicit stability limits and can congest. Load
    shares are derived from ERCOT NP6-345-CD actual load by weather zone
    by aggregating the 8 weather zones onto the 7 transmission zones (the
    EAST weather zone forms its own Northeast zone behind the NE_LOB export
    limit; see below); see scripts/derive_load_shares.py. Panhandle
    carries no modeled load: ERCOT has no Panhandle weather zone, and the
    small Lubbock load it would hold is reported inside the West weather
    zone and therefore currently lands in the West transmission zone.

    These static ``load_share`` values are now only a fallback: when the
    ERCOT native-load file is present (``data/raw/zone-specific-demand/
    ERCOT_Native_Load_<year>.xlsx``), :func:`eia_loader.load_demand` gives each
    zone its *own* measured hourly demand shape via
    :func:`eia_loader.ercot_zonal_load_shares` (zones peak at different hours),
    keyed by the same weather-zone → transmission-zone aggregation. The
    annual-average of those hourly shares reproduces the static shares below to
    within ~1 pt, so the levels are unchanged.
    """
    # Weather zone -> transmission zone: West <- FAR_WEST + WEST;
    # North <- NORTH_C + NORTH; Northeast <- EAST; Houston <- COAST;
    # South_Central <- SOUTH_C; South <- SOUTHERN.
    #
    # North/Northeast re-derived 2026-06 from a clean one-pass EAST->Northeast
    # aggregation in scripts/derive_load_shares.py (North 0.3081->0.3064,
    # Northeast 0.0335->0.0351). The prior values predated the consistent
    # EAST-carve-out; every other zone already matched the script exactly. The
    # unrounded vector sums to 1.0; rounding to 4 dp leaves a 0.0001 residual
    # absorbed into South (true 0.079948 -> 0.0800, largest-remainder) so the
    # literals still sum to exactly 1.0. Fallback-only, so this is low-risk.
    #
    # Northeast is split out of the old North zone to capture the NE_LOB generic
    # transmission constraint -- a ~1,300 MW export limit (binds 17.4% of SCED
    # intervals, 2023-24) on a generation-rich lobe of NE Texas (the EAST weather
    # zone): ~4.2 GW of coal (Martin Lake, Welsh, Pirkey) + ~3.9 GW of gas
    # (Tenaska Gateway CC, Wilkes, ...) serving only ~3.4% of system load. The
    # six-zone model let all of that pour into North as if unconstrained, over-
    # running Martin Lake (PRB) and mis-dispatching the NE CCs; the explicit
    # zone + NE_LOB link makes the trapped-generation congestion physical.
    zones = [
        Zone(name="West", iso="ERCOT", load_share=0.1494),
        Zone(name="Panhandle", iso="ERCOT", load_share=0.0),
        Zone(name="North", iso="ERCOT", load_share=0.3064),
        Zone(name="Northeast", iso="ERCOT", load_share=0.0351),
        Zone(name="Houston", iso="ERCOT", load_share=0.2649),
        Zone(name="South_Central", iso="ERCOT", load_share=0.1642),
        Zone(name="South", iso="ERCOT", load_share=0.0800),
    ]
    # ERCOT zonal transfer capabilities at the major congestion interfaces.
    # Data-first (see claude.md): use the measured GTC limits from the full
    # 2023-2024 NP6-86 SCED binding-constraint archive (202,512 intervals;
    # scripts/derive_ttc_limits.py) wherever the GTC maps cleanly to a model
    # interface.
    #   WESTEX ~10,000 MW (binds 9.3%) -> West export, split West->North +
    #          West->South_Central in the ~8:3 ratio (7,300 / 2,700).
    #   PNHNDL  ~2,680 MW (binds 10.2%) -> Panhandle->North.
    # The West/Panhandle limits are measured and have a NEGLIGIBLE effect on the
    # backcast: an old-estimate (8,900 MW) vs accurate (10,000 MW) West TTC give
    # an identical fuel mix (verified run34 old-TTC vs run37 new-TTC -- both coal
    # 70.4 TWh). So this is pure data-first hygiene, not a calibration lever. (An
    # earlier note here wrongly blamed the West TTC for a coal overshoot; that
    # overshoot is actually the n=6 econ-curve smoothing, see CHANGELOG.)
    #
    # North->Houston is the one carve-out: the single N_TO_H GTC (~4,810 MW,
    # binds 0.21%) is *one of several* parallel 345 kV paths this six-zone
    # reduction collapses into a single link, so using it literally would
    # understate the real interface and is less reflective of reality than the
    # aggregate estimate -- it stays at 8,000 MW. The remaining interior links
    # have no clean zonal-GTC match (ERCOT 2022 Constraints and Needs Report).
    #
    # Caveat: some ERCOT GTCs are intra-zone pockets this topology still cannot
    # represent -- VALEXP (Rio Grande Valley, binds 5.9%), EASTEX (0.5%), TRDWEL
    # (a single line). The biggest one, NE_LOB (NE Texas export, ~1,300 MW, binds
    # 17.4%), is now modeled explicitly as the Northeast->North link below.
    # Sources: ERCOT NP6-86-CD SCED Shadow Prices and Binding Transmission
    # Constraints (2023-2024); ERCOT 2022 Constraints and Needs Report.
    links = [
        TransferLink(from_zone="West", to_zone="North", ttc_mw=7300.0),
        TransferLink(from_zone="West", to_zone="South_Central", ttc_mw=2700.0),
        TransferLink(from_zone="Panhandle", to_zone="North", ttc_mw=2680.0),
        # NE_LOB: the NE-Texas export limit (~1,300 MW, binds 17.4% of 2023-24
        # SCED intervals) capping the trapped Martin Lake / NE-CC lobe.
        TransferLink(from_zone="Northeast", to_zone="North", ttc_mw=1300.0),
        TransferLink(from_zone="North", to_zone="Houston", ttc_mw=8000.0),
        TransferLink(from_zone="North", to_zone="South_Central", ttc_mw=5000.0),
        TransferLink(from_zone="South_Central", to_zone="South", ttc_mw=3000.0),
        TransferLink(from_zone="South_Central", to_zone="Houston", ttc_mw=4000.0),
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

    Load shares apportion CAISO TAC-area demand onto the three hubs: NP15 ≈
    PG&E north of Path 15; ZP26 ≈ the PG&E central San Joaquin Valley between
    Path 15 and Path 26; SP15 ≈ SCE + SDG&E (+ the tiny VEA TAC) south of
    Path 26. Measured from CAISO OASIS ``SLD_FCST`` ACTUAL TAC-area hourly
    load (upload U4, Jan-2023 sample; ``scripts/derive_load_shares.py
    caiso``): PGE-TAC 46.1%, SCE-TAC 44.3%, SDGE-TAC 9.2%, VEA-TAC 0.4% of
    component-TAC load. PGE-TAC straddles Path 15 and is split 0.86/0.14
    between NP15 and ZP26, preserving the prior 0.43:0.07 ratio (no TAC
    boundary exists at Path 15 to measure it; Tier 3 — calibration). Tier 2
    (derived): the sample is one winter month — summer AC load shifts share
    south, so SP15 is likely understated — refresh when the full 2023–25 U4
    pulls land. Hourly *shapes* come from the same file via
    ``eia_loader.caiso_zonal_load_shares``; these static shares are its
    fallback.
    """
    zones = [
        Zone(name="NP15", iso="CAISO", load_share=0.3969),
        Zone(name="ZP26", iso="CAISO", load_share=0.0646),
        Zone(name="SP15", iso="CAISO", load_share=0.5385),
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
    # Aggregate WECC→CAISO import cap. The two import paths' individual ratings
    # are correct, but their SUM (4,800 + 10,623 = 15,423 MW) is NOT the
    # *simultaneous* import capability: COI and the West-of-River corridor draw
    # on overlapping WECC generation and contract paths, so CAISO's deliverable
    # max import is far lower. Without this cap the priced-import supply curve
    # (IMPORT_TRANCHES["CAISO"], 11.4 GW total) clears its full depth in CAISO's
    # tightest hours, putting the modeled deepest-import tail at ~-11.2 GW versus
    # the EIA-930 CISO measured p01 of ~-8.3 GW. The aggregate cap binds the
    # signed sum of the two import-link flows at the measured simultaneous
    # rating, leaving the per-path TTCs intact; the WECC_scarcity import block
    # stays in the merit order but only clears within the cap.
    # Source: CAISO published Maximum Import Capability; EIA-930 CISO
    # net-interchange p01, 2023-25. Tier 3 (calibration) — verify against CAISO
    # OASIS simultaneous import transfer capability.
    interface_limits = [
        InterfaceLimit(
            name="WECC_import_simultaneous",
            links=[("WECC_import", "NP15"), ("WECC_import", "SP15")],
            cap_mw=8300.0,
        ),
    ]
    # CAISO VOLL: $2,000/MWh — represents the CAISO administrative price cap
    # for real-time energy. CAISO's bid cap is lower than ERCOT's because
    # CAISO has capacity-market-like mechanisms (RA program) that provide
    # revenue outside the energy market, so scarcity pricing carries less
    # of the reliability investment signal.
    # ERCOT's $5,000 DA SWCAP is higher because ERCOT is energy-only.
    # Source: CAISO Tariff §39.6.1; ERCOT Protocols §4.4.11.
    return ISOConfig(
        name="CAISO",
        zones=zones,
        links=links,
        voll=2000.0,
        interface_limits=interface_limits,
        # ISO-level scenario defaults applied by the runner when no explicit
        # override is given. CAISO renewables bid below $0 in oversupply
        # (RPS/REC/PTC keep-running value); the mechanism is fully implemented
        # in policy.eac.apply_negative_renewable_offer_floor and tested in
        # tests/test_negative_renewable_offers.py. Currently byte-identical
        # because the model is never long midday — structural correctness,
        # zero risk.
        default_scenario_overrides={
            "negative_renewable_offers": True,
        },
    )


def _miso_config() -> ISOConfig:
    """Build the MISO topology configuration.

    Three regions along MISO's real sub-regional structure, drawn as whole
    EIA-930 sub-BA (LRZ) unions so the load and transmission partitions
    coincide (pipe-and-bubble) — **MISO-North** (the wind-rich upper Midwest:
    LRZ 1 = MN/ND/SD/MT plus LRZ 3+5 = IA/MO), **MISO-Central** (the
    lower-Midwest load centers: LRZ 2+7 = WI/MI, LRZ 4 = IL, LRZ 6 = IN/KY),
    and **MISO-South** (the Entergy footprint AR/LA/MS and East Texas, LRZ
    8+9+10). MISO Midwest (North+Central) and MISO South are two electrically
    separate footprints that connect only through a contract path across SPP,
    so the Central↔South link is the defining MISO constraint.

    Load shares are the static fallback used only when the per-zone hourly
    sub-BA demand file is absent; when present, ``miso_zonal_load_shares``
    gives each zone its own measured 8760 shape. The fallback values are the
    measured 2023–2025 energy shares of the sub-BA groups above
    (0.285/0.444/0.271), which fall out of that same file. The Central region
    carries the populous lower-Midwest load, North the wind belt, and South
    roughly a quarter of the footprint. Source: EIA-930 region-sub-ba-data
    (parent=MISO); see docs/multi-iso/miso-data-audit.md Item 2.
    """
    zones = [
        # Static fallback = measured 2023–2025 sub-BA energy shares (audit Item 2).
        Zone(name="MISO-North", iso="MISO", load_share=0.285),
        Zone(name="MISO-Central", iso="MISO", load_share=0.444),
        Zone(name="MISO-South", iso="MISO", load_share=0.271),
    ]
    # MISO transfer links seeded from the MISO/SPP seams agreement and MTEP.
    #
    # The MISO-Central ↔ MISO-South interface is the Regional Directional
    # Transfer (RDT) contract path: MISO's northern (Midwest) and southern
    # footprints are not directly interconnected and exchange power only over a
    # contract path that wheels across SPP, governed by the RDT limits in the
    # MISO/SPP Joint Operating Agreement. Those limits are explicitly
    # *directional and asymmetric* — 3,000 MW north→south vs 2,500 MW
    # south→north — so the interface is encoded as a PAIR of one-way links
    # (``is_bidirectional=False``, flow in [0, ttc]): Central→South at 3,000 MW
    # and South→Central at 2,500 MW. The LP's net Central↔South interchange is
    # then the difference of the two link flows, reproducing the RDT asymmetry
    # exactly (the old single symmetric 3,000 MW link over-stated south→north
    # transfer by 500 MW). Source: MISO/SPP Joint Operating Agreement, Attach.
    # A — Regional Directional Transfer (RDT) limits (3,000 MW N→S / 2,500 MW
    # S→N); MISO/SPP Coordinated System Plan.
    #
    # The MISO-North ↔ MISO-Central link is the internal Midwest wind-export
    # corridor that moves the wind-rich north's output to the Central load
    # centers. Unlike the RDT seam there is no single posted TTC for this
    # interface: the model's pipe collapses the many parallel 345 kV ties
    # between the upper Midwest (LRZ 1/3/5) and the lower-Midwest load centers
    # (LRZ 2/4/6/7) into one link, whereas MISO posts limits at the flowgate
    # level. Per CLAUDE.md rule #12 the boundary misalignment is documented
    # rather than buried in a false-precision number: the value below is a
    # reconciled aggregate estimate (order-of-magnitude of the summed parallel
    # 345 kV interface, comfortably above North's ~16 GW coincident peak so the
    # north's wind surplus can clear south into Central). DATA NEEDED: the
    # posted MTEP/OASIS firm transfer capability for this interface is an
    # allowlist-blocked pull (misoenergy.org → HTTP 403; see
    # docs/multi-iso/miso-data-audit.md Item 5); replace the estimate with the
    # posted number when the OASIS/MTEP pull is available.
    #
    # Tier 3 (calibration) — verify binding frequency against MISO
    # market/congestion data, but never tune either limit to a price residual.
    links = [
        TransferLink(from_zone="MISO-North", to_zone="MISO-Central", ttc_mw=12000.0),
        # RDT directional asymmetry: a one-way link per direction.
        TransferLink(
            from_zone="MISO-Central",
            to_zone="MISO-South",
            ttc_mw=3000.0,
            is_bidirectional=False,
        ),
        TransferLink(
            from_zone="MISO-South",
            to_zone="MISO-Central",
            ttc_mw=2500.0,
            is_bidirectional=False,
        ),
    ]
    # MISO energy offer cap is $2,000/MWh: FERC Order 831 sets a $2,000/MWh
    # hard cap on incremental energy offers across all RTOs/ISOs (offers above
    # $1,000/MWh must be cost-verified). MISO also runs a seasonal Planning
    # Resource Auction (PRA) capacity construct that provides revenue outside
    # the energy market, so the energy-only VOLL sits below ERCOT's $5,000.
    # No distinct cited MISO VOLL is used here.
    # Source: FERC Order 831; MISO Tariff (energy offer cap).
    return ISOConfig(name="MISO", zones=zones, links=links, voll=2000.0)


def _pjm_config() -> ISOConfig:
    """Build the PJM topology configuration.

    **Eight zones** aligned to PJM's real LDA structure and the locational
    price clusters in the 2024 hub LMPs (cross-hub LMP std ≈ $6.4/MWh), each a
    roll-up of PJM transmission zones (real zone codes in parentheses):

    - **PJM_ComEd** (CE) — northern Illinois. The cheap, *export*-congested
      west (~$24/MWh, congestion −$5).
    - **PJM_AEP_Ohio** (AEP, DAY, DEOK, OVEC) — the central coal belt
      (OH/IN/MI/KY), ~$30/MWh, congestion ≈ 0.
    - **PJM_ATSI** (ATSI) — FirstEnergy northern Ohio / NW Pennsylvania.
    - **PJM_West_APS** (AP, DUQ) — Allegheny Power + Duquesne, western
      PA/WV/western MD. The *import*-congested west (Western Hub ~$33,
      congestion +$1.6); the AP-South / Bedington-BlackOak interfaces bind here.
    - **PJM_Central_PA** (PPL, PENELEC, METED, EKPC) — central/NE Pennsylvania.
    - **PJM_Dominion** (DOM) — Virginia + northern NC. Most import-constrained
      ($34, congestion +$2.5).
    - **PJM_EMAAC** (PSEG, JCPL, PECO, DPL, AECO, RECO) — the eastern
      Mid-Atlantic load pocket (NJ / DE / Philadelphia), electrically islanded
      behind import constraints (Eastern Hub correlates 0.5-0.66 with the rest).
    - **PJM_SWMAAC** (BGE, PEPCO) — Baltimore / DC.

    This replaces the earlier four-zone West/East/Central/South aggregation,
    which collapsed ComEd ($24), AEP ($30) and the import-constrained western
    PA ($33) into one PJM_West holding half the load — washing out the very
    price gradient (across AP-South / Bedington-BlackOak) that binds most.

    Load shares are the eight groups' shares of metered net energy for load
    from the PJM hourly metered-load file (``data/raw/
    zone-specific-demand/PJM2023_hrl_load_metered.csv``, the 20 real zones
    summed over their load areas). Backcasts use that file's *hourly* per-zone
    shape directly (see ``eia_loader``); these annual shares are the fallback /
    topology-sum check. Source: PJM Data Miner hourly metered load.
    """
    zones = [
        Zone(name="PJM_ComEd", iso="PJM", load_share=0.1185),
        Zone(name="PJM_AEP_Ohio", iso="PJM", load_share=0.2178),
        Zone(name="PJM_ATSI", iso="PJM", load_share=0.0844),
        Zone(name="PJM_West_APS", iso="PJM", load_share=0.0785),
        Zone(name="PJM_Central_PA", iso="PJM", load_share=0.1101),
        Zone(name="PJM_Dominion", iso="PJM", load_share=0.1499),
        Zone(name="PJM_EMAAC", iso="PJM", load_share=0.1672),
        # SWMAAC carries the rounding residual so the eight sum to 1.0.
        Zone(name="PJM_SWMAAC", iso="PJM", load_share=0.0736),
    ]
    # Inter-zone TTCs and the link topology trace PJM's real binding interfaces,
    # seeded from the 2024 transfer-limits/flows postings
    # (``data/raw/iso-specific-transmission/
    # PJM_2024_transfer_limits_and_flows.csv``): the most-binding interfaces
    # are AP-South (~3,870-4,453 MW), Bedington-BlackOak (~1,714-1,947 MW) and
    # AEP/DOM (~4,069 MW), all carrying the west/central → east and west →
    # Dominion congestion. The graph is a connected mesh over the west→east
    # gradient; limits not tied to a published interface are order-of-magnitude
    # estimates from the "Average Western/Central/Eastern" envelopes (~5,029 /
    # 3,336 / 8,168 MW). Tier 3 (calibration) — verify/refine against PJM Data
    # Miner interface binding frequency, exactly as ERCOT's WESTEX/PNHNDL
    # limits were derived from SCED binding-constraint data.
    links = [
        # West gradient: ComEd exports east into AEP; the 5004/5005 interface.
        TransferLink(from_zone="PJM_ComEd", to_zone="PJM_AEP_Ohio", ttc_mw=6000.0),
        # AEP coal belt out to ATSI (north), Dominion (south, AEP/DOM) and the
        # western-PA import area.
        TransferLink(from_zone="PJM_AEP_Ohio", to_zone="PJM_ATSI", ttc_mw=4500.0),
        TransferLink(from_zone="PJM_AEP_Ohio", to_zone="PJM_Dominion", ttc_mw=4069.0),
        TransferLink(from_zone="PJM_AEP_Ohio", to_zone="PJM_West_APS", ttc_mw=5029.0),
        # ATSI / West-APS feed central PA.
        TransferLink(from_zone="PJM_ATSI", to_zone="PJM_Central_PA", ttc_mw=3336.0),
        TransferLink(from_zone="PJM_West_APS", to_zone="PJM_Central_PA", ttc_mw=1947.0),
        # AP-South: the western (APS) → eastern Mid-Atlantic 500 kV interface.
        TransferLink(from_zone="PJM_West_APS", to_zone="PJM_SWMAAC", ttc_mw=4453.0),
        TransferLink(from_zone="PJM_West_APS", to_zone="PJM_Dominion", ttc_mw=3000.0),
        # Eastern load pocket: central PA and SWMAAC feed EMAAC; SWMAAC↔Dominion.
        TransferLink(from_zone="PJM_Central_PA", to_zone="PJM_EMAAC", ttc_mw=8168.0),
        TransferLink(from_zone="PJM_SWMAAC", to_zone="PJM_EMAAC", ttc_mw=5000.0),
        TransferLink(from_zone="PJM_SWMAAC", to_zone="PJM_Dominion", ttc_mw=3500.0),
    ]
    # PJM cost-based energy offer cap is $2,000/MWh. PJM's Reliability
    # Pricing Model (RPM) capacity market provides revenue outside energy,
    # so the energy-only VOLL is lower than ERCOT's.
    # Source: PJM Manual 11 §2.3.1, FERC Order 831.
    return ISOConfig(name="PJM", zones=zones, links=links, voll=2000.0)


def _nyiso_config() -> ISOConfig:
    """Build the NYISO topology configuration.

    Five zones aggregate NYISO's eleven load zones (A–K) along the cutsets
    that bound the state's recurring west-to-east and downstate-import
    congestion: **Upstate-West** (A–E), **Capital/Hudson** (F–G),
    **Lower-Hudson** (H–I), **NYC** (J) and **Long Island** (K). This
    preserves the critical downstate import constraints — zones J and K sit
    behind progressively tighter interfaces — while collapsing the eleven
    settlement zones the way ERCOT collapses its real GTCs onto six
    transmission zones.

    Load shares aggregate NYISO zonal load: Upstate-West ≈ A+B+C+D+E,
    Capital/Hudson ≈ F+G, Lower-Hudson ≈ H+I, NYC = J, Long Island = K. New
    York load is heavily downstate — zone J alone is ≈ 28% — so the link
    structure has to carry that load behind the import interfaces. Source:
    NYISO Load & Capacity Data ("Gold Book"), zonal energy/peak by load
    zone. **Tier 3 (calibration)** — static Gold-Book shares are the fallback
    pending upload U3. When ``data/raw/zone-specific-demand/NYISO/
    NYISO_load_actuals_<year>.csv`` is present, :func:`eia_loader.load_demand`
    gives each zone its own measured hourly shape via
    :func:`eia_loader.nyiso_zonal_load_shares` (zones peak at different hours),
    keyed by the A–K → model-zone aggregation. Refresh path: upload NYISO
    OASIS "pal" actual-load CSVs for 2023–2025 (upload manifest U3).
    """
    zones = [
        Zone(name="Upstate_West", iso="NYISO", load_share=0.365),
        Zone(name="Capital_Hudson", iso="NYISO", load_share=0.175),
        Zone(name="Lower_Hudson", iso="NYISO", load_share=0.06),
        Zone(name="NYC", iso="NYISO", load_share=0.28),
        Zone(name="Long_Island", iso="NYISO", load_share=0.12),
    ]
    # NYISO interface transfer limits, seeded from NYISO's published normal
    # transfer limits (Load & Capacity Data "Gold Book" / operating-limit
    # postings). The links trace the north-to-south path the binding
    # interfaces sit on, tightening toward the downstate load pockets:
    #   - Central-East / Total East (Upstate-West -> Capital/Hudson): the
    #     major west-to-east constraint that limits upstate generation —
    #     including the Niagara and St. Lawrence hydro and upstate wind —
    #     from reaching the east. Post-upgrade TTC ~2,850 MW (annual mean
    #     of measured DAM postings, 2024-25); reflects the NY Transco AC
    #     Transmission project (in service Dec 2023) which raised the
    #     Central-East limit from ~1,750 MW. Backcast years apply
    #     year-varying overrides via constants.NYISO_INTERFACE_TTC_BY_YEAR.
    #   - UPNY-SENY (Capital/Hudson -> Lower-Hudson): the Upstate-NY to
    #     Southeast-NY interface, ~5,150 MW.
    #   - Dunwoodie-South (Lower-Hudson -> NYC): the binding import limit
    #     into zone J from the Westchester (Dunwoodie) 345 kV system,
    #     ~3,900 MW.
    #   - Long Island import (NYC -> Long Island): the cable-limited import
    #     into zone K, ~1,650 MW.
    # Source: NYISO Load & Capacity Data ("Gold Book"), interface transfer
    # limits; NYISO Reliability Needs Assessment / locational ICAP studies.
    # Tier 3 (calibration) — verify against NYISO operating-limit postings
    # and binding-frequency from NYISO congestion data.
    links = [
        TransferLink(from_zone="Upstate_West", to_zone="Capital_Hudson", ttc_mw=2850.0),
        TransferLink(from_zone="Capital_Hudson", to_zone="Lower_Hudson", ttc_mw=5150.0),
        TransferLink(from_zone="Lower_Hudson", to_zone="NYC", ttc_mw=3900.0),
        TransferLink(from_zone="NYC", to_zone="Long_Island", ttc_mw=1650.0),
    ]
    # NYISO bid cap is $2,000/MWh for energy. NYISO has an installed
    # capacity market (ICAP) that provides capacity revenue outside the
    # energy market, similar to PJM's RPM and CAISO's RA, so the energy-only
    # VOLL is lower than ERCOT's energy-only $5,000 cap.
    # Source: NYISO Tariff §23.3.1.4, Market Administration and Control
    # Area Services Tariff (MST); FERC Order 831.
    return ISOConfig(name="NYISO", zones=zones, links=links, voll=2000.0)


def _neiso_config() -> ISOConfig:
    """Build the ISO New England topology configuration.

    Four trading zones aggregating ISO-NE's eight load zones along the
    interfaces that bound its recurring congestion — **North** (ME/NH/VT),
    **Central** (WCMA/SEMA/RI), **Boston** (the NEMA load pocket), and
    **Connecticut** (CT) — plus the zero-load ``HQ_import`` node for the
    Hydro-Québec Phase II HVDC tie. This preserves ISO-NE's two structural
    import pockets (Boston and Connecticut) and the North–South interface
    that bounds Maine wind/hydro deliveries to the southern load, mirroring
    the CAISO load-zones-plus-import-node pattern.

    Load shares apportion ISO-NE zonal metered load onto the four zones,
    aggregating the eight ISO-NE load zones:

    - **North** (ME + NH + VT): Maine, New Hampshire, Vermont
    - **Central** (WCMASS + SEMASS + RI): Western/Central MA, SE Mass, Rhode Island
    - **Boston** (NEMA): Northeast Massachusetts, the NEMA/Boston import pocket
    - **Connecticut** (CT): Connecticut

    The static shares (0.20/0.30/0.21/0.29) are seeded from the ISO-NE CELT
    Report and RSP zonal load data. Source: ISO-NE zonal net energy for load by
    load zone. Tier 3 (calibration). **Refresh path (U3):** upload the ISO-NE
    hourly load-zone NEL SMD CSV for 2023–2025 to
    ``data/raw/zone-specific-demand/NEISO/`` and run
    ``scripts/derive_load_shares.py neiso`` to derive measured shares and hourly
    zonal shapes. These static shares are then the fallback for years without a
    zonal file.

    **Net-load convention (playbook §8.1):** EIA-930 ISNE demand is metered at
    the transmission level and is already net of behind-the-meter PV (material
    in MA/CT). Backcasts model only front-of-meter resources. The ``HQ_import``
    node handles HQ Phase II imports as a priced supply node, not load.
    """
    zones = [
        Zone(name="North", iso="NEISO", load_share=0.20),
        Zone(name="Central", iso="NEISO", load_share=0.30),
        Zone(name="Boston", iso="NEISO", load_share=0.21),
        Zone(name="Connecticut", iso="NEISO", load_share=0.29),
        # HQ_import is the priced-import node (Hydro-Québec Phase II HVDC plus
        # the Highgate/NB and NYISO ties added below), not a load zone, so it
        # carries no load. It holds NEISO's import tranches + export sinks
        # (constants.IMPORT_TRANCHES/EXPORT_TRANCHES["NEISO"], P9); the priced
        # supply curve is exercised under --priced-interchange / forward runs.
        Zone(name="HQ_import", iso="NEISO", load_share=0.0),
    ]
    # ISO-NE interface TTCs seeded from the ISO-NE Regional System Plan (RSP)
    # published interface transfer limits:
    #   - North–South ≈ 2,800 MW: the limit on power moving from the northern
    #     (Maine wind/hydro) area into southern New England — the North → Central
    #     link.
    #   - Boston Import ≈ 4,900 MW: the Greater Boston / NEMA import interface
    #     into the Boston load pocket — the Central → Boston link.
    #   - Connecticut Import ≈ 3,500 MW: the import interface into the CT load
    #     pocket — the Central → Connecticut link.
    #   - SEMA/RI Export ≈ 3,150 MW: the limit on surplus generation leaving the
    #     SE-Mass/RI coastal pocket. In this four-load-zone aggregation SEMA/RI
    #     is folded into Central, and SE-Mass/RI sits physically between the
    #     Boston (NEMA) and Connecticut load pockets, so the export interface is
    #     represented as the meshed south-coast corridor it feeds — the
    #     Boston → Connecticut link.
    #   - HQ Phase II ≈ 2,000 MW: the Hydro-Québec Phase II HVDC tie into NEMA
    #     (Sandy Pond) — the HQ_import → Boston link.
    # The pipe-and-bubble LP carries a single symmetric TTC per link
    # (build_variable_bounds bounds flow in [-ttc, +ttc]).
    # Source: ISO-NE Regional System Plan (RSP) interface transfer limits;
    # ISO-NE CELT / operating-limit postings. Tier 3 (calibration) — verify
    # against ISO-NE interface limits and binding-frequency from ISO-NE
    # congestion/shadow-price data.
    links = [
        # North–South interface: Maine wind/hydro → southern load.
        TransferLink(from_zone="North", to_zone="Central", ttc_mw=2800.0),
        # Boston/NEMA import pocket.
        TransferLink(from_zone="Central", to_zone="Boston", ttc_mw=4900.0),
        # Connecticut import pocket.
        TransferLink(from_zone="Central", to_zone="Connecticut", ttc_mw=3500.0),
        # SEMA/RI export corridor (south-coast path between the load pockets).
        TransferLink(from_zone="Boston", to_zone="Connecticut", ttc_mw=3150.0),
        # External-import links out of the HQ_import bubble (the priced-node
        # zone holds NEISO's import tranches + export sinks; P9). Each lands
        # the neighbor blocks at the border zone they physically tie into.
        # The sum (~4.4 GW) envelopes the ~4,386 MW deepest measured 2023
        # import (EIA-930 ISNE). Source: ISO-NE RSP / external-interface
        # ratings. Tier 3 — verify against ISO-NE interface postings.
        #   - HQ Phase II HVDC (Sandy Pond) into NEMA/Boston, ~2,000 MW.
        TransferLink(from_zone="HQ_import", to_zone="Boston", ttc_mw=2000.0),
        #   - Northern import corridor into North: Highgate VT–HQ HVDC
        #     (~225 MW) + the New England–New Brunswick / Maine ties (~675).
        TransferLink(from_zone="HQ_import", to_zone="North", ttc_mw=900.0),
        #   - NYISO ties into Connecticut: Cross-Sound Cable (346 MW) +
        #     Northport–Norwalk (200 MW) + the NY–NE AC interface (~950).
        TransferLink(from_zone="HQ_import", to_zone="Connecticut", ttc_mw=1500.0),
    ]
    # ISO-NE energy offer cap is $2,000/MWh. ISO-NE has a Forward
    # Capacity Market (FCM) providing capacity revenue outside the energy
    # market, so the energy-only VOLL sits below ERCOT's $5,000.
    # Source: ISO-NE Tariff §III.1.10.1A; FERC Order 831.
    return ISOConfig(name="NEISO", zones=zones, links=links, voll=2000.0)


_ISO_BUILDERS = {
    "ERCOT": _ercot_config,
    "CAISO": _caiso_config,
    "MISO": _miso_config,
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
        raise ValueError(f"Unknown ISO '{iso_name}'. Supported ISOs: {supported}")
    config = builder()
    config.validate_topology()
    return config


import csv as _csv
from dataclasses import dataclass

from market_sim.config.paths import REFERENCE_DIR


@dataclass(frozen=True)
class ReliabilityFloorSpec:
    """One temperature- or net-load-driven reliability-commitment floor limb.

    An ISO's floor = a list of limbs in ``RELIABILITY_FLOOR_REGISTRY[iso]``.
    Each limb pins one ``plant_class`` in one ``zone`` at ``floor_pct`` ×
    available capacity for ALL 24 hours of every day its ``driver`` gate is
    flagged (no hour-of-day windows). The day gate is:

    * ``driver="tmax"`` — hot day ⇔ ``tmax_c > threshold`` (°C)
    * ``driver="tmin"`` — cold day ⇔ ``tmin_c < threshold`` (°C)
    * ``driver="netload"`` — high-stress day ⇔ ``net_load_mw > threshold`` (MW)

    ``floor_pct = commit_frac × min_stable_pct`` (a structural commitment share
    times the class's physical minimum-stable level — never a measured-CF
    ceiling; see ``docs/multi-iso/reliability-floor-rebuild-plan.md`` §B.3).
    ``min_event_hours`` (≥ 24) bridges an isolated flagged day to adjacent
    flagged days for steam classes so a committed boiler spans a multi-day
    heat-wave / cold-snap rather than a single calendar day.
    """

    zone: str  # model zone name
    plant_class: str  # plant_group: "ST_GAS", "CT_PEAKER", "COAL", "oil", …
    driver: str  # "tmax" (hot gate) | "tmin" (cold gate) | "netload"
    threshold: float  # °C for tmax/tmin; MW for netload
    floor_pct: float  # = commit_frac × min_stable_pct (see plan §B.3)
    enabled: bool = True  # toggle this exact (iso, zone, class, driver) limb
    min_event_hours: int = 24  # steam-gas event bridging; 24 = single-day
    distribution: str = "cheapest_first"  # "cheapest_first" or "pro_rata"


# Steam classes carry multi-day event bridging by default (a committed boiler
# stays online across a multi-day temperature event); fast-start peakers do not.
_STEAM_CLASSES: frozenset[str] = frozenset({"ST_GAS", "ST_CHP"})
_STEAM_MIN_EVENT_HOURS: int = 48  # bridge an isolated flagged day to neighbours


def _coerce_bool(value: str) -> bool:
    """Parse a CSV truthy string (``"True"``/``"1"``/``"yes"``) to ``bool``."""
    return str(value).strip().lower() in ("true", "1", "yes", "y", "t")


def _load_reliability_floor_registry() -> dict[str, list[ReliabilityFloorSpec]]:
    """Build ``RELIABILITY_FLOOR_REGISTRY`` from per-ISO coefficient CSVs.

    Reads ``data/raw/reference/reliability_floor_coeffs_<ISO>.csv`` (one row per
    (zone, class, driver) limb) for every registered ISO and maps each row to a
    :class:`ReliabilityFloorSpec`. Missing or header-only files yield an empty
    limb list for that ISO — the single source of truth is the CSV, so the
    registry is empty until ``scripts/derive_reliability_coeffs.py`` populates
    the coefficients (Phase 2). Required columns: ``zone, plant_class, driver,
    threshold, floor_pct, enabled``; optional: ``min_event_hours``,
    ``distribution``.
    """
    registry: dict[str, list[ReliabilityFloorSpec]] = {}
    for iso in _ISO_BUILDERS:
        path = REFERENCE_DIR / f"reliability_floor_coeffs_{iso}.csv"
        limbs: list[ReliabilityFloorSpec] = []
        if path.exists():
            with path.open(newline="") as fh:
                for row in _csv.DictReader(fh):
                    if not row.get("zone") or not row.get("plant_class"):
                        continue
                    cls = row["plant_class"].strip()
                    default_event = (
                        _STEAM_MIN_EVENT_HOURS if cls in _STEAM_CLASSES else 24
                    )
                    limbs.append(
                        ReliabilityFloorSpec(
                            zone=row["zone"].strip(),
                            plant_class=cls,
                            driver=row["driver"].strip(),
                            threshold=float(row["threshold"]),
                            floor_pct=float(row["floor_pct"]),
                            enabled=_coerce_bool(row.get("enabled", "True")),
                            min_event_hours=int(row["min_event_hours"])
                            if row.get("min_event_hours")
                            else default_event,
                            distribution=(
                                row.get("distribution") or "cheapest_first"
                            ).strip(),
                        )
                    )
        registry[iso] = limbs
    return registry


# Per-ISO list of (zone, class, driver) reliability-floor limbs, seeded from the
# derived coefficient CSVs (single source of truth). Empty until Phase 2 fills
# the CSVs; the engine no-ops byte-identically when an ISO has no enabled limbs.
RELIABILITY_FLOOR_REGISTRY: dict[str, list[ReliabilityFloorSpec]] = (
    _load_reliability_floor_registry()
)


def apply_reliability_floor_overrides(
    specs: list[ReliabilityFloorSpec],
    overrides: dict[str, dict] | None,
) -> list[ReliabilityFloorSpec]:
    """Return *specs* with per-limb run-config overrides applied.

    *overrides* is keyed ``"<ZONE>:<CLASS>:<driver>"`` →
    ``{"enabled"?: bool, "floor_pct"?: float, "threshold"?: float}`` (matching
    ``ScenarioConfig.reliability_floor_overrides``). Each matching limb is
    replaced via :func:`dataclasses.replace`; unrecognized keys are ignored.
    Returns the input list unchanged when *overrides* is falsy.
    """
    if not overrides:
        return specs
    import dataclasses as _dc

    out: list[ReliabilityFloorSpec] = []
    for spec in specs:
        key = f"{spec.zone}:{spec.plant_class}:{spec.driver}"
        ov = overrides.get(key)
        if not ov:
            out.append(spec)
            continue
        changes = {f: ov[f] for f in ("enabled", "floor_pct", "threshold") if f in ov}
        out.append(_dc.replace(spec, **changes) if changes else spec)
    return out
