"""NYISO-STGAS-2023 (ZERO LP): accept the year-isolated legs, then compose 2022-2025.

Reuses :mod:`scripts.probes.rnyiso_compose_span` (its S0-S2 checks and the
NYISO ``nyiso238_compose_span`` composition) and re-points them at this lane:

* S0 -- every leg solved at the PRECOMMIT pin
  (``docs/PRECOMMIT-nyiso-stgas-2023-ldc-leg-2026-09-25.md``);
* S1 -- the keeper's posture PLUS ``nyiso_ldc_generator_delivered_gas`` and
  ``nyiso_dynamic_reserve_requirements`` true; the offer-curve block equals the
  keeper's after the bare-``COAL`` fold (nothing is re-tuned, rule 1(c));
* S2 -- the keeper's CAMPD outage extract and thermal-tranche bytes;
* S5 -- the solve log carries the armed footprint line (42 rows, 6 plants).

Usage::

    python3 scripts/probes/nyisostg_compose_span.py --check-only \\
        --legs results/calibration/nyisostg_{2021,2022,2023,2024,2025}
    python3 scripts/probes/nyisostg_compose_span.py \\
        --legs results/calibration/nyisostg_{2022,2023,2024,2025} \\
        --out results/calibration/nyisostg_span
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes import rnyiso_compose_span as base  # noqa: E402

#: docs/PRECOMMIT-nyiso-stgas-2023-ldc-leg-2026-09-25.md commit SHA.
PIN = "54ac9e1a509c0cad01aadcb9d7583535fd27d883"
EXPECTED = base.EXPECTED + (
    ("nyiso_ldc_generator_delivered_gas", True),
    ("nyiso_dynamic_reserve_requirements", True),
)
FOOTPRINT = "42 gas unit rows at plants [2490, 2500, 8906, 55375, 56196, 57664]"


def check_footprint(legs: list[Path]) -> None:
    """S5: each leg's committed solve log carries the armed footprint line."""
    bad = []
    for leg in legs:
        log = leg / "solve.log"
        text = log.read_text(errors="replace") if log.exists() else ""
        ok = "NYISO LDC generator delivery leg" in text and FOOTPRINT in text
        print(f"  {leg.name}: S5 {'OK' if ok else 'MISSING footprint line'}")
        if not ok:
            bad.append(leg.name)
    if bad:
        raise SystemExit(f"legs {bad} fail S5; refusing to compose")


def main() -> None:
    """Check every leg, then compose the span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    legs = [Path(x) for x in args.legs]
    base.PIN = PIN
    base.EXPECTED = EXPECTED
    base.check_legs(legs)
    check_footprint(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    base._compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
