"""NYISO-NEXT (ZERO LP): accept the year-isolated legs, then compose 2022-2025.

Reuses :mod:`scripts.probes.rnyiso_compose_span` (its S0-S2 checks and the NYISO
``nyiso238_compose_span`` composition) and re-points them at this lane:

* S0 -- every leg solved at the PRECOMMIT pin
  (``docs/PRECOMMIT-nyiso-next-floor-layup-2026-09-25.md``), passed as ``--pin``
  because the pin is the commit that carries this file;
* S1 -- the keeper's posture (``nyiso_ldc_generator_delivered_gas`` and
  ``nyiso_dynamic_reserve_requirements`` true) PLUS
  ``reliability_floor_layup_window_mask`` true; the offer-curve block equals the
  keeper's after the bare-``COAL`` fold (nothing is re-tuned, rule 1(c));
* S2 -- the keeper's CAMPD outage extract and thermal-tranche bytes;
* S5 -- the solve log carries BOTH armed lines: the keeper's LDC footprint (42
  rows, 6 plants) and this lane's lay-up mask line.

Usage::

    python3 scripts/probes/nyisonext_compose_span.py --pin <sha> --check-only \\
        --legs results/calibration/nyisonext_{2021,2022,2023,2024,2025}
    python3 scripts/probes/nyisonext_compose_span.py --pin <sha> \\
        --legs results/calibration/nyisonext_{2022,2023,2024,2025} \\
        --out results/calibration/nyisonext_span
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes import rnyiso_compose_span as base  # noqa: E402

EXPECTED = base.EXPECTED + (
    ("nyiso_ldc_generator_delivered_gas", True),
    ("nyiso_dynamic_reserve_requirements", True),
    ("reliability_floor_layup_window_mask", True),
)
LDC_FOOTPRINT = "42 gas unit rows at plants [2490, 2500, 8906, 55375, 56196, 57664]"
MASK_LINE = "reliability_floor_layup_window_mask ARMED"


def check_footprint(legs: list[Path]) -> None:
    """S5: each leg's solve log carries both armed footprint lines."""
    bad = []
    for leg in legs:
        log = leg / "solve.log"
        text = log.read_text(errors="replace") if log.exists() else ""
        ok = LDC_FOOTPRINT in text and MASK_LINE in text
        print(f"  {leg.name}: S5 {'OK' if ok else 'MISSING footprint line(s)'}")
        if not ok:
            bad.append(leg.name)
    if bad:
        raise SystemExit(f"legs {bad} fail S5; refusing to compose")


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
    base.EXPECTED = EXPECTED
    # The incumbent keeper (rnyiso_span was pruned at the NYISO-STGAS-2023 promotion).
    base.KEEPER = _REPO / "results" / "calibration" / "nyisostg_span"
    base.check_legs(legs)
    check_footprint(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    base._compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
