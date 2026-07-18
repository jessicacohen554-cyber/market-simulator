"""Derive per-plant natural-gas contract-vs-spot share for an ISO from EIA-923
Schedule 5 — the measured input that re-grounds the ERCOT Waha delivered-gas
floor depth (CLAUDE.md #11/#12).

The zonal gas basis (``market_sim.data.fuel.apply_ercot_zonal_gas_basis``) shifts
each ERCOT gas unit to its zone's measured hub basis vs Henry Hub. For the
West/Panhandle (Permian) that basis is the **Waha hub** (pooling-point) discount,
which collapses to ~$0/MMBtu and goes negative ~42% of days when basin takeaway is
constrained. But a power plant does not transact at that depressed wellhead pool:
only the gas it buys **spot** sees the collapse; its **firm-contracted** tonnage is
priced off a term index and is insulated. So the *delivered* discount a zone can
reach is bounded by its spot share — and that share is observable, not a guess.

EIA-923 Schedule 5 (Page 5, Fuel Receipts and Costs) records a **Purchase Type**
for every fuel receipt, so the contracted-vs-spot split is measurable and
forward-reproducible. Per the EIA-923 instructions the codes are:

    C   contract     — term >= 1 year (firm; insulated from the spot hub)
    NC  new contract  — term >= 1 year, began in the reporting year (firm)
    S   spot          — spot-market purchase (sees the hub collapse)
    T   tolling       — fuel supplied under a tolling agreement (firm)

This reads the ``f923_*.zip`` releases, sums each gas plant's **natural-gas**
receipts by Purchase Type (by delivered MMBtu), and writes the spot share
``spot_share = S / (C + NC + S + T)`` to
``data/raw/_processed-legacy/gas_takeorpay_<ISO>.csv`` (one row per gas plant).
:func:`market_sim.data.fuel.ercot_gas_spot_share_by_zone` aggregates it to model
zones; when ``ScenarioConfig.ercot_gas_contract_haircut`` is set, the zone's hub
basis is scaled by its measured spot share (the firm fraction is priced at the
fleet/firm level), so the West delivered discount is a *measured* haircut of the
Waha hub rather than the full hub basis or a chosen scalar floor.

Usage:
    python scripts/data/derive_gas_takeorpay.py --iso ERCOT
    python scripts/data/derive_gas_takeorpay.py --iso ERCOT --year 2023 2024 2025

Requires the raw ``f923_*.zip`` releases under ``inputs/raw-data/`` (gitignored;
only the derived per-plant CSV is committed). Re-download from the EIA-923
**archive** path (the live ``/xls/`` path 301-redirects to the homepage):

    curl -o inputs/raw-data/f923_2024.zip \\
      https://www.eia.gov/electricity/data/eia923/archive/xls/f923_2024.zip

(The current in-progress year's annual file is not published until ~Sept of the
following year; the contract/spot mix is structural, so pooling the available
full-year releases is sufficient.)
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from scripts.data.process_f923_fuel_costs import _find_zips, _load_receipts  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_gas_takeorpay")

# Schedule-5 Purchase Type codes grouped into firm (insulated from the spot hub)
# vs spot (sees the Waha collapse). Contract (C), new contract (NC) and tolling
# (T) are firm/term obligations; spot (S) is the price-responsive remainder.
_CONTRACT_CODES: frozenset[str] = frozenset({"C", "NC", "T"})
_SPOT_CODES: frozenset[str] = frozenset({"S"})

# EIA-923 reports gas under the "Natural Gas" fuel group; the gas fleet covers
# the model's gas prime movers (CC, CT, ST gas) so we key off the EIA-860 fleet.
_GAS_FUEL_TYPES: frozenset[str] = frozenset({"gas_cc", "gas_ct", "gas_st", "gas"})


def _gas_spot_table(iso: str, years: list[int] | None) -> pd.DataFrame:
    """Return ``[plant_code, spot_share, contract_share, total_mmbtu, n_receipts,
    source, breakdown]`` — one row per gas plant in ``iso`` with gas receipts.

    ``spot_share`` is the avoidable (price-responsive) fraction of delivered MMBtu:
    ``S / (C + NC + S + T)``. Plants that report no Purchase Type on any gas
    receipt are omitted (the loader treats a missing plant as fully spot —
    ``spot_share = 1.0`` — so the zonal haircut leaves the hub basis unchanged for
    them, the conservative default).
    """
    iso_config = get_iso_config(iso)
    gas_codes = {
        int(g.plant_code)
        for g in load_fleet_from_csv(iso, iso_config)
        if g.fuel_type in _GAS_FUEL_TYPES and int(g.plant_code) > 0
    }
    logger.info("%s EIA-860 fleet has %d gas plants", iso, len(gas_codes))

    rframes = []
    for zip_path in _find_zips(REPO / "inputs" / "raw-data"):
        m = re.search(r"f923[_-]?(\d{4})", zip_path.stem)
        yr = int(m.group(1)) if m else 0
        if years is not None and yr not in years:
            continue
        rframes.append(_load_receipts(zip_path))

    receipts = pd.concat(rframes, ignore_index=True)
    if "purchase_type" not in receipts.columns:
        raise SystemExit(
            "EIA-923 receipts carry no Purchase Type column — re-run after "
            "extending process_f923_fuel_costs._RENAME, or the workbook layout "
            "changed (check Page 5 header names)."
        )
    receipts["plant_id"] = pd.to_numeric(receipts["plant_id"], errors="coerce")
    receipts["quantity"] = pd.to_numeric(receipts["quantity"], errors="coerce").fillna(
        0.0
    )
    receipts = receipts.dropna(subset=["plant_id"])
    receipts["plant_id"] = receipts["plant_id"].astype(int)
    gas = receipts[
        (receipts["fuel_group"] == "Natural Gas")
        & (receipts["plant_id"].isin(gas_codes))
        & (receipts["quantity"] > 0)
    ].copy()
    gas["pt"] = gas["purchase_type"].astype(str).str.strip().str.upper()

    rows = []
    for code, grp in gas.groupby("plant_id"):
        by_pt = grp.groupby("pt")["quantity"].sum()
        total = float(by_pt.sum())
        if total <= 0:
            continue
        contract = float(by_pt.reindex(list(_CONTRACT_CODES)).fillna(0.0).sum())
        spot = float(by_pt.reindex(list(_SPOT_CODES)).fillna(0.0).sum())
        # Receipts with an unrecognised / blank Purchase Type are excluded from
        # both buckets; renormalise over the classified MMBtu so a plant that
        # filed a few blank rows is not spuriously diluted.
        classified = contract + spot
        if classified <= 0:
            continue
        rows.append(
            {
                "plant_code": int(code),
                "spot_share": round(spot / classified, 4),
                "contract_share": round(contract / classified, 4),
                "total_mmbtu": round(total, 1),
                "n_receipts": int(len(grp)),
                "source": "receipts",
                "breakdown": ";".join(
                    f"{k}:{v / total:.0%}"
                    for k, v in by_pt.sort_values(ascending=False).items()
                ),
            }
        )

    cols = [
        "plant_code",
        "spot_share",
        "contract_share",
        "total_mmbtu",
        "n_receipts",
        "source",
        "breakdown",
    ]
    if not rows:
        logger.info("%s: no gas plants with classifiable Purchase Type", iso)
        return pd.DataFrame(columns=cols)
    out = pd.DataFrame(rows).sort_values("plant_code").reset_index(drop=True)
    missing = sorted(gas_codes - set(out["plant_code"]))
    if missing:
        logger.info(
            "%d %s gas plants had no classifiable gas Purchase Type "
            "(treated as fully spot = no haircut): %d plants",
            len(missing),
            iso,
            len(missing),
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Derive per-plant gas contract/spot share from EIA-923."
    )
    parser.add_argument("--iso", required=True, help="ISO (e.g. ERCOT).")
    parser.add_argument(
        "--year",
        type=int,
        nargs="*",
        default=None,
        help="Restrict to these EIA-923 release years (default: all).",
    )
    parser.add_argument("--out-dir", default="data/raw/_processed-legacy")
    args = parser.parse_args()

    table = _gas_spot_table(args.iso.upper(), args.year)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"gas_takeorpay_{args.iso.upper()}.csv"
    table.to_csv(out_path, index=False)

    if not table.empty:
        logger.info(
            "wrote %s: %d plants — spot share mean %.0f%%, range %.0f-%.0f%%",
            out_path,
            len(table),
            100 * table["spot_share"].mean(),
            100 * table["spot_share"].min(),
            100 * table["spot_share"].max(),
        )
    else:
        logger.warning("wrote %s: no plants classified", out_path)


if __name__ == "__main__":
    main()
