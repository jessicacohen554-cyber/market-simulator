"""Derive per-plant coal supply class (rank) for an ISO from EIA-923.

ERCOT coal is hand-curated into ``lignite`` / ``prb`` (mine-mouth vs rail) in
:data:`market_sim.data.fleet.COAL_PLANT_SUPPLY`. Other ISOs — PJM especially —
burn a *mix* of coal ranks (Appalachian/Illinois-Basin bituminous, Powder-River
sub-bituminous railed east, and Appalachian waste coal/culm) that a single
"COAL" class flattens. EIA-923 Schedule 5 (Fuel Receipts and Costs) records the
``ENERGY_SOURCE`` rank of every coal receipt, so each plant's dominant rank is
observable.

This reads the ``f923_*.zip`` releases, sums each plant's coal receipts by
``ENERGY_SOURCE`` (by delivered tons), and assigns the plant the supply class
of its dominant rank. The result is written to
``inputs/processed/coal_supply_<ISO>.csv`` (one row per coal plant), which
:func:`market_sim.data.fleet.coal_supply_class` merges on top of the ERCOT
base map — so adding an ISO is just running this script.

Usage:
    python scripts/derive_coal_supply.py --iso PJM
    python scripts/derive_coal_supply.py --iso PJM --year 2024
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from scripts.process_f923_fuel_costs import (  # noqa: E402
    _find_zips,
    _load_receipts,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_coal_supply")

# EIA-923 ``ENERGY_SOURCE`` coal rank codes -> model supply class. The model
# distinguishes the ranks that dispatch differently: sub-bituminous (PRB, cheap
# rail), bituminous (Appalachian/Illinois Basin), lignite (mine-mouth) and
# waste coal (culm/gob, near-zero or subsidised fuel, baseloaded). Anthracite
# and refined/synthetic coal are folded into the closest dispatch analogue.
_COAL_SOURCE_TO_SUPPLY: dict[str, str] = {
    "BIT": "bituminous",
    "SUB": "subbituminous",
    "LIG": "lignite",
    "WC": "waste",          # waste coal: culm, gob, coal-mine refuse
    "RC": "bituminous",     # refined coal (treated bituminous)
    "ANT": "bituminous",    # anthracite -> bituminous dispatch analogue
    "SC": "bituminous",     # coal-derived synfuel solids
    "SGC": "bituminous",    # coal-derived synthesis gas (rare in receipts)
}


def _coal_supply_table(iso: str, years: list[int] | None) -> pd.DataFrame:
    """Return ``[plant_code, supply_class, dominant_source, tons, ranks]``.

    One row per coal plant in ``iso``'s EIA-860 fleet that has coal receipts
    in the EIA-923 Schedule-5 releases; each plant's class is the supply class
    of its tonnage-dominant ``ENERGY_SOURCE``.
    """
    iso_config = get_iso_config(iso)
    coal_codes = {
        int(g.plant_code)
        for g in load_fleet_from_csv(iso, iso_config)
        if g.fuel_type == "coal" and int(g.plant_code) > 0
    }
    logger.info("%s EIA-860 fleet has %d coal plants", iso, len(coal_codes))

    frames = []
    for zip_path in _find_zips(REPO / "inputs" / "raw-data"):
        r = _load_receipts(zip_path)
        if years is not None and "year" in r.columns:
            r = r[pd.to_numeric(r["year"], errors="coerce").isin(years)]
        frames.append(r)
    receipts = pd.concat(frames, ignore_index=True)

    receipts["plant_id"] = pd.to_numeric(receipts["plant_id"], errors="coerce")
    receipts["quantity"] = pd.to_numeric(
        receipts["quantity"], errors="coerce"
    ).fillna(0.0)
    receipts = receipts.dropna(subset=["plant_id"])
    receipts["plant_id"] = receipts["plant_id"].astype(int)

    coal = receipts[
        (receipts["fuel_group"] == "Coal")
        & (receipts["plant_id"].isin(coal_codes))
    ].copy()
    coal["supply_class"] = coal["energy_source"].map(_COAL_SOURCE_TO_SUPPLY)
    coal = coal.dropna(subset=["supply_class"])

    rows = []
    for code, grp in coal.groupby("plant_id"):
        by_class = grp.groupby("supply_class")["quantity"].sum()
        dom = by_class.idxmax()
        rows.append({
            "plant_code": int(code),
            "supply_class": dom,
            "tons": float(by_class.sum()),
            "n_ranks": int((by_class > 0).sum()),
            "ranks": ";".join(
                f"{k}:{v / by_class.sum():.0%}"
                for k, v in by_class.sort_values(ascending=False).items()
            ),
        })
    out = pd.DataFrame(rows).sort_values("plant_code").reset_index(drop=True)

    missing = sorted(coal_codes - set(out["plant_code"]))
    if missing:
        logger.info(
            "%d %s coal plants had no EIA-923 coal receipts (kept generic "
            "COAL): %s", len(missing), iso, missing,
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Derive per-plant coal supply class from EIA-923."
    )
    parser.add_argument("--iso", required=True, help="ISO (e.g. PJM).")
    parser.add_argument(
        "--year", type=int, nargs="*", default=None,
        help="Restrict to these EIA-923 release years (default: all).",
    )
    parser.add_argument("--out-dir", default="inputs/processed")
    args = parser.parse_args()

    table = _coal_supply_table(args.iso.upper(), args.year)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"coal_supply_{args.iso.upper()}.csv"
    table.to_csv(out_path, index=False)

    counts = table["supply_class"].value_counts().to_dict()
    logger.info(
        "wrote %s: %d plants — %s",
        out_path, len(table), counts,
    )


if __name__ == "__main__":
    main()
