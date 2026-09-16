"""Regenerate the curated clean tree from raw.

The ``data/clean`` tree is gitignored (derived and disposable), so it must be
rebuilt from ``data/raw`` before the model — or CI — can read it through
``scripts.lib.clean_io.read_clean``. This is the single entrypoint that runs
the per-datatype curation scripts (``scripts/data/curate_<datatype>.py``); each of
those writes through ``clean_io.write_clean`` and self-validates.

Usage
-----
    python scripts/regenerate_clean.py                 # all datatypes
    python scripts/regenerate_clean.py lmp load        # a subset
    python scripts/regenerate_clean.py --list          # show known datatypes

Each curation script owns its own raw inputs and clean outputs, so they are
independent; a failure in one is reported but does not stop the others.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Datatypes in the standardization contract (one curate script each). Kept in
# sync with data/dictionary/schema/*.schema.yaml.
DATATYPES: tuple[str, ...] = (
    "lmp",
    "load",
    "demand-profile",
    "ancillary-services",
    "generation",
    "renewables",
    "emissions",
    "emissions-unit-annual",
    "outages",
    "validation",
    "fleet",
    "fuel-prices",
    "reference",
    "egrid",
    "unit-outage-events",
    "partial-outages",
    "capacity-deliverability",
    "confirmed-retirements",
    "transmission-expansion",
    "nuclear-license-status",
    "gtc-limits",
    "transfer-interface-limits",
    "winter-fuel-inventory",
    "rggi-co2-budgets",
    "carb-cap-schedule",
    "chp-btm-share",
    "ramp-capability",
    "nyiso-downstate-gas",
    "ercot-wtx-congestion",
    "nyiso-renewable-curtailment",
    "coal-basin-price",
    "coal-mining-ppi",
    # miso-258 (2026-09-14): plant-level monthly ending coal stocks, the
    # measured fuel-inventory state coal has never carried.
    "coal-stocks",
    # miso-259 (2026-09-14): the DELIVERY half of that state — plant-level
    # monthly coal receipts (EIA-923 Page 5). Supersedes the incomplete
    # _processed-legacy/eia923_monthly_fuel_costs.parquet extract for coal
    # tonnage (50/67 MISO coal plants, 17-21% understated).
    "coal-receipts",
    "nyiso-reserve-requirements",
    "nyiso-interface-flows",
    "nyiso-som-hub-fuel-annual",
    "reserve-requirements",
    "som-competitive-conduct",
    "storage-as-awards",
    "capacity-market-demand-curve",
    "capacity-market-auction-price",
    # capx D31 (2026-09-02): auction supply-side quantity accounting (MISO PRA
    # offered/cleared by category + requirement ledger).
    "capacity-market-auction-supply",
    "capacity-market-elcc",
    "capacity-market-avoidable-cost-rate",
    "transfer-constraint-binding",
    "lmp-components",
    "maxgen-events",
    "dam-public-bids",
    "benchmark-corridor",
    "hydro-plant-modes",
    # Both have had a curate_*.py since their intake but were never listed
    # here, so `regenerate_clean.py` (no args = "all") silently skipped them.
    # Registered 2026-07-31 (FFR-PB) while extending nrel-atb with its
    # version axis — the intake contract's step 5.
    "nrel-atb",
    "ira-credit-parameters",
    "miso-m2m-flowgates",
    # caiso-226: SoCalGas OFO/EFO declaration ledgers (gas-deliverability
    # events). Intake-only -- no mechanism consumes it yet.
    "gas-ofo-events",
    # caiso-227: measured hourly pumped-storage plant operations (Helms FLA
    # App B1, FERC P-2735). Intake-only -- no mechanism consumes it yet.
    "ps-water-state",
    # caiso-245: CAISO RA import capability HOLDINGS by LSE x intertie branch
    # group (the published annual allocation results). Intake-only -- the
    # pre-registered firm-block re-split arm's stop rule fired.
    "ra-import-allocations",
    # SCN-LOAD (owner ruling S4, card D-4): each ISO's PUBLISHED long-term load
    # forecast -- annual energy and seasonal peak by scenario, plus the
    # published data-centre / large-load, EV and building-electrification
    # decompositions. Consumed by constants.DEMAND_GROWTH_RATES,
    # DATACENTER_ADDITIONS_MW, DATACENTER_ZONE_SHARE and ELECTRIFICATION_LAYERS.
    "load-forecast",
)

SCRIPTS_DIR = Path(__file__).resolve().parent


def _script_for(datatype: str) -> Path:
    """Path of the curation script for a datatype (dashes -> underscores)."""
    return SCRIPTS_DIR / "data" / f"curate_{datatype.replace('-', '_')}.py"


def regenerate(datatypes: list[str]) -> int:
    """Run each datatype's curation script; return the count that failed."""
    failed = 0
    for datatype in datatypes:
        script = _script_for(datatype)
        if not script.is_file():
            print(f"[skip] {datatype}: no {script.name}", file=sys.stderr)
            failed += 1
            continue
        print(f"[run ] {datatype}: {script.name}")
        # Run with the repo root AND src/ on PYTHONPATH. Invoking a script by
        # path puts its own dir (scripts/) on sys.path, not the repo root, so
        # both hops of the import chain need help:
        #   repo_root  -> the curation scripts' `import scripts.lib.clean_io`
        #   repo_root/src -> clean_io's own `from market_sim.config import paths`
        # The src/ hop was missing, so on a container without an editable
        # install every curation script died with
        # `ModuleNotFoundError: No module named 'market_sim'` raised from INSIDE
        # clean_io — a traceback that names neither PYTHONPATH nor the caller.
        # Three separate NYISO solve shards mis-diagnosed that as an OOM or a
        # missing write permission and burned their budgets (nyiso-228 went on
        # to record capacity-deliverability as INERT on the strength of it).
        # Adding a path can only widen resolution, never change which module an
        # already-working environment picks: an editable install still wins
        # because site-packages precedes PYTHONPATH entries only when the entry
        # is absent, and here both point at the same tree. (nyiso-230)
        repo_root = SCRIPTS_DIR.parent
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [
                str(repo_root),
                str(repo_root / "src"),
                *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []),
            ]
        )
        result = subprocess.run([sys.executable, str(script)], cwd=repo_root, env=env)
        if result.returncode != 0:
            print(f"[FAIL] {datatype}: exit {result.returncode}", file=sys.stderr)
            failed += 1
        else:
            print(f"[ ok ] {datatype}")
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "datatypes",
        nargs="*",
        help=f"datatypes to regenerate (default: all). Known: {', '.join(DATATYPES)}",
    )
    parser.add_argument(
        "--list", action="store_true", help="list known datatypes and exit"
    )
    args = parser.parse_args(argv)

    if args.list:
        print("\n".join(DATATYPES))
        return 0

    selected = args.datatypes or list(DATATYPES)
    unknown = [d for d in selected if d not in DATATYPES]
    if unknown:
        parser.error(f"unknown datatype(s): {', '.join(unknown)}")

    failed = regenerate(selected)
    if failed:
        print(f"\n{failed}/{len(selected)} datatype(s) failed", file=sys.stderr)
        return 1
    print(f"\nregenerated {len(selected)} datatype(s) into data/clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
