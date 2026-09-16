"""nyiso-236 PHASE 0 (ZERO-LP): the delivered-gas offer anchor's INDEX GRAIN.

Record: ``docs/FINDING-nyiso236-the-anchor-grain-and-the-gas-slope-2026-09-16.md``
(§2.1 the within-year vs between-year index error; §4 the month-grain
separation from Object B).

The ``gas_offer_net_revenue_margin`` mechanism prices a band's markup above its
measured physical basis at a delivered-gas ANCHOR
(``data.offer_curves.apply_gas_offer_margin``:
``mc[g,t] += offer_markup_hr[g] x (anchor - fuel_price[g,t])``). With
``gas_offer_margin_zonal_anchor_vintage`` armed the anchor is resolved per
``(zone, solve-year)`` as an ANNUAL scalar
(``data.fuel.zonal_anchor.zonal_gas_anchors_for_year`` -> ``np.nanmean`` over
8,760 h). This probe measures, per ``(zone, year)``, the series that anchor is
taken over, and reports:

* the ANNUAL anchor (which reproduces the keeper's own recorded values), the
  MONTHLY means, and the within-year spread -- against the BETWEEN-year spread
  that ``gas_offer_margin_zonal_anchor_vintage`` (nyiso-230) was promoted to
  close;
* the load-weighted annual price delta a MONTH-grain anchor would produce,
  ``markup_hr x (gas_load_weighted - gas_annual)`` -- the zero-LP test that
  separates the anchor grain from the gas-slope defect (Object B).

Reads no price, no residual and no actual dispatch (rule 13 ``[R-MEASURED]``);
builds no fleet and touches no LP (rule 32 ``[R-SHARD]`` (a)). REPORTING ONLY --
it arms nothing and is not on any solve path.

Usage (from the repo root, ``--profile nyiso`` hydration)::

    python3 scripts/probes/nyiso236_anchor_grain_phase0.py
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("src").resolve()))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import FleetArrays  # noqa: E402
from market_sim.data.fuel._shared import _GAS_FUEL_IDX  # noqa: E402
from market_sim.data.fuel.basis import ZONAL_BASIS_APPLIERS  # noqa: E402
from market_sim.data.fuel.trajectories import _gas_series  # noqa: E402

ISO = "NYISO"
HOURS = 8760

#: nyiso-230's marginal-weighted ``offer_markup_hr`` for NYISO's registered
#: curve ($/MWh per $/MMBtu), cited from the field docstring in
#: ``config/scenarios.py::gas_offer_margin_zonal_anchor_vintage`` ("slope 2.691
#: $/MWh per $/MMBtu -- which is the marginal-weighted ``markup_hr`` the
#: registered curve itself carries"). Used ONLY to convert a measured anchor
#: delta into a price delta for the separation test; nothing is fitted here.
MARKUP_HR = 2.691


def month_index() -> np.ndarray:
    """Hour -> month (1..12) on the model's own non-leap 8,760 calendar."""
    days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    idx = np.concatenate([np.full(d * 24, m + 1) for m, d in enumerate(days)])
    assert idx.size == HOURS, idx.size
    return idx


def build_config(run_config: Path, year: int) -> ScenarioConfig:
    """The keeper's OWN recorded ``scenario_config``, per-year gas override applied.

    The harness sets ``gas_price_override`` per year from
    ``calibration_flags.gas_prices``; the recorded config carries only the last
    resolved value, so it is re-applied here.
    """
    rc = json.loads(run_config.read_text())
    valid = {f.name for f in dataclasses.fields(ScenarioConfig)}
    sc = {k: v for k, v in rc["scenario_config"].items() if k in valid}
    sc["gas_price_override"] = {int(k): v for k, v in rc["calibration_flags"]["gas_prices"].items()}[year]
    return ScenarioConfig(**sc)


def zonal_hourly(config: ScenarioConfig, year: int) -> tuple[list[str], np.ndarray]:
    """``(zone_names, (n_zone, HOURS) delivered gas $/MMBtu)``.

    Exactly ``zonal_gas_anchors_for_year``'s measurement -- one synthetic gas row
    per zone through the ISO's registered basis applier, which keys only on
    ``fuel_type_idx`` and ``zone_idx`` -- but keeping the array instead of its
    mean.
    """
    zone_names = list(get_iso_config(ISO).zone_names)
    n = len(zone_names)
    prices = np.repeat(np.asarray(_gas_series(config, year, HOURS), dtype=float)[None, :], n, axis=0)
    fleet = FleetArrays(
        pmax=np.ones(n),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 7.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.arange(n),
        fuel_type_idx=np.full(n, int(sorted(_GAS_FUEL_IDX)[0])),
        availability=np.ones((n, HOURS)),
        unit_ids=[f"probe_{z}" for z in zone_names],
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.zeros(n, dtype=int),
    )
    ZONAL_BASIS_APPLIERS[ISO](prices, fleet, config, year)
    return zone_names, prices


def zonal_load(bundle: Path, year: int) -> np.ndarray:
    """Total ISO load MW per hour, from the bundle's committed P1 system sidecar."""
    df = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return df.pivot(index="hour", columns="zone", values="demand").sort_index().to_numpy(float).sum(axis=1)


def main() -> None:
    """Measure the anchor grain and print both tables."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=Path("results/calibration/nyiso235_gasrepair_span"))
    ap.add_argument("--years", type=int, nargs="+", default=[2022, 2023, 2024, 2025])
    ap.add_argument("--reference-zone", default="Capital_Hudson")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    mi = month_index()
    out: dict = {"iso": ISO, "hours": HOURS, "bundle": str(args.bundle), "years": {}}
    print("=== anchor grain: within-year vs between-year index error ===")
    for year in args.years:
        cfg = build_config(args.bundle / "run_config.json", year)
        zones, px = zonal_hourly(cfg, year)
        yr: dict = {"zones": {}}
        for i, z in enumerate(zones):
            s = px[i]
            annual = float(np.nanmean(s))
            monthly = {int(m): float(np.nanmean(s[mi == m])) for m in range(1, 13)}
            month_h = np.array([monthly[int(m)] for m in mi])
            yr["zones"][z] = {
                "annual_anchor": annual,
                "monthly_anchor": monthly,
                "monthly_min": min(monthly.values()),
                "monthly_max": max(monthly.values()),
                "within_year_spread": max(monthly.values()) - min(monthly.values()),
                "mean_abs_dev_annual_index": float(np.nanmean(np.abs(annual - s))),
                "mean_abs_dev_month_index": float(np.nanmean(np.abs(month_h - s))),
            }
        out["years"][year] = yr
        d = yr["zones"][args.reference_zone]
        print(
            f"  {year}  annual {d['annual_anchor']:7.3f}   monthly {d['monthly_min']:6.3f}..{d['monthly_max']:7.3f}"
            f"   within-year spread {d['within_year_spread']:7.3f}   MAD from annual anchor {d['mean_abs_dev_annual_index']:6.3f}"
        )
    anns = [out["years"][y]["zones"][args.reference_zone]["annual_anchor"] for y in args.years]
    print(f"  BETWEEN-year spread (what nyiso-230 closed): {max(anns) - min(anns):.3f} $/MMBtu")

    print("\n=== separation test: what a MONTH-grain anchor does to the annual load-weighted price ===")
    gas_lvl, dprice = [], []
    for year in args.years:
        d = out["years"][year]["zones"][args.reference_zone]
        load = zonal_load(args.bundle, year)
        gas_h = np.array([d["monthly_anchor"][str(m)] if isinstance(next(iter(d["monthly_anchor"])), str) else d["monthly_anchor"][m] for m in mi])
        lw = float((gas_h * load).sum() / load.sum())
        delta = MARKUP_HR * (lw - d["annual_anchor"])
        out["years"][year]["month_anchor_price_delta"] = delta
        gas_lvl.append(d["annual_anchor"])
        dprice.append(delta)
        print(
            f"  {year}  annual {d['annual_anchor']:7.3f}  load-weighted {lw:7.3f}  "
            f"diff {lw - d['annual_anchor']:+6.3f}  => price delta {delta:+6.3f} $/MWh"
        )
    slope = float(np.polyfit(np.array(gas_lvl), np.array(dprice), 1)[0])
    out["month_anchor_slope_contribution"] = slope
    print(f"  slope contribution: {slope:+.4f} $/MWh per $/MMBtu")

    if args.out:
        args.out.write_text(json.dumps(out, indent=1))
        print("wrote", args.out)


if __name__ == "__main__":
    main()
