#!/usr/bin/env python3
"""Derive EIA-923 COMBINED-CYCLE-family heat rates per plant-year.

THE OBJECT (NWPP-NEXT-14; owner card "EIA-923 CC-family HR", 2026-09-30;
``docs/handoffs/FINDING-nwppnext14-bridger-and-clark-phase0-2026-09-30.md``):
the fleet's heat rate is eGRID's plant-grain ``PLHTRT`` = ``PLHTIAN`` /
``PLNGENAN``. Where CEMS meters only some of a plant's machines, ``PLHTIAN``
covers those machines while ``PLNGENAN`` covers the whole plant, so the rate
can fall below anything a combined cycle can physically do. Clark 2322 (NV
Energy): CAMPD meters its 24 GT peaker units but not its combined cycle, and
eGRID's plant rate reads 3.007 MMBtu/MWh.

THE CONSTRUCTION — zero free parameters, the owner's own fuel filing. For each
plant and year, over the EIA-923 generation-and-fuel rows whose prime mover is
in the combined-cycle family (CT, CA, CS, CC — the eGRID family construction's
CC set)::

    HR_cc = Σ elec_fuel_mmbtu ÷ Σ net_generation_mwh

The steam part (CA) burns no fuel of its own, so it enters the denominator
only, which is what makes the ratio a BLOCK rate. Each row is flagged ``ok``
when both sums are positive and the rate lies inside
``[EGRID_CC_HR_PHYSICAL_FLOOR, EGRID_CC_HR_PHYSICAL_CEILING]``, else
``out_of_window`` / ``no_data``. The consumer
(``market_sim.data.fleet.eia860._apply_eia923_cc_family_heat_rates``, under
``ScenarioConfig.eia923_cc_family_heat_rates``, default off) reads ``ok`` rows
only, and only for a non-CHP plant whose CC rows load a rate below the floor.

Membership: the ISO's operable EIA-860 plants (the ``derive_egrid_family_heat_rates``
membership, every BA the region comprises). Rule 13: EIA-923 regenerates for
any year and responds to changed conditions. Rule 23: re-derives only when
EIA-923 or EIA-860 updates. Rule 25: per-ISO artifact.

Output: ``data/raw/_processed-legacy/eia923_cc_family_heat_rates_<ISO>.csv``.
``--check`` re-derives and byte-compares against the committed file.

Usage::

    python scripts/data/derive_eia923_cc_family_heat_rates.py --iso NWPP
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

for _p in (
    str(Path(__file__).resolve().parents[2]),
    str(Path(__file__).resolve().parents[2] / "src"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config.constants import EGRID_CC_HR_PHYSICAL_CEILING  # noqa: E402
from market_sim.config.paths import (  # noqa: E402
    EIA_923_GENERATION_FUEL_PATH,
    PROCESSED_DIR,
)
from market_sim.data.fleet.eia860 import (  # noqa: E402
    _EIA923_CC_FAMILY_PRIME_MOVERS,
    EGRID_CC_HR_PHYSICAL_FLOOR,
)
from scripts.data.derive_egrid_family_heat_rates import iso_plant_ids  # noqa: E402

COLUMNS = [
    "plant_id",
    "plant_name",
    "year",
    "cc_prime_movers",
    "cc_elec_fuel_mmbtu",
    "cc_net_generation_mwh",
    "heat_rate_mmbtu_mwh",
    "flag",
    "iso",
    "source",
]


def derive(iso: str) -> pd.DataFrame:
    """Return the per-(plant, year) EIA-923 CC-family heat-rate rows for one ISO."""
    plants = iso_plant_ids(iso)
    g = pd.read_csv(EIA_923_GENERATION_FUEL_PATH)
    g = g[
        g["plant_id"].isin(plants)
        & g["prime_mover"]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(_EIA923_CC_FAMILY_PRIME_MOVERS)
    ]
    rows = []
    for (pid, year), grp in g.groupby(["plant_id", "year"], sort=True):
        fuel = float(grp["elec_fuel_mmbtu"].sum())
        net = float(grp["net_generation_mwh"].sum())
        if fuel > 0.0 and net > 0.0:
            hr = fuel / net
            flag = (
                "ok"
                if EGRID_CC_HR_PHYSICAL_FLOOR <= hr <= EGRID_CC_HR_PHYSICAL_CEILING
                else "out_of_window"
            )
        else:
            hr, flag = float("nan"), "no_data"
        rows.append(
            {
                "plant_id": int(pid),
                "plant_name": plants.get(int(pid), ""),
                "year": int(year),
                "cc_prime_movers": "+".join(
                    sorted(set(grp["prime_mover"].astype(str).str.strip().str.upper()))
                ),
                "cc_elec_fuel_mmbtu": round(fuel, 1),
                "cc_net_generation_mwh": round(net, 1),
                "heat_rate_mmbtu_mwh": round(hr, 4) if hr == hr else hr,
                "flag": flag,
                "iso": iso,
                "source": EIA_923_GENERATION_FUEL_PATH.name,
            }
        )
    return pd.DataFrame(rows, columns=COLUMNS)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--out-dir", type=Path, default=PROCESSED_DIR)
    ap.add_argument(
        "--check",
        action="store_true",
        help="re-derive and byte-compare against the committed artifact",
    )
    args = ap.parse_args()
    iso = args.iso.upper()
    df = derive(iso)
    out = args.out_dir / f"eia923_cc_family_heat_rates_{iso}.csv"
    if args.check:
        same = pd.read_csv(out).to_csv(index=False) == df.to_csv(index=False)
        print("MATCH" if same else "DIFFERS", out)
        sys.exit(0 if same else 1)
    df.to_csv(out, index=False)
    print(
        f"{iso}: {len(df)} (plant, year) rows over {df['plant_id'].nunique()} plants "
        f"({int((df['flag'] == 'ok').sum())} ok) -> {out}"
    )


if __name__ == "__main__":
    main()
