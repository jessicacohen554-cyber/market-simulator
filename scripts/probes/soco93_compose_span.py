"""SOCO-93 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-92 keeper recipe + ``hydro_pondage_bound`` (PRECOMMIT-soco-93 §1), one shard per
year (rule 36). Runs soco-92's full assertion chain (which carries soco-82/83/85/87's), then
PRECOMMIT-soco-93 §5:

1. :func:`assert_pondage_artifact` — ``data/raw/soco-hydro/soco_hydro_pondage.csv`` hashes to
   the PRECOMMIT value.
2. :func:`assert_pondage_arm` — every leg's run_config arms ``hydro_pondage_bound`` beside
   the reconciled floor, and no other hydro family.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/soco93_compose_span.py --check-only \\
        --pinned-sha <sha> --legs results/calibration/soco93_{2019,...,2025}
    PYTHONPATH=.:src:scripts python3 scripts/probes/soco93_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco93_{2019,...,2025} --out results/calibration/soco93_span
"""

from __future__ import annotations

import argparse
import hashlib
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
from scripts.probes import soco92_compose_span as s92  # noqa: E402

ROOT = s82.ROOT
PONDAGE = ROOT / "data/raw/soco-hydro/soco_hydro_pondage.csv"
#: PRECOMMIT-soco-93 §5.
PONDAGE_SHA256 = "abb10f83ef770fd4f36424f1db4a31d30d12a9915d2fbc9a41e45baf371b93fa"
OFF = (
    "hydro_cascade_coupling",
    "hydro_dispatch_envelope",
    "hydro_budget_period_by_instrument",
)

# soco92's import already appended the floor; the pondage row is built after the
# fleet_only exit, so the census build is unchanged by it (recorded for honesty).
s82.census.RECIPE_SETS = tuple(s82.census.RECIPE_SETS) + ("hydro_pondage_bound",)


def assert_pondage_artifact() -> None:
    """The committed SOCO pondage artifact is the PRECOMMIT's."""
    got = hashlib.sha256(PONDAGE.read_bytes()).hexdigest()
    if got != PONDAGE_SHA256:
        raise SystemExit(f"{PONDAGE}: sha256 {got} != {PONDAGE_SHA256}")
    print(f"  pondage artifact sha256 OK ({got[:12]})")


def assert_pondage_arm(legs: list[Path]) -> None:
    """Each leg arms hydro_pondage_bound and no other hydro family beside the floor."""
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text()).get(
            "scenario_config", {}
        )
        if sc.get("hydro_pondage_bound") is not True:
            raise SystemExit(f"{leg.name}: hydro_pondage_bound not armed")
        for f in OFF:
            if sc.get(f):
                raise SystemExit(f"{leg.name}: {f} armed beside the pondage row")
        print(f"  {leg.name}: hydro_pondage_bound true; {', '.join(OFF)} off")


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
    s92.assert_floor_arm(legs)
    assert_pondage_artifact()
    assert_pondage_arm(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    s82._compose(legs, out, True)


if __name__ == "__main__":
    main()
