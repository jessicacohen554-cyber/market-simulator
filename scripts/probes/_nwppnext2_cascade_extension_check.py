"""NWPP-NEXT-2 item 3: does the extended cascade artifact materialize in 2019-2022? ZERO LP.

Reproduces the numbers in
``docs/handoffs/FINDING-nwppnext2-hydro-cascade-2019-2022-2026-09-25.md``:

1. **Artifact layer** -- per year, ``load_hydro_cascade("NWPP", y, codes)`` on the
   year's own ``load_hydro_budget`` plant set: does a spec come back, with which
   coupled plants, links and τ.
2. **Fleet layer** (``--fleet``) -- per year, the keeper recipe rebuilt with
   ``run_year(fleet_only=True)`` (``scripts/replay_keeper.run_year_kwargs`` on the
   registered keeper ``results/calibration/nwppnext_span``; ``hydro_backfill_year``
   null for 2019-2022 exactly as the keeper recorded), the hydro block located as
   the fleet's ``fuel_type == "hydro"`` tail, and the solve path's own resolver
   ``pipeline.kwargs.resolve_hydro_cascade`` called on it -- the object the LP
   would receive. No LP is built or solved.
3. **τ diagnostic** -- per-year τ of the five coupled links in 2019-2022 on the
   builder's own anomaly cross-correlation, against the FROZEN 2023-2024 τ. Reported
   only; nothing is written back (rule 23).

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwppnext2_cascade_extension_check.py [--fleet]
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))

BUNDLE = Path("results/calibration/nwppnext_span")
YEARS = tuple(range(2019, 2026))
EXT_YEARS = (2019, 2020, 2021, 2022)


def artifact_layer() -> dict:
    """Spec summary per year from the artifact on the year's hydro-budget plant set."""
    from market_sim.data.hydro import load_hydro_budget, load_hydro_cascade

    out = {}
    for y in YEARS:
        hb = load_hydro_budget("NWPP", y, backfill_year=None if y < 2023 else 2024)
        spec = load_hydro_cascade("NWPP", y, hb.plant_ids.astype(int))
        out[y] = (
            None
            if spec is None
            else dict(
                n_coupled=int(spec.n_coupled),
                plants=spec.plant_codes.tolist(),
                n_links=int(spec.n_links),
                tau=np.asarray(spec.link_tau).tolist(),
                pond_cap=np.round(spec.pond_cap, 2).tolist(),
                side_inflow_mean=np.round(spec.side_inflow.mean(axis=1), 3).tolist(),
            )
        )
    return out


def fleet_layer(years: tuple[int, ...]) -> dict:
    """Resolver output on the keeper's fleet-only rebuild, per year."""
    from market_sim.pipeline.kwargs import resolve_hydro_cascade
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    out = {}
    for y in years:
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, y))
        kw["prb_overrides"] = copy.deepcopy(kw.get("prb_overrides") or {})
        if y < 2023:
            kw["hydro_backfill_year"] = None
        gas = meta["gas_prices"].get(str(y))
        if gas is None:
            from market_sim.pipeline import reference as _ref

            gas = float(_ref.henry_hub_actual(_ref.load_reference(), int(y)))
        built = run_year(y, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)
        fleet, config = built["fleet"], built["config"]
        hidx = np.asarray(
            [
                i
                for i, g in enumerate(fleet)
                if str(getattr(g, "fuel_type", "")) == "hydro"
            ],
            dtype=int,
        )
        spec = resolve_hydro_cascade("NWPP", y, fleet, hidx, config)
        armed = bool(getattr(config, "hydro_cascade_coupling", False))
        if getattr(spec, "n_coupled", 0):
            out[y] = dict(
                cascade_flag=armed,
                n_hydro=int(hidx.size),
                n_coupled=int(spec.n_coupled),
                plants=spec.plant_codes.tolist(),
                n_links=int(spec.n_links),
                tau=np.asarray(spec.link_tau).tolist(),
                lp_rows=int(spec.n_coupled)
                * 8760,  # one water-balance equality per plant-hour
                lp_cols=2 * int(spec.n_coupled) * 8760,  # spill + pond per plant-hour
            )
        else:
            out[y] = dict(cascade_flag=armed, n_hydro=int(hidx.size), spec="UNSET")
        print(y, out[y], flush=True)
    return out


def tau_diagnostic() -> pd.DataFrame:
    """Per-year τ of each coupled link, 2019-2022, on the builder's own construction."""
    import build_nwpp_hydro_cascade as bc

    links = pd.read_csv(bc.OUT_LINKS)
    coupled = links[links["coupled"].astype(bool)]
    hourly = bc.load_hourly(("2019-01-01", "2023-01-01"))
    anom = {st: bc._anomaly(df[bc.S_OUT]) for st, df in hourly.items()}
    rows = []
    for r in coupled.itertuples():
        rec = dict(link=r.link, u=r.u_station, d=r.d_station, tau_frozen=r.tau_h)
        for y in EXT_YEARS:
            sel = anom[r.u_station].index.year == y
            t, rr, _ = bc._peak(
                bc._lag_curve(
                    anom[r.u_station].values[sel], anom[r.d_station].values[sel]
                )
            )
            rec[f"tau_{y}"] = t
            rec[f"r_{y}"] = round(rr, 3)
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    """Run the three checks and print them."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--fleet", action="store_true", help="also run the fleet-only layer"
    )
    ap.add_argument("--fleet-years", type=int, nargs="+", default=list(YEARS))
    args = ap.parse_args()
    art = artifact_layer()
    for y, v in art.items():
        print("artifact", y, v)
    print(tau_diagnostic().to_string(index=False))
    if args.fleet:
        fleet_layer(tuple(args.fleet_years))


if __name__ == "__main__":
    main()
