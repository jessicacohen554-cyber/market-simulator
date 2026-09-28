#!/usr/bin/env python3
"""miso-279 phase 0 (ZERO LP): who carries the C1 ST_GAS held-out-year gap?

For each year of the MISO keeper span (``results/calibration/miso278_span``),
joins three measured/committed sources at plant grain:

* a fleet-only rebuild of the keeper recipe (``run_year(fleet_only=True)``):
  every LP unit's plant, class, pmax and floor MWh;
* CAMPD unit-level gross load of **gas-fired steam** units (``primaryFuelInfo``
  names gas and not coal; ``unitType`` is not a combined-cycle or combustion
  turbine) -- CEMS's own per-unit fuel and unit-type attributes;
* the keeper's committed run payload (per-plant annual model TWh).

and flags whether the keeper's tranche artifact
(``thermal_tranches-fuelsplit-MISO.csv``) carries an ST_GAS row for the plant.

Rule 13: nothing here is fed back into a solve; this sizes a population, it
does not choose a value. Rule 23: the artifact is read, never re-derived.

Usage::

    uv run python scripts/probes/_miso279_stgas_coverage_census.py --out-dir X
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402

KEEPER = REPO / "results/calibration/miso278_span"
KEEPER_ID = "2026-09-27-miso-278-fuelsplit"
ARTIFACT = REPO / "data/raw/_processed-legacy/thermal_tranches-fuelsplit-MISO.csv"
PAYLOAD = REPO / f"frontend/data/backcast/runs/{KEEPER_ID}.js"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
NON_STEAM = ("combined cycle", "combustion turbine", "combined-cycle")


def payload_model_twh() -> dict[int, dict[str, float]]:
    """``{year: {payload key: model TWh}}`` from the keeper's committed run payload.

    Keys are ``"<plant>"`` or ``"<plant>:<class>"`` (split plants).
    """
    s = PAYLOAD.read_text()
    blob = re.search(r'="([^"]+)"', s).group(1)
    d = json.loads(gzip.decompress(base64.b64decode(blob)))
    return {
        int(y): {str(k): float(r.get("m_ann") or 0.0) for k, r in yd["plants"].items()}
        for y, yd in d["years"].items()
    }


def campd_gas_steam(year: int) -> pd.DataFrame:
    """Gross TWh per (facility, unit) of CEMS gas-fired steam units in MISO states."""
    from market_sim.config.paths import CAMPD_UNIT_LEVEL_DIR
    from market_sim.data import campd

    out = []
    for st in campd.states_for_iso("MISO"):
        path = CAMPD_UNIT_LEVEL_DIR / f"{st}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path,
            columns=[
                "facilityId",
                "facilityName",
                "unitId",
                "grossLoad",
                "primaryFuelInfo",
                "unitType",
            ],
        )
        fuel = df["primaryFuelInfo"].astype(str)
        ut = df["unitType"].astype(str).str.lower()
        gas = fuel.str.contains("Gas") & ~fuel.str.contains("Coal")
        steam = ~ut.str.contains("|".join(NON_STEAM))
        g = df[gas & steam]
        if g.empty:
            continue
        agg = (
            g.groupby(["facilityId", "facilityName", "unitId"], as_index=False)[
                "grossLoad"
            ]
            .sum()
            .assign(state=st)
        )
        out.append(agg)
    res = pd.concat(out, ignore_index=True)
    res["twh"] = res["grossLoad"] / 1e6
    return res.drop(columns="grossLoad")


def fleet_units(year: int, hh: float) -> pd.DataFrame:
    """Fleet-only rebuild of the keeper recipe; one row per LP unit."""
    from scripts.run_calibration import run_year

    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, {}))
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    mg = (
        np.asarray(fa.min_gen, dtype=float)
        if fa.min_gen is not None
        else np.zeros((len(pmax), 8760))
    )
    return pd.DataFrame(
        {
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "group": list(fa.plant_group),
            "pmax": pmax,
            "floor_twh": np.clip(mg, 0.0, None).sum(axis=1) / 1e6,
        }
    )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=YEARS)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    art = pd.read_csv(ARTIFACT)
    stgas_rows = set(art.loc[art.plant_group == "ST_GAS", "plant_code"].astype(int))
    rows_by_plant = (
        art.groupby("plant_code")["plant_group"]
        .apply(lambda s: "/".join(sorted(s)))
        .to_dict()
    )
    model = payload_model_twh()
    ref = _load_reference()
    frames = []
    for y in args.years:
        fl = fleet_units(y, _henry_hub_actual(ref, y))
        fl.to_parquet(out / f"fleet_{y}.parquet", index=False)
        cg = campd_gas_steam(y)
        cg.to_parquet(out / f"campd_gs_{y}.parquet", index=False)
        by_fac = cg.groupby(["facilityId", "facilityName"], as_index=False)["twh"].sum()
        grp = fl.groupby("plant_code").apply(
            lambda s: "/".join(sorted(set(s["group"])))
        )
        st = (
            fl[fl.group == "ST_GAS"]
            .groupby("plant_code")
            .agg(st_pmax=("pmax", "sum"), st_floor_twh=("floor_twh", "sum"))
        )
        plants = set(by_fac.facilityId.astype(int)) | set(st.index)
        name = dict(zip(by_fac.facilityId.astype(int), by_fac.facilityName))
        cgt = dict(zip(by_fac.facilityId.astype(int), by_fac.twh))
        for pc in sorted(plants):
            frames.append(
                {
                    "year": y,
                    "plant_code": pc,
                    "name": name.get(pc, ""),
                    "campd_gas_steam_twh": round(cgt.get(pc, 0.0), 4),
                    "fleet_groups": grp.get(pc, "<not in fleet>"),
                    "st_gas_pmax": round(float(st.st_pmax.get(pc, 0.0)), 1),
                    "st_gas_floor_twh": round(float(st.st_floor_twh.get(pc, 0.0)), 4),
                    "artifact_rows": rows_by_plant.get(pc, ""),
                    "has_st_gas_row": pc in stgas_rows,
                    "model_plant_twh": round(
                        sum(
                            v
                            for k, v in model.get(y, {}).items()
                            if k.split(":")[0] == str(pc)
                        ),
                        4,
                    ),
                    "model_st_gas_key_twh": model.get(y, {}).get(f"{pc}:ST_GAS"),
                    "payload_keys": ",".join(
                        k for k in model.get(y, {}) if k.split(":")[0] == str(pc)
                    ),
                }
            )
        print(f"{y}: done", flush=True)
    df = pd.DataFrame(frames)
    df.to_csv(out / "census.csv", index=False)
    summ = {}
    for y, g in df.groupby("year"):
        norow = g[~g.has_st_gas_row & (g.campd_gas_steam_twh > 0.01)]
        summ[int(y)] = {
            "campd_gas_steam_twh_total": round(g.campd_gas_steam_twh.sum(), 3),
            "campd_gas_steam_twh_no_row": round(norow.campd_gas_steam_twh.sum(), 3),
            "no_row_in_fleet_as_st_gas_twh": round(
                norow[norow.st_gas_pmax > 0].campd_gas_steam_twh.sum(), 3
            ),
            "no_row_not_st_gas_in_fleet_twh": round(
                norow[norow.st_gas_pmax <= 0].campd_gas_steam_twh.sum(), 3
            ),
        }
    (out / "summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
