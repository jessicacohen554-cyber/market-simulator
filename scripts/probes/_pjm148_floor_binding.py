"""pjm-148 no-LP screen, Q1 — does PJM's CC_CHP host-steam floor actually BIND?

Pre-registration (committed and pushed before this ran):
``results/calibration/PREREG-pjm148-chp-host-steam-holdout-2026-08-03.md`` §3.

Q1 asks whether the ``chp_steam`` floor (``chp_grid_pmin_mw``, built into
``FleetArrays.min_gen`` and tagged ``MECH_CHP_STEAM``) is a *binding*
constraint on PJM's CC_CHP, because the named successor lane proposes to move
its **level**. A floor that never binds cannot be relaxed to release energy --
lowering it is a no-op -- and raising it is wrong-signed against a class that
already runs over its measured actual (prereg §2).

Two independent limbs, both pre-registered:

* **(a)** the committed D-2 ``chp_steam`` forced share for CC_CHP, read from the
  bundle's own ``legitimacy_diagnostics.json`` (no reconstruction).
* **(b)** an independent hourly reconstruction: the class's summed grid-facing
  floor per hour from ``fa.min_gen`` restricted to CC_CHP, against the P1 class
  dispatch in ``hourly/class_hourly_<year>.parquet``.

DEAD rule, fixed in the prereg and never moved: (a) < 1 % **and** (b) < 5 % in
every year => the floor is inert => "lowering an inert floor is a no-op".

Nothing here is tuned and no LP is solved.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm148_floor_binding.py \
        --bundle results/calibration/pjm147_chp_B \
        --years 2023 2024 2025 \
        --json-out results/calibration/_pjm148_floor_binding.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

#: Prereg §3 Q1 thresholds. Never moved to chase a result.
D2_SHARE_MAX = 0.01  # limb (a): committed D-2 forced share
HOURLY_BIND_MAX = 0.05  # limb (b): share of class-hours at the floor
BIND_TOL = 0.01  # "at the floor" = dispatch <= (1 + tol) x floor

TARGET_CLASS = "CC_CHP"


def _sys_path() -> None:
    """Put ``scripts/`` and ``scripts/data/`` on the path (bundle_fleet's rule)."""
    import sys

    for p in (REPO, REPO / "scripts", REPO / "scripts" / "data"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def _limb_a(bundle: Path, year: int) -> dict:
    """Committed D-2 ``chp_steam`` forced share for the target class."""
    diag = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    rows = diag["diagnostics"]["D2"]["rows"]
    hit = [
        r
        for r in rows
        if int(r["year"]) == year
        and r["class"] == TARGET_CLASS
        and r["mechanism"] == "chp_steam"
    ]
    any_row = [r for r in rows if int(r["year"]) == year and r["class"] == TARGET_CLASS]
    return {
        "d2_chp_steam_row_present": bool(hit),
        "d2_chp_steam_forced_twh": float(hit[0]["forced_twh"]) if hit else 0.0,
        "d2_chp_steam_share_of_class": float(hit[0]["share_of_class"]) if hit else 0.0,
        "d2_any_mechanism_rows_for_class": [r["mechanism"] for r in any_row],
    }


def _limb_b(bundle: Path, year: int) -> dict:
    """Independent hourly reconstruction of the class floor vs its dispatch."""
    from market_sim.data.floor_mechanisms import MECH_CHP_STEAM
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _meta = reconstruct_bundle_fleet(bundle, year)
    fleet = state["fleet"]
    fa = state["fleet_arrays"]
    groups = np.array([str(g.plant_group) for g in fleet])
    sel = groups == TARGET_CLASS

    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[(ch["klass"] == TARGET_CLASS) & (ch["pass"] == "P1")].sort_values("hour")
    disp = ch["mw"].to_numpy(dtype=float)
    hours = disp.size

    min_gen = getattr(fa, "min_gen", None)
    if min_gen is None:
        floor_t = np.zeros(hours, dtype=float)
        chp_floor_t = np.zeros(hours, dtype=float)
    else:
        mg = np.asarray(min_gen, dtype=float)[sel, :hours]
        floor_t = mg.sum(axis=0)
        mech = getattr(fa, "min_gen_mechanism", None)
        if mech is None:
            chp_floor_t = floor_t.copy()
        else:
            mm = np.asarray(mech)[sel, :hours]
            chp_floor_t = np.where(mm == MECH_CHP_STEAM, mg, 0.0).sum(axis=0)

    # "At the floor" = dispatch within tol of the summed floor, floor > 0.
    live = chp_floor_t > 0.0
    at_floor = live & (disp <= (1.0 + BIND_TOL) * chp_floor_t)

    return {
        "hours": int(hours),
        "class_twh": float(disp.sum() / 1e6),
        "chp_steam_floor_mw_mean": float(chp_floor_t.mean()),
        "chp_steam_floor_mw_max": float(chp_floor_t.max()),
        "chp_steam_floor_energy_twh_if_always_binding": float(chp_floor_t.sum() / 1e6),
        "hours_with_live_floor": int(live.sum()),
        "hours_at_floor": int(at_floor.sum()),
        "share_hours_at_floor": float(at_floor.sum() / hours) if hours else 0.0,
        "share_energy_at_floor": float(disp[at_floor].sum() / disp.sum())
        if disp.sum() > 0
        else 0.0,
        "mean_dispatch_over_floor_ratio": float(
            np.mean(disp[live] / chp_floor_t[live])
        )
        if live.any()
        else float("nan"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/pjm147_chp_B")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    _sys_path()
    bundle = Path(args.bundle)
    out: dict = {"bundle": str(bundle), "class": TARGET_CLASS, "by_year": {}}

    for year in args.years:
        a = _limb_a(bundle, year)
        b = _limb_b(bundle, year)
        dead_a = a["d2_chp_steam_share_of_class"] < D2_SHARE_MAX
        dead_b = b["share_hours_at_floor"] < HOURLY_BIND_MAX
        out["by_year"][str(year)] = {
            "limb_a_committed_d2": a,
            "limb_b_hourly_reconstruction": b,
            "limb_a_below_threshold": bool(dead_a),
            "limb_b_below_threshold": bool(dead_b),
        }
        print(
            f"{year}: D-2 chp_steam share={a['d2_chp_steam_share_of_class']:.5f} "
            f"(row present={a['d2_chp_steam_row_present']}) | "
            f"floor mean={b['chp_steam_floor_mw_mean']:.1f} MW "
            f"max={b['chp_steam_floor_mw_max']:.1f} MW | "
            f"hours at floor={b['share_hours_at_floor']:.5f} "
            f"({b['hours_at_floor']}/{b['hours']}) | "
            f"mean disp/floor={b['mean_dispatch_over_floor_ratio']:.3f}"
        )

    all_dead = all(
        v["limb_a_below_threshold"] and v["limb_b_below_threshold"]
        for v in out["by_year"].values()
    )
    out["Q1_verdict"] = (
        "DEAD — floor is inert; lowering it is a no-op"
        if all_dead
        else "SURVIVES — floor binds materially"
    )
    print(f"\nQ1: {out['Q1_verdict']}")

    if args.json_out:
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2, default=str))
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
