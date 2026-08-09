"""Write the ercot-185 A/B pair's `calibration_attestation.json` files.

Derived from the ercot181 keeper's attestation, which is the correct base
because the ercot-185 arm is a **single mechanism delta on that recipe** and
adds **ZERO free parameters** — so the DOF ledger (`free_parameters`) is carried
verbatim, which is itself the G-DOF evidence. Only `governance.attested_by` and
the carried C3c `exceptions` magnitudes are re-written per run.

Usage::

    python scripts/gen_ercot185_attestation.py \
        --base results/calibration/ercot185_shapedcontrol_A \
        --arm  results/calibration/ercot185_shapedarm_B \
        --keeper results/calibration/ercot181_positiontail_B
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
    "ercot-185 2026-08-09 — the A/B CONTROL: a same-HEAD replay of the "
    "2026-08-09-run181-position-tail keeper recipe with the ercot-185 gate at "
    "its DEFAULT (ercot_partial_outage_shaped_derate=false), i.e. the incumbent "
    "flat partial-outage plateau extract, byte-unchanged (SP-0/SP-1 sha256 "
    "8d6f049e…c736b5). It exists because the run181 keeper is known not to "
    "reproduce at current main (ercot-173 §5, carried through ercot-174 §5 item "
    "4), so every ercot-185 gate is scored on a same-HEAD pair rather than "
    "against the committed keeper's ledgered numbers. No mechanism is armed and "
    "no free parameter is added; the DOF ledger is the keeper's, verbatim. "
    "docs/PRECOMMIT-ercot185-fault3-partial-layer-construction-2026-08-09.md"
)

_ARM_ATTEST = (
    "ercot-185 2026-08-09 — the control plus ONE mechanism delta: "
    "ercot_partial_outage_shaped_derate=true (scripts/replay_keeper.py --set), "
    "the fault-3 partial-layer CONSTRUCTION repair authorized by the signed "
    "owner ruling of the 2026-08-09 sitting (card D2 option C, G-COAL148 carried "
    "live). NOT a composition change: the f_window × f_partial product is "
    "untouched and ERCOT-148/149 is not repealed. The partial-outage plateau "
    "stops imposing a multi-week MEDIAN OF DAILY MAXIMA as an HOURLY ceiling "
    "(FINDING-ercot172 §4 fault 3); the same plateaus over the same day spans "
    "carry a day-resolved profile clip(f0·sm[d]/median(sm[i:j]), 0, 1), with f0 "
    "the incumbent's own flat factor and sm the frozen detector's own centered "
    "_SMOOTH_DAYS rolling median of daily-max CF. Both are medians of the SAME "
    "daily-maximum series differing only in the median's window — a grain "
    "refinement IN TIME of one measured statistic (rule 23 [R-FROZEN-DERIVE]; "
    "trigger = the signed ruling + the ercot-172 measurement, never a residual). "
    "ZERO new fitted scalars, so the DOF ledger is the keeper's verbatim and "
    "G-DOF passes by construction. Scaling commutes with the median, so "
    "median(shaped)=f0 exactly: a provable pure re-shaping, never a net lift or "
    "cut (SP-6, max deviation 0.0005; measured two-sidedness ~50/50 in every "
    "year against the 100%-above signature of the adjudicated-dead composition "
    "arms). docs/PRECOMMIT-ercot185-fault3-partial-layer-construction-2026-08-09.md"
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
    att = json.loads(json.dumps(keeper_attest))  # deep copy
    att["governance"]["attested_by"] = attested_by
    counts = _tail_counts(bundle)
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") == "price_tail" and year in counts:
            exc["magnitude"] = (
                f"model {counts[year]} h vs actual RT {ACTUAL_TAIL[year]} h "
                f"> $200/MWh (re-measured on the ercot-185 {tag})"
            )
            exc["reason"] = re.sub(
                r"\s*CARRIED ONTO THE ercot-185.*$", "", exc.get("reason", "")
            ) + (
                " CARRIED ONTO THE ercot-185 "
                f"{tag.upper()}: the fault-3 construction repair is an "
                "AVAILABILITY-envelope change on measured plateau hours and the "
                "exhaustion record is unchanged; the counts are re-measured on "
                "this run and reported at full magnitude."
            )
    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(f"wrote {path} (tail counts {counts})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument(
        "--keeper",
        type=Path,
        default=REPO / "results/calibration/ercot181_positiontail_B",
    )
    args = ap.parse_args()

    keeper_attest = json.loads(
        (args.keeper / "calibration_attestation.json").read_text()
    )
    _write(args.base, keeper_attest, _CONTROL_ATTEST, "control")
    _write(args.arm, keeper_attest, _ARM_ATTEST, "arm")


if __name__ == "__main__":
    main()
