#!/usr/bin/env python3
"""miso-280 (ZERO LP): fleet footprint of ``campd_split_remap_companions``.

Fleet-only rebuilds (``run_year(fleet_only=True)``) of the designated MISO
keeper's recipe (``results/calibration/miso279_span``) per year 2019-2025,
twice: ``K`` the keeper as registered, ``A`` the same recipe with the single
delta ``campd_split_remap_companions=True`` (reads the seven ``-splitremap-``
companions: std / short-gas / maxgen unit-outage extracts, the measured CC heat
rates and the four ``-fuelsplit-stcov-`` tranche files). Records, per year:
availability and floor TWh by class (any class that moves is listed), and for
Riverside 55641 / West Riverside 64020 every LP unit's pmax, availability TWh,
floor TWh, heat rate and mean marginal cost.

Usage::

    uv run python scripts/probes/_miso280_splitremap_footprint.py
    uv run python scripts/probes/_miso280_splitremap_footprint.py --years 2023

Writes ``results/phase0/miso/_miso280_splitremap_footprint.json``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

KEEPER = REPO / "results/calibration/miso279_span"
OUT_JSON = REPO / "results/phase0/miso/_miso280_splitremap_footprint.json"
YEARS = list(range(2019, 2026))
DELTA = {"campd_split_remap_companions": True}
PLANTS = (55641, 64020)


def fleet_one(year: int, flips: dict) -> dict:
    """Fleet-only rebuild for one (year, variant): class sums and plant units."""
    import numpy as np
    import pandas as pd

    from scripts.probes import _miso271_cc_decomp as dec
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    hh = _henry_hub_actual(_load_reference(), year)
    st = run_year(
        year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, flips)
    )
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    av = np.asarray(fa.availability, dtype=float)
    avail = (pmax[:, None] * av).sum(axis=1) if av.ndim == 2 else pmax * av * 8760
    mg = (
        np.clip(np.asarray(fa.min_gen, dtype=float), 0, None).sum(axis=1)
        if fa.min_gen is not None
        else np.zeros(len(pmax))
    )
    mc = st.get("mc_base")
    mc_mean = (
        np.asarray(mc, dtype=float).reshape(len(pmax), -1).mean(axis=1)
        if mc is not None
        else np.full(len(pmax), np.nan)
    )
    df = pd.DataFrame(
        {
            "unit_id": list(fa.unit_ids),
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "group": list(fa.plant_group),
            "pmax": pmax,
            "avail_twh": avail / 1e6,
            "floor_twh": mg / 1e6,
            "hr": np.asarray(fa.heat_rate, dtype=float),
            "mc_mean": mc_mean,
        }
    )
    plants = {
        str(p): [
            {
                "unit": r.unit_id,
                "group": r.group,
                "pmax": round(float(r.pmax), 1),
                "avail_twh": round(float(r.avail_twh), 4),
                "floor_twh": round(float(r.floor_twh), 4),
                "hr": round(float(r.hr), 4),
                "mc_mean": round(float(r.mc_mean), 3),
            }
            for r in df[df.plant_code == p].itertuples()
        ]
        for p in PLANTS
    }
    by_group = df.groupby("group")[["avail_twh", "floor_twh"]].sum()
    per_unit = {
        str(u): [round(float(a), 6), round(float(f), 6), round(float(h), 6)]
        for u, a, f, h in zip(df.unit_id, df.avail_twh, df.floor_twh, df.hr)
    }
    return {
        "plants": plants,
        "by_group": {
            g: {k: round(float(v), 5) for k, v in row.items()}
            for g, row in by_group.to_dict(orient="index").items()
        },
        "per_unit": per_unit,
    }


def _worker(year: int, variant: str) -> dict:
    cp = subprocess.run(
        [
            sys.executable,
            __file__,
            "--worker",
            "--year",
            str(year),
            "--variant",
            variant,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    line = next(ln for ln in cp.stdout.splitlines() if ln.startswith("@@"))
    return json.loads(line[2:])


def summarize(year: int, k: dict, a: dict) -> dict:
    """The K -> A delta for one year."""
    groups = sorted(set(k["by_group"]) | set(a["by_group"]))
    zero = {"avail_twh": 0.0, "floor_twh": 0.0}
    moved = {}
    for g in groups:
        kk, aa = k["by_group"].get(g, zero), a["by_group"].get(g, zero)
        d_av = round(aa["avail_twh"] - kk["avail_twh"], 4)
        d_fl = round(aa["floor_twh"] - kk["floor_twh"], 4)
        if abs(d_av) > 1e-4 or abs(d_fl) > 1e-4:
            moved[g] = {"avail_twh_delta": d_av, "floor_twh_delta": d_fl}
    units_moved = sorted(
        u
        for u in set(k["per_unit"]) | set(a["per_unit"])
        if k["per_unit"].get(u) != a["per_unit"].get(u)
    )
    return {
        "cc_regular_avail_twh": [
            k["by_group"].get("CC_REGULAR", zero)["avail_twh"],
            a["by_group"].get("CC_REGULAR", zero)["avail_twh"],
        ],
        "classes_moved": moved,
        "units_moved": units_moved,
        "plants": {"K": k["plants"], "A": a["plants"]},
    }


def main() -> int:
    """CLI entry point: driver, or one worker (``--worker``)."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--year", type=int)
    ap.add_argument("--variant", choices=["K", "A"], default="K")
    ap.add_argument("--years", nargs="+", type=int, default=YEARS)
    ap.add_argument("--jobs", type=int, default=2)
    args = ap.parse_args()
    if args.worker:
        flips = DELTA if args.variant == "A" else {}
        print("@@" + json.dumps(fleet_one(args.year, flips)), flush=True)
        return 0
    tasks = [(y, v) for y in args.years for v in ("K", "A")]
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        res = dict(zip(tasks, ex.map(lambda t: _worker(*t), tasks)))
    out = {
        "keeper": str(KEEPER.relative_to(REPO)),
        "delta": DELTA,
        "years": {
            str(y): summarize(y, res[(y, "K")], res[(y, "A")]) for y in args.years
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=1, sort_keys=True))
    for y in args.years:
        s = out["years"][str(y)]
        print(y, s["cc_regular_avail_twh"], s["classes_moved"], len(s["units_moved"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
