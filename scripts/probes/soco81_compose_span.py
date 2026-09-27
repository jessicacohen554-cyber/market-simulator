"""SOCO-81 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-76 keeper recipe with ``coal_econ_marginal_hr_two_sided`` armed on SOCO's own
artifact (PRECOMMIT-soco-81 §1), one shard per year (rule 36). Runs every inherited
lane assertion of the soco-76 chain except the three that read the (now gone)
soco-72 legs, and replaces them with checks against zero-LP ``fleet_only`` rebuilds:

1. :func:`assert_two_sided_arm` — the ratio artifact on this checkout is the
   committed one (sha256), and every leg armed the flag in both ``run_config`` and
   ``meta``.
2. :func:`assert_census` — PRECOMMIT-soco-81 §7(2): the 11 moved tranches solved at
   the flag-ON build's median ``mc`` ±$0.01 (a ``_committed`` miss is reported, not
   fatal — P1 may add a start markup there), and every other non-``_committed``
   unit at the flag-OFF build's median ``mc`` ±$0.01.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/soco81_compose_span.py --check-only \\
        --pinned-sha <sha> --legs results/calibration/soco81_{2019,...,2025}
    PYTHONPATH=.:src:scripts python3 scripts/probes/soco81_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco81_{2019,...,2025} --out results/calibration/soco81_span
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for p in (_REPO, _REPO / "src", _REPO / "scripts", _REPO / "scripts" / "probes"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

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
from scripts.probes.soco71_compose_span import (  # noqa: E402
    assert_census as assert_coal_census,
    assert_coal_hr_artifact,
)
from scripts.probes.soco72_compose_span import assert_basis_table  # noqa: E402
from scripts.probes.soco76_compose_span import assert_identity_arm  # noqa: E402

import _soco81_census as census  # noqa: E402

FLAG = "coal_econ_marginal_hr_two_sided"
ARTIFACT = ROOT / "data/raw/_processed-legacy/coal_incremental_hr_ratio_SOCO.csv"
ARTIFACT_SHA = "c07b531c1b0a27f2e6c8f4fd6bbc008f3873616e11a987ac9bf5d951303d886d"
TOL = 0.01


def _year(leg: Path) -> int:
    return int(leg.name.rsplit("_", 1)[-1])


def assert_two_sided_arm(legs: list[Path]) -> None:
    """Fail loud unless the committed ratio artifact is live and every leg armed the flag."""
    got = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    if got != ARTIFACT_SHA:
        raise SystemExit(f"{ARTIFACT.name}: sha256 {got}, expected {ARTIFACT_SHA}")
    for leg in legs:
        sc = (
            json.loads((leg / "run_config.json").read_text()).get("scenario_config")
            or {}
        )
        meta = json.loads((leg / "meta.json").read_text())
        if sc.get(FLAG) is not True or meta.get(FLAG) is not True:
            raise SystemExit(
                f"{leg.name}: {FLAG} not armed (run_config {sc.get(FLAG)}, meta {meta.get(FLAG)})"
            )
    print(f"  ratio artifact live (sha256 matches); every leg armed {FLAG}")


def assert_census(legs: list[Path]) -> dict:
    """11 moved tranches at the flag-ON build; every other non-committed unit at flag-OFF."""
    report = {}
    for leg in legs:
        y = _year(leg)
        off, on = census.build(y, False), census.build(y, True)
        moved = {
            off["ids"][i]
            for i in np.flatnonzero(np.abs(on["mc"] - off["mc"]).max(axis=1) > 1e-9)
        }
        if len(moved) != 11:
            raise SystemExit(
                f"{leg.name}: fleet_only census moves {len(moved)} tranches, expected 11"
            )
        u = pd.read_parquet(
            leg / f"hourly/unit_hourly_{y}.parquet", columns=["unit_id", "mc"]
        )
        got = u.groupby(u.unit_id.astype(str)).mc.median()
        want_on = {x: float(np.median(on["mc"][i])) for i, x in enumerate(on["ids"])}
        want_off = {x: float(np.median(off["mc"][i])) for i, x in enumerate(off["ids"])}
        fatal, committed_miss = {}, {}
        for x in moved:
            g = float(got.get(x, np.nan))
            if not abs(g - want_on[x]) <= TOL:
                (committed_miss if x.endswith("_committed") else fatal)[x] = (
                    round(g, 3),
                    round(want_on[x], 3),
                )
        others = [
            x
            for x in got.index
            if x not in moved and not x.endswith("_committed") and x in want_off
        ]
        for x in others:
            g = float(got[x])
            if not abs(g - want_off[x]) <= TOL:
                fatal[x] = (round(g, 3), round(want_off[x], 3))
        if fatal:
            raise SystemExit(
                f"{leg.name}: census mismatch on {len(fatal)} units, e.g. {list(fatal.items())[:5]}"
            )
        report[y] = dict(
            moved=len(moved), others=len(others), committed_miss=committed_miss
        )
        print(
            f"  {leg.name}: 11 moved tranches at the flag-ON build (committed misses: {committed_miss or 'none'}); "
            f"{len(others)} other non-committed units at the flag-OFF build's median mc"
        )
    return report


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
    assert_coal_census(legs)
    assert_basis_table(legs)
    assert_identity_arm(legs)
    assert_two_sided_arm(legs)
    assert_census(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
