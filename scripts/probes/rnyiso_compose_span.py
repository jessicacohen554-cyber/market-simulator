"""R-NYISO (ZERO LP): compose the per-year corrected-input legs into one span bundle.

Rule 36 ``[R-YEAR-ISOLATION]`` (a) solves each backcast year in its own shard;
rule 34 ``[R-SHARD-PROMOTABLE]`` (a) makes each shard push its FULL bundle, so
the legs compose without a re-solve.

**REUSE, NOT A FORK.** The composition is
:mod:`scripts.probes.nyiso238_compose_span`, NYISO's own recipe (also used by
nyiso-247 and hydro-3). This module adds the lane's leg-acceptance checks from
``docs/PRECOMMIT-r-nyiso-backcast-inputs-2026-09-24.md`` §6, read from the
RESOLVED ``scenario_config`` (never the ``prb_overrides`` bag the CLI routed the
flags through), before any file is copied:

* S0 -- every leg was solved at the pinned PRECOMMIT SHA;
* S1 -- the F1 backcast posture is ON (year-matched EIA-860 vintage + all five
  measured heat-rate classes), the unarmed outage families are OFF, and the
  offer-curve block is byte-equal to the incumbent keeper's (rule 1(c): an
  input correction is never re-tuned);
* S2 -- the armed CAMPD outage extract and thermal tranches are the keeper's bytes.

A leg that silently solved the pre-F1 posture would otherwise compose in looking
like a null result.

Usage::

    python3 scripts/probes/rnyiso_compose_span.py \\
        --legs results/calibration/rnyiso_{2022,2023,2024,2025} \\
        --out  results/calibration/rnyiso_span

    # leg acceptance only (R-NYISO-2021: a held-out year registered on its own and
    # stamped to the keeper, never composed into it):
    python3 scripts/probes/rnyiso_compose_span.py --check-only \\
        --legs results/calibration/rnyiso_2021
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

#: The keeper the legs are checked against. R-NYISO checked its 2022-2025 legs against
#: ``hydro3_nyiso_ror_span`` (pinned ``e95436d5``); that bundle was pruned at the
#: 2026-09-25 promotion, so R-NYISO-2021 checks against the promoted keeper, whose
#: offer block is byte-identical to hydro3's (R-NYISO S1).
KEEPER = _REPO / "results" / "calibration" / "rnyiso_span"
#: R-NYISO-2021 PRECOMMIT (docs/PRECOMMIT-r-nyiso-2021-2026-09-25.md) commit SHA.
PIN = "__PIN__"
#: (resolved scenario_config field, required value) -- PRECOMMIT §6 S1.
EXPECTED = (
    ("eia860_vintage_tracks_solve_year", True),
    ("measured_ct_heat_rates", True),
    ("measured_coal_heat_rates", True),
    ("measured_st_heat_rates", True),
    ("measured_cc_heat_rates", True),
    ("measured_chp_heat_rates", True),
    ("hydro_ror_split", True),
    ("unit_partial_outage_windows", False),
    ("unit_outage_short_windows", False),
    ("unit_outage_short_windows_gas", False),
)
#: PRECOMMIT §6 S2 -- the keeper's own resolved input bytes.
INPUT_SHA = {
    "campd_unit_outages": "ee778a87d3739341a7c578078b5e0194545f9231efbef2cd32d72e88e0aa21fa",
    "thermal_tranches": "a3bbd6ef408ea8175c1fa73bb3f016bf2e4cd9e0984ceac08e6dfd93534d8376",
}


#: The ONE key a HEAD solve may lack relative to the keeper: #6611 retired the bare
#: ``COAL`` class, so ``scenarios._retire_bare_coal_class`` folds (drops) it when the
#: four subclasses are also present -- which they are in the keeper, with their own
#: bands. No NYISO unit reads it (0 coal units 2020-2024; R-NYISO-2021 PRECOMMIT §3).
FOLDED_KEYS = ("COAL",)


def _offer_block(rc: dict, fold: bool = False) -> str:
    """Canonical JSON of every offer-curve surface a run_config carries.

    ``fold=True`` drops :data:`FOLDED_KEYS` from ``offer_curve_by_group`` (used on
    the keeper side, which was solved before the bare-coal fold existed).
    """
    sc = rc.get("scenario_config") or {}
    cf = rc.get("calibration_flags") or {}
    ocg = sc.get("offer_curve_by_group")
    if fold and isinstance(ocg, dict):
        ocg = {k: v for k, v in ocg.items() if k not in FOLDED_KEYS}
    return json.dumps(
        {
            "offer_curve_by_group": ocg,
            "offer_curve_overrides": cf.get("offer_curve_overrides"),
            "offer_curve_deltas": cf.get("offer_curve_deltas"),
        },
        sort_keys=True,
    )


def check_legs(legs: list[Path]) -> None:
    """Fail loud if any leg misses the PRECOMMIT's S0-S2 acceptance."""
    keeper_offers = _offer_block(
        json.loads((KEEPER / "run_config.json").read_text()), fold=True
    )
    bad: list[str] = []
    for leg in legs:
        rc = json.loads((leg / "run_config.json").read_text())
        sc = rc.get("scenario_config") or {}
        errs = []
        basis = (rc.get("git") or {}).get("basis_sha") or ""
        if basis != PIN:
            errs.append(f"S0 basis_sha {basis!r}")
        for f, v in EXPECTED:
            if sc.get(f) is not v:
                errs.append(f"S1 {f}={sc.get(f)!r}")
        if _offer_block(rc) != keeper_offers:
            errs.append("S1 offer-curve block differs from the keeper")
        ri = rc.get("resolved_inputs") or {}
        for name, sha in INPUT_SHA.items():
            got = (ri.get(name) or {}).get("sha256")
            if got != sha:
                errs.append(f"S2 {name} sha256 {got!r}")
        print(f"  {leg.name}: {'OK' if not errs else errs}")
        if errs:
            bad.append(leg.name)
    if bad:
        raise SystemExit(
            f"legs {bad} fail the PRECOMMIT leg acceptance; refusing to compose"
        )


def main() -> None:
    """Check every leg, then compose the span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true", help="S0-S2 only; compose nothing")
    args = ap.parse_args()
    legs = [Path(x) for x in args.legs]
    check_legs(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    _compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
