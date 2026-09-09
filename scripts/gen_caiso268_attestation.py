"""Write the caiso-268 SPAN bundle's attestation — the fossil offer-band x0.92 arm.

The bundle needs a C6 attestation (an unattested C6 makes C3c FAIL instead of
reclassifying to a ledgered CAVEAT), and this arm additionally needs the rule 1
``[R-STRUCT]`` carve-out declaration: it uses the AUTHORIZED PRICE-TUNING
CHANNEL, so ``governance.authorized_price_tuning`` must be present and
well-formed or ``calibration_verdict.score_governance`` fails C6 outright
(``AUTHORIZED_TUNING_FIELDS``).

Pattern unchanged from ``gen_caiso267_attestation.py`` (E10: generated AT the
registration, never typed): the incumbent keeper's committed attestation is
carried, ``attested_by`` re-stamped with THIS bundle's narrative, and the
``price_tail`` (C3c) exception magnitudes RE-MEASURED on this bundle's own
committed sidecars. ``free_parameters`` is rebuilt afterwards by
``scripts/build_dof_ledger.py``.

THREE THINGS THAT BIT caiso-267 AND ARE FIXED HERE BY CONSTRUCTION:

1. ``years_held`` is read from the BUNDLE's own ``meta.json``, never hardcoded.
   Rule 1 (b) is tested by EXACT SET EQUALITY against the run's own scored years
   (``calibration_verdict._authorized_tuning_finding``); caiso-267's generator
   hardcoded ``(2023, 2024, 2025)`` and made C6 FAIL outright on a differently
   scoped bundle.
2. The keeper carried forward is ``caiso_fuelvintage_span`` (the LIVE keeper,
   ``2026-09-09-caiso-fuelvintage-860-gas``), NOT ``caiso260_demand_vintage``.
3. The C3c tail magnitudes are re-measured on THIS bundle's sidecars, never
   copied from caiso-267's.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso268_attestation.py \
        --bundle results/calibration/caiso268_fossil92_span --still-failing 2023 2024
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

#: Actual RT hours > $200/MWh (C3c basis; committed ``tail/actual_tail.json``,
#: the same numbers the live keeper's own ledger carries).
ACTUAL_TAIL = {2023: 47, 2024: 35, 2025: 8}
#: The LIVE keeper this arm is a single-delta replay of.
KEEPER = REPO / "results/calibration/caiso_fuelvintage_span"
KEEPER_RUN_ID = "2026-09-09-caiso-fuelvintage-860-gas"
CURVE = REPO / "results/calibration/_caiso268_fossil92_offer_curve.json"
SCALE = 0.92

_ATTEST = (
    "THIS BUNDLE IS THE ARM: the LIVE CAISO keeper recipe "
    f"({KEEPER_RUN_ID}, bundle caiso_fuelvintage_span) with EVERY fossil "
    "offer_curve_by_group band multiplier scaled by 0.92, and NOTHING ELSE. "
    "caiso-268 session, shard SPAN (2026-09-09). OWNER INSTRUCTION, verbatim: "
    "'Run a Caiso calibration session to move offer curve down 8% from current "
    "levels and launch shards for each year of the run, attach repo to shards "
    "and ensure they don't collide on merge'. 'CURRENT LEVELS' IS RESOLVED TO "
    "THE LIVE KEEPER, not to the caiso-267 x0.92 arm, because caiso-267 was "
    "REFUSED by the owner on 2026-09-09 (FINDING-caiso267-fossil-offer-8pct §9, "
    "'DO NOT PROMOTE') and its cut levels are therefore live nowhere: there is "
    "exactly one live CAISO offer curve and it is the keeper's. The cut is "
    "x0.92, NOT x0.92^2 = 0.8464. THIS IS THE RULE 1 [R-STRUCT] / RULE 13 "
    "[R-MEASURED] AUTHORIZED PRICE-TUNING CHANNEL and it is DECLARED as such in "
    "governance.authorized_price_tuning below — it is NOT a rule 14 "
    "[R-ACCURATE] measured-input repair and is never described as one. "
    "WHY THIS IS NOT A RE-TEST OF caiso-267 (rule 28 [R-MECH-MATRIX] "
    "DO-NOT-REDO): the BASELINE MOVED on 2026-09-09, after caiso-267 was "
    "decided. caiso-267's control was 2026-09-06-caiso-260-b1-demand, whose C3a "
    "FAILED in 2024 and 2025 (+4.37/+8.89/+8.25%); this run's control is the "
    "fuelvintage keeper, which armed the EIA-860 2019+ retiree window AND the "
    "measured monthly gas LEVEL — the very quantity the cut acts on — and whose "
    "C3a PASSES in all three years (+4.4/+8.9/+8.3% against a +/-10% band). "
    "That is the new evidence rule 28 requires before a cell is re-tested. "
    "DISCLOSED BEFORE THE SOLVE (PRECOMMIT §2.1): the keeper ALREADY PASSES "
    "C3a, so a cut of this size is the same order as the whole remaining "
    "residual and C3a may cross zero and fail on the LOW side; and C4-2025 is "
    "the named knife edge at NRMSE 0.298 against a <=0.300 bound, which "
    "caiso-267's identical cut pushed to 0.308. "
    "PRE-REGISTERED in docs/PRECOMMIT-caiso268-fossil-offer-8pct-2026-09-09.md, "
    "pushed BEFORE the first LP of any shard, and in "
    "docs/ADDENDUM-caiso268-span-gdrift-2026-09-09.md, pushed BEFORE this "
    "shard's first LP. "
    "G-CTRL: FORM 4 IS CLAIMED AND NO CONTROL SOLVE IS SPENT. The keeper's "
    "git_sha 873f7564 resolves in this repository, so the rule 29(b) code audit "
    "could actually be run (unlike the preceding CAISO lane, whose keeper "
    "recorded an unresolvable sha). It measured TWO files on the backcast solve "
    "path: 102 lines of COMMENT-ONLY change inside "
    "NUCLEAR_MONTHLY_CF_BY_YEAR's NYISO and NEISO keys (0 non-comment lines "
    "changed, verified mechanically) and one NYISO-scoped line in "
    "solve_surface_declared.py for HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT, which is "
    "NOT in CAISO's projected surface. ALL HUNKS INERT. The repo's own capx-D79 "
    "instrument corroborates end-to-end: CAISO's solve-surface fingerprint "
    "recomputes at HEAD to cba92d202f32f9fd / 204 rows / identical moved rows — "
    "byte-identical to the block the keeper recorded. "
    "DISCLOSED PHYSICS (carried from caiso-267 §8.5 and re-verified against "
    "THIS keeper): the cut moves CT_PEAKER.committed from exactly its measured "
    "phys_committed (0.991) to 8% below it, and CT_CHP.committed from 1.100 to "
    "1.012 against phys 1.073 — two NEW crossings of the measured physical "
    "min-load heat rate; CC_REGULAR/CC_CHP committed and peak and ST_GAS "
    "committed were already below theirs on the keeper and are deepened. "
    "phys_* is inert in this recipe (gas_offer_net_revenue_margin=false) and "
    "was NOT touched, so no LP row changes — but the model now offers committed "
    "gas below its own measured fuel cost, and that is worth saying. "
    "ALSO DISCLOSED: caiso_st_gas_committed_measured and "
    "caiso_st_gas_peak_measured are both armed and resolve those two bands PER "
    "PLANT for ST_GAS_PEAKER_PLANTS members, bypassing offer_curve_by_group "
    "entirely, so the ST_GAS committed and peak cuts reach only the "
    "non-bypassed units (ST_GAS is 0.02-0.19 TWh — a completeness note, not a "
    "material one)."
)


def _tail_counts(bundle: Path, years: list[int]) -> dict[int, int]:
    """Model hours > $200 per year on the scorer's max-zonal basis.

    Args:
        bundle: The bundle whose committed ``hourly/system_<year>.parquet``
            sidecars are read. RE-MEASURED here, never copied from another run.
        years: The bundle's own scored years.

    Returns:
        ``{year: count of hours whose max zonal P1 price exceeds $200/MWh}``.
    """
    out: dict[int, int] = {}
    for year in years:
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
            set equality against them, so the SPAN bundle declares
            ``[2023, 2024, 2025]``. The factor is identical whatever the span;
            only the span differs.

    Returns:
        The ``governance.authorized_price_tuning`` block.
    """
    curve = json.loads(CURVE.read_text())
    return {
        "channel": "offer_curve_by_group",
        "ruling": (
            "Owner instruction 2026-09-09, verbatim: 'Run a Caiso calibration "
            "session to move offer curve down 8% from current levels and launch "
            "shards for each year of the run, attach repo to shards and ensure "
            "they don't collide on merge'. 'Current levels' resolves to the "
            f"LIVE keeper {KEEPER_RUN_ID}, because the owner REFUSED caiso-267 "
            "on 2026-09-09 ('DO NOT PROMOTE'), so its cut levels are live "
            "nowhere. Authorized by the rules 1 [R-STRUCT] / 13 [R-MEASURED] "
            "carve-out of 2026-09-05."
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
                "runs AFTER the override (pipeline/backcast_config.py) and "
                "rebuilds the ladder from the post-override peak, so the five "
                "uniform rungs follow the cut automatically and the 'N equal "
                "sub-bands at one MC == one flat band' identity is preserved "
                "(verified pre-solve on this keeper: the CC_REGULAR and "
                "CT_PEAKER ladders are [[0.2, 1.386]]x5 and [[0.2, 1.154]]x5, "
                "uniform copies of peak). The three *_INTERMEDIATE classes are "
                "excluded because the offer-curve router does not read them "
                "(and cc_intermediate_split / ct_intermediate_split are both "
                "false, so they carry zero CAISO energy in all three years); "
                "ST_CHP is excluded because the keeper's resolved curve has no "
                "entry for it, so adding one would be a new parameter rather "
                "than a cut of an existing one."
            ),
            "file": "results/calibration/_caiso268_fossil92_offer_curve.json",
            "file_md5": "fc46efab534211a96600f8664a8b6779",
        },
        # Rule 1 (b) is tested by EXACT SET EQUALITY against the RUN's own scored
        # years (calibration_verdict._authorized_tuning_finding), so this is the
        # bundle's OWN span read from its meta.json — never a module constant.
        # Hardcoding it is what made C6 FAIL outright on caiso-267's shard
        # bundle (RESULT-caiso267-shard-2022-retest-2026-09-09.md §4(1)).
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
            "scorecard says. In the DOF ledger it is carried as the free "
            "parameter fossil_offer_band_scale = 0.92 whose identification "
            "source is 'price residual, authorized channel (rules 1/13 "
            "amendment 2026-09-05); owner instruction 2026-09-09' — the ruling "
            "itself, NEVER a measured input (rule 20 [R-DOF] cross-reference, "
            "owner ruling R-AY 2026-09-06)."
        ),
        "prereg": (
            "docs/PRECOMMIT-caiso268-fossil-offer-8pct-2026-09-09.md (pushed "
            "BEFORE the first LP of any shard) + "
            "docs/ADDENDUM-caiso268-span-gdrift-2026-09-09.md (the rule 29(b) "
            "G-DRIFT audit, pushed BEFORE this shard's first LP)"
        ),
        "disclosure": (
            "AGAINST INTEREST, on three counts. (1) This run moves the CAISO "
            "gas offer surface AWAY from CAISO's own measured DAM bids: "
            "caiso-266 §7 measured the pooled 2023-2025 CC bands at or ABOVE "
            "their armed values (committed 1.030 vs 1.000; econ_low / "
            "econ_high / peak at EXACTLY their armed 1.066 / 1.072 / 1.386), so "
            "the measured-faithful direction is UP and this run goes DOWN. "
            "(2) The incumbent keeper ALREADY PASSES C3a in all three years, so "
            "unlike caiso-267 — whose control failed C3a in two years — there "
            "is no failing price criterion for this cut to repair, and the cut "
            "is the same order as the entire remaining residual. (3) The "
            "caiso-267 structural objection is UNREFUTED and was the owner's "
            "stated ground for refusing it: a flat multiplier applies in all "
            "8,760 hours, so overnight it pulls gas in against imports the real "
            "fleet was running (h0-6 gas error +668 -> +1,329 MW in 2025 on the "
            "caiso-260 recipe). This run RE-MEASURES that objection on the new "
            "baseline rather than assuming it carries over or that it does "
            "not, and reports the result at full magnitude either way. "
            "Rule 25 [R-ISO-SCOPE]: the cut is a CLI override on a CAISO "
            "invocation and touches no shared default, no constants.py value "
            "and no other ISO's curve."
        ),
    }


def main() -> None:
    """Carry the live keeper's attestation onto the caiso-268 SPAN bundle."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--still-failing", type=int, nargs="*", default=[2023, 2024])
    args = ap.parse_args()

    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST
    bundle_years = sorted(
        int(y) for y in json.loads((args.bundle / "meta.json").read_text())["years"]
    )
    att["governance"]["authorized_price_tuning"] = _tuning_declaration(bundle_years)

    counts = _tail_counts(args.bundle, bundle_years)
    tag = "caiso-268 fossil offer-band x0.92 arm (SPAN)"
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
            f"> $200/MWh (RE-MEASURED on the {tag}'s own committed sidecars)"
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
                    f"disclosed flip vs the {KEEPER_RUN_ID} keeper, reported at "
                    "full magnitude)"
                ),
                "rationale": (
                    "C3c scarcity-tail model-class limitation (the ledgered "
                    "criterion; rubric v3.3 standing rule, v3.6 on a held-out "
                    "year) — adjudication belongs to the scorer"
                ),
            }
        )
    att["exceptions"] = kept

    path = args.bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} ({tag}; years_held {bundle_years} read from meta.json; "
        f"tail counts {counts}; ledger years "
        f"{sorted(e['year'] for e in kept if e.get('criterion') == 'price_tail')}; "
        "authorized_price_tuning DECLARED; free_parameters left to "
        "build_dof_ledger.py)"
    )


if __name__ == "__main__":
    main()
