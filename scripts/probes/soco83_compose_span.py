"""SOCO-83 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-82 keeper recipe + the SOCO ST_GAS out-of-merit must-run floor
(PRECOMMIT-soco-83 §1), one shard per year (rule 36). Runs soco-82's inherited
assertion chain (except its "2022-2025 equal the keeper" check — every year moves
here by design), then PRECOMMIT-soco-83 §7(2):

1. :func:`assert_oom_artifact` — the lambda-conditioned level file on this checkout.
2. :func:`assert_oom_arm` — every leg's run_config arms the three flags and the
   campaign floor, and every offer is the HEAD build's (the floor moves no offer).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/soco83_compose_span.py --check-only \\
        --pinned-sha <sha> --legs results/calibration/soco83_{2019,...,2025}
    PYTHONPATH=.:src:scripts python3 scripts/probes/soco83_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco83_{2019,...,2025} --out results/calibration/soco83_span
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

ROOT = s82.ROOT
OOM = ROOT / "data/raw/_processed-legacy/thermal_tranches_oom_level_mw_SOCO.csv"
OOM_SHA = "722e65b582a8699df8ee947270e6ea9f3c56eac227204d474bcbf152d9d7f2ba"
ARM = (
    "st_gas_mustrun_per_plant",
    "st_gas_mustrun_p25_level",
    "st_gas_mustrun_oom_level",
    "soco_gas_st_campaign_commitment",
)


def assert_oom_artifact() -> None:
    """Fail loud unless the lambda-conditioned level file is live."""
    got = hashlib.sha256(OOM.read_bytes()).hexdigest()
    if got != OOM_SHA:
        raise SystemExit(f"{OOM.name}: sha256 {got}, expected {OOM_SHA}")
    print(f"  {OOM.name} live (sha256 matches the PRECOMMIT)")


def assert_oom_arm(legs: list[Path]) -> None:
    """Each leg's recorded scenario_config arms the floor and keeps the campaign row."""
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text()).get(
            "scenario_config", {}
        )
        off = [k for k in ARM if sc.get(k) is not True]
        if off:
            raise SystemExit(f"{leg.name}: not armed: {off}")
        print(f"  {leg.name}: {', '.join(ARM)} all true")


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
    assert_oom_artifact()
    assert_oom_arm(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    s82._compose(legs, out, True)


if __name__ == "__main__":
    main()
