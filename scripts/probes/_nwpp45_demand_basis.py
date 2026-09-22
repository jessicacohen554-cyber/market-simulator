"""nwpp-45 (ZERO LP): the demand-basis identity behind NWPP's C1 gas deficit.

Reproduces `FINDING-nwpp-45-2026-09-22.md` §3-§4 from committed artifacts plus
the EIA-930 corpus: the LP's demand is built from EIA-930 BA telemetry
(``Net generation (Adj)`` less GRID's Desert-Southwest interchange legs) while
C1 scores the model against the EIA-923 plant basis (``classFull``). The two
differ by 9-12 TWh/yr, every non-thermal class is separately pinned to a
measured budget, and the marginal class therefore absorbs the whole difference.

Prints three tables:

1. the per-year identity ``model demand = pool NG(Adj) - GRID_SW`` and its
   decomposition of the scored ``model total gen - classFull`` gap;
2. the per-BA EIA-930 ``Net generation (Adj)`` against the eGRID annual
   generation of the plants eGRID assigns to that BA — the 21.3 TWh
   generation-only-BA attribution disagreement, GRID included;
3. the footprint check: every plant in ``_iso_plant_ids("NWPP")`` carries a
   ``BACODE`` in ``NWPP_BAS`` and no pool-BA plant is missing, so the
   disagreement is between SOURCES, not between footprints.

Run: ``python3 scripts/probes/_nwpp45_demand_basis.py``  (DATA PROFILE: nwpp)
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

RUN_ID = "2026-09-20-nwpp-44-measured-take"
BUNDLE = Path("results/calibration/nwpp44_takeorpay_reg")
BENCH = Path("frontend/data/backcast/bench/NWPP")
YEARS = (2023, 2024, 2025)


def _payload() -> dict:
    from scripts.lib import backcast_artifacts as ba

    return ba.decode_run_js(
        Path(f"frontend/data/backcast/runs/{RUN_ID}.js").read_text()
    )


def identity() -> None:
    """Table 1 — the per-year demand identity and the gap decomposition."""
    from market_sim.data.eia930 import frames as F
    from market_sim.data.eia930.envelopes import _nwpp_grid_external_legs

    pay = _payload()
    rows = {}
    for year in YEARS:
        frame = F._pool_hourly_frame("NWPP", year)
        bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]
        system = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
        rows[year] = {
            "d": frame["Demand (Adjusted)"].sum() / 1e6,
            "ng": frame["Net generation (Adjusted)"].sum() / 1e6,
            "sw": _nwpp_grid_external_legs(
                year, pd.DatetimeIndex(frame["UTC time"])
            ).sum()
            / 1e6,
            "cf": sum(bench["classFull"].values()),
            "gm": sum(pay["years"][str(year)]["gmModel"].values()),
            "dem": system[system["pass"] == "P1"]["demand"].sum() / 1e6,
        }

    def line(label, fn):
        print(f"{label:<46}" + "".join("%10.3f" % fn(rows[y]) for y in YEARS))

    print(f"\n{'':<46}" + "".join(f"{y:>10}" for y in YEARS))
    line("EIA-930 pool  Demand (Adj)        [A]", lambda r: r["d"])
    line("EIA-930 pool  Net generation (Adj)[B]", lambda r: r["ng"])
    line("  -> footprint net imports  A-B", lambda r: r["d"] - r["ng"])
    line("GRID Desert-SW legs subtracted   [C]", lambda r: r["sw"])
    line("MODEL LP demand    (= B - C)     [D]", lambda r: r["dem"])
    line("  check  B - C", lambda r: r["ng"] - r["sw"])
    print()
    line("C1 benchmark classFull total     [E]", lambda r: r["cf"])
    line("MODEL total generation           [F]", lambda r: r["gm"])
    line("SCORED GAP   F - E", lambda r: r["gm"] - r["cf"])
    print()
    line("  (a) GRID-SW leg              -C", lambda r: -r["sw"])
    line("  (b) 930 [B] vs 923 [E]", lambda r: r["ng"] - r["cf"])
    line("  (a)+(b)", lambda r: -r["sw"] + r["ng"] - r["cf"])
    line(
        "  residual (storage round-trip + slack)",
        lambda r: (r["gm"] - r["cf"]) - (-r["sw"] + r["ng"] - r["cf"]),
    )


def _egrid_by_plant() -> pd.DataFrame:
    from market_sim.config.paths import FLEET_DIR

    ba_part = pd.read_parquet(
        FLEET_DIR / "egrid2023_data_rev2.34b4ed0ca1914829.PLNT23.parquet"
    )
    gen_part = pd.read_parquet(
        FLEET_DIR / "egrid2023_data_rev2.18751623c0bd0d88.PLNT23.parquet"
    )
    return ba_part.merge(gen_part, on="ORISPL", suffixes=("", "_y"))


def attribution(year: int = 2023) -> None:
    """Table 2 — per-BA EIA-930 NG vs the eGRID generation of its own plants."""
    from market_sim.data.fleet.models import NWPP_BAS
    from market_sim.data.zone_assignment import build_zone_lookup

    egrid = _egrid_by_plant()
    lut = {int(x) for x in build_zone_lookup("NWPP")}
    inside = egrid[egrid["ORISPL"].isin(lut)]
    by_ba = (inside.groupby("BACODE")["PLNGENAN"].sum() / 1e6).round(3)
    print(f"\n{'BA':<7}{'930 NG':>10}{'930 D':>10}{'eGRID gen':>11}{'delta':>10}")
    t_ng = t_eg = 0.0
    for ba in sorted(NWPP_BAS):
        path = Path(f"data/raw/eia-930-hourly/{ba} hourly.parquet")
        if not path.exists():
            continue
        frame = pd.read_parquet(path)
        frame = frame[pd.DatetimeIndex(frame["UTC time"]).year == year]
        ng = float(frame["Net generation (Adjusted)"].sum()) / 1e6
        dem = float(frame["Demand (Adjusted)"].sum()) / 1e6
        eg = float(by_ba.get(ba, 0.0))
        t_ng += ng
        t_eg += eg
        print(f"{ba:<7}{ng:>10.3f}{dem:>10.3f}{eg:>11.3f}{ng - eg:>10.3f}")
    print(f"{'TOTAL':<7}{t_ng:>10.3f}{'':>10}{t_eg:>11.3f}{t_ng - t_eg:>10.3f}")


def footprint() -> None:
    """Table 3 — the benchmark footprint IS the pool-BA footprint, both ways."""
    from market_sim.data.fleet.models import NWPP_BAS
    from market_sim.data.zone_assignment import build_zone_lookup

    egrid = _egrid_by_plant()
    lut = {int(x) for x in build_zone_lookup("NWPP")}
    egrid = egrid.assign(
        inside=egrid["ORISPL"].isin(lut),
        in_ba=egrid["BACODE"].astype(str).isin(NWPP_BAS),
    )
    bench_side = egrid[egrid["inside"]]
    stray = bench_side[~bench_side["in_ba"]]
    missing = egrid[(~egrid["inside"]) & egrid["in_ba"]]
    print(f"\nbenchmark footprint plants matched in eGRID : {len(bench_side)}")
    print(f"  with BACODE outside NWPP_BAS              : {len(stray)}")
    print(f"  pool-BA plants missing from the footprint : {len(missing)}")


def main() -> None:
    identity()
    attribution()
    footprint()


if __name__ == "__main__":
    main()
