#!/usr/bin/env python3
"""miso-173 pre-solve CONSTRUCTION check + binding M-1/M-2 predictions (NO LP).

Builds the keeper's own fleet arrays for each solve year through the
production engine — the miso-156-blessed ``_miso134`` ``build_year`` chain
repointed to the current keeper bundle, followed by the FULL production
reliability-floor chain exactly as ``run_calibration.py`` composes it
(overrides → drag-drop → obligation-drop → plant exclusions → injection) —
once with ``mustrun_layup_window_mask`` off and once on, and records the
per-plant ST_GAS-mechanism floor VOLUMES both ways.

Two jobs:

1. CONSTRUCTION check — the mask must reproduce the instrument's ``est``
   exactly on the composition-clean plants (miso-173 measured 1402 / 3457 /
   6035 / 1403 at d = 0.0000 in 2023) and must be a construction no-op when
   off. A defect here stops the session before a ~50-minute solve is spent.
2. BINDING predictions — the per-plant volumes recorded here (the
   ``engine_volumes`` block written into
   ``results/calibration/_miso173_layup_mask_instrument.json``) are the M-1 /
   M-2 gate targets. The CSV-level ``est`` instrument is blind to
   floor-COMPOSITION competition (another mechanism out-bidding the p25 take
   re-stamps the cell's mechanism id — measured on 990 / 3459 / 1122 in the
   2023 check), so the engine build, not the CSV arithmetic, is what the
   arm's ``floors/<year>_P1.npz`` must reproduce.

Usage::

    python3 scripts/probes/_miso173_mask_construction_check.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts/probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

BUNDLE = REPO / "results/calibration/miso172_p25mw"
_m134.BUNDLE = BUNDLE
assert _m134.BUNDLE == BUNDLE

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402

from market_sim.config.iso_configs import (  # noqa: E402
    RELIABILITY_FLOOR_REGISTRY,
    apply_reliability_floor_overrides,
    apply_reliability_floor_plant_exclusions,
    drop_drag_owned_reliability_specs,
    drop_obligation_owned_reliability_specs,
    get_iso_config,
)
from market_sim.data.floor_mechanisms import (  # noqa: E402
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
)
from market_sim.data.renewables import load_renewable_profiles  # noqa: E402
from market_sim.model.transmission import inject_reliability_floor  # noqa: E402

INSTRUMENT = REPO / "results/calibration/_miso173_layup_mask_instrument.json"
LIVE = (3459, 1403, 990, 1122, 3457, 1402, 6035)


def _full_chain(cfg, year: int):
    """build_year + the production reliability-floor chain, run_calibration order."""
    cfg_y = dataclasses.replace(cfg, weather_year=year)
    raw_fleet, fleet, arrays, *_rest, zone_names = build_year(cfg_y, year)
    if getattr(cfg_y, "reliability_floor", False):
        specs = apply_reliability_floor_overrides(
            RELIABILITY_FLOOR_REGISTRY.get("MISO", []),
            getattr(cfg_y, "reliability_floor_overrides", None),
        )
        specs = drop_drag_owned_reliability_specs(specs, cfg_y)
        specs = drop_obligation_owned_reliability_specs(specs, cfg_y)
        specs = apply_reliability_floor_plant_exclusions(specs, cfg_y)
        sysf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        dem = sysf.pivot_table(index="hour", columns="zone", values="demand")
        hours = dem.shape[0]
        dz = np.zeros((len(zone_names), hours))
        for i, z in enumerate(zone_names):
            if z in dem.columns:
                dz[i] = dem[z].to_numpy()
        wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
            "MISO", year, get_iso_config("MISO"), cfg_y
        )
        inject_reliability_floor(
            arrays,
            "MISO",
            year,
            specs,
            zone_names,
            demand=dz,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=solar_cf,
            solar_cap=solar_cap,
        )
    return fleet, arrays


def _stgas_plant_volumes(fleet, arrays) -> dict[int, float]:
    """Per-plant TWh of ST_GAS-mechanism floor volume in the built arrays."""
    if arrays.min_gen is None:
        return {}
    mg = np.asarray(arrays.min_gen, float)
    mech = np.asarray(arrays.min_gen_mechanism)
    vols: dict[int, float] = {}
    for i, g in enumerate(fleet):
        if str(getattr(g, "plant_group", "") or "") != "ST_GAS":
            continue
        sel = mech[i] == MECH_ST_GAS_MUSTRUN_PER_PLANT
        if not sel.any():
            continue
        pc = int(getattr(g, "plant_code", 0) or 0)
        vols[pc] = vols.get(pc, 0.0) + float(mg[i, sel].sum()) / 1e6
    return vols


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()

    inst = json.loads(INSTRUMENT.read_text())
    pred = inst["volume_predictions"]
    engine: dict = {}

    cfg = keeper_config()
    assert not getattr(cfg, "mustrun_layup_window_mask", False)
    ok = True
    for year in args.years:
        _, arrays0 = None, None
        fleet0, arrays0 = _full_chain(cfg, year)
        vols0 = _stgas_plant_volumes(fleet0, arrays0)
        fleet1, arrays1 = _full_chain(
            dataclasses.replace(cfg, mustrun_layup_window_mask=True), year
        )
        vols1 = _stgas_plant_volumes(fleet1, arrays1)
        print(f"== {year}: per-plant ST_GAS floor volumes (TWh), engine off/on")
        engine[str(year)] = {}
        for pc in sorted(set(vols0) | set(vols1) | set(LIVE)):
            v0, v1 = vols0.get(pc, 0.0), vols1.get(pc, 0.0)
            p = pred[str(year)].get(str(pc), {})
            e0, e1 = p.get("est_ctrl_twh"), p.get("est_arm_twh")
            engine[str(year)][str(pc)] = {
                "engine_ctrl_twh": round(v0, 6),
                "engine_arm_twh": round(v1, 6),
            }
            note = ""
            if e0 is not None and (abs(v0 - e0) > 0.005 or abs(v1 - e1) > 0.005):
                note = "  (composition-competed; engine is the binding target)"
            print(
                f"  {pc}: off {v0:.4f} on {v1:.4f}"
                f"  [csv est {e0} -> {e1}]{note}"
            )
            if v1 > v0 + 1e-9:
                ok = False
                print(f"    ^^ FAIL: mask INCREASED plant {pc} volume")
    inst["engine_volumes"] = engine
    INSTRUMENT.write_text(json.dumps(inst, indent=1))
    print(f"updated {INSTRUMENT}")
    print(f"construction check: {'PASS' if ok else 'FAIL'}")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
