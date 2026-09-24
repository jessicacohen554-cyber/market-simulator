"""soco-61 (ZERO LP): compose the dark-unit-year per-year legs into one span bundle.

The keeper ``2026-09-23-soco60-boundary-span`` plus ONE delta:
``campd_dark_unit_year_windows=True`` (a ``ScenarioConfig`` field, routed by
``replay_keeper --set`` through ``prb_overrides``), which selects the
``-perunitdark-`` SOCO outage extract -- the ``-perunit-`` extract the keeper
reads, re-derived byte-identically, plus ONE full-year 2024 window for
Lindsay Hill (55271) CT3. Every inherited posture, the classifier snapshot and
the 185-row solve surface are asserted by :func:`soco60b_compose_span.assert_delta`
in its keeper mode (``"b"``) -- reused, not forked. This module adds the delta,
checked on BOTH the resolved config and the outage extract the leg actually read
(``run_config.json`` ``resolved_inputs.campd_unit_outages.path``), in both
directions.

Usage::

    python3 scripts/probes/soco61_compose_span.py --expect-arm false --check-only \\
        --legs results/calibration/soco60_armB_{2023,2024,2025}
    python3 scripts/probes/soco61_compose_span.py --expect-arm true \\
        --legs results/calibration/soco61_arm_{2023,2024,2025} \\
        --out  results/calibration/soco61_dark_unit_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes.soco55_compose_span import ROOT, compose as _compose  # noqa: E402
from scripts.probes.soco60b_compose_span import assert_delta as _assert_keeper  # noqa: E402

FIELD = "campd_dark_unit_year_windows"
EXTRACT = {
    True: "data/raw/campd-unit-outages-perunitdark-SOCO.csv",
    False: "data/raw/campd-unit-outages-perunit-SOCO.csv",
}
INHERITED_MEASURED_BASIS = True  # SOCO-55, positional in soco55 compose


def assert_delta(legs: list[Path], expect_arm: bool) -> None:
    """Fail loud unless every leg is the keeper posture plus exactly this lane's side."""
    _assert_keeper(legs, "b")
    for leg in legs:
        cfg = json.loads((leg / "run_config.json").read_text())
        armed = bool((cfg.get("scenario_config") or {}).get(FIELD))
        path = ((cfg.get("resolved_inputs") or {}).get("campd_unit_outages") or {}).get("path")
        if armed != expect_arm:
            raise SystemExit(f"{leg.name}: {FIELD}={armed}, expected {expect_arm}")
        if path != EXTRACT[expect_arm]:
            raise SystemExit(f"{leg.name}: outage extract read {path!r}, expected {EXTRACT[expect_arm]}")
        print(f"  {leg.name}: {FIELD}={armed}, extract {path}")


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--expect-arm", required=True, choices=("true", "false"))
    ap.add_argument("--check-only", action="store_true", help="assert, do not compose")
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    assert_delta(legs, a.expect_arm == "true")
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, INHERITED_MEASURED_BASIS)


if __name__ == "__main__":
    main()
