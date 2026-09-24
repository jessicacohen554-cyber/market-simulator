"""nwpp-51 phase 0: what ``eia860_vintage_tracks_solve_year`` changes in NWPP's fleet. ZERO LP.

Rebuilds the keeper's fleet (``results/calibration/nwpp49_ror_span``) with
``run_year(fleet_only=True)`` twice per year — the keeper recipe as recorded
(flag OFF) and the same recipe with the flag ON — and diffs the LP-facing
FleetArrays by ``unit_id``: which rows appear, vanish or change class /
pmax / pmin / heat rate / availability-weighted MWh / mc_base.

The recipe comes from ``scripts/replay_keeper.run_year_kwargs`` (the only
sanctioned fleet-only reconstruction, caiso-244) plus
``derived_run_year_inputs``; the flag is added through the same
``prb_overrides`` channel ``replay_keeper.py --set`` uses.

Prerequisites (zero LP, ~2 min):
``run_calibration_full.py --iso NWPP --restore-shared-inputs
results/calibration/nwpp49_ror_span`` and
``scripts/data/curate_hydro_plant_modes.py --iso NWPP``.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwpp51_vintage_census.py \
        [--years 2023 2024 2025] [--out results/calibration/_nwpp51_vintage_census.json]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nwpp49_ror_span")
FLAG = "eia860_vintage_tracks_solve_year"
#: FleetArrays fields hashed for the byte-identity check (every LP-facing array).
ARRAY_FIELDS = (
    "pmax", "pmin", "heat_rate", "vom", "emission_rate", "nox_rate", "zone_idx",
    "fuel_type_idx", "availability", "efficiency_bin", "plant_code", "min_gen",
)


def _build(year: int, on: bool) -> dict:
    """Fleet-only rebuild of the keeper recipe for one year, flag on or off."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    kw["prb_overrides"] = copy.deepcopy(kw.get("prb_overrides") or {})
    kw["prb_overrides"][FLAG] = bool(on)
    return run_year(year, meta["iso"], 8760, meta["gas_prices"][str(year)], {},
                    fleet_only=True, **kw)


def _frame(built: dict) -> pd.DataFrame:
    """One row per LP unit: id, plant, class, zone, pmax, pmin, hr, avail MWh, mean mc."""
    fa, fleet = built["fleet_arrays"], built["fleet"]
    avail = np.asarray(fa.availability, float)
    pmax = np.asarray(fa.pmax, float)
    mwh = (avail * pmax[:, None]).sum(1) if avail.ndim == 2 else avail * pmax * 8760
    mc = np.asarray(built["mc_base"], float)
    mc_mean = mc.mean(1) if mc.ndim == 2 else mc
    return pd.DataFrame({
        "unit_id": list(fa.unit_ids),
        "plant": np.asarray(fa.plant_code).astype(int),
        "klass": [str(getattr(g, "plant_group", None) or getattr(g, "fuel_type", "")) for g in fleet],
        "fuel": [str(getattr(g, "fuel_type", "")) for g in fleet],
        "pmax": pmax,
        "pmin": np.asarray(fa.pmin, float),
        "hr": np.asarray(fa.heat_rate, float),
        "avail_twh": mwh / 1e6,
        "mc": mc_mean,
    })


def _digest(built: dict) -> str:
    """sha256 over every LP-facing FleetArrays field plus mc_base."""
    fa = built["fleet_arrays"]
    h = hashlib.sha256()
    h.update("|".join(fa.unit_ids).encode())
    for f in ARRAY_FIELDS:
        v = getattr(fa, f, None)
        if v is not None:
            h.update(np.ascontiguousarray(np.asarray(v)).tobytes())
    h.update(np.ascontiguousarray(np.asarray(built["mc_base"], float)).tobytes())
    return h.hexdigest()


def census(year: int) -> dict:
    """Diff the flag-off and flag-on fleets for one year."""
    off, on = _build(year, False), _build(year, True)
    a, b = _frame(off), _frame(on)
    m = a.merge(b, on="unit_id", how="outer", suffixes=("_off", "_on"), indicator=True)
    added = m[m._merge == "right_only"]
    removed = m[m._merge == "left_only"]
    both = m[m._merge == "both"]
    changed = both[(both.klass_off != both.klass_on) | ~np.isclose(both.pmax_off, both.pmax_on)
                   | ~np.isclose(both.hr_off, both.hr_on) | ~np.isclose(both.avail_twh_off, both.avail_twh_on)
                   | ~np.isclose(both.mc_off, both.mc_on) | ~np.isclose(both.pmin_off, both.pmin_on)]
    by_class = pd.concat([
        a.groupby("klass").agg(mw_off=("pmax", "sum"), avail_off=("avail_twh", "sum")),
        b.groupby("klass").agg(mw_on=("pmax", "sum"), avail_on=("avail_twh", "sum")),
    ], axis=1).fillna(0.0)
    by_class["d_mw"] = by_class.mw_on - by_class.mw_off
    by_class["d_avail_twh"] = by_class.avail_on - by_class.avail_off
    by_class = by_class[(by_class.d_mw.abs() > 1e-6) | (by_class.d_avail_twh.abs() > 1e-6)]
    touched = set(added.plant_on.dropna().astype(int)) | set(removed.plant_off.dropna().astype(int)) \
        | set(changed.plant_off.dropna().astype(int))
    by_plant = []
    for p in sorted(touched):
        ao, bo = a[a.plant == p], b[b.plant == p]
        by_plant.append({
            "plant": p,
            "off": ao.groupby("klass").pmax.sum().round(3).to_dict(),
            "on": bo.groupby("klass").pmax.sum().round(3).to_dict(),
            "off_units": ao.unit_id.tolist(), "on_units": bo.unit_id.tolist(),
            "on_mc_by_unit": bo.set_index("unit_id").mc.round(3).to_dict(),
            "on_avail_twh_by_unit": bo.set_index("unit_id").avail_twh.round(4).to_dict(),
            "avail_twh_off": round(float(ao.avail_twh.sum()), 4),
            "avail_twh_on": round(float(bo.avail_twh.sum()), 4),
        })
    # Generator-object attribute diffs on changed units: names the field that
    # moved (e.g. a tranche's fuel fraction), not just the resulting mc.
    goff = {str(g.unit_id): g for g in off["fleet"]}
    gon = {str(g.unit_id): g for g in on["fleet"]}
    attr_diff = {}
    for uid in changed.unit_id:
        a_, b_ = vars(goff[uid]) if hasattr(goff[uid], "__dict__") else goff[uid].model_dump(), \
            vars(gon[uid]) if hasattr(gon[uid], "__dict__") else gon[uid].model_dump()
        d = {k: [str(a_.get(k))[:60], str(b_.get(k))[:60]] for k in sorted(set(a_) | set(b_))
             if str(a_.get(k)) != str(b_.get(k))}
        attr_diff[uid] = d
    d_off, d_on = _digest(off), _digest(on)
    return {
        "year": year, "n_units_off": len(a), "n_units_on": len(b),
        "digest_off": d_off, "digest_on": d_on, "byte_identical": d_off == d_on,
        "n_added": len(added), "n_removed": len(removed), "n_changed": len(changed),
        "by_class": by_class.round(4).reset_index().to_dict("records"),
        "by_plant": by_plant,
        "changed_units": changed[["unit_id", "plant_off", "klass_off", "klass_on", "pmax_off", "pmax_on",
                                  "mc_off", "mc_on", "avail_twh_off", "avail_twh_on"]]
        .round(4).to_dict("records"),
        "attr_diff": attr_diff,
    }


def main() -> None:
    """Run the census for every year and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=Path("results/calibration/_nwpp51_vintage_census.json"))
    args = ap.parse_args()
    out = []
    for y in args.years:
        r = census(y)
        out.append(r)
        print(f"\n== {y}: units {r['n_units_off']} -> {r['n_units_on']}  +{r['n_added']} "
              f"-{r['n_removed']} ~{r['n_changed']}  byte-identical={r['byte_identical']}")
        for c in r["by_class"]:
            print(f"   {c['klass']:<14} MW {c['mw_off']:9.1f} -> {c['mw_on']:9.1f} ({c['d_mw']:+8.1f})  "
                  f"avail TWh {c['d_avail_twh']:+7.3f}")
        for p in r["by_plant"]:
            print(f"   plant {p['plant']}: {p['off']} -> {p['on']}  avail TWh "
                  f"{p['avail_twh_off']:.3f} -> {p['avail_twh_on']:.3f}")
    args.out.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
