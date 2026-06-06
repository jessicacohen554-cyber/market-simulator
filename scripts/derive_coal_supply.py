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
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.plant_taxonomy import COAL_CODE_TO_SUPPLY  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from scripts.process_f923_fuel_costs import (  # noqa: E402
    _find_zips,
    _load_generation,
    _load_receipts,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_coal_supply")

# EIA-923 ENERGY_SOURCE coal rank code -> model supply class, from the canonical
# taxonomy (the single source of truth, shared with the dispatch/offer-curve
# classification).
_COAL_SOURCE_TO_SUPPLY = COAL_CODE_TO_SUPPLY


def _dominant_class(
    grp: pd.DataFrame, code: int, weight: str, source: str
) -> dict:
    """Return one classification row: the weight-dominant supply class."""
    by_class = grp.groupby("supply_class")[weight].sum()
    total = by_class.sum()
    return {
        "plant_code": int(code),
        "supply_class": by_class.idxmax(),
        "source": source,
        "weight": float(total),
        "n_ranks": int((by_class > 0).sum()),
        "ranks": ";".join(
            f"{k}:{v / total:.0%}"
            for k, v in by_class.sort_values(ascending=False).items()
        ),
    }


def _coal_supply_table(iso: str, years: list[int] | None) -> pd.DataFrame:
    """Return ``[plant_code, supply_class, source, weight, n_ranks, ranks]``.

    One row per coal plant in ``iso``'s EIA-860 fleet, classified by its
    dominant coal rank. Primary source is EIA-923 Schedule-5 fuel *receipts*
    (by delivered tons); plants that file no coal receipts — common for large
    units whose coal is reported off the receipts form (e.g. Conemaugh,
    Keystone) — fall back to their dominant Page-1 *generation* fuel code (by
    net MWh), so every generating coal plant is covered and the model matches
    how the EIA-923 benchmark classifies the same plants.
    """
    iso_config = get_iso_config(iso)
    coal_codes = {
        int(g.plant_code)
        for g in load_fleet_from_csv(iso, iso_config)
        if g.fuel_type == "coal" and int(g.plant_code) > 0
    }
    logger.info("%s EIA-860 fleet has %d coal plants", iso, len(coal_codes))

    rframes, gframes = [], []
    for zip_path in _find_zips(REPO / "inputs" / "raw-data"):
        m = re.search(r"f923[_-]?(\d{4})", zip_path.stem)
        yr = int(m.group(1)) if m else 0
        if years is not None and yr not in years:
            continue
        rframes.append(_load_receipts(zip_path))
        gframes.append(_load_generation(zip_path, yr))

    # Primary: fuel receipts, dominant rank by delivered tons.
    receipts = pd.concat(rframes, ignore_index=True)
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
    rows = [
        _dominant_class(grp, code, "quantity", "receipts")
        for code, grp in coal.groupby("plant_id")
    ]
    classified = {r["plant_code"] for r in rows}

    # Fallback: Page-1 generation fuel code, dominant rank by net MWh, for coal
    # plants that filed no coal receipts.
    gen = pd.concat(gframes, ignore_index=True)
    gen["plant_id"] = pd.to_numeric(gen["plant_id"], errors="coerce")
    gen["netgen_annual_mwh"] = pd.to_numeric(
        gen["netgen_annual_mwh"], errors="coerce"
    ).fillna(0.0)
    gen = gen.dropna(subset=["plant_id"])
    gen["plant_id"] = gen["plant_id"].astype(int)
    gen["supply_class"] = gen["fuel_type"].map(_COAL_SOURCE_TO_SUPPLY)
    gen = gen[
        gen["supply_class"].notna()
        & gen["plant_id"].isin(coal_codes - classified)
        & (gen["netgen_annual_mwh"] > 0)
    ]
    rows += [
        _dominant_class(grp, code, "netgen_annual_mwh", "generation")
        for code, grp in gen.groupby("plant_id")
    ]

    out = pd.DataFrame(rows).sort_values("plant_code").reset_index(drop=True)
    missing = sorted(coal_codes - set(out["plant_code"]))
    if missing:
        logger.info(
            "%d %s coal plants had no EIA-923 coal receipts or generation "
            "(kept generic COAL): %s", len(missing), iso, missing,
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
