"""ercot-188: measure the P0 delta the (c2) refinement causes — the REAL solve's P0.

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
actually moved*, not to argue it away.

**Why it re-solves P0 rather than reading the bundles.** A calibration bundle
persists only the **P1** dispatch frame and a P1-pass system frame, so the P0
run pattern the commitment channel actually reads is nowhere on disk. This probe
therefore replays each member through the SAME entry point the A/B used
(``run_calibration_full.solve_and_persist`` via ``replay_keeper``'s own kwargs
construction) with ``compute_monthly_markup`` **spied**: it captures the real
``r0.dispatch`` and the real markup array, then raises a sentinel to abort
BEFORE P1. What is measured is thus the A/B's own P0, not a reconstruction of
it. One P0 solve per member, one year (the object year).

Reported, per precommit §3:

* **P0 energy** — total and per class, plus the econ/committed split.
* **P0 run lengths on the ``committed`` rows** — starts, on-hours and mean run
  length. This is exactly what ``compute_monthly_markup(fleet, fleet_arrays,
  r0.dispatch, …)`` reads to set the P1 startup amortization.
* **The resulting P1 startup-markup delta on those rows** — MEMO §3.3 sized the
  exposure at 122 committed rows carrying 16.5 GW of gas CC/CT/ST, capacity
  sitting directly beneath the object hours' marginal rows.

Usage::

    python scripts/probes/ercot188_p0_delta.py --year 2023

Rule 22: every year is inside {2023, 2024, 2025}. Nothing is registered; the
probe writes into a scratch directory and deletes nothing in the A/B bundles.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# Same reproducibility pin replay_keeper sets, for the same reason: a P0 read
# must be basis-independent. Set BEFORE importing the solve core.
os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"

KEEPER = REPO / "results/calibration/ercot185_shapedarm_B"
FIELD = "ercot_econ_curve_top_refine"

#: A row is "on" in an hour when its dispatch clears this (MW). Dispatch dust
#: below it is LP noise, not a commitment decision.
ON_MW = 1e-6


class _StopAfterP0(Exception):
    """Sentinel raised inside the markup seam to abort before the P1 solve."""


def _run_stats(mw: np.ndarray) -> tuple[int, int]:
    """Return ``(starts, on_hours)`` for one row's hourly MW.

    A "start" is a 0 -> on transition — the same contiguous-block convention
    the commitment pass uses to discover run lengths.
    """
    on = mw > ON_MW
    if not on.any():
        return 0, 0
    starts = int(np.count_nonzero(on & ~np.concatenate(([False], on[:-1]))))
    return starts, int(on.sum())


def capture_p0(year: int, armed: bool) -> dict:
    """Solve ONE member's P0 for ``year`` and return its statistics.

    Spies ``pipeline.solve.compute_monthly_markup`` so the captured dispatch and
    markup are the ones the real A/B solve produced, then aborts before P1.
    """
    from scripts import run_calibration_full as rcf
    from scripts import replay_keeper as rk
    import market_sim.pipeline.solve as solve_mod

    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    if armed:
        kwargs.setdefault("prb_overrides", {})
        kwargs["prb_overrides"] = {**kwargs["prb_overrides"], FIELD: True}

    cap: dict = {}
    orig = solve_mod.compute_monthly_markup

    def _spy(fleet, fleet_arrays, dispatch, hours, **kw):
        markup = orig(fleet, fleet_arrays, dispatch, hours, **kw)
        cap["unit_ids"] = [str(g.unit_id) for g in fleet]
        cap["dispatch"] = np.array(dispatch, copy=True)
        cap["markup"] = np.array(markup, copy=True)
        cap["pmax"] = np.array([float(g.pmax_mw or 0.0) for g in fleet], dtype=float)
        raise _StopAfterP0()

    solve_mod.compute_monthly_markup = _spy
    try:
        with tempfile.TemporaryDirectory() as td:
            kwargs["out_dir"] = Path(td) / "p0probe"
            try:
                rcf.solve_and_persist(**kwargs)
            except _StopAfterP0:
                pass
    finally:
        solve_mod.compute_monthly_markup = orig

    if "dispatch" not in cap:
        raise SystemExit("P0 capture failed — the markup seam was never reached")

    uids = cap["unit_ids"]
    disp = cap["dispatch"]
    markup = cap["markup"]
    pmax = cap["pmax"]
    sfx = np.array([u.rpartition("_")[2] for u in uids])
    is_cmt = np.char.startswith(sfx, "committed")
    is_econ = np.char.startswith(sfx, "econc")

    cmt_idx = np.flatnonzero(is_cmt)
    per_row = {}
    for i in cmt_idx:
        s, h = _run_stats(disp[i])
        per_row[uids[i]] = (s, h, float(markup[i].mean()), float(pmax[i]))

    return {
        "n_gen": int(disp.shape[0]),
        "p0_total_twh": float(disp.sum() / 1e6),
        "p0_econ_twh": float(disp[is_econ].sum() / 1e6),
        "p0_committed_twh": float(disp[is_cmt].sum() / 1e6),
        "committed_rows": int(is_cmt.sum()),
        "committed_capacity_mw": float(pmax[is_cmt].sum()),
        "committed_total_starts": int(sum(v[0] for v in per_row.values())),
        "committed_on_hours": int(sum(v[1] for v in per_row.values())),
        "markup_committed_mean": float(markup[is_cmt].mean()),
        "markup_committed_capwtd_mean": float(
            (markup[is_cmt].mean(axis=1) * pmax[is_cmt]).sum()
            / max(1e-9, pmax[is_cmt].sum())
        ),
        "_per_row": per_row,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--year", type=int, default=2023, choices=(2023, 2024, 2025))
    ap.add_argument(
        "--out", type=Path, default=REPO / "results/calibration/ercot188_p0_delta.json"
    )
    args = ap.parse_args()

    print(f"capturing CONTROL P0 ({args.year}) ...")
    base = capture_p0(args.year, armed=False)
    print(f"  n_gen={base['n_gen']} P0 {base['p0_total_twh']:.3f} TWh")
    print(f"capturing ARM P0 ({args.year}) ...")
    arm = capture_p0(args.year, armed=True)
    print(f"  n_gen={arm['n_gen']} P0 {arm['p0_total_twh']:.3f} TWh")

    shared = sorted(set(base["_per_row"]) & set(arm["_per_row"]))
    d_starts = np.array(
        [arm["_per_row"][u][0] - base["_per_row"][u][0] for u in shared]
    )
    d_on = np.array([arm["_per_row"][u][1] - base["_per_row"][u][1] for u in shared])
    d_mk = np.array([arm["_per_row"][u][2] - base["_per_row"][u][2] for u in shared])
    caps = np.array([base["_per_row"][u][3] for u in shared])
    moved = int(np.count_nonzero((d_starts != 0) | (d_on != 0)))

    rec = {
        "year": args.year,
        "what_this_measures": (
            "The P0 motion the (c2) row-count change causes BY CONSTRUCTION. "
            "The offer-surface family's P1-only mc_bid_adjust seam does not "
            "apply here and its P0 bit-identity proof is FORFEITED "
            "(precommit §3 / MEMO-ercot184 §3.3); this is the honest statement "
            "of what moved, not a defence."
        ),
        "control": {k: v for k, v in base.items() if not k.startswith("_")},
        "arm": {k: v for k, v in arm.items() if not k.startswith("_")},
        "delta": {
            "n_gen": arm["n_gen"] - base["n_gen"],
            "p0_total_twh": arm["p0_total_twh"] - base["p0_total_twh"],
            "p0_econ_twh": arm["p0_econ_twh"] - base["p0_econ_twh"],
            "p0_committed_twh": arm["p0_committed_twh"] - base["p0_committed_twh"],
            "committed_starts": (
                arm["committed_total_starts"] - base["committed_total_starts"]
            ),
            "committed_on_hours": (
                arm["committed_on_hours"] - base["committed_on_hours"]
            ),
            "markup_committed_capwtd_mean": (
                arm["markup_committed_capwtd_mean"]
                - base["markup_committed_capwtd_mean"]
            ),
        },
        "commitment_channel": {
            "committed_rows_shared": len(shared),
            "rows_with_moved_commitment": moved,
            "share_rows_moved": moved / max(1, len(shared)),
            "capacity_mw_with_moved_commitment": float(
                caps[(d_starts != 0) | (d_on != 0)].sum()
            ),
            "max_abs_row_start_delta": int(
                np.abs(d_starts).max() if len(d_starts) else 0
            ),
            "max_abs_row_on_hour_delta": int(np.abs(d_on).max() if len(d_on) else 0),
            "max_abs_row_markup_delta_usd_mwh": float(
                np.abs(d_mk).max() if len(d_mk) else 0.0
            ),
            "capwtd_mean_abs_markup_delta_usd_mwh": float(
                (np.abs(d_mk) * caps).sum() / max(1e-9, caps.sum())
            ),
        },
    }
    args.out.write_text(json.dumps(rec, indent=1))
    d = rec["delta"]
    c = rec["commitment_channel"]
    print(
        f"\nP0 total {d['p0_total_twh']:+.4f} TWh | committed "
        f"{d['p0_committed_twh']:+.4f} TWh | starts {d['committed_starts']:+d} | "
        f"commitment moved on {c['rows_with_moved_commitment']}/"
        f"{c['committed_rows_shared']} rows "
        f"({c['capacity_mw_with_moved_commitment']:.0f} MW) | markup capwtd "
        f"{d['markup_committed_capwtd_mean']:+.4f} $/MWh"
    )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
