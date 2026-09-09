"""Write the caiso-fuelvintage-1 bundle's attestation (retiree window + monthly gas LEVEL).

Two bundles are produced this session and each needs a C6 attestation — an unattested C6
makes C3c FAIL instead of reclassifying to a ledgered CAVEAT under the rubric v3.3/v3.6
standing rule.

No control is solved (rule 29 clause (b)). The keeper's own ``git_sha`` (``e162147b``) does
not resolve in this repository, so the ``git diff`` form of G-DRIFT cannot be executed at
all; it was replaced by G-DRIFT-M, a measured detector pre-registered in
``docs/PRECOMMIT-caiso-fuelvintage-2026-09-09.md`` §1 and decided by years the lane solved
anyway. G-DRIFT-M **falsified** G-CTRL form 4: 2024 and 2025 move against the committed
keeper although both of this lane's changes are measured exactly zero there. The cause is
named at zero LP cost by the capx D79 solve-surface fingerprint — CAISO's surface went
202 → 204 rows between ``caiso262`` and HEAD, the two added rows being
``EGRID_CT_HR_PHYSICAL_FLOOR`` and ``F923_GAS_PRICE_PLAUSIBILITY_BAND``.

Pattern unchanged (E10: generated AT registration, never typed): the keeper's committed
attestation is carried, ``attested_by`` re-stamped with the narrative for THIS bundle, and
the ``price_tail`` (C3c) exception magnitudes RE-MEASURED on this bundle's own committed
sidecars. ``free_parameters`` is rebuilt afterwards by ``scripts/build_dof_ledger.py``;
this arm adds NO row — both changes are measured inputs with zero free parameters.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso_fuelvintage_attestation.py \
        --bundle results/calibration/caiso_fuelvintage_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

#: Actual RT hours > $200/MWh (C3c basis; caiso-204 finding §C / keeper ledger).
ACTUAL_TAIL = {2022: 0, 2023: 47, 2024: 35, 2025: 8}
KEEPER = REPO / "results/calibration/caiso260_demand_vintage"

_SHARED = (
    "caiso-fuelvintage-1 session (2026-09-09): TWO MEASURED-INPUT CHANGES, promoted "
    "together on the owner's ruling of 2026-09-09 (handoff "
    "docs/handoffs/xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md SSA7, verbatim: "
    "'these should be promoted as keepers on both 860 and gas shape counts regardless of "
    "inertness'). Pre-registered in docs/PRECOMMIT-caiso-fuelvintage-2026-09-09.md, "
    "pushed before the first LP; measured in docs/RESULT-caiso-fuelvintage-2026-09-09.md. "
    "ZERO new ScenarioConfig fields for CAISO, ZERO free parameters, no derive re-run, no "
    "authorized_price_tuning block, DOF ledger unchanged. "
    "(A) THE EIA-860 RETIREE WINDOW (commit 7934e92c, RETIREMENT_WINDOW_START 2023 -> "
    "2019, artifact 477 -> 1,094 units): a rule 14 [R-ACCURATE] fleet-membership repair, "
    "licensed by the program's supported span and never by a residual. Measured effect on "
    "CAISO's training window, before any solve, by two fleet_only rebuilds per year on the "
    "keeper recipe swapping ONLY the retiree parquet vintage: the 64 injected rows deliver "
    "EXACTLY 0.0000000000 effective MW-h in every year (the COD mask is per-unit and "
    "correct, confirming handoff SSA9 to ten decimals), and 2024 / 2025 are clean at "
    "0.000000. 2023 IS NOT: the plant-level binning folds AES Redondo Beach (plant 356) "
    "gen 7 — 480 MW of ST_GAS retired 2019-10 — into the plant total BEFORE the tranche "
    "split, so its capacity is redistributed onto gens 5/6/8, which survive to 2023-12. "
    "+480.0000 MW exactly across eight tranche rows (144 + 6x44 + 72); +3,367,624.32 "
    "effective MW-h, +0.8478 pct of CAISO 2023. This INDEPENDENTLY CORROBORATES the PJM "
    "lane's cross-ISO finding (docs/FINDING-pjm-retiree-window-redistribution-2026-09-09.md, "
    "W H Sammis, +0.0615 pct) at ~14x PJM's relative size and in a different mechanism "
    "class (gas-ST, not coal). REPORTED AT FULL MAGNITUDE AND NOT REPAIRED HERE: the fix "
    "is in the shared plant-binning path, moves every ISO's fleet in every year, and is an "
    "owner-level call already routed by the PJM lane (rule 25 [R-ISO-SCOPE]). "
    "(B) THE MEASURED MONTHLY GAS LEVEL (gas_electric_power_monthly_level, commit "
    "7648daa0), armed for this bundle and MEASURED PROVABLY INERT for CAISO on two "
    "independent legs, at zero LP cost. COVERAGE: iso_electric_power_monthly_level('CAISO', "
    "y) returns None for 2019 / 2020 / 2021 (California prints 11 of 12 N3045 months in "
    "each), so the admission test refuses those years. ORDERING: on all four ADMITted years "
    "(2022-2025) two fleet_only rebuilds give max |delta fuel_prices| = max |delta mc_base| "
    "= 0.0000000000, 0 of 16,731,600 offer cells moved — the keeper's own "
    "gas_hub_basis_overlay (SoCal / PG&E Citygate) reprices 1,443 gas generators at the "
    "measured hub spot in 12/12 months and supersedes a state-average delivered cost, which "
    "is the ordering the seam was deliberately given (rule 19 [R-ONE-MECH]). The sharpest "
    "case was pre-registered and answered: CAISO Dec-2022, 16.058 $/MMBtu below measured "
    "(~120 $/MWh, the western gas crisis and CAISO's one materially reachable ISO-month), "
    "is INERT for the same reason — the spike is already in the hub index the keeper uses. "
    "The mechanism is NOT refuted; it is unreachable behind a strictly better measured "
    "series. Matrix cell O -> I. "
    "G-DRIFT: the keeper's recorded git_sha e162147b does not exist in this repository, so "
    "the code-audit form cannot be run; the pre-registered measured replacement G-DRIFT-M "
    "FALSIFIED G-CTRL form 4 (2024 max |class-hour delta| 1,979.84 MW, 2025 1,585.38 MW, "
    "in years where both changes are provably zero), and the capx D79 solve-surface "
    "fingerprint attributes it at zero LP cost to CAISO's surface moving 202 -> 204 rows "
    "(f4057d6db19fe8d3 -> cba92d202f32f9fd): EGRID_CT_HR_PHYSICAL_FLOOR and "
    "F923_GAS_PRICE_PLAUSIBILITY_BAND, both gas/CT-side, which is exactly where every "
    "observed delta lives. The drift is HEAD's, not this lane's."
)


def _tail_counts(bundle: Path, years: tuple[int, ...]) -> dict[int, int]:
    """Count model hours above $200/MWh per year from the bundle's own sidecars.

    Args:
        bundle: Bundle directory holding ``hourly/system_<year>.parquet``.
        years: Solve years to measure.

    Returns:
        Mapping of year to the model's count of hours whose max zonal price
        exceeds $200/MWh, measured on this bundle rather than carried.
    """
    counts: dict[int, int] = {}
    for year in years:
        path = bundle / "hourly" / f"system_{year}.parquet"
        if not path.exists():
            continue
        frame = pd.read_parquet(path)
        frame = frame[frame["pass"].astype(str) == "P1"]
        hourly_max = frame.groupby("hour")["price"].max()
        counts[year] = int((hourly_max > 200.0).sum())
    return counts


def main() -> None:
    """Write ``calibration_attestation.json`` for one caiso-fuelvintage-1 bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()

    bundle = args.bundle if args.bundle.is_absolute() else REPO / args.bundle
    meta = json.loads((bundle / "meta.json").read_text())
    years = tuple(int(y) for y in meta["years"])

    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att["governance"]["attested_by"] = (
        f"THIS BUNDLE IS THE ARM (years {', '.join(str(y) for y in years)}). " + _SHARED
    )

    counts = _tail_counts(bundle, years)
    kept = []
    for year in years:
        if year not in counts or ACTUAL_TAIL.get(year, 0) <= 0:
            continue
        kept.append(
            {
                "criterion": "price_tail",
                "year": year,
                "magnitude": (
                    f"model {counts[year]} h vs actual RT {ACTUAL_TAIL[year]} h "
                    "> $200/MWh (RE-MEASURED on this bundle's own committed sidecars)"
                ),
                "rationale": (
                    "C3c scarcity-tail model-class limitation (the ledgered criterion; "
                    "rubric v3.3 standing rule, v3.6 on a held-out year) — adjudication "
                    "belongs to the scorer"
                ),
            }
        )
    att["exceptions"] = kept

    dest = bundle / "calibration_attestation.json"
    dest.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dest}")
    print(f"  years          : {list(years)}")
    print(f"  model tail h   : {counts}")
    print(f"  ledger years   : {[e['year'] for e in kept]}")


if __name__ == "__main__":
    main()
