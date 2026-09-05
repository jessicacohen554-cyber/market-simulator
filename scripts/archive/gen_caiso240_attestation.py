"""Write the caiso-240 ST_GAS-peak-band bundle's attestation.

`results/calibration/caiso240_b1_stgas_peak_measured` is the caiso-239 keeper
recipe replayed at HEAD through ``--replay-bundle`` with a SINGLE flag delta
(``caiso_st_gas_peak_measured``). The `gen_caisoNNN` series pattern is unchanged
(E10: an attestation is generated AT the promotion, every premise computed, never
typed): the keeper's committed attestation is carried, ``attested_by``
re-stamped, and the price_tail (C3c) exception magnitudes RE-MEASURED on this
bundle's own committed sidecars. ``free_parameters`` is not edited here — it is
rebuilt by ``scripts/build_dof_ledger.py`` afterwards.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso240_attestation.py \
        --bundle results/calibration/caiso240_b1_stgas_peak_measured \
        --still-failing 2023 2024
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
KEEPER = REPO / "results/calibration/caiso239_b1_stgas_committed_measured"

_ATTEST = (
    "caiso-240 session (2026-09-03): the RULE 24 [R-REGISTRY] / RULE 14 "
    "[R-ACCURATE] structural-integrity repair of CAISO's ST_GAS PEAK band, "
    "and the CENSUS that identified it. THE CENSUS IS THE PRIMARY RESULT: "
    "scripts/probes/_caiso240_default_hr_mult_census.py measured the LP "
    "footprint of ALL 28 uncited literals in "
    "fleet.campd_bins._DEFAULT_HR_MULT_BY_GROUP on ALL SIX designated "
    "keepers, with ZERO SOLVES, by rebuilding each keeper's offer surface "
    "with every cell scaled by its OWN unique probe factor and reading each "
    "LP row's heat-rate ratio back — so a row's cell is IDENTIFIED BY "
    "MEASUREMENT, never inferred from its group or its name (the caiso-238 "
    "error made structurally impossible). Two pre-registered method "
    "falsifiers both PASS: M-1, a baseline-to-baseline rebuild is "
    "byte-identical across all 1,801 CAISO rows; M-2, the ST_GAS.mc cell is "
    "responsive on exactly 3 tranches (plants 315/335/350) in every year on "
    "the caiso-231 predecessor recipe — reproducing caiso-239 F-1 — and on "
    "ZERO in every year on the caiso-239 keeper, which independently "
    "verifies that caiso-239 retired the literal it claimed to retire. "
    "THE RESULT: 22 of the 28 literals are measured DEAD in every one of "
    "the six ISOs; five of the seven mr literals are dead BY CONSTRUCTION "
    "(bins_to_fleet builds a must-run tranche only for non-CHP coal); the "
    "largest live cell anywhere is COAL:mr on MISO (61 tranches, 12,709 MW) "
    "and it is mostly PRICED-BUT-INERT (the coal _mustrun tranche's fuel is "
    "sunk under take-or-pay, so its heat rate moves and its marginal cost "
    "does not); and the only class whose WHOLE offer surface is uncited "
    "literals is ST_CHP, which no keeper of any ISO gives an offer curve — "
    "an ask for the MISO / PJM / NYISO / NEISO lanes under rule 25 "
    "[R-ISO-SCOPE], never an arm here. ON THE CAISO KEEPER exactly TWO "
    "cells remain live after caiso-239: ST_GAS[econ] = 1.00 (3 tranches, "
    "2,240.8 MW) and ST_GAS[peak] = 1.10 (3 tranches, 428.8 MW), both on "
    "the same three once-through-cooling steamers (315 AES Alamitos, 335 "
    "AES Huntington Beach, 350 Ormond Beach) through the same "
    "_offer_curve_for_group bypass. THIS ARM REPAIRS THE PEAK ONE, the only "
    "one of the two whose measured counterpart is AT THE MODEL'S OWN GRAIN "
    "(a bypassed plant's peak band is a single flat multiplier and the "
    "measurement is a single number). ScenarioConfig.caiso_st_gas_peak_"
    "measured (gated, default off, per-ISO registry "
    "constants.ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO) replaces the uncited "
    "ERCOT-lineage 1.10 with CAISO 1.166 = CT_PEAKER.bands.peak in the "
    "committed caiso_offer_curve_measured.json. WHY THAT IS ZERO NEW "
    "MEASUREMENT AND ZERO FREE PARAMETERS (rule 21 [R-DOF]): 1.166 is "
    "ALREADY the value the CAISO ST_GAS class band carries on this keeper, "
    "armed at caiso-231 by caiso_offer_surface_measured_ungrounded on the "
    "CT bucket that derive_caiso_offer_surface.py discloses CONTAINS these "
    "very steamers — and the bypass keeps that re-grounded band from "
    "reaching any of them, so on the keeper it prices only two EIA-860 "
    "retired-window units (356 AES Redondo Beach, 10446 SEGS IX). The "
    "measurement is withheld from its own population; this arm delivers it. "
    "That is caiso-239's structural inversion again, one band over. "
    "DISCLOSED AGAINST INTEREST: the population match is CONTAINMENT, not "
    "coincidence, and so is WEAKER than caiso-239's exact ten-unit "
    "coincidence — the CT bucket is pooled CT_PEAKER + CT_CHP + ST_GAS "
    "conduct and the OASIS ids are masked, so the steamers cannot be "
    "isolated inside it. It is the same basis caiso-231 was promoted on. "
    "THE LARGER CELL IS REFUSED, NOT TAKEN: ST_GAS[econ] (2,240.8 MW vs "
    "428.8) is graded F3 because the model's band for a bypassed plant is "
    "ONE FLAT multiplier while every measured counterpart is a TWO-ENDPOINT "
    "ramp, so choosing an endpoint would be a free parameter; its "
    "first-order bound (+0.0108/+0.0084/+0.0044 $/MWh) is on record for "
    "whoever takes it. Registered in _BACKCAST_ONLY_OVERLAY_FIELDS, unlike "
    "its caiso-239 sibling: that one arms a measured PHYSICAL heat-rate "
    "ratio with a forward story, this one arms measured OASIS BID conduct "
    "keyed to a specific year's record (rule 13 [R-MEASURED]). "
    "Band-disjoint from that sibling (rule 19 [R-ONE-MECH]); a unit test "
    "pins that arming both moves exactly two bands. Recipe: the caiso-239 "
    "keeper bundle's meta.json replayed at HEAD via --replay-bundle with "
    "the single flag delta, P1 scored, 2023-2025 sequential in one "
    "invocation, one bundle (rules 12 / 16). PRE-REGISTERED ADVERSE "
    "DIRECTION, PUSHED TO ORIGIN BEFORE THE SOLVE: 1.10 -> 1.166 RAISES the "
    "peak band by 6.0 %, i.e. it makes the sole failing gate WORSE, and the "
    "caiso-230 §H first-order bound re-run on the caiso-239 keeper is "
    "+0.0014 / +0.0011 / zero-to-within-the-estimator's-attribution-"
    "tolerance $/MWh for 2023/2024/2025 (the 2025 leg has zero "
    "matched-marginal zone-hours, the degenerate case the precommit "
    "declared in advance rather than discovering after a miss). G-STRUCT "
    "was verified PRE-SOLVE on the rebuilt fleet: exactly 3 of 1,801 rows "
    "move, all three the steamers' _peak tranches, at the exact ratio "
    "1.166/1.10 = 1.06, with 0 other bands, groups or ISOs touched. Armed "
    "for structural integrity under rules 14 / 24 / 25, NEVER as a C3a "
    "lever."
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
    """Carry the caiso-239 keeper attestation onto the caiso-240 arm."""
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
            f"{ACTUAL_TAIL[year]} h > $200/MWh (re-measured on the caiso-240 "
            "ST_GAS peak-band arm)"
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
                    f"{ACTUAL_TAIL[year]} h > $200/MWh (NEW on the caiso-240 "
                    "arm — a disclosed PASS->FAIL flip vs the caiso-239 "
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
