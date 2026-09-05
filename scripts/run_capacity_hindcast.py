#!/usr/bin/env python
"""Capacity hindcast + T1-X crossover + T1-FF full-forward harness.

(W2-P5 / FF-0E / FH-1 — plan §1.3, §2.2; T1-FF:
``docs/hindcast-forward-plan-2026-07.md`` §2.)

Runs the *forecast* machinery from a vintage fleet snapshot to test whether the
capacity-evolution screens (retirement / economic-entry / storage / CCS)
reproduce the builds and retirements an ISO actually saw. It is NOT a backcast:
``mode`` stays ``"forecast"`` and no backcast overlay fires -- the hindcast flag
only switches on vintage fleet init, realized per-year demand (no growth
scaling), the chosen fuel path, and the 2022 quarantine bridge.

Three modes, selected by ``--vintage`` / ``--crossover`` / ``--forward-from-base``:

* **Plain hindcast** (``--vintage 2020``, default; plan §1.1): initialise from
  the **EIA-860 2020 vintage**, evolve 2021 → 2025. 2021 seeds the price/margin
  signal but is not scored; **2022 is a bridge -- evolved but never solved, its
  data never read** (rule 22); 2023-2025 are solved and scored. Allowed solve
  years ``{2021, 2023, 2024, 2025}`` (``scripts.lib.holdout_policy``).

* **T1-X crossover** (``--crossover``, requires ``--vintage 2023``; plan §2.2):
  initialise from the **EIA-860 2023 vintage** and run the crossover window
  ``--start-year 2023 --end-year 2027``. 2023-2025 use realized per-year demand
  and realized fuel (the rule-13-admissible physical inputs); 2026+ switch to
  **pure forward drivers** — growth-scaled demand from the last realized year,
  the AEO gas path, forecast coal/oil, statistical outages, and NO measured
  overlays (the realized demand loader and the F923 plant-monthly overlay are
  both skipped for forward years). No bridge year — 2026/2027 are SOLVED as
  forecast-mode years (rule-22-legal: they read no measured H1-2026 actuals).
  Allowed solve years ``{2023, 2024, 2025, 2026, 2027}``. Score with
  ``scripts/score_crossover.py`` (dispatch skill + capacity events 2023-2025;
  years >= 2026 are invariants/plausibility only — the scorer REFUSES to read
  any bench/actual for a year >= 2026). **Tracked set (NEISO-RC-R R4,
  2026-08-31): a registered crossover bundle COMMITS its per-year
  ``evolution_<year>.json`` ledgers alongside meta/run_config/score** — the
  S-4b T1-F bundles already do, and the capxd14-era crossover bundles' bare
  three-file set left every mechanism claim about them
  inferred-with-mechanism (lag-censored retirement decisions unobservable;
  ``FINDING-capx-neiso-rc-phase0-2026-08-30.md`` §3/§6 R4). The scorer's
  ``retirement_decisions_in_window`` block degrades to an explicit note when
  the ledgers are absent.

* **T1-FF full-forward hindcast** (``--forward-from-base``; FH-1, hindcast-
  forward plan §2): the crossover boundary is pointed at the window's OWN
  start year (``crossover_forward_year = start_year``), so EVERY solve year
  runs the forward input stack — growth-scaled demand from the pinned weather
  base, trajectory fuel, statistical outages, estimator emission rates, no
  measured overlays — while being scored against held actuals. The gap to the
  ISO's keeper backcast is the measured price of the overlays. Window rules
  are the PLAIN-hindcast rules (2021 floor, end <= 2025, {2021} seed, 2022
  bridge); the vintage must be at/before the base year (Phase A: base 2023 /
  vintage 2023; Phase B: base 2021 / vintage 2020). Two pre-registered arms
  (plan §2.1), ``--arm``:

  - ``realized`` (Arm R, the default): realized annual Henry Hub
    (``hindcast_realized``) and per-solve-year weather
    (``crossover_solve_year_weather`` — given-weather / perfect-foresight-
    driver posture). Asks: *is the forecast configuration structurally right?*
  - ``asknown`` (Arm K): the as-known AEO gas vintage as-of the base year
    (``hindcast_asknown_aeo<base>``; hard error when that trajectory has not
    been intaken — FH-3) and the BASE year's weather for every solve year.
    Asks: *what is true ex-ante forecast skill?*

  Scoring never leaves 2023-2025 (the scorer refuses both bounds), so no
  rule-22 marker is spent and the holdout freeze is not implicated — the
  governance record is printed at launch rather than left implicit.

**Capacity-price posture (FFR-2E; audit FR-14).** The harness DEFAULT is the
SHIPPED production posture: ``capacity_market_clearing_by_iso`` is left at the
``ScenarioConfig`` default, so a leg for an ISO the forecast ships curve-ON
(PJM / MISO / CAISO / NEISO today) clears its RA position on that ISO's
published sloped VRR — the hindcast validates the configuration the forecast
actually runs. Two explicit arms remain:

* ``--fixed-net-cone`` — the flat net-CONE stub
  (``capacity_market_clearing_by_iso=None``). This was the harness default
  BEFORE FFR-2E, so it reproduces the posture every committed pre-2026-08-02
  leg ran; those legs' FC-3 verdicts stand as scored.
* ``--capacity-market-clearing`` — the RC-1B force-ON probe (``{iso: True}``),
  now needed only for an ISO production ships curve-OFF (ERCOT, NYISO).

The two are mutually exclusive. No ``ScenarioConfig`` default moves here: the
harness selects among postures the config already supports (rule 24).

**Announced-exit verification (owner directive 2026-08-22).** The harness
DEFAULT arms ``hindcast_verified_announced_exits``: announced/"known"
retirement dates from the vintage EIA-860 are countered by the realized
record before they execute — a plant whose exit was reversed outright by a
later public counter-instrument and demonstrably kept operating (the worked
case: Byron 1-2 / Dresden 2-3, 4.1 GW, 2021 dates reversed by IL CEJA's CMC
program 2021-09-15) is never false-retired. Mechanically the runner reads the
announced-REVERSAL registry without the RC-1B vintage information gate; the
confirmed-EXIT channel keeps its gate, so verification can suppress a
never-executed exit but never inject one. ``--no-verified-announced-exits``
restores the pure ex-ante arm (the posture every committed pre-2026-08-22 leg
ran — their verdicts stand as scored, and the scorer reports raw + IS-2020
side by side under either posture).

Rule 12: years run sequentially inside one invocation; independent variants /
ISOs are launched as concurrent background invocations with separate
``--out-dir``s.

Usage::

    # plain hindcast
    python scripts/run_capacity_hindcast.py --iso ERCOT --fuel-variant realized \\
        --out-dir results/hindcast/ercot-2021-2025-realized
    # T1-X crossover
    python scripts/run_capacity_hindcast.py --iso ERCOT --crossover --vintage 2023 \\
        --start-year 2023 --end-year 2027 \\
        --out-dir results/hindcast/ercot-2023-2027-crossover
    # T1-FF full-forward (Phase A, Arm R)
    python scripts/run_capacity_hindcast.py --iso ERCOT --forward-from-base \\
        --arm realized --vintage 2023 --start-year 2023 --end-year 2025 \\
        --out-dir results/hindcast/ercot-2023-2025-t1ff-armr

Then score with ``scripts/score_capacity_hindcast.py`` (hindcast) or
``scripts/score_crossover.py`` (crossover / full-forward).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
# Invoking this file directly (``python scripts/run_capacity_hindcast.py``) puts
# its own directory on sys.path[0], not the repo root, so the model's
# ``scripts.lib.clean_io`` clean-data seam (e.g. eia_loader's repaired
# demand-profile fallback) silently disables itself and falls back to raw data
# -- see the PJM demand-defect investigation, 2026-07-05. Add the repo root so
# it resolves, matching scripts/regenerate_clean.py's subprocess bootstrap.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.config.capacity_market import (  # noqa: E402
    resolve_capacity_market_clearing,
    resolve_capacity_market_supply_clearing,
)
from market_sim.config.iso_configs import (  # noqa: E402
    apply_iso_scenario_defaults,
)
from market_sim.config.scenarios import (  # noqa: E402
    CROSSOVER_FORWARD_BOUNDARY_YEAR as _SRC_CROSSOVER_FORWARD_YEAR,
)
from market_sim.config.scenarios import (  # noqa: E402
    ScenarioConfig,
    crossover_unbridges_year,
)  # isort: skip
from market_sim.results import cache as cachemod  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from market_sim.pipeline.api import run_scenario  # noqa: E402
from market_sim.runner import HINDCAST_BRIDGE_YEARS as _RUNNER_BRIDGE_YEARS  # noqa: E402
from market_sim.runner import hindcast_solve_years  # noqa: E402
from scripts.lib import holdout_policy  # noqa: E402
from scripts.lib.forecast_posture import (  # noqa: E402
    shipped_capacity_clearing_by_iso,
    shipped_forecast_xyear_warmstart,
)
from scripts.lib.run_record import (  # noqa: E402
    Derived,
    FromArgs,
    FromConfig,
    RecordSpec,
    write_run_config,
)

# Rule-22 carve-outs now live in scripts/lib/holdout_policy.py (FH-1 — moved
# out of prose and this file's former local literals): the {2021} seed, the
# {2022, 2026} bridge, and the solvable set. The runner keeps its own bridge
# constant (src must not import scripts); fail loud here if they ever drift.
HINDCAST_BRIDGE_YEARS = holdout_policy.HINDCAST_BRIDGE_YEARS
if HINDCAST_BRIDGE_YEARS != _RUNNER_BRIDGE_YEARS:  # pragma: no cover
    raise SystemExit(
        "holdout_policy.HINDCAST_BRIDGE_YEARS and runner.HINDCAST_BRIDGE_YEARS "
        f"disagree: {sorted(HINDCAST_BRIDGE_YEARS)} vs "
        f"{sorted(_RUNNER_BRIDGE_YEARS)} — fix the drift before running"
    )

# The only years a plain (or full-forward) hindcast may solve: the training
# window plus the {2021} seed (holdout_policy.HINDCAST_SOLVE_YEARS). 2022/2026
# are quarantined (rule 22); 2022 is bridged (evolved, not solved), 2026 is
# out of the window entirely.
ALLOWED_SOLVE_YEARS = holdout_policy.HINDCAST_SOLVE_YEARS
# A T1-X crossover (FF-0E, plan §2.2) additionally solves 2026/2027 as
# forecast-mode years (rule-22-legal: no measured H1-2026 actuals are read).
CROSSOVER_ALLOWED_SOLVE_YEARS = frozenset({2023, 2024, 2025, 2026, 2027})
# First forecast (forward-driver) year of a crossover: 2023-2025 realized,
# 2026+ pure forward drivers (plan §2.2). Since FFR-3U the literal lives in
# ``src`` (it is half of the bridge predicate, which src owns); this is an
# alias, so the two can never drift apart the way the two window predicates did.
CROSSOVER_FORWARD_YEAR = _SRC_CROSSOVER_FORWARD_YEAR
# The EIA-860 vintage a plain hindcast seeds from (plan §1.1); a crossover seeds
# from the 2023 vintage (plan §2.2); a full-forward hindcast seeds from any
# allowed vintage at/before its base year (FH-1: Phase A 2023, Phase B 2020).
# Selected by --vintage.
DEFAULT_VINTAGE_YEAR = 2020
CROSSOVER_VINTAGE_YEAR = 2023
ALLOWED_VINTAGES = (2020, 2023)

FUEL_VARIANT_GAS_PATH = {
    "realized": "hindcast_realized",
    "asknown": "hindcast_asknown_aeo2021",
}


def full_forward_gas_path(arm: str, base_year: int) -> str:
    """Return the T1-FF gas trajectory for an arm at a base year (plan §2.1).

    Arm R prices every (forward) year on realized annual Henry Hub; Arm K on
    the AEO Reference vintage as-known at the base year. An Arm K base whose
    as-known trajectory has not been intaken (only AEO2021 exists today;
    AEO2023 is FH-3's intake) is a HARD error — never a silent fallback to a
    forecast-edition path, which would be the §4-row-7 back-hold trap wearing
    a different hat.
    """
    from market_sim.config.fuel_trajectories import HENRY_HUB_TRAJECTORIES

    if arm == "realized":
        return "hindcast_realized"
    path = f"hindcast_asknown_aeo{int(base_year)}"
    if path not in HENRY_HUB_TRAJECTORIES:
        raise SystemExit(
            f"--arm asknown at base {base_year} needs the as-known gas "
            f"trajectory {path!r}, which is not in HENRY_HUB_TRAJECTORIES — "
            "land it first (FH-3 intake, cited to the AEO edition); refusing "
            "to substitute a different-vintage path (rule 13)"
        )
    return path


def window_forward_boundary(
    start_year: int, crossover: bool, forward_from_base: bool
) -> int | None:
    """Return the ``crossover_forward_year`` a window's config will carry.

    One resolution, two readers (FFR-3U, rule 19 ``[R-ONE-MECH]``):
    :func:`build_config` sets the field from THIS function, and
    :func:`_validate_window` derives the runner's bridge predicate from it — so
    the guard can never be checking a different window than the one that
    solves. FFR-3Q's breach was exactly that divergence: the guard read the
    ``--crossover`` CLI flag (False for a T1-FF run) while the runner read the
    boundary the config actually carried (the T1-FF base year).
    """
    if forward_from_base:
        return start_year
    return CROSSOVER_FORWARD_YEAR if crossover else None


def window_solve_years(
    start_year: int, end_year: int, crossover: bool, forward_from_base: bool
) -> list[int]:
    """Return the years the RUNNER will solve for this window.

    Thin composition of :func:`window_forward_boundary` with
    :func:`market_sim.runner.hindcast_solve_years` — the runner's own bridge
    predicate, not a harness-side re-derivation. Used by the guard
    (:func:`_validate_window`), by the launch governance banner, and by the
    completion parity assertion, so all three speak about one set.
    """
    return hindcast_solve_years(
        start_year,
        end_year,
        hindcast=True,
        crossover_forward_year=window_forward_boundary(
            start_year, crossover, forward_from_base
        ),
    )


def _validate_window(
    start_year: int,
    end_year: int,
    crossover: bool,
    forward_from_base: bool = False,
) -> None:
    """Enforce the rule-22 quarantine on the requested window.

    The plain-hindcast guard is unchanged (allowed solve years
    ``{2021, 2023, 2024, 2025}``, ``end <= 2025``, 2022 bridged). A crossover
    (FF-0E, plan §2.2) additionally admits 2026/2027 as forecast-mode solves,
    requires ``start >= 2023``, and un-bridges its forward years (>= 2026) — so
    the holdout guard stays intact for plain-hindcast mode while the crossover
    window is exactly the rule-22-legal ``{2023, 2024, 2025, 2026, 2027}``.

    A full-forward hindcast (``forward_from_base``, FH-1) keeps the PLAIN
    window rules exactly — the 2021 floor, the ``end <= 2025`` cap, the
    ``{2021}`` seed allowance and the 2022 bridge — because pointing the input
    boundary at the base year changes which STACK a year solves on, never
    which years may be solved. The solvable set is read from
    ``scripts.lib.holdout_policy`` (the carve-outs' single home), and every
    non-bridge year outside it fails closed with its tier named.

    **The solve-year set is the RUNNER's** (FFR-3U):
    :func:`market_sim.runner.hindcast_solve_years`, over the boundary
    :func:`build_config` will actually set. Before FFR-3U this function
    computed its own set from the ``--crossover`` flag, dropped 2022 as a
    bridge for a base-2021 T1-FF window the runner then SOLVED, and so never
    policy-checked the year at all — the fail-closed check could not fire
    because the guard had already deleted the year (FFR-3Q §2.2.1, owner
    Addendum L.1). Every year the runner solves is now checked here.
    """
    if start_year < 2021:
        raise SystemExit(
            "hindcast start-year must be >= 2021 (demand profiles start 2021)"
        )
    if crossover and forward_from_base:
        raise SystemExit(
            "--crossover and --forward-from-base are mutually exclusive: a "
            "crossover's boundary is 2026, a full-forward run's boundary is "
            "its own start year (one seam, two pointings — rule 19)"
        )
    if crossover:
        if start_year < 2023:
            raise SystemExit("crossover start-year must be >= 2023 (plan §2.2)")
        if end_year > 2027:
            raise SystemExit("crossover end-year must be <= 2027 (plan §2.2 window)")
        allowed = CROSSOVER_ALLOWED_SOLVE_YEARS
    else:
        if end_year > 2025:
            raise SystemExit(
                "hindcast end-year must be <= 2025 (2026 is a rule-22 holdout -- "
                "no solve/score; use --crossover for the forecast-mode 2026/2027 window)"
            )
        allowed = ALLOWED_SOLVE_YEARS
    # The years the RUNNER will solve, from the runner's own predicate over the
    # boundary build_config will set — never a locally recomputed set.
    solve_years = window_solve_years(start_year, end_year, crossover, forward_from_base)
    for y in solve_years:
        if y not in allowed:
            kind = "crossover" if crossover else "hindcast"
            raise SystemExit(f"year {y} is not an allowed {kind} solve year")
    # Fail-closed policy check (FH-1): the hindcast-lane solvable set is owned
    # by holdout_policy — anything outside training + seed refuses with its
    # tier named, whatever the local `allowed` literal says. Crossover forward
    # years (2026+) are the one legal exception (forecast-mode solves reading
    # no measured actuals, rule 22) — and since FFR-3U that exemption is the
    # SAME scoped predicate the runner un-bridges on (a genuine crossover, not
    # a T1-FF base-year boundary), so no year can be exempted here that the
    # runner would solve as a quarantined bridge year.
    _policy_years = [
        y
        for y in solve_years
        if not crossover_unbridges_year(
            y,
            crossover_forward_year=window_forward_boundary(
                start_year, crossover, forward_from_base
            ),
            start_year=start_year,
        )
    ]
    violations = holdout_policy.hindcast_solve_year_violations(_policy_years)
    if violations:
        raise SystemExit(
            "rule-22 holdout policy refuses this window:\n  - "
            + "\n  - ".join(violations)
        )


def production_capacity_clearing_default() -> dict[str, bool] | None:
    """Return the SHIPPED ``capacity_market_clearing_by_iso`` default.

    Thin alias over :func:`scripts.lib.forecast_posture.
    shipped_capacity_clearing_by_iso`, which FFR-3D made the ONE reader of the
    shipped posture across every runner (owner decision C.4(a) B1, signed
    2026-08-03). The implementation moved out of this file unchanged; the name
    is retained because ``resolve_capacity_clearing_posture`` and the FFR-2E
    posture tests are written against it.
    """
    return shipped_capacity_clearing_by_iso()


def resolve_capacity_clearing_posture(
    iso: str, force_on: bool, fixed_net_cone: bool
) -> tuple[dict[str, bool] | None, str]:
    """Resolve the leg's capacity-clearing posture (FFR-2E, audit FR-14).

    Returns ``(capacity_market_clearing_by_iso, posture_label)``. Three
    postures, in precedence order:

    * ``fixed_net_cone`` (``--fixed-net-cone``) → ``None``: the flat net-CONE
      comparison arm. This was the harness DEFAULT before FFR-2E, so every
      committed pre-2026-08-02 leg is a leg of this arm and its scored FC-3
      verdict stands as-scored.
    * ``force_on`` (``--capacity-market-clearing``, the RC-1B probe) →
      ``{iso: True}``: arm the CR-1 sloped curve for THIS ISO only, whatever
      production ships. Retained because it is the only way to exercise the
      curve for an ISO production leaves OFF (ERCOT, NYISO).
    * neither (the FFR-2E DEFAULT) → the production default verbatim: the
      hindcast validates the configuration the forecast actually ships (peer
      review §3.1). ``__post_init__`` does not coerce this field for a
      ``hindcast=True`` leg, so it reaches the screens.

    No ``ScenarioConfig`` default moves here — the harness selects among
    postures the config already supports (rule 24).
    """
    if fixed_net_cone and force_on:
        raise SystemExit(
            "--fixed-net-cone and --capacity-market-clearing are mutually "
            "exclusive (they select opposite capacity-price postures)"
        )
    if fixed_net_cone:
        return None, "fixed_net_cone"
    if force_on:
        return {iso: True}, "forced_curve"
    return production_capacity_clearing_default(), "shipped"


#: The hindcast/crossover/full-forward ``meta.json`` config-describing block,
#: declared once and built FROM THE SOLVED CONFIG (FFR-3R). Four lanes each
#: found the same defect here — a meta entry sourced from ``args`` rather than
#: from the object the solve ran on (FFR-1D's inert flag, FFR-3D's
#: ``bool(None)`` on a tri-state, FFR-2E's flag-sourced clearing gate that
#: mis-classified every shipped-posture leg, FFR-3L's ``retirement_rule: null``)
#: — and each was patched key-by-key with its own comment. This spec is the
#: class fix: every key below is read off ``config`` unless it is declared
#: ``FromArgs`` with a written reason, and ``RecordSpec.assert_sourced`` refuses
#: to write a meta that disagrees with the solve. A NEW ``ScenarioConfig`` field
#: cannot appear in this meta from ``args`` without a deliberate declaration —
#: an undeclared config-named key is itself a violation.
#:
#: NB scope: this governs the RECORD only. ``args`` → ``ScenarioConfig`` in
#: ``build_config`` above is what a CLI is for and is untouched.
META_RECORD_SPEC = RecordSpec(
    {
        "iso": FromConfig(),
        "variant": FromConfig(
            field="hindcast_fuel_variant",
            why=(
                "the record keeps the short harness name; a full-forward leg sets it to the arm so meta/variant stays one vocabulary"
            ),
        ),
        "energy_only_floor": FromConfig(
            field="market_design_retirement_floor",
            cast=bool,
            why=(
                "the CLI arm is named for the market design; the field it "
                "arms is market_design_retirement_floor (build_config)"
            ),
        ),
        "entry_lookahead_reprice": FromConfig(cast=bool),
        "retirement_rule": FromConfig(),
        "limited_foresight_dispatch": FromConfig(cast=bool),
        # The RESOLVED per-ISO clearing gate, NOT the scalar field of the same
        # name (which stays off in every posture). scripts/forecast_verdict.
        # _curve_on reads this key to classify a leg curve-ON/curve-OFF, so a
        # flag-sourced value mis-classified every shipped-posture leg (FFR-2E /
        # audit FR-14). Declared Derived so the resolution is checked against
        # the solved config rather than asserted by comment.
        "capacity_market_clearing": Derived(
            lambda cfg, ctx: bool(resolve_capacity_market_clearing(cfg, ctx["iso"])),
            "the RESOLVED per-ISO gate (FFR-2E), not the scalar field",
        ),
        "capacity_market_clearing_by_iso": FromConfig(),
        # Which of the three CLI arms this leg selected — the FC-3 evidence-row
        # discriminator. Genuinely not a config property: `shipped` and
        # `forced_curve` can resolve to the same by-ISO dict for a single-ISO
        # posture, so the solved config cannot recover the operator's choice.
        # Consistency with what the config actually carries is asserted
        # separately (see _assert_posture_consistent).
        "capacity_clearing_posture": FromArgs(
            "records WHICH harness arm was selected; the resolved config "
            "cannot distinguish forced_curve from a coincident shipped posture"
        ),
        "capacity_market_clearing_forced": FromArgs(
            "the raw --capacity-market-clearing force flag, deliberately "
            "distinct from the resolved gate recorded above (FFR-2E)"
        ),
        "correlated_forced_outage": FromConfig(cast=bool),
        "entry_screen_diagnostics": FromConfig(cast=bool),
        "entry_vre_capacity_revenue": FromConfig(cast=bool),
        # capx D33 VRE build-zone resolution. FromConfig, never FromArgs: the
        # record reads the SOLVED gate, so a meta can never claim an arming the
        # solve did not carry (FFR-3R). Armed for MISO through the ISO's
        # default_scenario_overrides, so it is ON in a bare MISO invocation.
        "entry_vre_zone_selection": FromConfig(cast=bool),
        "neiso_net_icr_requirement": FromConfig(cast=bool),
        # capx D48 PJM accreditation-design devintage + DR-as-supply gates.
        # FromConfig so the record reads the SOLVED gates (FFR-3R).
        "pjm_accreditation_design_vintage": FromConfig(cast=bool),
        "pjm_demand_response_supply": FromConfig(cast=bool),
        # capx D57: the capacity-market supply-clearing gate (the PJM clearing
        # half). Derived through the ONE predicate so the record reads the
        # RESOLVED gate — an armed row over a curve gate that is off resolves
        # False here exactly as it does in the screen (FFR-3R).
        "capacity_market_supply_clearing": Derived(
            lambda cfg, ctx: bool(
                resolve_capacity_market_supply_clearing(cfg, ctx["iso"])
            ),
            "resolve_capacity_market_supply_clearing(cfg, iso): the armed "
            "row AND the curve gate; the raw mapping is recorded below",
        ),
        "capacity_market_supply_clearing_by_iso": FromConfig(),
        # capx D52 NYISO adequacy-requirement devintage gates. FromConfig so
        # the record reads the SOLVED gates (FFR-3R).
        "nyiso_requirement_forecast_peak": FromConfig(cast=bool),
        "nyiso_requirement_vintage_factors": FromConfig(cast=bool),
        # capx D59 NYISO locality capacity-curve gate. FromConfig so the
        # record reads the SOLVED gate (FFR-3R).
        "locality_capacity_curves": FromConfig(cast=bool),
        # capx D51 MISO dated-net accounting-ratio gate. FromConfig so the
        # record reads the SOLVED gate (FFR-3R).
        "adequacy_accounting_ratio_dated_net": FromConfig(cast=bool),
        # capx D53 retirement-screen sector gate. FromConfig so the record
        # reads the SOLVED gate (FFR-3R).
        "retirement_sector_gate": FromConfig(cast=bool),
        "entry_rate_limits": FromConfig(cast=bool),
        "entry_commissioning_lag": FromConfig(cast=bool),
        "exit_rate_limits": FromConfig(cast=bool),
        "capacity_screen_unified_lookahead": FromConfig(cast=bool),
        "capacity_screen_scarcity_restoration": FromConfig(cast=bool),
        # FFR-5C anti-cobweb guard relocation, armed per-invocation by the
        # FFR-9C measurement lane. FromConfig so the record reads the SOLVED
        # gate (FFR-3R: a meta may never claim an arming the solve lacked).
        "entry_pipeline_aware_signal": FromConfig(cast=bool),
        # ENTRY-SIGNAL forward-expectation construction (the disarm finding
        # §6 rung): the screens' price object becomes the zonal dual surface
        # re-leveled against the entering year's stack. FromConfig so the
        # record reads the SOLVED gate (FFR-3R).
        "entry_forward_expectation_signal": FromConfig(cast=bool),
        # capx D43 dispersion-carrying entry expectation: the screens' price
        # object becomes each zone's realized price-duration curve indexed
        # by the entering year's headroom rank. FromConfig so the record
        # reads the SOLVED gate (FFR-3R).
        "entry_dispersion_expectation_signal": FromConfig(cast=bool),
        # D11-R margin-exhaustion entry volume rule: the allocators build
        # until the screen's own repriced margin is exhausted instead of the
        # bang-bang full-cap allocation. FromConfig so the record reads the
        # SOLVED gate (FFR-3R).
        "entry_margin_exhaustion": FromConfig(cast=bool),
        # D12 scarcity-consistent entry reserve leg: the entry screens'
        # hourly reserve legs read the entering year's own expected-ORDC
        # adder instead of the prior year's realized post-solve adder.
        # FromConfig so the record reads the SOLVED gate (FFR-3R).
        "entry_forward_reserve_leg": FromConfig(cast=bool),
        # T1-H capacity-entry Phase-1 Leg A storage pair: D-2 availability-
        # year gate + D-3 cost-normalized rank on the storage entry screen.
        # FromConfig so the record reads the SOLVED gates (FFR-3R).
        "storage_entry_availability_gate": FromConfig(cast=bool),
        "storage_entry_cost_normalized_rank": FromConfig(cast=bool),
        # FFR-9C R-b SMR availability-year gate (None = shipped ungated).
        "smr_available_year": FromConfig(),
        # Announced-exit verification posture (owner directive 2026-08-22).
        # FromConfig so the record reads the SOLVED gate (FFR-3R: a meta may
        # never claim a posture the solve lacked); absent from committed
        # pre-2026-08-22 metas, which all ran the ex-ante arm.
        "hindcast_verified_announced_exits": FromConfig(cast=bool),
        # capx D42 fossil announced-date step-1 channel (the D32 R1 posture
        # A/B; GATED default-off, nothing armed). FromConfig so the record
        # reads the SOLVED gate (FFR-3R).
        "fossil_announced_exits_enabled": FromConfig(cast=bool),
        # FFR-5E procurement channel (owner decision D-18(a)). Declared
        # FromConfig, never FromArgs: the record reads the SOLVED gate, so a
        # meta can never claim an arming the solve did not carry (FFR-3R).
        "vre_procurement_additions_enabled": FromConfig(cast=bool),
        "renewable_elcc_curves": FromConfig(cast=bool),
        "gas_price_path": FromConfig(),
        "crossover_forward_year": FromConfig(),
        # Nulled when there is no forward boundary: the field still carries the
        # harness default there, and recording it would imply a forward leg.
        "crossover_forward_gas_path": Derived(
            lambda cfg, ctx: (
                cfg.crossover_forward_gas_path
                if cfg.crossover_forward_year is not None
                else None
            ),
            "not applicable (recorded null) when the leg has no forward boundary",
        ),
        # Arm K's as-of demand-growth vintage (FH-2 §7 wiring, landed FH-4).
        # FromConfig so the record reads the SOLVED posture: an Arm K leg
        # carries its base year here, every other leg records null.
        "demand_growth_vintage": FromConfig(),
        # T1-FF weather posture (FH-1 plan §2.1). Config-derived, and nulled
        # outside a full-forward leg where the arm concept does not apply.
        "weather_posture": Derived(
            lambda cfg, ctx: (
                ("solve_year" if cfg.crossover_solve_year_weather else "base_year")
                if ctx["forward_from_base"]
                else None
            ),
            "the arm's weather posture, off config.crossover_solve_year_weather",
        ),
        "vintage_year": FromConfig(
            field="eia860_vintage_year",
            why="the record drops the source prefix; the field is the EIA-860 vintage",
        ),
        "start_year": FromConfig(),
        "end_year": FromConfig(),
    },
    name="capacity-hindcast meta.json",
)


def _assert_posture_consistent(posture: str, config: ScenarioConfig, iso: str) -> None:
    """Refuse a ``capacity_clearing_posture`` label the solved config contradicts.

    The posture label is the one genuinely args-sourced config-ish key in the
    meta (it records which CLI arm the operator picked, which the resolved
    config cannot always recover). An unchecked args-sourced label is exactly
    the FFR-3R defect, so the label is instead checked for CONSISTENCY with the
    posture the config actually carries — the strongest statement the solved
    object can make about it.

    Args:
        posture: The label ``resolve_capacity_clearing_posture`` returned.
        config: The ``ScenarioConfig`` the solve ran on.
        iso: The run's ISO.

    Raises:
        SystemExit: The label and the solved config disagree.
    """
    by_iso = config.capacity_market_clearing_by_iso
    expected = {
        "fixed_net_cone": None,
        "forced_curve": {iso: True},
        "shipped": production_capacity_clearing_default(),
    }.get(posture, "<unknown posture>")
    if by_iso != expected:
        raise SystemExit(
            f"capacity_clearing_posture={posture!r} contradicts the solved "
            f"config: capacity_market_clearing_by_iso={by_iso!r}, expected "
            f"{expected!r} (FFR-3R — an args-sourced record label may not "
            "disagree with the solve)"
        )


def build_config(
    iso: str,
    start_year: int,
    end_year: int,
    variant: str,
    vintage: int = DEFAULT_VINTAGE_YEAR,
    crossover: bool = False,
    forward_from_base: bool = False,
    arm: str = "realized",
    crossover_forward_gas_path: str = "mid",
    energy_only_floor: bool = False,
    entry_lookahead_reprice: "bool | None" = None,
    limited_foresight_dispatch: bool = False,
    legacy_renewable_credit: bool = False,
    capacity_market_clearing: bool = False,
    fixed_net_cone: bool = False,
    correlated_forced_outage: "bool | None" = None,
    retirement_rule: "str | None" = None,
    entry_screen_diagnostics: bool = False,
    entry_vre_capacity_revenue: "bool | None" = None,
    neiso_net_icr_requirement: "bool | None" = None,
    pjm_accreditation_design_vintage: "bool | None" = None,
    pjm_demand_response_supply: "bool | None" = None,
    capacity_market_supply_clearing: "bool | None" = None,
    nyiso_requirement_forecast_peak: "bool | None" = None,
    nyiso_requirement_vintage_factors: "bool | None" = None,
    locality_capacity_curves: "bool | None" = None,
    adequacy_accounting_ratio_dated_net: "bool | None" = None,
    retirement_sector_gate: "bool | None" = None,
    entry_rate_limits: "bool | None" = None,
    entry_commissioning_lag: "bool | None" = None,
    exit_rate_limits: "bool | None" = None,
    capacity_screen_unified_lookahead: "bool | None" = None,
    capacity_screen_scarcity_restoration: "bool | None" = None,
    vre_procurement_additions: "bool | None" = None,
    entry_pipeline_aware_signal: "bool | None" = None,
    entry_forward_expectation_signal: "bool | None" = None,
    entry_dispersion_expectation_signal: "bool | None" = None,
    entry_margin_exhaustion: "bool | None" = None,
    entry_forward_reserve_leg: "bool | None" = None,
    storage_entry_availability_gate: "bool | None" = None,
    storage_entry_cost_normalized_rank: "bool | None" = None,
    smr_available_year: "int | None" = None,
    ptc_window: "int | str | None" = None,
    verified_announced_exits: bool = True,
    fossil_announced_exits: "bool | None" = None,
) -> ScenarioConfig:
    """Assemble the hindcast ScenarioConfig (forecast machinery, vintage init).

    The hindcast must exercise the capacity screens under the **same price
    formation the forecast uses** for the ISO -- otherwise it validates a
    dispatch/margin signal the production path never sees. The ``s2`` run
    (`docs/hindcast-reports/ercot-2021-2025-realized-s2-2026-07-05.md` root
    cause 1) left ``scarcity_pricing_enabled`` at its ``False`` model default,
    so the ERCOT screens priced against bare perfect-foresight LP duals
    (mean ~$25/MWh, no ORDC overlay, no reserve-price signal) -- the exact
    revenue understatement the Stage-2 revenue-side fix targets was switched
    off in the harness, producing a 9.7 GW over-retirement (94 % false). We
    adopt each ISO's production scarcity footing here as the harness default:
    setting the master switch ``scarcity_pricing_enabled=True`` engages every
    ISO's ``ISOConfig.default_scenario_overrides`` scarcity footing in
    ``run_scenario_iso`` -- for ERCOT the published ORDC overlay
    (``scarcity_price_overlay=True``, the forecast's default cell), for PJM
    the capacity-market footing (no ORDC overlay; RPM net-CONE × UCAP already
    enters the screens via ``capacity_revenue_per_mw_yr``, so the master flag
    is a harmless no-op there). This is a **harness-config** choice, not a
    model-default change -- the ScenarioConfig default stays ``False`` (rule 1:
    fix the price signal the screens see, do not tune the screens).

    ``energy_only_floor`` is the stage-5 s4 PROBE leg (fom-scarcity stage 5
    §4-§5), NOT a harness default: it sets
    ``market_design_retirement_floor=True`` so energy-only ERCOT runs without
    the retirement reliability floor (the s3 ledgers show the floor retaining
    10.7-26.0 GW/yr -- with it off, exits can tighten a later year's LP and
    scarcity can form in the hindcast for the first time, mechanically
    unblocking the G-30 solar-entry question). Probe-only because the s3
    root cause stands: the screens see year-N-1 perfect-foresight prices on
    an over-supplied vintage fleet, so the floor-off leg is expected to
    over-retire further before any scarcity forms; adopting it as the
    harness footing awaits the G-31 grain fix.
    """
    # T1-FF full-forward wiring (FH-1, plan §2.1): the boundary is the start
    # year itself (one seam, re-pointed — rule 19), the gas path is the arm's
    # (realized Henry Hub / as-known AEO vintage, resolved with a hard error
    # for a missing as-known intake), and the weather posture is the arm's
    # (Arm R: per-solve-year weather via crossover_solve_year_weather; Arm K:
    # the base year's weather for every solve year). hindcast_fuel_variant
    # records the arm so the meta/variant vocabulary stays one namespace.
    if forward_from_base:
        _ff_gas = full_forward_gas_path(arm, start_year)
        variant = arm
        gas_path = _ff_gas
        fwd_gas_path = _ff_gas
        weather_year = start_year
        solve_year_weather = arm == "realized"
        # Arm K grows demand on the rates PUBLISHED as of its base year
        # (FH-2 handoff §7: "--arm asknown should set demand_growth_vintage =
        # base_year alongside its gas path"; values FH-3, plan §4 row 6).
        # Selected exactly like the gas path — by the arm, not a new flag —
        # and fail-closed: a base year with no intaken vintage table raises at
        # config build (rule 13, the §4-row-7 refusal one channel over).
        # Arm R stays on the default table: its growth spans are zero-year by
        # construction (per-solve-year weather), so the table never binds, and
        # None keeps its cache key exactly the FH-1 gate-probe surface.
        demand_growth_vintage = start_year if arm == "asknown" else None
    else:
        gas_path = FUEL_VARIANT_GAS_PATH[variant]
        fwd_gas_path = crossover_forward_gas_path
        demand_growth_vintage = None
        # T1-X: pin the weather year to the last realized year (boundary − 1 =
        # 2025) so "growth-scaled demand from the last realized year" (plan
        # §2.2) is exactly what the forward years see. A plain hindcast keeps
        # the model default weather_year (2024), unchanged.
        weather_year = (
            CROSSOVER_FORWARD_YEAR - 1 if crossover else ScenarioConfig().weather_year
        )
        solve_year_weather = False
    # ONE resolution of the forward boundary, shared with the window guard
    # (FFR-3U): whatever the guard policy-checked is exactly what the config
    # carries into the runner's bridge predicate.
    boundary = window_forward_boundary(start_year, crossover, forward_from_base)
    _clearing_by_iso, _ = resolve_capacity_clearing_posture(
        iso, capacity_market_clearing, fixed_net_cone
    )
    return ScenarioConfig(
        iso=iso,
        mode="forecast",
        hindcast=True,
        # Owner decision D-10 (2026-08-04, sitting Addendum K.3): the T1-H /
        # T1-X / T1-FF legs are forecast bundles, so they run cross-year warm
        # start OFF and stay reproducible from their own cache after a resume.
        # Explicit (non-default) by design — see FFR-3T and
        # scenarios.FORECAST_BUNDLE_XYEAR_WARMSTART for why a default flip
        # would collide these keys with their warm predecessors instead.
        forecast_xyear_warmstart=shipped_forecast_xyear_warmstart(),
        start_year=start_year,
        end_year=end_year,
        eia860_vintage_year=vintage,
        hindcast_fuel_variant=variant,
        # Announced-exit verification (owner directive 2026-08-22): announced/
        # "known" retirement dates are countered by the realized record — a
        # plant whose exit was reversed outright by a later public counter-
        # instrument and kept operating (Byron/Dresden under IL CEJA's CMC) is
        # NOT retired, whatever the vintage EIA-860 says. HARNESS default ON
        # (--no-verified-announced-exits restores the RC-1B ex-ante arm, the
        # posture every committed pre-2026-08-22 leg ran, so their verdicts
        # stand as scored); the ScenarioConfig default stays False (rule 24 —
        # no model default moves here). An armed leg hashes distinctly; the
        # off arm is byte-identical to the pre-flag harness.
        hindcast_verified_announced_exits=verified_announced_exits,
        gas_price_path=gas_path,
        # T1-X crossover (FF-0E, plan §2.2): set the forward boundary so years
        # >= CROSSOVER_FORWARD_YEAR (2026) run on pure forward drivers (the
        # runner un-bridges them, skips the realized demand loader + the F923
        # overlay, and prices gas on the AEO path below). None for a plain
        # hindcast (byte-identical). A full-forward run (FH-1) points the
        # boundary at start_year so EVERY solve year is a forward year.
        crossover_forward_year=boundary,
        crossover_forward_gas_path=fwd_gas_path,
        weather_year=weather_year,
        crossover_solve_year_weather=solve_year_weather,
        # As-of demand growth (Arm K only; None everywhere else, which is the
        # registered cache-neutral default — no existing posture's key moves).
        demand_growth_vintage=demand_growth_vintage,
        # Production scarcity footing (see docstring): ERCOT → ORDC overlay,
        # PJM → capacity-market (no-op). Harness default, not a model default.
        scarcity_pricing_enabled=True,
        market_design_retirement_floor=energy_only_floor,
        # G-31 first-wave corrective arm (PROBE, default-off):
        #   limited_foresight_dispatch -- deny the in-year LP perfect annual
        #     storage/hydro foresight so peak/net-load-ramp hours tighten and the
        #     ORDC overlay prices scarcity in-year once the fleet has thinned.
        # Zero fitted parameters; see the scenarios.py field docstring.
        # (staged_oversupply_thinning was DELETED at the FF-1A R-NEW commit,
        # rule 26 -- the execution-lag pipeline carries the deactivation queue.)
        limited_foresight_dispatch=limited_foresight_dispatch,
        # CR-3.1 frozen-penetration byte-compat arm: pin the VRE adequacy
        # credits back to the pre-curve flat constants for the BEFORE leg of
        # the before/after diagnostic. Default (False) keeps the model
        # default renewable_elcc_curves=True -- the AFTER leg.
        renewable_elcc_curves=not legacy_renewable_credit,
        # Capacity-price posture (FFR-2E, audit FR-14). The harness DEFAULT is
        # now the SHIPPED production posture -- the per-ISO clearing dict
        # ScenarioConfig actually carries -- so FC-3 evidence is scored on the
        # price formation the forecast runs (sloped VRR wherever the ISO ships
        # curve-ON), not on a flat net-CONE the production path never sees.
        # --fixed-net-cone restores the old flat arm (the posture every
        # committed pre-2026-08-02 leg ran, so their verdicts stand as scored);
        # --capacity-market-clearing keeps the RC-1B force-ON probe for an ISO
        # production leaves off. The scalar capacity_market_clearing stays off
        # in every posture, so an arm can never leak to another ISO.
        # See resolve_capacity_clearing_posture.
        capacity_market_clearing_by_iso=_clearing_by_iso,
        # RC-0C decision-neutral per-candidate entry-screen decomposition
        # (byte-identical fleet outcome; lands in evolution_<year>.json).
        entry_screen_diagnostics=entry_screen_diagnostics,
        # D-1 retirement rule + FF-2A entry-stack dampers (audit FR-4 / FR-5,
        # owner decisions D-1 / D-2 / D-2'). ``None`` means INHERIT THE SHIPPED
        # ScenarioConfig DEFAULT — the field is simply not passed.
        #
        # History: FFR-1D deleted the three entry CLI flags on 2026-07-31
        # (rule 26) because FF-3D had dropped their passthrough while keeping
        # the flags, so a leg launched with --entry-rate-limits recorded
        # `entry_rate_limits: true` in its meta on a solve that never armed it —
        # an inert flag that falsifies the run record. FFR-2B re-wired the
        # passthrough for real, mirroring the then-shipped defaults as literals
        # and noting "the flip is the owner's, executed at FFR-3A step 0".
        #
        # This IS that step. The owner signed D-1 (retirement_rule ->
        # "pipeline") and D-2 (both dampers -> True) on 2026-08-02; a mirrored
        # literal here would have silently overridden both flips and made the
        # signed decisions inert in exactly the T1-H / T1-X legs launched
        # through this harness — the same class of defect as the flag that
        # lied, one layer up. Reading the live default instead of mirroring it
        # is the FFR-2E instrument pattern already used for the capacity
        # posture above, and keeps ScenarioConfig the single source of truth
        # for a default (rule 24).
        #
        # ``correlated_forced_outage`` and ``entry_lookahead_reprice`` JOINED
        # this dict at FFR-3D, executing owner decision C.4(c) (signed
        # 2026-08-03, ffr-owner-sitting-2026-08-02.md Addendum D.1): "UN-PIN --
        # MATCH PRODUCTION". Both are ScenarioConfig defaults ``True`` (the
        # FF-1F / FF-2A flips), and both were passed here as harness-local
        # ``False`` literals -- so every hindcast leg validated a posture the
        # forecast does not ship, the audit FR-14 defect FFR-2E fixed for the
        # capacity posture and FFR-2E §6.2 flagged for these two. They are now
        # ``None``-sentinel like the four above: OMIT = inherit the shipped
        # default; ``--no-*`` forces the control arm explicitly.
        #
        # COST, acknowledged at signature (Addendum D.3): every T1-H verdict
        # COMMITTED before this commit was scored with both forced OFF, so
        # those verdicts are LEGACY EVIDENCE on a superseded posture. They are
        # not reinterpreted and not deleted; an FC-3 citation resting on them
        # says so. See docs/handoffs/ffr-3d-instrument-repair-2026-08-03.md §2.
        **{
            k: v
            for k, v in {
                "retirement_rule": retirement_rule,
                "entry_vre_capacity_revenue": entry_vre_capacity_revenue,
                # capx D40: NEISO published Net ICR requirement (+ curve
                # convention) gate — default-off; None inherits the shipped
                # default, True arms the D37 T1-H measurement posture.
                "neiso_net_icr_requirement": neiso_net_icr_requirement,
                # capx D48: PJM accreditation-design devintage + DR-as-supply
                # gates — default-off; None inherits the shipped default, True
                # arms the D48 A/B measurement posture (distinct cache key).
                "pjm_accreditation_design_vintage": pjm_accreditation_design_vintage,
                "pjm_demand_response_supply": pjm_demand_response_supply,
                # capx D57: the capacity-market supply-clearing gate (the PJM
                # clearing half, DESIGN-capx-d54 §7.1) — a {iso: bool} row
                # for THIS ISO only; default None; None (omit) or an explicit
                # --no-... inherits the shipped None default (both are the
                # unarmed posture, one key), True arms the D57 A/B measurement
                # posture (distinct cache key). Requires the curve gate ON.
                "capacity_market_supply_clearing_by_iso": (
                    {iso: True} if capacity_market_supply_clearing else None
                ),
                # capx D52: NYISO adequacy-requirement devintage gates —
                # default-off; None inherits the shipped default, True arms
                # the D52 A/B measurement posture (distinct cache key).
                "nyiso_requirement_forecast_peak": nyiso_requirement_forecast_peak,
                "nyiso_requirement_vintage_factors": nyiso_requirement_vintage_factors,
                # capx D59: the NYISO locality capacity-curve gate — default-off;
                # None inherits the shipped default, True arms the D59 A/B
                # measurement posture (distinct cache key).
                "locality_capacity_curves": locality_capacity_curves,
                # capx D51: the MISO dated-net accounting-ratio gate —
                # default-off; None inherits the shipped default, True arms the
                # D51 A/B measurement posture (distinct cache key).
                "adequacy_accounting_ratio_dated_net": adequacy_accounting_ratio_dated_net,
                # capx D53: the retirement-screen sector gate — default-off;
                # None inherits the shipped default, True arms the D53 A/B
                # measurement posture (distinct cache key).
                "retirement_sector_gate": retirement_sector_gate,
                "entry_rate_limits": entry_rate_limits,
                "entry_commissioning_lag": entry_commissioning_lag,
                "exit_rate_limits": exit_rate_limits,
                # G-30 entering-year stack re-price: the capacity screens see
                # the entering year's net load re-priced against the current
                # (post-retirement) fleet with the published ORDC curve, so a
                # genuinely-short thinned fleet is screened on scarcity the
                # over-supplied in-year dispatch never forms. Screens-only,
                # never dispatch; zero fitted parameters (rule 13). In a
                # FULL-FORWARD leg the runner's own seam falls to the growth-
                # scaled fallback rather than reading measured next-year demand
                # (runner.py, is_crossover_forward_year branch), so inheriting
                # the shipped ``True`` introduces no measured read (rule 22).
                "entry_lookahead_reprice": entry_lookahead_reprice,
                # FFR-5D (owner decision D-19(a)): unify EVERY capacity screen
                # on the lookahead price object for its entering year —
                # bridged/bridge-adjacent years included, priced on the
                # growth-scaled fallback so the rule-22 no-read contract is
                # unchanged — and repair the object's three FFR-5A §2a level
                # gaps (storage enters the stack, entering-year VRE capacity,
                # hourly availability). Screens-only, zero new tunables.
                "capacity_screen_unified_lookahead": (
                    capacity_screen_unified_lookahead
                ),
                # FFR-8A scarcity restoration (owner decision D-21(a)/AC.1):
                # the lookahead tail prices the published ORDC on the forward
                # COMMITTED-capability reserve quantity, with the pre-RTC
                # AS-plan withholding in the energy-stack search and the
                # fleet's own forced-outage uncertainty integrated (LOLP-
                # bearing). Requires the unified lookahead; ERCOT-only.
                "capacity_screen_scarcity_restoration": (
                    capacity_screen_scarcity_restoration
                ),
                # FF-1B correlated cold-event forced-outage derate
                # (data/outages.apply_correlated_outage_derate): a leg's deep-
                # cold days (Uri 2021, Heather 2024) physically thin the fleet
                # so in-year ORDC can form scarcity (the G-31 question).
                # Measured frozen curves (constants.CORRELATED_OUTAGE_CURVE).
                "correlated_forced_outage": correlated_forced_outage,
                # FFR-5E near-term VRE procurement limb (owner decision
                # D-18(a)), measured on its HINDCAST arm here — the arm
                # FFR-3V-FIX §6 unblocked by re-seeding the hindcast renewable
                # pools from the run's own EIA-860 vintage, so an injected row
                # with online_year > base_year names capacity demonstrably
                # absent from the base pool instead of double-counting against
                # a present-day constant. Rides the None-drop dict so OMIT
                # inherits the shipped GATED-OFF default and the control arm's
                # cache key is the untouched shipped one.
                "vre_procurement_additions_enabled": vre_procurement_additions,
                # FFR-5C anti-cobweb guard relocation (owner decision D-17(a)),
                # armed per-invocation by the FFR-9C staged repair lane: the
                # pending-pipeline stock leaves BOTH annual flow caps and the
                # pro-forma prices its own committed pipeline instead. GATED
                # default-off in ScenarioConfig; OMIT inherits that shipped
                # default so the control arm's cache key is untouched.
                "entry_pipeline_aware_signal": entry_pipeline_aware_signal,
                # capx D42 fossil announced-date step-1 channel, ARMED AS THE
                # DEFAULT by owner ruling Q30 (2026-09-03, capx D44). Moved
                # onto the None-drop dict by D44: the harness previously pinned
                # this field to its own ``False`` parameter default on every
                # invocation, which would have made the flip INERT for the
                # entire hindcast lane. OMIT now inherits the shipped
                # ScenarioConfig default (GATED ON);
                # --no-fossil-announced-exits passes an explicit False, which
                # is the pre-Q30 control posture AND — because the cache key
                # drops the field at its frozen ``False`` declaration (capx
                # D24-R (b'-1)) — keeps that arm on its pre-flip key.
                "fossil_announced_exits_enabled": fossil_announced_exits,
                # ENTRY-SIGNAL forward-expectation construction (the disarm
                # finding §6 rung, GATED default-off in ScenarioConfig): the
                # capacity screens' price object becomes the run's own
                # prior-year hourly zonal LP duals re-leveled against the
                # entering year's stack, replacing the zone-flat MC step.
                # OMIT inherits the shipped default so the control arm's
                # cache key is untouched.
                "entry_forward_expectation_signal": (entry_forward_expectation_signal),
                # capx D43 dispersion-carrying entry expectation (GATED
                # default-off in ScenarioConfig): the capacity screens' price
                # object becomes each zone's own realized price-duration
                # curve indexed by the entering year's headroom rank on the
                # current year's, replacing the zone-flat MC step. OMIT
                # inherits the shipped default so the control arm's cache
                # key is untouched.
                "entry_dispersion_expectation_signal": (
                    entry_dispersion_expectation_signal
                ),
                # D11-R margin-exhaustion entry volume rule (GATED
                # default-off in ScenarioConfig): both entry allocators build
                # in repriced tranches until the screen's own margin is
                # exhausted, bounded by the same caps, instead of the
                # bang-bang full-cap allocation. OMIT inherits the shipped
                # default so the control arm's cache key is untouched.
                "entry_margin_exhaustion": entry_margin_exhaustion,
                # D12 scarcity-consistent entry reserve leg (GATED
                # default-off in ScenarioConfig): the entry screens' hourly
                # reserve legs become the entering year's own expected-ORDC
                # adder — one scarcity object per margin — instead of the
                # prior year's realized post-solve adder. OMIT inherits the
                # shipped default so the control arm's cache key is
                # untouched.
                "entry_forward_reserve_leg": entry_forward_reserve_leg,
                # T1-H capacity-entry Phase-1 Leg A storage pair (GATED
                # default-off in ScenarioConfig): the D-2 availability-year
                # gate restricts the storage entry candidate pool to
                # technologies at/after their measured first-US-operating
                # year (STORAGE_TECH_AVAILABLE_YEAR, fail-closed), and the
                # D-3 rank repair selects clearing technologies on margin
                # per unit capital cost instead of absolute $/MW-yr — both
                # on BOTH storage allocation rules. OMIT inherits the
                # shipped defaults so the control arm's cache key is
                # untouched.
                "storage_entry_availability_gate": storage_entry_availability_gate,
                "storage_entry_cost_normalized_rank": (
                    storage_entry_cost_normalized_rank
                ),
                # FFR-9C R-b SMR availability-year gate: when set, nuclear_smr
                # joins the entry candidate pool only from this year (ATB
                # costs new nuclear from 2030 only). OMIT inherits the shipped
                # ungated default (None) — measurement arms pass 2030.
                "smr_available_year": smr_available_year,
            }.items()
            if v is not None
        },
        # FFR-4C §45 wind-PTC statutory window (owner decision D-13). This
        # field cannot ride the None-drop dict above because ``None`` is a
        # MEANINGFUL value here (the unwindowed full-book-life control arm,
        # distinct cache key) — so the inherit sentinel is the OMITTED CLI
        # flag instead: omit → the shipped ScenarioConfig default (10,
        # statutory); ``--ptc-window none`` → an explicit None; an integer →
        # a sensitivity window.
        **(
            {}
            if ptc_window is None
            else {
                "ira_ptc_credit_window_years": (
                    None if str(ptc_window).lower() == "none" else int(ptc_window)
                )
            }
        ),
    )


def assert_pipeline_from_vintage(
    iso: str, out_dir: Path, ledgers: dict, vintage: int = DEFAULT_VINTAGE_YEAR
) -> list[str]:
    """Leakage guard (plan §1.2.4): planned units trace to the run's vintage.

    Every ``source == "planned"`` addition in the ledgers must correspond to a
    unit in the ``vintage``-vintage proposed sheet -- a forecast started at the
    vintage cutoff cannot know a pipeline unit that first appeared in a later
    vintage. Generalized over ``vintage`` for the T1-X crossover (FF-0E), whose
    2023-vintage leakage test asserts no unit absent from the 2023 proposed
    sheet enters. Returns the list of violations (empty when clean).
    """
    import pandas as pd

    proposed_path = (
        Path("data/raw/eia-860")
        / f"vintage_{vintage}"
        / "eia860_generator_proposed.parquet"
    )
    if not proposed_path.exists():
        return [f"{vintage}-vintage proposed sheet missing: {proposed_path}"]
    proposed = pd.read_parquet(proposed_path)
    proposed_plants = {
        str(int(p))
        for p in pd.to_numeric(proposed["Plant Code"], errors="coerce").dropna()
    }
    violations: list[str] = []
    for year, led in ledgers.items():
        for add in led.get("thermal_additions", []):
            if add.get("source") != "planned":
                continue
            eia_id = str(add.get("eia860_id") or "")
            # unit_id form is ``planned_<plant>_<gen>``; extract the plant code.
            plant = eia_id.split("_")[1] if eia_id.startswith("planned_") else eia_id
            if plant and plant not in proposed_plants:
                violations.append(
                    f"{year}: planned {eia_id} absent from {vintage} vintage"
                )
    return violations


def assert_neighbor_seam_drivers(
    config: ScenarioConfig, forward_years: list[int]
) -> list[str]:
    """Assert the NEIGHBOR-PRICE seam prices forward years on forward gas.

    The import/export seam is a second gas consumer beside the ISO's own fuel
    (``runner.py`` → ``model.interchange.apply_interchange_injections`` →
    ``data.neighbor_price``), and audit FR-9 found it blind to the crossover
    boundary: it took ``config.gas_price_path`` unconditionally, so a forward
    year priced its imports off the realized hindcast path. Both callers now
    resolve through :func:`~market_sim.data.fuel.resolve_gas_scenario_path`;
    this asserts the end-to-end consequence — for every armed seam neighbor,
    the delivered gas the seam will actually charge in year ``y`` equals the
    declared forward trajectory, and (when the two paths differ) is NOT the
    realized path's value.

    Only ARMED seams are asserted: the generic reference-price interface
    (``reference_price_interface``, non-CAISO) and CAISO's two dedicated
    ladders (``caiso_reference_price_seam`` / ``caiso_intertie_reference_price``).
    A run with no armed seam never reaches the priced code path, so there is
    nothing to assert — that is precisely the state the FFR-2A diagnosis found
    the FF-2D MISO crossover in.

    Args:
        config: The resolved crossover/full-forward config.
        forward_years: Solve years at/above the boundary.

    Returns:
        Violation strings (empty when clean).
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.fuel import _hold_flat_extrapolate, resolve_gas_scenario_path
    from market_sim.data.neighbor_price import neighbor_gas_price
    from market_sim.model.interchange.spec import CAISO_PER_HUB_NEIGHBORS

    from market_sim.config.constants import HENRY_HUB_TRAJECTORIES

    iso = config.iso
    specs: list[tuple[str, object]] = []
    if getattr(config, "reference_price_interface", False) and iso != "CAISO":
        specs += [(n.name, n) for n in INTERFACE_NEIGHBORS.get(iso, [])]
    if iso == "CAISO" and (
        getattr(config, "caiso_reference_price_seam", False)
        or getattr(config, "caiso_intertie_reference_price", False)
    ):
        specs += list(CAISO_PER_HUB_NEIGHBORS.items())
    if not specs:
        return []

    violations: list[str] = []
    for y in forward_years:
        path = resolve_gas_scenario_path(config, y)
        if path != config.crossover_forward_gas_path:
            violations.append(
                f"{y}: neighbor seam would price gas on {path!r}, not the "
                f"declared forward path {config.crossover_forward_gas_path!r}"
            )
            continue
        fwd = _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES[path], y)
        realized = _hold_flat_extrapolate(
            HENRY_HUB_TRAJECTORIES[config.gas_price_path], y
        )
        for name, spec in specs:
            try:
                got = neighbor_gas_price(spec, y, path)
            except (KeyError, TypeError) as e:
                violations.append(
                    f"{y}: neighbor seam {name} failed to price gas on "
                    f"{path!r} ({type(e).__name__}: {e})"
                )
                continue
            basis = float(getattr(spec, "gas_basis", 0.0))
            if abs(got - (fwd + basis)) > 1e-9:
                violations.append(
                    f"{y}: neighbor seam {name} gas {got:.3f} != forward path "
                    f"{path} {fwd + basis:.3f}"
                )
            if config.gas_price_path != path and abs(got - (realized + basis)) <= 1e-9:
                violations.append(
                    f"{y}: neighbor seam {name} still on realized path "
                    f"{config.gas_price_path} (backcast-gated fuel leaked)"
                )
    return violations


def assert_no_measured_overlays(config: ScenarioConfig) -> list[str]:
    """Assert no measured (backcast-only) overlay is armed on a forward run.

    Belt-and-braces with the two landed guards this deliberately duplicates —
    ``ScenarioConfig.__post_init__``'s ``_BACKCAST_ONLY_OVERLAY_FIELDS`` refusal
    (FFR-1D) and FFR-1B's ``mode == "backcast"`` gate on the ``weather_year``-
    keyed measured single-event derate table. Both live far from the harness;
    this states the harness's own contract at run time, so a future loosening
    of either surfaces here as a leakage-guard violation on the very runs whose
    validity depends on it, rather than as a silently plausible number.

    Three checks:

    (a) no ``_BACKCAST_ONLY_OVERLAY_FIELDS`` member is armed (each is a
        specific year's published record with no forward edition — rule 13
        ``[R-MEASURED]``);
    (b) ``outage_source`` is not the measured ``"historic"`` record;
    (c) the ``weather_year`` pin sits strictly BELOW the forward boundary on a
        T1-X crossover. Every ``weather_year``-keyed lookup (the measured
        derate table, the temperature/ambient derate 8760s) then refers to a
        realized year the run is entitled to, and the forward years take the
        pinned weather shape by declared construction rather than by reaching
        for a measured record of their own. A T1-FF full-forward run is exempt
        by construction: its boundary IS its base year, so weather_year ==
        crossover_forward_year is that harness's contract (FH-1, plan §2.1).

    Args:
        config: The resolved crossover/full-forward config.

    Returns:
        Violation strings (empty when clean).
    """
    from market_sim.config.scenarios import (
        _BACKCAST_ONLY_OUTAGE_SOURCE,
        _BACKCAST_ONLY_OVERLAY_FIELDS,
    )

    violations = [
        f"measured overlay {name} armed on a forward run ({why})"
        for name, why in _BACKCAST_ONLY_OVERLAY_FIELDS.items()
        if getattr(config, name, None) not in (None, False)
    ]
    if config.outage_source == _BACKCAST_ONLY_OUTAGE_SOURCE:
        violations.append(
            f'outage_source="{_BACKCAST_ONLY_OUTAGE_SOURCE}" (the ISO\'s '
            "measured outage record) armed on a forward run"
        )
    if (
        not config.is_full_forward_hindcast
        and config.crossover_forward_year is not None
    ):
        if int(config.weather_year) >= int(config.crossover_forward_year):
            violations.append(
                f"weather_year {config.weather_year} is at/above the forward "
                f"boundary {config.crossover_forward_year}: the weather pin "
                "must sit in the realized window (plan §2.2)"
            )
    return violations


def assert_forward_drivers(
    config: ScenarioConfig, start_year: int, end_year: int
) -> list[str]:
    """Assert every FORWARD solve year runs on forward drivers only.

    (FF-0E §2.2, generalized by FH-1 to any boundary — a T1-FF run's boundary
    is its start year, so this covers EVERY solve year, not just 2026+.)

    A forward year (>= the boundary) must NOT consult any backcast-gated
    realized-input loader. This asserts the observable consequences from the
    resolved config, per non-bridge solve year at/above the boundary:

    (a) the year is flagged as a crossover-forward year. This single
        predicate IS the run-time gate of BOTH measured-input loaders — the
        realized per-year demand branch (``runner.run_scenario_iso``:
        ``config.hindcast and not is_crossover_forward_year(y)``) and the
        F923 plant-monthly overlay (``fuel.plant_prices``: returns before any
        read when ``is_crossover_forward_year(year)``) — so a year failing it
        here is exactly a year those loaders would fire for;
    (b) its resolved annual gas equals the declared forward trajectory
        (``crossover_forward_gas_path``) — and, in a full-forward run, that
        resolution itself hard-errors on the §4-row-7 back-hold trap (a year
        below the trajectory's earliest knot), surfaced here as a violation
        rather than an unhandled exception;
    (c) when the forward path differs from ``gas_price_path``, the resolved
        value is NOT the realized path's (backcast-gated fuel leak);
    (d) the NEIGHBOR-PRICE seam — the ISO's own fuel was never the only gas
        consumer — prices those same years on the same forward trajectory
        (:func:`assert_neighbor_seam_drivers`; audit FR-9, FFR-2A);
    (e) no measured backcast-only overlay is armed, including the
        ``weather_year``-keyed ones (:func:`assert_no_measured_overlays`).

    Returns violations (empty when clean); no-op for a plain hindcast. Called
    BEFORE the solve (fail fast — a leaked window must not burn a multi-hour
    run) and recorded in the meta afterwards.
    """
    if config.crossover_forward_year is None:
        return []
    from market_sim.config.constants import (
        GAS_BASIS_DIFFERENTIAL,
        HENRY_HUB_TRAJECTORIES,
    )
    from market_sim.data.fuel import _hold_flat_extrapolate, resolve_annual_gas_price

    basis = GAS_BASIS_DIFFERENTIAL.get(config.iso, 0.0)
    violations: list[str] = []
    # The solved forward years, collected as the loop clears each one's bridge
    # check, so the seam assertion (d) covers exactly the same set.
    forward_years: list[int] = []
    for y in range(max(start_year, config.crossover_forward_year), end_year + 1):
        # A genuine crossover forward year (>= 2026) is un-bridged (solved); a
        # full-forward run inside 2021-2025 keeps the 2022 bridge, which is
        # never solved — nothing to assert for it. This local expression had
        # the RIGHT scoping while the runner's did not (FFR-3Q's three-way
        # split); since FFR-3U all three read one predicate.
        if y in HINDCAST_BRIDGE_YEARS and not config.is_crossover_unbridged_year(y):
            continue
        forward_years.append(y)
        if not config.is_crossover_forward_year(y):
            violations.append(
                f"{y}: not flagged as a crossover-forward year (the measured "
                "demand loader and the F923 overlay would both fire for it)"
            )
            continue
        try:
            resolved = resolve_annual_gas_price(config, y)
        except ValueError as e:
            violations.append(f"{y}: {e}")
            continue
        fwd = (
            _hold_flat_extrapolate(
                HENRY_HUB_TRAJECTORIES[config.crossover_forward_gas_path], y
            )
            + basis
        )
        realized = (
            _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES[config.gas_price_path], y)
            + basis
        )
        if abs(resolved - fwd) > 1e-9:
            violations.append(
                f"{y}: forward gas {resolved:.3f} != forward path "
                f"{config.crossover_forward_gas_path} {fwd:.3f}"
            )
        if config.gas_price_path != config.crossover_forward_gas_path and (
            abs(resolved - realized) <= 1e-9
        ):
            violations.append(
                f"{y}: forward gas still on realized path "
                f"{config.gas_price_path} (backcast-gated fuel leaked)"
            )
    violations += assert_neighbor_seam_drivers(config, forward_years)
    violations += assert_no_measured_overlays(config)
    return violations


def main(argv: list[str] | None = None) -> int:
    # Emit the runner's INFO logs (per-year ORDC scarcity adder, lookahead
    # pro-forma, retirement/entry waves) so a hindcast probe is reproducible
    # from its captured log -- runner.main configures this, but the harness
    # calls run_scenario_iso directly and would otherwise stay silent.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default="ERCOT", help="ISO to hindcast.")
    # Defaults resolve by mode below: plain hindcast 2021-2025, crossover
    # 2023-2027 (None => mode default; an explicit value overrides).
    parser.add_argument("--start-year", type=int, default=None)
    parser.add_argument("--end-year", type=int, default=None)
    parser.add_argument(
        "--fuel-variant", choices=["realized", "asknown"], default="realized"
    )
    parser.add_argument(
        "--vintage",
        type=int,
        choices=list(ALLOWED_VINTAGES),
        default=None,
        help=(
            "EIA-860 vintage to seed the fleet + pipeline from. Default 2020 for "
            "a plain hindcast (plan §1.1); a --crossover run requires --vintage "
            f"2023 (plan §2.2). Choices: {ALLOWED_VINTAGES}."
        ),
    )
    parser.add_argument(
        "--crossover",
        action="store_true",
        help=(
            "T1-X crossover mode (FF-0E, plan §2.2): 2023-vintage init, realized "
            "inputs 2023-2025, PURE FORWARD DRIVERS 2026+ (growth-scaled demand, "
            "AEO gas path, statistical outages, no measured overlays; 2026/2027 "
            "SOLVED as forecast-mode years — rule-22-legal). Score with "
            "scripts/score_crossover.py. Requires --vintage 2023; window default "
            "2023-2027."
        ),
    )
    parser.add_argument(
        "--crossover-forward-gas-path",
        choices=["low", "mid", "high"],
        default="mid",
        help=(
            "AEO Henry Hub path a crossover uses for its FORWARD years (>=2026): "
            "the forecast fuel methodology (plan §2.2). 'mid' = AEO2025 "
            "Reference. Ignored outside --crossover (a --forward-from-base run "
            "derives its forward gas from --arm instead)."
        ),
    )
    parser.add_argument(
        "--forward-from-base",
        action="store_true",
        help=(
            "T1-FF full-forward hindcast (FH-1, hindcast-forward plan §2): set "
            "crossover_forward_year = start-year so EVERY solve year runs the "
            "forward input stack (no measured overlays), scored 2023-2025 "
            "only. Plain-hindcast window rules (2021 floor, end <= 2025, 2022 "
            "bridged, {2021} seed); --vintage must be at/before the base "
            "year. Wire the arm with --arm. Mutually exclusive with "
            "--crossover."
        ),
    )
    parser.add_argument(
        "--arm",
        choices=["realized", "asknown"],
        default="realized",
        help=(
            "T1-FF pre-registered arm (plan §2.1). 'realized' (Arm R): "
            "realized annual Henry Hub + per-solve-year weather (given-weather "
            "structural test). 'asknown' (Arm K): as-known AEO gas vintage "
            "as-of the base year (hindcast_asknown_aeo<base>; HARD ERROR if "
            "not intaken — FH-3) + base-year weather (pure ex-ante skill). "
            "Ignored outside --forward-from-base."
        ),
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--energy-only-floor",
        action="store_true",
        help=(
            "Stage-5 s4 PROBE leg: disable the retirement reliability floor "
            "for energy-only ISOs (market_design_retirement_floor=True). "
            "Probe-only, never the harness default -- see build_config."
        ),
    )
    parser.add_argument(
        "--entry-lookahead-reprice",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "G-30 entering-year stack re-price: the capacity screens see each "
            "entering year's net load re-priced against the current fleet with "
            "the published ORDC curve, tempering the perfect-foresight screen "
            "signal. OMIT to inherit the shipped default, ON since the FF-2A "
            "flip and UN-PINNED here by owner decision C.4(c) (2026-08-03); "
            "--no-entry-lookahead-reprice forces the un-repriced control."
        ),
    )
    parser.add_argument(
        "--retirement-rule",
        choices=["legacy", "pipeline"],
        default=None,
        help=(
            "Economic-retirement decision rule (audit FR-4 / owner D-1). OMIT "
            "to inherit the SHIPPED ScenarioConfig default, which owner "
            "decision D-1 flipped to 'pipeline' on 2026-08-02 (the R-NEW "
            "decision/execution split: uniform bar, joint adequacy-capped "
            "entry, soft latch, measured per-fuel execution lags) -- "
            "ff-retirement-rule-redesign-2026-07.md §3.6. Pass 'legacy' to "
            "force the retired per-fuel counters as a CONTROL arm."
        ),
    )
    parser.add_argument(
        "--legacy-renewable-credit",
        action="store_true",
        help=(
            "CR-3.1 BASELINE arm: renewable_elcc_curves=False, pinning the "
            "VRE adequacy credits to the pre-P-2C flat constants "
            "(frozen-penetration byte-compat mode) for the before/after "
            "hindcast diagnostic. Default runs the penetration-indexed "
            "published ELCC curves (the model default)."
        ),
    )
    parser.add_argument(
        "--limited-foresight-dispatch",
        action="store_true",
        help=(
            "G-31 corrective arm (PROBE): deny the in-year dispatch LP perfect "
            "annual storage/hydro foresight (within-day cycle bound) so peak/"
            "net-load-ramp hours tighten and the ORDC overlay prices scarcity "
            "in-year once the fleet has thinned. See build_config / scenarios.py."
        ),
    )
    parser.add_argument(
        "--capacity-market-clearing",
        action="store_true",
        help=(
            "RC-1B PROBE (force-ON): arm the CR-1 sloped capacity demand curve "
            "for THIS hindcast's own ISO only, via ScenarioConfig."
            "capacity_market_clearing_by_iso={iso: True} (the scalar stays "
            "off) EVEN IF production ships that ISO curve-OFF. Since FFR-2E "
            "the harness already defaults to the shipped posture, so this flag "
            "is only needed for an ISO production leaves off (ERCOT, NYISO). "
            "Mutually exclusive with --fixed-net-cone."
        ),
    )
    parser.add_argument(
        "--fixed-net-cone",
        action="store_true",
        help=(
            "FFR-2E comparison arm: price resource adequacy on the FLAT "
            "net-CONE stub (capacity_market_clearing_by_iso=None) instead of "
            "the shipped per-ISO posture. This was the harness default before "
            "FFR-2E, so it reproduces the posture every committed "
            "pre-2026-08-02 leg ran (audit FR-14). Mutually exclusive with "
            "--capacity-market-clearing."
        ),
    )
    parser.add_argument(
        "--correlated-forced-outage",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FF-1B correlated cold-event forced-outage availability derate, so "
            "deep-cold days physically thin the fleet and in-year ORDC scarcity "
            "can form (the G-31 question). Measured frozen curves "
            "(constants.CORRELATED_OUTAGE_CURVE). OMIT to inherit the shipped "
            "default, ON since the FF-1F flip and UN-PINNED here by owner "
            "decision C.4(c) (2026-08-03); --no-correlated-forced-outage "
            "forces the underated control."
        ),
    )
    parser.add_argument(
        "--entry-screen-diagnostics",
        action="store_true",
        help=(
            "RC-0C decision-neutral diagnostic: record the per-candidate "
            "entry-screen decomposition (energy/attribute/capacity revenue, "
            "cost terms, margin, binding cap) in each evolution ledger "
            "(entry_screen_diagnostics=True). Byte-identical fleet outcome."
        ),
    )
    parser.add_argument(
        "--ptc-window",
        default=None,
        help=(
            "FFR-4C §45 wind-PTC credit window, years from placed-in-service "
            "(owner decision D-13). OMIT to inherit the shipped ScenarioConfig "
            "default (10, statutory — 26 U.S.C. §45(a)(2)(A)(ii)). Pass "
            "'none' for the UNWINDOWED control arm (full-book-life crediting, "
            "the pre-4C posture, distinct cache key); an integer runs a "
            "sensitivity window."
        ),
    )
    parser.add_argument(
        "--neiso-net-icr-requirement",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D40 (2026-09-02) NEISO-only arm: resolve the adequacy "
            "requirement from ISO-NE's PUBLISHED per-CCP Net ICR series "
            "(constants.NET_ICR_REQUIREMENT_MW_BY_ISO, hold-last ratio beyond "
            "FCA 18) instead of the single-vintage composite, and evaluate "
            "the CR-1 position on the published curve's own x-convention. "
            "Inert on every other ISO. OMIT to inherit the shipped default "
            "(off, owner-armed only); --neiso-net-icr-requirement arms it "
            "(distinct cache key)."
        ),
    )
    parser.add_argument(
        "--pjm-accreditation-design-vintage",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D48 (2026-09-04) PJM-only arm: accredit the thermal fleet "
            "and resolve the pool requirement on the design each delivery "
            "year's auction actually cleared on — UCAP (1 - EFORd) + the "
            "published pre-CIFP FPR (constants.FORECAST_POOL_REQUIREMENT_"
            "PRE_REFORM_BY_ISO) before the 2025/2026 CIFP reform, the ELCC "
            "class ratings + post-CIFP FPR from it — instead of the 2025/26+ "
            "design for every year. Inert on every other ISO. OMIT to inherit "
            "the shipped default (off, owner-armed only); "
            "--pjm-accreditation-design-vintage arms it (distinct cache key)."
        ),
    )
    parser.add_argument(
        "--pjm-demand-response-supply",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D48 (2026-09-04) PJM-only arm: count the published BRA "
            "offered Demand Resource UCAP of each delivery year "
            "(constants.DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO) as adequacy "
            "SUPPLY on the accredited ledger and stop netting DR from the "
            "peak, so the CR-1 position sits on PJM's own VRR x-convention. "
            "Inert on every other ISO. OMIT to inherit the shipped default "
            "(off, owner-armed only); --pjm-demand-response-supply arms it "
            "(distinct cache key)."
        ),
    )
    parser.add_argument(
        "--capacity-market-supply-clearing",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D57 (2026-09-05) arm, building DESIGN-capx-d54 (the PJM "
            "clearing half): clear the fleet's net-ACR sell-offer stack "
            "(offer = max(0, going-forward cost - E&AS margin) on accredited "
            "MW; everything else a $0 price taker) against the delivery year's "
            "published VRR curve and settle the retirement screen's capacity "
            "leg from the result — cleared units earn the clearing price, "
            "uncleared units $0 — instead of evaluating the curve at the "
            "installed-fleet census; entry and storage read the clearing "
            "price as price takers. Sets capacity_market_supply_clearing_"
            "by_iso[<iso>]=True; requires the CR-1 curve gate ON for the ISO "
            "(shipped ON for PJM). OMIT or --no-... inherits the shipped "
            "default (off, owner-armed only); --capacity-market-supply-"
            "clearing arms it (distinct cache key). Generic in form, PJM-scoped "
            "by data (rule 25)."
        ),
    )
    parser.add_argument(
        "--nyiso-requirement-forecast-peak",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D52 (2026-09-04) NYISO-only arm: price the NYCA adequacy "
            "requirement on the PUBLISHED NYSRC ICAP-market forecast peak of "
            "the capability year (constants.NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO, "
            "Table D.2) instead of the model's own peak, in-table years only. "
            "Inert on every other ISO. OMIT to inherit the shipped default "
            "(off, owner-armed only); --nyiso-requirement-forecast-peak arms "
            "it (distinct cache key)."
        ),
    )
    parser.add_argument(
        "--nyiso-requirement-vintage-factors",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D52 (2026-09-04) NYISO-only arm: price the NYCA adequacy "
            "requirement at the capability year's ADOPTED IRM x (1 - derate) "
            "(constants.NYCA_IRM_ADOPTED_BY_ISO + NYCA_ICAP_UCAP_TRANSLATION_"
            "BY_ISO, hold-last beyond 2025/26) instead of the single-vintage "
            "1.244 x (1 - 0.1321) composite. Inert on every other ISO. OMIT to "
            "inherit the shipped default (off, owner-armed only); "
            "--nyiso-requirement-vintage-factors arms it (distinct cache key)."
        ),
    )
    parser.add_argument(
        "--locality-capacity-curves",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D59 (2026-09-05) NYISO-only arm: settle capacity revenue in "
            "NYC (Zone J) and Long Island (Zone K) at max(NYCA, the locality's "
            "own published ICAP demand curve at its own published LCR "
            "requirement) — ICAP Manual §5.15.2 — with thermal entry also "
            "screened sited in each locality at the published Gross-CONE cost "
            "ratio. Requires the NYCA curve gate ON (--capacity-market-clearing "
            "for NYISO); inert on every other ISO. OMIT to inherit the shipped "
            "default (off, owner-armed only); --locality-capacity-curves arms it "
            "(distinct cache key)."
        ),
    )
    parser.add_argument(
        "--adequacy-accounting-ratio-dated-net",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D51 (2026-09-04) MISO-only arm: resolve the internal-supply "
            "accounting ratio to its re-identification on the dates-ON fleet "
            "(constants.ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_"
            "ISO — D31's arithmetic with the denominators net of the fossil-"
            "dates channel's exits, D49 §2.6) everywhere the D31 ratio is "
            "applied (ledger / floor / backstop, one basis). Inert on every "
            "other ISO. OMIT to inherit the shipped default (off, owner-armed "
            "only); --adequacy-accounting-ratio-dated-net arms it (distinct "
            "cache key)."
        ),
    )
    parser.add_argument(
        "--retirement-sector-gate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D53 (2026-09-05) arm: the retirement-screen SECTOR GATE — "
            "every thermal unit whose plant's EIA-860 Sector (the run's active "
            "vintage) is 1, a regulated electric utility, is exogenous to the "
            "step-3 economic screen and exits only through step 0's instruments "
            "and step 1/1b's owner-filed dates; sectors 2-7 (IPP / commercial / "
            "industrial, CHP and non-CHP) face the screen as before, an unknown "
            "sector fails open to it (D32 C5/R3; design "
            "docs/handoffs/DESIGN-capx-d53-sector-gate-2026-09-05.md). ISO-"
            "agnostic by construction. OMIT to inherit the shipped default "
            "(off, owner-armed only); --retirement-sector-gate arms it "
            "(distinct cache key)."
        ),
    )
    parser.add_argument(
        "--entry-vre-capacity-revenue",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FF-2A item 1 PROBE arm (audit FR-5 / owner D-2): wind+solar entry "
            "candidates earn capacity_price_per_firm_mw_yr x the published "
            "ELCC credit at the model's own installed nameplate -- the SAME "
            "price seam thermal entry uses. Structural no-op in energy-only "
            "ISOs (capacity price 0). OMIT to inherit the shipped default -- owner "
            "decision D-2' is signed HOLD, so that is OFF."
        ),
    )
    parser.add_argument(
        "--entry-rate-limits",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FF-2A item 2 PROBE arm (audit FR-5 / BLK-10): cap per-tech annual "
            "economic entry AND the reserve-margin backstop at "
            "ENTRY_GROWTH_LIMIT_MULTIPLE (2.0) x the prior-max annual build, "
            "seeded from the measured EIA-860 record at the run's vintage "
            "(ReEDS relative-growth constraint). OMIT to inherit the shipped "
            "default, ARMED by owner decision D-2 (2026-08-02); "
            "--no-entry-rate-limits forces the undamped control."
        ),
    )
    parser.add_argument(
        "--exit-rate-limits",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FFR-3F exit-throughput PROBE arm (owner decision D-8, 2026-08-03): "
            "cap the MW of thermal capacity that may DEACTIVATE in one year at "
            "EXIT_THROUGHPUT_LIMIT_MULTIPLE (2.0) x the ISO's measured maximum "
            "single-year thermal deactivation, seeded from the EIA-860 retired "
            "sheet at the run's vintage. The EXIT half of the queue whose entry "
            "half --entry-rate-limits bounds; D-8 ruled queue latency "
            "(retirement_execution_lag_*) and queue throughput TWO mechanisms, "
            "so this composes with the lag rather than stacking on it. OMIT to "
            "inherit the shipped default (OFF); --exit-rate-limits arms the "
            "treatment and --no-exit-rate-limits forces the uncapped control."
        ),
    )
    parser.add_argument(
        "--entry-commissioning-lag",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FF-2A item 3 PROBE arm (audit FR-5 / FR-13): economic entry "
            "decides in year Y and commissions at Y+ENTRY_COD_LAG_YEARS (2, "
            "the LBNL 'Queued Up' IA->COD median); pending decided-not-online "
            "MW net against later years' caps. The structural anti-cobweb. OMIT to "
            "inherit the shipped default, ARMED by owner decision D-2 "
            "(2026-08-02); --no-entry-commissioning-lag forces the un-lagged "
            "control."
        ),
    )
    parser.add_argument(
        "--capacity-screen-unified-lookahead",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FFR-5D PROBE arm (owner decision D-19(a), 2026-08-05): unify "
            "every capacity screen — retirement pipeline decide AND "
            "re-screens, CCS, new entry, storage — on the lookahead price "
            "object for its entering year, bridged/bridge-adjacent entering "
            "years included (growth-scaled fallback; zero measured reads, "
            "rule 22 by construction), with the FFR-5A §2a level repairs "
            "(storage enters the stack, entering-year VRE capacity, hourly "
            "availability). OMIT to inherit the shipped default (OFF); "
            "--capacity-screen-unified-lookahead arms the treatment and "
            "--no-capacity-screen-unified-lookahead forces the control."
        ),
    )
    parser.add_argument(
        "--capacity-screen-scarcity-restoration",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FFR-8A PROBE arm (owner decision D-21(a) re-opened at Addendum "
            "AC.1, 2026-08-07): restore the published-design scarcity content "
            "of the unified lookahead's ORDC tail — the published curve on "
            "the forward COMMITTED-capability reserve quantity (RTOLCAP/"
            "RTOFFCAP share tables, storage AS share), the pre-RTC AS-plan "
            "withholding in the energy-stack search (forward NP3-160-CD "
            "requirement model), and the fleet's own forced-outage "
            "uncertainty integrated by Gauss-Hermite quadrature (LOLP-"
            "bearing). Requires --capacity-screen-unified-lookahead; "
            "ERCOT-only. OMIT to inherit the shipped default (OFF)."
        ),
    )
    parser.add_argument(
        "--entry-forward-expectation-signal",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "ENTRY-SIGNAL forward-expectation MEASUREMENT arm (the rung "
            "named by docs/FINDING-entry-signal-disarm-2026-08.md §6): the "
            "capacity screens' price object becomes the run's own prior-year "
            "hourly ZONAL LP dual surface re-leveled hour-by-hour against "
            "the ENTERING year's stack (the same lookahead instrument "
            "evaluated at the entering demand minus at the current dispatched "
            "demand), replacing the zone-flat MC-step object — locational "
            "AND forward-looking, zero fitted parameters. Requires the "
            "reprice (entry_lookahead_reprice). OMIT to inherit the shipped "
            "ScenarioConfig default (GATED OFF — this is a measurement, not "
            "an arming); --entry-forward-expectation-signal arms the "
            "treatment and --no-entry-forward-expectation-signal forces the "
            "control explicitly."
        ),
    )
    parser.add_argument(
        "--entry-dispersion-expectation-signal",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D43 dispersion-carrying entry expectation MEASUREMENT arm "
            "(the D39 object, docs/handoffs/FINDING-capx-d39-entry-underbuild-"
            "2026-09-02.md): the capacity screens' price object becomes each "
            "zone's OWN realized price-duration curve (the prior solve's "
            "zonal duals) indexed by the ENTERING year's stack-headroom rank "
            "on the current year's headroom distribution, replacing the "
            "zone-flat MC-step object — the realized dispersion (daily "
            "spread, hours >= $100, trough, zonal spread) the stack discards, "
            "zero fitted parameters. Requires the reprice "
            "(entry_lookahead_reprice); mutually exclusive with "
            "--entry-forward-expectation-signal and --entry-margin-exhaustion. "
            "OMIT to inherit the shipped ScenarioConfig default (GATED OFF — "
            "this is a measurement, not an arming); "
            "--entry-dispersion-expectation-signal arms the treatment and "
            "--no-entry-dispersion-expectation-signal forces the control "
            "explicitly."
        ),
    )
    parser.add_argument(
        "--entry-margin-exhaustion",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "D11-R margin-exhaustion entry volume rule MEASUREMENT arm "
            "(docs/FINDING-entry-signal-l1-2026-08.md §2, the L-1b closure "
            "productionized): BOTH entry allocators (thermal/VRE and "
            "storage) build in repriced tranches until the screen's own "
            "margin is exhausted, bounded by the SAME caps, replacing the "
            "bang-bang full-cap allocation. Composes with the reprice in "
            "EITHER state since owner ruling R-B (2026-08-31): armed WITH "
            "--no-entry-lookahead-reprice the screens keep the raw "
            "prior-year zonal duals as their level and this rule supplies "
            "the capacity response — the C-1 joint posture "
            "(docs/PRECOMMIT-c1-joint-wind-2026-08-31.md). OMIT to inherit the shipped "
            "ScenarioConfig default (GATED OFF — this is a measurement, not "
            "an arming); --entry-margin-exhaustion arms the treatment and "
            "--no-entry-margin-exhaustion forces the control explicitly."
        ),
    )
    parser.add_argument(
        "--entry-forward-reserve-leg",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "D12 scarcity-consistent entry reserve leg MEASUREMENT arm "
            "(docs/handoffs/FINDING-capx-d12-scarcity-basis-2026-08-30.md): "
            "the thermal entry screens' hourly reserve legs read the "
            "entering year's OWN expected-ORDC adder — the same instrument "
            "invocation that priced the energy leg — instead of the prior "
            "solved year's realized post-solve adder, so the whole margin "
            "carries ONE scarcity object. Requires the reprice "
            "(entry_lookahead_reprice) and screen_reserve_value_enabled. "
            "OMIT to inherit the shipped ScenarioConfig default (GATED OFF "
            "— this is a measurement, not an arming); "
            "--entry-forward-reserve-leg arms the treatment and "
            "--no-entry-forward-reserve-leg forces the control explicitly."
        ),
    )
    parser.add_argument(
        "--storage-entry-availability-gate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "T1-H capacity-entry D-2 storage availability-year gate "
            "MEASUREMENT arm (docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md "
            "Phase-1 Leg A): the storage entry screen admits a technology "
            "only at/after its measured first-US-operating year "
            "(constants.STORAGE_TECH_AVAILABLE_YEAR, derived from the "
            "EIA-860 energy-storage schedule, fail-closed for a class with "
            "zero national base ever) — the same availability-year gate the "
            "thermal path already carries, on BOTH storage allocation "
            "rules. OMIT to inherit the shipped ScenarioConfig default, "
            "which is GATED ON since the 2026-08-31 R-A arming (it was OFF "
            "through the A/B that produced that ruling); "
            "--storage-entry-availability-gate arms it explicitly and "
            "--no-storage-entry-availability-gate is now the way to get the "
            "disarmed control."
        ),
    )
    parser.add_argument(
        "--storage-entry-cost-normalized-rank",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "T1-H capacity-entry D-3 cost-normalized storage tech selection "
            "MEASUREMENT arm (same charter as "
            "--storage-entry-availability-gate): clearing storage "
            "technologies are ranked on margin per unit capital cost "
            "(margin / STORAGE_TECHS[tech]['capex_per_kw']) instead of "
            "absolute $/MW-yr, on BOTH storage allocation rules. "
            "Sign-preserving — which technologies clear is unchanged. OMIT "
            "to inherit the shipped ScenarioConfig default, which is GATED "
            "ON since the 2026-08-31 R-A arming (it was OFF through the A/B "
            "that produced that ruling); "
            "--storage-entry-cost-normalized-rank arms it explicitly and "
            "--no-storage-entry-cost-normalized-rank is now the way to get "
            "the disarmed control."
        ),
    )
    parser.add_argument(
        "--vre-procurement-additions",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FFR-5E near-term VRE procurement channel MEASUREMENT arm (owner "
            "decision D-18(a); channel landed by FFR-5E, hindcast arm "
            "unblocked by FFR-3V-FIX §6): step 4's wind/solar limb reads the "
            "run's OWN EIA-860 vintage proposed sheet at construction-"
            "committed status (U/V/TS) and commissions each row in its "
            "Effective Year as a per-year FLOW into the zonal pools tagged "
            "source='procured', netting that flow from the economic screen's "
            "queue/group budgets so one physical queue is spent once. Zero "
            "free parameters. OMIT to inherit the shipped ScenarioConfig "
            "default (GATED OFF — this is a measurement, not an arming); "
            "--vre-procurement-additions arms the treatment and "
            "--no-vre-procurement-additions forces the control explicitly."
        ),
    )
    parser.add_argument(
        "--entry-pipeline-aware-signal",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "FFR-5C anti-cobweb guard relocation MEASUREMENT arm (owner "
            "decision D-17(a); named repair candidate R-a by FFR-9B §4, "
            "staged by the FFR-9C lane): the pending-pipeline STOCK stops "
            "netting against the annual FLOW caps (growth ladder + per-tech "
            "queue cap bind as their citations define) and the entry "
            "pro-forma prices its own committed pipeline instead. Zero new "
            "parameters. OMIT to inherit the shipped ScenarioConfig default "
            "(GATED OFF); --entry-pipeline-aware-signal arms the treatment "
            "and --no-entry-pipeline-aware-signal forces the control "
            "explicitly."
        ),
    )
    parser.add_argument(
        "--smr-available-year",
        type=int,
        default=None,
        help=(
            "FFR-9C R-b SMR availability-year gate MEASUREMENT arm (FFR-9B "
            "§4): nuclear_smr joins the economic-entry candidate pool only "
            "from this calendar year. ATB 2024 costs new nuclear from 2030 "
            "only (NEW_ENTRY_COSTS), so the measurement arm passes 2030. "
            "OMIT to inherit the shipped ScenarioConfig default (None = the "
            "ungated always-eligible posture)."
        ),
    )
    parser.add_argument(
        "--fossil-announced-exits",
        dest="fossil_announced_exits",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "capx D42 channel, ARMED AS THE DEFAULT POSTURE by owner ruling "
            "Q30 (2026-09-03, capx D44): honor each FOSSIL unit's owner-filed "
            "EIA-860 Schedule-3 planned retirement date as an exogenous step-1 "
            "exit, read from the run's vintage snapshot (vintage-gated — a "
            "date is admissible only because it was on file at the cutoff), "
            "the reversal registry armed, the economic screen on the residual "
            "(undated) fleet and the admission-cap floor netting the dated "
            "exits. Under the default verification posture the dated set is "
            "checked against the later in-repo vintages (a re-filed deferral "
            "or a withdrawn date is honored per unit; nothing is injected or "
            "advanced); with --no-verified-announced-exits it is the pure "
            "ex-ante set. OMIT to inherit the shipped ScenarioConfig default "
            "(GATED ON since Q30); --no-fossil-announced-exits forces the "
            "pre-Q30 control posture explicitly, which is byte-identical to "
            "the pre-flip harness and keeps that arm's pre-flip cache key."
        ),
    )
    parser.add_argument(
        "--no-verified-announced-exits",
        dest="verified_announced_exits",
        action="store_false",
        default=True,
        help=(
            "Restore the RC-1B ex-ante announced-exit posture: honor every "
            "vintage EIA-860 announced date even when the realized record "
            "shows the exit was reversed by a later counter-instrument "
            "(Byron/Dresden under IL CEJA). The harness DEFAULT since "
            "2026-08-22 is verification ON — announced/'known' exits are "
            "countered by the reversal registry read without the vintage "
            "information gate, so a plant that demonstrably kept running is "
            "never false-retired. Committed pre-2026-08-22 legs all ran the "
            "ex-ante arm and their verdicts stand as scored."
        ),
    )
    args = parser.parse_args(argv)

    iso = args.iso.upper()
    crossover = bool(args.crossover)
    forward_from_base = bool(args.forward_from_base)
    arm = str(args.arm)
    if forward_from_base and args.entry_lookahead_reprice is True:
        # The G-30 lookahead's hindcast branch reads the NEXT year's measured
        # demand — a measured-input read every T1-FF solve year is defined to
        # exclude. (The runner's seam suppresses that read for forward
        # next-years, but a posture contradiction is refused loudly
        # rather than silently defanged.)
        #
        # ``is True`` since FFR-3D's C.4(c) un-pin: the flag is now tri-state,
        # and only an EXPLICIT --entry-lookahead-reprice is the contradiction
        # this refuses. Omitting it inherits the shipped default (True), which
        # the runner's is_crossover_forward_year branch resolves to the
        # growth-scaled fallback — no measured read, so no refusal. Testing
        # the resolved value here instead would refuse every T1-FF leg.
        raise SystemExit(
            "--entry-lookahead-reprice is not available with "
            "--forward-from-base: its hindcast branch consumes measured "
            "next-year demand, which the full-forward posture excludes"
        )
    # Vintage default resolves by mode; a crossover MUST seed from the 2023
    # vintage (plan §2.2) — reject a mismatched explicit --vintage loudly rather
    # than silently seeding a crossover from the wrong fleet. A full-forward
    # run must seed from a vintage at/before its base year (plan §2: "seeded
    # from an EIA-860 vintage at or before the base year"); its default is the
    # newest allowed vintage that satisfies that.
    vintage = args.vintage
    start_year = args.start_year
    if forward_from_base:
        if start_year is None:
            start_year = 2023  # Phase A default (plan §3.1)
        if vintage is None:
            eligible = [v for v in ALLOWED_VINTAGES if v <= start_year]
            if not eligible:
                raise SystemExit(
                    f"no allowed EIA-860 vintage at/before base {start_year} "
                    f"(allowed: {ALLOWED_VINTAGES})"
                )
            vintage = max(eligible)
        if vintage > start_year:
            raise SystemExit(
                f"--forward-from-base requires --vintage <= the base year "
                f"(a forecast started at {start_year} cannot seed from the "
                f"{vintage} snapshot; plan §2)"
            )
    elif vintage is None:
        vintage = CROSSOVER_VINTAGE_YEAR if crossover else DEFAULT_VINTAGE_YEAR
    if crossover and vintage != CROSSOVER_VINTAGE_YEAR:
        raise SystemExit(
            f"--crossover requires --vintage {CROSSOVER_VINTAGE_YEAR} "
            f"(plan §2.2); got {vintage}"
        )
    # Window defaults by mode (None => mode default; explicit value overrides).
    if start_year is None:
        start_year = 2023 if crossover else 2021
    end_year = args.end_year
    if end_year is None:
        end_year = 2027 if crossover else 2025
    _validate_window(start_year, end_year, crossover, forward_from_base)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # THE promise this run makes about which years it will solve. Derived from
    # the runner's own bridge predicate (FFR-3U), printed in the banner below,
    # and asserted against the realized ledgers at completion — so the banner
    # cannot say one thing while the solve does another. FFR-3Q's run printed
    # "bridges [2022, 2026] are never solved or read" and then solved 2022; a
    # governance banner not mechanically tied to behaviour is decoration
    # (owner Addendum L.1).
    promised_solve_years = window_solve_years(
        start_year, end_year, crossover, forward_from_base
    )
    promised_bridge_years = [
        y for y in range(start_year, end_year + 1) if y not in promised_solve_years
    ]

    # Governance record (FH-1, plan §5.3): the holdout freeze is read and the
    # run's legality stated EXPLICITLY at launch — deliberate, not accidental.
    # A T1-FF/hindcast window is freeze-legal by construction (solves = the
    # training years + the {2021} seed; scoring never leaves 2023-2025; the
    # 2022/2026 quarantine is bridged), which _validate_window has already
    # fail-closed enforced above. The freeze state is recorded in the meta.
    freeze_path = _ROOT / holdout_policy.FREEZE_FILE
    freeze_active = False
    if freeze_path.exists():
        freeze_active = bool(json.loads(freeze_path.read_text()).get("active"))
    if freeze_active:
        print(
            "[governance] HOLDOUT SPEND FREEZE is ACTIVE "
            f"({holdout_policy.FREEZE_FILE}). This run remains legal under it: "
            "solve years are the rule-22 training window "
            f"{sorted(holdout_policy.CALIBRATION_YEARS)} plus the enumerated "
            f"seed {sorted(holdout_policy.HINDCAST_SEED_YEARS)} (never scored), "
            "and scoring is bounded to the training window on both sides "
            "(score_crossover). No out-of-training year is solved, scored, or "
            "registered; no marker is spent."
        )
    # Stated for EVERY run, freeze or not, and stated as THIS window's own
    # resolved sets rather than the static bridge constant — a banner that
    # names {2022, 2026} unconditionally is true of the constant, not of the
    # run. Verified at completion (search: SOLVE-YEAR PARITY).
    print(
        f"[governance] this window SOLVES {promised_solve_years} and BRIDGES "
        f"{promised_bridge_years} (evolved across, LP never solved, measured "
        "data never read — rule 22). Asserted against the realized evolution "
        "ledgers at completion."
    )

    # FFR-2E posture label for the meta record (pure resolution, no side
    # effect — build_config resolves the same pair internally). Called here so
    # the mutual-exclusion check fails BEFORE the solve, not after it.
    _, _clearing_posture = resolve_capacity_clearing_posture(
        iso, args.capacity_market_clearing, args.fixed_net_cone
    )
    print(
        f"[posture] capacity-price arm: {_clearing_posture} "
        f"(FFR-2E / audit FR-14). Pass --fixed-net-cone for the flat "
        "net-CONE comparison arm."
    )

    config = build_config(
        iso,
        start_year,
        end_year,
        args.fuel_variant,
        vintage=vintage,
        crossover=crossover,
        forward_from_base=forward_from_base,
        arm=arm,
        crossover_forward_gas_path=args.crossover_forward_gas_path,
        energy_only_floor=args.energy_only_floor,
        entry_lookahead_reprice=args.entry_lookahead_reprice,
        limited_foresight_dispatch=args.limited_foresight_dispatch,
        legacy_renewable_credit=args.legacy_renewable_credit,
        capacity_market_clearing=args.capacity_market_clearing,
        fixed_net_cone=args.fixed_net_cone,
        correlated_forced_outage=args.correlated_forced_outage,
        retirement_rule=args.retirement_rule,
        entry_screen_diagnostics=args.entry_screen_diagnostics,
        entry_vre_capacity_revenue=args.entry_vre_capacity_revenue,
        neiso_net_icr_requirement=args.neiso_net_icr_requirement,
        pjm_accreditation_design_vintage=args.pjm_accreditation_design_vintage,
        pjm_demand_response_supply=args.pjm_demand_response_supply,
        capacity_market_supply_clearing=args.capacity_market_supply_clearing,
        nyiso_requirement_forecast_peak=args.nyiso_requirement_forecast_peak,
        nyiso_requirement_vintage_factors=args.nyiso_requirement_vintage_factors,
        locality_capacity_curves=args.locality_capacity_curves,
        adequacy_accounting_ratio_dated_net=args.adequacy_accounting_ratio_dated_net,
        retirement_sector_gate=args.retirement_sector_gate,
        entry_rate_limits=args.entry_rate_limits,
        entry_commissioning_lag=args.entry_commissioning_lag,
        exit_rate_limits=args.exit_rate_limits,
        capacity_screen_unified_lookahead=args.capacity_screen_unified_lookahead,
        capacity_screen_scarcity_restoration=(
            args.capacity_screen_scarcity_restoration
        ),
        vre_procurement_additions=args.vre_procurement_additions,
        entry_pipeline_aware_signal=args.entry_pipeline_aware_signal,
        entry_forward_expectation_signal=args.entry_forward_expectation_signal,
        entry_dispersion_expectation_signal=(args.entry_dispersion_expectation_signal),
        entry_margin_exhaustion=args.entry_margin_exhaustion,
        entry_forward_reserve_leg=args.entry_forward_reserve_leg,
        storage_entry_availability_gate=args.storage_entry_availability_gate,
        storage_entry_cost_normalized_rank=(args.storage_entry_cost_normalized_rank),
        smr_available_year=args.smr_available_year,
        ptc_window=args.ptc_window,
        verified_announced_exits=args.verified_announced_exits,
        fossil_announced_exits=args.fossil_announced_exits,
    )

    # Bundle lives under results/hindcast/<run>/ (plan §1.5) -- deliberately
    # OUTSIDE the backcast registry, so audit_keepers / legitimacy_diagnostics
    # never see a bundle with a 2021 solve year. Point the cache root here.
    cachemod.CACHE_ROOT = args.out_dir
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if forward_from_base:
        kind = "full_forward"
    elif crossover:
        kind = "crossover"
    else:
        kind = "hindcast"
    tag = f"[{kind}]"
    print(
        f"{tag} {iso} {start_year}-{end_year} variant={config.hindcast_fuel_variant} "
        f"gas={config.gas_price_path} vintage={vintage}"
        + (
            f" forward>={config.crossover_forward_year} "
            f"gas_fwd={config.crossover_forward_gas_path}"
            if config.crossover_forward_year is not None
            else ""
        )
        + (
            f" arm={arm} weather="
            + ("solve-year" if config.crossover_solve_year_weather else "base-year")
            if forward_from_base
            else ""
        )
    )
    # Pre-solve forward-driver guard (FH-1: "at run time, not only in unit
    # tests"): pure-config checks — the boundary flagging, the resolved gas
    # path per solve year, and the §4-row-7 back-hold trap — abort BEFORE a
    # multi-hour solve is burned. Re-asserted after the solve for the meta.
    pre_violations = assert_forward_drivers(config, start_year, end_year)
    if pre_violations:
        print(f"{tag} PRE-SOLVE forward-driver guard violations (aborting):")
        for v in pre_violations:
            print("  -", v)
        return 1
    key = run_scenario(config, iso)
    bundle = args.out_dir / iso / key
    ledgers = load_ledgers_for_run(bundle)

    violations = assert_pipeline_from_vintage(iso, args.out_dir, ledgers, vintage)
    # Crossover forward-driver guard (FF-0E §2.2, generalized FH-1): the
    # forward years must consult no backcast-gated realized loader.
    violations += assert_forward_drivers(config, start_year, end_year)
    if violations:
        print(f"{tag} LEAKAGE GUARD violations:")
        for v in violations:
            print("  -", v)

    solved = sorted(y for y in ledgers if not ledgers[y].get("bridge"))
    bridged = sorted(y for y in ledgers if ledgers[y].get("bridge"))

    # SOLVE-YEAR PARITY (FFR-3U, owner Addendum L.1 condition on the banner).
    # The realized set — read back from the evolution ledgers the solve itself
    # wrote — must equal what the launch banner promised. This is the assertion
    # FFR-3Q's run had no way to fail: its banner promised 2022 was bridged and
    # its ledgers recorded 2022 solved, and nothing compared the two. A
    # mismatch is a rule-22 STOP-THE-LINE, so it raises rather than warns:
    # by the time it fires the quarantined year has already been read, and the
    # only correct behaviour left is to refuse to produce a meta, a
    # run_config.json or a registrable bundle from it.
    if solved != sorted(promised_solve_years) or bridged != sorted(
        promised_bridge_years
    ):
        raise SystemExit(
            f"{tag} SOLVE-YEAR PARITY FAILURE (rule 22 STOP-THE-LINE): the "
            f"launch banner promised solved {sorted(promised_solve_years)} / "
            f"bridged {sorted(promised_bridge_years)}, but the run realized "
            f"solved {solved} / bridged {bridged}. A quarantined year may "
            "already have been solved and its measured data read — do NOT "
            "register this bundle; quarantine it, escalate, and treat the "
            f"cache key {key} as contaminated."
        )
    # The meta has three zones, and the middle one is the point of FFR-3R.
    #
    #   1. HARNESS LABELS — what mode/arm the operator asked for. Not
    #      ScenarioConfig properties, so the config cannot answer them.
    #   2. THE CONFIG-DESCRIBING BLOCK — built BY CONSTRUCTION from the
    #      ScenarioConfig the solve actually ran on, via META_RECORD_SPEC.
    #      No `args.*` may appear here: that is the defect four lanes each
    #      found and patched key-by-key (FFR-1D / FFR-3D / FFR-2E / FFR-3L).
    #      The two deliberately args-sourced keys are declared FromArgs in the
    #      spec with their reasons, and are the ONLY exemption.
    #   3. RUN OUTCOME — what came back from the solve.
    #
    # assert_sourced below re-checks the finished dict, so a key merged in
    # later (or a new ScenarioConfig field recorded from args) fails loudly at
    # write time instead of silently entering a scored verdict.
    _record_ctx = {"iso": iso, "forward_from_base": forward_from_base}
    _assert_posture_consistent(_clearing_posture, config, iso)
    meta = {
        # -- 1. harness labels --------------------------------------------- #
        "kind": kind,
        "crossover": crossover,
        # T1-FF record (FH-1, plan §2.1): mode + pre-registered arm + base, so
        # a full-forward bundle is self-describing and the scorer/registry
        # never has to infer the arm from the gas path.
        "forward_from_base": forward_from_base,
        "arm": arm if forward_from_base else None,
        "base_year": start_year if forward_from_base else None,
        "holdout_freeze_active_at_launch": freeze_active,
        # -- 2. config-describing block (solved-sourced by construction) ---- #
        # Built from the SEAM-RESOLVED config, not the request config: the
        # runner applies ``apply_iso_scenario_defaults`` internally before
        # solving (runner.run_scenario_iso), so for an ISO with
        # ``default_scenario_overrides`` (ERCOT's D-30 stage-B five, MISO's
        # D-26 pair) the request object under-reports the posture the solve
        # actually ran — the FFR-2E defect class the resolver's own docstring
        # names ("a record must report the posture it solved, not assert
        # one"; ARM3-MEASURE hit it first). Resolution honours the caller's
        # explicitly-set-field record (OVERRIDE-FIX 2026-08-13), so a control
        # arm passing an explicit False still records False. First exposed by
        # the first pass-nothing ERCOT leg after the D-30 arming
        # (ercot-2021-2025-realized-t1h-refresh, 2026-08-22): its meta said
        # the five stage-B flags were off while its own run_config.json — the
        # FC-7 artifact, from the RESOLVED config the solve wrote — said on.
        **META_RECORD_SPEC.build(
            (record_config := apply_iso_scenario_defaults(config, iso)),
            _record_ctx,
            args_values={
                "capacity_clearing_posture": _clearing_posture,
                "capacity_market_clearing_forced": bool(args.capacity_market_clearing),
            },
        ),
        # -- 3. run outcome ------------------------------------------------- #
        "cache_key": key,
        "bundle": str(bundle),
        "solved_years": solved,
        "bridged_years": bridged,
        "leakage_violations": violations,
        "started_utc": started,
    }
    META_RECORD_SPEC.assert_sourced(meta, record_config, _record_ctx)
    (args.out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    # Request-side dump, kept: build_forecast_dof_ledger._load_run_config still
    # falls back to it, and the FFR-3A-3 batteries documented its scorer
    # behaviour. The FC-7 artifact is the .json below, never this file.
    config.to_yaml_full(args.out_dir / "run_config.yaml")
    # FC-7 provenance artifact (FFR-3K — the hindcast analogue of FFR-3D's
    # blocker-7 fix): run_config.json from the bundle's OWN resolved
    # config.yaml (the RESOLUTION save_result wrote), via the same writer
    # run_full_horizon uses. Before this, every T1-H/T1-X/T1-FF leg FAILed
    # FC-7 row 1 "run_config.json absent" by construction. ``bundle`` is
    # passed ONLY positionally (the ea7cd5d binding contract): the writer
    # records ``run_dir`` itself.
    run_config_path = write_run_config(
        args.out_dir,
        bundle,
        iso=iso,
        cache_key=key,
        solved_years=solved,
        bridged_years=bridged,
        kind=kind,
    )
    print(f"{tag} done. solved {solved}, bridged {bridged}")
    print(f"{tag} bundle: {bundle}")
    print(f"{tag} meta:   {args.out_dir / 'meta.json'}")
    print(f"{tag} config: {run_config_path}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
