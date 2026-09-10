"""Write the caiso-271 bundle's attestation (eGRID prime-mover-family heat rates).

An unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT under the
rubric v3.3 / v3.6 standing rule, so the arm needs its own attestation before it can be
scored on its merits.

Pattern unchanged from ``gen_caiso269_attestation.py`` (E10: generated AT registration,
never typed): the LIVE keeper's committed attestation is carried, ``attested_by`` is
re-stamped with the narrative for THIS bundle, and the ``price_tail`` (C3c) exception
magnitudes are RE-MEASURED on this bundle's own committed sidecars.

The arm adds NO DOF-ledger row (rule 21 ``[R-DOF]``): the statistic is arithmetic on
published eGRID fields at a grain eGRID itself publishes, admission is a population rule,
and no threshold is introduced. No ``authorized_price_tuning`` block — no offer-curve
multiplier is exercised (rule 1 ``[R-STRUCT]`` condition (e) does not engage).

Usage::

    PYTHONPATH=.:src python3 scripts/gen_caiso271_attestation.py \
        --bundle results/calibration/caiso271_family_span
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

#: Actual RT hours > $200/MWh (C3c basis; caiso-204 finding SecC / keeper ledger).
ACTUAL_TAIL = {2022: 0, 2023: 47, 2024: 35, 2025: 8}
#: The LIVE keeper whose attestation this arm carries forward.
KEEPER = REPO / "results/calibration/caiso269_lateevening_span"

_SHARED = (
    "caiso-271 session (2026-09-10), REGISTERED BY caiso-273 (2026-09-10) after recovery "
    "from git history. ONE STRUCTURAL MECHANISM, ScenarioConfig.egrid_family_heat_rates, "
    "solved as ONE flag on the committed keeper recipe "
    "2026-09-10-caiso-269-lateevening-clean via --replay-bundle. Pre-registered in "
    "docs/PRECOMMIT-caiso271-egrid-family-hr-2026-09-10.md, pushed before the first LP of "
    "any shard; measured in docs/RESULT-caiso271-egrid-family-hr-2026-09-10.md; recovered "
    "and registered per docs/PRECOMMIT-caiso273-register-caiso271-2026-09-10.md. ZERO new "
    "free parameters, ZERO new thresholds, NO authorized_price_tuning block, DOF ledger "
    "unchanged. "
    "THE OBJECT IS A JOIN-GRAIN DEFECT: the fleet joins heat rate from eGRID at PLANT grain "
    "(PLNT<yy>.PLHTRT), so a plant hosting two prime-mover families hands BOTH halves one "
    "generation-weighted blend that is a measured number for NEITHER. eGRID publishes the "
    "per-family inputs in the same vintage the join already reads. The CAISO artifact "
    "covers 4 plants / 8 (plant, family) rows and the fleet effect is 6 units / 1,451.8 MW "
    "/ 4.54 pct of the CAISO fleet: AES Alamitos three ST units (1,142 MW) +2.288 "
    "MMBtu/MWh, Huntington Beach ST (225.8 MW) -0.356, Glenarm (84 MW gas_cc) -1.361. "
    "Rule 19 [R-ONE-MECH]: applied at the eGRID-input seam so every class-scoped measured "
    "mechanism keeps its precedence, and it RETIRES the MIXED_FACILITY_STEAM_HR hand number "
    "at covered plants rather than stacking on it. Rule 13 [R-MEASURED]: the identical "
    "construction regenerates from any eGRID vintage. Rules 1 [R-STRUCT] and 14 "
    "[R-ACCURATE] are the whole case - the direction was measured and declared BEFORE the "
    "solve, and an accurate input is not reverted because the residual moved. "
    "ALL FOUR PRE-REGISTERED STOP GATES PASS on all four years: G-IDENT; G-FOOT class-energy "
    "deltas confined to the gas classes plus a rounding-level import/solar/hydro reshuffle "
    "(largest non-gas import +0.0161 TWh in 2024); G-DIR ST_GAS energy FALLS in every year "
    "(-0.0353/-0.0386/-0.1048/-0.0095 TWh) as a +2.288 MMBtu/MWh reprice of 1,142 MW "
    "requires; G-NOFLIP no load-bearing criterion flips PASS -> FAIL. G-CTRL FORM 4, NO "
    "CONTROL SOLVE SPENT. "
    "G-IDENT IS CORRECTED HERE BY caiso-273 AND THE CORRECTION IS REPORTED, NOT BURIED: "
    "re-measured against the keeper's own recorded run_config, TWO ScenarioConfig fields "
    "differ, not one as RESULT-caiso271 sec 3 states. The second is "
    "nyiso_total_east_cutset_ttc None -> False. It is PROVABLY INERT for CAISO three ways: "
    "pipeline/ttc.py::apply_iso_monthly_ttc returns before reading it ('if iso != NYISO: "
    "return ttc'); bool(None) == bool(False) == False at the one read site; and the field "
    "came into existence at nyiso-224 (5af5d6fb) inside the 4-commit window between the "
    "keeper's git_sha 8d627e64 and the arm's 9ee5319b, recorded as a declared cache-key "
    "default-flip. The arm remains a ONE-MECHANISM run; the gate's conclusion stands. "
    "G-DRIFT (rule 29(b)), audited at code level by caiso-273 over that same 8d627e64 -> "
    "9ee5319b window, classifies EVERY changed hunk INERT for CAISO: 5af5d6fb nyiso-224 is "
    "NYISO hard-gated; 15beb03c is a cache-key registration its own commit message states "
    "RESTORES the pre-merge keys and leaves an armed run's key untouched, plus a test "
    "inventory line and a solve-surface digest transcription repair; 9be52b9e touches only "
    "scripts/lib/forecast_parity_registry.py, which a mode=backcast run never enters; "
    "87bd1999 is a merge commit. All INERT ⇒ form 4 valid ⇒ the keeper IS the control. "
    "REPORTED FIRST AND AGAINST THE ARM: C3a DEGRADES IN ALL FOUR YEARS "
    "(+0.100/+0.053/+0.115/+0.012 pp; 2022 +12.899 -> +12.999 pct against a <= +10 pct "
    "band). ST_GAS moves AWAY from measured in 2022, 2023 and 2025 - the class was already "
    "under-run and the arm makes 1,142 MW of it dearer. The arm is small (4.54 pct of fleet "
    "MW) and 2025 is close to inert. IT DOES NOT CLOSE THE 2022 RUBRIC FAILURE AND WAS NEVER "
    "CLAIMED TO: closing C3a-2022 needs -2.45 $/MWh and this moves +0.08, so 2022 stays "
    "NOT-YET on C3a and C3b - per rule 30(c) that never downgrades the ISO, whose "
    "determination is the train-tier verdict. "
    "IN ITS FAVOUR: it costs a little price and buys a little dispatch - the OPPOSITE trade "
    "to caiso-267/268, which bought price by degrading dispatch and which the owner refused "
    "on rule 1 [R-STRUCT] grounds. C1 moves TOWARD measured for CC_REGULAR (2023, 2024, "
    "2025), CT_PEAKER (2023, 2024, 2025) and CT_CHP (all four years); 2024 ST_GAS improves "
    "in magnitude (+0.067 -> -0.038 TWh). Nothing is close to a band: the worst C1 cell in "
    "any year is 2023 CC_REGULAR at -3.551 TWh against +/-5.27 TWh; C2 gas total moves "
    "<= 0.009 TWh; slack and dump are 0 in every zone-hour of every year. "
    "LOAD-BEARING ARTIFACT CHECK, done on the artifacts and never on a shard's claim: "
    "resolved_inputs.seam_import_cap reads source 'mic_partition' in all four bundles "
    "(cap_mw 15780.0/16055.0/16452.0/16148.0 for 2022/23/24/25), so no bundle solved on the "
    "retired fitted fallback import scalar (rules 20 [R-DOF] / 24 [R-REGISTRY]). "
    "COMPOSITION (rules 16 [R-ALLYEARS] / 32 [R-SHARD] (d)): four per-year shard bundles "
    "composed in the parent with ZERO LP; the four shard scenario_configs differ ONLY in "
    "gas_price_override (6.45/2.54/2.19/3.52) and weather_year (2022/23/24/25), both "
    "year-scoped by construction, so ONE config spans every scored year. "
    "NOT PROMOTED - the keeper stays 2026-09-10-caiso-269-lateevening-clean and promotion "
    "is the owner's call."
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
    """Write ``calibration_attestation.json`` for the caiso-271 composed bundle."""
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
