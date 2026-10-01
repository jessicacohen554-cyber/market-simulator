"""NYISO-NEXT-18 zero-LP fleet census: the keeper recipe vs the arm, per year.

Rebuilds the keeper's recipe with ``run_year(..., fleet_only=True)`` through the
sanctioned ``replay_keeper.run_year_kwargs`` path twice — the control and the arm
(``--flags``, each set True) — and reports every unit that appears, disappears or
changes zone / available energy, plus whether demand is identical. With ``--headroom``
(the keeper control only) it also reports, for the year, the Upstate_West gas
capacity priced below the Upstate_West model price against the gas MW the keeper
dispatched there (per-plant hourlies from the registered run payload). No LP.

Usage::

    python3 scripts/probes/nyisonext18_fleet_census.py <year> --bundle <dir> \\
        --flags mid_vintage_exit_carry,fleet_zone_vintage_coords,retiree_vintage_status_scope \\
        --out <json> [--headroom]
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (".", "scripts", "scripts/probes"):
    sys.path.insert(0, str(REPO / p))

GAS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP")


def build(bundle: Path, year: int, flags: list[str]) -> dict:
    """Fleet-only rebuild of the bundle's recipe with ``flags`` set True."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if flags:
        kw["prb_overrides"] = copy.deepcopy(kw.get("prb_overrides") or {})
        for f in flags:
            kw["prb_overrides"][f] = True
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def units(res: dict) -> dict:
    """``{unit_id: (plant, zone, group, pmax MW, available GWh)}``."""
    zones = res["iso_config"].zone_names
    fa = res["fleet_arrays"]
    pm = np.asarray(fa.pmax, dtype=float)
    av = np.asarray(fa.availability, dtype=float)
    return {
        str(u): (
            str(p),
            zones[z],
            str(g),
            round(float(pm[i]), 1),
            round(float((av[i] * pm[i]).sum()) / 1e3, 1),
        )
        for i, (u, p, z, g) in enumerate(
            zip(fa.unit_ids, fa.plant_code, fa.zone_idx, fa.plant_group)
        )
    }


def headroom(res: dict, year: int) -> dict:
    """UW gas capacity below the UW model price vs the keeper's UW gas dispatch."""
    import nyisonext18_phase0 as p18

    fa = res["fleet_arrays"]
    zi = np.asarray(fa.zone_idx)
    pg = np.asarray(fa.plant_group).astype(str)
    pm = np.asarray(fa.pmax, dtype=float)
    av = np.asarray(fa.availability, dtype=float)
    mc = np.asarray(res["mc_base"], dtype=float)
    uwm = p18.p13.model_prices(year).Upstate_West.to_numpy()
    gas = (zi == 0) & np.isin(pg, GAS)
    cap_all = (av[gas] * pm[gas, None]).sum(0)
    cap_below = (av[gas] * pm[gas, None] * (mc[gas] < uwm[None, :] - 0.5)).sum(0)
    import gzip

    P = p18._payload(p18.RUNS[year])["years"][str(year)]["plants"]
    B = json.load(
        gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{year}.json.gz")
    )["bench"]["plants"]
    disp = np.zeros(8760)
    for key, mp in P.items():
        b = B.get(key)
        if b and b["zone"] == "Upstate_West" and mp.get("m"):
            disp += p18._dec(mp["m"]) * b["npl"] / 100
    hi = p18.p17._ce_ratio(year) >= 0.85
    out = {}
    for nm, m in (("ce_ge_085", hi), ("all", np.isfinite(uwm))):
        out[nm] = {
            "uw_gas_available_mw": round(float(cap_all[m].mean())),
            "uw_gas_below_uw_price_mw": round(float(cap_below[m].mean())),
            "uw_gas_dispatched_mw_bench_plants": round(float(disp[m].mean())),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("year", type=int)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--flags", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--headroom", action="store_true")
    a = ap.parse_args(argv)
    flags = [f for f in a.flags.split(",") if f]
    ctl = build(Path(a.bundle), a.year, [])
    arm = build(Path(a.bundle), a.year, flags)
    c, r = units(ctl), units(arm)
    rec = {
        "year": a.year,
        "flags": flags,
        "added": {u: v for u, v in r.items() if u not in c},
        "removed": {u: v for u, v in c.items() if u not in r},
        "changed": {
            u: [c[u], r[u]]
            for u in c
            if u in r and (c[u][1] != r[u][1] or c[u][4] != r[u][4])
        },
        "demand_identical": bool(
            np.array_equal(np.asarray(ctl["demand"]), np.asarray(arm["demand"]))
        ),
    }
    if a.headroom:
        rec["headroom"] = headroom(ctl, a.year)
    Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
    print(
        json.dumps({k: (len(v) if isinstance(v, dict) else v) for k, v in rec.items()})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
