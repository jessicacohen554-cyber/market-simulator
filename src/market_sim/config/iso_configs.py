"""Per-ISO configuration parameters.

Defines the physical topology (zones and transfer links) for each supported
ISO using Pydantic models, plus a factory for retrieving them by name.
"""

from __future__ import annotations

import csv as _csv
from dataclasses import dataclass
from dataclasses import replace as _dataclass_replace

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

    ``flow_cost`` is an optional $/MWh charge on the link's directed flow —
    the LP mechanism for a *priced* transfer step (MISO's RDT Transmission
    Constraint Demand Curve prices flow above the derated limit at $40 then
    $500/MWh rather than hard-capping it; 2024 MISO SOM §III.B). Nonzero
    only on one-way links (``is_bidirectional=False``): a positive cost on a
    signed bidirectional flow would *credit* the reverse direction
    (validated in :func:`market_sim.model.dispatch.DispatchModel`).
    """

    from_zone: str
    to_zone: str
    ttc_mw: float = Field(gt=0.0)
    is_bidirectional: bool = True
    flow_cost: float = Field(default=0.0, ge=0.0)


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
    EAST weather zone forms its own Northeast zone behind the EASTEX
    East-Texas export limit; see below); see scripts/data/derive_load_shares.py. Panhandle
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
    # aggregation in scripts/data/derive_load_shares.py (North 0.3081->0.3064,
    # Northeast 0.0335->0.0351). The prior values predated the consistent
    # EAST-carve-out; every other zone already matched the script exactly. The
    # unrounded vector sums to 1.0; rounding to 4 dp leaves a 0.0001 residual
    # absorbed into South (true 0.079948 -> 0.0800, largest-remainder) so the
    # literals still sum to exactly 1.0. Fallback-only, so this is low-risk.
    #
    # Northeast is split out of the old North zone to make the East-Texas
    # trapped-generation congestion physical: a generation-rich lobe of NE
    # Texas (the EAST weather zone) -- ~4.2 GW of coal (Martin Lake, Welsh,
    # Pirkey) + ~3.9 GW of gas (Tenaska Gateway CC, Wilkes, ...) serving only
    # ~3.4% of system load -- behind ERCOT's East Texas GTC (EASTEX, "a
    # voltage stability limit associated with flows out of the East Texas
    # area", i.e. around Tyler/Lufkin/Nacogdoches; market notice #1557). The
    # six-zone model let all of that pour into North as if unconstrained,
    # over-running Martin Lake (PRB) and mis-dispatching the NE CCs. (The
    # split was ORIGINALLY built around the NE_LOB series under a name
    # misreading — NE_LOB is the Valley's North Edinburg-Lobo corridor —
    # repaired at ercot-234 under signed card Z-A; the zone itself stands on
    # the EASTEX physics + the ERCOT-76 measured import evidence. See
    # docs/FINDING-ercot234-subzonal-survey-nelob-identity-2026-08-24.md.)
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
    # scripts/data/derive_ttc_limits.py) wherever the GTC maps cleanly to a model
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
    # represent -- the Valley family inside South (NE_LOB "North Edinburg -
    # Lobo", the record's most-binding GTC; VALEXP; NELRIO; RV_RH), TRDWEL
    # (a single line), MCCAMY. The East Texas GTC (EASTEX) IS representable
    # and is modeled explicitly as the Northeast->North link below
    # (ercot-234 card Z-A repair; before 2026-08 this link wrongly carried
    # the NE_LOB series under a name misreading).
    # Sources: ERCOT NP6-86-CD SCED Shadow Prices and Binding Transmission
    # Constraints (2023-2024); ERCOT 2022 Constraints and Needs Report; ERCOT
    # GTC Workshop definitions (2020-02-24) + market notice #1557 for EASTEX.
    links = [
        TransferLink(from_zone="West", to_zone="North", ttc_mw=7300.0),
        TransferLink(from_zone="West", to_zone="South_Central", ttc_mw=2700.0),
        TransferLink(from_zone="Panhandle", to_zone="North", ttc_mw=2680.0),
        # EASTEX: the East Texas export limit capping the trapped Martin Lake
        # / NE-CC lobe (2,300 MW = the NP6-86 mean-limit-at-bind pooled
        # 2023+2024, per-year 2,386.5 / 1,916.7, derived per
        # PRECOMMIT-ercot234 P-2 with the instrument validated on
        # WESTEX +0.20% / PNHNDL +0.05%; 2025 context: 3 binding rows —
        # ERCOT ran the constraint effectively unconstrained). A GTC
        # is an EXPORT stability limit, not an import rating (data/gtc.py), so
        # the boundary is a one-way pair (the Far_West aad79c1 asymmetric-
        # rating recipe): export keeps the measured EASTEX limit-at-bind;
        # import carries the boundary's measured carrying capability. The old
        # symmetric 1,300 MW import bound was directly measured-refuted
        # (ERCOT-76): on 2024-05-07 h20 the real lobe imported >= 1,317 MW
        # (EAST-zone load 2,232 minus CAMPD local gross 915) while RT printed
        # $15 — the model shed load against the phantom import wall and
        # printed VOLL. Import rating = the pooled 2023-2025 DARK-HOUR
        # (hod 20-06, so unmetered zonal solar cannot inflate the proxy)
        # maximum of measured EAST-zone load minus CAMPD NE-plant net gross
        # (1,511 / 1,788 / 1,756 MW by year; leave-one-year-out 1,756-1,788 —
        # verdict-identical). Same admissibility class as the measured
        # limit-at-bind statics above (a measured deliverability envelope, the
        # MISO/PJM seam-envelope convention); re-derive only on source-data
        # updates (rule 23).
        TransferLink(
            from_zone="Northeast",
            to_zone="North",
            ttc_mw=2300.0,
            is_bidirectional=False,
        ),
        TransferLink(
            from_zone="North",
            to_zone="Northeast",
            ttc_mw=1788.0,
            is_bidirectional=False,
        ),
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
        #
        # FFR-9C STAGE B — ARMED FOR ERCOT by owner decision D-30 (sitting
        # Addendum AK.8, signed 2026-08-11; lane FFR-9C-PROMOTE, pre-registration
        # docs/handoffs/PREREG-ffr-9c-promote-stageb-2026-08-12.md). The five rows
        # below move as ONE unit and must not be separated:
        #
        #   * capacity_screen_unified_lookahead + capacity_screen_scarcity_restoration
        #     are the CONTROL RECIPE stage B was measured on top of. Addendum AG.1
        #     parked their promotion on "FH-4's own skill evidence"; FH-5 supplied it
        #     (AO.2, docs/handoffs/fh-5-phase-b-2026-08-11.md §4 — 11 of 12 arms, the
        #     I6 rider PASSING on every one). They are also a pair by construction:
        #     ScenarioConfig.__post_init__ REFUSES the restoration flag without the
        #     lookahead.
        #   * entry_pipeline_aware_signal (R-a) repairs a real double-count (rule 19).
        #   * smr_available_year=2030 (R-b) removes 4 GW of 2022-vintage ERCOT SMR — a
        #     non-real object — behind a published zero-parameter gate.
        #   * vre_procurement_additions_enabled (R-d) nets exactly, bounded to 1.84 GW
        #     at this vintage.
        #
        # Zero fitted parameters in any stage. Arming the three R-flags WITHOUT the
        # two screen flags would ship "stage B minus its own base recipe" — a
        # combination nobody has solved, and a posture whose only evidence measures a
        # different one (rule 13 [R-MEASURED]).
        #
        # Rule 25 [R-ISO-SCOPE]: ERCOT ONLY, and necessarily so —
        # capacity_screen_scarcity_restoration's committed-capability (RTOLCAP/
        # RTOFFCAP) share tables are ERCOT-identified, so __post_init__ RAISES for any
        # other ISO. A shipped-default flip on the ScenarioConfig scalar cannot express
        # this posture at all; the per-ISO seam is the only vehicle that can. This
        # follows the D-29 precedent from the same sitting (miso_clean_tier_rows, MISO
        # block below), rather than inventing a second mechanism (rule 19 [R-ONE-MECH]).
        #
        # EPOCH: this re-bases every ERCOT hindcast. Every pre-epoch ERCOT sidecar is
        # historical record and NEVER a baseline for post-epoch comparison — FH-5's own
        # ERCOT legs included. FH-5 is not re-solved; its artifacts were produced at
        # src/ == 3ae7465 (its §3 pin). The ERCOT forecast-lane RESOLVED default key
        # moves 062d440558103f81 -> 8d9ef77edb3e44cb; the GLOBAL pinned default key
        # 603c2498bf71d21d and every ERCOT backcast key are UNMOVED. Declared by
        # scripts/probes/_ffr9c_stageb_cache_epoch.py and pinned by
        # tests/unit/config/test_ercot_stageb_arming.py (2026-08-13 — the arming
        # commit a71fc84d merged as PR #3888 before the declaration could land with
        # it; sitting Addendum AQ records the gap this closes).
        #
        # PRECEDENCE — an explicit caller value ALWAYS wins, including one equal to
        # the ScenarioConfig field default. RESTORED 2026-08-13 by the OVERRIDE-FIX
        # lane (FINDING-ffr-9c-iso-override-precedence-2026-08-12.md, §4 remedy 2 +
        # its RESOLUTION ADDENDUM): between PR #3888 and that fix the seam had no
        # unset sentinel, so a caller value EQUAL to the field default was
        # indistinguishable from unset and was silently re-armed — which made an
        # ERCOT control arm for these five flags inexpressible through the config
        # path. apply_iso_scenario_defaults now consults the caller's own
        # explicitly-set-field record (scenarios.explicitly_set_fields), so the
        # control arm is expressible and a leg that passes nothing still resolves
        # all five armed. NOTE the pair constraint: the two capacity-screen flags
        # must be turned off TOGETHER — __post_init__ refuses restoration without
        # the lookahead (FFR-8A), so switching off only one RAISES.
        #
        # D12-A ARMING — entry_margin_exhaustion + entry_forward_reserve_leg
        # ARMED AS THE ERCOT FORECAST DEFAULT by owner ruling Q15 (r#18
        # sitting, 2026-08-30, docs/handoffs/capx-director-ledger-2026-08.md
        # §3), executing Q10's confirm-then-arm protocol; lane record
        # docs/handoffs/FINDING-capx-d12a-arming-2026-08-30.md. The two rows
        # move as ONE unit — the D12-C pair's single logical delta; a posture
        # shipping one without the other was never solved (rule 13
        # [R-MEASURED]).
        #
        # Q10 (r#15 sitting, 2026-08-30), verbatim: "CONFIRM-PAIR, THEN ARM.
        # Lane D12-C chartered: ONE arm-vs-control A/B on the ERCOT T1-H leg
        # at the registered posture with the TWO fields
        # (entry_margin_exhaustion + entry_forward_reserve_leg) as the single
        # logical delta, measuring the closed loop D12 open-loop-predicted.
        # Arming auto-executes on a confirming record (both flip to ERCOT
        # forecast defaults, honestly described); a contradiction does NOT
        # arm and comes back to the owner at full magnitude."
        #
        # The measured record (FINDING-capx-d12c-confirm-pair-2026-08-30.md
        # §4) was CONTRADICTING on exactly ONE of the five pre-declared
        # verdict windows, so the pair armed nothing and escalated per its
        # own protocol. Q15 (r#18 sitting, 2026-08-30), verbatim: "ARM BOTH
        # FIELDS (entry_margin_exhaustion + entry_forward_reserve_leg → ERCOT
        # forecast defaults), the owner judging the record
        # confirming-in-substance per the finding's own §4.3 clause. The V-2
        # miss is described honestly in the arming citation; matrix cells O →
        # K-forecast-armed on the registered pair's evidence; sister-ISO
        # cells stay U (rule 26). Execution = lane D12-A (zero-solve; prompt
        # in the pack)."
        #
        # THE HONEST POSTURE. Armed, ERCOT forecast entry is
        # exhaustion-bounded on the entering year's OWN expected-ORDC surface
        # for every candidate class: both entry allocators build in repriced
        # 250 MW tranches until the screen's one-object forward margin
        # (energy leg + the SAME instrument invocation's expected-ORDC
        # reserve adder — never the prior year's realized adder) is
        # exhausted, bounded by the same caps as bang-bang. THE V-2 MISS,
        # carried at full magnitude: the pair's entering-2022 gas_cc build
        # was 0 MW, OUTSIDE the pre-declared [750, 1,250] MW window (the
        # offline B-walk's 1,000 ± 1 tranche). Not a construction defect —
        # the armed run's start margin was bit-identical to the committed
        # +$45,930.9/MW-yr — but a pre-declaration derivation error: the
        # window came from the offline walk's RESTRICTED candidate set (VRE
        # held at shipped) while the live walk fields every class, so solar
        # won the early tranches and exhausted cc's margin before a tranche
        # cleared. Direction conservative (MORE exhaustion by the same
        # mechanism on the same one-object margin); every other criterion
        # and every structural claim confirmed (V-1/V-3/V-4/V-5 + both
        # gates; terminal RM 15.84 % inside the ex-ante [15.0, 21.0] band);
        # the tolerance was never widened after the record (rule 21
        # [R-DOF]).
        #
        # EVIDENCE = the registered D12-C pair (forecast namespace, both
        # bundles committed with run_config.json):
        #   ercot-2021-2025-realized-t1h-d12c-control  key 28cef3500ec1fd9e
        #   ercot-2021-2025-realized-t1h-d12c-armed    key f061b2646bfaac8b
        # The ARMED bundle IS the record of this default posture: after this
        # flip a bare ERCOT T1-H invocation resolves to exactly its config —
        # verified zero-solve at arming (bare build_config + resolution
        # reproduces f061b2646bfaac8b bit-equal; no re-solve, no
        # re-registration). CACHE EPOCH, ERCOT forecast lane only: the
        # resolved bare-construction default key moves 8d9ef77edb3e44cb ->
        # 68a207068509f2b0 (and the bare T1-H key 28cef3500ec1fd9e ->
        # f061b2646bfaac8b); the GLOBAL pin 603c2498bf71d21d, both
        # ScenarioConfig field defaults (False — the unarmed pole, so armed
        # runs ENTER the digest), every backcast key (both fields are
        # _CACHE_KEY_OPTIONAL_FIELDS members AND backcast-coerced off) and
        # every other ISO's resolution are UNMOVED. Pinned by
        # tests/unit/config/test_ercot_stageb_arming.py (TestD12AArming) and
        # tests/unit/config/test_iso_override_precedence.py.
        #
        # POLE LITERALS SUPERSEDED 2026-09-02 (this arming is untouched; the
        # cause is elsewhere). The owner-authorized capx D41 re-identification
        # moved two SHARED defaults onto the NREL ATB 2024 (2026$) basis —
        # fixed_om_gas_cc_ccs 25.0 -> 65.0 and ccs_retrofit_capex_kw 900.0 ->
        # 1521.4 — and NEITHER is a _CACHE_KEY_OPTIONAL_FIELDS member, so both
        # are hashed at every value and EVERY config in the program re-keys:
        # this ERCOT pole 68a207068509f2b0 -> 6bb61037c072502d, its pre-arm
        # 8d9ef77edb3e44cb -> 71f20d708a810f0a, the global pin
        # 603c2498bf71d21d -> cedadc285f8603b9 and every backcast key
        # e027bc248c93c835 -> e006dfd7cef8bedd. The literals above are the
        # dated measurements taken at THIS arming and are left as written; the
        # relations they assert (armed vs pre-arm distinct, no other ISO's
        # resolution disturbed by this arming) are unaffected, because the
        # poles moved together by the same delta. Cause block and blast
        # radius: tests/regression/test_persisted_identity.py and the
        # cache-epoch ledger in src/market_sim/results/cache.py.
        #
        # The control arm stays expressible (OVERRIDE-FIX precedence): an
        # explicit --no-entry-margin-exhaustion /
        # --no-entry-forward-reserve-leg (or constructor False) wins over
        # these rows, and committed registered-posture bundles pin their own
        # values in run_config.json. DEPENDENCY WALL: the reserve leg
        # requires entry_lookahead_reprice AND screen_reserve_value_enabled,
        # and the exhaustion walk requires the reprice (__post_init__
        # refusals) — an ERCOT leg that disarms the reprice or the
        # screen-reserve mechanism must now disarm these two WITH it or
        # construction RAISES, the same discipline as the stage-B screen
        # pair above. The retirement screens' internally-consistent backward
        # pair is untouched (the D12 finding's own scope line). Rule 25
        # [R-ISO-SCOPE]: ERCOT ONLY — the verdicts are the ERCOT pair's;
        # sister ISOs stay U and derive their own parameters from their own
        # markets.
        default_scenario_overrides={
            "scarcity_price_overlay": True,
            "capacity_screen_unified_lookahead": True,
            "capacity_screen_scarcity_restoration": True,
            "entry_pipeline_aware_signal": True,
            "smr_available_year": 2030,
            "vre_procurement_additions_enabled": True,
            # D12-A (owner ruling Q15): the margin-exhaustion entry volume
            # rule with its scarcity-consistent forward reserve leg — one
            # unit, see the D12-A block above.
            "entry_margin_exhaustion": True,
            "entry_forward_reserve_leg": True,
        },
    )


def _caiso_config() -> ISOConfig:
    """Build the CAISO topology configuration.

    Trading zones along CAISO's real north–south split — **NP15**
    (north of Path 15), **ZP26** (between Path 15 and Path 26) — and, south of
    Path 26, the former single ``SP15`` zone now split into its three local
    capacity areas (SP15 local-area split, 2026-07-09):

    - **LA_BASIN** — the SCE LA-basin LCR pocket (Big Creek/Ventura folded in),
    - **SDGE** — the SDG&E / Path-44 pocket (post-SONGS import-limited),
    - **SP15_rest** — the remaining SP15 south gateway that Path 26 and Path 46
      (WOR) feed, and from which the two pockets import over import-limited
      one-way links.

    Plus the ``WECC_import`` node for the rest of the WECC. These mirror CAISO's
    congestion-revenue-rights trading hubs, the Path 15 / Path 26 interties, and
    the LCT-study local capacity areas that set SP15's LA-basin/SDG&E congestion
    premium (which a single copperplate SP15 zone cannot form; see
    docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md).

    Load shares apportion CAISO TAC-area demand onto the hubs. NP15 ≈ PG&E
    north of Path 15; ZP26 ≈ the PG&E central San Joaquin Valley between Path 15
    and Path 26; the three SP15 sub-zones together are SCE + SDG&E (+ the tiny
    VEA TAC) south of Path 26, summing to the old SP15 0.5385. The whole-SP15
    share is measured from CAISO OASIS ``SLD_FCST`` ACTUAL TAC-area hourly load
    (upload U4, Jan-2023 sample; ``scripts/data/derive_load_shares.py caiso``):
    PGE-TAC 46.1%, SCE-TAC 44.3%, SDGE-TAC 9.2%, VEA-TAC 0.4% of component-TAC
    load. PGE-TAC straddles Path 15 and is split **0.883951 / 0.116049** between
    NP15 and ZP26 — MEASURED (caiso-172), not the former 0.86/0.14 estimate:
    OASIS ``ATL_LDF`` per-pnode load distribution factors inside
    ``DLAP_PGAE-APND``, joined by substation to ``ATL_PNODE_MAP``'s
    authoritative ``TH_NP15_GEN`` / ``TH_ZP26_GEN`` membership (CAISO's own
    Path-15 geography), day-weighted over 2023-2025. See
    ``scripts/data/derive_caiso_path15_load_split.py`` and
    ``constants.CAISO_TAC_ZONE_WEIGHTS``. The *intra-SP15* split is measured
    from the CAISO LCT study's published pocket peak loads (Table 3.3-7 vs the
    SP26 zone peak, Table 3.2-1): LA_BASIN 19,537 / SDGE 4,768 / SP26 28,149 MW
    (2023) → LA_BASIN = 0.374, SDGE = 0.091 of full ISO, with SP15_rest the
    exact residual (0.5385 − 0.374 − 0.091 = 0.0735) so the three sum to the
    old SP15 share (``validate_topology`` hard-errors otherwise). Note the
    scope table rounds the residual to 0.074; the exact 0.0735 is used here to
    keep the total at 1.0.

    Hourly *shapes* come from the same OASIS file via
    ``eia_loader.load_zonal_shares``; these static shares are its fallback.
    Source: CAISO Final LCT reports 2023–2025 (``data/raw/capacity-
    deliverability/caiso/caiso.csv``); ``scripts/data/derive_load_shares.py caiso``.
    """
    zones = [
        # PG&E TAC total (0.4615) re-split by the MEASURED Path-15 weight
        # (caiso-172): 0.4615 x 0.883951 / 0.116049. Was 0.3969 / 0.0646 on the
        # 0.86/0.14 estimate. The PG&E total is unchanged, so the SP15 sub-zone
        # shares below (LCT-sourced) are untouched and the five still sum to 1.0.
        Zone(name="NP15", iso="CAISO", load_share=0.4079),
        Zone(name="ZP26", iso="CAISO", load_share=0.0536),
        # SP15 local-area split (LCT peak_load ÷ SP26 peak × old SP15 0.5385).
        # LA_BASIN 19,537/28,149 and SDGE 4,768/28,149 (2023 LCT Table 3.3-7 /
        # 3.2-1) → 0.374 / 0.091 of the full ISO; SP15_rest is the exact
        # residual so the three sum to 0.5385 (validate_topology hard-errors on
        # any drift). Source: data/raw/capacity-deliverability/caiso/caiso.csv.
        Zone(name="LA_BASIN", iso="CAISO", load_share=0.374),
        Zone(name="SDGE", iso="CAISO", load_share=0.091),
        Zone(name="SP15_rest", iso="CAISO", load_share=0.0735),
        # WECC_import is an import node, not a load zone, so it carries no load.
        Zone(name="WECC_import", iso="CAISO", load_share=0.0),
    ]
    # LCT-sourced import caps into the two SP15 load pockets, using the literal
    # `import_cap = peak_load − LCR` convention (scope §reserve-margin: take the
    # published LCR literally; the reserve gross-up is a frozen sensitivity,
    # never tuned to the residual — rule 24). From the CAISO LCT rows
    # (data/raw/capacity-deliverability/caiso/caiso.csv, peak_load − requirement):
    #   LA Basin:  12,008 / 15,224 / 15,174 MW  (2023 / 2024 / 2025)
    #   SDG&E:      1,436 /  2,074 /  2,071 MW  (2023 / 2024 / 2025)
    # STATIC tightest-year (2023) values are used here — the smallest import cap,
    # i.e. the most binding / most conservative pocket boundary. Per-year caps are
    # the preferred end state (wired through the runner's per-year config build,
    # like transmission.apply_deliverability_seam_limit), but that requires a new
    # runner call site outside this foundation task's three-file scope; the static
    # 2023 value is the documented MVP and downstream tasks can promote it to
    # per-year. See the FOUNDATION DECISIONS block in the scope doc.
    _LA_BASIN_IMPORT_CAP_MW = 12008.0  # 19,537 − 7,529 (LCT 2023, tightest year)
    _SDGE_IMPORT_CAP_MW = 1436.0  # 4,768 − 3,332 (LCT 2023, tightest year; Path-44)
    # CAISO intertie TTCs seeded from the WECC Path Rating Catalog. Path 15
    # (Los Banos–Gates) is rated 5,400 MW N→S after the 2004 third-line
    # upgrade; Path 26 (Midway–Vincent) is rated 4,000 MW N→S. The WECC
    # import splits across the two major intertie groups: Path 66 / COI
    # (California–Oregon Intertie) ~4,800 MW into NP15 to the north, and
    # Path 46 / West of the River ~10,623 MW E→W into SP15_rest to the south
    # (the Palo Verde / WOR corridor). The two import links sum to ~15,400
    # MW, consistent with the 15,000 MW WECC import supply curve.
    # Source: WECC Path Rating Catalog (Path 15, Path 26, Path 46, Path 66).
    # Tier 3 (calibration) — verify against CAISO OASIS transfer capabilities
    # and binding-frequency from CAISO congestion/shadow-price data.
    links = [
        # Path 15: NP15 ↔ ZP26 (Los Banos–Gates).
        TransferLink(from_zone="NP15", to_zone="ZP26", ttc_mw=5400.0),
        # Path 26: ZP26 → SP15_rest (Midway–Vincent) — the dominant N–S
        # intertie, re-pointed onto the SP15 south gateway (same 4,000 MW
        # rating, re-homed off the removed SP15 zone).
        TransferLink(from_zone="ZP26", to_zone="SP15_rest", ttc_mw=4000.0),
        # Path 66 / COI: WECC import into NP15 (north).
        TransferLink(from_zone="WECC_import", to_zone="NP15", ttc_mw=4800.0),
        # Path 46 / West of the River: WECC import into SP15_rest (south),
        # re-pointed off the removed SP15 zone (same 10,623 MW rating).
        TransferLink(from_zone="WECC_import", to_zone="SP15_rest", ttc_mw=10623.0),
        # Internal LA-basin import limit: SP15_rest → LA_BASIN, one-way,
        # capped at the LCT import capability (peak_load − LCR). The one-way
        # import-limited link is what forms the LA-basin locational premium.
        TransferLink(
            from_zone="SP15_rest",
            to_zone="LA_BASIN",
            ttc_mw=_LA_BASIN_IMPORT_CAP_MW,
            is_bidirectional=False,
        ),
        # Path 44 / SDG&E import limit: SP15_rest → SDGE, one-way, capped at the
        # LCT import capability. SDG&E's ~1.4 GW cap is the post-SONGS Path-44
        # constraint — the physical reason SDGE is the most import-limited pocket.
        TransferLink(
            from_zone="SP15_rest",
            to_zone="SDGE",
            ttc_mw=_SDGE_IMPORT_CAP_MW,
            is_bidirectional=False,
        ),
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
            # Path 46/WOR now terminates on SP15_rest (the SP15 split re-pointed
            # it off the removed SP15 zone), so the simultaneous-import group's
            # southern link pair references SP15_rest; validate_topology requires
            # each pair to join a real TransferLink.
            links=[("WECC_import", "NP15"), ("WECC_import", "SP15_rest")],
            cap_mw=7500.0,
        ),
    ]
    # caiso-224 FSNO sub-zonal partition (ScenarioConfig
    # caiso_fsno_subzonal_topology, default off — armed process-wide via
    # config.topology_variant so the LP and every bare get_iso_config()
    # consumer see the same 7-zone topology). The caiso-223 P-A' partition
    # applied verbatim (FINDING-caiso223-subzonal-scope-2026-08-30.md §A;
    # PRECOMMIT-caiso224-fsno-arm-2026-08-30.md §1):
    # a new FSNO San-Joaquin-Valley pocket zone between the two cuts the DMM
    # record shows binding, replacing the single Path-15 link (whose own
    # elements are not top binders — Los Banos-Gates / Panoche-Gates become
    # FSNO-internal spine). Every number is a committed measured input
    # [R-MEASURED, R-ACCURATE], zero free parameters:
    #   load: PG&E TAC 0.4615 × the caiso-223 §C measured 3-way ATL_LDF
    #     split {NP15 0.752614, FSNO 0.132592, ZP26 0.114794}
    #     (results/calibration/_caiso223_subzonal_scope.json, gates 13/13);
    #   links: DMM 2023-annual published element average binding limits
    #     (CAISO DMM 2023 Annual Report on Market Issues & Performance) —
    #     NP15<->FSNO = Tesla-Los Banos #1 500 kV 1,600 + Moss Landing-Las
    #     Aguilas 230 kV 340 = 1,940 MW; FSNO<->ZP26 = Gates-Midway #1
    #     500 kV 2,500 MW. Lower-bound reconciliation (parallel unrated
    #     elements omitted) documented per rule 14 in the precommit §2.
    # The removed link also retires the ("NP15","ZP26") row of
    # CAISO_PATH_DIRECTIONAL_RATINGS for the armed variant (its pair no
    # longer exists — both directions tighten under the chain; declared in
    # the precommit §2, not a silent drop).
    from market_sim.config.topology_variant import caiso_fsno_partition_active

    if caiso_fsno_partition_active():
        # 0.4615 (PGE-TAC share, derive_load_shares) × the measured 3-way
        # weights at 6 dp, NP15 the exact residual so the three sum to 0.4615
        # and the seven to 1.0 (the same residual convention as SP15_rest
        # above; caiso-223 §C reports these very values: FSNO 0.061191 /
        # ZP26 0.052977 / NP15 0.347332).
        zones = [
            Zone(name="NP15", iso="CAISO", load_share=0.347332),
            Zone(name="FSNO", iso="CAISO", load_share=0.061191),
            Zone(name="ZP26", iso="CAISO", load_share=0.052977),
            Zone(name="LA_BASIN", iso="CAISO", load_share=0.374),
            Zone(name="SDGE", iso="CAISO", load_share=0.091),
            Zone(name="SP15_rest", iso="CAISO", load_share=0.0735),
            Zone(name="WECC_import", iso="CAISO", load_share=0.0),
        ]
        # Rounding to 6 dp leaves the three PG&E shares summing within the
        # validate_topology 1e-6 tolerance of 0.4615 (0.347332 + 0.061191 +
        # 0.052977 = 0.4615 exactly).
        links = [
            TransferLink(from_zone="NP15", to_zone="FSNO", ttc_mw=1940.0),
            TransferLink(from_zone="FSNO", to_zone="ZP26", ttc_mw=2500.0),
            TransferLink(from_zone="ZP26", to_zone="SP15_rest", ttc_mw=4000.0),
            TransferLink(from_zone="WECC_import", to_zone="NP15", ttc_mw=4800.0),
            TransferLink(from_zone="WECC_import", to_zone="SP15_rest", ttc_mw=10623.0),
            TransferLink(
                from_zone="SP15_rest",
                to_zone="LA_BASIN",
                ttc_mw=_LA_BASIN_IMPORT_CAP_MW,
                is_bidirectional=False,
            ),
            TransferLink(
                from_zone="SP15_rest",
                to_zone="SDGE",
                ttc_mw=_SDGE_IMPORT_CAP_MW,
                is_bidirectional=False,
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
        # ISO-level scenario default applied by the runner to any field the
        # caller left at its ScenarioConfig default (runner.py:585-593).
        #
        # entry_vre_capacity_revenue — ARMED FOR MISO by owner decision D-2'
        # (sitting Addendum O, signed 2026-08-04; lane FFR-4B, evidence
        # docs/handoffs/ffr-3v-miso-entry-screen-2026-08-04.md §3.3/§7 1a).
        # MISO's Planning Resource Auction accredits and PAYS wind and solar
        # like any other Planning Resource, so a MISO forecast that denies VRE
        # entry the RA payment is not modelling MISO's market. Before this,
        # VRE was the ONLY accredited resource class on the system denied that
        # payment while thermal entry, the thermal retirement screen and
        # storage entry all took it through the SAME seam
        # (MarketDesign.capacity_price_per_firm_mw_yr) — and VRE's accredited
        # MW were ALREADY counted on the supply side of the adequacy ledger,
        # so MISO solar was depressing the very price the others collected.
        # Arming removes that exception; it adds no second channel (rule 19
        # [R-ONE-MECH] — one price seam, one accreditation resolver).
        #
        # Rule 25 [R-ISO-SCOPE]: MISO ONLY. The other capacity-market ISOs are
        # separate per-ISO decisions, are NOT authorized by D-2', and must
        # derive their own accreditation from their own market's data.
        #
        # Measured MISO-scoped effect (FFR-4B 2x2, base 5eac75b0, T1-H
        # 2021-2025): INERT in the 2022-2024 decision years — MISO is long and
        # its VRR pays $0 to EVERY technology, thermal included, which is
        # faithful (the real PY2021-22 PRA cleared at ~$1,825/MW-yr). DECISIVE
        # in the 2025 decision year, which screens on 2024's short position:
        # solar's margin flips -33,406 -> +25,536 $/MW-yr and it decides
        # 1,236.4 MW, MISO's first modelled solar entry. It moves ZERO MW
        # inside the 2021-2025 window (ENTRY_COD_LAG_YEARS=2 puts that COD in
        # 2027) and was NOT signed on band movement.
        #
        # CAVEAT for anyone building a control arm: the runner applies this
        # override to any field whose value EQUALS the ScenarioConfig default,
        # so an explicit --no-entry-vre-capacity-revenue (which sets the
        # default, False) is re-armed here and does NOT reach a gate-off
        # control for MISO. Same pre-existing property as ERCOT's
        # scarcity_price_overlay and CAISO's negative_renewable_offers. FFR-4B's
        # own controls were therefore solved BEFORE this arming landed.
        #
        # miso_rps_compliance_regions — ARMED FOR MISO by owner decision D-26
        # (sitting Addendum Y.4, signed 2026-08-06; lane ARM-MISO, measured
        # basis FFR-7B-2 §3.1,
        # docs/handoffs/ffr-7b2-rps-krow-clean-rows-2026-08-06.md). The single
        # MISO-wide RPS row silently asserts FREE INTRA-ISO REC TRADE, which is
        # FALSE in MISO (MCL 460.1029 restricts Michigan credits to in-state
        # systems; CEJA's centralized IPA procurement; MN's delivered-to-retail
        # construction) — so the ISO-wide row let Iowa's surplus pay Michigan's
        # bill. Armed, that row is REPLACED (rule 19 [R-ONE-MECH] — never
        # stacked) by the K=5 per-state compliance-region rows, each with its
        # statute's eligibility mask, its obligated-load RHS and its own $30 ACP
        # escape. ZERO fitted parameters: every obligation is copied from the
        # cited STATE_RPS_FLOORS["MISO"] derivation.
        #
        # Measured on the FFR-7B-2 bounded 2026-2030 T1-F pair (control
        # 0723d2cc432fa346 vs armed ff144cd25848e4d8, registered
        # miso-2026-2030-ffr7b2-rpsk-{ctrl,armed}): Michigan's in-state row pins
        # at its $30 ACP in EVERY year and Illinois from 2027, while the
        # delivery-based MN/WI/MO rows correctly stay slack on Plains wind — the
        # regional shortfall the control's ISO-wide row (slack until 2029)
        # cannot see. Per-zone consumer vector [0,0,30,0,30,0] (W/P/IL/IN/E/S)
        # from 2027: the control BROADCAST its scalar to the 2029 MISO-South
        # 5,650 MW backstop solar build that the armed grain correctly credits
        # 0. Dispatch, prices, builds and retirements are IDENTICAL across the
        # pair — the mechanism's only output is a price (E-1 never acquires a
        # build limb, FFR-6B §5.3), so arming re-prices compliance without
        # moving energy in this window.
        #
        # FORECAST-LANE ONLY, and the gate that makes that true is at
        # CONSUMPTION, not here: runner.py requires config.mode == "forecast"
        # before build_rps_region_arrays is reached, so a backcast-mode MISO
        # config carrying this override still resolves the legacy ISO-wide row.
        # The backcast lane is doubly insulated — run_calibration_full.py never
        # applies default_scenario_overrides at all. BOTH legs are proven by
        # test, not asserted here: tests/unit/config/test_miso_rps_region_arming.py.
        #
        # Rule 25 [R-ISO-SCOPE]: MISO ONLY. The other four RPS ISOs' single
        # ISO-wide row is arithmetically EXACT under free intra-ISO REC trade
        # (FFR-6B §2.1) and stays byte-identical; PJM/NEISO zonal rows were
        # REFUSED ON STRUCTURE (FFR-6B §7).
        #
        # miso_clean_tier_rows — ARMED FOR MISO by owner decision D-29 (sitting
        # Addendum AK.8, signed 2026-08-11; lane ARM-3-ARM, measured basis
        # ARM3-FIX §4, docs/handoffs/arm3-fix-zone-mask-2026-08-09.md). Arm 3
        # rides the Arm-2 K-row machinery above (the dependency is strict and
        # one-directional, FFR-6B §6.2 — runner.py refuses the clean family
        # without the compliance-region grain), and adds a SECOND independent
        # row family: MN carbon-free (Minn. Stat. §216B.1691 subd. 2g) and MI
        # clean (2023 PA 235 / MCL 460.1029), each with its statute's
        # eligibility mask, its obligated-load RHS and its own $30 ACP escape.
        # ZERO fitted parameters — every obligation is copied from the cited
        # MISO_CLEAN_TIER_REGIONS derivation.
        #
        # THE BLOCKERS ARE BOTH CLOSED, in this order:
        #   1. The §45U-vs-clean-dual composition (the D-22/X.2 blocker) —
        #      decided by owner D-28 option A (F2-45U, 2026-08-09): §45U left
        #      the attribute max() and composes with that max()'s winner under
        #      26 U.S.C. §45U(b)(2)(B). Measured MOOT here besides: §45U dies
        #      after 2032 (§45U(e)) and MI cannot bind before 2035, and at the
        #      $30 ACP every defensible composition coincides to the cent.
        #   2. The zone-mask defect ARM3-MEASURE found — fixed by ARM3-FIX:
        #      _resolve_clean_region_gen_idx now takes the region's
        #      eligible_zone_mask, so a clean row's GENERATOR columns obey the
        #      same mask its wind/solar columns always did. Before the fix,
        #      MISO-South nuclear satisfied Michigan's East-only row, defeating
        #      the row's own cited statutory basis.
        #
        # Measured on the fixed rows, ARM3-FIX's pre-registered 2031-2035
        # --golden-posture pair (control cd2403cc031515db vs armed
        # 9337e00504e1e72a, registered miso-2031-2035-arm3fix-clean-{ctrl,armed}):
        # MI's row is exactly 0.0000 in 2031-2034 (RHS 0 — its obligation starts
        # at 2035) and BINDS in 2035, its first statutory obligation year, pinned
        # at the $30 ACP ceiling (in-mask supply 57.351 TWh vs a 95.771 TWh
        # obligation, -38.420 TWh => ~$1.15 bn of ACP); MN stays SLACK in all
        # five years under the shipped 5-zone delivery mask. Capacity events are
        # identical to the digit in every year — the row's ONLY output is a
        # price (E-1 never acquires a build limb, FFR-6B §5.3).
        #
        # CACHE EPOCH (rule 24 [R-REGISTRY], declared by ARM-3-ARM): this arming
        # moves the MISO forecast lane's resolved default key
        # cd2403cc031515db -> 9337e00504e1e72a. Every MISO forecast bundle under
        # the pre-arm key is superseded and NONE is silently re-used, because the
        # armed value differs from the registered _CACHE_KEY_OPTIONAL_FIELDS
        # default and so enters the digest. The GLOBAL pinned default key
        # 603c2498bf71d21d is UNMOVED — the field default stays False and the pin
        # is computed with no ISO override applied.
        #
        # FORECAST-LANE ONLY, gated at CONSUMPTION exactly as Arm 2 is:
        # runner.py requires config.mode == "forecast" before the region/clean
        # arrays are built, and run_calibration_full.py never applies
        # default_scenario_overrides at all. Rule 25 [R-ISO-SCOPE]: MISO ONLY —
        # MISO_CLEAN_TIER_REGIONS has no member outside MISO, and the flag
        # carries the strict Arm-2 dependency no other ISO can satisfy.
        #
        # CAVEAT, the same one the two overrides above carry: because the runner
        # applies an override to any field still EQUAL to the ScenarioConfig
        # default, and --miso-clean-tier-rows is store_true with no negative
        # form, NO CLI invocation can reach a clean-tier-OFF MISO forecast leg
        # once this is armed. The arm-off pole is the COMMITTED ARM3-FIX control
        # bundle (key cd2403cc031515db), not a re-solve.
        #
        # entry_vre_zone_selection — ARMED FOR MISO by capx D33
        # (docs/handoffs/FINDING-capx-d33-miso-additions-repair-2026-09-02.md
        # §2). MISO is the ISO where the single-bucket VRE siting is not merely
        # coarse but WRONG in kind: RENEWABLE_ZONE_ALLOCATION sends every
        # economically-entered solar MW to MISO-South, the one model zone
        # excluded from every state compliance region's eligible-zone mask
        # (MISO_RPS_MIDWEST_FOOTPRINT_ZONES; AR/LA/MS/E-TX carry no standard),
        # so the screen priced new solar at a $0 REC credit while the run's own
        # zonal REC vector peaked at the $30/MWh ACP — and declined solar and
        # wind in EVERY screen year of the 2021-2025 T1-H hindcast against a
        # market that built 18.6 GW of solar, 76% of it outside that bucket.
        # Rule 25 [R-ISO-SCOPE]: MISO ONLY. The mechanism is ISO-agnostic and
        # the ScenarioConfig default STAYS False, so every other ISO is
        # byte-identical and arming one is its own separate decision on its own
        # evidence.
        default_scenario_overrides={
            "entry_vre_capacity_revenue": True,
            "entry_vre_zone_selection": True,
            "miso_rps_compliance_regions": True,
            "miso_clean_tier_rows": True,
            # capx D53 (2026-09-05): the retirement-screen SECTOR GATE, ARMED
            # FOR MISO ONLY by owner instruction on the measured A/B
            # (FINDING-capx-d53-2026-09-05.md §6 — all four pre-stated limbs
            # met: a pure candidate-set partition, 59 GW of regulated-utility
            # capacity removed from a merchant screen, the floor's release
            # drawn from the merchant pool at 99.8 % plant-grain precision
            # instead of 1.1 %). Rule 25 [R-ISO-SCOPE]: the ScenarioConfig
            # default STAYS False; every other ISO measures its own sector
            # census before its cell moves (the PJM leg is the named
            # successor). The bare `miso-t1h` recipe now resolves to key
            # c306ddc6d28c60c2 (the solved D53 arm); the D46 record is
            # preserved at `miso-t1h-pre-d53`.
            "retirement_sector_gate": True,
            # capx D60 (2026-09-05), executing OWNER RULING Q40 (director
            # sitting r#37, capx ledger §0ah.3 / §3): the MISO internal-supply
            # accounting ratio RE-IDENTIFIED on the dates-ON fleet ARMS FOR
            # MISO ONLY (FINDING-capx-d51-2026-09-04.md §7 — 0.854600 ->
            # 0.893436, D31's own arithmetic with the denominators net of the
            # step-1b fossil-dates channel's accredited exits; ZERO free
            # parameters, derived and reconciled by test from three committed
            # inputs). Limbs (a)/(b)/(d) read MET on the pre-stated condition;
            # (b) closed the D49 double-netting to 1.5 pts of the market's
            # offered 2024 position. Limb (c) failed BY THE LETTER and the lane
            # declined to override its own pre-registration: the owner decided,
            # on D51 §7's measured cause — every `add.shares` move is the
            # arithmetic of a total that lost 2.9 GW of gas_ct when the longer
            # position stopped the BLK-10 backstop, with every `by_tech` MW
            # outside gas_ct identical to the decimal. Rule 14: exits HARDER,
            # not easier. Rule 25 [R-ISO-SCOPE]: the ScenarioConfig default
            # STAYS False, and an ISO absent from the dated-net registry falls
            # through to D31's value even when armed, so no other ISO's number
            # moves. Bare-key consequences (PREDECL-capx-d60-2026-09-05.md §2):
            # `miso-t1h` c306ddc6d28c60c2 -> 687bd75f2828bea1 (renamed to the
            # committed D53 rider, which carries gate + ratio at
            # 6ea92547eaa62559 and differs from the bare recipe only in the
            # flipped CCS default — unreachable below 2028); `miso-t1f`
            # 8d8bc63a0d4378a9 -> 3f85ecc45d90c248, RE-SOLVED here with the
            # D45-R record preserved at `miso-t1f-pre-d60`.
            "adequacy_accounting_ratio_dated_net": True,
        },
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
    # 3,336 / 8,168 MW). Tier 3 (calibration) — verified against PJM Data Miner
    # binding frequency/direction 2026-07-10 (constants.PJM_INTERFACE_LINK_MAP).
    # Under ScenarioConfig.pjm_measured_interface_limits (backcast overlay,
    # default off) the seeded links follow the measured HOURLY series
    # (transfer-interface-limits clean datatype) in the forward direction —
    # these static seeds remain the forecast-mode forward story and the
    # reverse-direction/fallback rating, exactly as ERCOT's WESTEX/PNHNDL
    # statics pair with ercot_gtc_limits_measured.
    links = [
        # West gradient: ComEd exports east into AEP. (The real ComEd
        # boundary interface is Manual-03 CE-East, unpublished in the
        # transfer-limit feed; the earlier "5004/5005" attribution here was
        # wrong — that interface is the Keystone/Conemaugh–Juniata 500 kV
        # corridor in Pennsylvania. pjm-cong-1, 2026-07-16.)
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
    return ISOConfig(
        name="PJM",
        zones=zones,
        links=links,
        voll=2000.0,
        # THE PJM CAPACITY-MARKET CLEARING CONFIGURATION — ARMED FOR PJM by
        # OWNER RULING 2026-09-05 (in-session, on the capx D57 A/B:
        # docs/handoffs/FINDING-capx-d57-2026-09-05.md §8, "if structural
        # integrity improves but gates regress that may still be a keeper"),
        # executing D48 §8's JOINT condition — the accreditation-design
        # devintage and DR-as-supply are never armed alone, and the clearing
        # half is the mechanism that prices the budget they make consistent.
        # Three gates, one posture: (i) pjm_accreditation_design_vintage —
        # UCAP + the published pre-CIFP FPR before DY 2025/26, ELCC class +
        # post-CIFP FPR from it (capx D48); (ii) pjm_demand_response_supply —
        # the published OFFERED DR UCAP counted as supply, the peak un-netted
        # (capx D48); (iii) capacity_market_supply_clearing_by_iso[PJM] — the
        # fleet's net-ACR sell-offer stack cleared against the published VRR
        # curve, the screen's failing set the auction's uncleared set (capx
        # D57, DESIGN-capx-d54). Measured: the cleared position lands within
        # 0.5 / 1.0 / 2.8 pts of the published BRA cleared position for
        # 2022/23-2024/25 (the census evaluation sat +8.5 / +4.1 / -4.3 pts
        # away), the identity holds in every solved screen, the price reads
        # 1.5-5.7x the published because the CT / ST / oil E&AS operand is zero
        # in the hindcast prices (the named successor, the D12 scarcity-basis
        # lane), and FC-3's COMPOSITION reads worse (steam over-exits, coal
        # under-exits; recall 17 -> 12/20) while the total and the HOLD do not
        # move — accepted by the owner on rule 1 [R-STRUCT]. Armed HERE, not by
        # flipping the shared ScenarioConfig defaults, so only PJM's forecast
        # keys move (the bare pjm-t1h recipe key becomes arm A's
        # f0e050e820c1159a — the same payload arm A hashed explicitly) and
        # every other ISO's key and every backcast keeper's key is
        # byte-identical: the three dataclass defaults STAY off, __post_init__
        # still coerces them in a plain backcast, and an explicit caller value
        # (--no-pjm-accreditation-design-vintage etc.) still wins (OVERRIDE-FIX).
        # Rule 25 [R-ISO-SCOPE]: PJM ONLY — the mechanisms are generic in form
        # and PJM-scoped by data; every other ISO is byte-identical and arming
        # one is its own decision on its own evidence (matrix cells stay U/n-a).
        default_scenario_overrides={
            "pjm_accreditation_design_vintage": True,
            "pjm_demand_response_supply": True,
            "capacity_market_supply_clearing_by_iso": {"PJM": True},
            # capx D67-ARM, OWNER RULING Q52 (capx ledger §3, r#47 amendment 1:
            # "ARM for PJM") on the measured D67 A/B. The adequacy
            # requirement's OPERAND becomes PJM's own published whole-RTO
            # Reliability Requirement for delivery year Y/Y+1, in place of the
            # model's `screen peak × FPR` reconstruction, at the ONE seam
            # (`gross_adequacy_requirement_mw`) the reliability floor, the
            # reserve-margin build backstop and the CR-1 position all reach
            # through (rule 19 [R-ONE-MECH]).
            #
            # Armed the D57/Q44 way -- through this ISOConfig override, NOT a
            # flip of the shared `ScenarioConfig` default, which stays `None`
            # (so no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry is needed,
            # no other ISO's key moves, and every backcast key is
            # byte-identical; a PJM plain backcast coerces the field back to
            # `None` with its key unmoved). An explicit caller still wins:
            # `--no-capacity-adequacy-requirement-published` reaches the
            # pre-arm posture and keeps its key `15a723ba3b6dc856`.
            #
            # Rule 21 [R-DOF]: ZERO free parameters. The MW is digitized from
            # the committed `data/raw/capacity-market/demand-curve/pjm/pjm.csv`
            # `reliability_requirement` rows and reconciled against them
            # byte-for-byte by test; the vintage rule (whole-RTO, never the
            # FRR-adjusted RPM comparator) and the hold-last rule (out-of-table
            # years fall through to the FPR path, which itself holds last) were
            # both fixed before any solve and neither is selectable by a
            # result. Rule 25 [R-ISO-SCOPE]: generic in form, PJM-scoped by
            # data -- another ISO arms on its own market's published table.
            #
            # Evidence: FINDING-capx-d67-2026-09-06.md §4 (phase 0, all four
            # checks to 0.000 MW), §6.1 (the structural screen, G1-G5 PASS) and
            # §7.1 (the full span: `arm - published = 0.000 MW` in all four
            # screened delivery years, and the pre-declared signs 4 of 4 --
            # 2022/23 and 2023/24 FALL, 2024/25 and 2025/26 RISE, which is why
            # this is a real operand rather than a one-way residual improver).
            # Execution: PRECOMMIT-capx-d67arm-2026-09-06.md.
            "capacity_adequacy_requirement_published_by_iso": {"PJM": True},
            # capx D75-R-ARM, OWNER RULING Q55 (capx ledger §3, r#51: "ARM for
            # PJM") on the measured D75-R A/B. The VRE HALF of the D48
            # devintage: PJM wind and solar are accredited at the delivery
            # year's OWN published ELCC class ratings (DY 2023/24 15 / 38 /
            # 54 %, DY 2024/25 21 / 33 / 50 % from the December 2023 FINAL
            # study, DY 2025/26 38 / 10 / 14 %) instead of
            # RENEWABLE_ELCC_CURVES_BY_ISO["PJM"], which is digitized from the
            # 2026/27+ MARGINAL-ELCC ratings and CLAMPS on every PJM pool in
            # the window -- i.e. applies one post-reform rating to three
            # delivery years that cleared under a different published
            # construct. Rule 14 [R-ACCURATE] is the reason and is dispositive
            # on its own: these are the ISO's own published accreditation
            # values for the year each auction actually cleared on, and the
            # rule requires preferring them WHATEVER they do to the fit.
            #
            # A SUB-GATE INSIDE THE D48 FAMILY, never a mechanism beside it
            # (rule 19 [R-ONE-MECH]): the predicate
            # (retirements.vre_accreditation_vintage_armed) requires this
            # field AND `pjm_accreditation_design_vintage` above AND a registry
            # entry for the ISO, so the VRE half can never be vintaged while
            # the thermal half is not -- a mixed accreditation basis is the
            # exact failure D45 §2.2 measured and D48 exists to remove. It
            # needs its own key because D48's is armed for PJM by ruling right
            # here, so keying off it alone would have armed an untested
            # mechanism BY DEFAULT the moment D75-R landed.
            #
            # Armed the D57/Q44 way -- through this ISOConfig override, NOT a
            # flip of the shared `ScenarioConfig` default, which stays `False`
            # (so no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry is needed,
            # no other ISO's key moves, and every backcast key is
            # byte-identical; a PJM plain backcast coerces the field back to
            # `False` with its key unmoved at 3a566deac3a85682). An explicit
            # caller still wins: `--no-pjm-vre-accreditation-vintage` reaches
            # the pre-arm posture and keeps its key `a9c66d8ea25acb9d`.
            #
            # Rule 21 [R-DOF]: ZERO scalar fields and ZERO free parameters
            # beyond the ONE cross-vintage reconciliation ruling R1 authorised
            # -- PJM's own published Table-5 installed-MW mix
            # 1189/(1189+8713) = 12.01 % fixed, re-derived from the committed
            # rows by test, admitted under rule 14's misalignment exception
            # because PJM publishes no pre-reform fixed/tracking pairing. The
            # conclusion is mix-INSENSITIVE (DY 2024/25's break-even blend
            # 0.5527 exceeds PJM's own tracking rating 0.50, so the implied
            # fixed share is negative -- no mix can flip the sign). Every
            # rating is reconciled byte-for-byte to
            # data/raw/capacity-market/elcc/pjm/pjm.csv by test. Rule 25
            # [R-ISO-SCOPE]: PJM-only by construction and locked by test across
            # the other five ISOs, whose accreditation constructs are their own
            # (CAISO NQC/exceedance, NYISO CAFs, MISO class-average, NEISO no
            # adopted study, ERCOT energy-only).
            #
            # Evidence: FINDING-capx-d75r-2026-09-06.md §3 (phase 0, zero LP:
            # accredited VRE DOWN 754.633 / 332.854 / 148.315 MW, and NOT a
            # uniform derate -- the two classes move in OPPOSITE directions),
            # §4 (the DY 2023/24 screen, PASS on all four legs), §5.1 (the
            # solve reproduces phase 0 to ~0.001 MW in every in-scope year),
            # §5.2 (ALL 26 SCORED BANDS BYTE-IDENTICAL -- nothing flips in
            # either direction -- with FC-3 improving inside its still-failing
            # bands) and §8 (the recommendation and this posture). What it does
            # NOT close, stated at the gate: the model still over-retires
            # (17.294 vs 15.062 GW actual), `unit_recall_gt300` is UNCHANGED at
            # 0.65 -- the repair removes false exits, it does not find missing
            # true ones -- and the 2024/25 and 2025/26 census move the wrong
            # way through fleet propagation (§5.4's fired STOP), which is D66
            # card B's remaining half. Execution:
            # PRECOMMIT-capx-d75r-arm-2026-09-06.md.
            "pjm_vre_accreditation_vintage": True,
            # capx D84-ARM, OWNER RULING 2026-09-07 (served by
            # FINDING-capx-d84-2026-09-07.md §8's card; execution
            # PRECOMMIT-capx-d84arm-2026-09-07.md) on the measured D84 A/B.
            # The THERMAL RATING half of the same D48 accreditation-design
            # devintage the two entries above already carry: PJM's
            # dispatchable classes are accredited at the delivery year's OWN
            # published ELCC class ratings
            # (constants.THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO) instead of
            # the single-vintage 2026/2027 BRA table
            # (THERMAL_ELCC_CLASS_RATING_BY_ISO), which the model applies to
            # EVERY post-reform delivery year — including DY 2025/2026, the
            # FIRST year of the ELCC-class design
            # (THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"]),
            # whose own published final (3IA, posted 2025-03-12) ratings
            # differ: gas CC 78 vs 74, CT 63 vs 60, steam 74 vs 73, diesel
            # 92 vs 91 (nuclear and coal equal).
            #
            # A SUB-GATE INSIDE the D48 family, not a mechanism beside it
            # (rule 19 [R-ONE-MECH]): the predicate also requires
            # ``pjm_accreditation_design_vintage``, which this same override
            # block arms, so the RATING and BASIS axes are devintaged together
            # or not at all. Pre-reform delivery years never reach the
            # registry — the basis resolver has already returned "ucap" — so
            # the two axes COMPOSE rather than stack.
            #
            # WHY, and the rule that decides it: rule 14 [R-ACCURATE], alone
            # and dispositive — these are PJM's OWN published accreditation
            # values for the delivery year the auction actually settled on.
            # The rule requires preferring the published vintage WHATEVER it
            # does to the fit, and D84 states it would have built the same
            # mechanism had the residual moved the other way (rule 1
            # [R-STRUCT]: a vintage is never selected by what it does to a
            # criterion). ZERO scalar fields, ZERO free parameters and —
            # unlike the VRE half — ZERO reconciliations (PJM rates each
            # model thermal class with exactly one published class); every
            # rating reconciles byte-for-byte to
            # data/raw/capacity-market/elcc/pjm/pjm.csv by
            # tests/unit/data/test_thermal_elcc_vintage_ratings.py.
            #
            # MEASURED (FINDING §5): accredited thermal +3,105.648 MW in DY
            # 2025/2026 — the ONLY window delivery year on the ELCC axis —
            # against the identity's predicted +3,105.6475, a gap of
            # 0.00046 MW; exactly 0.000 MW and byte-identical ledgers in
            # 2021-2024; only gas_cc / gas_ct / oil / gas_st move. ALL 361
            # substantive scored records byte-identical between arms (26
            # bands, zero flips either way).
            #
            # WHAT IT DOES NOT CLOSE, at the gate: all three published DY
            # 2025/26 comparators move AWAY (cleared MW +481.708 further
            # above published on both D66 frames; price 34.961 $/MW-day
            # further below the published 269.92) — rule 14's "treat the
            # worse fit as a discovered bug" case, reported at full
            # magnitude and never a reason to restore a foreign vintage;
            # unit_recall_gt300 and false_retire stay FAIL; and the Q56/D57
            # collision below (100.0 % of the newly-uncleared MW is
            # sector-1, so the clearing's failing set moves while nothing in
            # it can exit) is REPORTED, not resolved (FINDING §9 item 1).
            #
            # POSTURE: this ISO override, never a (b'-1) shared-default flip.
            # Measured at the arm over every committed run config
            # (scripts/probes/capxd84arm_iso_override_no_op_check.py, records
            # docs/handoffs/d84arm/): 33 of 227 move, ALL PJM/forecast; zero
            # non-PJM and zero backcast, so every other ISO and every
            # backcast keeper is byte-identical. Bare pjm-t1h
            # f736025631d0d27e -> b9fa47dedb6c3319;
            # --no-pjm-thermal-accreditation-vintage reaches the pre-arm
            # posture and keeps its key.
            "pjm_thermal_accreditation_vintage": True,
            # capx D78-ARM, OWNER RULING Q56 (served by
            # FINDING-capx-d78r3-2026-09-06.md §5 "RECOMMEND ARM"; ruled ARM
            # in this lane's charter) on the measured D78-R2 / D78-R3 full
            # window. The retirement-screen SECTOR GATE (capx D53 / D78): a
            # unit whose plant's EIA-860 ``Sector`` is 1 (a regulated
            # electric utility, read at the run's active vintage) still
            # OFFERS its accredited MW into the D57 capacity clearing at its
            # net-ACR cap -- PJM's must-offer requirement (Manual 18 Rev 62
            # §1.2 / §5.4.1) keys on existing-and-in-footprint, never on
            # ownership -- but is partitioned out of the step-3 economic
            # EXIT decision, which models a MERCHANT choice its owner never
            # faces: a utility exit is an IRP / rate-case filing carried by
            # step 0's instruments and step 1b's owner-filed dates.
            #
            # Armed the D57/Q44 -> D67-ARM -> Q55 way -- through this
            # ISOConfig override, NOT a flip of the shared `ScenarioConfig`
            # default, which stays `False` (so no
            # `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry is needed, no
            # other ISO's key moves, and every backcast key is byte-identical;
            # a PJM plain backcast coerces the field back to `False` with its
            # key unmoved at 3a566deac3a85682). An explicit caller still
            # wins: `--no-retirement-sector-gate` reaches the pre-arm (Q55)
            # posture and keeps its key `b518f5fe7d02f961`; the bare recipe
            # advances to `fb16fda2ddb0a94a`.
            #
            # Rule 21 [R-DOF]: ZERO free parameters -- a PARTITION on one
            # published per-plant boolean; no weight, threshold, share or
            # fitted value. Rule 19 [R-ONE-MECH]: one seam
            # (`exit_exempt_unit_ids`, the screen's sole exemption seam since
            # D78-R2 deleted `exempt_unit_ids`), and no unit's exit is decided
            # twice. Rule 25 [R-ISO-SCOPE]: a PJM posture on PJM's OWN
            # evidence -- MISO's D53 arm transferred nothing; PJM's cell moved
            # U -> O -> K on D58 / D78 / D78-R / D78-R2 / D78-R3, all PJM
            # legs. Rule 14: the decision rests on the STRUCTURAL limbs, never
            # on the residual -- the partition is exact in all five years
            # (W1/W2/W3: every control-only failing row is sector-1, the
            # arm-only set is EMPTY, zero sector-1 rows in any decision
            # ledger), the window decided total lands on the pre-registered
            # exact-partition point value 9,394.156 MW to the milli-MW (W4'),
            # the whole-ledger diff finds zero unclassified rows in five
            # years, and purity holds on D57 §4's PER-DELIVERY-YEAR zero-E&AS
            # set (W5'': 1,354 gated shared rows, 0 moved -- every mover
            # outside its DY's declared set). Reported at full magnitude and
            # NOT a criterion in either direction: retire.total_gw 18.058 ->
            # 15.937 GW (FAIL -> PASS against 15.062 actual), unit_recall_gt300
            # FALLS 0.650 -> 0.550 (a partition removing matched sector-1
            # exits must), the 2025/26 clearing price 358.267 -> 236.945
            # $/MW-day on the steep VRR limb, and limb (d) cannot discriminate
            # on recall in either leg. Evidence:
            # FINDING-capx-d78r2-2026-09-06.md §§3-8 and
            # FINDING-capx-d78r3-2026-09-06.md §§3-5. Execution:
            # PRECOMMIT-capx-d78arm-2026-09-06.md. The arming lane still OWES
            # the armed pjm-t1h re-solve, its scoring and its registration
            # (Q56 reads ARM, REGISTRATION REQUIRED); this override is the
            # config act alone and claims nothing about a registered bundle.
            "retirement_sector_gate": True,
        },
    )


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
    # capx D60 (2026-09-05), executing OWNER RULING Q41 (director sitting r#37,
    # capx ledger §0ah.3 / §3): NYISO's TWO adequacy-requirement devintage gates
    # ARM AS THIS ISO'S FORECAST DEFAULT (FINDING-capx-d52-2026-09-04.md §8(1),
    # recommendation ARM BOTH). NYISO declared no ISO-level overrides before
    # this; these two are the first.
    #
    # WHAT THEY ARE. `nyiso_requirement_forecast_peak` prices the NYCA
    # requirement on the NYSRC ICAP-market FORECAST peak of the capability year
    # (Table D.2 col. 1) instead of the model's own peak; a capability year
    # outside the published table returns the model's peak UNCHANGED, so the
    # forward horizon keeps a forecast peak and never a held-last MW.
    # `nyiso_requirement_vintage_factors` prices the requirement FACTOR at that
    # capability year's EC-adopted IRM x (1 - NYCA derate) (Table D.2 cols. 2-3)
    # instead of the single mixed vintage 1.244 x (1 - 0.1321); beyond the last
    # published pair it holds that pair's ratio, 1.244 x 0.870 = 1.0823, +0.24 %
    # over the shipped composite. Together the IN-TABLE requirement IS Table
    # D.2's published NYCA UCAP requirement to under 1 MW — the model's peak
    # drops out, exactly as under the NEISO Net ICR / PJM FPR paths.
    #
    # WHY ARMED (rules 1 / 13 / 14 / 21 / 23). Published per-capability-year
    # market-design parameters on the published forecast peak, digitized into
    # the committed demand-curve/nyiso/nyiso.csv rows and reconciled to their
    # source by test; ZERO free parameters; vintage-gated (the row of capability
    # year Y/Y+1 is read in model year Y only, every parameter in it fixed
    # before that year begins), so the identical construction regenerates
    # forward from the Gold Book + the adopted IRM. Measured: the position
    # artifact D45 §6 named is CLOSED — the model's census moves from +9.4 /
    # +5.2 / +7.3 pts LONG to 0.6-2.6 pts SHORT of the market's published
    # position in 2023 / 2024 / 2025, inside the +/-3-point band; the rule-22
    # LOYO is 3/3 PASS with every fold improving and an identical fleet; and the
    # shipped-default cost is exactly ZERO (FC-3 byte-identical to the control
    # in every row). The NYCA ICAP demand curve stays OFF — D52 §8(2)
    # recommended DO NOT ARM and D59 re-affirmed it; so does
    # `locality_capacity_curves` (D59). Rule 25 [R-ISO-SCOPE]: both
    # ScenarioConfig defaults STAY False and the registries are NYISO-keyed, so
    # no other ISO moves; each is a separate gate so either can be disarmed
    # alone. Both are coerced to their dataclass default in a plain backcast
    # (capacity evolution never runs there), so no backcast keeper key can move.
    # Bare-key consequences (PREDECL-capx-d60-2026-09-05.md §2): `nyiso-t1h`
    # 91686abe7a744a88 -> 6e70a637b3465542 (renamed to the committed D52 arm,
    # which carries both gates at 911371a8cf23d5c3 and differs from the bare
    # recipe only in the flipped CCS default); `nyiso-t1f` cc7d1050a8090c76 ->
    # 19a9690bb12c8459, RE-SOLVED here with the D45-R record preserved at
    # `nyiso-t1f-pre-d60`.
    return ISOConfig(
        name="NYISO",
        zones=zones,
        links=links,
        voll=2000.0,
        default_scenario_overrides={
            "nyiso_requirement_forecast_peak": True,
            "nyiso_requirement_vintage_factors": True,
        },
    )


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
    ``scripts/data/derive_load_shares.py neiso`` to derive measured shares and hourly
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


def _spp_config() -> ISOConfig:
    """Build the Southwest Power Pool (SPP) topology configuration.

    **Two zones**, drawn along the North–South seam the SPP MMU itself names
    as the footprint's structural price divide (owner ruling P1, SPP desk
    sitting r#2, 2026-09-06 — "2 zones now; two ranked levers";
    ``docs/handoffs/spp-desk-ledger-2026-09.md`` §2):

    - **SPP-North** — ND, SD, NE, MN, MT, IA, KS, MO plus the 19.5 MW of
      Colorado solar: the coal / nuclear / wind tier (both nuclear units,
      Wolf Creek KS and Cooper NE, sit here).
    - **SPP-South** — OK, TX (Panhandle + east Texas), NM, AR, LA: the
      gas-heavy tier (the gas-CC fleet concentrates in OK/TX). Wyoming is
      NOT in the footprint — no EIA-860 plant carries balancing authority
      ``SWPP`` there (``docs/multi-iso/spp-data-audit.md`` §2.4).

    Fleet partition: the FIPS state map ``zone_assignment._SPP_STATE_ZONES``
    (the seam runs along the KS/OK and MO/AR state lines, so no state
    straddles it on the plant side). Load partition: the EIA-930 sub-BA
    grouping North = {EDE, INDN, KACY, KCPL, LES, MPS, NPPD, OPPD, SECI,
    SPRM, WAUE, WR}, South = {CSWS, GRDA, OKGE, SPS, WFEC} (audit §5 row 5).
    ``EDE`` (Liberty / Empire District, 1.9 % of system energy) is the one
    sub-BA that genuinely straddles — it serves MO, KS, OK and AR — and is
    placed NORTH because its service territory is centred on Joplin,
    Missouri (a North state under the plant-side map), so its fleet and its
    load stay on the same side of the seam; moving it South would shift the
    split by 1.9 points and put a Missouri-centred sub-BA's load in the zone
    whose fleet holds no Missouri plant.

    Load shares are the static fallback used only when the per-zone hourly
    sub-BA demand shapes are absent (SPP-32 curates them); the values are the
    measured 2023-2025 energy shares of the two sub-BA groups computed from
    ``data/raw/zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv``
    (landed by SPP-11; 17 sub-BAs, 26,297 hours, a complete partition of the
    BA demand to 0.9995-0.9999): North 447.675 TWh / South 425.770 TWh over
    the three years = 0.5125 / 0.4875 (per year 0.5149 / 0.5129 / 0.5099).
    Independent cross-check from a DIFFERENT source: the SPP MMU State of the
    Market 2025 Fig. 2-8 participant roll-up gives North 50.2 % / South
    49.6 % of 2025 energy (audit §5 row 6) — within one point, so the two
    attributions agree.

    Congestion structure. The single N↔S ``TransferLink`` is the only
    structure beyond copperplate. Its TTC (3,400 MW) is a **rule-14
    reconciled figure derived from SPP's own published flowgate limits by
    lane SPP-53** (owner ruling P13; construction fixed in
    ``PRECOMMIT-spp-53-2026-09-07.md`` before any limit was read; every
    number in ``FINDING-spp-53-2026-09-07.md``) — see the citation comment
    on the link below for the two measured legs, the misalignment statement
    and the rejected alternatives. It replaced SPP-20's 48,700 MW Tier-3
    placeholder (the North zone's EIA-860 2025 ER summer capability, an
    upper bound that could not bind — ``FINDING-spp-20`` §3, §5 R-6). No
    public document states an SPP North↔South rated interface — SPP-13's
    row-11 sweep found the ITP Constraint Assessment ratings are NDA / CEII
    (FINDING-spp-13 §0) — which is why the value is derived from the
    binding-constraint archive rather than transcribed. The MMU's ">6,000 MW
    SPP↔MISO AC interties" is a SEAM rating, not the internal corridor, and
    is deliberately not borrowed. The link is symmetric by construction,
    which is right: the MMU records the North−South hub spread REVERSING
    sign for six (DA) to eight (RT) months of 2025 (FINDING-spp-12 §4), and
    the corridor's South→North-loaded flowgates give 4,206 MW by the same
    construction (FINDING-spp-53 §4).

    What two zones cannot represent, said here rather than found in a
    residual (audit §6.1): seven of the ten highest-valued 2025 constraints
    are INSIDE Oklahoma (Osage–Webber Tap, Russett–South Brown), and three
    of the four 2024 Frequently Constrained Areas (OKC, Tulsa, Lubbock) sit
    inside SPP-South. The SPS / Texas-Panhandle pocket (lever SPP-54) and an
    Oklahoma pocket (lever SPP-57) are pre-declared structural levers,
    ranked by the per-flowgate binding-share evidence when the binding-
    constraint archive lands (FINDING-spp-12 §5). The published hubs are
    node clusters (North ≈ Nebraska, South ≈ central Oklahoma), so the hub
    spread is a two-point spread, not a zonal price — SPP-40's PRECOMMIT
    states this limitation (audit §6.1).

    No import node (G7): SPP's seams are represented by the served measured
    EIA-930 ``Total interchange`` schedule (``_SCALAR_INTERCHANGE_ISOS``,
    owner ruling P2, positive = net export) plus three DEFAULT-OFF
    ``NeighborInterface`` blocks (MISO / AECI / ERCOT — rulings P2/P3) in
    ``model/interchange/spec.INTERFACE_NEIGHBORS["SPP"]``; the ERCOT DC ties
    (~1.5 % of peak) are a neighbour, not an import node.

    Market design: energy-only with a bilateral resource-adequacy obligation
    (no centralized capacity market), so SPP is deliberately ABSENT from
    ``capacity_market.MARKET_DESIGN`` and takes ``DEFAULT_MARKET_DESIGN``.
    Reserve co-optimisation (P4) and any scarcity / VRL overlay (P5) are
    deferred to SPP-56 and SPP-55, so there are no
    ``default_scenario_overrides``.
    """
    zones = [
        # Static fallback = measured 2023-2025 sub-BA energy shares (EIA-930
        # sub-BA demand, SPP-11 intake; sum = 1.0000). See the docstring.
        Zone(name="SPP-North", iso="SPP", load_share=0.5125),
        Zone(name="SPP-South", iso="SPP", load_share=0.4875),
    ]
    # N<->S link TTC = 3,400 MW: the North->South transfer at which the
    # corridor's limiting flowgate reaches its own effective limit (the
    # FCITC reading), derived by lane SPP-53 from SPP's OWN published limits
    # under a construction fixed BEFORE any limit was read
    # (docs/handoffs/PRECOMMIT-spp-53-2026-09-07.md §2.1; result and every
    # per-constituent number: FINDING-spp-53-2026-09-07.md §3-§5). Two
    # measured legs, no free parameter:
    #   L_f  = per-constituent limit-at-bind, the median `Real Time Effective
    #          Limit` over BINDING/BREACHED intervals of the 2026-03-17 ->
    #          2026-09-05 daily RTBM binding-constraint files (the ERCOT
    #          derive_ttc_limits.py instrument; reduced sidecar
    #          data/raw/spp-binding-constraints/rtbm_bc_corridor_limits_2026
    #          .parquet), else the registry rating (Temp_Flowgate.csv /
    #          Flowgates.csv) when the element bound < 100 intervals;
    #   psi_f = the constituent's sensitivity to a North->South hub transfer,
    #          identified from SPP's own price decomposition: hourly RT
    #          (SPPSOUTH_HUB - SPPNORTH_HUB) regressed on every constraint's
    #          hourly mean |shadow price| over 2023-2025 (OLS, HC1; 12 of the
    #          30 corridor constituents identify with psi > 0, t >= 2).
    #   TTC  = binding-hours-weighted median of T*_f = L_f / psi_f over the
    #          identified constituents = 3,355 MW -> 3,400 (nearest 100).
    # The median falls on the corridor's dominant constituent, the Franklin
    # 161/69 kV transformer (WR; 4,103 of the 2023-25 corridor's binding
    # hours; 100 MW registry rating / psi 0.0298); its neighbours read
    # LEC-LAWH 3,487, Sibley 345/161 kV 4,574, Mullergren-Ellsworth 6,408,
    # Cooper-St Joe 345 kV 6,437, Nashua 345/161 kV 9,378 MW. The
    # South->North-loaded set (psi < 0: Viola transformer, Stilwell-Redel,
    # Spearville-Mullergren, ...) gives 4,206 MW by the same rule, so the
    # symmetric link is within 25 % of the corridor's own reverse reading.
    # Rule 14 [R-ACCURATE] MISALIGNMENT, stated: (i) 2026 limits applied to a
    # 2023-2025 solve (no in-window limit column exists, FINDING-spp-14
    # §5.4); (ii) a flowgate limit is an element-under-contingency rating,
    # NOT a corridor capability -- SPP publishes no N<->S interface flowgate
    # (PRECOMMIT §1.2 census: the only cut-crossing SWPP element is the SPS
    # tie), so this is the N_TO_H case of _ercot_config, reconciled through
    # psi rather than used literally (a literal 100 MW element rating would
    # island two zones whose measured mean |hub spread| is $12-17/MWh);
    # (iii) psi is the Nebraska-hub -> central-Oklahoma-hub sensitivity, not
    # the bubble-to-bubble transfer PTDF; (iv) leave-one-year-out re-fits of
    # psi move the same construction to 2,645 / 3,681 / 11,121 MW (drop 2025
    # / 2023 / 2024) -- the honest width, reported beside the pooled value.
    # Residual-blind cross-check (PRECOMMIT §4): 3,400 < B_plaus 23,300 <
    # B_hard 37,400 MW, so the link CAN bind, unlike the 48,700 MW SPP-20
    # placeholder it replaces. Vintage 2026 (TRANSMISSION_BASE_STATIC_VINTAGE
    # ["SPP"]). Never tuned to a price or flow residual -- no SPP residual
    # exists; rejected alternatives (the literal dominant-flowgate rating,
    # a simultaneous-transfer sum, the hour-wise minimum) in PRECOMMIT §2.
    _ns_corridor_ttc = 3400.0
    links = [
        TransferLink(
            from_zone="SPP-North", to_zone="SPP-South", ttc_mw=_ns_corridor_ttc
        ),
    ]
    # voll = $2,000/MWh (owner ruling P10, desk sitting r#3, 2026-09-06):
    # the FERC Order 831 hard ceiling for COST-VERIFIED incremental energy
    # offers. Both published numbers, so neither is mistaken for the other:
    # SPP's posted Safety-Net Energy Offer Cap is $1,000/MWh (Integrated
    # Marketplace Protocols 119 §8.2.5, printed pp. 356-357, transcribed in
    # data/raw/spp-planning/README.md §2); offers above it must follow the
    # Mitigated Offer Development Guidelines (p. 344) and are capped at
    # $2,000/MWh (SPP Tariff Attachment AF §3.2; SPP MMU Order 831
    # Verification FAQ v4.0 Q25 p. 5 — audit §5 row 2). SPP's own scarcity
    # ceiling is the VRL stack ($250/MW spinning reserve, $50,000/MW global
    # power balance; Protocols Exhibit 4-1 pp. 71-72), which SPP-55 designs
    # against — deliberately not seeded here (P5).
    return ISOConfig(
        name="SPP",
        zones=zones,
        links=links,
        voll=2000.0,
    )


def _nwpp_config() -> ISOConfig:
    """Build the Northwest Power Pool (NWPP) topology configuration.

    **NWPP is a POOL OF SEVENTEEN BALANCING AUTHORITIES, not an ISO and not a
    BA** — the first many-to-one region in the registry (owner ruling N1, NWPP
    desk sitting #1, 2026-09-13; ``docs/multi-iso/nwpp-addition-plan-2026-09.md``
    §3): the Hermiston provenance is the illustration, plant 54761 (Hermiston
    Generating) filing under balancing authority ``PACW`` and plant 55328
    (Hermiston Power Partnership) under ``GRID`` one fence apart, so the
    footprint is the union BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD
    SCL TPWR AVRN GRID WAUW NEVP; Canada (BC Hydro, AESO) is inside the real
    pool and OUT of the footprint because it is entirely outside EIA-930, so it
    can only ever be an exogenous seam. The fleet is admitted by the two-key
    predicate ``BA ∈ NWPP_BAS AND NERC Region == "WECC"``
    (``fleet.models.ISO_NERC_REGION_ADMISSION``) — 939 plants / 1,930 operable
    generators / 98,238.1 MW at the EIA-860 2025 Early Release
    (``docs/multi-iso/nwpp-data-audit.md`` §2.1, §2.8(a)).

    **Five zones, each a WHOLE-BA GROUP** (owner ruling N5, sitting #4,
    2026-09-14). There is no EIA-930 sub-BA product for any of the seventeen,
    so a zone may not split a BA (plan §7 gate G18); the map is keyed on the
    balancing-authority code (``zone_assignment._NWPP_BA_ZONES``), never on
    state — a state here holds several BAs and a BA several states:

    - **NWPP-NW** — BPAT · PSEI · SCL · TPWR · CHPD · DOPD · GCPD, plus AVRN's
      Columbia-Gorge generation (no load). 43,619.1 MW; winter-peaking in
      every year (S/W 0.86 / 0.80 / 0.82).
    - **NWPP-OR** — PGE · PACW, plus GRID's Hermiston generation (no load).
      7,650.5 MW; summer / summer / winter (1.09 / 1.06 / 0.98).
    - **NWPP-INLAND** — IPCO · AVA · NWMT · WAUW. 12,574.2 MW; the weakest cut
      (within-group load correlation 0.682 vs 0.631 against the rest) and a
      MIXED regime: winter-peaking AVA/NWMT beside summer-peaking IPCO/WAUW.
    - **NWPP-EAST** — PACE (PacifiCorp East: UT, WY, SE Idaho). 18,737.4 MW;
      summer (1.24 / 1.34 / 1.30).
    - **NWPP-SNV** — NEVP, which is ALL of NV Energy, northern Nevada
      included (``SPPC`` is not a separate EIA-930 BA; the name invites a
      mis-file, NWPP-12 §3.2). 15,656.9 MW; summer at 1.95 / 2.06 / 1.87 × its
      own winter load, and load correlation 0.048 with NWPP-NW.

    Declared open, not hidden (N5): GCPD's placement is disputed by load
    correlation (0.90 with IPCO, 0.08-0.16 with its own zone) and stays,
    because load correlation is not a transmission constraint; and the
    largest published constraints in the footprint (WECC Paths 4/86/87/88 at
    4.8-10.7 GW) are BPA-INTERNAL east-west cuts a whole-BA zoning cannot
    represent at all — a property of the zoning to state on the first keeper.

    Load shares are the static fallback used only when the per-zone hourly
    shapes are absent (the per-BA regroup is lane NWPP-32's zero-derive
    item): the pooled 2023-2025 energy shares of the members'
    ``Demand (MW) (Adjusted)`` series, UTC-joined onto the Pacific local year
    (NW 0.3769 · OR 0.1509 · INLAND 0.1533 · EAST 0.1808 · SNV 0.1381; per
    year NW 0.3778 / 0.3740 / 0.3788, SNV 0.1355 / 0.1411 / 0.1376). Cross-
    check on the audit's independent 2024 measurement (audit §9.2): 37.41 /
    15.09 / 15.29 / 18.11 / 14.10 — identical to the fourth decimal.
    Coincident peaks reproduce 49,290 / 52,564 / 50,953 MW to the MW. AVRN
    and GRID carry exactly 0.0 of the load (null demand in all 26,304 hours).

    **Transfer limits — every link states its tier** (N5; WECC 2024 Path
    Rating Catalog Public Version, transcribed with printed pages in
    ``data/raw/nwpp-planning/README.md`` §1; convention of
    ``docs/multi-iso/04-transmission-zones-and-congestion.md``). Published
    ratings are asymmetric, so each rated boundary is a PAIR of one-way links
    (the ERCOT Northeast↔North precedent), never a symmetric average:

    - **EAST↔SNV — Tier 1 candidate.** Path 35 TOT 2C, one line (Red
      Butte–Harry Allen), printed p. 36: N→S 600 / S→N 580 MW.
    - **INLAND↔SNV — Tier 1 candidate.** Path 16 Idaho–Sierra, one line
      (Midpoint–Humboldt), p. 19: N→S 500 / S→N 360 MW.
    - **INLAND↔EAST — Tier 2.** Path 20 "Path C" (Pre-Gateway), p. 23: N→S
      (Idaho→Utah = INLAND→EAST) 1,600 / S→N 1,250 MW. Misalignment stated:
      PacifiCorp's SE-Idaho territory is inside PACE, so part of Path C is
      PACE-internal.
    - **NW↔INLAND — Tier 2, an AGGREGATION of three rated paths**, none of
      which is the whole boundary: Path 8 Montana-to-Northwest (NWMT↔BPA,
      p. 15) E→W 2,200 / W→E 1,350; Path 6 West of Hatwai (AVA↔BPA, p. 13)
      E→W 4,277 / W→E "Not defined"; Path 14 Idaho-to-Northwest (IPCO↔BPA,
      p. 17) E→W 2,400 / W→E 1,200–1,340 (winter 2,400). INLAND→NW = 2,200 +
      4,277 + 2,400 = 8,877 MW; NW→INLAND = 1,350 + 1,200 = 2,550 MW, taking
      the LOWER end of Path 14's range and 0 for Path 6's undefined W→E rating
      — a stated gap, not a guess. NorthWestern's own caveat rides with every
      rating here: "ATC is much less than TTC" (2026 MT IRP printed p. 122), so
      a path rating is a ceiling the real market does not reach.
    - **NW↔OR — Tier 3, a DOCUMENTED ABSENCE.** No WECC path rates a
      BPAT/PSEI/SCL/TPWR/CHPD/DOPD/GCPD ↔ PGE/PACW interface and none will:
      BPA and the PGE/PacifiCorp-West systems interconnect at many points
      around Portland and the Willamette Valley, exactly the case WECC's path
      process produces no number for (README §1.4; the full 89-slot table of
      contents was read). Paths 4/5/71/86/87/88 are east-west cuts across the
      Cascades and the Columbia, NOT BA interfaces — Path 5 mixes BPA-internal,
      BPA→PGE and PGE-internal limbs in one 7,200 MW rating — and must not be
      borrowed. The link therefore carries a NON-BINDING PLACEHOLDER by the
      SPP-20 construction (FINDING-spp-20 §3): the sending zone's own
      nameplate, 43,619.1 → 43,600 MW, an upper bound that cannot bind (OR is
      a leaf whose 2024 peak is ~9.9 GW). Pre-declared as lever NWPP-55; never
      tuned to a residual (rules 1 / 13 / 14).

    No import node (G7): the seams are the served measured schedule
    (``eia930.envelopes.nwpp_net_interchange``, ``_SCALAR_INTERCHANGE_ISOS``,
    owner ruling N4 — the PJM/NYISO/NEISO/SPP precedent) plus three
    DEFAULT-OFF ``NeighborInterface`` blocks (CAISO / WECC_SW / WECC_CAN) in
    ``model/interchange/spec.INTERFACE_NEIGHBORS["NWPP"]``. The served
    construction and the BPAT/GRID source conflict it works around are stated
    on that function, not repeated here.

    Market design (owner ruling N7): no capacity market anywhere in the
    footprint, so NWPP is deliberately ABSENT from ``capacity_market.
    MARKET_DESIGN`` / ``_CURVE_ISOS`` / ``_CAPACITY_ISOS`` and takes
    ``DEFAULT_MARKET_DESIGN`` (``capacity_market=False``, the ERCOT/SPP
    branch). The reliability floor reads ONE scalar
    ``PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"]`` against the footprint
    COINCIDENT peak — summer in all three years — and the two-regime mismatch
    is DECLARED here at full magnitude rather than softened: 8 winter-peaking
    BAs, 6 summer, 1 flipping (PACW); NWPP-NW peaks in WINTER every year
    (0.86 / 0.80 / 0.82) while NWPP-SNV peaks in SUMMER at 1.95 / 2.06 / 1.87×
    its own winter load, and NWPP-INLAND mixes both regimes inside one zone,
    so even a per-zone seasonal PRM would average two regimes there. A
    per-zone seasonal requirement is pre-declared lever NWPP-57, not a change
    to a dict every registered region reads. WRAP is a FORECAST-SIDE object
    only: its first binding season is Winter 2027-28, from 1 November 2027
    (WPP BPM 109 printed p. 4), two years past the backcast window.

    Fleet representation (owner ruling N8): legacy heat-rate bins
    (``use_campd_bins=False`` — NWPP is absent from ``CAMPD_BINNING_ISOS``,
    so the runner's per-plant path is never entered). CAMPD reaches 30.98 % of
    nameplate / 41.8-43.6 % of energy, and 36.3 % of the footprint is hydro
    that CEMS can never cover; per-plant binning is a W5 lever.

    Offer-curve bands stay 1.0 (gate G5): NWPP takes the generic base curve
    with no per-ISO delta. ``pipeline/backcast_config.py`` neutralizes the
    generic gas bands for every non-ERCOT region and deep-merges the SPP
    coal identity bands (``_SPP_OFFER_CURVE``, all four bands 1.0) for NWPP
    too, since NWPP is the second fallback region whose fleet carries coal
    (rule 25 ``[R-ISO-SCOPE]``). The rule-1 carve-out authorizes tuning
    MARKET offers, and most of this footprint is cost-based
    vertically-integrated dispatch (Electric Utility sector 69.7 % of
    nameplate). No ``default_scenario_overrides``.

    No reserve design (``model/reserves/spec.py``): ``energy_reserve_coopt``
    keeps its default ``False``, so the co-optimized design dispatch is never
    entered. The pool's contingency reserve is the NWPP Reserve Sharing Group
    (a bilateral obligation, no organized ancillary-service market and no
    published demand curve; the WEIM clears energy only), so there is no
    measured ORDC or AS price to ground a design on. A design is a later
    card's work, never inferred here.

    No price benchmark (card N2 / NWPP-13 read NO): the WEIM on-peak price
    sits 22.6 / 23.6 / 37.5 % below the Mid-C Peak traded index against a
    pre-registered ±10 % bar, so no ``actual_lmp.json`` block exists and the
    scorer reads ``PHYSICALLY-CALIBRATED (PRICE UNSCORED)`` (rubric v3.8).
    ``TAIL_THRESHOLD["NWPP"]`` is deliberately absent from all three copies
    (gate G6); a neighbouring hub stays refused (gate G17).
    """
    zones = [
        # Static fallback = pooled 2023-2025 member Demand (MW) (Adjusted)
        # energy shares, UTC-joined (sum = 1.0000). See the docstring.
        Zone(name="NWPP-NW", iso="NWPP", load_share=0.3769),
        Zone(name="NWPP-OR", iso="NWPP", load_share=0.1509),
        Zone(name="NWPP-INLAND", iso="NWPP", load_share=0.1533),
        Zone(name="NWPP-EAST", iso="NWPP", load_share=0.1808),
        Zone(name="NWPP-SNV", iso="NWPP", load_share=0.1381),
    ]
    # NW<->OR Tier-3 placeholder = NWPP-NW zone nameplate 43,619.1 MW (EIA-860
    # 2025 ER, post-adjudication footprint; audit §2.2 per-BA table), rounded
    # to the nearest 100 as SPP-20's 48,700 was. Cannot bind: see docstring.
    _nw_or_placeholder_ttc = 43_600.0
    links = [
        # EAST<->SNV: Path 35 TOT 2C, printed p. 36 (Tier 1 candidate).
        TransferLink(
            from_zone="NWPP-EAST",
            to_zone="NWPP-SNV",
            ttc_mw=600.0,
            is_bidirectional=False,
        ),
        TransferLink(
            from_zone="NWPP-SNV",
            to_zone="NWPP-EAST",
            ttc_mw=580.0,
            is_bidirectional=False,
        ),
        # INLAND<->SNV: Path 16 Idaho-Sierra, printed p. 19 (Tier 1 candidate).
        TransferLink(
            from_zone="NWPP-INLAND",
            to_zone="NWPP-SNV",
            ttc_mw=500.0,
            is_bidirectional=False,
        ),
        TransferLink(
            from_zone="NWPP-SNV",
            to_zone="NWPP-INLAND",
            ttc_mw=360.0,
            is_bidirectional=False,
        ),
        # INLAND<->EAST: Path 20 "Path C", printed p. 23 (Tier 2).
        TransferLink(
            from_zone="NWPP-INLAND",
            to_zone="NWPP-EAST",
            ttc_mw=1600.0,
            is_bidirectional=False,
        ),
        TransferLink(
            from_zone="NWPP-EAST",
            to_zone="NWPP-INLAND",
            ttc_mw=1250.0,
            is_bidirectional=False,
        ),
        # NW<->INLAND: Paths 8 + 6 + 14 aggregated, printed pp. 13/15/17
        # (Tier 2; the aggregation is the documented reconciliation).
        TransferLink(
            from_zone="NWPP-INLAND",
            to_zone="NWPP-NW",
            ttc_mw=8877.0,
            is_bidirectional=False,
        ),
        TransferLink(
            from_zone="NWPP-NW",
            to_zone="NWPP-INLAND",
            ttc_mw=2550.0,
            is_bidirectional=False,
        ),
        # NW<->OR: Tier 3, documented absence (README §1.4) — symmetric
        # non-binding placeholder.
        TransferLink(
            from_zone="NWPP-NW", to_zone="NWPP-OR", ttc_mw=_nw_or_placeholder_ttc
        ),
    ]
    # voll = $2,000/MWh — DECLARED INTERIM, and a ledgered free parameter
    # (rule 21 [R-DOF]). NWPP-10 §7.1 established that FERC Order 831's
    # $2,000 applies by its own terms to RTOs and ISOs and that NWPP is
    # neither, and proposed a sourcing rule in order of preference: (1) a
    # loss-of-load cost stated in a participant IRP — NONE states a $/MWh
    # (the seven IRP transcriptions were searched at registration: PacifiCorp
    # Vol. 1 prices "unserved energy costs" only as a "$0" PVRR stream);
    # (2) the LBNL Interruption Cost Estimate calculator on the footprint's
    # own customer mix — a derivation lane, not a registration; (3) a WECC /
    # WRAP planning VOLL — none published. What IS a real, cited cap for THIS
    # footprint in the window is the WEIM hard offer cap: eleven of the
    # seventeen balancing areas bid their resources into the CAISO-operated
    # Western Energy Imbalance Market under CAISO Tariff §39.6.1 (the Order
    # 831 $2,000/MWh hard cap; $1,000 soft cap with cost verification), and
    # NWPP-13 measured WEIM clearing 5.5-6.2 % of footprint energy net (10.6 %
    # pairwise-gross). The audit's objection is carried in full rather than
    # buried: the cap of an imbalance market that clears ~6 % of energy is
    # NOT a customer damage function, so this value is interim by
    # construction, must be declared as such in every attestation that
    # reads it, and route (2) is the pre-declared successor (routed,
    # FINDING-nwpp-20 §5). A VOLL below the most expensive real unit's
    # marginal cost would make shedding load cheaper than dispatching it;
    # $2,000 clears every unit in the footprint. Never swept against a gate.
    return ISOConfig(
        name="NWPP",
        zones=zones,
        links=links,
        voll=2000.0,
    )


def _soco_config() -> ISOConfig:
    """Build the Southern Company (SOCO) balancing-authority topology.

    **SOCO is a BALANCING AUTHORITY, not an ISO**: the Southern Company
    Services, Inc. – Trans control area (EIA-930 / EIA-860 balancing-
    authority code ``SOCO``, NERC region SERC) that dispatches Alabama Power,
    Georgia Power and Mississippi Power as one pooled, cost-based system under
    the Intercompany Interchange Contract — no day-ahead market, no LMP, no
    capacity auction, no ancillary-service market, no offer cap. The program
    that registered it was chartered on the question "which ISO is the
    Hillabee gas plant in?": Hillabee Energy Center is EIA plant **55411**
    (Tallapoosa County AL, 822.8 MW of gas CC), and its EIA-860 balancing
    authority is ``SOCO``, not any RTO; the north-Alabama fleet (8,396.4 MW /
    16 plants) is **TVA**, a different balancing authority, and is OUT of this
    footprint (``docs/multi-iso/soco-addition-plan-2026-09.md`` §0; owner
    card S1, ruled 2026-09-13: the key is the BA code, and every doc says
    "balancing authority"). Registered 2026-09-14 by lane SOCO-20.

    **Three zones, named for their GEOGRAPHY and never for an operating
    company** (owner card S3, ruled 2026-09-13 desk r#3, re-ruled r#5 on the
    five-respondent load basis): ``SOCO_AL`` (Alabama plus the six SERC
    Florida-panhandle plants, 309.6 MW, which interconnect west), ``SOCO_GA``
    (Georgia) and ``SOCO_MS`` (Mississippi). The plant-side partition is the
    FIPS state map ``zone_assignment._SOCO_STATE_ZONES`` — the cleanest of any
    registered footprint: every plant carries an unambiguous state and no
    plant straddles a state (``docs/multi-iso/soco-data-audit.md`` §6.2). A
    zone is a geographic object and an OpCo a commercial one — Georgia Power
    owns 241.6 MW in Alabama, and Oglethorpe + MEAG own 7.1 GW in Georgia that
    is not Georgia Power's — which is why the load side (below) does NOT map
    OpCos 1:1 onto zones.

    Load partition. The load side rests on FIVE FERC Form 714 planning-area
    respondents — Alabama Power (2), Georgia Power (183), Mississippi Power
    (184), Oglethorpe (107) and MEAG (210) — whose hourly sum closes the
    metered EIA-930 BA demand to a **3.03 / 2.92 / 1.26 %** residual in
    2023 / 2024 / 2025 (FINDING-soco-11 §3; FINDING-soco-14 cites 107 and
    210 into the BA: NERC/SERC audit NCR01248 p. 3 and MEAG's 2024 Annual
    Information Statement pp. 25-26). **Southern Power (186) is EXCLUDED** —
    SOCO-14 returned a documented NO on whether its planning-area LOAD sits
    in the BA, gate G22 is discharged for the five-set and no other, and
    186's 1.3-1.4 % is named on the first keeper's determination basis. The
    per-zone hourly load shapes and the respondent→zone construction are
    lane SOCO-32's declared derive (never rebuilt here, rule 23).

    The static ``load_share`` values below are therefore the audit's §5
    row 4 **fleet-MW share, a fallback of last resort and NOT a load share**:
    EIA-860 2025 ER operable nameplate GA 41,284.4 / AL+FL 24,803.6 /
    MS 4,577.7 of 70,665.7 MW → 0.5842 / 0.3510 / 0.0648 (the MA row is
    rejected, audit §2.6(a)). It is registered as the fallback only because
    (a) the load derive is SOCO-32's by ruling and (b) with the non-binding
    links below the fallback cannot move the dispatch — a three-zone and a
    one-zone SOCO produce the same dispatch until a link binds. SOCO-32
    replaces it with the FERC-714 hourly shapes.

    Congestion structure — TIER-3 PLACEHOLDERS THAT CANNOT BIND. **No public
    inter-OpCo transfer limit exists, structurally**: the Operating Companies
    "function as a single, integrated public-utility system" and are
    "committed and dispatched as a common System without regard to the
    ownership of each generating facility" (FY2025 10-K, quoted in
    ``data/raw/soco-planning/README.md`` §4b), so they publish no internal
    interface rating. The two links (AL↔GA and AL↔MS; Mississippi Power
    connects to the system through Alabama, not Georgia) therefore carry the
    SPP-20 precedent — an upper bound on any physically possible flow, which
    is the smaller side's EIA-860 winter capability — with the misalignment
    stated on the link. The real value is pre-declared lever **SOCO-54**, and
    it has NO public source and NO price signal to validate against: with no
    zonal price, spread or congestion archive (owner card S2), the zones are
    validated on load and dispatch only and the split is chosen for structure
    (rule 1 [R-STRUCT]) and **never sold as improving accuracy** (card S3
    condition (iii)).

    Two timezones, one clock (gate G19, closed by SOCO-10 §3.4): the
    footprint spans America/Chicago (AL, MS) and America/New_York (GA), but
    the BA is dispatched from one control centre and EIA stamps it on ONE
    clock — ``America/Chicago``, DST-aware, hour-ending — measured over all
    26,304 rows of the committed ``SOCO hourly.parquet`` (0 mismatches vs a
    Central wall clock, 26,301 vs Eastern; two offsets only, -6/-5 h). Every
    SOCO series is Central and joins on ``UTC time``; all three zones are
    Central, because the timezone is a property of the BA, not of a zone.

    No import node (gate G7): the seams are the served measured EIA-930
    ``Total interchange`` schedule (``_SCALAR_INTERCHANGE_ISOS``; owner card
    S4; SOCO is a net EXPORTER of +10.2 / +10.8 / +13.0 TWh) plus eight
    DEFAULT-OFF ``NeighborInterface`` blocks in
    ``model/interchange/spec.INTERFACE_NEIGHBORS["SOCO"]`` for lever SOCO-56.

    Market design: vertically integrated, cost-based dispatch against an IRP
    with a bilateral resource-adequacy obligation — deliberately ABSENT from
    ``capacity_market.MARKET_DESIGN`` (→ ``DEFAULT_MARKET_DESIGN``, owner card
    S6), from every offer-curve tuning channel (gate G5: SOCO takes no offers,
    so every band multiplier is the identity), and from any reserve
    co-optimisation or scarcity seed (card S5), so there are no
    ``default_scenario_overrides``.
    """
    zones = [
        # Static fallback = the EIA-860 2025 ER fleet-MW share (audit §5
        # row 4) — NOT a load share; see the docstring. Sum = 1.0000.
        Zone(name="SOCO_AL", iso="SOCO", load_share=0.3510),
        Zone(name="SOCO_GA", iso="SOCO", load_share=0.5842),
        Zone(name="SOCO_MS", iso="SOCO", load_share=0.0648),
    ]
    # TIER-3 PLACEHOLDERS THAT CANNOT BIND (the SPP-20 48,700 MW precedent,
    # FINDING-spp-20 §3 / §5 R-6). Each TTC is the smaller side's EIA-860
    # 2025 ER WINTER capability (audit §2.3, MA row excluded), rounded to the
    # nearest 100 MW: AL + FL panhandle 24,129.5 + 316.8 = 24,446.3 -> 24,400;
    # MS 4,324.6 -> 4,300. Why that is an upper bound in BOTH directions: the
    # smaller side cannot inject more than its own capability, and it cannot
    # absorb more than its own load, which is smaller still (MS peak load is
    # ~0.065 x 47,368 = ~3.1 GW under the fleet-share fallback; Mississippi
    # Power's own 714 planning-area peak is lower). Winter, not summer,
    # because SOCO is winter-peaking in two of the three backcast years
    # (card S6). Rule 14 [R-ACCURATE] MISALIGNMENT, stated: no published or
    # measured inter-OpCo limit exists (SOCO-12 README §4b — the OpCos are
    # one pooled dispatch under the IIC and publish no internal rating), so
    # these are bounds, not capabilities, and they are deliberately NOT a
    # borrowed seam rating (the 2024 Reserve Margin Study's EXTERNAL
    # transfer capabilities into the System are the SOCO-56 seam input, not
    # an internal corridor). Lever SOCO-54 owns the real value and has no
    # price signal to validate it against, ever (card S2). Never tuned.
    _al_ga_bound_mw = 24_400.0
    _al_ms_bound_mw = 4_300.0
    links = [
        TransferLink(from_zone="SOCO_AL", to_zone="SOCO_GA", ttc_mw=_al_ga_bound_mw),
        TransferLink(from_zone="SOCO_AL", to_zone="SOCO_MS", ttc_mw=_al_ms_bound_mw),
    ]
    # voll = $61,900/MWh (owner card S5, ruled 2026-09-13 desk r#3: "DOE/LBNL
    # ICE calculator, SERC/Southeast mix"). SOCO takes NO offers, so FERC
    # Order 831's $2,000 OFFER cap — every market ISO's voll here — has no
    # referent in this footprint and is deliberately NOT carried; in the LP
    # this number is the slack (load-shed) penalty, an ECONOMIC value of lost
    # load. Construction, fixed in PRECOMMIT-soco-20-2026-09-14.md §3 before
    # the number was written:
    #   source  = LBNL/DOE "ICE Calculator 2: Final Report for Phase 1 and 2"
    #             (Larsen, Carney, Eto et al., 2026-02-27, OSTI 3021993),
    #             ES Table 3 / Tables 3.5 + 4.6, cost per UNSERVED kWh, 2025$,
    #             2-HOUR interruption: residential $5.03, non-residential $100;
    #   mix     = EIA-861 2024 retail sales, every utility row with BA Code
    #             SOCO (85 rows, AL/GA/MS/FL): residential 89.686 TWh of
    #             223.70 = 0.4009, non-residential 0.5991;
    #   voll    = 0.4009 x 5,030 + 0.5991 x 100,000 = 61,927 -> 61,900 $/MWh.
    # The 2-hour column is the declared duration rule: an LP slack increment
    # is a one-hour firm curtailment, whose nearest published analogue is the
    # shortest SUSTAINED interruption ICE tabulates; the momentary column
    # prices a sub-minute event's fixed cost (not an energy price) and the
    # 8 h / 24 h columns amortise over multi-hour events the LP never treats
    # as one. The honest width, reported and never selected on: 8 h ->
    # $32,384/MWh, 24 h -> $19,447/MWh. MISALIGNMENT, stated on the field:
    # ICE 2's cost functions are NATIONAL pooled models (sponsors include Duke
    # Energy Carolinas/Florida, none of Southern's OpCos) and the report
    # defers regional variation to its Phase 3, so the "Southeast" leg is the
    # customer-class MIX, not a regional cost function. Brattle's ERCOT VOLL
    # study is method precedent only, never a value (rule 25).
    return ISOConfig(
        name="SOCO",
        zones=zones,
        links=links,
        voll=61_900.0,
    )


_ISO_BUILDERS = {
    "ERCOT": _ercot_config,
    "CAISO": _caiso_config,
    "MISO": _miso_config,
    "PJM": _pjm_config,
    "NYISO": _nyiso_config,
    "NEISO": _neiso_config,
    # SPP registered 2026-09-06 by lane SPP-20 (owner rulings P1-P11,
    # docs/handoffs/spp-desk-ledger-2026-09.md §2). Appended LAST so the
    # registration order of the six earlier ISOs — and every artifact that
    # iterates SUPPORTED_ISOS in order — is unchanged.
    "SPP": _spp_config,
    # NWPP registered 2026-09-14 by lane NWPP-20 (owner rulings N1, N3-N8,
    # docs/multi-iso/nwpp-addition-plan-2026-09.md §3) as the EIGHTH builder.
    # Appended after SPP for the same reason.
    "NWPP": _nwpp_config,
    # SOCO — the Southern Company BALANCING AUTHORITY, the NINTH region and
    # the first single-BA region that is not an ISO — registered 2026-09-14 by
    # lane SOCO-20 (owner cards S1, S3-S7, S9, S11, S12; docs/handoffs/
    # soco-desk-ledger-2026-09.md §2). The two 2026-09-14 registrations landed
    # in parallel; NWPP merged first, so it precedes SOCO here. Appended LAST
    # for the same reason as every earlier region.
    "SOCO": _soco_config,
}

# Canonical tuple of every registered region, in builder-registration order
# (ERCOT, CAISO, MISO, PJM, NYISO, NEISO, SPP, NWPP, SOCO). Single source of
# truth for the nine-region set — scripts should import this instead of
# hardcoding the tuple so a new region registered in ``_ISO_BUILDERS``
# propagates everywhere automatically. (Every downstream name still says
# "ISO"; NWPP is a pool of balancing authorities and SOCO is a single
# balancing authority — see ``_nwpp_config`` / ``_soco_config``.)
SUPPORTED_ISOS: tuple[str, ...] = tuple(_ISO_BUILDERS)


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
    plant_class: str  # class FAMILY: "ST_GAS", "CT_PEAKER", "COAL" (the coal family
    # token, plant_taxonomy.COAL_ARTIFACT_FAMILY — matches every coal subclass), "oil", …
    driver: str  # "tmax" (hot gate) | "tmin" (cold gate) | "netload"
    threshold: float  # °C for tmax/tmin; MW for netload
    floor_pct: float  # = commit_frac × min_stable_pct (see plan §B.3)
    enabled: bool = True  # toggle this exact (iso, zone, class, driver) limb
    min_event_hours: int = 24  # steam-gas event bridging; 24 = single-day
    distribution: str = "cheapest_first"  # "cheapest_first" or "pro_rata"
    start_hour: int | None = None  # sub-daily window start (inclusive, 0-23)
    end_hour: int | None = None  # sub-daily window end (inclusive, 0-23)
    ramp_group: str | None = None  # continuous-ramp family label (see below)
    threshold_percentile: float | None = (
        None  # engine-computed percentile (netload only)
    )
    # EIA plant codes this limb does NOT floor, even though they carry the
    # limb's (zone, plant_class). A persistent-baseline floor is derived from a
    # FLEET-aggregate capacity factor but applied per UNIT, so a plant that is
    # economically laid up — available in the outage extract, but idle in its
    # own metered conduct — is held at the fleet's baseline in every hour and
    # manufactures energy it never produced (rule 17 [R-FLOOR-WINDOW]: a floor
    # binding in hours its own driver evidence says the unit is offline is a
    # bug). Excluding it is a MEMBERSHIP correction to the limb's identification,
    # sourced from the same CAMPD conduct the coefficient is derived from, and is
    # frozen against residuals like every other coefficient (rule 23
    # [R-FROZEN-DERIVE]). Populated from the CSV's optional
    # ``exclude_plant_codes`` column; inert unless
    # ``ScenarioConfig.reliability_floor_plant_exclusions`` arms it (see
    # :func:`apply_reliability_floor_plant_exclusions`).
    exclude_plant_codes: frozenset[int] = frozenset()


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
    registry is empty until ``scripts/data/derive_reliability_coeffs.py`` populates
    the coefficients (Phase 2). Required columns: ``zone, plant_class, driver,
    threshold, floor_pct, enabled``; optional: ``min_event_hours``,
    ``distribution``, ``start_hour``, ``end_hour``, ``ramp_group``, ``r1_disabled``,
    ``exclude_plant_codes``.

    ``exclude_plant_codes`` is a ``;``- or ``,``-separated list of EIA plant codes
    the limb does not floor (see
    :attr:`ReliabilityFloorSpec.exclude_plant_codes`). It is parsed whenever
    present but stays inert until a run arms
    ``ScenarioConfig.reliability_floor_plant_exclusions``, so CSVs carrying the
    column load byte-identically for every existing run.

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
                    tp_raw = (row.get("threshold_percentile") or "").strip()
                    ex_raw = (row.get("exclude_plant_codes") or "").strip()
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
                            threshold_percentile=float(tp_raw) if tp_raw else None,
                            exclude_plant_codes=frozenset(
                                int(c) for c in ex_raw.replace(",", ";").split(";") if c
                            ),
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


# (zone, class) limbs the NYISO in-city commitment obligation SUPERSEDES. The
# obligation re-classes the published NYC/LI 10-minute reserve families onto an
# online-gated in-pocket class, making the published requirement the commitment
# driver for downstate steam — the same phenomenon the p25-derived NYC/LI
# ST_GAS reliability-floor limbs currently scaffold. The in-city must-run lane
# charter (docs/handoffs/nyiso-incity-mustrun-charter-2026-07.md §2) makes
# substitution a REQUIREMENT, not an option: "Any mechanism this lane produces
# MUST REPLACE OR RECONCILE WITH the NYC/LI ST_GAS limbs of reliability_floor.
# Stacking a second floor on the unexplained residual of the first is
# forbidden" (CLAUDE.md rule 19 [R-ONE-MECH]), and would in any case breach the
# C8 forced-energy budget. Zone-scoped: the Capital_Hudson ST_GAS limb is
# outside the load pockets and is untouched.
_INCITY_OBLIGATION_OWNED_LIMBS: frozenset[tuple[str, str]] = frozenset(
    {("NYC", "ST_GAS"), ("Long_Island", "ST_GAS")}
)


def drop_obligation_owned_reliability_specs(
    specs: list[ReliabilityFloorSpec],
    config,
) -> list[ReliabilityFloorSpec]:
    """Drop the NYC/LI ``ST_GAS`` limbs the in-city obligation supersedes.

    No-op unless ``config.nyiso_incity_commitment_obligation`` is set, so every
    other ISO/run is byte-identical. When it IS set the substitution is
    automatic rather than an operator-supplied override: the charter requires
    replacement, and leaving it to a hand-written
    ``reliability_floor_overrides`` entry makes silent STACKING (the forbidden
    outcome) the default failure mode.

    Args:
        specs: Reliability-floor limbs for the ISO, post-overrides.
        config: The run's ``ScenarioConfig``.

    Returns:
        *specs* with the superseded (zone, class) limbs removed.
    """
    if not getattr(config, "nyiso_incity_commitment_obligation", False):
        return specs
    return [
        s
        for s in specs
        if (s.zone, s.plant_class) not in _INCITY_OBLIGATION_OWNED_LIMBS
    ]


def apply_reliability_floor_plant_exclusions(
    specs: list[ReliabilityFloorSpec],
    config,
) -> list[ReliabilityFloorSpec]:
    """Arm or clear each limb's ``exclude_plant_codes`` membership correction.

    A persistent-baseline reliability floor is identified from a **fleet-aggregate**
    capacity factor but applied per **unit** (``distribution="pro_rata"`` floors
    every unit of the class in the zone at ``floor_pct × pmax × availability``).
    The two bases diverge whenever the fleet contains a plant that is
    *economically laid up*: idle in its own metered conduct, yet fully available
    in the outage extract, because lay-up is correctly not booked as a forced
    outage. Such a unit is then held at the fleet's baseline in all 8,760 hours
    and manufactures energy it never produced — rule 17 ``[R-FLOOR-WINDOW]``'s
    "a floor binding in hours its own driver evidence says the unit is offline is
    a bug by definition".

    The exclusion list is a **membership correction to the limb's own
    identification**, derived from the same CAMPD conduct as ``floor_pct`` and
    carried in the same frozen coefficient CSV, so it is governed by rule 23
    ``[R-FROZEN-DERIVE]``: it re-derives only when its source data does, never
    because a residual moved.

    Gated so an A/B is clean. Unless ``config.reliability_floor_plant_exclusions``
    is set, every limb's exclusions are CLEARED, making a control run
    byte-identical to the pre-mechanism engine even on a CSV that carries the
    column.

    Args:
        specs: Reliability-floor limbs for the ISO, post-overrides.
        config: The run's ``ScenarioConfig``.

    Returns:
        *specs* with ``exclude_plant_codes`` retained (armed) or emptied
        (disarmed). Limbs that carry no exclusions are returned unchanged either
        way, so the common path allocates nothing.
    """
    armed = bool(getattr(config, "reliability_floor_plant_exclusions", False))
    if armed:
        return specs
    return [
        _dataclass_replace(s, exclude_plant_codes=frozenset())
        if s.exclude_plant_codes
        else s
        for s in specs
    ]


# The nyiso-87 arm-A override: every enabled NYISO h14-21 peak-window ramp
# family OFF, every unwindowed limb untouched. Named here (rather than retyped
# per probe) so the arms, the keeper config and the test all cite ONE object.
#
# Driver: OWNER DIRECTIVE 2026-07-27 — "the h14-21 peak-hour must-run is
# INACCURATE — turn it off ... every floor we have added was a compensation for
# missing commitment drag". That is a rule-23 [R-FROZEN-DERIVE] source trigger
# of the admissible kind (an owner adjudication of the mechanism, NOT a
# residual moving): the windowed limbs are replaced by the NYISO gas commitment
# bridge (``ScenarioConfig.nyiso_gas_commitment_bridge``), which carries the
# same phenomenon on commitment physics instead of a boxcar (rule 19
# [R-ONE-MECH]).
#
# Scope note: the persistent 24 h NYC / Long_Island ST_GAS bases and the
# Capital_Hudson hot step are NOT in this dict. Their driver is a 24-hour one
# (in-city voltage/reliability commitment; a hot-day steam commitment), not the
# afternoon peak window the directive names, so they stay until a bridge arm
# shows the bridge reproduces them too.
NYISO_PEAK_WINDOW_FLOORS_OFF: dict[str, dict] = {
    "NYC:ST_GAS:tmax:NYC_ST_ev": {"enabled": False},
    "NYC:CT_PEAKER:tmax:NYC_CT_ev": {"enabled": False},
    "Long_Island:CT_PEAKER:tmax:LI_CT_ev": {"enabled": False},
    "Long_Island:ST_GAS:tmax:LI_ST_ev": {"enabled": False},
    "Capital_Hudson:ST_GAS:tmax:CH_ST_ev": {"enabled": False},
}


# Fourth-segment sentinel selecting the limbs that carry NO ``ramp_group``
# (standalone step limbs) in a ``reliability_floor_overrides`` key. A literal
# ramp-group label can never collide with it: the derive scripts emit
# ``<Zone>_<CLASS>_<window>`` labels, never a leading underscore.
_NO_RAMP_GROUP_KEY: str = "_none"


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

    **Ramp-family granularity** (nyiso-87): an optional FOURTH key segment
    selects one ``ramp_group`` within a (zone, class, driver) —
    ``"<ZONE>:<CLASS>:<driver>:<ramp_group>"``. A (zone, class, driver) can
    hold several limbs with different windows (NYISO ``NYC:ST_GAS:tmax`` holds
    the persistent 24 h base AND the two h14–21 ``NYC_ST_ev`` ramp knots), and
    the three-segment key cannot separate them — disabling the peak window
    would also disable the always-on voltage/reliability base. The four-segment
    form matches only limbs whose ``ramp_group`` equals the fourth segment;
    ``"...:_none"`` matches the limbs with NO ramp group (the standalone
    steps). Both forms are honoured, and the four-segment form takes precedence
    where both match, so existing three-segment overrides are unchanged.
    """
    if not overrides:
        return specs
    import dataclasses as _dc

    out: list[ReliabilityFloorSpec] = []
    for spec in specs:
        base_key = f"{spec.zone}:{spec.plant_class}:{spec.driver}"
        # Ramp-family key wins over the whole-(zone, class, driver) key, so a
        # config can disable one window and leave the family's other limbs (or
        # the standalone base) untouched.
        group_key = f"{base_key}:{spec.ramp_group or _NO_RAMP_GROUP_KEY}"
        ov = overrides.get(group_key) or overrides.get(base_key)
        if not ov:
            out.append(spec)
            continue
        changes = {f: ov[f] for f in ("enabled", "floor_pct", "threshold") if f in ov}
        out.append(_dc.replace(spec, **changes) if changes else spec)
    return out


def apply_iso_scenario_defaults(config, iso: str):
    """Return ``config`` with the ISO's ``default_scenario_overrides`` applied.

    An ISO-level default only fills a field the CALLER DID NOT PASS — an
    explicit caller value always wins, **including one that happens to equal the
    :class:`~market_sim.config.scenarios.ScenarioConfig` field default**. That
    last clause is the OVERRIDE-FIX (2026-08-13): until then "unset" was
    inferred by comparing values, so an explicit ``False``/``None`` was
    indistinguishable from absence and was silently re-armed — which made a
    control arm for any ISO-armed flag inexpressible. The caller's own
    explicitly-set-field record
    (:func:`~market_sim.config.scenarios.explicitly_set_fields`) is now
    consulted first. That is the rule this function exists to state
    once (rule 19 ``[R-ONE-MECH]``): it was inlined in
    ``runner.run_scenario_iso``, so every OTHER reader of a pre-solve config
    saw the UNRESOLVED posture. Concretely, MISO's overrides arm
    ``miso_rps_compliance_regions`` (owner D-26) and
    ``entry_vre_capacity_revenue``, so a leg that passes no flag still SOLVES
    the K-row grain — and a run record built from the caller's own config
    reported it as OFF, which is the FFR-2E defect (a record must report the
    posture it solved, not assert one). ARM3-MEASURE hit exactly that.

    Args:
        config: The pre-resolution ``ScenarioConfig``.
        iso: ISO code whose ``ISOConfig.default_scenario_overrides`` to apply.

    Returns:
        The config with the ISO's defaults applied — the SAME object when the
        ISO declares no overrides or the caller has set every one of them, so
        callers that already resolved stay byte-identical.
    """
    from market_sim.config.scenarios import ScenarioConfig, explicitly_set_fields

    overrides = get_iso_config(iso).default_scenario_overrides
    if not overrides:
        return config
    defaults = ScenarioConfig()
    # OVERRIDE-FIX 2026-08-13: "unset" is read from the CALLER'S OWN RECORD
    # first, and only then from the value. The value comparison alone cannot
    # see an explicit ``False``/``None`` — it equals the field default, which is
    # precisely the OFF value a control arm needs to request — so every
    # ISO-armed flag was silently re-armed and a control arm was inexpressible.
    set_fields = explicitly_set_fields(config)
    to_apply = {
        k: v
        for k, v in overrides.items()
        # ``set_fields is None`` = untracked provenance (a bare
        # ``dataclasses.replace`` copy, an unpickled config): fall back to the
        # value comparison alone, i.e. exactly the pre-fix behaviour.
        if (set_fields is None or k not in set_fields)
        # Retained, not replaced: a config MUTATED after construction carries no
        # record of it, and this still catches that. Keeping both conditions
        # makes the fix a strict NARROWING — it can only apply FEWER ISO
        # defaults than before, never more, so no unset caller's posture moves.
        and getattr(config, k) == getattr(defaults, k)
    }
    return config.with_overrides(**to_apply) if to_apply else config
