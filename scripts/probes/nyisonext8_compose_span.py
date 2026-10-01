"""NYISO-NEXT-8 leg acceptance + span composition (zero LP).

The arm is the incumbent keeper's recipe (``2026-09-27-nyisonext6-li-cap-span``)
replayed unchanged at the pin, where the only LIVE change is the HQ-deduped NYISO
import ladder (``docs/records/nyiso/PRECOMMIT-nyiso-next8-hq-dedupe-2026-09-27.md``). Checks:

* S0 -- every leg solved at the pin (``--pin``);
* S1 -- the keeper's flags (NEXT-6's expected set) and its offer-curve block;
* S2 -- the keeper's CAMPD outage extract and thermal-tranche bytes;
* S5 -- the keeper's armed footprint lines and NEXT-6's LI-clip G-1 line
  (unchanged: the ladder does not touch the seam envelope).

Usage::

    python3 scripts/probes/nyisonext8_compose_span.py --pin <sha> --check-only \\
        --legs results/calibration/nyisonext8_{2021,2022,2023,2024,2025}
    python3 scripts/probes/nyisonext8_compose_span.py --pin <sha> \\
        --legs results/calibration/nyisonext8_{2022,2023,2024,2025} \\
        --out results/calibration/nyisonext8_span
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes import nyisonext3_compose_span as n3  # noqa: E402
from scripts.probes import nyisonext6_compose_span as n6  # noqa: E402
from scripts.probes import nyisonext_compose_span as prev  # noqa: E402
from scripts.probes import rnyiso_compose_span as base  # noqa: E402


def main() -> None:
    """Check every leg, then compose the span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pin", required=True, help="the arm commit SHA (40 hex)")
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    legs = [Path(x) for x in args.legs]
    base.PIN = args.pin
    base.EXPECTED = n6.EXPECTED
    base.INPUT_SHA = n3.INPUT_SHA
    base.KEEPER = _REPO / "results" / "calibration" / "nyisonext6_span"
    base.check_legs(legs)
    prev.check_footprint(legs)
    n6.check_g1(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    base._compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
