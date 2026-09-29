"""SOCO-85 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-83 keeper recipe + ``gas_daily_shape`` (Henry Hub within-month gas shape;
PRECOMMIT-soco-85 §1), one shard per year (rule 36). Runs soco-83's inherited
assertion chain, with the input census rebuilt WITH ``gas_daily_shape`` so the
legs' gas offers are checked against the shaped build, then PRECOMMIT-soco-85 §5:

1. :func:`assert_hh_artifact` — the Henry Hub daily file on this checkout.
2. :func:`assert_shape_arm` — every leg's run_config arms ``gas_daily_shape``.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/soco85_compose_span.py --check-only \\
        --pinned-sha <sha> --legs results/calibration/soco85_{2019,...,2025}
    PYTHONPATH=.:src:scripts python3 scripts/probes/soco85_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco85_{2019,...,2025} --out results/calibration/soco85_span
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

ROOT = s82.ROOT
HH = ROOT / "data/raw/gas-prices/henry_hub_daily.csv"
HH_SHA = "7c2787a4001e0a6c2d7f468a77e4c2faadeb1df5d9214d9da990bfab162a4ad3"
FLAG = "gas_daily_shape"

# The input census rebuilds each year's offers; with the shape armed, the gas
# units' hourly offers carry the daily factor, so the census build must too.
s82.census.RECIPE_SETS = tuple(s82.census.RECIPE_SETS) + (FLAG,)


def assert_hh_artifact() -> None:
    """Fail loud unless the committed Henry Hub daily file is the PRECOMMIT's."""
    got = hashlib.sha256(HH.read_bytes()).hexdigest()
    if got != HH_SHA:
        raise SystemExit(f"{HH.name}: sha256 {got}, expected {HH_SHA}")
    print(f"  {HH.name} live (sha256 matches the PRECOMMIT)")


def assert_shape_arm(legs: list[Path]) -> None:
    """Each leg's recorded scenario_config arms gas_daily_shape."""
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
    assert_hh_artifact()
    assert_shape_arm(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    s82._compose(legs, out, True)


if __name__ == "__main__":
    main()
