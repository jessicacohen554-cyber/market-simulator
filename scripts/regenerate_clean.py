"""Regenerate the curated clean tree from raw.

The ``data/clean`` tree is gitignored (derived and disposable), so it must be
rebuilt from ``data/raw`` before the model — or CI — can read it through
``scripts.lib.clean_io.read_clean``. This is the single entrypoint that runs
the per-datatype curation scripts (``scripts/curate_<datatype>.py``); each of
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
    "nyiso-reserve-requirements",
    "nyiso-interface-flows",
    "nyiso-som-hub-fuel-annual",
    "reserve-requirements",
    "som-competitive-conduct",
    "storage-as-awards",
    "capacity-market-demand-curve",
    "capacity-market-auction-price",
    "capacity-market-elcc",
    "capacity-market-avoidable-cost-rate",
    "transfer-constraint-binding",
    "maxgen-events",
    "dam-public-bids",
    "benchmark-corridor",
)

SCRIPTS_DIR = Path(__file__).resolve().parent


def _script_for(datatype: str) -> Path:
    """Path of the curation script for a datatype (dashes -> underscores)."""
    return SCRIPTS_DIR / f"curate_{datatype.replace('-', '_')}.py"


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
        # Run with the repo root on PYTHONPATH so the curation scripts'
        # `import scripts.lib.clean_io` resolves. Invoking a script by path puts
        # its own dir (scripts/) on sys.path, not the repo root, so without this
        # the scripts that import the shared writer fail with ModuleNotFoundError.
        repo_root = SCRIPTS_DIR.parent
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(repo_root), env["PYTHONPATH"]]
            if env.get("PYTHONPATH")
            else [str(repo_root)]
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
