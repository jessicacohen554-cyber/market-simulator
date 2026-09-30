"""SOCO-96 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-93 keeper recipe + ``dual_fuel_measured_oil_burn`` (PRECOMMIT-soco-96 §1), one
shard per year (rule 36). Runs soco-93's full assertion chain (which carries soco-82/83/85/
87/92's), then PRECOMMIT-soco-96 §5:

1. :func:`assert_oil_burn_artifact` — the measured oil-burn artifact hashes to the PRECOMMIT
   value.
2. :func:`assert_oil_burn_arm` — every leg's run_config arms ``dual_fuel_measured_oil_burn``
   and does not arm ``dual_fuel_switching``.

The input census rebuilds each leg's offers with the new field in its recipe, so it checks
the arm's own measured-mix offers against the solved ones.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/soco96_compose_span.py --check-only \\
        --pinned-sha <sha> --legs results/calibration/soco96_{2019,...,2025}
    PYTHONPATH=.:src:scripts python3 scripts/probes/soco96_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco96_{2019,...,2025} --out results/calibration/soco96_span
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
from scripts.probes import soco93_compose_span as s93  # noqa: E402

ROOT = s82.ROOT
OIL_BURN = ROOT / "data/raw/_processed-legacy/campd_measured_oil_burn_days_SOCO.csv"
#: PRECOMMIT-soco-96 §5.
OIL_BURN_SHA256 = "7ea8096be5257e817d669245ee5c84fca10bd97cc54c5fd0f9490f8328409edf"

# soco93's import appended the pondage row; the measured mix is priced before the
# fleet_only exit, so the census build carries it and checks the arm's own offers.
s82.census.RECIPE_SETS = tuple(s82.census.RECIPE_SETS) + (
    "dual_fuel_measured_oil_burn",
)


def assert_oil_burn_artifact() -> None:
    """The committed SOCO measured oil-burn artifact is the PRECOMMIT's."""
    got = hashlib.sha256(OIL_BURN.read_bytes()).hexdigest()
    if got != OIL_BURN_SHA256:
        raise SystemExit(f"{OIL_BURN}: sha256 {got} != {OIL_BURN_SHA256}")
    print(f"  oil-burn artifact sha256 OK ({got[:12]})")


def assert_oil_burn_arm(legs: list[Path]) -> None:
    """Each leg arms dual_fuel_measured_oil_burn and not the parity switch."""
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text()).get(
            "scenario_config", {}
        )
        if sc.get("dual_fuel_measured_oil_burn") is not True:
            raise SystemExit(f"{leg.name}: dual_fuel_measured_oil_burn not armed")
        if sc.get("dual_fuel_switching"):
            raise SystemExit(f"{leg.name}: dual_fuel_switching armed beside it")
        print(
            f"  {leg.name}: dual_fuel_measured_oil_burn true; dual_fuel_switching off"
        )


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
    s93.assert_pondage_artifact()
    s93.assert_pondage_arm(legs)
    assert_oil_burn_artifact()
    assert_oil_burn_arm(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    s82._compose(legs, out, True)


if __name__ == "__main__":
    main()
