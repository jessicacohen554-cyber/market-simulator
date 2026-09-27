"""NYISO-NEXT-6 leg acceptance + span composition (zero LP).

The arm is the incumbent keeper's recipe (``2026-09-26-nyisonext3-tranche-basis-span``)
plus ``nyiso_li_seam_posted_limit_cap``, solved year-isolated (rule 36). Checks, per
``docs/PRECOMMIT-nyiso-next5-li-tie-posted-limit-2026-09-27.md`` §6 and its §9 addendum:

* S0 -- every leg solved at the pin (``--pin``);
* S1 -- the keeper's flags plus ``nyiso_li_seam_posted_limit_cap`` true, and the
  keeper's offer-curve block (nothing re-tuned);
* S2 -- the keeper's CAMPD outage extract and thermal-tranche bytes (NEXT-3's);
* S5 -- the keeper's armed footprint lines, PLUS G-1: the clip's own log line
  carries exactly the addendum §9.2 hours and TWh for the leg's year.

Usage::

    python3 scripts/probes/nyisonext6_compose_span.py --pin <sha> --check-only \\
        --legs results/calibration/nyisonext6_{2021,2022,2023,2024,2025}
    python3 scripts/probes/nyisonext6_compose_span.py --pin <sha> \\
        --legs results/calibration/nyisonext6_{2022,2023,2024,2025} \\
        --out results/calibration/nyisonext6_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes import nyisonext3_compose_span as n3  # noqa: E402
from scripts.probes import nyisonext_compose_span as prev  # noqa: E402
from scripts.probes import rnyiso_compose_span as base  # noqa: E402

EXPECTED = prev.EXPECTED + (("nyiso_li_seam_posted_limit_cap", True),)

#: G-1 reference (PRECOMMIT §4; 2024 per the §9.2 addendum): (hours, TWh).
G1 = {
    2021: (860, "0.160"),
    2022: (1468, "0.343"),
    2023: (1688, "0.268"),
    2024: (969, "0.269"),
    2025: (1734, "0.308"),
}


def check_g1(legs: list[Path]) -> None:
    """G-1: each leg's log carries the clip line with the pre-registered footprint."""
    bad = []
    for leg in legs:
        rc = json.loads((leg / "run_config.json").read_text())
        years = [int(y) for y in (rc.get("years") or [])] or [
            int(leg.name.rsplit("_", 1)[-1])
        ]
        text = (leg / "solve.log").read_text(errors="replace")
        for y in years:
            h, twh = G1[y]
            line = (
                f"nyiso_li_seam_posted_limit_cap {y}: Long_Island import cap falls "
                f"in {h} hours, {twh} TWh removed"
            )
            ok = line in text
            print(f"  {leg.name}: G-1 {y} {'OK' if ok else 'MISSING: ' + line}")
            if not ok:
                bad.append(f"{leg.name}:{y}")
    if bad:
        raise SystemExit(f"legs {bad} fail G-1; refusing to compose")


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
    base.EXPECTED = EXPECTED
    base.INPUT_SHA = n3.INPUT_SHA
    base.KEEPER = _REPO / "results" / "calibration" / "nyisonext3_span"
    base.check_legs(legs)
    prev.check_footprint(legs)
    check_g1(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    base._compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
