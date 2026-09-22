"""SOCO-59 rule 19 [R-ONE-MECH] proof, zero LP, keyed by ``unit_id``.

``_soco57_rule19.py`` compares fleets ROW BY ROW, which is only valid when the
arm and control fleets have the same unit list. The hydro arm changes the unit
list itself (2025: the 5 EIA-923-reporting hydro plants become 42 once the
backfill supplies coverage), so this probe aligns on ``unit_id`` and reports:

* units ADDED / REMOVED, by ``plant_group`` (the arm must add hydro and nothing
  else);
* on the SHARED units, ``fuel_prices`` / ``mc_base`` / ``pmax`` /
  ``availability`` / ``heat_rate`` max|delta| and KEYS MOVED (must be zero —
  the arm is a hydro ENERGY-BUDGET input and touches no thermal offer);
* the monthly hydro energy budget handed to the LP, control vs arm.

The arm is the two ``solve_and_persist`` kwargs ``replay_keeper --set`` routes
(``hydro_backfill_year=2024``, ``hydro_eia930_monthly=True``) on top of the
``EIA930_PS_SPLIT_COMPLETE_FROM['SOCO'] = 2025`` registration at HEAD.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

ARM = {"hydro_backfill_year": 2024, "hydro_eia930_monthly": True}


def _build(bundle: Path, year: int, arm: bool):
    """``run_year(fleet_only=True)`` off the bundle's recipe, optionally armed."""
    import json

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if arm:
        kw.update(ARM)
    return run_year(year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, help="leg bundle; YEAR is substituted")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    a = ap.parse_args()
    for year in a.years:
        bundle = Path(str(a.bundle).replace("YEAR", str(year)))
        c, r = _build(bundle, year, False), _build(bundle, year, True)
        uc = [str(g.unit_id) for g in c["fleet"]]
        ur = [str(g.unit_id) for g in r["fleet"]]
        gc = {str(g.unit_id): str(g.plant_group) for g in c["fleet"]}
        gr = {str(g.unit_id): str(g.plant_group) for g in r["fleet"]}
        added, removed = sorted(set(ur) - set(uc)), sorted(set(uc) - set(ur))
        print(f"\n===== {year}  control {len(uc)} units  arm {len(ur)} units =====")
        print(f"  added   {len(added)}  groups {sorted({gr[u] for u in added})}")
        print(f"  removed {len(removed)}  groups {sorted({gc[u] for u in removed})}")
        ic = {u: i for i, u in enumerate(uc)}
        ir = {u: i for i, u in enumerate(ur)}
        shared = [u for u in uc if u in ir]
        a_idx = np.array([ic[u] for u in shared])
        b_idx = np.array([ir[u] for u in shared])
        for key in ("fuel_prices", "mc_base"):
            x = np.asarray(c[key], float)[a_idx]
            y = np.asarray(r[key], float)[b_idx]
            d = np.abs(x - y).reshape(len(shared), -1).max(axis=1)
            print(f"  {key:12s} shared max|d| {float(d.max()):.12f}  keys moved {int((d > 0).sum())}/{len(shared)}")
        for key in ("pmax", "availability", "heat_rate"):
            fc, fr = c["fleet_arrays"], r["fleet_arrays"]
            if not hasattr(fc, key):
                continue
            x = np.asarray(getattr(fc, key), float)[a_idx]
            y = np.asarray(getattr(fr, key), float)[b_idx]
            d = np.abs(x - y).reshape(len(shared), -1).max(axis=1)
            print(f"  {key:12s} shared max|d| {float(d.max()):.12f}  keys moved {int((d > 0).sum())}/{len(shared)}")
        for label, built in (("control", c), ("arm", r)):
            me = built.get("hydro_monthly_energy")
            if me is not None:
                me = np.asarray(me, float)
                print(f"  hydro budget {label:7s} {me.sum() / 1e6:.4f} TWh")


if __name__ == "__main__":
    main()
