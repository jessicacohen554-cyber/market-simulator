"""Derive each ISO's gas-capacity footprint weights by state.

The identification table behind ``ScenarioConfig.gas_electric_power_monthly_level``
(``market_sim.data.fuel.electric_power``): the EIA N3045 "natural gas sold to
electric power consumers" series is published **per state**, while the model
prices gas **per ISO**, so an ISO's measured delivered level is the
capacity-weighted blend of its footprint states' series. The weights are the
ISO's own installed gas capacity in each state, read from the EIA-860 operable
generator sheet joined to its plant's balancing authority — a measured
quantity with **zero free parameters** (rules 21 ``[R-DOF]`` / 24
``[R-REGISTRY]``), and the same construction for every ISO (rule 25
``[R-ISO-SCOPE]``: no ISO carries another's number).

Rule 23 ``[R-FROZEN-DERIVE]``: re-run ONLY when the EIA-860 vintage on disk
changes, and cite that data change in the re-derivation commit. NEVER because
a price residual moved.

Usage::

    python scripts/data/derive_iso_gas_state_weights.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.paths import EIA_860_DIR, REFERENCE_DIR  # noqa: E402
from market_sim.data.fleet import BA_CODE_TO_ISO  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_iso_gas_state_weights")

OUT_CSV: Path = REFERENCE_DIR / "iso-gas-capacity-state-weights.csv"

# EIA-860 ``Energy Source 1`` code for pipeline natural gas. Only NG-primary
# units count: the series being weighted is the price of gas DELIVERED to
# electric-power consumers, so the weight must be the gas the ISO actually
# buys, not its whole nameplate.
_NG_ENERGY_SOURCE = "NG"


def build_weights(eia_860_dir: Path = EIA_860_DIR) -> pd.DataFrame:
    """Return ``iso, state, gas_capacity_mw, weight`` for every modelled ISO."""
    operable = pd.read_parquet(eia_860_dir / "eia860_generator_operable.parquet")
    plant = pd.read_parquet(eia_860_dir / "eia860_plant.parquet")
    ba_by_plant = plant.drop_duplicates("Plant Code").set_index("Plant Code")[
        "Balancing Authority Code"
    ]
    frame = operable.assign(
        ba=operable["Plant Code"].map(ba_by_plant).astype("string").str.strip()
    )
    frame["iso"] = frame["ba"].map(BA_CODE_TO_ISO)
    gas = frame[
        frame["Energy Source 1"].astype("string").str.strip() == _NG_ENERGY_SOURCE
    ]
    gas = gas.assign(
        state=gas["State"].astype("string").str.strip(),
        mw=pd.to_numeric(gas["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0),
    ).dropna(subset=["iso"])

    totals = (
        gas.groupby(["iso", "state"], as_index=False)["mw"]
        .sum()
        .rename(columns={"mw": "gas_capacity_mw"})
    )
    totals = totals[totals["gas_capacity_mw"] > 0.0]
    totals["weight"] = totals["gas_capacity_mw"] / totals.groupby("iso")[
        "gas_capacity_mw"
    ].transform("sum")
    return totals.sort_values(["iso", "weight"], ascending=[True, False]).reset_index(
        drop=True
    )


def main() -> None:
    """Write the weight table and log each ISO's footprint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eia-860-dir", type=Path, default=EIA_860_DIR)
    parser.add_argument("--out", type=Path, default=OUT_CSV)
    args = parser.parse_args()

    weights = build_weights(args.eia_860_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    weights.to_csv(args.out, index=False, float_format="%.6f")
    logger.info("Wrote %d rows to %s", len(weights), args.out)
    for iso, group in weights.groupby("iso"):
        top = "  ".join(f"{r.state}={r.weight:.3f}" for r in group.head(6).itertuples())
        logger.info(
            "  %-6s %2d states  %8.0f MW  %s",
            iso,
            len(group),
            group["gas_capacity_mw"].sum(),
            top,
        )


if __name__ == "__main__":
    main()
