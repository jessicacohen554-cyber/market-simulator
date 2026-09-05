"""Write the caiso-252 bundle's attestation (the B1 arm; NO control solve — G-CTRL form 4).

One bundle is produced this session and it needs a C6 attestation — an
unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT.
No control is solved: owner rule 2026-09-05 (rule 29 ``[R-SCREEN]`` clause b)
makes G-CTRL **form 4** the default, and the G-DRIFT code audit in
``PRECOMMIT-caiso252-c4-gas-nrmse-anatomy-2026-09-05.md`` Addendum A establishes
that every changed hunk on the backcast path between the keeper's ``git_sha``
90b2ef51 (the finding-stated solve basis) and HEAD is CAISO-backcast-inert, so the committed keeper IS the
control.

The ``gen_caisoNNN`` series pattern is unchanged (E10: an attestation is
generated AT the promotion, every premise computed, never typed): the caiso-251
keeper's committed attestation is carried, ``attested_by`` is re-stamped with
the narrative for THIS bundle, and the ``price_tail`` (C3c) exception
magnitudes are RE-MEASURED on this bundle's own committed sidecars.
``free_parameters`` is not edited here — ``scripts/build_dof_ledger.py``
rebuilds it afterwards.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso252_attestation.py \
        --bundle results/calibration/caiso252_arm_notrim \
        --arm b1 --still-failing 2023 2024
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
KEEPER = REPO / "results/calibration/caiso251_arm_nomargin"

_SHARED = (
    "caiso-252 session (2026-09-05): the evening-trim DISARM arm — "
    "caiso_dsw_daytime_evening_trim True -> False on the caiso-251 keeper "
    "recipe, ONE recorded override-bag value, ZERO new parameters, ZERO new "
    "fields, no derive re-run (PRECOMMIT-caiso252-c4-gas-nrmse-anatomy-"
    "2026-09-05.md Addendum A, pushed before the override was coded). THE "
    "OBJECT: the C4 2025 gas-fleet NRMSE cell (0.305 vs <= 0.30), which "
    "FINDING-caiso252 sec 2-3 measured as CC_REGULAR's DIURNAL error (90/87/95 "
    "pct of the gas MSE) mirroring the model's import shape hour for hour - "
    "night/evening under-import, mid-day over-import. The zero-LP read of the "
    "import stack found NO at-hub WEIM clean-transfer row for hod 18-23: "
    "caiso-93 covers 0-5, caiso-94 covered 6-21 until caiso-97 trimmed it to "
    "6-17 because the 2026-07-18 keeper OVER-imported the evening (+1.9/+2.1/"
    "+2.2 TWh vs EIA-930); on the caiso-251 keeper the sign has REVERSED "
    "(hod 18-21 UNDER-imported by 0.6-1.0 GW, CC over-generating +1.4 GW in "
    "exactly those hours), which is the new evidence rule 28(a) requires to "
    "re-test the trim. The measured admissibility of the row (FINDING-caiso94 "
    "sec 4A: evening 18-21 raw-hub spread CLEAN, 0 pct wedge) was never in "
    "question; the depth is the committed, frozen untrimmed measurement "
    "(5,441/5,762/5,998 MW). Rule-29 SCREEN on 2025 first (owner-directed AND "
    "the largest phase-0 footprint: 3.4-3.8 GW added at hod 18-21, 1.56 TWh "
    "clearing at the keeper's own duals), no control solve (owner rule, G-CTRL "
    "form 4 valid per the PRECOMMIT sec 4 G-DRIFT audit). DIRECTION HAZARD "
    "declared in advance: the SEVENTH consecutive favourable direction on "
    "C3a; C3a AND C4 are EXCLUDED from the promotion basis, which turns on "
    "G-FOOT / G-DIR / G-OVERSHOOT (the caiso-97 objection re-armed as this "
    "arm's own falsifier: the 2025 hod-18-21 import must land within "
    "[measured - 0.5, measured + 0.8] TWh) plus the absence of a new "
    "load-bearing failure in any year and the governance gates."
)

_B1 = "THIS BUNDLE IS THE ARM (single recorded-override delta on the caiso-251 keeper). " + _SHARED

_ATTEST = {"b1": _B1}


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
    """Carry the caiso-251 keeper attestation onto the caiso-251 bundle."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--arm", choices=sorted(_ATTEST), required=True)
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
    att["governance"]["attested_by"] = _ATTEST[args.arm]
    counts = _tail_counts(args.bundle)
    tag = "caiso-252 evening-trim disarm arm"
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
                    "disclosed PASS->FAIL flip vs the caiso-251 keeper, "
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
