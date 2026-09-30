"""SOCO-82 zero-LP composition: seven year-isolated legs -> ONE registrable span bundle.

The soco-81 keeper recipe on the regenerated ``campd-unit-outages-perunitdark-SOCO.csv``
(PRECOMMIT-soco-82 §1: F1's retiree append adds Wansley's dark windows), one shard per
year (rule 36). Runs soco-81's inherited assertion chain, then PRECOMMIT-soco-82 §7(2):

1. :func:`assert_dark_artifact` — the regenerated extract is the one on this checkout.
2. :func:`assert_input_census` — every leg's non-``_committed`` unit solved at the HEAD
   ``fleet_only`` build's median ``mc`` ±$0.01 (the artifact moves no offer), and
   Wansley's four tranches never dispatch above the regenerated availability × pmax.
3. :func:`assert_keeper_years` — 2022-2025 class TWh equal the keeper's ±0.01 TWh
   (their inputs are array-identical, §2).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/soco82_compose_span.py --check-only \\
        --pinned-sha <sha> --legs results/calibration/soco82_{2019,...,2025}
    PYTHONPATH=.:src:scripts python3 scripts/probes/soco82_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/soco82_{2019,...,2025} --out results/calibration/soco82_span
"""

from __future__ import annotations

import argparse
import hashlib
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
from scripts.probes.soco81_compose_span import assert_two_sided_arm  # noqa: E402

import _soco81_census as census  # noqa: E402

# Repointed soco-83 (2026-09-28): soco81_span was pruned at the soco-82 promotion (rule 35).
# Repointed again soco-84 (2026-09-28): soco82_span was pruned at the soco-83 promotion;
# the incumbent keeper is soco83_span (soco83_compose_span imports this module).
# Repointed soco-85 (2026-09-28): soco83_span was pruned at the soco-85 promotion (rule 35);
# the incumbent keeper is soco85_span (the soco-83 recipe + gas_daily_shape).
# Repointed soco-87 (2026-09-29): soco85_span was pruned at the soco-87 promotion (rule 35);
# the incumbent keeper is soco92_span (the soco-85 recipe + gas_hh_monthly_shape).
KEEPER_SPAN = (
    ROOT / "results/calibration/soco92_span"
)  # repointed soco-92 (rule 35 prune of soco92_span)
census.SPAN = KEEPER_SPAN
census.KEEPER = "2026-09-28-soco85-gas-daily-shape"
DARK = ROOT / "data/raw/campd-unit-outages-perunitdark-SOCO.csv"
DARK_SHA = "03ce606cfe118ef28e560739d12a005b2240aa112609e119c51a9f86ea2fd37c"
WANSLEY = "COAL_SOCO_GA_p6052_"
TOL = 0.01
TOL_TWH = 0.01


def _year(leg: Path) -> int:
    return int(leg.name.rsplit("_", 1)[-1])


def assert_dark_artifact() -> None:
    """Fail loud unless the regenerated perunitdark extract is live."""
    got = hashlib.sha256(DARK.read_bytes()).hexdigest()
    if got != DARK_SHA:
        raise SystemExit(f"{DARK.name}: sha256 {got}, expected {DARK_SHA}")
    print(f"  {DARK.name} live (sha256 matches the PRECOMMIT)")


def assert_input_census(legs: list[Path]) -> dict:
    """Non-committed offers at the HEAD build; Wansley within its regenerated availability."""
    report = {}
    for leg in legs:
        y = _year(leg)
        f = census.build(y, True)
        u = pd.read_parquet(leg / f"hourly/unit_hourly_{y}.parquet")
        if "pass" in u.columns:
            u = u[u["pass"].astype(str) == "P1"]
        u["unit_id"] = u.unit_id.astype(str)
        got = u.groupby("unit_id").mc.median()
        want = {x: float(np.median(f["mc"][i])) for i, x in enumerate(f["ids"])}
        bad = {
            x: (round(float(got[x]), 3), round(want[x], 3))
            for x in got.index
            if x in want
            and not x.endswith("_committed")
            and not abs(got[x] - want[x]) <= TOL
        }
        if bad:
            raise SystemExit(
                f"{leg.name}: offer mismatch on {len(bad)} units, e.g. {list(bad.items())[:5]}"
            )
        mwcol = next(c for c in ("mw", "gen_mw", "p", "gen") if c in u.columns)
        over = 0.0
        w_twh = 0.0
        for i, x in enumerate(f["ids"]):
            if not x.startswith(WANSLEY):
                continue
            g = u[u.unit_id == x].sort_values("hour")[mwcol].to_numpy(float)[: census.T]
            av = f["av"][i] if f["av"].ndim == 2 else np.full(census.T, f["av"][i])
            cap = f["pmax"][i] * av[: len(g)]
            over = max(over, float(np.max(g - cap, initial=0.0)))
            w_twh += g.sum() / 1e6
        if over > 1e-3:
            raise SystemExit(
                f"{leg.name}: Wansley dispatches {over:.3f} MW above its availability"
            )
        report[y] = dict(units_checked=int(len(got)), wansley_twh=round(w_twh, 3))
        print(
            f"  {leg.name}: {len(got)} units at the HEAD build's offers; Wansley {w_twh:.3f} TWh, within availability"
        )
    return report


def assert_keeper_years(legs: list[Path]) -> None:
    """2022-2025 class TWh equal the keeper's (inputs array-identical)."""
    for leg in legs:
        y = _year(leg)
        if y < 2022:
            continue
        a = pd.read_parquet(leg / f"hourly/class_hourly_{y}.parquet")
        k = pd.read_parquet(KEEPER_SPAN / f"hourly/class_hourly_{y}.parquet")
        if "pass" in a.columns:
            a = a[a["pass"].astype(str) == "P1"]
        if "pass" in k.columns:
            k = k[k["pass"].astype(str) == "P1"]
        d = (a.groupby("klass").mw.sum() - k.groupby("klass").mw.sum()).abs() / 1e6
        worst = float(d.max())
        if worst > TOL_TWH:
            raise SystemExit(
                f"{leg.name}: class TWh moved vs keeper by {worst:.4f} ({d.idxmax()})"
            )
        print(f"  {leg.name}: every class within {worst:.4f} TWh of the keeper")


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
    assert_dark_artifact()
    assert_input_census(legs)
    assert_keeper_years(legs)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
