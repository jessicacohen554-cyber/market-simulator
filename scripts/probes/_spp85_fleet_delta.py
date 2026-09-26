"""SPP-85 (zero LP): LP-input delta of ``unit_outage_netload_mask_repair`` on the SPP keeper.

Record: ``docs/handoffs/FINDING-spp-85-coal-outage-basis-2026-09-26.md``.

Rebuilds the keeper ``results/calibration/rspp_span``'s fleet ``fleet_only`` for one year twice --
the recipe as committed (control) and the same recipe with ``unit_outage_netload_mask_repair``
set True (arm) -- and reports, per fleet array, whether it is byte-identical, and the change in
available energy (``pmax x availability``) by class. Solves nothing.

Usage: ``python scripts/probes/_spp85_fleet_delta.py --year 2024 --out <json>``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.probes._spp81b_upper_tercile_marginal_unit import BUNDLE  # noqa: E402

ARRAYS = (
    "availability", "min_gen", "min_gen_mechanism", "pmax", "pmin", "heat_rate", "vom",
    "emission_rate", "nox_rate", "so2_rate", "zone_idx", "fuel_type_idx", "efficiency_bin",
    "plant_code", "unit_ids",
)


def build(year: int, arm: bool) -> dict:
    """``fleet_only`` reconstruction of the keeper year, optionally with the repair armed."""
    from market_sim.config.scenarios import ScenarioConfig
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    orig = ScenarioConfig.__post_init__

    def _patched(self):
        orig(self)
        object.__setattr__(self, "unit_outage_netload_mask_repair", True)

    if arm:
        ScenarioConfig.__post_init__ = _patched
    try:
        st, _ = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
    finally:
        ScenarioConfig.__post_init__ = orig
    assert bool(st["config"].unit_outage_netload_mask_repair) is arm
    return st


def _h(a) -> str:
    return hashlib.sha256(np.ascontiguousarray(np.asarray(a)).tobytes()).hexdigest()[:16]


def main() -> None:
    """Control vs arm for one year; print and write JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    c, r = build(a.year, False), build(a.year, True)
    fc, fr = c["fleet_arrays"], r["fleet_arrays"]
    out = {"year": a.year, "identical": {}, "hash": {}}
    for k in ARRAYS:
        x, y = getattr(fc, k, None), getattr(fr, k, None)
        if x is None:
            continue
        out["identical"][k] = bool(_h(x) == _h(y))
        out["hash"][k] = [_h(x), _h(y)]
    groups = np.array([g.plant_group or g.fuel_type for g in c["fleet"]])
    e0 = np.asarray(fc.pmax)[:, None] * np.asarray(fc.availability)
    e1 = np.asarray(fr.pmax)[:, None] * np.asarray(fr.availability)
    d = (e1 - e0).sum(1)
    out["d_avail_twh_by_class"] = {
        str(g): round(float(d[groups == g].sum() / 1e6), 4)
        for g in np.unique(groups)
        if abs(d[groups == g].sum()) > 0
    }
    out["d_avail_gw_mean"] = round(float(d.sum() / e0.shape[1] / 1e3), 4)
    out["rows_moved"] = int((np.abs(e1 - e0).sum(1) > 1e-6).sum())
    out["moved_plants"] = sorted(
        {int(g.plant_code) for g, m in zip(c["fleet"], np.abs(e1 - e0).sum(1) > 1e-6) if m}
    )
    print(json.dumps(out))
    a.out.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
