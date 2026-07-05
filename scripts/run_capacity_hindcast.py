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
    iso: str, start_year: int, end_year: int, variant: str
) -> ScenarioConfig:
    """Assemble the hindcast ScenarioConfig (forecast machinery, vintage init)."""
    return ScenarioConfig(
        iso=iso,
        mode="forecast",
        hindcast=True,
        start_year=start_year,
        end_year=end_year,
        eia860_vintage_year=VINTAGE_YEAR,
        hindcast_fuel_variant=variant,
        gas_price_path=FUEL_VARIANT_GAS_PATH[variant],
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default="ERCOT", help="ISO to hindcast.")
    parser.add_argument("--start-year", type=int, default=2021)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--fuel-variant", choices=["realized", "asknown"], default="realized"
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    iso = args.iso.upper()
    _validate_window(args.start_year, args.end_year)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    config = build_config(iso, args.start_year, args.end_year, args.fuel_variant)

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
