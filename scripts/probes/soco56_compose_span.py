"""soco-56 (ZERO LP): compose the per-year legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (a) puts each backcast year in its own shard
container; rule 34 ``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its FULL
bundle, so the legs compose without a re-solve.

**REUSE, NOT A FORK.** The composition itself — the year-scoped copy, the
bundle-root concatenation, the ``meta.json`` merge, the keeper-posture assertion,
gate G17's offer-curve band identity, the ``marginal_emission_rate`` and
``dispatch/<yr>_P1.parquet`` checks — is
:mod:`scripts.probes.soco55_compose_span`, VALIDATED against a committed keeper
(it reproduced SOCO-55's eighteen hourly sidecars byte-identically). This module
adds exactly one thing on top: the assertion of **this** lane's single delta.

``campd_per_unit_attribution`` is SOCO-56's delta and is asserted EXPLICITLY, to
the value ``--expect-perunit`` names, on every leg — read off the RESOLVED
``scenario_config``, never the ``prb_overrides`` bag the CLI routed it through.
A leg that silently solved the keeper's own recipe would otherwise compose in
looking like a null result.

``gas_basis_differential_measured_by_year`` is now SOCO-55's INHERITED posture,
so it is pinned ``True`` through the delegate's ``expect_measured`` rather than
being selectable here — this lane cannot accidentally compose a pre-SOCO-55 leg.

Usage::

    python3 scripts/probes/soco56_compose_span.py --expect-perunit true \\
        --legs results/calibration/soco56_arm_{2023,2024,2025} \\
        --out  results/calibration/soco56_perunit_outage
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:  # run as a script, like every other probe
    sys.path.insert(0, str(_REPO))

from scripts.probes.soco55_compose_span import ROOT, compose as _compose  # noqa: E402

#: This lane's single delta. Asserted on every leg before any file is copied.
DELTA_FIELD = "campd_per_unit_attribution"

#: SOCO-55's delta, INHERITED here and therefore not selectable: every SOCO-56
#: leg replays the SOCO-55 keeper's recipe, so a leg carrying False is a leg
#: solved against the wrong control.
INHERITED_MEASURED_BASIS = True


def assert_delta(legs: list[Path], expect_perunit: bool) -> None:
    """Fail loud if any leg solved the wrong side of this lane's A/B."""
    print(f"expecting {DELTA_FIELD} = {expect_perunit} on every leg")
    for leg in legs:
        cfg = json.loads((leg / "run_config.json").read_text())
        sc = cfg.get("scenario_config") or {}
        got = bool(sc.get(DELTA_FIELD))
        if got != expect_perunit:
            raise SystemExit(
                f"{leg.name}: {DELTA_FIELD} is {sc.get(DELTA_FIELD)!r}, expected "
                f"{expect_perunit} — this leg solved the WRONG side of the A/B"
            )
        print(f"  {leg.name}: {DELTA_FIELD}={got}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--expect-perunit",
        required=True,
        choices=("true", "false"),
        help=f"the value {DELTA_FIELD} MUST carry on every leg ('true' for the "
        "soco-56 arm, 'false' for a control composed from keeper-recipe legs)",
    )
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    assert_delta(legs, a.expect_perunit == "true")
    _compose(legs, out, INHERITED_MEASURED_BASIS)


if __name__ == "__main__":
    main()
