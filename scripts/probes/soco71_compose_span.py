"""SOCO-71 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-70 keeper recipe (eight ``--set`` fields, ``thermal_tranches_SOCO.csv``
unchanged) replayed on ``campd_coal_heat_rates_SOCO.csv`` re-derived over its declared
2019-2025 window with the coal-family population guard (PRECOMMIT-soco-71 §2), one
shard per year (rule 36). Checks every inherited lane assertion (via
:mod:`scripts.probes.soco70_compose_span`) plus:

1. :func:`assert_coal_hr_artifact` — this checkout carries the pinned re-derived
   artifact and every leg armed ``measured_coal_heat_rates``. The artifact is not in
   ``resolved_inputs``, so the config alone cannot show the lever fired; (2) does.
2. :func:`assert_census` — PRECOMMIT-soco-71 §7(2): every coal plant's ``_peak``
   tranche (the tranche that carries no start markup in any plant) solved at the
   median ``mc`` the zero-LP census predicted from the re-derived artifact, to
   ±$0.01/MWh.

Usage::

    python3 scripts/probes/soco71_compose_span.py --check-only --pinned-sha <sha> \\
        --legs results/calibration/soco71_{2019,2020,2021,2022,2023,2024,2025}
    python3 scripts/probes/soco71_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco71_{2019,...,2025} --out results/calibration/soco71_span
"""

from __future__ import annotations

import argparse
import hashlib
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
from scripts.probes.soco69_compose_span import assert_arm as assert_measured_arm  # noqa: E402
from scripts.probes.soco70_compose_span import (  # noqa: E402
    assert_artifact as assert_tranche_artifact,
    assert_mustrun_set,
)

#: The pinned re-derived artifact (PRECOMMIT-soco-71 §2).
COAL_HR = ROOT / "data/raw/_processed-legacy/campd_coal_heat_rates_SOCO.csv"
COAL_HR_SHA256 = "a55796376ce68c0b5004165084ad45eed650f293f7bccbfac491005d176d9d47"

#: PRECOMMIT-soco-71 §3 census: median ``mc`` of each coal plant's ``_peak`` tranche,
#: fleet_only on the keeper recipe with the re-derived artifact ($/MWh).
CENSUS: dict[int, dict[int, float]] = {
    2019: {26: 50.389, 3: 37.312, 6002: 23.244, 641: 35.822, 6052: 36.927, 6257: 32.795, 703: 35.304, 6073: 38.682},
    2020: {26: 48.477, 3: 36.982, 6002: 23.376, 641: 38.607, 6052: 34.12, 6257: 34.27, 703: 34.236, 6073: 36.309},
    2021: {26: 51.29, 3: 40.241, 6002: 24.286, 6052: 33.973, 6257: 34.624, 703: 33.88, 6073: 34.938},
    2022: {26: 76.056, 3: 46.05, 6002: 29.061, 6257: 41.509, 703: 44.213, 6073: 47.842},
    2023: {26: 84.345, 3: 64.539, 6002: 28.242, 6257: 43.927, 703: 60.435, 6073: 46.975},
    2024: {26: 75.107, 3: 31.887, 6002: 26.774, 6257: 40.359, 703: 57.443, 6073: 43.465},
    2025: {26: 77.515, 3: 30.059, 6002: 27.934, 8: 33.551, 6052: 41.805, 6257: 38.133, 703: 42.217, 708: 57.297, 6073: 37.972},
}  # fmt: skip
TOL = 0.01


def assert_coal_hr_artifact(legs: list[Path]) -> None:
    """Fail loud unless this checkout carries the pinned artifact and every leg armed it."""
    local = hashlib.sha256(COAL_HR.read_bytes()).hexdigest()
    if local != COAL_HR_SHA256:
        raise SystemExit(f"local {COAL_HR.name} sha256 {local} != pinned {COAL_HR_SHA256}")
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text()).get("scenario_config") or {}
        if sc.get("measured_coal_heat_rates") is not True:
            raise SystemExit(f"{leg.name}: measured_coal_heat_rates is not armed")
    print(f"  {COAL_HR.name} = pinned re-derived artifact; every leg armed")


def assert_census(legs: list[Path]) -> None:
    """Fail loud unless each coal ``_peak`` tranche solved at its censused median mc."""
    for leg in legs:
        y = int(leg.name.rsplit("_", 1)[-1])
        u = pd.read_parquet(
            leg / f"hourly/unit_hourly_{y}.parquet", columns=["unit_id", "plant_code", "mc"]
        )
        u = u[u.unit_id.astype(str).str.startswith("COAL") & u.unit_id.astype(str).str.endswith("_peak")]
        got = u.groupby("plant_code").mc.median()
        want = CENSUS[y]
        bad = {
            p: (round(float(got.get(p, float("nan"))), 3), w)
            for p, w in want.items()
            if not abs(float(got.get(p, float("nan"))) - w) <= TOL
        }
        extra = sorted(set(int(p) for p in got.index) - set(want))
        if bad or extra:
            raise SystemExit(f"{leg.name}: census mismatch {bad} extra plants {extra}")
        print(f"  {leg.name}: {len(want)} coal _peak medians match the census (±${TOL})")


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
    assert_measured_arm(legs)
    assert_tranche_artifact(legs)
    assert_mustrun_set(legs)
    assert_coal_hr_artifact(legs)
    assert_census(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
