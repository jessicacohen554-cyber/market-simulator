#!/usr/bin/env python3
"""miso-287 phase 0 (ZERO LP): where P1 departs from the base-cost merit clear at night.

Companion to ``_miso287_p1_residual.py``. Per year, the P0 stack is cleared at
the keeper's P1 thermal quantity (all hours, as there) and its night dispatch is
aggregated by class and band family, then set beside the keeper's committed P1
``class_band_hourly`` night dispatch. A class the LP runs ABOVE its merit-clear
position while a cheaper class runs BELOW it is the signature of a constraint
the copperplate clear omits (network, seam envelope, energy budget); the
per-class offer at the P1 price says which rows P1 must be pricing.

Output: ``results/phase0/miso/_miso287_class_gap.json``. Rule 13: nothing here
feeds a solve.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402
from scripts.probes._miso287_p1_residual import (  # noqa: E402
    KEEPER,
    NIGHT_H,
    NON_LP,
    T,
    clear_all,
)  # noqa: E402


CACHE = Path("/tmp/miso287_stack_cache")


def load_stack(y, run_year, hh_fn, ref_fn):
    """Fleet-only rebuild arrays for ``y`` (cached on local disk, never committed)."""
    f = CACHE / f"{y}_v2.npz"
    if f.exists():
        z = np.load(f, allow_pickle=False)
        return z["mc"], z["cap"], z["mg"], z["grp"], z["fam"], z["zone"]
    hh = hh_fn(ref_fn(), y)
    st = run_year(y, "MISO", T, hh, {}, fleet_only=True, **dec.recipe(y, {}))
    fa = st["fleet_arrays"]
    n = len(fa.pmax)
    mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
    if mc.shape[1] == 1:
        mc = np.repeat(mc, T, axis=1)
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    mg = np.minimum(np.asarray(fa.min_gen, float), cap)
    grp = np.asarray(fa.plant_group).astype(str)
    uid = np.asarray(list(fa.unit_ids)).astype(str)
    inv = {v: k for k, v in dec.FUEL_TYPE_MAP.items()}
    fuel = np.asarray([inv.get(int(i), "?") for i in np.asarray(fa.fuel_type_idx)])
    # Group-less rows: seam price bands (``<neighbour>#k``) are ``import`` as
    # in the sidecar; anything else (nuclear, hydro, ...) takes its fuel.
    grp = np.where(
        grp != "", grp, np.where(np.char.find(uid, "#") >= 0, "import", fuel)
    )
    band = np.array([u.rsplit("_", 1)[-1] if "_" in u else "?" for u in uid])
    fam = np.where(np.char.startswith(band, "econ"), "econ", band)
    zones = list(st["iso_config"].zone_names)
    zone = np.asarray([zones[i] for i in np.asarray(fa.zone_idx)])
    CACHE.mkdir(exist_ok=True)
    np.savez(f, mc=mc, cap=cap, mg=mg, grp=grp, fam=fam, zone=zone)
    return mc, cap, mg, grp, fam, zone


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=[2022, 2023, 2025])
    ap.add_argument("--months", type=int, nargs="*", default=[6, 7, 8])
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    path = REPO / "results/phase0/miso/_miso287_class_gap.json"
    out = json.loads(path.read_text()) if path.exists() else {}
    for y in args.years:
        mc, cap, mg, grp, fam, zone = load_stack(
            y, run_year, _henry_hub_actual, _load_reference
        )
        flex = cap - mg

        s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"].pivot(index="hour", columns="zone", values="price")
        pm = s["MISO-Illinois"].to_numpy()
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[(ch["pass"] == "P1") & ~ch.klass.astype(str).isin(NON_LP)]
        q = ch.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
        month = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), "h")).month
        month = np.minimum(np.asarray(month), 12)
        sel = (np.arange(T) % 24 < NIGHT_H) & np.isin(month, args.months)
        t = np.where(sel)[0]

        p0, _, d0 = clear_all(mc, mg, flex, q)
        stack = (
            pd.DataFrame(d0[:, t].mean(1), index=grp).groupby(level=0)[0].sum().round(0)
        )
        cb = pd.read_parquet(KEEPER / f"hourly/class_band_hourly_{y}.parquet")
        cb = cb[(cb["pass"] == "P1") & cb.hour.isin(t)]
        p1 = (cb.groupby("klass", observed=True).mw.sum() / len(t)).round(0)
        p1.index = p1.index.astype(str)
        # Offered MW (flex above floor) BELOW the P1 price that P1 left idle,
        # and MW dispatched ABOVE the P1 price, by class and zone.
        idle_below = pd.Series(
            (flex[:, t] * (mc[:, t] < pm[None, t] - 0.5)).mean(1), index=grp
        )
        comp = pd.DataFrame(
            {"stack": stack.astype(float), "p1": p1.astype(float)}
        ).fillna(0.0)
        comp["p1_minus_stack"] = comp["p1"] - comp["stack"]
        cheap_offer_by_zone = (
            pd.DataFrame(
                {
                    "z": zone,
                    "g": grp,
                    "mw": (cap[:, t] * (mc[:, t] < pm[None, t] - 0.5)).mean(1),
                }
            )
            .groupby(["z", "g"])
            .mw.sum()
            .round(0)
        )
        out[str(y)] = {
            "months": args.months,
            "night_hours": int(len(t)),
            "p1_median": round(float(np.median(pm[t])), 2),
            "p0_stack_median": round(float(np.median(p0[t])), 2),
            "class_mw": {
                k: {kk: float(vv) for kk, vv in r.items()}
                for k, r in comp.sort_values("p1_minus_stack").iterrows()
                if max(abs(r["stack"]), abs(r["p1"])) > 50
            },
            "cap_offered_below_p1_price_by_zone_class": {
                f"{z}|{g}": float(v)
                for (z, g), v in cheap_offer_by_zone.items()
                if v > 200
            },
            "flex_offered_below_p1_price_total": round(float(idle_below.sum()), 0),
        }
        print(y, json.dumps(out[str(y)]), flush=True)
        path.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
