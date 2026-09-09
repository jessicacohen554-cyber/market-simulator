"""Write the caiso-267 bundle's attestation — the fossil offer-band x0.92 arm.

The bundle needs a C6 attestation (an unattested C6 makes C3c FAIL instead of
reclassifying to a ledgered CAVEAT), and this arm additionally needs the rule 1
``[R-STRUCT]`` carve-out declaration: it uses the AUTHORIZED PRICE-TUNING
CHANNEL, so ``governance.authorized_price_tuning`` must be present and
well-formed or ``calibration_verdict.score_governance`` fails C6 outright
(``AUTHORIZED_TUNING_FIELDS``).

Pattern unchanged from ``gen_caiso260_attestation.py`` (E10: generated AT the
promotion, never typed): the incumbent keeper's committed attestation is
carried, ``attested_by`` re-stamped with THIS bundle's narrative, and the
``price_tail`` (C3c) exception magnitudes RE-MEASURED on this bundle's own
committed sidecars. ``free_parameters`` is rebuilt afterwards by
``scripts/build_dof_ledger.py``.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso267_attestation.py \
        --bundle results/calibration/caiso267_fossil92 --still-failing 2024
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
KEEPER = REPO / "results/calibration/caiso260_demand_vintage"
CURVE = REPO / "results/calibration/_caiso267_fossil92_offer_curve.json"
SCALE = 0.92

_ATTEST = (
    "THIS BUNDLE IS THE ARM: the caiso-260 keeper recipe with EVERY fossil "
    "offer_curve_by_group band multiplier scaled by 0.92, and NOTHING ELSE. "
    "caiso-267 session (2026-09-09). OWNER RULING, mid-session, verbatim: "
    "'pivot to a solve that reduces fossil [offer] curves by 8% across the "
    "board because they are overshooting significantly', and on being shown "
    "that CAISO's MEASURED offer surface points the other way, 'I don't care "
    "what measured says just adjust it 8% downward'. THIS IS THE RULE 1 "
    "[R-STRUCT] / RULE 13 [R-MEASURED] AUTHORIZED PRICE-TUNING CHANNEL and it "
    "is DECLARED as such in governance.authorized_price_tuning below — it is "
    "NOT a rule 14 [R-ACCURATE] measured-input repair and is never described "
    "as one. Two objections were raised to the owner BEFORE the solve and the "
    "owner reaffirmed: (1) caiso-266 §7 measured CAISO's pooled 2023-2025 CC "
    "bands at committed 1.030 vs armed 1.000 and econ_low/econ_high/peak at "
    "EXACTLY their armed 1.066/1.072/1.386, so a measured-faithful repair "
    "moves the CAISO belly price UP while this run moves it DOWN; (2) the "
    "ruling's stated motivation ('bring 2021 in tolerance') cannot be acted "
    "on — 2021 is validation tier (rule 22), is NOT touched by this run, and "
    "is not scoreable today (no 2021 row in actual_lmp_hourly_CAISO.parquet, "
    "no bench part, a 60-day RTM source gap 2021-08-02..09-30, and a "
    "CAISO_PARTIAL_YEARS amendment CAISO cannot grant itself). The factor was "
    "NOT selected against 2021 or against any gate, and was NOT swept. "
    "PRE-REGISTERED in PRECOMMIT-caiso267-belly-conduct-measured-2026-09-09.md "
    "+ ADDENDUM-caiso267-fossil-offer-8pct-2026-09-09.md, both pushed BEFORE "
    "the first LP. SCREENED on 2023 under rule 29 [R-SCREEN] (screen year "
    "named ex ante by the mechanism's own footprint — largest on BOTH the $ of "
    "offer re-pricing, $171.5M, and raw fossil energy, 60.28 TWh — and "
    "simultaneously the year with the SMALLEST residual, so the choice is "
    "demonstrably not residual-driven; a residual-driven choice picks 2024): "
    "G-IDENT max |demand delta| 0.000 MW over 61,320 zone-hours, G-FOOT fossil "
    "+2.3444 TWh vs non-fossil -2.3475 (conservation residual -0.0031), G-DIR "
    "d lambda -2.8497 $/MWh against a PRE-SOLVE prediction of -2.845, G-NOFLIP "
    "C1/C2/C3b/C4 all PASS->PASS. G-CTRL: form 4 was NOT claimed because the "
    "G-DRIFT audit measured 94 files / +46,838 lines on the backcast solve "
    "path since the keeper's merge commit bdfb3095 and a credible hunk-by-hunk "
    "INERT classification was not achievable; a 2023-only control was spent "
    "instead (rule 29(b)), and it MEASURED the drift at +0.0043 $/MWh with "
    "demand identical to the MWh — i.e. form 4 would have been valid. "
    "DISCLOSED BEFORE THE SOLVE (addendum §G): C3a was expected to be able to "
    "cross zero because the cut is the same order as the whole residual in "
    "every year, and C4-2025 sits at 0.298 against a <=0.300 tolerance. "
    "DISCLOSED PHYSICS: the cut moves CT_PEAKER.committed from exactly its "
    "measured phys_committed (0.991) to 8% below it, and CT_CHP.committed from "
    "1.100 to 1.012 against phys 1.073 — two NEW crossings of the measured "
    "physical min-load heat rate; CC_REGULAR/CC_CHP committed and peak and "
    "ST_GAS committed were already below theirs on the keeper and are "
    "deepened. phys_* is inert in this recipe "
    "(gas_offer_net_revenue_margin=false) and was NOT touched."
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


def _tuning_declaration(years: list[int]) -> dict:
    """The rule 1 [R-STRUCT] carve-out declaration, conditions (a)-(e).

    Args:
        years: The bundle's OWN scored years — condition (b) is checked by exact
            set equality against them, so a 2022-only bundle must declare
            ``[2022]`` and a full-span bundle ``[2023, 2024, 2025]``. The factor
            is identical either way; only the span differs.
    """
    curve = json.loads(CURVE.read_text())
    return {
        "channel": "offer_curve_by_group",
        "ruling": (
            "Owner ruling 2026-09-09, mid-session, verbatim: 'pivot to a solve "
            "that reduces fossil [offer] curves by 8% across the board because "
            "they are overshooting significantly'; reaffirmed after objection "
            "as 'I don't care what measured says just adjust it 8% downward'. "
            "Authorized by the rules 1 [R-STRUCT] / 13 [R-MEASURED] carve-out "
            "of 2026-09-05."
        ),
        "value": {
            "scalar": SCALE,
            "cut_pct": round((1.0 - SCALE) * 100.0, 3),
            "bands": sum(len(v) for v in curve.values()),
            "applied_to": {k: sorted(v) for k, v in sorted(curve.items())},
            "excluded": (
                "every phys_* key (measured physics), econ_low_share and "
                "pct_peaking (the structural shares), and peak_ladder — which "
                "is NOT separately parameterised: the CAISO conditional split "
                "rebuilds it from the post-override peak, so the five uniform "
                "rungs follow the cut automatically and the 'N equal sub-bands "
                "at one MC == one flat band' identity is preserved. The three "
                "*_INTERMEDIATE classes are excluded because the offer-curve "
                "router does not read them (and they carry zero CAISO energy "
                "in all three years); ST_CHP is excluded because the keeper's "
                "resolved curve has no entry for it, so adding one would be a "
                "new parameter rather than a cut of an existing one."
            ),
            "file": "results/calibration/_caiso267_fossil92_offer_curve.json",
        },
        # Rule 1 (b) is tested by EXACT SET EQUALITY against the RUN's own scored
        # years (calibration_verdict._authorized_tuning_finding), so this must be
        # the bundle's span, not this module's default. Hardcoding YEARS here made
        # C6 FAIL outright on the 2022-only shard bundle — found by the caiso-267
        # shard, RESULT-caiso267-shard-2022-retest-2026-09-09.md §4(1). The
        # SUBSTANCE of (b) is untouched and is the point: ONE config, the single
        # ex-ante constant 0.92 over the same 40 bands, held identically across
        # every year any bundle scores. No per-year value exists.
        "years_held": years,
        "set_ex_ante": True,
        "not_swept": True,
        "identification": (
            "NONE — and that is the point. 0.92 is an owner-supplied ex-ante "
            "constant, not a value identified against anything. No gate, no "
            "residual and no criterion was consulted to choose it, in this "
            "session or before it. Condition (c) forbids selecting a factor "
            "because it makes a criterion pass, so the factor is NOT resized "
            "after the fact in either direction, whatever the full-span "
            "scorecard says."
        ),
        "prereg": (
            "results/calibration/ADDENDUM-caiso267-fossil-offer-8pct-2026-09-09.md "
            "(pushed BEFORE the first LP), on "
            "PRECOMMIT-caiso267-belly-conduct-measured-2026-09-09.md"
        ),
        "disclosure": (
            "AGAINST INTEREST: this run moves the CAISO gas offer surface AWAY "
            "from CAISO's own measured DAM bids. caiso-266 §7 measured the "
            "pooled 2023-2025 CC bands at or ABOVE their armed values "
            "(committed 1.030 vs 1.000; econ_low/econ_high/peak exactly equal), "
            "so the measured-faithful direction is UP. The owner was shown this "
            "before the solve and ruled anyway; it is recorded so a later "
            "reader judges the ruling rather than a silence. Rule 25 "
            "[R-ISO-SCOPE]: the cut is a CLI override on a CAISO invocation and "
            "touches no shared default, no constants.py value and no other "
            "ISO's curve."
        ),
    }


def main() -> None:
    """Carry the caiso-260 keeper attestation onto the caiso-267 bundle."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--still-failing", type=int, nargs="*", default=[2024])
    args = ap.parse_args()

    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST
    _bundle_years = sorted(
        int(y) for y in json.loads((args.bundle / "meta.json").read_text())["years"]
    )
    att["governance"]["authorized_price_tuning"] = _tuning_declaration(_bundle_years)

    counts = _tail_counts(args.bundle)
    tag = "caiso-267 fossil offer-band x0.92 arm"
    kept, seen = [], set()
    for exc in att.get("exceptions", []):
        if exc.get("criterion") != "price_tail":
            kept.append(exc)
            continue
        year = int(exc.get("year", 0))
        seen.add(year)
        if year not in args.still_failing:
            continue  # band met on this bundle — a spent caveat is dropped
        exc["magnitude"] = (
            f"model {counts.get(year, '?')} h vs actual RT {ACTUAL_TAIL[year]} h "
            f"> $200/MWh (re-measured on the {tag})"
        )
        kept.append(exc)
    for year in args.still_failing:
        if year in seen or year not in ACTUAL_TAIL:
            continue
        kept.append(
            {
                "criterion": "price_tail",
                "year": year,
                "magnitude": (
                    f"model {counts.get(year, '?')} h vs actual RT "
                    f"{ACTUAL_TAIL[year]} h > $200/MWh (NEW on the {tag} — a "
                    "disclosed flip vs the caiso-260 keeper, reported at full "
                    "magnitude per the addendum)"
                ),
                "rationale": (
                    "C3c scarcity-tail model-class limitation (the ledgered "
                    "criterion; rubric v3.3/v3.6 standing rule) — adjudication "
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
        "authorized_price_tuning DECLARED; free_parameters left to "
        "build_dof_ledger.py)"
    )


if __name__ == "__main__":
    main()
