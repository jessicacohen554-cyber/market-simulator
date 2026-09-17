"""pjm-h9c — what does re-deriving the PJM offer surface over 2020-2025 do to 2023-2025?

ZERO LP. Pre-registration: ``docs/PRECOMMIT-pjm-h9c-offer-surface-own-year-2026-09-16.md`` §3.

THE RISK THIS MEASURES. ``derive_pjm_offer_midcurve`` computes each unit's physics medians over
**every month file it is given** and segments on those medians, so adding 2020-2022 to the corpus
can move a unit between ``CT_FAST`` / ``CC_LIKE`` / ``LONG_RUN`` — which would change the
**2023-2025** ladders as well, in a change that was only ever meant to give the held-out years
their own. The PRECOMMIT registers three readings, all of them about what the re-derivation DOES
and none of them gated on a residual (rule 1 ``[R-STRUCT]``):

* **D-1 SEGMENT STABILITY** — ``segment_units`` against the frozen counts
  (CT_FAST 1064 · CC_LIKE 883 · LONG_RUN 216).
* **D-2 IN-SAMPLE LADDER DRIFT** — ``six_year(2023..2025) − frozen(2023..2025)`` per
  (segment, bin, share). **If these move, the arm is not confined to the held-out years and the
  RESULT must say so in its headline.**
* **D-3 REPRODUCTION FLOOR** — D-2 is read against the drift pjm-h9 already measured between the
  frozen surface and a same-years re-derivation from PJM's live feed (median **0.10** implied-HR,
  sign-balanced, 2025 exact; ``RESULT-pjm-h9-comparator-admixture-bound`` §3). Drift at or below
  that floor is PJM restatement noise, not this change.

Run it AFTER the six-year derive has written a candidate surface, pointing at both files:

    python3 scripts/probes/_pjm_h9c_surface_drift.py --frozen <frozen.json> --candidate <new.json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/calibration/_pjm_h9c_surface_drift.json"

#: The frozen three-year segment census (committed artifact provenance).
FROZEN_SEGMENTS = {"CC_LIKE": 883, "CT_FAST": 1064, "LONG_RUN": 216}
#: pjm-h9 §3's measured same-years reproduction floor, in implied-HR units.
REPRO_FLOOR_MEDIAN = 0.10
IN_SAMPLE = ("2023", "2024", "2025")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--frozen",
        default="data/raw/_validation-source/pjm_offer_midcurve_condbinned.json",
    )
    ap.add_argument("--candidate", required=True)
    args = ap.parse_args(argv)

    fz = json.loads((REPO / args.frozen).read_text())
    cd = json.loads(Path(args.candidate).read_text())
    out: dict = {
        "precommit": "docs/PRECOMMIT-pjm-h9c-offer-surface-own-year-2026-09-16.md",
        "frozen": args.frozen,
        "candidate": str(args.candidate),
    }

    # ---- D-1 segment stability ---------------------------------------------
    cand_seg = cd["_provenance"]["segment_units"]
    d1 = {
        s: {
            "frozen": FROZEN_SEGMENTS.get(s),
            "candidate": cand_seg.get(s),
            "delta": (cand_seg.get(s) or 0) - (FROZEN_SEGMENTS.get(s) or 0),
        }
        for s in sorted(set(FROZEN_SEGMENTS) | set(cand_seg))
    }
    out["D1_segment_stability"] = d1
    moved = sum(abs(v["delta"]) for v in d1.values())
    print("D-1 SEGMENT STABILITY")
    for s, v in d1.items():
        print(
            f"   {s:<9} frozen {v['frozen']!s:>6}  candidate {v['candidate']!s:>6}"
            f"  delta {v['delta']:+d}"
        )
    print(
        f"   => total membership moves: {moved}"
        f"{'  (STABLE)' if moved == 0 else '  <-- NOT confined to the held-out years'}"
    )

    # ---- D-2 in-sample ladder drift ----------------------------------------
    rows = []
    for seg in sorted(set(fz) - {"_provenance"}):
        if seg not in cd:
            continue
        for y in IN_SAMPLE:
            fl = fz[seg].get("years", {}).get(y)
            cl = cd[seg].get("years", {}).get(y)
            if not fl or not cl:
                continue
            for b, (fb, cb) in enumerate(zip(fl, cl)):
                for (fs, fv), (cs, cv) in zip(fb, cb):
                    if abs(float(fs) - float(cs)) > 1e-9:
                        continue
                    a, c = float(fv), float(cv)
                    if np.isnan(a) or np.isnan(c):
                        continue
                    rows.append(
                        {
                            "segment": seg,
                            "year": int(y),
                            "bin": b,
                            "share": round(float(fs), 3),
                            "frozen": a,
                            "candidate": c,
                            "delta": round(c - a, 4),
                        }
                    )
    dv = np.array([abs(r["delta"]) for r in rows]) if rows else np.array([])
    d2 = {
        "cells": len(rows),
        "moved": int((dv > 1e-9).sum()) if dv.size else 0,
        "abs_delta_median": round(float(np.median(dv)), 4) if dv.size else None,
        "abs_delta_p90": round(float(np.percentile(dv, 90)), 4) if dv.size else None,
        "abs_delta_max": round(float(dv.max()), 4) if dv.size else None,
        "sign_up": int(sum(1 for r in rows if r["delta"] > 0)),
        "sign_down": int(sum(1 for r in rows if r["delta"] < 0)),
        "worst": sorted(rows, key=lambda r: -abs(r["delta"]))[:12],
    }
    out["D2_in_sample_ladder_drift"] = d2
    print("\nD-2 IN-SAMPLE LADDER DRIFT (2023-2025, frozen vs six-year derive)")
    print(
        f"   cells {d2['cells']}   moved {d2['moved']}   "
        f"median {d2['abs_delta_median']}   p90 {d2['abs_delta_p90']}   "
        f"max {d2['abs_delta_max']}   (up {d2['sign_up']} / down {d2['sign_down']})"
    )
    for r in d2["worst"][:6]:
        print(
            f"   {r['segment']:<9} {r['year']} bin{r['bin']} s{r['share']:<5} "
            f"{r['frozen']:>8.3f} -> {r['candidate']:>8.3f}  {r['delta']:+.3f}"
        )

    # ---- D-3 read against the measured reproduction floor -------------------
    med = d2["abs_delta_median"]
    verdict = (
        "NO IN-SAMPLE LADDER (nothing to compare)"
        if med is None
        else "AT OR BELOW the pjm-h9 reproduction floor — restatement noise, not this change"
        if med <= REPRO_FLOOR_MEDIAN
        else "ABOVE the pjm-h9 reproduction floor — this change moves the in-sample ladders"
    )
    out["D3_vs_reproduction_floor"] = {
        "floor_median_implied_hr": REPRO_FLOOR_MEDIAN,
        "measured_median": med,
        "verdict": verdict,
    }
    print(
        f"\nD-3 vs the pjm-h9 reproduction floor ({REPRO_FLOOR_MEDIAN} implied-HR median)"
    )
    print(f"   {verdict}")

    # ---- the new years, reported for the record -----------------------------
    new = {}
    for seg in sorted(set(cd) - {"_provenance"}):
        have = sorted(cd[seg].get("years", {}))
        new[seg] = have
    out["candidate_years_per_segment"] = new
    print("\nCANDIDATE own-year coverage:", json.dumps(new))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
