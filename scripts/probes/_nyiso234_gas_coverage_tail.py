"""OBJECT A, THE FUEL-SIDE FORK: does the model's gas price OBSERVE the tail? (nyiso-234, ZERO LP)

nyiso-233 measured that NYISO's price tail is an AVAILABILITY object rather than a
price-formation one — the model is not short in the hours the real market priced
highest (``docs/FINDING-nyiso233-tail-is-an-availability-object-2026-09-13.md``).
nyiso-227 had already measured the only availability instrument NYISO owns for
sub-5-day events and found it ~20x too small to bind
(``docs/FINDING-nyiso227-shortgas-outage-inert-2026-09-11.md``).

Both are consistent with a third reading neither tested, and which nyiso-233 §6
explicitly left open: **reality may not have been short either.** If the real
market cleared $573 on a marginal unit burning very expensive gas, then the
model's deficit is in the FUEL PRICE it burns in those hours, not in how much
capacity it has. That is a rule 14 ``[R-ACCURATE]`` input question, and it is
answerable with zero LP from committed artifacts.

This probe asks the narrow, falsifiable version:

    In the hours the tail is made of, does the model's delivered gas price rest
    on a SAME-DAY OBSERVATION, or on a fill across a hole in the source series?

The tail is selected on the ACTUAL price series only (nyiso-233's construction),
so no model outcome chooses the hours it is judged on. The model's gas series is
built by calling the keeper's own code path (``_nyiso_hub_daily_gas_prices``,
reached under the keeper's ``gas_hub_basis_overlay`` + ``gas_hub_basis_daily``),
never reconstructed by hand.

It reports coverage and the model's own gas level. It deliberately does NOT
assert what the unobserved price was — no committed source in this repository
carries it, and inventing one would be the magic number rule 5 ``[R-NO-MAGIC]``
forbids.

Run: ``python3 scripts/probes/_nyiso234_gas_coverage_tail.py [top_pct]``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BUN = Path("results/calibration/nyiso232_deleak_span/hourly")
ACT = Path("data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet")
SRC = Path("data/raw/gas-prices/transco_z6_ny_daily.csv")
YEARS = (2022, 2023, 2024, 2025)
TOP_PCT = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0


def _tail(year: int) -> pd.DataFrame:
    """Top-``TOP_PCT`` hours by ACTUAL RT price, with the model price and the gap."""
    s = pd.read_parquet(BUN / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    n = (
        s.assign(pw=s.price * s.demand)
        .groupby("hour")
        .agg(pw=("pw", "sum"), demand=("demand", "sum"))
    )
    g = pd.DataFrame(
        {
            "hour": n.index,
            "model": (n.pw / n.demand).to_numpy(),
            "demand": n.demand.to_numpy(),
        }
    )
    act = pd.read_parquet(ACT)
    a = act[act.year == year][["hour", "rt"]].rename(columns={"rt": "actual"})
    df = g.merge(a, on="hour").dropna()
    k = max(1, int(round(len(df) * TOP_PCT / 100.0)))
    t = df.nlargest(k, "actual").copy()
    t["gap"] = ((t.actual - t.model) * t.demand).clip(lower=0)
    return t


def _model_gas(year: int) -> np.ndarray:
    """The delivered gas series the keeper's own code path produces, $/MMBtu."""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel.hubs import _nyiso_hub_daily_gas_prices

    cfg = ScenarioConfig(
        iso="NYISO", mode="backcast", hindcast=True, start_year=year, end_year=year
    )
    return np.asarray(_nyiso_hub_daily_gas_prices(cfg, year, None, None), dtype=float)


def main() -> None:
    obs = pd.read_csv(SRC)
    obs["date"] = pd.to_datetime(obs["date"])
    observed = set(obs["date"].dt.date)

    print(f"NYISO tail GAS COVERAGE — top {TOP_PCT} % of hours by ACTUAL RT price")
    print(f"source: {SRC} ({len(obs)} rows, 2018-2025)\n")
    print(
        f"{'year':>5} {'tail h':>7} {'UNOBSERVED h':>13} {'% gap unobs':>12} "
        f"{'gas in tail':>12} {'yr median':>10} {'yr max':>8}"
    )

    rows = []
    for year in YEARS:
        t = _tail(year)
        gas = _model_gas(year)
        ts = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
            t.hour.to_numpy(), unit="h"
        )
        t["date"] = ts.date
        t["gas"] = gas[np.clip(t.hour.to_numpy(), 0, gas.size - 1)]
        t["unobs"] = ~t.date.isin(observed)

        total = float(t.gap.sum())
        pct = float(t.gap[t.unobs].sum()) / total * 100.0 if total > 0 else float("nan")
        tail_gas = float(np.average(t.gas, weights=t.demand))
        print(
            f"{year:>5} {len(t):>7} {int(t.unobs.sum()):>13} {pct:>11.1f}  "
            f"{tail_gas:>11.2f} {np.median(gas):>10.2f} {np.max(gas):>8.2f}"
        )
        rows.append((year, t, gas))

    print(
        "\nUNOBSERVED = the tail hour's own calendar date has NO row in the source daily\n"
        "series, so the model's gas there is a FILL, not a measurement. The source is a\n"
        "business-day series (~235 rows/yr), and holidays/weekends are exactly when the\n"
        "Northeast's extreme events fall.\n"
    )

    # The worst single window, named rather than summarised.
    year, t, gas = rows[0]
    idx = pd.date_range(f"{year}-01-01", periods=gas.size, freq="h")
    daily = pd.Series(gas, index=idx).resample("D").mean()
    worst = t.groupby("date").gap.sum().nlargest(3)
    print(
        f"{year} — the three days carrying the most tail gap, and the gas the model burnt:"
    )
    for d, gp in worst.items():
        mark = "  <-- NO OBSERVATION (filled)" if d not in observed else ""
        print(
            f"  {d}  gap-share {gp / t.gap.sum() * 100:>5.1f} %   "
            f"model gas {daily.loc[str(d)]:>6.2f} $/MMBtu{mark}"
        )


if __name__ == "__main__":
    main()
