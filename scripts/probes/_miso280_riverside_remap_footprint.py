#!/usr/bin/env python3
"""miso-280 phase 0 (ZERO LP): footprint of the West Riverside CAMPD remap.

CAMPD files West Riverside Energy Center's two CTs (EIA plant 64020, COD 2020)
under the legacy Riverside Energy Center ORIS 55641 as units ``CT-03`` /
``CT-04``. The proposed rule-14 identity fix adds ``(55641, "CT-03") -> 64020``
and ``(55641, "CT-04") -> 64020`` to ``campd.CAMPD_UNIT_PLANT_REMAP``. This
probe measures what that entry would move BEFORE any solve, by monkeypatching
the dict (plus the two derived facility sets) in-process -- no file is edited.

Three fleet-only rebuilds (``run_year(fleet_only=True)``) of the designated
MISO keeper recipe (``results/calibration/miso279_span``) per year, each in its
own subprocess so no ``lru_cache`` leaks between variants:

* ``K`` -- the keeper as registered;
* ``L`` -- K + the remap patched in-process (LIVE paths only: whatever the
  fleet build reads through the remap at solve time);
* ``D`` -- L + an emulated RE-DERIVE of the committed CAMPD outage extracts:
  every ``campd-unit-outages*`` / ``campd-partial-outages*`` row keyed
  ``(55641, CT-03|CT-04)`` is relabelled ``facility_id=64020`` at read time
  (the derive re-keys ``facilityId`` through the remap before detection, and
  detection is per-unit on the unit's own capacity, so relabelling is the
  first-order re-derive; merit-panel and plant-level columns are not
  recomputed -- stated in the JSON). E923 fallback rows for 64020 are dropped
  in D (64020 becomes CEMS-visible).

Every ``read_csv`` / ``read_parquet`` path touched in K is logged, which is
the live-vs-derived census. The benchmark side calls
``run_calibration_full._campd_hourly_frame`` with and without the patch.

Usage::

    uv run python scripts/probes/_miso280_riverside_remap_footprint.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

KEEPER = REPO / "results/calibration/miso279_span"
OUT_JSON = REPO / "results/calibration/_miso280_riverside_remap_footprint.json"
YEARS = list(range(2019, 2026))
OLD, NEW, UNITS = 55641, 64020, ("CT-03", "CT-04")
PLANTS = (OLD, NEW)


def patch_remap() -> None:
    """Add the two West Riverside entries to the live remap (in-process only)."""
    from market_sim.data import campd

    for u in UNITS:
        campd.CAMPD_UNIT_PLANT_REMAP[(OLD, u)] = NEW
    campd.CAMPD_SPLIT_FACILITIES = frozenset(f for f, _ in campd.CAMPD_UNIT_PLANT_REMAP)
    campd._CAMPD_REMAP_FACILITY_IDS = np.array(
        sorted(campd.CAMPD_SPLIT_FACILITIES), dtype=np.int64
    )
    campd._FACILITIES_NEEDING_UNIT_ROWS = (
        campd.CAMPD_SPLIT_FACILITIES | campd.CAMPD_STACK_DUPLICATE_FACILITIES
    )


READS: list[str] = []
RELABELLED: dict[str, int] = {}


def instrument(relabel: bool) -> None:
    """Log every pandas CSV/parquet read; optionally relabel outage rows (D)."""
    _csv, _pq = pd.read_csv, pd.read_parquet

    def _fix(df, path: str):
        name = Path(path).name
        if not relabel or not isinstance(df, pd.DataFrame):
            return df
        if not (
            name.startswith("campd-unit-outages")
            or name.startswith("campd-partial-outages")
        ):
            return df
        if "facility_id" not in df.columns or "unit_id" not in df.columns:
            return df
        fid = pd.to_numeric(df["facility_id"], errors="coerce")
        uid = df["unit_id"].astype(str).str.strip()
        m = (fid == OLD) & uid.isin(UNITS)
        e923 = (fid == NEW) & (uid == "E923")
        if m.any() or e923.any():
            df = df.loc[~e923.to_numpy()].copy()
            m = m.loc[df.index]
            df.loc[m, "facility_id"] = NEW
            if "facility_name" in df.columns:
                df.loc[m, "facility_name"] = "West Riverside Energy Center"
            RELABELLED[name] = int(m.sum()) * 1000 + int(e923.sum())
        return df

    def read_csv(path, *a, **k):
        READS.append(str(path))
        return _fix(_csv(path, *a, **k), str(path))

    def read_parquet(path, *a, **k):
        READS.append(str(path))
        return _fix(_pq(path, *a, **k), str(path))

    pd.read_csv = read_csv
    pd.read_parquet = read_parquet


def fleet_one(year: int, variant: str) -> dict:
    """Fleet-only rebuild for one (year, variant); per-plant and class sums."""
    instrument(relabel=(variant == "D"))
    if variant in ("L", "D"):
        patch_remap()
    from scripts.probes import _miso271_cc_decomp as dec
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    hh = _henry_hub_actual(_load_reference(), year)
    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, {}))
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    av = np.asarray(fa.availability, dtype=float)
    avail = (pmax[:, None] * av).sum(axis=1) if av.ndim == 2 else pmax * av * 8760
    mg = (
        np.clip(np.asarray(fa.min_gen, dtype=float), 0, None).sum(axis=1)
        if fa.min_gen is not None
        else np.zeros(len(pmax))
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
        }
    )
    plants = {
        str(p): [
            {
                "unit": r.unit_id,
                "group": r.group,
                "pmax": round(r.pmax, 1),
                "avail_twh": round(r.avail_twh, 4),
                "floor_twh": round(r.floor_twh, 4),
                "hr": round(r.hr, 4),
            }
            for r in df[df.plant_code == p].itertuples()
        ]
        for p in PLANTS
    }
    by_group = df.groupby("group")[["avail_twh", "floor_twh"]].sum().round(5)
    reads = sorted({r for r in READS if "data/" in r or "results/" in r})
    return {
        "plants": plants,
        "by_group": by_group.to_dict(orient="index"),
        "reads": reads,
        "relabelled": RELABELLED,
    }


def bench_one(year: int, patched: bool) -> dict:
    """Benchmark CAMPD net frame (``_campd_hourly_frame``) per plant, TWh."""
    if patched:
        patch_remap()
    from scripts import run_calibration_full as rcf  # type: ignore

    fac = rcf._parasitic_factor_map()
    fr = rcf._campd_hourly_frame(year, "MISO", fac, 8760)
    by = fr.groupby("plant_id")["net_mw"].sum() / 1e6 if fr is not None else pd.Series()
    return {
        "plants_twh": {str(p): round(float(by.get(p, 0.0)), 4) for p in PLANTS},
        "total_twh": round(float(by.sum()), 4),
        "factor": {str(p): fac.get(p) for p in PLANTS},
        "n_plants": int(len(by)),
    }


def identity() -> dict:
    """CAMPD gross by unit, EIA-923 net, EIA-860 vintage rows for both plants."""
    out: dict = {"campd_gross_twh": {}, "eia923_net_twh": {}, "eia860": {}}
    for y in YEARS:
        d = pd.read_parquet(REPO / f"data/raw/campd-unit-level/WI_{y}.parquet")
        d = d[pd.to_numeric(d.facilityId, errors="coerce") == OLD]
        out["campd_gross_twh"][str(y)] = {
            str(k): round(float(v) / 1e6, 4)
            for k, v in d.groupby("unitId").grossLoad.sum().items()
        }
    e = pd.read_csv(
        REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
    )
    e = e[e.plant_id.isin(PLANTS)]
    for (p, y), v in e.groupby(["plant_id", "year"]).net_generation_mwh.sum().items():
        out["eia923_net_twh"].setdefault(str(y), {})[str(p)] = round(float(v) / 1e6, 4)
    for v in range(2018, 2025):
        g = pd.read_parquet(
            REPO / f"data/raw/eia-860/vintage_{v}/eia860_generator_operable.parquet"
        )
        g = g[pd.to_numeric(g["Plant Code"], errors="coerce").isin(PLANTS)]
        out["eia860"][str(v)] = [
            [
                int(r["Plant Code"]),
                str(r["Generator ID"]),
                str(r["Prime Mover"]),
                float(r["Nameplate Capacity (MW)"]),
            ]
            for _, r in g.iterrows()
        ]
    return out


def main() -> int:
    """CLI entry point: driver, or one worker (``--worker``)."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--worker", choices=["fleet", "bench"])
    ap.add_argument("--year", type=int)
    ap.add_argument("--variant", default="K")
    ap.add_argument("--years", nargs="+", type=int, default=YEARS)
    args = ap.parse_args()
    if args.worker == "fleet":
        print("@@" + json.dumps(fleet_one(args.year, args.variant)))
        return 0
    if args.worker == "bench":
        print("@@" + json.dumps(bench_one(args.year, args.variant == "P")))
        return 0

    def run(*extra: str) -> dict:
        cp = subprocess.run(
            [sys.executable, __file__, *extra], capture_output=True, text=True, cwd=REPO
        )
        line = [x for x in cp.stdout.splitlines() if x.startswith("@@")]
        if not line:
            return {"error": cp.stderr[-3000:]}
        return json.loads(line[-1][2:])

    res: dict = {"identity": identity(), "fleet": {}, "bench": {}}
    for y in args.years:
        res["fleet"][str(y)] = {
            v: run("--worker", "fleet", "--year", str(y), "--variant", v)
            for v in ("K", "L", "D")
        }
        res["bench"][str(y)] = {
            v: run("--worker", "bench", "--year", str(y), "--variant", v)
            for v in ("K", "P")
        }
        f = res["fleet"][str(y)]
        print(
            y,
            {v: f[v].get("plants", f[v].get("error", "")[-300:]) for v in f},
            flush=True,
        )
        OUT_JSON.write_text(json.dumps(res, indent=1, sort_keys=True))
    res["notes"] = {
        "D_is_emulated": "relabel of committed outage rows, not a re-run of the derive: "
        "merit-panel layup split, plant_capacity_mw / peer columns not recomputed",
    }
    OUT_JSON.write_text(json.dumps(res, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
