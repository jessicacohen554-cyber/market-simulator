"""SOCO-92 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-87 keeper recipe + ``hydro_min_flow_floor`` reconciled under the keeper's
``hydro_ror_split`` (PRECOMMIT-soco-92 §1), one shard per year (rule 36). Runs
soco-87's inherited assertion chain (which carries soco-82/83/85's), then
PRECOMMIT-soco-92 §5:

1. :func:`assert_floor_arm` — every leg's run_config arms ``hydro_min_flow_floor``
   AND ``hydro_ror_split`` (the reconciled form; the floor alone is soco-hydro-4's
   ARM 1, which this lane does not test).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/soco92_compose_span.py --check-only \\
        --pinned-sha <sha> --legs results/calibration/soco92_{2019,...,2025}
    PYTHONPATH=.:src:scripts python3 scripts/probes/soco92_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco92_{2019,...,2025} --out results/calibration/soco92_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
for p in (_REPO, _REPO / "src", _REPO / "scripts", _REPO / "scripts" / "probes"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from scripts.probes import soco82_compose_span as s82  # noqa: E402
from scripts.probes import soco83_compose_span as s83  # noqa: E402
from scripts.probes import soco85_compose_span as s85  # noqa: E402
from scripts.probes import soco87_compose_span as s87  # noqa: E402

ROOT = s82.ROOT
FLAGS = ("hydro_min_flow_floor", "hydro_ror_split")

# soco87's import already appended gas_hh_monthly_shape; the census build also
# carries the floor so every leg is checked against the armed build.
s82.census.RECIPE_SETS = tuple(s82.census.RECIPE_SETS) + ("hydro_min_flow_floor",)


def assert_floor_arm(legs: list[Path]) -> None:
    """Each leg's recorded scenario_config arms the reconciled floor."""
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text()).get(
            "scenario_config", {}
        )
        for f in FLAGS:
            if sc.get(f) is not True:
                raise SystemExit(f"{leg.name}: {f} not armed")
        print(f"  {leg.name}: {' + '.join(FLAGS)} true")


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--pinned-sha", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true", help="assert, do not compose")
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    s82.assert_lane(legs)
    s82.assert_repairs(legs, a.pinned_sha)
    s82.assert_precod_arm(legs)
    s82.assert_basis_arm(legs)
    s82.assert_measured_arm(legs)
    s82.assert_tranche_artifact(legs)
    s82.assert_mustrun_set(legs)
    s82.assert_coal_hr_artifact(legs)
    s82.assert_coal_census(legs)
    s82.assert_basis_table(legs)
    s82.assert_identity_arm(legs)
    s82.assert_two_sided_arm(legs)
    s82.assert_dark_artifact()
    s82.assert_input_census(legs)
    s83.assert_oom_artifact()
    s83.assert_oom_arm(legs)
    s85.assert_hh_artifact()
    s85.assert_shape_arm(legs)
    s87.assert_hh_monthly_artifact()
    s87.assert_monthly_arm(legs)
    assert_floor_arm(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    s82._compose(legs, out, True)


if __name__ == "__main__":
    main()
