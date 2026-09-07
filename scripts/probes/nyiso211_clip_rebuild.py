"""nyiso-211 POST-HOC phase 0 — the ``unit_outage_per_unit_clip`` footprint on
the CURRENT NYISO keeper's own recipe, measured on the LP's availability array.

Zero-LP, and **arms nothing**. ``scripts/probes/nyiso211_clip_phase0.py`` sized
the flag through one loader (``unit_outage_derate_factors``); the flag actually
threads into four (``unit_outage_derate_factors``,
``unit_outage_short_derate_factors``, ``unit_partial_outage_derate_factors`` and
``unit_layup_removed_fractions``), so a one-channel census under-covers it. This
probe closes that gap the direct way: two on-recipe ``fleet_only`` rebuilds of
the keeper ``2026-09-06-nyiso-202-startup-aware`` — flag OFF (the keeper) and
flag ON — and a diff of the assembled ``FleetArrays.availability``, which is
every channel at once.

**POST-HOC.** Not among the predictions declared in
``results/calibration/PREREG-nyiso211-cricket-valley-lineage-attribution.md``;
decides no pre-registered verdict; proposes no arm and moves no default.

Run::

    uv run python scripts/probes/nyiso211_clip_rebuild.py
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))

from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)

KEEPER_ID = "2026-09-06-nyiso-202-startup-aware"
BUNDLE = ROOT / "results/calibration/nyiso202_startup_aware"
FLAG = "unit_outage_per_unit_clip"
YEARS = (2023, 2024, 2025)
T = 8760
CACHE = ROOT / ".cache/nyiso211"


def rebuild(year: int, arm: bool) -> dict:
    """On-recipe ``run_year(fleet_only=True)`` rebuild, cached as slim arrays."""
    cache = CACHE / f"clip_{year}_{'arm' if arm else 'keeper'}.pkl"
    if cache.exists():
        return pickle.load(open(cache, "rb"))
    ensure_probe_path()
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    if arm:
        bag = dict(kwargs.get("prb_overrides") or {})
        bag[FLAG] = True
        kwargs["prb_overrides"] = bag
    clear_fleet_caches()
    state = run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kwargs
    )
    fa = state["fleet_arrays"]
    rows = [
        {
            "i": i,
            "unit_id": str(g.unit_id),
            "plant": int(getattr(g, "plant_code", 0) or 0),
            "group": str(getattr(g, "plant_group", "") or ""),
            "zone": str(getattr(g, "zone", "")),
            "pmax": float(g.pmax_mw),
        }
        for i, g in enumerate(state["fleet"])
    ]
    st = {
        "units": pd.DataFrame(rows),
        "avail": np.asarray(fa.availability, dtype=np.float32),
        "flag": bool(getattr(state["config"], FLAG, False)),
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    pickle.dump(st, open(cache, "wb"))
    return st


def main() -> None:
    out = {}
    for year in YEARS:
        K, A = rebuild(year, arm=False), rebuild(year, arm=True)
        assert (K["units"].unit_id.to_numpy() == A["units"].unit_id.to_numpy()).all()
        assert K["flag"] is False and A["flag"] is True, "flag did not take"
        U = K["units"]
        dav = A["avail"][:, :T] - K["avail"][:, :T]
        moved_mask = np.abs(dav).max(axis=1) > 1e-6
        moved = U[moved_mask]
        # Energy headroom the clip restores, per plant (MWh -> GWh).
        gwh = (dav * U.pmax.to_numpy()[:, None]).sum(axis=1) / 1e3
        by_plant = (
            pd.DataFrame(
                {"plant": U.plant, "group": U.group, "gwh": gwh, "moved": moved_mask}
            )
            .groupby(["plant", "group"], as_index=False)
            .agg(gwh=("gwh", "sum"), units_moved=("moved", "sum"))
        )
        by_plant = by_plant[by_plant.units_moved > 0].sort_values("gwh", key=abs, ascending=False)
        out[str(year)] = {
            "units_availability_moved": int(moved_mask.sum()),
            "units_total": int(len(U)),
            "groups_moved": sorted(set(moved.group)) if len(moved) else [],
            "max_abs_availability_delta": round(float(np.abs(dav).max()), 6),
            "class_available_energy_delta_gwh": {
                g: round(float(v), 2)
                for g, v in by_plant.groupby("group").gwh.sum().items()
            },
            "total_available_energy_delta_gwh": round(float(by_plant.gwh.sum()), 2),
            "per_plant_gwh": [
                {"plant": int(r.plant), "group": r.group, "gwh": round(float(r.gwh), 2),
                 "units_moved": int(r.units_moved)}
                for r in by_plant.itertuples()
            ],
        }

    doc = {
        "session": "nyiso-211",
        "status": "POST-HOC phase 0 — arms nothing, moves no default, decides no declared verdict",
        "keeper": KEEPER_ID,
        "flag": FLAG,
        "instrument": "two on-recipe fleet_only rebuilds; diff of FleetArrays.availability (all four loader channels at once)",
        "years": list(YEARS),
        "by_year": out,
    }
    dest = ROOT / "results/calibration/_nyiso211_clip_rebuild.json"
    dest.write_text(json.dumps(doc, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
