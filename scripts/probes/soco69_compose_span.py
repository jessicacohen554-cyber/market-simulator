"""soco-69 (ZERO LP): verify the seven per-year legs and compose them into one span bundle.

PRECOMMIT: ``docs/handoffs/r-soco/PRECOMMIT-soco-69-2026-09-25.md`` §3/§5. Each leg is
the soco-68 keeper recipe (seven ``--set`` fields incl. ``summer_derate_basis_aware``)
plus ``coal_mustrun_requires_measured_row=true``, one shard per year (rule 36). Checks
run BEFORE anything is written:

1. :func:`scripts.probes.rsoco_compose_span.assert_lane` and
   :func:`scripts.probes.rsocob_compose_span.assert_repairs` — the inherited R-SOCO
   posture and the four boundary repairs, reused not forked;
2. :func:`scripts.probes.soco67_compose_span.assert_arm` and
   :func:`scripts.probes.soco68_compose_span.assert_arm` — the keeper fields
   ``unit_outage_precod_clip`` and ``summer_derate_basis_aware`` still True;
3. :func:`assert_arm` — ``coal_mustrun_requires_measured_row`` True in every leg's
   resolved ``scenario_config``, and no coal ``_mustrun`` tranche solved at a plant
   outside the measured rows of ``thermal_tranches_SOCO.csv``;
4. :func:`scripts.probes.soco55_compose_span.compose` — posture drift, band identity,
   dispatch present, identical solve-surface fingerprint and dependency set.

Usage::

    python3 scripts/probes/soco69_compose_span.py --check-only --pinned-sha <sha> \\
        --legs results/calibration/soco69_{2019,2020,2021,2022,2023,2024,2025}
    python3 scripts/probes/soco69_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco69_{2019,...,2025} --out results/calibration/soco69_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes.rsoco_compose_span import assert_lane  # noqa: E402
from scripts.probes.rsocob_compose_span import assert_repairs  # noqa: E402
from scripts.probes.soco55_compose_span import ROOT, compose as _compose  # noqa: E402
from scripts.probes.soco67_compose_span import assert_arm as assert_precod_arm  # noqa: E402
from scripts.probes.soco68_compose_span import assert_arm as assert_basis_arm  # noqa: E402

ARM_FIELD = "coal_mustrun_requires_measured_row"
TRANCHES = ROOT / "data/raw/_processed-legacy/thermal_tranches_SOCO.csv"


def assert_arm(legs: list[Path]) -> None:
    """Fail loud unless every leg solved with the soco-69 arm field True and fired."""
    t = pd.read_csv(TRANCHES)
    measured = set(t[t.plant_group == "COAL"].plant_code.astype(int))
    for leg in legs:
        sc = (
            json.loads((leg / "run_config.json").read_text()).get("scenario_config")
            or {}
        )
        if sc.get(ARM_FIELD) is not True:
            raise SystemExit(f"{leg.name}: {ARM_FIELD} is not True in scenario_config")
        y = leg.name.rsplit("_", 1)[-1]
        u = pd.read_parquet(leg / f"hourly/unit_hourly_{y}.parquet", columns=["unit_id", "plant_code", "plant_group"])
        u = u.drop_duplicates("unit_id")
        bad = u[u.plant_group.astype(str).str.startswith("COAL")
                & u.unit_id.astype(str).str.endswith("_mustrun")
                & ~u.plant_code.isin(measured)]
        if len(bad):
            raise SystemExit(f"{leg.name}: unmeasured coal _mustrun tranche(s) present: {sorted(bad.unit_id.astype(str))}")
        print(f"  {leg.name}: {ARM_FIELD} True; no unmeasured coal _mustrun tranche")


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
    assert_precod_arm(legs)
    assert_basis_arm(legs)
    assert_arm(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
