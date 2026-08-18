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
    ParityDeclaration(
        fields=("ercot_capability_reconciliation",),
        disposition=BACKCAST_ONLY,
        why="ercot-219 stage-1 measured NP6-905 aggregate-capability "
        "reconciliation (B-1 SIGNED by dispatch of ERCOT-219 2026-08-18): a "
        "measured availability overlay keyed to the year's published "
        "real-time telemetry — no forward analogue by definition (rule 13); "
        "the forecast substitute is the model's own availability chain. "
        "PRECOMMIT-ercot219 §1.1.",
        evidence=(_BACKCAST_ORCH,),
    ),
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
)


def declaration_for(field: str) -> ParityDeclaration | None:
    """Return the declaration covering ``field``, or None if undeclared."""
    for row in DECLARATIONS:
        if field in row.fields:
            return row
    return None
