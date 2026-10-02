"""closeout-NEISO W0 regression guard: zero-LP fleet census of the NEISO keeper recipe.

Rebuilds the LP inputs (``run_year(..., fleet_only=True)``, no solve) for one year on
the NEISO keeper's recipe at the CURRENT checkout, and writes a census JSON:

* ``watch`` — every LP unit of the guarded plants (Pilgrim 1590, Mystic 1588,
  Kendall 1595, Canal 1599) with plant_group, fuel, pmax, heat rate, monthly mean
  availability and mean mc_base;
* ``by_class`` — capacity (MW), available energy (TWh) and mean mc_base per
  plant_group/fuel class;
* ``digest`` — sha256 of every LP input array (pmax, pmin, heat_rate, vom,
  availability, mc_base, min_gen) so "byte-stable" is a checkable claim.

Run it twice — on the W0 base SHA (control) and on the W0 head (arm) — then
``w0_guard_compare.py`` applies the tripwires in
``SPEC-closeout-neiso-w0-regression-guard-2026-10-02.md``. The neiso-119
``lp_input_diff.py`` construction, generalised from one flag pair to two checkouts.

Usage:
    python docs/records/neiso/closeout-w1/w0_guard_census.py --year 2019 --out /tmp/control_2019.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
BUNDLE = REPO / "results/calibration/neiso119_span"

#: The guarded plants (EIA plant codes) and why each is guarded.
WATCH_PLANTS: dict[int, str] = {
    1590: "Pilgrim nuclear, retired 2019-05; carried only by mid_vintage_exit_carry",
    1588: "Mystic 7/8/9, Mystic 7 retired 2021-06, 8&9 2024-05-31; exit carries",
    1595: "Kendall CC_CHP, EIA-860 213/206 MW basis (CAMPD gross is an artifact, neiso-73)",
    1599: "Canal 3, class-preserving union_fleet heat rate (neiso-118)",
}

_HOURS_BY_MONTH = np.repeat(
    np.arange(12), [31 * 24, 28 * 24, 31 * 24, 30 * 24, 31 * 24, 30 * 24,
                    31 * 24, 31 * 24, 30 * 24, 31 * 24, 30 * 24, 31 * 24]
)


def _digest(arr) -> str | None:
    """sha256 of an array's bytes (None when the array is absent)."""
    if arr is None:
        return None
    a = np.ascontiguousarray(np.asarray(arr, dtype=float))
    return hashlib.sha256(a.tobytes()).hexdigest()


def build_census(year: int) -> dict:
    """Rebuild the keeper recipe's fleet for ``year`` (no LP) and census it."""
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf
    from scripts.run_calibration import run_year

    from market_sim.data.fleet.models import FUEL_TYPE_NAMES
    from market_sim.config.paths import set_eia860_vintage
    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = rk.run_year_kwargs(meta)
    kw.update(rk.derived_run_year_inputs(BUNDLE, year))
    st = run_year(
        year, "NEISO", 8760, henry_hub_actual(rcf._load_reference(), year), {},
        fleet_only=True, **kw,
    )
    set_eia860_vintage(None)
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], float)
    mc_mean = mc.mean(axis=1) if mc.ndim == 2 else mc
    avail = np.asarray(fa.availability, float)
    pmax = np.asarray(fa.pmax, float)
    plant = np.asarray(fa.plant_code).astype(int)
    grp = np.asarray(fa.plant_group).astype(str)
    fuel = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
    T = avail.shape[1]
    months = _HOURS_BY_MONTH[:T]

    watch = []
    for i in np.flatnonzero(np.isin(plant, list(WATCH_PLANTS))):
        watch.append({
            "unit_id": fa.unit_ids[i], "plant": int(plant[i]), "group": grp[i],
            "fuel": fuel[i], "pmax_mw": round(float(pmax[i]), 3),
            "heat_rate": round(float(np.asarray(fa.heat_rate)[i]), 4),
            "avail_by_month": [round(float(avail[i, months == m].mean()), 4) for m in range(12)],
            "mc_base_mean": round(float(mc_mean[i]), 4),
        })
    by_class = {}
    for key in sorted(set(zip(grp, fuel))):
        m = (grp == key[0]) & (fuel == key[1])
        by_class[f"{key[0] or '-'}|{key[1]}"] = {
            "n": int(m.sum()),
            "cap_mw": round(float(pmax[m].sum()), 1),
            "avail_twh": round(float((pmax[m, None] * avail[m]).sum()) / 1e6, 4),
            "mc_base_mean": round(float(mc_mean[m].mean()), 4),
        }
    return {
        "year": year,
        "n_units": int(len(fa.unit_ids)),
        "unit_ids_sha256": hashlib.sha256("\n".join(fa.unit_ids).encode()).hexdigest(),
        "watch": watch,
        "by_class": by_class,
        "digest": {
            name: _digest(getattr(fa, name, None))
            for name in ("pmax", "pmin", "heat_rate", "vom", "availability", "min_gen")
        } | {"mc_base": _digest(mc)},
    }


def main() -> int:
    """CLI: census one year to ``--out``."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    os.chdir(REPO)
    out = build_census(args.year)
    args.out.write_text(json.dumps(out, indent=1))
    print(f"wrote {args.out}: {out['n_units']} units, {len(out['watch'])} watched rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
