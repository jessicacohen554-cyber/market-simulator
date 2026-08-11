"""ercot-188: measure the P0 delta the (c2) refinement causes — read-only, no LP.

**Precommit §3 makes this measurement MANDATORY, not optional.** Every ERCOT
offer-surface mechanism since ERCOT-86 is applied at the ``mc_bid_adjust`` seam
(``pipeline/solve.py``): P0 solves on ``mc_base``, P1 on
``mc_base + startup_markup + mc_bid_adjust``. That seam is what lets each arm be
*proved* not to disturb commitment — the family's whole verification story rests
on P0 being bit-identical.

``_econ_curve_steps`` writes heat rates into the **base** fleet, so its output is
inside ``mc_base``, which **is** the P0 objective. A slicing change therefore
moves P0 **by construction** and the seam does not apply: the offer-surface
family's P0 bit-identity proof is **FORFEITED**, permanently, and every
control-vs-arm difference is confounded with commitment-side motion. That cost
was costed (MEMO-ercot184 §3.3) and accepted by the owner as the price of the
structural fidelity — so this probe exists to state at full magnitude *what
actually moved*, rather than to argue it away.

Two channels are reported separately:

1. **P0 dispatch** — total and per-class energy, from each bundle's own
   ``dispatch/<year>_P0.parquet``.
2. **The commitment channel** — P0 run lengths on the ``committed`` rows, which
   is exactly what ``compute_monthly_markup(fleet, fleet_arrays, r0.dispatch,
   …)`` reads to set the P1 startup amortization. MEMO §3.3 sized this at 122
   committed rows carrying 16.5 GW of gas CC/CT/ST whose P1 bid is set by P0 run
   lengths — capacity sitting directly beneath the object hours' marginal rows.

Usage::

    python scripts/probes/ercot188_p0_delta.py \
        --base results/calibration/ercot188_topfine_ctl_A \
        --arm  results/calibration/ercot188_topfine_arm_B

Rule 22: every year is inside {2023, 2024, 2025}. No LP is solved.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)

#: A row is "on" in an hour when its dispatch clears this (MW). Dispatch dust
#: below it is LP noise, not a commitment decision.
ON_MW = 1e-6


def _suffix(unit_id: str) -> str:
    return str(unit_id).rpartition("_")[2]


def _run_stats(mw: np.ndarray) -> tuple[int, float, int]:
    """Return ``(starts, mean_run_hours, on_hours)`` for one row's hourly MW.

    A "start" is a 0 -> on transition, counted on the same contiguous-block
    convention the commitment pass uses to discover run lengths.
    """
    on = mw > ON_MW
    if not on.any():
        return 0, 0.0, 0
    starts = int(np.count_nonzero(on & ~np.concatenate(([False], on[:-1]))))
    on_h = int(on.sum())
    return starts, (on_h / starts if starts else 0.0), on_h


def _year_stats(bundle: Path, year: int) -> dict | None:
    """Return one bundle-year's P0 dispatch and commitment-channel statistics."""
    path = bundle / "dispatch" / f"{year}_P0.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["unit_id", "klass", "hour", "mw"])
    df["mw"] = df["mw"].astype(float)

    by_class = df.groupby("klass")["mw"].sum().div(1e6)  # MWh -> TWh
    sfx = df["unit_id"].map(_suffix)
    is_cmt = sfx.str.startswith("committed")
    is_econ = sfx.str.startswith("econc")

    cmt = df[is_cmt]
    rows: list[tuple[str, int, float, int]] = []
    for uid, g in cmt.groupby("unit_id", sort=True):
        mw = g.sort_values("hour")["mw"].to_numpy(dtype=float)
        s, r, h = _run_stats(mw)
        rows.append((str(uid), s, r, h))
    starts = np.array([r[1] for r in rows], dtype=float)
    runs = np.array([r[2] for r in rows], dtype=float)

    return {
        "p0_total_twh": float(df["mw"].sum() / 1e6),
        "p0_twh_by_class": {str(k): float(v) for k, v in by_class.items()},
        "p0_econ_twh": float(df.loc[is_econ, "mw"].sum() / 1e6),
        "p0_committed_twh": float(cmt["mw"].sum() / 1e6),
        "committed_rows": len(rows),
        "committed_total_starts": int(starts.sum()),
        "committed_mean_run_h": float(np.nanmean(runs)) if len(runs) else 0.0,
        "committed_on_hours": int(sum(r[3] for r in rows)),
        "_per_row": {r[0]: (r[1], r[2], r[3]) for r in rows},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument(
        "--out", type=Path, default=REPO / "results/calibration/ercot188_p0_delta.json"
    )
    args = ap.parse_args()

    rec: dict = {
        "base": str(args.base),
        "arm": str(args.arm),
        "what_this_measures": (
            "The P0 motion the (c2) row-count change causes BY CONSTRUCTION. "
            "The offer-surface family's P1-only mc_bid_adjust seam does not "
            "apply here and its P0 bit-identity proof is FORFEITED "
            "(precommit §3 / MEMO-ercot184 §3.3); this is the honest statement "
            "of what moved, not a defence."
        ),
        "years": {},
    }
    for year in YEARS:
        b = _year_stats(args.base, year)
        a = _year_stats(args.arm, year)
        if b is None or a is None:
            rec["years"][str(year)] = {"skipped": "no P0 dispatch parquet"}
            continue
        shared = sorted(set(b["_per_row"]) & set(a["_per_row"]))
        d_starts = [a["_per_row"][u][0] - b["_per_row"][u][0] for u in shared]
        d_on = [a["_per_row"][u][2] - b["_per_row"][u][2] for u in shared]
        moved = int(sum(1 for x, y in zip(d_starts, d_on) if x or y))
        classes = sorted(set(b["p0_twh_by_class"]) | set(a["p0_twh_by_class"]))
        rec["years"][str(year)] = {
            "p0_total_twh_base": b["p0_total_twh"],
            "p0_total_twh_arm": a["p0_total_twh"],
            "p0_total_twh_delta": a["p0_total_twh"] - b["p0_total_twh"],
            "p0_econ_twh_delta": a["p0_econ_twh"] - b["p0_econ_twh"],
            "p0_committed_twh_base": b["p0_committed_twh"],
            "p0_committed_twh_arm": a["p0_committed_twh"],
            "p0_committed_twh_delta": a["p0_committed_twh"] - b["p0_committed_twh"],
            "p0_twh_delta_by_class": {
                c: a["p0_twh_by_class"].get(c, 0.0) - b["p0_twh_by_class"].get(c, 0.0)
                for c in classes
            },
            "committed_rows_base": b["committed_rows"],
            "committed_rows_arm": a["committed_rows"],
            "committed_rows_shared": len(shared),
            "committed_rows_with_moved_commitment": moved,
            "committed_starts_base": b["committed_total_starts"],
            "committed_starts_arm": a["committed_total_starts"],
            "committed_starts_delta": (
                a["committed_total_starts"] - b["committed_total_starts"]
            ),
            "committed_mean_run_h_base": b["committed_mean_run_h"],
            "committed_mean_run_h_arm": a["committed_mean_run_h"],
            "committed_on_hours_delta": (
                a["committed_on_hours"] - b["committed_on_hours"]
            ),
            "max_abs_row_start_delta": int(max([abs(x) for x in d_starts] or [0])),
            "max_abs_row_on_hour_delta": int(max([abs(x) for x in d_on] or [0])),
        }
        y = rec["years"][str(year)]
        print(
            f"  {year}: P0 total {y['p0_total_twh_base']:.3f} -> "
            f"{y['p0_total_twh_arm']:.3f} TWh "
            f"({y['p0_total_twh_delta']:+.4f}); committed run-lengths moved on "
            f"{moved}/{len(shared)} rows, starts "
            f"{y['committed_starts_delta']:+d}"
        )
    args.out.write_text(json.dumps(rec, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
