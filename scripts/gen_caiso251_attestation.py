"""Write the caiso-251 bundle's attestation (the B1 arm; NO control solve — G-CTRL form 4).

One bundle is produced this session and it needs a C6 attestation — an
unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT.
No control is solved: owner rule 2026-09-05 (rule 29 ``[R-SCREEN]`` clause b)
makes G-CTRL **form 4** the default, and the G-DRIFT code audit in
``PRECOMMIT-caiso251-fuel-coupling-form-2026-09-05.md`` Addendum B establishes
that every changed hunk on the backcast path between the keeper's ``git_sha``
900402b and HEAD is CAISO-backcast-inert, so the committed keeper IS the
control.

The ``gen_caisoNNN`` series pattern is unchanged (E10: an attestation is
generated AT the promotion, every premise computed, never typed): the caiso-246
keeper's committed attestation is carried, ``attested_by`` is re-stamped with
the narrative for THIS bundle, and the ``price_tail`` (C3c) exception
magnitudes are RE-MEASURED on this bundle's own committed sidecars.
``free_parameters`` is not edited here — ``scripts/build_dof_ledger.py``
rebuilds it afterwards.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso251_attestation.py \
        --bundle results/calibration/caiso251_arm_nomargin \
        --arm b1 --still-failing 2023 2024
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

YEARS = (2023, 2024, 2025)
#: Actual RT hours > $200/MWh (C3c basis; caiso-204 finding §C / keeper ledger).
ACTUAL_TAIL = {2023: 47, 2024: 35, 2025: 8}
KEEPER = REPO / "results/calibration/caiso246_b1_spot_coverage"

_SHARED = (
    "caiso-251 session (2026-09-05): the RULE 14 [R-ACCURATE] / RULE 25 "
    "[R-ISO-SCOPE] / RULE 1 [R-STRUCT] FUNCTIONAL-FORM repair of the CAISO gas "
    "offer's FUEL COUPLING. THE OBJECT (PRECOMMIT-caiso251-fuel-coupling-form-"
    "2026-09-05.md §0, queue item A of caiso-250 taken at its FORM rather than "
    "its level): the keeper armed gas_offer_net_revenue_margin, which prices "
    "every CAMPD gas tranche carrying a measured physical basis as phys x "
    "HR_base x fuel(t) + (mult - phys) x HR_base x anchor, i.e. the "
    "above-physical markup is a fuel-INVARIANT $/MWh margin identified at a "
    "$4.7964/MMBtu anchor (1,269/1,274/1,279 tranches, median fixed margin "
    "$14.37/MWh). THAT FORM'S IDENTIFICATION IS NEISO'S (the 2022 holdout "
    "rotation, neiso-45/46/47) AND CAISO'S OWN OASIS RECORD REFUTES IT FOR "
    "CAISO: caiso-242 §3.5 measured the band multiplier FLAT across a 1.93x "
    "fuel swing (CT_PEAKER econ_low range 0.013 against the 0.2775 the armed "
    "decomposition requires — 21.3x), the signature of the MULTIPLICATIVE "
    "form; and caiso-229 §5 measured the consequence, a model CC floor "
    "coupling to the CA citygate of 2.18/2.18/4.34 MMBtu/MWh against CAISO's "
    "MEASURED DAM body coupling of 6.7-7.4 — UNDER-coupled to fuel, "
    "'because the affine measured-marginal-HR + fixed-margin form is ALREADY "
    "armed'. THE ARM: the SINGLE flag --no-gas-offer-margin on the replayed "
    "keeper recipe. ZERO new parameters and zero new fields; the $4.7964 "
    "anchor is REMOVED (a rule-24 [R-DELETE] shrink), and under the armed "
    "caiso_offer_surface_measured the restored form is mult x HR_base x "
    "fuel(t) with mult the MEASURED OASIS multiplier — the form the OASIS "
    "record identifies. Per-year measured multipliers are rule-13 "
    "inadmissible (a same-year measured OUTCOME pin, PREREG-miso146 §9) and "
    "were NOT proposed. PHASE 0 (zero LP, two on-recipe fleet_only rebuilds "
    "differing in ONE kwarg; _caiso251_fuel_coupling_form.json): G-IDENT "
    "PASSES — the delta IS (mult-phys) x HR_base x (fuel-anchor) with a max "
    "within-tranche spread of the implied markup-HR of 4e-12 MMBtu/MWh; "
    "G-FOOTPRINT PASSES with ZERO non-gas tranches touched; and G-COUPLE, the "
    "load-bearing structural gate whose failure would have spent NO solve, "
    "PASSES in all three years — the disarmed CC_REGULAR econ Theil-Sen "
    "coupling is 6.719 MMBtu/MWh, inside the pre-registered [6.0, 8.0] band "
    "AND inside CAISO's measured DAM body coupling 6.7-7.4. As a ratio to each "
    "class's OWN measured base heat rate the armed form leaves CC at "
    "0.754/0.810/0.810 and CT at 0.526/0.559/0.532 against a measured 0.9-1.0, "
    "while disarmed they land at 0.903 and 0.877/0.932/0.919: the "
    "fixed-margin form HALVES CT's physical fuel sensitivity and flattens the "
    "two classes onto nearly one slope, which is the CC-hot/CT-cold split's "
    "mechanism measured from CAISO's own record rather than from the "
    "residual. RULE 29 [R-SCREEN] (owner rule, issued mid-session): the arm "
    "was SCREENED on 2024 alone before the full span — screen year chosen on "
    "the phase-0 FOOTPRINT (largest |fuel-anchor|), never on the residual — "
    "and G-SCREEN-A (non-gas confined, max 0.051 TWh vs a registered 0.5) and "
    "G-SCREEN-B (CT_PEAKER+CT_CHP RISES, +0.742 TWh) both PASSED, earning the "
    "remaining two years; G-SCREEN-C was NOT EVALUABLE as written and is "
    "reported as a defect in the session's own gate. G-CTRL is FORM 4 with NO "
    "control solve spent (owner rule 29 clause b), restored by the G-DRIFT "
    "audit of 900402b..HEAD (22 files, +2527/-149, EVERY hunk "
    "CAISO-backcast-inert with its reason cited). G-REPRO: the full arm's 2024 "
    "reproduces the screen's 2024 to 4e-5 on the load-weighted price, "
    "CT_PEAKER energy and all 13 class energies. C3a IS EXCLUDED FROM THE "
    "PROMOTION BASIS IN BOTH DIRECTIONS, declared before any measurement as "
    "the SIXTH consecutive favourable direction (PRECOMMIT §0.2), and the "
    "promotion rule registered with it turns on G-COUPLE plus the absence of a "
    "new non-C3a load-bearing failure — it can keep this run even if C3a "
    "worsens, and refuse it even if C3a improves."
)

_B1 = "THIS BUNDLE IS THE B1 ARM (single-flag delta). " + _SHARED

_ATTEST = {"b1": _B1}


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model hours > $200 per year on the scorer's max-zonal basis."""
    out: dict[int, int] = {}
    for year in YEARS:
        p = bundle / "hourly" / f"system_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["year"] == year) & (df["pass"] == "P1")]
        out[year] = int((df.groupby("hour")["price"].max() > 200.0).sum())
    return out


def main() -> None:
    """Carry the caiso-246 keeper attestation onto the caiso-251 bundle."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--arm", choices=sorted(_ATTEST), required=True)
    ap.add_argument(
        "--still-failing",
        type=int,
        nargs="*",
        default=[2023, 2024],
        help="years whose C3c still FAILS on this bundle's own scorecard "
        "(the keeper's ledger years are 2023 2024; pass 2025 too if its "
        "C3c flipped on this bundle)",
    )
    args = ap.parse_args()
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST[args.arm]
    counts = _tail_counts(args.bundle)
    tag = "caiso-251 B1 arm"
    kept = []
    seen_tail_years = set()
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") != "price_tail":
            kept.append(exc)
            continue
        seen_tail_years.add(year)
        if year not in args.still_failing:
            continue  # band met on this bundle — a spent caveat is dropped
        exc["magnitude"] = (
            f"model {counts.get(year, '?')} h vs actual RT "
            f"{ACTUAL_TAIL[year]} h > $200/MWh (re-measured on the {tag})"
        )
        kept.append(exc)
    for year in args.still_failing:
        if year in seen_tail_years or year not in ACTUAL_TAIL:
            continue
        kept.append(
            {
                "criterion": "price_tail",
                "year": year,
                "magnitude": (
                    f"model {counts.get(year, '?')} h vs actual RT "
                    f"{ACTUAL_TAIL[year]} h > $200/MWh (NEW on the {tag} — a "
                    "disclosed PASS->FAIL flip vs the caiso-246 keeper, "
                    "reported at full magnitude per the precommit)"
                ),
                "rationale": (
                    "C3c scarcity-tail model-class limitation (the ledgered "
                    "criterion; rubric v3.3 standing rule) — adjudication "
                    "belongs to the scorer"
                ),
            }
        )
    att["exceptions"] = kept
    path = args.bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} ({tag}; tail counts {counts}; ledger years "
        f"{sorted(e['year'] for e in kept if e.get('criterion') == 'price_tail')}; "
        "free_parameters left to build_dof_ledger.py)"
    )


if __name__ == "__main__":
    main()
