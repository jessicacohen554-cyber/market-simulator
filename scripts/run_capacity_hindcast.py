#!/usr/bin/env python
"""Capacity hindcast + T1-X crossover harness (W2-P5 / FF-0E, plan §1.3, §2.2).

Runs the *forecast* machinery from a vintage fleet snapshot to test whether the
capacity-evolution screens (retirement / economic-entry / storage / CCS)
reproduce the builds and retirements an ISO actually saw. It is NOT a backcast:
``mode`` stays ``"forecast"`` and no backcast overlay fires -- the hindcast flag
only switches on vintage fleet init, realized per-year demand (no growth
scaling), the chosen fuel path, and the 2022 quarantine bridge.

Two modes, selected by ``--vintage`` / ``--crossover``:

* **Plain hindcast** (``--vintage 2020``, default; plan §1.1): initialise from
  the **EIA-860 2020 vintage**, evolve 2021 → 2025. 2021 seeds the price/margin
  signal but is not scored; **2022 is a bridge -- evolved but never solved, its
  data never read** (rule 22); 2023-2025 are solved and scored. Allowed solve
  years ``{2021, 2023, 2024, 2025}``.

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

Then score with ``scripts/score_capacity_hindcast.py`` (hindcast) or
``scripts/score_crossover.py`` (crossover).
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
from market_sim.runner import HINDCAST_BRIDGE_YEARS, run_scenario_iso  # noqa: E402

# The only years a plain hindcast may solve. 2022/2026 are quarantined (rule
# 22); 2022 is bridged (evolved, not solved), 2026 is out of the window entirely.
ALLOWED_SOLVE_YEARS = frozenset({2021, 2023, 2024, 2025})
# A T1-X crossover (FF-0E, plan §2.2) additionally solves 2026/2027 as
# forecast-mode years (rule-22-legal: no measured H1-2026 actuals are read).
CROSSOVER_ALLOWED_SOLVE_YEARS = frozenset({2023, 2024, 2025, 2026, 2027})
# First forecast (forward-driver) year of a crossover: 2023-2025 realized,
# 2026+ pure forward drivers (plan §2.2).
CROSSOVER_FORWARD_YEAR = 2026
# The EIA-860 vintage a plain hindcast seeds from (plan §1.1); a crossover seeds
# from the 2023 vintage (plan §2.2). Selected by --vintage.
DEFAULT_VINTAGE_YEAR = 2020
CROSSOVER_VINTAGE_YEAR = 2023
ALLOWED_VINTAGES = (2020, 2023)

FUEL_VARIANT_GAS_PATH = {
    "realized": "hindcast_realized",
    "asknown": "hindcast_asknown_aeo2021",
}


def _validate_window(start_year: int, end_year: int, crossover: bool) -> None:
    """Enforce the rule-22 quarantine on the requested window.

    The plain-hindcast guard is unchanged (allowed solve years
    ``{2021, 2023, 2024, 2025}``, ``end <= 2025``, 2022 bridged). A crossover
    (FF-0E, plan §2.2) additionally admits 2026/2027 as forecast-mode solves,
    requires ``start >= 2023``, and un-bridges its forward years (>= 2026) — so
    the holdout guard stays intact for plain-hindcast mode while the crossover
    window is exactly the rule-22-legal ``{2023, 2024, 2025, 2026, 2027}``.
    """
    if start_year < 2021:
        raise SystemExit(
            "hindcast start-year must be >= 2021 (demand profiles start 2021)"
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
    for y in range(start_year, end_year + 1):
        # A crossover forward year (>= 2026) is a SOLVED forecast-mode year, not
        # a bridge — so it does not skip the allowed-year check below.
        if y in HINDCAST_BRIDGE_YEARS and not (
            crossover and y >= CROSSOVER_FORWARD_YEAR
        ):
            continue  # bridged: evolved, never solved
        if y not in allowed:
            kind = "crossover" if crossover else "hindcast"
            raise SystemExit(f"year {y} is not an allowed {kind} solve year")


def build_config(
    iso: str,
    start_year: int,
    end_year: int,
    variant: str,
    vintage: int = DEFAULT_VINTAGE_YEAR,
    crossover: bool = False,
    crossover_forward_gas_path: str = "mid",
    energy_only_floor: bool = False,
    entry_lookahead_reprice: bool = False,
    limited_foresight_dispatch: bool = False,
    legacy_renewable_credit: bool = False,
    capacity_market_clearing: bool = False,
    correlated_forced_outage: bool = False,
    retirement_rule: str = "legacy",
    entry_vre_capacity_revenue: bool = False,
    entry_rate_limits: bool = False,
    entry_commissioning_lag: bool = False,
    entry_screen_diagnostics: bool = False,
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
    return ScenarioConfig(
        iso=iso,
        mode="forecast",
        hindcast=True,
        start_year=start_year,
        end_year=end_year,
        eia860_vintage_year=vintage,
        hindcast_fuel_variant=variant,
        gas_price_path=FUEL_VARIANT_GAS_PATH[variant],
        # T1-X crossover (FF-0E, plan §2.2): set the forward boundary so years
        # >= CROSSOVER_FORWARD_YEAR (2026) run on pure forward drivers (the
        # runner un-bridges them, skips the realized demand loader + the F923
        # overlay, and prices gas on the AEO path below). None for a plain
        # hindcast (byte-identical). The forward demand is growth-scaled from the
        # weather-year base; pin the weather year to the last realized year
        # (boundary − 1 = 2025) so "growth-scaled demand from the last realized
        # year" (plan §2.2) is exactly what the forward years see. A plain
        # hindcast keeps the model default weather_year (2024), unchanged.
        crossover_forward_year=(CROSSOVER_FORWARD_YEAR if crossover else None),
        crossover_forward_gas_path=crossover_forward_gas_path,
        weather_year=(
            CROSSOVER_FORWARD_YEAR - 1 if crossover else ScenarioConfig().weather_year
        ),
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
        # FF-2A entry-stack probe arms (all default-off, never the harness
        # default): item 1 — ELCC-accredited VRE capacity revenue in the
        # entry screen (BLK-7 term c, one resolver — rule 19); item 2 — the
        # measured-throughput growth ladder on entry + backstop sizing
        # (BLK-10 / term e, ReEDS 200%-of-prior-max hard bound on the
        # EIA-860 vintage seed); item 3 — the LBNL clearance→COD lag with
        # pending-queue netting (NOTE: a vintage-start hindcast has no seed
        # of the real in-flight queue, so the lag arm shifts the entry path
        # late by construction — diagnostic use only here).
        # NOTE (FF-3D 2026-07-18): the FF-2A entry-stack passthrough
        # (entry_vre_capacity_revenue / entry_rate_limits /
        # entry_commissioning_lag) is NOT forwarded — those three fields were
        # never added to ScenarioConfig (git log -S finds them in no scenarios.py
        # commit) and have no runner consumer, so passing them raised TypeError on
        # every capacity hindcast since c48daca. All three are default-OFF, so
        # dropping the passthrough is byte-identical to any solve. The CLI flags
        # and build_config params are retained as inert no-ops until the FF-2A
        # lane wires the ScenarioConfig fields + runner hooks as a unit; see the
        # FF-3D findings doc. (entry_screen_diagnostics DOES exist and is kept.)
        #
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


def assert_forward_drivers(
    config: ScenarioConfig, start_year: int, end_year: int
) -> list[str]:
    """Assert crossover FORWARD years run on forward drivers only (FF-0E §2.2).

    A crossover's forward years (>= the boundary) must NOT consult any
    backcast-gated realized-input loader: the runner skips the realized per-year
    demand loader and the F923 plant-monthly overlay for them (structurally
    gated on ``config.is_crossover_forward_year``; covered by the crossover unit
    test), and gas is priced on the AEO path rather than the realized
    "hindcast_realized" trajectory held flat. This checks the two observable
    consequences from the resolved config: (a) each forward year is flagged as a
    crossover-forward year, and (b) its resolved annual gas equals the AEO
    forward path (``crossover_forward_gas_path``), NOT the realized path. Returns
    violations (empty when clean); no-op for a plain hindcast.
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
    for y in range(max(start_year, config.crossover_forward_year), end_year + 1):
        if not config.is_crossover_forward_year(y):
            violations.append(f"{y}: not flagged as a crossover-forward year")
            continue
        resolved = resolve_annual_gas_price(config, y)
        aeo = (
            _hold_flat_extrapolate(
                HENRY_HUB_TRAJECTORIES[config.crossover_forward_gas_path], y
            )
            + basis
        )
        realized = (
            _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES[config.gas_price_path], y)
            + basis
        )
        if abs(resolved - aeo) > 1e-9:
            violations.append(
                f"{y}: forward gas {resolved:.3f} != AEO "
                f"{config.crossover_forward_gas_path} {aeo:.3f}"
            )
        if config.gas_price_path != config.crossover_forward_gas_path and (
            abs(resolved - realized) <= 1e-9
        ):
            violations.append(
                f"{y}: forward gas still on realized path "
                f"{config.gas_price_path} (backcast-gated fuel leaked)"
            )
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
            "Reference. Ignored outside --crossover."
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
        "--entry-vre-capacity-revenue",
        action="store_true",
        help=(
            "FF-2A item 1 PROBE (BLK-7 term c): wind/solar entry candidates "
            "earn the ELCC-accredited RA capacity payment through the same "
            "accreditation resolver and price seam thermal entry uses "
            "(entry_vre_capacity_revenue=True). No-op in energy-only ERCOT."
        ),
    )
    parser.add_argument(
        "--entry-rate-limits",
        action="store_true",
        help=(
            "FF-2A item 2 PROBE (BLK-10 / term e): rate-limit annual entry "
            "and backstop builds at ENTRY_GROWTH_LIMIT_MULTIPLE (2.0, ReEDS "
            "hard bound) x the measured EIA-860 prior-max annual build by "
            "tech at the run's vintage, rising as the model builds "
            "(entry_rate_limits=True)."
        ),
    )
    parser.add_argument(
        "--entry-commissioning-lag",
        action="store_true",
        help=(
            "FF-2A item 3 DIAGNOSTIC: defer economic-entry commissioning by "
            "the measured LBNL IA-to-COD lag (2 yr) with pending-queue "
            "netting (entry_commissioning_lag=True). A vintage-start "
            "hindcast has no in-flight-queue seed, so this arm shifts the "
            "entry path late by construction — diagnostic only."
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
    args = parser.parse_args(argv)

    iso = args.iso.upper()
    crossover = bool(args.crossover)
    # Vintage default resolves by mode; a crossover MUST seed from the 2023
    # vintage (plan §2.2) — reject a mismatched explicit --vintage loudly rather
    # than silently seeding a crossover from the wrong fleet.
    vintage = args.vintage
    if vintage is None:
        vintage = CROSSOVER_VINTAGE_YEAR if crossover else DEFAULT_VINTAGE_YEAR
    if crossover and vintage != CROSSOVER_VINTAGE_YEAR:
        raise SystemExit(
            f"--crossover requires --vintage {CROSSOVER_VINTAGE_YEAR} "
            f"(plan §2.2); got {vintage}"
        )
    # Window defaults by mode (None => mode default; explicit value overrides).
    start_year = args.start_year
    if start_year is None:
        start_year = 2023 if crossover else 2021
    end_year = args.end_year
    if end_year is None:
        end_year = 2027 if crossover else 2025
    _validate_window(start_year, end_year, crossover)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    config = build_config(
        iso,
        start_year,
        end_year,
        args.fuel_variant,
        vintage=vintage,
        crossover=crossover,
        crossover_forward_gas_path=args.crossover_forward_gas_path,
        energy_only_floor=args.energy_only_floor,
        entry_lookahead_reprice=args.entry_lookahead_reprice,
        limited_foresight_dispatch=args.limited_foresight_dispatch,
        legacy_renewable_credit=args.legacy_renewable_credit,
        capacity_market_clearing=args.capacity_market_clearing,
        correlated_forced_outage=args.correlated_forced_outage,
        retirement_rule=args.retirement_rule,
        entry_vre_capacity_revenue=args.entry_vre_capacity_revenue,
        entry_rate_limits=args.entry_rate_limits,
        entry_commissioning_lag=args.entry_commissioning_lag,
        entry_screen_diagnostics=args.entry_screen_diagnostics,
    )

    # Bundle lives under results/hindcast/<run>/ (plan §1.5) -- deliberately
    # OUTSIDE the backcast registry, so audit_keepers / legitimacy_diagnostics
    # never see a bundle with a 2021 solve year. Point the cache root here.
    cachemod.CACHE_ROOT = args.out_dir
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    kind = "crossover" if crossover else "hindcast"
    tag = f"[{kind}]"
    print(
        f"{tag} {iso} {start_year}-{end_year} variant={args.fuel_variant} "
        f"gas={config.gas_price_path} vintage={vintage}"
        + (
            f" forward>={config.crossover_forward_year} "
            f"gas_fwd={config.crossover_forward_gas_path}"
            if crossover
            else ""
        )
    )
    key = run_scenario_iso(config, iso)
    bundle = args.out_dir / iso / key
    ledgers = load_ledgers_for_run(bundle)

    violations = assert_pipeline_from_vintage(iso, args.out_dir, ledgers, vintage)
    # Crossover forward-driver guard (FF-0E §2.2): the forward years must consult
    # no backcast-gated realized loader (gas on the AEO path, not realized).
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
        "variant": args.fuel_variant,
        "energy_only_floor": bool(args.energy_only_floor),
        "entry_lookahead_reprice": bool(args.entry_lookahead_reprice),
        "retirement_rule": args.retirement_rule,
        "limited_foresight_dispatch": bool(args.limited_foresight_dispatch),
        "capacity_market_clearing": bool(args.capacity_market_clearing),
        "capacity_market_clearing_by_iso": config.capacity_market_clearing_by_iso,
        "correlated_forced_outage": bool(args.correlated_forced_outage),
        "entry_vre_capacity_revenue": bool(args.entry_vre_capacity_revenue),
        "entry_rate_limits": bool(args.entry_rate_limits),
        "entry_commissioning_lag": bool(args.entry_commissioning_lag),
        "entry_screen_diagnostics": bool(args.entry_screen_diagnostics),
        "renewable_elcc_curves": bool(config.renewable_elcc_curves),
        "gas_price_path": config.gas_price_path,
        "crossover": crossover,
        "crossover_forward_year": config.crossover_forward_year,
        "crossover_forward_gas_path": (
            config.crossover_forward_gas_path if crossover else None
        ),
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
