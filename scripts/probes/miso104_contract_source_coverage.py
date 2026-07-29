"""miso-104 coverage ledger for the coal minimum-take TONNAGE data ask.

miso-103 adjudicated the minimum-take lane DATA-BLOCKED: every receipts-derived
tonnage is the same-year answer key (log R^2 0.87-0.94), so the constraint can
only be built on a genuinely CONTRACTUAL, ex-ante series. miso-104 sourced for
one and found none that spans the target set (see the standing ask,
``docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md``).

This probe prints, from committed artifacts only (NO LP, NO network), the
ledger a future intake session needs to size any candidate source:

  1. The 39-plant target set (the take-or-pay coal plants that report
     Schedule-5 fuel costs, i.e. the regulated set the constraint targets),
     with EIA-860 owner and state.
  2. Tonnage by STATE — the grain at which a state fuel-clause / contract
     repository would deliver coverage. Kentucky is the only MISO state with a
     public, un-redacted fuel-contract repository (807 KAR 5:056) and it holds
     exactly one target plant (D B Wilson, 6823).
  3. Tonnage by OWNER — the grain at which FERC Form 580 (docket IN79-6) would
     deliver coverage, since the form is filed per jurisdictional utility.

The ask's §2C coverage bar is >= 15 of the 39 plants AND >= 60 % of target-set
tonnage in EACH of 2023/2024/2025; this probe reports the denominators that bar
is measured against.

Usage:
    python scripts/probes/miso104_contract_source_coverage.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.fleet.eia860 import (  # noqa: E402
    active_eia860_dir,
    eia860_regulated_plants,
)

YEARS = [2023, 2024, 2025]
# The one MISO state publishing utility fuel-supply contracts in full
# (807 KAR 5:056; psc.ky.gov/webnet/fuelcontracts) — see the ask §3(b).
PUBLIC_CONTRACT_STATES = ["KY"]


def target_set() -> pd.DataFrame:
    """Per-plant annual coal receipt tons for the MISO take-or-pay target set.

    Same construction as ``miso103_mintake_pin_strength.annual_tons`` — the
    Schedule-5 fuel-cost parquet, restricted to the take-or-pay plant list.
    Receipts whose cost is withheld are dropped upstream, so the series covers
    the 39/49 cost-reporting (regulated) plants.
    """
    df = pd.read_parquet(
        REPO / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
    )
    coal = df[(df.fuel_group == "Coal") & (df.year <= 2025)]
    top = pd.read_csv(
        REPO / "data/raw/_processed-legacy/coal_takeorpay_MISO.csv"
    ).set_index("plant_code")
    coal = coal[coal.plant_id.isin(top.index)]
    return coal.groupby(["plant_id", "year"])["quantity"].sum().unstack("year")


def plant_identity() -> pd.DataFrame:
    """EIA-860 plant name / state / owning utility, one row per plant code."""
    p = pd.read_parquet(active_eia860_dir() / "eia860_plant.parquet")
    keep = [c for c in ("Plant Code", "Plant Name", "State", "Utility Name") if c in p.columns]
    return p[keep].drop_duplicates("Plant Code").set_index("Plant Code")


def main() -> None:
    ann = target_set()
    ident = plant_identity().reindex(ann.index)
    reg = eia860_regulated_plants()

    tbl = pd.DataFrame(
        {
            "plant": ident["Plant Name"],
            "state": ident["State"],
            "owner": ident["Utility Name"],
            "regulated": [c in reg for c in ann.index],
            **{f"tons_{y}": ann[y] for y in YEARS},
        }
    )

    print(f"== miso-104 target set: {len(tbl)} plants "
          f"({int(tbl.regulated.sum())} EIA-860 regulated) ==")
    for y in YEARS:
        print(f"   {y}: {tbl[f'tons_{y}'].sum() / 1e6:6.2f} Mt over "
              f"{int(tbl[f'tons_{y}'].notna().sum())} plants")

    print("\n== by STATE (the grain a state fuel-contract repository covers) ==")
    by_state = tbl.groupby("state").agg(
        plants=("plant", "size"), **{f"Mt_{y}": (f"tons_{y}", lambda s: s.sum() / 1e6) for y in YEARS}
    )
    print(by_state.sort_values(f"Mt_{YEARS[-1]}", ascending=False).round(2).to_string())

    for st in PUBLIC_CONTRACT_STATES:
        if st not in by_state.index:
            continue
        print(f"\n   {st} (public contract repository) coverage ceiling: "
              f"{int(by_state.loc[st, 'plants'])} of {len(tbl)} plants; " +
              ", ".join(
                  f"{y} {tbl.loc[tbl.state == st, f'tons_{y}'].sum() / tbl[f'tons_{y}'].sum():.1%}"
                  for y in YEARS
              ))

    print("\n== by OWNER (the grain a FERC Form 580 filing covers) ==")
    by_owner = tbl.groupby("owner").agg(
        plants=("plant", "size"), **{f"Mt_{y}": (f"tons_{y}", lambda s: s.sum() / 1e6) for y in YEARS}
    )
    print(by_owner.sort_values(f"Mt_{YEARS[-1]}", ascending=False).round(2).to_string())
    print(f"\n   {len(by_owner)} distinct owners must be covered to reach 100 % of the set; "
          f"the ask's §2C bar is >= 15 plants AND >= 60 % of tonnage in EVERY year.")


if __name__ == "__main__":
    main()
