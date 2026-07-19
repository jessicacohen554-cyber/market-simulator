"""Derive the ERCOT spatial reliability-deployment energy floor from CEMS.

The generalization of the CT AS/RUC-deployment overlay
(``scripts/data/derive_ct_deployment.py``) to the **load-pocket thermal fleet**. The
keeper backcast systematically over-generates the North zone and under-generates
South_Central / West / Northeast across classes (worst on the high-HR thermal
and COAL_PRB): the 7-zone reduced network cannot form the intra-zonal congestion
pockets (NE_LOB, the Rio Grande Valley cluster, HMLTN, WHARTN) that pin local
ERCOT prices above the system hub and force the pocket fleet on for reliability.
An energy-only single-system-price LP cannot dispatch that energy because, at
the *hub* price the LP clears against, those plants are out of merit.

The fix mirrors the CT deployment overlay but scopes on the **load-zone
congestion subset** the prior session validated. For each CEMS-covered thermal
plant (CC_REGULAR, COAL, ST_GAS, CC_CHP) in the under-running zones
(South_Central, West, Northeast) and each hour the plant ran, the hour is a
**deployment hour** when

    net_mw > --min-mw
    AND  LZ_price(plant zone) > marginal_cost(plant)     # economic locally
    AND  HB_HUBAVG          < marginal_cost(plant)        # out of merit at hub

with ``marginal_cost = plant_avg_heat_rate * --hr-mult * fuel_price + vom``
(gas classes priced at the backcast Henry Hub annual; coal priced at its
delivered supply cost — lignite vs PRB). The third condition is the critical
scoping found by the prior session: a naïve out-of-merit test on either the hub
*or* the load-zone price alone is ~44 / ~42 TWh (expensive high-HR plants
running below *every* price level in a low-price year), which does NOT scope.
Requiring the plant to be economic at its LOCAL load-zone price but out of merit
at the system hub isolates exactly the congestion energy the system-price LP
misses — the measured wedge is ~2.7 / 3.7 / 4.8 TWh (2023/24/25), ~40% of the
~11.5 TWh net under-zone gap. (The residual ~6.7 TWh ran below even the local
price = genuine RUC commitment, irreducible by a price-recoverable floor.)

In a deployment hour the floor is the plant's *measured* net output for that
hour; everywhere else it is zero. The overlay (consumed by
``market_sim.data.outages.reliability_deployment_floor_for_year`` and applied as
a sparse min-generation bound in ``fleet.generators_to_fleet_arrays`` when
``ScenarioConfig.reliability_deployment_overlay`` is set, ERCOT backcast only)
therefore pins these pocket plants to their observed level *only in the
out-of-merit-at-hub-but-economic-locally hours* — recovering the congestion
energy without flooring them to full CEMS (the in-merit hours dispatch
economically as before). The units keep the statistical WEFOR/POF model (the
floor is sparse and below pmax), so they are availability-capped where they
coincide.

``--report`` prints the per-year deployment energy and its share of the covered
CEMS by zone/class WITHOUT writing the artifact, so the wedge can be checked
against the measured ~2.7/3.7/4.8 TWh before it is committed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import HOURS_PER_YEAR, VOM  # noqa: E402
from market_sim.config.paths import (  # noqa: E402
    CALIBRATION_DIR,
    CAMPD_BINS_CSV,
    PROCESSED_DIR,
)
from market_sim.data import campd  # noqa: E402
from market_sim.data.coal import COAL_PLANT_SUPPLY  # noqa: E402
from market_sim.data.fuel import (  # noqa: E402
    COAL_PRICE_LIGNITE_BY_YEAR,
    COAL_PRICE_PRB_BY_YEAR,
)

# Annual Henry Hub gas price ($/MMBtu) the ERCOT backcast bids gas against
# (scripts.run_calibration_full._henry_hub_actual); the gas marginal-cost
# threshold uses the same annual price the LP's offer is built from, so "out of
# merit" is defined consistently with the dispatch (mirrors derive_ct_deployment).
DEFAULT_GAS_PRICE: dict[int, float] = {2023: 2.54, 2024: 2.19, 2025: 3.52}

# Under-running zones the overlay targets (the prior session's thermal miss by
# zone: South_Central -8.7, West -1.8, Northeast -1.0 TWh in 2025). North /
# Houston / South over- or roughly match and are excluded.
DEFAULT_ZONES: tuple[str, ...] = ("South_Central", "West", "Northeast")

# Load-pocket thermal classes (bin-sheet Plant_Group). Coal is a single group
# in the bin sheet; its PRB/lignite split is the supply tag (COAL_PLANT_SUPPLY).
DEFAULT_CLASSES: tuple[str, ...] = ("CC_REGULAR", "COAL", "ST_GAS", "CC_CHP")

# Plant zone -> load-zone settlement point(s). Multiple points are averaged
# (South_Central spans Austin Energy + CPS San Antonio + LCRA). The hub
# reference HB_HUBAVG reproduces the system actual_lmp_hourly_ERCOT rt.
ZONE_TO_LZ: dict[str, tuple[str, ...]] = {
    "South_Central": ("LZ_AEN", "LZ_CPS", "LZ_LCRA"),
    "West": ("LZ_WEST",),
    "Northeast": ("LZ_RAYBN",),
    "Houston": ("LZ_HOUSTON",),
    "South": ("LZ_SOUTH",),
    "North": ("LZ_NORTH",),
}
HUB_POINT = "HB_HUBAVG"

# Class -> VOM ($/MWh) and the fuel keyed for the marginal-cost threshold.
_CLASS_VOM: dict[str, float] = {
    "CC_REGULAR": VOM["gas_cc"],
    "CC_CHP": VOM["gas_cc"],
    "ST_GAS": VOM["gas_st"],
    "COAL": VOM["coal"],
}


def _out_default(iso: str) -> Path:
    return CALIBRATION_DIR / f"reliability_deployment_floor_{iso.upper()}.parquet"


def _plant_meta(bins_path: Path, classes: set[str], zones: set[str]) -> dict:
    """Return ``{plant_code: (plant_group, zone, plant_avg_HR)}`` for the
    in-scope (class, zone) bin-sheet plants.

    The bin sheet carries one row per (plant, bin); a plant's representative
    heat rate is its nameplate-weighted ``Plant_Avg_HR_MMBtu_MWh`` across its
    in-class rows (the rate the LP's economic-tranche offer is built from).
    Plants with no positive heat rate are skipped (they carry no usable
    marginal-cost threshold).
    """
    df = pd.read_csv(bins_path)
    df = df[df["Plant_Group"].isin(classes) & df["ERCOT_Zone"].isin(zones)]
    num: dict[int, float] = {}
    den: dict[int, float] = {}
    meta: dict[int, tuple[str, str]] = {}
    for r in df.itertuples(index=False):
        hr = getattr(r, "Plant_Avg_HR_MMBtu_MWh")
        cap = getattr(r, "Nameplate_MW")
        if pd.isna(hr) or float(hr) <= 0.0:
            continue
        cap = 1.0 if pd.isna(cap) or float(cap) <= 0.0 else float(cap)
        pc = int(r.Plant_Code)
        num[pc] = num.get(pc, 0.0) + float(hr) * cap
        den[pc] = den.get(pc, 0.0) + cap
        # Dominant-class / first-zone assignment (a plant's rows share a zone
        # in the ERCOT bin sheet; keep the first seen).
        meta.setdefault(pc, (r.Plant_Group, r.ERCOT_Zone))
    return {
        pc: (meta[pc][0], meta[pc][1], num[pc] / den[pc]) for pc in num if den[pc] > 0.0
    }


def _fuel_price(
    plant_group: str, plant_code: int, year: int, gas_price: dict[int, float]
) -> float:
    """Delivered fuel price ($/MMBtu) the marginal-cost threshold uses.

    Gas classes bid against the backcast Henry Hub annual; coal plants bid
    against their delivered supply cost (mine-mouth lignite vs PRB-by-rail),
    consistent with the LP's per-supply coal pricing. A coal plant absent from
    the supply map defaults to PRB.
    """
    if plant_group == "COAL":
        supply = COAL_PLANT_SUPPLY.get(plant_code, "prb")
        if supply == "lignite":
            return float(COAL_PRICE_LIGNITE_BY_YEAR[year])
        return float(COAL_PRICE_PRB_BY_YEAR[year])
    return float(gas_price[year])


def _zone_lz_price(lmp_year: pd.DataFrame, zone: str, hours: int) -> np.ndarray:
    """Average load-zone RT price (MW-array) for a plant zone."""
    points = ZONE_TO_LZ[zone]
    cols = []
    for p in points:
        s = lmp_year[lmp_year["settlement_point"] == p].set_index("hour")["rt"]
        cols.append(s.reindex(range(hours)).to_numpy(dtype=float))
    stack = np.vstack(cols)
    # Hours where no point reports (e.g. the 8760th of a 8759-hour clock) are
    # all-NaN; nanmean would warn. They stay NaN, so the deploy test (lz > mc)
    # is False there — correctly excluded.
    all_nan = np.isnan(stack).all(axis=0)
    out = np.full(stack.shape[1], np.nan)
    if (~all_nan).any():
        out[~all_nan] = np.nanmean(stack[:, ~all_nan], axis=0)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument(
        "--bins",
        default=str(CAMPD_BINS_CSV),
        help="ERCOT per-plant bin CSV; supplies the in-scope plant set, zones "
        "and heat rates.",
    )
    ap.add_argument(
        "--lmp",
        default=str(CALIBRATION_DIR / "actual_lmp_zonal_ERCOT.parquet"),
        help="Zonal LMP parquet (year, hour, settlement_point, rt, da). The rt "
        "series of the plant's load zone and HB_HUBAVG are the local / hub "
        "out-of-merit reference prices.",
    )
    ap.add_argument(
        "--classes",
        nargs="+",
        default=list(DEFAULT_CLASSES),
        help="Bin-sheet Plant_Group classes to scope (default the load-pocket "
        "thermal fleet).",
    )
    ap.add_argument(
        "--zones",
        nargs="+",
        default=list(DEFAULT_ZONES),
        help="ERCOT zones to scope (default the under-running pockets).",
    )
    ap.add_argument(
        "--hr-mult",
        type=float,
        default=1.0,
        help="Heat-rate multiplier on the plant average for the marginal-cost "
        "threshold (1.0 = the economic-tranche heat rate). Lower tightens "
        "the out-of-merit test (fewer hours, less energy).",
    )
    ap.add_argument(
        "--min-mw",
        type=float,
        default=1.0,
        help="Net-MW floor below which an hour is treated as noise/off.",
    )
    ap.add_argument(
        "--gas-price",
        nargs="*",
        default=None,
        help="Override annual gas price as YEAR:PRICE pairs (default the "
        "backcast Henry Hub actuals).",
    )
    ap.add_argument("--hours", type=int, default=HOURS_PER_YEAR)
    ap.add_argument(
        "--out",
        default=None,
        help="Output parquet path (long: year, plant_code, hour, floor_mw). "
        "Defaults to reliability_deployment_floor_<ISO>.parquet.",
    )
    ap.add_argument(
        "--report",
        action="store_true",
        help="Measure and print the deployment wedge by zone/class without "
        "writing the artifact (the quantification check).",
    )
    ap.add_argument(
        "--mode",
        choices=["congestion", "full"],
        default="congestion",
        help="Scoping of the floor. 'congestion' (default): the load-zone "
        "congestion subset (ran AND LZ_price > MC AND HB_HUBAVG < MC) — the "
        "price-recoverable wedge the single-price view misses (run118: the "
        "7-zone LP already dispatches most of it, so it is near-no-op). "
        "'full': floor every running hour to the plant's realized CEMS net "
        "(the top-down zone floor) — a min-gen bound that binds only where "
        "the model under-dispatches the pocket plant, forcing local "
        "generation to the realized level and pulling the over-running "
        "exporting zone down. Size with --floor at run time.",
    )
    args = ap.parse_args()

    iso = args.iso.upper()
    gas_price = dict(DEFAULT_GAS_PRICE)
    if args.gas_price:
        for pair in args.gas_price:
            y, p = pair.split(":")
            gas_price[int(y)] = float(p)
    classes = set(args.classes)
    zones = set(args.zones)
    out_path = Path(args.out) if args.out else _out_default(iso)

    meta = _plant_meta(Path(args.bins), classes, zones)
    lmp = pd.read_parquet(args.lmp)
    states = campd.states_for_iso(iso)
    par_path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    factors = (
        campd.pooled_factor_map(pd.read_parquet(par_path)) if par_path.exists() else {}
    )

    rows: list[dict] = []
    # Aggregators for the report.
    by_zone_class: dict[tuple[int, str, str], list[float]] = {}
    print(
        f"{'year':>5} {'gas':>6} {'#plnt':>6} {'#hrs':>9} "
        f"{'CEMS TWh':>9} {'deploy TWh':>11} {'share':>7}"
    )
    for year in args.years:
        if year not in gas_price:
            print(f"  (no gas price for {year}; skipped)")
            continue
        gp = gas_price[year]
        lmp_y = lmp[lmp["year"] == year]
        hub = (
            lmp_y[lmp_y["settlement_point"] == HUB_POINT]
            .set_index("hour")["rt"]
            .reindex(range(args.hours))
            .to_numpy(dtype=float)
        )
        lz_cache: dict[str, np.ndarray] = {
            z: _zone_lz_price(lmp_y, z, args.hours) for z in zones
        }
        df = campd.load_campd_hourly(states, [year])
        net = campd.plant_hourly_net(df, factors, year, hours=args.hours)

        cems_total = 0.0
        deploy_total = 0.0
        n_plants = 0
        n_hours = 0
        for code, (grp, zone, hr) in sorted(meta.items()):
            series = net.get(code)
            if series is None:
                continue
            mc = hr * args.hr_mult * _fuel_price(
                grp, code, year, gas_price
            ) + _CLASS_VOM.get(grp, 0.0)
            ran = series > args.min_mw
            if not ran.any():
                continue
            n_plants += 1
            cems_total += float(series[ran].sum())
            lz = lz_cache[zone]
            if args.mode == "full":
                # Top-down zone floor: floor every running hour to the realized
                # CEMS net. As a min-gen bound it binds only where the model
                # under-dispatches the pocket plant, so the bound energy is the
                # plant's under-run vs CEMS — the net pocket gap, not the 44 TWh
                # naive out-of-merit total.
                deploy = ran
            else:
                # Congestion subset: ran, economic at the LOCAL load-zone price,
                # but out of merit at the system hub. NaN price hours skipped.
                deploy = ran & (lz > mc) & (hub < mc)
            if not deploy.any():
                continue
            n_hours += int(deploy.sum())
            e = float(series[deploy].sum())
            deploy_total += e
            by_zone_class.setdefault((year, zone, grp), [0.0, 0.0])
            by_zone_class[(year, zone, grp)][0] += e
            by_zone_class[(year, zone, grp)][1] += float(series[ran].sum())
            for h in np.flatnonzero(deploy):
                rows.append(
                    {
                        "year": int(year),
                        "plant_code": int(code),
                        "hour": int(h),
                        "floor_mw": float(series[h]),
                    }
                )
        share = deploy_total / cems_total if cems_total > 0 else 0.0
        print(
            f"{year:>5} {gp:>6.2f} {n_plants:>6} {n_hours:>9} "
            f"{cems_total / 1e6:>9.2f} {deploy_total / 1e6:>11.2f} "
            f"{share:>6.1%}"
        )

    if by_zone_class:
        print("\nby zone/class (deploy TWh / share of covered CEMS):")
        print(f"{'year':>5} {'zone':>14} {'class':>11} {'deploy TWh':>11} {'share':>7}")
        for year, zone, grp in sorted(by_zone_class):
            dep, cems = by_zone_class[(year, zone, grp)]
            sh = dep / cems if cems > 0 else 0.0
            print(f"{year:>5} {zone:>14} {grp:>11} {dep / 1e6:>11.2f} {sh:>6.1%}")

    out = pd.DataFrame(rows, columns=["year", "plant_code", "hour", "floor_mw"]).astype(
        {"year": "int16", "plant_code": "int32", "hour": "int32", "floor_mw": "float32"}
    )
    if args.report:
        print(
            f"\n[report] {iso}: {len(out)} deployment-hour floors "
            f"({out['plant_code'].nunique()} plants) — NOT written"
        )
        return
    out.to_parquet(out_path, index=False)
    print(f"\nwrote {len(out)} deployment-hour floors to {out_path}")


if __name__ == "__main__":
    main()
