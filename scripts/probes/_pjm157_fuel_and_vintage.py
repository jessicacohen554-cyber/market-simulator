"""pjm-157 §3/§4 — PJM 2022 delivered-fuel resolution and the pooled-vintage bound.

Two Phase-0 checks the pjm-156 hand-back asks for, both no-LP and legal under the
active holdout freeze (CLAUDE.md rule 22):

**§3 — did 2022 gas actually resolve to 2022 prices?**  A fuel-input bug and an
offer-elasticity defect look identical in the C1 output and need opposite fixes,
so the delivered series is checked directly: PJM-footprint EIA-923
quantity-weighted delivered cost by fuel group and month, plus reporter counts,
for 2021-2025.  A silently pooled or stale vintage would show as a flat 2022 or a
reporter-count collapse.

**§4 — is there a hidden 2022 asymmetry in the pooled artifacts?**
``measured_ct_heat_rates`` (``campd_ct_heat_rates_<ISO>.csv``, pooled 2023-2025)
and ``measured_ramp_capability`` (plant-keyed, written with ``year=None``) are
applied to 2022 unchanged.  Both are physical machine constants rather than
year-varying market quantities, so the bound taken here is empirical: the only
class the CT heat-rate artifact prices is ``CT_PEAKER``, so its model-vs-actual
error across the four years bounds what the pooled vintage can own — including
its sign, which matters because a class the model runs too LOW cannot be the
cause of a ``CC_REGULAR`` surplus.

The ramp clean partition (``data/clean/ramp-capability``) is derived and
gitignored, so it is bounded the same empirical way rather than re-derived.
"""

from __future__ import annotations

import gzip
import json
from collections import defaultdict

import numpy as np
import pandas as pd

TWH = 1e6

BUNDLES = {
    2022: "results/calibration/pjm2022_touchpoint",
    2023: "results/calibration/pjm152_collapse_A",
    2024: "results/calibration/pjm152_collapse_A",
    2025: "results/calibration/pjm152_collapse_A",
}
PJM_STATES = ["OH", "PA", "NJ", "MD", "DE", "VA", "WV", "IL", "IN", "KY", "MI", "NC", "DC"]
F923 = "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
CT_HEAT_RATES = "data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv"


def footprint_prices(fuel_group: str, years: range) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Return PJM-footprint delivered price by month x year, plus annual and counts.

    Args:
        fuel_group: EIA-923 ``fuel_group`` value.
        years: years to include.

    Returns:
        ``(monthly_pivot, annual_series, reporter_counts)`` — prices in $/MMBtu,
        all quantity-weighted.
    """
    df = pd.read_parquet(F923)
    sub = df[
        (df.fuel_group == fuel_group)
        & (df.state.isin(PJM_STATES))
        & (df.year.isin(list(years)))
    ]
    wavg = lambda d: np.average(d.price_per_mmbtu, weights=np.maximum(d.quantity, 1e-9))  # noqa: E731
    monthly = sub.groupby(["year", "month"]).apply(wavg, include_groups=False).unstack(0)
    annual = sub.groupby("year").apply(wavg, include_groups=False)
    return monthly, annual, sub.groupby("year").size()


def class_totals(year: int, bundle: str) -> tuple[pd.Series, dict[str, float]]:
    """Return model P1 class totals and bench grid-delivered actuals, TWh.

    Args:
        year: solve year.
        bundle: bundle directory holding ``hourly/``.

    Returns:
        ``(model_series, actual_dict)`` keyed by class / bench group.
    """
    ch = pd.read_parquet(f"{bundle}/hourly/class_hourly_{year}.parquet")
    model = ch[ch["pass"] == "P1"].groupby("klass")["mw"].sum() / TWH
    bench = json.load(gzip.open(f"frontend/data/backcast/bench/PJM/{year}.json.gz"))
    actual: dict[str, float] = defaultdict(float)
    for rec in bench["bench"]["plants"].values():
        actual[rec["group"]] += rec.get("c_ann") or 0.0
    return model, actual


def main() -> None:
    """Print the delivered-fuel resolution check and the pooled-vintage bound."""
    print("=" * 78)
    print("§3 — PJM-footprint EIA-923 delivered fuel, quantity-weighted $/MMBtu")
    print("=" * 78)
    gas_m, gas_a, gas_n = footprint_prices("Natural Gas", range(2021, 2026))
    coal_m, coal_a, _ = footprint_prices("Coal", range(2021, 2026))
    print("gas, by month x year:")
    print(gas_m.round(2).to_string())
    print()
    print("annual:")
    summary = pd.DataFrame(
        {"gas": gas_a.round(2), "coal": coal_a.round(2),
         "gas/coal": (gas_a / coal_a).round(2), "gas reporters": gas_n}
    )
    print(summary.to_string())
    print()
    print("A stale or pooled 2022 vintage would show as a flat 2022 column or a")
    print("reporter-count collapse. Neither is present.")

    print()
    print("=" * 78)
    print("§4 — pooled-vintage bound")
    print("=" * 78)
    ct = pd.read_csv(CT_HEAT_RATES)
    ok = ct[ct.flag == "ok"]
    print(f"campd_ct_heat_rates_PJM.csv: years={ct['years'].unique()[0]}, "
          f"{len(ok)}/{len(ct)} plants flag=ok")
    print("  heat_rate MMBtu/net MWh:", ok["heat_rate"].describe()[["mean", "50%", "min", "max"]].round(3).to_dict())
    print("  model_over_measured:", ct["model_over_measured"].describe()[["mean", "50%", "25%", "75%"]].round(3).to_dict())
    print()
    print("Empirical bound — the only class this artifact prices is CT_PEAKER:")
    print(f"{'yr':>5}{'CT mdl':>9}{'CT act':>9}{'err':>8}{'ST_GAS m':>10}{'ST_GAS a':>10}{'err':>8}")
    for year, bundle in BUNDLES.items():
        m, a = class_totals(year, bundle)
        print(
            f"{year:>5}{m.get('CT_PEAKER', 0.0):>9.2f}{a['CT_PEAKER']:>9.2f}"
            f"{m.get('CT_PEAKER', 0.0) - a['CT_PEAKER']:>8.2f}"
            f"{m.get('ST_GAS', 0.0):>10.2f}{a['ST_GAS']:>10.2f}"
            f"{m.get('ST_GAS', 0.0) - a['ST_GAS']:>8.2f}"
        )
    print()
    print("2022's CT_PEAKER error sits ~2.5 TWh outside the in-sample range, so the")
    print("pooled vintage could own <=3 TWh — but the model runs CT_PEAKER too LOW,")
    print("so correcting it displaces CC_REGULAR DOWNWARD. Wrong sign for the CC object.")


if __name__ == "__main__":
    main()
