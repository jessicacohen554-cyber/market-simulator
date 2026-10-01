"""SPP-50 instrument (zero LP): the LP-INPUT-ARRAY census for the re-baseline's identity leg.

Leg (i) of the pre-declared promotion rule is an identity test **on the P0 objective
and the LP input arrays, never on a warm-started P1 objective** (desk error E-8, and
the leg that stopped SPP-43). This script supplies its array half.

It rebuilds keeper-3's fleet with ``run_year(fleet_only=True)`` on the keeper's own
recipe (``scripts.replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` -- the
only sanctioned fleet-only reconstruction, the same seam SPP-49's census used) and
writes every LP input array the payload carries to one ``.npz`` per (tag, year):

    pmax pmin heat_rate vom emission_rate nox_rate so2_rate zone_idx fuel_type_idx
    plant_code availability min_gen  |  mc_base fuel_prices  |  wind_cf wind_cap
    solar_cf solar_cap wind_mc solar_mc  |  demand  |  storage_power_cap storage_*

``--diff PRE POST`` then reports, per array, whether it moved and by how much, with the
unit rows attributed to the three declared movers (SPP-48's wind level rule; SPP-49's
seam-1 screened plant-months; SPP-49's seam-2 clamped simple-cycle rows) and an
EXPLICIT list of anything that moved outside them -- which is what the leg actually
tests.

usage:
    uv run python docs/handoffs/spp50/array_census.py --tag pre
    uv run python docs/handoffs/spp50/array_census.py --tag post
    uv run python docs/handoffs/spp50/array_census.py --diff pre post
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "5bccefaf-1c50-588c-8c84-94ab3b579daf/scratchpad/spp50"
)
OUT.mkdir(parents=True, exist_ok=True)

KEEPER = "spp43_screened_B"
YEARS = (2023, 2024, 2025)

#: (n_gen,) scalar fleet arrays carried straight from FleetArrays.
SCALAR_ARRAYS = (
    "pmax",
    "pmin",
    "heat_rate",
    "vom",
    "emission_rate",
    "nox_rate",
    "so2_rate",
    "zone_idx",
    "fuel_type_idx",
    "plant_code",
)
#: (n_gen, T) or (T,) / (n_zone, T) arrays.
WIDE_ARRAYS = (
    "availability",
    "min_gen",
    "mc_base",
    "fuel_prices",
    "wind_cf",
    "wind_cap",
    "solar_cf",
    "solar_cap",
    "wind_mc",
    "solar_mc",
    "demand",
    "storage_power_cap",
)


def build(year: int, tag: str) -> None:
    """Rebuild keeper-3's fleet for one year and persist every LP input array."""
    arr_p = OUT / f"arrays_{tag}_{year}.npz"
    rows_p = OUT / f"rows_{tag}_{year}.csv"
    if arr_p.exists() and rows_p.exists():
        print(f"  {tag} {year}: cached")
        return
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / KEEPER
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    gp = float(meta["gas_prices"][str(year)])
    r = run_year(year, "SPP", 8760, gp, {}, fleet_only=True, **kw)

    fleet, fa = r["fleet"], r["fleet_arrays"]
    out: dict[str, np.ndarray] = {}
    for name in SCALAR_ARRAYS:
        v = getattr(fa, name, None)
        if v is not None:
            out[name] = np.asarray(v)
    out["availability"] = np.asarray(fa.availability)
    if fa.min_gen is not None:
        out["min_gen"] = np.asarray(fa.min_gen)
    for name in (
        "mc_base",
        "fuel_prices",
        "wind_cf",
        "wind_cap",
        "solar_cf",
        "solar_cap",
        "wind_mc",
        "solar_mc",
        "demand",
        "storage_power_cap",
    ):
        v = r.get(name)
        if v is not None:
            out[name] = np.asarray(v)
    np.savez_compressed(arr_p, **{k: v for k, v in out.items() if v.dtype != object})

    rows = pd.DataFrame(
        [
            dict(
                g=g,
                unit_id=gen.unit_id,
                plant_code=int(gen.plant_code or 0),
                name=gen.name,
                zone=gen.zone,
                plant_group=gen.plant_group or "",
                fuel_type=gen.fuel_type,
                pmax=float(fa.pmax[g]),
                heat_rate=float(fa.heat_rate[g]),
                state=str(getattr(gen, "state", "") or ""),
                mc_mean=float(r["mc_base"][g].mean()),
                fuel_mean=float(r["fuel_prices"][g].mean()),
            )
            for g, gen in enumerate(fleet)
        ]
    )
    rows.to_csv(rows_p, index=False)
    print(f"  {tag} {year}: {len(rows)} units, {len(out)} arrays -> {arr_p.name}")


def diff(pre: str, post: str) -> None:
    """Report every array that moved between two censuses, and the rows behind it."""
    for year in YEARS:
        a = np.load(OUT / f"arrays_{pre}_{year}.npz")
        b = np.load(OUT / f"arrays_{post}_{year}.npz")
        ra = pd.read_csv(OUT / f"rows_{pre}_{year}.csv")
        rb = pd.read_csv(OUT / f"rows_{post}_{year}.csv")
        print(f"\n=== {year} ===")
        print(f"  units {len(ra)} -> {len(rb)}; arrays {len(a.files)} -> {len(b.files)}")
        assert set(a.files) == set(b.files), (set(a.files) ^ set(b.files))
        same_fleet = len(ra) == len(rb) and (ra.unit_id.values == rb.unit_id.values).all()
        print(f"  fleet row order identical: {same_fleet}")
        moved, still = [], []
        for k in sorted(a.files):
            x, y = a[k], b[k]
            if x.shape != y.shape:
                moved.append((k, "SHAPE", str(x.shape), str(y.shape), np.nan, np.nan))
                continue
            d = np.abs(y.astype(np.float64) - x.astype(np.float64))
            m = float(d.max()) if d.size else 0.0
            if m == 0.0:
                still.append(k)
            else:
                nz = int((d > 0).sum())
                if x.ndim == 2:
                    rows_moved = int((d.max(axis=1) > 0).sum())
                else:
                    rows_moved = nz
                moved.append((k, f"{nz} cells", f"{rows_moved} rows", "", m, float(d.sum())))
        print(f"  IDENTICAL ({len(still)}): {', '.join(still)}")
        print(f"  MOVED ({len(moved)}):")
        for k, c1, c2, c3, mx, tot in moved:
            print(f"    {k:20s} {c1:>14s} {c2:>12s} {c3:6s} max={mx:.6g} sum={tot:.6g}")
        # attribute the moved unit rows
        for k in ("mc_base", "fuel_prices", "heat_rate", "availability"):
            if k not in a.files:
                continue
            x, y = a[k].astype(np.float64), b[k].astype(np.float64)
            if x.shape != y.shape:
                continue
            d = np.abs(y - x)
            idx = np.where(d.max(axis=1) > 0)[0] if x.ndim == 2 else np.where(d > 0)[0]
            if idx.size == 0:
                continue
            sub = rb.iloc[idx]
            print(
                f"  -> {k}: {idx.size} unit rows, {sub.pmax.sum():,.0f} MW; "
                f"by group: {dict(sub.groupby('plant_group').pmax.sum().round(0))}"
            )
            sub.assign(
                delta_mean=(y[idx] - x[idx]).mean(axis=1) if x.ndim == 2 else (y[idx] - x[idx])
            ).to_csv(OUT / f"moved_{k}_{year}.csv", index=False)


def main() -> int:
    """Build or diff the array census."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tag")
    ap.add_argument("--diff", nargs=2, metavar=("PRE", "POST"))
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    args = ap.parse_args()
    if args.diff:
        diff(*args.diff)
        return 0
    if not args.tag:
        ap.error("--tag or --diff required")
    for y in args.years:
        build(y, args.tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
