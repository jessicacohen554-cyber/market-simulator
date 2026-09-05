"""Write the ercot-231 combined bundle's governance attestation.

The ercot-231 combined candidate (`ercot231_tiegtc_full`) is the ercot-223
keeper recipe with TWO structural repairs, both measured-input, zero fitted
scalars (`docs/PRECOMMIT-ercot231-nonas-tightness-2026-08-23.md` +
`docs/FINDING-ercot231-nonas-tightness-2026-08-23.md`):

* ``ercot_tie_zonal_interchange`` — the netted DC-tie interchange placed at
  the tie-host zones from the measured EIA-930 per-neighbor split (N1a);
* the ``gtc-limits`` clean partition restored, so
  ``ercot_gtc_limits_measured=True`` (already in the recipe) actually solves
  on the measured NP6-86 caps instead of the silent static-TTC fallback the
  keeper lineage had been riding (the FINDING §2 discovery).

Beyond the ercot-223 generator this one also discharges the promotion-owed
re-wording of the C3c exceptions-ledger reason: the ercot-216 measurement
spent the OPEN RESIDUAL LANE's both named candidates, so the reason text
now records the lane as SPENT and rests the limitation on the full
226/227/230/231 exhaustion record. ``free_parameters`` is not edited here —
``scripts/build_dof_ledger.py`` rebuilds it afterwards (G-DOF reads that).

Usage::

    PYTHONPATH=.:src python scripts/gen_ercot231_attestation.py \
        --arm results/calibration/ercot231_tiegtc_full
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
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}
KEEPER = REPO / "results/calibration/ercot223_release_arm"

_ATTEST_ARM = (
    "ercot-231 session (2026-08-23): the COMBINED tie-zone + measured-GTC "
    "candidate (PRECOMMIT-ercot231-nonas-tightness-2026-08-23.md; FINDING "
    "same date) — the ercot-223 keeper recipe with two measured-input "
    "structural repairs and ZERO fitted scalars. (1) "
    "ercot_tie_zonal_interchange: the netted DC-tie interchange placed at "
    "the tie-host zones (SWPP flow to Northeast 600/820 + North 220/820 by "
    "published tie rating, CEN flow to South; constants.ERCOT_DC_TIE_ZONE_MAP) "
    "from the measured EIA-930 BA-to-BA per-neighbor series, replacing the "
    "load-share spread — the PJM pjm_zonal_interchange precedent; column "
    "sums conserve the netted total exactly so the system energy balance is "
    "unchanged by construction. Grounding: all 114 keeper-2023 missed hours "
    "were net imports (p50 -814 MW, SWPP pinned at its tie limit), and the "
    "single-delta A/B moved C3a-2023 -39.7 -> -38.1 (+1.6 pp), C3b 0.729 -> "
    "0.696, miss split 67/114/7 -> 80/101/11, d_price_at_miss p50 +$8.28, "
    "97.4% window-concentrated, lambda-carried 1.0017 "
    "(ercot231_probe_n1a.json). (2) the gtc-limits clean partition restored: "
    "the recipe's own ercot_gtc_limits_measured=True had been silently "
    "degrading to static TTC across the ercot-215/221/223 lineage (G-REPRO "
    "numeric identity is achieved exactly and only WITHOUT the partition — "
    "FINDING §2); the restoration is the rule-14 repair, gates-clean as its "
    "own single delta (ercot231_gtc_gates.json, G-SPUR 11<->11). Judged by "
    "the PRECOMMIT-ercot231 §5.5/§5.6 criteria with the frozen "
    "ercot226/221 gate constructions; the N1a mechanical verdict "
    "(REJECTED-AS-ARMED on G-SPUR alone, 21 vs bar 14, all in-season, none "
    "above $500) is recorded unrewritten, and promotion is the owner's "
    "standing structural standard, given in-session in advance three times "
    "this session ('If structural integrity improves but gates regress that "
    "may still be a keeper' — the ercot-188/213/215/221 pattern)."
)

# The promotion-owed OPEN-RESIDUAL-LANE re-wording (charter deliverable),
# appended to each retained C3c exception's reason.
_C3C_CARRY = (
    " CARRIED ONTO THE ercot-231 COMBINED PROMOTION, WITH THE OPEN RESIDUAL "
    "LANE RE-WORDED AS SPENT (the re-wording owed since ercot-216, "
    "discharged here): ercot-216 (2026-08-17) spent the lane's both named "
    "candidates — (a) the storage AS-vs-energy split is "
    "ercot_storage_as_soc_reserve, armed since ercot-167 with its re-gate "
    "discharged RG-PASS (ercot-193), and (b) the CC headroom identification "
    "is item 11, FILED-UNLICENSED twice and CLOSED by the signed card-Q "
    "rule (Q-B automatic and final, ercot-191) — and measured the object "
    "empty on the keeper (dispatch matched fuel-by-fuel at the missed "
    "hours, RTORPA ~$1, PRC 5.7-7.7 GW). The 'a mechanism that lands there "
    "simply PASSes' clause therefore names no live route; the accepted "
    "limitation now rests on the full exhaustion record — AS procurement "
    "closed (ercot-226/227: every armed factor left d_price_at_miss at "
    "0.0), the within-year conduct family complete at every member "
    "(ercot-221/222/223/230: the keeper is the measured fixed point of its "
    "own adaptation map), and the non-AS tightness surface swept "
    "(ercot-231). The ercot-231 combined arm moves the count by PLACEMENT, "
    "not by scarcity formation: the measured DC-tie tie-zone attribution "
    "plus the measured-GTC restoration are physical-input repairs (zero "
    "fitted scalars) that let the existing competitive stack clear where "
    "the load actually sits. The counts are re-measured on this run and "
    "reported at full magnitude."
)


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model max-zonal > $200 tail count per year from the bundle sidecars."""
    counts: dict[int, int] = {}
    for year in YEARS:
        p = bundle / "hourly" / f"system_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["year"] == year) & (df["pass"] == "P1")]
        by_hour = df.groupby("hour")["price"].max()
        counts[year] = int((by_hour > 200.0).sum())
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument(
        "--still-failing",
        type=int,
        nargs="*",
        default=list(YEARS),
        help="years whose C3c still FAILS on the ARM's own scorecard",
    )
    args = ap.parse_args()

    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST_ARM
    counts = _tail_counts(args.arm)
    kept = []
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") != "price_tail":
            kept.append(exc)
            continue
        if year not in args.still_failing:
            continue  # band met on this bundle — a spent caveat is dropped
        exc["magnitude"] = (
            f"model {counts.get(year, '?')} h vs actual RT "
            f"{ACTUAL_TAIL[year]} h > $200/MWh (re-measured on the ercot-231 "
            "combined arm)"
        )
        exc["reason"] = str(exc.get("reason", "")) + _C3C_CARRY
        kept.append(exc)
    att["exceptions"] = kept
    path = args.arm / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} (tail counts {counts}; ledger years "
        f"{[e['year'] for e in kept if e.get('criterion') == 'price_tail']}; "
        "free_parameters left to build_dof_ledger.py)"
    )


if __name__ == "__main__":
    main()
