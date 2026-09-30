"""SOCO-87 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-85 keeper recipe + ``gas_hh_monthly_shape`` (measured Henry Hub MONTHLY gas
shape; PRECOMMIT-soco-87 §1), one shard per year (rule 36). Runs soco-85's inherited
assertion chain, with the input census rebuilt WITH ``gas_hh_monthly_shape`` so the
legs' gas offers are checked against the shaped build, then PRECOMMIT-soco-87 §5:

1. :func:`assert_hh_monthly_artifact` — the Henry Hub monthly file on this checkout.
2. :func:`assert_monthly_arm` — every leg's run_config arms ``gas_hh_monthly_shape``.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/soco87_compose_span.py --check-only \\
        --pinned-sha <sha> --legs results/calibration/soco87_{2019,...,2025}
    PYTHONPATH=.:src:scripts python3 scripts/probes/soco87_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco87_{2019,...,2025} --out results/calibration/soco92_span
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

ROOT = s82.ROOT
HHM = ROOT / "data/raw/gas-prices/henry_hub_monthly.csv"
HHM_SHA = "88e0b68814e4a857e1079d826998c0086e2bd31735e2d8ef1a4855da1faa5926"
FLAG = "gas_hh_monthly_shape"

# soco85's import already appended gas_daily_shape; the census build must also carry
# the monthly shape so the legs' gas offers are checked against the armed build.
s82.census.RECIPE_SETS = tuple(s82.census.RECIPE_SETS) + (FLAG,)


def assert_hh_monthly_artifact() -> None:
    """Fail loud unless the committed Henry Hub monthly file is the PRECOMMIT's."""
    got = hashlib.sha256(HHM.read_bytes()).hexdigest()
    if got != HHM_SHA:
        raise SystemExit(f"{HHM.name}: sha256 {got}, expected {HHM_SHA}")
    print(f"  {HHM.name} live (sha256 matches the PRECOMMIT)")


def assert_monthly_arm(legs: list[Path]) -> None:
    """Each leg's recorded scenario_config arms gas_hh_monthly_shape."""
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text()).get(
            "scenario_config", {}
        )
        if sc.get(FLAG) is not True:
            raise SystemExit(f"{leg.name}: {FLAG} not armed")
        print(f"  {leg.name}: {FLAG} true")


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
    assert_hh_monthly_artifact()
    assert_monthly_arm(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    s82._compose(legs, out, True)


if __name__ == "__main__":
    main()
