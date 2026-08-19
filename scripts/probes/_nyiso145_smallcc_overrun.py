#!/usr/bin/env python3
"""nyiso-145 — measure the NYISO small-merchant-CC over-dispatch, per plant.

Session nyiso-145, job 3. The handoff names plant 7314 (Richard M Flynn) as
"the bridge's single largest remaining D-4 unit-conduct failure" and asks why
the base-cost P0 pass runs it so much more than reality does. This probe
answers that by capturing the model's OWN P0 dispatch and the bridge floor it
produces, per LP row, and scoring both against the plant's measured output.

What it captures, by spying on ``pipeline.commitment._nyiso_gas_bridge_floor``
at the P0->P1 seam (no ``src/`` edit, no behaviour change):

* ``p0``     — the base-cost dispatch the bridge detector reads, ``(n_gen, T)``
* ``floor``  — the bridge floor that detector returns, ``(n_gen, T)``
* the fleet's identity arrays (plant code / class / zone / pmax)

and then reports, per plant:

* P0 energy vs the plant's own CAMPD-metered energy AND vs its EIA-923 annual
  net. The 923 leg matters because several of these plants are CT-ONLY CEMS
  reporters (only the combustion-turbine block reports; the steam turbine is
  absent), so their CAMPD series understates them by ~1.3-1.5x and a
  CAMPD-only ratio would overstate the over-run.
* the P0 run-pattern statistics the bridge detector actually consumes (run
  count, run-length quantiles, sub-4-hour run count), against the plant's own
  measured run pattern.
* the bridge floor volume, so the share of the over-run the bridge is
  responsible for is separated from the share the economic dispatch is.

DIAGNOSTIC PROBE ONLY. The solves are throwaway single-year replays of the
keeper recipe (rule 16's explicit carve-out for isolating a single-year
effect); nothing here is registered as a keeper. Every year read is 2023-2025
(rule 22; the holdout spend freeze is ACTIVE and untouched).

Usage::

    python scripts/probes/_nyiso145_smallcc_overrun.py [--year 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import collections
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from scripts.legitimacy_diagnostics import REBUILD_META_RENAMES  # noqa: E402
import scripts.run_calibration as RC  # noqa: E402
import market_sim.pipeline.commitment as PC  # noqa: E402

BUNDLE = REPO / "results/calibration/nyiso144_layup_arm"
OUT = REPO / "results/calibration/_nyiso145_smallcc_overrun.json"
# A unit counts as running when its dispatch exceeds this share of pmax — the
# bridge detector's own ``run_threshold_frac`` default, so the run pattern
# reported here is the pattern the detector saw.
RUN_THRESHOLD_FRAC = 0.05


def _kwargs(meta: dict) -> dict:
    """Return the ``run_year`` kwargs that reproduce *meta*'s recipe."""
    params = inspect.signature(RC.run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    out = {}
    for k, v in meta.items():
        k2 = REBUILD_META_RENAMES.get(k, k)
        if k2 in params and k2 not in skip:
            out[k2] = v
    return out


def _runs(flag: np.ndarray) -> list[tuple[int, int]]:
    """Return the ``[start, end)`` index pairs of each True run in *flag*."""
    idx = np.flatnonzero(np.diff(np.concatenate(([0], flag.astype(np.int8), [0]))) != 0)
    return list(zip(idx[0::2], idx[1::2]))


def _campd_plant_hourly(year: int) -> dict[str, np.ndarray]:
    """Return ``{plant_code: (T,) metered gross MW}`` for NYISO's CAMPD fleet."""
    df = pd.read_parquet(REPO / f"data/raw/campd-unit-level/NY_{year}.parquet")
    df = df[["facilityId", "date", "hour", "grossLoad"]].copy()
    g = df.groupby(["facilityId", "date", "hour"], as_index=False)["grossLoad"].sum()
    out: dict[str, np.ndarray] = {}
    for pid, sub in g.groupby("facilityId"):
        sub = sub.sort_values(["date", "hour"])
        out[str(pid)] = sub["grossLoad"].fillna(0.0).to_numpy(dtype=float)
    return out


def _e923_net(year: int) -> dict[int, float]:
    """Return ``{plant_code: EIA-923 annual net MWh}`` for the NYISO BA."""
    path = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
    df = pd.read_parquet(path)
    df = df[(df.year == year) & (df.ba_code == "NYIS")]
    return df.groupby("plant_id")["netgen_annual_mwh"].sum().to_dict()


def _capture(year: int, meta: dict) -> dict:
    """Solve *year* on the keeper recipe and return the captured P0 / floor."""
    cap: dict = {}
    orig = PC._nyiso_gas_bridge_floor

    def _spy(config, fleet, fleet_arrays, p0_dispatch, p0_prices, mc_base):
        out = orig(config, fleet, fleet_arrays, p0_dispatch, p0_prices, mc_base)
        cap["p0"] = np.array(p0_dispatch, copy=True)
        cap["floor"] = (
            np.zeros_like(cap["p0"]) if out is None else np.array(out, copy=True)
        )
        cap["pmax"] = np.array(fleet_arrays.pmax, copy=True)
        cap["plant"] = np.array(
            [int(getattr(g, "plant_code", 0) or 0) for g in fleet], dtype=int
        )
        cap["klass"] = np.array(
            [str(getattr(g, "plant_group", "")) for g in fleet], dtype=object
        )
        cap["zone"] = np.array(
            [str(getattr(g, "zone", "")) for g in fleet], dtype=object
        )
        return out

    PC._nyiso_gas_bridge_floor = _spy
    try:
        gas = meta["gas_prices"]
        RC.run_year(
            year,
            "NYISO",
            int(meta.get("hours", 8760)),
            float(gas[str(year)]),
            {},
            **_kwargs(meta),
        )
    finally:
        PC._nyiso_gas_bridge_floor = orig
    if "p0" not in cap:
        raise RuntimeError(
            f"{year}: the NYISO gas bridge never ran — the recipe did not arm it"
        )
    return cap


def _year_rows(year: int, cap: dict) -> list[dict]:
    """Return one per-plant row of P0-vs-measured statistics for *year*."""
    p0, floor, pmax = cap["p0"], cap["floor"], cap["pmax"]
    plant, klass, zone = cap["plant"], cap["klass"], cap["zone"]
    metered = _campd_plant_hourly(year)
    e923 = _e923_net(year)
    by_plant: dict[int, list[int]] = collections.defaultdict(list)
    for i in range(p0.shape[0]):
        if klass[i] == "CC_REGULAR" and plant[i] > 0:
            by_plant[int(plant[i])].append(i)
    rows = []
    for pc, idxs in by_plant.items():
        p0_mwh = float(sum(p0[i].sum() for i in idxs))
        fl_mwh = float(sum(floor[i].sum() for i in idxs))
        cap_mw = float(sum(pmax[i] for i in idxs))
        meas = metered.get(str(pc))
        # The detector reads each LP row separately; the cheapest row is the
        # one the bridge floors, so its pattern is the one that matters.
        base = min(idxs, key=lambda i: -float(pmax[i]))
        on = p0[base] > RUN_THRESHOLD_FRAC * pmax[base]
        r = _runs(on)
        lens = np.array([e - s for s, e in r], dtype=float) if r else np.zeros(1)
        row = {
            "plant": pc,
            "zone": str(zone[idxs[0]]),
            "lp_rows": len(idxs),
            "lp_capacity_mw": round(cap_mw, 1),
            "p0_gwh": round(p0_mwh / 1e3, 2),
            "bridge_floor_gwh": round(fl_mwh / 1e3, 2),
            "p0_runs": len(r),
            "p0_run_median_h": round(float(np.median(lens)), 1),
            "p0_run_p25_h": round(float(np.percentile(lens, 25)), 1),
            "p0_runs_under_4h": int((lens < 4).sum()),
            "p0_on_share": round(float(on.mean()), 4),
        }
        if meas is not None and meas.size:
            m_on = meas > 0
            mr = _runs(m_on)
            mlens = np.array([e - s for s, e in mr], dtype=float) if mr else np.zeros(1)
            row.update(
                campd_gwh=round(float(meas.sum()) / 1e3, 2),
                campd_on_share=round(float(m_on.mean()), 4),
                campd_runs=len(mr),
                campd_run_median_h=round(float(np.median(mlens)), 1),
            )
        e = e923.get(pc)
        if e:
            row["e923_gwh"] = round(float(e) / 1e3, 2)
            row["p0_over_e923"] = round(p0_mwh / float(e), 2)
        if meas is not None and meas.sum() > 0:
            row["p0_over_campd"] = round(p0_mwh / float(meas.sum()), 2)
        rows.append(row)
    return sorted(rows, key=lambda r: -(r["p0_gwh"] - r.get("e923_gwh", r.get("campd_gwh", 0.0))))


def main() -> int:
    """Run the per-year captures and write the probe record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    meta = json.loads((BUNDLE / "meta.json").read_text())
    out: dict = {"bundle": BUNDLE.name, "run_threshold_frac": RUN_THRESHOLD_FRAC,
                 "years": {}}
    for year in args.year:
        if year not in (2023, 2024, 2025):
            raise SystemExit(
                f"year {year} is outside the 2023-2025 training window "
                "(CLAUDE.md rule 22; the holdout spend freeze is ACTIVE)"
            )
        rows = _year_rows(year, _capture(year, meta))
        out["years"][str(year)] = rows
        print(f"=== {year}")
        hdr = ("plant", "zone", "cap", "P0", "CAMPD", "E923", "x923", "xCAMPD",
               "floor", "runs", "medlen")
        print("{:>7s} {:14s} {:>7s} {:>8s} {:>8s} {:>8s} {:>6s} {:>7s} {:>7s} {:>5s} {:>6s}".format(*hdr))
        for r in rows[:14]:
            print(
                f"{r['plant']:7d} {r['zone']:14s} {r['lp_capacity_mw']:7.1f} "
                f"{r['p0_gwh']:8.1f} {r.get('campd_gwh', float('nan')):8.1f} "
                f"{r.get('e923_gwh', float('nan')):8.1f} "
                f"{r.get('p0_over_e923', float('nan')):6.2f} "
                f"{r.get('p0_over_campd', float('nan')):7.2f} "
                f"{r['bridge_floor_gwh']:7.2f} {r['p0_runs']:5d} "
                f"{r['p0_run_median_h']:6.1f}"
            )
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
