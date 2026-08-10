"""Write the ercot-186 A/B pair's `calibration_attestation.json` files.

Derived from the ercot185 keeper's attestation, which is the correct base
because the ercot-186 arm is a **single grain-correction delta on that recipe**
and adds **ZERO free parameters** — so the DOF ledger (`free_parameters`) is
carried verbatim, which is itself the G-DOF evidence. Only
`governance.attested_by` and the carried C3c `exceptions` magnitudes are
re-written per run.

Usage::

    python scripts/gen_ercot186_attestation.py \
        --base results/calibration/ercot186_graincontrol_A \
        --arm  results/calibration/ercot186_plantphysics_B \
        --keeper results/calibration/ercot185_shapedarm_B
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}

_CONTROL_ATTEST = (
    "ercot-186 2026-08-10 — the A/B CONTROL: a same-HEAD replay of the "
    "2026-08-09-ercot185-shaped-partial keeper recipe with the ercot-186 gate "
    "at its DEFAULT (ercot_faststart_pool_plant_physics=false), i.e. the "
    "fast-start pool's rule-18 physics gate still read at TRANCHE-ROW grain, "
    "where it is vacuous. It exists because the ERCOT keeper is known not to "
    "reproduce byte-for-byte at current main (ercot-173 §5, carried through "
    "ercot-174/185), so every ercot-186 gate is scored on a same-HEAD pair "
    "rather than against the committed keeper's ledgered numbers. No mechanism "
    "is armed and no free parameter is added; the DOF ledger is the keeper's, "
    "verbatim. docs/PRECOMMIT-ercot186-rule18-grain-2026-08-10.md"
)

_ARM_ATTEST = (
    "ercot-186 2026-08-10 — the control plus ONE delta: "
    "ercot_faststart_pool_plant_physics=true (scripts/replay_keeper.py --set), "
    "the rule-18 [R-PHYSICS] GRAIN REPAIR authorized by the signed owner "
    "sitting of 2026-08-09 (card D3 option (ii), sequenced after D2 — which "
    "landed as this keeper). THE DEFECT: fleet assembly records the "
    "UC-coupling physics tags on a plant's `committed` anchor slice ALONE "
    "(deliberately — a bid tranche must acquire no commitment coupling), so "
    "every econ*/peak* row, exactly the rows the ERCOT-88 fast-start pool "
    "prices, carries min_down = min_run = 0. The leg's own eligibility test, "
    "`skip if min_down > FASTSTART_POOL_MIN_DOWN_HOURS`, is therefore False "
    "for EVERY row it can reach: vacuous, with its effective scope collapsed "
    "onto the CT_PEAKER class map — the hard-coded class tuple rule 18 "
    "forbids. THE REPAIR: the SAME UNCHANGED bound (2.0 h) evaluated at PLANT "
    "grain and inherited by that plant's bid rows — the ercot-176 Amendment-2 "
    "construction generalized to a shared helper "
    "(fleet/offer_surfaces.py::_plant_unit_physics), fed by the plant's own "
    "assembled physics now stamped on every tranche row. A GRAIN correction, "
    "not a parameter: ZERO new fitted scalars (so the DOF ledger is the "
    "keeper's verbatim and G-DOF passes by construction), no min-run bound "
    "added, no artifact re-derived (rule 23 untouched — nothing re-derives), "
    "no composition/ladder/boundary change, P1-only seam and P0 untouched. "
    "This is a LEGITIMACY repair: it is correct whether or not it improves any "
    "metric, and per rule 1 [R-STRUCT] a worse fit would not be grounds to "
    "revert it. docs/PRECOMMIT-ercot186-rule18-grain-2026-08-10.md"
)


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model hours > $200 per year, on the standing demand-weighted P1 basis."""
    out: dict[int, int] = {}
    for year in YEARS:
        p = bundle / "hourly" / f"system_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["year"] == year) & (df["pass"] == "P1")]
        num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
        den = df.groupby("hour")["demand"].sum()
        out[year] = int(((num / den) > 200.0).sum())
    return out


def _write(bundle: Path, keeper_attest: dict, attested_by: str, tag: str) -> None:
    """Write ``bundle``'s attestation from the keeper's, re-measuring C3c."""
    att = json.loads(json.dumps(keeper_attest))  # deep copy
    att["governance"]["attested_by"] = attested_by
    counts = _tail_counts(bundle)
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") == "price_tail" and year in counts:
            exc["magnitude"] = (
                f"model {counts[year]} h vs actual RT {ACTUAL_TAIL[year]} h "
                f"> $200/MWh (re-measured on the ercot-186 {tag})"
            )
            exc["reason"] = re.sub(
                r"\s*CARRIED ONTO THE ercot-186.*$", "", exc.get("reason", "")
            ) + (
                " CARRIED ONTO THE ercot-186 "
                f"{tag.upper()}: the rule-18 grain repair changes WHICH rows a "
                "measured offer surface is licensed to price, not the offer "
                "conduct the surface represents, and the exhaustion record is "
                "unchanged; the counts are re-measured on this run and reported "
                "at full magnitude."
            )
    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(f"wrote {path} (tail counts {counts})")


def main() -> None:
    """Write both bundles' attestations from the keeper's."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument(
        "--keeper",
        type=Path,
        default=REPO / "results/calibration/ercot185_shapedarm_B",
    )
    args = ap.parse_args()

    keeper_attest = json.loads(
        (args.keeper / "calibration_attestation.json").read_text()
    )
    _write(args.base, keeper_attest, _CONTROL_ATTEST, "control")
    _write(args.arm, keeper_attest, _ARM_ATTEST, "arm")


if __name__ == "__main__":
    main()
