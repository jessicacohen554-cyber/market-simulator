"""Per-ISO configuration parameters.

Defines the physical topology (zones and transfer links) for each supported
ISO using Pydantic models, plus a factory for retrieving them by name.
"""

from __future__ import annotations

import csv as _csv
from dataclasses import dataclass

from pydantic import BaseModel, Field

from market_sim.config.paths import REFERENCE_DIR

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

    ``links`` lists ``(from_zone, to_zone)`` pairs; each pair must connect two
    zones joined by at least one :class:`TransferLink` in either orientation
    (validated in :meth:`ISOConfig.validate_topology`). The *listed* orientation
    defines the group's positive flow direction: every link between the pair's
    zones is summed with sign ``+1`` when its own from→to matches the listed
    orientation and ``-1`` when reversed, so the sum always reads as the net
    corridor flow in the listed direction (a one-way link pair such as MISO's
    RDT contributes ``flow(a→b) − flow(b→a)`` from a single listed pair).

    ``reverse_cap_mw`` sets an *asymmetric* reverse-direction cap: the signed
    sum is bounded in ``[-reverse_cap_mw, cap_mw]`` (overriding
    ``bidirectional``). Used for per-zone directional deliverability groups
    whose import limit (MISO CIL) and export limit (CEL) differ; ``None``
    (default) keeps the symmetric/one-sided ``bidirectional`` behaviour.
    """

    name: str
    links: list[tuple[str, str]]
    cap_mw: float = Field(gt=0.0)
    bidirectional: bool = True
    reverse_cap_mw: float | None = Field(default=None, gt=0.0)


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

        # Aggregate interface limits must reference connected zone pairs (a
        # pair is valid when at least one TransferLink joins its two zones in
        # either orientation; the listed orientation only fixes the flow sign).
        link_pairs = {(link.from_zone, link.to_zone) for link in self.links}
        for limit in self.interface_limits:
            for pair in limit.links:
                a, b = tuple(pair)
                if (a, b) not in link_pairs and (b, a) not in link_pairs:
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
    :func:`eia_loader.load_zonal_shares` (zones peak at different hours),
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
    return ISOConfig(
        name="ERCOT",
        zones=zones,
        links=links,
        voll=5000.0,
        # ERCOT is energy-only (no capacity market), so it is the one ISO
        # whose published ORDC scarcity adder belongs in capacity economics
        # by default; see scarcity_price_overlay on ScenarioConfig. Still
        # requires scarcity_pricing_enabled (the master switch) to be set by
        # the caller — this default only preserves ERCOT's prior
        # `iso == "ERCOT"` behavior once that switch is on.
        default_scenario_overrides={
            "scarcity_price_overlay": True,
        },
    )


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
    ``eia_loader.load_zonal_shares``; these static shares are its
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
    # the EIA-930 CISO measured p01 of ~-8.3 GW. Tightened from 8,300 (raw p01)
    # to 7,500 MW: the p01 extreme rarely sustains across both corridors
    # simultaneously (overlapping WECC source generation); 7,500 is closer to
    # the sustained p05 simultaneous capability. The CAISO RA summer import
    # assumption is 5,500 MW, further supporting that 8,300 over-allocates.
    # Source: CAISO published Maximum Import Capability (11,665 MW non-peak);
    # CAISO RA 5,500 MW summer peak; EIA-930 CISO net-interchange 2023-25.
    # Tier 3 (calibration).
    #
    # NOTE (audit item C-5, resolved in the caiso-51 keeper — 2026-07-03;
    # docs/caiso-c5-wecc-cap-closeout-2026-07-03.md): this 7,500 MW value is a
    # fitted scalar. It is SUPERSEDED in the caiso-51 backcast keeper, where
    # `capacity_deliverability_limits` replaces it with the published branch-group
    # MIC seam limit (16,055/16,452/16,148 MW for 2023/24/25) and measured p95
    # corridor deliverability envelopes (`caiso_corridor_flow_limit`) bind tighter.
    # It is retained here (not deleted) because it remains the default cap for runs
    # with `capacity_deliverability_limits` OFF (forecast mode; the flag is GATED
    # default-off) and is preserved/re-homed by `split_caiso_import_node_per_hub`.
    # Re-grounding the forecast-path default on the published MIC/SIL is open item
    # O-1 (forecast/backcast parity), tracked in issue #1373 and carried as a
    # fallback-only DOF-ledger row (scalar-remediation B-CAI-1, 2026-07-05) so
    # this fallback cannot silently re-become the binding import limit.
    # Do not re-tune this value to the residual.
    interface_limits = [
        InterfaceLimit(
            name="WECC_import_simultaneous",
            links=[("WECC_import", "NP15"), ("WECC_import", "SP15")],
            cap_mw=7500.0,
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

    **Six zones**, drawn as whole EIA-930 sub-BA (LRZ) unions — the finest
    partition with fully measured hourly load — so the fleet and load
    partitions share identical boundaries (pipe-and-bubble; see
    docs/multi-iso/miso-zonal-refinement-scope.md §1):

    - **MISO-West** (LRZ 1 / sub-BA ``0001``: MN, ND, SD, MT) — the wind belt
      behind the MN/ND export interfaces; heavily import-constrained at peak.
    - **MISO-Plains** (LRZ 3+5 / ``0035``: IA, MO) — the Iowa wind-export
      corridor into the eastern load centers.
    - **MISO-Illinois** (LRZ 4 / ``0004``: IL, Ameren) — the W→E wheel-through
      zone; Illinois Hub is MISO's price reference.
    - **MISO-Indiana** (LRZ 6 / ``0006``: IN, KY) — the load-east anchor
      hosting Michigan's import path.
    - **MISO-East** (LRZ 2+7 / ``0027``: WI, MI) — the Michigan import pocket
      + WUMS, the strongest import-constrained pocket in MISO Midwest.
    - **MISO-South** (LRZ 8+9+10 / ``8910``: AR, LA, MS, East TX) — the
      Entergy footprint, unchanged; electrically separate from Midwest and
      connected only over the RDT contract path across SPP.

    The former 3-zone build (MISO-North/MISO-Central/MISO-South) was a
    copperplate — all three zones priced identically in all 8,760 hours — so
    the Midwest was split to the six measured sub-BA groups. The retired
    names ``MISO-North``/``MISO-Central`` must NOT be reused (stale-parquet /
    stale-CSV zero-fill hazard; scope doc §5).

    Load shares are the static fallback used only when the per-zone hourly
    sub-BA demand parquet is absent; when present, ``load_zonal_shares``
    gives each zone its own measured 8760 shape. The fallback values are the
    measured 2023–2025 energy shares of the six sub-BA groups. Source:
    EIA-930 region-sub-ba-data (parent=MISO); docs/multi-iso/
    miso-data-audit.md Item 2.

    Congestion structure (scope doc §2): the six internal bilateral links
    carry deliberately *non-binding* placeholder TTCs; all internal Midwest
    congestion is carried by the per-zone directional CIL/CEL interface
    groups below plus the RDT one-way pair. Decomposing a zone's CIL into
    per-link bilateral TTCs would be an invented apportionment, so the
    published per-zone limits are applied as exactly the quantity the LOLE
    transfer analysis measures — a cap on the zone's total simultaneous
    import (CIL) and export (CEL).
    """
    zones = [
        # Static fallback = measured 2023–2025 sub-BA energy shares
        # (EIA-930 region-sub-ba-data; scope doc §1, sum = 1.0000).
        Zone(name="MISO-West", iso="MISO", load_share=0.1466),
        Zone(name="MISO-Plains", iso="MISO", load_share=0.1385),
        Zone(name="MISO-Illinois", iso="MISO", load_share=0.0676),
        Zone(name="MISO-Indiana", iso="MISO", load_share=0.1340),
        Zone(name="MISO-East", iso="MISO", load_share=0.2422),
        Zone(name="MISO-South", iso="MISO", load_share=0.2711),
    ]
    # Internal Midwest bilateral links (L1–L6, scope doc §2.2): a light mesh
    # following the physical 345 kV tie structure. Each ``ttc_mw`` is a
    # deliberately GENEROUS, non-binding placeholder — about 2× the largest
    # max-seasonal member-CIL sum in the footprint (MISO-Plains fall PY2023-24,
    # LRZ 3+5 ≈ 19.8 GW) — because no single posted bilateral TTC exists at
    # these boundaries (MISO posts flowgate-level limits). All congestion is
    # instead carried by the cited per-zone CIL/CEL interface groups below
    # (rule #10 admissibility: LOLE CIL/CEL regenerate every planning year
    # from forward drivers). This retires the old reconciled 12,000 MW
    # North→Central estimate in favour of the measured per-zone limits
    # (rule #11). Never tune these placeholders to a price residual.
    _placeholder_ttc = 40000.0
    links = [
        # L1: MN–IA 345 kV ties (wind-belt export path).
        TransferLink(
            from_zone="MISO-West", to_zone="MISO-Plains", ttc_mw=_placeholder_ttc
        ),
        # L2: MN–WI corridor (MWEX).
        TransferLink(
            from_zone="MISO-West", to_zone="MISO-East", ttc_mw=_placeholder_ttc
        ),
        # L3: IA/MO–IL (Ameren) ties.
        TransferLink(
            from_zone="MISO-Plains", to_zone="MISO-Illinois", ttc_mw=_placeholder_ttc
        ),
        # L4: IL–IN ties.
        TransferLink(
            from_zone="MISO-Illinois", to_zone="MISO-Indiana", ttc_mw=_placeholder_ttc
        ),
        # L5: IL–WI ties.
        TransferLink(
            from_zone="MISO-Illinois", to_zone="MISO-East", ttc_mw=_placeholder_ttc
        ),
        # L6: IN–MI interface (Michigan's import path).
        TransferLink(
            from_zone="MISO-Indiana", to_zone="MISO-East", ttc_mw=_placeholder_ttc
        ),
        # L7: the Regional Directional Transfer (RDT) contract path. MISO's
        # Midwest and South footprints are not directly interconnected and
        # exchange power only over a contract path that wheels across SPP,
        # governed by the RDT limits in the MISO/SPP Joint Operating
        # Agreement — explicitly *directional and asymmetric* (3,000 MW N→S /
        # 2,500 MW S→N), encoded verbatim as a PAIR of one-way links
        # (``is_bidirectional=False``, flow in [0, ttc]). On the Midwest side
        # the pair attaches to MISO-Plains (the MO/AECI side of the wheel
        # path; scope decision D3 — decide-by-probe, swap to MISO-Illinois in
        # a single diagnostic re-solve if RDT binding produces spurious
        # Plains congestion). Source: MISO/SPP Joint Operating Agreement,
        # Attach. A — RDT limits; MISO/SPP Coordinated System Plan.
        TransferLink(
            from_zone="MISO-Plains",
            to_zone="MISO-South",
            ttc_mw=3000.0,
            is_bidirectional=False,
        ),
        TransferLink(
            from_zone="MISO-South",
            to_zone="MISO-Plains",
            ttc_mw=2500.0,
            is_bidirectional=False,
        ),
    ]
    # Per-zone directional deliverability groups: one InterfaceLimit per
    # Midwest zone spanning ALL of the zone's incident internal links,
    # oriented into the zone, with cap = the zone's Capacity Import Limit
    # (CIL) and reverse cap = its Capacity Export Limit (CEL) — the exact
    # island-model quantities MISO's LOLE transfer analysis publishes (CIL,
    # not ZIA, per scope decision D4: ZIA is a capacity-accounting quantity).
    # For the union zones (Plains = LRZ 3+5, East = LRZ 2+7) the member-CIL/
    # CEL SUM is a documented CEILING: each member's island CIL counts help
    # arriving from the other member, which is internal after aggregation
    # (small overstatement for East — the direct Z2↔Z7 ties across the
    # Straits of Mackinac are weak; larger for Plains, where IA↔MO ties are
    # real). MISO-South gets NO group: the RDT (far tighter than the Z8+9+10
    # CIL sum) governs, so a South group could never bind first.
    #
    # These static values are the PY2025-26 SUMMER limits — the forecast-mode
    # fallback. Backcasts replace them with per-season hourly caps from the
    # full seasonal CSV via transmission.build_miso_deliverability_groups
    # (scope decision D7), matched by the "MISO_CIL_" name prefix.
    # Source: MISO PY2025-26 LOLE Study Report (data/raw/
    # capacity-deliverability/miso/miso.csv; parser scripts/lib/
    # capacity_deliverability/miso.py).
    interface_limits = [
        # West (LRZ 1): CIL 6,025 / CEL 3,991 MW.
        InterfaceLimit(
            name="MISO_CIL_West",
            links=[("MISO-Plains", "MISO-West"), ("MISO-East", "MISO-West")],
            cap_mw=6025.0,
            reverse_cap_mw=3991.0,
        ),
        # Plains (LRZ 3+5, member sums — ceiling): CIL 9,635 / CEL 8,594 MW.
        # The RDT pair is incident to Plains, so the (South→Plains) net
        # corridor term is a member (one-way pair sums as L7b − L7a).
        InterfaceLimit(
            name="MISO_CIL_Plains",
            links=[
                ("MISO-West", "MISO-Plains"),
                ("MISO-Illinois", "MISO-Plains"),
                ("MISO-South", "MISO-Plains"),
            ],
            cap_mw=9635.0,
            reverse_cap_mw=8594.0,
        ),
        # Illinois (LRZ 4): CIL 8,649 / CEL 4,460 MW.
        InterfaceLimit(
            name="MISO_CIL_Illinois",
            links=[
                ("MISO-Plains", "MISO-Illinois"),
                ("MISO-Indiana", "MISO-Illinois"),
                ("MISO-East", "MISO-Illinois"),
            ],
            cap_mw=8649.0,
            reverse_cap_mw=4460.0,
        ),
        # Indiana (LRZ 6): CIL 8,650 / CEL 6,881 MW.
        InterfaceLimit(
            name="MISO_CIL_Indiana",
            links=[
                ("MISO-Illinois", "MISO-Indiana"),
                ("MISO-East", "MISO-Indiana"),
            ],
            cap_mw=8650.0,
            reverse_cap_mw=6881.0,
        ),
        # East (LRZ 2+7, member sums — ceiling): CIL 7,949 / CEL 10,330 MW.
        InterfaceLimit(
            name="MISO_CIL_East",
            links=[
                ("MISO-West", "MISO-East"),
                ("MISO-Illinois", "MISO-East"),
                ("MISO-Indiana", "MISO-East"),
            ],
            cap_mw=7949.0,
            reverse_cap_mw=10330.0,
        ),
    ]
    # MISO energy offer cap is $2,000/MWh: FERC Order 831 sets a $2,000/MWh
    # hard cap on incremental energy offers across all RTOs/ISOs (offers above
    # $1,000/MWh must be cost-verified). MISO also runs a seasonal Planning
    # Resource Auction (PRA) capacity construct that provides revenue outside
    # the energy market, so the energy-only VOLL sits below ERCOT's $5,000.
    # No distinct cited MISO VOLL is used here.
    # Source: FERC Order 831; MISO Tariff (energy offer cap).
    return ISOConfig(
        name="MISO",
        zones=zones,
        links=links,
        voll=2000.0,
        interface_limits=interface_limits,
    )


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
    :func:`eia_loader.load_zonal_shares` (zones peak at different hours),
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
        # (interchange_config.IMPORT_TRANCHES/EXPORT_TRANCHES["NEISO"], P9); the priced
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
    # Simultaneous Import Limit across all HQ_import border links.
    # The three border links (HQ_import→Boston 2,000 + HQ_import→North 900 +
    # HQ_import→Connecticut 1,500 = 4,400 MW sum of individual TTCs) share
    # upstream Hydro-Québec export capacity and New England import interface
    # capability. The aggregate simultaneous import is ~3,850 MW — the ICR
    # (Installed Capacity Requirement) tie-benefit assessment ceiling and the
    # sustained simultaneous import capability across all external ties.
    # Source: ISO-NE Capacity, Energy, Loads, and Transmission (CELT) Report;
    # ISO-NE Installed Capacity Requirement (ICR) / Regional System Plan (RSP)
    # tie-benefit analysis; ISO-NE Forward Capacity Market qualification rules.
    # Tier 3 (calibration).
    interface_limits = [
        InterfaceLimit(
            name="HQ_import_simultaneous",
            links=[
                ("HQ_import", "Boston"),
                ("HQ_import", "North"),
                ("HQ_import", "Connecticut"),
            ],
            cap_mw=3850.0,
            bidirectional=True,
        ),
    ]
    # ISO-NE energy offer cap is $2,000/MWh. ISO-NE has a Forward
    # Capacity Market (FCM) providing capacity revenue outside the energy
    # market, so the energy-only VOLL sits below ERCOT's $5,000.
    # Source: ISO-NE Tariff §III.1.10.1A; FERC Order 831.
    return ISOConfig(
        name="NEISO",
        zones=zones,
        links=links,
        interface_limits=interface_limits,
        voll=2000.0,
        # ISO-NE winter scarcity pricing: the post-solve ORDC overlay
        # recovers the reserve-shortage price tail the perfect-foresight LP
        # structurally misses (winter gas-pipeline events drive >$300/MWh
        # spikes the energy-only dual cannot produce). ISO-NE-grounded params:
        #   VOLL $2,000 = ISO-NE Tariff §III.1.10.1A energy offer cap
        #   MCL 1,200 MW ≈ Millstone 3 largest single contingency (1,233 MW
        #     nameplate; ISO-NE RSP Table 4.1 / NPCC Directory #1)
        #   sigma 900 MW = ISO-NE Probabilistic Energy Adequacy winter
        #     reserve-error std dev (load-forecast + forced-outage uncertainty
        #     in the cold-weather gas-constrained regime; ISO-NE PAF Study
        #     2022, bounded by the 10-min reserve requirement 1,000-1,200 MW)
        #   shift 0.0 = no administrative curve shift (ERCOT PUCT orders do
        #     not apply to ISO-NE)
        #   multistep_floor False = no OBDRR048 floor (ERCOT-specific)
        # Still gated by scarcity_pricing_enabled (the master switch).
        default_scenario_overrides={
            "scarcity_price_overlay": True,
            "ordc_voll": 2000.0,
            "ordc_mcl_mw": 1200.0,
            "ordc_lolp_sigma_mw": 900.0,
            "ordc_lolp_shift_sigma": 0.0,
            "ordc_multistep_floor": False,
        },
    )


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


@dataclass(frozen=True)
class ReliabilityFloorSpec:
    """One temperature- or net-load-driven reliability-commitment floor limb.

    An ISO's floor = a list of limbs in ``RELIABILITY_FLOOR_REGISTRY[iso]``.
    Each limb pins one ``plant_class`` in one ``zone`` at ``floor_pct`` ×
    available capacity on every day its ``driver`` gate is flagged. The day
    gate is:

    * ``driver="tmax"`` — hot day ⇔ ``tmax_c > threshold`` (°C)
    * ``driver="tmin"`` — cold day ⇔ ``tmin_c < threshold`` (°C)
    * ``driver="netload"`` — high-stress day ⇔ ``net_load_mw > threshold`` (MW)

    ``start_hour``/``end_hour`` restrict the floor to a sub-daily window
    (both inclusive, 0-23).  When both are ``None`` the floor binds all 24 h.
    This models evening-ramp commitment (e.g. NYISO ST_GAS HB14-21 hot-limb).

    ``floor_pct = commit_frac × min_stable_pct`` (a structural commitment share
    times the class's physical minimum-stable level — never a measured-CF
    ceiling; see ``docs/multi-iso/reliability-floor-rebuild-plan.md`` §B.3).
    ``min_event_hours`` (≥ 24) bridges an isolated flagged day to adjacent
    flagged days for steam classes so a committed boiler spans a multi-day
    heat-wave / cold-snap rather than a single calendar day.

    ``ramp_group`` labels a **continuous temperature-ramp family**: two or more
    limbs sharing the same non-empty ``ramp_group`` are read as ``(threshold,
    floor_pct)`` knots of one piecewise-linear ramp rather than independent
    step gates. For each hour the engine interpolates ``floor_pct`` linearly in
    the driver temperature between the knots (clamped flat to the end knots
    outside their range), reproducing the legacy ``clip(base + slope×(T−T0),
    base, cap)`` commitment curve exactly instead of a single over-firing step.
    All limbs in a family must share ``zone``/``plant_class``/``driver``/
    ``distribution``/``start_hour``/``end_hour`` and differ only in ``threshold``
    and ``floor_pct``; the ramp binds every hour in the window (its base knot is
    the persistent floor), so a ramp family needs no separate always-on base
    limb. Ramp families support only the ``tmax``/``tmin`` drivers.
    """

    zone: str  # model zone name
    plant_class: str  # plant_group: "ST_GAS", "CT_PEAKER", "COAL", "oil", …
    driver: str  # "tmax" (hot gate) | "tmin" (cold gate) | "netload"
    threshold: float  # °C for tmax/tmin; MW for netload
    floor_pct: float  # = commit_frac × min_stable_pct (see plan §B.3)
    enabled: bool = True  # toggle this exact (iso, zone, class, driver) limb
    min_event_hours: int = 24  # steam-gas event bridging; 24 = single-day
    distribution: str = "cheapest_first"  # "cheapest_first" or "pro_rata"
    start_hour: int | None = None  # sub-daily window start (inclusive, 0-23)
    end_hour: int | None = None  # sub-daily window end (inclusive, 0-23)
    ramp_group: str | None = None  # continuous-ramp family label (see below)


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
    ``distribution``, ``start_hour``, ``end_hour``, ``ramp_group``, ``r1_disabled``.

    An ``r1_disabled=True`` row is forced ``enabled=False`` here regardless of its
    ``enabled`` column: the limb is unidentified out-of-training (Spearman ρ sign
    flip, D-8 §2B) and permanently disabled under decision rule R1 (CLAUDE.md
    rule 17; scalar-remediation B-LIMB-1). The column is optional — absent means
    not R1-disabled — so ISO CSVs that predate the marker load unchanged.
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
                    sh_raw = (row.get("start_hour") or "").strip()
                    eh_raw = (row.get("end_hour") or "").strip()
                    rg_raw = (row.get("ramp_group") or "").strip()
                    limbs.append(
                        ReliabilityFloorSpec(
                            zone=row["zone"].strip(),
                            plant_class=cls,
                            driver=row["driver"].strip(),
                            threshold=float(row["threshold"]),
                            floor_pct=float(row["floor_pct"]),
                            enabled=(
                                _coerce_bool(row.get("enabled", "True"))
                                and not _coerce_bool(row.get("r1_disabled", ""))
                            ),
                            min_event_hours=int(row["min_event_hours"])
                            if row.get("min_event_hours")
                            else default_event,
                            distribution=(
                                row.get("distribution") or "cheapest_first"
                            ).strip(),
                            start_hour=int(sh_raw) if sh_raw else None,
                            end_hour=int(eh_raw) if eh_raw else None,
                            ramp_group=rg_raw or None,
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


# Reliability-floor plant classes whose commitment is OWNED by an active
# net-load deployment drag (data.fleet.apply_ct_netload_drag_floor /
# apply_gas_st_netload_drag_floor). The drag is a CAMPD-net-load-regressed,
# ramp-windowed [15,22) min-gen floor; when it is on it is the SINGLE
# commitment mechanism for its class (CLAUDE.md rule 19 — one mechanism per
# phenomenon). The temperature reliability floor ALSO detects a rising hot-day
# commitment for the same class (rho >= 0.3), but it binds all 24 h of a flagged
# day — including overnight, where measured CAMPD CT CF is ~0.016 (h0-6) vs
# ~0.38 at the afternoon cooling peak. Stacking it on the drag double-floors the
# class and pins it overnight where the fleet is physically offline: the D-4
# off-window binding failure (docs/FINDING-pjm-burndown-2026-07.md; a floor
# binding in hours its own driver evidence says the class is offline is a bug,
# CLAUDE.md rule 17). Dropping these limbs when the drag is active reconciles
# the two onto the grounded, forward-native mechanism rather than stacking them.
_DRAG_OWNED_RELIABILITY_CLASS: dict[str, str] = {
    "ct_netload_drag": "CT_PEAKER",
    "gas_st_netload_drag": "ST_GAS",
}


def drop_drag_owned_reliability_specs(
    specs: list[ReliabilityFloorSpec],
    config,
) -> list[ReliabilityFloorSpec]:
    """Drop reliability-floor limbs whose class is owned by an active net-load drag.

    When ``config.ct_netload_drag`` (or ``gas_st_netload_drag``) is set, the drag
    is the single commitment mechanism for its class (CLAUDE.md rule 19); the
    temperature reliability floor's limbs for that class are removed so the two
    do not stack into an all-day floor that binds overnight where the class is
    offline (:data:`_DRAG_OWNED_RELIABILITY_CLASS`; the D-4 off-window failure,
    ``docs/FINDING-pjm-burndown-2026-07.md``). No-op (returns *specs* unchanged)
    when no drag is active, so any ISO/run without the drag is byte-identical.
    """
    drop = {
        cls
        for flag, cls in _DRAG_OWNED_RELIABILITY_CLASS.items()
        if getattr(config, flag, False)
    }
    if not drop:
        return specs
    return [s for s in specs if s.plant_class not in drop]


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
