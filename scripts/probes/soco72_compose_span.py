"""SOCO-72 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-71 keeper recipe (eight ``--set`` fields, both SOCO artifacts unchanged)
replayed with ``GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO']`` extended to its
2019-2022 rows (PRECOMMIT-soco-72 §2), one shard per year (rule 36). Checks every
inherited lane assertion (via :mod:`scripts.probes.soco71_compose_span`, whose coal
``_peak`` census still binds: the lever moves no coal offer) plus:

1. :func:`assert_basis_table` — this checkout carries the extended table and every
   leg armed ``gas_basis_differential_measured_by_year`` with the per-plant print
   path off. The table is a module constant, not in ``resolved_inputs``, so the
   config alone cannot show the lever fired; (2) does.
2. :func:`assert_gas_census` — PRECOMMIT-soco-72 §7(2): every gas econ/peak tranche
   in 2019-2022 solved at the median ``mc`` the zero-LP census
   (``docs/handoffs/r-soco/soco72_gas_census.json``, arm column) predicts, ±$0.01.
3. :func:`assert_identity` — §6 E1 / §7(2): every leg's hourly ``cap_mw`` equals the
   soco-71 leg's, and 2023-2025 dispatch (unit ``mw``) and zone price are
   byte-identical to the soco-71 legs.

Usage::

    python3 scripts/probes/soco72_compose_span.py --check-only --pinned-sha <sha> \\
        --legs results/calibration/soco72_{2019,...,2025}
    python3 scripts/probes/soco72_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco72_{2019,...,2025} --out results/calibration/soco72_span
"""

from __future__ import annotations

import argparse
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

#: PRECOMMIT-soco-72 §2: the extended table this lane arms.
BASIS = {2019: 0.27, 2020: 0.32, 2021: 0.30, 2022: 1.20, 2023: 0.49, 2024: 0.64, 2025: 0.65}
CENSUS = ROOT / "docs/handoffs/r-soco/soco72_gas_census.json"
CONTROL = ROOT / "results/calibration/soco71_{y}"
IDENTITY_YEARS = (2023, 2024, 2025)
TOL = 0.01


def _year(leg: Path) -> int:
    return int(leg.name.rsplit("_", 1)[-1])


def assert_basis_table(legs: list[Path]) -> None:
    """Fail loud unless the checkout carries the extended table and every leg armed it."""
    from market_sim.config.fuel_trajectories import GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR

    live = GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR.get("SOCO")
    if live != BASIS:
        raise SystemExit(f"GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'] is {live!r}, expected {BASIS!r}")
    for leg in legs:
        cfg = json.loads((leg / "run_config.json").read_text())
        sc = cfg.get("scenario_config") or {}
        moved = (cfg.get("solve_surface") or {}).get("moved") or {}
        if "GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR" not in moved:
            raise SystemExit(f"{leg.name}: solve_surface.moved lacks GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR")
        if sc.get("gas_basis_differential_measured_by_year") is not True:
            raise SystemExit(f"{leg.name}: gas_basis_differential_measured_by_year is not armed")
        if sc.get("gas_plant_monthly_fuel_pricing"):
            raise SystemExit(f"{leg.name}: gas_plant_monthly_fuel_pricing is on")
    print("  extended basis table live; every leg armed it with the per-plant print off")


def assert_gas_census(legs: list[Path]) -> None:
    """Fail loud unless each censused gas econ/peak tranche solved at its arm median mc."""
    census = json.loads(CENSUS.read_text())
    for leg in legs:
        y = _year(leg)
        want = census.get(str(y), {})
        if not want:
            continue
        u = pd.read_parquet(leg / f"hourly/unit_hourly_{y}.parquet", columns=["unit_id", "mc"])
        got = u.groupby(u.unit_id.astype(str)).mc.median()
        bad = {k: (round(float(got.get(k, np.nan)), 3), v[1]) for k, v in want.items()
               if not abs(float(got.get(k, np.nan)) - v[1]) <= TOL}
        if bad:
            raise SystemExit(f"{leg.name}: gas census mismatch on {len(bad)} tranches, e.g. {list(bad.items())[:4]}")
        print(f"  {leg.name}: {len(want)} gas econ/peak medians match the census arm (±${TOL})")


def assert_identity(legs: list[Path]) -> None:
    """cap_mw identical to soco-71 everywhere; 2023-2025 mw and price byte-identical."""
    cols = ["unit_id", "hour", "mw", "cap_mw"]
    for leg in legs:
        y = _year(leg)
        ctl = Path(str(CONTROL).format(y=y))
        a = pd.read_parquet(leg / f"hourly/unit_hourly_{y}.parquet", columns=cols).sort_values(["unit_id", "hour"])
        k = pd.read_parquet(ctl / f"hourly/unit_hourly_{y}.parquet", columns=cols).sort_values(["unit_id", "hour"])
        if list(a.unit_id.astype(str)) != list(k.unit_id.astype(str)) or not np.array_equal(
            a.cap_mw.to_numpy(), k.cap_mw.to_numpy()
        ):
            raise SystemExit(f"{leg.name}: cap_mw differs from the soco-71 leg")
        if y in IDENTITY_YEARS:
            pa = pd.read_parquet(leg / f"hourly/system_{y}.parquet", columns=["zone", "hour", "price"])
            pk = pd.read_parquet(ctl / f"hourly/system_{y}.parquet", columns=["zone", "hour", "price"])
            if not (np.array_equal(a.mw.to_numpy(), k.mw.to_numpy()) and pa.equals(pk)):
                raise SystemExit(f"{leg.name}: E1 identity FAILED — stop the line")
            print(f"  {leg.name}: cap_mw, mw and price byte-identical to soco-71 (E1)")
        else:
            print(f"  {leg.name}: cap_mw byte-identical to soco-71")


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
    assert_gas_census(legs)
    assert_identity(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
