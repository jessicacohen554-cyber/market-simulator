"""soco-57 (ZERO LP): compose the per-year legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (a) puts each backcast year in its own shard
container; rule 34 ``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its FULL
bundle, so the legs compose without a re-solve.

**REUSE, NOT A FORK** — the SOCO-56 pattern, applied to SOCO-56 itself. The
composition (the year-scoped copy, the bundle-root concatenation, the
``meta.json`` merge, the keeper-posture assertion, gate G17's offer-curve band
identity, the ``marginal_emission_rate`` and ``dispatch/<yr>_P1.parquet``
checks) is :mod:`scripts.probes.soco55_compose_span`, validated against a
committed keeper. This module adds exactly one thing on top: the assertion of
**this** lane's single delta.

``measured_cc_heat_rates`` is SOCO-57's delta and is asserted EXPLICITLY, to the
value ``--expect-cc-hr`` names, on every leg — read off the RESOLVED
``scenario_config``, never the ``prb_overrides`` bag the CLI routed it through.
A leg that silently solved the keeper's own recipe would otherwise compose in
looking like a null result. That is not hypothetical here: this lane's first
rule-19 run read all four grains at exactly zero because one of the four fleet
call sites never received the flag, and an arm that never arms is indis-
tinguishable from an inert one unless something asserts the resolved value.

``campd_per_unit_attribution`` (SOCO-56) and
``gas_basis_differential_measured_by_year`` (SOCO-55) are INHERITED postures, so
both are pinned ``True`` rather than being selectable here — this lane cannot
accidentally compose a pre-SOCO-56 leg.

Usage::

    python3 scripts/probes/soco57_compose_span.py --expect-cc-hr true \\
        --legs results/calibration/soco57_arm_{2023,2024,2025} \\
        --out  results/calibration/soco57_measured_cc_hr
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
DELTA_FIELD = "measured_cc_heat_rates"

#: SOCO-55's delta, INHERITED and therefore not selectable.
INHERITED_MEASURED_BASIS = True

#: SOCO-56's delta, INHERITED and therefore not selectable: every SOCO-57 leg
#: replays the SOCO-56 keeper's recipe, so a leg carrying False is a leg solved
#: against the wrong control.
INHERITED_PERUNIT_FIELD = "campd_per_unit_attribution"


def assert_delta(legs: list[Path], expect_cc_hr: bool) -> None:
    """Fail loud if any leg solved the wrong side of this lane's A/B.

    Checks BOTH this lane's delta and the inherited SOCO-56 posture, because a
    leg that silently dropped the inherited flag would compose into a two-delta
    bundle whose A/B could not be attributed (rule 19 ``[R-ONE-MECH]``).
    """
    print(f"expecting {DELTA_FIELD} = {expect_cc_hr} on every leg")
    print(f"expecting {INHERITED_PERUNIT_FIELD} = True (inherited) on every leg")
    for leg in legs:
        cfg = json.loads((leg / "run_config.json").read_text())
        sc = cfg.get("scenario_config") or {}
        got = bool(sc.get(DELTA_FIELD))
        if got != expect_cc_hr:
            raise SystemExit(
                f"{leg.name}: {DELTA_FIELD} is {sc.get(DELTA_FIELD)!r}, expected "
                f"{expect_cc_hr} — this leg solved the WRONG side of the A/B"
            )
        inherited = bool(sc.get(INHERITED_PERUNIT_FIELD))
        if not inherited:
            raise SystemExit(
                f"{leg.name}: {INHERITED_PERUNIT_FIELD} is "
                f"{sc.get(INHERITED_PERUNIT_FIELD)!r}, expected True — this leg "
                "was solved against a PRE-SOCO-56 control, not this keeper"
            )
        print(f"  {leg.name}: {DELTA_FIELD}={got}  {INHERITED_PERUNIT_FIELD}={inherited}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--expect-cc-hr",
        required=True,
        choices=("true", "false"),
        help=f"the value {DELTA_FIELD} MUST carry on every leg ('true' for the "
        "soco-57 arm, 'false' for a control composed from keeper-recipe legs)",
    )
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    assert_delta(legs, a.expect_cc_hr == "true")
    _compose(legs, out, INHERITED_MEASURED_BASIS)


if __name__ == "__main__":
    main()
