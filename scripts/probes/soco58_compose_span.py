"""soco-58 (ZERO LP): compose the per-year legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (a) puts each backcast year in its own shard
container; rule 34 ``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its FULL
bundle, so the legs compose without a re-solve.

**REUSE, NOT A FORK** — the SOCO-57 pattern, applied to SOCO-57 itself. The
composition (the year-scoped copy, the bundle-root concatenation, the
``meta.json`` merge, the keeper-posture assertion, gate G17's offer-curve band
identity, the ``marginal_emission_rate`` and ``dispatch/<yr>_P1.parquet``
checks) is :mod:`scripts.probes.soco55_compose_span`, validated against a
committed keeper across three lanes. This module adds exactly one thing on top:
the assertion of **this** lane's delta and of every posture it inherits.

``coal_warm_committed`` is SOCO-58's delta and is asserted EXPLICITLY, to the
value ``--expect-warm`` names, on every leg — read off the RESOLVED
``scenario_config``, never the ``prb_overrides`` bag the CLI routed it through.

**THAT DISTINCTION IS LOAD-BEARING HERE IN A WAY IT WAS NOT IN SOCO-57.** This
mechanism lives entirely at the P0→P1 seam (``model/commitment.py::
compute_monthly_markup``), so it moves NOTHING on any fleet grain —
``fuel_prices``, ``mc_base``, ``pmax``, ``availability`` and ``heat_rate`` all
read exactly zero, BY CONSTRUCTION, and P0 is byte-identical. An armed leg and
an un-armed leg are therefore INDISTINGUISHABLE on every grain SOCO-57's
``_soco57_rule19.py`` probe reads. The resolved-config assertion below is the
ONLY thing that can tell them apart before the numbers are read, which is the
exact inverse of SOCO-57 §4's wiring defect (where all-grains-zero meant "an arm
that never armed"; here it is the required signature).

The four postures inherited from SOCO-54 … SOCO-57 are pinned rather than
selectable, so this lane cannot accidentally compose a leg solved against an
older control (rule 19 ``[R-ONE-MECH]``: a two-delta bundle has no attributable
A/B).

Usage::

    python3 scripts/probes/soco58_compose_span.py --expect-warm true \\
        --legs results/calibration/soco58_arm_{2023,2024,2025} \\
        --out  results/calibration/soco58_warm_committed
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
DELTA_FIELD = "coal_warm_committed"

#: SOCO-55's delta, INHERITED and therefore not selectable (it is the
#: positional argument ``soco55_compose_span.compose`` takes).
INHERITED_MEASURED_BASIS = True

#: Every other posture this lane inherits, pinned to the value the designated
#: keeper ``2026-09-20-soco57-measured-cc-heat`` carries. A leg missing any of
#: them was solved against the wrong control.
INHERITED_FIELDS: dict[str, bool] = {
    "campd_per_unit_attribution": True,  # SOCO-56
    "measured_cc_heat_rates": True,  # SOCO-57
    "measured_coal_heat_rates": True,  # SOCO-53f
    "gas_plant_monthly_fuel_pricing": False,  # SOCO-54 (back to its own default)
}


def assert_delta(legs: list[Path], expect_warm: bool) -> None:
    """Fail loud if any leg solved the wrong side of this lane's A/B.

    Checks this lane's delta AND every inherited posture, because a leg that
    silently dropped one would compose into a multi-delta bundle whose A/B
    could not be attributed (rule 19 ``[R-ONE-MECH]``).
    """
    print(f"expecting {DELTA_FIELD} = {expect_warm} on every leg")
    for f, v in INHERITED_FIELDS.items():
        print(f"expecting {f} = {v} (inherited) on every leg")
    for leg in legs:
        cfg = json.loads((leg / "run_config.json").read_text())
        sc = cfg.get("scenario_config") or {}
        got = bool(sc.get(DELTA_FIELD))
        if got != expect_warm:
            raise SystemExit(
                f"{leg.name}: {DELTA_FIELD} is {sc.get(DELTA_FIELD)!r}, expected "
                f"{expect_warm} — this leg solved the WRONG side of the A/B. "
                "NOTE: this mechanism moves no fleet grain, so nothing else can "
                "detect that (see this module's docstring)."
            )
        for f, want in INHERITED_FIELDS.items():
            if bool(sc.get(f)) != want:
                raise SystemExit(
                    f"{leg.name}: {f} is {sc.get(f)!r}, expected {want} — this "
                    "leg was solved against the WRONG control, not the "
                    "designated keeper 2026-09-20-soco57-measured-cc-heat"
                )
        if sc.get("coal_prb_sigmoid_overrides") is not None:
            raise SystemExit(
                f"{leg.name}: resolved coal_prb_sigmoid_overrides is "
                f"{sc.get('coal_prb_sigmoid_overrides')!r}, expected null"
            )
        pinned = " ".join(f"{f}={bool(sc.get(f))}" for f in INHERITED_FIELDS)
        print(f"  {leg.name}: {DELTA_FIELD}={got}  {pinned}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--expect-warm",
        required=True,
        choices=("true", "false"),
        help=f"the value {DELTA_FIELD} MUST carry on every leg ('true' for the "
        "soco-58 arm, 'false' for a control composed from keeper-recipe legs)",
    )
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    assert_delta(legs, a.expect_warm == "true")
    _compose(legs, out, INHERITED_MEASURED_BASIS)


if __name__ == "__main__":
    main()
