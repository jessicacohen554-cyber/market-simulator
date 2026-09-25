"""COAL-SUB: zero-LP fleet snapshot of one ISO-year under its designated keeper's recipe.

Owner instruction 2026-09-25 (verbatim): *"we need to completely eliminate the
class Coal From the model altogether all coal should be sorted into its
subclass"*. This probe is the evidence instrument for that change, and it does
two jobs from ONE rebuild:

1. **Census.** Every coal generator the keeper recipe builds for the year, with
   its plant code, nameplate, dispatch ``plant_group`` and the subclass the
   repo's own resolver (:func:`market_sim.data.coal.coal_supply_class`) gives it
   — so the MW that resolves to NO subclass (the former generic ``COAL``
   bucket) is measured, not asserted.
2. **Byte-identity baseline.** Every per-generator array of the assembled
   ``FleetArrays`` plus the assembled P0 offer (``mc_base``), written to an
   ``.npz`` (2-D arrays as one SHA-1 per generator row), so a rebuild AFTER the
   change can be compared row by row with :mod:`coal_subclass_compare`.

No LP is solved: the fleet is rebuilt through the sanctioned
``run_year(..., fleet_only=True)`` reconstruction
(:func:`scripts.lib.bundle_fleet.full_run_year_kwargs`), with the bundle's
per-year recipe overlay (``config_partition_overrides``) routed exactly as
``replay_keeper`` routes it. Run one interpreter per ISO-year (fleet loaders
are ``lru_cache``d).

Usage::

    python scripts/probes/coal_subclass_snapshot.py --iso SPP --year 2023 \
        --out <dir>
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import inspect
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def keeper_bundle(iso: str) -> Path:
    """Return the committed bundle dir of ``iso``'s designated keeper."""
    keeper = json.loads(
        (REPO / "frontend/data/backcast/keepers" / f"{iso}.json").read_text()
    )["keeper"]
    reg = json.loads(
        (REPO / "frontend/data/backcast/registry" / f"{keeper}.json").read_text()
    )
    return REPO / reg["bundle"]


def _row_hashes(arr: np.ndarray) -> np.ndarray:
    """One SHA-1 hex digest per leading-axis row of a 2-D array."""
    a = np.ascontiguousarray(arr)
    return np.array([hashlib.sha1(a[i].tobytes()).hexdigest() for i in range(a.shape[0])])


def rebuild(iso: str, year: int, sets: dict | None = None) -> dict:
    """Rebuild ``iso``/``year`` under its keeper recipe, no LP.

    ``sets`` overrides recipe keys (``ScenarioConfig`` fields / ``run_year``
    kwargs), applied identically to the BEFORE and AFTER rebuilds — used only
    to switch off an input whose gitignored corpus is absent from the
    container (PJM ``pjm_da_virtual_bids``: its pseudo-units are appended
    virtual-bid rungs, never coal rows, so the coal comparison is unaffected).
    """
    from scripts.lib.bundle_fleet import (
        bundle_gas_price,
        full_run_year_kwargs,
    )
    from scripts.replay_keeper import config_partition_overlay, derived_run_year_inputs
    from scripts.run_calibration import run_year
    from market_sim.config.scenarios import ScenarioConfig

    bundle = keeper_bundle(iso)
    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    overlay = config_partition_overlay(meta, year)
    overlay = {**overlay, **(sets or {})}
    if overlay:
        params = set(inspect.signature(run_year).parameters)
        fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
        kwargs["prb_overrides"] = dict(kwargs.get("prb_overrides") or {})
        for k, v in overlay.items():
            if k in params:
                kwargs[k] = v
            if k in fields:
                kwargs["prb_overrides"][k] = v
    try:
        derived = derived_run_year_inputs(bundle, year)
    except Exception:  # noqa: BLE001 — a non-keeper census year has no sidecar
        derived = {}
    return run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year),
        **kwargs, **derived,
    )


def main() -> None:
    """Rebuild one ISO-year and write the census JSON + identity npz."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument(
        "--register-supply",
        type=Path,
        help="JSON {plant_code: supply_class} registered through "
        "data.coal.register_partial_exit_coal_supply BEFORE the rebuild — the "
        "COUNTERFACTUAL that hands the pre-COAL-SUB code the generic-bucket "
        "plants' post-change ranks, isolating their resolution as the only "
        "difference",
    )
    ap.add_argument(
        "--set",
        action="append",
        default=[],
        help="KEY=JSON recipe override, applied to both BEFORE and AFTER",
    )
    a = ap.parse_args()
    sets = {k: json.loads(v) for k, v in (x.split("=", 1) for x in a.set)}
    a.out.mkdir(parents=True, exist_ok=True)

    from market_sim.data.coal import coal_supply_class
    from market_sim.config.plant_taxonomy import COAL_SUPPLY_TO_CLASS

    if a.register_supply:
        from market_sim.data.coal import register_partial_exit_coal_supply

        register_partial_exit_coal_supply(
            {int(k): v for k, v in json.loads(a.register_supply.read_text()).items()}
        )
    state = rebuild(a.iso, a.year, sets)
    fa = state["fleet_arrays"]
    n = len(fa.unit_ids)

    arrays: dict[str, np.ndarray] = {"unit_ids": np.array(fa.unit_ids, dtype=str)}
    for f in dataclasses.fields(fa):
        v = getattr(fa, f.name)
        if not isinstance(v, np.ndarray) or v.ndim == 0 or v.shape[0] != n:
            continue
        if v.dtype == object:
            v = v.astype(str)
        arrays[f.name] = _row_hashes(v) if v.ndim >= 2 else v
    mc = state.get("mc_base")
    if isinstance(mc, np.ndarray) and mc.ndim and mc.shape[0] == n:
        arrays["mc_base"] = _row_hashes(mc) if mc.ndim >= 2 else mc
    np.savez_compressed(a.out / f"{a.iso}_{a.year}.npz", **arrays)

    gens = state["fleet"].generators if hasattr(state["fleet"], "generators") else state["fleet"]
    coal = []
    for g in gens:
        if str(getattr(g, "fuel_type", "")) != "coal":
            continue
        pc = int(getattr(g, "plant_code", 0) or 0)
        sup = coal_supply_class(pc) if pc else ""
        coal.append(
            {
                "unit_id": g.unit_id,
                "plant_code": pc,
                "name": g.name,
                "pmax_mw": float(g.pmax_mw),
                "plant_group": str(g.plant_group),
                "coal_supply": str(getattr(g, "coal_supply", "")),
                "resolved_supply": sup,
                "resolved_subclass": COAL_SUPPLY_TO_CLASS.get(sup, ""),
            }
        )
    cfg = state["config"]
    (a.out / f"{a.iso}_{a.year}.json").write_text(
        json.dumps(
            {
                "iso": a.iso,
                "year": a.year,
                "n_gen": n,
                "offer_curve_by_group": getattr(cfg, "offer_curve_by_group", None),
                "coal_units": coal,
            },
            indent=1,
            default=str,
        )
    )
    print(a.iso, a.year, n, "gens", len(coal), "coal rows")


if __name__ == "__main__":
    main()
