"""SPP-86 (zero LP): coal outage share on the extract's OWN basis vs the keeper's construction.

Record: ``docs/handoffs/FINDING-spp-86-coal-floor-conduct-2026-09-26.md``.

The keeper divides each coal row's ``unit_capacity_mw`` (the extract's per-unit basis: EIA
nameplate digits or a CEMS proxy) by the fleet bin capacity (EIA-860 per-plant, the same MW the
LP's ``pmax`` sums to). The two bases differ, so a single-unit plant fully out reads
``348.7 / 358.9 = 0.97`` (Holcomb 108: 2.6-2.9 % residual availability, on which the
``coal_mustrun`` floor survives), and a unit at a plant whose extract basis exceeds its LP bin
removes more than its share. nyiso-196's ``unit_outage_extract_basis_share`` takes numerator and
denominator from ONE construction (``_extract_basis_index``) -- but its scope is
``_CC_NAMEPLATE_BASIS_GROUPS`` (combined cycle only).

This rebuilds the keeper ``results/calibration/spp85_arm_span`` fleet ``fleet_only`` twice per
year: as committed (control), and with ``ScenarioConfig.unit_outage_coal_extract_basis_share``
set (that same construction applied to the COAL bins only; no CC bin moves). It reports array
identity, available TWh by class, the coal must-run floor, and the per-plant moves. Solves
nothing. (Phase 0 first measured it by patching ``outages._CC_NAMEPLATE_BASIS_GROUPS`` to
``("COAL",)`` before the field existed; the field reproduces those numbers exactly.)

Usage: ``python scripts/probes/_spp86_coal_basis_delta.py --out <json>``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

BUNDLE = REPO_ROOT / "results/calibration/spp85_arm_span"
MECH_COAL_MUSTRUN = 3
ARRAYS = ("availability", "min_gen", "min_gen_mechanism", "pmax", "heat_rate", "vom")


def build(year: int, arm: bool) -> dict:
    """``fleet_only`` rebuild of the keeper year; ``arm`` = coal on the extract's own basis."""
    from market_sim.config.scenarios import ScenarioConfig
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    orig_post = ScenarioConfig.__post_init__

    def _patched(self):
        orig_post(self)
        object.__setattr__(self, "unit_outage_coal_extract_basis_share", True)

    if arm:
        ScenarioConfig.__post_init__ = _patched
    try:
        st, _ = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
    finally:
        ScenarioConfig.__post_init__ = orig_post
    assert bool(st["config"].unit_outage_coal_extract_basis_share) is arm
    return st


def main() -> None:
    """Control vs arm for each year; print and write JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    res = []
    for y in a.years:
        c, r = build(y, False), build(y, True)
        fc, fr = c["fleet_arrays"], r["fleet_arrays"]
        out: dict = {"year": y, "identical": {}}
        for k in ARRAYS:
            out["identical"][k] = bool(np.array_equal(np.asarray(getattr(fc, k)), np.asarray(getattr(fr, k))))
        groups = np.array([g.plant_group or g.fuel_type for g in c["fleet"]])
        plants = np.array([int(g.plant_code) for g in c["fleet"]])
        pm = np.asarray(fc.pmax)[:, None]
        e0, e1 = pm * np.asarray(fc.availability), pm * np.asarray(fr.availability)
        d = (e1 - e0).sum(1)
        out["d_avail_twh_by_class"] = {
            str(g): round(float(d[groups == g].sum() / 1e6), 4) for g in np.unique(groups) if abs(d[groups == g].sum()) > 1
        }
        out["d_avail_gw_mean"] = round(float(d.sum() / e0.shape[1] / 1e3), 4)
        mech = np.asarray(fc.min_gen_mechanism)
        f0 = np.where(mech == MECH_COAL_MUSTRUN, np.asarray(fc.min_gen), 0).sum()
        f1 = np.where(np.asarray(fr.min_gen_mechanism) == MECH_COAL_MUSTRUN, np.asarray(fr.min_gen), 0).sum()
        out["coal_mustrun_floor_twh"] = [round(float(f0 / 1e6), 4), round(float(f1 / 1e6), 4)]
        by_plant = {}
        for p in np.unique(plants[np.abs(d) > 1]):
            k = plants == p
            by_plant[int(p)] = {
                "d_avail_gwh": round(float(d[k].sum() / 1e3), 1),
                "lp_pmax_mw": round(float(np.asarray(fc.pmax)[k].sum()), 1),
                "classes": sorted(set(groups[k])),
            }
        out["by_plant"] = dict(sorted(by_plant.items(), key=lambda kv: -abs(kv[1]["d_avail_gwh"])))
        out["n_plants_up"] = sum(v["d_avail_gwh"] > 0 for v in by_plant.values())
        out["n_plants_down"] = sum(v["d_avail_gwh"] < 0 for v in by_plant.values())
        print(json.dumps({k: v for k, v in out.items() if k != "by_plant"}))
        res.append(out)
    a.out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
