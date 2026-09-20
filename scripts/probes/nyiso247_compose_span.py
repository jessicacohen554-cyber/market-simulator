"""nyiso-247 (ZERO LP): compose the four per-year arm legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (a) puts each backcast year in its own shard
container; rule 34 ``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its FULL
bundle — ``dispatch/<yr>_P1.parquet`` and the bundle-root parquets included — so
the legs compose without a re-solve.

**REUSE, NOT A FORK.** The composition itself is
:mod:`scripts.probes.nyiso238_compose_span`, this ISO's own recipe, already used
for a NYISO four-year ``replay_keeper`` fan-out and already allowing
``gas_offer_margin_anchor_by_zone`` as a per-year field. This module adds exactly
one thing on top, following the soco-56 pattern: **it asserts THIS lane's single
delta on every leg before any file is copied.**

nyiso-247's delta is the DISARM of the fuel-invariance limb, so all three of
``gas_offer_net_revenue_margin`` / ``gas_offer_margin_zonal_anchor`` /
``gas_offer_margin_zonal_anchor_vintage`` must read ``False`` on every leg. A leg
that silently solved the keeper's own recipe would otherwise compose in looking
like a null result — which on a lane whose whole question is "what does removing
this term do" is the one failure mode that could not be spotted downstream.

Usage::

    python3 scripts/probes/nyiso247_compose_span.py \\
        --legs results/calibration/nyiso247_fuelinv_{2022,2023,2024,2025} \\
        --out  results/calibration/nyiso247_fuelinv_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:  # run as a script, like every other probe
    sys.path.insert(0, str(_REPO))

from scripts.probes.nyiso238_compose_span import compose as _compose  # noqa: E402

#: This lane's single delta: all three must be OFF on every leg. The parent and
#: the child gates read the RESOLVED ``scenario_config``, never the
#: ``prb_overrides`` bag the CLI routed the override through.
DISARMED_FIELDS = (
    "gas_offer_net_revenue_margin",
    "gas_offer_margin_zonal_anchor",
    "gas_offer_margin_zonal_anchor_vintage",
)


def assert_delta(legs: list[Path]) -> None:
    """Fail loud if any leg solved the wrong side of this lane's A/B."""
    print(f"expecting {', '.join(DISARMED_FIELDS)} = False on every leg")
    bad: list[str] = []
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text()).get("scenario_config") or {}
        got = {f: sc.get(f) for f in DISARMED_FIELDS}
        ok = all(v is False for v in got.values())
        print(f"  {leg.name}: {got} -> {'OK' if ok else 'WRONG SIDE'}")
        if not ok:
            bad.append(leg.name)
    if bad:
        raise SystemExit(
            f"legs {bad} did not solve the disarm — the --set override did not "
            "reach the solve config. Refusing to compose: a keeper-recipe leg "
            "would read as a null result for this lane's whole question."
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    legs = [Path(x) for x in args.legs]
    assert_delta(legs)
    _compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
