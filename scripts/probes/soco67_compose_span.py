"""soco-67 (ZERO LP): verify the seven per-year legs and compose them into one span bundle.

PRECOMMIT: ``docs/handoffs/r-soco/PRECOMMIT-soco-67-2026-09-25.md`` §3/§5. Each leg is
the R-SOCO-B2 keeper recipe plus ``unit_outage_precod_clip=true``, one shard per year
(rule 36). Checks run BEFORE anything is written:

1. :func:`scripts.probes.rsoco_compose_span.assert_lane` and
   :func:`scripts.probes.rsocob_compose_span.assert_repairs` — the inherited R-SOCO
   posture and the four boundary repairs, reused not forked;
2. :func:`assert_arm` — ``unit_outage_precod_clip`` True in every leg's resolved
   ``scenario_config``;
3. :func:`scripts.probes.soco55_compose_span.compose` — posture drift, band identity,
   dispatch present, identical solve-surface fingerprint and dependency set.

Usage::

    python3 scripts/probes/soco67_compose_span.py --check-only --pinned-sha <sha> \\
        --legs results/calibration/soco67_{2019,2020,2021,2022,2023,2024,2025}
    python3 scripts/probes/soco67_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco67_{2019,...,2025} --out results/calibration/soco67_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes.rsoco_compose_span import assert_lane  # noqa: E402
from scripts.probes.rsocob_compose_span import assert_repairs  # noqa: E402
from scripts.probes.soco55_compose_span import ROOT, compose as _compose  # noqa: E402

ARM_FIELD = "unit_outage_precod_clip"


def assert_arm(legs: list[Path]) -> None:
    """Fail loud unless every leg solved with the soco-67 arm field True."""
    for leg in legs:
        sc = (
            json.loads((leg / "run_config.json").read_text()).get("scenario_config")
            or {}
        )
        if sc.get(ARM_FIELD) is not True:
            raise SystemExit(f"{leg.name}: {ARM_FIELD} is not True in scenario_config")
        print(f"  {leg.name}: {ARM_FIELD} True")


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--pinned-sha", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true", help="assert, do not compose")
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    assert_lane(legs)
    assert_repairs(legs, a.pinned_sha)
    assert_arm(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
