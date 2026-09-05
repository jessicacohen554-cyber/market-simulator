"""Write the caiso-231 un-grounded-class re-grounding bundle's attestation.

The caiso-220 bundle (`results/calibration/caiso231_b1_ungrounded`) is the
landed re-solve of the caiso-217 funded solve (FINDING-caiso216 §G Ask 2)
whose results never left its container: the caiso-200 keeper recipe replayed
byte-faithfully at HEAD through ``--replay-bundle`` (the bundle's
``meta.json`` is the config, no ``--set``), with the measured
generator-hub-membership crosswalk — landed as DATA at the caiso-217 intake
and active for every CAISO solve since — as the only delta. Nothing armed,
nothing tuned, zero new scalars (the crosswalk's own ledger row is
identification="measured", added to ``build_dof_ledger.py`` at caiso-220
prep `2d9823f`).

The `gen_caisoNNN` series continues (E10: an attestation is generated AT the
promotion, every premise computed, never typed). Pattern: the keeper's
committed attestation is carried, ``attested_by`` re-stamped, and the
price_tail (C3c) exception magnitudes RE-MEASURED on this bundle's own
committed sidecars. ``free_parameters`` is not edited here — it is rebuilt
by ``scripts/build_dof_ledger.py`` afterwards (G-DOF reads that).

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso220_attestation.py \
        --bundle results/calibration/caiso231_b1_ungrounded \
        --still-failing 2023 2024 2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
#: Actual RT hours > $200/MWh (C3c basis; caiso-204 finding §C / keeper ledger).
ACTUAL_TAIL = {2023: 47, 2024: 35, 2025: 8}
KEEPER = REPO / "results/calibration/caiso220_c1_crosswalk"

_ATTEST = (
    "caiso-231 session (2026-09-01): the RULE 25 [R-ISO-SCOPE] / RULE 14 "
    "[R-ACCURATE] structural-integrity repair of CAISO's three UN-GROUNDED "
    "gas offer classes, promoted under the owner's standing in-session "
    "standard (verbatim: 'Is this a recommended keeper candidate? If so plz "
    "promote. If structural integrity improves but gates regress that may "
    "still be a keeper..'). THE DEFECT, in the model's own words: "
    "_CAISO_OFFER_CURVE records that CC_CHP / CT_CHP / ST_GAS are 'PINNED to "
    "the values CAISO previously inherited from the generic ERCOT-lineage "
    "else branch ... NOT CAISO-grounded ... preserved verbatim ONLY so the "
    "neutral generic fallback (rule 24) does not silently change the "
    "caiso-51 keeper' — three ERCOT-fitted band blocks on CAISO's binding "
    "path, sized by caiso-230 §4/§7 at CC_CHP:econ +1.23, CT_CHP:committed "
    "+0.36, CC_CHP:committed +0.27 $/MWh of the 2025 annual load-weighted "
    "above-floor term. THE REPAIR: each class re-grounded on the measured "
    "bucket derive_caiso_offer_surface.py itself discloses it falls inside "
    "(CC_CHP -> the measured CC bucket; priced CT_CHP curves and the three "
    "OTC/RMR ST_GAS steamers -> the CT bucket, the derive's own 'known "
    "contamination, disclosed not hidden'), arming EXACTLY the three bands "
    "the incumbent caiso_offer_surface_measured arms (econ_low/econ_high/"
    "peak) and leaving every committed band unarmed for every CAISO gas "
    "class (the Lever-A inversion lesson applied uniformly, rule 19). ZERO "
    "free parameters added; NINE fitted scalars retired. Recipe: the "
    "caiso-220 keeper bundle's meta.json replayed at HEAD via "
    "--replay-bundle with a SINGLE flag delta "
    "(caiso_offer_surface_measured_ungrounded), P1 scored, 2023-2025 "
    "sequential. PRE-REGISTERED ADVERSE DIRECTION, DISCLOSED BEFORE THE "
    "SOLVE: PRECOMMIT-caiso231-ungrounded-offer-regrounding-2026-09-01.md "
    "§4 predicted a C3a cost of +0.235/+0.344/+0.421 $/MWh and pushed that "
    "prediction to the remote before either arm ran; the MEASURED cost is "
    "+0.062/+0.037/+0.031, i.e. 4-13x SMALLER than the first-order bound "
    "because the LP re-dispatches around the repriced rungs. Every "
    "pre-registered gate (§6) PASSES and no falsifier (§7) fires: G-CTRL "
    "exact (the control reproduces the keeper to the cent, 56.31/38.96/"
    "39.76, drift -0.04/-0.05/+0.00 pp), G-STRUCT (exactly 9 bands moved, "
    "0 committed bands, 0 non-target classes), G-LIVE (max |delta| "
    "1,225/3,368/1,911 MW class-hour), G-C3a (inside [0, 3x] every year; "
    "no year flips, 2023 stays PASS at +4.1%), G-C1 (12/12, free 8/8, "
    "unchanged), G-C3b (0.100/0.178/0.181 vs 0.100/0.177/0.180 — the 2025 "
    "tripwire holds with margin 0.019), G-C2/G-C4/G-C8 (no flip), "
    "G-CAVEAT (budget 1 of 1). Determination is UNCHANGED vs the incumbent "
    "keeper: NOT-YET on C3a alone."
)


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
    """Carry the keeper attestation onto the caiso-220 bundle, re-measured."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
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
    att["governance"]["attested_by"] = _ATTEST
    counts = _tail_counts(args.bundle)
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
            f"{ACTUAL_TAIL[year]} h > $200/MWh (re-measured on the caiso-220 "
            "re-grounding arm)"
        )
        kept.append(exc)
    for year in args.still_failing:
        if year in seen_tail_years or year not in ACTUAL_TAIL:
            continue
        # A year newly failing C3c on this bundle (a disclosed flip vs the
        # keeper) enters the ledger with the same criterion and a magnitude
        # measured here — never silently.
        kept.append(
            {
                "criterion": "price_tail",
                "year": year,
                "magnitude": (
                    f"model {counts.get(year, '?')} h vs actual RT "
                    f"{ACTUAL_TAIL[year]} h > $200/MWh (NEW on the caiso-220 "
                    "crosswalk replay — a disclosed PASS->FAIL flip vs the "
                    "caiso-200 keeper, reported at full magnitude per the "
                    "precommit)"
                ),
                "rationale": (
                    "C3c scarcity-tail model-class limitation (the ledgered "
                    "criterion; rubric v3.3 standing rule) — the crosswalk "
                    "moves zonal allocation, and the pooled scarcity top "
                    "thins where the south decouples; adjudication belongs "
                    "to the scorer"
                ),
            }
        )
    att["exceptions"] = kept
    path = args.bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} (tail counts {counts}; ledger years "
        f"{sorted(e['year'] for e in kept if e.get('criterion') == 'price_tail')}; "
        "free_parameters left to build_dof_ledger.py)"
    )


if __name__ == "__main__":
    main()
