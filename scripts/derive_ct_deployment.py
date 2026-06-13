"""Derive the ERCOT CT_PEAKER AS/RUC-deployment energy floor from CEMS.

ERCOT's energy-only LP structurally cannot dispatch the simple-cycle peaker
energy that runs *out of merit*: the IMM-documented ancillary-service /
reliability-unit-commitment deployment + reserve-adequacy wedge in which ERCOT
deploys CT peakers (Reg/RRS/ECRS/RUC, plus conservative ECRS holds) at a real-
time price below the unit's own marginal energy cost. The per-plant decomposition
(calibration-log "ERCOT Runs 97a/97b") measured 31/38/44% of the CEMS-covered
CT_PEAKER energy in 2023/24/25 running in hours where the RT price was below the
unit's marginal cost — ~1.4-2.3 TWh/yr the merit order omits because it is
economically irrational on price.

This script measures that wedge directly from EPA CAMPD CEMS and writes a
per-plant *hourly deployment floor* artifact, mirroring the outage overlays
(``scripts/derive_partial_outages.py`` / ``scripts/derive_campd_unit_outages.py``).
For each CEMS-covered CT_PEAKER plant and each hour it generated, the hour is a
**deployment hour** when

    net_mw > --min-mw   AND   actual RT LMP < marginal_cost(plant)

with ``marginal_cost = plant_avg_heat_rate * --hr-mult * gas_price + --vom``.
In a deployment hour the floor is the plant's *measured* net output for that
hour; everywhere else it is zero. The overlay (consumed by
``market_sim.data.outages.ct_deployment_floor_for_year`` and applied as a
min-generation bound in ``fleet.generators_to_fleet_arrays`` when
``ScenarioConfig.ct_deployment_overlay`` is set, ERCOT backcast only) therefore
pins these peakers to their observed level *only in the out-of-merit hours* —
recovering the deployment energy without flooring CT to its full CEMS output
(the in-merit hours dispatch economically as before).

Quantification guard (the brief's "do NOT over-credit"): the floor is the
out-of-merit subset of measured CEMS energy, self-limited to the documented
~1.4-2.3 TWh/yr. ``--report`` prints the per-year deployment energy and its
share of the covered CT_PEAKER CEMS total without writing the artifact, so the
threshold (``--hr-mult`` / ``--vom`` / ``--min-mw``) can be checked against the
measured wedge before it is committed.

Cogens mislabeled CT_PEAKER (San Jacinto 7325 — a refinery cogen pinned to the
class by the dominant-class override, flat ~50% CF, already restored by the
``--btm-backfill-year`` add-back) are excluded by default (``--exclude-plants``)
so the deployment floor does not double-count the BTM backfill.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import HOURS_PER_YEAR, VOM  # noqa: E402
from market_sim.data import campd  # noqa: E402

# Annual Henry Hub gas price ($/MMBtu) the ERCOT backcast bids gas against
# (scripts.run_calibration_full._henry_hub_actual); the CT marginal-cost
# threshold uses the same annual price the LP's CT offer is built from, so
# "out of merit" is defined consistently with the dispatch.
DEFAULT_GAS_PRICE: dict[int, float] = {2023: 2.54, 2024: 2.19, 2025: 3.52}

# San Jacinto (7325): a refinery cogen the dominant-class override pins to
# CT_PEAKER (flat ~50% CF, EIA chp=N). Its 65% must-run share is BTM-removed
# and restored from the plant's 923 net generation (--btm-backfill-year), so a
# deployment floor here would double-count the backfill. Excluded by default.
DEFAULT_EXCLUDE: frozenset[int] = frozenset({7325})

OUT_DEFAULT = REPO / "inputs" / "calibration" / "ct_deployment_floor_ERCOT.parquet"


def _ct_peaker_heat_rates(bins_path: Path) -> dict[int, float]:
    """Return ``{plant_code: plant_avg_heat_rate}`` for CT_PEAKER bins.

    One representative heat rate per plant (the bin sheet carries one
    ``Plant_Avg_HR_MMBtu_MWh`` per CT_PEAKER plant). Plants with no heat rate
    in the sheet (the tiny unassigned aggregator bins) are skipped — they
    carry no CEMS series either, so they never reach the deployment test.
    """
    df = pd.read_csv(bins_path)
    df = df[df["Plant_Group"] == "CT_PEAKER"]
    out: dict[int, float] = {}
    for code, hr in zip(df["Plant_Code"], df["Plant_Avg_HR_MMBtu_MWh"]):
        if pd.isna(hr) or float(hr) <= 0.0:
            continue
        out[int(code)] = float(hr)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument(
        "--bins", default=str(REPO / "inputs" / "custom-bin-assignments.csv"),
        help="Per-plant bin CSV; supplies the CT_PEAKER plant set + heat rates.",
    )
    ap.add_argument(
        "--lmp",
        default=str(REPO / "inputs" / "calibration"
                    / "actual_lmp_hourly_ERCOT.parquet"),
        help="Actual hourly LMP parquet (year, hour, rt, da); the rt series is "
             "the out-of-merit reference price.",
    )
    ap.add_argument(
        "--hr-mult", type=float, default=1.0,
        help="Heat-rate multiplier on the plant average for the marginal-cost "
             "threshold (1.0 = the plant's economic-tranche heat rate). Lower "
             "tightens the out-of-merit test (fewer hours, less energy).",
    )
    ap.add_argument(
        "--vom", type=float, default=VOM["gas_ct"],
        help="CT variable O&M added to fuel cost ($/MWh; default the model's "
             "gas_ct VOM).",
    )
    ap.add_argument(
        "--min-mw", type=float, default=1.0,
        help="Net-MW floor below which an hour is treated as noise/off (not a "
             "deployment hour even if priced out of merit).",
    )
    ap.add_argument(
        "--gas-price", nargs="*", default=None,
        help="Override annual gas price as YEAR:PRICE pairs (default the "
             "backcast Henry Hub actuals).",
    )
    ap.add_argument(
        "--exclude-plants", nargs="*", type=int, default=sorted(DEFAULT_EXCLUDE),
        help="EIA plant codes to exclude (default San Jacinto 7325, a BTM "
             "cogen).",
    )
    ap.add_argument("--hours", type=int, default=HOURS_PER_YEAR)
    ap.add_argument(
        "--out", default=str(OUT_DEFAULT),
        help="Output parquet path (long: year, plant_code, hour, floor_mw).",
    )
    ap.add_argument(
        "--report", action="store_true",
        help="Measure and print the deployment wedge without writing the "
             "artifact (the quantification check).",
    )
    args = ap.parse_args()

    iso = args.iso.upper()
    gas_price = dict(DEFAULT_GAS_PRICE)
    if args.gas_price:
        for pair in args.gas_price:
            y, p = pair.split(":")
            gas_price[int(y)] = float(p)
    exclude = set(args.exclude_plants)

    heat_rates = _ct_peaker_heat_rates(Path(args.bins))
    ct_codes = set(heat_rates) - exclude

    lmp = pd.read_parquet(args.lmp)
    states = campd.states_for_iso(iso)
    par_path = REPO / "inputs" / "processed" / "parasitic_load_factors.parquet"
    factors = (
        campd.pooled_factor_map(pd.read_parquet(par_path))
        if par_path.exists() else {}
    )

    rows: list[dict] = []
    print(f"{'year':>5} {'gas':>6} {'#plnt':>6} {'#hrs':>9} "
          f"{'CEMS TWh':>9} {'deploy TWh':>11} {'share':>7}")
    for year in args.years:
        if year not in gas_price:
            print(f"  (no gas price for {year}; skipped)")
            continue
        gp = gas_price[year]
        rt = (
            lmp[lmp["year"] == year]
            .set_index("hour")["rt"]
            .reindex(range(args.hours))
            .to_numpy(dtype=float)
        )
        df = campd.load_campd_hourly(states, [year])
        net = campd.plant_hourly_net(df, factors, year, hours=args.hours)

        cems_total = 0.0   # covered CT_PEAKER CEMS energy (MWh)
        deploy_total = 0.0  # out-of-merit subset (MWh)
        n_plants = 0
        n_hours = 0
        for code in sorted(ct_codes):
            series = net.get(code)
            if series is None:
                continue
            mc = heat_rates[code] * args.hr_mult * gp + args.vom
            ran = series > args.min_mw
            if not ran.any():
                continue
            n_plants += 1
            cems_total += float(series[ran].sum())
            # Out-of-merit: ran, and the RT price was below the unit's marginal
            # cost. NaN RT hours (missing price) are not counted out of merit.
            deploy = ran & (rt < mc)
            if not deploy.any():
                continue
            n_hours += int(deploy.sum())
            deploy_total += float(series[deploy].sum())
            for h in np.flatnonzero(deploy):
                rows.append({
                    "year": int(year),
                    "plant_code": int(code),
                    "hour": int(h),
                    "floor_mw": float(series[h]),
                })
        share = deploy_total / cems_total if cems_total > 0 else 0.0
        print(f"{year:>5} {gp:>6.2f} {n_plants:>6} {n_hours:>9} "
              f"{cems_total / 1e6:>9.2f} {deploy_total / 1e6:>11.2f} "
              f"{share:>6.1%}")

    out = pd.DataFrame(
        rows, columns=["year", "plant_code", "hour", "floor_mw"]
    ).astype({"year": "int16", "plant_code": "int32",
              "hour": "int32", "floor_mw": "float32"})
    if args.report:
        print(f"\n[report] {len(out)} deployment-hour floors "
              f"({out['plant_code'].nunique()} plants) — NOT written")
        return
    out.to_parquet(args.out, index=False)
    print(f"\nwrote {len(out)} deployment-hour floors to {args.out}")


if __name__ == "__main__":
    main()
