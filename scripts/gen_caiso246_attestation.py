"""Write the caiso-246 bundle's attestation (the B1 arm; no control is solved — G-CTRL form 2).

One bundle is produced this session and it needs a C6 attestation — an
unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT.
No control is solved: the arm has two measured-inert years (2023, 2024 —
12/12 EIA survey coverage, 0 rows in the pre-solve footprint), so G-CTRL takes
caiso-240's dispatch-identity form 2 under the owner's caiso-241 §B2 carve-out
(``PRECOMMIT-caiso246-spot-coverage-2026-09-04.md`` §1).

The ``gen_caisoNNN`` series pattern is unchanged (E10: an attestation is
generated AT the promotion, every premise computed, never typed): the caiso-243
keeper's committed attestation is carried, ``attested_by`` is re-stamped with
the narrative for THIS bundle, and the ``price_tail`` (C3c) exception magnitudes
are RE-MEASURED on this bundle's own committed sidecars. ``free_parameters`` is
not edited here — ``scripts/build_dof_ledger.py`` rebuilds it afterwards.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso246_attestation.py \
        --bundle results/calibration/caiso246_b1_spot_coverage \
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
KEEPER = REPO / "results/calibration/caiso243_b1_f923_fallback_guard"

_SHARED = (
    "caiso-246 session (2026-09-04): the RULE 14 [R-ACCURATE] / RULE 19 "
    "[R-ONE-MECH] / RULE 21 [R-DOF] / RULE 25 [R-ISO-SCOPE] COVERAGE repair of "
    "the keeper's own designed gas-pricing mechanism. THE OBJECT "
    "(PRECOMMIT-caiso246-spot-coverage-2026-09-04.md §0.2, queue item C of "
    "caiso-244/245): the CAISO hub-basis overlay covered 9/12 months in 2025 "
    "(Sep/Oct/Nov open) against 12/12 in 2023-24, which is what let the F923 "
    "plant-level fallback layer show through (caiso-242 §5, caiso-243's object, "
    "D3, the autumn-2025 slab). MEASURED FROM THE SOURCE, not inferred: EIA "
    "publishes N3050CA3 (CA citygate, monthly) as NA for 2025-09, -10, -11 "
    "(evidence data/raw/gas-prices/eia_citygate_CA_monthly.csv, parsed from the "
    "fetched xls) while the measured DAILY CA composite citygate spot the keeper "
    "prices gas at (caiso_citygate_spot_level, caiso-84) carries 21 / 22 / 12 "
    "prints in those months (means 3.24 / 2.87 / 3.20 $/MMBtu; HH 2.97 / 3.20 / "
    "3.79). Under spot_level the survey VALUE is never used where prints exist, "
    "so the survey row was a GATE and nothing else — the coverage gap is a GATE "
    "ARTIFACT keyed to a series EIA did not publish, not a data hole. THE ARM: "
    "ScenarioConfig.caiso_citygate_spot_coverage (default off; backcast-only "
    "overlay field; requires gas_hub_basis_overlay + caiso_citygate_spot_level; "
    "CAISO-only) — data/fuel/hubs.py::_caiso_hub_daily_gas_prices covers a "
    "month with measured daily prints of its OWN even when the survey has no "
    "basis row, its day series built EXACTLY as every other spot-level month "
    "(flow-date staircase / calendar interpolation, "
    "+CAISO_CITYGATE_TRANSPORT_ADDER 0.46 layered by the caller); months with "
    "neither stay uncovered. NO new constant, NO value chosen, ZERO free "
    "parameters. MEASURED PRE-SOLVE, zero LP (_caiso246_coverage_footprint.json): "
    "the on-recipe rebuild with the flag ON differs from the keeper rebuild in "
    "gas rows x Sep-Nov-2025 hours ONLY -- all 1,453 gas rows / 29,277.8 MW, 0 "
    "non-gas rows, 0 cells outside Sep-Nov, 0 rows in 2023 and 2024; "
    "capacity-weighted CA gas price Sep 4.2134 -> 3.6353 (fuel-side mc -5.93 "
    "$/MWh), Oct 4.3158 -> 3.1858 (-11.26), Nov 5.5714 -> 3.7643 (-16.29); "
    "plant 55077's own November row 96.161 -> 3.764 $/MMBtu, so caiso-243's "
    "open D3 closes BY CONSEQUENCE (the overlay overwrites the plant layer), "
    "reported as a consequence not a purpose; the F923 fallback reaches 0 of "
    "36 training-window months. G-CTRL: form 2 (caiso-240 dispatch identity in "
    "the two measured-inert years) under the owner's caiso-241 §B2 carve-out: "
    "no control solved, 2023/2024 must reproduce the keeper at 0.000 TWh per "
    "class and 0.000 $/MWh. DIRECTION DISCLOSED BEFORE ANY SOLVE AND NEVER "
    "ARGUED FROM (rule 1 [R-STRUCT]): the spot means sit BELOW the F923 "
    "state-mean fallback (~4.2 / 4.4 / 4.38) in all three months, so ~29 GW of "
    "CA gas is repriced DOWN for Sep-Nov 2025 and C3a-2025 moves DOWN -- the "
    "FIFTH consecutive favourable direction in this lane (caiso-241, -242, "
    "-243, -246 after caiso-244/245's zero-arm measurements), stated as such; "
    "the pre-registered price-leg envelope on the assembled offers is "
    "[-3.1376, +0.1849] $/MWh for 2025 and exactly [0, 0] for 2023/2024, and "
    "P-3 predicted the measured move lands in [-1.0, -0.2] with NO verdict "
    "change in any year (the arm does NOT close C3a-2025, required -1.498). "
    "The promotion basis is STRUCTURAL and excludes C3a's verdict in either "
    "direction (§4). Form (ii) of the import object was CLOSED AT PHASE A from "
    "the committed record (OASIS public bids are masked, no intertie id -- the "
    "caiso-150 wall). HOLDOUT: CAISO holds no `complete` and no `final` marker, "
    "the spend freeze is ACTIVE, and every read and the one solve stayed inside "
    "2023-2025."
)

_B1 = "THIS BUNDLE IS THE B1 ARM (single-flag delta). " + _SHARED

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
    """Carry the caiso-243 keeper attestation onto the caiso-246 bundle."""
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
    tag = "caiso-246 B1 arm"
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
                    "disclosed PASS->FAIL flip vs the caiso-243 keeper, "
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
