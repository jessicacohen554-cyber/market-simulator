#!/usr/bin/env python3
"""miso-282 phase 0 (ZERO LP): what does ``admit_standby_units`` add to MISO's fleet?

Two fleet-only rebuilds of the designated keeper's recipe
(``results/calibration/miso280_span``) per year — as registered, and with
``admit_standby_units=True`` (EIA-860 ``SB`` generators admitted by status
alone; the NWPP-NEXT-5 mechanism, MISO cell ``U``) — and a per-unit diff.

For every LP unit present in only one variant (or whose capacity moved) it
records plant, class, zone, pmax, available MWh and the price-taker envelope
at the keeper's own committed P1 zone prices,

    E = sum_t max(floor[t], pmax*avail[t] * 1[price_z[t] >= mc[t]])

which bounds from above what the LP could dispatch on the added capacity if
prices did not move. It is an estimate, not a solve (rule 29 clause 0).

Rule 13: status is a published ex-ante EIA-860 field; nothing measured about
the outcome selects a unit. Rule 23: artifacts are read, never re-derived.

Usage::

    uv run python scripts/probes/_miso282_standby_delta.py --year 2021 --out-dir X
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

KEEPER = REPO / "results/calibration/miso280_span"
FLIP = {"admit_standby_units": True}


def unit_table(year: int, flips: dict, price: pd.DataFrame) -> pd.DataFrame:
    """Fleet-only rebuild -> one row per LP unit with its price-taker envelope."""
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    hh = _henry_hub_actual(_load_reference(), year)
    st = run_year(
        year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, flips)
    )
    fa, isoc = st["fleet_arrays"], st["iso_config"]
    n = len(fa.pmax)
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    if avail.ndim == 1:
        avail = np.repeat(avail[:, None], 8760, axis=1)
    cap = pmax[:, None] * avail
    mg = (
        np.clip(np.asarray(fa.min_gen, dtype=float), 0.0, None)
        if fa.min_gen is not None
        else np.zeros((n, 8760))
    )
    mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
    if mc.shape[1] == 1:
        mc = np.repeat(mc, 8760, axis=1)
    zone_names = list(isoc.zone_names)
    zone = np.array([zone_names[i] for i in np.asarray(fa.zone_idx).astype(int)])
    pz = np.vstack(
        [price[z].to_numpy() if z in price else np.full(8760, np.nan) for z in zone]
    )
    env = np.maximum(mg, cap * (pz >= mc)).sum(axis=1)
    return pd.DataFrame(
        {
            "unit_id": list(fa.unit_ids),
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "group": np.asarray(list(fa.plant_group)),
            "zone": zone,
            "pmax": pmax,
            "avail_twh": cap.sum(axis=1) / 1e6,
            "floor_twh": mg.sum(axis=1) / 1e6,
            "mc_mean": mc.mean(axis=1),
            "env_twh": env / 1e6,
        }
    )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    dec.KEEPER = KEEPER
    y = args.year
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sysd = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    price = sysd.pivot(index="hour", columns="zone", values="price").sort_index()
    base = unit_table(y, {}, price)
    arm = unit_table(y, FLIP, price)
    m = base.merge(
        arm, on="unit_id", how="outer", suffixes=("_b", "_a"), indicator=True
    )
    for c in ("pmax", "avail_twh", "floor_twh", "env_twh"):
        m[f"d_{c}"] = m[f"{c}_a"].fillna(0.0) - m[f"{c}_b"].fillna(0.0)
    for c in ("plant_code", "group", "zone"):
        m[c] = m[f"{c}_a"].combine_first(m[f"{c}_b"])
    moved = m[
        (m._merge != "both") | (m.d_pmax.abs() > 1e-6) | (m.d_avail_twh.abs() > 1e-6)
    ]
    moved.to_parquet(out / f"standby_delta_{y}.parquet", index=False)
    by = (
        moved.groupby(["group", "zone"])[
            ["d_pmax", "d_avail_twh", "d_floor_twh", "d_env_twh"]
        ]
        .sum()
        .round(3)
    )
    plants = (
        moved.groupby(["plant_code", "group", "zone"])[["d_pmax", "d_env_twh"]]
        .sum()
        .round(3)
        .sort_values("d_pmax", ascending=False)
        .reset_index()
    )
    summ = {
        "year": y,
        "n_units_base": int(len(base)),
        "n_units_arm": int(len(arm)),
        "d_pmax_mw": round(float(moved.d_pmax.sum()), 1),
        "d_env_twh": round(float(moved.d_env_twh.sum()), 3),
        "by_group_zone": json.loads(by.reset_index().to_json(orient="records")),
        "plants": json.loads(plants.to_json(orient="records")),
    }
    (out / f"standby_delta_{y}.json").write_text(json.dumps(summ, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summ.items() if k != "plants"}, indent=1))
    print(plants.head(20).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
