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
  any bench/actual for a year >= 2026).

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

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results import cache as cachemod  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from market_sim.pipeline.api import run_scenario  # noqa: E402
from market_sim.runner import HINDCAST_BRIDGE_YEARS as _RUNNER_BRIDGE_YEARS  # noqa: E402
from scripts.lib import holdout_policy  # noqa: E402

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
# 2026+ pure forward drivers (plan §2.2).
CROSSOVER_FORWARD_YEAR = 2026
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
    solve_years = [
        y
        for y in range(start_year, end_year + 1)
        # A crossover forward year (>= 2026) is a SOLVED forecast-mode year,
        # not a bridge — so it does not skip the allowed-year check below.
        if not (
            y in HINDCAST_BRIDGE_YEARS
            and not (crossover and y >= CROSSOVER_FORWARD_YEAR)
        )
    ]
    for y in solve_years:
        if y not in allowed:
            kind = "crossover" if crossover else "hindcast"
            raise SystemExit(f"year {y} is not an allowed {kind} solve year")
    # Fail-closed policy check (FH-1): the hindcast-lane solvable set is owned
    # by holdout_policy — anything outside training + seed refuses with its
    # tier named, whatever the local `allowed` literal says. Crossover forward
    # years (2026+) are the one legal exception (forecast-mode solves reading
    # no measured actuals, rule 22).
    _policy_years = [
        y for y in solve_years if not (crossover and y >= CROSSOVER_FORWARD_YEAR)
    ]
    violations = holdout_policy.hindcast_solve_year_violations(_policy_years)
    if violations:
        raise SystemExit(
            "rule-22 holdout policy refuses this window:\n  - "
            + "\n  - ".join(violations)
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
    entry_lookahead_reprice: bool = False,
    limited_foresight_dispatch: bool = False,
    legacy_renewable_credit: bool = False,
    capacity_market_clearing: bool = False,
    correlated_forced_outage: bool = False,
    retirement_rule: str = "legacy",
    entry_screen_diagnostics: bool = False,
    entry_vre_capacity_revenue: bool = False,
    entry_rate_limits: bool = False,
    entry_commissioning_lag: bool = False,
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
        boundary = start_year
        weather_year = start_year
        solve_year_weather = arm == "realized"
    else:
        gas_path = FUEL_VARIANT_GAS_PATH[variant]
        fwd_gas_path = crossover_forward_gas_path
        boundary = CROSSOVER_FORWARD_YEAR if crossover else None
        # T1-X: pin the weather year to the last realized year (boundary − 1 =
        # 2025) so "growth-scaled demand from the last realized year" (plan
        # §2.2) is exactly what the forward years see. A plain hindcast keeps
        # the model default weather_year (2024), unchanged.
        weather_year = (
            CROSSOVER_FORWARD_YEAR - 1 if crossover else ScenarioConfig().weather_year
        )
        solve_year_weather = False
    return ScenarioConfig(
        iso=iso,
        mode="forecast",
        hindcast=True,
        start_year=start_year,
        end_year=end_year,
        eia860_vintage_year=vintage,
        hindcast_fuel_variant=variant,
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
        # Production scarcity footing (see docstring): ERCOT → ORDC overlay,
        # PJM → capacity-market (no-op). Harness default, not a model default.
        scarcity_pricing_enabled=True,
        market_design_retirement_floor=energy_only_floor,
        # G-30 corrective arm (probe, default-off): re-price each entering
        # year's KNOWN realized net load against the current (post-retirement)
        # fleet stack with the published ORDC curve, and feed that pro-forma to
        # the retirement / new-entry / storage screens. Tempers the perfect-
        # foresight LP's screen signal: where the thinned fleet is genuinely
        # short against next year's realized load, the screen sees scarcity the
        # over-supplied in-year dispatch never forms. Zero fitted parameters
        # (rule 13); screens-only, never dispatch. See scenarios.py:
        # entry_lookahead_reprice and the runner call site.
        entry_lookahead_reprice=entry_lookahead_reprice,
        # G-31 first-wave corrective arm (PROBE, default-off):
        #   limited_foresight_dispatch -- deny the in-year LP perfect annual
        #     storage/hydro foresight so peak/net-load-ramp hours tighten and the
        #     ORDC overlay prices scarcity in-year once the fleet has thinned.
        # Zero fitted parameters; see the scenarios.py field docstring.
        # (staged_oversupply_thinning was DELETED at the FF-1A R-NEW commit,
        # rule 26 -- the execution-lag pipeline carries the deactivation queue.)
        limited_foresight_dispatch=limited_foresight_dispatch,
        # FF-1A R-NEW probe arm (default "legacy" = byte-identical): the
        # decision/execution retirement pipeline, ff-retirement-rule-redesign-
        # 2026-07.md §3.6 (owner D1 = Option B). Never the harness default
        # pending the FF-2C flip decision.
        retirement_rule=retirement_rule,
        # CR-3.1 frozen-penetration byte-compat arm: pin the VRE adequacy
        # credits back to the pre-curve flat constants for the BEFORE leg of
        # the before/after diagnostic. Default (False) keeps the model
        # default renewable_elcc_curves=True -- the AFTER leg.
        renewable_elcc_curves=not legacy_renewable_credit,
        # RC-1B probe flag (PROBE, default-off): arm the CR-1 sloped capacity
        # demand curve for THIS hindcast's OWN ISO only, via the per-ISO
        # override mapping (RC-1B item 1 -- resolve_capacity_market_clearing).
        # The scalar capacity_market_clearing stays off, so the arm can never
        # leak to another ISO even if a future harness runs more than one per
        # invocation. Default (flag off) => None => byte-identical. Never the
        # harness default -- see plan §2.2 (the position-calibration measurement
        # this flag exists to run).
        capacity_market_clearing_by_iso=(
            {iso: True} if capacity_market_clearing else None
        ),
        # FF-1B probe arm (default-off): the correlated cold-event forced-
        # outage derate (data/outages.apply_correlated_outage_derate), so a
        # hindcast leg's realized deep-cold days (Uri 2021, Heather 2024)
        # physically thin the fleet and the in-year ORDC can form scarcity
        # (the G-31 question). Measured frozen curves, zero fitted parameters
        # -- see scenarios.py:correlated_forced_outage.
        correlated_forced_outage=correlated_forced_outage,
        # FF-2A entry-stack dampers (GATED, default-off; audit FR-5 / owner
        # decision D-2). History: FFR-1D deleted the three CLI flags on
        # 2026-07-31 (rule 26) because FF-3D had dropped their passthrough while
        # keeping the flags, so a leg launched with --entry-rate-limits recorded
        # `entry_rate_limits: true` in its meta on a solve that never armed it —
        # an inert flag that falsifies the run record. FFR-1D's own instruction
        # for the successor was "a session that needs them wires the passthrough
        # for real, one line each; it does not resurrect a flag that lies".
        # FFR-2B (2026-08-02) is that session: the fields are consumed at
        # runner.py:733,746 and new_entry.py:781,1104,1118, so each flag below
        # now genuinely arms its mechanism and the meta it writes is true.
        # Defaults stay False — no ScenarioConfig default moves here (rule 24;
        # the flip is the owner's, executed at FFR-3A step 0).
        entry_vre_capacity_revenue=entry_vre_capacity_revenue,
        entry_rate_limits=entry_rate_limits,
        entry_commissioning_lag=entry_commissioning_lag,
        # RC-0C decision-neutral per-candidate entry-screen decomposition
        # (byte-identical fleet outcome; lands in evolution_<year>.json).
        entry_screen_diagnostics=entry_screen_diagnostics,
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
        if y in HINDCAST_BRIDGE_YEARS and not (
            # A crossover forward year >= 2026 is un-bridged (solved); a
            # full-forward run inside 2021-2025 keeps the 2022 bridge, which
            # is never solved — nothing to assert for it.
            y >= CROSSOVER_FORWARD_YEAR and config.is_crossover_forward_year(y)
        ):
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
        action="store_true",
        help=(
            "G-30 corrective arm (PROBE): enable entry_lookahead_reprice so the "
            "capacity screens see each entering year's realized net load "
            "re-priced against the current fleet with the published ORDC curve. "
            "Tests whether tempering the perfect-foresight screen signal lets "
            "scarcity form so solar entry clears / over-retirement drops. "
            "Probe-only -- see build_config."
        ),
    )
    parser.add_argument(
        "--retirement-rule",
        choices=["legacy", "pipeline"],
        default="legacy",
        help=(
            "FF-1A PROBE arm: economic-retirement decision rule. 'legacy' "
            "(default) = per-fuel consecutive-loss counters, byte-identical. "
            "'pipeline' = the R-NEW decision/execution split (uniform bar, "
            "joint adequacy-capped entry, soft latch, measured per-fuel "
            "execution lags) -- ff-retirement-rule-redesign-2026-07.md §3.6. "
            "Never the harness default pending the FF-2C flip decision."
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
            "RC-1B PROBE: arm the CR-1 sloped capacity demand curve for THIS "
            "hindcast's own ISO only, via ScenarioConfig."
            "capacity_market_clearing_by_iso={iso: True} (the scalar stays "
            "off). Never the harness default."
        ),
    )
    parser.add_argument(
        "--correlated-forced-outage",
        action="store_true",
        help=(
            "FF-1B PROBE: arm the correlated cold-event forced-outage "
            "availability derate (correlated_forced_outage=True) so realized "
            "deep-cold days physically thin the fleet and in-year ORDC "
            "scarcity can form (the G-31 question). Measured frozen curves "
            "(constants.CORRELATED_OUTAGE_CURVE); see build_config."
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
        "--entry-vre-capacity-revenue",
        action="store_true",
        help=(
            "FF-2A item 1 PROBE arm (audit FR-5 / owner D-2): wind+solar entry "
            "candidates earn capacity_price_per_firm_mw_yr x the published "
            "ELCC credit at the model's own installed nameplate -- the SAME "
            "price seam thermal entry uses. Structural no-op in energy-only "
            "ISOs (capacity price 0). Never the harness default."
        ),
    )
    parser.add_argument(
        "--entry-rate-limits",
        action="store_true",
        help=(
            "FF-2A item 2 PROBE arm (audit FR-5 / BLK-10): cap per-tech annual "
            "economic entry AND the reserve-margin backstop at "
            "ENTRY_GROWTH_LIMIT_MULTIPLE (2.0) x the prior-max annual build, "
            "seeded from the measured EIA-860 record at the run's vintage "
            "(ReEDS relative-growth constraint). Never the harness default."
        ),
    )
    parser.add_argument(
        "--entry-commissioning-lag",
        action="store_true",
        help=(
            "FF-2A item 3 PROBE arm (audit FR-5 / FR-13): economic entry "
            "decides in year Y and commissions at Y+ENTRY_COD_LAG_YEARS (2, "
            "the LBNL 'Queued Up' IA->COD median); pending decided-not-online "
            "MW net against later years' caps. The structural anti-cobweb. "
            "Never the harness default."
        ),
    )
    args = parser.parse_args(argv)

    iso = args.iso.upper()
    crossover = bool(args.crossover)
    forward_from_base = bool(args.forward_from_base)
    arm = str(args.arm)
    if forward_from_base and args.entry_lookahead_reprice:
        # The G-30 lookahead's hindcast branch reads the NEXT year's measured
        # demand — a measured-input read every T1-FF solve year is defined to
        # exclude. (The runner's seam now suppresses that read for forward
        # next-years too, but a posture contradiction is refused loudly
        # rather than silently defanged.)
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
            f"bridges {sorted(holdout_policy.HINDCAST_BRIDGE_YEARS)} are never "
            "solved or read, and scoring is bounded to the training window on "
            "both sides (score_crossover). No out-of-training year is solved, "
            "scored, or registered; no marker is spent."
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
        correlated_forced_outage=args.correlated_forced_outage,
        retirement_rule=args.retirement_rule,
        entry_screen_diagnostics=args.entry_screen_diagnostics,
        entry_vre_capacity_revenue=args.entry_vre_capacity_revenue,
        entry_rate_limits=args.entry_rate_limits,
        entry_commissioning_lag=args.entry_commissioning_lag,
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
    meta = {
        "iso": iso,
        "kind": kind,
        "variant": config.hindcast_fuel_variant,
        "energy_only_floor": bool(args.energy_only_floor),
        "entry_lookahead_reprice": bool(args.entry_lookahead_reprice),
        "retirement_rule": args.retirement_rule,
        "limited_foresight_dispatch": bool(args.limited_foresight_dispatch),
        "capacity_market_clearing": bool(args.capacity_market_clearing),
        "capacity_market_clearing_by_iso": config.capacity_market_clearing_by_iso,
        "correlated_forced_outage": bool(args.correlated_forced_outage),
        "entry_screen_diagnostics": bool(args.entry_screen_diagnostics),
        # FF-2A dampers (FFR-2B): read from the SOLVED config, never from
        # args — the FFR-1D defect was a meta entry sourced from a flag that
        # armed nothing, so the record is taken from the object the solve
        # actually ran on and cannot diverge from it.
        "entry_vre_capacity_revenue": bool(config.entry_vre_capacity_revenue),
        "entry_rate_limits": bool(config.entry_rate_limits),
        "entry_commissioning_lag": bool(config.entry_commissioning_lag),
        "renewable_elcc_curves": bool(config.renewable_elcc_curves),
        "gas_price_path": config.gas_price_path,
        "crossover": crossover,
        "crossover_forward_year": config.crossover_forward_year,
        "crossover_forward_gas_path": (
            config.crossover_forward_gas_path
            if config.crossover_forward_year is not None
            else None
        ),
        # T1-FF record (FH-1, plan §2.1): mode + pre-registered arm + base +
        # weather posture, so a full-forward bundle is self-describing and the
        # scorer/registry never has to infer the arm from the gas path.
        "forward_from_base": forward_from_base,
        "arm": arm if forward_from_base else None,
        "base_year": start_year if forward_from_base else None,
        "weather_posture": (
            ("solve_year" if config.crossover_solve_year_weather else "base_year")
            if forward_from_base
            else None
        ),
        "holdout_freeze_active_at_launch": freeze_active,
        "vintage_year": vintage,
        "start_year": start_year,
        "end_year": end_year,
        "cache_key": key,
        "bundle": str(bundle),
        "solved_years": solved,
        "bridged_years": bridged,
        "leakage_violations": violations,
        "started_utc": started,
    }
    (args.out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    config.to_yaml_full(args.out_dir / "run_config.yaml")
    print(f"{tag} done. solved {solved}, bridged {bridged}")
    print(f"{tag} bundle: {bundle}")
    print(f"{tag} meta:   {args.out_dir / 'meta.json'}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
