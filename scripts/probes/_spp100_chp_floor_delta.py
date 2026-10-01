"""SPP-100 (zero LP): the CHP steam floor the conduct scope builds on the SPP keeper.

Record: ``docs/records/spp/PRECOMMIT-spp-100-chp-conduct-scope-2026-09-28.md``.

Rebuilds keeper ``results/calibration/spp99_remap_span``'s fleet ``fleet_only`` for one year
under one arm and dumps the per-row arrays. Arms: ``control`` (the keeper recipe), ``P``
(+ ``chp_steam_floor_p25``, SPP-75's declined arm) and ``S`` (+ ``chp_steam_floor_p25`` +
``chp_steam_floor_conduct_scope``, this lane's arm). Each arm runs in its own process (the
loaders are ``lru_cache``-d). ``--compare`` prints per-plant floor MW / floored hours and the
max |delta| of every array outside the CHP rows. Solves nothing.

Usage: ``python scripts/probes/_spp100_chp_floor_delta.py --year 2024 --arm S --out s.npz``
       ``python scripts/probes/_spp100_chp_floor_delta.py --compare c.npz s.npz``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

BUNDLE = REPO_ROOT / "results/calibration/spp99_remap_span"
ARRAYS = ("availability", "min_gen", "pmax", "pmin", "heat_rate", "vom")
ARM_FIELDS = {
    "control": {},
    "P": {"chp_steam_floor_p25": True},
    "S": {"chp_steam_floor_p25": True, "chp_steam_floor_conduct_scope": True},
}


def build(year: int, arm: str) -> dict:
    """``fleet_only`` reconstruction of the keeper year under ``arm``."""
    from market_sim.config.scenarios import ScenarioConfig
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    fields = ARM_FIELDS[arm]
    orig = ScenarioConfig.__post_init__

    def _patched(self):
        orig(self)
        for k, v in fields.items():
            object.__setattr__(self, k, v)

    ScenarioConfig.__post_init__ = _patched
    st, _ = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
    for k, v in fields.items():
        assert getattr(st["config"], k) is v, k
    return st


def dump(st: dict, out: Path) -> None:
    """Write the fleet arrays + per-row identity + CHP-floor mechanism mask to ``out``."""
    from market_sim.data.floor_mechanisms import MECH_CHP_STEAM

    fa = st["fleet_arrays"]
    arrs = {
        k: np.asarray(getattr(fa, k))
        for k in ARRAYS
        if getattr(fa, k, None) is not None
    }
    mech = np.asarray(getattr(fa, "min_gen_mechanism"))
    arrs["chp_mask"] = mech == MECH_CHP_STEAM
    arrs["plant_code"] = np.array([int(g.plant_code) for g in st["fleet"]])
    arrs["group"] = np.array([str(g.plant_group or g.fuel_type) for g in st["fleet"]])
    np.savez_compressed(out, **arrs)


def compare(c_path: Path, a_path: Path) -> None:
    """Print per-plant CHP floors and the max per-plant delta outside the CHP plants.

    Rows are aggregated per plant because the swap re-bands a CHP plant's committed/econ
    split (tranche count can change); every other plant must match exactly.
    """
    c, a = np.load(c_path), np.load(a_path)
    chp = set(c["plant_code"][c["chp_mask"].any(axis=1)]) | set(
        a["plant_code"][a["chp_mask"].any(axis=1)]
    )
    print("plant   group    ctrl_MW  ctrl_h  arm_MW  arm_h   ctrl_TWh  arm_TWh")
    tot_c = tot_a = 0.0
    for pc in sorted(chp):
        rc, ra = c["plant_code"] == pc, a["plant_code"] == pc
        mc = np.where(c["chp_mask"][rc], c["min_gen"][rc], 0.0).sum(axis=0)
        ma = np.where(a["chp_mask"][ra], a["min_gen"][ra], 0.0).sum(axis=0)
        tot_c += mc.sum()
        tot_a += ma.sum()
        hc, ha = int((mc > 0).sum()), int((ma > 0).sum())
        print(
            f"{pc:6d} {c['group'][rc][0]:8s} {mc[mc > 0].mean() if hc else 0:7.1f} {hc:6d} "
            f"{ma[ma > 0].mean() if ha else 0:7.1f} {ha:6d} {mc.sum() / 1e6:9.4f} "
            f"{ma.sum() / 1e6:8.4f}"
        )
    print(
        f"TOTAL CHP floor TWh ctrl {tot_c / 1e6:.4f}  arm {tot_a / 1e6:.4f}  "
        f"mean MW {tot_c / 8760:.1f} -> {tot_a / 8760:.1f}"
    )
    rest = sorted(set(c["plant_code"]) - chp)
    worst = {}
    for pc in rest:
        rc, ra = c["plant_code"] == pc, a["plant_code"] == pc
        if rc.sum() != ra.sum():
            worst["rowcount"] = max(worst.get("rowcount", 0), 1)
            continue
        for k in ("min_gen", "pmax", "pmin", "heat_rate", "vom"):
            if k in c and k in a:
                d = float(
                    np.abs(
                        np.asarray(c[k][rc], float) - np.asarray(a[k][ra], float)
                    ).max()
                )
                worst[k] = max(worst.get(k, 0.0), d)
        ec = (c["pmax"][rc][:, None] * c["availability"][rc]).sum()
        ea = (a["pmax"][ra][:, None] * a["availability"][ra]).sum()
        worst["avail_MWh"] = max(worst.get("avail_MWh", 0.0), abs(float(ec - ea)))
    print(f"non-CHP plants ({len(rest)}) max |delta|: {worst}")


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int)
    ap.add_argument("--arm", choices=sorted(ARM_FIELDS))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--compare", nargs=2, type=Path)
    ns = ap.parse_args()
    if ns.compare:
        compare(*ns.compare)
        return
    dump(build(ns.year, ns.arm), ns.out)


if __name__ == "__main__":
    main()
