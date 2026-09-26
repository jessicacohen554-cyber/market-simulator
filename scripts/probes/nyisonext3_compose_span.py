"""NYISO-NEXT-3 leg acceptance + span composition (zero LP).

The arm is the incumbent keeper's recipe with ZERO ``scenario_config`` changes, solved at a
pin carrying (a) the bin builder's committed-share read on the full CAMPD artifact selector
pair (``campd_bins.fleet_to_bins`` now passes ``merit_guard``; rule 19) and (b) the
``-perunitmerit-`` tranche artifact re-derived on the current outage-extract basis (rule 23).
Checks, per ``docs/PRECOMMIT-nyiso-next3-tranche-basis-2026-09-26.md`` §6:

* S0 -- every leg solved at the PRECOMMIT pin (``--pin``), not dirty;
* S1 -- the keeper's flags exactly (no new field) and the keeper's offer-curve block;
* S2 -- ``thermal_tranches`` resolves to the RE-DERIVED artifact's sha256 and
  ``campd_unit_outages`` to the keeper's hour-grain extract (unchanged);
* S5 -- the solve log carries both of the keeper's armed footprint lines.

Usage::

    python3 scripts/probes/nyisonext3_compose_span.py --pin <sha> --check-only \\
        --legs results/calibration/nyisonext3_{2021,2022,2023,2024,2025}
    python3 scripts/probes/nyisonext3_compose_span.py --pin <sha> \\
        --legs results/calibration/nyisonext3_{2022,2023,2024,2025} \\
        --out results/calibration/nyisonext3_span
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes import nyisonext_compose_span as prev  # noqa: E402
from scripts.probes import rnyiso_compose_span as base  # noqa: E402

#: S2 -- the re-derived tranche artifact and the keeper's unchanged hour-grain extract.
INPUT_SHA = {
    "campd_unit_outages": "986d1d43bf307a5d6f0b6a1cbb9d937d5344de0e1e8ce6feb27b6e9783232526",
    "thermal_tranches": "38cc256b288eded42b45b2b534a87aedd1ebf8d77cf4eb2b380b370661127414",
}


def main() -> None:
    """Check every leg, then compose the span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pin", required=True, help="the PRECOMMIT commit SHA (40 hex)")
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    legs = [Path(x) for x in args.legs]
    base.PIN = args.pin
    base.EXPECTED = prev.EXPECTED  # no new field
    base.INPUT_SHA = INPUT_SHA
    base.KEEPER = _REPO / "results" / "calibration" / "nyisonext2_span"
    base.check_legs(legs)
    prev.check_footprint(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    base._compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
