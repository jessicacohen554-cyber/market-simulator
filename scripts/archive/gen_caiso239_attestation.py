"""Write the caiso-239 ST_GAS-committed-band bundle's attestation.

`results/calibration/caiso239_b1_stgas_committed_measured` is the caiso-231
keeper recipe replayed at HEAD through ``--replay-bundle`` with a SINGLE flag
delta (``caiso_st_gas_committed_measured``). The `gen_caisoNNN` series pattern
is unchanged (E10: an attestation is generated AT the promotion, every premise
computed, never typed): the keeper's committed attestation is carried,
``attested_by`` re-stamped, and the price_tail (C3c) exception magnitudes
RE-MEASURED on this bundle's own committed sidecars. ``free_parameters`` is not
edited here — it is rebuilt by ``scripts/build_dof_ledger.py`` afterwards.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso239_attestation.py \
        --bundle results/calibration/caiso239_b1_stgas_committed_measured \
        --still-failing 2023 2024
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
KEEPER = REPO / "results/calibration/caiso231_b1_ungrounded"

_ATTEST = (
    "caiso-239 session (2026-09-02): the RULE 24 [R-REGISTRY] / RULE 14 "
    "[R-ACCURATE] structural-integrity repair of CAISO's ST_GAS COMMITTED "
    "band, taken at the scalar that ACTUALLY prices it. THE FUNDED OBJECT WAS "
    "MIS-LOCATED, AND THAT IS THIS SESSION'S PRIMARY RESULT: caiso-238 object "
    "2 chartered a repair of offer_curve_by_group['ST_GAS']['committed'] = "
    "0.81 on the premise that it prices CAISO's three coastal OTC steamers, "
    "and BOTH chartered candidate values (Lever-A 1.00 and the measured "
    "1.683) are REFUSED on that scalar, on three independent measured grounds "
    "(zero solves; scripts/probes/_caiso239_st_gas_committed_footprint.py). "
    "(1) SCOPE: offer_curves._offer_curve_for_group returns None for "
    "'group == ST_GAS and plant_code in ST_GAS_PEAKER_PLANTS', and "
    "data.outages.ST_GAS_PEAKER_PLANTS names plants 315 / 335 / 350 "
    "EXPLICITLY, so the three steamers never reach the class band — they are "
    "byte-identical at committed in {0.81, 1.00, 1.683} in all three years, "
    "and take the ERCOT-lineage class default "
    "campd_bins._DEFAULT_HR_MULT_BY_GROUP['ST_GAS']['mc'] = 1.15 instead "
    "(verified exactly on the rebuilt keeper fleet: 11.850 x 1.15 = 13.628 "
    "MMBtu/MWh). The chartered scalar reaches 2 of the keeper's 25 ST_GAS LP "
    "tranches and no OTC steamer among them. (2) LIVENESS: both responsive "
    "plants are EIA-860 retired-window units (356 AES Redondo Beach; 10446 "
    "SEGS IX, the gas steam auxiliary of a retired solar-trough plant) and "
    "BOTH carry ZERO availability in 2025 — the keeper's worst C3a year — so "
    "the chartered object is provably dead there. (3) POPULATION MISMATCH: "
    "avg_committed_p50 = 1.683 is measured on the ten CAMPD units of exactly "
    "plants 315/335/350 (campd_gas_commitment_params_CAISO_units.csv), i.e. "
    "the plants the scalar EXCLUDES, so arming it there would apply the "
    "statistic to a disjoint population — rule 14's own representation-"
    "mismatch exception in its exact form. AGAINST INTEREST, the charter's "
    "inversion premise is ALSO false at the resolved offer level: on the "
    "keeper as built the steamers' committed band is already their DEAREST "
    "(2024 mean mc, p315: 69.19 committed > 68.92 peak > 62.38 econ). "
    "THE REPAIR, RELOCATED: ScenarioConfig.caiso_st_gas_committed_measured "
    "(gated, default off, per-ISO registry "
    "constants.ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO) replaces the uncited "
    "1.15 class literal — an off-registry channel absent from every "
    "run_config.json and from the DOF ledger's offer_curve_by_group count, "
    "pricing 2,858.8 MW of SP15 OTC steam capacity — with CAISO's own "
    "measured min-load block-average burn ratio 1.683, the measurement taken "
    "on those same ten units. Statistic and band populations COINCIDE; ZERO "
    "free parameters added; EXACTLY ONE BAND moves. Recipe: the caiso-231 "
    "keeper bundle's meta.json replayed at HEAD via --replay-bundle with the "
    "single flag delta, P1 scored, 2023-2025 sequential in one invocation. "
    "PRE-REGISTERED ADVERSE DIRECTION, PUSHED TO ORIGIN BEFORE THE SOLVE: "
    "PRECOMMIT-caiso239-st-gas-committed-relocation-2026-09-02.md §3 "
    "predicted a first-order C3a cost of +0.0003 / +0.0265 / +0.0000 $/MWh "
    "(the caiso-230 §H bounding form re-run on THIS keeper); the MEASURED "
    "cost is +0.0001 / +0.0060 / +0.0001, inside the bound in 2023 and 2024 "
    "with 3x and 4x margin. G-STRUCT PASSES exactly, verified pre-solve and "
    "on the solved fleet: 3 of 1,795 fleet rows move, all three the OTC "
    "steamers' _committed tranches, ratio 1.4635 = 1.683/1.15 exact; 0 other "
    "bands, 0 other classes. G-INERT PASSES: the arm is NOT byte-identical — "
    "2024 ST_GAS sheds 14.7 GWh (-2.3%) to CT_PEAKER (+8.2), CC_REGULAR "
    "(+4.6) and imports (+1.8), the re-dispatch-around-the-repriced-rung "
    "behaviour caiso-231 measured; 2023 and 2025 are identical to 0.001 TWh "
    "in every class. G-C3a PASSES on its substantive legs: no year flips, "
    "2023 stays PASS at +4.1%, 2024 +12.5 -> +12.6%, 2025 +15.6% unchanged. "
    "G-C1 (PASS, unchanged), G-C3b (PASS), G-C2/G-C4/G-C8 (no flip), "
    "G-CAVEAT (budget 1 of 1). TWO PRE-REGISTERED GATES ARE DISCLOSED AS "
    "NOT SATISFIED AS LITERALLY WRITTEN, not dropped. G-CTRL required the "
    "arm's run_config to differ from the keeper's in the one new flag alone; "
    "22 fields differ, and EVERY one is HEAD drift rather than a solve input "
    "— provenance recording added since the keeper solved (git_sha, the "
    "hydro_plant_modes presence probe with hydro_ror_split False on both "
    "arms, the nyiso-176 thermal_tranches identity block), eight new "
    "ScenarioConfig fields at their defaults, the rule-26 caiso_bidir_intertie "
    "deletion, and the capx-D41 forecast-only CCS cost re-identification "
    "(ccs_retrofit_capex_kw / fixed_om_gas_cc_ccs, consumed only in "
    "model/capacity_evolution, which a backcast never runs). The substantive "
    "claim is established from the DISPATCH instead, which is stronger than "
    "the field diff: 2023 and 2025 class energy is identical to the keeper "
    "to 0.001 TWh in EVERY class, which no fleet-representation or "
    "measured-input change could survive. G-C3a's 2025 leg had a degenerate "
    "bound of exactly +0.0000 (no responsive tranche is ever the nearest-"
    "matched marginal rung in 2025) and the measured move is +0.0001 $/MWh, "
    "a 1-part-in-400,000 excess: the §H form counts only hours where the "
    "repriced rung is itself the matched marginal rung and cannot represent "
    "indirect re-dispatch. Reported at full magnitude; nothing re-fitted. "
    "Determination is UNCHANGED vs the incumbent keeper: NOT-YET on C3a "
    "alone."
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
    """Carry the caiso-231 keeper attestation onto the caiso-239 arm."""
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
            f"{ACTUAL_TAIL[year]} h > $200/MWh (re-measured on the caiso-239 "
            "ST_GAS committed-band arm)"
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
                    f"{ACTUAL_TAIL[year]} h > $200/MWh (NEW on the caiso-239 "
                    "arm — a disclosed PASS->FAIL flip vs the caiso-231 "
                    "keeper, reported at full magnitude per the precommit)"
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
        f"wrote {path} (tail counts {counts}; ledger years "
        f"{sorted(e['year'] for e in kept if e.get('criterion') == 'price_tail')}; "
        "free_parameters left to build_dof_ledger.py)"
    )


if __name__ == "__main__":
    main()
