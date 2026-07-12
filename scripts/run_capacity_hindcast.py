#!/usr/bin/env python
"""Capacity hindcast harness (W2-P5, plan §1.3).

Runs the *forecast* machinery backwards from a vintage fleet snapshot to test
whether the capacity-evolution screens (retirement / economic-entry / storage /
CCS) reproduce the builds and retirements an ISO actually saw. It is NOT a
backcast: ``mode`` stays ``"forecast"`` and no backcast overlay fires — the
hindcast flag only switches on vintage fleet init, realized per-year demand (no
growth scaling), the chosen fuel path, and the 2022 quarantine bridge.

Window (plan §1.1): initialise from the **EIA-860 2020 vintage**, evolve
2021 → 2025. 2021 is solved to seed the price/margin signal but not scored;
**2022 is a bridge — evolved but never solved, its data never read** (rule 22);
2023-2025 are solved and scored. The allowed solve years are therefore
``{2021, 2023, 2024, 2025}`` only.

Rule 12: years run sequentially inside one invocation; the two fuel variants are
launched as two concurrent background invocations with separate ``--out-dir``s.

Usage::

    python scripts/run_capacity_hindcast.py --iso ERCOT --fuel-variant realized \
        --out-dir results/hindcast/ercot-2021-2025-realized

Then score with ``scripts/score_capacity_hindcast.py``.
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
# — see the PJM demand-defect investigation, 2026-07-05. Add the repo root so
# it resolves, matching scripts/regenerate_clean.py's subprocess bootstrap.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results import cache as cachemod  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from market_sim.runner import HINDCAST_BRIDGE_YEARS, run_scenario_iso  # noqa: E402

# The only years a hindcast may solve. 2022/2026 are quarantined (rule 22); 2022
# is bridged (evolved, not solved), 2026 is out of the window entirely.
ALLOWED_SOLVE_YEARS = frozenset({2021, 2023, 2024, 2025})
VINTAGE_YEAR = 2020

FUEL_VARIANT_GAS_PATH = {
    "realized": "hindcast_realized",
    "asknown": "hindcast_asknown_aeo2021",
}


def _validate_window(start_year: int, end_year: int) -> None:
    """Enforce the rule-22 quarantine on the requested window."""
    if start_year < 2021:
        raise SystemExit(
            "hindcast start-year must be >= 2021 (demand profiles start 2021)"
        )
    if end_year > 2025:
        raise SystemExit(
            "hindcast end-year must be <= 2025 (2026 is a rule-22 holdout — no solve/score)"
        )
    for y in range(start_year, end_year + 1):
        if y in HINDCAST_BRIDGE_YEARS:
            continue  # bridged: evolved, never solved
        if y not in ALLOWED_SOLVE_YEARS:
            raise SystemExit(f"year {y} is not an allowed hindcast solve year")


def build_config(
    iso: str,
    start_year: int,
    end_year: int,
    variant: str,
    energy_only_floor: bool = False,
    entry_lookahead_reprice: bool = False,
    staged_oversupply_thinning: bool = False,
    staged_thinning_max_gw_per_year: float = 3.0,
    limited_foresight_dispatch: bool = False,
    legacy_renewable_credit: bool = False,
) -> ScenarioConfig:
    """Assemble the hindcast ScenarioConfig (forecast machinery, vintage init).

    The hindcast must exercise the capacity screens under the **same price
    formation the forecast uses** for the ISO — otherwise it validates a
    dispatch/margin signal the production path never sees. The ``s2`` run
    (`docs/hindcast-reports/ercot-2021-2025-realized-s2-2026-07-05.md` root
    cause 1) left ``scarcity_pricing_enabled`` at its ``False`` model default,
    so the ERCOT screens priced against bare perfect-foresight LP duals
    (mean ~$25/MWh, no ORDC overlay, no reserve-price signal) — the exact
    revenue understatement the Stage-2 revenue-side fix targets was switched
    off in the harness, producing a 9.7 GW over-retirement (94 % false). We
    adopt each ISO's production scarcity footing here as the harness default:
    setting the master switch ``scarcity_pricing_enabled=True`` engages every
    ISO's ``ISOConfig.default_scenario_overrides`` scarcity footing in
    ``run_scenario_iso`` — for ERCOT the published ORDC overlay
    (``scarcity_price_overlay=True``, the forecast's default cell), for PJM
    the capacity-market footing (no ORDC overlay; RPM net-CONE × UCAP already
    enters the screens via ``capacity_revenue_per_mw_yr``, so the master flag
    is a harmless no-op there). This is a **harness-config** choice, not a
    model-default change — the ScenarioConfig default stays ``False`` (rule 1:
    fix the price signal the screens see, do not tune the screens).

    ``energy_only_floor`` is the stage-5 s4 PROBE leg (fom-scarcity stage 5
    §4-§5), NOT a harness default: it sets
    ``market_design_retirement_floor=True`` so energy-only ERCOT runs without
    the retirement reliability floor (the s3 ledgers show the floor retaining
    10.7-26.0 GW/yr — with it off, exits can tighten a later year's LP and
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
        eia860_vintage_year=VINTAGE_YEAR,
        hindcast_fuel_variant=variant,
        gas_price_path=FUEL_VARIANT_GAS_PATH[variant],
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
        # G-31 first-wave corrective arms (PROBE, default-off). The G-30
        # lookahead only bites evolution waves 2+ because the first (largest)
        # coal wave is decided on the un-thinned over-supplied fleet's 2021 raw
        # dual (ORDC ≈ 0). These two attack that first-wave root cause from the
        # LP regime, not a floor/adder:
        #   staged_oversupply_thinning — cap each fuel class's exits to
        #     staged_thinning_max_gw_per_year GW/yr so the coal wave spreads into
        #     later years whose thinned fleet the LP can price as scarce; the
        #     retain/exit call stays the screen's (rule 11).
        #   limited_foresight_dispatch — deny the in-year LP perfect annual
        #     storage/hydro foresight so peak/net-load-ramp hours tighten and the
        #     ORDC overlay prices scarcity in-year once the fleet has thinned.
        # Both zero fitted parameters; see scenarios.py field docstrings.
        staged_oversupply_thinning=staged_oversupply_thinning,
        staged_thinning_max_gw_per_year=staged_thinning_max_gw_per_year,
        limited_foresight_dispatch=limited_foresight_dispatch,
        # CR-3.1 frozen-penetration byte-compat arm: pin the VRE adequacy
        # credits back to the pre-curve flat constants for the BEFORE leg of
        # the before/after diagnostic. Default (False) keeps the model
        # default renewable_elcc_curves=True — the AFTER leg.
        renewable_elcc_curves=not legacy_renewable_credit,
    )


def assert_pipeline_from_vintage(iso: str, out_dir: Path, ledgers: dict) -> list[str]:
    """Leakage guard (plan §1.2.4): planned units trace to the 2020 vintage.

    Every ``source == "planned"`` addition in the ledgers must correspond to a
    unit in the 2020-vintage proposed sheet — a forecast started in 2020 cannot
    know a pipeline unit that first appeared in a later vintage. Returns the
    list of violations (empty when clean).
    """
    import pandas as pd

    proposed_path = (
        Path("data/raw/eia-860")
        / f"vintage_{VINTAGE_YEAR}"
        / "eia860_generator_proposed.parquet"
    )
    if not proposed_path.exists():
        return [f"2020-vintage proposed sheet missing: {proposed_path}"]
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
                violations.append(f"{year}: planned {eia_id} absent from 2020 vintage")
    return violations


def main(argv: list[str] | None = None) -> int:
    # Emit the runner's INFO logs (per-year ORDC scarcity adder, lookahead
    # pro-forma, retirement/entry waves) so a hindcast probe is reproducible
    # from its captured log — runner.main configures this, but the harness
    # calls run_scenario_iso directly and would otherwise stay silent.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default="ERCOT", help="ISO to hindcast.")
    parser.add_argument("--start-year", type=int, default=2021)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--fuel-variant", choices=["realized", "asknown"], default="realized"
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--energy-only-floor",
        action="store_true",
        help=(
            "Stage-5 s4 PROBE leg: disable the retirement reliability floor "
            "for energy-only ISOs (market_design_retirement_floor=True). "
            "Probe-only, never the harness default — see build_config."
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
            "Probe-only — see build_config."
        ),
    )
    parser.add_argument(
        "--staged-oversupply-thinning",
        action="store_true",
        help=(
            "G-31 corrective arm (PROBE): cap each fuel class's economic exits "
            "to --staged-thinning-max-gw-per-year GW/yr so a large single-year "
            "over-supply wave (e.g. the 14 GW coal first wave) spreads across "
            "years the LP regime can price as scarce. Rate cap, not a "
            "floor/adder — see build_config / scenarios.py."
        ),
    )
    parser.add_argument(
        "--staged-thinning-max-gw-per-year",
        type=float,
        default=3.0,
        help="Per-fuel-class exit budget (GW/yr) for --staged-oversupply-thinning.",
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
    args = parser.parse_args(argv)

    iso = args.iso.upper()
    _validate_window(args.start_year, args.end_year)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    config = build_config(
        iso,
        args.start_year,
        args.end_year,
        args.fuel_variant,
        energy_only_floor=args.energy_only_floor,
        entry_lookahead_reprice=args.entry_lookahead_reprice,
        staged_oversupply_thinning=args.staged_oversupply_thinning,
        staged_thinning_max_gw_per_year=args.staged_thinning_max_gw_per_year,
        limited_foresight_dispatch=args.limited_foresight_dispatch,
        legacy_renewable_credit=args.legacy_renewable_credit,
    )

    # Bundle lives under results/hindcast/<run>/ (plan §1.5) — deliberately
    # OUTSIDE the backcast registry, so audit_keepers / legitimacy_diagnostics
    # never see a bundle with a 2021 solve year. Point the cache root here.
    cachemod.CACHE_ROOT = args.out_dir
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(
        f"[hindcast] {iso} {args.start_year}-{args.end_year} variant={args.fuel_variant} "
        f"gas={config.gas_price_path} vintage={VINTAGE_YEAR}"
    )
    key = run_scenario_iso(config, iso)
    bundle = args.out_dir / iso / key
    ledgers = load_ledgers_for_run(bundle)

    violations = assert_pipeline_from_vintage(iso, args.out_dir, ledgers)
    if violations:
        print("[hindcast] LEAKAGE GUARD violations:")
        for v in violations:
            print("  -", v)

    solved = sorted(y for y in ledgers if not ledgers[y].get("bridge"))
    bridged = sorted(y for y in ledgers if ledgers[y].get("bridge"))
    meta = {
        "iso": iso,
        "variant": args.fuel_variant,
        "energy_only_floor": bool(args.energy_only_floor),
        "entry_lookahead_reprice": bool(args.entry_lookahead_reprice),
        "staged_oversupply_thinning": bool(args.staged_oversupply_thinning),
        "staged_thinning_max_gw_per_year": float(args.staged_thinning_max_gw_per_year),
        "limited_foresight_dispatch": bool(args.limited_foresight_dispatch),
        "renewable_elcc_curves": bool(config.renewable_elcc_curves),
        "gas_price_path": config.gas_price_path,
        "vintage_year": VINTAGE_YEAR,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "cache_key": key,
        "bundle": str(bundle),
        "solved_years": solved,
        "bridged_years": bridged,
        "leakage_violations": violations,
        "started_utc": started,
    }
    (args.out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    config.to_yaml_full(args.out_dir / "run_config.yaml")
    print(f"[hindcast] done. solved {solved}, bridged {bridged}")
    print(f"[hindcast] bundle: {bundle}")
    print(f"[hindcast] meta:   {args.out_dir / 'meta.json'}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
