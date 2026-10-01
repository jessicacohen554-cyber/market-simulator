"""SOCO-76 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-72 keeper recipe (nine ``--set`` fields) with ``egrid_identity_heat_rates``
armed on SOCO's own artifact (Dahlberg 7709<->7765, Hartwell 54538<->70454;
PRECOMMIT-soco-76 §2a), one shard per year (rule 36). Checks every inherited lane
assertion (via the soco-72 chain) except soco-72's own census/identity pair, which
this lane replaces:

1. :func:`assert_identity_arm` — the artifact on this checkout is the committed one
   (sha256), and every leg resolved ``egrid_identity_heat_rates`` True.
2. :func:`assert_census` — PRECOMMIT-soco-76 §7(2) / E1: the six Dahlberg/Hartwell
   tranches solved at the zero-LP census arm median ``mc`` (``soco76_identity_fleet_census.json``)
   ±$0.01, and every OTHER soco-72-censused gas econ/peak tranche still solved at the
   soco-72 census arm median ±$0.01.
3. :func:`assert_cap_identity` — every unit's hourly ``cap_mw`` equals the soco-72 leg's.

Usage::

    python3 scripts/probes/soco76_compose_span.py --check-only --pinned-sha <sha> \\
        --legs results/calibration/soco76_{2019,...,2025}
    python3 scripts/probes/soco76_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco76_{2019,...,2025} --out results/calibration/soco76_span
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
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

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

ARTIFACT = ROOT / "data/raw/_processed-legacy/egrid_identity_heat_rates_SOCO.csv"
ARTIFACT_SHA = "32c46c93a1552a4a48e077dffac75dd817530fb50872eac31887d34c8390985f"
CENSUS76 = ROOT / "docs/records/soco/r-soco/soco76_identity_fleet_census.json"
CENSUS72 = ROOT / "docs/records/soco/r-soco/soco72_gas_census.json"
CONTROL = ROOT / "results/calibration/soco72_{y}"
TOL = 0.01


def _year(leg: Path) -> int:
    return int(leg.name.rsplit("_", 1)[-1])


def assert_identity_arm(legs: list[Path]) -> None:
    """Fail loud unless the committed artifact is live and every leg armed the flag."""
    got = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    if got != ARTIFACT_SHA:
        raise SystemExit(f"{ARTIFACT.name}: sha256 {got}, expected {ARTIFACT_SHA}")
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text()).get("scenario_config") or {}
        if sc.get("egrid_identity_heat_rates") is not True:
            raise SystemExit(f"{leg.name}: egrid_identity_heat_rates is not armed")
    print("  identity artifact live (sha256 matches); every leg armed egrid_identity_heat_rates")


def assert_census(legs: list[Path]) -> None:
    """Six identity tranches at the soco-76 census; every other censused gas tranche at soco-72's."""
    c76 = json.loads(CENSUS76.read_text())
    c72 = json.loads(CENSUS72.read_text())
    for leg in legs:
        y = _year(leg)
        u = pd.read_parquet(leg / f"hourly/unit_hourly_{y}.parquet", columns=["unit_id", "mc"])
        got = u.groupby(u.unit_id.astype(str)).mc.median()
        six = {k: v["mc_new"] for k, v in c76[str(y)]["moved"].items()}
        if len(six) != 6:
            raise SystemExit(f"{leg.name}: census names {len(six)} moved tranches, expected 6")
        bad = {k: (round(float(got.get(k, np.nan)), 3), v) for k, v in six.items()
               if not abs(float(got.get(k, np.nan)) - v) <= TOL}
        rest = {k: v[1] for k, v in c72.get(str(y), {}).items() if k not in six}
        bad.update({k: (round(float(got.get(k, np.nan)), 3), v) for k, v in rest.items()
                    if not abs(float(got.get(k, np.nan)) - v) <= TOL})
        # every other non-_committed unit: median mc equal to the soco-72 leg's (all years)
        k = pd.read_parquet(Path(str(CONTROL).format(y=y)) / f"hourly/unit_hourly_{y}.parquet",
                            columns=["unit_id", "mc"])
        kmed = k.groupby(k.unit_id.astype(str)).mc.median()
        others = [x for x in kmed.index if x not in six and not x.endswith("_committed")]
        bad.update({x: (round(float(got.get(x, np.nan)), 3), round(float(kmed[x]), 3)) for x in others
                    if not abs(float(got.get(x, np.nan)) - float(kmed[x])) <= TOL})
        if bad:
            raise SystemExit(f"{leg.name}: census mismatch on {len(bad)} tranches, e.g. {list(bad.items())[:4]}")
        print(f"  {leg.name}: 6 identity tranches at the soco-76 census; {len(rest)} gas tranches at soco-72's census;"
              f" {len(others)} other non-committed units at the soco-72 leg's median mc")


def assert_cap_identity(legs: list[Path]) -> None:
    """Every unit's hourly cap_mw byte-identical to the soco-72 leg's."""
    cols = ["unit_id", "hour", "cap_mw"]
    for leg in legs:
        y = _year(leg)
        ctl = Path(str(CONTROL).format(y=y))
        a = pd.read_parquet(leg / f"hourly/unit_hourly_{y}.parquet", columns=cols).sort_values(["unit_id", "hour"])
        k = pd.read_parquet(ctl / f"hourly/unit_hourly_{y}.parquet", columns=cols).sort_values(["unit_id", "hour"])
        if list(a.unit_id.astype(str)) != list(k.unit_id.astype(str)) or not np.array_equal(
            a.cap_mw.to_numpy(), k.cap_mw.to_numpy()
        ):
            raise SystemExit(f"{leg.name}: cap_mw differs from the soco-72 leg")
        print(f"  {leg.name}: cap_mw byte-identical to soco-72")


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
    assert_census(legs)
    assert_cap_identity(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
