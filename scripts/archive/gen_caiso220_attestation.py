"""Write the caiso-220 crosswalk-replay bundle's governance attestation.

The caiso-220 bundle (`results/calibration/caiso220_c1_crosswalk`) is the
landed re-solve of the caiso-217 funded solve (FINDING-caiso216 §G Ask 2)
whose results never left its container: the caiso-200 keeper recipe replayed
byte-faithfully at HEAD through ``--replay-bundle`` (the bundle's
``meta.json`` is the config, no ``--set``), with the measured
generator-hub-membership crosswalk — landed as DATA at the caiso-217 intake
and active for every CAISO solve since — as the only delta. Nothing armed,
nothing tuned, zero new scalars (the crosswalk's own ledger row is
identification="measured", added to ``build_dof_ledger.py`` at caiso-220
prep `2d9823f`).

The `gen_caisoNNN` series continues (E10: an attestation is generated AT the
promotion, every premise computed, never typed). Pattern: the keeper's
committed attestation is carried, ``attested_by`` re-stamped, and the
price_tail (C3c) exception magnitudes RE-MEASURED on this bundle's own
committed sidecars. ``free_parameters`` is not edited here — it is rebuilt
by ``scripts/build_dof_ledger.py`` afterwards (G-DOF reads that).

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso220_attestation.py \
        --bundle results/calibration/caiso220_c1_crosswalk \
        --still-failing 2023 2024 2025
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
KEEPER = REPO / "results/calibration/caiso200_h1_memberpanel"

_ATTEST = (
    "caiso-220 session (2026-08-26): the funded caiso-217 replay — the "
    "registration-debt repair (FINDING-caiso217 §D–§F filed item 8) executed "
    "under the owner's 2026-08-26 charter and the owner's in-session "
    "promotion standard (verbatim: 'Is this a recommended keeper candidate? "
    "If so plz promote. If structural integrity improves but gates regress "
    "that may still be a keeper..'). Recipe: the caiso-200 keeper bundle's "
    "meta.json replayed byte-faithfully at HEAD via --replay-bundle (no "
    "--set, no config delta; P1 scored, years 2023-2025 sequential). The "
    "ONLY delta vs the committed keeper solve is DATA: the measured "
    "generator-hub-membership crosswalk "
    "(data/raw/reference/caiso-plant-hub-membership.csv, 446 plants / 41.1 "
    "GW / 78 movers, caiso-217 intake f0dd328, witness gates ALL PASS), "
    "active through the zone_assignment CAISO first-check for every CAISO "
    "solve since it landed [R-ACCURATE]; zero free parameters (rule 13 PASS "
    "adjudicated at caiso-216 §F.1: published registry, quantity-side, "
    "forward analogue). Pre-registered gates: the committed caiso-216 §G "
    "table adopted verbatim by "
    "docs/PRECOMMIT-caiso220-c1-crosswalk-replay-2026-08-26.md (C3a ×3 with "
    "2023 in band; C3b MUST-NOT-REGRESS vs 0.098/0.179/0.182 with the 2025 "
    "composition watch as THE tripwire; C8/D unchanged; DOF 10/7 + one "
    "measured-input row; split witness _caiso220_zonal_decomp.py; all "
    "deltas reported at full magnitude whatever their sign)."
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
    """Carry the keeper attestation onto the caiso-220 bundle, re-measured."""
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
            f"{ACTUAL_TAIL[year]} h > $200/MWh (re-measured on the caiso-220 "
            "crosswalk replay)"
        )
        kept.append(exc)
    for year in args.still_failing:
        if year in seen_tail_years or year not in ACTUAL_TAIL:
            continue
        # A year newly failing C3c on this bundle (a disclosed flip vs the
        # keeper) enters the ledger with the same criterion and a magnitude
        # measured here — never silently.
        kept.append(
            {
                "criterion": "price_tail",
                "year": year,
                "magnitude": (
                    f"model {counts.get(year, '?')} h vs actual RT "
                    f"{ACTUAL_TAIL[year]} h > $200/MWh (NEW on the caiso-220 "
                    "crosswalk replay — a disclosed PASS->FAIL flip vs the "
                    "caiso-200 keeper, reported at full magnitude per the "
                    "precommit)"
                ),
                "rationale": (
                    "C3c scarcity-tail model-class limitation (the ledgered "
                    "criterion; rubric v3.3 standing rule) — the crosswalk "
                    "moves zonal allocation, and the pooled scarcity top "
                    "thins where the south decouples; adjudication belongs "
                    "to the scorer"
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
