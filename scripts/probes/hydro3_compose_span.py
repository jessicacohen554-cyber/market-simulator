"""hydro-3 (ZERO LP): compose the four per-year ``hydro_ror_split`` legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (a) solves each backcast year in its own shard;
rule 34 ``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its FULL bundle, so
the legs compose without a re-solve.

**REUSE, NOT A FORK.** The composition is
:mod:`scripts.probes.nyiso238_compose_span`, NYISO's own recipe (also used by
nyiso-247). This module adds one thing: it asserts THIS lane's single delta on
every leg before any file is copied — ``hydro_ror_split`` ON and
``hydro_budget_nameplate_aware`` OFF, read from the RESOLVED
``scenario_config`` (never the ``prb_overrides`` bag the CLI routed it through).
A leg that silently solved the keeper's recipe would otherwise compose in
looking like a null result (PRECOMMIT-hydro-3 §4, check R0).

Usage::

    python3 scripts/probes/hydro3_compose_span.py \\
        --legs results/calibration/hydro3_nyiso_ror_{2022,2023,2024,2025} \\
        --out  results/calibration/hydro3_nyiso_ror_span
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

#: This lane's single delta, as (field, required resolved value).
EXPECTED = (("hydro_ror_split", True), ("hydro_budget_nameplate_aware", False))


def assert_delta(legs: list[Path]) -> None:
    """Fail loud if any leg solved the wrong side of this lane's A/B."""
    print(f"expecting {dict(EXPECTED)} on every leg")
    bad: list[str] = []
    for leg in legs:
        sc = json.loads((leg / "run_config.json").read_text()).get("scenario_config") or {}
        got = {f: sc.get(f) for f, _ in EXPECTED}
        ok = all(got[f] is v for f, v in EXPECTED)
        print(f"  {leg.name}: {got} -> {'OK' if ok else 'WRONG SIDE'}")
        if not ok:
            bad.append(leg.name)
    if bad:
        raise SystemExit(
            f"legs {bad} did not solve the hydro_ror_split arm — the --set "
            "override did not reach the solve config. Refusing to compose."
        )


def main() -> None:
    """Assert the delta on every leg, then compose the span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    legs = [Path(x) for x in args.legs]
    assert_delta(legs)
    _compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
