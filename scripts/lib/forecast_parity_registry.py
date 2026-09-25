"""Backcast→forecast parity registry (FR-22, the generalized D-5 gap).

**The failure this prevents.** ``docs/FINDING-nyiso102-d5-parity-wiring-2026-07-30.md``
records three NYISO downstate mechanisms (``inject_nyiso_local_selfsupply``,
``apply_nyiso_li_tsl_import_cap``, ``apply_nyiso_nyc_tsl_import_cap``) that were
called only from the BACKCAST orchestrator (``scripts/run_calibration.py``) — the
forecast orchestrator (``src/market_sim/runner.py``) never referenced them. A
keeper armed all three; a forecast carrying the same config would silently have
dropped them. The gap was found ad hoc, by a session looking at something else.

Keeper mechanisms land weekly, so this is a *class* of defect, not an incident.
:mod:`scripts.check_forecast_parity` sweeps every ISO's current keeper posture,
enumerates the armed solve-affecting ``ScenarioConfig`` fields, and requires each
one to resolve to either

  **(a)** a forecast-orchestrator consumer, discovered from the SOURCE (see
  :data:`SOURCE_ROLES` and the evidence tiers in the checker), or
  **(b)** an explicit declaration in this module saying why it is
  backcast-only-by-design (measured overlay with no forward analogue, rule 13
  ``[R-MEASURED]``), a parameter of another mechanism, a scenario input, an
  alias for a differently-gated forecast path, or a FILED GAP.

Anything in neither set fails the check loud. That is the whole point: a new
keeper mechanism cannot quietly fork the two paths.

**Dispositions** (:class:`ParityDeclaration.disposition`):

``BACKCAST_ONLY``
    Backcast-only by design. The forecast path must NOT reach it. Verified: the
    field has no forecast-orchestrator evidence (a stale declaration — one that
    HAS since been wired forward — fails, so this list cannot rot into a
    permanent excuse). Most rows here are the measured-overlay family already
    annotated in the backcast orchestrator with the in-code convention
    ``[measured: <source> | forecast substitute: <forward channel>]``; the
    checker reports which rows carry that annotation.
``PARAMETER_OF``
    Not a mechanism — a parameter of ``parent``. Resolves to the parent's
    disposition; reported INERT when the parent is not armed in that keeper.
``FORECAST_ALIAS``
    The forecast path reaches the same mechanism through a DIFFERENT gate
    (``alias_gate``), so the field itself is backcast-side plumbing. Verified:
    the alias gate must itself resolve to forecast evidence.
``SCENARIO_INPUT``
    Not a mechanism — scenario identity or path plumbing both modes set from
    their own driver.
``GAP``
    A REAL parity gap, filed in ``finding``. Reported loudly on every run and
    counted in the report header; wiring it is a follow-up session's job, never
    this check's (FFR-1E scope: build the detector, file what it finds).

Rule 24 ``[R-REGISTRY]`` note: nothing here changes a solve. This is a
governance artifact read by a no-LP checker and its tests.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "BACKCAST_ONLY",
    "FORECAST_ALIAS",
    "GAP",
    "PARAMETER_OF",
    "SCENARIO_INPUT",
    "DECLARATIONS",
    "DYNAMIC_CONSUMERS",
    "SOURCE_ROLES",
    "ARCHIVED_FUNCTIONS",
    "FORECAST_ORCHESTRATOR",
    "DynamicConsumer",
    "ParityDeclaration",
    "declaration_for",
]

BACKCAST_ONLY = "BACKCAST_ONLY"
PARAMETER_OF = "PARAMETER_OF"
FORECAST_ALIAS = "FORECAST_ALIAS"
SCENARIO_INPUT = "SCENARIO_INPUT"
GAP = "GAP"

_DISPOSITIONS = frozenset(
    {BACKCAST_ONLY, PARAMETER_OF, FORECAST_ALIAS, SCENARIO_INPUT, GAP}
)


@dataclass(frozen=True)
class ParityDeclaration:
    """One registry row: why these fields need no forecast-orchestrator consumer.

    Attributes:
        fields: The ``ScenarioConfig`` field names this row covers. A field may
            appear in exactly one row (duplicates fail the integrity check).
        disposition: One of the module-level disposition constants.
        why: One line stating the reason. Required on every row — a row without
            a reason is an unexplained exemption, which is what this registry
            exists to prevent.
        evidence: Repo-relative paths backing the claim (source or doc). Each
            must exist and at least one must name at least one of ``fields``.
        parent: ``PARAMETER_OF`` only — the gating mechanism's field name.
        alias_gate: ``FORECAST_ALIAS`` only — the field the forecast path gates
            the same mechanism on.
        finding: ``GAP`` only — repo-relative path of the doc filing the gap.
    """

    fields: tuple[str, ...]
    disposition: str
    why: str
    evidence: tuple[str, ...] = ()
    parent: str | None = None
    alias_gate: str | None = None
    finding: str | None = None

    def __post_init__(self) -> None:
        if self.disposition not in _DISPOSITIONS:
            raise ValueError(f"unknown disposition {self.disposition!r}")
        if not self.fields:
            raise ValueError("a declaration must cover at least one field")
        if not self.why.strip():
            raise ValueError(f"{self.fields[0]}: every declaration needs a why")


@dataclass(frozen=True)
class DynamicConsumer:
    """A consumer that reads config fields under a COMPUTED attribute name.

    ``getattr(config, f"coal_{stem}_{p}")`` is invisible to a name-based scan,
    so the fields it serves would look unconsumed. Each row declares the exact
    field-name pattern one such site covers, the module it lives in, and why —
    hand-written and narrow on purpose (a loose pattern would hand out
    forecast evidence to fields nobody reads).

    Attributes:
        pattern: Fully-anchored regex matched against the field name.
        module: Repo-relative module holding the dynamic ``getattr``.
        symbol: The f-string source text, so the citation can be verified.
        why: One line on what the site does.
    """

    pattern: str
    module: str
    symbol: str
    why: str


# ---------------------------------------------------------------------------
# Source roles — which files speak for which mode
# ---------------------------------------------------------------------------

#: The forecast orchestrator. A field read here is forecast-wired, full stop.
FORECAST_ORCHESTRATOR = "src/market_sim/runner.py"

#: Role of each scanned source. ``backcast`` files NEVER supply forecast
#: evidence (``pipeline/backcast_config.py`` lives under ``src/`` but is the
#: backcast config builder — import-reachability from ``runner.py`` says
#: nothing about whether the forecast path *calls* it). ``bookkeeping`` files
#: name fields for recording/CLI purposes only, so a mention there is not
#: consumption. Everything else under ``src/market_sim/`` is ``shared``: a
#: builder both orchestrators thread their config into.
SOURCE_ROLES: dict[str, str] = {
    "src/market_sim/runner.py": "forecast",
    "scripts/run_calibration.py": "backcast",
    "scripts/run_calibration_full.py": "backcast",
    "src/market_sim/pipeline/backcast_config.py": "backcast",
    "src/market_sim/pipeline/persist.py": "bookkeeping",
    "src/market_sim/pipeline/flags.py": "bookkeeping",
    "src/market_sim/config/scenarios.py": "bookkeeping",
    "src/market_sim/config/entry_config.py": "bookkeeping",
}

#: (module, function) pairs whose reads are NOT evidence of a live forecast
#: path. ``run_commitment_pass`` is the ARCHIVED P2 solve (CLAUDE.md "Dispatch
#: & Commitment": "P2 is ARCHIVED … no keeper uses it"); it is still imported
#: by ``runner.py``, so a mention inside it would hand out forecast evidence
#: for a pass that never runs — and it is exactly where the nyiso-102 incident
#: would have hidden (``preserve_min_gen`` names ``nyiso_local_selfsupply``).
ARCHIVED_FUNCTIONS: frozenset[tuple[str, str]] = frozenset(
    {("src/market_sim/pipeline/commitment.py", "run_commitment_pass")}
)


# ---------------------------------------------------------------------------
# Dynamic consumers
# ---------------------------------------------------------------------------

DYNAMIC_CONSUMERS: tuple[DynamicConsumer, ...] = (
    DynamicConsumer(
        pattern=r"coal_(prb_passthrough|prb_follower|sub_passthrough|"
        r"bit_passthrough|lignite_passthrough|waste_passthrough)_"
        r"(floor|ceil|gas_mid|gas_slope)",
        module="src/market_sim/data/fuel/trajectories.py",
        symbol='f"coal_{stem}_{p}"',
        why="coal_sigmoid_params resolves each supply chain's sigmoid params "
        "by computed name over _COAL_SIGMOID_FIELD_STEM × _COAL_SIGMOID_PARAMS "
        "— shared fuel builder, both orchestrators",
    ),
    DynamicConsumer(
        pattern=r"coal_(prb_passthrough|prb_follower|sub_passthrough|"
        r"bit_passthrough|lignite_passthrough|waste_passthrough)_sigmoid",
        module="src/market_sim/data/fuel/trajectories.py",
        symbol='f"coal_{stem}_sigmoid"',
        why="coal_passthrough_series gates each supply chain's gas-keyed "
        "passthrough sigmoid by computed name — shared fuel builder",
    ),
)


# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------

_BACKCAST_ORCH = "scripts/run_calibration.py"
_MEASURED_AUDIT = "docs/backcast-measured-data-audit-2026-06.md"

DECLARATIONS: tuple[ParityDeclaration, ...] = (
    # -- (b) measured transmission / interface limits ------------------------
    # Same family as nyiso_central_east_measured_ttc, adjudicated K-backcast /
    # G-forecast: measured transfer capability was explicitly REFUSED a forward
    # channel because the transmission-expansion registry owns forward TTC.
    # Pushing a measured hourly limit forward imports one historical year's
    # outage/derate schedule into every forecast year.
    ParityDeclaration(
        fields=("ercot_gtc_limits_measured",),
        disposition=BACKCAST_ONLY,
        why="measured hourly ERCOT GTC export limits (rule 13-admissible "
        "network availability events); forward TTC is owned by the static "
        "ratings + transmission-expansion registry, per the "
        "nyiso_central_east_measured_ttc adjudication",
        evidence=(_BACKCAST_ORCH, _MEASURED_AUDIT),
    ),
    ParityDeclaration(
        fields=(
            "pjm_congestion",
            "pjm_measured_interface_limits",
            "pjm_east_interface_cut",
            "pjm_external_net_position_cut",
        ),
        disposition=BACKCAST_ONLY,
        why="measured PJM internal transfer-limit postings (Data Miner 2 / "
        "PJM_MEASURED_INTERNAL_TTC) applied as backcast overlays — each "
        "declared 'backcast overlay' at its call site; the forward channel is "
        "the static link ratings + transmission-expansion registry",
        evidence=(_BACKCAST_ORCH, "src/market_sim/config/constants.py"),
    ),
    # -- (b) the declared measured-interchange overlay block -----------------
    # scripts/run_calibration.py carries an explicit banner: "BACKCAST MEASURED
    # INTERCHANGE OVERLAYS … backcast-only by design (plan §3.1). None is
    # reachable from the forecast path: the forecast substitutes are noted per
    # overlay." Each field below sits under a
    # "[measured: … | forecast substitute: …]" annotation naming its own
    # forward channel; the checker reports which rows it can see that on.
    ParityDeclaration(
        fields=(
            "miso_seam_flow_limit",
            "miso_seam_export_limit",
            "pjm_seam_flow_limit",
            "pjm_seam_export_limit",
        ),
        disposition=BACKCAST_ONLY,
        why="measured EIA-930 / tie-line per-neighbour flow envelopes bounding "
        "the priced seam bands; forecast substitute declared in-code — the "
        "seam's interface_limit_mw + reference prices",
        evidence=(_BACKCAST_ORCH,),
    ),
    ParityDeclaration(
        fields=("miso_seam_measured_ladder", "nyiso_import_hub_prices"),
        disposition=BACKCAST_ONLY,
        why="measured seam price series (MISO Q-Q ladders, PJM/ISO-NE DA "
        "system LMP) overwriting the priced node's mc rows; forecast "
        "substitute declared in-code — the gas-elastic reference-price formula",
        evidence=(_BACKCAST_ORCH, "src/market_sim/config/interchange_config.py"),
    ),
    ParityDeclaration(
        fields=(
            "miso_seam_neighbour_anchored_ladder",
            "miso_seam_neighbour_hourly_ladder",
        ),
        disposition=BACKCAST_ONLY,
        why="the NEIGHBOUR-priced forms of the same measured seam ladder "
        "declared above, and backcast-only for the same reason: both price a "
        "band off a MEASURED neighbour DA series that exists only for a "
        "historical year — the PJM western-border DA "
        "(MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR, the annual Q-Q form, miso-225) "
        "and the same series read hourly as per-band offsets, band k at "
        "pjm_border(t) + delta_k (miso-231). The hourly form DISPLACES the "
        "annual one on the seams it covers and degrades to it, never to an "
        "unpriced seam; neither has a forward analogue, and the forecast "
        "substitute is the one already declared for the family — the "
        "gas-elastic reference-price formula",
        evidence=(
            _BACKCAST_ORCH,
            "src/market_sim/model/interchange/miso.py",
            "src/market_sim/config/interchange_config.py",
        ),
    ),
    ParityDeclaration(
        fields=("pjm_interface_feed_admissibility_gate",),
        disposition=BACKCAST_ONLY,
        why="the admissibility JUDGE on a measured, backcast-only feed: it "
        "tests the year's posted PJM Eastern interface series against that "
        "year's OWN measured flows (interface_series_admissibility) before the "
        "joint EMAAC import cut is enforced, and on failure returns an "
        "all-+inf array so the two links keep their static per-link TTCs. Both "
        "halves are backcast-side — the hourly feed reaches the solve only "
        "through the backcast orchestrator "
        "(data/transfer_interface_limits.py, imported at run_calibration.py) "
        "and the flag is set by the BACKCAST config builder alone "
        "(pipeline/backcast_config.py, iso == 'PJM'). The forecast substitute "
        "needs no wiring because it is the fall-through itself: the function's "
        "own docstring names the gate's failure branch as 'the same posture a "
        "forecast year already takes' — static per-link TTCs, no measured cut. "
        "Rule 14 [R-ACCURATE]'s named misalignment exception (the pre-2023 "
        "vintage is a near-static seasonal limit-set posting, a DIFFERENT "
        "QUANTITY from the post-2023 hourly TLC under one series name), and "
        "the fall-through is selected by the FEED alone — never by a price, a "
        "residual or any model output — and logged at WARNING with its full "
        "arithmetic",
        evidence=(
            _BACKCAST_ORCH,
            "src/market_sim/data/transfer_interface_limits.py",
            "src/market_sim/pipeline/backcast_config.py",
        ),
    ),
    ParityDeclaration(
        fields=("caiso_corridor_flow_limit",),
        disposition=BACKCAST_ONLY,
        why="measured EIA-930 per-corridor p95 net-flow envelope; forecast "
        "substitute declared in-code — caiso_corridor_atc_forward, the shared "
        "forward_corridor_interface_groups capability envelope the forecast "
        "runner wires instead",
        evidence=(_BACKCAST_ORCH,),
    ),
    # -- (b) explicitly mode-gated / declared backcast-only ------------------
    ParityDeclaration(
        fields=("carry_operating_mothballs",),
        disposition=BACKCAST_ONLY,
        why="gated on config.mode == 'backcast' at its call site — re-carries "
        "mothballed-but-operating units the backcast snapshot's OP filter "
        "drops; a forecast must not carry them",
        evidence=(
            _BACKCAST_ORCH,
            "docs/handoffs/miso-cc-vintage-undercarry-plan-2026-07.md",
        ),
    ),
    ParityDeclaration(
        fields=("maxgen_emergency_tier_pricing",),
        disposition=BACKCAST_ONLY,
        why="declared-window ELMP emergency-tier slack repricing inside a "
        "measured maxgen-events registry window; its call site states "
        "'Backcast-only overlay (D-5): the forecast runner never arms it'",
        evidence=(
            _BACKCAST_ORCH,
            "docs/handoffs/miso-f5-scarcity-depth-design-2026-07.md",
        ),
    ),
    ParityDeclaration(
        fields=("dual_fuel_oil_reattribution",),
        disposition=BACKCAST_ONLY,
        why="output attribution only — re-labels the measured dual-fuel "
        "switch hours' MWh as petroleum for reporting; the switch itself is "
        "objective-side and shared, so the LP is unchanged either way",
        evidence=(_BACKCAST_ORCH,),
    ),
    # ercot-167 measured storage AS SOC reservation (Y-18, 2026-09-06). The
    # quantity is Sigma_p award_p(t) x duration_p. The DURATIONS are published
    # and forward-safe (reserves.spec.ERCOT_AS_PRODUCT_DURATION_H, Nodal
    # Protocols 3.17.3); the AWARDS are not — model/storage.py reads them from
    # data/raw/ercot-AS/ercot_{year}_{as_by_restype,storage_as_products}
    # _hourly.parquet, a PER-HISTORICAL-YEAR 60-Day DAM PWRSTR corpus whose
    # documented forward behaviour is an all-zero (inert) floor when the file
    # is absent. Both limbs of the rule 13 test therefore fail: no forward-year
    # artifact, and a frozen historical award series does not respond to a
    # changed forward fleet. Not a bare assertion — the function's own docstring
    # states it (storage.py:620-623), a construction-time validator makes the
    # field mutually exclusive with the forward substitute
    # (scenarios.py:16697-16701), the forecast orchestrator branches on that
    # substitute (runner.py:4630), and the whole measured-award family is gated
    # `and not ercot_storage_as_endogenous` inside the SHARED reserves builder
    # under the comment "backcast-only record (the forward story is
    # ercot_storage_as_endogenous)" (reserves/spec.py:1365-1371, 2124-2131).
    # That last point is also why the FFR-1E sibling row above
    # (ercot_storage_capability_measured / ercot_storage_as_deployment) does not
    # carry over: `storage_as_commitment` being "shared" is a checker-TIER fact
    # about which module reads the flag, not an admissibility fact — its shared
    # reads are themselves endogenous-gated. Adjudication: Y-18 finding 1.2-1.3.
    ParityDeclaration(
        fields=("ercot_storage_as_soc_reserve",),
        disposition=BACKCAST_ONLY,
        why="ercot-167 measured storage AS SOC reservation — floors battery SOC "
        "at the MEASURED 60-Day-DAM PWRSTR award x the PUBLISHED per-product "
        "duration (Nodal Protocols 3.17.3). Measured source: the per-year "
        "data/raw/ercot-AS/ercot_{year}_*_hourly.parquet corpus, which has no "
        "forward-year artifact (missing file -> all-zero inert floor) and does "
        "not respond to a changed forward fleet. Forecast substitute: "
        "ercot_storage_as_endogenous, which prices the AS/energy split itself — "
        "named in the function docstring (model/storage.py:620-623) and "
        "ENFORCED by a construction-time mutual-exclusion validator "
        "(scenarios.py:16697-16701), so the two can never both be armed. Gated "
        "at scripts/run_calibration.py:4826-4832, whose third clause is "
        "`and not getattr(config, 'ercot_storage_as_endogenous', False)`",
        evidence=(_BACKCAST_ORCH, "src/market_sim/model/storage.py"),
    ),
    ParityDeclaration(
        fields=("neiso_oil_burn_budget",),
        disposition=BACKCAST_ONLY,
        why="SUPERSEDED reference path — EIA-923 petroleum RECEIPTS, a "
        "measured deliveries-to-tank OUTCOME its own call site marks "
        "inadmissible under rule 13; never a forward channel (the admissible "
        "twin is neiso_winter_fuel_inventory)",
        evidence=(_BACKCAST_ORCH,),
    ),
    # -- parameters ----------------------------------------------------------
    ParityDeclaration(
        fields=("caiso_gas_floor_frac",),
        disposition=PARAMETER_OF,
        parent="caiso_gas_commitment_floor",
        why="scale factor on the CAISO gas commitment floor — inert unless "
        "that floor is armed",
        evidence=(_BACKCAST_ORCH,),
    ),
    ParityDeclaration(
        fields=("miso_seam_envelope_merit_cap",),
        disposition=PARAMETER_OF,
        parent="miso_seam_flow_limit",
        why="envelope composition semantics (merit-order waterfall vs uniform "
        "per-band derate) for the MISO seam import cap",
        evidence=(_BACKCAST_ORCH,),
    ),
    ParityDeclaration(
        fields=("miso_seam_neighbour_hourly_spp",),
        disposition=PARAMETER_OF,
        parent="miso_seam_neighbour_hourly_ladder",
        why="miso-233 extension of the hourly neighbour anchor to the SECOND "
        "seam, pricing SPP band k at spp_hub(t) + delta_k against the measured "
        "SPP NORTH hub DA — declared a SUB-GATE and never a mechanism beside "
        "its parent by rule 19 [R-ONE-MECH] (the predicate REQUIRES "
        "miso_seam_neighbour_hourly_ladder, so the two seams are never "
        "anchored apart) and riding the same per-seam hourly_anchor mapping "
        "the PJM entry already uses. Same treatment as its siblings "
        "miso_seam_envelope_merit_cap / miso_seam_envelope_hour_ending_key; it "
        "resolves to the parent's BACKCAST_ONLY disposition",
        evidence=(
            _BACKCAST_ORCH,
            "src/market_sim/model/interchange/miso.py",
            "src/market_sim/model/interchange/spec.py",
        ),
    ),
    ParityDeclaration(
        fields=("miso_seam_envelope_hour_ending_key",),
        disposition=PARAMETER_OF,
        parent="miso_seam_flow_limit",
        why="miso-175 hour-ENDING stamp convention for the measured (month x "
        "hod) seam-envelope cap key — read only inside the miso_seam_flow_limit "
        "/ miso_seam_export_limit blocks, the same treatment as its sibling "
        "miso_seam_envelope_merit_cap (armed in the MISO keeper since miso-198)",
        evidence=(_BACKCAST_ORCH, "src/market_sim/model/interchange/miso.py"),
    ),
    ParityDeclaration(
        fields=("caiso_offer_surface_measured_ungrounded",),
        disposition=PARAMETER_OF,
        parent="caiso_offer_surface_measured",
        why="caiso-231 scope extension of the measured CAISO offer surface to "
        "the un-grounded CHP / ST_GAS classes — re-uses the SAME measured "
        "artifact and band set and raises ValueError unless the parent is "
        "armed, so it inherits the parent's filed GAP (FFR-1E F-5) rather "
        "than opening a second one (armed in the CAISO keeper since caiso-231)",
        evidence=("src/market_sim/pipeline/backcast_config.py",),
    ),
    # -- alias ---------------------------------------------------------------
    ParityDeclaration(
        fields=("plant_level_fleet",),
        disposition=FORECAST_ALIAS,
        alias_gate="use_campd_bins",
        why="backcast-side gate for the per-plant thermal fleet; the forecast "
        "path reaches the same per-plant bins through "
        "fleet.assembly.load_or_synthesize_bins, gated on use_campd_bins + "
        "CAMPD_BINNING_ISOS (see the ffr-1e findings doc for the one residual "
        "asymmetry: the backcast's legacy_n_bins=0 fallback has no forecast twin)",
        evidence=(
            _BACKCAST_ORCH,
            "src/market_sim/data/fleet/assembly.py",
            "src/market_sim/runner.py",
        ),
    ),
    # -- scenario inputs -----------------------------------------------------
    ParityDeclaration(
        fields=(
            "campd_bins_path",
            "plant_registry_path",
            "plant_emission_rates_path",
            "plant_emission_rates_v2_path",
            "control_retrofit_path",
        ),
        disposition=SCENARIO_INPUT,
        why="on-disk artifact paths resolved through config/paths.py — "
        "plumbing both modes set from the same registry, not a mechanism",
        evidence=(
            "src/market_sim/config/scenarios.py",
            "src/market_sim/config/paths.py",
        ),
    ),
    ParityDeclaration(
        fields=("net_cone_forward_escalation",),
        disposition=SCENARIO_INPUT,
        why="FORECAST-ONLY capacity-price axis that a backcast never chooses — "
        "__post_init__ coerces it in mode='backcast' (no capacity evolution "
        "runs there), so its value in a keeper's run_config.json is the "
        "coercion, not an armed lever. Surfaced 2026-08-03 when owner decision "
        "D-3a moved the default 'hold_last' -> 'reindex_gross': every keeper's "
        "COMMITTED run_config.json still records the pre-flip coerced "
        "'hold_last', which reads as non-default and so as 'armed' in all six "
        "ISOs at once. Nothing on either path consumes it yet in any case — "
        "capacity_market.forward_net_cone_anchor is not wired into "
        "capacity_price_per_firm_mw_yr (FF-2C owns that seam), so there is no "
        "fork for a parity gap to open in. Re-check this row WHEN FF-2C WIRES "
        "IT: at that point it becomes a real forecast mechanism and must "
        "resolve to a forecast-orchestrator consumer like any other.",
        evidence=(
            "src/market_sim/config/scenarios.py",
            "src/market_sim/config/capacity_market.py",
        ),
    ),
    # -- FILED GAPS ----------------------------------------------------------
    # Each of these is armed in a CURRENT keeper and has no forecast-side
    # consumer and no by-design reason to lack one. FFR-1E files them; wiring
    # is a follow-up session per mechanism (the session prompt forbids this
    # session from wiring anything it finds).
    ParityDeclaration(
        fields=("reliability_floor_overrides",),
        disposition=GAP,
        why="NYISO keeper uses it to DISABLE the five peak-window "
        "reliability-floor limbs (NYISO_PEAK_WINDOW_FLOORS_OFF, owner "
        "directive 2026-07-27); the forecast orchestrator never reads the "
        "override dict, so a forecast on the keeper config re-arms the very "
        "floors the directive removed",
        finding="docs/handoffs/ffr-1e-forecast-parity-check-2026-07-31.md",
        evidence=(_BACKCAST_ORCH, "src/market_sim/data/floor_mechanisms.py"),
    ),
    ParityDeclaration(
        fields=("tranche_startup_conditional_runs",),
        disposition=GAP,
        why="condition-keyed fast-start amortization horizon (CAMPD-measured "
        "run-length bands × the hour's net-load percentile) — a forward-"
        "reproducible offer-surface mechanism armed in the MISO and PJM "
        "keepers with no forecast-side call site",
        finding="docs/handoffs/ffr-1e-forecast-parity-check-2026-07-31.md",
        evidence=(_BACKCAST_ORCH,),
    ),
    ParityDeclaration(
        fields=("caiso_storage_shape_anchor",),
        disposition=GAP,
        why="measured p95 hour-of-day charge/discharge capability envelope per "
        "MW of fleet — a capability input (rule 13-admissible, regenerates "
        "forward) armed in the CAISO keeper with no forecast-side call site",
        finding="docs/handoffs/ffr-1e-forecast-parity-check-2026-07-31.md",
        evidence=(_BACKCAST_ORCH, "src/market_sim/model/storage.py"),
    ),
    ParityDeclaration(
        fields=("caiso_offer_surface_measured",),
        disposition=GAP,
        why="CAISO measured offer surface, armed in the CAISO keeper but "
        "consumed only in pipeline/backcast_config.py — the backcast config "
        "builder, not a shared builder the forecast path calls",
        finding="docs/handoffs/ffr-1e-forecast-parity-check-2026-07-31.md",
        evidence=("src/market_sim/pipeline/backcast_config.py",),
    ),
    ParityDeclaration(
        fields=("gas_offer_margin_anchor_vintage",),
        disposition=GAP,
        why="moves the gas net-revenue margin's identification point from the "
        "frozen 2023-2025 window anchor onto the SOLVE YEAR's own mean "
        "delivered-gas series (pjm-169 F4; armed in the MISO keeper since "
        "miso-264). Forward-derivable — the forecast year's own gas "
        "trajectory mean is the same quantity — yet the forecast "
        "orchestrator's apply_gas_offer_margin reads the frozen "
        "config.gas_offer_margin_anchor, so a forecast on the keeper config "
        "prices the margin at the window anchor in every year",
        finding="docs/FINDING-miso268-coal-yard-grain-and-the-open-objects-2026-09-24.md",
        evidence=(_BACKCAST_ORCH, "src/market_sim/runner.py"),
    ),
    ParityDeclaration(
        fields=("neiso_winter_fuel_inventory",),
        disposition=GAP,
        why="its own call site calls it the 'forward-derivable capacity/"
        "logistics budget' (tank fill + re-supply) and the keeper path — yet "
        "the forecast orchestrator never builds the oil-budget rows",
        finding="docs/handoffs/ffr-1e-forecast-parity-check-2026-07-31.md",
        evidence=(_BACKCAST_ORCH,),
    ),
    ParityDeclaration(
        fields=("ercot_storage_capability_measured", "ercot_storage_as_deployment"),
        disposition=GAP,
        why="measured ERCOT storage capability envelope + AS-deployment "
        "shaping, both armed in the ERCOT keeper; the admissible twin "
        "storage_as_commitment IS shared, so these two forking to the "
        "backcast orchestrator alone is an asymmetry, not a design",
        finding="docs/handoffs/ffr-1e-forecast-parity-check-2026-07-31.md",
        evidence=(_BACKCAST_ORCH,),
    ),
    # ercot_capability_reconciliation (ercot-219 stage 1) carries NO row here
    # deliberately: it lives in the SHARED fleet assembly
    # (data/fleet/arrays.py::_apply_outage_overlays) like the rest of the
    # measured-overlay family, so the checker resolves it through the
    # shared-module evidence tier; its backcast-only enforcement is the
    # _BACKCAST_ONLY_OVERLAY_FIELDS mode guard (ValueError in forecast mode)
    # plus the in-block mode gate. A BACKCAST_ONLY row would be flagged
    # stale ("IS forecast-wired via shared module") by the checker itself.
    ParityDeclaration(
        fields=(
            "ercot_exhaustion_expectation",
            "ercot_storage_reservation_offer",
        ),
        disposition=BACKCAST_ONLY,
        why="ercot-219 stages 2-3 (exhaustion expectation + P1-only storage "
        "reservation-price offer): forward-computable by construction — the "
        "expectation regenerates from the model's own state and "
        "self-extinguishes with the sequestration design (post-reform / "
        "RTC+B) — but wired in the backcast orchestrator only today; arming "
        "them forward is its own future decision, never a silent fork. "
        "PRECOMMIT-ercot219 §1.2-§1.3.",
        evidence=(_BACKCAST_ORCH,),
    ),
    # -- FILED GAPS, owner ruling R-X (2026-09-02) ---------------------------
    # The ercot-221 / ercot-223 backcast->forecast fork
    # (docs/FINDING-fast-tier-repair-2026-09.md §3.8 + §7.1). The owner ruled
    # FILE GAP DECLARATIONS — the FFR-1E route the two storage-envelope fields
    # above took: the fork is KNOWN and TRACKED, not silenced. Whether to wire
    # it forward (the runner.py / pipeline/solve.py seam,
    # p1_storage_discharge_cost) or to declare it BACKCAST_ONLY is the
    # capx/forecast desk's adjudication and is deliberately NOT decided here.
    # Filing record: docs/FINDING-fr22-gap-leg2-2026-09.md.
    ParityDeclaration(
        fields=("ercot_storage_adaptive_expectation", "ercot_adaptive_event_release"),
        disposition=GAP,
        why="ercot-221 adaptive-expectation storage offer floor (a second P1 "
        "pass floored on the model's OWN daily settle duals — zero measured "
        "content) and its ercot-223 event-realized release guard, both armed "
        "in the ERCOT forward keeper; their only consumer is the backcast "
        "orchestrator's two-pass block, so a forecast on the keeper config "
        "silently drops the floor. Wire-forward vs BACKCAST_ONLY is the "
        "forecast desk's call (owner ruling R-X), not this row's",
        finding="docs/FINDING-fr22-gap-leg2-2026-09.md",
        evidence=(_BACKCAST_ORCH,),
    ),
    # Same fork class, surfaced by the same test on the same run, armed in the
    # NYISO keeper before R-X's pin but masked from R-W's §3.8 by the test's
    # per-ISO assertion order (ERCOT first). Filed under the R-X route — the
    # disposition that decides nothing — never as BACKCAST_ONLY.
    ParityDeclaration(
        fields=("nyiso_seam_par_attribution",),
        disposition=GAP,
        why="nyiso-127 full-seam PAR attribution — all four NYISO_external "
        "border-link caps rebuilt from the measured MIS P-32 per-neighbour "
        "schedules (the SCH-PJ-NY row split by NYISO's published PAR shares); "
        "armed in the NYISO keeper since nyiso-159 and consumed only in the "
        "backcast orchestrator's TTC overlay block. Whether it joins the "
        "measured-TTC BACKCAST_ONLY family or gets a forward channel is the "
        "forecast desk's call — its superseded sibling "
        "nyiso_seam_deliverability_envelope stays pinned open in "
        "tests/scoring/test_forecast_parity.py on the same question",
        finding="docs/FINDING-fr22-gap-leg2-2026-09.md",
        evidence=(_BACKCAST_ORCH, "src/market_sim/data/nyiso_par_attribution.py"),
    ),
    # The superseded HALF of that same NYISO pair (Y-18, 2026-09-06). It is the
    # `elif` limb at run_calibration.py:2739-2756 — armed in the keeper but
    # SHADOWED at runtime by nyiso_seam_par_attribution above (rule 19
    # [R-ONE-MECH]: exactly one of the two applies). Shadowing is a fact about
    # the current keeper, not an admissibility answer, which is why the field
    # still needs a row: a keeper that later drops the PAR attribution
    # re-exposes the fork.
    #
    # BACKCAST_ONLY IS NOT AVAILABLE HERE, and the reason is the code's rather
    # than this row's: data/nyiso_seam_envelope.py:50-58 carries a section headed
    # "Admissibility (rule 13 [R-MEASURED])" answering BOTH limbs of the test
    # affirmatively — "It regenerates for a forward year from the forward tie set
    # by the same frozen formula and responds to changed conditions … a new tie
    # such as CHPE is picked up automatically". The construction is a frozen
    # formula over the TIE SET (p90 of the directionally-clipped net schedule per
    # (month x hod) bin at the definitional NYISO_SEAM_FLOW_PERCENTILE), not a
    # per-year artifact like ercot_storage_as_soc_reserve above, and not the
    # measured outage/derate schedule that makes ercot_gtc_limits_measured
    # backcast-only. A BACKCAST_ONLY row would assert a non-regenerability the
    # code denies — the caiso_ct_peaker_committed_measured reasoning below.
    #
    # It is filed GAP beside its SUPERSEDING twin rather than wired forward
    # because the two are ONE question: wiring the shadowed limb while the limb
    # that actually fires stays open would arm two-of-four links forward and
    # four-of-four in backcast, a worse fork than the one being closed. Owner
    # ruling R-X reserved that call to the forecast desk, and the twin's row
    # above already names this field as pinned open "on the same question".
    # Adjudication + the desk's stated question: the Y-18 finding, 2.2-2.5.
    ParityDeclaration(
        fields=("nyiso_seam_deliverability_envelope",),
        disposition=GAP,
        why="nyiso-125 two-link external seam deliverability envelope (NYC / "
        "Long_Island measured p90 directional MIS P-32 envelope in place of the "
        "flat symmetric statics), armed in the NYISO keeper and consumed only "
        "by the backcast orchestrator's TTC overlay block. Its own module "
        "asserts rule-13 forward regeneration and condition-response verbatim, "
        "so BACKCAST_ONLY would assert a non-regenerability the code denies; "
        "but it is the rule-19 SUPERSEDED half of a pair whose superseding half "
        "(nyiso_seam_par_attribution) is itself an open GAP under owner ruling "
        "R-X, so wiring this limb forward alone would widen the fork rather "
        "than close it. Both halves are the forecast desk's single call",
        finding="docs/handoffs/FINDING-y18-fr22-parity-2026-09-06.md",
        evidence=(_BACKCAST_ORCH, "src/market_sim/data/nyiso_seam_envelope.py"),
    ),
    # Same fork class again, one keeper later: armed by the caiso-241 promotion
    # (2026-09-03, #4663) whose lane left the FR-22 duty undischarged. Filed by
    # the Y-4 audit lane under the R-X route.
    #
    # BACKCAST_ONLY IS NOT AVAILABLE HERE, and the reason is the code's, not
    # this row's: the field is DELIBERATELY absent from
    # scenarios._BACKCAST_ONLY_OVERLAY_FIELDS, and its docstring states the
    # positive claim -- `avg_committed_p50` is a measured PHYSICAL heat-rate
    # ratio that regenerates for a forward year from CAMPD conduct and responds
    # to fleet change, so it is rule-13 [R-MEASURED] admissible in BOTH modes
    # (unlike its caiso-240 sibling caiso_st_gas_peak_measured, which IS
    # registered there as measured BID conduct keyed to one year's OASIS
    # record). A BACKCAST_ONLY row would assert a non-regenerability the code
    # denies. PARAMETER_OF is unavailable too: the block requires no other
    # CAISO offer-surface flag armed, is band-disjoint from all of them
    # (`committed` only), and is applied LAST so it wins over them.
    ParityDeclaration(
        fields=("caiso_ct_peaker_committed_measured",),
        disposition=GAP,
        why="caiso-241 CT_PEAKER `committed` band grounded on its own measured "
        "phys_committed (0.991 avg_committed_p50, n = 75) in place of the "
        "fitted 1.35 — armed in the CAISO keeper and consumed only in "
        "pipeline/backcast_config.py, the backcast config builder, exactly "
        "like its caiso_offer_surface_measured sibling: the CAISO per-ISO "
        "merge curve and every substitution into it live there, so a forecast "
        "on the keeper config records the flag armed and still prices the "
        "min-load block at 1.35. Wire-forward vs an evidenced BACKCAST_ONLY "
        "is the forecast desk's call (owner ruling R-X), not this row's",
        finding="docs/FINDING-caiso-ct-peaker-committed-measured-parity-2026-09.md",
        evidence=("src/market_sim/pipeline/backcast_config.py",),
    ),
    # Three more promoter misses, filed by audit lane Y-29 (board v42 §4/§5,
    # 2026-09-24). None of the promoting lanes (nyiso-232, nyiso-241 ->
    # nyiso-247, miso-268) declared its field; each row below states the
    # posture the mechanism's OWN record and code give, and routes the
    # wire-forward vs BACKCAST_ONLY call to the owning desk (owner ruling R-X).
    # No forecast consumer is invented.
    #
    # The two NYISO rows are the caiso_ct_peaker_committed_measured class
    # exactly: a band re-grounded on the class's own CAMPD-measured `phys_*`
    # conduct (a physical ratio that regenerates forward, so BACKCAST_ONLY
    # would assert a non-regenerability the code does not claim — neither
    # field is in scenarios._BACKCAST_ONLY_OVERLAY_FIELDS), substituted into
    # the NYISO per-ISO merge curve that only pipeline/backcast_config.py
    # builds. A forecast on the keeper config records the flag armed and still
    # prices the pre-repair bands.
    ParityDeclaration(
        fields=("nyiso_ct_peaker_committed_measured",),
        disposition=GAP,
        why="nyiso-241 CT_PEAKER `committed` band grounded on its own measured "
        "phys_committed (0.843) in place of the fitted 1.35 start hurdle, "
        "which double-charged the start recovery tranche_startup_amortization "
        "already pays; carried by the NYISO keeper since nyiso-247. Consumed "
        "only in pipeline/backcast_config.py, the backcast config builder, so "
        "a forecast on the keeper config still prices the min-load block at "
        "1.35. Wire-forward vs an evidenced BACKCAST_ONLY is the forecast "
        "desk's call with the NYISO desk (owner ruling R-X)",
        finding="docs/handoffs/FINDING-y29-promotion-provenance-2026-09-24.md",
        evidence=(
            "src/market_sim/pipeline/backcast_config.py",
            "docs/PRECOMMIT-nyiso247-fuel-invariance-limb-2026-09-20.md",
        ),
    ),
    ParityDeclaration(
        fields=("nyiso_st_gas_econ_bands_deleaked",),
        disposition=GAP,
        why="nyiso-232 third limb of the rule-25 [R-ISO-SCOPE] de-leak: the "
        "_NYISO_OFFER_CURVE ST_GAS econ_low/econ_high re-grounded on the "
        "measured steam marginal instead of the CC class's reach ratio. Armed "
        "in the NYISO keeper (owner ruling 'Arm it') and consumed only in "
        "pipeline/backcast_config.py, so a forecast on the keeper config "
        "still prices ST_GAS on the leaked CC-derived bands. Wire-forward vs "
        "an evidenced BACKCAST_ONLY is the forecast desk's call with the "
        "NYISO desk (owner ruling R-X)",
        finding="docs/handoffs/FINDING-y29-promotion-provenance-2026-09-24.md",
        evidence=(
            "src/market_sim/pipeline/backcast_config.py",
            "docs/PRECOMMIT-nyiso247-fuel-invariance-limb-2026-09-20.md",
        ),
    ),
    # The MISO row is NOT PARAMETER_OF its parent coal_fuel_inventory, though
    # the field is a declared sub-gate of it (rule 19), because the parent's
    # FORECAST_WIRED reading is a checker false positive: its only non-backcast
    # "consumer" is the string key in data/input_completeness.py:235 (a
    # completeness report), while scripts/run_calibration.py RAISES on the
    # parent in any mode other than "backcast" ("that carry is not built
    # yet"). PARAMETER_OF would inherit that false wiring. The record's own
    # forward story (PRECOMMIT §2: "a forecast year's per-yard opening stock is
    # the model's own carried per-yard inventory") is forward-derivable and not
    # built, which is a GAP. The parent's misclassification is routed in the
    # Y-29 FINDING, not repaired here.
    ParityDeclaration(
        fields=("coal_fuel_inventory_plant_grain",),
        disposition=GAP,
        why="miso-268 per-coal-YARD annual grain of coal_fuel_inventory "
        "(Dec(Y-1) stock + mean Y-2..Y-1 receipts per yard), armed in the "
        "MISO keeper. Its forward story is the model's own carried per-yard "
        "inventory, which is not built: the backcast orchestrator raises on "
        "the parent outside mode='backcast' and the forecast orchestrator "
        "never builds the budget rows. Building the carry is the MISO desk's "
        "and the forecast desk's call (owner ruling R-X)",
        finding="docs/handoffs/FINDING-y29-promotion-provenance-2026-09-24.md",
        evidence=(
            _BACKCAST_ORCH,
            "docs/PRECOMMIT-miso268-coal-yard-grain-2026-09-24.md",
        ),
    ),
    # PJM-NEXT card 1 (2026-09-25) armed spp-49's benchmark membership union
    # in the PJM keeper. It is SCORING, not a mechanism: it widens which
    # plants' EIA-923 generation enter the backcast ACTUALS
    # (run_calibration_full._iso_plant_ids) and never touches the LP, so a
    # forecast — which has no measured actuals to score against — has nothing
    # for it to reach.
    ParityDeclaration(
        fields=("benchmark_membership_vintage_union",),
        disposition=BACKCAST_ONLY,
        why="spp-49 benchmark-side plant membership union: widens the EIA-923 "
        "backcast ACTUALS to the solve year's EIA-860 BA cohort; scoring-only, "
        "no LP effect, so a forecast (no measured actuals) has no consumer by "
        "design",
        evidence=(
            "scripts/run_calibration_full.py",
            "docs/PRECOMMIT-pjm-next-c1-year-correct-membership-2026-09-25.md",
        ),
    ),
)


def declaration_for(field: str) -> ParityDeclaration | None:
    """Return the declaration covering ``field``, or None if undeclared."""
    for row in DECLARATIONS:
        if field in row.fields:
            return row
    return None
