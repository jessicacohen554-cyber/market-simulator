#!/usr/bin/env python3
"""nyiso-146 K2 — predict the arm's floor and start counts BEFORE it solves.

The pre-registered liveness prediction for the per-plant min-run A/B
(``PREREG-nyiso146-perplant-min-run-2026-08-19.md`` gate K2). The bridge floor
is a DETERMINISTIC function of the base-cost P0 pattern and the config, and P0
is config-invariant across the two arms (the bridge is injected at the P0->P1
seam; nothing upstream of it differs), so the ARM's floor can be computed
EXACTLY from a CONTROL-side capture, before the arm ever solves:

* replay the keeper recipe per year (zero config delta — the nyiso-145
  instrumentation pattern: no bundle, no metrics, nothing registrable);
* spy on ``pipeline.commitment._nyiso_gas_bridge_floor`` to capture its
  inputs, let the CONTROL floor through unchanged, and ALSO call the same
  function on the same inputs with ``nyiso_gas_bridge_plant_min_run=True`` —
  the arm's floor, computed but NEVER injected (the replayed solve stays the
  control);
* report, per plant: control vs arm floor volume (exact), and the predicted
  plant-level P1 start count under each floor — the maximal blocks of
  ``(sum_rows P0 + sum_rows floor) > 0.05 x plant capacity``, the same
  0.05 x npl threshold the nyiso-145 object is measured on. The floor half of
  the prediction is exact; the start half carries a band because P1 re-runs
  the LP economics above the floor.

DIAGNOSTIC PROBE ONLY; years 2023-2025 (rule 22; freeze ACTIVE).

Usage::

    python scripts/probes/_nyiso146_k2_prediction.py [--year 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from scripts.legitimacy_diagnostics import REBUILD_META_RENAMES  # noqa: E402
import scripts.run_calibration as RC  # noqa: E402
import market_sim.pipeline.commitment as PC  # noqa: E402

BUNDLE = REPO / "results/calibration/nyiso144_layup_arm"
OUT = REPO / "results/calibration/_nyiso146_k2_prediction.json"
RUN_THRESHOLD_FRAC = 0.05

# The plants K2/K3 name: the two over-cycling objects and the currently-fine
# cohort (nyiso-145 / handoff), plus every plant whose identified per-plant
# value differs materially from its class scalar.
WATCH = (2539, 7314, 56234, 56940, 2500, 55405, 57185, 50292, 56196, 2517, 2511)


def _kwargs(meta: dict) -> dict:
    """Return the ``run_year`` kwargs that reproduce *meta*'s recipe."""
    params = inspect.signature(RC.run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    out = {}
    for k, v in meta.items():
        k2 = REBUILD_META_RENAMES.get(k, k)
        if k2 in params and k2 not in skip:
            out[k2] = v
    return out


def _runs(flag: np.ndarray) -> list[tuple[int, int]]:
    """Return the ``[start, end)`` index pairs of each True run in *flag*."""
    idx = np.flatnonzero(np.diff(np.concatenate(([0], flag.astype(np.int8), [0]))) != 0)
    return list(zip(idx[0::2], idx[1::2]))


def _capture(year: int, meta: dict) -> dict:
    """Solve *year* on the keeper recipe; capture control AND arm floors."""
    cap: dict = {}
    orig = PC._nyiso_gas_bridge_floor

    def _spy(config, fleet, fleet_arrays, p0_dispatch, p0_prices, mc_base):
        out = orig(config, fleet, fleet_arrays, p0_dispatch, p0_prices, mc_base)
        arm_cfg = config.with_overrides(nyiso_gas_bridge_plant_min_run=True)
        arm = orig(arm_cfg, fleet, fleet_arrays, p0_dispatch, p0_prices, mc_base)
        cap["p0"] = np.array(p0_dispatch, copy=True)
        z = np.zeros_like(cap["p0"])
        cap["floor_ctl"] = z if out is None else np.array(out, copy=True)
        cap["floor_arm"] = z if arm is None else np.array(arm, copy=True)
        cap["pmax"] = np.array(fleet_arrays.pmax, copy=True)
        cap["plant"] = np.array(
            [int(getattr(g, "plant_code", 0) or 0) for g in fleet], dtype=int
        )
        cap["klass"] = np.array(
            [str(getattr(g, "plant_group", "")) for g in fleet], dtype=object
        )
        return out  # the replayed solve stays the CONTROL

    PC._nyiso_gas_bridge_floor = _spy
    try:
        gas = meta["gas_prices"]
        RC.run_year(
            year,
            "NYISO",
            int(meta.get("hours", 8760)),
            float(gas[str(year)]),
            {},
            **_kwargs(meta),
        )
    finally:
        PC._nyiso_gas_bridge_floor = orig
    if "p0" not in cap:
        raise RuntimeError(
            f"{year}: the NYISO gas bridge never ran — the recipe did not arm it"
        )
    return cap


def _predict(cap: dict) -> list[dict]:
    """Per watched plant: exact floor volumes and predicted start counts."""
    p0, pmax = cap["p0"], cap["pmax"]
    plant, klass = cap["plant"], cap["klass"]
    rows = []
    for pc in WATCH:
        idxs = [
            i
            for i in range(p0.shape[0])
            if plant[i] == pc and klass[i] in ("CC_REGULAR", "ST_GAS")
        ]
        if not idxs:
            continue
        cap_mw = float(sum(pmax[i] for i in idxs))
        p0_sum = np.sum([p0[i] for i in idxs], axis=0)
        row = {
            "plant": pc,
            "plant_class": str(klass[idxs[0]]),
            "lp_capacity_mw": round(cap_mw, 1),
        }
        for tag in ("ctl", "arm"):
            fl = np.sum([cap[f"floor_{tag}"][i] for i in idxs], axis=0)
            on = (p0_sum + fl) > RUN_THRESHOLD_FRAC * cap_mw
            row[f"floor_{tag}_gwh"] = round(float(fl.sum()) / 1e3, 2)
            row[f"pred_starts_{tag}"] = len(_runs(on))
            row[f"pred_on_share_{tag}"] = round(float(on.mean()), 4)
        rows.append(row)
    return rows


def main() -> int:
    """Run the per-year control-side captures and write the K2 record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    meta = json.loads((BUNDLE / "meta.json").read_text())
    out: dict = {
        "probe": "_nyiso146_k2_prediction",
        "bundle": BUNDLE.name,
        "run_threshold_frac": RUN_THRESHOLD_FRAC,
        "note": (
            "floor_arm_gwh is EXACT (the floor is a deterministic function of "
            "the config-invariant P0 pattern); pred_starts_* is the block "
            "count of (P0 + floor) > 0.05 x plant capacity and carries the "
            "pre-registered band (P1 re-runs the economics above the floor)"
        ),
        "years": {},
    }
    for year in args.year:
        if year not in (2023, 2024, 2025):
            raise SystemExit(
                f"year {year} is outside the 2023-2025 training window "
                "(CLAUDE.md rule 22; the holdout spend freeze is ACTIVE)"
            )
        rows = _predict(_capture(year, meta))
        out["years"][str(year)] = rows
        print(f"=== {year}")
        hdr = ("plant", "class", "cap", "flrC", "flrA", "startsC", "startsA",
               "onC", "onA")
        print("{:>7s} {:11s} {:>7s} {:>8s} {:>8s} {:>8s} {:>8s} {:>7s} {:>7s}".format(*hdr))
        for r in rows:
            print(
                f"{r['plant']:7d} {r['plant_class']:11s} "
                f"{r['lp_capacity_mw']:7.1f} {r['floor_ctl_gwh']:8.2f} "
                f"{r['floor_arm_gwh']:8.2f} {r['pred_starts_ctl']:8d} "
                f"{r['pred_starts_arm']:8d} {r['pred_on_share_ctl']:7.4f} "
                f"{r['pred_on_share_arm']:7.4f}"
            )
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
