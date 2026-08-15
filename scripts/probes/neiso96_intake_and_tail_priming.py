"""Record the H1-2026 NEISO actuals intake and the C3c tail deriver's state.

neiso-96, 2026-08-15.  Two things are recorded, both read-only:

1. THE INTAKE.  Per-year shape of
   ``data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet`` after the
   H1-2026 block landed -- rows, coverage, mean/max, and the actual RT hours
   above NEISO's $300 scarcity threshold.  The point of comparison is 2019,
   the other half of the ``final`` locked test, whose whole-year RT maximum is
   $261.35 against that $300 threshold (0 tail hours, permanently).

2. THE ORDERING HAZARD, MEASURED.  neiso-90 flagged that
   ``scripts/data/derive_actual_tail.py`` withholds an out-of-training row
   pending the tier marker, so a ``final`` grant that does not re-run the
   deriver FIRST spends the touch-once year with C3c SKIPPED.  This probe
   establishes that the deriver is now correctly PRIMED: the 2026 data is
   present, the gate still refuses it at HEAD, and the row it WOULD emit under
   a ``final`` marker is computed here so the hazard is quantified rather than
   described.

   The counterfactual is evaluated against an IN-MEMORY marker document.
   Nothing is written to ``calibration-complete.json``, no marker is created,
   and no grant is implied -- this is arithmetic over a committed parquet, the
   same arithmetic the deriver would do, and it is reported precisely so the
   owner can see what a grant would unlock before granting it.

NO YEAR IS SOLVED, SCORED OR REGISTERED.  A tail COUNT over published actual
prices is not a model score: it is one side of the C3c comparison, the side
that is a property of the market. The model side is untouched.

Output: ``results/calibration/_neiso96_intake_and_tail_priming.json``.

Usage:
    uv run python scripts/probes/neiso96_intake_and_tail_priming.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.data import derive_actual_tail as dat  # noqa: E402
from scripts.lib import holdout_policy  # noqa: E402

ISO = "NEISO"
OUT = REPO / "results" / "calibration" / "_neiso96_intake_and_tail_priming.json"
SRC = REPO / "data" / "raw" / "_validation-source" / f"actual_lmp_hourly_{ISO}.parquet"
TAIL_JSON = REPO / "frontend" / "data" / "backcast" / "tail" / "actual_tail.json"


def intake_shape() -> dict:
    """Per-year shape of the committed NEISO hub actuals series."""
    thr = dat.TAIL_THRESHOLD[ISO]
    df = pd.read_parquet(SRC)
    out = {}
    for year, d in df.groupby(df["year"].astype(int)):
        rt = d["rt"].to_numpy(float)
        da = d["da"].to_numpy(float)
        out[str(year)] = {
            "rows": int(len(d)),
            "rt_coverage": round(float(np.mean(~np.isnan(rt))), 4),
            "da_coverage": round(float(np.mean(~np.isnan(da))), 4),
            "rt_mean": round(float(np.nanmean(rt)), 2),
            "rt_max": round(float(np.nanmax(rt)), 2),
            "rt_gt_threshold": int(np.nansum(rt > thr)),
            "da_gt_threshold": int(np.nansum(da > thr)),
        }
    return {"threshold": thr, "years": out}


def gate_state() -> dict:
    """The rule-22 tier gate's verdict for NEISO, per year, at HEAD."""
    marker = dat._marker_doc()
    df = pd.read_parquet(SRC)
    years = sorted(df["year"].astype(int).unique().tolist())
    rows = {}
    for y in years:
        tier = holdout_policy.tier_for_year(y)
        rows[str(y)] = {
            "tier": tier,
            "emittable_at_head": bool(dat._year_emittable(ISO, y, marker)),
        }
    return {
        "marker_final_block_present": bool(marker.get("final")),
        "marker_complete_has_neiso": ISO in (marker.get("complete") or {}),
        "years": rows,
    }


def counterfactual_2026() -> dict:
    """What the deriver WOULD emit for NEISO 2026 under a ``final`` marker.

    Computed with an in-memory marker only. The arithmetic is copied from
    :func:`derive_actual_tail.derive` so the number is the deriver's own, not a
    look-alike; the gate is exercised through the real
    :func:`derive_actual_tail._year_emittable` to confirm the synthetic marker
    is what flips it.
    """
    real = dat._marker_doc()
    hypothetical = dict(real)
    hypothetical["final"] = {
        **(real.get("final") or {}),
        ISO: {"note": "IN-MEMORY COUNTERFACTUAL ONLY -- no grant, nothing written"},
    }
    gated_now = dat._year_emittable(ISO, 2026, real)
    gated_then = dat._year_emittable(ISO, 2026, hypothetical)

    thr = dat.TAIL_THRESHOLD[ISO]
    d = pd.read_parquet(SRC)
    d = d[d["year"].astype(int) == 2026]
    rt = d["rt"].to_numpy(float)
    da = d["da"].to_numpy(float)
    return {
        "emittable_at_head": bool(gated_now),
        "emittable_under_final": bool(gated_then),
        "row_that_would_be_emitted": {
            "threshold": thr,
            "da_gt": int(np.nansum(da > thr)),
            "rt_gt": int(np.nansum(rt > thr)),
            "da_coverage": round(float(np.mean(~np.isnan(da))), 3),
            "rt_coverage": round(float(np.mean(~np.isnan(rt))), 3),
            "hours": int(len(d)),
        },
    }


def main() -> int:
    """Write the intake + priming record."""
    committed_tail = json.loads(TAIL_JSON.read_text())
    rec = {
        "note": (
            "NEISO H1-2026 actuals intake (neiso-96) and the C3c tail deriver's "
            "gate state. The 2026 row is PRESENT IN THE DATA and WITHHELD BY THE "
            "GATE at HEAD -- locked-test tier, `final` empty -- which is the "
            "correct behaviour and is what makes the neiso-90 ordering hazard "
            "now merely an ordering requirement rather than a data gap. The "
            "counterfactual row is computed against an in-memory marker; no "
            "marker file was written and NO GRANT IS IMPLIED. No year solved, "
            "scored or registered."
        ),
        "intake": intake_shape(),
        "gate": gate_state(),
        "counterfactual_2026": counterfactual_2026(),
        "committed_actual_tail_neiso_years": sorted(
            committed_tail["isos"].get(ISO, {}).keys()
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1) + "\n")

    t = rec["intake"]
    print(f"{ISO} hub actuals, threshold ${t['threshold']:.0f}/MWh")
    print(
        f"{'year':>6} {'rows':>6} {'rt_cov':>7} {'rt_mean':>9} {'rt_max':>10} "
        f"{'RT>thr':>7} {'emit@HEAD':>10}"
    )
    for y, r in t["years"].items():
        g = rec["gate"]["years"][y]
        print(
            f"{y:>6} {r['rows']:>6} {r['rt_coverage']:>7.4f} {r['rt_mean']:>9.2f} "
            f"{r['rt_max']:>10.2f} {r['rt_gt_threshold']:>7} "
            f"{str(g['emittable_at_head']):>10}"
        )
    c = rec["counterfactual_2026"]
    print(
        f"\n2026 gate: emittable at HEAD = {c['emittable_at_head']}, "
        f"under a `final` marker = {c['emittable_under_final']}"
    )
    print(f"  row it would emit: {c['row_that_would_be_emitted']}")
    print(f"committed actual_tail.json NEISO years: "
          f"{rec['committed_actual_tail_neiso_years']}")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
