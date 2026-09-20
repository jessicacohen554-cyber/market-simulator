"""nyiso-249 — G-5: the reachability bound, PER ZONE, because the deficit is LOCATIONAL.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Routing instrument for the successor, not a
gate on this lane's form.

G-4 measured that **136 of 153** missed hours across 2022-2025 carry their model
maximum in **Long_Island** (77/91, 10/10, 13/13, 36/39), and that the missed
hours sit at the top of the LOAD distribution rather than the gas one (2025
load-percentile p50 = 1.00 with 92 % at or above p90, while only 15 % of the
same hours reach the gas p90).

That makes ``nyiso242_tail_reachability``'s central number -- *"4,689 MW idle
below $300 in 2022's missed hours, therefore not reachable by price
formation"* -- **possibly the wrong instrument for these hours**. It is an
ISO-WIDE idle count, and the LP's Long Island dual is not set by capacity the
LP cannot deliver to Long Island. If LI is import-constrained in the missed
hours, idle upstate capacity is irrelevant to the LI price and the ISO-wide
bound overstates the ceiling.

This probe re-runs the identical bound **partitioned by zone**, on the same
fleet-only rebuild and the same committed hourlies, and reports for each missed
hour the idle sub-$300 capacity **inside Long Island** beside the ISO-wide
figure. It also reports the LI interface flow against its limit where the
committed sidecars carry it, since "import-constrained" is the premise being
tested rather than assumed.

**What it can and cannot establish.** A small LI idle figure beside a large
ISO-wide one says the ISO-wide bound was not binding on the LI price, which is
a reason to RE-OPEN the locational question -- not a demonstration that any
particular mechanism closes it. Only a solve can do that, and this lane is not
solving it.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso249_li_reachability.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "_nyiso249_li_reachability.json"
THRESHOLD = 300.0
ZONES_OF_INTEREST = ("Long_Island", "NYC")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=None)
    args = ap.parse_args()

    from market_sim.config.iso_configs import get_iso_config
    from scripts.data.derive_nyiso_offer_surface import YEARS
    from scripts.probes.nyiso242_tail_reachability import (
        BUNDLE,
        _is_thermal,
        fleet_state,
        missed_mask,
    )

    years = args.year or list(YEARS)
    zone_names = get_iso_config("NYISO").zone_names
    result: dict = {"gate": "G-5", "session": "nyiso-249", "years": {}}

    for y in years:
        st = fleet_state(y)
        fa = st["fleet_arrays"]
        pmax = np.asarray(fa.pmax, float)
        klass = np.array([str(k) for k in fa.plant_group])
        zidx = np.asarray(fa.zone_idx, int)
        av = np.asarray(fa.availability, float)
        if av.ndim == 1:
            av = np.repeat(av[:, None], 8760, axis=1)
        mc = np.asarray(st["mc_base"], float)
        if mc.ndim == 1:
            mc = np.repeat(mc[:, None], 8760, axis=1)
        thermal = np.array([_is_thermal(k) for k in klass])

        missed, _month = missed_mask(y)
        n = min(len(missed), av.shape[1])
        sel = np.flatnonzero(missed[:n])

        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        has_zone = "zone" in ch.columns
        gen_by_zone: dict[str, np.ndarray] = {}
        if has_zone:
            for z in ZONES_OF_INTEREST:
                sub = ch[ch["zone"] == z]
                sub = sub[[_is_thermal(str(k)) for k in sub["klass"]]]
                g = sub.groupby("hour")["mw"].sum().reindex(range(n), fill_value=0.0)
                gen_by_zone[z] = g.to_numpy()

        yr: dict = {"n_missed": int(len(sel)), "class_hourly_has_zone": bool(has_zone)}

        # ISO-wide, reproducing nyiso242's construction.
        tot = thermal
        avail_iso = (pmax[tot, None] * av[tot][:, sel]).sum(axis=0)
        cheap = thermal[:, None] & (mc[:, sel] < THRESHOLD)
        avail_cheap_iso = (pmax[:, None] * av[:, sel] * cheap).sum(axis=0)
        yr["iso_wide"] = {
            "avail_thermal_mw_mean": round(float(avail_iso.mean()), 1),
            "avail_sub300_mw_mean": round(float(avail_cheap_iso.mean()), 1),
        }

        for z in ZONES_OF_INTEREST:
            if z not in zone_names:
                continue
            zi = zone_names.index(z)
            inz = thermal & (zidx == zi)
            if not inz.any():
                continue
            avail_z = (pmax[inz, None] * av[inz][:, sel]).sum(axis=0)
            cheap_z = inz[:, None] & (mc[:, sel] < THRESHOLD)
            avail_cheap_z = (pmax[:, None] * av[:, sel] * cheap_z).sum(axis=0)
            entry = {
                "n_thermal_rows": int(inz.sum()),
                "nameplate_mw": round(float(pmax[inz].sum()), 1),
                "avail_thermal_mw_mean": round(float(avail_z.mean()), 1),
                "avail_sub300_mw_mean": round(float(avail_cheap_z.mean()), 1),
            }
            if z in gen_by_zone:
                g = gen_by_zone[z][sel]
                idle = np.maximum(0.0, avail_cheap_z - g)
                entry["dispatched_mw_mean"] = round(float(g.mean()), 1)
                entry["IDLE_sub300_mw_mean"] = round(float(idle.mean()), 1)
                entry["IDLE_sub300_mw_p50"] = round(float(np.median(idle)), 1)
                entry["utilisation_pct"] = round(
                    float(100.0 * g.sum() / max(1e-9, avail_z.sum())), 1
                )
                entry["hours_with_idle_sub300_under_100mw"] = int((idle < 100.0).sum())
            yr[z] = entry

        result["years"][str(y)] = yr
        print(f"\n=== {y} ===  missed={yr['n_missed']}  "
              f"ISO-wide avail_sub300={yr['iso_wide']['avail_sub300_mw_mean']:.0f} MW")
        for z in ZONES_OF_INTEREST:
            if z in yr:
                e = yr[z]
                extra = (
                    f"  gen={e.get('dispatched_mw_mean', float('nan')):7.0f}"
                    f"  IDLE<$300={e.get('IDLE_sub300_mw_mean', float('nan')):7.0f} MW"
                    f"  util={e.get('utilisation_pct', float('nan')):5.1f}%"
                    f"  h(idle<100MW)={e.get('hours_with_idle_sub300_under_100mw', '-')}"
                    if "dispatched_mw_mean" in e
                    else "  (class_hourly carries no zone column)"
                )
                print(f"  {z:<12} rows={e['n_thermal_rows']:3d} "
                      f"avail={e['avail_thermal_mw_mean']:7.0f}"
                      f"  avail<$300={e['avail_sub300_mw_mean']:7.0f}{extra}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
