"""Write the caiso-260 bundle's attestation (the demand-artifact vintage re-derive; NO control solve — G-CTRL form 4).
One bundle is produced this session and it needs a C6 attestation — an
unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT.
No control is solved (rule 29 clause b; G-CTRL form 4): ``_caiso255_gdrift_identity.py``
rebuilt the keeper's LP inputs at ``c78f6d94`` and at HEAD with the demand
artifact committed and found every array bit-identical in all three years
(``results/calibration/_caiso260_gdrift_at_solve.json``), so the caiso-257
keeper IS the control and the re-derived demand artifact is the only live hunk.
Pattern unchanged (E10: generated AT the promotion, never typed): the caiso-257
keeper's committed attestation is carried, ``attested_by`` re-stamped with the
narrative for THIS bundle, and the ``price_tail`` (C3c) exception magnitudes
RE-MEASURED on this bundle's own committed sidecars. ``free_parameters`` is
rebuilt afterwards by ``scripts/build_dof_ledger.py``; this arm adds NO row.
Usage::
    PYTHONPATH=.:src python scripts/gen_caiso260_attestation.py \
        --bundle results/calibration/caiso260_demand_vintage \
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
KEEPER = REPO / "results/calibration/caiso257_ctonly"
_SHARED = (
    "caiso-260 session (2026-09-06): THE DEMAND-ARTIFACT VINTAGE RE-DERIVE - a "
    "rule 14 [R-ACCURATE] / rule 23 [R-FROZEN-DERIVE] measured-input repair, "
    "pre-registered in PRECOMMIT-caiso260-demand-vintage-rederive-2026-09-06.md "
    "and ADDENDUM-caiso260-phase0-2026-09-06.md, both pushed before any LP. THE "
    "OBJECT (ASSESSMENT-caiso259 sec 8): the keeper's demand input, the caiso-80 "
    "Option A supply-consistent series (data/raw/reference/"
    "caiso-supply-consistent-demand/*.csv), had been derived on a bench whose "
    "CEMS anchors read 60.344 / 53.428 TWh (2023/24) and a flat cogen block of "
    "8.399 TWh, while the bench parts C1/C4 are scored against carry 62.209 / "
    "54.588 / 44.429 TWh and cogen 6.604 / 6.416 / 6.416 - the CEMS plant map the "
    "caiso-196 (El Segundo remap, 5f3e35c5), caiso-199 (Desert Star, da33e509) "
    "and caiso-200 (member panel, cf156483) landings widened after the artifact's "
    "2026-07-13 vintage. The keeper's demand basis and its scoring basis therefore "
    "no longer shared a coverage vintage, which is the defect caiso-80 Option A "
    "was written to remove ('the model's demand basis becomes identical to the "
    "honest basis it is scored against'). THE ARM is the committed producer "
    "scripts/data/derive_caiso_supply_consistent_demand.py re-run UNCHANGED at "
    "HEAD on the current bench: its own guards (_ANCHOR_TOL, _ANNUAL_GUARD) pass "
    "untouched, no threshold or window moves, no ScenarioConfig field is added, "
    "and the DOF ledger is unchanged - ZERO free parameters. The re-derive is "
    "licensed by a SOURCE-DATA update (the three bench refreshes above), never by "
    "a residual; no residual is named as its reason and none may be. Measured "
    "before any solve (G-REPRO R-1/R-2/R-3, all PASS): max |delta demand| "
    "1,451.7 / 862.8 / 583.3 MW in an hour, annual +69.4 / -33.0 / -752.7 GWh, "
    "the ONLY moved input column cems_gas_grid_mw, the constant flat term "
    "-204.9 / -136.2 / -136.2 MW (1.8 TWh of 2023 cogen moved from a flat block "
    "into the hourly CEMS term), and the hourly delta IS El Segundo 57901 + "
    "Desert Star 55077 to the MW in 2024/2025 (least-squares coefficients "
    "1.000 / 1.000, R2 0.99998) with a 6.8 pct variance remainder in 2023. "
    "PROMOTION BASIS (owner ruling in the caiso-260 handoff): structural "
    "integrity improving while gates regress MAY still be a keeper; promoted iff "
    "(a) the demand identity holds on the full span (the arm's summed zone "
    "demand equals the re-derived artifact to <1 MW every hour), (b) governance "
    "holds (C6 attested, C8 PASS), (c) every load-bearing criterion that "
    "regresses to a NEW FAIL is reported at full magnitude and put to the owner "
    "in the FINDING before the keeper shard is edited. C3a and C4 enter none of "
    "(a)-(c): C3a is EXCLUDED both ways (caiso-257 was the EIGHTH consecutive "
    "favourable C3a direction in this lane and the streak was declared in the "
    "PRECOMMIT, never quoted), and C4-2025 - at 0.300 against the <=0.30 bound on "
    "the keeper - is supporting-tier: its pre-solve direction statistic "
    "S = sum(e_t * delta_d_t) read NEGATIVE (expected better) in every year with "
    "a first-order bound of at most 1.75 pct of the keeper's MSE, recorded "
    "before the screen. THIS IS NOT THE RULE-1 [R-STRUCT] AUTHORIZED "
    "PRICE-TUNING CHANNEL and declares no authorized_price_tuning block: no "
    "value was chosen against a price, a residual or a gate; a measured input "
    "was brought back onto the vintage the run is scored against. Rule 25: "
    "CAISO's own bench, CAISO's own artifact. Screened under rule 29 on 2023 "
    "(named by the GROSS footprint sum|delta d| = 1,976 GWh, fixed before it was "
    "computed; the handoff's expectation of 2025 was falsified and the rule "
    "governed), STOP-only gates G-IDENT / G-FOOT / S-3 C1 / S-3b C3b, then the "
    "full 2023-2025 span in ONE invocation."
)

_ATTEST = {
    "b1": "THIS BUNDLE IS THE ARM (the re-derived supply-consistent demand artifact on the caiso-257 keeper recipe; the demand input is the ONLY delta). "
    + _SHARED
}


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
    """Carry the caiso-257 keeper attestation onto the caiso-260 bundle."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--arm", choices=sorted(_ATTEST), required=True)
    ap.add_argument(
        "--still-failing",
        type=int,
        nargs="*",
        default=[2024],
        help="years whose C3c still FAILS on this bundle's own scorecard "
        "(the caiso-257 keeper's single ledger year is 2024; pass others if "
        "their C3c flipped on this bundle)",
    )
    args = ap.parse_args()
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST[args.arm]
    counts = _tail_counts(args.bundle)
    tag = "caiso-260 demand-vintage re-derive arm"
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
                    "disclosed PASS->FAIL flip vs the caiso-257 keeper, "
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
