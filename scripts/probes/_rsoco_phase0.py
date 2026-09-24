"""R-SOCO phase 0 (ZERO LP): per-year fleet-only census on the incumbent SOCO keeper recipe.

Audit `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.8.
Two sides per year, ONE side per process (loaders are lru_cached):

* ``ctl`` -- the keeper recipe at HEAD with the F1 default flips forced back OFF
  (``eia860_vintage_tracks_solve_year`` / ``measured_chp_heat_rates`` False) and
  no new outage family: the pre-audit input posture, as far as HEAD can express it.
* ``arm`` -- the R-SOCO recipe: F1 defaults ON (declared explicitly) + short-coal,
  short-gas and unit-partial outage families armed.

Writes a JSON summary: active EIA-860 dir, thermal MW by group, class-table heat-rate
MW (the audit heuristic: unit heat rate equals a HEAT_RATE_BINS value) with the units
listed, capacity-weighted heat rate by group, and availability energy removed by group.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

KEEPER = _ROOT / "results/calibration/soco61_dark_unit_span"
ARM = {
    "eia860_vintage_tracks_solve_year": True,
    "measured_chp_heat_rates": True,
    "unit_outage_short_windows": True,
    "unit_outage_short_windows_gas": True,
    "unit_partial_outage_windows": True,
}
CTL = {
    "eia860_vintage_tracks_solve_year": False,
    "measured_chp_heat_rates": False,
}


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("year", type=int)
    ap.add_argument("side", choices=("ctl", "arm"))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    from market_sim.config.constants import HEAT_RATE_BINS
    from market_sim.config.paths import active_eia860_dir
    from scripts.replay_keeper import run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **(ARM if a.side == "arm" else CTL)}
    kw.setdefault("inject_biomass_mustrun", False)
    r = run_year(a.year, "SOCO", 8760, None, {}, fleet_only=True, **kw)
    fa = r["fleet_arrays"]
    fleet = r["fleet"]
    bins = {round(v, 6) for d in HEAT_RATE_BINS.values() for v in d.values()}
    pmax = np.asarray(fa.pmax, float)
    hr = np.asarray(fa.heat_rate, float)
    av = np.asarray(fa.availability, float).reshape(len(fleet), -1)
    out = {"year": a.year, "side": a.side, "eia860_dir": str(active_eia860_dir().relative_to(_ROOT)),
           "config_flags": {k: getattr(r["config"], k) for k in ARM}, "groups": {}, "class_table_units": []}
    groups = np.array([str(g.plant_group) for g in fleet])
    for grp in sorted(set(groups)):
        m = groups == grp
        mw = float(pmax[m].sum())
        ht = hr[m]
        ct = np.array([round(float(h), 6) in bins for h in ht])
        out["groups"][grp] = {
            "units": int(m.sum()), "mw": round(mw, 1),
            "hr_capwt": round(float((ht * pmax[m]).sum() / mw), 4) if mw > 0 and np.isfinite(ht).all() else None,
            "class_table_mw": round(float(pmax[m][ct].sum()), 1),
            "avail_removed_twh": round(float(((1 - av[m]) * pmax[m][:, None]).sum() / 1e6), 4),
        }
    for i, g in enumerate(fleet):
        if round(float(hr[i]), 6) in bins and hr[i] > 0:
            out["class_table_units"].append([str(g.unit_id), str(g.plant_group), int(getattr(g, "plant_code", -1) or -1), round(float(pmax[i]), 1), float(hr[i])])
    a.out.write_text(json.dumps(out, indent=1))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
