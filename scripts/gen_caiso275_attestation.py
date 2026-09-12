"""Write the caiso-275 bundle's attestation (measured desert-SW import gas coupling).

An unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT under the
rubric v3.3 / v3.6 standing rule, so the arm needs its own attestation before it can be
scored on its merits.

Pattern unchanged from ``gen_caiso271_attestation.py`` (E10: generated AT registration,
never typed): the LIVE keeper's committed attestation is carried, ``attested_by`` is
re-stamped with the narrative for THIS bundle, and the ``price_tail`` (C3c) exception
magnitudes are RE-MEASURED on this bundle's own committed sidecars.

The arm adds NO DOF-ledger row (rule 21 ``[R-DOF]``): the shift is arithmetic on two
published monthly gas series times an existing heat rate, it introduces no threshold, and
it is ~0 at the baseline gas level by construction. No ``authorized_price_tuning`` block —
no offer-curve multiplier is exercised (rule 1 ``[R-STRUCT]`` condition (e) does not
engage).

Usage::

    PYTHONPATH=.:src python3 scripts/gen_caiso275_attestation.py \
        --bundle results/calibration/caiso275_B_gascoupling_span
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
KEEPER = REPO / "results/calibration/caiso271_egrid_family_span"

_SHARED = (
    "caiso-275 session (2026-09-12). ONE STRUCTURAL MECHANISM, "
    "ScenarioConfig.caiso_import_gas_coupling, solved as ONE flag on the committed keeper "
    "recipe 2026-09-10-caiso-271-egrid-family via replay_keeper --set. Pre-registered in "
    "docs/PRECOMMIT-caiso275-belly-and-winter-basis-2026-09-12.md, pushed and its SHA "
    "pinned (b8ddf8bc) before the first LP of any shard; measured in "
    "docs/RESULT-caiso275-belly-and-winter-basis-2026-09-12.md. ZERO new free parameters, "
    "ZERO new thresholds, NO authorized_price_tuning block, DOF ledger unchanged. "
    "THE OBJECT IS A FLAT HAND-FITTED LADDER PRICE: interchange_config.IMPORT_TRANCHES "
    "prices the desert-SW gas blocks DSW_CCGT at $68 and DSW_CT at $110 in EVERY MONTH OF "
    "EVERY YEAR - numbers caiso_import_hub_prices's own docstring describes as 're-fit in "
    "bundle mode against the model's OWN solved price'. The arm shifts those blocks by the "
    "MEASURED commodity delta (iso_hub_monthly_gas_prices - iso_monthly_gas_prices) x heat "
    "rate, so desert-SW gas imports track the same spot the already-armed "
    "gas_hub_basis_overlay applies to in-state gas. Rule 19 [R-ONE-MECH]: applied at the "
    "post-assembly mc seam through the per-hub-aware _caiso_import_tranche_of matcher, "
    "REPLACING the static ladder value on those blocks rather than stacking on it. Rule 13 "
    "[R-MEASURED]: the identical construction regenerates for a forward year from forward "
    "gas curves, and the shift is ~0 at the baseline gas level, so it is self-limiting. "
    "Rules 1 [R-STRUCT] and 14 [R-ACCURATE] are the whole case - a measured commodity basis "
    "replaces a number fitted against the model's own output, and an accurate input is not "
    "reverted because a residual moved. "
    "THE DECISIVE MEASUREMENT IS G-2 IN 2022, AND IT WAS SIZED BEFORE THE SOLVE: the basis "
    "was computed from the two gas series with NO reference to the price residual, and it "
    "predicts a December-concentrated response. Measured, the monthly price move tracks the "
    "monthly |basis| at Pearson +0.990 / Spearman +0.902 - Dec-2022 basis -11.68 $/MMBtu "
    "(SoCal citygate $23.10 against a WECC hub spot of $11.42, the western gas crisis) "
    "implies a -81.4 $/MWh DSW_CCGT offer shift and moves the CAISO price -14.32 $/MWh, "
    "against -0.02 to -0.91 in every other month of that year. December 2022 carries 44.8 "
    "pct of that year's price failure. That is a PREDICTION CONFIRMED, not a fit. "
    "HEADLINE RESULT: C3b-2022 FLIPS 0.240 FAIL -> 0.194 PASS, closing ONE of the TWO "
    "load-bearing failures behind the 2022 rung's NOT-YET. C3b also improves in 2023 "
    "(0.082 -> 0.077), 2024 (0.139 -> 0.137) and 2025 (0.107 -> 0.106). C3a improves in "
    "every year: 2022 95.47 -> 94.07 (+13.0 -> +11.3 pct), 2023 56.54 -> 55.89, 2024 37.65 "
    "-> 37.55, 2025 37.13 -> 37.07. NOTHING REGRESSES IN ANY YEAR. "
    "REPORTED FIRST AND AGAINST THE ARM - IT FAILS TWO OF ITS OWN PRE-REGISTERED GATES IN "
    "2024, AND AN EARLIER CLAIM THAT IT PASSED EVERY GATE IS WITHDRAWN (that claim predated "
    "the 2024 shard; withdrawn in commit 66259c12 and in RESULT sec 3 / sec 3.1): G-1 "
    "LIVENESS 2022 1,276 h PASS / 2023 1,478 h PASS / 2024 580 h FAIL / 2025 481 h FAIL "
    "against a >= 1,000 h gate; G-2 CONFINEMENT 2022 +0.990 PASS / 2023 +0.565 PASS / 2024 "
    "-0.214 FAIL / 2025 +0.596 PASS against a > 0 gate. 2025's shortfall was DECLARED IN "
    "ADVANCE (PRECOMMIT sec 10.2 - the hub gas series is NaN in Sep/Oct/Nov 2025 and the "
    "code zeroes the delta there, so those three months move 0.005-0.012 and are correctly "
    "inert). 2024's was NOT declared and is a genuine failure. RESULT sec 3.1 explains it "
    "as LOW TEST POWER - 2024's basis spans only -0.09 to -1.41 $/MMBtu, a range of 1.32 "
    "against 2022's 11.33, so the independent variable is nearly constant and the "
    "month-ranked correlation is noise - and that explanation is recorded as an explanation "
    "of the failure, NOT as a conversion of it into a pass. The honest consequence is "
    "stated at the gate: THE ARM RESTS ON ONE DISCRIMINATING YEAR (2022), which is also the "
    "year it was screened on; a second year with a wide within-year basis spread and full "
    "hub coverage does not exist in the committed file. "
    "ALSO AGAINST THE ARM: C3a-2022 STILL FAILS at +11.3 pct against the +/-10 pct band, so "
    "the 2022 rung stays NOT-YET and per rule 30(c) [R-TOUCHPOINT-FOLD] that never "
    "downgrades the ISO, whose determination is the train-tier verdict. The arm does not "
    "touch the object the session's own sec 1 measured - the belly gas deficit (model 1.5 GW "
    "against an actual 7.2 GW in the 2024 lowest net-load decile) and the reversed seam "
    "direction (model +2 GW import against an actual -1 GW export) are UNREPAIRED, and the "
    "successor object is CAISO commitment, not the import offer. "
    "THE SIBLING ARM WAS REJECTED ON ITS OWN GATE, and the rejection is load-bearing "
    "evidence for this one: caiso_import_solar_shape moved only 339 / 307 / 518 hours in "
    "2023 / 2024 / 2025 against the same >= 1,000 h G-1 gate, while being perfectly "
    "confined (off-window dP -0.015 to -0.030 against -0.46 to -0.63 on-window) and "
    "correctly signed - i.e. ~1/20 the magnitude a -36 to -46 $/MWh collapse over 30 pct of "
    "hours implies. dump stays 0.000 TWh in every hour of every arm-year, so THE MARGINAL "
    "IMPORT BLOCK IS NOT THE BELLY PRICE-SETTER; CAISO gas is. That reproduces caiso-272 "
    "sec 3.1 from a fourth direction and closes the import-offer route to the belly "
    "over-price. It was NOT resized and no second value was tried (rule 1 forbids sweeping "
    "against the gates). "
    "ALSO ESTABLISHED, DO-NOT-ARM: caiso_import_hub_prices is PROVABLY INERT on this keeper "
    "- inject_caiso_import_hub_prices matches rows with a raw "
    "uid.startswith(IMPORT_ZONE[iso]) i.e. WECC_import_ only, while its two siblings were "
    "repaired to use the per-hub-aware _caiso_import_tranche_of, so under the armed "
    "caiso_per_hub_intertie the WECC_PNW / WECC_DSW rows never match and it returns False. A "
    "real code defect, recorded, deliberately NOT repaired here (rule 32(c)6 keeps src/ out "
    "of shards). "
    "G-CTRL FORM 4, NO CONTROL SOLVE SPENT, earned by a G-DRIFT code audit over "
    "9ee5319b -> HEAD in which every changed hunk is INERT for a CAISO backcast "
    "(pjm-d4-4 unit_outage_short_windows_gas and spp-27 mustrun_window_commitment_grain, "
    "both default-off and absent from the keeper recipe; a MISO 2022 seam ladder; a "
    "miso-253 memory-lifetime fix its own comment documents as bit-identical; a "
    "replay_keeper dropped-keys addition; an SPP lib; another ISO's reliability-floor CSV). "
    "STRONGER THAN A HUNK READ: rebuilding ScenarioConfig at HEAD from the keeper's 838 "
    "recorded fields moves ZERO fields, and HEAD's 3 new fields are all False and absent "
    "from the keeper recipe. "
    "COMPOSITION (rules 16 [R-ALLYEARS] / 32 [R-SHARD] (d)): four per-year shard bundles "
    "solved in four containers with the PARENT RUNNING ZERO LP, then composed in the parent. "
    "The per-year _shared caches were UNIONED through lib.bundle_io.write_shared_input "
    "BEFORE the first registration call - the caiso-273 sec 5 trap, which on that session's "
    "first attempt rebuilt an EMPTY bench for every year but one and overwrote three "
    "committed bench parts. Verified here: the unioned content hashes reproduce the "
    "keeper's own byte-for-byte (campd-48c0f1dd36b6 / eia923-8ca120c6637d / "
    "eia930-3697b3115384) and all four committed bench parts are byte-identical after "
    "registration. Every shard's config signature was re-verified in the parent from its "
    "own run_config.json, never from a shard's claim, and each re-solve reproduces its "
    "first-pass load-weighted price to within 0.004 $/MWh. "
    "COST DISCLOSED: the first six Arm B / Arm A shards were told NOT to commit "
    "system.parquet and dispatch/, which the registration path requires, so four Arm B "
    "years were RE-SOLVED to recover them after the original containers were archived. That "
    "was the session's own prompt error; no conclusion depends on the re-solve, since every "
    "gate number was computed in the parent from the committed hourly/ sidecars."
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
    """Write ``calibration_attestation.json`` for a caiso-275 Arm B bundle."""
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
