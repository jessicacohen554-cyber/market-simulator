"""Write the caiso-257 bundle's attestation (the CT-only partition arm; NO control solve — G-CTRL form 4).

One bundle is produced this session and it needs a C6 attestation — an
unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT.
No control is solved: owner rule 2026-09-05 (rule 29 ``[R-SCREEN]`` clause b)
makes G-CTRL **form 4** the default, and this session's G-DRIFT is a
MEASUREMENT rather than a reading — ``_caiso255_gdrift_identity.py`` rebuilt
the keeper's LP inputs at ``fa23c1f7`` and at the solve sha with the artifact
pair reverted and found **every array bit-identical in all three years**
(``results/calibration/_caiso257_gdrift_at_solve.json``,
``ADDENDUM-caiso257-s1-recharter-2026-09-06.md §6.1``), so the committed
keeper IS the control and the artifact pair is the only live hunk.

The ``gen_caisoNNN`` series pattern is unchanged (E10: an attestation is
generated AT the promotion, every premise computed, never typed): the caiso-252
keeper's committed attestation is carried, ``attested_by`` is re-stamped with
the narrative for THIS bundle, and the ``price_tail`` (C3c) exception
magnitudes are RE-MEASURED on this bundle's own committed sidecars.
``free_parameters`` is not edited here — ``scripts/build_dof_ledger.py``
rebuilds it afterwards, and this arm adds NO row to it (see the narrative).

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso257_attestation.py \
        --bundle results/calibration/caiso257_ctonly \
        --arm b1 --still-failing 2024
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
KEEPER = REPO / "results/calibration/caiso252_b1_notrim"

_SHARED = (
    "caiso-257 session (2026-09-06): the CT-ONLY OASIS CLASS-PARTITION REPAIR "
    "- the owner's grant of FINDING-caiso254 sec 4 OPTION 1, pre-registered in "
    "PRECOMMIT-caiso255-ct-only-partition-adoption-2026-09-06.md and screened "
    "under rule 29 [R-SCREEN] on a RE-CHARTERED S-1 "
    "(ADDENDUM-caiso257-s1-recharter-2026-09-06.md, pushed before the artifact "
    "pair was re-applied and before any LP). THE OBJECT: CAISO's measured "
    "offer surface pools its high-heat-rate gas STEAMERS into the CT_PEAKER "
    "bucket, so the CT band multipliers were a statistic contaminated by a "
    "class that is not a peaker. caiso-254 located the second cut as the "
    "CT-side capacity-density ANTIMODE at 11.738 MMBtu/MWh - inside the "
    "pre-registered [10.9, 12.5] window fixed from published fleet heat rates, "
    "never swept and never chosen against any criterion (G-BIMODAL PASS, 2.559 "
    "GW above it inside the registered [1.5, 4.5] GW) - and the derive's own "
    "G4 physical-sanity gate then REFUSED the separated ST_GAS bucket (peak "
    "1.196 inverted 0.350 below econ_high 1.546). The owner granted OPTION 1: "
    "write CC + CT, publish ST_GAS as _provenance.reported_not_consumed with "
    "its G4 FAIL verbatim. G4 IS NOT RELAXED, no threshold is retuned, hr_cut "
    "stays 8.5 (rule 23 [R-FROZEN-DERIVE]), and the de-contamination happens "
    "in the CLASSIFICATION, not the consumption - the steamers leave the CT "
    "bucket by being classified ST_GAS, so omitting the ST_GAS entry does not "
    "put them back (caiso-255 P-3, verified byte-identical). "
    "THE EVIDENCE IT RESTS ON CONTAINS NO PRICE, and that is registered ex "
    "ante (PRECOMMIT-caiso255 sec 3.1): G-BIMODAL plus the G1 capacity "
    "reconciliation - the pooled CT bucket's 9,950 MW against its own "
    "published 7,616 MW fleet, a 30 pct excess, collapses to 7,391 MW / 3 pct "
    "when the high-HR mode is separated. ALL THREE CT BANDS FALL (econ_low "
    "1.145 -> 1.103, econ_high 1.166 -> 1.146, peak 1.166 -> 1.154) and the "
    "keeper's open residual is a C3a OVERSHOOT, so the repair moves price in "
    "the direction the residual wants; that was declared UNUSABLE AS EVIDENCE "
    "before the artifact existed and C3a is EXCLUDED FROM THE PROMOTION BASIS "
    "IN BOTH DIRECTIONS, together with C4. "
    "ZERO FREE PARAMETERS (rule 21 [R-DOF]): every operand already existed, "
    "--st-split-report-only is a boolean SCOPE switch on a derive and not a "
    "solve-affecting ScenarioConfig field, and NO DOF ledger row is added - "
    "the ledger stays at 9 entries / 6 residual. THIS IS NOT THE RULE-1 "
    "[R-STRUCT] AUTHORIZED PRICE-TUNING CHANNEL and declares no "
    "authorized_price_tuning block: no band multiplier was chosen against a "
    "price, a residual or a gate; the bands moved because a contaminated "
    "population was corrected, which is rule 14 [R-ACCURATE] and rule 13 "
    "[R-MEASURED] (CAISO's own OASIS record, pooled 2023-2025, ONE "
    "construction across every scored year; per-year multipliers remain "
    "inadmissible and were not proposed). Rule 25 [R-ISO-SCOPE]: CAISO's own "
    "bid record throughout. "
    "THE SCREEN, AND THE ESTIMATOR THAT WAS REPLACED - reported because it is "
    "the uncomfortable half. caiso-256 screened this same arm on 2023 and it "
    "DIED on S-1: the arm's measured CT_PEAKER rise of +219.8 GWh fell below a "
    "311.8 GWh floor derived from a price-held-fixed tranche count that "
    "over-counted 4.26x, because sibling tranches of ONE plant whose bands all "
    "contain lambda were each charged their full pmax in the same hour. The "
    "owner re-chartered S-1 on the plant-deduplicated form (at most one "
    "tranche's worth of MW per plant-hour, dE_dedup 261.5 GWh over 79 plants, "
    "band [87.2, 784.5]) KNOWING the prior result - stated at the top of the "
    "addendum, not in a footnote - and adopted it on its construction (a plant "
    "cannot displace its capacity twice in one hour), never because it passes. "
    "The re-screen therefore carries NO claim of out-of-sample surprise and "
    "none is made anywhere in this bundle's record. Its own bias runs the "
    "other way (LOW: a plant whose several tranches genuinely clear displaces "
    "their sum, not their max), so the two estimators bracket the truth; the "
    "factor of 3 was carried unchanged and NO third estimator is permitted. "
    "THE ARM'S KNOWN STRUCTURAL COST, reported not buried (FINDING-caiso256 "
    "sec 3): the +220 GWh lands on p57482/p57515/p57555 (462/375/281 GWh), the "
    "three LA-basin/SDGE peakers, and NOT on Panoche 56803 (172), so the arm "
    "moves the CT class toward its C1 actual through the wrong plants and "
    "DEEPENS the caiso-252 sec 3.3 mis-allocation. The owner ruled the arm "
    "wanted on that record: it is right about the measured OFFER and silent "
    "about the PLANT, which is a separate open object, and caiso-252 sec 7 #4 "
    "forbids reaching Panoche by re-pricing the class. This bundle claims no "
    "closure of the CT volume miss."
)

_ATTEST = {"b1": "THIS BUNDLE IS THE ARM (the df277e89 artifact pair on the caiso-252 keeper recipe; the offer surface is the ONLY delta). " + _SHARED}


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
    """Carry the caiso-252 keeper attestation onto the caiso-257 bundle."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--arm", choices=sorted(_ATTEST), required=True)
    ap.add_argument(
        "--still-failing",
        type=int,
        nargs="*",
        default=[2024],
        help="years whose C3c still FAILS on this bundle's own scorecard "
        "(the caiso-252 keeper's single ledger year is 2024; pass others if "
        "their C3c flipped on this bundle)",
    )
    args = ap.parse_args()
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST[args.arm]
    counts = _tail_counts(args.bundle)
    tag = "caiso-257 CT-only partition arm"
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
                    "disclosed PASS->FAIL flip vs the caiso-252 keeper, "
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
