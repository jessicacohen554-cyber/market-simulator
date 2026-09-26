"""SOCO-70 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-69 keeper recipe (eight ``--set`` fields) replayed on the extended
``thermal_tranches_SOCO.csv`` — the incumbent artifact plus five COAL rows derived by
``derive_thermal_tranches.py --coal-unit-coverage`` (Barry 3, Gaston 26, Crist 641,
Wansley 6052, Daniel 6073) — one shard per year (rule 36). Checks every inherited
lane assertion (via :mod:`scripts.probes.soco69_compose_span`, which now reads the
extended artifact, so its "no unmeasured coal ``_mustrun``" check still binds) plus:

1. :func:`assert_artifact` — every leg's ``resolved_inputs.thermal_tranches.sha256``
   equals the pinned extended artifact (the lever is DATA, so the config alone cannot
   show it fired).
2. :func:`assert_mustrun_set` — the coal ``_mustrun`` tranches each leg solved are
   exactly the plants whose row carries ``mustrun_pct > 0`` and that the leg's fleet
   carries as coal: Bowen 703, Miller 6002, Scherer 6257 (unchanged) plus Gaston 26 and
   Daniel 6073 (new). Barry, Crist and Wansley carry a row with ``mustrun_pct = 0`` and
   must show none.

Usage::

    python3 scripts/probes/soco70_compose_span.py --check-only --pinned-sha <sha> \\
        --legs results/calibration/soco70_{2019,2020,2021,2022,2023,2024,2025}
    python3 scripts/probes/soco70_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco70_{2019,...,2025} --out results/calibration/soco70_span
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
from scripts.probes.soco69_compose_span import (
    TRANCHES,
    assert_arm as assert_measured_arm,
)  # noqa: E402

#: The pinned extended artifact (PRECOMMIT-soco-70 §3).
ARTIFACT_SHA256 = "ab5ec265d192379551c14facc6f65d8d972f117a565bae36b0179bbf96122ad7"


def assert_artifact(legs: list[Path]) -> None:
    """Fail loud unless every leg (and this checkout) solved on the pinned artifact."""
    local = hashlib.sha256(TRANCHES.read_bytes()).hexdigest()
    if local != ARTIFACT_SHA256:
        raise SystemExit(
            f"local {TRANCHES.name} sha256 {local} != pinned {ARTIFACT_SHA256}"
        )
    for leg in legs:
        ri = (
            json.loads((leg / "run_config.json").read_text()).get("resolved_inputs")
            or {}
        )
        got = (ri.get("thermal_tranches") or {}).get("sha256")
        if got != ARTIFACT_SHA256:
            raise SystemExit(
                f"{leg.name}: thermal_tranches sha256 {got} != pinned {ARTIFACT_SHA256}"
            )
        print(f"  {leg.name}: thermal_tranches_SOCO.csv = pinned extended artifact")


def assert_mustrun_set(legs: list[Path]) -> None:
    """Fail loud unless each leg's coal _mustrun plants == rows with mustrun_pct > 0 in its fleet."""
    t = pd.read_csv(TRANCHES)
    coal = t[t.plant_group == "COAL"]
    with_mr = set(coal[coal.mustrun_pct > 0].plant_code.astype(int))
    for leg in legs:
        y = leg.name.rsplit("_", 1)[-1]
        u = pd.read_parquet(
            leg / f"hourly/unit_hourly_{y}.parquet",
            columns=["unit_id", "plant_code", "plant_group"],
        )
        u = u.drop_duplicates("unit_id")
        c = u[u.plant_group.astype(str).str.startswith("COAL")]
        fleet = set(c.plant_code.astype(int))
        got = set(
            c[c.unit_id.astype(str).str.endswith("_mustrun")].plant_code.astype(int)
        )
        want = with_mr & fleet
        if got != want:
            raise SystemExit(
                f"{leg.name}: coal _mustrun plants {sorted(got)} != expected {sorted(want)}"
            )
        print(f"  {leg.name}: coal _mustrun plants {sorted(got)} (as censused)")


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
    assert_artifact(legs)
    assert_mustrun_set(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
