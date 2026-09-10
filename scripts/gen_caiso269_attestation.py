"""Write the caiso-269 bundle's attestation (the hod 22-23 clean-import window gap).

An unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT under the
rubric v3.3 / v3.6 standing rule, so the arm needs its own attestation before it can be
scored on its merits.

Pattern unchanged from ``gen_caiso_fuelvintage_attestation.py`` (E10: generated AT
registration, never typed): the LIVE keeper's committed attestation is carried,
``attested_by`` is re-stamped with the narrative for THIS bundle, and the ``price_tail``
(C3c) exception magnitudes are RE-MEASURED on this bundle's own committed sidecars.

The arm adds NO DOF-ledger row: the window is the complement the caiso-93 / caiso-94 /
caiso-87 constructions leave, the depth is those siblings' own p95 statistic taken over
exactly the window it arms, and the arming gate is caiso-253's PRE-REGISTERED [-2, +4]
raw-hub discriminator re-used unchanged. Zero new free parameters, zero new thresholds,
and no ``authorized_price_tuning`` block (no offer-curve multiplier is exercised).

Usage::

    PYTHONPATH=.:src python3 scripts/gen_caiso269_attestation.py \
        --bundle results/calibration/caiso269_lateevening_span
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
KEEPER = REPO / "results/calibration/caiso_fuelvintage_span"

_SHARED = (
    "caiso-269 session (2026-09-10): ONE STRUCTURAL MECHANISM, "
    "ScenarioConfig.caiso_dsw_lateevening_clean, solved as ONE flag on the committed "
    "keeper recipe 2026-09-09-caiso-fuelvintage-860-gas via --replay-bundle. "
    "Pre-registered in docs/PRECOMMIT-caiso269-lateevening-clean-2026-09-10.md, pushed "
    "before the first LP of any shard; measured in "
    "docs/RESULT-caiso269-lateevening-clean-2026-09-10.md. ZERO new free parameters, ZERO "
    "new thresholds, NO authorized_price_tuning block, DOF ledger unchanged. "
    "THE OBJECT IS A WINDOW GAP, not a new mechanism: the three DSW clean-depth "
    "constructions do not tile the clock — caiso-93 runs hod 0-5, caiso-94 runs hod 6-21, "
    "and caiso-87's surplus trigger is coverage-STARVED at hod 22-23 (ON in 0.3/0.8 pct of "
    "2024 and 1.6/1.9 pct of 2025 hod 22/23, caiso-253's G-WINDOW leg, which CLOSED the "
    "window question with '22-23 are OVERNIGHT-construction hours'). On the keeper's own "
    "committed sidecars the armed clean capability falls 3,420 MW at hod 21 to 33 MW at hod "
    "22 (2025) while the measured WECC_DSW corridor net import RISES across the same "
    "boundary, against a measured EIA-930 import deficit of 1.0-1.8 GW there. "
    "THE ARMING GATE IS caiso-253's OWN REFUSAL, ADOPTED UNCHANGED: that session refused "
    "extending raw-hub pricing to hod 22-23 because its pre-registered [-2, +4] raw-hub "
    "discriminator FAILED in 2023 (DA block median -3.98/-2.56) while PASSING in 2024 "
    "(-0.73/+0.11) and 2025 (-0.19/+0.06). This tranche arms an hour ONLY where the "
    "measured (month x hod) median DA CAISO-PaloVerde spread lies inside that same band, so "
    "2023 stays dark BY CONSTRUCTION (4 of 20 admissible buckets vs 18/24 and 19/24) — the "
    "DO-NOT-REDO is honoured by making the refusal criterion the gate. "
    "DEPTH: p95 of measured WECC_DSW corridor net import over the SAME hod 22-23 window the "
    "capability arms (the sibling derives' window-match rule), 6,120 / 6,429 / 6,697 MW for "
    "2023 / 2024 / 2025; FROZEN caiso-81/86/87/88 gates CV 0.037 (<= 0.20) and LOYO worst "
    "6.8 pct (<= 25 pct), tighter than the caiso-93 overnight depth. Producer "
    "scripts/data/derive_caiso_lateevening_clean_depth.py. EF 0 and the no-wheel WEIM basis "
    "are MEASURED for these two hours by caiso-253's G-WEDGE leg, not inherited. Netted per "
    "hour against the shaped firm block and all three sibling clean tranches (rule 19). "
    "ALL FOUR STOP GATES PASS: G-IDENT exactly ONE differing ScenarioConfig field; G-FOOT "
    "tranche dispatch EXACTLY 0.0000 MW outside hod 22-23 in every year and an annual "
    "import/gas substitution that is one-for-one (+0.826/+0.172/+0.764/+0.540 TWh import "
    "against -0.821/-0.172/-0.771/-0.551 TWh gas for 2022/23/24/25); G-DIR import "
    "+752/+1479, +236/+265, +865/+1332, +936/+850 MW at hod 22/23, positive everywhere, "
    "below the armed capability everywhere, and 2023 smallest by ~4x exactly as the gate "
    "predicts; G-NOFLIP no load-bearing criterion flips. G-CTRL FORM 4, NO CONTROL SOLVE "
    "SPENT — earned by a G-DRIFT code audit against the keeper's git_sha 873f7564 in which "
    "every changed hunk on the backcast path is INERT for CAISO (ERCOT-only benchmark "
    "rows, a default-off ERCOT-gated field, a NYISO-scoped declaration, comment-only "
    "constants, and the [R-HOLDOUT] gate removal). "
    "REPORTED AGAINST THE ARM: it does NOT achieve what the session was chartered for. "
    "2022's C3a stays FAIL at +12.90 pct against a <= +10 pct band (95.621 -> 95.389, i.e. "
    "0.27 pp of a 3.2 pp gap) and C3b stays FAIL at 0.2402, so CAISO's 2022 rung remains "
    "NOT-YET on the same two criteria. C1 CC_REGULAR moves AWAY from measured in 2023 "
    "(-3.431 -> -3.578 TWh) and 2024 (+0.111 -> -0.529) while moving toward it in 2022 and "
    "2025; no band is crossed (rubric v3.4 floor +/-5.27 TWh) so C1 holds PASS. "
    "IN ITS FAVOUR, and the reason it is promotable where caiso-267/268 were refused: it "
    "improves EVERY scored price and dispatch criterion in EVERY year without costing "
    "dispatch — C3a +13.17->+12.90 / +4.39->+4.33 / +8.90->+8.54 / +8.25->+7.87 pct, C3b "
    "0.2422->0.2402 / 0.0830->0.0827 / 0.1425->0.1391 / 0.1110->0.1070, and C4 gas NRMSE "
    "0.287->0.287 / 0.260->0.256 with the PRE-REGISTERED EXPOSURE C4-2025 going 0.298 -> "
    "0.294 against a <= 0.300 bound, i.e. AWAY from the edge (gas hourly r 0.877 -> 0.881)."
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
    """Write ``calibration_attestation.json`` for one caiso-269 bundle."""
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
