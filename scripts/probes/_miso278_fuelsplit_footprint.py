#!/usr/bin/env python3
"""miso-278 phase 0 (ZERO LP): floor footprint of the unit-fuel-split tranche companions.

Fleet-only rebuilds (``run_year(fleet_only=True)``) of the designated MISO
keeper's recipe (``results/calibration/miso277_span``) per year, twice:

* ``K`` — the keeper as registered (incumbent ``thermal_tranches_MISO.csv`` family);
* ``F`` — the same recipe reading the four ``-fuelsplit-`` companions written by
  ``derive_thermal_tranches.py --unit-fuel-split`` in place of the incumbents.

``F`` is produced WITHOUT any ScenarioConfig change: ``campd_bins.PROCESSED_DIR``
is pointed at a scratch directory of symlinks to every processed artifact, in
which only the four tranche-family files are swapped for their companions. So
the only thing that differs between ``K`` and ``F`` is the artifact bytes -- the
exact single delta a gated arm would carry.

Per (year, variant, LP unit) it records plant, class, pmax, floor MWh
(``min_gen`` summed over the year) and the floor MWh supplied by each mechanism
id, and writes one parquet per (year, variant) plus a JSON summary.

Usage::

    uv run python scripts/probes/_miso278_fuelsplit_footprint.py \
        --years 2019 2020 2021 2022 2023 2024 2025 --out-dir X
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402

KEEPER = REPO / "results/calibration/miso277_span"
FAMILY = (
    "thermal_tranches_MISO.csv",
    "thermal_tranches_online_frac_by_year_MISO.csv",
    "thermal_tranches_p25_level_mw_MISO.csv",
    "thermal_tranches_oom_level_mw_MISO.csv",
)


def _companion(name: str) -> str:
    """``thermal_tranches_X_MISO.csv`` -> ``thermal_tranches_X-fuelsplit-MISO.csv``."""
    stem, rest = name.rsplit("_", 1)
    return f"{stem}-fuelsplit-{rest}"


def _swap_dir(scratch: Path) -> Path:
    """Build a symlink mirror of PROCESSED_DIR with the four companions swapped in."""
    from market_sim.config.paths import PROCESSED_DIR

    d = scratch / "processed_fuelsplit"
    d.mkdir(parents=True, exist_ok=True)
    for f in PROCESSED_DIR.iterdir():
        link = d / f.name
        if link.is_symlink() or link.exists():
            link.unlink()
        src = PROCESSED_DIR / (_companion(f.name) if f.name in FAMILY else f.name)
        if not src.exists():
            raise SystemExit(f"missing companion {src}")
        os.symlink(src.resolve(), link)
    return d


def _clear_caches() -> None:
    """Drop every lru_cache in campd_bins so the next build re-reads artifacts."""
    from market_sim.data.fleet import campd_bins

    for obj in vars(campd_bins).values():
        if hasattr(obj, "cache_clear"):
            obj.cache_clear()


def unit_floors(year: int, hh: float) -> pd.DataFrame:
    """Fleet-only rebuild of the keeper recipe; one row per LP unit with floor MWh."""
    from scripts.run_calibration import run_year

    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, {}))
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    mg = (
        np.asarray(fa.min_gen, dtype=float)
        if fa.min_gen is not None
        else np.zeros((len(pmax), 8760))
    )
    mech = (
        np.asarray(fa.min_gen_mechanism)
        if fa.min_gen_mechanism is not None
        else np.zeros(mg.shape, dtype=np.int8)
    )
    rows = {
        "unit_id": list(fa.unit_ids),
        "plant_code": np.asarray(fa.plant_code),
        "group": list(fa.plant_group) if fa.plant_group is not None else "",
        "pmax": pmax,
        "floor_mwh": np.clip(mg, 0.0, None).sum(axis=1),
    }
    for m in np.unique(mech[mech > 0]):
        rows[f"mech_{int(m)}_mwh"] = np.where(mech == m, np.clip(mg, 0, None), 0).sum(
            axis=1
        )
    return pd.DataFrame(rows)


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2019])
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    from market_sim.data.fleet import campd_bins
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    swap = _swap_dir(out)
    base = campd_bins.PROCESSED_DIR
    ref = _load_reference()
    summary: dict = {}
    for y in args.years:
        hh = _henry_hub_actual(ref, y)
        for tag, pdir in (("K", base), ("F", swap)):
            campd_bins.PROCESSED_DIR = pdir
            _clear_caches()
            df = unit_floors(y, hh)
            df.to_parquet(out / f"{y}_{tag}.parquet", index=False)
            st = df[df["group"] == "ST_GAS"]
            summary.setdefault(str(y), {})[tag] = {
                "st_gas_mw": round(float(st.pmax.sum()), 1),
                "st_gas_floor_twh": round(float(st.floor_mwh.sum()) / 1e6, 4),
                "st_gas_floored_plants": sorted(
                    int(c) for c in st.loc[st.floor_mwh > 0, "plant_code"].unique()
                ),
                "floor_twh_by_group": {
                    str(g): round(float(s.floor_mwh.sum()) / 1e6, 4)
                    for g, s in df.groupby("group")
                },
            }
            print(json.dumps({"year": y, tag: summary[str(y)][tag]}), flush=True)
        campd_bins.PROCESSED_DIR = base
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
