"""NYISO-NEXT-17 zero-LP pre-flight: the F/G re-partition in a fleet-only rebuild.

Rebuilds the keeper's recipe with ``run_year(..., fleet_only=True)`` (the
sanctioned ``replay_keeper.run_year_kwargs`` path) twice — the control and the
arm (``nyiso_fg_split``) — and reports, per model zone, demand energy, thermal
nameplate and wind/solar capacity, plus the topology's links. No LP.

Usage::

    python3 scripts/probes/nyisonext17_fleet_check.py <year> [--bundle <dir>]
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def build(bundle: Path, year: int, arm: bool) -> dict:
    """Fleet-only rebuild of the bundle's recipe, optionally with the arm."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if arm:
        kw["prb_overrides"] = copy.deepcopy(kw.get("prb_overrides") or {})
        kw["prb_overrides"]["nyiso_fg_split"] = True
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def summarize(res: dict) -> dict:
    """Per-zone demand / thermal / renewable totals and the link list."""
    iso = res["iso_config"]
    zones = iso.zone_names
    fa = res["fleet_arrays"]
    zi = np.asarray(fa.zone_idx)
    pmax = np.asarray(fa.pmax, dtype=float)
    dem = np.asarray(res["demand"], dtype=float)
    if dem.shape[0] != len(zones):
        dem = dem.T
    out = {}
    for i, z in enumerate(zones):
        out[z] = {
            "demand_gwh": round(float(dem[i].sum()) / 1e3, 1)
            if i < dem.shape[0]
            else None,
            "thermal_mw": round(float(pmax[zi == i].sum()), 1),
            "wind_mw": round(float(np.asarray(res["wind_cap"]).reshape(-1)[i]), 1)
            if np.asarray(res["wind_cap"]).size == len(zones)
            else None,
            "solar_mw": round(float(np.asarray(res["solar_cap"]).reshape(-1)[i]), 1)
            if np.asarray(res["solar_cap"]).size == len(zones)
            else None,
        }
    return {
        "zones": out,
        "links": [f"{ln.from_zone}>{ln.to_zone}:{ln.ttc_mw:.0f}" for ln in iso.links],
        "fg_split": bool(getattr(res["config"], "nyiso_fg_split", False)),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("year", type=int)
    ap.add_argument("--bundle", default="results/calibration/nyisonext16_span")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    bundle = REPO / a.bundle
    rec = {
        "control": summarize(build(bundle, a.year, False)),
        "arm": summarize(build(bundle, a.year, True)),
    }
    Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
