"""Derive the ERCOT delivered-gas CORROBORATOR series (ercot-261).

Writes ``data/raw/ercot_gas_corroborator_monthly.csv``: the EIA-923
Schedule-5 quantity-weighted delivered natural-gas price paid by Texas
electric-power plants, one row per (year, month), in $/MMBtu.

**What it is for.** The model's ERCOT delivered-gas LEVEL comes from EIA
series N3045TX3 (a state-level survey aggregate, ``$/Mcf``, read by
:func:`market_sim.data.fuel.basis.ercot.ercot_electric_power_gas_basis`).
That series is a monthly **cost / volume ratio**, and in a month whose
within-month price distribution is extreme it stops being a price at all:
February 2021 (Winter Storm Uri) prints $61.88/Mcf against a $4.49 median
over the other eleven months, because Texas gas traded near $3/MMBtu for
about twenty-four days and $100-1,200 for about four.

This script produces the **independent second measurement** of the same
quantity -- built from plant-level Schedule-5 receipts rather than the state
survey -- against which each month's survey print is corroborated by
:func:`~market_sim.data.fuel.basis.ercot.ercot_electric_power_gas_basis_monthly`
under ``ScenarioConfig.ercot_ep_gas_basis_corroborated``. A month where the
two independent measurements agree is admissible at monthly resolution; a
month where they disagree is not (rule 14 ``[R-ACCURATE]``).

Measured over 2019-01..2025-12 the two series agree within **$0.85/MMBtu in
82 of 84 months** and disagree in exactly two -- 2021-02 ($13.77) and
2021-12 ($3.47) -- with no month in the factor-4.1 gap between them
(``docs/PRECOMMIT-ercot261-gas-level-retirements-2026-09-09.md`` SS1c).

**Rule 23 ``[R-FROZEN-DERIVE]``**: this is a measured-behaviour derivation.
Re-run it only when the EIA-923 source data updates, and cite the data change
in the commit -- never because a residual moved.

Usage:
    python scripts/data/derive_ercot_gas_corroborator.py [--out PATH]
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.eia923 import load_monthly_fuel_costs

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_ercot_gas_corroborator")

#: Default output path (mirrors ERCOT_GAS_CORROBORATOR_PATH).
DEFAULT_OUT: Path = RAW_DATA_DIR / "ercot_gas_corroborator_monthly.csv"

#: The state whose Schedule-5 gas receipts proxy the ERCOT footprint -- the same
#: TX proxy ``ERCOT_ELECTRIC_POWER_GAS_PATH`` (series N3045TX3) is defined on, so
#: the two series measure the same population and are directly comparable.
_STATE: str = "TX"

#: EIA-923 ``FUEL_GROUP`` value for natural gas.
_FUEL_GROUP: str = "Natural Gas"


def build_corroborator(costs: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return the (year, month, price_usd_mmbtu, n_plants, quantity) frame.

    The price is the **quantity-weighted** mean of the reporting plants'
    delivered cost, which is the same statistic the state survey publishes --
    total cost over total volume -- so a disagreement between the two is a
    disagreement about the measurement, not about the estimator.

    Args:
        costs: Pre-loaded EIA-923 monthly cost frame (tests); loaded when None.

    Returns:
        One row per (year, month) with the quantity-weighted delivered price in
        $/MMBtu, sorted by year then month.
    """
    if costs is None:
        costs = load_monthly_fuel_costs()
    sub = costs[(costs["state"] == _STATE) & (costs["fuel_group"] == _FUEL_GROUP)]
    rows: list[dict[str, float | int]] = []
    for (year, month), grp in sub.groupby(["year", "month"], sort=True):
        qty = grp["quantity"].to_numpy(dtype=float)
        price = grp["price_per_mmbtu"].to_numpy(dtype=float)
        total = float(qty.sum())
        if total <= 0:
            continue
        rows.append(
            {
                "year": int(year),
                "month": int(month),
                "price_usd_mmbtu": float((price * qty).sum() / total),
                "n_plants": int(len(grp)),
                "quantity_mmbtu": total,
            }
        )
    return pd.DataFrame(rows).sort_values(["year", "month"]).reset_index(drop=True)


def main() -> None:
    """Build the corroborator series and write it to CSV."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    frame = build_corroborator()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    logger.info(
        "Wrote %d (year, month) rows covering %d-%02d..%d-%02d to %s",
        len(frame),
        int(frame["year"].iloc[0]),
        int(frame["month"].iloc[0]),
        int(frame["year"].iloc[-1]),
        int(frame["month"].iloc[-1]),
        args.out,
    )


if __name__ == "__main__":
    main()
