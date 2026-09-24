"""R-SOCO (ZERO LP): compose the per-year corrected-input legs into one span bundle.

The keeper ``2026-09-24-soco61-dark-unit`` replayed per year (rule 36) with the F1/F2
backcast-input corrections (``docs/handoffs/r-soco/PRECOMMIT-r-soco-2026-09-24.md`` §5).
Every inherited posture, the band identity, the dispatch parquet and the MER column are
asserted by :func:`soco55_compose_span.compose` (reused, not forked). This module adds
the lane's own posture, read from each leg's RESOLVED ``scenario_config`` and its
``resolved_inputs``: every F1 flag and outage family on, the ``-perunitdark-`` std
extract, and the year-matched EIA-860 vintage.

Usage::

    python3 scripts/probes/rsoco_compose_span.py --check-only \\
        --legs results/calibration/rsoco_{2023,2024,2025}
    python3 scripts/probes/rsoco_compose_span.py \\
        --legs results/calibration/rsoco_{2023,2024,2025} \\
        --out  results/calibration/rsoco_corrected_inputs_span
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

#: The lane's resolved posture (PRECOMMIT §5): F1 flips declared + the three F2
#: outage families, on top of the keeper's inherited measured / dark-unit fields.
LANE_TRUE = (
    "eia860_vintage_tracks_solve_year",
    "measured_chp_heat_rates",
    "unit_outage_short_windows",
    "unit_outage_short_windows_gas",
    "unit_partial_outage_windows",
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "egrid_family_heat_rates",
    "campd_dark_unit_year_windows",
    "gas_basis_differential_measured_by_year",
)
STD_EXTRACT = "data/raw/campd-unit-outages-perunitdark-SOCO.csv"


def assert_lane(legs: list[Path]) -> None:
    """Fail loud unless every leg solved this lane's recipe."""
    for leg in legs:
        cfg = json.loads((leg / "run_config.json").read_text())
        sc = cfg.get("scenario_config") or {}
        off = [f for f in LANE_TRUE if sc.get(f) is not True]
        if off:
            raise SystemExit(f"{leg.name}: not True in resolved scenario_config: {off}")
        ri = cfg.get("resolved_inputs") or {}
        path = (ri.get("campd_unit_outages") or {}).get("path")
        if path != STD_EXTRACT:
            raise SystemExit(f"{leg.name}: std extract {path!r}, expected {STD_EXTRACT}")
        for k in ("offer_curve_overrides", "offer_curve_deltas"):
            if (cfg.get("calibration_flags") or {}).get(k) not in (None, {}):
                raise SystemExit(f"{leg.name}: {k} not empty")
        print(f"  {leg.name}: lane posture OK; std extract {path}; "
              f"outage inputs {sorted(k for k in ri if 'outage' in k)}")


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true", help="assert, do not compose")
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    assert_lane(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
