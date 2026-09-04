"""Write a caiso-243 bundle's attestation (the B1 arm; no control is solved — G-CTRL form 2).

One bundle is produced this session and it needs a C6 attestation — an
unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT
(``PRECOMMIT-caiso243-f923-fallback-guard-2026-09-04.md`` §5.5). No control is
solved: the arm has two measured-inert years, so G-CTRL takes caiso-240's
dispatch-identity form 2 at the owner's choice (precommit §0.4).

The ``gen_caisoNNN`` series pattern is unchanged (E10: an attestation is
generated AT the promotion, every premise computed, never typed): the caiso-241
keeper's committed attestation is carried, ``attested_by`` is re-stamped with
the narrative for THIS bundle, and the ``price_tail`` (C3c) exception magnitudes
are RE-MEASURED on this bundle's own committed sidecars. ``free_parameters`` is
not edited here — ``scripts/build_dof_ledger.py`` rebuilds it afterwards.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso243_attestation.py \
        --bundle results/calibration/caiso243_b1_f923_fallback_guard \
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
KEEPER = REPO / "results/calibration/caiso241_b1_ctpeaker_committed"

_SHARED = (
    "caiso-243 session (2026-09-04): the RULE 14 [R-ACCURATE] / RULE 19 "
    "[R-ONE-MECH] / RULE 21 [R-DOF] / RULE 25 [R-ISO-SCOPE] DATA-INTEGRITY "
    "repair of the F923 low-volume fallback defect, repair form (a)+(c) "
    "CHOSEN BY THE OWNER from the three shapes caiso-242 measured and "
    "deliberately did not select. THE OBJECT "
    "(FINDING-caiso242-offer-basis-identity-2026-09-03.md §5-§6): three "
    "compounding defects delivered one EIA-923 row -- plant 55077 (NV), "
    "96.161 $/MMBtu on 5,234 MMBtu, 2.6 % of its own normal monthly volume, a "
    "fixed/reservation charge over a near-zero denominator, not a marginal "
    "delivered price -- to 2,446 MW of its CAISO neighbours (55518 960.0, "
    "55656 779.0, 55295 591.0 MW of CC_REGULAR among them) at ~$736/MWh for "
    "all 720 hours of November 2025: (D1) `state` was EMPTY on 100 % of the "
    "CAISO gas fleet (1,411/1,411 rows, 29,319 MW) because "
    "data/fleet/assembly.py::bins_to_fleet never set Generator.state, so the "
    "fallback's documented state-first donor tier -- the ONLY tier carrying a "
    "distinct-reporter floor (nearby_fuel_price_min_state_plants = 2) -- was "
    "skipped fleet-wide on every plant-level fleet (CAISO, PJM, MISO, NYISO, "
    "NEISO); (D2) the zone tier it fell to had NO reporter floor and its pool "
    "for those rows held exactly ONE plant, 55077, whose price it returned to "
    "five decimals; (D3) the source row itself. Reachable only because the "
    "CAISO hub-basis overlay covers 9/12 months in 2025 (Sep/Oct/Nov open) "
    "against 12/12 in 2023-24, which is why no keeper caught it. THE REPAIR: "
    "ScenarioConfig.fleet_state_from_eia860 (form (c), the root cause of D1 "
    "-- bins_to_fleet stamps each generator's USPS state from the EIA-860 "
    "plant table, data/raw/eia-860/eia860_plant.parquet, so the designed tier "
    "order is reachable) and ScenarioConfig.nearby_fuel_price_zone_donor_guard "
    "(form (a), D2 -- the zone tier requires the SAME registered floor the "
    "state tier already carries). NO new constant, NO value chosen, ZERO free "
    "parameters. Form (b), a volume-admissibility cut on F923 rows, was NOT "
    "armed: every candidate cut is a new parameter pair with no measured "
    "identification (rule 5), and the tightest swept cut (2 % of the "
    "plant-year median) MISSES the motivating row (55077-Nov is 2.62 %). "
    "MEASURED PRE-SOLVE, zero LP (_caiso243_fallback_footprint.json, "
    "_caiso243_gstruct_presolve.json): the coded mechanism reproduces the "
    "pre-registered footprint BYTE FOR BYTE -- 1,322 rows / 25,568.3 MW of CA "
    "gas re-tier onto the 6-reporter CA state mean in Sep/Oct/Nov 2025 only "
    "(Nov cap-weighted 13.47 -> 4.38 $/MMBtu; the 96.161 rows to 4.38; "
    "NP15/LA_BASIN/ZP26 by < $1/MMBtu); 0 non-gas rows; 0 rows in 2023 and "
    "2024 (12/12 overlay); (a)+(c) byte-identical to (c) alone on CAISO, so "
    "(a) is armed as the protective generic guard and is measured INERT here. "
    "WHAT IT DOES NOT TOUCH, disclosed before the solve: plant 55077's OWN "
    "reported row (370.1 MW CC_REGULAR at ~$736/MWh, Nov-2025) -- tier 1 is "
    "not a fallback; D3 stays open as an owner ask. G-CTRL: form 4 (code-path "
    "emptiness) is VOID by its letter (one ruff-format commit, b9384baf, "
    "touched campd_bins.py and offer_curves.py since the keeper's 607f9324 -- "
    "both AST-IDENTICAL, reported not used); form 2 (caiso-240 dispatch "
    "identity in the two measured-inert years) binds under the owner's "
    "caiso-241 §B2 carve-out and was the owner's choice: no control solved, "
    "2023/2024 class energies must reproduce the keeper to 0.001 TWh. "
    "DIRECTION DISCLOSED BEFORE ANY SOLVE AND NEVER ARGUED FROM (rule 1 "
    "[R-STRUCT]): restoring ~2.4 GW of cheap CC to the Sep-Nov 2025 stack is "
    "FAVOURABLE to the sole failing gate (C3a-2025 required move -1.878 "
    "$/MWh) -- the THIRD consecutive favourable-direction repair in this lane "
    "(caiso-241, caiso-242, caiso-243), stated as such; the pre-registered "
    "price-leg envelope on the assembled offers is [-2.634, +0.311] $/MWh for "
    "2025 and exactly [0, 0] for 2023/2024, and P-2 predicted the measured "
    "move lands in [-0.60, 0.00] with NO verdict change in any year. The "
    "promotion basis is STRUCTURAL and excludes C3a's verdict in either "
    "direction. HOLDOUT: CAISO holds no `complete` and no `final` marker, the "
    "spend freeze is ACTIVE, and every read and the one solve stayed inside "
    "2023-2025."
)

_B1 = (
    "THIS BUNDLE IS THE B1 ARM (two-flag delta, both the owner-chosen repair). "
    + _SHARED
)

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
    """Carry the caiso-241 keeper attestation onto the caiso-243 bundle."""
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
    tag = "caiso-243 B1 arm"
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
                    "disclosed PASS->FAIL flip vs the caiso-241 keeper, "
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
